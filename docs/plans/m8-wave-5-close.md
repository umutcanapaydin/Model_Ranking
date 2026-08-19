---
record_type: wave
id: m8-wave-5-close
status: ratified
process_version: v5.0
date: 2026-08-19
---
# Wave-Close Checklist — M8 Wave 5 (the fix wave the bypassed review paid for)

> **CLOSED 2026-08-19.** W5 exists because the owner authorised the review that D-122 had let three
> waves skip. Three independent seats read `bfd93bf..HEAD` — fifteen commits no fresh eyes had seen
> — and **all three returned BLOCKING.** This wave closes what was live or cheap and escalates four
> items that are genuinely the owner's.

## What the review cost, measured

- **Fault injection.** Author claimed 23 mutants, 23 killed — 100%. An independently designed set
  of 47 mutants was **12 killed, 35 survived: 25.5%.**
- **V3C-02 on REQ-APP-001..005 and REQ-API-010.** All six were marked MET. **All six fail**: seven
  of seven attacks kept the citing test green while breaking the requirement it cites.
- **Stage 4.0 security.** The author's self-review returned PASS with 0 BLOCKING. The independent
  seat returned **BLOCKING**, and found one claim in the self-review to be factually false
  (`docs/reviews/m8-security-review.md:55` — "nothing in a response can redirect the app at
  another host"; there was no redirect delegate).
- **`epoch_board.py`.** Named in no M8 record at all. **32% coverage, zero tests referencing it**,
  and 14 of 14 mutants placed in it survived.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | **HIGH.** V4C-50: a fix inherits the risk class of the bug it fixes, and this wave repairs the scoring path (`epoch_board.py`, `categories.py`), the frozen payload's serializer (`_ranking_json`) and a network trust boundary (the redirect delegate). Re-tiered from the client-only MED of W1–W3 rather than inherited | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → test → self-review → fix on every item, with each fix's mutant replayed before it was accepted. Three of this wave's own tests had to be corrected because their FIXTURES could not violate what they asserted (`docs/plans/m8-wave-5-close.md` below) | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | **This wave IS the review**, run by three seats that authored none of the code: `docs/reviews/m8-code-review.md` equivalents returned as agent reports, plus `docs/reviews/m8-security-review-independent.md`. The three PRESSURE bypasses recorded in W1–W3 are what it answers | ✅ |
| 4 | Fault injection — V3C-72 | 2026-08-19, against `src/app/clients/epoch_board.py`, `src/app/workflows/build.py`, `src/app/workflows/categories.py`, `src/app/adapter/main.py` and `ios/ModelRanking/Engine/EngineClient.swift`. Author replayed **35 of the tester's survivors** plus 12 new mutants of this wave's own fixes; every file md5-verified restored, tree confirmed byte-identical to HEAD after the tester's run (which had its own restore incident, caught by its md5 assertion in seconds) | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `tests/unit/test_epoch_board.py` (26), `test_build_boards.py` (10), plus new tests in `test_categories.py`, `test_ranking_payload.py`, `test_ios_client_contract.py`, `test_ios_payload_contract.py`. **REQ-APP-002 and REQ-APP-005 were DOWNGRADED to PARTIAL in `docs/prd.md`** rather than left claiming a grep is a proof | ✅ |
| 6 | REQ-IDs current in the PRD | `docs/prd.md` — REQ-APP-004's unreachable case and the two downgrades written at this wave, 2026-08-19 | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · **578 passed / 12 skipped** (533 before the review) · `make secrets` no leaks, 33 MB · ruff and mypy clean · `check_records` PASS · `wave-check` PASS on all four M8 wave records · `xcodebuild` exit 0 | ✅ |
| 8 | ADRs for decisions made | None written, deliberately: the four escalated items are the owner's rulings, not the agent's. `docs/decisions.md` unchanged | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md`: **W-040** (unbounded ranking payload — blocked, needs a second `/v1` revision), **W-041** (no `--cov-fail-under`), **W-042** (`app.sh` runs the relaxed env), **W-043** (REQ-API-010 cannot have a citing test). **W-033 CLOSED** — it had sat ESCALATED for a day after D-125 resolved it | ✅ |
| 10 | Plan promises delivered | Not a planned wave. Its scope is the review's findings, and every BLOCKING is closed or escalated with a named owner. Verified live: `docs/closure-report-m8.md` §7 | ✅ |

## The three findings this wave should be remembered for

**1. A record that stated the opposite of reality, in the document awaiting signature.** The closure
report, two wave records and the retrospective all said D-124's single `/v1` revision was UNSPENT.
D-125 spends it and says so in its own text. Worse than a wrong fact: **the retrospective drew a
CONCLUSION from it** — "the client asked for nothing, so a payload designed by people imagining a
consumer proved sufficient" — and shipped that conclusion into a closure report. A retrospective is
the easiest place in this process to launder an unverified premise into a finding, because nothing
downstream re-derives it.

**2. The module with no test at all, found by all three seats independently.** `epoch_board.py` is
the single reader behind six of the nine categories and reached HEAD at 32% coverage with zero tests
naming it. Its bundle-escape guard cites M5's `/etc/shadow` incident in its own docstring — **the
check was carried forward as PROSE and the test was not carried with it**, and an independent tester
re-reproduced the finding by planting a symlink. Now 91%, with all 15 replayed mutants dying.

**3. A test cannot fail if its fixture cannot reach what it asserts.** Three times in this wave: the
rounding fixture's scores were already round AND it carried no secondary-benchmark rows at all; the
build-report fixture had `stored == skipped == 2`, so swapping them was invisible. Each produced a
test that read as a gate and was a decoration. This is the same defect as a control whose scope is
narrower than its rule, one level down — in the DATA rather than the code.

## What is NOT closed

- **W-040** — the ranking payload is unbounded and cannot be bounded honestly without a second
  `/v1` revision. Silent truncation is the one thing this product refuses.
- **W-041** — no coverage floor. **The control that would have caught finding 2, and it outranks
  every individual finding in this review.**
- **W-042, W-043** — the relaxed startup lane, and a criterion V3C-02 cannot express.
- **Two attacks remain green and cannot be caught by reading source**: laundered arithmetic and a
  hand-rolled sort. REQ-APP-002 and REQ-APP-005 say so now instead of claiming MET.

---

Touched: `docs/closure-report-m8.md`, `docs/plans/m8-wave-2-close.md`, `docs/plans/m8-wave-3-close.md`, `docs/prd.md`, `docs/retrospectives/m8-retrospective.md`, `docs/warnings.ledger.md`, `ios/ModelRanking/Engine/EngineClient.swift`, `src/app/adapter/main.py`, `src/app/clients/epoch_board.py`, `src/app/workflows/categories.py`, `tests/unit/test_build_boards.py`, `tests/unit/test_categories.py`, `tests/unit/test_epoch_board.py`, `tests/unit/test_ios_client_contract.py`, `tests/unit/test_ios_payload_contract.py`, `tests/unit/test_ranking_payload.py`

K.8 contracts: none moved. `/v1` stays as D-125 left it; D-124's window remains SPENT.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-19 · Wave commit range: `bb42224..acc9ffa`
