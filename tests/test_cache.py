from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from source_checker import cache
from source_checker.cache import cache_source, read_cached_blocks
from source_checker.model import DocumentRecord, TextBlock


def _document(path: Path, digest: str, *, locator: str = "page=4;block=2") -> DocumentRecord:
    return DocumentRecord(
        document_id="source-document",
        role="source",
        path=str(path),
        media_type="application/pdf",
        sha256=digest,
        extraction_method="test-extractor",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=(TextBlock("block-2", "Original\ntext", "original text", "physical-page", locator, ""),),
        citations=(),
    )


def test_cache_writes_required_lossless_jsonl_records_atomically(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"first")
    digest = hashlib.sha256(b"first").hexdigest()

    result = cache_source(
        "doi:10.1000/example",
        source,
        tmp_path / "cache",
        extractor=lambda path, role: _document(path, digest),
    )

    records = [json.loads(line) for line in result.cache_path.read_text(encoding="utf-8").splitlines()]
    assert result.reused is False
    assert result.cache_path.parent == tmp_path / "cache"
    assert records[0] == {
        "block_id": "block-2",
        "block_count": 1,
        "block_index": 1,
        "cache_schema_version": "3",
        "document_hash": digest,
        "document_id": "source-document",
        "extraction_method": "test-extractor",
        "extraction_status": "extracted",
        "locator_type": "physical-page",
        "locator_value": "page=4;block=2",
        "record_type": "block",
        "source_id": "doi:10.1000/example",
        "text_normalized": "original text",
        "text_original": "Original\ntext",
        "text_quality": "good",
    }
    assert not list(result.cache_path.parent.glob("*.tmp"))


def test_cache_reuses_only_a_valid_matching_document_hash(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"same")
    digest = hashlib.sha256(b"same").hexdigest()
    calls = 0

    def extract(path: Path, role: str) -> DocumentRecord:
        nonlocal calls
        calls += 1
        return _document(path, digest)

    first = cache_source("source-id", source, tmp_path / "cache", extractor=extract)
    second = cache_source("source-id", source, tmp_path / "cache", extractor=extract)

    assert calls == 1
    assert first.cache_path == second.cache_path
    assert second.reused is True
    assert read_cached_blocks(second.cache_path)[0]["locator_value"] == "page=4;block=2"


def test_cache_reextracts_and_replaces_when_the_source_hash_changes(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"before")
    calls: list[str] = []

    def extract(path: Path, role: str) -> DocumentRecord:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        calls.append(digest)
        return _document(path, digest, locator=f"page={len(calls)};block=1")

    first = cache_source("source-id", source, tmp_path / "cache", extractor=extract)
    source.write_bytes(b"after")
    second = cache_source("source-id", source, tmp_path / "cache", extractor=extract)

    assert len(calls) == 2
    assert first.cache_path == second.cache_path
    assert read_cached_blocks(second.cache_path)[0]["document_hash"] == calls[-1]
    assert read_cached_blocks(second.cache_path)[0]["locator_value"] == "page=2;block=1"


def test_malformed_or_incomplete_cache_is_not_reused(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"same")
    cache_dir = tmp_path / "cache"
    digest = hashlib.sha256(b"same").hexdigest()
    calls = 0

    def extract(path: Path, role: str) -> DocumentRecord:
        nonlocal calls
        calls += 1
        return _document(path, digest)

    first = cache_source("source-id", source, cache_dir, extractor=extract)
    first.cache_path.write_text('{"document_hash":"' + digest + '"}\n', encoding="utf-8")
    result = cache_source("source-id", source, cache_dir, extractor=extract)

    assert calls == 2
    assert result.reused is False
    assert read_cached_blocks(result.cache_path)[0]["text_original"] == "Original\ntext"


def test_complete_first_jsonl_line_from_a_truncated_multiblock_cache_is_not_reused(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"same")
    digest = hashlib.sha256(b"same").hexdigest()
    calls = 0

    def extract(path: Path, role: str) -> DocumentRecord:
        nonlocal calls
        calls += 1
        first = TextBlock("one", "One", "one", "physical-page", "page=1;block=1", "")
        second = TextBlock("two", "Two", "two", "physical-page", "page=1;block=2", "")
        third = TextBlock("three", "Three", "three", "physical-page", "page=2;block=1", "")
        return replace(_document(path, digest), blocks=(first, second, third))

    first = cache_source("source-id", source, tmp_path / "cache", extractor=extract)
    first.cache_path.write_text(first.cache_path.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
    second = cache_source("source-id", source, tmp_path / "cache", extractor=extract)

    assert calls == 2
    assert second.reused is False
    assert len(read_cached_blocks(second.cache_path)) == 3


def test_content_change_during_extraction_preserves_the_old_cache_and_returns_failure(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"before")
    before = hashlib.sha256(b"before").hexdigest()
    first = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, before))
    old_contents = first.cache_path.read_text(encoding="utf-8")

    def mutate(path: Path, role: str) -> DocumentRecord:
        path.write_bytes(b"after")
        return _document(path, hashlib.sha256(b"after").hexdigest())

    result = cache_source("source-id", source, tmp_path / "cache", extractor=mutate, force=True)

    assert result.extraction_status == "error:ValueError"
    assert result.reused is False
    assert first.cache_path.read_text(encoding="utf-8") == old_contents


