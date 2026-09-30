"""Package contracts for the Plagiarism Audit skill."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from source_checker.extractors import SUPPORTED_SUFFIXES

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "plagiarism-audit"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
README_PATH = REPOSITORY_ROOT / "README.md"

EXPECTED_DESCRIPTION = (
    "Use when checking a document against a defined source corpus for textual "
    "similarity, originality concerns, close paraphrase, patchwriting, translated "
    "overlap, or visible attribution signals, including when the corpus is incomplete."
)
EXPECTED_LICENSE = "MIT; see LICENSE.txt"
EXPECTED_COMPATIBILITY = (
    "Requires Python 3.11+ and local file access; optional pdftotext for PDF layout "
    "extraction and LibreOffice for legacy DOC conversion."
)
EXPECTED_METADATA = {"author": "MicheleGarbelotto", "version": "0.1.0"}


def normalized_skill_text() -> str:
    """Return whitespace-normalized skill instructions for structural assertions."""
    return " ".join(SKILL_PATH.read_text(encoding="utf-8").lower().split())


def source_corpus_text() -> str:
    """Return the source-corpus reference with normalized line endings."""
    return (SKILL_ROOT / "references" / "source-corpus.md").read_text(
        encoding="utf-8"
    ).replace("\r\n", "\n")


def reference_text(filename: str) -> str:
    """Return one plagiarism-audit reference with normalized line endings."""
    return (SKILL_ROOT / "references" / filename).read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    )


def normalized_reference_text(filename: str) -> str:
    """Return whitespace-normalized reference prose without Markdown emphasis marks."""
    text = " ".join(reference_text(filename).lower().split())
    return re.sub(r"[*_`]", "", text)


def methodology_concept_rows() -> dict[str, tuple[str, str, str]]:
    """Parse the five concept rows from the methodology Markdown table."""
    rows: dict[str, tuple[str, str, str]] = {}
    for line in reference_text("methodology-and-attribution.md").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or cells[0] == "Concept" or set(cells[0]) == {"-"}:
            continue
        rows[cells[0].lower()] = (cells[1], cells[2], cells[3])
    return rows


def requires_partial_corpus_quantification(text: str) -> bool:
    """Detect an affirmative requirement to quantify any analyzable source subset."""
    normalized = " ".join(text.lower().split())
    condition = (
        r"(?:at least one|one or more|any)[^.]{0,100}"
        r"(?:source|expected source)[^.]{0,80}"
        r"(?:(?:is|are|remains?) analyzable|(?:has|have) been analyzed)"
    )
    result = r"(?:results?|metrics?|similarity|percentages?)"
    negated_requirement = (
        r"\b(?:must|should|is|are) not\b|\bnot (?:required|mandatory)\b|"
        r"\b(?:do|does|did) not\b|\bmust (?:avoid|refrain from)\b|"
        r"\b(?:avoid|refrain from)\b[^.]{0,80}(?:comput\w*|quantif\w*)|"
        r"\bno requirement\b|\bnever\b"
    )
    affirmative_requirement = (
        r"\bmust\b[^.]{0,100}(?:quantif\w*|compute)|"
        r"\brequired to\b[^.]{0,100}(?:be )?(?:quantif\w*|comput\w*)|"
        r"\balways\b[^.]{0,100}(?:quantif\w*|compute)|"
        r"\bmandatory\b"
    )
    for sentence in re.split(r"(?<=[.!?])\s+", normalized):
        if not (re.search(condition, sentence) and re.search(result, sentence)):
            continue
        if re.search(negated_requirement, sentence):
            continue
        if re.search(affirmative_requirement, sentence):
            return True
    return False


def requires_scope_label_for_every_percentage(text: str) -> bool:
    """Detect an affirmative all-percentages complete/partial labelling rule."""
    normalized = " ".join(text.lower().split())
    for sentence in re.split(r"(?<=[.!?])\s+", normalized):
        if not re.search(r"\b(?:every|each|all)\b[^.]{0,80}\bpercent(?:age)?s?\b", sentence):
            continue
        if not ("complete" in sentence and "partial" in sentence):
            continue
        if re.search(
            r"\b(?:must|should|is|are) not\b|\bnot (?:required|mandatory)\b|"
            r"\b(?:do|does|did) not\b|\bmust (?:avoid|refrain from)\b|"
            r"\b(?:avoid|refrain from)\b[^.]{0,80}label\w*|"
            r"\bno requirement\b|\bnever\b",
            sentence,
        ):
            continue
        if re.search(r"\b(?:must|label|required|mandatory)\b", sentence):
            return True
    return False


def documents_affirmative_corpus_route(
    text: str, route_pattern: str, capability_pattern: str
) -> bool:
    """Return whether one clause affirmatively documents a route capability."""
    for clause in re.split(r"(?<=[.;])\s+|\n", text):
        if not (
            re.search(route_pattern, clause, re.IGNORECASE)
            and re.search(capability_pattern, clause, re.IGNORECASE)
        ):
            continue
        if not re.search(
            r"\b(?:not|never|cannot|can't|unsupported|does not|do not|no)\b",
            clause,
            re.IGNORECASE,
        ):
            return True
    return False


def stops_for_missing_sources(text: str) -> bool:
    """Detect a stop rule whose stated condition is only source unavailability."""
    stop_verb = r"(?:stop|halt|end|abort|pause)"
    unavailable = (
        r"(?:missing|inaccessible|unavailable|unresolved|incomplete|ambiguous|unusable|"
        r"cannot\s+(?:be\s+)?(?:access(?:ed)?|resolve(?:d)?))"
    )
    unavailable_source = (
        rf"(?:{unavailable})[^.;\n]{{0,100}}\b(?:sources?|corpus)\b|"
        rf"\b(?:sources?|corpus)\b[^.;\n]{{0,100}}(?:{unavailable})"
    )

    def stop_is_negated(clause: str) -> bool:
        negated_patterns = (
            (
                rf"\b(?:do|does|did|must|should|can|could|may|might)\s+not"
                rf"(?:\s+\w+){{0,3}}\s+{stop_verb}\b"
            ),
            (
                rf"\b(?:do|does|did)\s+not(?:\s+\w+){{0,3}}\s+require\b[^.;\n]{{0,80}}"
                rf"\bto\s+{stop_verb}\b"
            ),
            (
                rf"\b(?:is|are)\s+not\s+(?:a\s+)?(?:reason|basis|cause)\b"
                rf"[^.;\n]{{0,60}}\bto\s+{stop_verb}\b"
            ),
            rf"\bnever(?:\s+\w+){{0,3}}\s+{stop_verb}\b",
        )
        return any(re.search(pattern, clause, re.IGNORECASE) for pattern in negated_patterns)

    for clause in re.split(r"[.;]\s*|\n", text):
        if (
            re.search(unavailable_source, clause, re.IGNORECASE)
            and re.search(rf"\b{stop_verb}\b", clause, re.IGNORECASE)
            and not stop_is_negated(clause)
        ):
            return True

    stop_section = re.search(
        rf"^#{{2,6}}\s+[^\n]*\b{stop_verb}\b[^\n]*\n(.*?)(?=^#{{1,6}}\s|\Z)",
        text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if not stop_section:
        return False
    for bullet in re.findall(r"^\s*[-*]\s+(.+)$", stop_section.group(1), re.MULTILINE):
        if (
            re.search(unavailable_source, bullet, re.IGNORECASE)
            and not re.search(r"\bcontinue\b", bullet, re.IGNORECASE)
            and not stop_is_negated(bullet)
        ):
            return True
    return False


def load_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    sections = text.split("---", 2)
    assert len(sections) == 3 and not sections[0].strip(), "Missing YAML frontmatter"
    frontmatter = yaml.safe_load(sections[1])
    assert isinstance(frontmatter, dict), "Frontmatter must be a YAML mapping"
    return frontmatter


def test_plagiarism_skill_has_one_consistent_name() -> None:
    frontmatter = load_frontmatter(SKILL_PATH)
    interface = yaml.safe_load(
        (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )

    assert frontmatter == {
        "name": "plagiarism-audit",
        "description": EXPECTED_DESCRIPTION,
        "license": EXPECTED_LICENSE,
        "compatibility": EXPECTED_COMPATIBILITY,
        "metadata": EXPECTED_METADATA,
    }
    assert interface["interface"] == {
        "display_name": "Plagiarism Audit",
        "short_description": "Audit a document for source-bounded similarity",
        "default_prompt": (
            "Use $plagiarism-audit to audit this document against the specified source "
            "corpus and report similarity evidence and coverage."
        ),
    }


def test_plagiarism_skill_license_matches_repository_license_bytes() -> None:
    assert (SKILL_ROOT / "LICENSE.txt").read_bytes() == (
        REPOSITORY_ROOT / "LICENSE"
    ).read_bytes()


def test_plagiarism_skill_treats_audited_content_as_untrusted_evidence() -> None:
    text = " ".join(SKILL_PATH.read_text(encoding="utf-8").lower().split())

    for term in ("untrusted evidence", "never as instructions", "embedded", "commands", "links"):
        assert term in text


def test_plagiarism_source_corpus_discloses_persistent_write_and_tool_boundaries() -> None:
    text = " ".join(source_corpus_text().lower().split())

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


def test_plagiarism_skill_uses_generic_document_terminology() -> None:
    description = load_frontmatter(SKILL_PATH)["description"]

    assert isinstance(description, str) and description.strip()
    assert re.search(r"\bdocument\b", description, re.IGNORECASE)
    assert not re.search(r"\bthesis\b|\bZotero\s+PDFs\b", description, re.IGNORECASE)


def test_plagiarism_skill_has_no_format_or_provider_specific_scope_assumption() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")

    assert not re.search(r"\bthes(?:is|es)\b", text, re.IGNORECASE)
    assert not re.search(
        r"\b(?:qmd|pdfs?|zotero)[- ]only\b|"
        r"\b(?:only|exclusively)\s+(?:qmd|pdfs?|zotero)\b",
        text,
        re.IGNORECASE,
    )


def test_plagiarism_skill_links_all_references() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    links = set(re.findall(r"\]\((references/[^\s)]+)\)", text))
    required = {
        "references/source-corpus.md",
        "references/metrics-and-rules.md",
        "references/report-template.md",
        "references/methodology-and-attribution.md",
    }

    assert required <= links, f"Missing reference links: {required - links}"
    assert all((SKILL_ROOT / link).is_file() for link in required)


def test_plagiarism_skill_defines_source_bounded_non_verdict_judgment() -> None:
    text = normalized_skill_text()

    assert re.search(r"\bsource[- ]bounded\b", text)
    assert (
        "this audit does not determine misconduct, intent, authorship, legal liability, "
        "or institutional findings."
    ) in text


def test_plagiarism_skill_places_methodological_notice_after_purpose() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    purpose = text.split("## Purpose and limits", 1)[1].split("## Intake and authorization", 1)[0]
    normalized = " ".join(purpose.lower().split())

    assert "independent implementation" in normalized
    assert "public" in normalized
    assert "source-bounded" in normalized
    assert "not equivalent" in normalized
    assert "not affiliated" in normalized
    assert "not a plagiarism or misconduct verdict" in normalized
    assert "[methodology and attribution](references/methodology-and-attribution.md)" in normalized
    assert "has not been certified by any cited product or organization" in normalized


def test_methodology_snapshot_rows_trace_each_concept_to_official_sources() -> None:
    rows = methodology_concept_rows()
    expected_sources = {
        "plagiarism boundary": (
            "https://ori.hhs.gov/definition-research-misconduct",
            "https://ori.hhs.gov/plagiarism-text",
        ),
        "overall and per-source similarity": (
            (
                "https://guides.ithenticate.com/hc/en-us/articles/"
                "27838877807245-Overview-of-the-new-Similarity-Report-experience"
            ),
            "https://www.crossref.org/documentation/similarity-check/similarity-report-understand/",
        ),
        "match categories": (
            "https://docs.copyleaks.com/concepts/features/detection-levels",
        ),
        "attribution groups": (
            (
                "https://guides.turnitin.com/hc/en-us/articles/"
                "28057483210637-How-do-the-Match-Groups-work-in-the-new-Similarity-Report"
            ),
        ),
        "review bands": (
            (
                "https://help.anthology.com/blackboard/student/en/plagiarism/safeassign/"
                "safeassign-originality-report.html"
            ),
        ),
    }

    assert set(rows) == set(expected_sources)
    for concept, urls in expected_sources.items():
        source, adaptation, non_claim = rows[concept]
        assert all(url in source for url in urls)
        assert source.count("accessed 2026-09-23") == len(urls)
        assert adaptation.strip()
        assert non_claim.strip()


def test_methodology_snapshot_distinguishes_copyleaks_term_from_repository_label() -> None:
    source, adaptation, _ = methodology_concept_rows()["match categories"]

    assert "Copyleaks" in source
    assert "Cross-Language Detection" in adaptation
    assert "repository label" in adaptation.lower()
    assert "derived from" in adaptation.lower()
    assert not re.search(
        r"public labels?[^.]{0,240}Cross-language / Translated Match", adaptation
    )

    metrics = reference_text("metrics-and-rules.md")
    report = reference_text("report-template.md")
    assert re.search(
        r"Cross-language / Translated Match[^.]{0,180}(?:adaptation|adapted)"
        r"[^.]{0,120}Cross-Language Detection",
        metrics,
    )
    assert "repository category adapted from Copyleaks Cross-Language Detection" in report


def test_passage_template_uses_neutral_category_placeholder_with_provenance() -> None:
    report = reference_text("report-template.md")
    passage_template = report.split("## 6. Passage-level parallel evidence", 1)[1].split(
        "## 7.", 1
    )[0]

    assert "[Copyleaks-style category]" not in passage_template
    assert "- Match type: [verified category;" in passage_template
    assert "repository label as adapted from Copyleaks vocabulary" in passage_template
    assert "Cross-language / Translated Match" in passage_template
    assert "adapted from Copyleaks Cross-Language Detection" in passage_template


def test_methodology_snapshot_describes_independently_specified_formula_adaptation() -> None:
    text = reference_text("methodology-and-attribution.md")
    preamble = text.split("## Concept-level traceability", 1)[0]
    _, adaptation, _ = methodology_concept_rows()["overall and per-source similarity"]

    assert "original adaptations" not in preamble.lower()
    assert "independently specified" in preamble.lower()
    assert re.search(r"public(?:ly)? documented[^.]{0,160}formula", adaptation, re.IGNORECASE)


def test_methodology_snapshot_preserves_required_nonclaims() -> None:
    normalized = normalized_reference_text("methodology-and-attribution.md")

    assert "independent adaptation" in normalized
    assert "explicit non-claim" in normalized
    assert "not product-equivalent" in normalized
    assert "not affiliated" in normalized
    assert "no plagiarism or misconduct determination" in normalized


def test_methodology_snapshot_has_no_pending_placeholders() -> None:
    methodology = normalized_reference_text("methodology-and-attribution.md")
    metrics = normalized_reference_text("metrics-and-rules.md")

    assert "pending refresh" not in methodology
    assert "pending refresh" not in metrics
    assert "when their official definitions have been verified" not in metrics
    assert "safeassign-derived contextual review labels" in metrics
    assert "do not estimate the probability of plagiarism" in metrics
    assert "not decision thresholds" in metrics


def test_readme_repeats_plagiarism_methodology_nonclaims() -> None:
    text = " ".join(README_PATH.read_text(encoding="utf-8").lower().split())

    assert re.search(r"plagiarism audit[^.]{0,220}independent implementation", text)
    assert re.search(r"plagiarism audit[^.]{0,420}not product-equivalent", text)
    assert re.search(r"plagiarism audit[^.]{0,500}not affiliated", text)
    assert re.search(r"plagiarism audit[^.]{0,560}not (?:a )?misconduct verdict", text)


def test_plagiarism_skill_continues_with_an_incomplete_analyzable_corpus() -> None:
    text = normalized_skill_text()

    assert re.search(
        r"\bcontinue\b[^.]{0,140}\b(?:any|a)\b[^.]{0,80}"
        r"\bnon-empty\b[^.]{0,80}\banalyzable corpus\b",
        text,
    )
    assert re.search(r"\bquantif\w*\b[^.]{0,140}\bonly\b[^.]{0,80}\banalyzed sources\b", text)
    assert re.search(r"\bcorpus coverage\b[^.]{0,100}\bnext to every score\b", text)


def test_plagiarism_skill_has_no_missing_source_stop_condition() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert not stops_for_missing_sources(text), "Missing sources alone must not trigger a stop"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("If a source is missing, stop the audit.", True),
        ("Halt the audit when sources are inaccessible.", True),
        ("End the audit if a source is missing.", True),
        ("Abort when a source is unavailable.", True),
        ("Pause the review when the source cannot be accessed.", True),
        ("Stop the audit when you cannot access a source.", True),
        ("A requested source cannot be accessed, so stop the audit.", True),
        ("Stop the audit for an incomplete corpus.", True),
        ("Halt the audit for an ambiguous source.", True),
        ("Pause the audit for an unusable source.", True),
        ("Missing sources are not a reason to stop.", False),
        ("Do not automatically stop when sources are missing.", False),
        ("Missing sources do not require the audit to stop.", False),
        ("Missing sources do not by themselves require the audit to stop.", False),
        ("If sources are unavailable, continue with accessible sources.", False),
        ("Missing sources alone must not stop the audit.", False),
    ],
)
def test_missing_source_stop_guard(text: str, expected: bool) -> None:
    assert stops_for_missing_sources(text) is expected


def test_plagiarism_skill_defines_critical_decisions() -> None:
    text = normalized_skill_text()

    assert re.search(r"\bask\b[^.]{0,100}\btarget\b[^.]{0,100}\bonly when\b[^.]{0,50}\bmissing\b", text)
    assert re.search(r"\bask\b[^.]{0,100}\bcorpus\b[^.]{0,100}\bonly when\b[^.]{0,50}\bmissing\b", text)
    assert re.search(r"\b(?:all|every) supported document formats?\b", text)
    assert re.search(r"\b(?:all|every) supported corpus routes?\b", text)
    assert re.search(r"\braw\b[^.]{0,100}\badjusted\b[^.]{0,100}\bseparate\b", text)
    assert all(term in text for term in ("candidate generation", "verified passages", "interpretation"))
    assert re.search(r"\bdo not\b[^.]{0,100}\bsubstantive citation-support judgments?\b", text)
    assert re.search(r"\bnever edit\b[^.]{0,100}\btarget\b[^.]{0,120}\bauthori[sz]", text)
    assert re.search(r"\bnever\b[^.]{0,100}\bsearch\b[^.]{0,60}\bopen web\b[^.]{0,120}\bauthori[sz]", text)


def test_plagiarism_skill_defers_nonessential_intake_questions() -> None:
    text = normalized_skill_text()

    assert re.search(
        r"when both[^.]{0,80}target[^.]{0,80}source corpus[^.]{0,80}missing"
        r"[^.]{0,100}ask only[^.]{0,80}target document or file"
        r"[^.]{0,80}source corpus",
        text,
    )
    assert all(
        prohibited in text
        for prohibited in (
            "no scope or section question",
            "no metric or exclusion question",
            "no provider option",
            "no explanation or assurance until both are supplied",
        )
    )
    assert "use the complete target by default, so no scope question is needed" in text


def test_plagiarism_skill_defines_semantic_both_missing_response_contract() -> None:
    normalized = normalized_skill_text()

    assert re.search(
        r"when both[^.]{0,100}missing[^.]{0,120}ask only[^.]{0,120}target"
        r"[^.]{0,120}source corpus",
        normalized,
    )
    assert all(
        term in normalized
        for term in (
            "no scope or section question",
            "no metric or exclusion question",
            "no provider option",
            "no explanation or assurance",
            "emit no commentary or preface",
        )
    )
    assert "use this response verbatim" not in normalized


def test_plagiarism_runtime_is_synchronized() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/sync_skill_runtime.py",
            "--check",
            "skills/plagiarism-audit",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("suffix", SUPPORTED_SUFFIXES)
def test_source_corpus_documents_supported_extensions(suffix: str) -> None:
    text = source_corpus_text()
    assert re.search(rf"(?<!\w){re.escape(suffix)}(?!\w)", text), suffix


@pytest.mark.parametrize(
    ("route", "capability"),
    [
        (
            r"local\s+files?\s+(?:and|or)\s+director(?:y|ies)",
            r"(?:use\s+`?--source`?|searched recursively)",
        ),
        (r"\bzotero\b", r"read-only local zotero desktop api"),
        (r"\bmendeley\s+exports?\b", r"accessible (?:local )?attachments?"),
        (r"\bbibtex\b", r"use\s+`?--bibliography`?"),
        (r"\bbiblatex\b", r"use\s+`?--bibliography`?"),
        (r"\bris\b", r"use\s+`?--bibliography`?"),
        (r"\bcsl\s+json\b", r"use\s+`?--bibliography`?"),
        (
            r"\bembedded\s+(?:references\s*[/&]\s*)?bibliograph(?:y|ies)\b",
            r"(?:inspect|supply)[^.]{0,100}(?:entries|records)",
        ),
        (r"\bsource-manifest\.csv\b", r"use\s+`?--manifest`?"),
    ],
)
def test_source_corpus_documents_affirmative_generic_routes(
    route: str, capability: str
) -> None:
    assert documents_affirmative_corpus_route(source_corpus_text(), route, capability), route


@pytest.mark.parametrize(
    ("text", "route", "capability"),
    [
        (
            "- Local files and directories are unsupported.",
            r"local\s+files?\s+(?:and|or)\s+director(?:y|ies)",
            r"unsupported",
        ),
        (
            "- Mendeley exports cannot use accessible attachments.",
            r"\bmendeley\s+exports?\b",
            r"use accessible attachments",
        ),
    ],
)
def test_affirmative_corpus_route_guard_rejects_negated_claims(
    text: str, route: str, capability: str
) -> None:
    assert not documents_affirmative_corpus_route(text, route, capability)


def test_source_corpus_limits_mendeley_to_exports_and_accessible_attachments() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"mendeley exports?[^.]{0,180}accessible (?:local )?attachments?", text
    )
    assert re.search(
        r"mendeley[^.]{0,180}(?:does not|no)[^.]{0,120}private[^.]{0,80}database",
        text,
    )
    assert re.search(r"mendeley[^.]{0,220}(?:does not|no)[^.]{0,120}cloud api", text)


def test_source_corpus_keeps_mapping_ambiguity_in_main_manifest() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"(?:mapping )?ambiguit(?:y|ies)[^.]{0,180}source-manifest\.csv", text
    )
    assert re.search(r"candidate source ids?", text)
    assert re.search(
        r"(?:do not|no)[^.]{0,100}separate[^.]{0,100}"
        r"(?:unresolved|ambiguous|ambiguity)[^.]{0,80}(?:artifact|file|manifest)",
        text,
    )


def test_source_corpus_discloses_current_manifest_cli_mapping_limits() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"current manifest cli[^.]{0,160}(?:supplies|passes)[^.]{0,100}"
        r"extracted citation identifiers?[^.]{0,100}(?:to|into)[^.]{0,80}mapping",
        text,
    )
    assert re.search(
        r"keyless visible citations?[^.]{0,120}visible:<hash>[^.]{0,120}remain unresolved",
        text,
    )
    assert re.search(
        r"title-author-year[^.]{0,120}title[^.]{0,120}filename[^.]{0,160}"
        r"available[^.]{0,100}common mapping precedence",
        text,
    )
    assert re.search(
        r"current manifest cli path[^.]{0,160}(?:does not|cannot|not)[^.]{0,100}"
        r"automatically exercise[^.]{0,160}(?:imported|source) metadata",
        text,
    )


def test_source_corpus_defines_precise_filename_mapping_semantics() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert "filename or document metadata" not in text
    assert re.search(
        r"filename[^.]{0,120}case-insensitive[^.]{0,100}basename[^.]{0,120}"
        r"supplied filename inputs?[^.]{0,120}`local_files`",
        text,
    )


def test_source_corpus_fail_on_missing_is_only_for_requested_strict_automation() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"default[^.]{0,120}(?:partial-tolerant|partial tolerant|continues?[^.]{0,80}gaps?)",
        text,
    )
    assert re.search(
        r"--fail-on-missing[^.]{0,180}(?:only|solely)[^.]{0,100}"
        r"(?:user-requested|user requested)[^.]{0,80}strict automation",
        text,
    )
    assert all(
        phrase in text
        for phrase in (
            "zero expected rows",
            "unresolved",
            "ambiguous",
            "missing its artifact",
            "unusable extraction status or text quality",
            "row-based runtime conditions",
            "`coverage_percent` as `null`",
        )
    )


def test_source_corpus_documents_bundled_runtime_and_conversion_dependencies() -> None:
    text = source_corpus_text()

    assert "imports its bundled sibling `source_checker` runtime" in text
    assert "discoverable `soffice` executable" in text
    assert "discoverable `pdftotext` executable" in text
    assert "falls back to `pypdf`" in text


def test_source_corpus_preserves_non_enriched_zotero_states_and_attachment_identity() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert all(state in text for state in ("ambiguity", "unavailability", "no match", "error"))
    assert "set `mapping_rule` to `zotero-live`" in text
    assert "retain a status diagnostic in `conflicts`" in text
    assert "`attachment_unresolved` outcome contains valid bibliographic identity" in text
    assert "retain its source record" in text
    assert "record the absent attachment through extraction or artifact status" in text


def test_source_corpus_defines_continuation_decision_table() -> None:
    rows = {
        tuple(" ".join(cell.lower().split()) for cell in line.strip().strip("|").split("|"))
        for line in source_corpus_text().splitlines()
        if line.lstrip().startswith("|")
    }
    expected_rows = {
        (
            "readable target, expected sources > 0, and all expected sources analyzed",
            "complete expected-source-set coverage audit",
        ),
        (
            "readable target and at least one expected source analyzed",
            "partial audit with quantitative observed similarity",
        ),
        (
            "readable target and zero sources analyzed",
            "diagnostic coverage report; no similarity percentage",
        ),
        (
            "unreadable target",
            "stop substantive analysis; diagnostic report",
        ),
    }

    assert expected_rows <= rows


def test_source_corpus_defines_locator_and_extraction_disclosure() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"non-pdf[^.]{0,160}heading[^.]{0,100}paragraph[^.]{0,100}block locators?",
        text,
    )
    assert re.search(
        r"pdf page locators?[^.]{0,160}(?:preferred|prefer)[^.]{0,100}exact page evidence",
        text,
    )
    assert re.search(r"disclose[^.]{0,120}extraction quality", text)
    assert re.search(r"disclose[^.]{0,120}conversion", text)


def test_source_corpus_discloses_jsonl_cache_context_limits() -> None:
    text = " ".join(source_corpus_text().lower().split())

    assert re.search(
        r"direct extractors?[^.]{0,120}(?:populate|provide)[^.]{0,120}"
        r"headings?[^.]{0,100}conversion context",
        text,
    )
    assert re.search(
        r"jsonl cache[^.]{0,160}(?:omits|does not (?:store|preserve))[^.]{0,120}"
        r"`?textblock\.heading`?[^.]{0,100}`?conversion_note`?",
        text,
    )
    assert re.search(
        r"cached `?locator_type`?[^.]{0,100}`?locator_value`?[^.]{0,100}remain available",
        text,
    )
    assert re.search(
        r"heading[^.]{0,100}conversion context[^.]{0,160}"
        r"(?:direct re-extraction|authoritative-source inspection)",
        text,
    )


def test_source_corpus_uses_windows_safe_quoted_cli_examples() -> None:
    text = source_corpus_text()
    manifest_command = (
        'python "<skill-dir>/scripts/source_corpus.py" manifest '
        '--target "<target-document>" --source "<source-directory>" '
        '--bibliography "<references.bib>" '
        '--output "<audit-dir>/source-manifest.csv" '
        '--cache-dir "<audit-dir>/text-cache"'
    )
    cache_command = (
        'python "<skill-dir>/scripts/source_corpus.py" cache '
        '--manifest "<audit-dir>/source-manifest.csv" '
        '--cache-dir "<audit-dir>/text-cache" '
        '--output "<audit-dir>/source-manifest.csv"'
    )

    assert manifest_command in text
    assert cache_command in text


def test_metrics_define_word_populations_and_score_variants() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert re.search(
        r"analyzable target words? (?:are|means?)[^.]{0,180}selected target scope"
        r"[^.]{0,180}(?:extract|token)",
        text,
    )
    assert re.search(
        r"matched target words? (?:are|means?)[^.]{0,180}analyzable target words?"
        r"[^.]{0,180}(?:verified|retained)[^.]{0,100}(?:match|overlap)",
        text,
    )
    assert re.search(r"\braw overall similarity\b", text)
    assert re.search(r"\badjusted overall similarity\b", text)


@pytest.mark.parametrize(
    "formula",
    [
        (
            "observed overall similarity = unique target words matched in analyzed corpus / "
            "analyzable target words * 100"
        ),
        (
            "observed per-source similarity = unique union of target positions matched to that analyzed source / "
            "analyzable target words * 100"
        ),
        (
            "match-type coverage = unique union of target positions in that verified category / "
            "analyzable target words * 100"
        ),
        "corpus coverage = analyzed expected sources / all expected sources * 100",
    ],
)
def test_metrics_define_required_similarity_and_coverage_formulas(formula: str) -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())
    assert formula in text


def test_metrics_define_exclusions_overlap_and_unique_overall_counting() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"raw and adjusted[^.]{0,160}differ only[^.]{0,140}documented exclusions", text
    )
    assert re.search(
        r"per-source[^.]{0,140}(?:and|/) category percentages?[^.]{0,140}overlap", text
    )
    assert re.search(
        r"overall[^.]{0,160}(?:word|target word)[^.]{0,100}(?:counted|counts?) once", text
    )


def test_metrics_define_semantic_positions_and_unique_source_category_unions() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert re.search(
        r"semantic or cross-language matches[^.]{0,180}target words[^.]{0,180}"
        r"smallest verified aligned target span",
        text,
    )
    assert re.search(
        r"eligible[^.]{0,120}per-source[^.]{0,80}category[^.]{0,80}overall unions", text
    )
    assert "unique union of target positions matched to that analyzed source" in text
    assert "unique union of target positions in that verified category" in text


def test_metrics_require_quantitative_results_for_any_analyzed_source_subset() -> None:
    assert requires_partial_corpus_quantification(reference_text("metrics-and-rules.md"))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            (
                "When at least one source is analyzable, the report must compute quantitative "
                "similarity results."
            ),
            True,
        ),
        (
            (
                "When one or more expected sources are analyzable, quantitative metrics are "
                "required to be computed."
            ),
            True,
        ),
        (
            (
                "When at least one source is analyzable, the report may compute quantitative "
                "similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, the report must not compute quantitative "
                "similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, the report is not required to compute "
                "quantitative similarity."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, quantitative similarity reporting is "
                "not mandatory."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, quantitative similarity reporting is "
                "mandatory."
            ),
            True,
        ),
        (
            (
                "When at least one source is analyzable, it is mandatory that the report does "
                "not compute quantitative similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, the report must avoid computing "
                "quantitative similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, the report must refrain from computing "
                "quantitative similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, it is mandatory that the report avoid "
                "computing quantitative similarity results."
            ),
            False,
        ),
        (
            (
                "When at least one source is analyzable, it is mandatory that the report refrain "
                "from computing quantitative similarity results."
            ),
            False,
        ),
        (
            "When zero sources are analyzable, the report must compute quantitative results.",
            False,
        ),
    ],
)
def test_partial_corpus_quantification_guard(text: str, expected: bool) -> None:
    assert requires_partial_corpus_quantification(text) is expected


def test_metrics_state_canonical_affirmative_partial_quantification_contract() -> None:
    text = normalized_reference_text("metrics-and-rules.md")
    assert (
        "when at least one expected source has been analyzed, the report must compute quantitative "
        "similarity results over the analyzed source subset."
    ) in text


def test_metrics_scope_partial_results_without_estimating_unseen_sources() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"partial corpus[^.]{0,180}prefix[^.]{0,100}(?:metric|label)[^.]{0,100}`?observed`?",
        text,
    )
    assert re.search(r"partial corpus[^.]{0,240}within the analyzed corpus", text)
    assert re.search(
        r"(?:do not|never|must not)[^.]{0,140}(?:estimate|extrapolate)[^.]{0,160}"
        r"(?:unseen|unavailable|unanalyzed)[^.]{0,80}(?:source|corpus)[^.]{0,60}similarity",
        text,
    )


def test_complete_scope_is_separate_from_source_text_coverage() -> None:
    metrics = normalized_reference_text("metrics-and-rules.md")
    report = normalized_reference_text("report-template.md")

    assert "expected-source set is non-empty" in metrics
    assert "complete describes expected-source-set coverage only" in metrics
    assert "report partial source-text coverage separately" in metrics
    assert "source-text coverage: [complete/partial/unknown" in report


def test_metrics_define_zero_raw_and_adjusted_denominator_outcomes() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert re.search(
        r"raw analyzable target[- ]word denominator[^.]{0,120}(?:is|equals?) zero"
        r"[^.]{0,180}diagnostic coverage and method report[^.]{0,160}"
        r"no similarity percentages?",
        text,
    )
    assert re.search(
        r"adjusted denominator[^.]{0,100}(?:is|equals?) zero[^.]{0,160}raw"
        r"[^.]{0,80}(?:remain|reported)[^.]{0,180}"
        r"unavailable \(zero adjusted denominator\)",
        text,
    )
    assert re.search(
        r"unavailable \(zero adjusted denominator\)[^.]{0,120}(?:never|not)[^.]{0,80}0%",
        text,
    )


def test_report_exposes_both_zero_denominator_states_without_zero_percentages() -> None:
    text = " ".join(reference_text("report-template.md").lower().split())

    assert re.search(
        r"zero raw analyzable target[- ]word denominator[^.]{0,180}"
        r"diagnostic coverage and method report[^.]{0,140}no similarity percentages?",
        text,
    )
    assert "unavailable (zero adjusted denominator)" in text
    assert re.search(
        r"unavailable \(zero adjusted denominator\)[^.]{0,120}(?:never|not)[^.]{0,80}0%",
        text,
    )


def test_match_only_exclusions_recompute_union_of_target_token_positions() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert re.search(
        r"matched target words? (?:are|means?)[^.]{0,120}target token positions?", text
    )
    assert re.search(
        r"match-only exclusions?[^.]{0,160}match relationships? first[^.]{0,180}"
        r"recompute[^.]{0,100}union[^.]{0,100}retained verified target positions?",
        text,
    )
    assert re.search(
        r"target token[^.]{0,120}leaves?[^.]{0,100}overall numerator[^.]{0,180}"
        r"only when[^.]{0,120}no retained verified match remains",
        text,
    )


def test_metrics_include_compact_overlapping_match_arithmetic_fixture() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert "source a verified positions = {2, 3, 4}" in text
    assert "source b verified positions = {4, 5}" in text
    assert "raw union = {2, 3, 4, 5} = 4 / 10 = 40%" in text
    assert "after excluding source a relationship = {4, 5} = 2 / 10 = 20%" in text
    assert re.search(r"position 4[^.]{0,100}remains[^.]{0,100}source b", text)


def test_metrics_separate_global_score_union_from_relationship_evidence_units() -> None:
    metrics = normalized_reference_text("metrics-and-rules.md")
    report = " ".join(reference_text("report-template.md").lower().split())

    assert re.search(
        r"overall similarity[^.]{0,180}global union[^.]{0,140}"
        r"verified target[- ]token positions?[^.]{0,120}counted once",
        metrics,
    )
    assert re.search(
        r"retained evidence passage (?:is|means?)[^.]{0,180}verified relationship"
        r"[^.]{0,120}target passage[^.]{0,120}source passage",
        metrics,
    )
    assert re.search(
        r"grouping key[^.]{0,260}canonical source artifact and version[^.]{0,260}"
        r"coherent source block or span",
        metrics,
    )
    assert re.search(
        r"merge evidence only[^.]{0,140}both the target spans and the source spans"
        r"[^.]{0,160}coherent and contiguous or overlapping",
        metrics,
    )
    for key_part in (
        "canonical source artifact and version",
        "match type/category",
        "attribution group",
        "target document block",
        "coherent source block or span",
    ):
        assert key_part in metrics
    assert re.search(
        r"same target positions?[^.]{0,140}multiple retained-evidence rows"
        r"[^.]{0,140}counted once[^.]{0,80}overall",
        metrics,
    )
    assert "retained evidence passages" in report
    assert "unique target blocks" in report


def test_metrics_include_multi_source_score_and_evidence_example() -> None:
    text = normalized_reference_text("metrics-and-rules.md")

    assert "evidence row a = (source a, identical match, not cited or quoted, block t1)" in text
    assert "evidence row b = (source b, identical match, not cited or quoted, block t1)" in text
    assert re.search(
        r"position 4[^.]{0,100}both evidence rows[^.]{0,100}once[^.]{0,80}raw union",
        text,
    )


def test_retained_evidence_is_verified_and_candidates_are_excluded() -> None:
    metrics = normalized_reference_text("metrics-and-rules.md")
    report = reference_text("report-template.md")
    normalized_report = " ".join(report.lower().split())

    assert re.search(
        r"retained evidence passages?[^.]{0,120}(?:must be|are) verified", metrics
    )
    assert re.search(
        r"(?:partial|unverified)[^.]{0,120}candidate diagnostics?[^.]{0,180}"
        r"excluded[^.]{0,100}(?:numerators?|retained evidence)",
        metrics,
    )
    assert "- Verification status: verified" in report
    assert "[verified/partial/unverified]" not in normalized_report
    assert "### Candidate diagnostics (excluded)" in report
    assert re.search(
        r"candidate diagnostics[^.]{0,180}(?:partial|unverified)[^.]{0,180}"
        r"excluded[^.]{0,100}(?:numerators?|retained evidence)",
        normalized_report,
    )


def test_metrics_preserve_public_vocabulary_without_proprietary_equivalence() -> None:
    text = " ".join(reference_text("metrics-and-rules.md").lower().split())

    assert re.search(
        r"repository labels?[^.]{0,180}adapted[^.]{0,180}copyleaks", text
    )
    assert re.search(r"turnitin-style[^.]{0,180}(?:not cited or quoted|missing quotations)", text)
    assert re.search(
        r"(?:do not|never|must not)[^.]{0,180}(?:reproduce|replicate)[^.]{0,120}"
        r"proprietary (?:algorithm|detector)",
        text,
    )
    assert "safeassign-derived contextual review labels" in text
    assert "accessed on 2026-09-23" in text
    assert "do not estimate the probability of plagiarism" in text
    assert "not decision thresholds" in text


def test_report_requires_complete_or_partial_label_for_every_percentage() -> None:
    assert requires_scope_label_for_every_percentage(reference_text("report-template.md"))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Label every reported percentage either Complete or Partial.", True),
        ("Each percentage must be labelled complete or partial.", True),
        ("Some percentages may be labelled complete or partial.", False),
        ("Every percentage must not be labelled complete or partial.", False),
        (
            "There is no requirement to label every reported percentage Complete or Partial.",
            False,
        ),
        (
            "It is not mandatory to label every reported percentage Complete or Partial.",
            False,
        ),
        ("It is mandatory to label every reported percentage Complete or Partial.", True),
        (
            (
                "It is mandatory that the report does not label every reported percentage "
                "Complete or Partial."
            ),
            False,
        ),
        (
            "The report must avoid labelling every reported percentage Complete or Partial.",
            False,
        ),
        (
            "The report must refrain from labelling every reported percentage Complete or Partial.",
            False,
        ),
        (
            (
                "It is mandatory that the report avoid labelling every reported percentage "
                "Complete or Partial."
            ),
            False,
        ),
        (
            (
                "It is mandatory that the report refrain from labelling every reported percentage "
                "Complete or Partial."
            ),
            False,
        ),
        ("Label every result complete or partial.", False),
    ],
)
def test_percentage_scope_label_guard(text: str, expected: bool) -> None:
    assert requires_scope_label_for_every_percentage(text) is expected


def test_report_states_canonical_affirmative_percentage_scope_contract() -> None:
    text = normalized_reference_text("report-template.md")
    assert "label every reported percentage either complete or partial." in text


def test_report_sections_follow_required_evidence_order() -> None:
    headings = re.findall(r"^##\s+\d+\.\s+(.+)$", reference_text("report-template.md"), re.MULTILINE)

    assert headings == [
        "Target and corpus coverage",
        "Extraction, method settings, and exclusions",
        "Complete or partial quantitative scorecard",
        "Source-level results",
        "Attribution-group summary",
        "Passage-level parallel evidence",
        "Inaccessible sources needed for broader coverage",
        "Limitations and non-verdict conclusion",
    ]


def first_score_table_columns() -> list[str]:
    """Return normalized columns from the first quantitative score table."""
    scorecard = reference_text("report-template.md").split(
        "## 3. Complete or partial quantitative scorecard", 1
    )[1]
    table_header = next(
        line for line in scorecard.splitlines() if line.startswith("|") and "---" not in line
    )
    return [column.strip().lower() for column in table_header.strip("|").split("|")]


def test_first_score_table_places_corpus_coverage_next_to_observed_similarity() -> None:
    columns = first_score_table_columns()
    coverage_index = next(
        index for index, column in enumerate(columns) if "corpus coverage" in column
    )
    similarity_indices = [
        index
        for index, column in enumerate(columns)
        if "observed" in column and "overall similarity" in column
    ]

    assert similarity_indices
    assert min(abs(coverage_index - index) for index in similarity_indices) == 1


def test_partial_first_score_table_prefixes_adjacent_corpus_coverage_with_observed() -> None:
    columns = first_score_table_columns()
    coverage_index = next(
        index for index, column in enumerate(columns) if "observed corpus coverage (partial)" in column
    )
    similarity_indices = [
        index
        for index, column in enumerate(columns)
        if "observed" in column and "overall similarity" in column
    ]

    assert similarity_indices
    assert min(abs(coverage_index - index) for index in similarity_indices) == 1


def test_category_score_rows_declare_raw_or_adjusted_denominator_basis() -> None:
    report = reference_text("report-template.md")

    assert (
        "| Metric label | Basis | Numerator / denominator | Result and scope label |"
        in report
    )
    assert "[Raw or Adjusted]" in report
    assert "[raw or adjusted analyzable target words]" in report
    assert "Observed [category] coverage (Partial)" in report
    assert "[category] coverage (Complete)" in report


def test_source_table_operationalizes_partial_and_complete_metric_labels() -> None:
    report = reference_text("report-template.md")

    assert "| Scope | Metric label |" in report
    assert "| Partial | Observed per-source similarity |" in report
    assert "| Complete | Per-source similarity |" in report
    assert "Retained evidence passages" in report
    assert "Unique target blocks" in report
    assert "Authoritative-artifact inspection" in report


def test_report_separates_coverage_limit_counts_and_narrows_no_action() -> None:
    report = reference_text("report-template.md")

    for label in (
        "Inaccessible source artifacts",
        "Unusable source extractions",
        "Unresolved source mappings",
        "Unanalyzed expected sources",
    ):
        assert label in report
    assert "The four limitation counts can overlap" in report
    assert "no similarity-related action based on this corpus" in report
    assert "or no action]" not in report
