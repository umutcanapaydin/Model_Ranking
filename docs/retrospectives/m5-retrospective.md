# M5 Retrospective (G.12 — third retrospective; answers M4's carried question)

Date: 2026-08-16 · Scope: M5 (W1–W4 + closure, commits `38eaa17..HEAD`) · Author: the closing agent,
which authored none of W1–W4. Verdicts cite committed artifacts, not memory.

## Answer to M4's carried question

M4 asked: *when a provider names a model no benchmark covers, should the product (a) stay silent,
(b) say "we cannot rank this plan and here is why" in the answer itself, or (c) rank it on a weaker
documented signal with the weakness stated?*

**M5 answers (b), and the milestone is largely the machinery for saying why.** No inference entered
the ranking path — D-104 held. What changed is that "cannot rank" stopped being one undifferentiated
silence and became a set of stated reasons the user and the owner can act on: no link at all
(curation), linked but no score on this benchmark (benchmark coverage), scoreable but priced out
(`excluded_by_budget`, D-111), and — new and uncomfortable — scoreable but on evidence that carries
no evaluation date at all (`agentic-coding`, REQ-ING-011b branch b). Option (c) was never needed
because a second documented board existed; the answer would be different if it had not, and that
version of the question now belongs to whoever faces a category with no board at all.

## Discipline verdicts

| Discipline | Verdict | Evidence |
|---|---|---|
| **Measure in the wave BEFORE the criterion** (the rule M4's retrospective adopted) | **PULLED-WEIGHT — decisively** | W1 measured five boards before anyone committed, and the board choice changed because of it: the obvious swap (best coverage) publishes no evaluation dates, so the category kept its dated source and the new board arrived as a separate category. Without W1 this milestone ships a category aged on model release dates |
| Fresh-eyes per-wave review (K.7/V3C-68) | **PULLED-WEIGHT, and its absence is the milestone's largest single finding** | W1–W3 got reviews and closed clean. W4 got none — and carried 3 BLOCKING + 9 MINOR, one of which printed a success message over an unusable database. The control's value is measured exactly by the wave that skipped it |
| Security review at closure (Stage 4.0) | **PULLED-WEIGHT** | Found a BLOCKING the code review missed — the picks published the effort policy instead of the evidence — by reading the payload against the export of the same run. Two artifacts of one run contradicting each other is a shape a code reviewer does not naturally look for |
| Fault-injection (V3C-72) | **PULLED-WEIGHT, with a new sub-lesson** | 22 mutants. Two initially stayed green and in ONE case the mutant was wrong, not the test (first-match-wins). "Green mutant → weak test" is a reflex that was 50% wrong here |
| Citing-test discipline (V3C-02) | **PARTIAL** | It works when the test can fail. The W4 structural guard could not — it asserted the predicate it had filtered on — and stayed green for four waves while the defect it named shipped. Third instance of this class in this project |
| Live-name corpus for the registry (M4-W1) | **PARTIAL — did not generalise to new sources** | It defends the boards it has met. M5 added two boards, the corpus was not extended, and `kimi-k2.5`/`kimi-k2.6` folded into `kimi-k2` on live data. The rule that fixes it is written into EXPERIENCE: a new source is a new corpus, in the same commit |
| Warnings ledger | **PULLED-WEIGHT** | 5 new rows, each with an owning milestone and a reason; W-002/W-005 were re-assigned when M5's scope changed rather than left contradicting the plan. Counter-example: W-001 has now survived THREE closes because its remedy is an owner decision the ledger has no way to model |
| Wave-close checklists as a HANDOVER medium | **PULLED-WEIGHT — unplanned use** | The previous agent's checklists and W4 implementation plan are the only reason an unrelated agent could reconstruct the milestone. They were designed as evidence; they worked as memory |
| A0.5 + D-106 | **PULLED-WEIGHT** | 6 attributable commits at boundaries, zero catastrophe-class ops, and the milestone stopped at the owner's gate on a criterion-meaning question exactly as the escalate-now list requires |
| Council-instead-of-owner | **THEORETICAL (fourth milestone running)** | 0 convened. The two decisions that mattered — the board choice and the effort policy — are precisely the class that must go to the signer |

## The milestone's transferable lesson

**A guard that cannot fail is worse than no guard, because it reads like coverage.** This project has
now paid for that three times, and the third instance was written by an agent that had already read
the other two in EXPERIENCE — which means the lesson as previously written was not operational.
Restated so it can be acted on: *when you write a guard, write the mutant that should kill it in the
same sitting; if you cannot describe that mutant in one sentence, you have written a comment with an
`assert` in front of it.*

## Carried question (answer due M6)

M5 shipped two coding surfaces: `coding` (dated evidence, 5/10 plans, mixed effort levels, now
disclosed) and `agentic-coding` (6/10 plans, one effort level, no evaluation dates at all). Both are
honest about what they are. **Question: should the product present two coding answers to a user, or
choose one and relegate the other to evidence?** A user asking "which subscription for coding" gets
two rankings with different memberships and different weaknesses, and no rule currently says which
one leads. Choosing means deciding whether dated-but-narrow beats undated-but-broad — a product
judgement about which weakness a buyer should be exposed to, not a technical one. Owner input shapes
the M6 plan, and the HTTP API freezes whatever is decided into a contract.

## Numbers

4 waves + closure · +78 tests (193 → 271) · 40 review findings (20 in-wave, 20 at closure; 4 BLOCKING
total) · 22 fault injections, 2 initially green · coding coverage 1/10 → 5/10, new agentic-coding
6/10, union 6/10 · security close PASS (condition — the owner's migration review — discharged at the
gate) · quality gate BLOCKING on one owner ruling, cleared by ratifying D-112 at the gate · 5
warnings carried to M6 with owning milestones · 1 tautological test found and removed · 1 agent
handover mid-milestone, recovered from files alone.

**Gate outcome (2026-08-16):** three rulings — D-112 and D-111 ratified, migration reviewed and
approved, W-011 ruled RE-AUTHOR. M5 CLOSED and signed.
