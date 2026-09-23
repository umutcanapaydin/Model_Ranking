# Issues, labels and the verification pipeline

The skills **implement** this file. This file is the reason they do what they do — change it here
and the skills follow, never the other way round.

## The one load-bearing rule

**The agent opens drafts; a human marks them ready and merges.** No exception — not for a
one-line fix, not for an interactive session with the human watching.

Branch protection on the default branch is what makes this real rather than an honour system.
Everything below is downstream of it: the skills stop where they stop because of it, the label
pipeline exists because a merge is not a verification, and the gates exist because the human
doing the merging cannot read every line.

## The label vocabulary — and it is closed

Five groups. That is the whole set; `make labels` creates the missing ones once per repository.
**Use one that already exists.** If a new one is genuinely
needed, ask before a skill relies on it: *a skill keying on a label nobody created fails
silently* — which is exactly how one repo's gate labels sat documented-but-absent while every
issue went unpicked by CI.

| Group | Labels |
|---|---|
| **Type** | `bug` · `enhancement` · `documentation` · `question` · `duplicate` · `invalid` · `wontfix` · `good first issue` · `help wanted` |
| **Severity** | `severity:critical` · `severity:high` · `severity:medium` · `severity:low` |
| **Gate** (CI only) | `agent:triage` · `agent:fix` |
| **Verification** | `dev:done` · `qa:ready` · `qa:passed` · `qa:failed` · `qa:blocked` |
| **Scope** | `out-of-scope` |

**Severity:** exactly one on a `bug`, chosen by **measured impact**, never the reporter's urgency.
It stays for the issue's whole life, including after it closes — that is what makes the archive
readable. Non-bug issues carry none.

**`out-of-scope`:** deliberately outside this release, by the owner's decision. The issue **stays
open** and keeps its type and severity. `wontfix` means *never*; closing would drop it from every
open list. It is a deferral, not a rejection — removing the label puts it back in the queue.
Applied only after triage, only on the owner's word, carries no QA meaning, and never sits beside
a `dev:`/`qa:` label.

**Area labels are deliberately absent.** The question triage actually has to answer — *which
component?* — belongs in the diagnosis comment, not in a label nobody maintains.

## The verification pipeline

**A `bug` is not closed by merging its fix.** Merging proves the code changed. It does not prove
the bug is gone — and where the suite runs against a stub, a green run proves only that the code
behaves as the stub was *told* to answer.

| Label | Meaning | Who sets it |
|---|---|---|
| `dev:done` | the fix is merged. **Not verified.** | `/post-merge`, at merge |
| `qa:ready` | waiting for a person to verify on a deployed build | us, once a human says it is deployed |
| `qa:passed` | verified — now it may be closed | the verifier |
| `qa:failed` | still broken; back to triage | the verifier |
| `qa:blocked` | could not be tested at all — environment or seed data, not code | the verifier |

- **Nothing is applied when the PR opens.** At draft-PR time neither state is true, and
  `qa:ready` sends someone after a build that does not exist.
- **Never infer a deploy from a merge.** An agent has no signal for it. Wait to be told.
- **Swap, never accumulate.** Each transition removes the one before it:
  `gh issue edit <n> --remove-label "dev:done" --add-label "qa:ready"`. Two lifecycle labels on
  one issue reads as two states at once, and a label people cannot trust is worse than none.
- **The last three are the verifier's**, never the agent's.
- Enhancements and documentation are **not** in this pipeline. There, the merge closing the issue
  is correct.

## A bug's PR carries no closing keyword

This is what makes the rule above hold instead of being undone one step later. No
`Closes`/`Fixes`/`Resolves #<n>` in a bug's PR body or in any of its commit messages. Write
`Ref #<n>` and say in the body that the issue stays open on purpose.

**Mind the phrasing, then verify it.** GitHub links on any `close`/`fix`/`resolve` immediately
followed by an issue reference, **whatever the surrounding sentence says** — so
*"please do not close #12"* creates the very link it warns against. Write
**"please leave #12 open"**.

Then check rather than assume:

```bash
gh pr view <pr> --json closingIssuesReferences   # must be an empty list
```

A grep over the body first is fine — `(?i)\b(clos|fix|resolv)[a-z]*\s*:?\s*#[0-9]+` — but
`closingIssuesReferences` is the **authority**: a body can read clean while the link survives
from an earlier revision.

**Any PR naming a bug's number can close it** — a docs PR, an unrelated refactor, a comment
quoting the issue. It does not need the `bug` label itself. That is why the check lives in
`/pre-merge` and runs on **every** PR, whatever its branch prefix.

## What a skill never does

No skill merges, marks a draft ready, force-pushes, uses `--no-verify`, touches
`.github/workflows/**`, or writes AI attribution — no `Co-Authored-By`, no "Generated with", no
badges — in commits, PR bodies, issue bodies or comments. This holds interactively **and** in CI.
