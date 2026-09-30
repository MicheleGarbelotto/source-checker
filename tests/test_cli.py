from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pypdf import PdfWriter

from source_checker import cli
from source_checker.bibliography import make_source_record
from source_checker.cache import CacheResult, cache_source
from source_checker.manifest import MANIFEST_COLUMNS, ManifestRow
from source_checker.model import CitationMention, DocumentRecord, TextBlock
from source_checker.resolvers.zotero import ZoteroResolution


def _document(path: Path, role: str) -> DocumentRecord:
    return DocumentRecord(
        document_id=f"{role}:{path.name}",
        role=role,
        path=str(path),
        media_type="text/plain",
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        extraction_method="test",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=(TextBlock("1", "Text", "text", "line", "1", ""),),
        citations=(),
    )


def test_manifest_cli_keeps_successful_outputs_when_one_source_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target.md"
    good = tmp_path / "good.txt"
    bad = tmp_path / "bad.txt"
    target.write_text("Target", encoding="utf-8")
    good.write_text("Good", encoding="utf-8")
    bad.write_text("Bad", encoding="utf-8")

    def extract(path: Path | str, role: str) -> DocumentRecord:
        path = Path(path)
        if path == bad:
            raise ValueError("broken")
        return _document(path, role)

    monkeypatch.setattr(cli, "extract_document", extract)
    output = tmp_path / "source-manifest.csv"
    exit_code = cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--source",
            str(good),
            "--source",
            str(bad),
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )

    summary = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output.is_file()
    assert summary == {
        "ambiguous": 0,
        "analyzed": 1,
        "coverage_percent": 50.0,
        "expected": 2,
        "extracted": 1,
        "missing": 0,
        "resolved": 2,
        "unusable": 1,
    }
    assert len(list((tmp_path / "cache").glob("*.jsonl"))) == 1
    assert not list(tmp_path.glob("*unresolved*"))


def test_fail_on_missing_is_opt_in_and_returns_two(tmp_path: Path, capsys) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text [@missing]", encoding="utf-8")
    output = tmp_path / "source-manifest.csv"

    normal = cli.main(
        ["manifest", "--target", str(target), "--output", str(output), "--cache-dir", str(tmp_path / "cache")]
    )
    capsys.readouterr()
    strict = cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--fail-on-missing",
        ]
    )
    summary = json.loads(capsys.readouterr().out)

    assert normal == 0
    assert strict == 2
    assert summary["missing"] == 1
    assert summary["coverage_percent"] == 0.0


def test_zero_expected_sources_have_unavailable_coverage_and_fail_strict_mode(
    tmp_path: Path, capsys
) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text without citations", encoding="utf-8")
    output = tmp_path / "source-manifest.csv"

    exit_code = cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--fail-on-missing",
        ]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert summary["expected"] == 0
    assert summary["coverage_percent"] is None


def test_summary_counts_overlapping_ambiguous_and_missing_states_without_going_negative() -> None:
    summary = cli._summary(
        (
            ManifestRow(
                bibliography_key="ambiguous-missing",
                mapping_status="ambiguous",
                extraction_status="missing",
            ),
        ),
        {},
    )

    assert summary["expected"] == 1
    assert summary["missing"] == 1
    assert summary["ambiguous"] == 1
    assert summary["resolved"] == 0
    assert 0 <= summary["resolved"] <= summary["expected"]


def test_cli_does_not_contact_zotero_without_the_live_flag(tmp_path: Path, monkeypatch, capsys) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))

    assert cli.main(
        ["manifest", "--target", str(target), "--output", str(tmp_path / "out.csv"), "--cache-dir", str(tmp_path / "cache")]
    ) == 0
    json.loads(capsys.readouterr().out)


