---
record_type: wave
id: m8-wave-1-close
status: ratified
process_version: v5.0
date: 2026-08-19
---
# Wave-Close Checklist — M8 Wave 1 (the engine gets a reader, and the reader gets nine surfaces)

> **CLOSED 2026-08-19.** W1 was planned as "one screen, real data". It delivered that and then
> absorbed the D-126/D-127 scope change: the product is now an advisor for all AI tools, and nine
> categories had to answer before a client was worth looking at. The wave's real product was the
> friction the plan predicted — the contract held, and everything that broke was on this side.

## What the wave delivered

A SwiftUI app that calls the running engine and renders the real answer, and the six new categories
it needed in order to have anything to show. `src/app/clients/epoch_board.py` reads all seven Epoch
boards through one parameterised reader; `EPOCH_BOARDS` in `sources.py` declares them as data;
`build()` gained the `boards` seam. Nine surfaces answer at unlimited/medium/low, except
`assistant`, which discloses that arena is down rather than inventing an answer.

**Measured through the production entry point, not reported by the writer:** 13 sources, 9 of them
Epoch, 73 models, 72 price medians, exit 3 (arena's blind-surface report, D-121 working).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m8-plan.md` §2 records W1 **MED** (a new client codebase; the engine's frozen surface untouched). The category work added during the wave is data, not a new code path — six `CategorySpec` entries and one reader | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix, repeatedly. The author's own runs caught the calibration population error, the `boards` seam and the attribution gap; none of the three was found by reading | ✅ |
| 3 | Review per tier — V3C-78 / D-122 | **WAIVED under PRESSURE**, 2026-08-19, recorded as a `control-bypass` under V4C-13 rather than hidden. No fresh-eyes seat ran. D-122 sets depth by blast radius and the owner ruled explicitly on 2026-08-18 that the methodology be lightened and that waves not stop for review *(owner, translated from Turkish: "you don't need to wait between waves, your own tests are enough; I do the milestone tests")*. M6-W1 measured what a skipped review costs (`docs/plans/m6-wave-1-close.md`, W-016); this is the same exposure, accepted deliberately at a lower tier by the person who owns the risk. **Second consecutive PRESSURE bypass of this control in M8** — a third sends the CONTROL for review under `C2b`, not the seat | WAIVED — PRESSURE, owner ruling D-122 |
| 4 | Fault injection — V3C-72 | 6 mutants over the delta, 6 killed; every file md5-verified restored. One mutant read GREEN and the test was not the reason — `main.py` carries `"title"` twice and `replace(..., 1)` hit the wrong one. Re-aimed by line number | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-APP-001: `test_ios_client_contract.py::test_the_shipping_client_carries_no_canned_payload`, proven RED against both the escaped and triple-quoted fixture spellings. The nine categories: `test_categories.py::test_no_category_can_exclude_a_model_it_calls_level_with_the_leader` and `::test_every_source_the_build_ingests_can_be_attributed`, both proven RED | ✅ |
| 6 | New REQ-IDs in the PRD, at the wave not at closure | **WAIVED — the promise was kept LATE**, 2026-08-19. `docs/prd.md` REQ-APP-001..005 and REQ-API-010 exist, and they were written during W2 rather than W1 — the F-1 drift the M4 gate raised, repeated by the same agent that cited it. Recorded in this checklist's ledger under V4C-13 rather than backdated | WAIVED — ledger, delivered at W2 |
| 7 | Gates green at the closing tree | `make check` exit 0 · **526 passed / 12 skipped** · ruff clean across `src tests scripts` · mypy clean across 32 files · `check_records` PASS across 38 records | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-126** (all AI tools; the router may only route to a pre-existing category and may never say a model is good) and **D-127** (nine categories, `assistant` split, Tier-3 demoted to evidence) | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: **W-035** (two boards can no longer separate their top models), **W-036** (module-global source injection), **W-037** (third wrong calibration population) — all three ACCEPTED with an owning milestone of M9 | ✅ |
| 10 | Plan promises delivered | `docs/plans/m8-plan.md` §2 W1 asked for one screen against real data; delivered, plus the D-126/D-127 scope the owner added mid-wave (`docs/decisions.md`). The one shortfall is row 6 | ✅ |

## The three findings this wave should be remembered for

**1. The calibration measured a population the engine never ranks — for the third time.** Thresholds
were sized on 521 models; the engine ranks the 58 that reconcile AND carry a price. Each previous
correction had been to a different wrong set. All three were caught by measuring, none by review.

**2. A seam is only a seam if it reaches the caller.** `_ingest_boards` took a `boards` parameter
and read it at call time, correctly — and `build()` exposed no way to pass one, so eight tests that
believed they controlled the source set ran the real board list against a directory that did not
exist. Third instance of this defect in this project, in a new half.

**3. A test narrower than the rule it cites is not a gate.** The attribution guard asked only about
each category's `primary_source`; `epoch_mmlu` is nobody's primary source and is served as evidence,
so a mutant deleting its attribution walked through. Rebasing it on the source registry then made it
too WIDE — it demanded citations from two pricing sources — which is why `RemoteSource` now says
`writes_scores` out loud.

## What is NOT closed

- **W-024** — arena's upstream 500, standing for days. `assistant` ships blind and says so.
- **W-035 / W-036 / W-037** — all owned by M9, all with named remedies.
- **No fresh-eyes review ran on this wave.** Stated in row 3, not implied.

---

Touched: `docs/decisions.md`, `docs/prd.md`, `docs/research/`, `docs/reviews/m8-category-calibration.md`, `docs/warnings.ledger.md`, `ios/ModelRanking/`, `ios/app.sh`, `src/app/clients/epoch_board.py`, `src/app/workflows/build.py`, `src/app/workflows/categories.py`, `src/app/workflows/rank.py`, `src/app/workflows/sources.py`, `tests/unit/test_build.py`, `tests/unit/test_build_artifact_safety.py`, `tests/unit/test_categories.py`, `tests/unit/test_ios_payload_contract.py`, `tests/unit/test_sources.py`

K.8 contracts: `app.workflows.sources` (EPOCH_BOARDS added), `app.workflows.build` (`boards` parameter added). Frozen surfaces untouched: `/v1` payload (D-115), CLI vocabulary (D-118), `schema migrate` exit codes (D-120).

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-19 · Wave commit range: `6aca9b7..a9dc034`
