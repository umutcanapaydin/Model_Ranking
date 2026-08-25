---
record_type: ratification
id: closure-report-m12
status: draft
date: 2026-08-25
---
# Closure Report — M12: the 60-year-old CFO can use it

> **AWAITING THE OWNER'S SIGNATURE.** Section 0 is what needs him. Every figure below was measured
> at the closing tree rather than reported by the thing that produced it.

## 0. What needs the owner

1. **Run `./runner`, then `./scripts/simulator_session.sh`, then make the milestone commit.** The
   second one matters more than usual this time: **this is the first milestone written entirely
   from what people outside the work said**, and the only way to know whether it landed is to look
   at it. Tap the Turkish flag — it has never been tapped by a human.
2. **W-074 is still open by your decision.** No shell linting anywhere: `runner`, six scripts,
   `ios/app.sh`. Offered at M11, declined, and recorded as a decision rather than an oversight.
3. **W-040 is yours and is now answerable.** Whether the unfiltered ranking is too long was
   deferred to your own use of the app — and until M12-W3 there was no budget control, so every
   judgement you could have made was against the widest possible list. Now it is not.
4. **Nothing deployed, fifth milestone.** D-123, W-030, W-031. By your sequencing: local, then your
   phone, then the App Store. The Senior Mobile seat found the device build has **never once
   succeeded** — `DEVELOPMENT_TEAM` appears zero times — which is M13's opening, not this one's.

## 1. What shipped (from the signed plan)

| REQ-ID | Criterion | Citing test (able to fail) |
|---|---|---|
| REQ-GOV-001 | Every cited ADR exists; `C2b` counts something reachable | `tests/unit/test_adr_citations.py`, `tests/unit/test_c2b_counter.py`, and the rewritten `--self-test` probe |
| REQ-LOC-002 | Text matching is correct under a Turkish locale, pinned by a test that SETS the locale | `ios/EngineTests/OwnerSessionDefectTests.swift` — and the test that matters asserts the CHOICE, because the behavioural ones cannot see a locale they do not set |
| REQ-CMP-001 | Every number says what it means; a RANK where the scale is arbitrary | `ios/EngineTests/OwnerSessionDefectTests.swift` |
| REQ-CMP-002 | Price in a unit a person outside this industry uses | same |
| REQ-CMP-003 | Surface names say what they measure; no two share a first word | `tests/unit/test_category_titles.py` |
| REQ-DSC-001 | A source's property stated once; a data STATE keeps its warning (D-135) | `DisclosureClassificationTests` — including D-135's own every-fact-survives test |
| REQ-BGT-001 | A reader can choose a budget and the answer changes | `BudgetOptionTests`, `BudgetIsSentTests` |
| REQ-LOC-001 | `/v1` returns facts; the client writes the sentence | `tests/unit/test_why_facts.py` (34 cases), `ios/EngineTests/LanguageTests.swift` |

## 1a. Per-wave table

| Wave | Risk | Delivered | Record |
|---|---|---|---|
| W1 | MED | D-119/D-120 written; the ADR-citation gate; `make gate` repaired; `C2b` rekeyed; Turkish case folding | `docs/plans/m12-wave-1-close.md` |
| W2 | MED | Six renames, rank + scale + price-in-pages, disclosures under D-135, three council defects | `docs/plans/m12-wave-2-close.md` |
| W3 | LOW | The budget picker | `docs/plans/m12-wave-3-close.md` |
| W4 | HIGH | D-136, the contract move; Turkish across the screen; `L1` narrowed to prose | `docs/plans/m12-wave-4-close.md` |
| W5 | LOW | Stage 4.0, capture, this report | `docs/plans/m12-wave-5-close.md` |

## 1b. Decisions made on your behalf

- **D-119 and D-120 were written with today's date**, describing contracts in force since M6.
  Backdating would have committed the defect inside its own repair.
- **The `3` divergence in the exit-code contract is recorded, not resolved.** Both consumers depend
  on their number; changing one to tidy a document would break a caller.
