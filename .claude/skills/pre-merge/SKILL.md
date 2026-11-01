---
name: pre-merge
description: Use before handing a branch or PR to a human to merge, before marking work ready for review, and before saying a slice or milestone is closed.
---

Runs on any agent branch — `wave/*`, `plan/*`, `fix/issue-*`, `enhancement/*`, `integration/*`,
`release/*`, `setup/*`, `upgrade/*`, `close/*` — that already has a draft PR. The human merging
cannot read every line; this is what makes that safe.

`.agents/rules/issues.md` (read at `/start-session`; open it again only after a compaction or in a new session).

## 1 · The base — merge it in, never rebase

Read the PR's **real** base, never assume the default branch: comparing against the wrong one
reports commits the merge would never bring in. Inside a
run the base is `integration/run-<name>`, whatever `baseRefName` says: a wave's draft PR targets the
default branch, but the wave was cut from, and merges into, the integration branch.

```bash
gh pr view <pr> --json baseRefName
git fetch origin <base>          # a stale remote-tracking ref understates how far behind you are
git rev-list --left-right --count origin/<base>...HEAD
```

If the branch is behind: warn, show `git log --oneline HEAD..origin/<base>`, and **offer** to
merge the base in — never silently. On approval, merge it, **re-run the gates because the base
moved**, and push so CI runs against the latest base. Inside a run (`/plan-run`) nobody is there to
answer and the base is the run's own integration branch: merge it in, re-run the gates, push.

**Merge the base in. Never rebase, never force-push:** a rebase rewrites commits a reviewer may
have read.

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
not apply. The rule and its reasons: `.agents/rules/issues-qa.md`.

When it is on, this applies to **every** PR, whatever its branch or labels: any PR naming a bug's
number can close it.

```bash
gh pr view <pr> --json closingIssuesReferences   # must name no bug (an enhancement's Closes #n is right)
gh issue view <n> --json labels                  # for each link, is it a `bug`?
```

If any link carries `bug`, rewrite the body and **re-read the field until it is empty** — a link
can survive from an earlier revision of a body that reads clean.

Mind the phrasing: GitHub links on `close`/`fix`/`resolve` immediately followed by an issue
reference **whatever the surrounding sentence says**, so *"please do not close #12"* creates the
link it warns against. Write *"please leave #12 open"*.

**Fail closed** — do not hand the PR over while a `bug` is still linked.

## 2a · The commits close issues too — always, whatever the brief says

GitHub closes an issue that a closing keyword directly precedes in a **commit message** once that
commit reaches the default branch, whatever the PR body says, and `closingIssuesReferences` (§2)
reads only the body and the manual links. `fix: #194's model names ...` closed #194 with that
field empty, and #222 the same way, seconds after the merge (#255).

```bash
make closing-keywords RANGE=$(git merge-base origin/<base> HEAD)..HEAD   # <base>: the PR's real base (§1)
```

It reads every commit the merge brings in, merge commits included, with GitHub's keyword set, and
its last line is the answer: `closing-keywords: none`, or each issue the merge would close. Every
issue it lists must be one the PR means to close — its own `Closes #<n>` lines, or for an
integration PR the union of the stacked PRs' lines (§1a) — and with QA verification on, none may
be a `bug` (§2). One that is not: the commits are pushed and are not rewritten (§8), so the PR body
names it, for the human who merges, as an issue the merge closes by mistake and that is reopened
after it. A line `closing-keywords: ERROR` means the range was empty or unreadable: it graded
nothing, so fix the range and run it again — never read it as clean.

Write your own commit messages so that this stays quiet: *"for #12"*, never *"fix #12"* or
*"fix: #12's ..."*.

## 3 · Every acceptance criterion has a citing test

Not "the suite is green" — a named test at `file:line` for each criterion the change touched. A
criterion with no citing test is BLOCKING.

If the change fixes a reported symptom, the history must show it reproduced RED first: a `test:`
commit before the `fix:` commit. Check the order; do not take it on trust.

## 4 · The proof the test is real

A behaviour whose removal keeps the suite green is untested, whatever the coverage says. Who proves
it (owner's ruling, 2026-10-17): in light mode, the red-test commit before the fix (`/fix-issue`
step 3); in heavy mode, the milestone Tester's fault injection on the plan's last wave — the author
does not break and revert every PR's behaviours by hand. When you do break something on purpose,
revert it **in place** — byte-identical, never `git checkout` on uncommitted work.

## 5 · Fresh eyes, and not the author's

Reviewed by something that did not write the code. What is owed is what `make review-need`
computes for the branch — its last line is in the PR body; recompute it and compare:
- `wave/*` (heavy) — the Code-Reviewer's verdict; on the plan's last wave the milestone
  Security-Reviewer's (`m<N>-security.md`) and the milestone Tester's. `make wave-check` refuses the
  close without them.
