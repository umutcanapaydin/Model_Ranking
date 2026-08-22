---
record_type: ratification
id: closure-report-m9
status: draft
date: 2026-08-22
---
# Closure Report — M9: The product keeps itself current, and finds out what one machine costs

## 0. What needs the owner

1. **One command turns the schedule on.** `deploy/com.hcs.modelranking.refresh.plist` is written,
   lint-clean and NOT installed:
   `cp deploy/com.hcs.modelranking.refresh.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.hcs.modelranking.refresh.plist`
   Until it is loaded, nothing runs every twelve hours. Loading a background job onto someone's
   machine is not an agent's decision, which is why it waits here.
2. **REQ-REF-007 cannot be met on one machine, and that is this milestone's answer to M8's carried
   question.** D-116 says ingestion never runs on the serving host; the owner's Mac is both. The
   structural half is enforced and tested; the physical half needs a second host. **A separation
   you cannot violate because you only have one machine is not a separation you have verified.**
3. **Two independent seats ran and BOTH returned BLOCKING**, six findings between them, every one
   in a row that read COVERED at the time. The Stage-4.0 seat found that a lock added in W3 to fix
   a concurrency finding **restored the same finding**, and that a MAJOR raised at the W2 review had
   been left unfixed and came back as BLOCKING. W1 and W3 had no seat of their own.
4. **Carried and unresolved from before M9:** W-027 (`contract-tests.yml` has still never run; 21
   commits unpushed), W-030 and W-031 (unverifiable without a deploy), W-035..W-039, W-044,
   GPF-001..006.

## 1. What shipped

**The evidence stops being as fresh as the last time somebody remembered.** `python -m
app.workflows.refresh` builds a candidate, compares what it would SERVE against what is being
served, and publishes, refuses or does nothing — with a durable record of which, and a `launchd`
schedule waiting on one command.

**And arena came back.** Not part of the plan: W-024 recorded a source as "upstream down" for the
whole of M8, and the diagnosis was wrong. Only the `filter` endpoint fails — with no `where` clause
at all, so it was never our query. The client reads the board as the ordered prefix of `/rows` now:
**394 rows, 394 models, and all NINE surfaces answer for the first time.**

## 1a. Per-wave table

| Wave | Record | Delivered | Gate at close |
|---|---|---|---|
| W1 | `docs/plans/m9-wave-1-close.md` | One cycle by hand; the hot swap PINNED rather than built | 611 passed / 12 skipped |
| W2 | `docs/plans/m9-wave-2-close.md` | The refusal rule (D-128) and the record (D-129) | 620 passed / 12 skipped |
| W3 | `docs/plans/m9-wave-3-close.md` | The lock, the escalation counter, the schedule, the two owed tests | 638 passed / 12 skipped |

## 1b. Decisions made on your behalf

- **D-128 / D-129 / D-130** — the plan's three §5 questions, decided under your instruction to
  proceed. Each is one constant or one file away from being reversed, and each says so.
- **D-128 was AMENDED after review**: prices became a third refusal condition (a price is also a
  hard filter, not merely a reported number), the boundary moved to `<=`, and its worked arithmetic
  was corrected — it was off by one in both examples. **The 25% figure itself did not move**, on the
  reviewer's reasoning that every degradation they landed passes at any value of it.
- **arena's `minimum_rows` moved from 1 to 250.** One could not catch anything.
- **The record's scratch file and the lock are cleaned up automatically**; a lock whose holder pid
  is gone is reclaimed at once rather than after two hours.

## 2. Git record

`1fd9df4..HEAD` — 6 commits, 17 files, +2759/-60. Every commit carries the agent's own identity and
the `Co-Authored-By` trailer; none is attributable to the owner (V4C-64).

**One commit went in on a RED gate** (`fbba5ba`), and the next one says so in its subject. The
`check_records` exit code was read after the commit rather than before it — the third instance in
this project, the previous two also recorded.

## 3. Trust telemetry

`make check` exit 0 at the closing tree: **638 passed / 12 skipped**, coverage 87.9% against the
85% floor, `refresh.py` 93% against the 60% per-module floor, ruff and mypy clean, `check_records`
PASS, `wave-check-all` PASS on 15 v5.0 records, `make secrets` clean.

**Fault injection: the author wrote 32 mutants across three waves and reported all killed. An
independent seat wrote 40 against the same module and 8 survived.** Six were genuine test gaps and
five of those sat on the status record — the artefact the owner actually reads. All eight now die.

## 4. Security & invariants

