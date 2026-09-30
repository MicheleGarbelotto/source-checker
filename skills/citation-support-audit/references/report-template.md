# Citation Support Audit report template

Adapt detail to the requested scope. Keep corpus coverage, evidence availability, substantive support, and citation mechanics separate. Give every finding a target locator and, where evidence is available, an authoritative source locator.

## 1. Scope and corpus coverage

Record the target path and selected sections, citation scope, identifiable style, claim-eligibility rule, manifest path and generation time, and whether the result scope is **complete** or **partial**. If partial, name the verified subset without presenting it as the whole scope.

Report these source counts explicitly:

| Source state | Count | Meaning |
|---|---:|---|
| Expected sources | Number | Distinct source records required by the selected scope |
| Resolved sources | Number | Expected records mapped to a source identity |
| Extracted sources | Number | Resolved sources with usable extracted content, with extraction quality recorded separately |
| Analyzed sources | Number | Expected sources inspected deeply enough for every dependent in-scope use |
| Missing sources | Number | Expected sources for which no authoritative content is available |

Also report eligible claims, classifiable eligible claims, all citations evaluated, classifiable citations, unresolved or unusable sources, and cache and extraction statuses. State why each unavailable source affects audit or corpus coverage; do not infer a substantive verdict from its absence.

## 2. Method and extraction quality

State the claim-segmentation rule, citation-to-claim association rule, source-mapping route, source-reading depth, abstract-only checks, extraction method and quality, treatment of unavailable sources, and whether methodological references were refreshed. Distinguish authoritative documents from converted or extracted representations and identify any locator changes introduced by conversion.

## 3. Quantitative scorecard

Show the numerator and denominator for every percentage. Report whole-scope citation recall only when every eligible claim is classifiable, and report whole-scope citation precision only when every in-scope claim-citation association is classifiable. Otherwise report each applicable verified-subset metric whenever at least one eligible claim is classifiable.

| Measure | Numerator / denominator | Result | Meaning |
|---|---|---|---|
| ALCE-style whole-scope citation recall | Fully supported eligible claims / all eligible claims | Percentage or unavailable | Completeness of full claim support across the complete scope |
| ALCE-style whole-scope citation precision | Supporting citations / all citations evaluated | Percentage or unavailable | Support contributed by attached citations across the complete scope |
| ALCE-style verified-subset citation recall | Fully supported classifiable claims / classifiable eligible claims | Percentage or unavailable | Full claim support among claims that can be classified |
| ALCE-style verified-subset citation precision | Supporting classifiable citations / classifiable citations | Percentage or unavailable | Support contributed by citations that can be classified |
| Audit coverage | Classifiable eligible claims / all eligible claims | Percentage or unavailable | Claim-adjudication coverage, not support adequacy or source availability |
| Corpus coverage | Analyzed expected sources / all expected sources | Percentage or unavailable | Depth of source-corpus completion, not support adequacy |

List support-label counts and diagnostic counts separately. Do not add an overall adequacy score, composite score, or interpretive band.

## 4. Reference integrity and citation mechanics

Report unresolved identifiers, in-text/reference mismatches, unused references when in scope, ambiguous placement, style deviations, quotation issues, and locator problems separately from support verdicts. For each problem, give its target locator, affected citation or reference, status, and recommended action.

## 5. Claim-source matrix

| Claim ID | Target locator | Atomic claim | Citation(s) | Joint support | Individual source verdicts | Recommended action |
|---|---|---|---|---|---|---|
| C01 | Section/paragraph or page | Claim text | Source identifiers | Fully supported / not fully supported / unverifiable | Label for each source | Keep / narrow / split / correct |

Keep unresolved mappings and unavailable evidence explicit rather than forcing substantive labels.

## 6. Passage-level evidence

For each claim requiring discussion, provide:

- Target locator and exact claim.
- Citation position and defensible claim scope.
- Source title and stable identifier, with an authoritative source locator.
- Individual support label and joint cited-set support.
- A short evidence excerpt sufficient to demonstrate the verdict, with surrounding context summarized.
- Assessment of fit, missing qualifiers, design or population limits, and primary versus secondary reporting.
- Recommended action: keep, narrow, split, move a citation, correct a quotation or locator, or mark explicit synthesis. Source replacement requires verified evidence and authorized discovery.

Where evidence is unavailable, state the verification limitation and its effect on coverage rather than inventing a passage or calling the associated claim unsupported. Avoid unnecessary reproduction of copyrighted text.

## 7. Potentially missing citations

List eligible claims that lack an attached citation or whose defensible citation scope leaves material content uncited. Give the target locator, atomic claim, reason support is expected, and recommended action. Keep this diagnostic distinct from whether any existing citation supports a neighboring claim.

## 8. Inaccessible/ambiguous sources needed for fuller coverage

List each missing, inaccessible, unusable, or ambiguously mapped source needed to increase coverage. Include the affected claim IDs, current source or mapping status, attempted route, and next evidence needed. Every source limitation must state its effect on audit coverage or corpus coverage without classifying unavailable evidence as unsupported.

## 9. Limitations and conclusion

Identify inaccessible or poor-quality sources, abstract-only or secondary checks, corpus boundaries, sources not searched, and uncertainty in segmentation or citation scope. Explain the effect of each limitation on the result. Summarize whole-scope results only for a complete classifiable scope; otherwise conclude from the explicitly labelled verified subset and coverage measures. Percentages summarize the audited text and do not replace passage-level scholarly judgment.
