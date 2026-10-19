# Run — night-351

Mode: light
Started: 2026-10-19
Ended: open
Integration branch: `integration/run-night-351` · PR: #357
Plan PR: #356
Rulings: D-212

The queue in order (D-212): #351's draft (#352) with its next step, the named non-search kinds, kept only if the measurement says so; #348; #354; #353 once its example pool is relabelled; #355, whose set is written tonight and judges only on macOS 27. Questions the run meets that are reversible and outside a ⛔ zone take their most conservative answer in `docs/plans/assumptions-night-351.md`.

## Milestones, in order

| # | Milestone | Base | Plan | Status |
|---|---|---|---|---|
| 1 | queue | 37cf7e1 | issues | running |

## Waves

| Wave | Branch | PR | Close record | Status |
|---|---|---|---|---|
| issue-351 | enhancement/issue-351-apple-intelligence | #352 | none | stacked |
| issue-348 | fix/issue-348-smoke-short-source | #358 | none | stacked |
| issue-354 | enhancement/issue-354-prewarm | none | none | running |
| issue-353 | enhancement/issue-353-retrieved-examples | none | none | stopped |
| issue-355 | none | none | none | queued |

## Stops

| When | Wave | Class | What the owner decides | Continued on |
|---|---|---|---|---|
| 2026-10-20 | issue-353 | control-change | Whether the client may order the example pool by similarity to the typed question (our own labelled questions, never a model, a score or an answer): an exemption in Ruling A's two pins, `SORTING_PERMITTED` and the compiled client-decls gate, which are controls the agent does not widen. Measured on m24 the nearest 8 gave 152 of 173 against 139 (p = 0.015; #353's comment). The red step is commit `aa7b941` on the local branch (the pre-push gate refuses a red test); the green step is `build/night-351/issue-353-green.patch` in the main clone | #354 |

## For the owner

The run is in progress.
