---
record_type: ratification
id: closure-report-m8
status: draft
date: 2026-08-19
---
# Closure Report — M8: The engine gets a reader, and the product stops being about coding

## 0. What needs the owner

1. **Go-live moved AGAIN, and this time it is a scope decision rather than a schedule one.** D-123
   said the deploy ships with the iOS app. The app is built and running. The deploy did not happen
   because the owner ruled that money goes to iOS only, and Fly.io is money. **D-123 is not
   discharged.** W-030 and W-031 stay UNVERIFIED for a third milestone. This needs a ruling: either
   a new ADR moving go-live to M9 with a trigger, or an acceptance that the engine stays on this
   Mac indefinitely and the app is a local tool until that changes.
2. **The design direction is still unpicked.** Three artboards were drafted and published; the
   category strip shipped as a deliberate placeholder that commits to none of them.
3. **`C2b` has fired on the review control.** Three consecutive waves closed with no fresh-eyes
   review, each under an explicit owner ruling. The rule says the third sends the CONTROL for
   review, not the seat. Carried to M9 rather than declared satisfied.
4. **Four decisions still open from M7:** W-027 (`contract-tests.yml` has never run), W-032 (wire
   `make wave-check` into `make check`), the Artificial Analysis API key, and whether
   `agentic-coding` stays as a tenth category.

## 1. What shipped

**The product stopped being a coding-model ranker.** D-126 widened it to all AI tools with a hard
boundary — a free LLM in the middle may route a question to a pre-existing category and may never
say a model is good — and D-127 set the nine categories. Six of them are new, and all nine answer.

**The engine's first reader that is not a test.** A SwiftUI app runs in the Simulator, fetches the
surface list, renders the real answer, and states a real failure when the engine is not there.

**Measured, read back from the artifact rather than reported by the writer:** 13 sources, 9 of them
Epoch boards, 73 models, 72 price medians. Nine surfaces answer at unlimited/medium/low, except
`assistant`, which discloses that arena is unreachable.

## 1a. Per-wave table

| Wave | Record | Delivered | Gate at close |
|---|---|---|---|
| W1 | `docs/plans/m8-wave-1-close.md` | The screen, and the six categories it needed to be worth looking at | 526 passed / 12 skipped |
| W2 | `docs/plans/m8-wave-2-close.md` | Ruling A and the disclosures; four client invariants became gates | 530 passed / 12 skipped |
| W3 | `docs/plans/m8-wave-3-close.md` | The failure states; one verified by stopping the engine | 533 passed / 12 skipped |

## 1b. Decisions made on your behalf

- **The category strip's design.** A horizontal chip row, chosen because it commits to none of the
  three drafted directions and makes every surface reachable. Reversible in one file.
- **`advisor.db` was overwritten with `--force`.** It is gitignored, derived, and reproducible by
  one command; the build is atomic and preserves the previous file on failure.
