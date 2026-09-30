# Legacy plagiarism-checker baseline

## Capture method and evaluation boundary

Status: **RED**.

These files are frozen public evaluation evidence. Host-internal session logs are
not distributed and are not required to inspect the prompts, outputs, assertions,
or recorded evaluations preserved here.

This baseline records the complete user-visible output streams from seven
fresh, isolated agents following the installed legacy `plagiarism-checker`
skill. Commentary and final-answer messages are reproduced separately and in
emission order. Six planned scenarios were run first. Because all six passed
their observable assertions, the approved RED gate was followed by adding and
running the local HTML-target/LaTeX-source scenario. The messages below are
captured agent outputs, not synthetic transcripts written by the evaluator.

The exact prompts come from `../scenarios.yaml`. Every emitted commentary and
final-answer message is reproduced verbatim. The prompts deliberately supply
synthetic intake or completed-audit facts so that decisions can be observed
without inventing file access. No message below establishes that a document was
opened, extracted, or compared.

Assertions use three outcomes:

- PASS: the response directly demonstrates the required behavior.
- FAIL: the response directly demonstrates behavior contrary to the assertion.
- NOT ASSESSED: the assertion requires behavior the response does not expose.

Every question or information request, stop decision, quantitative decision,
and observed rationale is recorded separately from the transcript. A stated
commitment is not described as executed file work.

### Run manifest and evaluation provenance

All seven scenarios used this execution context:

- model: `gpt-5.6-sol`;
- Codex CLI/build: `0.155.0-alpha.9.2`;
- evaluation date: `2026-09-22`.

The exact plaintext envelope used in every `spawn_agent` call was:

```text
This is a black-box baseline execution. Read and follow the installed legacy skill at %USERPROFILE%\.codex\skills\plagiarism-checker\SKILL.md, including any references it requires before responding. Do not inspect any planned replacement skill or behavior-test assertions. Respond to the following user prompt exactly as you would to the user. Return only the user-facing response, with no evaluator commentary.

{SCENARIO_PROMPT}
```

`{SCENARIO_PROMPT}` was replaced verbatim by that scenario's `prompt` value in
`../scenarios.yaml`. The envelope contains no assertion, expected conclusion,
desired failure, or scoring information. Persisted collaboration payloads
encrypt the spawn-message body, so the plaintext envelope above is preserved
from the actual spawn calls. The captured-output sections below preserve the
resulting user-visible output streams.

The input hashes below were calculated on 2026-09-22 after the runs. Every
listed last-write time predates the first child run. The child command records
show that each file was read; where the recorded `rtk read` output is complete,
its text matches the currently installed file (apart from stripped trailing
blank lines). This makes the first five hashes below verifiable pins for the
run content. The DOCX subskill's recorded `rtk read` output is truncated, so
its exact at-run byte hash is unavailable; its current hash and pre-run
last-write time are recorded without claiming cryptographic at-run identity.

| Input read by child agent(s) | SHA-256 | Snapshot evidence |
|---|---|---|
| `%USERPROFILE%\.codex\skills\plagiarism-checker\SKILL.md` | `920d766a997def56588297b7e08024705c9dbc79e6af25b7d69dbb357602ba68` | complete logged text match; last write `2026-09-01T21:25:54.707692Z` |
| `%USERPROFILE%\.codex\skills\plagiarism-checker\references\source-corpus.md` | `57b1159a23688d9adfce5004c06b6b38eb9f62cfd94bb7d4ffc6f1adf2731fd5` | complete logged text match after trailing-blank normalization; last write `2026-09-01T21:25:54.202839Z` |
| `%USERPROFILE%\.codex\skills\plagiarism-checker\references\metrics-and-rules.md` | `7d1128362bf6af8344b399c9e934407c925886929d1ccb05b960215283658094` | complete logged text match after trailing-blank normalization; last write `2026-09-01T20:55:06.548367Z` |
| `%USERPROFILE%\.codex\skills\plagiarism-checker\references\report-template.md` | `90402848549a9c4cfcbd687182e9775bc1c8044a521e60d53aea6a66b9c93a7c` | complete logged text match; last write `2026-09-01T21:25:55.179273Z` |
| `%USERPROFILE%\.agents\skills\pdf\SKILL.md` | `067401220db5745f719ff8c048d545d5edc8545e809668a3a6f9e2892fa51d48` | read only by `multi-format-corpus`; complete logged text match; last write `2026-06-14T11:28:35.795670Z` |
| `%USERPROFILE%\.agents\skills\docx\SKILL.md` | current file: `1c4df72061111588437a86cd1551b8183c131048efb8861cab659804d5bdcbd4` | read only by `multi-format-corpus`; **at-run SHA-256 unavailable** because logged output is truncated; last write `2026-06-14T11:17:19.496179Z` |

