# Independent review record and controller disposition

The four fenced blocks below preserve the reviewers' final user-visible outputs, with only host-specific absolute link targets replaced by repository-relative links. They describe what each reviewer saw at review time. The disposition section is a later controller assessment against the revised implementation; it must not be read as a claim that a reviewer inspected, approved, or re-reviewed a later change.

## Provenance correction

The accepted-set manifest committed in `a483b5f` separately verified outer envelope hashes and a current skill-tree hash, but it failed to cross-check envelope-embedded skill hashes after older workspaces had been copied and replaced. That accepted set is superseded and is not relied on by the definitive evidence. The replacement set was rebuilt from scratch and cross-validates outer envelopes/artifacts/trees, every embedded skill entry against its copied file, and every embedded/copied skill tree against the current repository skill. This correction is a controller provenance finding; it does not alter or retroactively extend any reviewer conclusion below.

## English review

~~~text
No blocking issues found. Concrete findings:

1. **Important — analyzed vs. analyzable**
   - Locations: `references/report-template.md:44`; `references/metrics-and-rules.md:67`
   - Wording: “If at least one expected source is analyzable…” / “When at least one source is analyzable…”
   - Rationale: *Analyzable* means capable of being analyzed, whereas the quantitative result requires a source actually to have been compared. An agent could generate results prematurely.
   - Replacement: “If at least one expected source has been analyzed…” and “When at least one source has been analyzed…”. Likewise replace “zero analyzable sources” with “zero analyzed sources” in these two passages.

2. **Important — contradictory `Observed` labeling**
   - Locations: `references/report-template.md:5,50`
   - Wording: “For a partial corpus, prefix each metric label with `Observed`” versus the unconditional headers “Observed corpus coverage,” “Observed raw overall similarity,” and “Observed adjusted overall similarity.”
   - Rationale: The prose reserves `Observed` for partial-corpus labels, but the shared table applies it to complete audits as well.
   - Replacement: Make the headers conditional, for example: `[Observed, if Partial] corpus coverage`, `[Observed, if Partial] raw overall similarity`, and `[Observed, if Partial] adjusted overall similarity`.

3. **Important — inconsistent category names**
   - Locations: `references/metrics-and-rules.md:79-80`; `references/report-template.md:62-63`; `references/methodology-and-attribution.md:11`
   - Wording varies among “Related Meaning / Paraphrased Content,” “Paraphrased Content / Related Meaning,” “Related Meaning,” “Cross-language / Translated Match,” and “Cross-language.”
   - Rationale: An agent could treat abbreviated or reversed names as different reporting categories.
   - Replacement: Use the canonical labels from the metrics reference everywhere: `Related Meaning / Paraphrased Content` and `Cross-language / Translated Match`, including the scorecard rows.

4. **Minor — comma splice and unclear certification subject**
   - Location: `SKILL.md:12`
   - Wording: “it is not equivalent to or certified by any cited product, it is not affiliated with any cited product or organization, and it is not a plagiarism or misconduct verdict.”
   - Rationale: This joins independent clauses with commas, and a product is not naturally the entity that certifies an implementation.
   - Replacement: “It is not equivalent to any cited product, is not certified or endorsed by any cited vendor or organization, and does not render a plagiarism or misconduct verdict.”

5. **Minor — inconsistent route terminology**
   - Location: `SKILL.md:22`
   - Wording: “all supported corpus providers”
   - Rationale: `source-corpus.md` defines corpus *routes*, several of which are not providers.
   - Replacement: “Accept all supported document formats and corpus routes documented in [source-corpus.md](references/source-corpus.md).”

6. **Minor — unidiomatic instruction**
   - Location: `references/report-template.md:44`
   - Wording: “every meaning says `within the analyzed corpus`”
   - Rationale: *Meaning* does not identify a report field clearly.
   - Replacement: “every interpretation states `within the analyzed corpus`.”

7. **Minor — overloaded compound**
   - Location: `references/metrics-and-rules.md:17`
   - Wording: “a verified target-source relationship-level unit”
   - Rationale: The stacked modifiers are difficult to parse in a key definition.
   - Replacement: “a verified unit defined at the level of a target–source relationship.”

