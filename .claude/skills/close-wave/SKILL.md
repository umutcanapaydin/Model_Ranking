---
name: close-wave
description: Use when a planned wave's code is written and committed on its wave/m<N>-w<W> branch, before anything else happens to it. Dispatches Code-Reviewer and then Tester as two separate fresh-eyes subagents, fills the wave-close checklist, runs make wave-check and the gate, and opens the wave's draft PR.
---

1. All of the wave's work is committed on `wave/m<N>-w<W>`. Take the range once and pass it to
   both reviewers: `git fetch origin <base> && git merge-base origin/<base> HEAD` → `<start>`,
   `git rev-parse HEAD` → `<end>`. Read the wave's risk tier and REQ-IDs from
   `docs/plans/m<N>-plan.md`.
2. **Code-Reviewer, as its own subagent** (`.claude/agents/Code-Reviewer.md`, subagent type
   `code-reviewer`). Give it the plan path, the range `<start>..<end>`, the risk tier, and the
   output path `docs/reviews/m<N>-wave-<W>-review.md`. You are the author: you do not review,
   and you do not edit its verdict.
3. Verdict **BLOCKING** → fix on the same branch, commit, then dispatch a **new** Code-Reviewer on
   the new range. Never re-use the first one; it has seen its own findings.
4. **Tester, as a separate subagent** (`.claude/agents/Tester.md`, subagent type `tester`) —
   never the same one as step 2. Same range and plan; output
   `docs/reviews/m<N>-wave-<W>-tester.md`. BLOCKING → fix, commit, new Tester.
5. HIGH wave: also a security pass on the slice (`.claude/agents/Security-Reviewer.md`), recorded
   in checklist row 4.
6. Copy `docs/wave-checklist.template.md` to `docs/plans/m<N>-wave-<W>-close.md` and fill it —
   every row cites evidence from THIS wave's range. `make wave-check FILE=docs/plans/m<N>-wave-<W>-close.md`
   must PASS: it refuses a close unless both verdict files exist and neither is BLOCKING.
7. `make gate` green. Add the checklist and both reviews by path, commit, push the branch, open
   the wave's **draft** PR listing the issues it resolves (from the plan). Run `/pre-merge`.
8. Comment the PR link on each of those issues. A human marks it ready and merges; after the
   merge, `/post-merge`.
