"""Publication-readiness contracts for the 0.1.0 repository release."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import yaml
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from source_checker.extractors import extract_document

ROOT = Path(__file__).resolve().parents[1]
READABLE_SMOKE_FILENAME = "readable.pdf"
RELEASE_SMOKE_RECORD = "tests/behavior/plagiarism-audit/release-smoke.md"
INSTALLED_SKILL_TRANSCRIPT = (
    "tests/behavior/plagiarism-audit/revised-results/release-installed-skill-smoke.md"
)
CLEAN_COPY_RECEIPT = "tests/behavior/release-clean-copy-verification.md"
ACTIVATION_SCENARIOS = "tests/behavior/activation-scenarios.yaml"
ACTIVATION_RESULTS = "tests/behavior/activation-results.md"
STANDALONE_SKILLS = ("citation-support-audit", "plagiarism-audit")
ACTIVATION_CATEGORIES = ("direct", "indirect", "incomplete", "non-trigger", "edge")
EXPECTED_ACTIVATION_PROMPTS = {
    "citation-support-audit": {
        "direct": (
            "Use Citation Support Audit to verify whether the claims in this paper "
            "are supported by the supplied sources."
        ),
        "indirect": (
            "Check whether each cited source actually supports the nearby claim and "
            "flag claims that need citations."
        ),
        "incomplete": "Check my citations.",
        "non-trigger": (
            "Copyedit this paper for grammar without checking its sources or citations."
        ),
        "edge": (
            "Check citation support using the readable sources, but one cited source "
            "is unavailable."
        ),
    },
    "plagiarism-audit": {
        "direct": (
            "Use Plagiarism Audit to compare this document with the supplied source "
            "corpus."
        ),
        "indirect": (
            "Find close paraphrases, patchwriting, and unattributed textual overlap "
            "against these source files."
        ),
        "incomplete": "Check this for plagiarism.",
        "non-trigger": (
            "Verify whether the cited studies support the paper's causal claims; do "
            "not assess textual similarity."
        ),
        "edge": (
            "Report observed textual overlap against the three readable sources while "
            "a fourth expected source is unavailable."
        ),
    },
}
EXPECTED_SKILL_COMPATIBILITY = (
    "Requires Python 3.11+ and local file access; optional pdftotext for PDF layout "
    "extraction and LibreOffice for legacy DOC conversion."
)
COMMUNITY_FILES = (
    "SECURITY.md",
    "CONTRIBUTING.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/skill_behavior.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/pull_request_template.md",
)
ISSUE_FORM_NAMES = {"bug_report.yml", "skill_behavior.yml"}
ISSUE_TEMPLATE_ROOT = ROOT / ".github" / "ISSUE_TEMPLATE"
SKILLS_REF_SOURCE = (
    "git+https://github.com/agentskills/agentskills.git@"
    "69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
)
SKILLS_REF_INSTALL = f'python -m pip install "skills-ref @ {SKILLS_REF_SOURCE}"'
CHECKOUT_ACTION = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON_ACTION = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_required_community_files_exist() -> None:
    for relative_path in COMMUNITY_FILES:
        assert (ROOT / relative_path).is_file(), relative_path


def issue_form_body_by_id(filename: str) -> dict[str, dict[str, object]]:
    relative_path = f".github/ISSUE_TEMPLATE/{filename}"
    issue_form = yaml.safe_load(read(relative_path))
    assert isinstance(issue_form, dict), relative_path

    for field in ("name", "description"):
        value = issue_form.get(field)
        assert isinstance(value, str) and value.strip(), (relative_path, field)

    body = issue_form.get("body")
    assert isinstance(body, list) and body, (relative_path, "body")
    identified_items = {
        item["id"]: item
        for item in body
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    assert len(identified_items) == sum(
        isinstance(item, dict) and isinstance(item.get("id"), str) for item in body
    ), f"duplicate body ID in {relative_path}"
    return identified_items


def test_issue_forms_are_exactly_the_two_supported_reports() -> None:
    issue_form_names = {
        path.name
        for path in ISSUE_TEMPLATE_ROOT.iterdir()
        if path.suffix in {".yaml", ".yml"} and path.name != "config.yml"
    }

    assert issue_form_names == ISSUE_FORM_NAMES


def test_bug_report_collects_required_reproduction_context() -> None:
    body_by_id = issue_form_body_by_id("bug_report.yml")
    required_types = {
        "version": "input",
        "operating-system": "input",
        "python-version": "input",
        "input-format": "input",
        "corpus-route": "input",
        "reproduction": "textarea",
        "actual-behavior": "textarea",
        "expected-behavior": "textarea",
        "logs": "textarea",
    }

    assert required_types.keys() <= body_by_id.keys()
    for field_id, field_type in required_types.items():
        item = body_by_id[field_id]
        assert item.get("type") == field_type
        assert item.get("validations") == {"required": True}
        attributes = item.get("attributes")
        assert isinstance(attributes, dict)
        assert str(attributes.get("label", "")).strip()

    version = body_by_id["version"]["attributes"]
    reproduction = body_by_id["reproduction"]["attributes"]
    logs = body_by_id["logs"]["attributes"]
    assert isinstance(version, dict)
    assert "version or commit" in " ".join(map(str, version.values())).lower()
    assert isinstance(reproduction, dict)
    assert "minimal synthetic" in " ".join(map(str, reproduction.values())).lower()
    assert isinstance(logs, dict)
    assert "confidential material" in " ".join(map(str, logs.values())).lower()


def test_skill_behavior_report_collects_activation_and_boundary_context() -> None:
    body_by_id = issue_form_body_by_id("skill_behavior.yml")
    required_types = {
        "skill-name": "dropdown",
        "triggering-prompt": "textarea",
        "expected-activation": "textarea",
        "supplied-inputs": "textarea",
        "observed-output": "textarea",
        "expected-boundary": "textarea",
        "corpus-completeness": "dropdown",
        "confidentiality-confirmation": "checkboxes",
    }

    assert required_types.keys() <= body_by_id.keys()
    for field_id, field_type in required_types.items():
        item = body_by_id[field_id]
        assert item.get("type") == field_type
        attributes = item.get("attributes")
        assert isinstance(attributes, dict)
        assert str(attributes.get("label", "")).strip()
        if field_id != "confidentiality-confirmation":
            assert item.get("validations") == {"required": True}

    skill_options = body_by_id["skill-name"]["attributes"]
    corpus_options = body_by_id["corpus-completeness"]["attributes"]
    assert isinstance(skill_options, dict)
    assert skill_options.get("options") == [
        "citation-support-audit",
        "plagiarism-audit",
    ]
    assert isinstance(corpus_options, dict)
    assert corpus_options.get("options") == ["Complete", "Partial", "Unknown"]

    confirmation = body_by_id["confidentiality-confirmation"]
    assert confirmation.get("type") == "checkboxes"
    confirmation_attributes = confirmation.get("attributes")
    assert isinstance(confirmation_attributes, dict)
    confirmation_options = confirmation_attributes.get("options")
    assert isinstance(confirmation_options, list) and len(confirmation_options) == 1
    option = confirmation_options[0]
    assert isinstance(option, dict)
    assert option.get("required") is True
    assert "no confidential documents" in str(option.get("label", "")).lower()


def test_issue_template_configuration_allows_blank_issues_without_contacts() -> None:
    config = yaml.safe_load(read(".github/ISSUE_TEMPLATE/config.yml"))

    assert config == {"blank_issues_enabled": True, "contact_links": []}


def test_security_policy_names_private_reporting_and_project_risks() -> None:
    text = " ".join(read("SECURITY.md").lower().split())

    for required_text in (
        "private vulnerability reporting",
        "private vulnerability reporting must be enabled before public release",
        "do not open a public issue for a suspected vulnerability.",
        "if private vulnerability reporting is unavailable",
        "do not disclose vulnerability details",
        "metadata-free public contact request",
        "enable or provide a private channel",
        "without naming affected documents or inputs",
        "reproduction details",
        "prompt injection",
        "path traversal",
        "unintended file writes",
        "unsafe subprocess invocation",
        "embedded-code execution",
        "network access outside the documented local zotero route",
        "dependency vulnerabilities",
        "disclosure of target or source contents",
        "audit outputs are evidence aids",
    ):
        assert required_text in text
    assert "macro" in text
    assert "not security, legal, plagiarism, or misconduct verdicts" in text


def test_contributing_documents_complete_local_validation_and_runtime_sync() -> None:
    text = read("CONTRIBUTING.md")
    lowered = " ".join(text.lower().split())

    assert "python 3.11 or newer" in lowered
    assert 'python -m pip install -e ".[dev]"' in text
    assert "failing test before implementation" in lowered
    assert "citation-support-audit" in lowered
    assert "claim-source support" in lowered
    assert "plagiarism-audit" in lowered
    assert "source-bounded textual similarity" in lowered
    assert "does not make citation-support judgments" in lowered
    assert "`src/source_checker` is the authoritative implementation" in lowered
    assert "runtime synchronization" in lowered
    assert "both skills" in lowered
    assert "only synthetic fixtures" in lowered
    assert "private vulnerability reporting" in lowered
    for security_prerequisite in (
        "private vulnerability reporting must be enabled before public release",
        "do not disclose vulnerability details",
        "metadata-free public contact request",
        "enable or provide a private channel",
    ):
        assert security_prerequisite in lowered
    assert SKILLS_REF_INSTALL in text
    assert text.index(SKILLS_REF_INSTALL) < text.index("python -m pytest -q")
    for command in (
        "python -m pytest -q",
        "python -m ruff check .",
        "python -m pyright",
        "skills-ref validate skills/citation-support-audit",
        "skills-ref validate skills/plagiarism-audit",
        "python tools/sync_skill_runtime.py --check skills/citation-support-audit",
        "python tools/sync_skill_runtime.py --check skills/plagiarism-audit",
    ):
        assert command in text


def test_pull_request_template_requires_release_hardening_evidence() -> None:
    text = read(".github/pull_request_template.md")
    lowered = text.lower()

    for heading in (
        "## Summary",
        "## Affected skill and runtime",
        "## Test evidence",
        "## Security and privacy impact",
        "## Documentation impact",
    ):
        assert heading in text

    checkboxes = [
        line.lower() for line in text.splitlines() if line.startswith("- [ ] ")
    ]
    assert any("synchron" in line and "runtime" in line for line in checkboxes)
    assert any("synthetic" in line and "only" in line for line in checkboxes)
    assert "## checklist" in lowered


def test_standalone_skill_bundles_are_release_self_describing() -> None:
    root_license = (ROOT / "LICENSE").read_bytes()

    for skill_name in STANDALONE_SKILLS:
        skill_root = ROOT / "skills" / skill_name
        sections = (skill_root / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
        assert len(sections) == 3 and not sections[0].strip()
        frontmatter = yaml.safe_load(sections[1])

        assert frontmatter["license"] == "MIT; see LICENSE.txt"
        assert frontmatter["compatibility"] == EXPECTED_SKILL_COMPATIBILITY
        assert frontmatter["metadata"] == {
            "author": "MicheleGarbelotto",
            "version": "0.1.0",
        }
        assert (skill_root / "LICENSE.txt").read_bytes() == root_license


def write_readable_synthetic_pdf(path: Path) -> None:
    """Create a one-page PDF with enough real text to pass the quality gate."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)  # pyright: ignore[reportPrivateUsage]
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_reference})}
    )
    lines = (
        "First page block one. This synthetic readable document contains sufficient",
        "additional neutral prose to exceed the extraction quality threshold while",
        "preserving a single verified matching span for this release smoke",
        "examination and providing no further lexical parallels whatsoever.",
    )
    stream = DecodedStreamObject()
    commands = "BT /F1 12 Tf 72 720 Td " + " ".join(
        f"({line}) Tj 0 -18 Td" for line in lines
    ) + " ET"
    stream.set_data(commands.encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(  # pyright: ignore[reportPrivateUsage]
        stream
    )
    with path.open("wb") as handle:
        writer.write(handle)


def test_readme_documents_both_skills_and_their_separate_boundaries() -> None:
    text = read("README.md")
    lowered = text.lower()

    assert "`citation-support-audit`" in text
    assert "`plagiarism-audit`" in text
    assert "claim-source support" in lowered
    assert "source-bounded textual similarity" in lowered
    assert "does not make citation-support judgments" in lowered


def test_readme_documents_installation_dependencies_and_validation() -> None:
    text = read("README.md")
    lowered = text.lower()
    normalized = " ".join(lowered.split())
    validator_requirement = (
        "skills-ref @ git+https://github.com/agentskills/agentskills.git@"
        "69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
    )

    assert "complete repository" in lowered
    assert "individual skill" in lowered
    for dependency in ("beautifulsoup4", "python-docx", "pypdf"):
        assert dependency in text
    for executable in ("pdftotext", "soffice"):
        assert executable in text
    assert validator_requirement in text
    assert "external verification tool" in lowered
    assert "not a project dependency" in normalized
    for skill in ("citation-support-audit", "plagiarism-audit"):
        assert f"skills-ref validate skills/{skill}" in text
        assert f"sync_skill_runtime.py --check skills/{skill}" in text
    assert "quick_validate.py" not in lowered
    assert ".codex\\skills\\.system\\skill-creator" not in lowered


def test_readme_documents_portable_skill_installation_and_execution_modes() -> None:
    text = read("README.md")
    lowered = text.lower()
    normalized = " ".join(lowered.split())

    for expected in (
        "windows powershell",
        "macos and linux",
        "single top-level skill directory",
        "agent skills-compatible",
        "hosted environment",
        "local zotero",
        "untrusted evidence",
        "security.md",
        "persistent project artifacts",
        "system temporary directory",
        "libreoffice may update its own user profile",
        "source-manifest.csv",
        "text-cache/",
        "tool calls",
        "network access",
        "command execution",
        "scope expansion",
    ):
        assert expected in normalized
    assert "$HOME/.codex/skills" in text
    assert "the runtime writes only" not in normalized


def test_public_release_docs_do_not_contain_absolute_user_profile_paths() -> None:
    public_docs = (
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        *(ROOT / "skills").glob("**/*.md"),
        *(ROOT / "skills").glob("**/*.yaml"),
    )
    profile_path = re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s`]+", re.IGNORECASE)

    for path in public_docs:
        assert not profile_path.search(path.read_text(encoding="utf-8")), path.relative_to(ROOT)


def test_all_tracked_public_text_is_free_of_local_user_paths() -> None:
    public_text = (
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "LICENSE",
        ROOT / "pyproject.toml",
        ROOT / "CITATION.cff",
        *(path for path in (ROOT / "docs").rglob("*") if path.is_file()),
        *(path for path in (ROOT / "skills").rglob("*") if path.suffix in {".md", ".yaml"}),
        *(path for path in (ROOT / "tests").rglob("*.py") if path.is_file()),
        *(path for path in (ROOT / "tests" / "behavior").rglob("*") if path.is_file()),
    )
    profile_path = re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s`]+", re.IGNORECASE)

    for path in public_text:
        assert not profile_path.search(path.read_text(encoding="utf-8")), path.relative_to(ROOT)


