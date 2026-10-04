---
record_type: plan
id: m18-wave-2-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W2 plan — screen quality

**Working plan for `wave/m18-w2`**, deleted before merge. Milestone plan: `docs/plans/m18-plan.md` §2 W2,
with the 2026-10-04 amendment that moved #74 and #56 here.

**Risk: HIGH.** The plan says MED. The wave touches `ios/ModelRanking/Engine/EngineClient.swift` (#56),
which is a security glob, and it adds a test hook to the app. By D-172 there is no security pass on
the slice; the Tester's fault injection is owed.

**Order.** The owner lifted the simulator restriction on 2026-10-04 ("the restriction of simulator
has been discarded, you can test whenever you need"). The screen is driven for real in this wave.

## Issues

| Issue | What |
|---|---|
| #69 | A committed UI test target |
| #63 | The owner's 14 UI findings from `cce2ced`, reproduced on today's screen |
| #67 | Disclosures held as data |
| #72 | A stale board said on the combined list |
| #70 | The plan computed when its inputs change |
| #74 | `combine` in O(n log n) |
| #56 | The phone's read capped while it streams |
| #78 | Accessibility: a reader filter, or stop serving it |
| #95 | The local-network permission text in Turkish |
| #96 | The failure screen's sentences in both languages |

## Design (D-175, written in P0)

1. **A UI test target, `ModelRankingUITests`,** in `ios/UITests/`, folder-synchronised. Its bundle id
   lives in an xcconfig, because the project carries none (#93's rule).
2. **It runs locally, never in CI.** `make ui-test` does three things:
   - it starts an engine on 127.0.0.1:8090 from a copy of the served artifact;
   - it builds the app for that address (`ENGINE_URL` on the command line, as `ios/app.sh` does);
   - it runs the target on the iPhone 17 Pro simulator, then stops the engine.

   It is not a `check-fast` or `gate` leg: it needs a simulator and a built artifact, and takes
   minutes. A wave that changes a screen cites a `make ui-test` run in its close record.
3. **Routing is scripted in UI tests,** so a screen path does not depend on the on-device model's
   mood. A Debug-only launch argument gives the model tier a fixed table, from question to surface
   and refinements. Its answers still pass through `ModelOutputBoundary`, so nothing a UI test feeds
   in can reach a choice that the boundary would refuse. Release builds carry no such hook, and a
   test holds that. The real model's reading is measured by the probe (W3), not by UI tests.
4. **Product choices in #63 and #78.** These are decided per finding once it is reproduced, and each
   decision is recorded in D-175 as it is made.

## Phases (each red first where it changes behaviour)

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan and D-175 committed |
| P1, the UI test target | #69 | `make ui-test` drives: ask, the combined list, removing and restoring a chip, the detail, "Change", the failure screen. Each of M17-W5's two simulator-found defects fails a test when re-introduced |
| P2, reproduce #63 | #63 | Each of the 14 findings is checked on today's screen, with a screenshot from the UI target. Each is listed as standing or gone |
| P3, fix what stands | #63, #95, #96 | Each standing finding is fixed with a test, or recorded as a decision not to |
| P4, disclosures as data | #67, #72 | The combined list carries its disclosures as fields of the plan, including a stale board. A path that skips one fails a test on the plan |
| P5, cost and robustness | #70, #74, #56 | The plan is computed in state, not in `body`. `combine` passes the property oracle and is O(n log n). A response is cut off at its route's byte ceiling while it streams |
| P6, accessibility | #78 | Either a reader filter, "models I can use", held by a UI test, or the attribute stops being served; recorded in D-175 |

## K.8 contracts (grep at `d080060`)

```
ios/ModelRanking/Engine/Combine.swift:47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
ios/ModelRanking/Engine/AnswerPlan.swift:86:func answerPlan(
ios/ModelRanking/Engine/Router.swift:602:struct TieredRouter {
ios/ModelRanking/Engine/EngineClient.swift:165:    static let localDefault = engineURL(from: Bundle.main.object(forInfoDictionaryKey: "EngineURL") as? String)
```

`/v1` changes no field and no route unless an ADR written in this wave says so.

## The one alternative

**Driving the real on-device model in UI tests.** It is more realistic, but it is flaky by nature: the
model's reading of the same question varies between runs (M17's probes). The screen's paths are
tested with scripted routing, and the model's reading is measured where measurement belongs: the
probe in W3.