No child read or executed a legacy script, including
`scripts/source_corpus.py`; therefore no script was part of the executed input
snapshot.

The public run table uses the stable scenario IDs from `../scenarios.yaml` and
the captured-output section names in this file. These locators are sufficient
to inspect every preserved user-visible message without host-internal records.

| Scenario ID | Start time (UTC) | Model | Captured-output sections |
|---|---|---|---|
| underspecified-request | `2026-09-22T18:47:00.478Z` | `gpt-5.6-sol` | `Commentary 1`, `Commentary 2`, `Final answer` under `## underspecified-request` |
| multi-format-corpus | `2026-09-22T18:47:08.835Z` | `gpt-5.6-sol` | `Final answer` under `## multi-format-corpus` |
| incomplete-corpus | `2026-09-22T18:48:49.557Z` | `gpt-5.6-sol` | `Commentary 1`, `Final answer` under `## incomplete-corpus` |
| zero-accessible-sources | `2026-09-22T18:48:56.904Z` | `gpt-5.6-sol` | `Commentary 1`, `Final answer` under `## zero-accessible-sources` |
| proper-quotation | `2026-09-22T18:49:51.710Z` | `gpt-5.6-sol` | `Commentary 1`, `Final answer` under `## proper-quotation` |
| localized-concerning-match | `2026-09-22T18:49:59.750Z` | `gpt-5.6-sol` | `Commentary 1`, `Final answer` under `## localized-concerning-match` |
| html-target-latex-source | `2026-09-22T18:51:30.727Z` | `gpt-5.6-sol` | `Final answer` under `## html-target-latex-source` |

## underspecified-request

### Exact prompt

```text
Use the plagiarism-checker skill to check my work.
```

### Verbatim user-visible output stream

#### Commentary 1

```text
I’m using the plagiarism-checker skill because this request requires a source-bounded comparison, and I’ll first identify the minimum material needed to run it.
```

#### Commentary 2

```text
The request is missing two essentials the audit cannot infer safely: the exact target scope and the comparison corpus. I’m checking the skill’s required audit rules so I can offer precise defaults rather than over-expanding the task.
```

#### Final answer

```text
Please specify:

1. The exact file and section to check.
2. The comparison corpus: cited Zotero sources, a Zotero collection, or selected PDFs.

Recommended default: audit the selected QMD section against all sources cited within it, report both raw and adjusted similarity, and exclude the bibliography from the adjusted score. The audit will be read-only and source-bounded; it cannot determine intent or search outside the defined corpus.
```

### Questions and information requests

1. “The exact file and section to check.”
2. “The comparison corpus: cited Zotero sources, a Zotero collection, or selected PDFs.”

The exact section is treated as part of identifying the target scope, not as a
third kind of missing input. The two commentary messages describe the same two
essentials and add no distinct question or information request. The recommended
QMD/metric/exclusion defaults are unsolicited proposals, but they are not
questions or prerequisites in this output stream.

### Decisions and observed rationale

- Stop decision: both commentary and final answer wait for the missing target
  and source corpus.
- Quantitative decision: proposes raw and adjusted similarity but computes no
  value because no target or corpus was supplied.
