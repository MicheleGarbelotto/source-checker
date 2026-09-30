"""Small, dependency-free BibTeX and BibLaTeX export loader."""

from __future__ import annotations

import re
from pathlib import Path

from source_checker.extractors import SUPPORTED_SUFFIXES

from . import SourceRecord, make_source_record, resolve_local_path

_ENTRY_START = re.compile(r"@(\w+)\s*([({])", re.IGNORECASE)


def load_bibtex(path: Path) -> list[SourceRecord]:
    export_path = Path(path).expanduser().resolve()
    return [_record(entry_type, key, body, export_path) for entry_type, key, body in _entries(export_path.read_text(encoding="utf-8-sig"))]


def _entries(text: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    start = 0
    while (match := _ENTRY_START.search(text, start)):
        entry_type = match.group(1).casefold()
        opening = match.group(2)
        closing = "}" if opening == "{" else ")"
        content_start = match.end()
        content_end = _matching_end(text, content_start, opening, closing)
        if content_end is None:
            break
        content = text[content_start:content_end]
        key, separator, body = content.partition(",")
        if separator and entry_type not in {"comment", "preamble", "string"}:
            entries.append((entry_type, key.strip(), body))
        start = content_end + 1
    return entries


def _matching_end(text: str, start: int, opening: str, closing: str) -> int | None:
    entry_depth = 1
    brace_depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if not quoted and character == "{":
            brace_depth += 1
            continue
        if not quoted and character == "}":
            if brace_depth:
                brace_depth -= 1
                continue
            if closing == "}":
                entry_depth -= 1
                if not entry_depth:
                    return index
                continue
        if character == '"' and brace_depth == 0:
            quoted = not quoted
        elif not quoted and brace_depth == 0 and opening == "(" and character == "(":
            entry_depth += 1
        elif not quoted and brace_depth == 0 and character == closing:
            entry_depth -= 1
            if not entry_depth:
                return index
    return None


def _record(entry_type: str, key: str, body: str, path: Path) -> SourceRecord:
    fields = _fields(body)
    date = fields.get("date", fields.get("year", ""))
    year_match = re.search(r"\b(\d{4})\b", date)
    author_value = fields.get("author", "")
    authors = _split_authors(author_value)
    aliases = [key, *re.split(r"\s*[,;]\s*", fields.get("ids", ""))]
    return make_source_record(
        aliases=aliases,
        title=_decode_bibtex_text(fields.get("title", "")),
        authors=[_decode_bibtex_text(author) for author in authors],
        year=int(year_match.group(1)) if year_match else None,
        doi=fields.get("doi", ""),
        url=fields.get("url", ""),
        local_files=[resolve_local_path(value, path) for value in _file_links(fields.get("file", ""))],
        provider="bibtex",
        preserve_author_order=tuple(_is_protected_corporate_author(author) for author in authors),
    )


def _fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in _split_top_level(body, ","):
        name, separator, value = part.partition("=")
        if separator:
            fields[name.strip().casefold()] = _field_value(value)
    return fields


def _split_top_level(value: str, separator: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quoted = False
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
        elif character == '"' and depth == 0:
            quoted = not quoted
        elif not quoted and character == "{":
            depth += 1
        elif not quoted and character == "}":
            depth = max(depth - 1, 0)
        elif not quoted and depth == 0 and character == separator:
            parts.append(value[start:index])
            start = index + 1
    parts.append(value[start:])
    return parts


def _field_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and ((value[0], value[-1]) in {("{", "}"), ('"', '"')}):
        value = value[1:-1].strip()
    return value.strip()


def _split_authors(value: str) -> list[str]:
    authors: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(value):
        if character == "{":
            depth += 1
        elif character == "}":
            depth = max(depth - 1, 0)
        elif (
            depth == 0
            and value[index : index + 3].casefold() == "and"
            and (index == 0 or value[index - 1].isspace())
            and (index + 3 == len(value) or value[index + 3].isspace())
        ):
            authors.append(value[start:index].strip())
            start = index + 3
    authors.append(value[start:].strip())
    return [author for author in authors if author]


def _file_links(value: str) -> list[str]:
    links: list[str] = []
    for item in value.split(";"):
        item = item.strip()
        if not item:
            continue
        link = _file_link(item)
        if link:
            links.append(link)
    return links


def _file_link(value: str) -> str:
    value = value.lstrip(":").replace(r"\:", ":")
    if re.match(r"^https?://", value, flags=re.IGNORECASE):
        return ""
    extension = "(?:" + "|".join(
        re.escape(suffix) for suffix in sorted(SUPPORTED_SUFFIXES, key=len, reverse=True)
    ) + ")"
    for pattern in (
        rf"^(file:///.+?{extension})(?::.+)?$",
        rf"^([A-Za-z]:[\\/].+?{extension})(?::.+)?$",
        rf"^[^:]+:(.+?{extension})(?::.+)?$",
        rf"^(.+?{extension})(?::.+)?$",
    ):
        if match := re.match(pattern, value, re.IGNORECASE):
            return match.group(1)
    return value


def _is_protected_corporate_author(value: str) -> bool:
    value = value.strip()
    return value.startswith("{") and value.endswith("}")


def _decode_bibtex_text(value: str) -> str:
    value = value.replace(r"\{", "\ue000").replace(r"\}", "\ue001")
    value = re.sub(r"\\([$%&_#'\"`^~=])", r"\1", value)
    value = value.replace("~", " ")
    value = re.sub(r"[{}]", "", value)
    return value.replace("\ue000", "{").replace("\ue001", "}")
