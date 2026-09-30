# Revised-skill black-box forward-test results

## Capture and evaluation method

Five independent forward-test agents were each given one scenario from
`tests/behavior/citation-support-audit/scenarios.yaml` and the revised citation
support audit skill. This report evaluates only the agents' observable replies
against the scenario assertions. It does not use the baseline outputs as an
answer key.

The paths and documents in the scenarios are synthetic fixtures. No target or
source file contents were exposed to the agents. Consequently, statements about
what an audit *would* do are evidence of intake, routing, and reporting behavior
only; they are not evidence that a substantive file inspection or citation audit
was completed.

## Scenario 1: `underspecified-request`

### Exact prompt

```text
Use the skill to check my paper.
```

### Exact verbatim output from `forward_underspecified`

```text
Please provide:

1. The paper to audit.
2. The source corpus or its location/provider—for example, a Zotero library, PDFs folder, or attached source files.

I’ll then perform the complete citation audit without editing the paper.
```

### Questions or requests for information

1. `The paper to audit.`
2. `The source corpus or its location/provider—for example, a Zotero library, PDFs folder, or attached source files.`

### Assertion results

| Assertion | Result | Evidence |
|---|---|---|
| The agent identifies that the target is missing. | PASS | It requests “The paper to audit.” |
| The agent identifies that the source corpus is missing. | PASS | It requests “The source corpus or its location/provider”. |
| The result records every question the agent asks. | PASS | Both requests are reproduced above; there are no other interrogative or information-seeking requests in the output. |

Scenario total: **3/3 PASS**.

## Scenario 2: `docx-plus-pdf-folder`

### Exact prompt

```text
Check C:\study\draft.docx. The source corpus is the PDFs in C:\study\sources\; the DOCX contains author-year citations and a reference list.
```

### Exact verbatim output from `forward_docx_pdf`

```text
I would run a complete, read-only citation audit of `C:\study\draft.docx` against the canonical PDFs under `C:\study\sources\`, including:

- Matching author–year citations to reference-list entries and then to the PDFs, preserving any genuinely ambiguous matches.
- Checking in-text/reference-list consistency, citation placement, unused references, quotations, and potentially missing citations.
- Splitting the text into atomic, citation-worthy claims and assessing each cited set jointly and source by source.
- Classifying support as fully supported, partially supported, unsupported, contradictory, unresolved, or unverifiable.
- Verifying decisive evidence in the PDFs, citing DOCX paragraph locators and PDF page/block locators.
- Reporting ALCE-style recall and precision with explicit numerators and denominators, alongside audit and corpus coverage. If any evidence remains unclassifiable, scores would be labelled as verified-subset results rather than whole-document results.

The deliverable would include a claim–source matrix, passage-level evidence, reference-mechanics findings, missing-citation candidates, mapping or extraction limitations, and targeted correction recommendations. The DOCX and source PDFs would remain unchanged.
```

### Questions or requests for information

None.

### Assertion results

| Assertion | Result | Evidence |
|---|---|---|
| The agent accepts the DOCX target and PDF folder as supported inputs. | PASS | It says it “would run a complete, read-only citation audit” of the named DOCX against the named PDF folder, without requesting conversion or replacement inputs. |
| The agent attempts automatic citation-to-source mapping. | PASS | It specifies “Matching author–year citations to reference-list entries and then to the PDFs”. This is an intended workflow action, not a completed mapping. |
| The agent does not ask the user to create a mapping file or map. | PASS | It asks no question and makes no mapping-file request. |

Scenario total: **3/3 PASS**.

## Scenario 3: `incomplete-corpus`

### Exact prompt

```text
Audit C:\study\paper.md against C:\study\sources\. Four cited sources are expected: Alpha 2020, Bravo 2021, Chen 2022, and Diaz 2023. Alpha, Bravo, and Chen are readable PDFs; Diaz 2023 is absent.
```

### Exact verbatim output from `forward_incomplete`

```text
I’ll proceed with a partial-corpus audit:

- Expected sources: 4
- Readable sources: Alpha (2020), Bravo (2021), Chen (2022)
- Missing source: Diaz (2023)

I’ll assess citation integrity, placement, missing citations, and substantive support using the three readable PDFs. Claims dependent on Diaz (2023) will be marked **unverifiable**, not unsupported. Whole-scope support metrics will not be reported; any quantitative results will be explicitly limited to the verified subset, with corpus coverage reported separately. No files will be edited.
```

### Questions or requests for information

None.

### Assertion results

| Assertion | Result | Evidence |
|---|---|---|
| The agent continues the audit with the three accessible sources. | PASS | It says “I’ll proceed with a partial-corpus audit” and will assess using the three readable PDFs. This records intended continuation, not completed inspection. |
| The agent records Diaz 2023 as missing or unverifiable. | PASS | It lists “Missing source: Diaz (2023)” and says dependent claims will be “unverifiable”. |
| The agent does not label Diaz 2023 unsupported. | PASS | It explicitly says “**unverifiable**, not unsupported.” |

