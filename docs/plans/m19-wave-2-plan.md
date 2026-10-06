---
record_type: plan
id: m19-wave-2-plan
status: draft
process_version: v6.6
date: 2026-10-06
---
# M19-W2 plan — the phone's promises, held by what the code does

**Working plan for `wave/m19-w2`**, deleted at the wave's close. The milestone plan
(`docs/plans/m19-plan.md` §2 W2) is the approved scope; the owner merged it on 2026-10-06.

**Risk: HIGH.** `EngineClient.swift`, `StandingsStore.swift`, `src/app/adapter/main.py` and the
client gates are touched, all security globs (`m19-plan.md` §3). By D-172 no security pass runs on
the slice; the milestone closure's security seat reads it, from `docs/security-invariants.md`.

## Issues

| Issue | What | Phase |
|---|---|---|
| #85 | G-1: the privacy sinks hold by spelling, not by what reaches them | P0 spike, P1 |
| #60 | G-2: the arithmetic and sort tripwires match names | P2 |
| #107 | G-3: more ways to make a URL from text, the unapplied `.init` among them | P2 |
| #110 | G-3: text pins and the declaration gate accept code under `#if false` | P2 |
| #144 | The engine session accepts and resends cookies | P3 |
| #132 | The held reading lives in `ContentView.swift`, out of `swift test`'s reach | P3 |
| #138 | Picks carry no model id, so the app merges cards by name, vendor, score and price | P4 |

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | #85 (design) | This plan, and the spike: both G-1 designs (a type that cannot carry the question; a gate on the compiled module) tried on a throwaway `spike-m19-g1` branch against the two M17 mutants, P2 (a refinement relayed onto `/v1/boards` through a static) and P3 (the typed question saved through `StandingsStore`). The design chosen, and why, is a decision record before P1's code |
| P1 | #85 | Each M17 mutant fails a gate in the lane that has the toolchain, shown red on the shipping client with the mutant planted, as a fixture the gate refuses (#51's discipline). INV-66 gets its negative tests and gap G-1 closes |
| P2 | #60, #107, #110 | An aliased position and a second same-named sort each fail a gate; a URL made by `URL(_:strategy:)`, `NSDataDetector` or a generic decode wrapper fails one, and so does an unapplied `.init`; code under `#if false` fails the text pins or the declaration gate. Each shown red on a planted case. Gaps G-2 and G-3 close |
| P3 | #144, #132 | The session neither stores nor sends a cookie, with a Swift test that a `Set-Cookie` answer is not sent back. The held reading's state and transitions are an Engine type driven by `swift test`; `ContentView` renders it, and `make ui-test` passes |
| P4 | #138 | An ADR, written first, adds each pick's model id to `/v1` (additive). The app keys its cards on it: two picks that share name, vendor, score and price but not a model show as two cards, through a test |

**The valve.** #132 is the part to cut if the wave runs long: it moves screen logic and needs the
simulator to prove. #138 waits on nothing but its ADR.

## K.8 contracts

```
scripts/client_decl_gate.py:110:NETWORK_FILE = "EngineClient.swift"
scripts/client_decl_gate.py:126:FILESYSTEM_FILES = {
scripts/client_decl_gate.py:220:FIXTURE_REFUSALS = {
scripts/client_decl_gate.py:253:def references(ast: str) -> dict[str, set[str]]:
scripts/client_decl_gate.py:335:def problems(found: dict[str, set[str]]) -> list[str]:
ios/ModelRanking/Engine/EngineClient.swift:159:struct EngineClient {
ios/ModelRanking/Engine/EngineClient.swift:205:            let configuration = URLSessionConfiguration.ephemeral
ios/ModelRanking/Engine/EngineClient.swift:242:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/AnswerPlan.swift:173:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
tests/unit/test_router_hints.py:80:def _code(swift: str) -> str:
```

`/v1` gains one additive pick field in P4, under its ADR; no route changes shape.