`docs/reviews/m9-security-review.md` — Stage 4.0, run by an independent seat: **BLOCKING as
returned, 3 blocking / 6 medium / 6 minor, all three blocking fixed inside the milestone.** Two of
the three were in code written during this same milestone, one of them the third instance of a
defect class this module had already fixed twice. The third was not about code at all: the arena
restoration had no authorization the REPOSITORY could show, which is now **D-131**.
`docs/reviews/m9-wave-2-review.md` — the W2 code+tester review, **BLOCKING with three findings**,
all three fixed inside the milestone.

Engine invariants held: D-104, D-105, D-109 (the refresh reuses the engine's rounding rather than
inventing its own — and a second, quieter rounding at a different precision was found and removed),
D-115/D-124/D-125 (`/v1` untouched; the revision window remains SPENT), D-116 (structurally, see
§0.2), D-121 (an optional source blind at build time still publishes — the freeze direction, and
correctly defended).

## 5. Ledgers

Opened and CARRIED to M10 from the Stage-4.0 review: **W-049** (nothing bounds what an
upstream can publish UPWARD — the failure mode the refresh created rather than exposed), **W-050**
(unbounded aggregate allocation across pages), **W-051** (four environment assumptions nothing
checks). Opened and CLOSED inside this milestone: **W-046** (no escalation on consecutive refusals),
**W-047** (nothing serialised two refreshes), **W-048** (two criteria MET with no test). Also closed:
**W-024** (arena restored) and eleven M7 carry-overs, five of which turned out to have been fixed at
M6 with nobody closing the rows.

Carried: W-027, W-030, W-031, W-035..W-039, W-044, GPF-001..006.

## 6. Architecture delta — PROSE

**The product gained a second process, and that is a bigger change than the code suggests.**

Until M9 this system had one shape: a human runs a build, a human checks the output, a human
restarts a server. Every control in it was designed with that human in the loop, and most of them
depend on it more than their tests admit — a build that "fails loud" is loud to somebody who is
reading, and an artifact that "discloses staleness" discloses it to somebody who is looking.

The refresh removes that person. What it needed, therefore, was not more correctness but a
different KIND: controls whose failure is visible when nobody is watching. That is what the refusal
rule, the status record, the escalation counter and the lock are, and it is why the milestone's
worst defect — a cycle that crashed while its record said `published` — was so much more serious
than it looked. In the old shape, a crash was a traceback somebody read. In the new one it was a
green light.

**The second change is smaller in code and larger in what it revealed.** Writing REQ-REF-007 made
D-116 concrete, and it could not be satisfied: there is one machine. Three milestones of "deployed
soon" had left a load-bearing separation as an untested claim, and it took a requirement that
depends on two hosts to make that visible. The refresh runs where the engine runs, and the only
thing keeping ingestion out of the serving process is that the code does not import it — enforced,
tested, and not the same as being unable to.

**The third is the fingerprint, and it is a design lesson about comparison.** "Has anything
changed" sounds like a question about the data. It is a question about the READER: what a reader
would notice is the definition, and any hand-written list of fields is a guess at that definition
which drifts the moment the payload grows. Deriving it from the row and naming the exclusions
inverts the failure: a new published field is covered by default, and dropping one requires saying
so out loud.

## 7. Definition of done

| Requirement | State |
|---|---|
| `make check` exit 0 | ✅ 638 / 12 |
| A refresh cycle demonstrated end to end against real sources | ✅ published, then unchanged, then published again after arena returned |
| The degradation guard proven on a deliberately-degraded candidate | ✅ blinded surface, 33% loss, exactly 25%, and a pricing feed that blinds a budget |
| Every criterion has a citing test PROVEN RED | ⚠ **PARTIAL** — REQ-REF-005 and REQ-REF-007 are half-met for reasons outside the code (§0.1, §0.2); the other five are covered, `docs/coverage-by-req.md` |
| Fresh-eyes review per D-122 | ⚠ **PARTIAL** — W2 reviewed independently (BLOCKING, 3 findings) and Stage 4.0 reviewed the whole range independently (BLOCKING, 3 findings). W1 and W3 had no seat of their own, and the Stage-4.0 pass covered their code |
| ADRs for the three §5 decisions | ✅ D-128, D-129, D-130 — and D-130's claim to answer §5.2 is corrected in W-046 rather than in the ADR |
| Retrospective (M ≥ 3) | ✅ `docs/retrospectives/m9-retrospective.md` |
| Dated `docs/EXPERIENCE.md` entry | ✅ |
| `note.txt` refreshed | ✅ |
| **Quarterly handover (M % 3 == 0)** | ✅ `docs/handovers/handover_q3.txt` |
| Deploy (4.3) | ❌ **NOT DONE** — D-123 undischarged for a third milestone; §0.2 is what that now costs |

**M9 closes AGENT-side with two rows partial and one red, all stated rather than absorbed.** It
awaits the owner's signature.
