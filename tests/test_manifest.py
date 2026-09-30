from __future__ import annotations

import csv
import hashlib

from source_checker.bibliography import make_source_record
from source_checker.manifest import (
    MANIFEST_COLUMNS,
    SourceArtifact,
    build_manifest,
    write_manifest,
)
from source_checker.model import CitationMention, DocumentRecord


def source(**overrides):
    defaults = {
        "aliases": (),
        "title": "",
        "authors": (),
        "year": None,
        "doi": "",
        "local_files": (),
        "provider": "test",
    }
    defaults.update(overrides)
    return make_source_record(**defaults)


def target(path: str, *citations: CitationMention) -> DocumentRecord:
    return DocumentRecord(
        document_id=path,
        role="target",
        path=path,
        media_type="text/markdown",
        sha256="target-hash",
        extraction_method="markup",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=(),
        citations=citations,
    )


def mention(key: str, locator: str) -> CitationMention:
    return CitationMention(
        raw_text=f"[@{key}]",
        citation_keys=(key,),
        locator_type="line",
        locator_value=locator,
        mapping_status="unresolved",
    )


def by_key(rows, key: str):
    return next(row for row in rows if row.bibliography_key == key)


def test_manifest_keeps_unresolved_citations_and_uncited_explicit_sources() -> None:
    cited = source(aliases=("cited",), title="Cited")
    uncited = source(aliases=("uncited",), title="Uncited")

    rows = build_manifest((target("/work/target.qmd", mention("missing", "3")),), (cited, uncited))

    assert len(rows) == 3
    assert by_key(rows, "missing").mapping_status == "unresolved"
    assert {row.source_id for row in rows if row.bibliography_key != "missing"} == {
        cited.source_id,
        uncited.source_id,
    }


def test_ambiguous_mapping_is_a_main_manifest_row_with_ordered_candidates() -> None:
    first = source(aliases=("duplicate",), title="First")
    second = source(aliases=("duplicate",), title="Second")

    rows = build_manifest((target("/work/target.qmd", mention("duplicate", "4")),), (second, first))

    row = by_key(rows, "duplicate")
    assert row.mapping_status == "ambiguous"
    assert row.candidate_source_ids == tuple(sorted((first.source_id, second.source_id)))
    assert row.source_id == ""


def test_manifest_preserves_deterministic_lossless_aliases_targets_and_locators() -> None:
    record = source(aliases=("original", "another|alias"), title="Cited")
    first = target("/work/b.qmd", mention("original", "line:2|x"))
    second = target("/work/a.qmd", mention("original", "line:1"))

    rows = build_manifest((first, second), (record,))
    row = by_key(rows, "original")

    assert row.aliases == ("another|alias", "original")
    assert row.target_files == ("/work/a.qmd", "/work/b.qmd")
    assert row.target_locators == ("line:line:1", "line:line:2|x")


def test_resolved_source_artifact_metadata_is_carried_to_its_manifest_row() -> None:
    record = source(aliases=("key",), title="Cited")
    artifact = SourceArtifact(
        source_id=record.source_id,
        source_path="/corpus/cited.pdf",
        media_type="application/pdf",
        source_sha256=hashlib.sha256(b"cited").hexdigest(),
        extraction_status="extracted",
        text_quality="good",
        cache_path="/cache/cited.jsonl",
    )

    row = by_key(build_manifest((target("/work/t.qmd", mention("key", "8")),), (record,), (artifact,)), "key")

    assert row.source_path == artifact.source_path
    assert row.media_type == artifact.media_type
    assert row.source_sha256 == artifact.source_sha256
    assert row.extraction_status == artifact.extraction_status
    assert row.text_quality == artifact.text_quality
    assert row.cache_path == artifact.cache_path
    assert row.canonical_pdf_path == artifact.source_path
    assert row.pdf_sha256 == artifact.source_sha256


def test_writer_uses_required_columns_then_legacy_compatibility_columns_and_safe_csv(tmp_path) -> None:
    record = source(aliases=("quoted,key",), title="A, title")
    rows = build_manifest((target("/work/t,qmd", mention("quoted,key", "2")),), (record,))
    destination = tmp_path / "nested" / "source-manifest.csv"

    write_manifest(destination, rows)

    required = (
        "source_id", "provider", "bibliography_key", "aliases", "title", "authors", "year", "doi",
        "source_path", "media_type", "source_sha256", "target_files", "target_locators", "mapping_status",
        "mapping_rule", "candidate_source_ids", "extraction_status", "text_quality", "cache_path", "conflicts",
    )
    assert MANIFEST_COLUMNS[: len(required)] == required
    with destination.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        written = next(reader)
    assert written["aliases"] == '["quoted,key"]'
    assert written["target_files"] == '["/work/t,qmd"]'
    assert written["canonical_pdf_path"] == ""
    assert not list(destination.parent.glob("*.tmp"))


