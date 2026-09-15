---
record_type: wave
id: m13-wave-5-close
status: ratified
process_version: v5.0
date: 2026-09-15
---
# Wave-Close Checklist — M13 Wave 5 (Stage 4.0 discharge)

> **STATUS: CLOSED 2026-09-15.** This wave discharges the M13 Stage 4.0 independent security
> review, which returned PASS WITH FINDINGS: **no BLOCKING, 3 MAJOR, 3 MINOR, 2 NIT**. The review
> found nothing the reader types leaving the device, and the web and API baseline holding. What it
> found were two instruments that had stopped telling the truth, and a control that had been
> skipped three times where nothing counted.

## What the wave delivered

**MAJOR**

- **M-1 — `/health` read `servable` for an artifact the process could not open.** W1 memoised the
  probe on `(path, mtime, size)`. A `chmod 000`, or a same-size rewrite with the mtime set back,
  left that key unchanged while `/v1` answered 503. The key now also carries `st_dev`, `st_ino`,
  `st_ctime_ns`, `st_mode`, `st_uid` and `st_gid` (`src/app/adapter/main.py::_artifact_key`).
  `tests/unit/test_health_memo.py` proves both states through `/health`. It also proves that three
  polls of an unchanged artifact still run the probe once, so the fix cannot quietly remove the
  memo it corrects.
- **M-2 — REQ-RTR-004's citing test passed a client that sent the typed question to the engine.**
  It looked for the word `question`, and W3 had rewritten the path around `asked` and `typed`. It
  now asserts data flow: every argument of every engine call is the bare `task` or `budget`, and
  `task` is assigned only the router's surface id or the id the reader tapped.
- **M-3 — the three waived HIGH-tier security passes never reached the warnings ledger**, so the
  counter built to notice repetition could not see them. W-088, W-089 and W-090 now count them.
  This is V3C-78's seventh acceptance, and D-141 (PROPOSED) is the control review. The W1 waiver had
  a measured cost: it is the slice M-1 shipped in.

**MINOR and NIT**

- MINOR-1: `/v1/categories` now warns once per artifact identity, not once per request. The route
  is unauthenticated, and 101 requests had written 101 lines.
- MINOR-2: the D-126 boundary test now reads stored `var` fields as well as `let`, and
  `alternatives` must stay `[String]`.
- MINOR-3: the Swift test floor (121, against 215 tests) is ESCALATED as W-091, because a gate
  definition is the owner's.
- NIT-1: `firstWithin` clamps its deadline before converting it, so NaN and 1e30 no longer trap.
- NIT-2: queued to M14 in the closure report.

**From the re-verification**

- MINOR-4: four more routes carried the typed text into `task` past the rewritten test:
  `select(typed)`, `task += typed`, a second `EngineClient` called directly, and a `RoutingOutcome`
  built in the view. Four rules were added, and all four mutants are RED. **This fix came after the
  seat's read and has not been re-read by it.**
- MINOR-5: C2b accepts a PROPOSED ADR as a discharge. See the first item under "What this wave
  leaves open".

**Capture:** retrospective, EXPERIENCE entry, M13 coverage rows, process-log entry, closure report
and `note.txt`, plus the `AGENTS.md` diet check: 156 → 149 lines, over its cap since M11-W1.

## Escalated in this wave (`AGENTS.md` §3)

- **Two security-invariant tests were modified:**
  `test_nothing_typed_by_the_reader_reaches_the_engine` (REQ-RTR-004) and
  `test_the_router_never_produces_anything_but_a_category_id` (D-126). Both were made stricter after
  the seat showed each passing a mutant that broke its invariant. Every assertion of the old
  versions is kept, and the mutants are listed in row 4. The owner is told in closure report §0.
- **The Swift test floor**, W-091.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | **HIGH**: the wave changes what the readiness probe reports (`src/app/adapter/main.py::_artifact_key`) and two security-invariant tests (`tests/unit/test_router_hints.py`) | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Reproduce → fix → prove the fix fires, for each finding. Every new test was run against the defect it names, on private copies: with the old memo key restored by a pytest plugin, both `/health` negative tests FAIL and the other two pass; with per-request logging restored, the warning test FAILS | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m13-security-review.md` (`seat: independent`, 2026-09-15) found the work. `docs/reviews/m13-security-rereview.md` (`seat: independent`, 2026-09-15) re-verified it: **PASS WITH FINDINGS, no BLOCKING, every MAJOR closed**. The seat rebuilt the tree itself, compared it byte for byte with the working tree, and ran `make check` there (874 / 215). It raised two new MINOR, dispositioned above | ✅ |
| 4 | Fault injection — V3C-72 | 11 mutants, 11 killed, all on private copies: the old memo key · per-request logging · the seat's `task: asked.isEmpty ? task : asked` · `task = typed` · `self.task = asked` · the seat's four re-verification mutants (`select(typed)`, `task += typed`, a second `EngineClient`, a `RoutingOutcome` built in the view) · the seat's `var praise: String` · `alternatives` retyped to `String` | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `tests/unit/test_health_memo.py` (4 tests) · `tests/unit/test_router_hints.py` (2 rewritten) · `FrontDoorTests.swift::testADeadlineThatIsNotASensibleNumberDoesNotTrap` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | None. The findings discharge against REQ-RTR-004, REQ-FIX-002 and REQ-UNC-002, already in `docs/prd.md` | N/A |
| 7 | Gates green at the closing tree | `make check` exit 0 · 874 passed / 12 skipped · 215 Swift · `check_records` PASS · `wave-check-all` PASS · `conformance-gate` PASS | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md`: **D-141**, PROPOSED (a HIGH wave owes its pulled-forward security pass, and its author cannot waive it) | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: W-088, W-089 and W-090 ACCEPTED, naming `V3C-78`, with `C2b-reviewed: D-141 @7` · W-091 ESCALATED | ✅ |
| 10 | Plan promises delivered | `docs/plans/m13-plan.md` §2 W5: Stage 4.0, capture and the closure report are delivered. The diet check was owed since M11 | ✅ |

## What this wave leaves open

- **D-141 is PROPOSED.** It discharges the repetition counter because the control WAS reviewed. The
  decision it recommends is the owner's to ratify, amend or refuse. **If the owner refuses it, the
  `C2b-reviewed` marker on W-090 must go as well**, because C2b reads the `@7` and never the ADR's
  status (re-verification MINOR-5). Making C2b read the status is a gate change, queued to the
  owner for M14.
- **W-091**: the floor stays at 121 until the owner moves it.
- **NIT-2**: an abandoned on-device model call is not waited for, so repeated questions into a hung
  model can stack on the reader's device. Nothing leaves the device. Queued to M14.

Touched: `src/app/adapter/main.py` · `tests/unit/test_health_memo.py` (new) · `tests/unit/test_router_hints.py` · `ios/ModelRanking/Engine/Router.swift` · `ios/EngineTests/FrontDoorTests.swift` · `docs/decisions.md` · `docs/warnings.ledger.md` · `AGENTS.md` · `.agents/rules/practices.md` · `docs/reviews/m13-security-review.md` · `docs/reviews/m13-security-rereview.md` · `docs/plans/m13-wave-5-close.md`

K.8 contracts: **`/v1` did not move.** The shape of `/health`'s `evidence` is unchanged, and it is
now correct in two states where it was not. `firstWithin`'s signature is unchanged. The frozen
surfaces are untouched: D-104, D-115, D-127, D-138.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-09-15 · Wave commit range: `3b13b11..HEAD`
