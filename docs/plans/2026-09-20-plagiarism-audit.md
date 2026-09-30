# Plagiarism Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the existing plagiarism-checker into the English-language `plagiarism-audit` skill, retaining transparent source-bounded similarity analysis while supporting multiple formats/providers and mandatory quantitative reporting over incomplete corpora.

**Architecture:** The skill consumes the already verified shared runtime and keeps similarity methodology separate from citation-support judgments. `SKILL.md` contains only routing, boundaries, and critical decisions; detailed metrics, corpus handling, methodological attribution, and report schema remain in focused references.

**Tech Stack:** Codex skill Markdown/YAML, shared Python runtime from the core plan, pytest, official methodological references, isolated agent forward-tests.

---

## File map

```text
skills/plagiarism-audit/
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
tests/behavior/plagiarism-audit/
├── scenarios.yaml
├── baseline-results/
└── revised-results/
tests/test_plagiarism_skill_package.py
```

### Task 1: Capture baseline behavior before editing the skill

**Files:**
- Create: `tests/behavior/plagiarism-audit/scenarios.yaml`
- Create: `tests/behavior/plagiarism-audit/baseline-results/README.md`

- [ ] **Step 1: Define six realistic scenarios**

Create scenarios with these assertions:

1. **Underspecified request:** asks only for the missing target and corpus.
2. **Multi-format corpus:** accepts a DOCX target and PDF, HTML, and DOCX sources without changing the audit meaning.
3. **Incomplete corpus:** computes observed similarity from three accessible sources while listing one inaccessible source and labelling the result partial.
4. **Zero accessible sources:** produces a diagnostic coverage report and withholds similarity percentages.
5. **Proper quotation:** high similarity with quotation and citation is described as similarity, not automatically plagiarism.
6. **Localized concerning match:** a low overall percentage does not dismiss one verified distinctive passage.

- [ ] **Step 2: Run the scenarios against the installed legacy `plagiarism-checker` without the new design**

Save exact prompts, outputs, questions, stop decisions, quantitative decisions, and observed rationalizations in `baseline-results/README.md`.

- [ ] **Step 3: Confirm RED**

At least one scenario must demonstrate a real gap, particularly failure to compute partial-corpus metrics or over-reliance on QMD/Zotero/PDF. If not, add a local HTML or LaTeX source scenario before editing.

- [ ] **Step 4: Commit baseline tests**

```powershell
git add tests/behavior/plagiarism-audit
git commit -m "test: capture plagiarism audit baseline behavior"
```

### Task 2: Scaffold the consistently renamed skill

**Files:**
- Create: `skills/plagiarism-audit/SKILL.md`
- Create: `skills/plagiarism-audit/agents/openai.yaml`
- Create: `skills/plagiarism-audit/references/source-corpus.md`
- Create: `skills/plagiarism-audit/references/metrics-and-rules.md`
- Create: `skills/plagiarism-audit/references/report-template.md`
- Create: `skills/plagiarism-audit/references/methodology-and-attribution.md`
- Create: `tests/test_plagiarism_skill_package.py`

- [ ] **Step 1: Write failing package tests**

Assert exact consistency:

```python
def test_plagiarism_skill_has_one_consistent_name():
    root = Path("skills/plagiarism-audit")
    frontmatter = load_frontmatter(root / "SKILL.md")
    interface = yaml.safe_load((root / "agents/openai.yaml").read_text(encoding="utf-8"))
    assert frontmatter["name"] == "plagiarism-audit"
    assert interface["interface"]["display_name"] == "Plagiarism Audit"
    assert "$plagiarism-audit" in interface["interface"]["default_prompt"]
```

Also assert that runtime synchronization check succeeds.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_plagiarism_skill_package.py -q`

Expected: failure because the new skill does not exist.

- [ ] **Step 3: Scaffold from the legacy skill without copying duplicate runtime code**

Preserve verified conceptual boundaries and public metric definitions. Remove thesis-specific, QMD-only, PDF-only, and Zotero-only wording. Synchronize the validated common runtime:

```powershell
python tools/sync_skill_runtime.py skills/plagiarism-audit
```

- [ ] **Step 4: Use exact interface metadata**

```yaml
interface:
  display_name: "Plagiarism Audit"
  short_description: "Audit a document for source-bounded similarity"
  default_prompt: "Use $plagiarism-audit to audit this document against the specified source corpus and report similarity evidence and coverage."
