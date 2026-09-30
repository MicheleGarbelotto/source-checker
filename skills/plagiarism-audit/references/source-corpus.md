# Source corpus, adaptive intake, and text cache

Use the bundled `scripts/source_corpus.py` to generate the main `source-manifest.csv` and derived source text. The runtime is synchronized from the shared `source_checker` package; do not maintain a separate extraction implementation in this skill. The manifest inventories source identity, mappings, extraction, and availability. It is an audit aid, not evidence of textual overlap or plagiarism.

Persistent project artifacts are limited to manifest, cache, or output
locations configured for the run, including documented defaults when options
are omitted. The default manifest output is `source-manifest.csv` when the
`manifest` command omits `--output`, and the default `--cache-dir` is
`text-cache/`; both are relative to the current working directory. Legacy DOC
conversion creates an intermediate DOCX in the system temporary directory, and
LibreOffice may update its user profile outside the configured project
locations. These temporary and external-tool side effects do not modify the
target, source corpus, Zotero library, or Mendeley export. `pdftotext` and
LibreOffice are invoked only for the documented PDF and legacy DOC extraction
routes; treat untrusted office and PDF files as parser inputs and use an
appropriately isolated environment when their origin is unknown.

## Adaptive intake and continuation

Use information already supplied or available in authorized inputs before asking questions. Do not require a separate mapping file from the user. Build working mappings during intake and retain them in the main manifest.

| Missing information | Required action |
| --- | --- |
| Target | Ask only for the file(s). |
| Corpus | Ask where the sources are available. |
| Specific mapping ambiguity | Present the candidates and ask only for that match; continue independent checks. |
| Inaccessible source | Continue with accessible evidence and record its availability or extraction status. |
| Unreadable target | Stop substantive analysis of that target and issue a diagnostic report describing the extraction failure and what input is needed. |

Apply the following result routes from top to bottom:

| Target/corpus state | Result |
| --- | --- |
| readable target, expected sources > 0, and all expected sources analyzed | complete expected-source-set coverage audit |
| readable target and at least one expected source analyzed | partial audit with quantitative observed similarity |
| readable target and zero sources analyzed | diagnostic coverage report; no similarity percentage |
| unreadable target | stop substantive analysis; diagnostic report |

The quantitative result for a partial audit describes observed similarity only within the analyzed sources. It does not estimate similarity to unavailable sources. Missing, inaccessible, ambiguous, or unusable sources do not by themselves stop work when at least one expected source can be analyzed.

## Supported inputs and corpus routes

The tooling supports target and source documents in `.qmd`, `.md`, `.txt`, `.tex`, `.latex`, local static `.html` and `.htm`, `.docx`, `.docm`, legacy `.doc`, and `.pdf`. These are extraction routes, not guarantees of complete or usable text. HTML inputs must be local snapshots; the runtime does not fetch live pages or execute JavaScript. Legacy `.doc` extraction requires a discoverable `soffice` executable for LibreOffice conversion. PDF extraction prefers a discoverable `pdftotext` executable and falls back to `pypdf`. Macro-enabled `.docm` content is read without executing macros.

Combine any applicable corpus routes:

- Local files and directories: use `--source`. Directories are searched recursively for supported document extensions, excluding the selected cache directory.
- BibTeX and BibLaTeX (`.bib`), RIS (`.ris`), and CSL JSON (`.json`): use `--bibliography` for explicit export files. Bibliographic metadata identifies works; only accessible linked local attachments provide text for comparison.
- Mendeley exports: use BibTeX, BibLaTeX, RIS, or CSL JSON exports plus accessible local attachments. Mendeley support does not access a private Mendeley database and provides no Mendeley cloud API integration.
- Zotero: use a supported export or optionally add `--zotero-live` for the read-only local Zotero Desktop API. The current live resolver is PDF-attachment-only; use an export or explicit `--source` for other supported local formats. Do not write to the library.
- Existing `source-manifest.csv`: use `--manifest` to import compatible source records, paths, and mapping provenance. It is an optional input as well as the generated inventory, not a user-supplied prerequisite.
- Embedded bibliography or references: inspect the target to identify entries and mapping candidates. The runtime does not automatically ingest an embedded bibliography or a document bibliography declaration. Supply identified records through an explicit supported bibliography export or compatible `source-manifest.csv`, preserve their origin, and disclose manual transcription.

Bibliographic metadata without accessible full text can establish an expected source but cannot supply passages for similarity analysis. Do not describe visible references or export records as analyzed full text.

## Generate or refresh the manifest

Run from the project directory and substitute the actual paths. The bundled script imports its bundled sibling `source_checker` runtime and does not vendor third-party packages, so install the runtime dependencies in the Python environment first.

```text
python "<skill-dir>/scripts/source_corpus.py" manifest --target "<target-document>" --source "<source-directory>" --bibliography "<references.bib>" --output "<audit-dir>/source-manifest.csv" --cache-dir "<audit-dir>/text-cache"
```

Use only applicable inputs. Repeat `--target`, `--source`, `--bibliography`, or `--manifest` for multiple inputs. `manifest` requires at least one `--target`; target paths may also be directories of supported files. Add `--manifest "<existing-manifest.csv>"` to import an inventory or `--zotero-live` to enrich mappings from Zotero Desktop. Keep selected targets aligned with the user's audit scope.

Refresh cached source text from a manifest with:

