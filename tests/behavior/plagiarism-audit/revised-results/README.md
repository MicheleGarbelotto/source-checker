# Plagiarism-audit Task 7 behavioral evidence

## Scope and capture method

These files are frozen public evaluation evidence. Host-internal session logs are
not distributed and are not required to inspect the prompts, outputs, assertions,
or recorded evaluations preserved here.

This record covers the seven accepted black-box scenarios in `../scenarios.yaml`: the six planned acceptance scenarios plus `html-target-latex-source`, an additional portability regression for native HTML and LaTeX inputs. The authoritative prompts and assertion text below are copied from that YAML file.

Each definitive run used a from-scratch isolated directory containing `envelope.json`, a complete 29-file snapshot of the then-current committed `plagiarism-audit` skill at `a483b5f`, and only the scenario's synthetic artifacts. Artifacts were created or copied before each envelope was generated from the exact YAML prompt/material and hashes of the already-copied skill files. Agents received a neutral controller wrapper explaining that the legacy invocation phrase in the scenario prompt referred to the supplied revised snapshot; the wrapper did not add assertions, expected wording, or a proposed answer. All definitive runs used `gpt-5.6-sol` with Codex CLI `0.155.0-alpha.9.2`.

The seven definitive scenarios contain 11 user-visible assistant messages, preserved below by phase and emission order. Assertions were assessed strictly against observable text in those messages. No file opening, extraction, comparison, metric execution, or audit operation is inferred unless the output itself says it occurred. `run-manifest.json` records stable scenario IDs, timestamps, model labels, public artifact paths, tree hashes, and result summaries.

Deleted temporary inputs are represented by hashes and are not claimed as independently reproducible inputs. The preserved public evidence is sufficient to inspect the prompts, user-visible output, assertions, evaluations, and stated provenance limits.

### Provenance correction

The accepted-set manifest committed in `a483b5f` separately verified each outer envelope hash and a repository skill-tree hash, but it failed to cross-check the skill hashes embedded inside each envelope after older workspaces had been copied and replaced. That accepted set is superseded and is not relied on here. The definitive set was rebuilt from scratch and cross-validates all three layers: every outer envelope/artifact/tree hash, every envelope-embedded skill entry against its copied file, and the embedded/copied skill tree against the repository skill at capture.

## Results summary

| Scenario | Passed | Failed | Not assessed | Result |
|---|---:|---:|---:|---|
| `underspecified-request` | 4 | 0 | 0 | PASS |
| `multi-format-corpus` | 4 | 0 | 0 | PASS |
| `incomplete-corpus` | 6 | 0 | 0 | PASS |
| `zero-accessible-sources` | 4 | 0 | 0 | PASS |
| `proper-quotation` | 4 | 0 | 0 | PASS |
| `localized-concerning-match` | 4 | 0 | 0 | PASS |
| `html-target-latex-source` | 4 | 0 | 0 | PASS |
| **Overall** | **30** | **0** | **0** | **30/30 PASS** |

### Post-quality-review intake regression

After the byte-stable response template was relaxed to a semantic two-essential-items contract, the latest fresh context-free run received only the verified current `SKILL.md` entrypoint, exact scenario prompt, and empty available-material list. It received no assertion text, expected wording, or prior output.

The complete user-visible stream contains one message:

1. `final_answer`

~~~text
Please provide the target document or file and the source corpus you want it checked against.
~~~

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent identifies that the target is missing. | PASS | The sole message requests the target document or file. |
| The agent identifies that the source corpus is missing. | PASS | The sole message requests the source corpus. |
| The agent asks no other intake question before those materials are supplied. | PASS | The only request contains the target and corpus; it includes no other question, option, commentary, or explanation. |
| The result records every question or information request the agent makes. | PASS | The sole request is reproduced above in full. |

Accepted follow-up total: **4 PASS, 0 FAIL, 0 NOT ASSESSED**. The one-message run passes the stricter no-commentary/no-explanation semantic contract and supplements rather than replaces the original seven-scenario 30/30 record.

## Scenario evidence

### `underspecified-request`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to check my work.
~~~

User-visible assistant messages, verbatim and in order:

1. `final_answer`

~~~text
Please provide:

1. The target document or file.
2. The source corpus to compare it against.
~~~

Information requests/questions:

