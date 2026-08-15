# M4 Retrospective (G.12 — second retrospective; answers M3's carried question, poses the next)

Date: 2026-08-15 · Scope: M4 (W1-W4, commits `0f840a9..20312a1` + closure) · Author: lead agent
(fresh-eyes verdicts cited from committed review artifacts, not memory).

## Answer to M3's carried question

M3 asked: *is the honest-but-thin answer ("7 plans unscored") acceptable product behaviour, or does
M4 need registry + benchmark expansion and provider-roster curation before the subscription answer
is user-facing?*

**Answered by doing it, and the answer is: expansion helped exactly as far as published evidence
allowed, and then stopped — which turned out to be the more useful finding.**

- Registry expansion took plan-name drops from 2 to **0**. Every model a plan page names now links.
- Roster curation took assistant coverage from **3/9 to 5/9**. The remaining three plans
  (ChatGPT Go, Claude Pro, Claude Max) name no model version *anywhere* the provider publishes —
  probed and recorded in `data/rosters.yaml`, not guessed at.
- Coding coverage stayed at **1** (now 1/10): every link in the world does not help when the
  benchmark behind the category has published nothing since 2026-02-26.

So the thinness had two causes, and only one of them was ours. The half we owned is closed. The
half we do not own is now a **printed number with a date next to it** on every run, which is a
better product answer than either hiding it or pretending to fix it.

## Discipline verdicts

| Discipline | Verdict | Evidence |
|---|---|---|
| Fresh-eyes per-wave review (K.7/V3C-68) | **PULLED-WEIGHT** | 4/4 waves produced findings (7 BLOCKING + 13 MINOR in-wave). W1's four BLOCKING were all *silent correctness* defects — a model folded into its base family, a coverage number quoted wrong in its own record, a live score lost to an over-eager guard. None would have failed a test the author wrote |
| **Reviewing the FIX delta, not just the original** (new this milestone) | **PULLED-WEIGHT — and it caught the milestone's only escaped blocker** | W4's round-1 fixes were themselves reviewed; round 2 found that the display-delta fix shipped with no citing test in *either* engine, plus three further defects (budget-cap leakage into the equivalence group, name-keyed group membership, an overclaiming verb). Without the second pass, four defects ship green |
| Fault-injection (V3C-72) | **PULLED-WEIGHT** | 18 mutants across the milestone, 18 RED after fixes. Two STAYED GREEN when first probed — both became mandatory tests. The stay-green rate (2/18) is the honest measure of how much the protocol is still finding |
| Live-probe-before-fixture (FP-M2-2 doctrine) | **PULLED-WEIGHT** | Held under pressure twice: no parser was written for Epoch or Terminal-Bench against unseen shapes (both proxy-403), and the Google AI Plus price entered only after the "dispute" was re-probed and explained as a dated price cut |
| Coverage as a shipped metric (new, REQ-SUB-005) | **PULLED-WEIGHT** | It immediately measured something uncomfortable and true (coding 1/10), and it is what let the milestone answer M3's carried question with numbers instead of impressions |
| Warnings ledger C2a/b/c | **MIXED** | It worked as a router (5 new rows, each with an owning milestone) but **W-001 survived its owning milestone's close** — the ledger's own headline rule. The rule has no enforcement for the case where the remedy is an owner decision an agent may not take; recorded as a GP-upstream note |
| Quality gate V3C-02 (every criterion has a citing test) | **PULLED-WEIGHT — decisively** | It is the control that stopped this milestone from closing on agent authority after the agent restated a signed criterion. A gate that only ever says PASS is not a gate; this one said BLOCKING for the right reason |
| Trust telemetry (V3C-84) | **FIRST REAL TABLE** | M3 could only set a baseline. M4's table is in the closure report §3: 27 findings, 24 closed in-wave, 5 ledgered, 1 tripwire |
| D-106 agent git + V4C-64 trailers | **PULLED-WEIGHT** | 4 wave commits + closure, attributable, zero catastrophe-class ops |
| Council-instead-of-owner | **THEORETICAL (third milestone running)** | 0 convened. The one genuine judgment call — retiring a signed criterion — is precisely the class that must go to the owner, not a council |

## The milestone's transferable lesson

**A fix written to close a review finding is new code, and it inherits the review obligation.**
"It was written to close a BLOCKING finding" reads like evidence of correctness and is not: the
W4 display-delta fix was correct in behaviour and undefended in fact, and it also *introduced* a
second-order defect (the zero-guard existed on one output field and not the three next to it).
The general shape is V4C-49 — a rule without its gate — applied to fixes rather than to rules.
Operationally: after closing review findings, re-review the delta with fresh eyes before the wave
closes, and fault-inject the FIX, not only the original defect.

Second, smaller: **a criterion can be wrong.** M4's headline criterion was written before the data
existed to test it, and the data said it could only be met by lying. The pipeline handled this
correctly — restate in the open, write the ADR, block the gate, escalate to the signer — but the
cheaper move is to notice earlier that a criterion asserts a fact about data nobody has measured
yet. Candidate rule for the next plan: any criterion containing a NUMBER about live data gets a
measurement task in the wave that precedes it.

## Carried question (posed by this retrospective, answer due M5)

The engine can now say "these four plans are the same model; buy the $4.99 one". That is the most
useful sentence it produces — and it is only true because four plans happen to name the same model
*and* that model happens to be benchmarked. **Question: when a provider names a model no benchmark
covers (today: the entire Claude and ChatGPT plan surface for coding), should the product (a) stay
silent as now, (b) say "we cannot rank this plan and here is why", in the answer itself rather than
in a coverage report, or (c) rank it on a weaker-but-documented signal with the weakness stated?**
Option (c) opens the door this project has kept shut since M1 — inference in the ranking path — so
it needs the owner, not a rule. Owner input shapes the M5 plan.

## Numbers

4 waves · +41 tests (152→193) · 27 review findings (24 closed in-wave, 3 fixed at closure,
5 ledgered with owning milestones) · 18 fault injections, 2 initially stay-green · security close
**PASS** (0 BLOCKING) · quality gate **BLOCKING** on one owner signature · 1 escaped-blocker
tripwire · 2 criteria deferred to M5 with reproduced environmental evidence · 0 control bypasses.
