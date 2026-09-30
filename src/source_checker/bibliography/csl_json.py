"""CSL-JSON bibliography export loader."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import SourceRecord, is_local_path_reference, make_source_record, resolve_local_path


def load_csl_json(path: Path) -> list[SourceRecord]:
    export_path = Path(path).expanduser().resolve()
    payload = json.loads(export_path.read_text(encoding="utf-8-sig"))
    items = payload if isinstance(payload, list) else [payload]
    return [_record(item, export_path) for item in items if isinstance(item, Mapping)]


def _record(data: Mapping[str, Any], path: Path) -> SourceRecord:
    issued = data.get("issued", {})
    date_parts = issued.get("date-parts", []) if isinstance(issued, Mapping) else []
    year = _year(date_parts)
    aliases = [_identifier(data.get(key)) for key in ("id", "citation-key", "citationKey", "item-key", "zotero-item-key")]
    return make_source_record(
        aliases=aliases,
        title=_text(data.get("title")),
        authors=_authors(data.get("author", [])),
        year=year,
        doi=_text(data.get("DOI", data.get("doi"))),
        url=_text(data.get("URL", data.get("url"))),
        local_files=[resolve_local_path(link, path) for link in _attachments(data) if is_local_path_reference(link)],
        provider="csl-json",
        preserve_author_order=True,
    )


def _year(date_parts: Any) -> int | None:
    if isinstance(date_parts, list) and date_parts and isinstance(date_parts[0], list) and date_parts[0]:
        value = date_parts[0][0]
        if isinstance(value, int) or (isinstance(value, str) and re.fullmatch(r"\d{4}", value)):
            return int(value)
    return None


def _authors(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    authors: list[str] = []
    for value in values:
        if not isinstance(value, Mapping):
            continue
        if literal := value.get("literal"):
            authors.append(_text(literal))
        else:
            authors.append(
                " ".join(
                    _text(value.get(key))
                    for key in ("given", "non-dropping-particle", "family")
                    if value.get(key)
                )
            )
    return authors


def _attachments(data: Mapping[str, Any]) -> list[str]:
    links: list[str] = []
    for key in ("attachment", "attachments", "file"):
        value = data.get(key)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, str):
                links.append(item)
            elif isinstance(item, Mapping):
                for field in ("path", "file", "url"):
                    if item.get(field):
                        links.append(_text(item[field]))
                        break
    return links


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _identifier(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""
