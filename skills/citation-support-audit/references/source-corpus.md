# Source corpus, adaptive intake, and text cache

Use the bundled `scripts/source_corpus.py` to generate `source-manifest.csv` and derived source text. The runtime is synchronized from the shared `source_checker` package; do not maintain a separate extraction implementation in this skill. A manifest inventories sources and mappings; it does not establish that a source supports a claim.

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

## Adaptive intake

Use information already supplied or available in the authorized inputs before asking questions. Do not require a separate mapping file from the user. Build the working mappings during intake and retain them in the generated manifest.

| Missing information | Required action |
| --- | --- |
| Target | Ask only for the file(s). |
| Corpus | Ask where the sources are available. |
| Specific mapping ambiguity | Present the candidates and ask only for that match; continue independent checks. |
| Inaccessible source | Continue with accessible evidence and record its availability or extraction status. |
| Unreadable target | Stop substantive analysis of that target and issue a diagnostic report describing the extraction failure and what input is needed. |

Use the complete audit default unless the user has already requested a narrower scope.

An unreadable target prevents claim-level assessment of that target; it does not justify findings about its claims. Source availability is a separate issue: retain unresolved citations and inaccessible sources in coverage reporting instead of treating them as unsupported claims.

## Supported inputs and corpus routes

The tooling supports target and source documents in `.qmd`, `.md`, `.txt`, `.tex`, `.latex`, local static `.html`/`.htm`, `.docx`, `.docm`, legacy `.doc`, and `.pdf`. These are extraction routes, not a guarantee of complete or usable text. HTML inputs must be local snapshots; the core does not fetch live pages or execute JavaScript. Legacy `.doc` extraction requires LibreOffice conversion. Macro-enabled `.docm` content is read without executing macros.

Sources may come from local directories or explicit files, bibliography exports, compatible CSV manifests, or optional read-only Zotero Desktop resolution. Combine routes when necessary:

- Local files and directories: use `--source`. Directories are searched recursively for supported document extensions, excluding the selected cache directory. Local file stems supply aliases; descriptive filenames alone may not resolve citation identifiers.
- BibTeX/BibLaTeX (`.bib`), RIS (`.ris`), and CSL JSON (`.json`): use `--bibliography` for explicit export files. Bibliographic metadata identifies works; accessible linked local attachments provide their text. An export without accessible attachments is not a full-text corpus.
- Mendeley exports: use BibTeX/BibLaTeX, RIS, or CSL JSON exports plus accessible attachments. This route does not access a private Mendeley database or imply a live Mendeley integration.
- Zotero: use a supported export, or optionally add `--zotero-live` for the read-only local Desktop API. The current `--zotero-live` resolver is PDF-only for linked attachments; use an export or explicit `--source` input for other supported local formats. Zotero availability is not a prerequisite for local corpus work. Do not write to the library.
- Existing `source-manifest.csv`: use `--manifest` to import compatible source records, paths, and mapping provenance. This is an optional input as well as the normal generated inventory, not a user-supplied prerequisite.
- Embedded bibliography or references: inspect the supplied target to identify entries and mapping candidates. The current core CLI does not automatically ingest embedded bibliographies, including a document's bibliography declaration. Supply the identified records through an explicit supported bibliography export or compatible CSV manifest, preserving their origin and disclosing any manual transcription. Do not describe visible reference text as automatically resolved source records.

The CLI maps extracted explicit citation identifiers against available source records. Visible author-year citations without identifiers can remain unresolved even when the source is in the corpus; inspect the bibliography and candidate records rather than assuming an automatic match. A keyless visible citation is represented by a hashed `visible:<hash>` identifier in the manifest; its raw human-readable citation text is not retained there, so return to the target locator when presenting candidates. Preserve competing candidates and metadata conflicts instead of silently choosing a plausible source.

## Generate or refresh the manifest

Run from the project directory, substituting the actual paths. The bundled script imports the project runtime and does not vendor third-party packages, so install the project runtime dependencies in the Python environment before invoking it.

```text
python <skill-dir>/scripts/source_corpus.py manifest --target <document> --source <source-directory> --bibliography <references.bib> --output <audit-dir>/source-manifest.csv --cache-dir <audit-dir>/text-cache
```

