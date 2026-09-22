---
record_type: handover
id: handover-m15
status: draft
date: 2026-09-21
---
# HANDOVER — M15, written mid-milestone

**Written for whoever picks this up next, human or agent, assuming they know nothing about the
project.** It supersedes `handover_q4.txt` on STATE (that file stops at M12) and supersedes
nothing else: `handover_rocky.txt` is still the best account of the DOCTRINE, and
`docs/closure-report-m14.md` is the evidence behind every claim about M14 below.

Written by: the lead agent (Claude Code, cloud lane, D-117), which built M14 and is building M15.
**Every number here was measured, not recalled**, and each one says where it was measured, because
this project has been wrong three times about its own figures (W-093 is the record of one).

The quarterly handover proper (`handover_q5.txt`, 15 % 3 == 0) is owed at M15 CLOSURE. This file is
the mid-milestone one, written because the owner asked for it on 2026-09-21.

---

## 0. Read in this order

1. `note.txt` — 30 lines, the current turn's state. Always read first.
2. This file.
3. `docs/closure-report-m14.md` §0 — the four rulings the owner owes, with recommendations.
4. `AGENTS.md` §3 and §5 — house rules. **§5: every committed file is English.** Enforced by `L1`
   in `scripts/check_records.py`; exemptions are named one by one in `.language-allow`.
5. `docs/decisions.md` — for M14/M15 specifically: D-104, D-105, D-117, D-126, D-138, D-142..D-146.
6. `docs/plans/m15-plan.md` — what is being built now, and §0 lists what it waits on.

---

## 1. What the product is, in five sentences

`model_ranking` aggregates free-and-legal benchmark and pricing data and answers one question: *for
what I want to do, which model should I use, and what does it cost?* A person types the question in
their own words; an on-device router picks the surface; the engine decides every number and the iOS
client only chooses words (D-104). Eleven surfaces answer today. Nothing is deployed, nothing
bills, and the app has never been on a physical phone — the simulator is the only place it has run.

**The doctrine that governs everything: never present something unmeasured as measured.** If a fact
and a sentence disagree, the fact is right and the sentence is the defect. Every threshold is data
in `categories.py`, never a code branch. Scores are never blended across boards (D-105), and
nothing the reader types ever leaves their device (D-126).

---

## 2. Where things stand — measured 2026-09-21

    HEAD                855b44a (local == origin/main, pushed)
    make check          exit 0 on the owner's Mac, 2026-09-21 13:52
      Python            919 passed, 12 skipped, coverage 88.76% (floor 85%)
      Swift             242 tests (floor 242)
      records           check_records PASS · wave-check-all PASS (35 v5.0 records)
      conformance       conformance-gate PASS (7 findings, all exempted, all still firing)
    live artifact       refresh published 2026-09-21 10:23 UTC, exit 0, surfaces_answering 11
    catalogue           74 models, 72 with a price median, 2427 score rows, 13 benchmarks

M1–M13 are closed and signed. **M14 is closed, signed and pushed** (five waves). M15 is open: W1's
measurement is done and recorded, W2–W4 are not started.

**The eleven surfaces:** coding, agentic-coding, assistant (chat), everyday, expert, mathematics,
computer-use, abstract, web-dev, document, factuality. The last two arrived in M14.

---

## 3. What M14 shipped, and what it cost