8. **Minor — faulty coordination**
   - Location: `references/metrics-and-rules.md:101`
   - Wording: “These labels are not probabilities or plagiarism or misconduct-risk estimates”
   - Rationale: The construction makes *plagiarism* grammatically parallel to *probabilities* and *estimates*.
   - Replacement: “These labels are neither probabilities of plagiarism nor estimates of misconduct risk, and they are not decision thresholds.”

9. **Minor — vague expression**
   - Location: `references/methodology-and-attribution.md:17`
   - Wording: “for verbatim text, quotation treatment”
   - Rationale: *Quotation treatment* is abstract and may not tell an agent what visible signal is meant.
   - Replacement: “copied wording requires appropriate credit and verbatim text must also be marked as a quotation.”

No concrete English issue was found in `references/source-corpus.md`. No files were edited.

~~~

## Methodology review

~~~text
Reviewed only `SKILL.md` and the four Markdown references. No files were edited. Defects found.

## Blocking defects

1. **Semantic and cross-language passages have no coherent word-count rule.**

   - `references/metrics-and-rules.md:13-15` defines matched words as positions in a “verified textual-overlap match.”
   - `:29-30` uses matched words for per-source and category percentages.
   - `:79-82` also requires word coverage for “Related Meaning” and “Cross-language / Translated Match,” which may have little or no lexical overlap.

   It is therefore unclear whether semantic/translated passage spans enter overall similarity. Including them makes the measure broader than textual similarity; excluding them leaves their required word numerators undefined.

   **Minimal correction:** explicitly define eligible position sets by category. Prefer limiting overall/per-source textual similarity to lexical matches and reporting semantic/cross-language evidence separately as passage/span coverage. Otherwise rename and justify the broader construct.

2. **A final or “Complete” score can exclude unresolved candidates without showing verification incompleteness.**

   - `metrics-and-rules.md:19` excludes partial/unverified candidates from every numerator.
   - `:67-71` requires a percentage once a source is analyzable and labels it `Complete` solely from corpus coverage.
   - `report-template.md:112-118` permits unresolved candidates in the final report.

   Thus a score can be zero or low while unresolved candidates could materially increase it.

   **Minimal correction:** require every in-scope candidate above declared retrieval thresholds to be resolved before a final score is issued. Otherwise label the result `Provisional confirmed-overlap minimum`, disclose candidate-review coverage, and do not label the similarity result `Complete`.

## Important defects

3. **Per-source and per-category deduplication is unspecified.**

   `metrics-and-rules.md:28-35` explicitly says `unique` only for the overall numerator. Repeated evidence relationships for the same source/category could therefore count a target position more than once.

   **Minimal correction:** define per-source similarity as the unique union of target positions across all retained relationships for that source, and category coverage as the unique union across all retained relationships in that category.

4. **The evidence grouping key can merge matches that point to unrelated source locations.**

   `metrics-and-rules.md:17` groups by source record, category, attribution group, and target block, but omits source artifact/version and source span. Contiguous target spans matching distant passages—or different attachments of one record—can become one passage despite requiring different authoritative locators.

   **Minimal correction:** include canonical source artifact/version and source block/span in the grouping logic; merge only when both target and source spans are coherent and contiguous/overlapping.

5. **Passage counts and block counts are conflated.**

   - `metrics-and-rules.md:17` says retained passages are the unit for both passage and block counts.
   - `report-template.md:69,74` uses one `Retained passages (blocks)` value.

   Multiple disjoint passages can occur in one target block, so these counts are not generally identical.

   **Minimal correction:** report separate `Retained passages` and `Unique target blocks` columns, with independent deduplication definitions.

6. **“Complete” corpus status does not adequately handle partial source-text extraction.**

   - `metrics-and-rules.md:21` defines analyzed source content only as compared “deeply enough.”
   - `source-corpus.md:76` says successful extraction does not establish complete corpus coverage.
   - `report-template.md:71-72` nevertheless allows `Artifact status: partial` on a `Complete` result.

   All expected records may be present while substantial portions of one or more sources remain unavailable.

   **Minimal correction:** distinguish source-set coverage from source-text coverage. Either require full usable selected-scope content for `Complete`, or report dual labels such as `Complete source set; partial source-text coverage`.

