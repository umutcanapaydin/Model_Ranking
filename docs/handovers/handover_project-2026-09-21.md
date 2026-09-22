---
record_type: handover
id: handover-project-2026-09-21
status: draft
date: 2026-09-21
---
# HANDOVER — the whole project, 2026-09-21

**For whoever picks `model_ranking` up next, human or agent, assuming they know nothing.** One
file, fourteen closed milestones, one in progress. It supersedes `handover_q4.txt` on STATE (that
one stops at M12) and stands beside two others rather than over them: `handover_rocky.txt` is still
the fullest account of the DOCTRINE, and `handover_m15.md` is the short operational brief for the
milestone now open.

Written by: the lead agent (Claude Code, cloud lane, D-117), which built M14 and opened M15.
**Every figure was measured, and says where.** This project has been wrong about its own numbers
three times (W-093 is the record of one), and the habit that fixed it is citing the run.

---

## 1. What this is

A person asks, in their own words, *what should I use for this, and what will it cost me?* The
product answers with a named model, a score, a price and the evidence behind it — or says plainly
that nobody measures what they asked.

- **An engine** (Python, FastAPI, SQLite) ingests free-and-legal benchmark and price data, decides
  every number, and serves it at `/v1`.
- **An iOS app** (Swift, SwiftUI) renders the answer and writes the sentences. It decides no
  numbers — D-104 — and, since M13, its front door is a single question field.
- **A governance harness** (records, gates, independent review seats) exists because the product's
  one unforgivable failure is a confident wrong answer.

Nothing is deployed. Nothing bills. The app has run only on a simulator. The product is real in the
sense that its data is live and its answers are defensible; it is not real in the sense that no
stranger has ever used it.

**The doctrine, in one line: never present something unmeasured as measured.** If a fact and a
sentence disagree, the fact is right and the sentence is the defect.

---

## 2. State, measured 2026-09-21

    HEAD              855b44a  (local == origin/main, pushed)
    make check        exit 0 on the owner's Mac, 13:52
      Python          919 passed, 12 skipped, coverage 88.76% (floor 85%)
      Swift           242 tests (floor 242)
      records         check_records PASS · wave-check-all PASS, 35 v5.0 records
      conformance     conformance-gate PASS, 7 findings, all exempted and all still firing
    live artifact     refresh published 10:23 UTC, exit 0, surfaces_answering 11
    catalogue         74 models · 72 with a price median · 2427 score rows · 13 benchmarks
    governance        146 ADRs (D-100..D-146, D-141 proposed) · 109 ledger rows · 110 records

M1–M14 closed and signed. M15 open: its measurement wave is recorded, nothing built yet.

### The eleven surfaces

| id | what the reader sees | board | metric | floor | window | tie margin |
|---|---|---|---|---|---|---|
| coding | Coding | SWE-bench Verified | % resolved | 65.0 | 6.0 | 1.5 |
| agentic-coding | Agentic coding | DeepSWE | % resolved | 50.0 | 6.0 | 1.5 |
| assistant | Chat | Arena text | elo | 1400.0 | 30.0 | 8.0 |
| everyday | General knowledge | Epoch Capabilities Index | ECI | 149.9 | 3.0 | 0.5 |
| expert | Hard science questions | GPQA Diamond | % correct | 83.6 | 5.0 | 5.0 |
| mathematics | Mathematics | AIME (mock) | % correct | 84.4 | 10.0 | 9.5 |
| computer-use | Operating a computer | TerminalBench | % resolved | 53.4 | 5.0 | 0.8 |
| abstract | Puzzles & pattern finding | ARC-AGI | % correct | 72.8 | 5.0 | 1.0 |
| web-dev | Web development | WebDev Arena | elo | 1478.9 | 100.0 | 6.8 |
| document | Working with documents | Arena document | elo | 1467.5 | 35.0 | 8.7 |
| factuality | Getting facts right | Arena factuality | elo | 1450.6 | 20.0 | 4.0 |

Every number in that table is DATA in `src/app/workflows/categories.py`, never a code branch. A new
surface is a map entry, and `test_categories_are_data_not_code` is the test that keeps it so.

---

## 3. How the milestones got here

