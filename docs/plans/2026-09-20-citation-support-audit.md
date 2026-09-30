# Citation Support Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the existing citation-checker into the English-language `citation-support-audit` skill, preserving its evidence standards while supporting multiple document formats, corpus providers, a complete default audit, and quantitative verified-subset reporting.

**Architecture:** The skill remains a judgment-oriented workflow backed by the completed `source_checker` runtime. Its concise `SKILL.md` routes to focused references for corpus handling, methods, and reporting. Behavioral tests evaluate decisions and reports; Python tests validate the vendored runtime rather than encoding prose wording.

**Tech Stack:** Codex skill Markdown/YAML, shared Python runtime from the core plan, pytest, official methodological references, isolated agent forward-tests.

---

## File map

```text
skills/citation-support-audit/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── methodology-and-attribution.md
│   ├── metrics-and-rules.md
│   ├── report-template.md
│   └── source-corpus.md
└── scripts/
    ├── source_corpus.py
    └── source_checker/
tests/behavior/citation-support-audit/
├── scenarios.yaml
├── baseline-results/
└── revised-results/
tests/test_citation_skill_package.py
```

### Task 1: Capture baseline behavior before editing the skill

**Files:**
- Create: `tests/behavior/citation-support-audit/scenarios.yaml`
- Create: `tests/behavior/citation-support-audit/baseline-results/README.md`

- [ ] **Step 1: Define five realistic scenarios**

Create scenarios with these exact behavioral assertions:

1. **Underspecified request:** “Use the skill to check my paper.” The agent must identify that target and corpus are missing; record every question it asks.
2. **DOCX plus PDF folder:** the agent must accept the formats and attempt automatic mapping without asking for a user-created map.
3. **Incomplete corpus:** four sources are expected, three are readable, and one is missing; the agent must continue and must not label the missing source unsupported.
4. **Ambiguous mapping:** two same-author/same-year PDFs plausibly match one citation; the agent must ask only about that pair and must not select silently.
5. **Default scope:** the user requests a citation check without narrowing it; the agent must cover substantive support, potentially missing citations, reference integrity, placement/scope, direct quotations, style when determinable, metrics, and coverage.

- [ ] **Step 2: Run the scenarios against the installed legacy `citation-checker` without showing the new design**

Store the exact prompts, agent outputs, and observed failures in `baseline-results/README.md`. Required baseline observations include whether it over-focuses on QMD/Zotero/PDF, stops on inaccessible sources, asks unnecessary scope questions, or omits verified-subset metrics.

- [ ] **Step 3: Confirm RED**

The baseline is considered failing when at least one required assertion is violated. If all assertions already pass, add a LaTeX/HTML extraction scenario that demonstrates a genuine unsupported behavior before editing.

- [ ] **Step 4: Commit baseline tests**

```powershell
git add tests/behavior/citation-support-audit
git commit -m "test: capture citation audit baseline behavior"
```

### Task 2: Scaffold the renamed skill and synchronize the runtime

**Files:**
- Create: `skills/citation-support-audit/SKILL.md`
- Create: `skills/citation-support-audit/agents/openai.yaml`
- Create: `skills/citation-support-audit/references/source-corpus.md`
- Create: `skills/citation-support-audit/references/metrics-and-rules.md`
- Create: `skills/citation-support-audit/references/report-template.md`
- Create: `skills/citation-support-audit/references/methodology-and-attribution.md`
- Create: `tests/test_citation_skill_package.py`

- [ ] **Step 1: Write the failing package test**

Assert:

```python
def test_citation_skill_has_one_consistent_name():
    root = Path("skills/citation-support-audit")
    frontmatter = load_frontmatter(root / "SKILL.md")
    interface = yaml.safe_load((root / "agents/openai.yaml").read_text(encoding="utf-8"))
    assert frontmatter["name"] == "citation-support-audit"
    assert interface["interface"]["display_name"] == "Citation Support Audit"
    assert "$citation-support-audit" in interface["interface"]["default_prompt"]


def test_citation_runtime_is_synchronized():
    result = subprocess.run(
        [sys.executable, "tools/sync_skill_runtime.py", "--check", "skills/citation-support-audit"],
        check=False,
    )
    assert result.returncode == 0
```

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_citation_skill_package.py -q`

Expected: failure because the new skill does not exist.

- [ ] **Step 3: Copy only the validated conceptual content from the legacy skill**

Create the new files from the installed citation skill while removing thesis-specific, QMD-only, PDF-only, and Zotero-only assumptions. Do not copy the duplicate legacy Python implementation. Use the sync tool:

```powershell
python tools/sync_skill_runtime.py skills/citation-support-audit
```

- [ ] **Step 4: Set exact interface metadata**

`agents/openai.yaml` must contain:

```yaml
interface:
  display_name: "Citation Support Audit"
  short_description: "Audit whether citations support a document's claims"
  default_prompt: "Use $citation-support-audit to run a complete source-grounded citation support audit of this document."
