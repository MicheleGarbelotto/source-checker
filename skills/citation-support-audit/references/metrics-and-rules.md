# Citation metrics and support rules

## Unit of analysis

Use an atomic, independently verifiable claim. Preserve material qualifiers when splitting compound claims. Document the segmentation rule and the total number of eligible claims.

These are academic-document adaptations of statement-level citation evaluation. Label the metrics `ALCE-style`; do not claim direct comparability with published benchmark scores. See [methodology-and-attribution.md](methodology-and-attribution.md) for the inherited methodological references and their verification status.

## Support labels

- **Fully supports:** the source substantiates the whole associated claim, including all material qualifiers.
- **Partially supports:** the source substantiates a material portion of the claim, or supports it under narrower qualifiers.
- **Does not support:** the source is merely topically related, supports a different proposition, or provides no evidence for the claim.
- **Contradicts:** the source provides evidence or a statement incompatible with the claim.
- **Unverifiable:** the necessary source or passage is inaccessible, illegible, incomplete, or cannot be located reliably.

For terminology used in the main workflow, **Unsupported** maps to **Does not support**. **Contradictory** maps to **Contradicts**. An unresolved citation-to-source mapping remains a reference-resolution state rather than a substantive support label.

Unverifiable must not be treated as unsupported. Unavailable evidence has not been inspected and therefore is not evidence that a source fails to support a claim. Preserve reference-resolution problems, evidence-availability limits, and substantive verdicts as separate states.

Typical partial-support problems include population or task mismatch, correlation presented as causation, mechanism confused with outcome, a review described as though it conducted the study, and a supported clause embedded in a broader unsupported claim.

## Metric populations and eligibility

An **eligible claim** is an atomic claim within the selected scope that requires citation support under the documented segmentation rule. An eligible claim that warrants citation but lacks one is classifiable for claim-level recall and contributes `0`. For claims with citations, evidence accessibility governs classifiability: the evidence needed for a substantive verdict must be accessed and interpreted reliably. A citation is classifiable when its mapping and relevant evidence can be evaluated reliably.

For precision, each in-scope claim-citation association is one counting unit. Treat grouped citations as separate units when each is associated with the claim. If the same source is cited for different eligible claims, repeated citations count as separate associations for each claim; do not multiply repeated mentions of the same source for the same claim unless they perform distinct citation functions that are documented in the audit.

A claim-citation association is classifiable for precision only when its individual contribution and the joint-support gate are both classifiable. If joint support is unverifiable, all attached claim-citation associations are excluded from verified-subset citation precision, including associations whose individual sources are otherwise readable.

Whole-scope citation recall is allowed only when all eligible claims are classifiable. Whole-scope citation precision is allowed only when all in-scope claim-citation associations are classifiable. Otherwise, the report must compute the applicable verified-subset metrics when at least one eligible claim is classifiable. If no eligible claim is classifiable, report the verified-subset claim metrics as unavailable and retain the coverage and diagnostic counts. Never present a verified subset as a whole-scope result. The verified subset is non-random because access and extractability determine inclusion; it cannot estimate or represent the unavailable scope.

## Required formulas

Use these formulas and show the numerator and denominator beside every reported percentage:

```text
whole-scope citation recall = fully supported eligible claims / all eligible claims * 100
whole-scope citation precision = supporting citations / all citations evaluated * 100
verified-subset citation recall = fully supported classifiable claims / classifiable eligible claims * 100
verified-subset citation precision = supporting classifiable citations / classifiable citations * 100
audit coverage = classifiable eligible claims / all eligible claims * 100
corpus coverage = analyzed expected sources / all expected sources * 100
```

For recall, count an eligible claim as fully supported only when it has a citation and the evidence from its cited set supports the whole claim, including all material qualifiers. An uncited citation-worthy claim or a partially supported claim contributes `0` when it belongs in the applicable denominator; retain its qualitative diagnosis.

For precision, assess joint support first and then each citation's contribution. A citation is supporting when the cited set fully supports the claim and that individual citation fully or partially supports it. A classifiable citation that either does not support or contradicts the claim contributes `0`; so does a classifiable citation in a cited set that does not fully support the claim. Do not require a mathematically minimal set: legitimate redundant support is not an error. If one of two citations fully supports a claim and the other is irrelevant, claim recall is `1/1` and citation precision is `1/2`.

Apply these mixed cited-set rules explicitly. A cited set containing a source that contradicts a material part of the claim is not fully supported, even if another source supports it; report the disagreement. When one source fully supports the claim and another offers narrower or partial support, the cited set can remain fully supported and the partial source can contribute to precision. An unavailable citation is unverifiable for precision but does not prevent full joint support when another accessible citation independently fully supports the claim; when the accessible citations do not fully support the claim, the joint result remains unverifiable rather than unsupported.

An abstract-only check is classifiable only when the abstract directly contains all needed evidence and all material qualifiers; otherwise, label the citation or claim unverifiable pending authoritative full text.

Audit coverage is claim adjudication coverage: it reports how much of the eligible claim population can be classified, including uncited eligible claims that contribute `0`; it is not a direct measure of source access. For corpus coverage, an expected source is a distinct source record required by the selected audit scope. An analyzed source is an expected source whose authoritative content was inspected deeply enough to classify every in-scope use that depends on it. A resolved identifier or successful extraction does not by itself make a source analyzed. If the applicable denominator is zero, report the metric as unavailable rather than dividing by zero.

## Diagnostics and interpretation constraints

Diagnostic counts remain separate from recall, precision, audit coverage, and corpus coverage. Report potentially missing citations, in-text/reference mismatches, unused references when in scope, style issues, ambiguous placement, quotation or locator problems, unresolved mappings, and unavailable evidence as separate counts. Do not invent composite scores, F1 scores, pass/fail thresholds, probabilities, or qualitative score bands.

- Source existence and thematic relevance do not establish support.
- Support concerns attribution fit, not universal truth or proof of a field's consensus.
- Full support requires all material qualifiers.
- Identify secondary reporting when prose implies direct primary evidence.
- Keep formatting, reference resolution, substantive support, and evidence availability separate.
- Check decisive wording, numbers, methods, results, tables, figures, and locators in the authoritative source document.
- Do not infer support from bibliography metadata, plans, isolated converted fragments, or model memory.
- Include locators in audit records; add them to target prose only when correcting it is authorized and the citation style requires them.