```

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests/test_plagiarism_skill_package.py -q
git add skills/plagiarism-audit tests/test_plagiarism_skill_package.py
git commit -m "feat: scaffold plagiarism audit skill"
```

### Task 3: Rewrite `SKILL.md` around source-bounded judgment

**Files:**
- Modify: `skills/plagiarism-audit/SKILL.md`
- Modify: `tests/test_plagiarism_skill_package.py`

- [ ] **Step 1: Add structural tests**

Test valid frontmatter, exact name, generic document terminology, links to all references, explicit non-verdict boundary, default continuation under incomplete corpus, and absence of stop conditions triggered only by missing sources.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_plagiarism_skill_package.py -q`

Expected: copied legacy language fails generic-format and incomplete-corpus assertions.

- [ ] **Step 3: Use this trigger-only description**

```yaml
---
name: plagiarism-audit
description: Use when checking a document against a defined source corpus for textual similarity, originality concerns, close paraphrase, patchwriting, translated overlap, or visible attribution signals, including when the corpus is incomplete.
---
```

- [ ] **Step 4: Write the decision-complete body**

Require the skill to:

- ask for target or corpus only when missing;
- accept all supported document formats and corpus providers;
- continue with any non-empty analyzable corpus;
- quantify observed overlap only within analyzed sources;
- state corpus coverage next to every score;
- preserve raw and adjusted results separately;
- keep candidate generation, verified passages, and interpretation distinct;
- refrain from misconduct, intent, authorship, legal, or institutional findings;
- refrain from substantive citation-support judgments;
- never edit the target or search the open web without authorization.

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests/test_plagiarism_skill_package.py -q
git add skills/plagiarism-audit/SKILL.md tests/test_plagiarism_skill_package.py
git commit -m "docs: generalize plagiarism audit decisions"
```

### Task 4: Generalize corpus instructions and incomplete-access behavior

**Files:**
- Modify: `skills/plagiarism-audit/references/source-corpus.md`
- Modify: `tests/test_plagiarism_skill_package.py`

- [ ] **Step 1: Add corpus invariant tests**

Assert all supported extensions and corpus routes are named; Mendeley is accurately limited to exports/accessible attachments; ambiguity lives in the main manifest; and missing sources do not cause `--fail-on-missing` unless the user explicitly requests strict automation.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_plagiarism_skill_package.py -q`

Expected: generic routes are absent before the rewrite.

- [ ] **Step 3: Rewrite `source-corpus.md` from the common contract**

Document the same extraction and mapping behavior as Citation Support Audit without copying citation-specific judgment rules. Explain that non-PDF sources use heading/paragraph/block locators and that PDF page locators remain preferred when exact page evidence is available. Require extraction quality and conversion disclosure.

- [ ] **Step 4: Define precise continuation rules**

Use this decision table:

| Target/corpus state | Result |
|---|---|
| readable target and all expected sources analyzed | complete audit |
| readable target and at least one expected source analyzed | partial audit with quantitative observed similarity |
| readable target and zero sources analyzed | diagnostic coverage report; no similarity percentage |
| unreadable target | stop substantive analysis; diagnostic report |

- [ ] **Step 5: Verify and commit**

```powershell
pytest tests/test_plagiarism_skill_package.py -q
git add skills/plagiarism-audit/references/source-corpus.md tests/test_plagiarism_skill_package.py
git commit -m "docs: generalize plagiarism corpus handling"
```

### Task 5: Make partial-corpus quantitative reporting mandatory and transparent

**Files:**
- Modify: `skills/plagiarism-audit/references/metrics-and-rules.md`
- Modify: `skills/plagiarism-audit/references/report-template.md`
- Modify: `tests/test_plagiarism_skill_package.py`

- [ ] **Step 1: Write failing metric/report invariants**

Assert the metrics reference defines analyzable target words, matched target words, raw/adjusted overall similarity, per-source similarity, category coverage, overlapping matches, and corpus coverage. Assert it explicitly requires partial-corpus quantitative results when at least one source is analyzable. Assert the report labels every percentage as complete or partial.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_plagiarism_skill_package.py -q`