def test_all_tracked_public_text_is_free_of_personal_gmail_addresses() -> None:
    public_text = (
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "LICENSE",
        ROOT / "pyproject.toml",
        ROOT / "CITATION.cff",
        *(path for path in (ROOT / "docs").rglob("*") if path.is_file()),
        *(path for path in (ROOT / "skills").rglob("*") if path.suffix in {".md", ".yaml"}),
        *(path for path in (ROOT / "tests" / "behavior").rglob("*") if path.is_file()),
    )
    personal_gmail = re.compile(
        r"\b[A-Z0-9._%+-]+@gmail\.com\b",
        re.IGNORECASE,
    )

    for path in public_text:
        assert not personal_gmail.search(path.read_text(encoding="utf-8")), path.relative_to(ROOT)


def test_public_behavior_evidence_has_no_internal_host_provenance() -> None:
    behavior_root = ROOT / "tests" / "behavior"
    public_evidence = (
        path
        for path in behavior_root.rglob("*")
        if path.suffix.lower() in {".md", ".json", ".yaml", ".yml"}
    )
    forbidden_literals = (
        "<oai-mem-citation>",
        "MEMORY.md",
        "<rollout_ids>",
        "/root/task",
        r"%USERPROFILE%\Documents\TesiUNIPD",
        r".codex\sessions",
        ".codex/sessions",
    )
    opaque_evidence_id = re.compile(
        r"\b01[a-f0-9]{6,}-[a-f0-9-]{20,}\b",
        re.IGNORECASE,
    )
    rollout_filename = re.compile(
        r"rollout-\d{4}-\d{2}-\d{2}[^\s`\"]+\.jsonl",
        re.IGNORECASE,
    )

    for path in public_evidence:
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(ROOT)
        for literal in forbidden_literals:
            assert literal not in text, (relative_path, literal)
        assert not opaque_evidence_id.search(text), relative_path
        assert not rollout_filename.search(text), relative_path


