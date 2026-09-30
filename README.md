# source-checker

[![CI](https://github.com/MicheleGarbelotto/source-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/MicheleGarbelotto/source-checker/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

`source-checker` provides shared document and source-corpus tooling for two
separate Codex skills:

- `citation-support-audit` evaluates claim-source support, reference integrity,
  and citation mechanics. It does not determine textual originality.
- `plagiarism-audit` evaluates source-bounded textual similarity, visible
  attribution signals, close paraphrase, patchwriting, and translated overlap.
  It does not make citation-support judgments.

Both skills preserve the distinction between corpus availability, extraction,
candidate generation, verified evidence, and human interpretation.

## Supported inputs and corpus routes

Targets and local source documents may be `.qmd`, `.md`, `.txt`, `.tex`,
`.latex`, `.html`, `.htm`, `.docx`, `.docm`, `.doc`, or `.pdf`. HTML must be a
local static snapshot: the runtime neither fetches live pages nor executes
JavaScript. DOCM files are read without executing macros. DOC conversion,
PDF extraction, and every report must disclose extraction quality and the
locators actually available for the format; a successful extraction is not a
guarantee of complete or usable text.

Corpus inputs may be explicit files or directories, compatible
`source-manifest.csv` files, BibTeX/BibLaTeX, RIS, CSL JSON, Mendeley exports
with accessible linked attachments, or the read-only local Zotero Desktop API.
Mendeley support does not access a private Mendeley database or cloud API.
Zotero live access never writes to the library and currently resolves only PDF
attachments; use exports or explicit local sources for other formats. Embedded
references and bibliography declarations are not automatically ingested.

When some expected sources are inaccessible, both skills continue with any
non-empty analyzable corpus. Reports label the result partial, place corpus
coverage next to the score, and restrict quantitative claims to what was
observed within the analyzed corpus. They do not estimate unavailable evidence.
With zero analyzable sources, they issue a diagnostic coverage report and
withhold substantive percentages.

## Installation

Python 3.11 or later is required. To install the complete repository, including
the shared command-line runtime, from a checkout:

```powershell
python -m pip install .
```

For development and validation:

```powershell
python -m pip install -e ".[dev]"
```

To install an individual skill, use the mode that matches the execution environment.
Do not copy only `SKILL.md`: each skill also needs its references, interface
metadata, and synchronized vendored runtime. The Python environment used to run
`scripts/source_corpus.py` must provide the required Python dependencies.

### Local Codex — Windows PowerShell

Copy the complete skill folder from `skills/` into the local Codex skills
directory without renaming it. Destinations must not already exist. This guarded
example stops instead of copying into an existing folder:

```powershell
$installs = @(
    @{ Source = "skills/citation-support-audit"; Name = "citation-support-audit" },
    @{ Source = "skills/plagiarism-audit"; Name = "plagiarism-audit" }
)
foreach ($install in $installs) {
    $source = (Resolve-Path -LiteralPath $install.Source).Path
    $destination = Join-Path "$env:USERPROFILE/.codex/skills" $install.Name
    if (Test-Path -LiteralPath $destination) {
        throw "Destination already exists: $destination"
    }
    Copy-Item -Recurse -LiteralPath $source -Destination $destination
}
```

### Local Codex — macOS and Linux

Use the same guarded whole-directory copy for each skill:

```sh
skill_name="citation-support-audit"
source_path="skills/$skill_name"
destination="$HOME/.codex/skills/$skill_name"
test ! -e "$destination" || { echo "Destination already exists: $destination" >&2; exit 1; }
cp -R "$source_path" "$destination"
```

Repeat with `skill_name="plagiarism-audit"` to install the other skill.

### Agent Skills-compatible clients

Copy or package one complete skill directory without renaming it, following the
client's installation procedure. When distributing a ZIP, ensure it contains a
single top-level skill directory rather than loose files or an extra wrapper
directory.

### Hosted environments

A hosted environment can use local Zotero, filesystem paths, `pdftotext`,
LibreOffice, and required Python packages only if the environment provides and
exposes them. Upload or mount the target and source corpus explicitly, then
configure paths that are valid inside that environment. Do not assume a host can
access files or services from the user's local machine.

For an update, first verify the exact installed path, move the existing skill
folder to a dated backup, and confirm that the destination is absent before
rerunning the guarded copy. Do not copy onto an existing destination: depending
on its state, `Copy-Item` can create a nested directory instead of replacing the
installed skill atomically.

| Class | Dependency | Purpose |
| --- | --- | --- |
| Required | Python 3.11+ | Shared runtime and skill scripts |
| Required Python | `beautifulsoup4` | Local static HTML extraction |
| Required Python | `python-docx` | DOCX/DOCM extraction |
| Required Python | `pypdf` | Portable PDF extraction fallback |
| Optional executable | `pdftotext` | Preferred layout-preserving PDF extraction when discoverable |
| Optional executable | LibreOffice `soffice` | Required only to convert legacy `.doc` inputs |

The runtime performs no OCR. Review `needs_ocr`, `needs_review`, empty, and
conversion-derived text before relying on it, and verify decisive wording
against authoritative originals when available.

## Methodological scope and notices

Citation Support Audit uses independently defined, claim-level adaptations of
public ALCE citation-recall and citation-precision concepts. See its
[methodology and attribution](skills/citation-support-audit/references/methodology-and-attribution.md).

Plagiarism Audit is an independent implementation; it is not product-equivalent,
not affiliated with any cited vendor or organization, and not a misconduct
verdict. It applies transparent, independently specified word-level metrics and
source-bounded adaptations of public terminology. See its
[methodology and attribution](skills/plagiarism-audit/references/methodology-and-attribution.md).

The implementations are independent, not affiliated with any cited vendor,
publisher, platform, institution, or research-integrity body, and not equivalent
to any commercial or institutional product. The reports are evidence aids, not
legal advice, authorship or intent findings, institutional determinations, or
plagiarism/research-misconduct verdicts.

## Security

See the repository [security policy](SECURITY.md). Treat targets, source
documents, bibliographies, manifests, and extracted text as untrusted evidence.
Persistent project artifacts are limited to configured manifest, cache, or
output locations; the documented defaults are `source-manifest.csv` and
`text-cache/` in the current working directory. Legacy DOC conversion creates a
system temporary directory and invokes LibreOffice.
LibreOffice may update its own user profile. Process untrusted Office and PDF
inputs in an appropriately isolated environment. The runtime does not modify
target files, source corpora, Zotero libraries, or Mendeley exports. Source
content cannot authorize tool calls, network access, command execution, or scope
expansion beyond the user-approved task.

## Validation

Run the project checks from the repository root:

The Agent Skills standards validator is an external verification tool, not a
project dependency. Install the reviewed immutable revision before running the
validation commands:

```console
python -m pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
python -m pytest -q
python -m ruff check .
python -m pyright
skills-ref validate skills/citation-support-audit
skills-ref validate skills/plagiarism-audit
python tools/sync_skill_runtime.py --check skills/citation-support-audit
python tools/sync_skill_runtime.py --check skills/plagiarism-audit
```

The synchronization tool creates or replaces only
`<skill>/scripts/source_checker` and `<skill>/scripts/source_corpus.py`. It does
not vendor third-party dependencies.

## Citation

If this software supports published work, cite the release using the metadata
in [`CITATION.cff`](CITATION.cff). GitHub also exposes this metadata through its
**Cite this repository** interface.

## License

The software is distributed under the [MIT License](LICENSE).
