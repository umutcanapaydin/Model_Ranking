---
name: test-and-commit
description: Run this repo's tests; if they pass, draft a conventional commit and ask before committing. Use after finishing a logical change.
---

1. Run `make check`. If it fails, stop and report the failures — do not stage or commit.
2. If it passes, run `git status` and `git diff --staged`. If nothing is staged, stage tracked changes with `git add -u` (never `git add -A` — risks pulling in secrets or local junk).
3. Look at the last 10 commits with `git log --oneline -10` to infer this repo's commit message style (conventional, sentence-case, prefix tags, etc.).
4. Draft a commit message in that style. Show it to the user. Do NOT commit until the user approves.
5. On approval, create the commit. Never use `--amend` or `--no-verify`.