7. **Vendor review bands are applied despite explicit non-comparability.**

   - `methodology-and-attribution.md:10` states repository scores are not directly comparable with commercial results.
   - `:13,21` and `metrics-and-rules.md:99-101` apply SafeAssign’s numeric bands to repository scores.

   Reusing thresholds derived for another database and calculation system has no stated validity, especially for partial corpora or scores containing semantic/translated categories. `Low/Medium/High` also invites risk interpretation despite disclaimers.

   **Minimal correction:** do not apply vendor bands to repository scores. If mentioned, present them only as vendor documentation in an explicitly requested product comparison.

8. **Attribution labels overstate detection and have no indeterminate category or overlap rule.**

   `metrics-and-rules.md:90-95` uses “Missing Citation” and “Missing Quotations” while acknowledging detection can fail. `report-template.md:78-85` reports matched-word counts without specifying deduplication or overlap when the same target span has different source-specific attribution relationships.

   **Minimal correction:** use neutral labels such as `No associated citation detected`, add `Indeterminate/extraction-limited`, require exactly one group per relationship, and define each group’s matched words as unique target positions while disclosing cross-group overlap.

9. **The complete-result score table contradicts the labeling rule.**

   `report-template.md:5,56` says only partial metrics receive the `Observed` prefix, but `:50-52` labels all table columns `Observed`, including complete results.

   **Minimal correction:** use conditional headings or neutral headings, with `Observed` added only for partial-corpus output.

10. **“Reuse of source content” implies an unsupported direction of derivation.**

    `metrics-and-rules.md:80` defines cross-language matches as “translated or cross-language reuse of source content.” Similarity evidence cannot establish that the target reused that source rather than the reverse or both sharing another source.

    **Minimal correction:** use “cross-language correspondence consistent with translation” and explicitly leave direction and common-source explanations undetermined.

## Minor defects

11. **The zero-expected-source routing is logically inconsistent.**

    In the top-to-bottom table at `source-corpus.md:19-23`, “all expected sources analyzed” is vacuously true when both expected and analyzed counts are zero, so it can route to `complete audit` before the zero-source diagnostic. This conflicts with the zero-denominator handling in `metrics-and-rules.md`.

    **Minimal correction:** require `expected sources > 0` in the complete route, or place the zero-source diagnostic first.

12. **Coverage inventory combines non-exclusive states.**

    `report-template.md:15-19` combines “Inaccessible/unusable/unresolved expected sources” into one count. Mapping resolution, extraction usability, and analysis status are distinct; an unresolved mapping can coexist with analyzable explicit source text.

    **Minimal correction:** report separate distinct-source counts for unresolved mapping, unusable extraction, inaccessible artifact, and unanalyzed source, noting overlaps.

## Optional refinements

- At `metrics-and-rules.md:5`, replace “Properly quoted and credited” with “Text displaying quotation and citation signals”; the audit does not establish proper credit.
- At `report-template.md:107`, narrow `no action` to `no similarity-related action based on this corpus`.
- At `report-template.md:69-72`, rename `Artifact status: verified/partial` to something like `Authoritative-artifact inspection: complete/partial` so it cannot be confused with the rule that retained relationships must be verified.
~~~

## Portability review

~~~text
Independent review completed. No files were edited, and I did not inspect tests, plans, prior results, history, or other reviews.

## Defects