def test_public_behavior_evidence_is_self_describing() -> None:
    readmes = (
        "tests/behavior/plagiarism-audit/baseline-results/README.md",
        "tests/behavior/plagiarism-audit/revised-results/README.md",
    )

    for readme in readmes:
        text = " ".join(read(readme).lower().split())
        assert "frozen public evaluation evidence" in text, readme
        assert "host-internal session logs are not distributed" in text, readme


def load_activation_scenarios() -> dict[str, dict[str, dict[str, object]]]:
    document = yaml.safe_load(read(ACTIVATION_SCENARIOS))

    assert isinstance(document, dict)
    assert document.get("schema_version") == 1
    assert document.get("non_trigger_definition") == (
        "The named suite skill must not activate; another skill may be the correct "
        "route when the prompt explicitly requests that other workflow."
    )
    skills = document.get("skills")
    assert isinstance(skills, dict)
    return skills


def test_activation_scenario_schema_has_exact_skill_category_and_field_contract() -> None:
    skills = load_activation_scenarios()

    assert set(skills) == set(STANDALONE_SKILLS)
    for skill_name, scenarios in skills.items():
        assert set(scenarios) == set(ACTIVATION_CATEGORIES), skill_name
        sibling = next(name for name in STANDALONE_SKILLS if name != skill_name)
        for category, scenario in scenarios.items():
            assert set(scenario) == {
                "prompt",
                "expected_activation",
                "requestable_missing_inputs",
                "forbidden_substitution",
            }, (skill_name, category)
            assert scenario["prompt"] == EXPECTED_ACTIVATION_PROMPTS[skill_name][category]
            expected_activation = skill_name
            expected_forbidden_substitution = sibling
            if category == "non-trigger":
                expected_activation = "none"
            if (skill_name, category) == ("plagiarism-audit", "non-trigger"):
                expected_activation = "citation-support-audit"
                expected_forbidden_substitution = "none"
            assert scenario["expected_activation"] == expected_activation
            missing_inputs = scenario["requestable_missing_inputs"]
            assert isinstance(missing_inputs, list)
            assert all(
                isinstance(item, str) and item.strip() for item in missing_inputs
            )
            assert (
                scenario["forbidden_substitution"]
                == expected_forbidden_substitution
            )