Expected: the legacy stop/partial wording is too discretionary and fails the mandatory partial-report assertion.

- [ ] **Step 3: Preserve public metric formulas with explicit scope labels**

Use:

```text
observed overall similarity = unique target words matched in analyzed corpus / analyzable target words * 100
observed per-source similarity = target words matched to that analyzed source / analyzable target words * 100
match-type coverage = target words in that verified category / analyzable target words * 100
corpus coverage = analyzed expected sources / all expected sources * 100
```

Raw and adjusted calculations differ only by documented exclusions. Per-source/category percentages may overlap; overall words are counted once. For a partial corpus, prefix metrics with `Observed` and write `within the analyzed corpus`; do not estimate unseen-source similarity.

- [ ] **Step 4: Preserve interpretation constraints**

Retain public match-type and attribution-group vocabulary only with `-style` or explicit attribution, as appropriate. Forbid claims that the skill reproduces proprietary algorithms. Retain review bands only when verified as current and label them review bands, never plagiarism probabilities.

- [ ] **Step 5: Rewrite the report template**

Required order:

1. target and corpus coverage;
2. extraction/method settings and exclusions;
3. complete or partial quantitative scorecard;
4. source-level results;
5. attribution-group summary;
6. passage-level parallel evidence;
7. inaccessible sources needed for broader coverage;
8. limitations and non-verdict conclusion.

The first score table must display corpus coverage adjacent to observed similarity.

- [ ] **Step 6: Verify and commit**

```powershell
pytest tests/test_plagiarism_skill_package.py -q
git add skills/plagiarism-audit/references tests/test_plagiarism_skill_package.py
git commit -m "docs: require partial-corpus similarity reporting"
```

### Task 6: Add traceable methodology and copyright-safe attribution

**Files:**
- Modify: `skills/plagiarism-audit/SKILL.md`
- Modify: `skills/plagiarism-audit/references/methodology-and-attribution.md`
- Modify: `README.md`

- [ ] **Step 1: Refresh every external definition from authoritative sources**

Check current official sources for research-misconduct/plagiarism boundaries, similarity scores, match groups, similarity categories, and any retained review bands. Prefer ORI, Turnitin/iThenticate, Crossref, Copyleaks, and SafeAssign documentation. Record access dates and remove any definition that cannot be verified reliably.

- [ ] **Step 2: Write the attribution reference in original English**

For each adapted concept, record:

| Concept | Public source | Adaptation | Explicit non-claim |
|---|---|---|---|
| plagiarism boundary | ORI | scope and caution | no misconduct determination |
| overall/per-source similarity | iThenticate/Crossref documentation | transparent word-level formula | no product equivalence |
| match categories | Copyleaks public terminology | human-readable classification | no proprietary detector reproduction |
| attribution groups | Turnitin public terminology | visible-signal classification | no affiliation or certified compatibility |
| review bands | SafeAssign, only if still current | contextual review label | no probability or threshold |

Do not copy vendor graphics, interfaces, long passages, or code.

- [ ] **Step 3: Add the early methodological notice**

Immediately after purpose, explain independent implementation, public inspirations, source-bounded scope, and non-verdict status; link to the detailed reference.

- [ ] **Step 4: Update repository notices and commit**

Ensure README uses the same non-affiliation and no-equivalence language.

```powershell
git add README.md skills/plagiarism-audit
git commit -m "docs: attribute plagiarism audit methodology"
```

### Task 7: Forward-test and independently review the revised skill

**Files:**
- Modify: `tests/behavior/plagiarism-audit/revised-results/`
- Modify only files implicated by observed failures

- [ ] **Step 1: Run all six scenarios in isolated temporary workspaces**

Provide independent agents only the revised skill, scenario prompt, and synthetic artifacts. Do not provide expected prose or baseline conclusions.

- [ ] **Step 2: Evaluate and repair observed failures minimally**

Require all assertions to pass. If a correction changes shared corpus behavior, return to the core plan's tests and update both skills' synchronized runtimes before continuing.

- [ ] **Step 3: Run independent reviews authorized by the user**

