# Plagiarism Audit 0.1.0 release smoke test

This record uses only generated or repository-owned synthetic fixtures. The
target is `tests/fixtures/documents/release-smoke-target.html`. The release test
generates a readable one-page PDF and declares it together with a deliberately
absent `missing-source.pdf` in a temporary BibTeX corpus.

## Corpus and extraction observation

- Target extraction: local static HTML, one analyzable block, eight analyzable
  target words.
- Readable source: generated PDF physical page 1, block 1, beginning `First page
  block one.` and containing enough neutral text to pass the extraction-quality
  gate.
- Unavailable source: `missing-source.pdf` (`missing`).
- Corpus coverage: 1 / 2 (50.00%); result scope: partial.

## Quantitative output

| Metric | Result | Scope |
| --- | ---: | --- |
| Observed overall similarity | 50.00% (4 / 8 target words) | Partial; within the analyzed corpus |
| Observed per-source similarity: `readable.pdf` | 50.00% (4 / 8 target words) | Partial; analyzed source only |
| Corpus coverage | 1 / 2 (50.00%) | One expected source unavailable |

The verified parallel is the four-word target span “First page block one” and
the same PDF span at physical page 1, block 1. Raw and adjusted results are both
50.00% because no exclusion was applied. The unavailable source is listed but
no unseen-source similarity is estimated.

## Non-verdict conclusion

This source-bounded similarity result does not determine plagiarism or misconduct,
intent, authorship, legal liability, or an institutional finding.
Human review must interpret the verified passage and its attribution context.
