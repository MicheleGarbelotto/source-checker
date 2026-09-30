# Installed plagiarism-audit skill: release smoke evidence

## Scenario prompt

The following is the exact scenario prompt, subject only to the path-prefix presentation substitution recorded in the run manifest:

> Perform an independent smoke test of the globally installed skill at %USERPROFILE%\.codex\skills\plagiarism-audit. First read that SKILL.md completely and follow it, including required references. Audit this synthetic target: %USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\tests\fixtures\documents\release-smoke-target.html. Use only this declared synthetic corpus bibliography: %USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\corpus.bib. The corpus has whatever accessibility state the files actually show; inspect it rather than assuming. Work read-only, do not search the web, do not read repository expected-output files or tests, and do not edit anything. Return your complete audit output plus a concise provenance appendix listing the installed skill path, runtime path/commands used, target, corpus input, and source locators. Be quantitative only where evidence supports it.

## Run manifest

- Run date/time: 2026-09-23T05:50:00.145841+02:00
- Installed skill path: `%USERPROFILE%\.codex\skills\plagiarism-audit`
- Installed skill file count: 39 regular files
- Installed skill tree SHA-256: `cf9f2a60eb2c079d813558b6242ee7a112b8f30ccab3cbbd1bac689f71dbf515`
- Tree-hash scheme: SHA-256 of the UTF-8 concatenation of lines sorted by relative POSIX path, each formatted as `<file_sha256><two spaces><relative_posix_path><LF>`.
- Target: `%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\tests\fixtures\documents\release-smoke-target.html`
  - SHA-256: `c860789125052d246b6161e25d0f4c2ee3fbf0db395e64fb82a08c38934bfe82`
  - Size: 185 bytes
- Corpus bibliography: `%USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\corpus.bib`
  - SHA-256: `4580bb7e920527874f5c84a890d6ad1a0eab47c086b67eb88eed295b24e4b35c`
  - Size: 384 bytes
- Accessible source: `%USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\readable.pdf`
  - SHA-256: `94fe2c7df2907f982a6a777dafb93e4db65e37021eac200bc4ae35b3796842fb`
  - Size: 993 bytes
- Unavailable source: `%USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\missing-source.pdf`
  - SHA-256: unavailable because the declared file was absent
- Python runtime: `%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\.venv\Scripts\python.exe`
- Installed runtime entry point: `%USERPROFILE%\.codex\skills\plagiarism-audit\scripts\source_corpus.py`
- Main runtime command:

```text
%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\.venv\Scripts\python.exe %USERPROFILE%\.codex\skills\plagiarism-audit\scripts\source_corpus.py manifest --target %USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\tests\fixtures\documents\release-smoke-target.html --bibliography %USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\corpus.bib --output %USERPROFILE%\AppData\Local\Temp\codex-plagiarism-audit-smoke-20260923\source-manifest.csv --cache-dir %USERPROFILE%\AppData\Local\Temp\codex-plagiarism-audit-smoke-20260923\text-cache --force
```

- Additional read-only checks: direct `extract_document` calls from the installed runtime; exact four-token n-gram enumeration; `pdftotext -layout readable.pdf -`.
- Repository-inspection boundary: no repository expected-output file or test implementation was read. The only file read under the repository `tests` tree was the explicitly declared synthetic target fixture.
- Mutation boundary: the temporary manifest and cache were removed after inspection. The target, bibliography, source PDF, repository, and installed skill were not edited during the audit.
- Presentation sanitization: the user-profile prefix in displayed paths was replaced with `%USERPROFILE%` for portability and privacy. No audit result, number, wording, locator, hash, or conclusion was changed.

# Plagiarism audit

## 1. Target and corpus coverage

Target: `%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\tests\fixtures\documents\release-smoke-target.html`, complete visible body, HTML `block=1`.

Selected target scope: the entire visible body. The `<head>` title is excluded by the installed HTML extractor.

Manifest: `%USERPROFILE%\AppData\Local\Temp\codex-plagiarism-audit-smoke-20260923\source-manifest.csv`, generated 2026-09-23 05:43:11 local time, inspected, then deleted with its temporary cache to preserve read-only operation.