def test_current_activation_scenarios_use_current_skill_names() -> None:
    text = read(ACTIVATION_SCENARIOS)

    assert "plagiarism-audit" in text
    assert "plagiarism-checker" not in text


def test_frozen_plagiarism_scenarios_match_manifest_record() -> None:
    manifest = json.loads(
        read("tests/behavior/plagiarism-audit/revised-results/run-manifest.json")
    )
    scenario_record = manifest["scenario_file"]
    scenario_bytes = (ROOT / scenario_record["path"]).read_bytes()

    assert len(scenario_bytes) == scenario_record["bytes"]
    assert hashlib.sha256(scenario_bytes).hexdigest() == scenario_record["sha256"]


def test_frozen_plagiarism_scenarios_are_lf_stable_in_git_archives() -> None:
    attributes = read(".gitattributes").splitlines()

    assert (
        "tests/behavior/plagiarism-audit/scenarios.yaml text eol=lf" in attributes
    )


def parse_activation_result_sections() -> dict[tuple[str, str], str]:
    text = read(ACTIVATION_RESULTS)
    headings = list(
        re.finditer(
            r"(?m)^## (citation-support-audit|plagiarism-audit) / "
            r"(direct|indirect|incomplete|non-trigger|edge)$",
            text,
        )
    )
    sections: dict[tuple[str, str], str] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        key = (heading.group(1), heading.group(2))
        assert key not in sections
        sections[key] = text[heading.end() : end]
    return sections


def activation_result_field(section: str, field: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(field)}: (.+)$", section)

    assert match is not None, field
    return match.group(1).strip().strip("`")


def parse_activation_public_record(section: str) -> tuple[str, set[str]]:
    fenced_blocks = re.findall(r"```text\n(.*?)\n```", section, re.DOTALL)
    assert len(fenced_blocks) == 1
    block = fenced_blocks[0]
    assert block.count("PUBLIC_RECORD") == 1
    assert block.count("selected_skill:") == 1
    assert block.count("missing_inputs_requested:") == 1
    record = re.search(
        r"(?m)^PUBLIC_RECORD\n"
        r"selected_skill: ([^\n]+)\n"
        r"missing_inputs_requested: ([^\n]+)$",
        block,
    )
    assert record is not None
    assert block[record.start() :].splitlines() == [
        "PUBLIC_RECORD",
        f"selected_skill: {record.group(1)}",
        f"missing_inputs_requested: {record.group(2)}",
    ]
    selected_skill = record.group(1).strip()
    missing_inputs = record.group(2).strip()
    if missing_inputs == "none":
        return selected_skill, set()
    return selected_skill, {
        item.strip() for item in missing_inputs.split(",") if item.strip()
    }