Shipped: two surfaces from boards already licensed; a live price defect fixed (an image model's
per-image price was being published as a text model's per-token price, W-092); the 12-hour refresh
running again after a 24-day silence (W-096) and now installable from the repository (W-100); the
**gap register** — every question the router declines is kept on the phone with a count, readable
most-asked-first, and nothing leaves the device; and **one score out of 100 per surface** (D-143,
the owner's ruling), where an Elo becomes "how often people prefer this model over one at the
surface's pinned anchor" and a percentage stays as it is.

The cost, all of it recorded rather than argued away:

- **Elo surfaces read lower than percentage surfaces** — 57–79 against 73–100 — and the owner
  accepted that knowingly (D-146, option A). It is D-143's own revisit trigger.
- **There is no detail screen**, and the plan's mitigation for taking the unit off the card was
  "it stays on the detail screen" (W-105). Four carried requirements had no home until the closure
  seat found them.
- **The HIGH-tier security pass was waived twice more** while its ADR (D-141) stays proposed — five
  times now, counted in W-106 where the counter can finally see it.
- **Two gates only reproduce on the owner's machine** (W-108): CI lints less than `make lint` does,
  and 45 tests need a gitignored database.

---

## 4. The four things only the owner can settle

All four are in `docs/closure-report-m14.md` §0 with recommendations; repeated here because a new
agent will otherwise re-derive them from scratch.

1. **The detail screen** (W-105) — build it in M15-W2, or rule that the unit is gone for good.
2. **D-141** (W-106) — ratify (recommended) or refuse; if refused, W-090's `C2b-reviewed` marker
   comes off, because the project would then have stopped counting.
3. **The two unreproducible gates** (W-108) — pin the ruff version, widen CI's lint, ship a seeded
   artifact. Touches `.github/`, which is his surface.
4. **`agentic-coding`'s floor** — 50.0 shipped against 67.2 under the rule the product actually
   follows (§6). Re-derive it, or keep it and say why.

---

## 5. How to run anything

**Neither agent lane can compile Swift, and neither can reach the benchmark data.** Everything that
needs either runs on the owner's Mac, through one script, and the agent reads the logs:

    ~/Desktop/terminal_output/model_ranking/runner.sh    make check + probe build + calibration
                                                         + the real refresh job; logs under m14-runs/
    ~/Desktop/terminal_output/model_ranking/survey.sh    M15-W1's board survey; logs under m15-runs/
    scripts/enable_refresh.sh                            installs the wrapper AND the plist (W-100)
    scripts/install_refresh_wrapper.sh                   the wrapper alone, for a job already loaded
    ./ios/app.sh up                                      engine + app on the simulator

In the cloud lane: `pytest`, `ruff`, `mypy src`, `scripts/check_records.py`,
`scripts/wave_check_all.py`, `scripts/conformance_gate.py` all run — but `pytest` needs
`advisor.db`, which is gitignored (W-108), so copy one in before believing a green.

---

## 6. What M15-W1 measured, and the one long-open question it closed

Record: `docs/research/m15-board-survey-2026-09-21.md`. The dataset the product already licenses
carries 22 boards and the product reads 3. All 22 were measured on one footing, and the method
reproduces the three shipped surfaces exactly (65, 29, 59 ranked models), which is the only reason
to trust the rest.

- **Candidates:** `vision` (41 ranked models), `search` + `search_factuality` (25 / 24),
  `webdev` (53) as a second board for the existing `web-dev` surface rather than a new one.
- **Every image and video board ranks zero models** — all priced per image or per second. The
  pricing-basis ruling now unblocks five boards, not one.
- **The six `agent_*` boards publish a different kind of number** (a signed score with a 95%
  interval, not an Elo), and they are the closest thing in the dataset to the owner's own examples
  — *does it invent tool calls*, *does it take a correction*. They cannot be served yet: the scale
  is undocumented and goes negative, direction is per board (low is good for hallucination), and
  one of them cannot separate its own models at one decimal. Research, not build.
- **W-094 is answered.** Nine of the eleven shipped surfaces sit closer to the floor rule D-145
  names — the top third of the whole board over distinct models — than to the "ranked population"
  rule `categories.py` has claimed since M8. The comment has been describing the wrong rule; the
  owner's M14 ruling was already the product's real rule.

---

## 7. The traps, in the order they will bite

1. **`ContentView.swift` is compiled by nothing in the test suite.** `swift test` builds Engine +
   EngineTests only. The file holding the reader's typed words therefore has the least proof around
   it, which is exactly where the M14 closure seat found a four-line `URLSession` mutant surviving
   every gate. The Python source-contract tests (`tests/unit/test_ios_client_contract.py`,
   `test_router_hints.py`) are the substitute: **scope them to the invariant, not to one file.**
2. **The owner's machine is the only measurement for Swift, and for anything needing the network.**
   Plan the work so his runs are few and each one answers something.
3. **macOS privacy protection on `~/Desktop`** broke the refresh for 24 days and cost nine probes
   that all "cleared" it — they used Apple-signed programs, and protection is decided per program.
   Anything launchd opens on the job's behalf lives outside `~/Desktop` now. Do not move it back.
4. **File sync to the device can report success and deliver nothing.** It happened once and the
   commit script caught it only because a decision record still said "proposed". **Verify by
   checksum after every sync.**
5. **The agent never commits as the owner** (D-117): the milestone commit is his, agent commits
   carry the agent identity and GP trailers. The agent also cannot delete files in his folders, and
   must not run `git` in his repository at all — a stray `git status` from the sandbox leaves an
   `index.lock` he then has to remove.
6. **`deploy/` and `.github/` are his surfaces.** Propose, never edit.
7. **A record that names a remedy owes that remedy a path in the repo.** W-096 closed citing an
   installer that existed only in a scratch folder; the repository's own install path stayed broken
   for a milestone.

---

## 8. If you are starting cold, do this

1. Read `note.txt`, then `docs/closure-report-m14.md` §0.
2. Ask the owner for the four rulings in §4. Do not start M15-W2 without the first one.
3. Run `runner.sh` once and read `m14-runs/latest/summary.txt`. If it is green, the tree is what
   this file says it is.
4. Then M15-W2 (the detail screen) or W3 (the surfaces W1's measurement supports) —
   `docs/plans/m15-plan.md` §2 has both, with the risk tiers and the review each one owes.