| | what it was for | what it taught |
|---|---|---|
| **M1** 08-11 | data layer + a coding recommendation | the shape: ingest → registry → rank → recommend |
| **M2** | two more sources + an assistant category | a parser's dropped row must be COUNTED, never silent |
| **M3** | subscription plans | curated data needs per-row provenance as much as fetched data |
| **M4** | make the plan answers real | an answer nobody can act on is not an answer |
| **M5** 08-16 | rescue the coding category | release dates are not evaluation dates; a harness that disagrees is a separate surface |
| **M6** | the HTTP API | a control that reads as installed and does not run (three times in one milestone) |
| **M7** | the engine feeds itself | never write to the artifact you are reading |
| **M8** 08-19 | a reader, and nine surfaces | the product stopped being about coding |
| **M9** | keeps itself current | what one machine costs: locks, refusals, a refresh that can say no (D-128) |
| **M10** 08-22 | the app answers a question in the reader's own words | the router, and its right to decline |
| **M11** | the reviewer became somebody else | D-133: in a one-agent lane, review is a separate SESSION leaving a FILE. Three seats, three BLOCKINGs, all in the machinery, none in the product |
| **M12** 08-25 | the 60-year-old CFO can use it | names a person would use; the council, convened from outside |
| **M13** 09-15 | the question is the front door | rank RANGES instead of false precision; "confidence" left the screen |
| **M14** 09-21 | the catalogue answers more real questions | two surfaces; one score out of 100; the gap register; the refresh repaired |
| **M15** open | coverage becomes a measurement | all 22 boards measured; W-094 answered |

---

## 4. The engine

**Data in.** `src/app/clients/` — one client per upstream, each with provenance and a licence on
record (D-101, no scraping): LiteLLM and OpenRouter for prices; SWE-bench, DeepSWE, Aider; the
LMArena dataset (CC-BY-4.0) for three boards; and an owner-fetched Epoch bundle for ECI, GPQA,
AIME, TerminalBench, ARC-AGI and WebDev. `src/app/workflows/sources.py` registers them; a source
may be OPTIONAL, but a surface blinded by a missing source discloses rather than answers (D-121).

**The pipeline.** `ingest` → `registry.reconcile` (canonical model identity, effort identity,
modality refusal since M14-W1) → `rank.build_price_medians` (two-stage median so no source outvotes
another by alias count) → `rank.category_ranking` → `recommend`. Everything lands in a DISPOSABLE
SQLite working set; the served artifact is built, fingerprinted and swapped.

**The three answers per surface**: the best score, the best value inside a window, and the cheapest
that still clears the floor — plus the full ranking beside them (D-125), because hiding the rest
would make the three look like the whole world.

**What the engine refuses to do.** Blend scores across boards (D-105). Order two models it cannot
separate — it publishes RANGES (`#1–27 of 50`) computed from the board's own margin (D-138). Call a
coverage claim upgraded by a second benchmark older than 90 days (D-139). Publish a refresh that
blinds a surface or loses a quarter of one (D-128). Print a number without saying what it is out of
(D-140, amended by D-143).

**The refresh.** Every 12 hours through `launchd`, because a missed trigger must be caught up
(D-130). It writes a record file (`advisor.db.refresh.json`) and `runner` makes it visible (D-129).
It exits 0 published, 1 unchanged, 2 failed, 3 refused, 4 busy.

---

## 5. The client

`ios/ModelRanking/` — seven Engine files and `ContentView.swift`. The split that matters:

- **`EngineClient.swift`** is the only thing that touches the network, and it sends the surface id
  and the budget, never the reader's words (D-126).
- **`Router.swift`** picks the surface on the device, in two tiers: Apple's on-device model first,
  sentence similarity second. It may decline (`__none__`), and a declined question is answered with
  the chat ranking LABELLED as unmeasured rather than silently (REQ-RTR-005).
- **`Uncertainty.swift`** is the ONE file allowed arithmetic on a served score (D-138), including
  M14's out-of-100 conversion. A Python test enforces that by file name.
- **`Language.swift`** writes every sentence from the engine's FACTS (D-136), in English and
  Turkish. A composer returns `nil` rather than a sentence that has lost its number.
- **`FrontDoor.swift`** holds the question field's logic and, since M14, the gap register: every
  declined question kept on the phone with a count, in its own backup-excluded folder, and nothing
  leaves the device.

**`swift test` compiles Engine + EngineTests only — never `ContentView.swift`.** That gap is why
`tests/unit/test_ios_client_contract.py` and `test_router_hints.py` exist: Python tests that read
the Swift source and fail when a call loses an argument or the screen opens a network door.

---

## 6. The harness, and why it is this heavy

Fourteen milestones of evidence say the product's defects are rarely in the served answer; they are
in the controls that were supposed to catch them. So:

