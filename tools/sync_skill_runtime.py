"""Package the source-checker runtime into a skill's scripts directory.

Use ``--check`` to verify that an existing packaged runtime matches this
repository without modifying the skill directory.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

SOURCE_RUNTIME = Path(__file__).resolve().parents[1] / "src" / "source_checker"
RUNTIME_NAME = "source_checker"
WRAPPER_NAME = "source_corpus.py"
_LOCK_NAME = ".source_checker.sync.lock"
_WRAPPER = (
    '"""Thin entry point for the vendored source-checker runtime."""\n\n'
    "import sys\n\n"
    "sys.dont_write_bytecode = True\n\n"
    "from source_checker.cli import main\n\n\n"
    'if __name__ == "__main__":\n'
    "    raise SystemExit(main())\n"
)


class RuntimeSyncError(RuntimeError):
    """A sync failure that may require manual recovery."""

    def __init__(self, message: str, *, recovery_path: Path | None = None) -> None:
        super().__init__(message)
        self.recovery_path = str(recovery_path) if recovery_path is not None else None


class RuntimeSyncLockError(RuntimeSyncError):
    """Raised when another sync currently owns the skill runtime lock."""


@dataclass(frozen=True)
class _Destination:
    skill: Path
    scripts: Path
    skill_identity: tuple[str, int, int]
    scripts_identity: tuple[str, int, int]


@dataclass
class _InstallState:
    destination: Path
    existed: bool
    backup: Path | None = None
    installed: bool = False


def sync_runtime(skill_dir: Path | str, *, check: bool = False) -> bool:
    """Synchronize the canonical runtime into ``skill_dir/scripts``."""
    source = _validated_source()
    destination = _validated_destination(skill_dir)
    runtime = destination.scripts / RUNTIME_NAME
    wrapper = destination.scripts / WRAPPER_NAME
    _validate_targets(destination, runtime, wrapper)
    expected = _expected_hashes(source)
    if check:
        return _installed_hashes(runtime, wrapper) == expected

    lock = _acquire_lock(destination)
    stage: Path | None = None
    wrapper_stage: Path | None = None
    runtime_state = _InstallState(runtime, runtime.exists())
    wrapper_state = _InstallState(wrapper, wrapper.exists())
    completed = False
    try:
        _reverify(destination)
        stage = Path(tempfile.mkdtemp(prefix=f".{RUNTIME_NAME}.stage-", dir=destination.scripts))
        _reverify(destination)
        wrapper_stage = destination.scripts / f".{WRAPPER_NAME}.stage-{uuid4().hex}"
        _copy_runtime(source, stage, lambda: _reverify(destination))
        _reverify(destination)
        wrapper_stage.write_text(_WRAPPER, encoding="utf-8", newline="\n")
        _replace_runtime(stage, runtime_state, lambda: _reverify(destination))
        _replace_wrapper(wrapper_stage, wrapper_state, lambda: _reverify(destination))
        completed = True
        return True
    except Exception as error:
        recovery_path = _rollback((wrapper_state, runtime_state), destination)
        if recovery_path is not None:
            raise RuntimeSyncError(
                f"Runtime sync failed; recovery backup preserved at {recovery_path}",
                recovery_path=recovery_path,
            ) from error
        raise
    finally:
        cleanup_error: RuntimeSyncError | None = None
        try:
            _cleanup_transaction(
                destination,
                (stage, wrapper_stage),
                (runtime_state, wrapper_state),
                completed=completed,
            )
        except (OSError, RuntimeSyncError) as error:
            recovery_path = _recovery_backup((runtime_state, wrapper_state))
            cleanup_error = RuntimeSyncError(
                f"Runtime sync cleanup failed; recovery backup preserved at {recovery_path}",
                recovery_path=recovery_path,
            )
            cleanup_error.__cause__ = error
        finally:
            _release_lock(destination, lock)
        if cleanup_error is not None:
            raise cleanup_error


def runtime_hashes() -> dict[str, str]:
    """Return a deterministic SHA-256 map for canonical runtime Python files."""
    return _tree_hashes(_validated_source())


def _validated_source() -> Path:
    source = SOURCE_RUNTIME.resolve(strict=True)
    if not source.is_dir():
        raise ValueError(f"Canonical runtime is not a directory: {source}")
    return source


def _validated_destination(skill_dir: Path | str) -> _Destination:
    supplied = Path(skill_dir).expanduser()
    if ".." in supplied.parts:
        raise ValueError("Skill directory traversal is not allowed")
    _assert_safe_ancestors(supplied)
    skill = supplied.resolve(strict=True)
    if not skill.is_dir():
        raise ValueError(f"Skill directory is not a directory: {skill}")
    scripts = skill / "scripts"
    if not scripts.is_dir():
        raise ValueError(f"Skill scripts directory is missing: {scripts}")
    _assert_safe_ancestors(scripts)
    scripts = scripts.resolve(strict=True)
    if not _is_within(scripts, skill):
        raise ValueError("Skill scripts directory escapes the supplied skill directory")
    return _Destination(skill, scripts, _identity(skill), _identity(scripts))


def _assert_safe_ancestors(path: Path) -> None:
    current = path.absolute()
    while True:
        if current.is_symlink() or _is_junction(current):
            raise ValueError(f"Skill path symlinks or junctions are not allowed: {current}")
        if current.parent == current:
            return
        current = current.parent


def _is_junction(path: Path) -> bool:
    predicate = getattr(path, "is_junction", None)
    if predicate is not None:
        return bool(predicate())
    # Python 3.11 lacks Path.is_junction; reject directory reparse points conservatively.
    try:
        status = path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return False
    attributes = getattr(status, "st_file_attributes", 0)
    return stat.S_ISDIR(status.st_mode) and bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _identity(path: Path) -> tuple[str, int, int]:
    resolved = path.resolve(strict=True)
    status = resolved.stat()
    return str(resolved), status.st_dev, status.st_ino


def _reverify(destination: _Destination) -> None:
    try:
        _assert_safe_ancestors(destination.skill)
        _assert_safe_ancestors(destination.skill / "scripts")
        scripts = (destination.skill / "scripts").resolve(strict=True)
        if scripts != destination.scripts or not _is_within(scripts, destination.skill):
            raise RuntimeSyncError("Skill scripts directory changed during sync")
        if _identity(destination.skill) != destination.skill_identity:
            raise RuntimeSyncError("Skill directory changed during sync")
        if _identity(scripts) != destination.scripts_identity:
            raise RuntimeSyncError("Skill scripts directory changed during sync")
    except RuntimeSyncError:
        raise
    except (OSError, ValueError) as error:
        raise RuntimeSyncError("Skill path changed during sync") from error


def _validate_targets(destination: _Destination, runtime: Path, wrapper: Path) -> None:
    _reverify(destination)
    for candidate in (runtime, wrapper):
        if candidate.is_symlink() or _is_junction(candidate):
            raise ValueError(f"Destination symlink or junction is not allowed: {candidate}")
        if candidate.exists() and not _is_within(candidate.resolve(), destination.scripts):
            raise ValueError(f"Destination escapes skill scripts directory: {candidate}")
    if runtime.exists() and not runtime.is_dir():
        raise ValueError(f"Runtime destination is not a directory: {runtime}")
    if wrapper.exists() and not wrapper.is_file():
        raise ValueError(f"Wrapper destination is not a file: {wrapper}")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return path != parent


def _runtime_files(source: Path) -> list[Path]:
    return sorted(
        (path for path in source.rglob("*.py") if not _is_test_file(path.relative_to(source))),
        key=lambda path: path.relative_to(source).as_posix(),
    )


def _is_test_file(relative_path: Path) -> bool:
    name = relative_path.name
    return (
        "__pycache__" in relative_path.parts
        or "tests" in relative_path.parts
        or name == "conftest.py"
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _copy_runtime(source: Path, stage: Path, guard: Callable[[], None]) -> None:
    for source_file in _runtime_files(source):
        target = stage / source_file.relative_to(source)
        guard()
        target.parent.mkdir(parents=True, exist_ok=True)
        guard()
        shutil.copy2(source_file, target)


def _tree_hashes(directory: Path) -> dict[str, str]:
    return {path.relative_to(directory).as_posix(): _sha256(path) for path in _runtime_files(directory)}


def _expected_hashes(source: Path) -> dict[str, str]:
    return {
        **{f"{RUNTIME_NAME}/{name}": digest for name, digest in _tree_hashes(source).items()},
        WRAPPER_NAME: hashlib.sha256(_WRAPPER.encode("utf-8")).hexdigest(),
    }


def _installed_hashes(runtime: Path, wrapper: Path) -> dict[str, str]:
    if not runtime.is_dir() or not wrapper.is_file():
        return {}
    return {
        **{
            f"{RUNTIME_NAME}/{path.relative_to(runtime).as_posix()}": _sha256(path)
            for path in sorted(runtime.rglob("*"))
            if path.is_file()
        },
        WRAPPER_NAME: _sha256(wrapper),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _replace_runtime(stage: Path, state: _InstallState, guard: Callable[[], None]) -> None:
    _replace_stage(stage, state, guard, RUNTIME_NAME)


def _replace_wrapper(stage: Path, state: _InstallState, guard: Callable[[], None]) -> None:
    _replace_stage(stage, state, guard, WRAPPER_NAME)


def _replace_stage(stage: Path, state: _InstallState, guard: Callable[[], None], name: str) -> None:
    if state.existed:
        backup = state.destination.parent / f".{name}.backup-{uuid4().hex}"
        guard()
        os.replace(state.destination, backup)
        state.backup = backup
    try:
        guard()
        os.replace(stage, state.destination)
        state.installed = True
    except Exception:
        if state.backup is not None:
            _restore_if_needed(state.backup, state.destination, guard)
            state.backup = None
        raise


def _restore_if_needed(backup: Path, destination: Path, guard: Callable[[], None]) -> None:
    guard()
    if destination.exists():
        _remove_path(destination, guard)
    guard()
    os.replace(backup, destination)


def _rollback(states: Sequence[_InstallState], destination: _Destination) -> Path | None:
    for state in states:
        try:
            _rollback_state(state, lambda: _reverify(destination))
        except (OSError, RuntimeSyncError):
            return _recovery_backup(states)
    return None


def _rollback_state(state: _InstallState, guard: Callable[[], None]) -> None:
    if state.existed and state.backup is not None and state.backup.exists():
        _restore_if_needed(state.backup, state.destination, guard)
        state.backup = None
        state.installed = False
    elif not state.existed and state.installed:
        _remove_path(state.destination, guard)
        state.installed = False


def _recovery_backup(states: Sequence[_InstallState]) -> Path | None:
    return next(
        (state.backup for state in states if state.backup is not None and state.backup.exists()),
        None,
    )


def _cleanup_transaction(
    destination: _Destination,
    temporary_paths: Sequence[Path | None],
    states: Sequence[_InstallState],
    *,
    completed: bool,
) -> None:
    try:
        _reverify(destination)
    except RuntimeSyncError:
        return
    guard = lambda: _reverify(destination)
    for path in temporary_paths:
        _remove_path(path, guard)
    if completed:
        for state in states:
            _remove_path(state.backup, guard)
            state.backup = None


def _remove_path(path: Path | None, guard: Callable[[], None]) -> None:
    if path is None or not path.exists():
        return
    guard()
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _acquire_lock(destination: _Destination) -> Path:
    lock = destination.scripts / _LOCK_NAME
    _reverify(destination)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeSyncLockError(
            f"Runtime sync lock already exists: {lock}. Remove it only after confirming no sync is active."
        ) from error
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
    finally:
        os.close(descriptor)
    return lock


def _release_lock(destination: _Destination, lock: Path) -> None:
    try:
        _remove_path(lock, lambda: _reverify(destination))
    except RuntimeSyncError:
        return


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that each packaged runtime matches this repository without writing files",
    )
    parser.add_argument("skill_dirs", metavar="SKILL_DIR", nargs="+", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    results = [sync_runtime(skill_dir, check=args.check) for skill_dir in args.skill_dirs]
    if args.check:
        for skill_dir, matches in zip(args.skill_dirs, results, strict=True):
            print(f"{'up to date' if matches else 'out of date'}: {skill_dir}")
        return 0 if all(results) else 1
    for skill_dir in args.skill_dirs:
        print(f"synced: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
