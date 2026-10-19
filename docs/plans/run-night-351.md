# Run — night-351

Mode: light
Started: 2026-10-19
Ended: 2026-10-20 — stopped at control-change, nothing independent left
Integration branch: `integration/run-night-351` · PR: #357
Plan PR: #356
Rulings: D-212

The queue in order (D-212): #351's draft (#352) with its next step, the named non-search kinds, kept only if the measurement says so; #348; #354; #353 once its example pool is relabelled; #355, whose set is written tonight and judges only on macOS 27. Questions the run meets that are reversible and outside a ⛔ zone take their most conservative answer in `docs/plans/assumptions-night-351.md`.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 37cf7e1 | issues | stopped |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-351 | enhancement/issue-351-apple-intelligence | #352 | none | stacked |
| issue-348 | fix/issue-348-smoke-short-source | #358 | none | stacked |
| issue-354 | enhancement/issue-354-prewarm | #360 | none | stacked |
| issue-353 | enhancement/issue-353-retrieved-examples | none | none | stopped |
| issue-355 | none | none | none | stopped |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-20 | issue-353 | control-change | Whether the client may order the example pool by similarity to the typed question (our own labelled questions, never a model, a score or an answer): an exemption in Ruling A's two pins, `SORTING_PERMITTED` and the compiled client-decls gate, which are controls the agent does not widen. Measured on m24 the nearest 8 gave 152 of 173 against 139 (p = 0.015; #353's comment). The red step is commit `aa7b941` on the local branch (the pre-push gate refuses a red test); the green step is `build/night-351/issue-353-green.patch` in the main clone | #354 |
| 2026-10-20 | issue-355 | environment | Upgrade the Mac to macOS 27 (the row in `docs/owner-actions.md`): m25 is written and sealed (511 rows; its sha256 on #355) and judges once on the OS 27 model, recording the build and `SystemLanguageModel.default.variant` | nothing |

## For the owner

The run ended on 2026-10-20. Three PRs are stacked on #357; two waves stopped, each with one question below. Nothing was deployed and nothing went to TestFlight.

In the morning, in order:
1. **Merge the plan PR #356.** It carries D-212, your four answers.
2. **Merge the integration PR #357 with a merge commit, never a squash.** It carries #352 (#351, with D-213), #358 (#348) and #360 (#354). The delta security verdict is `docs/reviews/integration-run-night-351-security.md` (PASS WITH FINDINGS; its queued risks are #361 and #353's comment). Before merging you may rebuild `advisor.db` in the main clone and re-run the gate (assumption 4).
3. **#353, a ruling:** may the client order the example pool by similarity? The nearest 8 examples raised m24 from 139 to 152 of 173. Yes means an exemption in Ruling A's two pins and the patch `build/night-351/issue-353-green.patch`, re-measured without m22.
4. **#355:** upgrade the Mac to macOS 27 (the row in `docs/owner-actions.md`); m25 then judges once.
5. **After this session ends,** remove the broken work tree `w-up-dry` (the new row in `docs/owner-actions.md`, #359).
