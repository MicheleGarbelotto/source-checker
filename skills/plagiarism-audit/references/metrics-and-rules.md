# Metrics and classification rules

## Operational boundary

This audit records source-bounded textual similarity and visible attribution signals. It does not determine intent or make a plagiarism, authorship, legal, institutional, or research-misconduct finding. Properly quoted and credited text can be highly similar. Common knowledge, standard phrases, and limited conventional method wording require passage-level judgment.

Use an applicable institutional policy when it adds requirements, but do not turn a similarity percentage into a verdict or acceptance threshold.

## Counting populations

**Analyzable target words** are word tokens in the selected target scope that the documented extraction and tokenization process recovered reliably enough to compare. Record the selected scope, tokenizer, and count. Technical extraction failures are outside this population and must be disclosed as target-extraction limits.

**Matched target words** are target token positions among analyzable target words, retained in at least one verified textual-overlap match to an analyzed source. For semantic or cross-language matches, the positions are the target words in the smallest verified aligned target span. Those positions are eligible for per-source, category, and overall unions. Candidate matches do not enter a numerator until the relevant target-source relationship has been verified.

Overall similarity deduplicates the global union of verified target-token positions across all retained match relationships; each target position is counted once in the overall numerator.

A **retained evidence passage** is one verified relationship between a target passage and a source passage. Its grouping key is the canonical source artifact and version, match type/category, attribution group, target document block, and coherent source block or span. Merge evidence only when both the target spans and the source spans are coherent and contiguous or overlapping; never merge across grouping keys.

A **unique target block** is a distinct target document block represented by one or more retained evidence passages. Retained-evidence-passage counts and unique-target-block counts are separate: multiple passages can occur in one target block, and one target position can participate in separate verified relationships.

Retained evidence passages must be verified. Partially verified and unverified items remain candidate diagnostics and are excluded from every numerator and from retained evidence. The same target positions may appear in multiple retained-evidence rows when their grouping keys differ, but those positions are counted once in overall similarity.

An **expected source** is a distinct source record required by the defined corpus. An **analyzed expected source** is an expected source whose usable content was compared deeply enough for the selected audit scope. Resolution, download, or extraction alone does not make a source analyzed.

## Required formulas and scope labels

Use these transparent formulas. Show the numerator and denominator next to every percentage:

```text
observed overall similarity = unique target words matched in analyzed corpus / analyzable target words * 100
observed per-source similarity = unique union of target positions matched to that analyzed source / analyzable target words * 100
match-type coverage = unique union of target positions in that verified category / analyzable target words * 100
corpus coverage = analyzed expected sources / all expected sources * 100
```

Count each matched target word once in the overall numerator even when the word matches multiple sources or categories. Retain all verified source and category relationships separately. Per-source and category percentages may overlap and need not sum to the overall percentage; overall target words are counted once.

If the raw analyzable target-word denominator is zero, produce a diagnostic coverage and method report and report no similarity percentages. Do not convert an empty target-word population into a zero-similarity result.

Report both variants:

- **Raw overall similarity:** apply the observed overall formula to the full analyzable target-word population before optional reporting exclusions.
- **Adjusted overall similarity:** apply the same formula after the stated exclusions. A target-text exclusion removes the excluded words from the adjusted denominator and their matches from the numerator. A match-only exclusion leaves the denominator unchanged.

Raw and adjusted results differ only through documented exclusions. Keep the tokenizer, analyzed corpus, verification decisions, and counting rules fixed, and list each exclusion with whether it changes the numerator, denominator, or both. State whether each per-source and match-type result uses the raw or adjusted analyzable-target-word denominator.

Apply match-only exclusions to verified match relationships first, then recompute the union of retained verified target positions for the overall numerator. A target token position leaves the overall numerator only when no retained verified match remains for that position. Removing one source or category relationship must not remove a position that remains matched through another retained relationship.

Compact overlap example:

```text
analyzable target positions = 10
source A verified positions = {2, 3, 4}
source B verified positions = {4, 5}
raw union = {2, 3, 4, 5} = 4 / 10 = 40%
evidence row A = (Source A, Identical Match, Not Cited or Quoted, block T1): {2, 3, 4}
evidence row B = (Source B, Identical Match, Not Cited or Quoted, block T1): {4, 5}
after excluding source A relationship = {4, 5} = 2 / 10 = 20%
```

