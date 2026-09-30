# Public skill-activation evaluation results

This is a controller-attested record, not independently authenticated evidence.
The controller reports that each exact prompt was sent in a fresh evaluator
context with both skills discoverable. Host logs and session IDs are intentionally
absent from this public artifact. Therefore, this artifact cannot independently
prove fresh-context isolation, the model/runtime version, or the exact
installed-skill bytes used during evaluation.

What is directly verifiable here is limited to the exact prompts, preserved
public responses and self-reported decisions, the declared scenario contract,
and the internal consistency tests applied to those public fields.

Here, `non-trigger` means that the skill naming the scenario suite must not
activate. A different skill may still be the correct route when the prompt
explicitly requests that different workflow.

## citation-support-audit / direct

- Prompt: `Use Citation Support Audit to verify whether the claims in this paper are supported by the supplied sources.`
- Expected activation: `citation-support-audit`
- Observed activation: `citation-support-audit`
- Verdict: PASS
- Rationale: The evaluator selected the explicitly named citation-support workflow and requested the missing paper and supplied sources needed to perform it; it did not substitute the textual-similarity workflow.

### Public response

```text
Please attach:

- The paper to audit, preferably as PDF or DOCX.
- The supplied source corpus, such as PDFs, full texts, or accessible links.

If the paper does not clearly map claims or citations to individual sources, please also provide that mapping.

PUBLIC_RECORD
selected_skill: citation-support-audit
missing_inputs_requested: paper, supplied sources, claim-to-source mapping if unclear
```

## citation-support-audit / indirect

- Prompt: `Check whether each cited source actually supports the nearby claim and flag claims that need citations.`
- Expected activation: `citation-support-audit`
- Observed activation: `citation-support-audit`
- Verdict: PASS
- Rationale: The evaluator recognized claim-source support and missing-citation review as citation-support work, requested the target and accessible sources, and did not select plagiarism-audit.

### Public response

```text
Please provide:

- The document or passages to audit, including in-text citations.
- The cited sources themselves, or a bibliography with accessible links/DOIs.

I’ll assess claim-by-claim support, flag overstatements or mismatches, and identify uncited claims.

PUBLIC_RECORD
selected_skill: citation-support-audit
missing_inputs_requested: cited text or document, cited sources or accessible bibliography
```

## citation-support-audit / incomplete

- Prompt: `Check my citations.`
- Expected activation: `citation-support-audit`
- Observed activation: `citation-support-audit`
- Verdict: PASS
- Rationale: The evaluator routed the underspecified citation request to citation-support-audit and requested the absent document and source material rather than substituting plagiarism-audit.

### Public response

```text
Please attach or paste the text/document and say what you want checked: reference formatting, citation accuracy, or whether each source supports the cited claim. For claim-support checking, also provide the relevant source PDFs, links, or Zotero items.

PUBLIC_RECORD
selected_skill: citation-support-audit
missing_inputs_requested: document or text, type of citation check, source materials for claim-support checking
```

## citation-support-audit / non-trigger

- Prompt: `Copyedit this paper for grammar without checking its sources or citations.`
- Expected activation: `none`
- Observed activation: `none`
- Verdict: PASS
- Rationale: The evaluator honored the explicit exclusion of source and citation checking. It selected a general writing workflow, preserved below, so no audit skill activated and the normalized audit activation is none.

### Public response

```text
Please paste or attach the paper. I’ll copyedit its grammar and clarity while leaving sources and citations unchecked.

PUBLIC_RECORD
selected_skill: academic-writing-skills
missing_inputs_requested: paper text or file
```

## citation-support-audit / edge

- Prompt: `Check citation support using the readable sources, but one cited source is unavailable.`
- Expected activation: `citation-support-audit`
- Observed activation: `citation-support-audit`
- Verdict: PASS
- Rationale: The evaluator selected citation-support-audit, requested the target and readable sources, and correctly proposed recording claims dependent on the absent source as unverifiable rather than unsupported.

### Public response