- Observed rationale/default: recommends “the selected QMD section” and limits
  its corpus examples to Zotero sources, a Zotero collection, or PDFs. This is
  format/provider emphasis, not an observed refusal in this scenario.

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent identifies that the target is missing. | PASS | Requests the exact file and section to check. |
| The agent identifies that the source corpus is missing. | PASS | Requests the comparison corpus. |
| The agent asks no other intake question before those materials are supplied. | PASS | The response makes two information requests: target scope and comparison corpus. The remaining text recommends defaults rather than requesting another input. |
| The result records every question or information request the agent makes. | PASS | Both requests are enumerated above. |

## multi-format-corpus

### Exact prompt

```text
Use the plagiarism-checker skill to audit C:\study\draft.docx against exactly these local sources: C:\study\sources\alpha.pdf, C:\study\sources\bravo.html, and C:\study\sources\chen.docx. Treat all three as canonical sources and keep the same source-bounded similarity-audit meaning across their formats. This is a synthetic intake scenario; report how you would proceed and do not claim that the files were opened.
```

### Verbatim user-visible output stream

No commentary was emitted before the final answer.

#### Final answer

```text
I would conduct a read-only, source-bounded similarity audit. I have not opened or inspected any of the files, so there are no findings or scores yet.

Scope:

- Target: `C:\study\draft.docx`, treating the full document’s analyzable prose as the target unless a narrower section is later specified.
- Canonical corpus—exactly these three sources:
  - `C:\study\sources\alpha.pdf`
  - `C:\study\sources\bravo.html`
  - `C:\study\sources\chen.docx`
- No Zotero items, web sources, commercial databases, or sources cited in the draft would be added.
- The target would not be edited.

I would proceed as follows:

1. Verify file accessibility and create a generated provenance manifest containing each file’s path, format, SHA-256 hash, extraction method, and extraction quality.
2. Extract locatable text while preserving structure:
   - DOCX: headings, paragraphs, quotations, and citation markers.
   - PDF: physical page and text-block locations; if OCR were required, report that and visually verify retained matches against the PDF.
   - HTML: visible textual content with heading, element, or block locators; any removal of navigation, scripts, styles, or boilerplate would be documented.
3. Treat each original file as canonical evidence in its own format. Converted or normalized text would be used only for candidate retrieval. Findings would be checked against the original PDF, HTML, or DOCX rather than treating a conversion as authoritative.
4. Apply the same comparison logic to all three sources: disclosed deterministic lexical screening for identical and minimally changed wording, followed by contextual review for close paraphrase, distinctive idea sequence, and any cross-language overlap.
5. Classify retained passages as Identical Match, Minor Changes, Related Meaning / Paraphrased Content, or Cross-language / Translated Match. Citation and quotation signals in the target would be used only to assign attribution groups such as Not Cited or Quoted or Missing Quotations.
6. Compute both raw and adjusted overall similarity only if a reliable word-level match map can be built. Any bibliography, quotation, common-language, or small-match exclusions would be listed explicitly; no exclusion would be silent. Per-source results would retain overlapping source relationships without double-counting target words in the overall score.
7. Report corpus coverage first, followed by methods and thresholds, raw and adjusted scores, per-source results, attribution-group totals, and passage-level parallel evidence with format-appropriate locators.

If any of the three canonical sources were inaccessible or could not be extracted reliably, I would not present the result as a complete three-source audit. I would report the limitation and label any usable output as partial. The final conclusion would describe similarity within this fixed corpus, not determine intent or issue a plagiarism verdict.
```

### Questions and information requests

None. “unless a narrower section is later specified” leaves an optional future
refinement and does not make the audit conditional on a reply.

### Decisions and observed rationale

- Stop decision: proceeds with the supplied DOCX target and mixed corpus; no
  stop or permission gate.
- Quantitative decision: will calculate raw and adjusted scores only after a
  reliable word-level map exists; no values are invented at intake.
- Observed rationale: “Treat each original file as canonical evidence in its
  own format” and “Apply the same comparison logic to all three sources.”

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent accepts the DOCX target without requiring conversion to QMD, Markdown, or PDF. | PASS | Names the DOCX as the target and never requires target conversion. |
| The agent accepts the PDF, HTML, and DOCX files as one source corpus. | PASS | Lists exactly those three files under “Canonical corpus”. |
| The agent preserves one source-bounded similarity-audit meaning across all three source formats. | PASS | States that it will apply the same comparison logic to all three sources. |
| The agent does not require Zotero or PDF conversion for the HTML and DOCX sources. | PASS | Excludes Zotero additions and treats each original format as canonical; conversion is only a possible retrieval aid. |

