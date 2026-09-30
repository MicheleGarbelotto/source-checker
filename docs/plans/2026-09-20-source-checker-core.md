# Source Checker Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and package the format-neutral document, bibliography, source-resolution, manifest, and cache infrastructure shared by Citation Support Audit and Plagiarism Audit.

**Architecture:** A canonical Python package under `src/source_checker` owns all runtime behavior. Each published skill receives a synchronized vendored runtime copy so it remains independently installable. Format adapters emit one neutral document model; manifests and audit skills never branch directly on file type.

**Tech Stack:** Python 3.11+, standard library, `beautifulsoup4`, `python-docx`, `pypdf`, optional Pandoc/LibreOffice/Poppler executables, pytest, Ruff, Pyright.

---

## File map

Create these files:

```text
source-checker/
├── LICENSE
├── README.md
├── pyproject.toml
├── src/source_checker/
│   ├── __init__.py
│   ├── cache.py
│   ├── citations.py
│   ├── cli.py
│   ├── manifest.py
│   ├── mapping.py
│   ├── model.py
│   ├── normalize.py
│   ├── bibliography/
│   │   ├── __init__.py
│   │   ├── bibtex.py
│   │   ├── csl_json.py
│   │   └── ris.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── html.py
│   │   ├── latex.py
│   │   ├── markup.py
│   │   ├── office.py
│   │   └── pdf.py
│   └── resolvers/
│       ├── __init__.py
│       ├── exports.py
│       ├── local.py
│       └── zotero.py
├── tests/
│   ├── fixtures/
│   │   ├── bibliographies/
│   │   ├── documents/
│   │   └── pdfs/
│   ├── test_bibliography.py
│   ├── test_cache.py
│   ├── test_cli.py
│   ├── test_extractors.py
│   ├── test_manifest.py
│   └── test_mapping.py
└── tools/
    └── sync_skill_runtime.py
```

The later skill plans create `skills/citation-support-audit` and `skills/plagiarism-audit`. Do not create either skill while executing this core plan.

### Task 1: Initialize the repository and record the legacy baseline

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `LICENSE`
- Create: `tests/fixtures/legacy-baseline.json`

- [ ] **Step 1: Initialize Git without touching the installed skills**

Run:

```powershell
git init
git branch -M main
```

Expected: an empty repository on branch `main` under the chosen repository root.

- [ ] **Step 2: Capture the current tests and identical-script invariant**

Run:

```powershell
python -m unittest discover -s "$env:USERPROFILE\.codex\skills\citation-checker\scripts\tests" -v
python -m unittest discover -s "$env:USERPROFILE\.codex\skills\plagiarism-checker\scripts\tests" -v
```

Expected: both suites run 3 tests and return `OK`.

Record this JSON exactly in `tests/fixtures/legacy-baseline.json`:

```json
{
  "citation_checker_tests": 3,
  "plagiarism_checker_tests": 3,
  "legacy_source_corpus_sha256": "0d3ac8720615db13bb014ba69d270083c639fddb5677e434782da9ff951d7f0d",
  "preserved_behaviors": [
    "Pandoc citekeys retain first-seen order and heading provenance",
    "CSV aliases merge into one cited-source manifest",
    "resolved PDFs receive SHA-256 hashes",
    "missing sources remain explicit manifest rows",
    "PDF caches are page-and-block addressable",
    "unchanged PDF hashes reuse the existing cache"
  ]
}
```

- [ ] **Step 3: Add project configuration**

