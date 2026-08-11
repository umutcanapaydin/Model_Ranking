# HANDOVER — GP v4.2 material (cut 2026-08-05)

> **What this cut is.** A MINOR (two additive guardrails) **plus a repair cut** — and the repair
> that matters most is to a document the chair filed the same morning. Owner directive **OD-8**
> (`v4-candidate-register.md` §12.5) asked for a cut carrying the current rules and repairs before
> the next project starts. This is it.
>
> **The one-line version:** *a control nobody has watched fail is a rumour — including the one you
> wrote this morning.*

## 1. Provenance

| | |
|---|---|
| Increment | **12** — HCS MaaS rev-5 field harvest (F41–F48), evidence class **FIELD** |
| Council | **6 seats** (Software, Quality, Security, DevOps, PM, Skeptic), blind-parallel, scoped |
| Ballot | **V4C-49 + V4C-50 only** — the Skeptic's Increment-12 gate ruling held; V4C-51..56 stayed gated |
| Result | **6/6 ADOPT-WITH-CONDITIONS** on both, provisional until the 2026-09-16 pilot report |
| Owner rulings | OD-8 (cut now; version labels corrected to v4.2 / v1.2 by V4C-11 semver) |
| Files | **95 (v4.0) → 116 (v4.1) → 121 (v4.2)**, +5: four conformance fixtures + this handover |
| Gates | **0 new.** The gate count stays at one (`governance-contract`), still **Tier 2 / advisory** |

## 2. What the council actually did, and why this record leads with it

The chair filed both instruments the previous gate demanded, 28 and 42 days early — and then wrote,
in `council-telemetry.md` §4, that a new check called **C1** *"is added to
`scripts/check_records.py`."* **It was not. It was a paragraph.**

**All six seats found that sentence independently.** Three read the 317-line file; one ran the
validator; one imported `governed_records()` and observed that neither instrument filed that day was
even in its glob. Verdicts on condition 1: **6/6 PARTIALLY CLOSED**, nobody willing to call it done.
Verdicts on OD-8: **6/6 DISSENT**, because the chair had cited an owner directive without first
recording it anywhere — every OD-1…OD-7 sits in a record independent of the document invoking it.

Both objections were correct and both were paid rather than argued:

- **C1 was written.** C1a (a condition's closure artifact must be nameable) + C1b (a **due**
  condition whose named artifact is absent = `EVAPORATED`), two fail fixtures, falsified before
  shipping. Its first draft was **circular and could never have fired** — it asked *"is the artifact
  resolvable?"* and then failed only when a resolvable artifact was missing.
- **OD-8 was recorded** verbatim, dated, with the chair's own concession that its stated
  justification was overstated: the PM seat checked the HCS handover and found it targets v4.1 and
  never names v4.2, so the cut reflects an owner **preference**, not a technical dependency.

The Skeptic then re-polled on the trigger it had pre-committed to, verified all of it by execution
rather than reading — including falsifying C1 five ways itself — and moved both candidates to
ADOPT-WITH-CONDITIONS and condition 1 to **CLOSED**. It also found four more live defects in the
process (§4).

`council-telemetry.md` **TB-008** records the chair's overclaim as the report's largest single
finding. Read it before trusting anything else in this package.

## 3. Adopted — 2

| ID | What | Weight | Condition |
|---|---|---|---|
| **V4C-49** | **Mechanical rule installation + per-artifact replay.** Ship the grep gate in the same change that writes the rule. When a NEW standalone artifact is created, replay the last N harvest rules against **it** rather than assume the lesson travelled. Any standalone tool goes to a zero-context external reviewer before its first customer-facing use. (F45, N=2) | guardrail | chair+proposer · **2026-09-16** · condition 3's pilot report |
| **V4C-50** | **A fix inherits the risk class of the bug it fixes** — re-tier, never inherit. A concurrency fix is a concurrency change. The moment a helper acquires a lock, every call site becomes a suspect. Every load-bearing path needs **≥1 test through the real entry point**. (F44, CRITICAL — a P2 became a P0) | guardrail | same |

Several seats noted that both candidates are **two halves in one id**: the greppable half is
mechanically enforceable now, the review-practice half is not. Recorded so it cannot inflate to gate
weight by association.

## 4. Repairs — 6 in GP, 4 more found during the repair

**In GP:**

1. **C1a/C1b** — the check whose absence let **V4C-25 and V4C-12** both lapse in silence.
   Forward-only for C1a: the corpus has two incompatible condition formats and the older one (prose
   in a ballot table, due markers like *"at cut"*) is **not parsed — it is deprecated**. The Software
   seat established that pretending otherwise was false precision.
2. **`--self-test` could not reach P2 or P3** — `self_test()` never called `package_invariants()`.
   The two rules the validator is credited with were unasserted regardless of fixture count. Now
   probed against a deliberately broken throwaway package.
3. **R3's duplicate-id branch was dead code** — `collect()` keyed records by id, so duplicates
   collapsed before the uniqueness check could see them.