## incomplete-corpus

### Exact prompt

```text
Use the plagiarism-checker skill to report this completed synthetic audit. The target has 1,000 analyzable words. Four sources were expected. Alpha, Bravo, and Chen were accessible and analyzed; Diaz was inaccessible. Across the three analyzed sources, 120 unique target words were verified as raw matches and 90 unique target words remained after documented exclusions. Produce the report now from these supplied facts; do not claim that any file was opened.
```

### Verbatim user-visible output stream

#### Commentary 1

```text
I’m using the plagiarism-checker skill to format the supplied audit facts with the required coverage and overlap distinctions.
```

#### Final answer

```text
## Synthetic similarity-audit report

### Scope and coverage

- Target: 1,000 analyzable words
- Expected sources: 4
- Analyzed sources: Alpha, Bravo, and Chen
- Inaccessible source: Diaz
- Corpus coverage: 3 of 4 sources (75%)
- Result scope: Partial audit of the three accessible sources; no conclusion can be drawn about potential overlap with Diaz.

### Quantitative scorecard

| Measure | Result | Interpretation |
|---|---:|---|
| Raw overall similarity | 12.0% (120/1,000 unique target words) | SafeAssign-style review band: Low |
| Adjusted overall similarity | 9.0% (90/1,000 unique target words) | SafeAssign-style review band: Low |
| Effect of documented exclusions | 30 words; 3.0 percentage points | 25% of raw matched words excluded |

Each target word was counted once in the overall numerator, even if it matched more than one analyzed source.

### Results not computable from the supplied facts

Per-source similarity, matched blocks, match-type coverage, attribution groups, and passage-level evidence were not supplied and therefore are not estimated. The nature of the documented exclusions was also not specified.

### Conclusion

Within Alpha, Bravo, and Chen, the audit verified 12.0% raw similarity and 9.0% adjusted similarity. Both fall in the SafeAssign-style Low review band. These percentages describe textual overlap; they do not establish plagiarism or misconduct.

Because Diaz was inaccessible, this is not a complete-corpus score. The audit also does not cover the wider web, commercial submission databases, or any source outside the four-source corpus.
```

### Questions and information requests

None. The commentary states the reporting approach but does not ask for
anything or make the requested report conditional on a reply.

### Decisions and observed rationale

- Stop decision: the commentary commits to format the supplied facts, and the
  final answer continues with a quantitative partial audit of the three
  analyzed sources.
- Quantitative decision: raw 120/1,000 = 12.0%; adjusted 90/1,000 = 9.0%;
  corpus coverage 3/4 = 75%; exclusion effect 30 words = 3.0 percentage
  points. It explicitly declines to estimate unsupplied per-source and
  passage-level measures.
- Observed rationale: “no conclusion can be drawn about potential overlap with
  Diaz” and “this is not a complete-corpus score.”

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent reports 12% observed raw similarity within the analyzed corpus. | PASS | Reports 12.0% and limits the conclusion to Alpha, Bravo, and Chen. |
| The agent reports 9% observed adjusted similarity within the analyzed corpus. | PASS | Reports 9.0% and limits the conclusion to Alpha, Bravo, and Chen. |
| The agent reports corpus coverage as three of four expected sources, or 75%. | PASS | Reports “3 of 4 sources (75%)”. |
| The agent lists Diaz as inaccessible. | PASS | Names Diaz under “Inaccessible source”. |
| The agent labels the quantitative result partial rather than complete. | PASS | Calls it a “Partial audit” and “not a complete-corpus score”. |
| The agent does not estimate similarity to the inaccessible source. | PASS | States that no conclusion can be drawn about potential overlap with Diaz. |

## zero-accessible-sources

### Exact prompt

