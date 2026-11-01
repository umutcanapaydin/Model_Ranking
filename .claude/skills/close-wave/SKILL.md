---
name: close-wave
description: Use in HEAVY mode when a planned wave's code is written and committed on its wave/m<N>-w<W> branch, before anything else happens to it — the wave's reviews, its checklist and its draft PR.
---

**Heavy mode only.** `make mode` prints `light` → stop: a light project has no waves; its work goes
`/file-issue` → `/triage-issue` → `/fix-issue`, and its milestone Tester runs before a release, not
here (`docs/closure-checklist.md` §B.0 and §E.1).

**A wave is its container issue.** `/plan-milestone` opened one issue per wave; the wave's plan, its
tasks and the child issues that joined it live in that issue's body. The wave's PR resolves the
container and every child it fixed. A plan written before containers existed (a project upgraded
mid-milestone) has none: the plan file stands in for the container, and the wave's issues are the
ones the plan lists for it.

**Nobody edits the tree while a reviewer runs** — not the author, not another reviewer. The
Code-Reviewer and, on the last wave, the Security-Reviewer only read and write their own verdict file:
dispatch them together. The Tester writes tests and plants faults, so it runs alone, after both have
returned and their fixes are committed. Two editing reviewers in one checkout at once collided in both
field projects; one left a planted fault live in the product.

1. All of the wave's work is committed on `wave/m<N>-w<W>`. Take the range once:
   `git fetch origin <base> && git merge-base origin/<base> HEAD` → `<start>`, `git rev-parse HEAD`
   → `<end>` — inside a run (`/plan-run`) `<base>` is `integration/run-<name>`, the branch the wave
   was cut from, not the default branch. Read the wave's risk tier and REQ-IDs from the container issue and
   `docs/plans/m<N>-plan.md`. Run `make review-need RANGE=<start>..<end>` and keep its last line.
2. **Code-Reviewer, as its own subagent** (`.claude/agents/Code-Reviewer.md`, subagent type
   `code-reviewer`), on every wave. Give it the plan and container issue, the range, the risk tier,
   and the output path `docs/reviews/m<N>-wave-<W>-review.md`. You are the author: you do not review,
   and you do not edit its verdict. It declares `**Independent:** yes`. On the plan's last wave it also reads the **whole milestone** (from the commit the plan merged at;
   in a run, the milestone's `Base` sha) for what no single wave could see — one fact changed in one
   wave and not another, documentation drift, a rule applied in one wave and not the next — under
   `## Across the milestone` in the same verdict. That is the milestone's cross-wave review; there
   is no separate `/repo-review` after the merge.
3. Verdict **BLOCKING** → fix on the same branch, commit, and send the fix diff to **the same
   reviewer** (SendMessage) to re-verify its own BLOCKING items, recorded in the same file: the reviewer rewrites
   that file's `## Verdict` line to the new verdict and appends the round below it — `make wave-check` and
   the deploy gate read that line, so a PASS appended under a BLOCKING one stays BLOCKING. A new
   reviewer only for a BLOCKING on a HIGH path, or when the owner asks — or when the reviewer is gone
   (a compaction, a new session): then a fresh subagent of the same profile re-verifies the recorded
   BLOCKING items, and it continues the round count rather than restarting it. New findings in a re-review
   are MINOR unless they are exploitable or break an acceptance criterion: they go to step 6, they do
   not reopen the loop. **The third BLOCKING verdict on the same finding ends it**
   (`.agents/rules/practices.md`, "Three attempts, then stop"), and ending means: no fourth round,
   no new reviewer, no one more try. Revert that slice in place on this branch (byte-identical,
   never `git checkout`), `/file-issue` it as a `bug` whose body carries the three verdicts and
   what each round changed, write the issue on the footprint's `Stopped at three attempts:` line,
   and close the wave on the rest. A finding the author still disputes after three rounds is not
   refused by the author: its triage verdict is `work-issue`, and the owner's answer is an ADR
   (`/log-decision`) or a `docs/refusals.md` row.
