# Plagiarism audit report template

Adapt the detail to the selected scope, but preserve this section order and the separation among corpus coverage, textual similarity, attribution signals, and interpretation. Give every retained match a target locator and an authoritative source locator when available. Reproduce only the minimum text needed to demonstrate a parallel.

Label every reported percentage either `Complete` or `Partial`. `Complete` means the non-empty expected-source set was fully analyzed; it describes expected-source-set coverage only and is not a favorable verdict or a claim of complete source-text extraction. Report source-text coverage separately. For a partial corpus, prefix each metric label with `Observed`, add `within the analyzed corpus`, and never estimate similarity for unseen sources.

## 1. Target and corpus coverage

Record:

```markdown
Target: [absolute path and included locator range]
Selected target scope: [sections/pages/blocks]
Manifest: [absolute path; generated date/time]
Expected sources: [n]
Resolved sources: [n]
Extracted sources: [n, with extraction quality reported separately]
Analyzed expected sources: [n]
Inaccessible source artifacts: [n]
Unusable source extractions: [n]
Unresolved source mappings: [n]
Unanalyzed expected sources: [n]
Expected-source-set coverage label: [Complete or Partial]
Source-text coverage: [Complete/Partial/Unknown; identify affected sources and missing sections/pages]
```

Define the expected corpus and explain why each source counts once. Keep source resolution, artifact access, extraction usability, and analysis distinct. The four limitation counts can overlap, so identify any source counted in more than one. State any target text that could not be analyzed; expected-source-set completeness does not repair incomplete target or source-text extraction.

## 2. Extraction, method settings, and exclusions

State:

- target and source extraction methods, conversion notes, and quality limitations;
- target tokenizer and analyzable-target-word count;
- lexical candidate detector and every minimum-match or similarity setting;
- semantic or cross-language comparison method, when used;
- match verification rule and treatment of overlapping sources/categories;
- evidence grouping key: canonical source artifact/version, match type/category, attribution group, target document block, and coherent source block/span;
- raw denominator and numerator definitions;
- each adjusted exclusion and whether it changes the numerator, denominator, or both;
- whether the authoritative artifacts were inspected for passages and locators;
- the access date used to verify external metric definitions and any optional review bands.

Do not present candidate-generation settings as commercial-product metrics. Do not infer source support merely from textual overlap.

## 3. Complete or partial quantitative scorecard

If at least one expected source has been analyzed, this scorecard is mandatory. Show numerator, denominator, percentage, and `Complete` or `Partial` on every percentage. With a partial corpus, every metric label begins `Observed` and every interpretation says `within the analyzed corpus`. With zero analyzed sources, write `not computed: zero analyzed sources` instead of estimating a percentage.

With a zero raw analyzable target-word denominator, produce a diagnostic coverage and method report and no similarity percentages. If the raw denominator is nonzero but target-text exclusions make the adjusted denominator zero, retain the valid raw result and write adjusted similarity as `Unavailable (zero adjusted denominator)`; never report that state as 0%.

The first score table must keep corpus coverage immediately adjacent to overall similarity. Use the `Observed` heading only for the `Partial` alternative:

| Scope label | Corpus coverage (Complete) / Observed corpus coverage (Partial) | Raw overall similarity (Complete) / Observed raw overall similarity (Partial) | Adjusted overall similarity (Complete) / Observed adjusted overall similarity (Partial) |
|---|---:|---:|---:|
| Complete/Partial | analyzed expected sources / all expected sources = x.x% [Complete/Partial] | unique matched target words / analyzable target words = x.x% [Complete/Partial] | unique adjusted matched words / adjusted analyzable target words = x.x% [Complete/Partial] |

Use the same scope label for corpus coverage and similarity only when it accurately describes the defined expected corpus. Name all exclusions below the table; raw and adjusted values differ only through those documented exclusions.

Use `Observed [category] coverage (Partial)` for partial-corpus rows and `[category] coverage (Complete)` for complete-corpus rows.

| Metric label | Basis | Numerator / denominator | Result and scope label | Interpretation |
|---|---|---|---:|---|
| Observed Identical Match coverage (Partial) / Identical Match coverage (Complete) | [Raw or Adjusted] | unique union of verified category target positions / [raw or adjusted analyzable target words] | x.x% [Complete/Partial] | repository category adapted from Copyleaks vocabulary; within the analyzed corpus when Partial |
| Observed Minor Changes coverage (Partial) / Minor Changes coverage (Complete) | [Raw or Adjusted] | unique union of verified category target positions / [raw or adjusted analyzable target words] | x.x% [Complete/Partial] | repository category adapted from Copyleaks vocabulary; within the analyzed corpus when Partial |
| Observed Related Meaning / Paraphrased Content coverage (Partial) / Related Meaning / Paraphrased Content coverage (Complete) | [Raw or Adjusted] | unique union of verified category target positions / [raw or adjusted analyzable target words] | x.x% [Complete/Partial] | repository category adapted from Copyleaks vocabulary; within the analyzed corpus when Partial |
| Observed Cross-language / Translated Match coverage (Partial) / Cross-language / Translated Match coverage (Complete) | [Raw or Adjusted] | unique union of verified category target positions / [raw or adjusted analyzable target words] | x.x% [Complete/Partial] | repository category adapted from Copyleaks Cross-Language Detection; within the analyzed corpus when Partial |

