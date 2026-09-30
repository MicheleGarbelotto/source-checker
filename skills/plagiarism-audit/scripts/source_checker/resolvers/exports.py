"""Dispatch read-only bibliography-export loading by filename suffix."""

from __future__ import annotations

from pathlib import Path

from source_checker.bibliography import SourceRecord, load_bibtex, load_csl_json, load_ris


class UnsupportedExportError(ValueError):
    """Raised when a path is not a supported bibliography export."""


def load_export(path: Path) -> list[SourceRecord]:
    export_path = Path(path)
    loaders = {".bib": load_bibtex, ".ris": load_ris, ".json": load_csl_json}
    try:
        return loaders[export_path.suffix.casefold()](export_path)
    except KeyError as error:
        raise UnsupportedExportError(f"Unsupported bibliography export: {export_path.suffix}") from error