def normalize_audit_activation(selected_skill: str) -> str:
    if selected_skill in STANDALONE_SKILLS:
        return selected_skill
    return "none"


def test_activation_results_cover_exact_scenarios_and_match_contract() -> None:
    scenarios = load_activation_scenarios()
    results = parse_activation_result_sections()
    expected_keys = {
        (skill_name, category)
        for skill_name in STANDALONE_SKILLS
        for category in ACTIVATION_CATEGORIES
    }

    assert set(results) == expected_keys
    assert len(results) == 10
    for (skill_name, category), section in results.items():
        scenario = scenarios[skill_name][category]
        assert activation_result_field(section, "Prompt") == scenario["prompt"]
        assert (
            activation_result_field(section, "Expected activation")
            == scenario["expected_activation"]
        )
        observed_activation = activation_result_field(section, "Observed activation")
        assert observed_activation == scenario["expected_activation"]
        selected_skill, missing_inputs = parse_activation_public_record(section)
        assert normalize_audit_activation(selected_skill) == observed_activation
        requestable_missing_inputs = scenario["requestable_missing_inputs"]
        assert isinstance(requestable_missing_inputs, list)
        assert all(isinstance(item, str) for item in requestable_missing_inputs)
        assert missing_inputs <= set(requestable_missing_inputs)
        assert activation_result_field(section, "Verdict") == "PASS"
        assert activation_result_field(section, "Rationale")
        assert "### Public response" in section
        assert re.search(r"```text\n.+?\n```", section, re.DOTALL)


def test_activation_results_state_controller_attestation_and_evidence_limits() -> None:
    text = " ".join(read(ACTIVATION_RESULTS).lower().split())

    for required_text in (
        "controller-attested",
        "not independently authenticated",
        (
            "controller reports that each exact prompt was sent in a fresh evaluator "
            "context with both skills discoverable"
        ),
        "host logs and session ids are intentionally absent",
        "cannot independently prove fresh-context isolation",
        "model/runtime version",
        "exact installed-skill bytes",
        "exact prompts",
        "preserved public responses and self-reported decisions",
        "scenario contract",
        "internal consistency tests",
    ):
        assert required_text in text
    assert "each scenario ran in a fresh evaluator context" not in text


def test_build_backend_supports_pep_639_license_metadata() -> None:
    build_system = tomllib.loads(read("pyproject.toml"))["build-system"]

    assert build_system["requires"] == ["hatchling>=1.27.0"]


def test_package_metadata_identifies_public_project() -> None:
    metadata = tomllib.loads(read("pyproject.toml"))["project"]

    assert metadata["readme"] == "README.md"
    assert metadata["license"] == "MIT"
    assert metadata["license-files"] == ["LICENSE"]
    assert metadata["keywords"] == [
        "agent-skills",
        "citation-verification",
        "document-analysis",
        "plagiarism-audit",
        "research-integrity",
    ]
    assert metadata["authors"] == [{"name": "Michele Garbelotto"}]
    assert metadata["urls"]["Homepage"] == (
        "https://github.com/MicheleGarbelotto/source-checker"
    )
    assert metadata["urls"]["Changelog"] == (
        "https://github.com/MicheleGarbelotto/source-checker/blob/main/CHANGELOG.md"
    )
    assert metadata["urls"]["Repository"] == (
        "https://github.com/MicheleGarbelotto/source-checker"
    )
    assert metadata["urls"]["Issues"] == (
        "https://github.com/MicheleGarbelotto/source-checker/issues"
    )


def test_skills_ref_is_not_a_project_dependency() -> None:
    project = tomllib.loads(read("pyproject.toml"))["project"]
    dependency_groups = {
        "dependencies": project.get("dependencies", []),
        **project.get("optional-dependencies", {}),
    }

    for group_name, requirements in dependency_groups.items():
        normalized_names = {
            re.sub(
                r"[-_.]+",
                "-",
                re.split(r"[\s\[<>=!~;@]", requirement.strip(), maxsplit=1)[0].lower(),
            )
            for requirement in requirements
        }
        assert "skills-ref" not in normalized_names, group_name


def test_citation_metadata_describes_release() -> None:
    citation = yaml.safe_load(read("CITATION.cff"))

    assert citation["cff-version"] == "1.2.0"
    assert citation["type"] == "software"
    assert citation["title"] == "source-checker"
    assert citation["version"] == "0.1.0"
    assert citation["license"] == "MIT"
    assert citation["repository-code"] == (
        "https://github.com/MicheleGarbelotto/source-checker"
    )
    assert citation["authors"] == [
        {"family-names": "Garbelotto", "given-names": "Michele"}
    ]


