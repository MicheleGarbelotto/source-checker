# Changelog

All notable changes to this project are documented here.

## [0.1.0] - 2026-09-23

### Added

- `citation-support-audit` for bounded claim-source support, reference-integrity,
  and citation-mechanics review.
- `plagiarism-audit` for source-bounded similarity, attribution-signal, close
  paraphrase, patchwriting, and translated-overlap review.
- Supported formats: QMD, Markdown, plain text, TeX/LaTeX, local static HTML,
  DOCX, DOCM, legacy DOC through LibreOffice conversion, and PDF.
- Corpus providers and routes: explicit files/directories, compatible manifests,
  BibTeX/BibLaTeX, RIS, CSL JSON, Mendeley exports with accessible attachments,
  and optional read-only Zotero Desktop resolution.
- Shared manifest, deterministic mapping, extraction-quality, and incremental
  source-cache runtime with synchronized copies in both skills.
- Transparent complete- and partial-corpus metrics. Partial percentages describe
  only observed evidence within the analyzed corpus and are reported beside
  corpus coverage.
- Cross-platform GitHub Actions validation on supported Python versions.
- Public package, repository, license, and software-citation metadata.
- Sanitized public evaluation evidence with an explicit prompt-injection and
  untrusted-evidence boundary.
- Standalone skill license and compatibility metadata, portable installation
  guidance, and community contribution and security-reporting files.
- Immutable GitHub Actions references, official `skills-ref` validation pinned
  to an exact upstream revision, and weekly Dependabot checks.
- A public activation-evaluation suite covering direct, indirect, incomplete,
  non-trigger, and boundary cases for both skills.
- PEP 639 license metadata plus wheel-content, license-file, installation, and
  console-entry-point verification.
- LF normalization for the frozen plagiarism scenario fixture so exact-byte
  verification remains stable in Git archives created on Windows.

### Known limitations

- The runtime does not fetch live HTML, execute JavaScript, or automatically
  ingest embedded bibliographies.
- It does not perform OCR. Sparse or degraded PDFs require separate inspection.
- Legacy DOC extraction depends on a discoverable LibreOffice `soffice`
  executable; conversion uses the system temporary directory and LibreOffice
  may update its own user profile. PDF layout extraction optionally uses
  `pdftotext`.
- Zotero live resolution is read-only and PDF-attachment-only. Mendeley support
  is export-based and does not access private databases or cloud APIs.
- The skills do not reproduce proprietary detection algorithms and do not make
  legal, authorship, intent, plagiarism, or research-misconduct determinations.
