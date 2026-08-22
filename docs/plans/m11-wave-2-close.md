---
record_type: wave
id: m11-wave-2-close
status: draft
process_version: v5.0
date: 2026-08-22
---
# Wave-Close Checklist — M11 Wave 2 (Swift gets executed)

> **STATUS: CLOSED 2026-08-22.** 1,093 lines of Swift had never been run by anything in this
> repository. They are now run by `make check` and by `runner`. The independent seat returned
> **BLOCKING**, and its first finding was that the `runner` half of that sentence was false: the
> section reported ALL PASS with the Swift tests red.

## What the wave delivered

- `ios/Package.swift` — a package whose target `path` is `ModelRanking/Engine`, so `swift test`
  compiles **the sources the app ships**. The `.xcodeproj` is not modified; there is no second copy.
- `ios/EngineTests/` — **39 tests** over the router's boundary, the similarity threshold, the
  redirect guard and the client's failure decisions.
- `make swift-test` in `check:`, and a `swift-tests` section in `runner`.
- Two seams opened in production code, both because a property the requirement depends on could
  not be reached: `TieredRouter.model` and `SimilarityRouter.floor`.
- `tests/unit/test_ios_platform_drift.py` — the drift guard `Package.swift` had merely CLAIMED.

**Measured at the closing tree:** `make check` exit **0** · **691 Python passed / 12 skipped** ·
**39 Swift tests** · ruff, mypy, gitleaks clean · `check_records` PASS · `wave-check-all` PASS ·
`conformance-gate` PASS.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m11-plan.md` §3 records W2 **HIGH** (the only unexecuted half of the product) | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix on `ios/Package.swift`, `ios/EngineTests/`, `ios/ModelRanking/Engine/Router.swift`, then a full remediation round against the seat's findings | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-wave-2-review.md`, `seat: independent`. Returned BLOCKING; all 3 blocking, all 4 major and 6 of 8 minor fixed in this wave, the remaining two ledgered as W-060 | ✅ |
| 4 | Fault injection — V3C-72 | The seat ran **20 mutants, 9 killed / 9 survived**. Every survivor it named is now killed: re-run of its 8 behavioural survivors gives **8/8**, md5 restore verified on `Router.swift` and `EngineClient.swift` | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-IOS-001: `ios/EngineTests/`, `Makefile` `swift-test`, `runner` · REQ-IOS-002: `ios/EngineTests/RouterBoundaryTests.swift`, both sides of the floor driven. `make swift-test` proven to exit 2 on a broken assertion and 0 otherwise | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-IOS-001, REQ-IOS-002 | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · 691 passed / 12 skipped · 39 Swift tests · `scripts/check_records.py` PASS · `scripts/wave_check_all.py` PASS · `scripts/conformance_gate.py` PASS | ✅ |
| 8 | ADRs for decisions made | None. The package scopes to the Engine layer, which is a scoping decision recorded in `ios/Package.swift` and in W-038 rather than a project ruling | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-038 **FIXED**, W-059 raised and **FIXED**, W-060 opened | ✅ |
| 10 | Plan promises delivered | `docs/plans/m11-plan.md` §3 W2, all four items | ✅ |

## The three findings this wave should be remembered for

**1. Proving one half of a change proves nothing about the other half.** The `make swift-test`
recipe was written with a pipe, measured to return 0 with a broken assertion, and fixed — and the
comment recording that lesson sits four lines above the `runner` section that shipped the *same
class* of defect with different mechanics. `pass` and `fail` are not commands in `runner`; only
`record` is. Both branches died silently, `$FAILED` stayed empty, and the runner reported all-pass
over a red suite. It was found by replicating the lines against a red tree, not by reading them —
which is exactly how the Makefile half had been found, and exactly what was not repeated here.

**2. A test that builds the value it checks has tested nothing.** Nine of twenty mutants survived
the first version of these tests, and every survivor shared one shape: the assertion was made
against a `RoutingOutcome` the test constructed by hand, or against a threshold no fixture ever
crossed. `unmeasured: true → false` survived 18 passing tests. This is the project's most-recorded
defect appearing in a brand-new language, which is worth stating plainly: **it is not a Python
habit, it is a testing habit.**

**3. A manifest that argues for itself.** `Package.swift`'s comment claimed the macOS-26 floor was
what kept the `FoundationModels` tier compiled, and that the iOS pair could not silently drift.
The seat lowered the floor (still green, tier still compiled) and observed that nothing compared
the two declarations. The rationale is corrected — and the drift claim is now TRUE rather than
merely withdrawn, because `tests/unit/test_ios_platform_drift.py` performs the comparison the
comment described.

## What is NOT closed

- **W-060** — `ContentView.swift` and `ModelRankingApp.swift` remain unexecuted, and the Swift gate
  runs in no CI workflow (every job is `ubuntu-latest`). Both stated in the records rather than
  implied away.
- **The W2 code was committed inside the W1 commit**, whose subject and `GP-Task:` trailer both say
  `m11-w1`. An attribution error by the author, recorded here rather than rewritten: V4C-64 exists
  so a commit's provenance is legible, and a range that says W1 while carrying W2 is exactly the
  legibility it protects. This record's commit range names the truth.

---

Touched: `docs/plans/m11-wave-2-close.md`, `docs/prd.md`, `docs/reviews/m11-wave-2-review.md`, `docs/warnings.ledger.md`, `ios/EngineTests/EngineClientTests.swift`, `ios/EngineTests/RouterBoundaryTests.swift`, `ios/ModelRanking/Engine/Router.swift`, `ios/Package.swift`, `Makefile`, `runner`, `tests/unit/test_ios_platform_drift.py`

K.8 contracts: `ios/Package.swift` is NEW and compiles the shipping Engine sources; `TieredRouter.model` and `SimilarityRouter.floor` are NEW injection points with their measured values as defaults. `make swift-test` is a new `check:` dependency. Frozen surfaces untouched: `/v1` payload, D-104, the router's nine-id boundary.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22 · Wave commit range: `8f02ddf..HEAD` (the Swift itself landed inside `8f02ddf`, mislabelled `m11-w1`; see above)
