"""Package contracts for the Citation Support Audit skill."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from source_checker.extractors import SUPPORTED_SUFFIXES

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "citation-support-audit"
EXPECTED_LICENSE = "MIT; see LICENSE.txt"
EXPECTED_COMPATIBILITY = (
    "Requires Python 3.11+ and local file access; optional pdftotext for PDF layout "
    "extraction and LibreOffice for legacy DOC conversion."
)
EXPECTED_METADATA = {"author": "MicheleGarbelotto", "version": "0.1.0"}


def instruction_clauses(text: str) -> list[str]:
    """Split simple sentences, semicolon clauses, and bullets; preserve wrapped lines."""
    return [
        " ".join(clause.lower().split()).lstrip("-* ")
        for clause in re.split(r"[.!?;]\s*|\n\s*[-*]\s+", text)
    ]


def has_positive_directive(clause: str, pattern: str) -> bool:
    """Recognize local negations of directive verbs, not arbitrary prose semantics."""
    for match in re.finditer(pattern, clause):
        prefix = clause[: match.start()]
        suffix = clause[match.end() :]
        negated = re.search(
            r"\b(?:not|never|without|cannot|can't)(?:\s+(?:alone|by themselves))?\s*$",
            prefix,
        )
        if not negated and not re.match(r"\s+not\b", suffix):
            return True
    return False


def requires_upfront_source_map(text: str) -> bool:
    """Guard bounded pre-audit requirement wording; this is not a prose parser."""
    for clause in instruction_clauses(text):
        mapping = re.search(r"\bsource[- ](?:map|mapping)s?\b", clause)
        upfront = re.search(
            r"\b(?:up[- ]front|before (?:the audit|starting|auditing|proceeding)|prerequisite)\b",
            clause,
        )
        requirement = has_positive_directive(
            clause, r"\b(?:must|required|mandatory|require|requiring|obtain|ask for|request)\b"
        )
        if mapping and upfront and requirement:
            return True
    return False


def stops_for_missing_sources(text: str) -> bool:
    """Guard simple stop directives with availability conditions in either order."""
    for clause in instruction_clauses(text):
        source = re.search(r"\bsources?\b", clause)
        unavailable = re.search(r"\b(?:missing|inaccessible|unavailable|absent)\b", clause)
        stopping = has_positive_directive(clause, r"\b(?:stop|halt|abort|pause)\b")
        if source and unavailable and stopping:
            return True
    return False


def load_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    sections = text.split("---", 2)
    assert len(sections) == 3 and not sections[0].strip(), "Missing YAML frontmatter"
    frontmatter = yaml.safe_load(sections[1])
    assert isinstance(frontmatter, dict), "Frontmatter must be a YAML mapping"
    return frontmatter


def test_citation_skill_has_one_consistent_name() -> None:
    frontmatter = load_frontmatter(SKILL_ROOT / "SKILL.md")
    interface = yaml.safe_load((SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    assert frontmatter["name"] == "citation-support-audit"
    assert interface["interface"]["display_name"] == "Citation Support Audit"
    assert "$citation-support-audit" in interface["interface"]["default_prompt"]


def test_citation_skill_description_is_document_and_provider_neutral() -> None:
    description = load_frontmatter(SKILL_ROOT / "SKILL.md")["description"]

    assert isinstance(description, str) and description.strip()
    assert not re.search(r"\bthesis\b|\bZotero\s+PDFs\b", description, re.IGNORECASE)


def test_citation_skill_declares_standalone_distribution_metadata() -> None:
    frontmatter = load_frontmatter(SKILL_ROOT / "SKILL.md")

    assert frontmatter["license"] == EXPECTED_LICENSE
    assert frontmatter["compatibility"] == EXPECTED_COMPATIBILITY
    assert frontmatter["metadata"] == EXPECTED_METADATA


def test_citation_skill_license_matches_repository_license_bytes() -> None:
    assert (SKILL_ROOT / "LICENSE.txt").read_bytes() == (
        REPOSITORY_ROOT / "LICENSE"
    ).read_bytes()


def test_citation_skill_treats_audited_content_as_untrusted_evidence() -> None:
    text = " ".join(
        (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").lower().split()
    )

    for term in ("untrusted evidence", "never as instructions", "embedded", "commands", "links"):
        assert term in text


def test_citation_source_corpus_discloses_persistent_write_and_tool_boundaries() -> None:
    text = " ".join(
        (SKILL_ROOT / "references" / "source-corpus.md")
        .read_text(encoding="utf-8")
        .lower()
        .split()
    )

    assert re.search(
        r"persistent project artifacts?[^.]{0,180}(?:limited|written only)"
        r"[^.]{0,180}(?:configured|selected)[^.]{0,180}"
        r"documented defaults?[^.]{0,100}omitted",
        text,
    )
    assert not re.search(r"\bruntime\b[^.]{0,160}\bwrites only\b", text)
    assert re.search(
        r"default manifest output[^.]{0,100}`source-manifest\.csv`"
        r"[^.]{0,100}`--output`",
        text,
    )
    assert re.search(r"default[^.]{0,80}`--cache-dir`[^.]{0,80}`text-cache/`", text)
    assert re.search(
        r"legacy doc conversion[^.]{0,180}system temporary directory", text
    )
    assert re.search(
        r"libreoffice[^.]{0,180}(?:may|can)[^.]{0,100}(?:update|write)"
        r"[^.]{0,100}user profile",
        text,
    )
    assert re.search(
        r"(?:runtime|side effects?)[^.]{0,120}(?:does|do) not modify the target, "
        r"source corpus, zotero library, or mendeley export",
        text,
    )
    assert (
        "`pdftotext` and libreoffice are invoked only for the documented pdf and legacy "
        "doc extraction routes"
    ) in text
    assert "appropriately isolated environment" in text


def test_citation_skill_links_all_references() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    links = set(re.findall(r"\]\((references/[^\s)]+)\)", text))
    required = {
        "references/source-corpus.md",
        "references/metrics-and-rules.md",
        "references/report-template.md",
        "references/methodology-and-attribution.md",
    }

    assert required <= links, f"Missing reference links: {required - links}"
    assert all((SKILL_ROOT / link).is_file() for link in required)


def test_citation_skill_does_not_require_an_upfront_source_map() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert not requires_upfront_source_map(text), "Source map must not be an up-front requirement"


def test_citation_skill_does_not_stop_for_missing_sources() -> None:
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert not stops_for_missing_sources(text), "Missing sources alone must not trigger a stop"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A completed source map is required before the audit.", True),
        ("- Before auditing, require a source map.", True),
        ("If starting the audit, the user must provide a source map up front.", True),
        ("A source map is not required up front.", False),
        ("- Do not require a source map before auditing.", False),
        ("Infer source mappings; ask only about materially ambiguous pairs.", False),
        ("A source map is not required up front. Before auditing, require a source map.", True),
    ],
)
def test_upfront_source_map_guard(text: str, expected: bool) -> None:
    assert requires_upfront_source_map(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("If a source is missing, stop the audit.", True),
        ("- Stop the audit if sources are unavailable.", True),
        ("When sources are inaccessible, pause the audit.", True),
        (
            "Stop or issue a partial audit when material source documents are inaccessible.",
            True,
        ),
        (
            "Stop only if the target is unreadable; missing sources alone do not stop the audit.",
            False,
        ),
        ("- Do not stop if sources are missing.", False),
        ("If sources are unavailable, continue with accessible sources.", False),
        ("Missing sources alone cannot stop the audit.", False),
        ("Do not stop for missing sources. If a source is missing, stop the audit.", True),
    ],
)
def test_missing_source_stop_guard(text: str, expected: bool) -> None:
    assert stops_for_missing_sources(text) is expected


def test_citation_runtime_is_synchronized() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/sync_skill_runtime.py",
            "--check",
            "skills/citation-support-audit",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("suffix", SUPPORTED_SUFFIXES)
def test_source_corpus_documents_supported_extensions(suffix: str) -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    assert re.search(rf"(?<!\w){re.escape(suffix)}(?!\w)", text), suffix


@pytest.mark.parametrize(
    "route",
    [
        r"local\s+(?:files\s+(?:and|or)\s+)?director(?:y|ies)",
        r"\bzotero\b",
        r"\bmendeley\s+exports?\b",
        r"\bbibtex\b",
        r"\bbiblatex\b",
        r"\bris\b",
        r"\bcsl\s+json\b",
        r"\bembedded\s+(?:references\s*[/&]\s*)?bibliograph(?:y|ies)\b",
        r"\bsource-manifest\.csv\b",
    ],
)
def test_source_corpus_documents_generic_routes(route: str) -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    assert re.search(route, text, re.IGNORECASE), route


@pytest.mark.parametrize(
    "option", ["--target", "--source", "--bibliography", "--manifest", "--zotero-live"]
)
def test_source_corpus_documents_cli_inputs(option: str) -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    assert option in text


@pytest.mark.parametrize(
    "status",
    [
        "resolved",
        "ambiguous",
        "unresolved",
        "not-applicable",
        "not_run",
        "extracted",
        "missing",
        "empty",
        "needs_ocr",
        "needs_review",
        "unusable",
        "error:",
    ],
)
def test_source_corpus_documents_runtime_statuses(status: str) -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    assert re.search(rf"(?<![\w-]){re.escape(status)}(?![\w-])", text), status


def test_source_corpus_does_not_require_a_separate_mapping_file() -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    assert not requires_upfront_source_map(text)
    assert not stops_for_missing_sources(text)
    # Require an explicit exemption, allowing different prose around the contract.
    clauses = instruction_clauses(text)
    assert any(
        "separate" in clause
        and "mapping" in clause
        and "file" in clause
        and re.search(r"\b(?:no|not|never|without)\b", clause)
        for clause in clauses
    ), "Intake must explicitly waive a separate mapping file"


@pytest.mark.parametrize(
    ("condition", "required_actions"),
    [
        (r"\btarget\b", [r"\bask\b", r"\bfiles?\b"]),
        (r"\bcorpus\b", [r"\bask\b", r"\bwhere\b", r"\bsources?\b"]),
        (
            r"\bmapping\s+ambiguity\b",
            [r"\bcandidates?\b", r"\bask\b", r"\bonly\b", r"\bmatch\b"],
        ),
        (r"\binaccessible\s+source\b", [r"\bcontinue\b", r"\brecord\b", r"\bstatus\b"]),
        (
            r"\bunreadable\s+target\b",
            [r"\bstop\b", r"\bsubstantive\b", r"\bdiagnostic\s+report\b"],
        ),
    ],
)
def test_source_corpus_has_adaptive_intake_actions(
    condition: str, required_actions: list[str]
) -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    rows = [
        [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.lstrip().startswith("|")
    ]
    matching = [row[1] for row in rows if len(row) == 2 and re.search(condition, row[0])]
    assert matching, f"Missing intake route: {condition}"
    assert any(all(re.search(action, cell) for action in required_actions) for cell in matching)


def test_missing_target_uses_complete_default_without_asking_scope() -> None:
    text = (SKILL_ROOT / "references" / "source-corpus.md").read_text(encoding="utf-8")
    rows = [
        [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        for line in text.splitlines()
        if line.lstrip().startswith("|")
    ]
    target_actions = [row[1] for row in rows if len(row) == 2 and row[0] == "target"]

    assert target_actions
    assert all("scope" not in action for action in target_actions)
    assert "complete audit" in text.lower()


def test_source_corpus_discloses_runtime_boundaries() -> None:
    text = " ".join(reference_text("source-corpus.md").lower().split())

    assert re.search(
        r"runtime summary[^.]{0,180}manifest(?:-| )row[^.]{0,180}"
        r"(?:not|do not)[^.]{0,120}(?:report|audit)[^.]{0,80}denominators?",
        text,
    )
    assert re.search(
        r"(?:install|installed|provide)[^.]{0,100}(?:runtime|third-party) dependencies",
        text,
    )
    assert re.search(r"zotero-live[^.]{0,180}(?:pdf-only|pdf attachments? only)", text)


def test_source_corpus_discloses_non_persisted_runtime_details() -> None:
    text = " ".join(reference_text("source-corpus.md").lower().split())

    assert re.search(
        r"(?:detailed|full) (?:extraction )?error[^.]{0,180}"
        r"(?:not|does not)[^.]{0,100}(?:manifest|summary|csv)",
        text,
    )
    assert re.search(
        r"visible citation[^.]{0,180}(?:hash|hashed)[^.]{0,180}"
        r"(?:raw|original|human-readable)[^.]{0,80}(?:not|isn't|is not)",
        text,
    )


def reference_text(name: str) -> str:
    """Read one Citation Support Audit reference with normalized line endings."""
    return (SKILL_ROOT / "references" / name).read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize(
    "formula",
    [
        (
            "whole-scope citation recall = fully supported eligible claims / "
            "all eligible claims * 100"
        ),
        ("whole-scope citation precision = supporting citations / all citations evaluated * 100"),
        (
            "verified-subset citation recall = fully supported classifiable claims / "
            "classifiable eligible claims * 100"
        ),
        (
            "verified-subset citation precision = supporting classifiable citations / "
            "classifiable citations * 100"
        ),
        ("audit coverage = classifiable eligible claims / all eligible claims * 100"),
        ("corpus coverage = analyzed expected sources / all expected sources * 100"),
    ],
)
def test_metrics_define_required_formulas(formula: str) -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())
    assert formula in text


def test_whole_scope_recall_and_precision_have_independent_classifiability_gates() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"whole-scope citation recall[^.]{0,180}(?:only|allowed)[^.]{0,100}"
        r"all eligible claims? (?:is|are) classifiable",
        text,
    )
    assert re.search(
        r"whole-scope citation precision[^.]{0,180}(?:only|allowed)[^.]{0,100}"
        r"all in-scope claim-citation (?:occurrences|associations) (?:is|are) classifiable",
        text,
    )


def test_precision_defines_occurrence_counting_for_grouped_and_repeated_citations() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"each in-scope claim-citation (?:occurrence|association)[^.]{0,120}"
        r"(?:counting unit|one unit)",
        text,
    )
    assert re.search(r"grouped citations?[^.]{0,140}(?:separate|one unit per)", text)
    assert re.search(
        r"repeated citations?[^.]{0,180}(?:each|separate)[^.]{0,80}"
        r"(?:claim|association|occurrence)",
        text,
    )


def test_joint_set_rules_cover_contradictory_and_unavailable_citations() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"(?:joint|cited set)[^.]{0,180}contradict[^.]{0,180}not fully supported",
        text,
    )
    assert re.search(
        r"unavailable citation[^.]{0,220}unverifiable[^.]{0,220}"
        r"(?:another|remaining|accessible) citation[^.]{0,160}fully supports",
        text,
    )
    assert re.search(
        r"(?:fully supports|full support)[^.]{0,180}(?:partial|narrower)[^.]{0,180}"
        r"(?:joint|cited set)[^.]{0,120}(?:fully supported|full support)",
        text,
    )


def test_verified_subset_precision_requires_classifiable_joint_support() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"claim-citation (?:occurrence|association)[^.]{0,180}classifiable"
        r"[^.]{0,180}(?:individual contribution|individual source)"
        r"[^.]{0,180}(?:joint-support gate|joint support)"
        r"[^.]{0,100}classifiable",
        text,
    )
    assert re.search(
        r"joint[^.]{0,100}unverifiable[^.]{0,180}(?:every|all)"
        r"[^.]{0,100}(?:attached|associated) claim-citation (?:occurrences|associations)"
        r"[^.]{0,180}(?:exclude|excluded|excluding)"
        r"[^.]{0,120}verified-subset citation precision",
        text,
    )


def test_verified_subset_metrics_are_required_when_any_claim_is_classifiable() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"(?:must|required to|compute)[^.]{0,160}verified-subset metrics?[^.]{0,180}"
        r"(?:at least one|one or more)[^.]{0,100}(?:eligible )?claims? "
        r"(?:is|are) classifiable",
        text,
    )


def test_verified_subset_warns_against_extrapolating_to_unavailable_scope() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"verified subset[^.]{0,180}(?:not random|non-random|selection bias)", text
    )
    assert re.search(
        r"verified subset[^.]{0,240}(?:cannot|must not|does not)[^.]{0,120}"
        r"(?:estimate|represent|generalize|extrapolate)[^.]{0,120}"
        r"(?:unavailable|unverified|full) scope",
        text,
    )


def test_audit_coverage_is_claim_adjudication_not_evidence_availability() -> None:
    metrics = " ".join(reference_text("metrics-and-rules.md").lower().split())
    report = " ".join(reference_text("report-template.md").lower().split())

    assert re.search(r"audit coverage[^.]{0,160}(?:claim adjudication|claim classification)", metrics)
    assert not re.search(r"audit coverage[^.]{0,160}evidence availability", report)


def test_abstract_only_rule_requires_all_evidence_and_qualifiers() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"abstract-only[^.]{0,180}(?:all|every)[^.]{0,120}"
        r"(?:needed|required|material)[^.]{0,120}(?:evidence|qualifiers?)",
        text,
    )
    assert re.search(r"abstract-only[^.]{0,260}otherwise[^.]{0,100}unverifiable", text)


def test_unverifiable_evidence_is_not_classified_as_unsupported() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"unverifiable[^.]{0,100}(?:is not|must not be|do not (?:treat|classify))"
        r"[^.]{0,80}unsupported",
        text,
    )


def test_diagnostics_stay_separate_and_composite_scores_are_forbidden() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(r"diagnostic counts?[^.]{0,120}\bseparate\b", text)
    assert re.search(r"(?:do not|never|must not)[^.]{0,100}\bcomposite scores?\b", text)


@pytest.mark.parametrize(
    ("skill_term", "metric_label"),
    [
        ("Unsupported", "Does not support"),
        ("Contradictory", "Contradicts"),
    ],
)
def test_metrics_map_skill_outcome_terms_to_support_labels(
    skill_term: str, metric_label: str
) -> None:
    lines = reference_text("metrics-and-rules.md").splitlines()

    assert any(
        skill_term.lower() in line.lower() and metric_label.lower() in line.lower()
        for line in lines
    ), f"Document the mapping between {skill_term!r} and {metric_label!r}"


def test_report_has_the_required_nine_sections_in_order() -> None:
    headings = re.findall(
        r"^##\s+\d+\.\s+(.+?)\s*$",
        reference_text("report-template.md"),
        re.MULTILINE,
    )

    assert [heading.lower() for heading in headings] == [
        "scope and corpus coverage",
        "method and extraction quality",
        "quantitative scorecard",
        "reference integrity and citation mechanics",
        "claim-source matrix",
        "passage-level evidence",
        "potentially missing citations",
        "inaccessible/ambiguous sources needed for fuller coverage",
        "limitations and conclusion",
    ]


@pytest.mark.parametrize(
    "source_count", ["expected", "resolved", "extracted", "analyzed", "missing"]
)
def test_report_requires_each_source_count(source_count: str) -> None:
    text = reference_text("report-template.md")

    assert re.search(
        rf"\b{source_count}\s+(?:source\s+)?(?:records?|sources?)\b",
        text,
        re.IGNORECASE,
    )


def test_report_requires_an_explicit_complete_or_partial_scope() -> None:
    text = " ".join(reference_text("report-template.md").lower().split())

    assert re.search(
        r"(?:result|audit) scope[^.]{0,100}\bcomplete\b[^.]{0,60}\bpartial\b",
        text,
    )


def test_uncited_eligible_claims_are_classifiable_zeroes_for_recall() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())
    clauses = instruction_clauses(text)

    assert any(
        "eligible claim" in clause
        and "warrants citation" in clause
        and "lacks one" in clause
        and "classifiable" in clause
        and re.search(r"\b(?:contributes?|counts?)\b[^.]{0,40}`?0`?", clause)
        for clause in clauses
    )
    assert any(
        re.search(r"\bclaims?\s+(?:that have|with)\s+citations?\b", clause)
        and "classifi" in clause
        and "evidence" in clause
        and re.search(r"\b(?:access|accessible|accessibility|availability)\w*\b", clause)
        for clause in clauses
    ), "Evidence accessibility must govern classifiability for cited claims"


def test_report_scorecard_labels_recall_and_precision_as_alce_style() -> None:
    rows = [
        [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        for line in reference_text("report-template.md").splitlines()
        if line.lstrip().startswith("|")
    ]
    metric_names = [
        row[0]
        for row in rows
        if row and re.search(r"\b(?:citation recall|citation precision)\b", row[0])
    ]

    assert metric_names
    assert all("alce-style" in metric for metric in metric_names)


def test_every_source_limitation_reports_effect_without_negative_classification() -> None:
    clauses = instruction_clauses(reference_text("report-template.md"))

    assert any(
        "every source limitation" in clause and "effect" in clause and "coverage" in clause
        for clause in clauses
    )
    assert any(
        "unsupported" in clause
        and re.search(r"\bevidence\s+(?:is\s+)?unavailable\b|\bunavailable evidence\b", clause)
        and re.search(r"\b(?:not|never|without|must not|do not)\b", clause)
        for clause in clauses
    )
