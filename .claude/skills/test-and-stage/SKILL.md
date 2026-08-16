---
name: test-and-stage
description: Run this repo's tests; if they pass, draft a conventional commit and ask before committing. Use after finishing a logical change.
---

1. Run `make check`. If it fails, stop and report the failures — do not stage or commit.
2. If it passes, run `git status` and `git diff --staged`. If nothing is staged, stage tracked changes with `git add -u` (never `git add -A` — risks pulling in secrets or local junk).
3. Look at the last 10 commits with `git log --oneline -10` to infer this repo's commit message style (conventional, sentence-case, prefix tags, etc.).
4. Draft a commit message in that style. Show it to the user. Do NOT commit until the user approves.
5. On approval, create the commit. Never use `--amend` or `--no-verify`.

## v4.3.2 — this skill STOPS at staging

An external reviewer found this skill creating commits while `AGENTS.md` said agents never run git.
The skill was wrong, not the rule.

**Do not run `git commit`. Do not run `git push`.** Stage with `git add -u`, then print the commit
message you would have used and stop. The owner runs the commit.

The reason is attribution, not ceremony: in the field, one agent-authored commit was **indistinguishable
from the owner's own** because it carried his identity. An owner who cannot tell which commits he wrote
cannot review his own history, and a signed history that is not true is worse than an unsigned one.
