---
record_type: wave
id: m16-wave-2-close
status: draft
process_version: v5.0
date: 2026-09-23
---
# Wave-Close Checklist — M16 Wave 2, one application (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The engine keeps itself current.** Once a night inside 23:00-01:00, and once at startup on a stale
record, the engine runs `refresh.py` as a child process it can kill and the server never waits on
(D-151, D-154). The app gains the two facts W1 published: the surface's floor on the detail screen,
and on the search surfaces, that the search call is not in the price. No button, no refresh screen,
no `/v1` change.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m16-plan.md` §2 W2 "(risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Scheduling, catch-up and isolation tested red-first on 7 mutants of `nightly.py`; then the reviews' findings, each with its own test and mutant (19 author mutants in all, every one RED). `make check`: pytest 1014 passed / 15 skipped, `swift-test PASS: 268`, `client-decls PASS` in 4 configurations, Xcode Debug build SUCCEEDED | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester | `docs/reviews/m16-wave-2-review.md` (`seat: independent`, 2026-09-23): **PASS WITH FINDINGS**, 0 BLOCKING / 2 MAJOR / 5 MINOR / 2 NIT, 23 mutants, 4 survived. The fix round of both reviews was re-reviewed: `docs/reviews/m16-wave-2-rereview.md` (`seat: independent`, 2026-09-23): **PASS WITH FINDINGS**, 0 BLOCKING / 0 MAJOR / 3 MINOR / 9 NIT -- every earlier MAJOR resolved and a real cycle published under the restricted environment. Its three MINORs are fixed after it: the 12-hour skip rule narrowed to 4 hours with a test (the old value re-run RED, and the fake clock now fails a schedule that never runs instead of hanging), the REQ-PRC-002 row cites the new pin, and D-154 says what the retirement script's listener check actually checks. Its NITs stand as written in the review | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass (D-141) | `docs/reviews/m16-wave-2-security.md` (`seat: independent`, 2026-09-23): **PASS WITH FINDINGS**, 0 BLOCKING / 1 MAJOR / 4 MINOR / 4 NIT. The switch could not be turned on outside a development environment by any spelling tried, and nothing could be injected into the child's arguments. MAJOR-1 (the server loads the source parsers) corrected in D-154 and ledgered as W-125; the four MINORs fixed, each with a test | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | `tests/unit/test_nightly_refresh.py`, with REAL child processes: one that hangs (killed at the timeout, pid gone), one that raises, one that fails, one that cannot start, one killed mid-publish (live artifact byte-identical, lock released, next cycle publishes), one that floods its output, one that crashes before writing a record. `/health` and `/v1/categories` answer at once while a child hangs, through `TestClient(app)`. A real nightly cycle ran on a COPY of `advisor.db` at 00:41 and published. The seat's own 23 mutants are in its review | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-REF-008: `tests/unit/test_nightly_refresh.py` (the lifespan through `TestClient(main.app)`; the switch through `main.validate_startup_config`). REQ-FLR-002, REQ-PRC-002: `ios/EngineTests/DetailTests.swift`, `EngineClientTests` on a payload copied from the live route, and the view pins in `tests/unit/test_ios_client_contract.py` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | D-116 clause 2 becomes a startup error: `test_production_refuses_to_boot_with_the_switch_on`, `test_the_switch_is_on_only_where_ingestion_may_run` (9 cases), `test_the_schedule_rechecks_the_switch_when_it_starts`. The child's environment: `test_the_child_inherits_no_secret_from_the_server`. D-126 unchanged, both client gates PASS | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None. Every mutant of `src/app/adapter/nightly.py` and `ios/ModelRanking/ContentView.swift` restored from a byte copy with an md5 check; the one run that hung was stopped and the file restored and verified the same way | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | What the server loads, from `sys.modules` in a fresh interpreter rather than from import lines: the refresh, build, sources, epoch and rosters modules are absent; the source parsers are present, and that is W-125 (`tests/unit/test_nightly_refresh.py::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers`) | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: the engine's schedule and catch-up, fault isolation, `/health`, the switch and its D-116 refusal, the owner's retirement script, the floor line, the price notes. **Owner's step, not done by an agent:** retiring the launchd job (`scripts/retire_refresh.sh`, which refuses until the engine reports its own refresh). Deferred with records: W-124 (a killed cycle's candidate file), W-125 (the parser import chain), W-126 (a stuck child outliving a hard-killed engine), all to the M16 closure | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | `git diff --shortstat`: about 360 lines changed in tracked files, plus three new files (`src/app/adapter/nightly.py`, `tests/unit/test_nightly_refresh.py`, `scripts/retire_refresh.sh`; about 950 lines, most of them tests). **VARIANCE noted:** a HIGH wave owes its fault injection, and two review rounds each added tests | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check (pytest 1014/15, Swift 268, client-decls 4 configurations) · ruff/mypy clean · Xcode build SUCCEEDED · outcome: closed agent-side; committed only on the owner's word, owner reviews at the milestone` | ✅ |

## What the reviews changed

The first design was right about isolation and wrong about what `/health` would say on a bad night:
a cycle killed at the timeout left the previous cycle's "published" on display, which is the
silence-reads-as-success shape D-129 exists to forbid. The code review also found a third screen
printing search prices with no note, and two notes no test would have missed. The security pass
found the docstring's claim about what the server loads was false before this wave began. Each is
fixed with a test, or recorded where the fix belongs in `refresh.py` rather than here.

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-23 · Wave commit range:
`acef579..<this wave's commit>`

## Wave footprint — RECORD ONLY

```
Touched:        src/app/adapter/nightly.py (new) · src/app/adapter/main.py
                tests/unit/test_nightly_refresh.py (new) · tests/unit/test_ios_client_contract.py
                ios/ModelRanking/ContentView.swift · ios/ModelRanking/Engine/{Detail,Models}.swift
                ios/EngineTests/{DetailTests,EngineClientTests}.swift · ios/EngineTests/test-manifest.txt
                ios/app.sh · scripts/retire_refresh.sh (new)
                docs/{decisions,prd,warnings.ledger}.md · docs/plans/m16-plan.md · note.txt
                docs/reviews/m16-wave-2-{review,security,rereview}.md (new)

K.8 contracts:  /v1 unchanged (D-151 clause 4). /health gains refresh, refresh_next, refresh_last,
                refresh_last_at -- additive, as that route's contract allows (D-154 clause 3). The
                detail floor reads /v1/categories min_quality; the price notes read price_excludes.
```