Scenario total: **3/3 PASS**.

## Scenario 4: `ambiguous-mapping`

### Exact prompt

```text
Audit C:\study\paper.md against C:\study\sources\. Every citation maps uniquely except Garcia (2021), which could plausibly map to either Garcia_2021_A.pdf or Garcia_2021_B.pdf. Both PDFs are readable.
```

### Exact verbatim output from `forward_ambiguous`

```text
I can proceed with all uniquely mapped citations. Which PDF is the intended source for Garcia (2021): `Garcia_2021_A.pdf` or `Garcia_2021_B.pdf`?

Until clarified, I will retain Garcia (2021) as an ambiguous mapping rather than choose one. Its dependent claims and citation will remain unresolved and be excluded from substantive classification; any interim scores will be reported only for the verified subset, with explicit coverage denominators.
```

### Questions or requests for information

1. `Which PDF is the intended source for Garcia (2021): Garcia_2021_A.pdf or Garcia_2021_B.pdf?`

### Assertion results

| Assertion | Result | Evidence |
|---|---|---|
| The agent asks the user to resolve only the Garcia (2021) pair. | PASS | Its sole question presents only the two Garcia candidates. |
| The agent does not silently select either Garcia PDF. | PASS | It says it will retain the ambiguity “rather than choose one.” |
| The agent does not request a complete user-created mapping. | PASS | It says it can proceed with uniquely mapped citations and asks only about Garcia (2021). |

Scenario total: **3/3 PASS**.

## Scenario 5: `default-scope`

### Exact prompt

```text
Check the citations in C:\study\paper.md against the readable source corpus in C:\study\sources\.
```

### Exact verbatim output from `forward_default`

```text
# Citation support audit

**Target:** `C:\study\paper.md`  
**Source corpus:** `C:\study\sources\`  
**Scope:** Complete, read-only audit of reference integrity, citation placement, potentially missing citations, and substantive claim support.  
**Edits made:** None.

Because the synthetic fixture description does not expose the document text, source passages, or audit counts, substantive verdicts and numerical results cannot be truthfully populated here. A completed audit would report them in the following form.

## 1. Scope and corpus coverage

The report identifies:

- Citation style detected in the target.
- Rule used to split the text into atomic, independently verifiable claims while retaining material qualifiers.
- Expected, resolved, extracted, analyzed, and missing source counts.
- Eligible and classifiable claim counts.
- Evaluated and classifiable citation counts.
- Unresolved mappings, unusable sources, extraction status, and text-quality limitations.
- Whether the result covers the complete document or only a verified subset.

Source availability, citation-to-source resolution, extraction quality, and substantive support are reported separately. A source’s presence in the corpus or successful extraction does not establish that it supports a claim.

## 2. Method and extraction quality

- Markdown claims are located by heading and source line range.
- Citations are associated only with the defensible claim span supported by their placement.
- Citation identifiers and reference-list metadata are mapped to corpus documents without assuming that similar filenames or topics identify the correct source.
- Decisive claims are checked against authoritative source passages, including relevant population, design, measures, results, and qualifiers.
- Each cited set is assessed jointly, followed by the contribution of each individual source.
- Unavailable or unreliable evidence is marked **Unverifiable**, not unsupported.
- Ambiguous or unresolved mappings remain resolution findings and do not receive substantive support verdicts.
- Extraction method, conversions, omissions, and locator limitations are disclosed.

## 3. Quantitative scorecard

Every percentage is accompanied by its numerator and denominator. Values are reported only after claim-level inspection.

| Measure | Calculation | Reporting rule |
|---|---|---|
| ALCE-style whole-scope citation recall | Fully supported eligible claims / all eligible claims | Report only if every relevant claim is classifiable |
| ALCE-style whole-scope citation precision | Supporting citations / all citations evaluated | Report only if every relevant citation is classifiable |
| ALCE-style verified-subset citation recall | Fully supported classifiable claims / classifiable eligible claims | Report when at least one eligible claim is classifiable but the full scope is incomplete |
| ALCE-style verified-subset citation precision | Supporting classifiable citations / classifiable citations | Report for the classifiable subset |
| Audit coverage | Classifiable eligible claims / all eligible claims | Measures evidence availability, not support quality |
| Corpus coverage | Analyzed expected sources / all expected sources | Measures depth of corpus completion, not support quality |

Support-label counts and mechanics diagnostics are listed separately. No composite score, F1 score, pass/fail threshold, or qualitative score band is assigned.

## 4. Reference integrity and citation mechanics

The completed report lists each problem separately, with its target line range, affected citation or reference, status, and recommended correction:

- In-text citations lacking matching reference-list entries.
- Reference-list entries lacking in-text use, when within scope.
- Unresolved or ambiguous citation-to-source mappings.
- Ambiguous citation placement or overbroad claim scope.
- Citation-style deviations.
- Quotation inaccuracies.
- Missing, invalid, or inappropriate locators.

These mechanics findings are not treated as substantive support verdicts.

## 5. Claim–source matrix

| Claim ID | Target locator | Atomic claim | Citation(s) | Joint support | Individual source verdicts | Recommended action |
|---|---|---|---|---|---|---|
| Assigned during audit | Heading and Markdown line range | Exact audited claim | Citation identifier(s) | Full / not full / unverifiable | Fully supports / partially supports / does not support / contradicts / unverifiable; or unresolved mapping | Keep / narrow / split / correct / move citation / mark synthesis |

Material qualifiers are preserved. A partially supported compound claim is not counted as fully supported merely because one clause is substantiated.

## 6. Passage-level evidence

For every claim requiring discussion, the report provides:

- Exact claim and target line range.
- Citation position and defensible scope.
- Source title and stable identifier.
- Authoritative source locator.
- A short evidence excerpt, with surrounding context summarized.
- Joint cited-set assessment.
- Individual source label.
- Any population, task, design, measure, causal-language, or primary-versus-secondary-reporting mismatch.
- Recommended action.

The substantive labels are:

- **Fully supports**
- **Partially supports**
- **Does not support**
- **Contradicts**
- **Unverifiable**

An unresolved citation-to-source mapping is reported separately as **Unresolved** rather than forced into one of these evidence labels.

## 7. Potentially missing citations

The audit separately identifies citation-worthy claims that:

- Have no attached citation.
- Contain material uncited content despite a nearby citation.
- Extend beyond the defensible scope of the attached citation.

Each record includes the target locator, atomic claim, reason evidence is required, and recommended action. No replacement source is proposed unless it has been verified within the authorized corpus or separate source discovery is authorized.

## 8. Inaccessible or ambiguous sources

For every missing, inaccessible, unusable, or ambiguously mapped source, the report records:

- Affected claim IDs.
- Current mapping and extraction status.
- Attempted access route.
- Evidence required to resolve the item.
- Effect on audit coverage and corpus coverage.

Unavailable evidence reduces coverage; it is not evidence that a claim lacks support.

## 9. Conclusion and limitations

The conclusion distinguishes:

- Citation mechanics and reference integrity.
- Citation-to-source resolution.
- Evidence availability and extraction quality.
- Substantive claim support.
- Potentially missing citations.

Whole-scope conclusions are made only if every relevant claim and citation is classifiable. Otherwise, conclusions are explicitly limited to the verified subset, with coverage reported separately. The audit assesses whether the supplied sources substantiate the document’s claims; it is not a plagiarism review, similarity score, misconduct determination, or proof that a claim is universally true.
```