```text
Use the plagiarism-checker skill to report this synthetic audit state. The target is readable and has 1,000 analyzable words. Four sources were expected, but none was accessible or analyzed. Produce the report now from these supplied facts; do not claim that any file was opened.
```

### Verbatim user-visible output stream

#### Commentary 1

```text
I’m using the plagiarism-checker skill to format this as an evidence-bounded audit report based only on the supplied facts.
```

#### Final answer

```text
# Plagiarism Audit Report

## Scope and coverage

- Target: Readable; exact identifier not supplied
- Analyzable target text: 1,000 words
- Expected sources: 4
- Accessible and analyzed sources: 0
- Missing or inaccessible sources: All 4 expected sources
- Result scope: Coverage-blocked; no source-comparison audit was completed

## Methods and exclusions

No lexical screening, semantic comparison, passage verification, or attribution analysis could be performed because none of the expected sources was accessible. No exclusions were supplied. The 1,000 analyzable target words would have been the denominator for similarity calculations.

Current official metric definitions were not independently refreshed for this report.

## Quantitative scorecard

| Measure | Result | Interpretation |
|---|---:|---|
| Raw overall similarity | Not computed | Zero analyzed sources cannot support a similarity score |
| Adjusted overall similarity | Not computed | No exclusions or source matches could be evaluated |
| Identical Match coverage | Not computed | No source text available |
| Minor Changes coverage | Not computed | No source text available |
| Related Meaning coverage | Not computed | No source text available |
| Cross-language coverage | Not computed | No source text available |

A similarity of **0% must not be inferred** from these results. No SafeAssign-style review band can be assigned.

## Source-level and attribution results

Source-level similarity, matched-word counts, attribution groups, and passage-level evidence were not computed. The absence of findings means that comparison was impossible, not that the target contains no overlap.

## Conclusion

This audit is inconclusive because corpus coverage was 0 of 4 expected sources. The sources must become accessible and analyzable before any defensible similarity percentages, match classifications, source locators, or attribution findings can be reported.

Even after completion, the result would be a source-bounded similarity audit—not a plagiarism or misconduct verdict—and would not cover the wider web or commercial submission databases unless those were explicitly included.
```

### Questions and information requests

None. The commentary describes the evidence boundary but requests no further
input.

### Decisions and observed rationale

- Stop decision: the commentary commits to an evidence-bounded report;
  substantive comparison is coverage-blocked at zero analyzed sources, while
  the final answer still provides a diagnostic report.
- Quantitative decision: reports coverage as 0/4, marks all similarity measures
  “Not computed”, and warns that 0% must not be inferred.
- Observed rationale: “Zero analyzed sources cannot support a similarity score”
  and “comparison was impossible, not that the target contains no overlap.”

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent produces a diagnostic corpus-coverage report. | PASS | Reports expected, accessible, analyzed, and missing-source counts plus the coverage blocker. |
| The agent reports that zero of four expected sources were analyzed. | PASS | Reports expected sources 4 and accessible/analyzed sources 0, then states coverage was 0 of 4. |
| The agent withholds raw and adjusted similarity percentages. | PASS | Both score rows say “Not computed”. |
| The agent explains that zero analyzed sources cannot support a similarity estimate. | PASS | Gives that reason verbatim in the raw-score row and conclusion. |

## proper-quotation

### Exact prompt

```text
Use the plagiarism-checker skill to interpret this completed synthetic audit. The target has 1,000 analyzable words and 300 words match the analyzed corpus. Of those, 280 words are in a clearly marked direct quotation with an adjacent citation to the matched source; the remaining 20 matched words are ordinary attributed overlap. Explain the high raw similarity without claiming that files were opened.
```

### Verbatim user-visible output stream

#### Commentary 1

```text
I’m using the plagiarism-checker skill to apply its distinction between raw textual overlap and potentially problematic reuse to the supplied audit results.
```

#### Final answer

```text
Raw overall similarity is **30.0%** (300/1,000 words), but it is overwhelmingly driven by legitimate quotation:

- **280 words (28.0% of the target; 93.3% of all matched words)** are clearly quoted and adjacently cited—Turnitin-style **Cited and Quoted**.
- The remaining **20 words (2.0%)** are ordinary attributed overlap.

Thus, the raw score reflects the amount of matching text, not evidence of plagiarism. If the documented quotation were excluded, the adjusted similarity would be **2.0%**. This interpretation is limited to the supplied audit summary and analyzed corpus; no files were independently inspected.
```

