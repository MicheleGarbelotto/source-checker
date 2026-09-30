"""Format-neutral, deterministic source manifests."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from source_checker.bibliography import SourceRecord
from source_checker.mapping import MappingResult, coalesce_source_records, map_source
from source_checker.model import DocumentRecord

REQUIRED_COLUMNS = (
    "source_id",
    "provider",
    "bibliography_key",
    "aliases",
    "title",
    "authors",
    "year",
    "doi",
    "source_path",
    "media_type",
    "source_sha256",
    "target_files",
    "target_locators",
    "mapping_status",
    "mapping_rule",
    "candidate_source_ids",
    "extraction_status",
    "text_quality",
    "cache_path",
    "conflicts",
)

LEGACY_COLUMNS = (
    "zotero_item_key",
    "zotero_attachment_key",
    "canonical_pdf_path",
    "section",
    "source_manifests",
    "pdf_status",
    "text_cache_path",
    "validation_status",
    "pdf_sha256",
    "zotero_status",
    "manifest_status",
)

MANIFEST_COLUMNS = (*REQUIRED_COLUMNS, *LEGACY_COLUMNS)


@dataclass(frozen=True)
class SourceArtifact:
    """Resolved local-source metadata that belongs in a manifest row."""

    source_id: str
    source_path: str
    media_type: str
    source_sha256: str
    extraction_status: str
    text_quality: str
    cache_path: str = ""
    conflicts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "conflicts", tuple(self.conflicts))


@dataclass(frozen=True)
class ManifestRow:
    """One serializable source-manifest row."""

    source_id: str = ""
    provider: str = ""
    bibliography_key: str = ""
    aliases: tuple[str, ...] = ()
    title: str = ""
    authors: tuple[str, ...] = ()
    year: int | None = None
    doi: str = ""
    source_path: str = ""
    media_type: str = ""
    source_sha256: str = ""
    target_files: tuple[str, ...] = ()
    target_locators: tuple[str, ...] = ()
    mapping_status: str = "unresolved"
    mapping_rule: str = "none"
    candidate_source_ids: tuple[str, ...] = ()
    extraction_status: str = "not_run"
    text_quality: str = "unknown"
    cache_path: str = ""
    conflicts: tuple[str, ...] = ()

    @property
    def canonical_pdf_path(self) -> str:
        return self.source_path

    @property
    def pdf_sha256(self) -> str:
        return self.source_sha256

    def to_csv_row(self) -> dict[str, str]:
        values = {
            "source_id": self.source_id,
            "provider": self.provider,
            "bibliography_key": self.bibliography_key,
            "aliases": _json(self.aliases),
            "title": self.title,
            "authors": _json(self.authors),
            "year": "" if self.year is None else str(self.year),
            "doi": self.doi,
            "source_path": self.source_path,
            "media_type": self.media_type,
            "source_sha256": self.source_sha256,
            "target_files": _json(self.target_files),
            "target_locators": _json(self.target_locators),
            "mapping_status": self.mapping_status,
            "mapping_rule": self.mapping_rule,
            "candidate_source_ids": _json(self.candidate_source_ids),
            "extraction_status": self.extraction_status,
            "text_quality": self.text_quality,
            "cache_path": self.cache_path,
            "conflicts": _json(self.conflicts),
            "zotero_item_key": "",
            "zotero_attachment_key": "",
            "canonical_pdf_path": self.canonical_pdf_path,
            "section": " | ".join(self.target_locators),
            "source_manifests": "",
            "pdf_status": _compatibility_pdf_status(self.extraction_status),
            "text_cache_path": self.cache_path,
            "validation_status": "not_validated",
            "pdf_sha256": self.pdf_sha256,
            "zotero_status": "disabled",
            "manifest_status": self.mapping_status,
        }
        return {column: values[column] for column in MANIFEST_COLUMNS}


@dataclass
class _CitationProvenance:
    keys: set[str]
    pairs: set[tuple[str, str]]
    has_keyless_visible_citation: bool = False
    result: MappingResult | None = None


def build_manifest(
    target_documents: Iterable[DocumentRecord],
    sources: Iterable[SourceRecord],
    source_artifacts: Iterable[SourceArtifact] = (),
) -> tuple[ManifestRow, ...]:
    """Return manifest rows for citations and every explicit corpus source."""
    source_groups = coalesce_source_records(sources)
    ordered_sources = tuple(group.source for group in source_groups)
    source_conflicts = {group.source.source_id: group.conflicts for group in source_groups}
    artifact_by_id = _artifact_index(source_artifacts)
    citations = _citation_index(target_documents)
    resolved: dict[str, _CitationProvenance] = {}
    incomplete: list[ManifestRow] = []

    for key, provenance in citations.items():
        result = (
            MappingResult(
                "unresolved",
                (),
                "visible-citation",
                "visible citation has no explicit identifier",
            )
            if provenance.has_keyless_visible_citation
            else map_source(ordered_sources, identifiers=(key,))
        )
        if result.status == "resolved":
            source_id = result.source_ids[0]
            data = resolved.setdefault(source_id, _provenance())
            data.keys.add(key)
            data.pairs.update(provenance.pairs)
            if data.result is None or _mapping_priority(result) < _mapping_priority(data.result):
                data.result = result
        else:
            incomplete.append(_incomplete_row(key, provenance, result))

    rows = [
        _source_row(
            source,
            resolved.get(source.source_id),
            artifact_by_id.get(source.source_id),
            source_conflicts[source.source_id],
        )
        for source in ordered_sources
    ]
    rows.extend(incomplete)
    return tuple(sorted(rows, key=_row_sort_key))


def write_manifest(path: Path, rows: Iterable[ManifestRow]) -> None:
    """Write CSV safely using a same-directory temporary file and replacement."""
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            delete=False,
            dir=destination.parent,
            suffix=".tmp",
        ) as handle:
            temporary_name = handle.name
            writer = csv.DictWriter[str](handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow(row.to_csv_row())
        os.replace(temporary_name, destination)
    except Exception:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def _citation_index(target_documents: Iterable[DocumentRecord]) -> dict[str, _CitationProvenance]:
    citations: dict[str, _CitationProvenance] = {}
    for document in sorted(target_documents, key=lambda item: _sort_value(item.path)):
        if document.role != "target":
            raise ValueError("target_documents must contain target DocumentRecord values")
        for mention in document.citations:
            locator = f"{mention.locator_type}:{mention.locator_value}"
            keys = mention.citation_keys or (_visible_citation_key(mention.raw_text),)
            for key in keys:
                provenance = citations.setdefault(key, _provenance())
                provenance.pairs.add((document.path, locator))
                provenance.has_keyless_visible_citation = (
                    provenance.has_keyless_visible_citation or not mention.citation_keys
                )
    return citations


def _artifact_index(source_artifacts: Iterable[SourceArtifact]) -> dict[str, SourceArtifact]:
    indexed: dict[str, SourceArtifact] = {}
    for artifact in sorted(source_artifacts, key=lambda item: _sort_value(item.source_id)):
        previous = indexed.get(artifact.source_id)
        if previous is not None and previous != artifact:
            raise ValueError(f"multiple source artifacts for {artifact.source_id}")
        indexed[artifact.source_id] = artifact
    return indexed


def _provenance() -> _CitationProvenance:
    return _CitationProvenance(keys=set(), pairs=set())


def _source_row(
    source: SourceRecord,
    provenance: _CitationProvenance | None,
    artifact: SourceArtifact | None,
    source_conflicts: tuple[str, ...],
) -> ManifestRow:
    keys = _sorted_values(provenance.keys) if provenance else ()
    files, locators = _paired_columns(provenance.pairs) if provenance else ((), ())
    result = provenance.result if provenance else None
    aliases = _sorted_values((*source.aliases, *keys))
    status = result.status if isinstance(result, MappingResult) else "not-applicable"
    rule = result.rule if isinstance(result, MappingResult) else "explicit-corpus"
    artifact = artifact or SourceArtifact(
        source.source_id,
        source.local_files[0] if source.local_files else "",
        "",
        "",
        "not_run",
        "unknown",
    )
    return ManifestRow(
        source_id=source.source_id,
        provider=source.provider,
        bibliography_key=keys[0] if keys else "",
        aliases=aliases,
        title=source.title,
        authors=source.authors,
        year=source.year,
        doi=source.doi,
        source_path=artifact.source_path,
        media_type=artifact.media_type,
        source_sha256=artifact.source_sha256,
        target_files=files,
        target_locators=locators,
        mapping_status=status,
        mapping_rule=rule,
        candidate_source_ids=(source.source_id,) if status == "resolved" else (),
        extraction_status=artifact.extraction_status,
        text_quality=artifact.text_quality,
        cache_path=artifact.cache_path,
        conflicts=_sorted_values((*source_conflicts, *artifact.conflicts)),
    )


def _incomplete_row(
    key: str, provenance: _CitationProvenance, result: MappingResult
) -> ManifestRow:
    return ManifestRow(
        bibliography_key=key,
        aliases=(key,),
        target_files=_paired_columns(provenance.pairs)[0],
        target_locators=_paired_columns(provenance.pairs)[1],
        mapping_status=result.status,
        mapping_rule=result.rule,
        candidate_source_ids=result.source_ids,
        conflicts=(result.confidence_note,),
    )


def _row_sort_key(row: ManifestRow) -> tuple[tuple[str, str], tuple[str, str], tuple[str, str]]:
    return (_sort_value(row.bibliography_key), _sort_value(row.source_id), _sort_value(row.mapping_status))


def _sorted_values(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values), key=_sort_value))


def _paired_columns(pairs: Iterable[tuple[str, str]]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered = tuple(sorted(set(pairs), key=lambda pair: (_sort_value(pair[0]), _sort_value(pair[1]))))
    return tuple(pair[0] for pair in ordered), tuple(pair[1] for pair in ordered)


def _mapping_priority(result: MappingResult) -> int:
    return {
        "doi": 0,
        "identifier": 1,
        "title-author-year": 2,
        "title": 3,
        "filename": 4,
    }.get(result.rule, 5)


def _compatibility_pdf_status(extraction_status: str) -> str:
    if extraction_status in {"extracted", "cached"}:
        return "ready"
    if extraction_status in {"missing", "unusable", "unknown", "not_run"}:
        return extraction_status
    return "unusable" if extraction_status.startswith("error:") else "unknown"


def _visible_citation_key(raw_text: str) -> str:
    digest = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:16]
    return f"visible:{digest}"


def _sort_value(value: str) -> tuple[str, str]:
    return value.casefold(), value


def _json(values: Iterable[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False, separators=(",", ":"))