- Expected sources: 2 distinct BibTeX records
- Resolved/available source artifacts: 1
- Extracted sources: 1, quality `good`
- Analyzed expected sources: 1
- Inaccessible source artifacts: 1
- Unusable source extractions: 0
- Unresolved source mappings: 0; both records were explicit-corpus entries with mapping status `not-applicable`
- Unanalyzed expected sources: 1
- Expected-source-set coverage: **Partial**
- Source-text coverage: **Partial**. The one-page accessible PDF was fully recovered as one block; no text was available for the missing PDF.

The expected corpus is exactly the two distinct records in the declared bibliography. No web or additional corpus was searched.

## 2. Extraction, method settings, and exclusions

- Target extraction: installed `source_checker` HTML extractor; status `extracted`, quality `good`, SHA-256 `c860789125052d246b6161e25d0f4c2ee3fbf0db395e64fb82a08c38934bfe82`.
- Accessible source extraction: `pdftotext-layout`; status `extracted`, quality `good`, one physical PDF page and one extracted block; SHA-256 `94fe2c7df2907f982a6a777dafb93e4db65e37021eac200bc4ae35b3796842fb`.
- Target tokenizer: lower-cased English word tokens matching `[A-Za-z]+(?:'[A-Za-z]+)*|[0-9]+`; punctuation is not counted. The visible target contains 8 analyzable words.
- Lexical candidate detector: exhaustive contiguous four-token n-gram comparison between the complete target and accessible source. It returned one candidate, beginning at target token 1 and source token 1.
- Semantic/cross-language method: no automated semantic or translation detector. The complete eight-token target and complete accessible 38-token source were manually compared in context.
- Verification: candidate wording was checked against the raw HTML and directly against the PDF using `pdftotext -layout ... -`.
- Evidence grouping key: canonical PDF/version, category, attribution group, target block, and coherent PDF block.
- Raw numerator: the union of verified matched target-token positions.
- Raw denominator: all 8 analyzable target words.
- Adjusted exclusions: none. Adjusted numerator and denominator therefore equal the raw values.
- Overlap rule: target positions would be counted once globally. Only one retained relationship exists here.
- Optional contextual review band: omitted; the user prohibited web access and no current-product comparison was needed.

## 3. Partial quantitative scorecard

| Scope label | Observed corpus coverage | Observed raw overall similarity | Observed adjusted overall similarity |
|---|---:|---:|---:|
| Partial | 1 / 2 = **50.0% [Partial]** | 4 / 8 = **50.0% [Partial]** | 4 / 8 = **50.0% [Partial]** |

All similarity results apply **only within the analyzed half of the declared corpus**. They do not estimate overlap with the inaccessible source.

| Metric label | Basis | Positions / denominator | Result | Retained passages | Unique target blocks |
|---|---|---:|---:|---:|---:|
| Observed Identical Match coverage (Partial) | Raw | 4 / 8 | **50.0% [Partial]** | 1 | 1 |
| Observed Minor Changes coverage (Partial) | Raw | 0 / 8 | **0.0% [Partial]** | 0 | 0 |
| Observed Related Meaning / Paraphrased Content coverage (Partial) | Raw | 0 / 8 | **0.0% [Partial]** | 0 | 0 |
| Observed Cross-language / Translated Match coverage (Partial) | Raw | 0 / 8 | **0.0% [Partial]** | 0 | 0 |

The labels are repository categories adapted from public Copyleaks vocabulary. There is no category overlap in this audit.

## 4. Source-level results

| Scope | Metric | Source | Identifier | Basis | Numerator / denominator | Result | Positions | Passages | Blocks | Artifact inspection |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| Partial | Observed per-source similarity | *Synthetic readable source* | BibTeX alias `readable`; source ID `source:8396…15f1` | Raw | 4 / 8 | **50.0% [Partial]** | 4 | 1 | 1 | Inspected directly |

The inaccessible source receives no similarity value.

## 5. Attribution-group summary

| Turnitin-style visible-signal group | Passages | Unique matched target words | Notes |
|---|---:|---:|---|
| Not Cited or Quoted | 1 | 4 | The authoritative HTML contains neither a citation nor quotation marks |
| Missing Quotations | 0 | 0 | — |
| Missing Citation | 0 | 0 | — |
| Cited and Quoted | 0 | 0 | — |