1. **High — Bundled entry point is not portable enough to start in the current environment**

   - Evidence: running the documented help route,
     `python ...\scripts\source_corpus.py manifest --help`,
     fails before argument parsing with `ModuleNotFoundError: No module named 'docx'`.
   - Cause: [extractors/__init__.py](../../../../skills/plagiarism-audit/scripts/source_checker/extractors/__init__.py#L7) eagerly imports all extractors; [office.py](../../../../skills/plagiarism-audit/scripts/source_checker/extractors/office.py#L10) imports `python-docx` and [html.py](../../../../skills/plagiarism-audit/scripts/source_checker/extractors/html.py#L5) imports BeautifulSoup. Thus even `--help` or a `.txt` audit needs unrelated format dependencies.
   - Documentation only says to install “runtime dependencies” without naming them or providing dependency metadata ([source-corpus.md](../../../../skills/plagiarism-audit/references/source-corpus.md#L45)).
   - Minimal correction: add an explicit dependency/bootstrap file or exact package list, and preferably lazy-import format-specific extractors so help and dependency-independent formats still work.

2. **High — A bad bibliography export or imported manifest aborts the whole run, contrary to partial-corpus continuation**

   - [cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L147) calls `load_export()` and `_load_compatible_manifest()` with no per-input exception boundary. Missing, unreadable, malformed, or wrongly encoded `.bib`, `.ris`, `.json`, or `.csv` inputs therefore terminate collection before accessible local sources are cached.
   - This conflicts directly with [SKILL.md](../../../../skills/plagiarism-audit/SKILL.md#L28) and [source-corpus.md](../../../../skills/plagiarism-audit/references/source-corpus.md#L14), which require accessible evidence to continue.
   - Minimal correction: isolate each bibliography/manifest input, retain a provider/path diagnostic row, continue collecting other sources, then let strict mode decide the final exit status after writing diagnostics.

3. **Medium — An empty corpus is reported as 100% coverage, and strict mode succeeds**

   - `_summary()` defines `expected = len(entries)` and returns `coverage_percent = 100.0` when `expected == 0` ([cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L543), [cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L552)).
   - `_has_required_gap()` sees no missing/ambiguous/unusable rows, so even `--fail-on-missing` exits successfully ([cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L556)).
   - This contradicts the zero-source diagnostic route and the rule that a zero expected-source denominator is unavailable, not 100% ([source-corpus.md](../../../../skills/plagiarism-audit/references/source-corpus.md#L23), [metrics-and-rules.md](../../../../skills/plagiarism-audit/references/metrics-and-rules.md#L63)).
   - Minimal correction: emit unavailable/null coverage plus an explicit `zero_sources` diagnostic; strict mode should fail when a supplied corpus route yields no source records.

4. **Medium — Most Zotero failure states are discarded, preventing the required attempted-route reporting**

   - The resolver produces `unavailable`, `not_found`, `attachment_unresolved`, and `error:*` states ([zotero.py](../../../../skills/plagiarism-audit/scripts/source_checker/resolvers/zotero.py#L93), [zotero.py](../../../../skills/plagiarism-audit/scripts/source_checker/resolvers/zotero.py#L167)).
   - `_apply_zotero_resolutions()` records only `ambiguous`; all other non-success states are ignored ([cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L222)).
   - The resulting manifest cannot distinguish “API unavailable,” “item not found,” and “attachment unavailable,” although the report requires current state and attempted route ([report-template.md](../../../../skills/plagiarism-audit/references/report-template.md#L122)).
   - Minimal correction: append provider-resolution provenance/conflicts for every non-`enriched` Zotero outcome.

5. **Low — Strict-mode wording does not describe actual runtime semantics**

   - [source-corpus.md](../../../../skills/plagiarism-audit/references/source-corpus.md#L59) says strict mode fails for “remaining required gaps.”
   - There is no required/optional field. Runtime fails on any counted missing, ambiguous, or unusable row; `unusable` includes `needs_review` ([cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L556), [cli.py](../../../../skills/plagiarism-audit/scripts/source_checker/cli.py#L560)).
   - Minimal correction: document the exact row-based conditions, or add explicit requiredness before retaining the current wording.

## Optional portability improvements

- State that legacy `.doc` conversion requires a discoverable `soffice` executable on `PATH`; runtime invokes the bare command ([office.py](../../../../skills/plagiarism-audit/scripts/source_checker/extractors/office.py#L163)).
- Likewise document `pdftotext` discovery and the `pypdf` fallback ([pdf.py](../../../../skills/plagiarism-audit/scripts/source_checker/extractors/pdf.py#L21)).
- Change “imports the project runtime” to “imports the bundled sibling runtime”; [source_corpus.py](../../../../skills/plagiarism-audit/scripts/source_corpus.py#L7) imports the included `source_checker` package.

## Areas with no defect found

- The stated target/source format list exactly matches `SUPPORTED_SUFFIXES`.
- Locator claims match the Markdown, plain-text, LaTeX, HTML, Word, converted-DOC, and PDF extractors.
- Mendeley is correctly limited to exports plus accessible local attachments; no private database/cloud route exists.
- Zotero live discovery is correctly described as read-only and PDF-child-only.
- Temporary DOC conversion is isolated in `TemporaryDirectory` and uses argument-list subprocess invocation.
- Cache omissions for headings and conversion notes are accurately disclosed.
- Individual local attachment extraction failures are isolated, alternate attachments are attempted, and accessible sources can continue.

~~~

## Copyright and attribution review

~~~text
Read-only review completed. I inspected only the four requested skill files, the repository `LICENSE`, and the cited official pages.

## Defect

**Low — Copyleaks terminology is attributed, but one sentence presents adapted labels as exact public labels.**

- File: `references/methodology-and-attribution.md:11`
- Quote: “Use the public labels Identical Match, Minor Changes, and Paraphrased Content / Related Meaning.”
- Evidence: Copyleaks currently displays **“Identical Matches”** and **“Paraphrased Content (Related Meaning)”**, whereas the repository uses singular **“Identical Match”** and reverses the latter label. `metrics-and-rules.md:75-84` more accurately calls these “Copyleaks-style” labels, and `report-template.md:60-63,97` also treats them as derived/adapted.
- Why it matters: Attribution is present, but “the public labels” implies exact reproduction of Copyleaks’s terminology when two labels have been normalized.
- Minimal correction: Change the sentence to: “Use repository labels adapted from Copyleaks’s publicly documented terms: Identical Match (from Identical Matches), Minor Changes, and Related Meaning / Paraphrased Content (from Paraphrased Content (Related Meaning)).”

Official evidence: [Copyleaks detection levels](https://docs.copyleaks.com/concepts/features/detection-levels).

## Optional improvement

**Currentness wording could age more cleanly.**

- Files: `references/metrics-and-rules.md:99,116`; compare `references/methodology-and-attribution.md:23` and `references/report-template.md:38`.
- Quote: “The current official SafeAssign documentation was checked on 2026-09-23.”
- Assessment: Defensible now. The access date and SafeAssign’s stated last-modified date, 2026-08-28, are independently verifiable, and methodology line 23 already requires rechecking before describing current vendor behavior. The relative word “current” will nevertheless become stale.
- Minimal improvement: Use “The official SafeAssign documentation accessed on 2026-09-23…” and retain the existing re-verification instruction.
- Official evidence: [SafeAssign Originality Report](https://help.anthology.com/blackboard/student/en/plagiarism/safeassign/safeassign-originality-report.html).

## No other defects found

- Vendor-derived terminology and formula inspiration are visibly attributed in `methodology-and-attribution.md:7-13` and reinforced in `metrics-and-rules.md:75-101`.
- Non-affiliation, non-equivalence, and non-certification language is precise in `SKILL.md:10-12`, `methodology-and-attribution.md:3,10-13`, and `metrics-and-rules.md:84`.
- Quotation/reproduction instructions are copyright-conscious: `report-template.md:3` requires only the minimum text needed, and lines 101-110 repeat that excerpts must be minimal and unnecessary copyrighted reproduction avoided.
- No language claims that vendor documentation or terminology is licensed under the repository’s MIT license. The MIT grant in `LICENSE:1-13` therefore does not create an apparent third-party licensing claim.
- The official pages support the described terminology and warnings: [iThenticate](https://guides.ithenticate.com/hc/en-us/articles/27838877807245-Overview-of-the-new-Similarity-Report-experience), [Crossref](https://www.crossref.org/documentation/similarity-check/similarity-report-understand/), [Turnitin](https://guides.turnitin.com/hc/en-us/articles/28057483210637-How-do-the-Match-Groups-work-in-the-new-Similarity-Report), and [ORI](https://ori.hhs.gov/plagiarism-text).

~~~

## Controller disposition

The rows below record controller decisions and resulting files. “Accepted with narrower correction” means the controller accepted the defect but selected a more bounded correction than the reviewer's preferred remedy. “Rejected” means the proposed change was not adopted; it does not erase the original review observation.

| Review item | Disposition | Resulting file(s) or reason |
|---|---|---|
| English 1 — analyzed vs. analyzable | Accepted | `references/metrics-and-rules.md`, `references/report-template.md`, and package tests now gate quantitative reporting on sources that have been analyzed. |
| English 2 — conditional `Observed` labels | Accepted | `references/report-template.md` now separates Partial/Observed and Complete/unprefixed scorecard rows. |
| English 3 — canonical category names | Accepted | `references/metrics-and-rules.md`, `references/report-template.md`, and `references/methodology-and-attribution.md` use `Related Meaning / Paraphrased Content` and `Cross-language / Translated Match` consistently. |
| English 4 — notice grammar/certification subject | Accepted | `SKILL.md` splits the sentence and states the non-equivalence, non-affiliation, non-certification, and non-verdict boundaries explicitly. |
| English 5 — providers vs. routes | Accepted | `SKILL.md` now says “corpus routes.” |
| English 6 — “every meaning” | Accepted | `references/report-template.md` now refers to every interpretation. |
| English 7 — overloaded relationship-level compound | Accepted | `references/metrics-and-rules.md` defines a retained passage as one verified target-passage/source-passage relationship. |
| English 8 — faulty probability/risk coordination | Accepted | `references/metrics-and-rules.md` now says the labels do not estimate plagiarism probability or misconduct risk and are not thresholds. |
| English 9 — quotation treatment | Accepted | `references/methodology-and-attribution.md` now identifies quotation marks and credit explicitly. |
| Methodology 1 — semantic/cross-language position rule | Accepted with narrower correction | `references/metrics-and-rules.md` defines the eligible target positions as the smallest verified aligned target span. Those positions remain in the intended broader per-source, category, and overall unions; the audit construct was not narrowed to lexical-only similarity. Tests in `tests/test_plagiarism_skill_package.py` cover the definition. |
| Methodology 2 — candidate-resolution gate before `Complete` | Rejected | The specification defines `Complete` as expected-source-set coverage, not exhaustive candidate-resolution coverage. Unverified candidates remain diagnostics and stay out of numerators; the proposed new provisional gate would change the adopted construct. |
| Methodology 3 — per-source/category deduplication | Accepted | `references/metrics-and-rules.md` and `references/report-template.md` now require unique target-position unions; package tests cover the formulas. |
| Methodology 4 — evidence grouping key | Accepted | `references/metrics-and-rules.md` now includes canonical artifact/version and coherent source block/span and limits merging to coherent contiguous/overlapping target and source spans. |
| Methodology 5 — passage vs. block counts | Accepted | `references/metrics-and-rules.md` and `references/report-template.md` separate retained-evidence-passage counts from unique-target-block counts. |
| Methodology 6 — source-set vs. source-text coverage | Accepted | `references/metrics-and-rules.md` and `references/report-template.md` state that `Complete` covers the non-empty expected-source set only and separately report source-text coverage; `references/source-corpus.md` uses the explicit complete expected-source-set route. |
| Methodology 7 — remove SafeAssign-derived bands | Rejected | The plan explicitly retains verified-current bands as optional named contextual labels with non-probability, non-risk, non-threshold, and re-verification boundaries. |
| Methodology 8 — rename/add attribution groups | Rejected | The plan explicitly adopts Turnitin-style public vocabulary with uncertainty and extraction-warning disclosures. Replacing the vocabulary or adding a new group would diverge from that plan. |
| Methodology 9 — complete-table label conflict | Accepted | `references/report-template.md` uses distinct Partial/Observed and Complete/unprefixed rows. |
| Methodology 10 — unsupported translation direction | Accepted | `references/metrics-and-rules.md` uses “correspondence consistent with translation” and leaves direction and common-source explanations undetermined. |
| Methodology 11 — vacuous zero-source complete route | Accepted | `references/source-corpus.md` requires `expected sources > 0`; `skills/plagiarism-audit/scripts/source_checker/cli.py` reports null coverage and fails strict mode for zero expected rows; `tests/test_cli.py` and package tests cover both layers. |
| Methodology 12 — combined coverage states | Accepted | `references/report-template.md` separates inaccessible artifacts, unusable extractions, unresolved mappings, and unanalyzed sources and states that counts may overlap. |
| Methodology optional — “properly quoted and credited” | Accepted | `references/metrics-and-rules.md` uses visible quotation/citation-signal wording rather than adjudicating propriety. |
| Methodology optional — narrow “no action” | Accepted | `references/report-template.md` uses “no similarity-related action based on this corpus.” |
| Methodology optional — artifact-status label | Accepted | `references/report-template.md` uses `Authoritative-artifact inspection` with inspected/not inspected/partially inspected values. |
| Portability 1 — lazy imports/bootstrap metadata | Rejected | The project `pyproject.toml` lists runtime dependencies, and the documented help route passes in the configured project virtual environment. A new bootstrap or lazy-import redesign was outside the accepted scope. The review's failure remains valid for the interpreter it used, but not sufficient to require that redesign. |
| Portability 2 — recover from malformed bibliography/manifest input | Rejected | A malformed provider input is a provider-input failure, not a known expected-source access gap. Recovery semantics require a separate design; the partial-corpus rule does not by itself define how to continue from corrupt input. |
| Portability 3 — zero-source 100%/strict success | Accepted | `skills/plagiarism-audit/scripts/source_checker/cli.py` returns null coverage and treats zero expected rows as a strict gap; `references/source-corpus.md`, `tests/test_cli.py`, and package tests document and verify the behavior. |
| Portability 4 — preserve Zotero diagnostics | Accepted with narrower correction | `skills/plagiarism-audit/scripts/source_checker/cli.py` and `references/source-corpus.md` preserve non-enriched status diagnostics. `tests/test_cli.py` covers unavailable, not-found, error, ambiguity, and attachment-unresolved behavior. The correction retains a valid source record for `attachment_unresolved` rather than implying bibliographic identity loss. |
| Portability 5 — strict-mode wording | Accepted | `references/source-corpus.md` now documents exact row-based exit-2 conditions and the independent target-extraction diagnostic behavior. |
| Portability optional — executable discovery | Accepted | `references/source-corpus.md` names discoverable `soffice` and `pdftotext` executables and the `pypdf` fallback. |
| Portability optional — bundled runtime wording | Accepted | `references/source-corpus.md` now says the script imports its bundled sibling `source_checker` runtime. |
| Implied removal/loss of the `attachment_unresolved` source record | Rejected and corrected | Spec re-review established that `attachment_unresolved` retains valid bibliographic identity. `skills/plagiarism-audit/scripts/source_checker/cli.py`, `references/source-corpus.md`, and `tests/test_cli.py` retain the source record and add the missing-attachment diagnostic. |
| Copyright defect — adapted labels presented as exact public labels | Accepted | `references/methodology-and-attribution.md`, `references/metrics-and-rules.md`, and `references/report-template.md` consistently identify the repository labels as adaptations of public Copyleaks vocabulary. |
| Copyright optional — aging “current” wording | Accepted | `references/metrics-and-rules.md` and `references/methodology-and-attribution.md` use access-date wording and retain the re-verification instruction. |

## Iterative review and correction history

- The specification review caught an analyzable-versus-analyzed continuation regression. The skill and reporting rules were corrected so the quantitative route requires at least one source actually analyzed, while zero analyzed sources take the diagnostic route.
- The same specification review caught a proposed loss of bibliographic metadata for Zotero `attachment_unresolved`. The controller corrected the implementation so the valid source record remains, with the missing attachment represented as a diagnostic rather than erased identity.
- The quality review caught duplicate Zotero diagnostics and an overfit Markdown-table test. The implementation/tests were narrowed so diagnostics are de-duplicated and the test verifies the contract without binding to one incidental table shape.
- Early `underspecified-request` runs were RED because the agent asked extra metric and scope questions. A later revision still allowed extra prose. The post-quality-review correction retains the semantic two-essential-items contract without requiring byte-stable English; a fresh targeted run asks only for the target and source corpus and passes 4/4 assertions.
- The accepted-set evidence committed in `a483b5f` was superseded after a provenance defect was identified: it did not cross-check envelope-embedded skill hashes after copied workspaces had been replaced. The definitive run workspace was rebuilt from scratch and all three provenance layers were cross-validated before relying on its outputs.
- The final quality review identified two Zotero refresh defects. Transition regressions now preserve stronger existing mapping provenance on live lookup failures and replace, rather than accumulate, `Zotero live resolution:` diagnostics; both skill runtimes are synchronized from the canonical implementation.
- Host-specific temporary and agent paths, opaque evidence IDs, and host-local lookup templates were removed from the committed public evidence. Stable scenario IDs, timestamps, model labels, tree hashes, public artifact paths, and result summaries are retained; the record explicitly does not claim portable standalone reproduction.

## Final validation

The prior validation record applied only to the superseded accepted set and is not relied on. For the definitive from-scratch set, the controller independently cross-validated every provenance layer, all session streams, and all assertion rows, then removed the temporary root. The targeted post-review intake run was separately validated against its current copied skill before cleanup. The complete repository test suite, Ruff, Pyright, both skill quick validations, both runtime synchronization checks, the evidence verifier, and `git diff --check` were rerun afterward and every command exited 0. Exact commands and observable results are recorded in `README.md`.
