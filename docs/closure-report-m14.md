---
record_type: closure
id: closure-report-m14
status: draft
process_version: v5.0
date: 2026-09-21
---
# Closure Report — M14: the catalogue answers more of the questions people actually ask

> **Read §0 first.** It is what needs you. Everything below it is evidence for the claims in it.
> Every figure was measured at the closing tree, `fc7fe5b` plus the closure wave; where a figure
> could only be measured on your machine, it says so and names the run.

## 0. What needs the owner

1. **Run the runner once more, and expect one test that may legitimately fail.**
   `~/Desktop/terminal_output/model_ranking/runner.sh`. The closure wave added
   `testTheTwoNewSurfacesAreReachableByAsking`, which runs Apple's real embedding router against
   two plain questions ("summarise this 40 page contract pdf for me" → `document`, "is this quote
   real or did it invent the citation" → `factuality`). Nothing in the agent lane can run it. If it
   comes back red, the HINT is wrong, not the test, and fixing the hint is a ten-minute change.
2. **Rule on the detail screen (W-105).** M14 took the unit off every card and row on your ruling
   (D-143). The plan's stated mitigation was "it stays available on the detail screen" — and there
   is no detail screen in the app. The closure seat found it. Two honest options: build it in M15
   (it also holds the price, which is where your "price as a hidden attribute" note lands), or rule
   that the unit is simply gone and amend REQ-DTL-001/002 out of the carried list.
3. **Rule on D-141, which has now been bypassed five times** (W-106). It says a HIGH wave owes a
   security pass, and that a waiver must be written in the warnings ledger where the counter reads
   it. It has been `proposed` since M13. M14 waived the pass on both its HIGH waves. Either ratify
   it — and the next HIGH wave cannot close without the pass or a counted waiver — or refuse it, in
   which case W-090's `C2b-reviewed` marker comes off and the project stops pretending to count.
4. **Two gates only work on your machine (W-108).** `make lint` runs `ruff check src tests scripts`
   while CI runs `ruff check src tests`, and on a newer ruff the Makefile form fails on a finding
   your version does not raise; 45 tests fail on any clone without `advisor.db`, which is
   gitignored. Consequence: no independent seat can reproduce "918 passed", and your CI test jobs
   are almost certainly red with nothing requiring them. Both fixes touch `.github/`, your surface.
5. **Sign, then commit.** The closure wave is uncommitted; `commit_w5.sh` in the runner folder
   makes the one commit after `make check`.

## 1. What M14 shipped

| | |
|---|---|
| **The catalogue answers more questions** | Two surfaces, `document` ("Working with documents", 29 ranked models) and `factuality` ("Getting facts right", 59), from boards of the LMArena dataset already licensed. Eleven surfaces answer on the live artifact. |
| **A price defect that was live** | An image model's per-image price was published as a text model's per-token price. `ModelRule.modality` refuses the match and counts it apart from registry drift (W-092). |
| **The refresh job runs again** | 24 days of silence, exit 78 on every trigger. The cause was macOS privacy protection on `~/Desktop`, for the files launchd opens on the job's behalf. Program and logs moved out (W-096) — and, after the closure seat, the job can now be installed from this repository rather than by hand (W-100). |
| **The product records what it cannot answer** | Every declined question is kept on the phone with a count, readable most-asked-first from the tray. Nothing leaves the device. This is the input to M15's coverage work. |
| **One score, out of 100, per surface** | Your ruling (D-143). Percentages as they are; an Elo score as how often people prefer the model over one at the surface's pinned anchor; ECI still rank-only. The card's sentences and the tie note speak the same scale. |

## 2. What it cost, and what it did not do

- **The tenth surface was refused by its own measurement.** W1 set out to add image editing and
  measured the ranked population at zero: every model on that board is priced per image, and the
  engine only ranks what somebody can buy at a per-token price. The plan's own stop condition
  fired. That is the milestone working, and it is why `document` and `factuality` exist instead.
- **The detail screen was not built** (§0 item 2), and four carried requirements left the milestone
  with no home until the closure seat named them (W-105).
- **Elo surfaces read lower than percentage surfaces.** Live: `document` 57.0, `factuality` 57.2,
  `assistant` 65.0, `web-dev` 79.3, against percentage leaders of 72.8–100. You accepted this
  knowingly (D-146, option A). It is D-143's revisit trigger and it is likely to fire.
- **No Tester seat was convened in any wave**, and the security pass was waived twice (W-106).

## 3. The independent seat's verdict, and what it caught

`docs/reviews/m14-closure-review.md`, `seat: independent`, 2026-09-21. **BLOCKING**, 8 MAJOR,
11 MINOR, 11 mutants run.

Two findings no gate in this repository could have caught:

- **The privacy invariant's test could not fail.** REQ-GAP-001 says nothing the reader types leaves
  the device. The test searched the register's own section of `FrontDoor.swift`; the reader's words
  are recorded from `ContentView.swift`. A four-line `URLSession` POST of the typed question
  survived every gate, `swift test` included. No such code existed — the hole was in the proof.
  Fixed, and the seat's mutant was re-run red (W-099).
- **The refresh job this milestone repaired could not be installed.** The plist was rewritten to run
  a wrapper under Application Support; the installer still copied the plist alone, and the script
  W-096 named as the remedy did not exist in the repository. Anyone installing from this repo got a
  job whose program was missing: the same outage, reinstated by its own fix (W-100).

Six more MAJORs are fixed (W-101, W-102, W-103, W-104, W-107, W-109); three are escalated to you
(W-105, W-106, W-108). Full disposition table in the review record.

## 4. Evidence

- **Gates at the closing tree:** `pytest 918 passed / 13 skipped`; `ruff check src tests` clean;
  `check_records PASS`; `wave_check_all PASS` (35 v5.0 records); `conformance_gate PASS` (6
  standing exemptions, all pre-M14, all still firing); `mypy src` clean. **Swift:** the owner's
  `make check` of 2026-09-20 reported `swift-test PASS: 241 test(s) (floor 241)`; the closure
  wave's one new Swift test is not in that count.
- **Criteria trace:** `docs/coverage-by-req.md` §M14 — twelve rows, each with the test that would
  fail if the criterion were violated.
- **Wave records:** `docs/plans/m14-wave-{1,2,3,4,5}-close.md`. **Reviews:**
  `docs/reviews/m14-wave-1-review.md`, `m14-wave-2-review.md`, `m14-wave-3-4-review.md`,
  `m14-closure-review.md`, `m14-category-calibration.md`.
- **Decisions this milestone added:** D-142 (answer the questions people ask), D-143 (one score out
  of 100), D-144 as you amended it (per-source carry-forward, ~30-day drop → M15), D-145 (a new
  surface's floor follows the rule the product ships), D-146 (the anchor is its own pinned field,
  published on `/v1/categories`).
- **Commits:** `cb8d9e6` (M13 signed), `fb02ebe` (W1), `3e06512` (W2), `fc7fe5b` (W3/W4), plus the
  closure wave, uncommitted at the time of writing.

## 5. Carried into M15

`docs/plans/m15-plan.md` §1 holds the full list with its evidence. In one line each: the detail
screen and the four homeless requirements (W-105); D-141 and the waiver count (W-106); the two
gates that only reproduce on your machine (W-108); per-source carry-forward (D-144); which floor
rule is right for all eleven surfaces (W-094); the retrieval board and image pricing; the
app/harness split you asked for; and the first read of the gap register, which is the only thing in
this project that can tell us what people actually ask.