1. Provide the target document or file.
2. Provide the source corpus.

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent identifies that the target is missing. | PASS | The final asks for “The target document or file.” |
| The agent identifies that the source corpus is missing. | PASS | The final asks for “The source corpus to compare it against.” |
| The agent asks no other intake question before those materials are supplied. | PASS | The only two requests are the target and corpus; no metric, scope, format, output, or other intake question appears. |
| The result records every question or information request the agent makes. | PASS | Both requests are enumerated above; there is no commentary or other user-visible message containing another request. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `multi-format-corpus`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to audit C:\study\draft.docx against exactly these local sources: C:\study\sources\alpha.pdf, C:\study\sources\bravo.html, and C:\study\sources\chen.docx. Treat all three as canonical sources and keep the same source-bounded similarity-audit meaning across their formats. This is a synthetic intake scenario; report how you would proceed and do not claim that the files were opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `commentary`

~~~text
I’m reading the supplied audit instructions and corpus, then I’ll report the plagiarism assessment without altering any files.
~~~

2. `final_answer`

~~~text
I would proceed with a source-bounded similarity audit using:

- Target: `C:\study\draft.docx`, complete document by default.
- Canonical corpus: exactly `alpha.pdf`, `bravo.html`, and `chen.docx`.
- Expected sources: 3, each counted once.
- No open-web or commercial-database searching.

The formats are supported directly. I would extract the target and `chen.docx` with Word paragraph locators, `alpha.pdf` with physical-page/block locators, and the local `bravo.html` snapshot with HTML block, heading, and element-ID locators. The extraction route would not change the meaning of the audit: all three sources would undergo the same candidate-generation, contextual verification, classification, and counting rules.

I would then:

1. Create a manifest recording each canonical artifact, hash, extraction method, status, text quality, and locator system.
2. Generate possible lexical—and, where applicable, semantic or translated—matches.
3. Verify every retained parallel against the target and canonical source context; detector candidates alone would not count as findings.
4. Calculate deduplicated raw overall similarity, any explicitly adjusted result, match-type coverage, and per-source similarity using the analyzable target-word denominator.
5. Report visible citation and quotation signals separately from textual similarity.
6. Report corpus coverage before interpreting similarity. If all three sources were usable and analyzed, coverage would be `3/3 = 100% [Complete]`; otherwise, I would continue with any analyzable subset and label every quantitative result `Observed ... [Partial]`, naming the unavailable sources. With zero analyzed sources, I would provide a diagnostic report and no similarity percentage.
7. Provide concise parallel-passage evidence with format-appropriate locators, extraction limitations, exclusions, and a non-verdict conclusion.

No files have been opened or analyzed in this synthetic intake response, so no similarity score or passage-level finding is claimed. Any eventual result would describe overlap only within these three supplied canonical sources—not plagiarism, intent, misconduct, or similarity to the wider web.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent accepts the DOCX target without requiring conversion to QMD, Markdown, or PDF. | PASS | It identifies `draft.docx` as the target and gives a native Word extraction route; no conversion is requested. |
| The agent accepts the PDF, HTML, and DOCX files as one source corpus. | PASS | It lists exactly the three files under one “Canonical corpus.” |
| The agent preserves one source-bounded similarity-audit meaning across all three source formats. | PASS | It says formatting and locator differences do not change candidate-generation, verification, classification, or counting rules. |
| The agent does not require Zotero or PDF conversion for the HTML and DOCX sources. | PASS | It supplies native HTML and Word routes and makes no Zotero or conversion request. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `incomplete-corpus`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to report this completed synthetic audit. The target has 1,000 analyzable words. Four sources were expected. Alpha, Bravo, and Chen were accessible and analyzed; Diaz was inaccessible. Across the three analyzed sources, 120 unique target words were verified as raw matches and 90 unique target words remained after documented exclusions. Produce the report now from these supplied facts; do not claim that any file was opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `commentary`

~~~text
I’m using the supplied plagiarism-checker skill snapshot because this is a source-corpus audit; I’ll keep the audit read-only and explicitly report the incomplete coverage.
~~~

2. `final_answer`

~~~text
## 1. Target and corpus coverage

- Target: synthetic target; 1,000 analyzable words
- Selected scope: complete supplied target
- Expected sources: 4 — Alpha, Bravo, Chen, Diaz
- Analyzed expected sources: 3 — Alpha, Bravo, Chen
- Inaccessible and unanalyzed sources: 1 — Diaz
- Observed corpus coverage: 3/4 = **75.0% [Partial]**
- Source-text coverage: **Partial** because Diaz was unavailable

