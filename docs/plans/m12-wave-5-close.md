---
record_type: wave
id: m12-wave-5-close
status: ratified
process_version: v5.0
date: 2026-08-25
---
# Wave-Close Checklist — M12 Wave 5 (Stage 4.0 discharge)

> **STATUS: CLOSED 2026-08-25.** Not a feature wave. This is the wave that discharges the M12
> Stage 4.0 independent security review — **3 BLOCKING, 7 MAJOR, 6 MINOR** — and it exists because
> that review was the first independent read of M12's code, four waves after the code was written.

## What the wave delivered

**BLOCKING**

- **B-1 — three client crashes reachable from a `/v1` number.** `Int(Double)` traps; it is not a
  conversion but an assertion that the value fits, and the values come off the wire. `wholeNumber()`
  and `money()` now guard finiteness and range. Verified live: `Int(1e19.rounded())` exits 133.
- **B-2 — `L1` failed OPEN on an unbalanced fence**, and was already failing open here: 26 lines of
  `docs/reviews/m11-wave-1-review.md` were exempt from the English-only rule by a stray ```` ``` ````.
  The scanner now fails CLOSED when it cannot tell code from prose.
- **B-3 — all four M12 waves closed K.7 green citing reviews written before the code existed.**
  See below; this is the finding the milestone is about.

**MAJOR**

- **M-1 — the C2b rekey had not made the counter able to count.** Two defects pulling opposite
  ways: the key was read from the PATH column (19 of 22 ACCEPTED rows had no key at all, so the
  counter read three rows and called nineteen zero), and the discharge was any `D-nnn` anywhere in
  any counted row — W-020's incidental mention of D-120 had silenced K.7 permanently. Now: the
  whole row is read, `C2d` requires an acceptance to name its control, and the discharge is the
  explicit `C2b-reviewed: D-nnn @N`, anchored so a fourth acceptance **re-arms** the trigger.
- **M-2 — `/v1` prose changed on 116 sites while the records said it had not.** The shape moved
  once and additively, as recorded; the VALUES did not hold. D-136 amended with the measurement.
- **M-3 — the frozen key set stopped one level above where a pick lives.** `primary`,
  `display_order`, `internal_debug_sql` and `authoritative` injected into every pick and row, and
  both assertions passed. Pick (21) and ranking-row (11) vocabularies now frozen.
- **M-4 — the composition layer dropped a number and kept the claim.** `number()` returned `""`
  for anything it could not read, so `cheaper_by_percent: "ninety"` shipped
  `2.7 points behind the best one, and % cheaper.` Every value a sentence quotes is now a
  precondition of writing it.
- **M-5 — `cheaper_phrase` was dead code the ledger named as the fix**, with nine green tests
  beside it and no caller. Deleted; the nine now run through the shipping composer.
- **M-6 — D-118 was ratified and unsuperseded while M12 shipped what its Revisit-when named.**
  Marked SUPERSEDED IN PART by D-136, with the half that still holds stated separately.
- **M-7 — the Turkish placeholder invited a question the router cannot read.** The similarity tier
  is pinned to English; a Turkish sentence embedded as English produces noise that clears the
  floor. It now declines what it cannot read and drops to the chips.

**MINOR** — M-1 (the CLI stated a rounded bar the engine does not apply, 6 of 9 surfaces) ·
M-2 (L1's code-span exemption had no bound and mis-read the double-backtick form) ·
M-3 (`.swift` was not in `LANG_SUFFIXES`, so L1 had never read one line of the client) ·
M-5 (closed by B-1's guard). **M-4 is already recorded as W-019. M-6 is for the owner:** two
commits landed while the review was running — a Stage 4.0 pass cannot certify a tree another
session is still writing to, and the previous milestone's seat raised the same class.

**Measured at the closing tree:** `make check` exit **0** · `make gate` exit **0** ·
**785 Python passed / 12 skipped** (781 at wave start) · **132 Swift tests** (127 at start,
floor 121) · `check_records` PASS across 73 records · `wave-check-all` PASS (24 v5.0 records).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | **HIGH** — this wave edits the gates that judge every other wave: `scripts/check_records.py`, `scripts/wave_check.py`, `.language-allow` | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Reproduce → fix → prove the fix fires, per finding. The seat's own injection re-run verbatim against `src/app/adapter/main.py:878`: `internal_debug_sql` in every pick now fails `tests/unit/test_api_v1.py` | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m12-security-review.md`, `seat: independent`, dated 2026-08-25 — **this wave IS the discharge of that review**, and it is the first M12 review not dated before the code it read | ✅ |
| 4 | Fault injection — V3C-72 | 4 mutants, 4 killed: the seat's pick-key injection (RED, restored, md5 verified) · `:g`→`:.0f` in `subscribe.py` (RED, restored, md5) · Turkish into a non-exempt `.swift` (RED, restored) · `C2b-reviewed: @3` against a count of 4 (re-armed, live) | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | `test_c2b_counter.py` (+4 cases) · `test_api_v1.py` frozen pick/row sets · `test_categories.py` bar equality · `LanguageTests.swift` `RouterLanguageTests` + the rewritten hostile-value tests · 6 L1 scope probes in `--self-test` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | None — no new product requirement. The findings discharge against REQ-RTR-005, REQ-LOC-001 and REQ-GOV-001, already in `docs/prd.md` | N/A |
| 7 | Gates green at the closing tree | `make check` exit 0 · `make gate` exit 0 · 785 passed / 12 skipped · 132 Swift · `check_records` PASS (73) · `wave_check_all` PASS (24) | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` — **D-137** (a review has a DATE) · **D-136 amended** (the prose did not stay) · **D-118 SUPERSEDED IN PART** by D-136 | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — **W-087** raised and ACCEPTED (the K.7 bypass, naming its controls) · **W-081 corrected** — it named a dead symbol and gave a measurably false reason | ✅ |
| 10 | Plan promises delivered | `docs/plans/m12-plan.md` — W5 was not in the signed plan. It exists because Stage 4.0 found BLOCKING work, which is the stage doing its job | ✅ |

## The finding this wave should be remembered for

**A review has a DATE, and nothing had ever asked what it was.**

All four M12 waves closed the K.7 row green. Each cited an M11 council review declaring
`seat: independent`. Each row explained itself in the same words — *"the review preceded the
code"* — written as the defence, and standing as the proof. Those seats reviewed M11's product and
named the findings M12 then implemented; that is what shaped this milestone and it was worth more
than most reviews. It is not a reading of M12's code.

**Nobody read M12's code independently until Stage 4.0, and Stage 4.0 found two BLOCKING defects
in it.** Both were in code that four green K.7 rows said had been reviewed.

The gate inherited the blind spot exactly. `review_seat_problems` asked whether a cited review
exists and declares an independent seat — the two properties anyone would think to check — and had
no notion of whether that seat could have SEEN the work. V3C-78 tiers review DEPTH by risk. D-133
settled review IDENTITY. Between them they answer *how much* and *by whom*, and neither answers
**when**. A review is the only artifact in this process whose entire value depends on its position
in time, and time was the one property nothing asserted.

That is this milestone's through-line arriving in the governance layer itself: **a thing asserted
somewhere and exercised nowhere, each half locally correct.** The council reviewed. The waves
cited. Both true, and no code was read.

### The second-order finding, which is worse

The control that exists to catch this **had been silenced by a coincidence**. C2b counts
acceptances per control so that a control bypassed three times goes under review. Two defects kept
it from ever counting: it read its key from a column that holds paths, and it accepted any `D-nnn`
in any counted row as proof of review — so W-020's passing reference to D-120, the CLI exit-code
contract, discharged K.7 forever. K.7 was bypassed four more times in this milestone with the
alarm already switched off, by a mention that had nothing to do with it.

Both are fixed, and the fix that matters is the anchor: `@N` binds a discharge to the count it was
written against, so the fourth acceptance re-arms the trigger. **A trigger that can never fire
twice is not a trigger.** This milestone spent itself finding that shape in test gates; it was in
the governance rules the whole time.

## What this wave leaves open

- **MINOR-6, for the owner.** Two commits landed while Stage 4.0 was running. A review cannot
  certify a tree another session is still writing to, and D-137 now makes the date load-bearing —
  which makes a moving tree a sharper problem than it was, not a softer one.
- **`m7-wave-1-close.md`** cites a review dated one day before it. It predates the seat rule
  entirely and is left as history (GPF-001); the new date rule reports it, and the report is
  correct.

Touched: `.language-allow`,`docs/closure-report-m12.md` `docs/decisions.md`,`docs/plans/m12-wave-1-close.md` `docs/plans/m12-wave-2-close.md`,`docs/plans/m12-wave-3-close.md` `docs/plans/m12-wave-4-close.md`,`docs/plans/m12-wave-5-close.md` `docs/retrospectives/m12-retrospective.md`,`docs/reviews/m12-security-review.md` `docs/warnings.ledger.md`,`ios/EngineTests/LanguageTests.swift` `ios/ModelRanking/Engine/Language.swift`,`ios/ModelRanking/Engine/Router.swift` `note.txt`,`scripts/check_records.py` `scripts/wave_check.py`,`src/app/workflows/recommend.py` `src/app/workflows/subscribe.py`,`tests/unit/test_api_v1.py` `tests/unit/test_c2b_counter.py`,`tests/unit/test_categories.py` `tests/unit/test_cheaper_phrase.py`

K.8 contracts: **the `/v1` payload did NOT move** — no key added or removed at any level; the
change is that its inner vocabularies are now FROZEN by test (21 pick keys, 11 ranking-row keys).
Three GOVERNANCE contracts moved and every one of them tightens: **K.7** now requires a review
dated on or after the record citing it (D-137, enforced in `scripts/wave_check.py`); **C2b**'s key
and discharge changed shape, and `C2d` is new, so an ACCEPTED row from W-087 on must name its
control; **L1** now reads `.swift`, fails closed on an unbalanced fence, understands the
double-backtick span, and stops exempting a code span longer than 120 characters. Client contract:
`whySentence`/`tradeOffSentence` return `nil` on any value they cannot render — a widening of the
documented fall-back to English, not a new one. Frozen surfaces untouched: D-104 (the engine still
decides every number), D-115/D-125/D-136 on payload shape, D-127, the refresh exit codes.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Wave commit range: `5fb5755..HEAD`
