# Release clean-copy verification receipt

This file is **execution evidence, not a test substitute**. It records the
original Task 8 clean-copy verification of the tree subsequently committed as
`ec501a1375ef386badb3c7f4b02817aa937a7c30`, an independent archive rerun of
that commit, and the publication-hardening verification recorded below.
Automated package tests continue to define the executable contracts.

Paths use `%USERPROFILE%`, `%TEMP%`, `%WORKTREE%`, `%BUNDLED_PYTHON%`, and
`%SKILL_CREATOR%` placeholders so the receipt contains no private absolute
profile path.

## Original Task 8 execution

The original release run copied the then-current worktree—the tree subsequently
committed as `ec501a1375ef386badb3c7f4b02817aa937a7c30`—to
`%TEMP%\source-checker-clean-20260923-task8`. It excluded `.git`, `.venv`,
`.worktrees`, generated audit output, and tool caches, then verified those
development paths were absent before creating the fresh environment.

Commands, with only path prefixes replaced by the placeholders above:

```powershell
$root = "%TEMP%\source-checker-clean-20260923-task8"
robocopy %WORKTREE% $root /E /XD .venv .worktrees audit-output-release-smoke __pycache__ .pytest_cache .ruff_cache /XF .git *.pyc
Push-Location $root
try {
    & %BUNDLED_PYTHON%\python.exe -m venv .venv-clean
    & .\.venv-clean\Scripts\python.exe -m pip install -e ".[dev]"
    & .\.venv-clean\Scripts\python.exe -m pytest -q
    & .\.venv-clean\Scripts\ruff.exe check .
    & .\.venv-clean\Scripts\python.exe %SKILL_CREATOR%\scripts\quick_validate.py skills/citation-support-audit
    & .\.venv-clean\Scripts\python.exe %SKILL_CREATOR%\scripts\quick_validate.py skills/plagiarism-audit
    & .\.venv-clean\Scripts\python.exe skills/citation-support-audit/scripts/source_corpus.py --help
    & .\.venv-clean\Scripts\python.exe skills/plagiarism-audit/scripts/source_corpus.py --help
}
finally {
    Pop-Location
}
```

Observed outcomes:

- editable development installation exited 0;
- pytest: **479 / 479 passed**;
- Ruff: `All checks passed!`;
- both validators: `Skill is valid!`;
- both vendored `source_corpus.py --help` commands exited 0 and printed the
  `usage: source_corpus.py [-h] {manifest,cache} ...` line;
- cleanup resolved the exact temporary path under `%TEMP%`, removed it
  recursively, and verified that it no longer existed.

## Independent specification review of `ec501a1`

At execution time, the reviewer first resolved the then-current local release
alias to `ec501a1375ef386badb3c7f4b02817aa937a7c30`. To keep this durable receipt
replayable after local release aliases move, the command below records that
resolved immutable commit in place of the alias; the outcomes are those from
the original review run. The unique temporary root was
`%TEMP%\source-checker-spec-review-f495174ec3bc4a978277f227ce23dbd8`.

```powershell
$root = "%TEMP%\source-checker-spec-review-f495174ec3bc4a978277f227ce23dbd8"
$zip = "$root.zip"
git -C %WORKTREE% archive --format=zip --output=$zip ec501a1375ef386badb3c7f4b02817aa937a7c30
Expand-Archive -LiteralPath $zip -DestinationPath $root
Remove-Item -LiteralPath $zip
Push-Location $root
try {
    & (Join-Path %WORKTREE% ".venv\Scripts\python.exe") -m venv (Join-Path $root ".venv")
    $py = Join-Path $root ".venv\Scripts\python.exe"
    & $py -m pip install -q -e "$root[dev]"
    & $py -m pytest -q
    & $py %SKILL_CREATOR%\scripts\quick_validate.py skills/citation-support-audit
    & $py %SKILL_CREATOR%\scripts\quick_validate.py skills/plagiarism-audit
    & $py skills/citation-support-audit/scripts/source_corpus.py --help
    & $py skills/plagiarism-audit/scripts/source_corpus.py --help
}
finally {
    Pop-Location
}
```

Observed outcomes:

