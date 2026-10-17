---
name: pre-merge
description: Use before handing a branch or PR to a human to merge, before marking work ready for review, and before saying a slice or milestone is closed. The last thing that runs while the change is still yours. Checks the base, checks the PR cannot close a bug, and checks the evidence a reviewer is owed.
---

Runs on any agent branch — `wave/*`, `plan/*`, `fix/issue-*`, `enhancement/*`, `integration/*` —
that already has a draft PR. The human merging
cannot read every line; this is what makes that safe, and it is the last moment anyone is looking.

Read `.agents/rules/issues.md` first.

## 1 · The base — merge it in, never rebase

Read the PR's **real** base. Do not assume the default branch; a PR may target an integration
branch, and comparing against the wrong one reports commits the merge would never bring in.

```bash
gh pr view <pr> --json baseRefName
git fetch origin <base>          # a stale remote-tracking ref understates how far behind you are
git rev-list --left-right --count origin/<base>...HEAD
```

If the branch is behind: warn, show `git log --oneline HEAD..origin/<base>`, and **offer** to
merge the base in — never silently. On approval, merge it, **re-run the gates because the base
moved**, and push so CI runs against the latest base. Inside a run (`/plan-run`) nobody is there to
answer and the base is the run's own integration branch: merge it in, re-run the gates, push.

**Merge the base in. Never rebase, never force-push.** A rebase rewrites commits a reviewer may
already have read.

## 1a · The integration lane (`integration/<name>`)

Only when the owner has said not to wait for merges (AGENTS.md §3). The open drafts are merged
into one `integration/<name>` branch — each merged in, never rebased — and their conflicts are
resolved there, once; a stacked branch is never edited to fit the stack. The integration PR is a
draft like any other. Its body names the PRs it carries in merge order, what the merge resolved,
and what only the combination broke. What this section owes on it:

- the stacked PRs keep the base they were opened against; the integration PR targets the default
  branch, and its `Closes` lines are the union of the stacked PRs' lines (§2 applies to the union);
- `make review-need RANGE=$(git merge-base origin/<default> HEAD)..HEAD` on the whole stack — the
  reviews are owed once, on the integration PR (§5): a stacked PR's own verdict covers its branch,
  not the combination;
- the body asks for a **merge commit**: a squash leaves every stacked PR unmerged, and
  `/post-merge` then has nothing to close;
- `make gate` on the integration branch (§9), not only on each stacked one;
- a run (`/plan-run`) is this lane with the name `integration/run-<name>`: its record
  `docs/plans/run-<name>.md` passes `make run-check FILE=docs/plans/run-<name>.md`, its `Ended:`
  line is no longer `open`, and the body's merge list is the run file's `stacked` rows in order —
  a `stopped` wave's PR is named apart, as open work for the owner.

## 2 · With QA verification on, the PR must not be able to close a bug

**Only when the brief says `QA verification: on`.** Off — the default — a bug closes when its fix
merges and its red→green test is the verification: `Closes #<n>` is right, and this section does
not apply. In the field neither project had a separate verifier; the agent set `qa:passed` itself.

When it is on, this applies to **every** PR — whatever its branch prefix, whatever its labels. A
docs PR, an unrelated refactor, a comment quoting the issue: any PR naming a bug's number can close it.

```bash
gh pr view <pr> --json closingIssuesReferences   # must name no bug (an enhancement's Closes #n is right)
gh issue view <n> --json labels                  # for each link, is it a `bug`?
```

If any link carries `bug`, rewrite the body and **re-read the field until it is empty**. A body
can read clean while the link survives from an earlier revision — the field is the authority, the
body is not.

Mind the phrasing: GitHub links on `close`/`fix`/`resolve` immediately followed by an issue
reference **whatever the surrounding sentence says**, so *"please do not close #12"* creates the
link it warns against. Write *"please leave #12 open"*.

**Fail closed** — do not hand the PR over while a `bug` is still linked.

## 3 · Every acceptance criterion has a citing test

Not "the suite is green" — a named test at `file:line` for each criterion the change touched. A
criterion with no citing test is BLOCKING, and this is the highest-recurrence rule in the corpus.

