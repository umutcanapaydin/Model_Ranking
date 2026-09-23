---
name: pre-merge
description: Use before handing a branch or PR to a human to merge, before marking work ready for review, and before saying a slice or milestone is closed. The last thing that runs while the change is still yours. Checks the base, checks the PR cannot close a bug, and checks the evidence a reviewer is owed.
---

Runs on any agent branch — `wave/*`, `plan/*`, `fix/issue-*`, `enhancement/*` — that already has
a draft PR. The human merging
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
moved**, and push so CI runs against the latest base.

**Merge the base in. Never rebase, never force-push.** A rebase rewrites commits a reviewer may
already have read.

## 2 · The PR must not be able to close a bug

This applies to **every** PR — whatever its branch prefix, whatever its labels. A docs PR, an
unrelated refactor, a comment quoting the issue: any PR naming a bug's number can close it.

```bash
gh pr view <pr> --json closingIssuesReferences   # must be an empty list
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

- `wave/*` — both verdicts, Code-Reviewer then Tester, each declaring `**Independent:** yes`;
  `make wave-check` refuses the close without them.
- `fix/issue-<n>-*` — the Tester alone: `docs/reviews/fix-issue-<n>-tester.md` exists, its
  `## Verdict` is PASS or MINOR, it declares `**Independent:** yes`, and the history shows a new
  Tester after any BLOCKING one. No gate reads this file: you do.
- `enhancement/*` — the `/repo-review` of the whole branch, each of its findings fixed on the
  branch or filed. It is the author's review, not fresh eyes: the PR body says so.
- `plan/*` — no code, so no review is owed. The owner's merge is the plan's approval.

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
