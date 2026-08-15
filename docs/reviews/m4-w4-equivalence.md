---
record_type: register
id: m4-w4-equivalence
status: ratified
date: 2026-08-15
---
# M4-W4 — Rounding, the $4.99 row, and the sentence the product exists to say

## 1. What the wave was asked for, and what the data said back

The plan (m4-plan.md §3 W4) asked for three things: a boundary rounding rule (REQ-REC-010), the
Google AI Plus re-probe (REQ-SUB-006), and **"live end-to-end proof that `--subscription` offers
≥3 distinct plans"** (REQ-REC-009).

The first two shipped as written. The third **cannot be satisfied honestly, and this record is the
reason.** Measured on live data, 2026-08-15, `--budget sinirsiz --task assistant`:

| Plan | $/month | Scored via | Score |
|---|---|---|---|
| Perplexity Max | 200.00 | Claude Opus 5 | 1507.8 |
| Google AI Plus | **4.99** | Gemini 3.1 Pro | 1479.6 |
| Google AI Pro | 19.99 | Gemini 3.1 Pro | 1479.6 |
| Perplexity Pro | 20.00 | Gemini 3.1 Pro (roster) | 1479.6 |
| Google AI Ultra | 99.99 | Gemini 3.1 Pro | 1479.6 |

Four of the five plans rank on **the same model**. Manufacturing three "distinct" answers out of
that would mean recommending a $99.99 plan over a $4.99 plan on a difference of zero — the exact
dishonesty this project is built against. So the criterion was **changed, in the open**: the engine
now names the equivalence instead of hiding it.

```
"equivalence_note": "4 plan aynı modeli (Gemini 3.1 Pro) listeliyor, yani kalite açısından
 ayırt edilemezler: Google AI Plus, Google AI Pro, Google AI Ultra, Perplexity Pro.
 Bu grupta en ucuzu Google AI Plus ($4.99/ay). Aynı model için aylık fark: $4.99 — $99.99."
```

That last sentence — same engine, $4.99 versus $99.99 — is the single most useful fact in the
dataset, and before this wave the product could not say it.

## 2. The design, and the two rules it obeys

Equivalence is computed for **every plan a label actually picked**, not only the quality pick. The
first cut compared against the quality pick alone; the reviewer proved that in the live `sinirsiz`
case (quality = Perplexity Max, alone) it stayed **silent** while both other labels collapsed onto
Google AI Plus. BLOCKING-1, fixed, with a citing test that reproduces exactly that shape.

Two rules the group construction may never break:

1. **Only cap-filtered rows.** A plan the budget excluded can never be named as an option, and can
   never widen the quoted price span. Under `orta` ($25) the note reads `$4.99 — $20.00`; the
   $99.99 plan is absent. (`subscribe.py` group loop; citing test
   `test_equivalence_never_names_a_plan_the_budget_excluded`.)
2. **Membership by `plan_id`, never by display name.** `plans.name` carries no UNIQUE constraint,
   so re-resolving a group by name can drag in a different plan scoring a different model — and the
   sentence claiming "the same model" would then quote a price span built from two models. Verified
   by a fixture with two same-named plans (citing test
   `test_equivalence_group_membership_is_resolved_by_plan_id_not_name`).

**Equivalence is not the only reason three labels can collapse, and must never be read as if it
were.** On the CODING category the labels also land on one plan — because only **1 of 10** curated
plans is scoreable at all (SWE-bench has published nothing since 2026-02-26; M4-W3). That is a
COVERAGE failure, reported by `coverage.plan_coverage`, and it correctly leaves `equivalent_plans`
empty: there is no second plan to be equivalent *to*. The distinction is written into the field's
own docstring so a future reader cannot conflate them.

## 3. Rounding: one boundary, one decimal (REQ-REC-010)

Arena hands us `1481.5937567329202`. Scores now reach the JSON contract rounded to 1 decimal, and
**only** at the output boundary — ranking, Pareto and every threshold comparison keep the raw value.
A sub-0.05 gap is real to the threshold and invisible in the fields, so all prose deltas are
computed from the **rounded** numbers (`shown_gap`) and say "aynı puanda" rather than the nonsense
"0.0 behind" (`lead_phrase`). Both engines route every trade-off string through the same helper.

Two mistakes were made here and both are now pinned by tests: rounding inside the ranking (which
would let a 0.04 gap tie and hand the quality label to the cheaper plan), and rounding *after*
subtracting instead of before (which prints a 0.1 gap between two fields that both read 77.4).

## 4. Google AI Plus — the "dispute" that was a date (REQ-SUB-006)

M3 withheld this row because two trackers disagreed: $4.99 vs $7.99. Re-probed 2026-08-15: they do
not disagree. $7.99 was the US launch price, **cut to $4.99 on 2026-06-08**, reported the same day
by four independent outlets (9to5google, TechRepublic, Engadget, Digital Trends). costbench was
verified 2026-05-27 (pre-cut); felloai was updated 2026-06-11 (post-cut). One price change, two
dated snapshots. The row is entered at $4.99 with that reasoning in the seed header.

Its `included_models` comes from Google's own page, not from the trackers: **an amount may be
cross-checked against secondary sources; a model list may not** (M1 rule 4). The price is also the
table's minimum, which makes it the row every budget answer lands on — so it carries its own citing
test asserting the value survives parse and store exactly.

## 5. Findings carried forward (ledger, not silence)

Raised by the wave's fresh-eyes re-review and deliberately NOT fixed here, because each is a
JSON-contract addition that deserves its own review rather than a same-day patch at wave close:

| # | Finding | Why deferred | Owner |
|---|---|---|---|
| L-1 | The note says N plans "listeliyor" (*list* the model), but a roster-sourced link means the provider's separate model page names it, not the plan page. Live, this is asserted about Perplexity Pro. The per-pick `why` text already makes this distinction 30 lines away | Wording change to a user-facing string that the same output distinguishes elsewhere; needs one consistent phrasing decision, not two | M4 closure |
| L-2 | `equivalent_plans` flattens to a name list, so with 2+ groups a machine consumer cannot tell which pick each plan is equivalent to, or at what price | Contract shape for the future API — decide once, in M5, with the API surface | M5 |
| L-3 | Under `dusuk` only one plan is eligible, all three labels return it, and nothing says why. `eligible_count: 1` states the fact but no prose does. The sharper missing sentence: **five scoreable plans were priced out** and the output never says so | New nullable output field + REQ-ID + ADR; overloading `equivalence_note` would contradict §2 of this record | M4 closure |

## 6. Standing consequence

The product's headline answer is no longer "here are three plans". It is: *here are three plans —
and where two of them are the same engine wearing different badges, we say so and point at the
cheaper one.* Any future change that makes the three labels look distinct when the underlying model
is identical is a regression against this record, not an improvement to the UX.