- **The engine's composed prose was left alone at W2** and turned into facts at W4. Rewording it
  twice was the alternative.
- **`elo` and `ECI` are not translated.** They are the names of scales; translating a proper noun
  would leave two readers unable to compare notes.

## 2. Git record

`d13c810..HEAD` — **11 commits** at agent hand-off. All carry the `GP Agent (Claude Code)` identity
and `GP-Agent:` / `GP-Task:` trailers. The owner makes the closing commit.

## 3. Trust telemetry

- Tests: **714 → 781 Python**, **59 → 121 Swift.** 12 skipped, unchanged.
- Governed records: 61 → **71**.
- `make check` exit 0 **and `make gate` exit 0** — the second for the first time in this project's
  history, on a target that had been red for months while the post-edit hook ran it.
- Fault injection: **34 mutants across the milestone, 34 killed.**
- Independent seats: **five** — four council chairs before the milestone, one Stage 4.0 within it.
- **Zero new K.7 waivers.**

## 4. Security & invariants

Stage 4.0: `docs/reviews/m12-security-review.md`, run by a seat that wrote none of the code.

**The payload MOVED**, deliberately and additively, under D-136 — the second recorded move in this
project's history and the first since D-125. Every pre-existing field is unchanged; `why_fact` and
`trade_off_fact` are new. **D-104 holds and the distinction is worth stating:** the engine still
decides every number, and the client only chooses which words carry it. A translation is a
judgement about wording, and the engine that must not say a model is good should not be choosing
how to say anything.

## 5. Ledgers

**Opened this milestone:** W-076..W-086 — eleven rows, nine of them **FIXED** in the same wave that
raised them. **Open in total: 28**, unchanged from M11 — every row this milestone added, it also
closed, except the two that are the owner's.

## 6. Architecture delta — prose

For eleven milestones this product was specified by people who already knew what a benchmark was,
and it showed: `161.7 ECI`, `$1.03/1M`, `Abstract reasoning`. All correct, none usable. M12 is the
milestone where that stopped, and the shape of the fix is the interesting part.

**The engine did not get worse at being precise; the product stopped making the reader do the
conversion.** A rank sits beside every score because a rank needs no scale to be understood. A page
count sits beside every price because a CFO thinks in cost per unit of work. Six surfaces are named
for what they measure. Not one exact number was removed — the M12 plan named that as its first
trap, and the test of every change was whether the precise figure survived beside the plain one.

The larger structural change is D-136. `/v1` now publishes the FACTS behind each pick sentence and
the client writes the sentence, in English or Turkish, from those facts alone. That is the answer
to a question the project could not see until a second language arrived: **every sentence on screen
was generated by the engine, in English**, which is eleven milestones of localisation debt that
nothing could reveal. The cheaper option — a `?lang=tr` parameter — would have written every future
sentence twice and put the product's voice inside the engine that D-104 forbids from having
opinions.

And the disclosures got quieter without getting fewer. Six of nine surfaces carried a permanent
"may be out of date" notice, five of them because the source publishes no dates **at all** — a
structural fact wearing a transient warning's costume, drowning the one notice that was real.
D-135 separates the two: a property of a source is stated once, calmly; a state of the data keeps
its orange. Every fact survives, and the test that says so is the one that must never be deleted.

## 7. The carried question, for M13

Every wave of this milestone discharged findings that came from **outside the people doing the
work** — four council seats and one CFO — and it produced the largest usability gain in twelve
milestones.

That is a good outcome and an uncomfortable one. **The work the team chose for itself, across
eleven milestones, was correctness. Correctness was never the thing standing between this product
and a user.**

So: **what else is the team not choosing?** The council was convened once, by the owner, on a
hunch, and it found a defect class nobody inside had named. M13 should decide whether an outside
seat is a thing this project HAS — scheduled, with a standing question — or a thing it reaches for
when somebody remembers.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Range: `d13c810..HEAD`
