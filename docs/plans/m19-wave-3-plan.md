---
record_type: plan
id: m19-wave-3-plan
status: draft
process_version: v6.6
date: 2026-10-06
---
# M19-W3 plan — the gates see before the push

**Working plan for `wave/m19-w3`**, deleted at the wave's close. The milestone plan
(`docs/plans/m19-plan.md` §2 W3) is the approved scope; the owner merged it on 2026-10-06.

**Risk: HIGH.** Gate definitions change (`Makefile`, `scripts/wave_check*.py`,
`scripts/coverage_floor.py`, `tests/conftest.py`), so the owner reviews the wave (AGENTS.md §3).
Each new or changed check goes through `/writing-a-control`: watched failing on a planted violation,
watched quiet on the clean tree, derived rather than listed, and failing closed. By D-172 no security
pass runs on the slice.

## Issues

| Issue | What | Phase |
|---|---|---|
| #137 | The skip budget is checked only in CI, so a wave sees its raise after it pushes | P1 |
| #140 | The wave gates read only heading waves and one HIGH path, not amendments and globs | P2 |
| #122 | A child process a test starts can reach the network (its second half, gap G-5) | P3 |
| #149 | The model-tier deadline test took 11.4 s against 5 s under a loaded run | P4 |
| #117 | No gate flags signal words that only a held-out set holds | P5 |
| #108 | `URLSessionConfiguration()` trapped an xctest process; cause unmeasured | P5 |

## Decisions taken on the owner's standing instruction

The owner's standing instruction (2026-09-29): take the agent's recommendation, don't ask.
- **#122:** option B, the one its re-triage recommends. On macOS, `make test` runs pytest inside a
  `sandbox-exec` profile that denies every outbound connection but loopback, so every child process
  is offline whatever its language or environment. The CI half is a patch for the owner
  (`.github/workflows/**` is theirs), posted on the issue as #81's was.
- **#117:** matching by whole words, a Turkish word also matched with its suffixes, the design the
  issue's triage left to a human.

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P1 | #137 | Every skip in the Python suite goes through a named marker, each marker saying whether CI has what it needs. A local check counts the tests CI will skip from those markers (no second list) and fails when the count differs from `docs/skip-budget.txt`, in `make check-fast`. Shown red on a planted extra artifact test and on a raw `pytest.skip` outside the markers; quiet on the clean tree |
| P2 | #140 | `wave-check-all` counts a wave added by amendment, shown red on a planted plan whose amended wave has no close. `wave-check`'s HIGH rule reads the plan's own security globs and fails closed on a plan with none, shown red on a MED close touching `EngineClient.swift` |
| P3 | #122 | On macOS, `make test` runs inside the sandbox profile; a test that starts a child which opens an outbound connection fails, shown red on a planted one, and the loopback engine tests still pass. The CI patch is posted on #122. Gap G-5 narrows to CI until the owner applies it |
| P4 | #149 | The deadline test's failure is read to its cause, from the code, before any bound moves. If the router's race can be late under a loaded cooperative pool, the race is fixed and a test holds it under load; if only the bound is tight, the record says why |
| P5 | #117, #108 | A test lists each entry of `Reading.swift`'s signal lists found in a live held-out set and in no tuning set, and fails naming the entry, shown red on M18-W3's case as a fixture. #108's cause is found by reading, never by trapping a process on the owner's Mac; a source check holds the finding |

**The valve.** #108, then #117, is the part to cut if the wave runs long: neither guards a path that
runs today.

## K.8 contracts

```
scripts/coverage_floor.py:33:DEFAULT_BUDGET = ROOT / "docs" / "skip-budget.txt"
scripts/coverage_floor.py:36:def read_budget(path: pathlib.Path) -> int | None:
scripts/wave_check_all.py:79:def missing_closes(root: pathlib.Path) -> list[str]:
scripts/wave_check.py:277:def main(argv: list[str]) -> int:
Makefile:95:test: install  ## pytest in parallel, with the served artifact required (another stack: STACK_TEST)
Makefile:117:check: lint typecheck test check-records check-records-selftest install-check harvest-context-check shell-dialect wave-check-all conformance swift-test client-decls
tests/conftest.py:278:def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
ios/ModelRanking/Engine/Router.swift:277:    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
ios/EngineTests/FrontDoorTests.swift:511:final class SlowTierTests: OfflineTestCase {
```

No `/v1` field or route changes.