4. **X2 and duplicate-id had no fixtures**, though V4C-32's adopted text named both. 13 fail fixtures now.
5. **`sec_pat2` in `bootstrap-check.sh`** — declared in v3, never passed to `grep`, **eight cuts**,
   and in every project that copied the package. Wired and scoped; **0 false positives** measured
   against a 576-test production codebase before shipping.
6. **`D1`** — the shipped validator copy and the copy CI runs must be byte-identical.

**Found while repairing, all by the Skeptic on re-poll:**

7. The new **GDF CI workflow reintroduced GDF-010's exact defect** thirty lines from where it was
   fixed. There is now **one** shared detector, not two.
8. **`gdf-check.sh` step 3 had two more bypasses** — a placeholder *prefix* laundered a real value;
   `webhook_signing_key` and `bearer` were not in the key list.
9. **The narrowed detector exempted bare `SCREAMING_SNAKE` as a CI-secret name** — and an AWS key is
   also uppercase alphanumeric, which silently un-fixed both GDF-010 fixtures.
10. **The scanner exited 0 on its own crash**, and both callers read that as "clean". A crashed
    detector reporting clean is the fail-open one level up. Now exits 2 and fails closed.

**7–10 are the argument for V4C-49 restated as evidence:** four defects, in four hours, all in
*newly written* code, none found by its author.

## 5. Refused, not carried

**V4C-12** (process-artifact A/B) → `docs/refusals.md` **row 12**. Adopted at v4.0, never piloted,
condition lapsed at Increments 11 **and** 12. The PM seat ruled against a third carry. At one owner
plus agents, N is too small for a held-out split to say anything; our working evidence engine is
field harvest at N=1–3. Re-open trigger: ≥3 concurrent projects on the same package, or a
process-artifact change two seats dispute with no field evidence available.

## 6. Condition-4 rulings on V4C-51..56 — PROCEDURAL, no adoptions

Consensus across six seats on whether a mechanical enforcement point could be **named**:

| Candidate | Ruling | Note |
|---|---|---|
| V4C-51 lifecycle-state matrix | **SATISFIED** | heading-presence grep; checks existence, not matrix completeness |
| V4C-52 external-contract discipline | **INSUFFICIENT (6/6)** | only 1 of 3 clauses mechanizable; unbundle and resubmit clause (b) alone |
| V4C-53 dependency-gate triage | **SATISFIED** | `CVE-`/`GHSA-` comment + bare `>=` ban; clean |
| V4C-54 status vocabulary by evidence class | **SATISFIED — strongest** | independently verified as already prototyped in `friction-ledger.md` §1 |
| V4C-55 competitor-assessment protocol | **NOT MECHANIZABLE — accept as template** | the chair declined to fake a check; several seats credited the restraint |
| V4C-56 UI driver owns subject by identity | **SATISFIED**, but **DEFER** on merits | clean selector-ban grep, no UI phase to run it against |

**None of these is adopted.** The bloc hearing remains gated by condition 6.

## 7. What is still owed

| # | Owed | Owner | Date |
|---|---|---|---|
| 3 | V4C-49's first production run targets V4C-13 and V4C-25 **themselves** | chair+proposer | 2026-09-16 |
| 5 | rev-5 (F41–F48) preserved; V4C-49 replayed retroactively as calibration | chair | concurrent with #3 |
| — | **Owner, outside the repo:** make `governance-contract` a required check on the protected branch, bind it to the app, disable bypass. **Until then the gate is Tier 2, advisory** | owner | — |
| — | `friction-ledger.md` **A1 remains `UNVERIFIED-BY-CHAIR`** — the only Tier-3 gate has never been observed to execute by its own author | — | — |
| — | Lane B of the friction ledger is **entirely empty**. Only a project running v4.2 fills it | — | — |
| — | The dead `sec_pat2` also sits in the **deployed HCS project copy** of `bootstrap-check.sh`. Flagged, not silently patched — that is a live project and its own agent's call | HCS agent | first session |

## 8. Not regenerated, deliberately

The deck is the **v4.1** edition (`GP-v4.1-presentation.html` + `-TR.html`). v4.2 adds one row to its
version narrative; a 21-slide bilingual regeneration is not warranted for that. Said plainly here
because the v4.1 handover once carried a "deck not regenerated" line that went stale the moment it
did get regenerated — the exact propagation class `P1`/`P2`/`P3` now hunt.

## 9. Read order for whoever picks this up

1. `council-telemetry.md` §6 — the eight tracebacks, **TB-008 first**
2. `friction-ledger.md` §4 — what the first real friction report found, including that we have no
   bypass problem we can see and a dead-control problem we can
3. `v4-candidate-register.md` §12.4 (the gate ruling), §12.5 (OD-8), §12.6 (this council)
4. `docs/refusals.md` — 12 rows; do not re-litigate them
5. `pipeline-architecture.html` — the structural spec, still accurate for v4.2
