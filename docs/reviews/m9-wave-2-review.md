---
record_type: review
id: m9-wave-2-review
status: ratified
date: 2026-08-22
---
# Independent review — M9 Wave 2 (the refusal rule)

> **VERDICT: BLOCKING — 3 blocking, 7 major, 10 minor.** Run by a seat that authored none of the
> code, discharging the obligation `docs/plans/m9-wave-2-close.md` row 3 recorded as OWED. The plan
> §4 required an independent seat on this wave specifically; it did not run at the wave and it ran
> here.
>
> **Fault injection: 40 mutants written, 32 killed, 8 survived** — against the author's report of
> 24 across both waves, all killed. Six of the eight survivors were genuine test gaps and five of
> those six sat on the status record, which is the artefact the owner actually reads.

## The three BLOCKING findings, all confirmed by the author before fixing

**B1 — a crashed cycle reported as a healthy one.** `record()` was reachable only from the four
return sites inside the `try`, so a builder that raised wrote no record at all — and the PREVIOUS
record survived, still saying `published` with its own old timestamp. Measured: crash at
`t=99999`, record afterwards `outcome='published' at=1000.0`. `runner` then printed "last cycle:
minutes ago", "outcome: published", and **exited 0**. A refresh crashing on every cycle read as
healthy. `write_status`'s own docstring said *"written on EVERY path"*; the claim and the code
disagreed, in code written by the agent that wrote the claim.

**B2 — `degradations()` compared row counts and nothing else.** Three constructed candidates all
published: every price ×100 (which blinds `low` and `medium` on all nine surfaces while no surface
changes SIZE), twelve good models replaced by twelve bad ones, and a loss of **exactly** 25%
(`9 < 9` is False). The price case is the one that matters, and it invalidated a line of reasoning
in D-128: prices are not merely reported numbers here, because `BUDGETS` is a **hard filter applied
before any scoring** (REQ-REC-002). A surface that answered a reader on `low` and now answers
nothing IS "fewer surfaces answering" in the only sense a reader experiences.

**B3 — the fingerprint omitted four published fields, and the refresh could not publish a freshness
update.** `evidence_date`, `vendor`, `input_per_m`, `output_per_m` were all served and none was
hashed. Measured: the same scores republished with FRESH EVALUATION DATES returned `UNCHANGED`. The
served artifact would keep disclosing `stale: true` forever while every cycle exited 0 — **the plan
§0 freeze, arriving through the fingerprint instead of through the threshold, and inverting the
milestone's entire purpose.**

## What the author changed in response

| Finding | Fix |
|---|---|
| B1 | The cycle body is wrapped in `except BaseException` → record → re-raise, with the live-artifact read and the workspace creation moved INSIDE it. Two citing tests, both proven RED |
| B2 | `<` became `<=` at the boundary, and `ServingSummary` gained per-(surface, budget) eligibility so a pricing feed that prices a budget out is a refusal. D-128 amended |
| B3 | The digest is now DERIVED from `RankingRow`'s fields minus a measured exclusion set, so a field added tomorrow is hashed by default. The exclusion set was measured against `PUBLIC_RANKING_FIELDS ∪ PUBLIC_PICK_FIELDS` and is two fields long |
| M4/M5 | The atomicity test stopped AST-dumping for identifiers and now asserts the rename's source is not its destination; the record's payload — surface count, both fingerprints, `at_iso` against `at` — is asserted |
| M7 | The exactly-25% boundary is pinned |
| M9 | Pinned at the branch that owns it, after the first attempt was satisfied by the budget axis instead |

All eight of the reviewer's survivors were replayed after the fixes. **Eight of eight now die**,
and so do three mutants reverting the blocking fixes themselves.

## Carried, with the reviewer's reasoning intact

- **M1** — plan §5.2 (*"what happens on the SECOND consecutive refusal?"*) is genuinely unanswered.
  D-130 claims to answer it "in part" and does not: it is about `launchd` vs `cron` and missed
  triggers, a different question. The record is depth-1, so it cannot even represent two in a row.
- **M3** — no mutual exclusion. Two cycles share the record's fixed scratch name, and a refresh
  decides against a baseline another writer may already have replaced.
- **M6** — REQ-REF-001's SIGKILL clause and REQ-REF-006's in-flight-request clause have no test,
  and both criteria are marked MET.

## On D-128's threshold, in the reviewer's words

> *The direction is right; the number is not the problem; I would not move it. I would add axes.*

Every degradation the reviewer actually landed on the product passes at **any** value of
`MAX_SURFACE_LOSS`, because none of them changes a row count. Tightening would catch none of them
and would move the product measurably closer to the freeze the ADR fears most.

**Two corrections the reviewer found in the ADR's own arithmetic:** the worked examples were off by
one. `now <= was * 0.75` trips on the smallest surface (13 models) at the **4th** model lost —
30.8%, not "a quarter is three" — and on `everyday` (58) at **15**, not fourteen. D-128 is amended
rather than rewritten.

Filled by: an independent reviewing seat · Date: 2026-08-22 · Tree at review: `277459d`
