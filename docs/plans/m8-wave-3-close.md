---
record_type: wave
id: m8-wave-3-close
status: ratified
process_version: v5.0
date: 2026-08-19
---
# Wave-Close Checklist — M8 Wave 3 (the failure states, one of them verified by pulling the plug)

> **CLOSED 2026-08-19.** The wave found that the app's most likely failure was the one it had no
> name for, and that a required failure state cannot be reached at all.

## What the wave delivered

`EngineError` gained `timedOut` and `offline`; the client configures its own URLSession with a
10-second request AND resource timeout. Verified live by stopping the engine and relaunching the
app. Four structural gates protect the failure vocabulary from being quietly widened.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m8-plan.md` §2 records W3 **MED**. Client-side only; no engine code changed in this wave | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix on `ios/ModelRanking/Engine/EngineClient.swift`. The author's own mutants caught the remedy check measuring spelling instead of a read | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **WAIVED under PRESSURE**, 2026-08-19, `control-bypass` under V4C-13. Same owner ruling as `docs/plans/m8-wave-2-close.md` row 3. **THIRD consecutive bypass — under `C2b` this sends the CONTROL, not the seat, for review, and that review is carried to M9 rather than declared satisfied here** | WAIVED — PRESSURE, D-122, C2b triggered |
| 4 | Fault injection — V3C-72 | 6 mutants over the W3 delta, 6 killed after one correction; `EngineClient.swift` and `ContentView.swift` md5-verified restored | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-APP-004: `tests/unit/test_ios_client_contract.py::test_no_failure_switch_falls_back_to_a_default_clause`, `::test_the_client_bounds_how_long_it_will_wait`, `::test_every_failure_the_client_names_reaches_the_screen_with_a_sentence`. All proven RED on 2026-08-19. Plus a LIVE verification: engine stopped, app relaunched, condition and remedy shown | ✅ |
| 6 | New REQ-IDs in the PRD | `docs/prd.md` REQ-APP-004 status written at this wave, with the unreachable case named rather than claimed | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **533 passed / 12 skipped** · `xcodebuild` exit 0 · `check_records` PASS across 41 records | ✅ |
| 8 | ADRs for decisions made | None written, and that is the finding: the fail-direction question **W-039** raises is the owner's under V3C-33/45, so it is recorded in `docs/warnings.ledger.md` and NOT decided here. `docs/decisions.md` is unchanged by this wave | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: **W-039** (the 503 REQ-APP-004 requires cannot be produced) opened, ACCEPTED, owning milestone M9 | ✅ |
| 10 | Plan promises delivered | `docs/plans/m8-plan.md` §2 W3 asked for a stated screen on each failure. Delivered for unreachable (live), timeout and offline (structural); 503 is unreachable and recorded as such | ✅ |

## The two findings this wave should be remembered for

**1. The spinner that never ends was structural, not hypothetical.** `URLSession.shared` waits SIXTY
seconds by default and the screen shows `ProgressView` until the request returns. Nothing was
wrong — only unbounded — so every test passed. A timeout was also being reported as
`unreachable`, whose remedy tells the user to start an engine that is already running: wrong advice
that sends someone to fix the wrong thing, which is the same defect class as reporting a locked
database as an unbuilt one (M7-W2).

**2. Two correct controls, built two milestones apart, made one of them dead.** `/v1` returns 503 on
an unbuilt artifact; M7 added a startup probe that refuses to BOOT on one. By the time anything can
answer `/v1`, the condition has already stopped the process. Neither is a defect — failing at boot
is strictly better — but REQ-APP-004 required a verified failure state that cannot be entered, and a
branch in the API that no live request reaches. **W-039**, and the remedy is a fail-direction call.

**A method note worth keeping:** the compiler is the strongest gate available in a repository with
no iOS test target. Swift requires an exhaustive switch, so a new `EngineError` case without a
sentence is a BUILD failure. The test therefore forbids `default:` rather than checking the
sentences — it protects the guarantee, not the wording.

## What is NOT closed

- **W-039** — owner's call, M9.
- **W-038** — still no iOS test target; `timedOut` and `offline` are gated structurally, not run.
- **`C2b` has fired on the review control.** Row 3.

---

Touched: `docs/prd.md`, `docs/warnings.ledger.md`, `ios/ModelRanking/Engine/EngineClient.swift`, `tests/unit/test_ios_client_contract.py`

K.8 contracts: none moved by THIS wave. `/v1` was moved earlier in M8 by D-125; D-124's single permitted revision is **SPENT** at M8 close.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-19 · Wave commit range: `c10bf3a..dbbc436`