def test_manifest_is_deterministic_when_inputs_are_reversed() -> None:
    first = source(aliases=("first",), title="One")
    second = source(aliases=("second",), title="Two")
    first_target = target("/work/z.qmd", mention("second", "2"))
    second_target = target("/work/a.qmd", mention("first", "1"))

    forward = build_manifest((first_target, second_target), (first, second))
    backward = build_manifest((second_target, first_target), (second, first))

    assert forward == backward


def test_duplicate_source_ids_merge_aliases_and_linked_files_regardless_of_order() -> None:
    first = source(
        doi="10.1000/duplicate", aliases=("a",), local_files=("/corpus/a.pdf",), provider="zotero"
    )
    second = source(
        doi="10.1000/duplicate", aliases=("b",), local_files=("/corpus/b.pdf",), provider="mendeley"
    )
    cited = target("/work/t.qmd", mention("b", "1"))

    forward = build_manifest((cited,), (first, second))
    backward = build_manifest((cited,), (second, first))

    assert forward == backward
    assert len(forward) == 1
    assert forward[0].aliases == ("a", "b")
    assert forward[0].source_path == first.local_files[0]
    assert first.local_files[0] in forward[0].conflicts[0]
    assert second.local_files[0] in forward[0].conflicts[0]
    assert "provider:" in " ".join(forward[0].conflicts)


def test_keyless_visible_citation_remains_an_unresolved_manifest_row() -> None:
    visible = CitationMention(
        raw_text="(Smith, 2020)",
        citation_keys=(),
        locator_type="line",
        locator_value="3",
        mapping_status="not-applicable",
    )

    rows = build_manifest((target("/work/target.qmd", visible),), ())

    assert len(rows) == 1
    assert rows[0].bibliography_key.startswith("visible:")
    assert rows[0].mapping_status == "unresolved"
    assert rows[0].target_files == ("/work/target.qmd",)
    assert rows[0].target_locators == ("line:3",)


def test_target_file_and_locator_pairs_are_preserved_not_independently_sorted() -> None:
    source_record = source(aliases=("key",), title="Cited")
    paired = build_manifest(
        (target("/work/a.md", mention("key", "1")), target("/work/b.md", mention("key", "2"))),
        (source_record,),
    )
    swapped = build_manifest(
        (target("/work/a.md", mention("key", "2")), target("/work/b.md", mention("key", "1"))),
        (source_record,),
    )
    repeated = build_manifest(
        (target("/work/a.md", mention("key", "2")), target("/work/a.md", mention("key", "1"))),
        (source_record,),
    )

    assert paired != swapped
    assert paired[0].target_files == ("/work/a.md", "/work/b.md")
    assert paired[0].target_locators == ("line:1", "line:2")
    assert swapped[0].target_locators == ("line:2", "line:1")
    assert repeated[0].target_files == ("/work/a.md", "/work/a.md")
    assert repeated[0].target_locators == ("line:1", "line:2")


def test_manifest_preserves_source_author_order() -> None:
    record = source(aliases=("key",), authors=("Zoe Zulu", "Ada Alpha"), title="Cited")

    row = by_key(build_manifest((target("/work/t.qmd", mention("key", "1")),), (record,)), "key")

    assert row.authors == ("Zoe Zulu", "Ada Alpha")


def test_resolved_mapping_provenance_retains_the_strongest_rule_across_citation_order() -> None:
    record = source(doi="10.1000/strong", aliases=("weak",), title="Cited")
    by_doi = mention("10.1000/strong", "1")
    by_alias = mention("weak", "2")

    forward = build_manifest((target("/work/t.qmd", by_alias, by_doi),), (record,))
    backward = build_manifest((target("/work/t.qmd", by_doi, by_alias),), (record,))

    assert forward == backward
    assert forward[0].mapping_rule == "doi"
    assert forward[0].mapping_status == "resolved"
    assert forward[0].target_files == ("/work/t.qmd", "/work/t.qmd")


def test_compatibility_pdf_status_requires_explicit_available_extraction_state() -> None:
    record = source(aliases=("key",), local_files=("/not-present/cited.pdf",), title="Cited")
    unavailable = by_key(build_manifest((), (record,)), "")
    available_artifact = SourceArtifact(
        source_id=record.source_id,
        source_path=record.local_files[0],
        media_type="application/pdf",
        source_sha256="hash",
        extraction_status="extracted",
        text_quality="good",
    )
    available = by_key(build_manifest((), (record,), (available_artifact,)), "")

    assert unavailable.source_path == record.local_files[0]
    assert unavailable.to_csv_row()["pdf_status"] == "not_run"
    assert available.to_csv_row()["pdf_status"] == "ready"