Resolution, extraction, and manifest details were not supplied, so they cannot be reported separately.

## 2. Method and exclusions

The supplied results use unique target-word positions: overlapping matches are counted once in the overall numerator. The raw result includes 120 verified matched words. After the supplied exclusions, 90 matched words remain. Because no excluded target text was reported, the adjusted calculation retains the 1,000-word denominator and treats the adjustment as removing 30 matched positions from the numerator.

The exclusion identities, extraction methods, tokenizer specification, candidate-detection settings, source locators, and authoritative-artifact inspection status were not supplied. Consequently, match-type, attribution, passage-level, and per-source distributions cannot be reconstructed.

## 3. Partial quantitative scorecard

| Scope label | Observed corpus coverage | Observed raw overall similarity within the analyzed corpus | Observed adjusted overall similarity within the analyzed corpus |
|---|---:|---:|---:|
| Partial | 3/4 = **75.0% [Partial]** | 120/1,000 = **12.0% [Partial]** | 90/1,000 = **9.0% [Partial]** |

The adjusted result removes 30 matched target-word positions. The supplied facts do not identify the passages or rules responsible for that adjustment.

Match-type coverage cannot be calculated because the verified positions were not divided among Identical Match, Minor Changes, Related Meaning / Paraphrased Content, or Cross-language / Translated Match categories.

## 4. Source-level results

| Source | Analysis status | Observed per-source similarity |
|---|---|---:|
| Alpha | Analyzed | Not derivable from the supplied aggregate counts |
| Bravo | Analyzed | Not derivable from the supplied aggregate counts |
| Chen | Analyzed | Not derivable from the supplied aggregate counts |
| Diaz | Inaccessible; not analyzed | Not computed |

No similarity value is assigned to Diaz, and the observed aggregate percentages must not be extrapolated to it.

## 5. Attribution and passage evidence

Attribution-group counts cannot be reported because no passage-level citation or quotation signals were supplied. Likewise, no parallel passages or authoritative source locators were supplied, so there is no basis for presenting passage-level evidence.

## 6. Limitations and conclusion

Within the three analyzed sources, the observed raw similarity is **12.0% [Partial]**, and the observed adjusted similarity is **9.0% [Partial]**, with **75.0% [Partial] corpus coverage**. These percentages describe only Alpha, Bravo, and Chen. Diaz remains outside the analysis, and no inference is made about what its content might add.

This is a source-bounded similarity result, not a plagiarism verdict, misconduct finding, probability estimate, or reproduction of a proprietary detector.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent reports 12% observed raw similarity within the analyzed corpus. | PASS | The scorecard reports `120/1,000 = 12.0% [Partial]` and limits it to the three analyzed sources. |
| The agent reports 9% observed adjusted similarity within the analyzed corpus. | PASS | The scorecard reports `90/1,000 = 9.0% [Partial]` and applies the same analyzed-corpus qualification. |
| The agent reports corpus coverage as three of four expected sources, or 75%. | PASS | It reports `3/4 = 75.0% [Partial]`. |
| The agent lists Diaz as inaccessible. | PASS | Diaz appears as the one inaccessible, unanalyzed source. |
| The agent labels the quantitative result partial rather than complete. | PASS | The section, scorecard, and every reported metric use `Partial`. |
| The agent does not estimate similarity to the inaccessible source. | PASS | It says no similarity value is assigned to Diaz's unseen content. |

Totals: **6 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `zero-accessible-sources`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to report this synthetic audit state. The target is readable and has 1,000 analyzable words. Four sources were expected, but none was accessible or analyzed. Produce the report now from these supplied facts; do not claim that any file was opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `commentary`

~~~text
I’m using the supplied revised plagiarism-checker skill because this is a source-overlap audit; I’ll keep the result read-only and bounded to the supplied artifacts.
~~~

2. `final_answer`

~~~text
## 1. Target and corpus coverage

- Target: readable synthetic target; no path or locator range supplied
- Selected scope: supplied target scope
- Analyzable target words: 1,000
- Expected sources: 4
- Accessible source artifacts: 0
- Analyzed expected sources: 0
- Unanalyzed expected sources: 4
- Resolved sources: not reported
- Unresolved mappings: not reported
- Manifest: not supplied
- Expected-source-set coverage: 0 / 4 = 0% **[Partial]**
- Source-text coverage: none; all four expected sources were inaccessible

This report is based exclusively on the supplied audit-state facts. No target or source-file inspection is claimed.

