---
record_type: closure
id: closure-report-m13
status: draft
process_version: v5.0
date: 2026-09-15
---
# Closure Report — M13: the question is the front door, and the numbers stop overstating

> **AWAITING THE OWNER'S SIGNATURE.** Section 0 is what needs you. Every figure below was measured
> at the closing tree.

## 0. What needs the owner

1. **Type a question into the app.** Nobody has. Run `./ios/app.sh up`, type into the field, and
   press Return and then the arrow. If no keyboard shows, press ⌘K. Safari's address bar showed no
   keyboard on this simulator either (W3 close, ledger L2), so the keyboard gap is the simulator's,
   not the app's. That still has to be seen by a person.
2. **`launchctl kickstart -p gui/$(id -u)/com.hcs.modelranking.refresh`.** It still exits 78, and
   the artifact dates from 2026-08-27. Until it runs, the terminalbench dates this milestone fixed
   stay invisible. If it returns 78 again, give Full Disk Access to `.venv/bin/python3.14`.
3. **Ratify, amend or refuse D-141** (proposed). It is the control review the warnings ledger
   asked for: the pulled-forward security pass of a HIGH wave was waived in all three code waves
   (W-088..W-090), and the waived slice shipped the `/health` memo defect. If you refuse it,
   remove the `C2b-reviewed` marker from W-090 too: the counter reads the marker, never the
   ADR's status (re-verification MINOR-5).
4. **Raise `SWIFT_TEST_FLOOR`** in `Makefile` from 121 to the count `make check` prints (W-091). A
   gate definition, so it is yours.
5. **Know that two security-invariant tests were modified**, escalated here as `AGENTS.md` §3
   requires: REQ-RTR-004's test and the D-126 boundary test. Both were made STRICTER after the
   Stage 4.0 seat showed each passing a mutant that broke its invariant. Every old assertion is
   kept, and the mutants are recorded in the W5 close.
6. **Read §1b.** Four decisions were yours in session; one is the council's, overturned by a
   measurement.
7. **Make the milestone commit** (D-117 §5 keeps it yours), after your own `make check`.

## 1. What shipped

| Criterion | Citing test | Status |
|---|---|---|
| REQ-FIX-001 Pareto admits equality on one axis | `tests/unit/test_pareto_dominance.py` | ✅ W1 |
| REQ-FIX-002 startup refuses an unservable database | `tests/unit/test_startup_schema_validation.py` | ✅ W1 |
| REQ-FIX-003 attribution changes the fingerprint | `tests/unit/test_refresh_attribution_fingerprint.py` | ✅ W1 |
| REQ-FIX-004 an unrun leg is not a pass | `tests/unit/test_runner_accounting.py` | ✅ W1 |
| REQ-UNC-001 no order inside the margin | `ios/EngineTests/UncertaintyTests.swift` (property over every margin) | ✅ W2 |
| REQ-UNC-002 a count, never "confidence" | `UncertaintyTests.swift::EvidenceBreadthTests` | ✅ W2 |
| REQ-UNC-003 dated, or named | `tests/unit/test_uncertainty_contract.py` | ✅ W2 (artifact lag) |
| REQ-ASK-001 focus, keyboard, submit | `ios/EngineTests/FrontDoorTests.swift::SubmissionTests` + source contract | ◐ W3 (keyboard unverified) |
| REQ-ASK-002 echo + one-tap correction | `FrontDoorTests.swift::EchoTests` | ✅ W3 |
| REQ-ASK-003 unmeasured → ranking + sentence | `FrontDoorTests.swift::UnmeasuredQuestionTests` | ✅ W3 |
| REQ-ASK-004 no stale overwrite | `FrontDoorTests.swift::RequestGateTests` | ✅ W3 |
| REQ-CMP-004 a score says what it is out of | `ios/EngineTests/ScoresTests.swift`; call sites pinned by `test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line` | ✅ W4 (per metric family) |
| REQ-DTL-001/002 detail screen, vendor links | — | → M14 (council ruling F2) |

**Criteria diffs since plan signature:** REQ-UNC-001's verification reads "overlapping ranges"
where it read "a shared band" (owner, 2026-09-15; plan §8 row 4).

## 1a. Per-wave table

| Wave | Tier | Review | Findings | Tests Δ | Escalations | Commit |
|---|---|---|---|---|---|---|
| W1 | HIGH | C-R + Tester | 2 BLOCKING, 4 MAJOR, all closed | +68 Py | none | `3440abe` |
| W2 | HIGH | C-R + re-review + Tester + re-run | 1 BLOCKING (escalated), 2 MAJOR, 10 MINOR, 4 NIT | +14 Py, +31 Swift | criterion meaning → owner | `10a521c` |
| W3 | HIGH | C-R + 2 re-reviews + Tester + re-run | C-R: 2 BLOCKING, 3 MAJOR, 8 MINOR. Tester: 3 BLOCKING. Re-reviews: NEW-1 (MAJOR), resolved as a chosen trade-off and endorsed by the seat; the rest closed or ledgered | +2 Py, +34 Swift | none | `cda57b1` |
| W4 | MED | combined + re-review | 1 MAJOR (a stay-green fault with no test: both call sites could print a bare score), 7 MINOR, 3 NIT. MINOR-5 queued to M14, the rest closed. Re-review: all eleven dispositions confirmed, 31 of 33 mutants killed, three NITs fixed | +1 Py, +18 Swift | MAJOR-1, by class | `3b13b11` |
| W5 | HIGH | Stage 4.0 + re-verification | 3 MAJOR, 3 MINOR, 2 NIT, no BLOCKING. Five fixed with tests; the waivers ledgered with a control review (D-141); the Swift floor escalated; NIT-2 queued to M14 | +4 Py, +1 Swift | two security-invariant tests modified (made stricter); gate floor | `a5e3c89` |