def test_ci_runs_release_checks_on_supported_platforms() -> None:
    workflow = read(".github/workflows/ci.yml")
    configuration = yaml.safe_load(workflow)

    assert isinstance(configuration, dict)
    assert "on" in configuration
    assert configuration["permissions"] == {"contents": "read"}
    matrix = configuration["jobs"]["test"]["strategy"]["matrix"]
    assert matrix["os"] == ["ubuntu-latest", "windows-latest"]
    assert [str(version) for version in matrix["python-version"]] == ["3.11", "3.12"]

    steps = configuration["jobs"]["test"]["steps"]
    action_uses = [step["uses"] for step in steps if "uses" in step]
    run_commands = [step["run"] for step in steps if "run" in step]
    assert action_uses == [CHECKOUT_ACTION, SETUP_PYTHON_ACTION]
    workflow_lines = {line.strip() for line in workflow.splitlines()}
    assert f"uses: {CHECKOUT_ACTION} # v6" in workflow_lines
    assert f"uses: {SETUP_PYTHON_ACTION} # v5" in workflow_lines
    assert run_commands.count(SKILLS_REF_INSTALL) == 1
    assert "python -m pip wheel . --no-deps --wheel-dir build/release-check" in run_commands
    assert "source-checker-corpus --help" in run_commands
    assert "skills-ref validate skills/citation-support-audit" in run_commands
    assert "skills-ref validate skills/plagiarism-audit" in run_commands

    for expected in (
        "ubuntu-latest",
        "windows-latest",
        '"3.11"',
        '"3.12"',
        f"{CHECKOUT_ACTION} # v6",
        f"{SETUP_PYTHON_ACTION} # v5",
        'python -m pip install -e ".[dev]"',
        "python -m pip wheel . --no-deps --wheel-dir build/release-check",
        "source-checker-corpus --help",
        SKILLS_REF_INSTALL,
        "python -m pytest -q",
        "python -m ruff check .",
        "python -m pyright",
        "skills-ref validate skills/citation-support-audit",
        "skills-ref validate skills/plagiarism-audit",
        "sync_skill_runtime.py --check skills/citation-support-audit",
        "sync_skill_runtime.py --check skills/plagiarism-audit",
    ):
        assert expected in workflow


def test_ci_inspects_and_installs_the_built_wheel_before_entrypoint_smoke() -> None:
    configuration = yaml.safe_load(read(".github/workflows/ci.yml"))
    steps = configuration["jobs"]["test"]["steps"]
    step_names = [step["name"] for step in steps]

    assert len(step_names) == len(set(step_names))
    steps_by_name = {step["name"]: step for step in steps}
    source_tree_checks = (
        "Run tests",
        "Run Ruff",
        "Run Pyright",
        "Validate Citation Support Audit skill",
        "Validate Plagiarism Audit skill",
        "Verify Citation Support Audit runtime synchronization",
        "Verify Plagiarism Audit runtime synchronization",
    )
    artifact_steps = (
        "Build wheel",
        "Verify wheel contents",
        "Install built wheel",
        "Verify installed entry point",
    )

    for step_name in (*source_tree_checks, *artifact_steps):
        assert step_name in steps_by_name
    assert all(
        step_names.index(step_name) < step_names.index("Build wheel")
        for step_name in source_tree_checks
    )
    assert [step_names.index(step_name) for step_name in artifact_steps] == sorted(
        step_names.index(step_name) for step_name in artifact_steps
    )

    inspection = " ".join(steps_by_name["Verify wheel contents"]["run"].split())
    for required_text in (
        "python -c",
        "pathlib",
        "zipfile",
        "build/release-check",
        "glob",
        "len(wheels) == 1",
        ".dist-info/METADATA",
        ".dist-info/licenses/LICENSE",
    ):
        assert required_text in inspection

    installation = " ".join(steps_by_name["Install built wheel"]["run"].split())
    for required_text in (
        "python -c",
        "pathlib",
        "subprocess",
        "sys.executable",
        "build/release-check",
        "glob",
        "len(wheels) == 1",
        "pip",
        "install",
        "--force-reinstall",
        "--no-deps",
    ):
        assert required_text in installation
    assert steps_by_name["Verify installed entry point"]["run"] == (
        "source-checker-corpus --help"
    )


def test_dependabot_updates_python_and_github_actions_weekly() -> None:
    configuration = yaml.safe_load(read(".github/dependabot.yml"))

    assert configuration["version"] == 2
    updates = configuration["updates"]
    assert isinstance(updates, list)
    assert len(updates) == 2
    assert {
        update["package-ecosystem"]: {
            "directory": update["directory"],
            "schedule": update["schedule"],
            "open-pull-requests-limit": update["open-pull-requests-limit"],
        }
        for update in updates
    } == {
        "pip": {
            "directory": "/",
            "schedule": {"interval": "weekly"},
            "open-pull-requests-limit": 5,
        },
        "github-actions": {
            "directory": "/",
            "schedule": {"interval": "weekly"},
            "open-pull-requests-limit": 5,
        },
    }


def test_readme_discloses_formats_providers_partial_results_and_nonclaims() -> None:
    text = read("README.md")
    lowered = text.lower()

    for suffix in (
        ".qmd",
        ".md",
        ".txt",
        ".tex",
        ".latex",
        ".html",
        ".htm",
        ".docx",
        ".docm",
        ".doc",
        ".pdf",
    ):
        assert f"`{suffix}`" in text
    assert "mendeley exports" in lowered
    assert "does not access" in lowered and "mendeley" in lowered
    assert "zotero" in lowered and "read-only" in lowered
    assert "partial" in lowered and "within the analyzed corpus" in lowered
    assert "extraction quality" in lowered
    assert "not affiliated" in lowered
    assert "not equivalent" in lowered
    assert "legal advice" in lowered
    assert "misconduct" in lowered
    assert "skills/citation-support-audit/references/methodology-and-attribution.md" in text
    assert "skills/plagiarism-audit/references/methodology-and-attribution.md" in text