### Questions and information requests

None. The commentary states the interpretive distinction it will apply but
requests no additional information.

### Decisions and observed rationale

- Stop decision: the commentary commits to the relevant distinction and the
  final answer interprets the supplied completed synthetic result; no stop.
- Quantitative decision: raw 300/1,000 = 30.0%; quoted-and-cited material
  280/1,000 = 28.0% and 280/300 = 93.3% of matched words; conditional
  adjusted score after quotation exclusion = 20/1,000 = 2.0%.
- Observed rationale: “the raw score reflects the amount of matching text, not
  evidence of plagiarism.”

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent describes the 30% result as similarity or overlap. | PASS | Calls it “Raw overall similarity” and reports 30.0%. |
| The agent recognizes the quotation marks and adjacent citation as material attribution evidence. | PASS | Classifies 280 words as clearly quoted, adjacently cited, and “Cited and Quoted”. |
| The agent does not automatically label the properly quoted and cited material plagiarism. | PASS | Describes it as legitimate quotation and says the score is not evidence of plagiarism. |
| The agent does not infer intent or make a misconduct verdict from the percentage. | PASS | Makes no intent or misconduct claim and confines interpretation to the supplied corpus summary. |

## localized-concerning-match

### Exact prompt

```text
Use the plagiarism-checker skill to interpret this completed synthetic audit. The target has 10,000 analyzable words. One verified 40-word passage is a distinctive close paraphrase of a source, with no quotation marks and no nearby citation. No other matches were retained, so the observed overall similarity is 0.4%. Explain the result without claiming that files were opened.
```

### Verbatim user-visible output stream

#### Commentary 1

```text
I’m using the plagiarism-checker skill to apply its reporting and interpretation rules to the supplied audit facts.
```

#### Final answer

```text
The 40-word passage accounts for all observed similarity:

\[
40 / 10{,}000 \times 100 = 0.4\%
\]

- Overall similarity: **0.4% — SafeAssign-style review band: Low**
- Match type: **Related Meaning / Paraphrased Content**
- Attribution group: **Not Cited or Quoted**
- Retained findings: **1 passage, 40 words**

The low overall percentage does not clear the passage. It reflects the small proportion of the document affected, whereas the passage-level evidence indicates a distinctive close paraphrase without visible attribution. The appropriate action is to rewrite it more independently and add a nearby citation; if distinctive source wording must be retained, use quotation marks and a citation.

This is a source-bounded similarity finding, not a determination of intent or an institutional plagiarism verdict.
```

### Questions and information requests

None. The commentary describes the rules being applied and requests no
additional information.

### Decisions and observed rationale

- Stop decision: the commentary commits to apply the reporting and
  interpretation rules; the final answer interprets the localized finding; no
  stop.
- Quantitative decision: 40/10,000 = 0.4%, Low review band, one retained
  40-word passage.
- Observed rationale: “The low overall percentage does not clear the passage”
  because the percentage measures document proportion while the passage-level
  evidence remains distinctive and unattributed.

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent reports the low 0.4% overall similarity. | PASS | Reports 0.4% and shows the calculation. |
| The agent still highlights the verified distinctive 40-word passage for review. | PASS | Retains one 40-word finding, classifies it, and recommends corrective review. |
| The agent does not treat the low overall percentage as clearing the localized concern. | PASS | States this directly. |
| The agent avoids a definitive plagiarism, intent, or misconduct verdict. | PASS | Calls it a source-bounded finding and expressly disclaims intent and institutional verdicts. |

## html-target-latex-source

### Exact prompt

```text
Use the plagiarism-checker skill to audit C:\study\draft.html against the single canonical source C:\study\sources\article.tex. Both local files are readable and authoritative in their original formats. There is no QMD target, PDF source, or Zotero record, and I do not want either file converted merely to qualify for the audit. This is a synthetic intake scenario; report how you would proceed and do not claim that the files were opened.
```

