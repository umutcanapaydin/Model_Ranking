---
record_type: ratification
id: closure-report-m11
status: draft
date: 2026-08-23
---
# Closure Report — M11: the reviewer became somebody else, and then a user arrived

> **AWAITING THE OWNER'S SIGNATURE.** Section 0 is what needs him. Every figure below was measured
> at the closing tree rather than reported by the thing that produced it.

## 0. What needs the owner

1. **Run `./runner` and make the milestone commit.** The agent does not commit as the owner
   (AGENTS.md §3). Eighteen commits this milestone carry the `GP Agent (Claude Code)` identity and
   `GP-Agent:` / `GP-Task:` trailers, under the standing permission he gave on 2026-08-22 — this is
   the first milestone in the project's history where agent work is distinguishable from his in
   `git log`, which is what V4C-64 exists for.
2. **REQ-RUN-002 is NOT MET and it is a signed plan promise.** The 12-hour refresh has still never
   run unattended. One command starts it —
   `/Users/umutcanapaydin/Desktop/ILGAR/model_ranking/scripts/enable_refresh.sh` — and two cycles
   then have to be OBSERVED. Worse than the gap: the requirement was never written into the PRD at
   its wave, so nothing traced it and W3 closed without noticing (W-071).
3. **Two gate-definition changes are his and only his.** `shellcheck` is not installed and no gate
   lints any shell in this repository, across `runner` and six scripts, while this milestone
   shipped three shell defects nothing looked for (W-074). And Stage 4.3 reading `/health.evidence`
   to fail a deploy (W-058) waits on there being a deploy.
4. **Nothing deployed, fourth milestone.** D-123, W-030, W-031. By his own sequencing: local tests
   first, then his phone, then the App Store.

## 1. What shipped (from the signed plan)

| REQ-ID | Criterion | Citing test (able to fail) |
|---|---|---|
| REQ-REV-001 | K.7 is executable: a passing close cites an independent review, or names a ledger row | `tests/unit/test_review_seat_gate.py` — 20 tests, including two through the real entry point and one that renames the row |
| REQ-IOS-001 | The Engine layer is executed by a gate | `ios/EngineTests/` (59 tests), `Makefile` `swift-test` with a count floor, `runner` |
| REQ-IOS-002 | The router's boundary proven IN SWIFT | `ios/EngineTests/RouterBoundaryTests.swift`, `ModelOutputBoundaryTests` |
| REQ-IOS-003 | The 503 can be PRODUCED on demand | `tests/unit/test_unavailable_after_boot.py` |
| REQ-API-010 | `/v1` gives ONE account of a query | `tests/unit/test_budgets_endpoint.py` — the served cap reproduces the served `eligible_count` |
| REQ-RUN-001 | A person has operated the product and written down what happened | the owner's two sessions, 2026-08-22 and 2026-08-23; `scripts/simulator_session.sh` |
| REQ-RUN-002 | Two unattended refresh cycles, observed | **NOT MET.** See §0.2 |

## 1a. Per-wave table

| Wave | Risk | Delivered | Review | Record |
|---|---|---|---|---|
| W1 | MED | D-133; the seat gate; `seat` in the schema; `docs/reviews/` governed | `docs/reviews/m11-wave-1-review.md` — BLOCKING, 3+5+5 | `docs/plans/m11-wave-1-close.md` |
| W2 | HIGH | `ios/Package.swift` over the shipping sources; 59 Swift tests in `make check` and `runner` | `docs/reviews/m11-wave-2-review.md` — BLOCKING, 3+4+8 | `docs/plans/m11-wave-2-close.md` |
| W3 | MED | `/v1/budgets` (D-134); `/health.evidence`; `contract-tests` green for the first time; the simulator session | folded into Stage 4.0 | `docs/plans/m11-wave-3-close.md` |
| W3.5 | MED | The card design; six defects the owner found by using the app | folded into Stage 4.0 | this report §4 |
| W4 | LOW | Stage 4.0, capture, this report | `docs/reviews/m11-security-review.md` — CONDITIONAL PASS, 1+2+10 | `docs/plans/m11-wave-4-close.md` |

## 1b. Decisions made on your behalf

- **The K.7 gate stopped asking about row labels.** The first repair would have been a longer list
  of recognised names; that is the same defect with more words in it. The rule moved to something
  the record answers as a whole.
- **`/v1/budgets` is a sibling resource, not a payload revision.** D-134 states the reading it
  rejects, because "any addition to `/v1` is a revision" would make the freeze a ban on the surface
  rather than a promise about the payload.
- **`contract-tests.yml` triggers are scoped by path.** Running five live endpoints on every push
  would hammer other people's services and go red for reasons nobody caused, and the answer to a
  flaky red is a named quarantine, never `continue-on-error`. Written down while nothing is flaky.
- **The design pass kept three shapes.** A card, a badge, a section title. Every disclosure survived.

## 2. Git record

`1069907..HEAD` — **18 commits, 49 files changed, 5,059 insertions(+), 426 deletions(−)**.
All eighteen carry the agent identity and `GP-Agent:` / `GP-Task:` trailers. The owner makes the
closing commit.

