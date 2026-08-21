---
record_type: ratification
id: closure-report-m8
status: ratified
date: 2026-08-19
---
# Closure Report — M8: The engine gets a reader, and the product stops being about coding

> **CLOSED at the owner's ruling, 2026-08-21.** Signed after the M7 carry-over was worked
> (eleven of fifteen rows closed) and after he ruled that W-024, W-027, W-030 and W-031 stay
> open while nothing deploys. Two §7 rows remain red and are meant to: the deploy did not
> happen, and the citing-test row is PARTIAL because two client criteria are gated by source
> tripwires an independent tester walked through. Both are stated rather than absorbed.

## 0. What needs the owner

1. **Go-live moved AGAIN, and this time it is a scope decision rather than a schedule one.** D-123
   said the deploy ships with the iOS app. The app is built and running. The deploy did not happen
   because the owner ruled that money goes to iOS only, and Fly.io is money. **D-123 is not
   discharged.** W-030 and W-031 stay UNVERIFIED for a third milestone. This needs a ruling: either
   a new ADR moving go-live to M9 with a trigger, or an acceptance that the engine stays on this
   Mac indefinitely and the app is a local tool until that changes.
2. **The design direction is still unpicked.** Three artboards were drafted and published; the
   category strip shipped as a deliberate placeholder that commits to none of them.
3. **`C2b` fired on the review control, and the owner then ran the review. It found three
   BLOCKING.** Three waves had closed with no fresh eyes, each under an explicit ruling. When
   three independent seats finally read the fifteen-commit range, every one returned BLOCKING —
   including a module at 32% coverage with no test naming it, a payload publishing one model's
   score twice with two different values, and this report itself stating the opposite of what
   `docs/decisions.md` records. **This is the measured cost of the bypass, and it is the evidence
   the CONTROL review should be decided on.** W5 closes the findings; `docs/plans/m8-wave-5-close.md`.
4. **Four items are escalated and unresolved**, ledgered W-040..W-043: the unbounded `ranking`
   payload (which cannot be fixed honestly without a SECOND `/v1` revision that D-124 no longer
   permits), the missing `--cov-fail-under` (**the control that would have caught the 32%
   module**), `app.sh` running the relaxed startup lane, and REQ-API-010 having no expressible
   citing test.
5. **The M7 carry-over was worked on 2026-08-21: eleven of the fifteen open rows closed.**
   W-032 shipped with the coverage floors. W-002/-005/-008/-009/-010 turned out to have been
   FIXED at M6 with nobody closing the rows — the ledger denying controls that were present, for
   three milestones. W-015 handed back as GPF-003; W-019 mitigated locally and handed back as
   **GPF-006**; W-025 (a 3.14 CI leg), W-028 (workspace sweep) and W-029 (closed on the control
   that does run) resolved. **Left open by the owner's ruling of 2026-08-21, since nothing
   deploys:** W-024, W-027, W-030, W-031.
6. **W-024 is not what the records said it was.** Diagnosed 2026-08-21: the arena dataset is
   healthy — `/is-valid`, `/splits`, `/first-rows` and `/rows` all answer, and `category='overall'`
   is present. It is the `filter` ENDPOINT that fails, and it fails **with no `where` clause at
   all**, so it was never our query. A dependency was written off for the whole milestone on one
   endpoint's word. A bounded read of `/rows` would restore the surface in four or five requests;
   it is NOT done, because it requires rewriting the citing test of a security finding (W-007),
   which is an owner call and was deferred with the rest.

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
| W5 | `docs/plans/m8-wave-5-close.md` | The fix wave: everything three independent seats found | **578 passed** / 12 skipped |

## 1b. Decisions made on your behalf

- **The category strip's design.** A horizontal chip row, chosen because it commits to none of the
  three drafted directions and makes every surface reachable. Reversible in one file.
- **`advisor.db` was overwritten with `--force`.** It is gitignored, derived, and reproducible by
  one command; the build is atomic and preserves the previous file on failure.
- **`expert` and `mathematics` keep wide value windows** (25 and 28 candidates against `coding`'s 7)
  because narrowing them below `close_call` would rank measurement noise. See §6.
- **`/v1` WAS moved, and D-124's single window is SPENT by D-125**, which adds the `ranking`
  array and says so in its own text. An earlier version of this report claimed the opposite
  in four places and built a retrospective conclusion on it. **M9 must not spend this window
  again.**
  needed already existed.

## 2. Git record

`6aca9b7..HEAD` — the M8 range. Every commit is the agent's own identity with the `Co-Authored-By`
trailer; none is attributable to the owner (V4C-64, the rule W-011 was raised under).

## 3. Trust telemetry

`make check` exit 0 at the closing tree: **533 passed / 12 skipped**, ruff clean across
`src tests scripts`, mypy clean across 32 files, `check_records` PASS across 42 records,
`wave-check` PASS on all three M8 wave records. `make secrets` — no leaks, 32.99 MB scanned.
`xcodebuild` exit 0.

**Fault injection, corrected by the independent tester.** The author reported 23 mutants, 23
killed. An independently designed set of 47 was **12 killed, 35 survived — 25.5%**. Every survivor
is closed or ledgered in W5. The honest reading is that a 100% kill rate against one's own mutants
measures the imagination of the person writing them.

## 4. Security & invariants

`docs/reviews/m8-security-review.md` — **PASS, 0 BLOCKING**, and it is a SELF-review; the agent that
wrote the code ran it. The one finding worth carrying: App Transport Security is correct by absence,
so the day `baseURL` points at a deployed host, iOS will refuse cleartext and the app will look
broken. **That refusal is the control working.** The fastest "fix" is `NSAllowsArbitraryLoads`,
which would ship this product's first real network call unencrypted.

Engine invariants: D-104 (no LLM in the scoring path) and D-105 (no cross-scale averaging) held.
**D-109 was BROKEN by this milestone** — `_ranking_json` publishes unrounded scores, so one model
appears twice in one payload with two different values. **D-115 was moved once, under D-124's
permission, by D-125.** D-118 (English query values) held; D-121 (a blind surface is never silent — exercised
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
| `make check` exit 0 | ✅ **578 / 12** |
| App builds and runs against a live engine | ✅ verified on the Simulator, `dev-c10bf3a` |
| Every criterion has a citing test able to fail | ⚠ **PARTIAL, honestly stated.** REQ-APP-001/-003 met; REQ-APP-004 met with one case unreachable (W-039); **REQ-APP-002 and REQ-APP-005 DOWNGRADED to PARTIAL** — their gates are source tripwires that an independent tester walked through, and no proof exists without an iOS test target (W-038); **REQ-API-010 has no expressible citing test** (W-043) |
| Fault injection on the client's failure states | ✅ 6 mutants, 6 killed |
| Fresh-eyes review per D-122 | ✅ **DONE at W5**, after three PRESSURE bypasses fired `C2b`. Three seats, all BLOCKING; findings closed or escalated |
| ADRs for contract questions | ✅ D-125 written; D-124's window is SPENT and recorded as such |
| Retrospective (M ≥ 3) | ✅ `docs/retrospectives/m8-retrospective.md` |
| Dated `docs/EXPERIENCE.md` entry | ✅ |
| `note.txt` refreshed | ✅ |
| Deploy (4.3) | ❌ **NOT DONE** — §0 item 1 |

**M8 closes AGENT-side with the deploy row red and the citing-test row partial, both stated rather
than absorbed.** The review row turned green the hard way. It awaits the owner's signature.