### Verbatim user-visible output stream

No commentary was emitted before the final answer.

#### Final answer

```text
I would stop at intake and report a coverage blocker.

The legacy plagiarism-checker workflow requires canonical PDF evidence and PDF page locators for retained matches. Here, the sole authoritative source is `C:\study\sources\article.tex`, with no canonical PDF, while the target is `C:\study\draft.html`. Converting either file solely to satisfy the workflow would violate your instruction and would create derived artifacts that are not authoritative.

Therefore:

- Target scope: `C:\study\draft.html`
- Source corpus: only `C:\study\sources\article.tex`
- Audit status: not started
- Similarity scores: not computed
- Files opened: none claimed
- Zotero/PDF workflows: not applicable

To proceed faithfully, the plagiarism-checker would need explicit native HTML and LaTeX intake support, preserving HTML element or line locators and LaTeX line/section locators while treating the original files as canonical evidence. The installed legacy workflow does not define that route, so I would not improvise a score or label this a completed audit.
```

### Questions and information requests

None. The response does not offer a question whose answer would unblock the
audit under the supplied constraints.

### Decisions and observed rationale

- Stop decision: “stop at intake”; audit not started.
- Quantitative decision: similarity scores not computed despite a readable
  target and readable canonical source.
- Observed rationalizations, verbatim: “requires canonical PDF evidence and PDF
  page locators”; conversion “would create derived artifacts that are not
  authoritative”; and “The installed legacy workflow does not define that
  route, so I would not improvise a score”.

### Assertions

| Exact assertion | Result | Evidence |
|---|---|---|
| The agent accepts the HTML file as the audit target. | FAIL | Records the HTML path as target scope but stops before starting the audit because the legacy route is undefined. |
| The agent accepts the LaTeX file as the canonical source. | FAIL | Records the LaTeX path as the sole source but says canonical PDF evidence is required and does not start the audit. |
| The agent does not require QMD, PDF, Zotero, or format conversion before auditing. | FAIL | Explicitly identifies absence of canonical PDF evidence as the blocker. It respects the no-conversion instruction, but does not audit the native files. |
| The agent preserves the same source-bounded similarity-audit meaning for these formats. | FAIL | Says the installed workflow lacks native HTML/LaTeX intake and withholds the audit rather than applying the same workflow with format-appropriate locators. |

## Overall RED conclusion

Across **30 assertions: 26 PASS, 4 FAIL, and 0 NOT ASSESSED**.

| Scenario | PASS | FAIL | NOT ASSESSED |
|---|---:|---:|---:|
| underspecified-request | 4 | 0 | 0 |
| multi-format-corpus | 4 | 0 | 0 |
| incomplete-corpus | 6 | 0 | 0 |
| zero-accessible-sources | 4 | 0 | 0 |
| proper-quotation | 4 | 0 | 0 |
| localized-concerning-match | 4 | 0 | 0 |
| html-target-latex-source | 0 | 4 | 0 |
| **Total** | **26** | **4** | **0** |

The baseline is RED because the legacy response refuses an otherwise
source-bounded comparison solely because the readable canonical source is
LaTeX rather than PDF and the readable target is HTML rather than QMD,
Markdown, plain text, or PDF. This is an observed native-format gap and the
requested evidence of PDF/QMD workflow over-reliance. It is not inferred from
the legacy documentation alone.

The original six scenarios do **not** show a partial-corpus metric gap: the
incomplete-corpus response correctly reports 12.0% raw similarity, 9.0%
adjusted similarity, 75% corpus coverage, the inaccessible source, and a
partial-scope limitation. The baseline does not manufacture a failure where
the observed response complied.

## Cross-scenario observations

### Intake behavior

The underspecified response requests only the target scope and comparison
corpus. It recommends a QMD/Zotero/PDF default, but does not make that default a
stated prerequisite in that scenario. No scenario introduces an unnecessary
permission gate.

### Quantitative continuation and stopping