Add unique matched-position, retained-evidence-passage, and unique-target-block counts for every category. State whether category rows overlap; never sum overlapping percentages as though they were mutually exclusive. Include a review band verified on the reported access date only when permitted by the metrics reference, label it a review band, and do not call it a plagiarism probability.

## 4. Source-level results

| Scope | Metric label | Source | Stable identifier | Basis | Numerator / denominator | Result and scope label | Matched target positions | Retained evidence passages | Unique target blocks | Authoritative-artifact inspection |
|---|---|---|---|---|---|---:|---:|---:|---:|---|
| Partial | Observed per-source similarity | Author, year, title | DOI/citekey/other ID | [Raw or Adjusted] | unique union of source-matched target positions / [raw or adjusted analyzable target words] | x.x% [Partial] | n | n | n | inspected/not inspected/partially inspected |
| Complete | Per-source similarity | Author, year, title | DOI/citekey/other ID | [Raw or Adjusted] | unique union of source-matched target positions / [raw or adjusted analyzable target words] | x.x% [Complete] | n | n | n | inspected/not inspected/partially inspected |

For a partial corpus, add `within the analyzed corpus` and do not infer what an inaccessible version or unseen source might add. Explain overlapping matches when per-source percentages do not sum to overall similarity. Keep retained-evidence-passage counts separate from unique-target-block counts. The same target positions may occur in multiple source relationships but count once in the unique per-source union and once in overall similarity.

## 5. Attribution-group summary

| Turnitin-style group | Passages | Matched words | Notes |
|---|---:|---:|---|
| Not Cited or Quoted | n | n | Review visible citation and quotation signals |
| Missing Quotations | n | n | Review exact and minor-change wording |
| Missing Citation | n | n | Verify citation association |
| Cited and Quoted | n | n | Similarity may be legitimate |

Treat these as visible-signal groups, not proprietary classifications or substantive citation-support verdicts. Passage counts mean verified retained evidence passages. Record extraction or citation-association uncertainty.

## 6. Passage-level parallel evidence

For each verified retained evidence passage:

```markdown
### Match [ID]

- Target locator: [available document locator]
- Source: [title and stable identifier]
- Authoritative source locator: [available document locator]
- Match type: [verified category; identify each repository label as adapted from Copyleaks vocabulary, including Cross-language / Translated Match as adapted from Copyleaks Cross-Language Detection]
- Attribution group: [Turnitin-style group]
- Verification status: verified

Target passage: "[minimum text needed to show the parallel]"

Source passage: "[minimum text needed to show the parallel]"

Assessment: [distinctive overlap, relevant context, conventional-language alternative, and uncertainty]

Recommended review action: [quote and cite, rewrite and cite, verify locator, or no similarity-related action based on this corpus]
```

Do not make substantive source-support judgments here; reserve them for a citation-support audit. Avoid unnecessary reproduction of copyrighted text.

### Candidate diagnostics (excluded)

Candidate diagnostics may be partial or unverified and are excluded from all numerators and retained evidence. Keep them visibly separate from retained passages:

| Candidate ID | Target locator | Candidate source | Status | Reason excluded | Next verification step |
|---|---|---|---|---|---|
| D01 | Section/paragraph or page | Source identifier | partial/unverified | Relationship or passage not verified | Inspect authoritative target/source context |

## 7. Inaccessible sources needed for broader coverage

List each expected source that was inaccessible, unusable, or unresolved. Include its identifier or candidate mapping, current state, attempted route, affected target passages when known, and the evidence needed to analyze it. State how it changes corpus coverage without assigning a similarity value or substantive verdict to unseen content.

## 8. Limitations and non-verdict conclusion

Identify:

- incomplete target extraction or conversion and its effect on analyzable target words;
- inaccessible or poor-quality sources and their effect on corpus coverage;
- scope not searched, including the wider web and commercial submission databases;
- possible missed semantic or translated matches;
- possible match-classification, extraction, locator, and citation-detection errors;
- exclusions and any uncertainty they introduce.

Conclude with the applicable complete or observed-partial metrics, their corpus coverage, and the most important passage-level evidence. State explicitly that the report is a source-bounded similarity audit, not a plagiarism verdict, misconduct finding, probability estimate, or reproduction of a proprietary detector.