These groups describe visible signals only; they are not substantive citation-support or misconduct judgments.

## 6. Passage-level parallel evidence

### Match M01

- Target locator: HTML `block=1`
- Source: *Synthetic readable source*, alias `readable`
- Authoritative source locator: physical PDF `page=1;block=1`
- Match type: **Identical Match**, a repository label adapted from Copyleaks vocabulary
- Attribution group: **Not Cited or Quoted**, Turnitin-style visible-signal vocabulary
- Verification status: verified

Target passage: “First page block one”

Source passage: “First page block one.”

Assessment: four consecutive target words are identical after case and punctuation normalization. The next words diverge, so the verified span ends after “one.” The wording is short and not intrinsically highly distinctive; the 50% percentage is largely a consequence of the target containing only eight words.

Recommended review action: no misconduct inference. For this synthetic smoke fixture, no textual change is warranted; in substantive prose, provenance should be checked before deciding whether to quote, credit, or rewrite.

Candidate diagnostics excluded: none. The sole generated candidate was verified and retained.

## 7. Inaccessible source needed for broader coverage

- Source: *Synthetic unavailable source*
- BibTeX alias: `missing`
- Declared artifact: `%USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\missing-source.pdf`
- State: file absent; extraction status `missing`, text quality `unknown`
- Attempted route: local PDF attachment declared in `corpus.bib`
- Affected target passages: unknown because no source text was available
- Needed evidence: the declared PDF, or an authoritative equivalent explicitly added to the corpus

This source reduces expected-source-set coverage to 1/2. No similarity value can be assigned to unseen content.

## 8. Limitations and non-verdict conclusion

The target’s complete visible body was extracted, but its `<head>` title was intentionally outside the extractor’s visible-body scope. One of two declared source artifacts was absent. No wider web, commercial submission database, or undeclared source collection was searched. The four-token lexical screen plus complete manual comparison of the accessible texts may still miss relationships requiring broader semantic, translation, or common-source investigation. Extraction, locator, category, and visible citation detection can also be imperfect.

Within the one analyzed source, observed raw and adjusted overall similarity are **4/8 = 50.0% [Partial]**, with **1/2 = 50.0% [Partial]** corpus coverage. The only verified evidence is the four-word identical span at target HTML `block=1` and PDF `page=1;block=1`.

This is a source-bounded similarity audit, not a plagiarism verdict, misconduct finding, probability estimate, authorship determination, legal judgment, or reproduction of a proprietary detector.

## Provenance appendix

- Installed skill: `%USERPROFILE%\.codex\skills\plagiarism-audit`
- Installed entry point: `%USERPROFILE%\.codex\skills\plagiarism-audit\scripts\source_corpus.py`
- Python runtime: `%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\.venv\Scripts\python.exe`
- Global Python was not used because it lacked `python-docx`; no package was installed.
- Main runtime command:

```text
%USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\.venv\Scripts\python.exe %USERPROFILE%\.codex\skills\plagiarism-audit\scripts\source_corpus.py manifest --target %USERPROFILE%\Documents\source-checker\.worktrees\plagiarism-audit\tests\fixtures\documents\release-smoke-target.html --bibliography %USERPROFILE%\AppData\Local\Temp\source-checker-installed-skill-smoke-fix\test_release_smoke_uses_one_re0\corpus.bib --output %USERPROFILE%\AppData\Local\Temp\codex-plagiarism-audit-smoke-20260923\source-manifest.csv --cache-dir %USERPROFILE%\AppData\Local\Temp\codex-plagiarism-audit-smoke-20260923\text-cache --force
```

- Additional read-only checks: direct `extract_document` calls from the installed runtime; exact four-token n-gram enumeration; `pdftotext -layout readable.pdf -`.
- Target locator: HTML `block=1`.
- Corpus-input locators: `corpus.bib` record 1 (`readable`) and record 2 (`missing`).
- Source locator: `readable.pdf`, physical page 1, block 1.
- No repository expected-output file or test implementation was read. Only the explicitly declared target fixture was read under the test-fixture tree.
- Temporary manifest/cache artifacts were removed after inspection; target, bibliography, source PDF, repository, and installed skill were not edited.
