"""Neutral records and loaders for common bibliography export formats."""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class SourceRecord:
    """A bibliography source independent of the application that exported it."""

    source_id: str
    aliases: tuple[str, ...]
    title: str
    authors: tuple[str, ...]
    year: int | None
    doi: str
    url: str
    local_files: tuple[str, ...]
    provider: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "aliases", tuple(self.aliases))
        object.__setattr__(self, "authors", tuple(self.authors))
        object.__setattr__(self, "local_files", tuple(self.local_files))


def normalize_doi(value: str | None) -> str:
    """Return a canonical DOI without a resolver URL or prefix."""
    result = value.strip() if isinstance(value, str) else ""
    result = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", result, flags=re.IGNORECASE)
    result = re.sub(r"^doi\s*:\s*", "", result, flags=re.IGNORECASE)
    result = result.strip().rstrip(".,;")
    wrappers = {(")", "("), ("]", "["), ("}", "{")}
    while result and any(result.endswith(closing) and result.count(closing) > result.count(opening) for closing, opening in wrappers):
        result = result[:-1].rstrip()
    return result.casefold()


def normalize_authors(
    values: Iterable[str], *, preserve_order: bool | Iterable[bool] = False
) -> tuple[str, ...]:
    normalized: list[str] = []
    protected = None if isinstance(preserve_order, bool) else tuple(preserve_order)
    for index, value in enumerate(values):
        name = _clean_text(value)
        if not name:
            continue
        preserve_token_order = preserve_order if isinstance(preserve_order, bool) else (
            protected[index] if protected is not None and index < len(protected) else False
        )
        if not preserve_token_order and "," in name:
            family, given = (part.strip() for part in name.split(",", 1))
            name = " ".join(part for part in (given, family) if part)
        normalized.append(name)
    return tuple(normalized)


def resolve_local_path(value: str, export_path: Path) -> str:
    """Resolve a linked local path without requiring it to exist."""
    candidate = value.strip().strip('"')
    if candidate.lower().startswith("file:"):
        parsed = urlparse(candidate)
        candidate = unquote(parsed.path)
        if parsed.netloc and parsed.netloc.casefold() != "localhost":
            prefix = "\\\\" if os.name == "nt" else "//"
            candidate = prefix + parsed.netloc + candidate
        if re.match(r"^/[A-Za-z]:[\\/]", candidate):
            candidate = candidate[1:]
    if _is_windows_absolute(candidate):
        return _canonical_local_path(candidate)
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = export_path.parent / path
    return str(path.resolve())


def is_local_path_reference(value: str) -> bool:
    """Whether an export link names a local file rather than a web resource."""
    candidate = value.strip()
    if re.match(r"^[A-Za-z]:[\\/]", candidate):
        return True
    scheme = urlparse(candidate).scheme.casefold()
    return not scheme or scheme == "file"


def make_source_record(
    *,
    aliases: Iterable[str] = (),
    title: str = "",
    authors: Iterable[str] = (),
    year: int | None = None,
    doi: str = "",
    url: str = "",
    local_files: Iterable[str] = (),
    provider: str,
    preserve_author_order: bool | Iterable[bool] = False,
) -> SourceRecord:
    clean_title = _clean_text(title)
    clean_authors = normalize_authors(authors, preserve_order=preserve_author_order)
    clean_doi = normalize_doi(doi)
    clean_aliases = _unique(_clean_text(value) for value in aliases)
    clean_files = _unique(_canonical_local_path(value) for value in local_files if value)
    metadata_fingerprint = "\x1f".join((clean_title.casefold(), "\x1e".join(clean_authors), str(year or "")))
    fallback_fingerprint = "\x1f".join(
        (metadata_fingerprint, "\x1e".join(sorted(clean_aliases)), "\x1e".join(sorted(clean_files)))
    )
    fingerprint = metadata_fingerprint if clean_title or clean_authors else fallback_fingerprint
    source_id = f"doi:{clean_doi}" if clean_doi else f"source:{hashlib.sha256(fingerprint.encode()).hexdigest()}"
    return SourceRecord(
        source_id=source_id,
        aliases=clean_aliases,
        title=clean_title,
        authors=clean_authors,
        year=year,
        doi=clean_doi,
        url=(url or "").strip(),
        local_files=clean_files,
        provider=provider,
    )


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _is_windows_absolute(value: str) -> bool:
    return re.match(r"^[A-Za-z]:[\\/]", value) is not None


def _canonical_local_path(value: str) -> str:
    candidate = str(value).strip()
    if os.name != "nt" and _is_windows_absolute(candidate):
        return candidate.replace("\\", "/")
    return str(Path(candidate).expanduser().resolve())


def _clean_text(value: str) -> str:
    value = value if isinstance(value, str) else ""
    return re.sub(r"\s+", " ", value).strip()


from .bibtex import load_bibtex
from .csl_json import load_csl_json
from .ris import load_ris

__all__ = [
    "SourceRecord",
    "is_local_path_reference",
    "load_bibtex",
    "load_csl_json",
    "load_ris",
    "make_source_record",
    "normalize_authors",
    "normalize_doi",
    "resolve_local_path",
]