def test_release_gitignore_covers_local_and_sensitive_outputs() -> None:
    text = read(".gitignore")

    for pattern in (
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        ".ruff_cache/",
        "audit-output*/",
        "text-cache/",
        "source-manifest.csv",
        "*.pdf",
        "*.docx",
        "*.docm",
        "*.doc",
        "*.converted.*",
        "zotero-data/",
        "mendeley-data/",
        "*.sqlite",
    ):
        assert pattern in text


def git_check_ignored(path: str) -> bool:
    with tempfile.TemporaryDirectory() as temporary_directory:
        repository = Path(temporary_directory)
        shutil.copy2(ROOT / ".gitignore", repository / ".gitignore")
        subprocess.run(
            ["git", "init", "-q"],
            cwd=repository,
            check=True,
        )
        result = subprocess.run(
            [
                "git",
                "-c",
                f"core.excludesFile={os.devnull}",
                "check-ignore",
                "--no-index",
                "-q",
                "--",
                path,
            ],
            cwd=repository,
            check=False,
        )
        assert result.returncode in {0, 1}, f"git check-ignore failed for {path}"
        return result.returncode == 0


def test_gitignore_keeps_future_fixtures_and_docs_trackable() -> None:
    for path in (
        "tests/fixtures/future.pdf",
        "tests/fixtures/future.docx",
        "docs/examples/future.docm",
        "docs/examples/future.doc",
        "tests/fixtures/cache.jsonl",
        "tests/fixtures/source-manifest.csv",
    ):
        assert not git_check_ignored(path), path


def test_gitignore_scopes_private_inputs_and_outputs_to_local_locations() -> None:
    for path in (
        "draft.pdf",
        "draft.docx",
        "local-output.jsonl",
        "source-manifest.csv",
        "local-sources/paper.pdf",
        "corpus/paper.docx",
        "audit-output-run/report.jsonl",
        "audit-results-run/source-manifest.csv",
        "text-cache/derived.jsonl",
        "zotero-data/zotero.sqlite",
        "mendeley-data/export.json",
    ):
        assert git_check_ignored(path), path


def test_changelog_records_release_scope_and_known_limits() -> None:
    text = read("CHANGELOG.md")
    lowered = text.lower()

    assert "## [0.1.0]" in text
    assert "supported formats" in lowered
    assert "zotero" in lowered and "mendeley" in lowered
    assert "within the analyzed corpus" in lowered
    assert "known limitations" in lowered
    assert "does not fetch live html" in lowered
    assert "does not perform ocr" in lowered


def test_release_smoke_uses_one_readable_pdf_and_one_missing_source(tmp_path: Path) -> None:
    readable = tmp_path / READABLE_SMOKE_FILENAME
    missing = tmp_path / "missing-source.pdf"
    bibliography = tmp_path / "corpus.bib"
    manifest = tmp_path / "source-manifest.csv"
    cache = tmp_path / "text-cache"
    target = ROOT / "tests" / "fixtures" / "documents" / "release-smoke-target.html"
    runtime_script = Path(
        os.environ.get(
            "SOURCE_CHECKER_SMOKE_RUNTIME",
            ROOT / "skills" / "plagiarism-audit" / "scripts" / "source_corpus.py",
        )
    )
    write_readable_synthetic_pdf(readable)
    readable_entry = (
        "@article{readable, title = {Synthetic readable source}, "
        + f"file = {{:{readable.as_posix()}:PDF}}}}"
    )
    missing_entry = (
        "@article{missing, title = {Synthetic unavailable source}, "
        + f"file = {{:{missing.as_posix()}:PDF}}}}"
    )
    bibliography.write_text(
        f"{readable_entry}\n{missing_entry}",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(runtime_script),
            "manifest",
            "--target",
            str(target),
            "--bibliography",
            str(bibliography),
            "--output",
            str(manifest),
            "--cache-dir",
            str(cache),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "ambiguous": 0,
        "analyzed": 1,
        "coverage_percent": 50.0,
        "expected": 2,
        "extracted": 1,
        "missing": 1,
        "resolved": 1,
        "unusable": 0,
    }
    target_document = extract_document(target, "target")
    source_document = extract_document(readable, "source")
    target_words = re.findall(r"\b[\w'-]+\b", target_document.blocks[0].text_normalized)
    source_words = re.findall(r"\b[\w'-]+\b", source_document.blocks[0].text_normalized)
    verified_match_words = source_words[:4]
    assert source_document.extraction_status == "extracted"
    assert source_document.text_quality == "good"
    assert target_words[:4] == verified_match_words
    assert len(target_words) == 8
    assert set(target_words).isdisjoint(source_words[4:])
    assert len(verified_match_words) / len(target_words) * 100 == 50.0


def test_release_smoke_record_preserves_required_observations() -> None:
    text = read(RELEASE_SMOKE_RECORD)

    assert "Observed overall similarity" in text
    assert "50.00%" in text
    assert "Corpus coverage" in text
    assert "1 / 2 (50.00%)" in text
    assert "missing-source.pdf" in text
    assert "does not determine plagiarism or misconduct" in text
    assert f"Observed per-source similarity: `{READABLE_SMOKE_FILENAME}`" in text
    assert "two-page.pdf" not in text


