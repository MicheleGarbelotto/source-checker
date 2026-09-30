"""Contract tests for the self-contained skill runtime packager."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import types
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPOSITORY_ROOT / "tools" / "sync_skill_runtime.py"


def _load_sync_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("runtime_sync_under_test", SYNC_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_skill(tmp_path: Path) -> Path:
    skill = tmp_path / "mock-skill"
    (skill / "scripts").mkdir(parents=True)
    return skill


def _file_hashes(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _import_vendored_runtime(scripts: Path) -> tuple[ModuleType, ModuleType, ModuleType]:
    original_path = sys.path.copy()
    original_dont_write_bytecode = sys.dont_write_bytecode
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "source_checker" or name.startswith("source_checker.")
    }
    for name in list(saved_modules):
        del sys.modules[name]
    dependency_modules = _install_optional_dependency_stubs()
    try:
        sys.dont_write_bytecode = True
        sys.path[:] = [
            str(scripts),
            *(
                entry
                for entry in original_path
                if str(REPOSITORY_ROOT).casefold() not in entry.casefold()
            ),
        ]
        import source_checker
        import source_checker.cli

        wrapper_spec = importlib.util.spec_from_file_location("vendored_source_corpus", scripts / "source_corpus.py")
        assert wrapper_spec is not None and wrapper_spec.loader is not None
        wrapper = importlib.util.module_from_spec(wrapper_spec)
        wrapper_spec.loader.exec_module(wrapper)
        return source_checker, source_checker.cli, wrapper
    finally:
        sys.dont_write_bytecode = original_dont_write_bytecode
        sys.path[:] = original_path
        for name in list(sys.modules):
            if name == "source_checker" or name.startswith("source_checker."):
                del sys.modules[name]
        sys.modules.update(saved_modules)
        for name, module in dependency_modules.items():
            if sys.modules.get(name) is module:
                del sys.modules[name]


def _install_optional_dependency_stubs() -> dict[str, ModuleType]:
    added: dict[str, ModuleType] = {}
    if importlib.util.find_spec("bs4") is not None:
        return added
    bs4 = types.ModuleType("bs4")
    bs4.__dict__.update({"BeautifulSoup": object})
    element = types.ModuleType("bs4.element")
    element.__dict__.update(
        {"Comment": object, "Doctype": object, "NavigableString": object, "Tag": object}
    )
    sys.modules["bs4"] = bs4
    sys.modules["bs4.element"] = element
    added.update({"bs4": bs4, "bs4.element": element})
    return added


def test_sync_vendors_complete_runtime_and_delegating_entrypoint(tmp_path: Path) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)

    assert runtime_sync.sync_runtime(skill) is True

    scripts = skill / "scripts"
    runtime = scripts / "source_checker"
    source_checker, cli, wrapper = _import_vendored_runtime(scripts)
    assert source_checker.__version__ == "0.1.0"
    assert wrapper.main is cli.main
    assert _file_hashes(runtime) == runtime_sync.runtime_hashes()
    assert all(path.suffix == ".py" for path in runtime.rglob("*") if path.is_file())
    assert not list(runtime.rglob("__pycache__"))
    assert not list(runtime.rglob("*.pyc"))
    assert not list(runtime.rglob("test*.py"))


def test_second_sync_is_deterministic_and_check_is_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    first = _file_hashes(skill / "scripts")

    assert runtime_sync.sync_runtime(skill) is True
    assert _file_hashes(skill / "scripts") == first
    assert runtime_sync.sync_runtime(skill, check=True) is True

    wrapper = skill / "scripts" / "source_corpus.py"
    wrapper.write_text("drift\n", encoding="utf-8")
    drifted = _file_hashes(skill / "scripts")
    assert runtime_sync.sync_runtime(skill, check=True) is False
    assert _file_hashes(skill / "scripts") == drifted

    assert runtime_sync.sync_runtime(skill) is True
    restored = _file_hashes(skill / "scripts")
    source = tmp_path / "changed-source"
    shutil.copytree(runtime_sync.SOURCE_RUNTIME, source)
    (source / "normalize.py").write_text("# changed source\n", encoding="utf-8")
    monkeypatch.setattr(runtime_sync, "SOURCE_RUNTIME", source)
    assert runtime_sync.sync_runtime(skill, check=True) is False
    assert _file_hashes(skill / "scripts") == restored


def test_sync_filters_test_files_without_excluding_testability_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    source = tmp_path / "canonical-source"
    (source / "tests").mkdir(parents=True)
    for relative_path in (
        "__init__.py",
        "testability.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_unit.py",
        "test_runtime.py",
        "runtime_test.py",
        "conftest.py",
    ):
        (source / relative_path).write_text(f"# {relative_path}\n", encoding="utf-8")
    monkeypatch.setattr(runtime_sync, "SOURCE_RUNTIME", source)
    skill = _make_skill(tmp_path)

    assert runtime_sync.sync_runtime(skill) is True

    runtime = skill / "scripts" / "source_checker"
    assert sorted(path.relative_to(runtime).as_posix() for path in runtime.rglob("*.py")) == [
        "__init__.py",
        "testability.py",
    ]
    assert runtime_sync.runtime_hashes() == _file_hashes(runtime)
    assert runtime_sync.sync_runtime(skill, check=True) is True
    (runtime / "testability.py").write_text("# drift\n", encoding="utf-8")
    assert runtime_sync.sync_runtime(skill, check=True) is False


@pytest.mark.parametrize(
    "relative_path",
    ("extra.txt", "test_unexpected.py", "tests/extra.py", "__pycache__/unexpected.pyc"),
)
def test_check_rejects_any_unexpected_installed_runtime_file(
    tmp_path: Path, relative_path: str
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    unexpected = skill / "scripts" / "source_checker" / relative_path
    unexpected.parent.mkdir(parents=True, exist_ok=True)
    unexpected.write_bytes(b"unexpected")
    before_check = _file_hashes(skill / "scripts")

    assert runtime_sync.sync_runtime(skill, check=True) is False
    assert _file_hashes(skill / "scripts") == before_check


def test_sync_rejects_unsafe_skill_and_destination_paths_without_external_deletion(tmp_path: Path) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    protected = outside / "keep.txt"
    protected.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="traversal"):
        runtime_sync.sync_runtime(skill / "..")

    linked_skill = tmp_path / "linked-skill"
    os.symlink(skill, linked_skill, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        runtime_sync.sync_runtime(linked_skill)

    destination = skill / "scripts" / "source_checker"
    os.symlink(outside, destination, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        runtime_sync.sync_runtime(skill)
    assert protected.read_text(encoding="utf-8") == "keep"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction regression")
def test_sync_rejects_junction_when_path_is_junction_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    protected = skill / "scripts" / "keep.txt"
    protected.write_text("keep", encoding="utf-8")
    linked_skill = tmp_path / "junction-skill"
    winapi = pytest.importorskip("_winapi")
    winapi.CreateJunction(str(skill), str(linked_skill))
    assert linked_skill.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    monkeypatch.delattr(Path, "is_junction", raising=False)
    assert not hasattr(linked_skill, "is_junction")

    with pytest.raises(ValueError, match="junction"):
        runtime_sync.sync_runtime(linked_skill)

    assert protected.read_text(encoding="utf-8") == "keep"
    assert sorted(path.name for path in (skill / "scripts").iterdir()) == ["keep.txt"]


def test_sync_stages_before_replacing_existing_runtime_on_copy_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    before = _file_hashes(skill / "scripts" / "source_checker")

    def fail_copy(*_: object) -> None:
        raise OSError("simulated copy failure")

    monkeypatch.setattr(runtime_sync, "_copy_runtime", fail_copy)
    with pytest.raises(OSError, match="simulated copy failure"):
        runtime_sync.sync_runtime(skill)
    assert _file_hashes(skill / "scripts" / "source_checker") == before
    assert not list((skill / "scripts").glob(".source_checker.stage-*"))
    assert not list((skill / "scripts").glob(".source_checker.backup-*"))


def test_wrapper_commit_failure_removes_a_fresh_partial_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)

    def fail_wrapper(*_: object) -> None:
        raise PermissionError("simulated wrapper commit failure")

    monkeypatch.setattr(runtime_sync, "_replace_wrapper", fail_wrapper)
    with pytest.raises(PermissionError, match="simulated wrapper commit failure"):
        runtime_sync.sync_runtime(skill)
    assert not (skill / "scripts" / "source_checker").exists()
    assert not (skill / "scripts" / "source_corpus.py").exists()


def test_restore_failure_preserves_backup_and_reports_its_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True

    def fail_wrapper(*_: object) -> None:
        raise PermissionError("simulated wrapper commit failure")

    def fail_restore(*_: object) -> None:
        raise PermissionError("simulated restore failure")

    monkeypatch.setattr(runtime_sync, "_replace_wrapper", fail_wrapper)
    monkeypatch.setattr(runtime_sync, "_restore_if_needed", fail_restore)
    with pytest.raises(runtime_sync.RuntimeSyncError, match="recovery") as error:
        runtime_sync.sync_runtime(skill)
    recovery_path = Path(error.value.recovery_path)
    assert recovery_path.exists()
    assert recovery_path.name.startswith(".source_checker.backup-")


def test_sync_aborts_if_scripts_directory_is_substituted_during_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    scripts = skill / "scripts"
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("do not touch", encoding="utf-8")
    original_copy = runtime_sync._copy_runtime

    def copy_then_substitute(source: Path, stage: Path, guard: object) -> None:
        original_copy(source, stage, guard)
        scripts.rename(skill / "scripts-original")
        os.symlink(outside, scripts, target_is_directory=True)

    monkeypatch.setattr(runtime_sync, "_copy_runtime", copy_then_substitute)
    with pytest.raises(runtime_sync.RuntimeSyncError, match="changed"):
        runtime_sync.sync_runtime(skill)
    assert sentinel.read_text(encoding="utf-8") == "do not touch"
    assert sorted(path.name for path in outside.iterdir()) == ["sentinel.txt"]


def test_overlapping_sync_is_rejected_while_the_first_sync_owns_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    original_copy = runtime_sync._copy_runtime
    outcomes: list[str] = []
    interleaved = False

    def copy_with_interleaved_sync(source: Path, stage: Path, guard: object) -> None:
        nonlocal interleaved
        if interleaved:
            original_copy(source, stage, guard)
            return
        interleaved = True
        try:
            runtime_sync.sync_runtime(skill)
        except runtime_sync.RuntimeSyncLockError:
            outcomes.append("blocked")
        else:
            outcomes.append("completed")
        original_copy(source, stage, guard)

    monkeypatch.setattr(runtime_sync, "_copy_runtime", copy_with_interleaved_sync)
    assert runtime_sync.sync_runtime(skill) is True
    assert outcomes == ["blocked"]
    assert runtime_sync.sync_runtime(skill, check=True) is True


def test_wrapper_subprocess_keeps_packaged_runtime_bytecode_free(tmp_path: Path) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    unrelated_cwd = tmp_path / "unrelated cwd"
    unrelated_cwd.mkdir()
    environment = os.environ.copy()
    environment.pop("PYTHONDONTWRITEBYTECODE", None)

    result = subprocess.run(
        [sys.executable, str(skill / "scripts" / "source_corpus.py"), "--help"],
        cwd=unrelated_cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not list((skill / "scripts" / "source_checker").rglob("__pycache__"))
    assert not list((skill / "scripts" / "source_checker").rglob("*.pyc"))
    assert runtime_sync.sync_runtime(skill, check=True) is True


@pytest.mark.parametrize("destination_name", ("source_checker", "source_corpus.py"))
def test_backup_creation_failure_preserves_existing_destinations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination_name: str
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    scripts = skill / "scripts"
    runtime_before = _file_hashes(scripts / "source_checker")
    wrapper_before = (scripts / "source_corpus.py").read_bytes()
    original_replace = runtime_sync.os.replace

    def fail_backup(source: Path, destination: Path) -> None:
        if source.name == destination_name and ".backup-" in destination.name:
            raise PermissionError("simulated backup creation failure")
        original_replace(source, destination)

    monkeypatch.setattr(runtime_sync.os, "replace", fail_backup)
    with pytest.raises(PermissionError, match="simulated backup creation failure"):
        runtime_sync.sync_runtime(skill)
    assert _file_hashes(scripts / "source_checker") == runtime_before
    assert (scripts / "source_corpus.py").read_bytes() == wrapper_before
    assert not list(scripts.glob("*.backup-*"))


def test_cleanup_failure_releases_lock_and_preserves_backup_for_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime_sync = _load_sync_module()
    skill = _make_skill(tmp_path)
    assert runtime_sync.sync_runtime(skill) is True
    old_file = skill / "scripts" / "source_checker" / "old.txt"
    old_file.write_text("old", encoding="utf-8")
    old_file.chmod(0o444)
    original_remove = runtime_sync._remove_path
    failed = False

    def fail_readonly_backup(path: Path | None, guard: object) -> None:
        nonlocal failed
        if path is not None and ".source_checker.backup-" in path.name and not failed:
            failed = True
            raise PermissionError("simulated read-only backup cleanup failure")
        original_remove(path, guard)

    monkeypatch.setattr(runtime_sync, "_remove_path", fail_readonly_backup)
    with pytest.raises(runtime_sync.RuntimeSyncError, match="cleanup") as error:
        runtime_sync.sync_runtime(skill)
    assert error.value.recovery_path is not None
    assert Path(error.value.recovery_path).exists()
    assert not (skill / "scripts" / ".source_checker.sync.lock").exists()
    assert runtime_sync.sync_runtime(skill) is True
    assert runtime_sync.sync_runtime(skill, check=True) is True
