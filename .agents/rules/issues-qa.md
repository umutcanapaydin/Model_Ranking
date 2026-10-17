# Issues with QA verification on

Read this only when the brief says `QA verification: on` (`.agents/rules/issues.md`, "The verification
pipeline"); off, the default, a bug closes when its fix merges and none of this applies. The skills
that act on it — `/pre-merge` §2, `/post-merge` §3–§5 — check the flag themselves.

## The verification pipeline

**On** — a person verifies on a deployed build — this file holds. **A `bug` is not closed by merging
its fix.** Merging proves the code changed. It does not prove the
bug is gone — and where the suite runs against a stub, a green run proves only that the code
behaves as the stub was *told* to answer.

| Label | Meaning | Who sets it |
|---|---|---|
| `dev:done` | the fix is merged. **Not verified.** | `/post-merge`, at merge |
| `qa:ready` | waiting for a person to verify on a deployed build | us, once a human says it is deployed |
| `qa:passed` | verified — now it may be closed | the verifier |
| `qa:failed` | still broken; back to `/triage-issue` | the verifier |
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
- **This project (D-178):** on the owner's instruction, a bug whose fix the owner merged in full is
  closed with `dev:done` and a comment that it is merged and not verified. The verifier's labels and
  a reopen on `qa:failed` stand.

## With QA on, a bug's PR carries no closing keyword

This is what makes the rule above hold instead of being undone one step later. No
`Closes`/`Fixes`/`Resolves #<n>` in a bug's PR body or in any of its commit messages. Write
`Ref #<n>` and say in the body that the issue stays open on purpose.

**Mind the phrasing, then verify it.** GitHub links on any `close`/`fix`/`resolve` immediately
followed by an issue reference, **whatever the surrounding sentence says** — so
*"please do not close #12"* creates the very link it warns against. Write
**"please leave #12 open"**.

Then check rather than assume:

```bash
gh pr view <pr> --json closingIssuesReferences   # must name no bug
```

A grep over the body first is fine — `(?i)\b(clos|fix|resolv)[a-z]*\s*:?\s*#[0-9]+` — but
`closingIssuesReferences` is the **authority**: a body can read clean while the link survives
from an earlier revision.

**Any PR naming a bug's number can close it** — a docs PR, an unrelated refactor, a comment
quoting the issue. It does not need the `bug` label itself. That is why the check lives in
`/pre-merge` and runs on **every** PR, whatever its branch prefix.