Use separate reviewers for:

- idiomatic, precise English;
- methodology, formulas, and non-verdict boundaries;
- portability and incomplete-corpus behavior;
- copyright/licensing and attribution wording.

Verify reviewer suggestions before applying them.

- [ ] **Step 4: Run complete validation**

```powershell
pytest -q
ruff check .
pyright
$skillValidator = Join-Path $env:USERPROFILE ".codex\skills\.system\skill-creator\scripts\quick_validate.py"
python $skillValidator skills/plagiarism-audit
python tools/sync_skill_runtime.py --check skills/plagiarism-audit
```

Expected: every command exits 0.

- [ ] **Step 5: Commit**

```powershell
git add skills/plagiarism-audit tests/behavior/plagiarism-audit
git commit -m "test: verify plagiarism audit behavior"
```

### Task 8: Install recoverably and finish publication readiness

**Files:**
- Copy verified skill to: `$env:USERPROFILE\.codex\skills\plagiarism-audit`
- Move legacy skill to: `$env:USERPROFILE\.codex\skill-backups\2026-09-20\plagiarism-checker`
- Modify: `README.md`
- Create: `.gitignore`
- Create: `CHANGELOG.md`

- [ ] **Step 1: Perform the same resolved-path safety checks used for Citation Support Audit**

Do not delete the legacy folder. Move it to the dated backup only after the new skill passes validation in the repository.

- [ ] **Step 2: Install and smoke-test the new skill**

Use a synthetic HTML target and a corpus containing one readable PDF plus one missing source. Confirm the output includes an observed quantitative result, corpus coverage, the missing source, and the non-verdict statement.

- [ ] **Step 3: Finalize public repository documentation**

README must contain:

- the two exact skill names and boundaries;
- supported targets/sources and extraction-quality caveats;
- installation instructions for the complete repository and individual skill folders;
- dependency table distinguishing required Python dependencies from optional external executables;
- Mendeley export limitation and Zotero read-only behavior;
- incomplete-corpus behavior;
- methodological attribution links;
- non-affiliation, non-equivalence, non-legal-advice, and non-misconduct-verdict notices;
- test and validation commands.

Do not add screenshots, badges, logos, or marketing comparisons unless they have a defined maintenance purpose.

- [ ] **Step 4: Add release hygiene**

`.gitignore` excludes virtual environments, caches, audit outputs, copyrighted source documents, converted temporary files, and local Zotero/Mendeley data. `CHANGELOG.md` records version `0.1.0` with supported formats, providers, metric scope, and known limitations.

- [ ] **Step 5: Run the clean-clone simulation**

Copy the repository to a temporary directory without `.git`, install the package in a new virtual environment, run all tests, validate both skills, and invoke each vendored runtime with `--help`. No test may depend on the user's Zotero library or thesis files.

- [ ] **Step 6: Final repository verification**

```powershell
pytest -q
ruff check .
pyright
$skillValidator = Join-Path $env:USERPROFILE ".codex\skills\.system\skill-creator\scripts\quick_validate.py"
python $skillValidator skills/citation-support-audit
python $skillValidator skills/plagiarism-audit
python tools/sync_skill_runtime.py --check skills/citation-support-audit
python tools/sync_skill_runtime.py --check skills/plagiarism-audit
git status --short
```

Expected: all validations pass and the worktree is clean after the final commit.

- [ ] **Step 7: Commit the release candidate**

```powershell
git add .gitignore CHANGELOG.md README.md
git commit -m "release: prepare source-checker 0.1.0"
git tag -a v0.1.0 -m "Source Checker 0.1.0"
```

Do not create a GitHub repository, push, or publish a release until the user explicitly authorizes that external action.

## Final completion gate

The project is ready for user review when:

- both installed skills use exactly their new names;
- both legacy skills exist in the dated recoverable backup;
- all supported formats have tested extraction and disclosed locator quality;
- both skills continue under incomplete source access as specified;
- citation and plagiarism metrics remain separate and correctly scoped;
- all methodology and vendor-derived terminology is attributed without equivalence claims;
- independent reviews are complete;
- clean-clone tests pass;
- no user source document, Zotero/Mendeley data, audit report, or copyrighted corpus file is tracked.