- `fix/issue-<n>-*` — `none`: nothing. `code-reviewer` (heavy only): `docs/reviews/fix-issue-<n>-review.md`.
  `security` (light only; heavy runs security once per milestone): `docs/reviews/fix-issue-<n>-security.md`.
- `enhancement/*` (light) — `docs/reviews/enhancement-<slug>-security.md` when the branch needs security; no Code-Reviewer, no
  Tester per enhancement — the milestone Tester runs once before the next release (§B.0).
- both: `make findings-check closing-keywords` (in a run, `RANGE=` as below): each verdict
  PASS or MINOR and independent, each finding id a row of the body's findings table (`/fix-issue` step 6).
- `plan/*` — no code, so no review is owed. The owner's merge is the plan's approval.
- `release/*` — the release verdicts it carries are the review; nothing else is owed. The owner's merge
  is the release's signature.
- `integration/*` — one delta review of the stack, on the whole range (1a): the security verdict
  when the line says so (`docs/reviews/integration-<name>-security.md`), the Code-Reviewer's in
  heavy mode (`docs/reviews/integration-<name>-review.md`). A BLOCKING finding is fixed by a commit
  on the integration branch itself and re-verified by the same reviewer. The stacked PRs' verdicts
  stay as they are and are not re-run.
- a `wave/*`, `fix/*` or `enhancement/*` branch inside a run was cut from the integration branch, so its range is
  `RANGE=$(git merge-base integration/run-<name> HEAD)..HEAD`, not the merge-base with the default
  branch; its GitHub diff against the default branch is cumulative, and the PR body says which
  commits are its own.

`**Independent:** yes` is a declaration, not a proof: no file shows which session wrote the code,
so a false one is found by a reader, not by the gate.

## 6 · What did NOT run is written down

Every check that legitimately did not run gets a row with a reason. **A skip is not a pass** — a
control that could not run reports NOT RUNNABLE and fails; never convert a refusing check into a
skipped one to get a green run. A bypass under pressure is a row in `docs/control-events.csv`; the
same control bypassed three times is a review of the control.

## 7 · Done Evidence

`AGENTS.md` §7. **No claim without an artefact behind it** — no PASS, badge or "verified" unless a
named, re-runnable command produces it.

## 8 · The PR itself

- **Draft, always** — and everything else `AGENTS.md` §3, "Git authority", forbids: no force-push,
  no `--amend` on anything pushed, no `--no-verify`, no AI attribution, `.github/workflows/**`
  untouched (propose the diff and stop).
- The body is a **live document** (`.agents/rules/practices.md`): what the change is, rewritten in
  place as the work evolves; no "update: …" notes.
- `make closing-keywords` (fix, enhancement: ran in §5; in a run, `RANGE=` as §5): a commit message's
  `fix: #12` closes #12 on the merge, unlinked, so each keyword must name an issue the body closes.
- **The process-log entry** — `/fix-issue` step 7 and `/close-wave` step 8 commit it before their gate;
  any other branch: before the push, append this PR's entry to `docs/process-log.md` on
  this branch: `## <date> · <branch> — <what it did>`, 3-10 lines, a `Lesson:` line (the file's
  comment has the format). One per PR; never a number, so parallel branches do not collide.
- **For the owner.** Every step the change leaves to a human — a workflow change (`make ci-diff`), a
  re-pin, a secret, a tag — is one row in `docs/owner-actions.md` (what, why, the one command) and one
  line under "For the owner" in the body. A file you may not edit (a workflow, the guard): its new content
  under `build/owner-bundle/src/<path>`, then `make owner-bundle` prints the row's command; on `review: owed`
  the Security-Reviewer reads the patch first, its verdict naming `**Reviewed patch:** <sha256>`. Nothing reaches the owner as loose text in a chat.
  The section ends with the merge the owner makes: `gh pr checks <n> --watch --fail-fast && gh pr ready <n> && gh pr merge <n> --merge`
  (it waits for CI; no Actions: drop `gh pr checks`; a stacked PR has none).
- **Apply no lifecycle label here.** At draft-PR time neither `dev:done` nor `qa:ready` is true.

## 9 · Gates green, by name

`make gate` — the full gate, including the network legs (`deps`, `slopsquat`) that the post-edit
`make check-fast` leaves out, with `make check` in order. Run it and name it; "checks pass" is not
evidence. **Once per tree:** when it passes on a clean tree it writes the gate stamp, and `make gate-ok`
then says PASS while HEAD is still that commit — cite that line instead of running the gate again; the
push's pre-push hook reads the same stamp. HEAD moved (the base merged in, a fix committed): run
`make gate` again. Never write the stamp by hand (the guards refuse it).
