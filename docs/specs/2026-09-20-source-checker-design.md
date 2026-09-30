# Source Checker design specification

**Status:** Approved for implementation planning on 2026-09-20.

## Product boundary

`source-checker` contains two English-language Codex skills:

- `citation-support-audit` / **Citation Support Audit**
- `plagiarism-audit` / **Plagiarism Audit**

The folder name, frontmatter `name`, UI display name, documentation name, and invocation name must remain semantically identical. Do not introduce a separate public and technical name.

Citation Support Audit assesses reference resolution, citation placement and scope, potentially missing citations, quotation accuracy, citation mechanics, and whether the cited evidence substantively supports the associated claim. Plagiarism Audit assesses source-bounded textual similarity, close paraphrase, patchwriting, translated overlap, and visible attribution signals. It does not determine intent or make a misconduct finding.

The two skills share document acquisition and corpus infrastructure but retain separate methods, metrics, reports, and behavioral tests.

## Supported inputs

### Target documents and source documents

The first release supports:

| Extension | Extraction route | Locator contract |
|---|---|---|
| `.qmd`, `.md` | native markup parser with Pandoc citation recognition | heading and line range |
| `.txt` | native plain-text parser | line range |
| `.tex`, `.latex` | LaTeX parser with explicit `\\cite...{}` recognition | section and line range |
| `.html`, `.htm` | static local HTML parser; scripts, styles, navigation, and boilerplate excluded | heading, element id when present, and block index |
| `.docx`, `.docm` | non-executing OOXML extraction | heading and paragraph index |
| `.doc` | temporary conversion with LibreOffice, followed by OOXML extraction | converted heading and paragraph index, with conversion disclosed |
| `.pdf` | `pdftotext -layout`, then `pypdf`; OCR is explicit and never silent | physical PDF page and block index |

Local static HTML is in scope. Automatic crawling of remote or dynamic websites is outside the first release. A user may provide a saved HTML snapshot as an ordinary local file.

`.docm` files are read as OOXML packages. Macros are never executed. `.doc` conversion runs in a temporary directory and the report records the conversion route.

### Corpus and bibliography inputs

The first release accepts:

- explicit files or directories;
- Zotero Desktop through read-only supported access;
- Mendeley exports and their linked local files;
- BibTeX/BibLaTeX, RIS, and CSL JSON exports;
- references and bibliography embedded in the target document;
- CSV source manifests compatible with the existing skills.

Direct access to Mendeley's private local database is out of scope. The skill must ask for an export or accessible file directory when no supported Mendeley input is available. Direct Mendeley cloud API support is not claimed.

## Common document contract

Every extractor returns the same neutral records:

```text
DocumentRecord
  document_id
  role                       target | source
  path
  media_type
  sha256
  extraction_method
  extraction_status
  text_quality
  conversion_note
  blocks[]
  citations[]

TextBlock
  block_id
  text_original
  text_normalized
  locator_type
  locator_value
  heading

CitationMention
  raw_text
  citation_keys[]
  locator_type
  locator_value
  mapping_status             resolved | ambiguous | unresolved | not-applicable
```

Audit logic must consume this contract rather than branch on file type. Format-specific limitations are represented by extraction and mapping status, not hidden.

## Source identity and mapping

`source_id` is independent of any one reference manager. A source may have aliases including citekey, DOI, ISBN, PMID, Zotero item key, title-author-year fingerprint, or explicit user identifier.

Mapping order is deterministic:

1. exact stable identifier such as DOI;
2. exact citekey or reference-manager identifier;
3. normalized title plus author and year;
4. normalized title alone when unique;
5. filename or document metadata only when it yields one unambiguous candidate.

The system never silently chooses among multiple candidates. Ambiguities are stored in the main source manifest and displayed in the report. There is no separate `unresolved-source-mapping.csv`. If an ambiguity prevents a needed judgment, the skill asks only about those specific pairs.

## Intake behavior

The skills infer all available information before asking questions.

- If the target is missing, ask for the file or document scope.
- If the source corpus is missing, ask where the sources are available and name the supported routes relevant to the user's context.
- Do not ask for a citation-source map in advance.
- Do not ask which Citation Support Audit mode to run. Its default is the complete audit unless the user narrows the scope.
- Do not ask whether to continue after missing sources. Continue by default and disclose the limitation.
- Ask a mapping question only when a specific unresolved ambiguity materially blocks a judgment.

## Incomplete corpus contract

An unreadable target prevents substantive analysis. Missing or inaccessible sources do not.

Every report states:

- expected sources;
- sources resolved;
- sources successfully extracted;
- sources analyzed;
- sources missing, inaccessible, ambiguous, or unusable;
- corpus coverage percentage;
- whether results are complete or partial.

Citation Support Audit reports whole-scope metrics only when the denominator is defensible. Otherwise it reports verified-subset citation recall and precision with exact denominators plus audit coverage. `Unverifiable` is not converted to `Does not support`.

Plagiarism Audit reports observed similarity within the analyzed corpus. It does not extrapolate to missing sources or to the open web. Quantitative results remain available when the target and at least one source are analyzable.

## Outputs

The common tooling produces only the artifacts required for reproducibility:

- `source-manifest.csv`;
- one JSONL text cache per extracted document;
- a concise machine-readable run summary printed by the CLI.

Each skill produces its Markdown audit report. Additional artifact suggestions are not embedded in the skill. A new artifact may be added only when its purpose, consumer, and validation are defined.

## Methodological attribution and copyright posture

Each skill contains an early, concise **Methodological basis and limitations** section and a focused reference document with full attribution.

The documentation must:

- state that the implementation is independent;
- distinguish adapted public concepts from proprietary implementations;
- cite ALCE for adapted citation-support metrics;
- cite the public definitions used for similarity, match types, attribution groups, and review bands;
- avoid claims of product equivalence, affiliation, certification, or reproduced accuracy;
- use original wording, code, tables, and diagrams;
- quote external material only when necessary and briefly;
- preserve applicable license notices for reused code, if any.

The repository uses the MIT License for original code and documentation. The README includes a non-affiliation statement and explains that the tools do not provide legal or institutional misconduct determinations.

## Quality gates

Implementation follows test-first development. Existing behavior is captured before refactoring. Each changed skill is behaviorally tested before installation.

Required gates:

1. unit and integration tests for every extractor, resolver, mapping rule, cache invariant, and partial-corpus calculation;
2. fixture-based tests containing no copyrighted full-text sources;
3. baseline agent scenarios before rewriting each skill;
4. the same scenarios after rewriting each skill;
5. independent agent review of English, methodological fidelity, portability, and user-intake behavior;
6. skill frontmatter and `agents/openai.yaml` validation;
7. clean installation test from the repository into an isolated temporary skill directory;
8. final cutover to the user's installed skills only after the corresponding skill passes all gates.

The two skills are not revised in a single batch. Citation Support Audit is completed and verified before Plagiarism Audit is changed.