Create `pyproject.toml` with:

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "source-checker"
version = "0.1.0"
description = "Shared document and source-corpus tooling for citation support and plagiarism audits"
requires-python = ">=3.11"
license = { text = "MIT" }
dependencies = [
  "beautifulsoup4>=4.12",
  "python-docx>=1.1",
  "pypdf>=5.0"
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.7", "pyright>=1.1"]

[project.scripts]
source-checker-corpus = "source_checker.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pyright]
include = ["src", "tests", "tools"]
pythonVersion = "3.11"
```

- [ ] **Step 4: Add publication boundary documents**

Use the standard MIT license text in `LICENSE`. In `README.md`, state only the repository purpose, the two final skill names, supported input classes, installation status as pre-release, independent-implementation/non-affiliation notice, and the fact that neither skill makes a misconduct determination. Do not document unfinished commands.

- [ ] **Step 5: Commit the baseline**

```powershell
git add LICENSE README.md pyproject.toml tests/fixtures/legacy-baseline.json docs
git commit -m "chore: establish source-checker baseline"
```

### Task 2: Define the neutral document model and normalization rules

**Files:**
- Create: `src/source_checker/__init__.py`
- Create: `src/source_checker/model.py`
- Create: `src/source_checker/normalize.py`
- Create: `tests/test_model.py`

- [ ] **Step 1: Write the failing model tests**

Create tests asserting this public API:

```python
from source_checker.model import CitationMention, DocumentRecord, TextBlock
from source_checker.normalize import normalize_text


def test_document_record_serializes_format_neutral_locators():
    block = TextBlock(
        block_id="b1",
        text_original="A cited claim.",
        text_normalized="a cited claim.",
        locator_type="paragraph",
        locator_value="12",
        heading="Results",
    )
    citation = CitationMention(
        raw_text="(Alpha, 2020)",
        citation_keys=("alpha2020",),
        locator_type="paragraph",
        locator_value="12",
        mapping_status="resolved",
    )
    document = DocumentRecord(
        document_id="target-1",
        role="target",
        path="draft.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        sha256="abc",
        extraction_method="python-docx",
        extraction_status="extracted",
        text_quality="good",
        conversion_note="",
        blocks=(block,),
        citations=(citation,),
    )
    assert document.to_dict()["blocks"][0]["locator_type"] == "paragraph"


def test_normalize_text_preserves_original_only_in_caller():
    assert normalize_text("inter-\nnational  TEST") == "international test"
```

- [ ] **Step 2: Run the tests and verify RED**

Run: `pytest tests/test_model.py -q`

Expected: collection fails because `source_checker.model` does not exist.

- [ ] **Step 3: Implement immutable dataclasses and normalization**

Implement exactly three frozen dataclasses with the fields shown in the design specification. Validate `role`, `mapping_status`, non-empty locator type/value, and unique block IDs in `DocumentRecord.__post_init__`. Implement `to_dict()` using `dataclasses.asdict`. Port the legacy NFKC, line-break dehyphenation, whitespace collapse, and case-fold behavior into `normalize_text`.

- [ ] **Step 4: Run model tests and the legacy suite**

Run:

```powershell
pytest tests/test_model.py -q
python -m unittest discover -s "$env:USERPROFILE\.codex\skills\citation-checker\scripts\tests" -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/source_checker tests/test_model.py
git commit -m "feat: define neutral document records"
```

### Task 3: Implement markup, LaTeX, and local HTML extraction

**Files:**
- Create: `src/source_checker/citations.py`
- Create: `src/source_checker/extractors/__init__.py`
- Create: `src/source_checker/extractors/markup.py`
- Create: `src/source_checker/extractors/latex.py`
- Create: `src/source_checker/extractors/html.py`
- Create: `tests/test_extractors.py`
- Create: `tests/fixtures/documents/sample.qmd`
- Create: `tests/fixtures/documents/sample.tex`
- Create: `tests/fixtures/documents/sample.html`

- [ ] **Step 1: Write failing parametrized extraction tests**

The tests must assert:

```python
@pytest.mark.parametrize(
    ("filename", "locator_type", "key"),
    [
        ("sample.qmd", "line", "alpha2020"),
        ("sample.tex", "line", "beta2021"),
        ("sample.html", "html-block", "gamma2022"),
    ],
)
def test_structured_formats_emit_common_blocks_and_citations(filename, locator_type, key):
    document = extract_document(FIXTURES / filename, role="target")
    assert document.blocks
    assert document.blocks[0].locator_type == locator_type
    assert key in {item for citation in document.citations for item in citation.citation_keys}
```

Add separate tests proving that fenced code in Markdown, commented LaTeX citations, and HTML `script`, `style`, `nav`, and `template` nodes do not become prose or citations.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_extractors.py -q`

Expected: failure because `extract_document` and adapters do not exist.

- [ ] **Step 3: Implement the dispatcher and three adapters**

`extract_document(path, role)` dispatches by lowercase suffix and raises `UnsupportedFormatError` with the supported extension list. Preserve the legacy Pandoc `@citekey` pattern and heading tracking for QMD/Markdown. Parse LaTeX `\\cite`, `\\citep`, `\\citet`, `\\autocite`, `\\parencite`, `\\textcite`, and their starred/optional-argument variants while removing `%` comments outside escaped `\%`. Parse static HTML with BeautifulSoup; remove non-content elements; honor `data-cites`; otherwise retain visible citation text with an empty key tuple.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_extractors.py tests/test_model.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/source_checker tests/test_extractors.py tests/fixtures/documents
git commit -m "feat: extract markup latex and html documents"
```

### Task 4: Implement Word, legacy DOC, and PDF extraction

**Files:**
- Create: `src/source_checker/extractors/office.py`
- Create: `src/source_checker/extractors/pdf.py`
- Modify: `src/source_checker/extractors/__init__.py`
- Modify: `tests/test_extractors.py`
- Create: `tests/fixtures/documents/sample.docx`
- Create: `tests/fixtures/documents/sample.docm`
- Create: `tests/fixtures/pdfs/two-page.pdf`

- [ ] **Step 1: Add failing tests**

Test that DOCX and DOCM extraction returns paragraph locators, visible text, headings, and non-executed field-code citations. Test that a mocked LibreOffice runner receives an explicit temporary output directory for `.doc`. Test that PDF extraction preserves physical page and block values, prefers `pdftotext`, falls back to `pypdf`, and labels sparse text `needs_ocr` without invoking OCR.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_extractors.py -q`

Expected: failures for unsupported `.docx`, `.docm`, `.doc`, and `.pdf`.

- [ ] **Step 3: Implement Office extraction safely**

Use `python-docx` for paragraphs/headings and `zipfile` plus `xml.etree.ElementTree` for visible OOXML field results. Never import or execute VBA. For `.doc`, invoke:

```text
soffice --headless --convert-to docx --outdir <temporary-directory> <input.doc>
```

Read only the converted file, record `conversion_note="Converted from .doc with LibreOffice"`, and delete the temporary directory through `TemporaryDirectory` cleanup.

- [ ] **Step 4: Port PDF behavior**

Preserve the existing `pdftotext -layout -enc UTF-8` preference, `pypdf` fallback, physical-page splitting, block splitting, quality assessment, and explicit `needs_ocr` state. Generalize the emitted records to `DocumentRecord` without changing the legacy normalization semantics.

- [ ] **Step 5: Run all extractor tests**

Run: `pytest tests/test_extractors.py -q`

Expected: all tests pass; no macro or OCR process is started.

- [ ] **Step 6: Commit**

```powershell
git add src/source_checker tests/test_extractors.py tests/fixtures
git commit -m "feat: extract office and pdf documents safely"
```

### Task 5: Load bibliographic exports and resolve local/Mendeley/Zotero sources

**Files:**
- Create: `src/source_checker/bibliography/__init__.py`
- Create: `src/source_checker/bibliography/bibtex.py`
- Create: `src/source_checker/bibliography/ris.py`
- Create: `src/source_checker/bibliography/csl_json.py`
- Create: `src/source_checker/resolvers/__init__.py`
- Create: `src/source_checker/resolvers/exports.py`
- Create: `src/source_checker/resolvers/local.py`
- Create: `src/source_checker/resolvers/zotero.py`
- Create: `tests/test_bibliography.py`
- Create: `tests/fixtures/bibliographies/sample.bib`
- Create: `tests/fixtures/bibliographies/sample.ris`
- Create: `tests/fixtures/bibliographies/sample.json`

- [ ] **Step 1: Write failing bibliography tests**

Use one synthetic source represented in all three formats. Assert the common output contains `source_id`, aliases, title, authors, year, DOI, linked file paths, and provider. Include Mendeley-style `file` fields and Zotero-style citation keys as data variations, not separate record types.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_bibliography.py -q`

Expected: import failure for the bibliography package.

- [ ] **Step 3: Implement export loaders**

Implement minimum complete field parsing for BibTeX/BibLaTeX, RIS, and CSL JSON. Resolve relative linked-file paths against the export file's parent. Do not open a Mendeley database or claim Mendeley API access.

- [ ] **Step 4: Port the Zotero client as an optional resolver**

Keep the legacy read-only base URL, status check, exact citation-key resolution, item-key route, child attachment resolution, ambiguity behavior, and `--require-zotero` semantics. Rename Zotero-specific output fields as aliases inside the neutral source record while retaining them in the CSV manifest for traceability.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_bibliography.py -q`

Expected: all tests pass without a live Zotero or Mendeley installation.

- [ ] **Step 6: Commit**

```powershell
git add src/source_checker tests/test_bibliography.py tests/fixtures/bibliographies
git commit -m "feat: resolve bibliography exports and source managers"
```

### Task 6: Implement deterministic mapping and the generalized manifest

**Files:**
- Create: `src/source_checker/mapping.py`
- Create: `src/source_checker/manifest.py`
- Create: `tests/test_mapping.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 1: Write failing mapping tests**

Cover the ordered rules: DOI, citekey/manager ID, title-author-year, unique title, and unique filename metadata. Assert that two equally plausible sources yield `ambiguous` with both candidate IDs, never the first candidate. Assert that unresolved citations and uncited explicit corpus sources remain manifest rows.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_mapping.py tests/test_manifest.py -q`

Expected: failure because mapping and manifest modules do not exist.

- [ ] **Step 3: Implement source identity and matching**

Use normalized Unicode title tokens, normalized DOI values, case-insensitive citekeys, and normalized family-name/year fingerprints. Return a structured `MappingResult(status, source_ids, rule, confidence_note)`; do not use probabilistic confidence scores.

- [ ] **Step 4: Implement `source-manifest.csv`**

Retain legacy columns needed for compatibility and add neutral fields:

```text
source_id, provider, bibliography_key, aliases, title, authors, year, doi,
source_path, media_type, source_sha256, target_files, target_locators,
mapping_status, mapping_rule, candidate_source_ids, extraction_status,
text_quality, cache_path, conflicts
```

Write atomically. Store ambiguity in `mapping_status` and `candidate_source_ids`. Do not create an auxiliary unresolved-mapping file.

- [ ] **Step 5: Verify compatibility**

Run:

```powershell
pytest tests/test_mapping.py tests/test_manifest.py -q
python -m unittest discover -s "$env:USERPROFILE\.codex\skills\citation-checker\scripts\tests" -v
```

Expected: new and legacy tests pass.

- [ ] **Step 6: Commit**

```powershell
git add src/source_checker tests/test_mapping.py tests/test_manifest.py
git commit -m "feat: build format-neutral source manifests"
```

### Task 7: Generalize the incremental cache and CLI

**Files:**
- Create: `src/source_checker/cache.py`
- Create: `src/source_checker/cli.py`
- Create: `tests/test_cache.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing cache and CLI tests**

Assert that every cached block contains document hash, source ID, original/normalized text, locator type/value, extraction method/status, and quality. Assert unchanged hashes skip extraction. Assert one failed source does not discard successful sources. Assert the default exit code is zero for a partial corpus and `--fail-on-missing` returns 2.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_cache.py tests/test_cli.py -q`

Expected: import or command failures.

- [ ] **Step 3: Implement cache and CLI compatibility**

Keep subcommands `manifest` and `cache`. Generalize `--target`, add repeatable `--source`, repeatable `--bibliography`, and retain repeatable `--manifest`. Keep `--zotero-live`, `--require-zotero`, and `--fail-on-missing`. Print JSON summaries with `expected`, `resolved`, `extracted`, `analyzed`, `missing`, `ambiguous`, `unusable`, and `coverage_percent`.

- [ ] **Step 4: Run full tests and static checks**

Run:

```powershell
pytest -q
ruff check .
pyright
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit**

```powershell
git add src/source_checker tests
git commit -m "feat: add generalized corpus cache and cli"
```

### Task 8: Add reproducible skill-runtime packaging

**Files:**
- Create: `tools/sync_skill_runtime.py`
- Create: `tests/test_runtime_sync.py`
- Modify: `README.md`

- [ ] **Step 1: Write a failing synchronization test**

The test creates a temporary mock skill directory, calls `sync_runtime`, imports the vendored `source_checker` package from that directory, and verifies its version and CLI entry point without the repository root on `sys.path`.

- [ ] **Step 2: Run and verify RED**

Run: `pytest tests/test_runtime_sync.py -q`

Expected: failure because `sync_skill_runtime.py` does not exist.

- [ ] **Step 3: Implement deterministic synchronization**

`sync_skill_runtime.py` copies `src/source_checker` to `<skill>/scripts/source_checker` and writes a thin `<skill>/scripts/source_corpus.py` that calls `source_checker.cli.main`. Remove the destination runtime before copying only after resolving and verifying that it is inside a supplied skill directory. Provide `--check` mode that compares file hashes without writing.

- [ ] **Step 4: Test packaging**

Run:

```powershell
pytest tests/test_runtime_sync.py -q
python tools/sync_skill_runtime.py --help
```

Expected: tests pass and help describes sync/check modes.

- [ ] **Step 5: Document only stable developer commands**

Update `README.md` with environment setup, `pytest -q`, static checks, and runtime synchronization. Keep user-facing installation instructions out until at least one complete skill exists.

- [ ] **Step 6: Final core verification and commit**

Run:

```powershell
pytest -q
ruff check .
pyright
git status --short
```

Expected: all checks pass; status contains only intended documentation changes, if any.

Commit:

```powershell
git add README.md tools tests
git commit -m "build: package self-contained skill runtimes"
```

## Core completion gate

Do not start the Citation Support Audit plan until:

- all core tests and static checks pass;
- every supported extension has a fixture-based test;
- partial corpus is the default non-failing behavior;
- the manifest contains ambiguities without a second mapping artifact;
- a vendored runtime imports in isolation;
- installed legacy skill directories remain unchanged.