- archive and extraction exited 0; `.git` was absent (`git_absent=True`);
- virtual-environment creation and editable installation both exited 0;
- pytest: **479 / 479 passed**;
- both validators printed `Skill is valid!`;
- both vendored `--help` commands exited 0 and printed their usage line;
- the reviewer emitted `CLEAN_COPY_OK` for the unique root;
- cleanup first verified the resolved target was beneath `%TEMP%` with the
  exact expected leaf, then removed it recursively and observed `exists=False`.

The independent run used only the immutable archive and a fresh environment.
It did not depend on the repository `.git` directory, the worktree virtual
environment as an installed package environment, a user Zotero library, or any
thesis file.

## Current release verification receipt

A tracked file cannot truthfully contain results produced only after its own
commit without creating a self-reference. For the earlier local release
checkpoint, the annotated local `v0.1.0` tag message was therefore the
authoritative post-commit receipt at the time. It identifies the exact verified
commit and records the clean-archive date, `.git` exclusion, fresh environment
and installation, exact pytest count, Ruff result, both skill validators, both
vendored `--help` checks, and cleanup.

Inspect that receipt locally with either command:

```powershell
git tag -n99 v0.1.0
git cat-file -p v0.1.0
```

## Publication hardening verification

The **verified parent commit** is
`3b25cc3a7f5d0bf3449f96bc5000da3c0b2cdd97`. This is the immutable
`VERIFICATION_SUBJECT` used for every archive result below. This receipt does
not name or claim to verify its own later documentation commit.

Verification ran on Python **3.12.14**. Commands below are relative to the
repository or extracted archive root. The system-generated temporary root is
represented by `$root`; no private absolute host path or execution-session
identifier is retained.

### Worktree verification