```

Do not add a separate technical or legacy display name.

- [ ] **Step 5: Run package tests and commit**

Run: `pytest tests/test_citation_skill_package.py -q`

Expected: pass.

```powershell
git add skills/citation-support-audit tests/test_citation_skill_package.py
git commit -m "feat: scaffold citation support audit skill"
```

### Task 3: Write the minimal decision-complete `SKILL.md`

**Files:**
- Modify: `skills/citation-support-audit/SKILL.md`
- Modify: `tests/test_citation_skill_package.py`

- [ ] **Step 1: Add structural tests before prose changes**

Test only observable invariants: valid frontmatter, exact name, no words `thesis` or `Zotero PDFs` in the description, links to all four references, no mandatory up-front source map, and no stop condition triggered solely by missing sources. Do not test exact paragraphs or heading counts.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_citation_skill_package.py -q`

Expected: the copied legacy-oriented text fails at least the generic-description and missing-source assertions.

- [ ] **Step 3: Rewrite the frontmatter description**

Use this trigger-only description:

```yaml
---
name: citation-support-audit
description: Use when checking whether a document's citations resolve correctly, are appropriately placed, cover claims that need support, and substantively support those claims against a defined source corpus, including partial or incomplete corpora.
---
```

- [ ] **Step 4: Rewrite the workflow around decisions, not file-specific recipes**

The body must state:

- complete audit is the default unless the user narrows it;
- ask for target only when absent;
- ask for source location/provider only when absent;
- infer citation-source mappings and ask only about material ambiguous pairs;
- continue with accessible sources;
- distinguish unsupported, contradictory, unresolved, and unverifiable;
- calculate verified-subset metrics plus coverage when the corpus is incomplete;
- never edit the target or expand the corpus without authorization;
- use the common corpus runtime for supported files and providers;
- keep citation support separate from plagiarism similarity.

Keep format details, formulas, and report schemas in references.

- [ ] **Step 5: Run tests and commit**

```powershell
pytest tests/test_citation_skill_package.py -q
git add skills/citation-support-audit/SKILL.md tests/test_citation_skill_package.py
git commit -m "docs: generalize citation audit decisions"
```

### Task 4: Generalize corpus instructions and adaptive intake

**Files:**
- Modify: `skills/citation-support-audit/references/source-corpus.md`
- Modify: `tests/test_citation_skill_package.py`

- [ ] **Step 1: Add tests for required corpus content**

Assert that the reference names every supported extension, local directories, Zotero, Mendeley exports, BibTeX/BibLaTeX, RIS, CSL JSON, embedded bibliography, `source-manifest.csv`, mapping statuses, extraction statuses, and the no-separate-mapping-file rule.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_citation_skill_package.py -q`

Expected: failures for the newly required generic routes.

- [ ] **Step 3: Rewrite `source-corpus.md`**

Document one intake table:

| Missing information | Required action |
|---|---|
| target | ask for file(s) and scope |
| corpus | ask where sources are available |
| specific mapping ambiguity | present candidates and ask only for that match |
| inaccessible source | continue and record status |
| unreadable target | stop substantive analysis and issue diagnostic report |

Document the CLI using `--target`, `--source`, `--bibliography`, `--manifest`, and optional `--zotero-live`. Explain locator fidelity by format and require conversion/extraction disclosure. State that Mendeley means supported exports plus accessible attachments, not private-database access.

- [ ] **Step 4: Verify and commit**

```powershell
pytest tests/test_citation_skill_package.py -q
git add skills/citation-support-audit/references/source-corpus.md tests/test_citation_skill_package.py
git commit -m "docs: generalize citation corpus intake"
```

### Task 5: Define complete default auditing and partial quantitative metrics

**Files:**
- Modify: `skills/citation-support-audit/references/metrics-and-rules.md`
- Modify: `skills/citation-support-audit/references/report-template.md`
- Modify: `tests/test_citation_skill_package.py`

- [ ] **Step 1: Add invariant tests**

Assert the metrics reference contains the exact formulas for ALCE-style citation recall, citation precision, and audit coverage; explicitly forbids treating unverifiable claims as unsupported; and defines verified-subset labels. Assert the report template includes expected/resolved/extracted/analyzed/missing counts and a `complete` or `partial` result scope.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_citation_skill_package.py -q`

Expected: failure because current references allow withholding instead of requiring useful verified-subset metrics.

- [ ] **Step 3: Rewrite the metrics rules**

Retain existing claim segmentation and support labels. Use:

```text
whole-scope citation recall = fully supported eligible claims / all eligible claims * 100
whole-scope citation precision = supporting citations / all citations evaluated * 100
verified-subset citation recall = fully supported classifiable claims / classifiable eligible claims * 100
verified-subset citation precision = supporting classifiable citations / classifiable citations * 100
audit coverage = classifiable eligible claims / all eligible claims * 100
corpus coverage = analyzed expected sources / all expected sources * 100
```

Whole-scope metrics are allowed only when all relevant claims/citations are classifiable. Otherwise the report must compute the verified-subset metrics when at least one eligible claim is classifiable. Keep diagnostic counts separate and forbid composite scores.