def test_hash_permission_failure_is_isolated_before_extraction(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    monkeypatch.setattr(cache, "_sha256_file", lambda path: (_ for _ in ()).throw(PermissionError("denied")))

    result = cache_source("source-id", source, tmp_path / "cache")

    assert result.extraction_status == "error:PermissionError"


def test_cache_rejects_tampered_row_metadata_locators_and_boolean_block_indexes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    digest = hashlib.sha256(b"source").hexdigest()
    calls = 0

    def extract(path: Path, role: str) -> DocumentRecord:
        nonlocal calls
        calls += 1
        return _document(path, digest)

    first = cache_source("source-id", source, tmp_path / "cache", extractor=extract)
    records = [json.loads(line) for line in first.cache_path.read_text(encoding="utf-8").splitlines()]
    records[0].update({"block_index": True, "locator_type": "", "extraction_method": "tampered"})
    first.cache_path.write_text(json.dumps(records[0]) + "\n", encoding="utf-8")

    second = cache_source("source-id", source, tmp_path / "cache", extractor=extract)

    assert calls == 2
    assert second.reused is False
    assert read_cached_blocks(second.cache_path)[0]["extraction_method"] == "test-extractor"


def test_atomic_replace_failure_preserves_existing_cache_and_returns_current_failure(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"before")
    before = hashlib.sha256(b"before").hexdigest()
    first = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, before))
    old_contents = first.cache_path.read_text(encoding="utf-8")
    source.write_bytes(b"after")
    after = hashlib.sha256(b"after").hexdigest()
    monkeypatch.setattr(cache, "_write_jsonl_atomic", lambda *args: (_ for _ in ()).throw(OSError("disk full")))

    result = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, after))

    assert result.extraction_status == "error:OSError"
    assert first.cache_path.read_text(encoding="utf-8") == old_contents


def test_long_source_ids_use_bounded_collision_safe_cache_filenames(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    digest = hashlib.sha256(b"source").hexdigest()
    source_id = "x" * 271

    result = cache_source(source_id, source, tmp_path / "cache", extractor=lambda path, role: _document(path, digest))

    assert result.cache_path.is_file()
    assert len(result.cache_path.stem.split("-")[0]) <= 80
    assert result.cache_path.name.endswith(".jsonl")


def test_long_source_ids_that_share_the_bounded_prefix_do_not_collide(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    digest = hashlib.sha256(b"source").hexdigest()

    first = cache_source("x" * 270 + "a", source, tmp_path / "cache", extractor=lambda path, role: _document(path, digest))
    second = cache_source("x" * 270 + "b", source, tmp_path / "cache", extractor=lambda path, role: _document(path, digest))

    assert first.cache_path != second.cache_path


def test_cache_rejects_conflicting_row_extraction_metadata(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"source")
    digest = hashlib.sha256(b"source").hexdigest()
    calls = 0

    def extract(path: Path, role: str) -> DocumentRecord:
        nonlocal calls
        calls += 1
        one = TextBlock("one", "One", "one", "page", "1", "")
        two = TextBlock("two", "Two", "two", "page", "2", "")
        return replace(_document(path, digest), blocks=(one, two))

    first = cache_source("source-id", source, tmp_path / "cache", extractor=extract)
    records = [json.loads(line) for line in first.cache_path.read_text(encoding="utf-8").splitlines()]
    records[1]["text_quality"] = "tampered"
    first.cache_path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")

    second = cache_source("source-id", source, tmp_path / "cache", extractor=extract)

    assert calls == 2
    assert second.reused is False


def test_schema_two_empty_cache_is_rebuilt_as_current_unusable_metadata(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_bytes(b"")
    digest = hashlib.sha256(b"").hexdigest()
    cache_path = cache.cache_path_for(tmp_path / "cache", "source-id", source)
    cache_path.parent.mkdir()
    cache_path.write_text(
        json.dumps(
            {
                "block_id": "document-empty", "block_count": 1, "block_index": 1,
                "cache_schema_version": "2", "document_hash": digest, "document_id": "source",
                "source_id": "source-id", "text_original": "", "text_normalized": "",
                "locator_type": "document", "locator_value": "whole", "extraction_method": "test",
                "extraction_status": "extracted", "text_quality": "good",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    document = replace(_document(source, digest), blocks=())

    result = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: document)

    current = read_cached_blocks(result.cache_path)[0]
    assert result.reused is False
    assert (result.extraction_status, result.text_quality) == ("unusable", "empty")
    assert (current["cache_schema_version"], current["record_type"]) == ("3", "document-metadata")


def test_empty_specific_extraction_failure_is_not_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_bytes(b"")
    digest = hashlib.sha256(b"").hexdigest()
    document = replace(_document(source, digest), blocks=(), extraction_status="needs_ocr", text_quality="sparse")

    result = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: document)

    assert (result.extraction_status, result.text_quality) == ("needs_ocr", "sparse")


def test_os_replace_failure_preserves_old_cache_and_removes_the_temporary_file(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.txt"
    source.write_bytes(b"before")
    first = cache_source(
        "source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, hashlib.sha256(b"before").hexdigest())
    )
    old_contents = first.cache_path.read_text(encoding="utf-8")
    source.write_bytes(b"after")
    monkeypatch.setattr(cache.os, "replace", lambda source, destination: (_ for _ in ()).throw(OSError("locked")))

    result = cache_source(
        "source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, hashlib.sha256(b"after").hexdigest())
    )

    assert result.extraction_status == "error:OSError"
    assert first.cache_path.read_text(encoding="utf-8") == old_contents
    assert not list(first.cache_path.parent.glob("*.tmp"))
