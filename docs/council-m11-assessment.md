---
record_type: council
id: council-m11-assessment
status: draft
date: 2026-08-24
---
# Council — situation assessment after M11

> **Convened by the owner on 2026-08-24**, immediately after M11 was ratified, with two new chairs
> he added to the core council: a **Senior Software Developer** and a **Senior Mobile Developer**.
> A fourth seat, **Product & Delivery**, was added by the lead agent for a reason stated in §1.
>
> Four seats, four separate sessions, no shared context, each reading policy from the protected
> base ref (V4C-06). This is the first council record in this project's history.

| Seat | Its question | Record |
|---|---|---|
| Senior Software Developer *(new)* | What will this codebase be like in six months, and what is accumulating that nobody counts? | `docs/reviews/m11-council-senior-swe.md` |
| Senior Mobile Developer *(new)* | What stands between here, the owner's phone, and the App Store? | `docs/reviews/m11-council-senior-mobile.md` |
| Tester | Do 714 tests CATCH things, or DESCRIBE them? | `docs/reviews/m11-council-tester.md` |
| Product & Delivery | Is this worth using, and by whom? | `docs/reviews/m11-council-product.md` |

## 0. Why the fourth chair

The owner named two. The lead agent added Product & Delivery, and the reason is the finding that
made the council necessary: **every seat that existed asked whether the work was correct,
maintainable, testable or shippable, and nobody was accountable for whether the product was worth
using.** Eleven milestones later a 60-year-old CFO produced five requirements in twenty minutes
that nobody inside the project would ever have written. A chair that had been empty is cheaper to
notice than to keep paying for.

## 1. The through-line, which no single seat could see

Four seats worked independently on four different questions and returned, between them, the same
shape more than a dozen times:

> **A thing is asserted somewhere, and exercised nowhere — and each half is locally correct.**

| What is asserted | Where | What is actually true |
|---|---|---|
| "budget-aware recommendations" — the product's own one-line description | `README`, PRD, `/v1/budgets` (built at M11-W3) | `ContentView.swift:29` hardcodes `budget = "unlimited"`. **There is no budget control in the app.** |
| **D-120**, cited as a "K.8 frozen contract" | `build.py:25`, three tests, M10 and M11 plans — 27 files | **D-119 and D-120 were never written.** `decisions.md` goes D-118 → D-121. |
| **C2b** — the counter that sends a control for review after three bypasses | two records state it fired | It keys on a free-text column where all 22 rows are unique. **It cannot fire.** K.7 has been bypassed 10 times. |
| `MIN_QUALITY_PCT == 65.0` | `test_recommend.py:238` | A literal compared to itself in the module that defines it. The engine reads `spec.min_quality`. **Mutating the number that decides answers kills nothing.** |
| Code signing, "skipped" for the Simulator | `ios/app.sh:113` `CODE_SIGNING_ALLOWED=NO` | `DEVELOPMENT_TEAM` appears **zero** times. The device build has never once succeeded. |
| `EngineError.insecureTransport`, written so a cleartext refusal is not misreported | `EngineClient.swift` | Has never executed. Both real failure modes land in `unreachable`, whose advice is the wrong one. |
| The M8 calibration record, ratified, defending seven surfaces' thresholds | `docs/reviews/m8-category-calibration.md` | Every number still reproduces today — **and nothing asserts them.** |
| "the base URL is configuration, not a constant" | `EngineClient.swift` comment | Hardcoded `127.0.0.1` at the only call site. |

**This is not a list of eight bugs. It is one defect with eight instances**, and it explains
something eleven milestones of good review could not: why a project this disciplined keeps finding
that its records describe controls that are not there. Each instance is *locally consistent*. The
code is right about what it does. The record is right about something. **The gap only exists across
the boundary between them, and no seat that reviews one side can see it.** That is what a council
is for, and it is the argument for holding another one.

## 2. What each seat found that the others could not

**Senior Software Developer — the engine is healthy and the debt is elsewhere.** Measured: median
function 22 lines across 205 functions, 23 duplicated 8-line windows, `make check` in 18.4 s. The
verdict worth quoting: *"what is accumulating is not in `src/`."* It is in the governance corpus
(2.4× the product, ~78k mandatory words, no ADR index), in a ledger that is 87.7% one prose column
with 4,753-character cells, and in `make gate` — which **exits 2 on a clean tree** and is the only
thing the post-edit hook runs.