- [ ] **Step 4: Rewrite the report template**

The complete default report must contain, in order:

1. scope and corpus coverage;
2. method and extraction quality;
3. quantitative scorecard;
4. reference integrity and citation mechanics;
5. claim-source matrix;
6. passage-level evidence;
7. potentially missing citations;
8. inaccessible/ambiguous sources needed for fuller coverage;
9. limitations and conclusion.

Every source limitation must state its effect without calling the associated claim unsupported.

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests/test_citation_skill_package.py -q
git add skills/citation-support-audit/references tests/test_citation_skill_package.py
git commit -m "docs: require complete and partial citation reporting"
```

### Task 6: Add methodological attribution in original English

**Files:**
- Modify: `skills/citation-support-audit/SKILL.md`
- Modify: `skills/citation-support-audit/references/methodology-and-attribution.md`
- Modify: `README.md`

- [ ] **Step 1: Add a source-verification checklist**

Verify the current official ALCE paper/repository and relevant public citation-assistance documentation. Record title, organization/authors, URL, access date, adapted concept, and what is not reproduced. Use primary or official sources.

- [ ] **Step 2: Write the attribution reference**

Explain in original English that claim-level recall/precision are academic-document adaptations of public ALCE concepts and are not directly comparable with ALCE benchmark scores. State independent implementation and no product equivalence or affiliation. Include the formulas already defined, not copied prose or graphics.

- [ ] **Step 3: Add the early methodological notice**

Place a concise `Methodological basis and limitations` section immediately after the purpose in `SKILL.md`, linking to the reference. It must be informative but not dominate skill routing.

- [ ] **Step 4: Verify links and commit**

Run the repository's link checker if added; otherwise issue HTTP HEAD/GET checks for every cited URL and record any access failures in the review notes.

```powershell
git add README.md skills/citation-support-audit
git commit -m "docs: attribute citation audit methodology"
```

### Task 7: Forward-test, review English, and close observed gaps

**Files:**
- Modify: `tests/behavior/citation-support-audit/revised-results/`
- Modify only skill files implicated by observed failures

- [ ] **Step 1: Run the five baseline scenarios with the revised skill**

Use independent agents in isolated temporary workspaces. Provide the skill and scenario artifacts, but do not provide intended answers or known baseline failures. Save exact outputs.

- [ ] **Step 2: Evaluate behavior against scenario assertions**

Require all five scenarios to pass. For each failure, add only the smallest instruction or runtime correction that addresses the observed behavior, then rerun the failed scenario and at least one neighboring scenario.

- [ ] **Step 3: Run three independent review passes**

The user has authorized multi-agent review. Assign separate passes for:

- English clarity, idiomatic usage, and consistent terminology;
- methodological fidelity and metric interpretation;
- portability across formats/providers and adaptive intake.

Reviewers propose changes; the implementing agent verifies each proposal against the design before applying it.

- [ ] **Step 4: Run all validation**

```powershell
pytest -q
ruff check .
pyright
$skillValidator = Join-Path $env:USERPROFILE ".codex\skills\.system\skill-creator\scripts\quick_validate.py"
python $skillValidator skills/citation-support-audit
python tools/sync_skill_runtime.py --check skills/citation-support-audit
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit the verified skill**

```powershell
git add skills/citation-support-audit tests/behavior/citation-support-audit
git commit -m "test: verify citation support audit behavior"
```

### Task 8: Install with a recoverable cutover

**Files:**
- Copy verified skill to: `$env:USERPROFILE\.codex\skills\citation-support-audit`
- Move legacy skill to: `$env:USERPROFILE\.codex\skill-backups\2026-09-20\citation-checker`

- [ ] **Step 1: Verify exact source and destination paths**

Resolve all three absolute paths and confirm the new destination does not contain unrelated files. Do not delete the legacy skill.

- [ ] **Step 2: Move the legacy skill to the dated backup directory**

Use native PowerShell `Move-Item -LiteralPath` after confirming the resolved source remains under `$env:USERPROFILE\.codex\skills` and the backup remains under `$env:USERPROFILE\.codex\skill-backups\2026-09-20`.

- [ ] **Step 3: Copy the verified new skill**

Copy only `skills/citation-support-audit` into the installed skill root. Run `quick_validate.py` on the installed destination and invoke its runtime help in isolation.

- [ ] **Step 4: Perform a smoke invocation**

Use a synthetic DOCX target plus one PDF source. Confirm the skill asks no unnecessary mapping question and produces a complete default audit outline.

- [ ] **Step 5: Commit installation notes**

Record only version, validation commands, and backup location in a concise repository release note. Do not copy private local paths into public-facing README examples.

## Citation skill completion gate

Do not begin the Plagiarism Audit plan until the new Citation Support Audit:

- passes all unit, package, and behavioral tests;
- has completed independent English, methods, and portability reviews;
- computes verified-subset metrics under incomplete access;
- never requests a full mapping file;
- has one consistent name everywhere;
- is installed with the legacy version recoverably backed up.
