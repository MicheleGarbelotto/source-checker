"""Deterministic mapping between citation metadata and bibliography sources."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from source_checker.bibliography import SourceRecord, normalize_doi


@dataclass(frozen=True)
class MappingResult:
    """The public result of a deterministic source-mapping attempt."""

    status: str
    source_ids: tuple[str, ...]
    rule: str
    confidence_note: str

    def __post_init__(self) -> None:
        source_ids = tuple(sorted(set(self.source_ids)))
        if self.status not in {"resolved", "ambiguous", "unresolved"}:
            raise ValueError("invalid mapping status")
        if self.status == "resolved" and len(source_ids) != 1:
            raise ValueError("resolved mappings require exactly one source ID")
        if self.status == "ambiguous" and len(source_ids) < 2:
            raise ValueError("ambiguous mappings require at least two source IDs")
        if self.status == "unresolved" and source_ids:
            raise ValueError("unresolved mappings cannot name source IDs")
        object.__setattr__(self, "source_ids", source_ids)


@dataclass(frozen=True)
class CoalescedSource:
    """One source identity merged from duplicate bibliography records."""

    source: SourceRecord
    conflicts: tuple[str, ...]


def map_source(
    sources: Iterable[SourceRecord],
    *,
    doi: str = "",
    identifiers: Iterable[str] = (),
    title: str = "",
    authors: Iterable[str] = (),
    year: int | None = None,
    filenames: Iterable[str] = (),
) -> MappingResult:
    """Map metadata to a source using the documented, ordered exact rules."""
    records = tuple(sources)
    identifier_values = tuple(value for value in identifiers if isinstance(value, str) and value.strip())
    doi_values = tuple(value for value in (doi, *identifier_values) if _looks_like_doi(value))

    candidates = _matching_doi(records, doi_values)
    if candidates:
        return _result(candidates, "doi", "exact normalized DOI")

    candidates = _matching_identifiers(records, identifier_values)
    if candidates:
        return _result(candidates, "identifier", "exact case-insensitive identifier or alias")

    candidates = _matching_title_author_year(records, title, authors, year)
    if candidates:
        return _result(candidates, "title-author-year", "normalized title, family name, and year")

    candidates = _matching_title(records, title)
    if candidates:
        return _result(candidates, "title", "normalized title match")

    candidates = _matching_filenames(records, filenames)
    if candidates:
        return _result(candidates, "filename", "normalized filename or document metadata match")

    return MappingResult("unresolved", (), "none", "no deterministic match")


def coalesce_source_records(sources: Iterable[SourceRecord]) -> tuple[CoalescedSource, ...]:
    """Coalesce duplicate source IDs deterministically without dropping aliases or files."""
    grouped: dict[str, list[SourceRecord]] = {}
    for source in sources:
        grouped.setdefault(source.source_id, []).append(source)
    return tuple(_coalesce_group(source_id, grouped[source_id]) for source_id in sorted(grouped))


def _coalesce_group(source_id: str, records: list[SourceRecord]) -> CoalescedSource:
    conflicts: list[str] = []
    title = _select_text(records, "title", conflicts)
    authors = _select_authors(records, conflicts)
    year = _select_year(records, conflicts)
    doi = _select_text(records, "doi", conflicts)
    url = _select_text(records, "url", conflicts)
    provider = _select_text(records, "provider", conflicts)
    aliases = _sorted_unique(alias for record in records for alias in record.aliases)
    local_files = _sorted_unique(path for record in records for path in record.local_files)
    if len(local_files) > 1:
        conflicts.append(f"local_files: {' <> '.join(local_files)}")
    return CoalescedSource(
        SourceRecord(
            source_id=source_id,
            aliases=aliases,
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            url=url,
            local_files=local_files,
            provider=provider,
        ),
        tuple(conflicts),
    )


def _select_text(records: list[SourceRecord], field: str, conflicts: list[str]) -> str:
    values = _sorted_unique(str(getattr(record, field)) for record in records if getattr(record, field))
    if len(values) > 1:
        conflicts.append(f"{field}: {' <> '.join(values)}")
    return values[0] if values else ""


def _select_authors(records: list[SourceRecord], conflicts: list[str]) -> tuple[str, ...]:
    values = sorted({record.authors for record in records if record.authors}, key=_author_sort_key)
    if len(values) > 1:
        conflicts.append(f"authors: {' <> '.join(', '.join(value) for value in values)}")
    return values[0] if values else ()


def _select_year(records: list[SourceRecord], conflicts: list[str]) -> int | None:
    values = sorted({record.year for record in records if record.year is not None})
    if len(values) > 1:
        conflicts.append(f"year: {' <> '.join(str(value) for value in values)}")
    return values[0] if values else None


def _sorted_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values), key=lambda value: (value.casefold(), value)))


def _author_sort_key(value: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((part.casefold(), part) for part in value)


def _result(candidates: Iterable[SourceRecord], rule: str, note: str) -> MappingResult:
    source_ids = tuple(sorted({candidate.source_id for candidate in candidates}))
    status = "resolved" if len(source_ids) == 1 else "ambiguous"
    return MappingResult(status, source_ids, rule, note)


def _matching_doi(records: tuple[SourceRecord, ...], values: Iterable[str]) -> tuple[SourceRecord, ...]:
    normalized = {normalize_doi(value) for value in values}
    normalized.discard("")
    return tuple(record for record in records if record.doi and record.doi in normalized)


def _matching_identifiers(
    records: tuple[SourceRecord, ...], identifiers: Iterable[str]
) -> tuple[SourceRecord, ...]:
    requested = {_casefold(value) for value in identifiers if _casefold(value)}
    return tuple(
        record
        for record in records
        if requested & {_casefold(value) for value in (*record.aliases, record.source_id)}
    )


def _matching_title_author_year(
    records: tuple[SourceRecord, ...], title: str, authors: Iterable[str], year: int | None
) -> tuple[SourceRecord, ...]:
    normalized_title = _title_key(title)
    families = set().union(*(_family_name_variants(author) for author in authors))
    if not normalized_title or not families or year is None:
        return ()
    return tuple(
        record
        for record in records
        if _title_key(record.title) == normalized_title
        and record.year == year
        and families & set().union(*(_family_name_variants(author) for author in record.authors))
    )


def _matching_title(records: tuple[SourceRecord, ...], title: str) -> tuple[SourceRecord, ...]:
    normalized_title = _title_key(title)
    if not normalized_title:
        return ()
    return tuple(record for record in records if _title_key(record.title) == normalized_title)


def _matching_filenames(records: tuple[SourceRecord, ...], filenames: Iterable[str]) -> tuple[SourceRecord, ...]:
    requested = {_filename_key(value) for value in filenames}
    requested.discard("")
    if not requested:
        return ()
    return tuple(
        record
        for record in records
        if requested & {_filename_key(path) for path in record.local_files}
    )


def _looks_like_doi(value: str) -> bool:
    return bool(re.match(r"^10\.\d{4,9}/\S+$", normalize_doi(value)))


def _title_key(value: str) -> tuple[str, ...]:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return tuple(re.findall(r"\w+", without_marks.casefold(), flags=re.UNICODE))


def _family_name_variants(value: str) -> set[tuple[str, ...]]:
    """Return exact normalized family-name phrases, including natural-order suffixes."""
    if "," in value:
        family = value.split(",", 1)[0]
        parts = _title_key(family)
        return {parts} if parts else set()
    parts = _title_key(value)
    return {parts[index:] for index in range(len(parts))}


def _filename_key(value: str) -> str:
    return Path(value).name.casefold().strip()


def _casefold(value: str) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""