## 2. Extraction, method settings, and exclusions

The target was reported as readable with 1,000 analyzable words. The tokenizer, extraction method, target locators, and extraction quality details were not supplied.

No source text was available for candidate generation, passage verification, or comparison. Therefore:

- lexical, semantic, and cross-language comparison: not run;
- authoritative-source inspection: not performed;
- verified matched positions: unavailable;
- raw or adjusted exclusions: none applied;
- visible citation and quotation signals: not assessed;
- review band: not applicable.

## 3. Diagnostic quantitative scorecard

| Scope label | Observed corpus coverage | Observed raw overall similarity | Observed adjusted overall similarity |
|---|---:|---:|---:|
| Partial | 0 / 4 = 0% [Partial] | Not computed: zero analyzed sources | Not computed: zero analyzed sources |

No similarity percentage can validly be reported. Reporting 0% similarity would incorrectly treat unavailable sources as sources that were analyzed and found to contain no overlap.

Match-type coverage was likewise not computed for Identical Match, Minor Changes, Related Meaning / Paraphrased Content, or Cross-language / Translated Match.

## 4. Source-level results

No source-level similarity results are available because none of the four expected sources was accessible or analyzed.

## 5. Attribution-group summary

No verified passages were available for classification into visible-signal groups such as Not Cited or Quoted, Missing Quotations, Missing Citation, or Cited and Quoted.

## 6. Passage-level parallel evidence

No verified passage evidence can be reported. There were also no supplied candidate diagnostics to retain separately.

## 7. Inaccessible sources needed for broader coverage

All four expected sources remain unanalyzed. Their identities, identifiers, attempted access routes, and affected target passages were not supplied, so they cannot be individually described.

A substantive audit requires accessible full text for at least one expected source. Analyzing all four would be required for complete expected-source-set coverage.

## 8. Limitations and non-verdict conclusion

The wider web, commercial submission databases, and any source outside the defined four-source corpus were not searched. Because corpus coverage was **0 / 4 = 0% [Partial]**, textual similarity, match types, source-level overlap, attribution signals, and passage evidence remain undetermined.

This is a diagnostic coverage report for a source-bounded similarity audit. It is not a plagiarism verdict, misconduct finding, probability estimate, originality clearance, or reproduction of a proprietary detector.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent produces a diagnostic corpus-coverage report. | PASS | It provides target/corpus coverage and a “Diagnostic scorecard.” |
| The agent reports that zero of four expected sources were analyzed. | PASS | It reports `Analyzed expected sources: 0` and `0 / 4 = 0%`. |
| The agent withholds raw and adjusted similarity percentages. | PASS | Similarity is “Not computed”; neither raw nor adjusted percentage is supplied. |
| The agent explains that zero analyzed sources cannot support a similarity estimate. | PASS | It explicitly says a percentage cannot be calculated without at least one analyzed source and distinguishes 0% coverage from 0% similarity. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `proper-quotation`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to interpret this completed synthetic audit. The target has 1,000 analyzable words and 300 words match the analyzed corpus. Of those, 280 words are in a clearly marked direct quotation with an adjacent citation to the matched source; the remaining 20 matched words are ordinary attributed overlap. Explain the high raw similarity without claiming that files were opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `final_answer`

~~~text
Based solely on the supplied synthetic audit summary:

- Raw overall similarity: **300 / 1,000 = 30.0%**
- Clearly quoted with an adjacent citation: **280 / 1,000 = 28.0%**
- Remaining attributed overlap: **20 / 1,000 = 2.0%**
- Thus, **93.3% of all matched words** are within the clearly marked, cited quotation.

The 30.0% raw similarity is therefore driven overwhelmingly by transparently presented quotation, not by unattributed matching text. Properly quoted and cited language still counts as textual similarity, so it remains in the raw numerator. The remaining 2.0% is described as ordinary attributed overlap and, on the supplied evidence, does not itself justify an originality concern.

No adjusted score should be substituted automatically. If a documented match-only exclusion for the cited quotation were intentionally applied, the resulting adjusted similarity would be **20 / 1,000 = 2.0%**; otherwise, the adjusted score remains the raw **30.0%**.

