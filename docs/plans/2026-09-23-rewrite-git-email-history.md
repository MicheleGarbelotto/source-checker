# Git Email History Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the personal Gmail address in every publishable commit and tag with GitHub's ID-based `noreply` address while preserving commit names, dates, messages, topology, and file contents.

**Architecture:** Perform the rewrite locally before any remote exists. Preserve the already verified external bundle as the recovery point, remove only clean linked worktrees, use `git-filter-repo` for author/committer/tagger rewriting, recreate `v0.1.0` at the rewritten final `main`, and validate metadata invariants plus the complete release suite before stopping without a push.

**Tech Stack:** Git, git-filter-repo 2.47.0, Python 3.12, PowerShell, pytest, Ruff, Pyright, Agent Skills `skills-ref` validator.

---

## Fixed inputs and boundaries

- Repository: `%REPOSITORY%`
- Old email: `<OLD_PRIVATE_EMAIL>`
- New email: `222029692+MicheleGarbelotto@users.noreply.github.com`
- Author/committer name remains `MicheleGarbelotto`.
- Verified recovery bundle: `%BACKUP_ROOT%\2026-09-23-before-email-rewrite\source-checker-all-refs.bundle`
- Expected bundle SHA-256: `5cf43fc1469c6b8b1f5fcb1507a04d293f3c25a2885bf8c65451880f701011b8`
- Do not change the global Git email, create a remote, push, publish to PyPI, or alter repository files.
- Preserve the untracked `docs/plans/2026-09-23-publication-hardening.md`; its verified copy is beside the recovery bundle.

### Task 1: Establish the recovery and invariants gate

- [ ] Verify that `main` contains this plan commit, every linked worktree is clean, and the only main-worktree exception is the known untracked publication-hardening plan.
- [ ] Run `git bundle verify` on the recovery bundle and recompute its SHA-256. Stop if either check differs from the fixed inputs above.
- [ ] Record outside the repository: the complete pre-rewrite ref map, commit count, branch-tip tree IDs, tag message, and a byte-for-byte metadata stream containing each commit's tree ID, author name/date, committer name/date, and message but excluding emails and commit hashes.
- [ ] Confirm that all current author, committer, and `v0.1.0` tagger emails equal the old email and that no signed commits or signed tags exist.

Expected: the backup is valid and the pre-rewrite snapshot is sufficient to prove that only identities and hashes change.

### Task 2: Remove linked-worktree constraints without deleting branches

- [ ] From the main repository, recheck each linked worktree with `git status --short`.
- [ ] Remove these four clean worktrees and then prune registrations:

```powershell
git worktree remove "%REPOSITORY%\.worktrees\citation-support-audit"
git worktree remove "%REPOSITORY%\.worktrees\plagiarism-audit"
git worktree remove "%REPOSITORY%\.worktrees\publication-hardening"
git worktree remove "%REPOSITORY%\.worktrees\source-checker-core"
git worktree prune
```
- [ ] Confirm that all five branch refs still exist and that only the main checkout remains registered.

Do not delete any branch. Stop instead of removing a worktree if it contains an uncommitted or untracked file.

### Task 3: Rewrite every branch identity

- [ ] Create a uniquely named temporary virtual environment directly beneath the system temporary directory using the repository's Python 3.12 interpreter.
- [ ] Install exactly `git-filter-repo==2.47.0` into that environment and record its version.
- [ ] Delete the old local `v0.1.0` tag; the recovery bundle retains it.
- [ ] From the main repository root run the temporary environment's
  `git-filter-repo.exe --force --email-callback` with this callback body:

```python
return (
    b"222029692+MicheleGarbelotto@users.noreply.github.com"
    if email == b"<OLD_PRIVATE_EMAIL>"
    else email
)
```

`git-filter-repo` must process all local branches. Its email callback also rewrites annotated-tag tagger emails, although the obsolete release tag has deliberately been removed.

### Task 4: Configure future commits and recreate the release tag

- [ ] Set only the repository-local identity:

```powershell
git config --local user.name "MicheleGarbelotto"
git config --local user.email "222029692+MicheleGarbelotto@users.noreply.github.com"
```

- [ ] Recreate annotated `v0.1.0` at the rewritten `main` tip with message `Source Checker 0.1.0` and the repository-local `noreply` identity.
- [ ] Confirm that every branch retains its own rewritten tip and the same
  branch-tip tree recorded before the rewrite. `main` intentionally contains
  the later email-rewrite plan commits and therefore must not be forced to
  equal `codex/publication-hardening`. Confirm that `v0.1.0^{}` resolves to the
  rewritten `main` tip.

### Task 5: Prove that the rewrite changed only identities and hashes

- [ ] Compare the post-rewrite commit count, branch-tip tree IDs, and email-excluded metadata stream with the pre-rewrite snapshot; require exact equality.
- [ ] Require every author and committer email reachable from every local branch to equal the new `noreply` address.
- [ ] Require the annotated tagger email to equal the new address.
- [ ] Scan all publishable refs and commit/tag metadata for the old Gmail and fail on any occurrence.
- [ ] Confirm that no `refs/original/`, backup ref, replace ref, or remote exists and run `git fsck --full`.

The external recovery bundle may contain the old email by design; it is private and outside the repository.

### Task 6: Re-run the release gate and stop before publication

- [ ] Run from rewritten `main`:

```powershell
.\.venv\Scripts\python.exe -m pytest -o addopts= -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pyright
.\.venv\Scripts\skills-ref.exe validate skills/citation-support-audit
.\.venv\Scripts\skills-ref.exe validate skills/plagiarism-audit
.\.venv\Scripts\python.exe tools/sync_skill_runtime.py --check skills/citation-support-audit
.\.venv\Scripts\python.exe tools/sync_skill_runtime.py --check skills/plagiarism-audit
```

- [ ] Create a standard `git archive` of rewritten `main`, extract it into a fresh temporary directory, confirm `.git` and `.venv` are absent, install `.[dev]`, and repeat pytest, Ruff, Pyright, both skill validators, both synchronization checks, wheel inspection, and installed entry-point help.
- [ ] Validate and remove only the uniquely named temporary rewrite and archive directories.
- [ ] Report the old-to-new `main` and tag hashes, test count, invariant checks, local email configuration, and clean working-tree status.

Stop without adding a remote, pushing any ref, changing GitHub settings, or deleting the private recovery bundle.
