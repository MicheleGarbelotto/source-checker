# Security policy

## Reporting a vulnerability

GitHub private vulnerability reporting must be enabled before public release.
Use it from the repository Security tab.
Do not open a public issue for a suspected vulnerability.
Include the affected version or commit, operating system, input type,
reproduction steps, impact, and any suggested mitigation. Do not include
confidential source documents or credentials.

If private vulnerability reporting is unavailable, do not disclose
vulnerability details. You may open only a metadata-free public contact request
asking maintainers to enable or provide a private channel. Do so without naming
affected documents or inputs and without providing reproduction details.

## Security scope

Reports may include prompt injection through document content, path traversal,
unintended file writes, unsafe subprocess invocation, macro or embedded-code
execution, network access outside the documented local Zotero route, dependency
vulnerabilities, or disclosure of target or source contents.

The project parses untrusted documents and may invoke `pdftotext` or LibreOffice
for explicitly requested routes. Use isolation when processing documents of
unknown origin. Audit outputs are evidence aids, not security, legal,
plagiarism, or misconduct verdicts.