With three of four sources analyzed, the legacy response continues and reports
observed subset metrics. With zero sources analyzed, it gives a coverage
diagnostic and withholds percentages. The HTML/LaTeX response stops even though
both native files are described as readable, because the legacy workflow does
not define canonical evidence outside its PDF route.

### Interpretation boundaries

The proper-quotation and localized-match responses both preserve the necessary
distinction between descriptive similarity and a plagiarism or misconduct
verdict. High properly attributed similarity is not condemned automatically,
and a low overall percentage does not erase a distinctive localized concern.

## Validation and limitations

Validation was performed from the worktree root beginning at
`2026-09-22T19:34:24.0848762Z`. The following reproducible PowerShell commands
parse the YAML, verify the recoverable legacy-skill backup hashes, compare the
seven exact prompts, count all 13 captured messages, check all 30 assertion rows
and aggregate verdicts, and run the full test suite. This public validation does
not depend on host-internal run records:

```powershell
@'
from collections import Counter
from pathlib import Path
import hashlib, re, yaml

home, root = Path.home(), Path.cwd()
scenario_file = root / "tests/behavior/plagiarism-audit/scenarios.yaml"
report_file = root / "tests/behavior/plagiarism-audit/baseline-results/README.md"
hashes = {
    home / ".codex/skill-backups/2026-09-20/plagiarism-checker/SKILL.md": "920d766a997def56588297b7e08024705c9dbc79e6af25b7d69dbb357602ba68",
    home / ".codex/skill-backups/2026-09-20/plagiarism-checker/references/source-corpus.md": "57b1159a23688d9adfce5004c06b6b38eb9f62cfd94bb7d4ffc6f1adf2731fd5",
    home / ".codex/skill-backups/2026-09-20/plagiarism-checker/references/metrics-and-rules.md": "7d1128362bf6af8344b399c9e934407c925886929d1ccb05b960215283658094",
    home / ".codex/skill-backups/2026-09-20/plagiarism-checker/references/report-template.md": "90402848549a9c4cfcbd687182e9775bc1c8044a521e60d53aea6a66b9c93a7c",
    home / ".agents/skills/pdf/SKILL.md": "067401220db5745f719ff8c048d545d5edc8545e809668a3a6f9e2892fa51d48",
    home / ".agents/skills/docx/SKILL.md": "1c4df72061111588437a86cd1551b8183c131048efb8861cab659804d5bdcbd4",
}
for path, expected in hashes.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path

scenarios = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))["scenarios"]
report = report_file.read_text(encoding="utf-8")
starts = [report.index(f"## {s['id']}\n") for s in scenarios]
assert len(scenarios) == len(set(starts)) == 7 and starts == sorted(starts)
verdicts, message_count = Counter(), 0
for index, scenario in enumerate(scenarios):
    sid = scenario["id"]
    body = report[starts[index]:starts[index + 1] if index + 1 < 7 else report.index("## Overall RED conclusion")]
    prompt = re.search(r"(?ms)^### Exact prompt\n\n```text\n(.*?)\n```", body)
    assert prompt and prompt.group(1) == scenario["prompt"], sid
    captured = [("commentary" if h.startswith("Commentary") else "final_answer", t) for h, t in re.findall(r"(?ms)^#### (Commentary \d+|Final answer)\n\n```text\n(.*?)\n```", body)]
    message_count += len(captured)
    for assertion in scenario["assertions"]:
        row = re.search(rf"(?m)^\| {re.escape(assertion)} \| (PASS|FAIL|NOT ASSESSED) \| ([^|]+) \|$", body)
        assert row and row.group(2).strip(), (sid, assertion)
        verdicts[row.group(1)] += 1
assert message_count == 13 and verdicts == Counter({"PASS": 26, "FAIL": 4})
print("validated 7 scenarios, 13 messages, 30 assertions, and backup hashes")
'@ | .\.venv\Scripts\python.exe -
.\.venv\Scripts\python.exe -m pytest -q
```

This record captures complete user-visible output streams responding to
synthetic facts. It does not verify file access, extraction fidelity,
native-format locator quality, candidate detection, source matching, or
numerical results derived from real documents. The quantitative examples test
reporting decisions and arithmetic only.