### Questions or requests for information

None.

### Assertion results

| Assertion | Result | Evidence |
|---|---|---|
| The audit covers substantive claim-source support. | PASS | The scope names “substantive claim support”; sections 5 and 6 specify joint and source-level assessment. The output correctly does not pretend the synthetic files were inspected. |
| The audit checks potentially missing citations. | PASS | The scope includes potentially missing citations and section 7 defines the check. |
| The audit checks reference integrity. | PASS | The scope includes reference integrity and section 4 enumerates integrity findings. |
| The audit checks citation placement and scope. | PASS | Section 2 limits citations to defensible claim spans; section 4 lists ambiguous placement and overbroad scope. |
| The audit verifies direct quotations. | PASS | Section 4 lists quotation inaccuracies, and section 6 requires authoritative locators and evidence excerpts. This is specified behavior, not a completed quotation check. |
| The audit checks style when it is determinable. | PASS | Section 1 detects citation style and section 4 lists citation-style deviations. |
| The audit reports citation metrics. | PASS | Section 3 gives recall and precision formulas and reporting conditions while truthfully withholding unavailable values. |
| The audit reports corpus and audit coverage. | PASS | Section 3 defines both audit coverage and corpus coverage; section 1 requires their component counts. |

Scenario total: **8/8 PASS**.

## Overall result

| Scenario | Passed | Failed | Total |
|---|---:|---:|---:|
| `underspecified-request` | 3 | 0 | 3 |
| `docx-plus-pdf-folder` | 3 | 0 | 3 |
| `incomplete-corpus` | 3 | 0 | 3 |
| `ambiguous-mapping` | 3 | 0 | 3 |
| `default-scope` | 8 | 0 | 8 |
| **Total** | **20** | **0** | **20** |

Acceptance result: **PASS — all 20 observable assertions passed.**

## Limitations

- These are black-box language-behavior tests over scenario descriptions, not
  end-to-end audits of actual DOCX, Markdown, or PDF files.
- The fixture paths were not resolved and file contents were unavailable. Future-
  tense descriptions such as “would run” or “I’ll assess” therefore demonstrate
  intended routing only, not completed extraction, mapping, evidence verification,
  or metric computation.
- No numerical result, substantive support verdict, locator fidelity, extraction
  quality, or source-content accuracy was independently verified by these tests.
- PASS means the agent reply exhibited each scenario's required observable
  behavior. It does not establish that all runtime branches or source formats work
  end to end.
