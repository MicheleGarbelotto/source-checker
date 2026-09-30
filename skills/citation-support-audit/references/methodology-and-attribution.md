# Methodology and attribution

## Basis of the adaptation

This package uses original instructions and formulas for an academic-document audit. It adapts two public ALCE concepts: citation recall asks whether claims that require evidence receive complete support from their cited set, and citation precision asks whether each attached citation contributes support. The adaptation changes the unit of analysis, corpus conditions, and judgment procedure. It applies human, passage-level review to atomic claims in user-supplied documents and explicitly handles incomplete access.

The resulting measures must be labelled **ALCE-style**. They are not directly comparable with published ALCE benchmark scores. ALCE evaluates generated answers under its own tasks, corpora, sentence- and claim-handling procedures, automated entailment components, and aggregation rules; this package does not reproduce those conditions.

Public Turnitin documentation informed the decision to report citation mechanics and quotation checks separately from substantive source support. It did not supply the support labels or quantitative formulas used here.

## Formulas used by this package

These formulas restate the package's own definitions in [metrics-and-rules.md](metrics-and-rules.md); they do not reproduce external prose, code, tables, or graphics:

```text
whole-scope citation recall = fully supported eligible claims / all eligible claims * 100
whole-scope citation precision = supporting citations / all citations evaluated * 100
verified-subset citation recall = fully supported classifiable claims / classifiable eligible claims * 100
verified-subset citation precision = supporting classifiable citations / classifiable citations * 100
audit coverage = classifiable eligible claims / all eligible claims * 100
corpus coverage = analyzed expected sources / all expected sources * 100
```

Whole-scope citation recall requires every eligible claim to be classifiable. Whole-scope citation precision separately requires every in-scope claim-citation association to be classifiable. When access is incomplete but at least one eligible claim is classifiable, report the applicable verified-subset results and coverage instead. These coverage measures and incomplete-corpus rules are package-specific and are not ALCE benchmark metrics.

## Source-verification checklist

The following primary or official sources were checked on **2026-09-22**.

| Source title | Authors or organization | URL | Adapted concept | Not reproduced |
|---|---|---|---|---|
| *Enabling Large Language Models to Generate Text with Citations* | Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen; published by the Association for Computational Linguistics | https://aclanthology.org/2023.emnlp-main.398/ | Citation quality includes recall of supported statements and precision of individual citations; evaluation distinguishes joint support from citation contribution. | Benchmark tasks, datasets, prompts, automatic entailment models, reported scores, prose, tables, and graphics. |
| *ALCE: Enabling Large Language Models to Generate Text with Citations* repository | Princeton NLP; repository for Gao et al. | https://github.com/princeton-nlp/ALCE | Public implementation confirms benchmark-specific citation-recall and citation-precision aggregation and multiple-citation handling in `eval.py`. | Source code, model dependencies, data, configurations, and reproduction claims. |
| *Writing in Turnitin Clarity* | Turnitin | https://guides.turnitin.com/hc/en-us/articles/37509711350285-Writing-in-Turnitin-Clarity | Citation assistance checks in-text and reference-list formatting against a selected style; suggestions remain reviewable rather than self-validating. | Product workflow, interface, generated suggestions, supported-style claims as a package capability, prose, and images. |
| *How do the Match Groups work in the new Similarity Report?* | Turnitin | https://guides.turnitin.com/hc/en-us/articles/28057483210637-How-do-the-Match-Groups-work-in-the-new-Similarity-Report | Citation and quotation detection can be fallible, so mechanics findings need explicit limits and remain separate from support judgments. | Similarity matching, Match Groups, machine-learning detection, misconduct classification, product workflow, prose, and images. |

## Independence and limits

`citation-support-audit` is an independent implementation. It is not affiliated with, endorsed by, validated by, or technically integrated with ALCE's authors, Princeton University, the Association for Computational Linguistics, or Turnitin. Similar terminology does not imply equivalent inputs, procedures, reliability, scores, or product functionality.

The audit evaluates whether cited evidence substantiates claims within a defined document and corpus. It does not establish the universal truth of a claim, reproduce a benchmark evaluation, provide a similarity score, or make a research-misconduct determination.