@pytest.mark.parametrize(
    ("extraction_status", "text_quality"),
    [("empty", "empty"), ("needs_ocr", "sparse"), ("needs_review", "degraded")],
)
def test_unusable_target_is_a_diagnostic_non_success_without_false_full_coverage(
    tmp_path: Path,
    monkeypatch,
    capsys,
    extraction_status: str,
    text_quality: str,
) -> None:
    target = tmp_path / "target.txt"
    target.write_text("placeholder", encoding="utf-8")
    unusable = replace(
        _document(target, "target"),
        extraction_status=extraction_status,
        text_quality=text_quality,
        blocks=(),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: unusable)

    exit_code = cli.main(
        ["manifest", "--target", str(target), "--output", str(tmp_path / "out.csv")]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert summary["target_unusable"] == 1
    assert summary["coverage_percent"] != 100.0
    assert len(summary["target_diagnostics"]) == 1
    diagnostic = summary["target_diagnostics"][0]
    assert Path(diagnostic["path"]).resolve() == target.resolve()
    assert diagnostic["block_count"] == 0
    assert diagnostic["extraction_method"] == "test"
    assert diagnostic["extraction_status"] == extraction_status
    assert diagnostic["text_quality"] == text_quality


def test_target_extraction_error_is_reported_as_a_diagnostic_non_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "locked.txt"
    target.write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(
        cli,
        "extract_document",
        lambda path, role: (_ for _ in ()).throw(PermissionError("denied")),
    )

    exit_code = cli.main(
        ["manifest", "--target", str(target), "--output", str(tmp_path / "out.csv")]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert summary["target_unusable"] == 1
    assert summary["coverage_percent"] != 100.0
    diagnostic = summary["target_diagnostics"][0]
    assert Path(diagnostic["path"]).resolve() == target.resolve()
    assert diagnostic["extraction_status"] == "error:PermissionError"
    assert "denied" in diagnostic["error"]


def test_unreadable_target_preserves_analyzed_source_coverage(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target.txt"
    source = tmp_path / "source.txt"
    target.write_text("target", encoding="utf-8")
    source.write_text("source", encoding="utf-8")

    def extract(path: Path | str, role: str) -> DocumentRecord:
        path = Path(path)
        if path == target:
            raise PermissionError("denied")
        return _document(path, role)

    monkeypatch.setattr(cli, "extract_document", extract)

    exit_code = cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--source",
            str(source),
            "--output",
            str(tmp_path / "out.csv"),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert summary["expected"] == 1
    assert summary["resolved"] == 1
    assert summary["analyzed"] == 1
    assert summary["coverage_percent"] == 100.0
    assert summary["target_unusable"] == 1


@pytest.mark.parametrize("target_name", ["empty-target-directory", "unsupported-only-directory"])
def test_target_directory_without_supported_files_is_a_diagnostic_non_success(
    monkeypatch, capsys, target_name: str
) -> None:
    target_directory = Path(target_name)
    monkeypatch.setattr(cli, "_expand_paths", lambda paths, suffixes: [])
    monkeypatch.setattr(cli, "write_manifest", lambda path, rows: None)

    exit_code = cli.main(
        [
            "manifest",
            "--target",
            str(target_directory),
        ]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code != 0
    assert summary["coverage_percent"] is None
    assert summary["target_unusable"] == 1
    assert len(summary["target_diagnostics"]) == 1
    diagnostic = summary["target_diagnostics"][0]
    assert Path(diagnostic["path"]).resolve() == target_directory.resolve()
    assert diagnostic["extraction_status"] == "error:NoSupportedTargets"
    assert "no supported target files" in diagnostic["error"].lower()


def test_source_cache_tries_attachments_deterministically_until_one_is_usable(
    tmp_path: Path,
) -> None:
    unusable = tmp_path / "a-empty.txt"
    usable = tmp_path / "b-usable.txt"
    unusable.write_text("", encoding="utf-8")
    usable.write_text("Usable source text", encoding="utf-8")
    source = make_source_record(
        title="One source",
        local_files=(str(usable), str(unusable)),
        provider="test",
    )

    artifacts, results = cli._cache_source_documents([source], tmp_path / "cache", False)

    assert len(artifacts) == 1
    assert artifacts[0].source_path == str(usable.resolve())
    assert artifacts[0].extraction_status == "extracted"
    assert results[source.source_id].source_path == str(usable.resolve())
    conflicts = "\n".join(artifacts[0].conflicts)
    assert str(unusable.resolve()) in conflicts
    assert "unusable" in conflicts


def test_fail_on_missing_treats_ocr_required_sources_as_unusable(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "image-only.txt"
    source.write_text("Text", encoding="utf-8")

    def extract(path: Path | str, role: str) -> DocumentRecord:
        document = _document(Path(path), role)
        return replace(document, extraction_status="needs_ocr", text_quality="sparse")

    monkeypatch.setattr(cli, "extract_document", extract)

    exit_code = cli.main(
        ["cache", "--source", str(source), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]
    )
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert summary["unusable"] == 1


def test_cache_cli_accepts_compatible_csv_manifest_and_prints_zero_safe_summary(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Text", encoding="utf-8")
    manifest = tmp_path / "input.csv"
    manifest.write_text("source_id,source_path,aliases,title\nlocal-1," + str(source) + ",[],Source\n", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(manifest), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["expected"] == summary["resolved"] == summary["extracted"] == summary["analyzed"] == 1
    assert summary["coverage_percent"] == 100.0


def test_explicit_sources_with_the_same_filename_remain_distinct_documents(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    first = tmp_path / "one" / "paper.txt"
    second = tmp_path / "two" / "paper.txt"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("First", encoding="utf-8")
    second.write_text("Second", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--source", str(first), "--source", str(second), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == summary["extracted"] == summary["analyzed"] == 2
    assert len(list((tmp_path / "cache").glob("*.jsonl"))) == 2


def test_cache_cli_isolates_a_missing_explicit_source_before_hashing(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    good = tmp_path / "good.md"
    missing = tmp_path / "missing.txt"
    good.write_text("Good", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--source", str(good), "--source", str(missing), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == 2
    assert summary["missing"] == 1
    assert summary["extracted"] == summary["analyzed"] == 1


def test_stale_cache_for_a_deleted_manifest_source_is_not_counted_as_current_analysis(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Text", encoding="utf-8")
    manifest = tmp_path / "input.csv"
    manifest.write_text("source_id,source_path,aliases,title\nlocal-1," + str(source) + ",[],Source\n", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))
    assert cli.main(["cache", "--manifest", str(manifest), "--cache-dir", str(tmp_path / "cache")]) == 0
    capsys.readouterr()
    source.unlink()

    assert cli.main(["cache", "--manifest", str(manifest), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["missing"] == 1
    assert summary["extracted"] == summary["analyzed"] == 0
    assert summary["coverage_percent"] == 0.0


def test_cli_does_not_count_an_old_cache_after_the_current_atomic_write_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Text", encoding="utf-8")
    initial = cache_source("source-id", source, tmp_path / "cache", extractor=lambda path, role: _document(path, role))
    failed = CacheResult("source-id", str(source), initial.document_hash, initial.cache_path, "error:OSError", "unknown", False)
    monkeypatch.setattr(cli, "cache_source", lambda *args, **kwargs: failed)

    assert cli.main(["cache", "--manifest", str(_write_manifest(tmp_path, source, "source-id")), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert initial.cache_path.is_file()
    assert summary["unusable"] == 1
    assert summary["extracted"] == summary["analyzed"] == 0


def test_zotero_ambiguity_is_preserved_in_manifest_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    citation = replace(
        _document(target, "target"),
        citations=(
            CitationMention("[@ambiguous]", ("ambiguous",), "line", "1", "unresolved"),
        ),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: citation)
    monkeypatch.setattr(cli, "_check_zotero_available", lambda: None)
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: ZoteroResolution("ambiguous", candidates=("ONE", "TWO")))
    output = tmp_path / "out.csv"

    assert cli.main(["manifest", "--target", str(target), "--zotero-live", "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["ambiguous"] == 1
    assert summary["missing"] == 0
    assert "ONE" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "outcome",
    [
        ZoteroResolution("unavailable"),
        ZoteroResolution("not_found"),
        ZoteroResolution("error:OSError"),
    ],
)
def test_zotero_non_enriched_states_remain_diagnostics_on_the_unresolved_row(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outcome: ZoteroResolution,
) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    citation = replace(
        _document(target, "target"),
        citations=(CitationMention("[@unresolved]", ("unresolved",), "line", "1", "unresolved"),),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: citation)
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: outcome)
    output = tmp_path / "out.csv"

    assert cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--zotero-live",
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    ) == 0
    json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert len(rows) == 1
    assert rows[0]["source_id"] == ""
    assert rows[0]["mapping_status"] == "unresolved"
    assert rows[0]["mapping_rule"] == "zotero-live"
    assert outcome.status in rows[0]["conflicts"]


@pytest.mark.parametrize(
    "outcome",
    [
        ZoteroResolution("unavailable"),
        ZoteroResolution("not_found"),
        ZoteroResolution("error:OSError"),
    ],
)
def test_zotero_live_failure_preserves_stronger_ambiguous_mapping(
    outcome: ZoteroResolution,
) -> None:
    row = ManifestRow(
        bibliography_key="ambiguous",
        mapping_status="ambiguous",
        mapping_rule="explicit-corpus",
        candidate_source_ids=("candidate-one", "candidate-two"),
        conflicts=("existing ambiguity",),
    )

    updated = cli._apply_zotero_resolutions((row,), {"ambiguous": outcome})[0]

    assert updated.mapping_status == "ambiguous"
    assert updated.mapping_rule == "explicit-corpus"
    assert updated.candidate_source_ids == ("candidate-one", "candidate-two")
    assert updated.conflicts == (
        "existing ambiguity",
        "Zotero live resolution: " + outcome.status,
    )


def test_zotero_live_ambiguity_preserves_stronger_explicit_ambiguity() -> None:
    row = ManifestRow(
        bibliography_key="ambiguous",
        mapping_status="ambiguous",
        mapping_rule="explicit-corpus",
        candidate_source_ids=("candidate-a", "candidate-b"),
        conflicts=("existing ambiguity",),
    )

    updated = cli._apply_zotero_resolutions(
        (row,),
        {
            "ambiguous": ZoteroResolution(
                "ambiguous", candidates=("zotero-z1", "zotero-z2")
            )
        },
    )[0]

    assert updated.mapping_status == "ambiguous"
    assert updated.mapping_rule == "explicit-corpus"
    assert updated.candidate_source_ids == ("candidate-a", "candidate-b")
    assert updated.conflicts == (
        "existing ambiguity",
        "Zotero live resolution: ambiguous; candidates: zotero-z1 | zotero-z2",
    )


def test_zotero_live_ambiguity_refreshes_previous_live_candidates() -> None:
    row = ManifestRow(
        bibliography_key="ambiguous",
        mapping_status="ambiguous",
        mapping_rule="zotero-live",
        candidate_source_ids=("zotero-z1", "zotero-z2"),
        conflicts=(
            "existing conflict",
            "Zotero live resolution: ambiguous; candidates: zotero-z1 | zotero-z2",
        ),
    )

    updated = cli._apply_zotero_resolutions(
        (row,),
        {
            "ambiguous": ZoteroResolution(
                "ambiguous", candidates=("zotero-z3", "zotero-z4")
            )
        },
    )[0]

    assert updated.mapping_status == "ambiguous"
    assert updated.mapping_rule == "zotero-live"
    assert updated.candidate_source_ids == ("zotero-z3", "zotero-z4")
    assert updated.conflicts == (
        "existing conflict",
        "Zotero live resolution: ambiguous; candidates: zotero-z3 | zotero-z4",
    )


@pytest.mark.parametrize("status", ["not_found", "unavailable", "error:TimeoutError"])
def test_zotero_live_ambiguity_refreshes_to_current_failure(status: str) -> None:
    row = ManifestRow(
        bibliography_key="ambiguous",
        mapping_status="ambiguous",
        mapping_rule="zotero-live",
        candidate_source_ids=("zotero-z1", "zotero-z2"),
        conflicts=(
            "existing conflict",
            "Zotero live resolution: ambiguous; candidates: zotero-z1 | zotero-z2",
        ),
    )

    updated = cli._apply_zotero_resolutions(
        (row,), {"ambiguous": ZoteroResolution(status)}
    )[0]

    assert updated.mapping_status == "unresolved"
    assert updated.mapping_rule == "zotero-live"
    assert updated.candidate_source_ids == ()
    assert updated.conflicts == (
        "existing conflict",
        f"Zotero live resolution: {status}",
    )


@pytest.mark.parametrize("old_status", ["unavailable", "attachment_unresolved"])
def test_zotero_live_success_removes_previous_live_diagnostic(old_status: str) -> None:
    row = ManifestRow(
        source_id="known-source",
        bibliography_key="known",
        mapping_status="resolved",
        mapping_rule="identifier",
        candidate_source_ids=("known-source",),
        conflicts=("existing conflict", f"Zotero live resolution: {old_status}"),
    )

    updated = cli._apply_zotero_resolutions(
        (row,), {"known": ZoteroResolution("enriched")}
    )[0]

    assert updated.conflicts == ("existing conflict",)
    assert updated.mapping_status == "resolved"
    assert updated.mapping_rule == "identifier"
    assert updated.candidate_source_ids == ("known-source",)


def test_zotero_live_failure_replaces_previous_live_diagnostic() -> None:
    row = ManifestRow(
        bibliography_key="missing",
        mapping_status="unresolved",
        mapping_rule="zotero-live",
        conflicts=("existing conflict", "Zotero live resolution: unavailable"),
    )

    updated = cli._apply_zotero_resolutions(
        (row,), {"missing": ZoteroResolution("error:TimeoutError")}
    )[0]

    assert updated.conflicts == (
        "existing conflict",
        "Zotero live resolution: error:TimeoutError",
    )


def test_zotero_attachment_unresolved_preserves_identity_and_missing_artifact(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    citation = replace(
        _document(target, "target"),
        citations=(CitationMention("[@known]", ("known",), "line", "1", "unresolved"),),
    )
    source = make_source_record(
        aliases=("known", "ZOTERO-ITEM"),
        title="Known Zotero item without an accessible attachment",
        doi="10.1234/known",
        provider="zotero",
    )
    outcome = ZoteroResolution("attachment_unresolved", source=source)
    monkeypatch.setattr(cli, "extract_document", lambda path, role: citation)
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: outcome)
    output = tmp_path / "out.csv"

    assert cli.main(
        [
            "manifest",
            "--target",
            str(target),
            "--zotero-live",
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    ) == 0
    json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert len(rows) == 1
    assert rows[0]["source_id"] == source.source_id
    assert rows[0]["title"] == source.title
    assert rows[0]["doi"] == source.doi
    assert rows[0]["mapping_status"] == "resolved"
    assert rows[0]["mapping_rule"] != "zotero-live"
    assert rows[0]["extraction_status"] == "missing"
    assert outcome.status in rows[0]["conflicts"]


@pytest.mark.parametrize(
    "outcome",
    [
        ZoteroResolution("unavailable"),
        ZoteroResolution(
            "attachment_unresolved",
            source=make_source_record(
                aliases=("refresh", "ZOTERO-REFRESH"),
                title="Known Zotero item without an accessible attachment",
                doi="10.1234/refresh",
                provider="zotero",
            ),
        ),
    ],
)
def test_repeated_zotero_live_refresh_deduplicates_identical_diagnostics(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outcome: ZoteroResolution,
) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    citation = replace(
        _document(target, "target"),
        citations=(CitationMention("[@refresh]", ("refresh",), "line", "1", "unresolved"),),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: citation)
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: outcome)
    output = tmp_path / "out.csv"
    base_args = [
        "manifest",
        "--target",
        str(target),
        "--zotero-live",
        "--output",
        str(output),
        "--cache-dir",
        str(tmp_path / "cache"),
    ]

    assert cli.main(base_args) == 0
    json.loads(capsys.readouterr().out)
    assert cli.main([*base_args, "--manifest", str(output)]) == 0
    json.loads(capsys.readouterr().out)
    rows = _read_rows(output)
    diagnostic = f"Zotero live resolution: {outcome.status}"

    assert len(rows) == 1
    assert json.loads(rows[0]["conflicts"]).count(diagnostic) == 1


def test_required_live_zotero_checks_availability_without_citations(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "target.md"
    target.write_text("Text", encoding="utf-8")
    monkeypatch.setattr(cli, "_check_zotero_available", lambda: (_ for _ in ()).throw(RuntimeError("unavailable")))
    monkeypatch.setattr(cli, "resolve_zotero", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))

    try:
        cli.main(["manifest", "--target", str(target), "--zotero-live", "--require-zotero", "--cache-dir", str(tmp_path / "cache")])
    except RuntimeError as error:
        assert str(error) == "unavailable"
    else:
        raise AssertionError("required Zotero availability must fail before citation resolution")


def test_cache_manifest_round_trip_preserves_imported_mapping_and_provenance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Text", encoding="utf-8")
    rows = (
        ManifestRow(
            source_id="source-1", bibliography_key="resolved", aliases=("resolved",), title="Resolved",
            source_path=str(source), target_files=("target.md",), target_locators=("line:2",),
            mapping_status="resolved", mapping_rule="identifier", candidate_source_ids=("source-1",),
            conflicts=("source conflict",),
        ),
        ManifestRow(
            bibliography_key="missing", aliases=("missing",), target_files=("target.md",),
            target_locators=("line:3",), mapping_status="unresolved", mapping_rule="none",
            conflicts=("missing provenance",),
        ),
        ManifestRow(
            bibliography_key="ambiguous", aliases=("ambiguous",), target_files=("target.md",),
            target_locators=("line:4",), mapping_status="ambiguous", mapping_rule="zotero-live",
            candidate_source_ids=("one", "two"), conflicts=("ambiguous provenance",),
        ),
    )
    imported = tmp_path / "input.csv"
    _write_rows(imported, rows)
    output = tmp_path / "output.csv"
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(imported), "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)
    written = {row["bibliography_key"]: row for row in _read_rows(output)}

    assert summary["expected"] == 3
    assert (summary["resolved"], summary["missing"], summary["ambiguous"], summary["analyzed"]) == (1, 1, 1, 1)
    for key in ("missing", "ambiguous"):
        original = next(row.to_csv_row() for row in rows if row.bibliography_key == key)
        assert written[key] == original
    assert written["resolved"]["target_files"] == '["target.md"]'
    assert written["resolved"]["target_locators"] == '["line:2"]'
    assert written["resolved"]["candidate_source_ids"] == '["source-1"]'
    assert written["resolved"]["conflicts"] == '["source conflict"]'
    assert written["resolved"]["extraction_status"] == "extracted"


def test_source_directory_ignores_nested_cache_and_unsupported_files_on_repeat_run(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "paper.md").write_text("Text", encoding="utf-8")
    (corpus / "ignored.bin").write_bytes(b"ignored")
    cache_dir = corpus / "cache"
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))
    argv = ["cache", "--source", str(corpus), "--cache-dir", str(cache_dir)]

    assert cli.main(argv) == 0
    capsys.readouterr()
    assert cli.main(argv) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == summary["analyzed"] == 1
    assert summary["coverage_percent"] == 100.0


def test_explicit_unsupported_source_is_an_isolated_unusable_outcome(tmp_path: Path, capsys) -> None:
    source = tmp_path / "unsupported.bin"
    source.write_bytes(b"binary")

    assert cli.main(["cache", "--source", str(source), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == summary["unusable"] == 1


@pytest.mark.parametrize("contents", [b"", b" \n\t "])
def test_empty_or_whitespace_sources_are_unusable_and_strict(tmp_path: Path, contents: bytes, capsys) -> None:
    source = tmp_path / "empty.txt"
    source.write_bytes(contents)

    assert cli.main(["cache", "--source", str(source), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]) == 2
    summary = json.loads(capsys.readouterr().out)

    assert summary["unusable"] == 1
    assert summary["analyzed"] == 0
    assert summary["coverage_percent"] == 0.0


def test_blank_pdf_is_unusable_on_fresh_and_reused_cli_cache_runs(tmp_path: Path, capsys) -> None:
    source = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with source.open("wb") as handle:
        writer.write(handle)
    argv = ["cache", "--source", str(source), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]

    assert cli.main(argv) == 2
    fresh = json.loads(capsys.readouterr().out)
    assert cli.main(argv) == 2
    reused = json.loads(capsys.readouterr().out)

    expected = {
        "expected": 1, "resolved": 1, "extracted": 0, "analyzed": 0,
        "missing": 0, "ambiguous": 0, "unusable": 1, "coverage_percent": 0.0,
    }
    assert fresh == reused == expected


def test_require_zotero_without_live_is_an_argparse_usage_error(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Text", encoding="utf-8")

    with pytest.raises(SystemExit):
        cli.main(["cache", "--source", str(source), "--require-zotero"])


def test_cli_uses_shared_media_types_for_all_supported_source_suffixes(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    suffixes = (".qmd", ".html", ".tex", ".docx", ".docm", ".doc", ".pdf")
    sources = []
    for index, suffix in enumerate(suffixes):
        path = tmp_path / f"source-{index}{suffix}"
        path.write_text("Text", encoding="utf-8")
        sources.extend(["--source", str(path)])
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))
    output = tmp_path / "output.csv"

    assert cli.main(["cache", *sources, "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    capsys.readouterr()
    actual = {Path(row["source_path"]).suffix: row["media_type"] for row in _read_rows(output)}

    assert actual == {
        ".qmd": "text/markdown", ".html": "text/html", ".tex": "text/x-tex",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docm": "application/vnd.ms-word.document.macroEnabled.12", ".doc": "application/msword",
        ".pdf": "application/pdf",
    }


def test_duplicate_imported_source_ids_coalesce_to_one_bound_artifact_row(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("alpha", encoding="utf-8")
    second.write_text("beta", encoding="utf-8")
    imported_a = tmp_path / "one.csv"
    imported_b = tmp_path / "two.csv"
    _write_rows(imported_a, (ManifestRow(source_id="same", aliases=("alpha",), title="Alpha", source_path=str(first)),))
    _write_rows(imported_b, (ManifestRow(source_id="same", aliases=("beta",), title="Beta", source_path=str(second)),))
    output = tmp_path / "output.csv"
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(imported_a), "--manifest", str(imported_b), "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert len(rows) == summary["expected"] == summary["analyzed"] == 1
    row = rows[0]
    assert Path(row["source_path"]).read_text(encoding="utf-8") == "alpha"
    assert row["source_sha256"] == hashlib.sha256(b"alpha").hexdigest()
    assert {"alpha", "beta"} <= set(json.loads(row["aliases"]))
    assert "source_path:" in row["conflicts"]


def test_fresh_target_evidence_upgrades_imported_not_applicable_source(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.md"
    source.write_text("source", encoding="utf-8")
    target.write_text("[@x]", encoding="utf-8")
    imported = tmp_path / "input.csv"
    _write_rows(imported, (ManifestRow(source_id="source-x", aliases=("x",), source_path=str(source), conflicts=("old",)),))
    source_document = _document(source, "source")
    target_document = replace(
        _document(target, "target"),
        citations=(CitationMention("[@x]", ("x",), "line", "1", "unresolved"),),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: target_document if Path(path) == target else source_document)
    output = tmp_path / "output.csv"

    assert cli.main(["manifest", "--target", str(target), "--manifest", str(imported), "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    capsys.readouterr()
    row = _read_rows(output)[0]

    assert (row["mapping_status"], row["bibliography_key"], row["target_files"], row["target_locators"]) == (
        "resolved", "x", '["' + str(target.resolve()).replace("\\", "\\\\") + '"]', '["line:1"]'
    )
    assert "old" in row["conflicts"]


def test_legacy_key_and_canonical_path_without_source_id_is_cached(tmp_path: Path, monkeypatch, capsys) -> None:
    source = tmp_path / "legacy.txt"
    source.write_text("source", encoding="utf-8")
    imported = tmp_path / "legacy.csv"
    imported.write_text("bibliography_key,canonical_pdf_path\nlegacy," + str(source) + "\n", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(imported), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == summary["analyzed"] == 1


def test_identity_bearing_manifest_source_without_path_is_missing_and_strict(
    tmp_path: Path, capsys
) -> None:
    imported = tmp_path / "input.csv"
    _write_rows(imported, (ManifestRow(source_id="identity-only", aliases=("x",)),))

    assert cli.main(["cache", "--manifest", str(imported), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]) == 2
    summary = json.loads(capsys.readouterr().out)

    assert summary["expected"] == summary["missing"] == 1


@pytest.mark.parametrize("reversed_order", [False, True])
def test_pathless_and_readable_same_identity_emit_one_complete_artifact_tuple(
    tmp_path: Path, monkeypatch, capsys, reversed_order: bool
) -> None:
    source = tmp_path / "a.txt"
    source.write_text("alpha", encoding="utf-8")
    pathless = tmp_path / "pathless.csv"
    readable = tmp_path / "readable.csv"
    _write_rows(pathless, (ManifestRow(source_id="same", provider="z-provider", aliases=("old",)),))
    _write_rows(readable, (ManifestRow(source_id="same", provider="a-provider", aliases=("new",), source_path=str(source)),))
    manifests = (readable, pathless) if reversed_order else (pathless, readable)
    output = tmp_path / "out.csv"
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(manifests[0]), "--manifest", str(manifests[1]), "--output", str(output), "--cache-dir", str(tmp_path / "cache")]) == 0
    summary = json.loads(capsys.readouterr().out)
    row = _read_rows(output)[0]

    assert (summary["expected"], summary["analyzed"], summary["missing"]) == (1, 1, 0)
    assert Path(row["source_path"]) == source.resolve()
    assert row["media_type"] == "text/plain"
    assert row["source_sha256"] == hashlib.sha256(b"alpha").hexdigest()
    assert row["extraction_status"] == "extracted"
    assert row["cache_path"]


def test_imported_unresolved_citation_is_upgraded_and_deduplicated_by_current_resolution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "x.txt"
    target = tmp_path / "target.md"
    source.write_text("source", encoding="utf-8")
    target.write_text("[@x]", encoding="utf-8")
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    _write_rows(first, (ManifestRow(bibliography_key="x", aliases=("x",), target_files=("old-a.md",), target_locators=("line:1",), mapping_status="unresolved", conflicts=("first",)),))
    _write_rows(second, (ManifestRow(bibliography_key="x", aliases=("x",), target_files=("old-b.md",), target_locators=("line:2",), mapping_status="unresolved", conflicts=("second",)),))
    source_document = _document(source, "source")
    target_document = replace(_document(target, "target"), citations=(CitationMention("[@x]", ("x",), "line", "1", "unresolved"),))
    monkeypatch.setattr(cli, "extract_document", lambda path, role: target_document if Path(path) == target else source_document)
    output = tmp_path / "output.csv"

    exit_code = cli.main(["manifest", "--target", str(target), "--source", str(source), "--manifest", str(first), "--manifest", str(second), "--output", str(output), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"])
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert exit_code == 0
    assert len(rows) == 1
    assert summary == {"expected": 1, "resolved": 1, "extracted": 1, "analyzed": 1, "missing": 0, "ambiguous": 0, "unusable": 0, "coverage_percent": 100.0}
    assert {"first", "second"} <= set(json.loads(rows[0]["conflicts"]))
    assert "old-a.md" in rows[0]["target_files"] and "old-b.md" in rows[0]["target_files"]


def test_path_only_legacy_row_without_mapping_status_is_nonmissing_but_explicit_unresolved_is_preserved(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "legacy.txt"
    source.write_text("source", encoding="utf-8")
    absent = tmp_path / "absent.csv"
    explicit = tmp_path / "explicit.csv"
    absent.write_text("bibliography_key,canonical_pdf_path\nlegacy," + str(source) + "\n", encoding="utf-8")
    explicit.write_text("bibliography_key,canonical_pdf_path,mapping_status\nlegacy," + str(source) + ",unresolved\n", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))

    assert cli.main(["cache", "--manifest", str(absent), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]) == 0
    absent_summary = json.loads(capsys.readouterr().out)
    assert cli.main(["cache", "--manifest", str(explicit), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing"]) == 2
    explicit_summary = json.loads(capsys.readouterr().out)

    assert (absent_summary["analyzed"], absent_summary["missing"]) == (1, 0)
    assert explicit_summary["missing"] == 1


def test_imported_concrete_source_absorbs_matching_unresolved_citation_after_target_resolution(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.md"
    source.write_text("source", encoding="utf-8")
    target.write_text("[@x]", encoding="utf-8")
    imported = tmp_path / "input.csv"
    _write_rows(
        imported,
        (
            ManifestRow(source_id="source-x", aliases=("x",), source_path=str(source), conflicts=("source",)),
            ManifestRow(
                bibliography_key="x", aliases=("x",), target_files=("old.md",),
                target_locators=("line:2",), mapping_status="unresolved", conflicts=("citation",),
            ),
        ),
    )
    source_document = _document(source, "source")
    target_document = replace(
        _document(target, "target"),
        citations=(CitationMention("[@x]", ("x",), "line", "1", "unresolved"),),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: target_document if Path(path) == target else source_document)
    output = tmp_path / "output.csv"

    exit_code = cli.main([
        "manifest", "--target", str(target), "--manifest", str(imported), "--output", str(output),
        "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing",
    ])
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert exit_code == 0
    assert len(rows) == 1
    assert summary == {
        "expected": 1, "resolved": 1, "extracted": 1, "analyzed": 1,
        "missing": 0, "ambiguous": 0, "unusable": 0, "coverage_percent": 100.0,
    }
    assert {"source", "citation"} <= set(json.loads(rows[0]["conflicts"]))
    assert "old.md" in rows[0]["target_files"]


def test_cross_provider_merge_keeps_artifact_fields_bound_to_selected_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    bibliography_path = tmp_path / "a.txt"
    imported_path = tmp_path / "b.txt"
    bibliography_path.write_text("alpha", encoding="utf-8")
    imported_path.write_text("beta", encoding="utf-8")
    imported = tmp_path / "input.csv"
    _write_rows(
        imported,
        (ManifestRow(
            source_id="doi:10.1000/x", doi="10.1000/x", aliases=("x",),
            source_path=str(imported_path), provider="imported",
        ),),
    )
    bibliography = tmp_path / "sources.json"
    bibliography.write_text(json.dumps([{
        "id": "csl-x", "DOI": "10.1000/x", "title": "X", "attachment": str(bibliography_path),
    }]), encoding="utf-8")
    monkeypatch.setattr(cli, "extract_document", lambda path, role: _document(Path(path), role))
    output = tmp_path / "output.csv"

    assert cli.main([
        "cache", "--manifest", str(imported), "--bibliography", str(bibliography), "--output", str(output),
        "--cache-dir", str(tmp_path / "cache"),
    ]) == 0
    capsys.readouterr()
    rows = _read_rows(output)

    assert len(rows) == 1
    row = rows[0]
    selected_path = Path(row["source_path"])
    assert row["source_sha256"] == hashlib.sha256(selected_path.read_bytes()).hexdigest()
    assert row["media_type"] == "text/plain"
    assert row["extraction_status"] == "extracted"
    assert row["text_quality"] == "good"
    assert row["cache_path"]
    conflicts = " ".join(json.loads(row["conflicts"]))
    assert str(bibliography_path) in conflicts
    assert str(imported_path) in conflicts


def test_current_ambiguous_citation_is_not_absorbed_by_historically_resolved_source(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    old_source = tmp_path / "old.txt"
    new_source = tmp_path / "x.txt"
    target = tmp_path / "target.md"
    old_source.write_text("old", encoding="utf-8")
    new_source.write_text("new", encoding="utf-8")
    target.write_text("[@x]", encoding="utf-8")
    imported = tmp_path / "historical.csv"
    _write_rows(
        imported,
        (ManifestRow(
            source_id="old", bibliography_key="x", aliases=("x",), source_path=str(old_source),
            mapping_status="resolved", mapping_rule="historical", candidate_source_ids=("old",),
        ),),
    )
    old_document = _document(old_source, "source")
    new_document = _document(new_source, "source")
    target_document = replace(
        _document(target, "target"),
        citations=(CitationMention("[@x]", ("x",), "line", "1", "unresolved"),),
    )
    monkeypatch.setattr(
        cli,
        "extract_document",
        lambda path, role: (
            target_document if Path(path) == target else old_document if Path(path) == old_source else new_document
        ),
    )
    output = tmp_path / "output.csv"

    exit_code = cli.main([
        "manifest", "--target", str(target), "--manifest", str(imported), "--source", str(new_source),
        "--output", str(output), "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing",
    ])
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)
    ambiguous = [row for row in rows if row["mapping_status"] == "ambiguous"]

    assert exit_code == 2
    assert summary["ambiguous"] == 1
    assert summary["coverage_percent"] < 100.0
    assert len(ambiguous) == 1
    assert "old" in json.loads(ambiguous[0]["candidate_source_ids"])


def test_currently_resolved_secondary_citation_key_absorbs_imported_unresolved_row(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.md"
    source.write_text("source", encoding="utf-8")
    target.write_text("[@a; @b]", encoding="utf-8")
    imported = tmp_path / "input.csv"
    _write_rows(
        imported,
        (
            ManifestRow(source_id="source", aliases=("a", "b"), source_path=str(source)),
            ManifestRow(bibliography_key="b", aliases=("b",), mapping_status="unresolved"),
        ),
    )
    source_document = _document(source, "source")
    target_document = replace(
        _document(target, "target"),
        citations=(
            CitationMention("[@a]", ("a",), "line", "1", "unresolved"),
            CitationMention("[@b]", ("b",), "line", "1", "unresolved"),
        ),
    )
    monkeypatch.setattr(cli, "extract_document", lambda path, role: target_document if Path(path) == target else source_document)
    output = tmp_path / "output.csv"

    exit_code = cli.main([
        "manifest", "--target", str(target), "--manifest", str(imported), "--output", str(output),
        "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing",
    ])
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert exit_code == 0
    assert len(rows) == 1
    assert summary == {
        "expected": 1, "resolved": 1, "extracted": 1, "analyzed": 1,
        "missing": 0, "ambiguous": 0, "unusable": 0, "coverage_percent": 100.0,
    }
    assert rows[0]["bibliography_key"] == "a"
    assert "b" in json.loads(rows[0]["aliases"])


def test_currently_ambiguous_secondary_citation_key_remains_ambiguous(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    target = tmp_path / "target.md"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    target.write_text("[@a; @b]", encoding="utf-8")
    imported = tmp_path / "input.csv"
    _write_rows(
        imported,
        (
            ManifestRow(source_id="first", aliases=("a", "b"), source_path=str(first)),
            ManifestRow(source_id="second", aliases=("b",), source_path=str(second)),
            ManifestRow(bibliography_key="b", aliases=("b",), mapping_status="unresolved"),
        ),
    )
    first_document = _document(first, "source")
    second_document = _document(second, "source")
    target_document = replace(
        _document(target, "target"),
        citations=(
            CitationMention("[@a]", ("a",), "line", "1", "unresolved"),
            CitationMention("[@b]", ("b",), "line", "1", "unresolved"),
        ),
    )
    monkeypatch.setattr(
        cli,
        "extract_document",
        lambda path, role: (
            target_document if Path(path) == target else first_document if Path(path) == first else second_document
        ),
    )
    output = tmp_path / "output.csv"

    exit_code = cli.main([
        "manifest", "--target", str(target), "--manifest", str(imported), "--output", str(output),
        "--cache-dir", str(tmp_path / "cache"), "--fail-on-missing",
    ])
    summary = json.loads(capsys.readouterr().out)
    rows = _read_rows(output)

    assert exit_code == 2
    assert summary == {
        "expected": 3, "resolved": 2, "extracted": 2, "analyzed": 2,
        "missing": 0, "ambiguous": 1, "unusable": 0, "coverage_percent": 66.67,
    }
    ambiguous = [row for row in rows if row["bibliography_key"] == "b"]
    assert len(ambiguous) == 1
    assert ambiguous[0]["mapping_status"] == "ambiguous"


def _write_manifest(tmp_path: Path, source: Path, source_id: str) -> Path:
    manifest = tmp_path / "input.csv"
    manifest.write_text("source_id,source_path,aliases,title\n" + source_id + "," + str(source) + ",[],Source\n", encoding="utf-8")
    return manifest


def _write_rows(path: Path, rows: tuple[ManifestRow, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter[str](handle, fieldnames=list(MANIFEST_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