```text
python "<skill-dir>/scripts/source_corpus.py" cache --manifest "<audit-dir>/source-manifest.csv" --cache-dir "<audit-dir>/text-cache" --output "<audit-dir>/source-manifest.csv"
```

Use `manifest --help` or `cache --help` to check the installed runtime. `--force` bypasses cache reuse. The default is partial-tolerant and continues despite source gaps. Use `--fail-on-missing` only for user-requested strict automation. Strict mode exits 2 when the manifest has zero expected rows or any row is unresolved, ambiguous, missing its artifact, or has an unusable extraction status or text quality; target extraction diagnostics also exit 2 independently of the flag. These are row-based runtime conditions, not a distinct-source audit denominator. The flag changes exit behavior; it does not make missing sources analyzable or justify a similarity finding. When there are zero expected rows, the JSON summary reports `coverage_percent` as `null` rather than treating the empty set as complete.

The cache is incremental. Reuse derived text only when the recorded source hash matches the canonical artifact. Refresh after source changes and force regeneration when extraction settings or methods change. The JSONL cache preserves original and normalized text, `locator_type`, `locator_value`, extraction method, and text quality. Direct extractors populate headings and conversion context, but the current JSONL cache omits `TextBlock.heading` and `conversion_note`. Cached `locator_type` and `locator_value` remain available; heading and conversion context require direct re-extraction or authoritative-source inspection. Normalized text supports retrieval and screening; it is not final quotation evidence.

## Mapping and extraction behavior

The common mapping layer defines this deterministic precedence: normalized DOI; exact identifier, citekey, manager ID, or alias; normalized title-author-year; normalized title; and a filename rule using case-insensitive basename comparison from supplied filename inputs to each source record's `local_files` entries. The current manifest CLI supplies only extracted citation identifiers to that mapping step. Keyless visible citations use `visible:<hash>` and remain unresolved. Title-author-year, title, and filename rules remain available in the common mapping precedence, but the current manifest CLI path does not automatically exercise them without compatible imported or source metadata. Keep `mapping_status` distinct from `extraction_status` and later similarity judgments:

- `resolved`: one source is identified.
- `ambiguous`: multiple plausible sources remain.
- `unresolved`: no deterministic match is established.
- `not-applicable`: for example, an explicit corpus source has no target mapping.

Keep every mapping ambiguity in the main `source-manifest.csv`, including its `candidate_source_ids` and conflicts. For Zotero live ambiguity, unavailability, no match, or an error, keep the affected citation row unresolved (ambiguous when multiple candidates exist), set `mapping_rule` to `zotero-live`, and retain a status diagnostic in `conflicts`. An `attachment_unresolved` outcome contains valid bibliographic identity: retain its source record so title, DOI, item identity, and mapping behave normally; record the absent attachment through extraction or artifact status and add the Zotero live diagnostic to `conflicts`. Do not create a separate unresolved-mapping artifact, file, or manifest, and do not silently select a plausible candidate.

Current extraction outcomes include `not_run`, `extracted`, `missing`, `empty`, `needs_ocr`, `needs_review`, `unusable`, and `error:<ExceptionName>`. Preserve the actual status and keep `text_quality` separate. Detailed extraction errors are not retained in the CSV manifest or ordinary runtime summary, so separately record any diagnostic needed for the audit. Imported manifests may contain legacy values such as `cached` or `unknown`; cache reuse retains the stored status rather than creating a new `cached` status.

The PDF extractor does not perform OCR. `needs_ocr` is a quality signal, not proof that OCR will recover all content. Inspect degraded, empty, or unusable extraction before relying on it. A successful command or generated manifest does not establish usable text or complete corpus coverage.

Inspect manifest rows before defining audit denominators. Retain source identities, aliases, paths, hashes, target locators, mapping rules, candidate source IDs, conflicts, extraction statuses, text quality, and cache paths. Runtime summary counts are manifest-row diagnostics and are not automatically the distinct expected-source counts used in an audit report.

## Locator fidelity and extraction disclosure

For non-PDF sources, use the available heading, paragraph, and block locators rather than inventing pagination:

- `.qmd` and `.md`: source line ranges and available headings; `.txt`: source line numbers.
- `.tex` and `.latex`: source line numbers or citation line ranges and recognized section headings. These are not rendered page numbers, and extraction is not TeX compilation.
- `.html` and `.htm`: ordered HTML blocks, element IDs when present, and available headings. These identify the local snapshot, not a stable live-page position.
- `.docx` and `.docm`: document body paragraph indices and recognized headings. The adapter does not provide rendered pagination or comprehensive coverage of tables, footnotes, and other Word parts.
- `.doc`: paragraph locators from the converted DOCX. Verify decisive wording against the original where accessible.
- `.pdf`: physical PDF page and within-page block, such as `page=3;block=2`. Printed page labels may differ and must be checked separately.

PDF page locators remain preferred when exact page evidence exists. Do not equate source lines, paragraphs, physical PDF pages, and printed page labels. Preserve format-specific locators with enough surrounding context to assess each retained match.

Disclose extraction quality, the extraction method, known omissions, and any separately performed OCR. Disclose conversion details for converted formats and verify decisive wording against authoritative originals when available. Report the manifest path, corpus boundary, expected and analyzed sources, unavailable sources, mapping conflicts, extraction failures, and which decisive passages were checked against authoritative artifacts.