Position 4 appears in both evidence rows but once in the raw union. Position 4 remains matched through Source B after the Source A exclusion, so it remains in the adjusted numerator.

If the adjusted denominator is zero after target-text exclusions, raw similarity may remain reported when its denominator is nonzero, but adjusted similarity is `Unavailable (zero adjusted denominator)`; never report this state as 0%.

Corpus coverage is independent of similarity. If the expected-source denominator is zero, report corpus coverage as unavailable rather than dividing by zero.

## Complete and partial corpus reporting

When at least one expected source has been analyzed, the report must compute quantitative similarity results over the analyzed source subset. With zero analyzed sources, issue a diagnostic coverage report and no similarity percentage.

For a partial corpus, prefix every metric label with `Observed` and state that it applies `within the analyzed corpus`. Label every percentage `Partial`, place corpus coverage beside the similarity result, and name the unanalyzed expected sources. Do not estimate unseen-source similarity, extrapolate the observed percentage to unavailable sources, or imply that the partial result describes the complete expected corpus.

When the expected-source set is non-empty and all expected sources are analyzed, label every percentage `Complete`. `Complete` describes expected-source-set coverage only, not full source-text coverage, adequacy, originality, or misconduct risk. Report partial source-text coverage separately, even when expected-source-set coverage is `Complete`.

## Match-type coverage

Use these repository labels, adapted from public Copyleaks vocabulary:

- **Identical Match:** word-for-word or effectively verbatim wording.
- **Minor Changes:** localized substitutions, inflectional changes, omissions, additions, or superficial reordering while substantial wording remains.
- **Related Meaning / Paraphrased Content:** substantially reworded text that preserves the source's meaning or distinctive idea sequence.
- **Cross-language / Translated Match:** a repository adaptation derived from Copyleaks's public **Cross-Language Detection** feature, for correspondence consistent with translation. The translation direction and any common-source explanation remain undetermined unless separately verified.

For each verified category, report the unique union of target positions, match-type coverage, retained-evidence-passage count, and unique-target-block count. A target span can belong to more than one category when the classification purpose requires it; disclose category overlap and never sum overlapping percentages as if they were mutually exclusive. Explain borderline evidence and uncertainty instead of forcing a stronger label.

These labels do not reproduce or certify compatibility with a proprietary algorithm or detector. The audit must not claim commercial-product equivalence, accuracy, or affiliation.

## Attribution groups

Use these **Turnitin-style** visible-signal groups only as public vocabulary:

- **Not Cited or Quoted:** neither an associated in-text citation nor quotation marks were detected.
- **Missing Quotations:** an associated citation was detected, but substantially matching language is not marked as quotation.
- **Missing Citation:** quotation marks were detected, but an associated citation was not.
- **Cited and Quoted:** both an associated citation and quotation marks were detected.

Citation recognition can fail when a citation is distant, nonstandard, or lost during extraction. Verify the authoritative target when possible. The groups describe visible attribution signals; they do not establish source support or reproduce a proprietary grouping algorithm.

## Contextual review bands

The official SafeAssign documentation accessed on 2026-09-23 gave the numeric ranges retained here as **SafeAssign-derived contextual review labels**: **Low** below 15%, **Medium** from 15% through 40%, and **High** above 40%. Apply a band only to the named overall score, and omit the bands if the official definitions cannot be reverified when a current-product comparison is requested.

These labels do not estimate the probability of plagiarism or the risk of misconduct, and they are not decision thresholds. A low band can contain a serious localized match, while a high band can be driven by legitimate quoted or conventional material. See [methodology and attribution](methodology-and-attribution.md) for the official source and adaptation boundary.

## Interpretation constraints

- Similarity is descriptive evidence, not a plagiarism verdict.
- Do not derive a composite score from match type, attribution group, or review band.
- Do not set an automatic acceptance, rejection, or rewriting threshold.
- Keep corpus coverage, target-extraction coverage, and similarity separate.
- Keep candidate-detection confidence separate from the seriousness of a verified passage.
- List exclusions and detector settings next to the score they affect.
- Treat authoritative source artifacts as canonical for quotations, locators, tables, figures, formulas, and disputed conversions.
- Do not make substantive citation-support judgments in this audit.

## Source provenance

The external vocabulary and review-band ranges were checked against the official pages listed in [methodology and attribution](methodology-and-attribution.md) on 2026-09-23. They remain descriptive inputs to the repository's independently defined rules, not claims of current product equivalence.
