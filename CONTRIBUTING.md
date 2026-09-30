# Contributing

source-checker requires Python 3.11 or newer. Create a virtual environment and
install the project in editable development mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Write a failing test before implementation, confirm that it fails for the
expected reason, make the smallest change that passes it, and then run the full
local validation set.

## Project boundaries

Keep the two skills separate. `citation-support-audit` evaluates claim-source
support and citation placement. `plagiarism-audit` evaluates source-bounded
textual similarity and does not make citation-support judgments. Code under
`src/source_checker` is the authoritative implementation.

Runtime synchronization is mandatory for both skills whenever authoritative
code changes. Update both bundled skill runtimes and verify that each remains in
sync; do not edit bundled runtime copies as independent implementations.

Use only synthetic fixtures in tests and examples. Never commit confidential
target documents, source documents, credentials, or participant data. Report
security problems through GitHub private vulnerability reporting from the
repository Security tab. Private vulnerability reporting must be enabled before
public release. If it is unavailable, do not disclose vulnerability details;
open only a metadata-free public contact request asking maintainers to enable or
provide a private channel.

## Local validation

Install the official skill validator from its immutable source revision:

```powershell
python -m pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
```

Run the complete validation set before submitting a pull request:

```powershell
python -m pytest -q
python -m ruff check .
python -m pyright
skills-ref validate skills/citation-support-audit
skills-ref validate skills/plagiarism-audit
python tools/sync_skill_runtime.py --check skills/citation-support-audit
python tools/sync_skill_runtime.py --check skills/plagiarism-audit
```
