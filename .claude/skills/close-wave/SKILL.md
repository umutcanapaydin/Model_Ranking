---
name: close-wave
description: Use in HEAVY mode when a planned wave's code is written and committed on its wave/m<N>-w<W> branch, before anything else happens to it. Runs the reviews the change needs — a Code-Reviewer always, the Security-Reviewer when make review-need says so, and on the plan's last wave the milestone Tester — files what the wave did not fix, fills the wave-close checklist, runs make wave-check and the gate, and opens the wave's draft PR.
---

**Heavy mode only.** `make mode` prints `light` → stop: a light project has no waves; its work goes
`/file-issue` → `/triage-issue` → `/fix-issue`, and its milestone Tester runs before a release, not
here (`docs/closure-checklist.md` §B.0 and §E.1).

**A wave is its container issue.** `/plan-milestone` opened one issue per wave; the wave's plan, its
tasks and the child issues that joined it live in that issue's body. The wave's PR resolves the
container and every child it fixed. A plan written before containers existed (a project upgraded
mid-milestone) has none: the plan file stands in for the container, and the wave's issues are the
ones the plan lists for it.

**The reviewers run one at a time, and nobody edits the tree while one runs** — not the author, not
another reviewer. Dispatch the next only when the previous has returned and its changes are
committed or reverted. Two reviewers in one checkout at once collided in both field projects; one
left a planted fault live in the product.

1. All of the wave's work is committed on `wave/m<N>-w<W>`. Take the range once:
   `git fetch origin <base> && git merge-base origin/<base> HEAD` → `<start>`, `git rev-parse HEAD`
   → `<end>` — inside a run (`/plan-run`) `<base>` is `integration/run-<name>`, the branch the wave
   was cut from, not the default branch. Read the wave's risk tier and REQ-IDs from the container issue and
   `docs/plans/m<N>-plan.md`. Run `make review-need RANGE=<start>..<end>` and keep its last line.
2. **Code-Reviewer, as its own subagent** (`.claude/agents/Code-Reviewer.md`, subagent type
   `code-reviewer`), on every wave. Give it the plan and container issue, the range, the risk tier,
   and the output path `docs/reviews/m<N>-wave-<W>-review.md`. You are the author: you do not review,
   and you do not edit its verdict. It declares `**Independent:** yes`.
3. Verdict **BLOCKING** → fix on the same branch, commit, and send the fix diff to **the same
   reviewer** (SendMessage) to re-verify its own BLOCKING items, recorded in the same file. A new
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
   (`/log-decision`) or a `docs/refusals.md` row. In the field the loop ran to five and six rounds
   because nothing said what the third one ends with, and a new reviewer per round turned one
   close into ten reviewers and eight and a half hours.
4. **Security-Reviewer, when step 1's line says `security`** (`.claude/agents/Security-Reviewer.md`),
   after the Code-Reviewer: the slice, output `docs/reviews/m<N>-wave-<W>-security.md`. The need is
   computed — declared HIGH paths, sensitive path names, a new parser of untrusted input — and
   `make wave-check` recomputes it from the range, so it cannot be left out by judgment.
5. **The plan's last wave only: the milestone Tester** (`.claude/agents/Tester.md`, subagent type
   `tester`), after the reviews above, on the whole milestone — from the commit the plan merged at
   (in a run: the milestone's `Base` sha in `docs/plans/run-<name>.md`) to `<end>` — with the plan's
   acceptance criteria. Output `docs/reviews/m<N>-tester.md` with its `**Reviewed head:**` (`<end>`;
   the deploy gate reads it). BLOCKING →
   fix on this branch; the same Tester re-verifies its own items. No per-wave Tester: it was the
   costliest review per real defect in the field.
6. **Every finding the wave does not fix leaves it as an issue.** Go through each id in the
   verdicts' MINOR, K.9 and queued-risk sections (`**M1**`, `**K1**`, `**R1**`):
   - fix it now on this branch → its disposition is `fixed <sha>`; nothing is filed;
   - otherwise `/file-issue` it — a defect as `bug` with one `severity:*`, an improvement as
     `enhancement` → its disposition is `#<n>`;
   - the reviewer is wrong → `refused — <why>`, in a sentence.
   A BLOCKING finding fixed before the wave closes is not filed: an issue for code that never
   merged is noise. Then `/triage-issue` each issue this wave filed.
7. Copy `docs/wave-checklist.template.md` to `docs/plans/m<N>-wave-<W>-close.md` and fill it —
   every row cites evidence from THIS wave's range; `Review need:` is step 1's line, and
   `Last wave of the plan:` says yes or no. `make wave-check FILE=docs/plans/m<N>-wave-<W>-close.md`
   must PASS: it requires the Code-Reviewer verdict, the security verdict when the range needs one,
   and the milestone Tester's on the last wave — none BLOCKING, each `**Independent:** yes` — and a
   findings-table row for every id from step 6. If no subagent could review and the author did,
   WAIVE row 3 and add a row for the wave to `docs/control-events.csv`.
8. `make gate` green. Add the checklist and the reviews by path, commit, push the branch, open the
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