- **Records** — `docs/decisions.md` (ADRs), `docs/prd.md` (85 acceptance criteria in 30 families),
  a wave-close checklist per wave, a review record per wave, `docs/warnings.ledger.md` (109 rows;
  a warning may not survive the close it was raised in), closure reports, retrospectives,
  `docs/EXPERIENCE.md`.
- **Gates** — `make check` runs lint, typecheck, tests, a coverage floor, the record validators,
  the conformance suite and `swift test`. `scripts/check_records.py` and `wave_check_all.py`
  validate the records themselves; `conformance/` proves each gate against inputs it must reject.
- **Independent seats (D-133, D-137)** — a review is a separate session that reads policy from the
  base ref and leaves a dated file. They have earned it: M11 three BLOCKINGs; M14-W1 refuted three
  of the author's measurements; M14-W2 found a mutant merging two boards under 905 green tests;
  M14 closure found a privacy test that could not fail and a refresh job that could not be
  installed.
- **The owner's authority** — the agent never commits as him (D-117); `deploy/` and `.github/` are
  his; every ADR that changes a contract is his to ratify.

---

## 7. What is open

**Four rulings** (`docs/closure-report-m14.md` §0): the detail screen (W-105), D-141 and five
uncounted security-pass waivers (W-106), two gates that only reproduce on his machine (W-108), and
`agentic-coding`'s floor — 50.0 against the 67.2 the product's real rule produces.

**Nineteen ledger rows stand OPEN or ESCALATED**, the oldest from M6. The ones that matter now:
W-094 (answered by M15-W1, awaiting the ruling), W-105, W-106, W-108, and the image/video pricing
basis, which M15-W1 showed blocks five boards rather than one.

**M15's plan** (`docs/plans/m15-plan.md`): W1 measure (done), W2 the detail screen, W3 the surfaces
the measurement supports — `vision` (41 ranked models), `search`/`search_factuality` (25/24) — plus
D-144's per-source carry-forward, W4 closure and the quarterly handover.

**The direction the owner set, larger than M15**: the catalogue should cover the questions people
actually ask — a tax officer's table, a gardener's pruning question — and the way there is
measurement, not intuition. The gap register (M14) is the instrument for our own readers; public
corpora of real prompts are the instrument for everyone else. The six `agent_*` boards are the
closest thing the licensed data has to that direction, and M15-W1 found they publish a signed,
undocumented score where every other board publishes an Elo — research before build.

---

## 8. Environment, and the traps

**Two lanes, neither complete.** A cloud container (Python, no Swift, no benchmark network) and a
Linux VM on the owner's Mac that can read his folders. Everything needing Swift or the upstream
data runs on HIS machine, through one script, and the agent reads the logs: `runner.sh` (gates and
the real refresh), `survey.sh` (M15's board survey), `./ios/app.sh up` (engine + simulator).

1. **`ContentView.swift` is compiled by nothing in the suite** — the file holding the reader's
   words has the least proof around it. Scope its source-contract tests to the invariant, not to
   one file. (M14 closure BLOCKING-1.)
2. **macOS privacy protection on `~/Desktop`** silently broke the refresh for 24 days; nine probes
   "cleared" it because they used Apple-signed programs. Nothing launchd opens lives there now.
3. **File sync to the device can report success and deliver nothing.** Verify by checksum, every
   time. It happened once, and only a decision record's stale wording caught it.
4. **Never run `git` in the owner's repository from the sandbox** — a stray `git status` leaves an
   `index.lock` he has to delete.
5. **A record that names a remedy owes that remedy a path in the repo** (W-100).
6. **A pin that passes by coincidence is not a pin** — four anchors equalled four thresholds, so
   serving the wrong one passed everything (W-107).
7. **`make test` needs `advisor.db`, which is gitignored.** A fresh clone reports 45 failures that
   mean nothing (W-108).

---

## 9. If you are starting cold

1. `note.txt`, then this file, then `docs/closure-report-m14.md` §0.
2. `bash ~/Desktop/terminal_output/model_ranking/runner.sh`, read `m14-runs/latest/summary.txt`. If
   it is green, the tree is what this file says it is.
3. Ask the owner for the four rulings. Do not start M15-W2 without the first.
4. Then `docs/plans/m15-plan.md` §2, in order, with the review each wave owes.

**And the one sentence to keep**: this project's value is not that it ranks models — anybody can
rank models. It is that every number it shows can be traced to a measurement, and every number it
refuses to show is refused for a reason somebody wrote down.