- **`expert` and `mathematics` keep wide value windows** (25 and 28 candidates against `coding`'s 7)
  because narrowing them below `close_call` would rank measurement noise. See §6.
- **`/v1` was NOT moved.** D-124 permits one move during M8; it is UNSPENT. Every field the client
  needed already existed.

## 2. Git record

`6aca9b7..HEAD` — the M8 range. Every commit is the agent's own identity with the `Co-Authored-By`
trailer; none is attributable to the owner (V4C-64, the rule W-011 was raised under).

## 3. Trust telemetry

`make check` exit 0 at the closing tree: **533 passed / 12 skipped**, ruff clean across
`src tests scripts`, mypy clean across 32 files, `check_records` PASS across 42 records,
`wave-check` PASS on all three M8 wave records. `make secrets` — no leaks, 32.99 MB scanned.
`xcodebuild` exit 0.

**Fault injection across the milestone: 23 mutants, 23 killed** — but four of them only after the
test that should have caught them was corrected, and one after the mutant itself was re-aimed. That
ratio is the honest number, not 23/23 first pass.

## 4. Security & invariants

`docs/reviews/m8-security-review.md` — **PASS, 0 BLOCKING**, and it is a SELF-review; the agent that
wrote the code ran it. The one finding worth carrying: App Transport Security is correct by absence,
so the day `baseURL` points at a deployed host, iOS will refuse cleartext and the app will look
broken. **That refusal is the control working.** The fastest "fix" is `NSAllowsArbitraryLoads`,
which would ship this product's first real network call unencrypted.

Engine invariants held: D-104 (no LLM in the scoring path — the client computes nothing, gated by
test), D-105 (no cross-scale averaging), D-109 (rounding at the output boundary), D-115 (`/v1`
frozen — unmoved), D-118 (English query values), D-121 (a blind surface is never silent — exercised
for real, since arena was down for the whole milestone).

## 5. Ledgers

Opened: **W-035** (two boards can no longer separate their top models), **W-036** (module-global
source injection), **W-037** (third wrong calibration population), **W-038** (no iOS test target),
**W-039** (the 503 REQ-APP-004 requires cannot be produced). All five ACCEPTED with M9 as the owning
milestone and a named remedy.

Carried unresolved: W-019, W-024 (arena, standing for days), W-025, W-027, W-028, W-029, W-030,
W-031, W-032, GPF-001..005.

## 6. Architecture delta — PROSE

Two things changed shape this milestone, and only one of them is code.

**The product acquired a second axis.** Until M8 the engine ranked models on one question and the
architecture reflected that: one category layer, one primary benchmark per category, one reader per
source. Nine categories did not change that structure — they proved it. Six new surfaces were added
by writing six `CategorySpec` entries and one parameterised reader, with no branch anywhere in the
scoring path, which is exactly what "categories are data, not code" was supposed to buy and had
never been tested at scale. The one structural addition is `EpochBoard`: a declaration that says
which column of which CSV carries which metric on which scale. Adding a tenth board is now a data
edit.

**The engine acquired a consumer, and consumers change what a contract means.** `/v1` was designed,
frozen and reviewed by people imagining a client. Writing the client found no field it wanted
changed — D-124's single permitted move is unspent — but it found something the reviews could not:
a field the payload carries, the client decodes, and no screen mentions. `ranking_effort` was
invisible for as long as there was nobody to be misled by its absence. **The contract was correct
and the product was not**, and no test on either side could see the gap, because the gap was between
them. That is the shape the seam tests now cover: they derive what the client requires from the
Swift source and assert the engine satisfies it, in both directions.

The third change is smaller and worth naming because it will recur: **the ranked population is not
the ingested population.** The engine can only recommend a model that reconciles to the registry and
carries a price — 58 of 521 on ECI. Three separate calibrations have now been sized against three
different wrong sets, and the reason is that this population has no name in the codebase. Until it
has one, the question keeps being answered from whatever data is nearest.

## 7. Definition of done

| Requirement | State |
|---|---|
| `make check` exit 0 | ✅ 533 / 12 |
| App builds and runs against a live engine | ✅ verified on the Simulator, `dev-c10bf3a` |
| Every criterion has a citing test able to fail | ✅ REQ-APP-001/-002/-003/-005 met; REQ-APP-004 met with one case recorded as unreachable (W-039) |
| Fault injection on the client's failure states | ✅ 6 mutants, 6 killed |
| Fresh-eyes review per D-122 | ❌ **NOT DONE** — three PRESSURE bypasses, `C2b` fired |
| ADRs for contract questions | ✅ D-124 unspent and recorded as such |
| Retrospective (M ≥ 3) | ✅ `docs/retrospectives/m8-retrospective.md` |
| Dated `docs/EXPERIENCE.md` entry | ✅ |
| `note.txt` refreshed | ✅ |
| Deploy (4.3) | ❌ **NOT DONE** — §0 item 1 |

**M8 closes AGENT-side with two rows red, both stated rather than absorbed.** It awaits the owner's
signature.