Corpus coverage, passage locators, source-level results, and extraction details were not supplied, so they cannot be reported here. This is a source-bounded similarity interpretation—not a plagiarism verdict, misconduct finding, or probability estimate.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent describes the 30% result as similarity or overlap. | PASS | It reports `Raw overall similarity: 300 / 1,000 = 30.0%`. |
| The agent recognizes the quotation marks and adjacent citation as material attribution evidence. | PASS | It identifies 280 words as a clearly marked direct quotation with an adjacent citation and uses that to explain the high score. |
| The agent does not automatically label the properly quoted and cited material plagiarism. | PASS | It says the descriptive percentage is not evidence of plagiarism or misconduct. |
| The agent does not infer intent or make a misconduct verdict from the percentage. | PASS | It makes no intent inference and explicitly rejects a misconduct inference. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `localized-concerning-match`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to interpret this completed synthetic audit. The target has 10,000 analyzable words. One verified 40-word passage is a distinctive close paraphrase of a source, with no quotation marks and no nearby citation. No other matches were retained, so the observed overall similarity is 0.4%. Explain the result without claiming that files were opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `final_answer`

~~~text
The 0.4% overall similarity is numerically low, but it does not clear the individual passage.

- Raw overall similarity: 40 / 10,000 words = 0.4%.
- Adjusted similarity: also 0.4%, because no exclusions were specified.
- Match type: verified Related Meaning / Paraphrased Content—a distinctive close paraphrase.
- Visible attribution group: Not Cited or Quoted—neither quotation marks nor a nearby citation was detected.

The 40-word passage should remain a retained finding despite the low document-level percentage. It warrants revision: substantially rephrase it and add an appropriate citation, or quote and cite it if the source’s distinctive wording must be preserved. This classification concerns textual overlap and visible attribution only; it does not establish whether the source supports the claim.

Corpus coverage figures were not supplied, so the result cannot be labelled complete or partial, nor generalized to unavailable sources, the wider web, or commercial databases. This is a source-bounded similarity finding, not a plagiarism verdict, misconduct finding, or probability estimate.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent reports the low 0.4% overall similarity. | PASS | It reports `40 / 10,000 ... = 0.4%`. |
| The agent still highlights the verified distinctive 40-word passage for review. | PASS | It retains the distinctive close paraphrase as a finding despite the low percentage and says it warrants revision. |
| The agent does not treat the low overall percentage as clearing the localized concern. | PASS | It opens by saying the low 0.4% “does not clear the individual passage.” |
| The agent avoids a definitive plagiarism, intent, or misconduct verdict. | PASS | It makes no intent inference and explicitly says the finding is not a plagiarism or misconduct verdict. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

### `html-target-latex-source`

Exact scenario prompt:

~~~text
Use the plagiarism-checker skill to audit C:\study\draft.html against the single canonical source C:\study\sources\article.tex. Both local files are readable and authoritative in their original formats. There is no QMD target, PDF source, or Zotero record, and I do not want either file converted merely to qualify for the audit. This is a synthetic intake scenario; report how you would proceed and do not claim that the files were opened.
~~~

User-visible assistant messages, verbatim and in order:

1. `commentary`

~~~text
I’m using the supplied revised plagiarism-checker skill because the scenario explicitly calls for it. I’ll keep the audit confined to the provided synthetic artifacts and report it read-only.
~~~

2. `final_answer`

~~~text
The audit can proceed directly in the supplied formats; neither file needs conversion.

- Target: `C:\study\draft.html`, treated as a local static HTML snapshot and analyzed in full by default.
- Expected corpus: one canonical source, `C:\study\sources\article.tex`.
- Extraction: visible HTML text with ordered-block, heading, and element-ID locators where available; LaTeX source text with line and recognized-section locators. The `.tex` file would be parsed directly, not compiled.
- Verification: candidate similarities would be checked against the authoritative HTML and LaTeX passages in context before becoming findings.
- Reporting: if the source is successfully analyzed, corpus coverage would be `1 / 1 = 100% [Complete]`. “Complete” would refer only to this defined one-source corpus, not the wider web or commercial submission databases.
- Metrics: raw and adjusted similarity would be reported separately as matched target-word positions divided by analyzable target words, with passage-level evidence and visible citation/quotation signals. No adjustment would be made unless a documented exclusion applied.
- Boundaries: the wider web, commercial databases, and nonexistent QMD, PDF, or Zotero records would not be searched or treated as missing requirements.

No similarity percentage or passage finding is reported here because, as requested, this describes the procedure without claiming that either file was opened or analyzed. The eventual result would be a source-bounded similarity audit, not a plagiarism or misconduct verdict.
~~~

Information requests/questions: **None.**

