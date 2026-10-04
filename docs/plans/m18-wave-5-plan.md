---
record_type: plan
id: m18-wave-5-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W5 plan — the gates and records backlog

**Working plan for `wave/m18-w5`**, deleted before merge. Milestone plan: `docs/plans/m18-plan.md`
§2 W5. Risk: **MED** in the plan. The diff will touch `ios/ModelRanking/Engine/EngineClient.swift`
(#58) and the D-126 gates, so it is **HIGH** by the plan's security globs. There is no security pass
on the slice (D-172); the Tester's fault injection is owed.

**Order.** The owner said on 2026-10-04 not to wait for open pull requests (translated from Turkish:
"you don't need to wait for the other PR, I'll merge in the right order, carry on"). The branch is
stacked on `wave/m18-w4`, and W4's later fixes are merged in, never rebased. Every gate change
here is shown red by the defect it closes, and no simulator is used (the owner, 2026-10-01).

## Phases (each red first where it changes behaviour; `make check-fast` green after each)

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan committed |
| P1 records | #68, #33, #80, #84, #52 | The REQ-APP-002/003/005 rows describe the combined path and cite its tests. `REQ-API-010` names one requirement. Every id cited in tests has a PRD row, or is listed as never built. D-154 and D-157 carry their ruling's status. `docs/architecture.md` and `AGENTS.md` §1 describe the product after M18-W4. `AGENTS.md` §4 states that review seats run one after another, each in its own worktree |
| P2 the phone's gates | #59, #51, #58, #98 | A Swift test that opens a connection fails the suite. A committed fixture shows `client-decls` refusing `URLSession` outside `EngineClient.swift`, `FileManager` outside its files, and a `URL` decoded outside `EngineClient.swift`. `GapRegisterStore` refuses an address that is not a file. A pin no longer passes on a line wrapped in `/* */` |
| P3 the engine's and the process's gates | #92, #82, #83 | Each of the closure Tester's seven holes fails a test. `wave-check-all` fails on a planned wave with no close record. `wave-check` refuses a close that is not HIGH when its diff touches `src/app/clients/` |
| P4 compiler-level tripwires | #60, #85 | An aliased position and a second same-named sort each fail a gate. The two mutants from the closure seat each fail a gate: a refinement relayed onto `/v1/boards`, and the question stored in the standings file. The three-attempts rule applies: a third failed design files the rest |

## Decisions (the owner's standing instruction of 2026-09-29)

- **#52.** The rule lives in this project's `AGENTS.md` §4, the way D-172 lives there. It is handed back
  to DevFlow on the issue. The skills stay DevFlow's.
- **#84.** It is resolved by D-172 and `AGENTS.md` §4, both in M18-W1. What is left is handing it back
  to DevFlow, done on the issue.
- **#33 item 4.** D-154 and D-157 move to `accepted` only where the record shows the owner's approval:
  D-157's principle was ruled by him on 2026-09-23, and each ADR's wave merged by his hand. The merge
  that approved each is found in the history and cited. Each gets a dated status line; the bodies are
  not edited. If no such merge is found, the ADR stays `proposed` and the PR body asks.

## K.8 contracts (grep at `5623f4b`)

```
scripts/client_decl_gate.py:107:NETWORK_FILE = "EngineClient.swift"
scripts/wave_check_all.py:51:PATTERN = "docs/plans/m*-wave-*-close.md"
tests/unit/test_router_hints.py:31:def _code(swift: str) -> str:
```

## The one alternative

**Drop W5 to the next milestone** (the plan's own valve). It is rejected for now: the app-facing waves
wait for the simulator, and these gates are the ones the owner's first release leans on. P4 is the
part to cut if it runs long.