```text
I can perform the citation-support audit, but no document or source corpus is attached. Please provide:

- The text or document to audit.
- The readable cited sources.
- The full citation or bibliographic details of the unavailable source.

I’ll assess claims supported by the readable sources and mark claims relying on the unavailable source as unverifiable—not unsupported—unless another supplied source independently supports them.

PUBLIC_RECORD
selected_skill: citation-support-audit
missing_inputs_requested: text or document to audit, readable cited sources, bibliographic details of unavailable source
```

## plagiarism-audit / direct

- Prompt: `Use Plagiarism Audit to compare this document with the supplied source corpus.`
- Expected activation: `plagiarism-audit`
- Observed activation: `plagiarism-audit`
- Verdict: PASS
- Rationale: The evaluator selected the explicitly named plagiarism-audit workflow, requested the missing document and corpus, and kept the result bounded to observed similarity rather than a plagiarism verdict.

### Public response

```text
Please attach the document to check and the source corpus to compare it against. I’ll then run a read-only plagiarism audit and report observed textual similarities, corpus coverage, and limitations—not a definitive plagiarism verdict.

PUBLIC_RECORD
selected_skill: plagiarism-audit
missing_inputs_requested: document, source corpus
```

## plagiarism-audit / indirect

- Prompt: `Find close paraphrases, patchwriting, and unattributed textual overlap against these source files.`
- Expected activation: `plagiarism-audit`
- Observed activation: `plagiarism-audit`
- Verdict: PASS
- Rationale: The evaluator recognized close paraphrase, patchwriting, and overlap detection as source-bounded textual-similarity work and requested only the absent target and comparison sources.

### Public response

```text
Please attach:

- The document you want checked.
- The source files to compare it against.

I’ll then identify close paraphrases, patchwriting, and unattributed textual overlap, with exact locations in both the document and sources.

PUBLIC_RECORD
selected_skill: plagiarism-audit
missing_inputs_requested: document to examine, source files to compare against
```

## plagiarism-audit / incomplete

- Prompt: `Check this for plagiarism.`
- Expected activation: `plagiarism-audit`
- Observed activation: `plagiarism-audit`
- Verdict: PASS
- Rationale: The evaluator routed the incomplete plagiarism request to plagiarism-audit and requested the missing target and comparison corpus without substituting citation-support-audit.

### Public response

```text
Please upload or paste the document you want checked and specify the comparison corpus—such as cited sources, provided files, or the public web.

PUBLIC_RECORD
selected_skill: plagiarism-audit
missing_inputs_requested: document to check, comparison corpus or scope
```

## plagiarism-audit / non-trigger

- Prompt: `Verify whether the cited studies support the paper's causal claims; do not assess textual similarity.`
- Expected activation: `citation-support-audit`
- Observed activation: `citation-support-audit`
- Verdict: PASS
- Rationale: The evaluator did not activate plagiarism-audit and followed the prompt's explicit claim-source-support request. Under the corrected non-trigger definition, citation-support-audit is the intended route rather than a forbidden substitution.

### Public response

```text
I’ll assess citation support for the paper’s causal claims, not textual similarity. Please provide:

- The paper or the relevant passages containing the causal claims and citations.
- The cited studies, or accessible links/DOIs to them.

I’ll report each claim, whether the cited evidence supports a causal interpretation, key limitations, and any needed wording correction.

PUBLIC_RECORD
selected_skill: citation-support-audit
missing_inputs_requested: paper or relevant cited passages, cited studies or accessible links/DOIs
```

## plagiarism-audit / edge

- Prompt: `Report observed textual overlap against the three readable sources while a fourth expected source is unavailable.`
- Expected activation: `plagiarism-audit`
- Observed activation: `plagiarism-audit`
- Verdict: PASS
- Rationale: The evaluator selected plagiarism-audit, requested the target and readable subset, and proposed reporting partial observed overlap with an explicit coverage limitation for the unavailable source.

### Public response

```text
I can report partial, observed textual overlap without treating it as a plagiarism verdict. Please provide:

- The document to assess.
- The three readable source texts or files.
- The citation or identifier of the unavailable fourth expected source, so I can record the coverage limitation.

PUBLIC_RECORD
selected_skill: plagiarism-audit
missing_inputs_requested: target document, three readable sources, identifier of unavailable fourth source
```