**Senior Mobile Developer — the strongest single finding of the council, and it is aimed at M12.**
Under a Turkish locale, `localizedCaseInsensitiveContains` stops matching: searching *i* no longer
finds "GPT-5.1 Instruct", because Turkish has a dotless lower-case counterpart to capital I, and the standard lower-case i is a different letter there. (Spelled out in words rather than shown, because `L1` cannot distinguish text that IS Turkish from text ABOUT Turkish — GPF-005, reproducing in the record that reports a Turkish-locale defect). **Verified in three
locales.** The six tests that pin that predicate — written the day before, closing W-069 — all run
under the process locale and *cannot* see it. It fires the day Turkish ships, which is M12's first
item. The seat also checked two adjacent call sites, found them locale-independent, and marked them
**do not fix** — refusing the reflex that would have made the change bigger and wrong.

**Tester — the kill rate is not the finding, the split is.** 54 mutants, 65% killed: **71% on the
engine, 22% on the nine surfaces' thresholds, 100% on planted defects.** The repo-scanning guards
this project has built genuinely work. What does not: threshold fixtures with a 30-point hole around
a 65.0 floor, so `65.0 → 58.0` is fully green. And the Pareto price-tie case, absent from every
fixture and present **nine times in the shipped artifact**.

**Product & Delivery — the product does not do the thing it says it does.** Beyond the budget
control: `subscribe.py` (599 lines) answers the CFO's literal question — which subscription to buy,
in dollars per month — and is **on no HTTP route**. Disclosure load measured at 155–185 words of
caveat against 40–60 words of answer, eight blocks rendering as up to five identical orange
triangles with no severity order, carrying about four distinct facts. Six of nine surfaces show a
**permanent** "may be out of date" notice, five because the source publishes no dates at all — a
structural fact dressed as a transient warning that can never clear, drowning the one real one.

## 3. What is working, said as plainly as the failures

A council that only finds fault is a council nobody convenes twice.

- **The engine's internals are in good shape**, and that is a measurement, not an impression.
- **The repo-scanning guards work.** Four planted defects — a hand-built `file:` URI, an
  ASCII-Turkish string, a calibration script bypassing `ranked_population`, a swallowed
  corrupt-artifact error — were caught 4 of 4 by controls written in earlier milestones for exactly
  those shapes.
- **Earning their keep**, named by the seat that was invited to criticise the process:
  `check_records --self-test`, per-finding exemptions that fail when stale, the per-module coverage
  floor, `review_seat_problems`, `serialize.py`, and `make check`'s 18 seconds.
- **Sediment**, named by the same seat: `falsify` as a permanent no-op leg of `gate`; "20 of 40 wave
  records out of scope" reported as a pass; `journey.py` (271 lines, called by nothing);
  `smoke-deps`, asserted at eleven closures and executed at zero.

## 4. What the council recommends, in order

1. **Give the app a budget control**, or stop calling the product budget-aware. Everything M11 built
   for W-044 currently serves a control that does not exist.
2. **Fix the Turkish case folding before Turkish ships**, and pin it with a test that sets the
   locale rather than inheriting it.
3. **Write D-119 and D-120**, dated today, describing a contract that has been in force since M6 —
   not backdated, because backdating would commit the defect a second time.
4. **Repair `make gate`** (one line) and either wire `C2b` to something it can count or delete it.
   A counter that cannot fire is worse than no counter: two records already claim it did.
5. **Add the calibration-reproduction test** the Tester seat specifies — it kills 13 of 14 threshold
   survivors and catches the future defect no current control can see: boards drifting the static
   floors stale under a twice-daily refresh.
6. **Route `subscribe.py`**, or decide out loud that the subscription answer is not part of this
   product.
7. **Cut the disclosure load.** Six permanent staleness notices that can never clear are not
   disclosure; they are noise that hides the one notice that means something.

Items 1, 2 and 7 belong in M12 with the CFO's five. Items 3, 4 and 5 are governance and testing
debt that can be paid at any time and get cheaper the sooner they are.

## 5. What the council did not do

- **No seat ran the simulator session**, which `note.txt` records as the thing that found six
  defects the gates missed. The Senior Software Developer seat flagged this as the gap in its own
  review, which is the right instinct and is recorded here rather than left in one file.
- **No seat could check a physical device or an Apple account.** Nine mobile findings are stated as
  unverifiable from here and are listed as such in that seat's record.
- **Seats ran concurrently in one working tree.** Two seats recorded that another's mutation was
  live during one of their measurements; both re-measured clean and said so. A council that shares
  a tree needs either isolation or this disclosure, and next time it should have isolation.

---

Convened by: the owner · Seats: Senior Software Developer, Senior Mobile Developer, Tester,
Product & Delivery · Synthesised by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-24