Use only the applicable corpus inputs: `--source` and `--bibliography` are optional. Repeat `--target`, `--source`, `--bibliography`, or `--manifest` for multiple inputs. `manifest` requires at least one `--target`; target paths may also be directories of supported files. Add `--manifest <existing-manifest.csv>` to import an inventory, or optional `--zotero-live` to enrich mappings from Zotero Desktop. Keep the selected target files aligned with the user's audit scope.

Refresh cached source text from a manifest with:

```text
python <skill-dir>/scripts/source_corpus.py cache --manifest <audit-dir>/source-manifest.csv --cache-dir <audit-dir>/text-cache --output <audit-dir>/source-manifest.csv
```

Use `manifest --help` or `cache --help` to check the installed runtime. `--force` bypasses cache reuse. `--fail-on-missing` changes the exit code when required gaps remain; it does not turn a gap into a support verdict. A successful command does not establish complete coverage or sound evidence.

Inspect the generated rows before defining audit denominators. Retain source identity, aliases, paths, hashes, target locators, mapping rules, candidate source IDs, conflicts, extraction status, text quality, and cache paths. The CLI includes explicit corpus sources as well as citation mapping rows; a row count is not automatically a claim count. The runtime summary uses manifest-row diagnostics for `expected`, `resolved`, `extracted`, `analyzed`, and `coverage_percent`; these are not the report denominators defined for distinct expected sources or eligible claims.

## Mapping and extraction status

Keep `mapping_status` distinct from `extraction_status` and from the eventual support verdict:

- `resolved`: the mapping identifies one source.
- `ambiguous`: multiple source candidates remain.
- `unresolved`: no deterministic match is established, including visible citations lacking an explicit identifier.
- `not-applicable`: for example, an explicit corpus source has no matched target citation. This does not establish that it is irrelevant to the audit.

Current extraction outcomes include `not_run` (no extraction recorded), `extracted` (text extracted), `missing` (no accessible local file), `empty` (PDF text is empty), `needs_ocr` (PDF text is sparse), `needs_review` (PDF text is degraded), `unusable` (for example, an otherwise successful extraction produced no source blocks), and `error:<ExceptionName>` (an isolated source extraction failure). Preserve the actual status value. Detailed extraction errors are not retained in the CSV manifest or ordinary runtime summary; record any separately observed diagnostic needed for the audit rather than implying that the manifest contains it. Imported manifests may contain legacy values such as `cached` or `unknown`; cache reuse itself retains the stored extraction status rather than setting a new `cached` status. `text_quality` is separate from these statuses.

The PDF extractor does not perform OCR. Sparse text flagged `needs_ocr` is a quality signal, not proof that OCR will recover all content. Inspect degraded, empty, or otherwise unusable extraction before relying on it. Record failures and continue checks that have adequate evidence; when the target itself cannot be read substantively, follow the diagnostic route above.

## Locator fidelity and extraction disclosure

Use only locators the extraction format supports:

- `.qmd` and `.md`: source line ranges, with available headings; `.txt`: source line numbers.
- `.tex` and `.latex`: source line numbers or citation line ranges, with recognized section headings. These are not rendered page numbers, and extraction is not TeX compilation.
- `.html` and `.htm`: ordered HTML blocks and element IDs when present, with available headings. These identify the local snapshot, not a stable live-page position.
- `.docx` and `.docm`: document body paragraph indices and recognized headings. The current adapter does not provide rendered pagination or comprehensive coverage of tables, footnotes, and other Word parts.
- `.doc`: paragraph locators from the converted DOCX. Disclose conversion and verify decisive wording against the original where accessible.
- `.pdf`: physical PDF page and within-page block, such as `page=3;block=2`. Printed page labels may differ and must be checked separately.

Do not invent page numbers for unpaginated inputs or equate source lines, paragraphs, physical PDF pages, and printed page labels. Preserve format-specific locators alongside quotations and enough surrounding context to assess the claim.

Disclose the extraction method, conversions, any separately performed OCR, and known omissions or text-quality limits in the report. Record conversion details explicitly rather than assuming the CSV or source cache preserves every extractor field. Reuse caches only for the current source content and suitable extraction configuration; refresh after source changes and force regeneration when extraction settings or methods change. Normalized text supports retrieval; original extracted blocks preserve local wording. Check passages that determine a verdict against authoritative documents when available.

Report the manifest path, corpus boundaries, resolved and unavailable sources, mapping conflicts, extraction failures, and which decisive passages were checked against authoritative documents. Keep availability, mapping, extraction, and substantive support as separate findings.