4. **The plan's last wave only: the milestone Security-Reviewer** (`.claude/agents/Security-Reviewer.md`, subagent type
   `security-reviewer`),
   dispatched together with the Code-Reviewer (both only read), on the whole milestone — the same range
   as step 5 — with the security
   signals `make review-need` prints for that range (declared HIGH paths, sensitive path names, a new
   parser of untrusted input) as its starting list, and the four gate lines (`make secrets`, `deps`, `slopsquat`, `conformance`) from the last `make gate`. Output `docs/reviews/m<N>-security.md`; BLOCKING →
   fix on this branch, the same reviewer re-verifies (the reviewer rewrites the file's `## Verdict` line to the new verdict and appends the round below
   it: the gates read that line). Heavy mode runs no per-wave security review (the
   owner's ruling of 2026-10-16): `make review-need` prints a wave's signals and routes them here, and
   `make wave-check` requires this verdict on the last wave. A HIGH-path finding that cannot wait for
   the milestone's end is an Escalate-NOW event (AGENTS.md §3), not a reason to skip this review.
5. **The plan's last wave only: the milestone Tester** (`.claude/agents/Tester.md`, subagent type
   `tester`), after the reviews above, on the whole milestone — from the previous milestone's Tester head (`docs/reviews/m<N-1>-tester.md`, its `**Reviewed head:**`;
   the first milestone: the commit the plan merged at; in a run: the milestone's `Base` sha) to `<end>`,
   so a fix merged between milestones falls in one — with the plan's
   acceptance criteria. Output `docs/reviews/m<N>-tester.md` with its `**Reviewed head:**` — the branch head after the last
   fix it verified, its own new tests included, not step 1's `<end>`, which those commits move past (the
   deploy gate reads it). BLOCKING →
   fix on this branch; the same Tester re-verifies its own items (the reviewer rewrites the file's `## Verdict` line to the new verdict and appends the round below
   it: the gates read that line). No per-wave Tester: it was the
   costliest review per real defect in the field. Then, when the Tester's commits are code to the deploy
   gate (a test is, unless the brief names its `Security-invariant tests:` and it is not one of them), send
   them to the same Security-Reviewer (SendMessage) for a delta read; it moves its
   `**Reviewed head:**` to the final head, so its verdict is current at the release.
6. **Every finding the wave does not fix leaves it as an issue.** Go through each id in the
   verdicts' MINOR, K.9 and queued-risk sections (`**M1**`, `**K1**`, `**R1**`):
   - fix it now on this branch → its disposition is `fixed <sha>`; nothing is filed;
   - otherwise `/file-issue` it — a defect as `bug` with one `severity:*`, an improvement as
     `enhancement` → its disposition is `#<n>`. Commit the verdict files by path first, and give
     each issue a pointer that never moves: `` `<sha>:docs/reviews/<file>`, <finding> ``, the sha
     of the commit that wrote that round (`git log -1 --format=%h -- docs/reviews/<file>`) — the
     next round renames the file, and a bare path then shows another round's findings (#252);
   - the reviewer is wrong → `refused — <why>`, in a sentence.
   A BLOCKING finding fixed before the wave closes is not filed: an issue for code that never
   merged is noise. Then `/triage-issue` each issue this wave filed.
7. **The plan's last wave only, first: the milestone closes here, on this branch, before its PR** (inside
   a run, on the integration branch after this wave stacks — `/plan-run` §3.2)
   (`docs/closure-checklist.md` §B): Capture (§B.2 — the process-log entry, the ADRs, the dated
   `docs/EXPERIENCE.md` entry, the roadmap snapshot) and, with the Quality Gate on, the closure report
   (§B.1; its sign-off line says `pending` — the owner's merge signs it). They ride on this wave's PR,
   so the owner's merge closes the milestone, and no fix after the close moves a reviewed head.
   Then, every wave: copy `docs/wave-checklist.template.md` to `docs/plans/m<N>-wave-<W>-close.md` and fill it —
   every row cites evidence from THIS wave's range; `Review need:` is step 1's line, and
   `Last wave of the plan:` says yes or no. `make wave-check FILE=docs/plans/m<N>-wave-<W>-close.md`
   must PASS: it requires the Code-Reviewer verdict, and on the last wave the milestone
   Security-Reviewer's and the milestone Tester's — none BLOCKING, each `**Independent:** yes` — and a
   findings-table row for every id from step 6. If no subagent could review and the author did,
   WAIVE row 3 and add a row for the wave to `docs/control-events.csv`.
8. Add the checklist, the reviews and this PR's `docs/process-log.md` entry (`/pre-merge` §8) by path,
   commit, then `make gate` green on that commit — its stamp
   spares the push and `/pre-merge` §9 a second run on the same tree. Push the branch, open the
   wave's **draft** PR: `Closes #<container>` (if the plan has one) and each child it resolves (a `bug` child under
   `QA verification: on` is named `Ref #<n>` instead: it closes when QA passes), and on a line of their own
   the issues it filed (`Filed: #12, #13` — never after a closing keyword: they stay open). Run
   `/pre-merge`.
9. Comment the PR link on the container and its children. A human marks it ready and merges; after
   the merge, `/post-merge`. **Inside a run:** merge the wave into `integration/run-<name>` instead
   (`--no-ff`, conflicts resolved there, never on this branch), `make gate` there, push, mark the
   wave `stacked` in `docs/plans/run-<name>.md` (`make run-check`), and go on to the next wave; on
   the plan's last wave the milestone closes on the integration branch (`/plan-run` §3.2). The
   human merges the integration PR in the morning.