## 1b. Decisions made on your behalf, and the ones you made

- **Yours, in session:** M12 signed · D-138 (margin and age on `/v1/categories`) · wave commits and
  pushes under D-117 · rank ranges over the council's greedy bands.
- **Mine:** rounding concedes one step toward "tied", so it can never order a tie (D-138) · the
  budget client code deleted with its tests, `/v1/budgets` kept · ECI prints no number (council
  C1, D-140) · D-139 written late for council ruling A3.

## 2. Git record

- Range `335d844..a5e3c89`: five wave commits under `Claude <noreply@anthropic.com>`, each with
  `GP-Agent`/`GP-Task` trailers; none authored as you. The capture commit on top of it carries
  this report, and the milestone commit is yours.

## 4. Security & invariants

- Stage 4.0: **PASS WITH FINDINGS, no BLOCKING** (`docs/reviews/m13-security-review.md`). The web
  and API baseline holds, and nothing the reader types leaves the device.
  - MAJOR-1: the `/health` memo read `servable` for an artifact the process could not open. Fixed:
    the key now carries ctime, inode, mode and owners, with two negative tests through `/health`.
  - MAJOR-2 and MINOR-2: two invariant tests passed mutants that broke their invariants. Both now
    assert data flow and stored fields.
  - MAJOR-3: the waivers had never reached the ledger. Now W-088..W-090 and D-141.
  - Re-verification (`docs/reviews/m13-security-rereview.md`): **PASS WITH FINDINGS**. Every MAJOR is
    closed, each reproduction re-run on a tree the seat rebuilt itself. Two new MINOR:
    - MINOR-4: four more routes into `task` that the rewritten test missed. Fixed after the
      re-read, with all four shown RED; the seat has not read that fix.
    - MINOR-5: C2b accepts a proposed ADR as a discharge. Recorded in §0 item 3.
- Invariant added: `SCORE_ARITHMETIC_PERMITTED` names the one file allowed to compare served scores
  (D-138), and a second file fails the gate.

## 5. Ledgers

- **Waived, and now counted:** the pulled-forward security pass on W1, W2 and W3. These are
  W-088..W-090, the seventh acceptance of V3C-78, reviewed as D-141 (proposed, yours to ratify).
- **Escalated:** W-091, the Swift test floor.
- **Diet:** `AGENTS.md` was 156 lines against its 150 cap, and had been since M11-W1; neither the
  M11 nor the M12 closure checked. The Done Evidence template moved to `.agents/rules/practices.md`,
  and the file is 149.
- **Accepted:**
  - `rankRanges` is quadratic, at most 250k comparisons per answer at the default publication cap.
  - ECI's number is gone from the card.
  - The terminalbench fix is not visible yet.
  - **The wording tier's decline exit declines some measured tasks.** A task that involves a photo
    is one example. No threshold separates those tasks from genuinely unmeasured questions, so a
    false decline is labelled and puts the closest surfaces one tap away (W3 close, ledger L5).
  - One error of the forbidden kind remains on the probe: "compose a song for my wedding" is
    answered from chat as measured.
- **Risks to M14:**
  - the device build (`DEVELOPMENT_TEAM` set zero times) and the localhost-only engine
  - the image-edit surface and typed pricing
  - the detail screen
  - `coverage-by-req.md` has no M10–M12 rows
  - two `% resolved` surfaces share one score form, told apart only by their section titles (W4
    MINOR-5)
  - an abandoned on-device model call is not waited for, so repeated questions into a hung model
    can stack on the reader's own device (Stage 4.0 NIT-2)
  - C2b accepts a PROPOSED ADR as a discharge. Making it read the ADR's status is a gate change,
    and so the owner's (re-verification MINOR-5)

## 6. Architecture delta

M13 changed what the product claims, not what it computes. The engine's numbers are almost
untouched: one predicate (Pareto dominance) was wrong and was fixed. Everything else moved at the
boundary where numbers become sentences.

The engine had always held two facts it never published: the margin inside which it calls two
models indistinguishable, and how old the second benchmark behind a pick is. D-138 publishes both on
the discovery route, `/v1/categories`, and leaves the answer payload's field sets frozen. The client
turns the margin into a RANGE of positions for every model: models clearly ahead and clearly behind
are counted, and everything else is "could be here". Two models inside the margin of each other
always get overlapping ranges, which a single rank number can never guarantee, and a property test
asserts it. The rounding of served scores is conceded toward "tied", so rounding can never create
an order the engine does not see.

The home screen went from a control panel to one input. The router's choice is echoed in the
reader's own words with a one-tap correction, an unmeasured question is answered and labelled, and
every load carries a ticket so a slow answer cannot replace a newer choice. All of that logic lives
in `ios/ModelRanking/Engine/`, where `swift test` runs it. `ContentView` renders, and a source-contract
test pins the calls and the arguments that carry the engine's facts, because the app still has no
UI test target.

**What could break.**
- A metric the client does not know renders with the engine's own label and exact positions.
- An engine older than D-138 renders exactly as M12 did.
- A future client that sorts the ranking breaks the ranges' meaning; Ruling A's tripwire still
  forbids it.

**What a maintainer must know.** The one place allowed to do arithmetic on a served score is
`Uncertainty.swift`, and the gate says so by name.

---
*Generated from raw referents at closure. Owner sign-off: `<initials/date>`.*