These commands each exited 0 against the verified parent:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -o addopts= -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright
.\.venv\Scripts\skills-ref.exe validate skills/citation-support-audit
.\.venv\Scripts\skills-ref.exe validate skills/plagiarism-audit
.\.venv\Scripts\python.exe tools/sync_skill_runtime.py --check skills/citation-support-audit
.\.venv\Scripts\python.exe tools/sync_skill_runtime.py --check skills/plagiarism-audit
.\.venv\Scripts\python.exe skills/citation-support-audit/scripts/source_corpus.py --help
.\.venv\Scripts\python.exe skills/plagiarism-audit/scripts/source_corpus.py --help
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --wheel-dir build/release-check
.\.venv\Scripts\python.exe -c "from pathlib import Path; import zipfile; wheels=list(Path('build/release-check').glob('*.whl')); assert len(wheels)==1, wheels; z=zipfile.ZipFile(wheels[0]); names=z.namelist(); metadata=[n for n in names if n.endswith('.dist-info/METADATA')]; licenses=[n for n in names if n.endswith('.dist-info/licenses/LICENSE')]; entries=[n for n in names if n.endswith('.dist-info/entry_points.txt')]; assert len(metadata)==1, metadata; assert len(licenses)==1, licenses; assert len(entries)==1, entries; meta=z.read(metadata[0]).decode(); entry=z.read(entries[0]).decode(); assert 'Name: source-checker' in meta; assert 'Version: 0.1.0' in meta; assert 'License-Expression: MIT' in meta; assert 'source-checker-corpus = source_checker.cli:main' in entry"
```

The first pytest command is the required release command; the second used an
empty configured `addopts` value only to surface the otherwise suppressed exact
summary. The full suite passed **523 tests**. Ruff reported `All checks passed!`
and Pyright reported `0 errors, 0 warnings, 0 informations`. Both official
`skills-ref` validations reported `Valid skill`, both runtime synchronization
checks reported `up to date`, and both vendored help commands printed
`usage: source_corpus.py [-h] {manifest,cache} ...`.

The wheel inspection found exactly one `.dist-info/METADATA`, exactly one
`.dist-info/licenses/LICENSE`, and exactly one
`.dist-info/entry_points.txt`. It confirmed `Name: source-checker`,
`Version: 0.1.0`, `License-Expression: MIT`, and the
`source-checker-corpus = source_checker.cli:main` entry point.

### Exact-commit clean archive

The first extracted ZIP empirically produced a CRLF byte-count mismatch in one
frozen YAML artifact. The accepted run used `-c core.autocrlf=false`, but
acceptance depended on the explicit 8,011-byte and SHA-256 checks below, not on
an assumption about what that Git setting would do.

The exact archive and extraction procedure was:

~~~powershell
$subject = "3b25cc3a7f5d0bf3449f96bc5000da3c0b2cdd97"
$worktreePython = (Resolve-Path -LiteralPath ".\.venv\Scripts\python.exe").Path
$root = Join-Path ([IO.Path]::GetTempPath()) ("source-checker-archive-" + [guid]::NewGuid().ToString("N"))
$checkout = Join-Path $root "checkout"
$zip = Join-Path $root "subject.zip"
New-Item -ItemType Directory -Path $root -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $checkout -ErrorAction Stop | Out-Null
git -c core.autocrlf=false archive --format=zip --output=$zip $subject
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }
& $worktreePython -c "import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" $zip $checkout
if ($LASTEXITCODE -ne 0) { throw "ZIP extraction failed" }
Remove-Item -LiteralPath $zip -Force
if (Test-Path -LiteralPath (Join-Path $checkout ".git")) { throw "archive contains .git" }
if (Test-Path -LiteralPath (Join-Path $checkout ".venv")) { throw "archive contains .venv" }
~~~

Before environment creation, the two absence checks returned
`git_absent=True` and `venv_absent=True`. A separate byte/hash assertion
confirmed the frozen plagiarism scenario file retained its recorded 8,011-byte
size and SHA-256 digest.

The known worktree Python created the archive environment after
`Push-Location` established the extracted checkout as the current directory.
The project and the pinned official validator were installed separately, then
the complete verification was replayed:

~~~powershell
function Assert-NativeSuccess([string]$step) {
    if ($LASTEXITCODE -ne 0) { throw "$step failed with exit $LASTEXITCODE" }
}

Push-Location $checkout
try {
    & $worktreePython -m venv .venv
    Assert-NativeSuccess "venv creation"
    $python = (Resolve-Path -LiteralPath ".\.venv\Scripts\python.exe").Path
    $pythonVersion = & $python --version
    Assert-NativeSuccess "Python version"
    if ($pythonVersion -ne "Python 3.12.14") { throw "Unexpected Python: $pythonVersion" }

    & $python -m pip install ".[dev]"
    Assert-NativeSuccess "archive project installation"
    & $python -m pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
    Assert-NativeSuccess "official validator installation"
    $validator = (Resolve-Path -LiteralPath ".\.venv\Scripts\skills-ref.exe").Path

    & $python -m pytest -q
    Assert-NativeSuccess "pytest"
    & $python -m pytest -o addopts= -q
    Assert-NativeSuccess "pytest count"
    & $python -m ruff check .
    Assert-NativeSuccess "Ruff"
    & $python -m pyright
    Assert-NativeSuccess "Pyright"
    & $validator validate skills/citation-support-audit
    Assert-NativeSuccess "Citation Support Audit validation"
    & $validator validate skills/plagiarism-audit
    Assert-NativeSuccess "Plagiarism Audit validation"
    & $python tools/sync_skill_runtime.py --check skills/citation-support-audit
    Assert-NativeSuccess "Citation Support Audit synchronization"
    & $python tools/sync_skill_runtime.py --check skills/plagiarism-audit
    Assert-NativeSuccess "Plagiarism Audit synchronization"
    & $python skills/citation-support-audit/scripts/source_corpus.py --help
    Assert-NativeSuccess "Citation Support Audit help"
    & $python skills/plagiarism-audit/scripts/source_corpus.py --help
    Assert-NativeSuccess "Plagiarism Audit help"
    & $python -m pip wheel . --no-deps --wheel-dir build/release-check
    Assert-NativeSuccess "wheel build"
    & $python -c "from pathlib import Path; import zipfile; wheels=list(Path('build/release-check').glob('*.whl')); assert len(wheels)==1, wheels; z=zipfile.ZipFile(wheels[0]); names=z.namelist(); metadata=[n for n in names if n.endswith('.dist-info/METADATA')]; licenses=[n for n in names if n.endswith('.dist-info/licenses/LICENSE')]; entries=[n for n in names if n.endswith('.dist-info/entry_points.txt')]; assert len(metadata)==1, metadata; assert len(licenses)==1, licenses; assert len(entries)==1, entries; meta=z.read(metadata[0]).decode(); entry=z.read(entries[0]).decode(); assert 'Name: source-checker' in meta; assert 'Version: 0.1.0' in meta; assert 'License-Expression: MIT' in meta; assert 'source-checker-corpus = source_checker.cli:main' in entry"
    Assert-NativeSuccess "wheel inspection"
    & $python -m pip install --force-reinstall --no-deps .\build\release-check\source_checker-0.1.0-py3-none-any.whl
    Assert-NativeSuccess "wheel force installation"
    & .\.venv\Scripts\source-checker-corpus.exe --help
    Assert-NativeSuccess "installed entry point"
}
finally {
    Pop-Location
}
~~~

All commands exited 0: **523 tests passed**, Ruff and Pyright were clean, both
official validators reported `Valid skill`, both synchronization checks
reported `up to date`, both vendored help commands printed the expected usage,
and the wheel build and content assertions passed. The force-reinstall occurred
in the already provisioned archive virtual environment. It is an
installed-artifact and entry-point smoke test, not proof that the wheel's
dependencies are isolated or independently complete.

The installed entry point printed
`usage: source-checker-corpus [-h] {manifest,cache} ...`.

The official pinned `skills-ref` validator replaces the stale bundled Codex
validator for this verification by explicit user-approved decision; the stale
validator rejects valid compatibility metadata and is not used as a release
gate.

### Privacy and evidence limits

The complete required host-path, private-memory, rollout/session, credential
prefix, cloud-key prefix, and private-key-header pattern set was scanned both
in tracked files at the verified parent and in the extracted archive. The only
matches were nine deliberate negative-test literals in
`tests/test_release_readiness.py` at lines 462-466 and 1120-1123. They are test
implementation inputs that assert public evidence rejects private provenance;
no public evidence, documentation, package metadata, or runtime file matched.

The scanner below defines all eleven required patterns without embedding their
complete sensitive literals in this receipt. Its fourth tuple field is the
stable pattern label defined in the patterns collection, so output has the
shape (scope, path, line, pattern) without source-line or secret content. It
scans the exact subject blobs and the corresponding tracked paths in the
extracted archive:

~~~powershell
$privacyScan = @'
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

subject = sys.argv[1]
archive_root = Path(sys.argv[2])

def fixed(label: str, value: str) -> tuple[str, re.Pattern[str]]:
    return label, re.compile(re.escape(value))

patterns = (
    fixed("windows-profile", "C:" + "\\" + "Users" + "\\"),
    fixed("thesis-profile", "%USERPROFILE%" + "\\" + "Documents" + "\\" + "TesiUNIPD"),
    fixed("memory-citation", "<oai-" + "mem-citation>"),
    fixed("memory-file", "MEMORY" + ".md"),
    fixed("rollout-ids", "<rollout_" + "ids>"),
    (
        "rollout-jsonl",
        re.compile(r'rollout-\d{4}-\d{2}-\d{2}[^\s"<>]+\.jsonl\b', re.IGNORECASE),
    ),
    fixed("agent-task", "/root/" + "task"),
    fixed("classic-token", "gh" + "p_"),
    fixed("fine-grained-token", "github_" + "pat_"),
    fixed("cloud-key", "AK" + "IA"),
    fixed("private-key-header", "-----BEGIN PRIVATE " + "KEY-----"),
)

expected_logical = {
    ("tests/test_release_readiness.py", 462, "memory-citation"),
    ("tests/test_release_readiness.py", 463, "memory-file"),
    ("tests/test_release_readiness.py", 464, "rollout-ids"),
    ("tests/test_release_readiness.py", 465, "agent-task"),
    ("tests/test_release_readiness.py", 466, "thesis-profile"),
    ("tests/test_release_readiness.py", 1120, "windows-profile"),
    ("tests/test_release_readiness.py", 1121, "memory-citation"),
    ("tests/test_release_readiness.py", 1122, "memory-file"),
    ("tests/test_release_readiness.py", 1123, "rollout-ids"),
}

tracked = subprocess.run(
    ["git", "ls-tree", "-r", "--name-only", subject],
    check=True,
    capture_output=True,
    text=True,
    encoding="utf-8",
).stdout.splitlines()

def scan(scope: str, path: str, data: bytes) -> set[tuple[str, str, int, str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return set()
    found = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in patterns:
            if pattern.search(line):
                found.add((scope, path, line_number, label))
    return found

matches = set()
for path in tracked:
    subject_data = subprocess.run(
        ["git", "show", f"{subject}:{path}"],
        check=True,
        capture_output=True,
    ).stdout
    matches.update(scan("subject", path, subject_data))

    archive_path = archive_root.joinpath(*PurePosixPath(path).parts)
    if not archive_path.is_file():
        raise SystemExit(f"archive is missing tracked path: {path}")
    matches.update(scan("archive", path, archive_path.read_bytes()))

for match in sorted(matches):
    print(match)

subject_logical = {(path, line, label) for scope, path, line, label in matches if scope == "subject"}
archive_logical = {(path, line, label) for scope, path, line, label in matches if scope == "archive"}
if subject_logical != expected_logical:
    raise SystemExit("subject privacy matches differ from the exact allowlist")
if archive_logical != expected_logical:
    raise SystemExit("archive privacy matches differ from the exact allowlist")
if len(matches) != 18:
    raise SystemExit(f"expected 18 scope-qualified matches, observed {len(matches)}")
logical_matches = subject_logical | archive_logical
if len(logical_matches) != 9:
    raise SystemExit(f"expected nine deduplicated logical exceptions, observed {len(logical_matches)}")
print("PRIVACY_SCAN_OK scopes=2 scope_qualified=18 logical=9")
'@
$privacyScan | & $worktreePython - $subject $checkout
if ($LASTEXITCODE -ne 0) { throw "privacy scan failed" }
~~~

Both scopes produced identical nine-item logical sets. The scanner therefore
observed 18 scope-qualified matches and exactly nine deduplicated logical
exceptions; any extra, missing, or scope-divergent match fails the procedure.

Only after the archive scan completed did cleanup resolve and validate the
exact generated root before deletion:

~~~powershell
$tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
$resolvedRoot = [IO.Path]::GetFullPath($root).TrimEnd([IO.Path]::DirectorySeparatorChar)
$resolvedParent = [IO.Path]::GetDirectoryName($resolvedRoot)
$resolvedLeaf = [IO.Path]::GetFileName($resolvedRoot)
if ($resolvedParent -ne $tempRoot) { throw "cleanup target is not a direct child of system temp" }
if ($resolvedLeaf -notmatch "^source-checker-archive-[0-9a-f]{32}$") { throw "cleanup target name is not unique and expected" }
Remove-Item -LiteralPath $resolvedRoot -Recurse -Force -ErrorAction Stop
if (Test-Path -LiteralPath $resolvedRoot) { throw "cleanup target still exists" }
Write-Output "exists_after=False"
~~~

The verified cleanup reported `exists_after=False`.

Controller attestation covers the committed public activation scenarios,
recorded outcomes, assertion rows, and stated evidence limits. No host-only
logs are needed or claimed for that attestation. This receipt does not claim
hidden-runtime reproduction, GitHub publication, or PyPI publication.

## Default-archive line-ending correction

The **verified parent commit** for this follow-up is
`0d6a92d67fcf1f7c3496603b0facbb0dd8effaa9`. It adds an explicit
`text eol=lf` attribute for the frozen plagiarism scenario fixture and a
regression test for that contract. The earlier verification remains above as
historical evidence; this follow-up demonstrates that its Windows-only
`core.autocrlf=false` archive override is no longer required.

Verification ran on Python **3.12.14** with the repository configured as
`core.autocrlf=true`. The exact commit was exported with the ordinary command:

```powershell
git archive --format=zip --output=$zip $subject
```

No command-line Git configuration override was used. Before environment
creation, the extracted archive contained neither `.git` nor `.venv`. The
archived `tests/behavior/plagiarism-audit/scenarios.yaml` contained exactly
**8,011 bytes** and its SHA-256 was
`94c01216dcaee86d6e925953037f59f99207038ae8897e66cced4d9b8b3a76a0`,
matching `run-manifest.json`.

A fresh virtual environment was created inside the extracted archive. The
project was installed with `.[dev]`, and the official `skills-ref` validator
was installed from the pinned upstream revision already recorded above. The
following results were observed:

- pytest: **524 tests passed**;
- Ruff: `All checks passed!`;
- Pyright: `0 errors, 0 warnings, 0 informations`;
- both Agent Skills: `Valid skill`;
- both vendored runtime synchronization checks: `up to date`;
- both vendored `source_corpus.py --help` commands exited 0;
- the wheel built successfully and contained the expected MIT license
  expression, license file, and `source-checker-corpus` entry point;
- force-installing that wheel and running `source-checker-corpus --help`
  exited 0.

The generated temporary directory was validated as a uniquely named direct
child of the system temporary directory before recursive removal, and its
absence was confirmed after cleanup. This follow-up does not claim GitHub or
PyPI publication.
