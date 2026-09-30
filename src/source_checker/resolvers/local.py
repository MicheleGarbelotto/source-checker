"""Deterministic local-file discovery without reference-manager database access."""

from __future__ import annotations

import hashlib
import mimetypes
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalFile:
    path: str
    sha256: str
    media_type: str


def resolve_local_sources(paths: Iterable[Path]) -> list[LocalFile]:
    expanded: set[Path] = set()
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path.is_file():
            expanded.add(path.resolve())
        elif path.is_dir():
            expanded.update(child.resolve() for child in path.rglob("*") if child.is_file())
        else:
            raise FileNotFoundError(f"Local source path does not exist: {path}")
    return [_local_file(path) for path in sorted(expanded, key=_path_sort_key)]


def _path_sort_key(path: Path) -> tuple[str, str]:
    value = str(path)
    return value.casefold(), value


def _local_file(path: Path) -> LocalFile:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return LocalFile(path=str(path), sha256=digest.hexdigest(), media_type=media_type)
