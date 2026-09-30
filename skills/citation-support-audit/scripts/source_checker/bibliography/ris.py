"""RIS bibliography export loader."""

from __future__ import annotations

import re
from pathlib import Path

from . import SourceRecord, is_local_path_reference, make_source_record, resolve_local_path


def load_ris(path: Path) -> list[SourceRecord]:
    export_path = Path(path).expanduser().resolve()
    records: list[SourceRecord] = []
    current: dict[str, list[str]] | None = None
    for line in export_path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^([A-Z0-9]{2})\s{2}-\s?(.*)$", line)
        if not match:
            continue
        tag, value = match.groups()
        if tag == "TY":
            current = {"TY": [value]}
        elif tag == "ER":
            if current is not None:
                records.append(_record(current, export_path))
            current = None
        elif current is not None:
            current.setdefault(tag, []).append(value.strip())
    return records


def _first(record: dict[str, list[str]], *tags: str) -> str:
    for tag in tags:
        if values := record.get(tag):
            return values[0]
    return ""


def _record(data: dict[str, list[str]], path: Path) -> SourceRecord:
    year_match = re.search(r"\b(\d{4})\b", _first(data, "PY", "Y1", "DA"))
    aliases = [*_values(data, "CN", "ID"), *_values(data, "C1")]
    links = [
        resolve_local_path(value, path)
        for value in _values(data, "UR", "L1", "L2")
        if is_local_path_reference(value)
    ]
    return make_source_record(
        aliases=aliases,
        title=_first(data, "TI", "T1", "CT"),
        authors=_values(data, "AU", "A1"),
        year=int(year_match.group(1)) if year_match else None,
        doi=_first(data, "DO"),
        url=_first(data, "UR"),
        local_files=links,
        provider="ris",
    )


def _values(record: dict[str, list[str]], *tags: str) -> list[str]:
    return [value for tag in tags for value in record.get(tag, [])]