## 3. Trust telemetry

- Tests: **666 (M10) → 714 Python**, plus **59 Swift where there were none.** 12 skipped, unchanged.
- Governed records: 50 (M10) → **61**. `docs/reviews/` is governed for the first time.
- Gates in `make check`: lint, typecheck, test, coverage-floor, check-records, selftest,
  install-check, wave-check-all, conformance-gate, **swift-test** — exit 0.
- Fault injection: **21 mutants across the milestone, 21 killed.**
- **Independent reviews: three, all leaving a file, all returning BLOCKING or CONDITIONAL.** Every
  blocking finding was in the machinery, never in the served product.
- Control bypasses: **zero new K.7 waivers.** The count stopped at four (W-055, resolved by D-133).

## 4. Security & invariants

Stage 4.0: `docs/reviews/m11-security-review.md` — **CONDITIONAL PASS**, run by a seat that wrote
none of the code, under D-133.

One BLOCKING (**W-072**): the K.7 gate could be switched off by renaming a table cell, and the test
written to catch that used a label still containing the word "review". Two MAJOR: **W-073**, the
simulator session's engine survived its own shutdown because `( cd … && … ) &` forks a subshell;
**W-074**, the shell in this repository is unlinted. All fixed or escalated; ten MINOR ledgered.

**Invariants verified by measurement, not assertion:**
- **D-115 / D-125** — the `/v1` payload is **byte-identical** between the M10 tree and HEAD across
  4 tasks × 3 budgets, 8 adversarial inputs and `/v1/categories`: same md5 on both trees.
- **D-104** — `git diff 1069907..HEAD -- src/` on the scoring path is two files, one a docstring.
- **INV-23, D-116, D-129** — hold, each with its evidence stated in the record.
- `/v1/budgets` takes no input and touches no database; `/health.evidence` collapses every
  diagnostic to one token and costs 0.92 ms; launchd runs as the user with no writable path in the
  chain; CI has no `pull_request_target`, all action SHAs pinned; gitleaks clean over 55 MB.

## 5. Ledgers

**Closed:** W-001, W-012, W-014, W-015, W-024, W-025, W-027, W-032, W-033, W-034, W-038, W-039,
W-041, W-046, W-047, W-049, W-053, W-055, W-056, W-059, W-061..W-068, W-072, W-073 — **27 rows.**
Eleven of them were closed by an audit that found they had been resolved by earlier work and never
struck off.

**Opened and still open:** W-057, W-058, W-060, W-069(fixed), W-070(fixed), W-071, W-074.
**Still carried:** W-030, W-031, W-035, W-036, W-040, W-054. **28 open in total**, down from a pile
that read as 41 and was mostly stale.

## 6. Architecture delta — prose

Two things changed shape this milestone and neither is a feature.

The first is that **the reviewer became somebody else.** For eleven milestones K.7 — the rule that
the reviewer never authored the code — described a situation that did not exist in a single-agent
lane, so the author reviewed their own work and said so, four times, each recorded and each closed
green. D-133 makes it executable: the reviewing seat is a separate session that reads its policy
from the protected base ref and leaves a FILE, and a close that cannot cite one must name the
ledger row for the bypass. Three seats ran under the new rule this milestone and all three returned
BLOCKING. **Every blocking finding was in the machinery built to enforce a rule, not in the product
being ruled** — which is the honest summary of what independent review buys: not better code, but
the discovery that the controls were weaker than the records said.

The second is that **1,093 lines of Swift stopped being unexecuted.** `ios/Package.swift` compiles
the same sources the app ships, with no second copy and no change to the project file, and 59 tests
run from `make check` and from `runner` behind a count floor that fails when the suite stops being
discovered. The scoping is deliberate and stated everywhere it matters: this covers the Engine
layer, where a defect changes what a reader is TOLD, and not SwiftUI.

And then a third thing happened that is not architecture at all. **The owner gave the app to other
people**, and one of them is a 60-year-old CFO. A person using it for twenty minutes found six
defects that eleven milestones of gates had not, because every one of them is about what a reader
concludes from what they can see — a router that could not say "I do not measure this", a surface
answering under another surface's name, a list that repeats itself, a strip that loses the reader's
place. Then five requirements arrived that nobody inside this project would have written, and four
of them are one finding: **the product explains what it measured in the language of the
measurement.** `161.7 ECI`. `$1.03/1M`. `Abstract reasoning`. All correct. None usable.

## 7. The carried question, for M12

Eleven milestones specified this product, and every requirement written before 2026-08-23 came from
someone who already knew what a benchmark was.

The fix for each of the CFO's five items is easy and obvious the moment it is stated. **The question
is why none of them was ever stated**, and the answer is not carelessness — it is that a
correctness culture measures whether a number is right and has no instrument at all for whether it
is understood.

So: **what would this project have to measure to catch the next one of these before a user does?**
Not a gate that checks wording. Something that makes *"would a stranger understand this"* a question
with an answer, in a repository whose entire discipline is built on answers that can be executed.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-23 · Range: `1069907..HEAD`