| Exact assertion | Verdict | Observable evidence |
|---|---|---|
| The agent accepts the HTML file as the audit target. | PASS | It says the audit can proceed directly and identifies `draft.html` as the target. |
| The agent accepts the LaTeX file as the canonical source. | PASS | It identifies `article.tex` as the single canonical source and describes native LaTeX extraction. |
| The agent does not require QMD, PDF, Zotero, or format conversion before auditing. | PASS | It says neither file needs conversion and treats the nonexistent QMD, PDF, and Zotero records as non-requirements. |
| The agent preserves the same source-bounded similarity-audit meaning for these formats. | PASS | It applies the same candidate, verification, coverage, metric, passage-evidence, and verdict boundaries to the HTML/LaTeX pair. |

Totals: **4 PASS, 0 FAIL, 0 NOT ASSESSED**.

## Limitations

- These are controlled synthetic behavioral cases, not audits of real documents.
- Intake-only cases describe intended handling; they do not demonstrate that extractors or comparisons executed successfully.
- Fact-driven cases test reporting and interpretation from supplied facts; they do not independently validate tokenization, candidate retrieval, passage verification, or source-resolution code.
- The seven cases cover the assertions stated in `scenarios.yaml`, not every supported format, failure mode, or evidentiary judgment.
- Reviewer findings and controller dispositions are recorded separately in `reviews.md`; a disposition is not retroactive reviewer approval.
- The definitive snapshot root was a local ephemeral capture source and was removed after full controller cross-validation. Its hashes are internal audit anchors, not independently reproducible inputs.
- The earlier `a483b5f` accepted set is superseded because its embedded skill hashes were not cross-checked after copied workspaces were replaced; none of its run output is relied on here.

## Reproducible verification guidance

1. Hash `../scenarios.yaml` and compare it with `scenario_file.sha256` in `run-manifest.json`.
2. Use each stable scenario ID to compare its exact prompt and captured-output blocks with the corresponding assertion table below.
3. Recompute each available copied skill-tree hash by sorting paths relative to the scenario's `plagiarism-audit` directory using forward slashes, appending `relative_path + NUL + lowercase_file_sha256 + LF` for every file, concatenating those byte records, and SHA-256 hashing the result.
4. For every retained `envelope.json` `skill_snapshot` entry, verify both SHA-256 and byte size against the referenced copied file. Remove the leading `plagiarism-audit/` component, sort the normalized paths case-sensitively, and recompute the same tree record from the embedded hashes. Confirm that it equals both the copied tree and the repository skill tree recorded for that run.
5. Reassess each exact assertion only against observable messages. The totals above follow mechanically from the 30 row verdicts.

## Final validation

The superseded set's validation is not reused. For this definitive set, the controller independently verified 7 exact prompts/material envelopes, every outer envelope and artifact hash/size, all 203 envelope-embedded skill hashes/sizes, embedded/copied/repository-at-capture tree equality, 7 scenario timestamps and model labels, 11 ordered assistant messages, and 30/30 exact assertion rows before removing the temporary root. The latest one-message intake rerun was separately verified against the post-review repository tree and passed the semantic contract and 4/4 YAML assertions.

Fresh post-record repository validation then ran from the worktree root in the repository virtual environment. Every command exited 0:

| Command | Result |
|---|---|
| `.venv\\Scripts\\python.exe -m pytest -q` | PASS; complete suite reached 100% |
| `.venv\\Scripts\\ruff.exe check .` | PASS; `All checks passed!` |
| `.venv\\Scripts\\pyright.exe` | PASS; `0 errors, 0 warnings, 0 informations` |
| `.venv\\Scripts\\python.exe %USERPROFILE%\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py skills\\plagiarism-audit` | PASS; `Skill is valid!` |
| `.venv\\Scripts\\python.exe %USERPROFILE%\\.codex\\skills\\.system\\skill-creator\\scripts\\quick_validate.py skills\\citation-support-audit` | PASS; `Skill is valid!` |
| `.venv\\Scripts\\python.exe tools\\sync_skill_runtime.py --check skills\\plagiarism-audit` | PASS; runtime up to date |
| `.venv\\Scripts\\python.exe tools\\sync_skill_runtime.py --check skills\\citation-support-audit` | PASS; shared runtime copy up to date |
| `.venv\\Scripts\\python.exe %TEMP%\\verify_task7_followup.py` | PASS; 7 original scenarios/30 assertions/11 messages plus the latest one-message accepted 4/4 follow-up verified |
| `git diff --check` | PASS |