def test_installed_skill_transcript_records_required_release_evidence() -> None:
    text = read(INSTALLED_SKILL_TRANSCRIPT)
    prompt = text.split("## Scenario prompt", 1)[1].split("## Run manifest", 1)[0]

    assert "The following is the exact scenario prompt" in prompt
    assert "> Perform an independent smoke test of the globally installed skill" in prompt
    assert "%USERPROFILE%\\.codex\\skills\\plagiarism-audit" in prompt
    assert "do not read repository expected-output files or tests" in prompt
    assert re.search(
        r"Installed skill tree SHA-256: `[0-9a-f]{64}`",
        text,
    )
    assert "Expected-source-set coverage: **Partial**" in text
    assert "1 / 2 = **50.0% [Partial]**" in text
    assert "4 / 8 = **50.0% [Partial]**" in text
    assert "missing-source.pdf" in text and "file absent" in text
    assert f"Source locator: `{READABLE_SMOKE_FILENAME}`" in text
    assert "not a plagiarism verdict" in text
    assert "No repository expected-output file or test implementation was read" in text


def test_installed_skill_transcript_is_publication_safe() -> None:
    text = read(INSTALLED_SKILL_TRANSCRIPT)

    profile_path = re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s`]+", re.IGNORECASE)
    assert not profile_path.search(text)
    assert "<oai-mem-citation>" not in text
    assert "MEMORY.md" not in text
    assert "<rollout_ids>" not in text
    assert "application-added memory" not in text.lower()
    assert "memory-citation footer" not in text.lower()
    assert "repository-owned synthetic" in read(RELEASE_SMOKE_RECORD)


def test_clean_copy_receipt_records_both_verified_runs_without_replacing_tests() -> None:
    text = read(CLEAN_COPY_RECEIPT)
    lowered = text.lower()

    assert "execution evidence, not a test substitute" in lowered
    assert "## Original Task 8 execution" in text
    assert "## Independent specification review of `ec501a1`" in text
    assert "ec501a1375ef386badb3c7f4b02817aa937a7c30" in text
    assert re.search(r"git\s+[^\n]*archive --format=zip", text)
    assert "Expand-Archive" in text
    assert re.search(r"\S*python(?:\.exe)?\s+-m venv \.venv-clean", text)
    assert '-m venv (Join-Path $root ".venv")' in text
    assert '$py = Join-Path $root ".venv\\Scripts\\python.exe"' in text
    assert "pip install" in text and '".[dev]"' in text
    assert "pytest -q" in text
    assert text.count("479 / 479 passed") == 2
    for skill in ("citation-support-audit", "plagiarism-audit"):
        assert f"quick_validate.py skills/{skill}" in text
        assert f"skills/{skill}/scripts/source_corpus.py --help" in text
    assert "git_absent=True" in text
    assert "exists=False" in text


def test_historical_receipts_use_immutable_refs_and_explicit_clean_root_cwd() -> None:
    text = read(CLEAN_COPY_RECEIPT)
    historical, current = text.split("## Current release verification receipt", 1)
    blocks = re.findall(r"```powershell\n(.*?)```", historical, re.DOTALL)

    assert "v0.1.0" not in historical
    assert re.search(
        r"git\s+[^\n]*archive --format=zip[^\n]*"
        r"ec501a1375ef386badb3c7f4b02817aa937a7c30",
        historical,
    )
    assert len(blocks) == 2
    assert all("Push-Location $root" in block for block in blocks)
    assert all("Pop-Location" in block for block in blocks)
    assert "git tag -n99 v0.1.0" in current
    assert "git cat-file -p v0.1.0" in current
    assert "authoritative post-commit receipt" in " ".join(current.lower().split())


def test_legacy_baseline_validator_uses_the_recoverable_backup() -> None:
    text = read("tests/behavior/plagiarism-audit/baseline-results/README.md")
    validation = text.split("## Validation and limitations", 1)[1]

    assert '.codex/skill-backups/2026-09-20/plagiarism-checker/SKILL.md' in validation
    assert '.codex/skills/plagiarism-checker/SKILL.md' not in validation


def test_independent_receipt_invokes_variable_held_python_with_call_operator() -> None:
    text = read(CLEAN_COPY_RECEIPT)
    independent = text.split("## Independent specification review of `ec501a1`", 1)[1]
    commands = independent.split("```powershell", 1)[1].split("```", 1)[0]

    required_invocations = (
        '& $py -m pip install -q -e "$root[dev]"',
        "& $py -m pytest -q",
        (
            "& $py %SKILL_CREATOR%\\scripts\\quick_validate.py "
            "skills/citation-support-audit"
        ),
        "& $py %SKILL_CREATOR%\\scripts\\quick_validate.py skills/plagiarism-audit",
        "& $py skills/citation-support-audit/scripts/source_corpus.py --help",
        "& $py skills/plagiarism-audit/scripts/source_corpus.py --help",
    )
    assert all(invocation in commands for invocation in required_invocations)
    assert not re.search(r"(?m)^\$py\s+(?!=)", commands)


def test_readme_guards_individual_skill_copy_destinations() -> None:
    text = read("README.md")
    installation = text.split("## Installation", 1)[1].split("## Methodological scope", 1)[0]
    normalized = " ".join(installation.lower().split())

    assert "destinations must not already exist" in normalized
    assert "Test-Path -LiteralPath $destination" in installation
    assert "Copy-Item -Recurse -LiteralPath $source -Destination $destination" in installation
    assert "nested directory" in normalized
    assert "dated backup" in normalized
