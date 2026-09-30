"""Incremental, lossless JSONL caches for extracted source documents."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from source_checker.extractors import extract_document
from source_checker.model import DocumentRecord

_REQUIRED_FIELDS = frozenset(
    {
        "block_id",
        "block_count",
        "block_index",
        "cache_schema_version",
        "document_hash",
        "document_id",
        "source_id",
        "text_original",
        "text_normalized",
        "locator_type",
        "locator_value",
        "record_type",
        "extraction_method",
        "extraction_status",
        "text_quality",
    }
)
_TEXT_FIELDS = _REQUIRED_FIELDS - {"document_hash", "block_count", "block_index"}
_CACHE_SCHEMA_VERSION = "3"


@dataclass(frozen=True)
class CacheResult:
    """The cache state for one source document."""

    source_id: str
    source_path: str
    document_hash: str
    cache_path: Path
    extraction_status: str
    text_quality: str
    reused: bool
    error: str = ""


def cache_path_for(cache_dir: Path | str, source_id: str, document_path: Path | str) -> Path:
    """Return a stable cache location for the source identity and local document."""
    directory = Path(cache_dir).expanduser().resolve()
    document = str(Path(document_path).expanduser().resolve())
    safe_source = (re.sub(r"[^A-Za-z0-9_.-]+", "_", source_id).strip("._") or "source")[:80]
    suffix = hashlib.sha256(f"{source_id}\x1f{document}".encode()).hexdigest()[:16]
    return directory / f"{safe_source}-{suffix}.jsonl"


def cache_source(
    source_id: str,
    source_path: Path | str,
    cache_dir: Path | str,
    *,
    extractor: Callable[[Path, str], DocumentRecord] = extract_document,
    force: bool = False,
) -> CacheResult:
    """Reuse a valid cache or extract one source without exposing partial writes."""
    raw_path = Path(source_path).expanduser()
    destination = Path(cache_dir).expanduser() / "unavailable.jsonl"
    document_hash = ""
    try:
        path = raw_path.resolve()
        destination = cache_path_for(cache_dir, source_id, path)
        if not path.is_file():
            return CacheResult(source_id, str(path), "", destination, "missing", "unknown", False)
        document_hash = _sha256_file(path)
        cached = _valid_cache(destination, source_id, document_hash)
        if cached is not None and not force:
            first = cached[0]
            return CacheResult(
                source_id,
                str(path),
                document_hash,
                destination,
                str(first["extraction_status"]),
                str(first["text_quality"]),
                True,
            )
        document = extractor(path, "source")
        if document.role != "source":
            raise ValueError("source cache extractor must return a source DocumentRecord")
        if document.sha256 != document_hash or _sha256_file(path) != document_hash:
            raise ValueError("source content changed during extraction")
        if (
            not document.blocks
            and document.extraction_status == "extracted"
            and document.text_quality == "good"
        ):
            document = replace(document, extraction_status="unusable", text_quality="empty")
        records = _document_records(document, source_id, document_hash)
        _write_jsonl_atomic(destination, records)
        return CacheResult(
            source_id,
            str(raw_path),
            document_hash,
            destination,
            document.extraction_status,
            document.text_quality,
            False,
        )
    except Exception as error:  # noqa: BLE001 - source failures are intentionally isolated
        return CacheResult(
            source_id,
            str(raw_path),
            document_hash,
            destination,
            f"error:{type(error).__name__}",
            "unknown",
            False,
            str(error),
        )


def read_cached_blocks(path: Path | str) -> tuple[dict[str, Any], ...]:
    """Read a valid cache; reject malformed or schema-incomplete JSONL."""
    records = _read_jsonl(Path(path))
    if records is None or not _has_complete_schema(records):
        raise ValueError(f"Invalid source cache: {path}")
    return tuple(records)


def _document_records(
    document: DocumentRecord, source_id: str, document_hash: str
) -> list[dict[str, Any]]:
    common = {
        "block_count": len(document.blocks) or 1,
        "cache_schema_version": _CACHE_SCHEMA_VERSION,
        "document_hash": document_hash,
        "document_id": document.document_id,
        "source_id": source_id,
        "extraction_method": document.extraction_method,
        "extraction_status": document.extraction_status,
        "text_quality": document.text_quality,
        "record_type": "block" if document.blocks else "document-metadata",
    }
    records = [
        {
            **common,
            "block_index": index,
            "block_id": block.block_id,
            "text_original": block.text_original,
            "text_normalized": block.text_normalized,
            "locator_type": block.locator_type,
            "locator_value": block.locator_value,
        }
        for index, block in enumerate(document.blocks, start=1)
    ]
    if not records:
        records.append(
            {
                **common,
                "block_id": "document-empty",
                "block_index": 1,
                "text_original": "",
                "text_normalized": "",
                "locator_type": "document",
                "locator_value": "whole",
            }
        )
    return records


def _valid_cache(path: Path, source_id: str, document_hash: str) -> list[dict[str, Any]] | None:
    records = _read_jsonl(path)
    if records is None or not _has_complete_schema(records):
        return None
    if any(record["source_id"] != source_id or record["document_hash"] != document_hash for record in records):
        return None
    return records


def _read_jsonl(path: Path) -> list[dict[str, Any]] | None:
    if not path.is_file():
        return None
    try:
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    return None
                records.append(value)
        return records
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _has_required_schema(record: Mapping[str, Any]) -> bool:
    return (
        _REQUIRED_FIELDS <= record.keys()
        and all(isinstance(record[field], str) for field in _TEXT_FIELDS | {"document_hash"})
        and isinstance(record["block_index"], int)
        and isinstance(record["block_count"], int)
        and not isinstance(record["block_index"], bool)
        and not isinstance(record["block_count"], bool)
        and bool(record["locator_type"].strip())
        and bool(record["locator_value"].strip())
    )


def _has_complete_schema(records: Sequence[Mapping[str, Any]]) -> bool:
    if not records or not all(_has_required_schema(record) for record in records):
        return False
    first = records[0]
    if first["cache_schema_version"] != _CACHE_SCHEMA_VERSION:
        return False
    count = first["block_count"]
    identity = (first["source_id"], first["document_hash"], first["document_id"])
    extraction = (
        first["extraction_method"],
        first["extraction_status"],
        first["text_quality"],
    )
    return (
        count == len(records)
        and [record["block_index"] for record in records] == list(range(1, count + 1))
        and len({record["block_id"] for record in records}) == count
        and all(
            record["cache_schema_version"] == _CACHE_SCHEMA_VERSION
            and record["block_count"] == count
            and (record["source_id"], record["document_hash"], record["document_id"]) == identity
            and (
                record["extraction_method"],
                record["extraction_status"],
                record["text_quality"],
            )
            == extraction
            for record in records
        )
    )


def _write_jsonl_atomic(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent, suffix=".tmp"
        ) as handle:
            temporary_name = handle.name
            for record in records:
                handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temporary_name, path)
    except Exception:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
