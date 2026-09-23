---
name: close-wave
description: Use when a planned wave's code is written and committed on its wave/m<N>-w<W> branch, before anything else happens to it. Dispatches Code-Reviewer and then Tester as two separate fresh-eyes subagents, files what the wave did not fix, fills the wave-close checklist, runs make wave-check and the gate, and opens the wave's draft PR.
---

1. All of the wave's work is committed on `wave/m<N>-w<W>`. Take the range once and pass it to
   both reviewers: `git fetch origin <base> && git merge-base origin/<base> HEAD` → `<start>`,
   `git rev-parse HEAD` → `<end>`. Read the wave's risk tier and REQ-IDs from
   `docs/plans/m<N>-plan.md`.
2. **Code-Reviewer, as its own subagent** (`.claude/agents/Code-Reviewer.md`, subagent type
   `code-reviewer`). Give it the plan path, the range `<start>..<end>`, the risk tier, and the
   output path `docs/reviews/m<N>-wave-<W>-review.md`. You are the author: you do not review,
   and you do not edit its verdict. Its verdict declares `**Independent:** yes`: the reviewer
   wrote none of the wave's code.
3. Verdict **BLOCKING** → fix on the same branch, commit, then dispatch a **new** Code-Reviewer on
   the new range. Never re-use the first one; it has seen its own findings. **The third BLOCKING
   verdict on the same finding ends the loop** (`.agents/rules/practices.md`, "Three attempts,
   then stop"): take that slice out of the wave, file it as a `bug`, and close the wave on the rest.
4. **Tester, as a separate subagent** (`.claude/agents/Tester.md`, subagent type `tester`) —
   never the same one as step 2. Same range and plan; output
   `docs/reviews/m<N>-wave-<W>-tester.md`. BLOCKING → fix, commit, new Tester — the same
   three-verdict limit as step 3.
5. HIGH wave: also a security pass on the slice (`.claude/agents/Security-Reviewer.md`), recorded
   in checklist row 4.
6. **Every finding the wave does not fix leaves it as an issue.** Go through each id in both
   verdicts' MINOR, K.9 and queued-risk sections (`**M1**`, `**K1**`, `**R1**`):
   - fix it now on this branch → its disposition is `fixed <sha>`; nothing is filed;
   - otherwise `/file-issue` it — a defect as `bug` with one `severity:*`, an improvement as
     `enhancement` → its disposition is `#<n>`;
   - the reviewer is wrong → `refused — <why>`, in a sentence.
   A BLOCKING finding fixed before the wave closes is not filed: an issue for code that never
   merged is noise. Then `/triage-issue` each issue this wave filed, so none reaches the queue
   without a verdict.
7. Copy `docs/wave-checklist.template.md` to `docs/plans/m<N>-wave-<W>-close.md` and fill it —
   every row cites evidence from THIS wave's range. `make wave-check FILE=docs/plans/m<N>-wave-<W>-close.md`
   must PASS. It refuses a close unless both verdict files exist, neither is BLOCKING, and each
   declares `**Independent:** yes`. If no subagent could review and the author did, WAIVE row 3
   and add a row for the wave to `docs/control-events.csv`: that is the only author review it accepts.
   The findings table holds one row per id from step 6; `make wave-check` refuses a close that
   leaves one out.
8. `make gate` green. Add the checklist and both reviews by path, commit, push the branch, open
   the wave's **draft** PR listing the issues it resolves (from the plan) and, on a line of
   their own, the issues it filed (`Filed: #12, #13` — never after a closing keyword: they stay
   open). Run `/pre-merge`.
9. Comment the PR link on each of those issues. A human marks it ready and merges; after the
   merge, `/post-merge`.