If the change fixes a reported symptom, the history must show it reproduced RED first: a `test:`
commit before the `fix:` commit. Check the order; do not take it on trust.

## 4 · Break it and watch the test go red

For each load-bearing behaviour the change touches: break it on purpose, confirm a test fails,
revert **in place** — byte-identical, never `git checkout` on uncommitted work.

A behaviour whose removal keeps the suite green is untested, whatever the coverage says. One
project removed a release-slot path and a tenant check and stayed green on both.

## 5 · Fresh eyes, and not the author's

Reviewed by something that did not write the code — strictly stronger dispatched to a subagent than
performed by the author in the same context. Thirty BLOCKING findings across three rounds in one
project, none found by the author. What is owed depends on the branch:

What is owed is what `make review-need` computes for the branch — its last line is in the PR body;
recompute it and compare:
- `wave/*` (heavy) — the Code-Reviewer's verdict; on the plan's last wave the milestone
  Security-Reviewer's (`m<N>-security.md`) and the milestone Tester's. `make wave-check` refuses the
  close without them.
- `fix/issue-<n>-*` — `none`: nothing. `code-reviewer` (heavy only): `docs/reviews/fix-issue-<n>-review.md`.
  `security` (light only; heavy runs security once per milestone): `docs/reviews/fix-issue-<n>-security.md`.
  `code-reviewer+security` (light): the security verdict alone. Each PASS or MINOR, each
  `**Independent:** yes`, and each unfixed finding filed or refused. No gate reads these files: you do.
- `enhancement/*` (light) — `docs/reviews/enhancement-<slug>-security.md` when the branch needs security; no Code-Reviewer, no
  Tester per enhancement — the milestone Tester runs once before the next release (§B.0).
- `plan/*` — no code, so no review is owed. The owner's merge is the plan's approval.
- `integration/*` — one delta review of the stack, on the whole range (1a): the security verdict
  when the line says so (`docs/reviews/integration-<name>-security.md`), the Code-Reviewer's in
  heavy mode (`docs/reviews/integration-<name>-review.md`). A BLOCKING finding is fixed by a commit
  on the integration branch itself and re-verified by the same reviewer. The stacked PRs' verdicts
  stay as they are and are not re-run.
- a `wave/*` branch inside a run was cut from the integration branch, so its range is
  `RANGE=$(git merge-base integration/run-<name> HEAD)..HEAD`, not the merge-base with the default
  branch; its GitHub diff against the default branch is cumulative, and the PR body says which
  commits are its own.

The declaration is not a proof. No file can show which session wrote the code, so a false `yes` is
found by a reader, not by the gate.

## 6 · What did NOT run is written down

Every check that legitimately did not run gets a row with a reason. **A skip is not a pass** — a
control that could not run reports NOT RUNNABLE and fails; it never reports success, and you do
not convert a refusing check into a skipped one to get a green run.

A bypass under pressure is a ledger row, not a silence. The same control bypassed three times is
a review of the control.

## 7 · Done Evidence

Files changed · tests run and their outcomes · assumptions · decisions recorded · risks queued.
Every PASS cites `file:line`. **No claim without an artefact behind it** — no PASS, badge or
"verified" unless a named, re-runnable command produces it.

## 8 · The PR itself

- **Draft. Always.** You do not mark it ready and you do not merge it.
- No force-push, no `--amend` on anything pushed, no `--no-verify` — a hook you skipped is a gate
  you removed.
- The body is a **live document**: it describes what the change is, not how it got there. When
  the work evolves, rewrite the body in place. Never a history log, no "update: …" notes.
- No AI attribution anywhere.
- `.github/workflows/**` untouched. If CI must change, propose the diff and stop.
- **Apply no lifecycle label here.** At draft-PR time neither `dev:done` nor `qa:ready` is true.

## 9 · Gates green, by name

`make gate` — the full gate, including the network legs (`deps`, `slopsquat`) that the post-edit
`make check-fast` leaves out, with `make check` in order. Run it and name it. "Checks pass" is not
evidence.
