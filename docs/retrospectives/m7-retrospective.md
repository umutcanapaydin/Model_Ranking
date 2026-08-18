---
record_type: retrospective
id: m7-retrospective
status: draft
date: 2026-08-18
---
# M7 Retrospective (G.12 — fifth retrospective; answers M6's carried question)

Date: 2026-08-18 · Scope: M7 (W1–W4 + closure, `9f4471d..HEAD`) · Author: the lead agent, which
wrote every line of this milestone's code and none of its reviews.

## Answer to M6's carried question

M6 asked: *ten of ten BLOCKING findings were reachability failures — a control that existed, was
cited, and did not run. Should M7 spend a wave making "does this control actually execute"
mechanically checkable, or is a control about controls the same bet at one remove?*

**The owner ruled: no — fix the reachability failure that was actually costing something, and carry
the general question.** M7 is the answer to that ruling, and the milestone supplies unusually direct
evidence for it, because the two approaches were run side by side without anyone planning to.

**What deleting unreached code bought:** W3 removed `serving_snapshot` and W-017 closed. Not
bounded — *gone*. Three security passes had derived three different amplification figures for that
defect across two milestones; the fourth pass derived a fifth number and it no longer mattered,
because a file inflated 125× cost zero additional memory. **An entire class of finding stopped
existing**, along with the five constants, one derived function and three tests that had been
maintaining the bound.

**What a control-about-controls bought:** also a lot, and it is worth being fair to the idea the
owner deferred. The registry-coverage test in `test_sources.py` walks `src/app/clients/` with `ast`
and refuses any client the build neither ingests nor declares a bundle. `test_ci_argument_drift.py`
reads the workflows and resolves every module they invoke. Both are exactly "a control that checks
whether controls are wired", and both caught real things.

**But the milestone also showed the trap the owner was worried about, twice, in my own hands.**
`test_ci_argument_drift`'s module check lived *inside* the test that used it — replacing its
predicate with `if False:` left 462 tests green. And the `unresolvable_modules` extraction that
fixed it is now itself a control that would need a control. The regress is real; what stops it is
not another layer but driving the predicate with a known-bad input, which is cheap and does not
generalise into a framework.

**Verdict on the question: the owner was right, and for a reason M6 could not have known.** A
reachability gate would have flagged `serving_snapshot` as reached and healthy — it *was* reached,
on every request. The defect was not that it never ran. **Reachability tooling finds unrun code; it
cannot find code that runs and should not exist.** M6 generalised from ten findings that happened to
share a symptom.

## Discipline verdicts

| Discipline | Verdict | Evidence |
|---|---|---|
| **Fresh-eyes review (K.7)** | **PULLED-WEIGHT, and it is again the only reason this is honest** | **Thirty BLOCKING in W1 alone**, across three seats and three rounds, none found by the author. Round two and three found defects the author introduced *while fixing round one*. The Stage-4.0 closure pass then returned PASS with 8 MINOR, of which six were real and fixed |
| **The owner's calibration ruling (D-122)** | **PULLED-WEIGHT, and it should have come sooner** | The owner said, in plain words, that we are not writing avionics — after one wave consumed an entire session on a solo project with no users. He had given the same instruction in M6 and the agent had not applied it. W2–W4 ran at calibrated depth and cost a fraction of W1 while still closing W-017 and finding real defects |
| **Fault injection (V3C-72)** | **PARTIAL, and the pattern is sharper than M6's** | The author's mutants killed 100% of the author's mutants again. But two of W2's four survivors were failures of the author's own TESTS rather than of the code: one drove the wrong exception path entirely, and one pinned a fix the security seat had already proven and the author had never tested. And one "survivor" was an equivalent mutant — `(False and X) or Y` is `Y` — which would have sent me hunting a hole that was not there |
| **Citing-test discipline (V3C-02)** | **PARTIAL — fourth milestone running** | Every criterion had a citing test at every gate. The Stage-4.0 seat still found one surviving mutant of eight (the 500 body), and W3's own deletion removed a live guard nobody noticed for two mutants |
| **The warnings ledger** | **PULLED-WEIGHT — the two oldest rows closed** | **W-017 closed by deletion** and **W-023 closed by production** — and neither closed the way its own ledger row proposed. W-023's recorded remedy was a one-line `schema migrate`, which could not have worked: a migration adds a column, it cannot populate `px_median`. **A correct diagnosis can carry an insufficient remedy for two milestones and nobody re-reads the remedy** |
| **Records-versus-reality** | **FAILED once, in the worst possible place** | The D-121 amendment claimed a test file "also asserts that a surface WITH evidence still gets the budget sentence". It did not. A record asserting a control that was not there — the defect this project has spent five milestones on — committed by the author *in the sentence documenting the fix* |
| **Deferral with a stated trigger** | **PULLED-WEIGHT** | D-123 defers go-live with a product event as the trigger rather than a date, and W-030/W-031 carry the two things the Stage-4.0 seat marked unverified. The seat named them itself instead of letting a PASS stand unqualified |

## The milestone's transferable lesson

**A control that runs on every request can still be the defect, and no reachability tool will say
so. The question is not "does this execute" but "should this exist".**

`serving_snapshot` executed perfectly, on every request, for a whole milestone. It was cited, tested,
measured three times, and given a budget with five declared constants. Deleting the *reason* it
existed — a write on the read path — deleted the control, the constants, the budget, the tests and
the entire class of finding in one move.

Second, smaller, and paid for twice in one milestone: **deleting a test is a decision that needs the
same care as writing one.** W3 removed three tests that guarded the memory budget; one of them also
guarded the concurrency agreement, which had nothing to do with snapshots and is still live. Two
mutants walked through the gap. The replacing test's own docstring says quiet deletion is how a
control disappears.

## Numbers

4 waves + closure · **396 → 511 tests** (+115) · **30 BLOCKING in W1** across three seats and three
rounds, plus Stage 4.0's 8 MINOR (6 fixed, 2 carried as unverified) · author fault injection: 31
mutants across W1–W3, 11 survivors, all given mandatory tests, all subsequently killed · Tester seat:
118 mutants across two rounds, 26 then 22 surviving · **W-017 and W-023 closed**, W-021 closed,
8 new rows opened · 3 ADRs (D-121, D-122, D-123) · 1 signed-plan promise not delivered and ledgered
rather than dropped (W-027) · 0 catastrophe-class git operations · 0 deploys.

## Carried question (answer due M8)

M7 closes with the engine deploy-ready and not deployed, and M8 puts an iOS client in front of it —
the first consumer this project has ever had that is not a test.

**Question: `/v1` was frozen by D-115 with no consumer in existence. Now that a real client is being
written against it, should M8 treat the contract as fixed and build the app around it, or is the
first consumer exactly the event that earns one revision?**

The argument for holding it: a contract that moves when its first consumer complains is not a
contract, and D-115 exists because the owner's Ruling A was trivial to state and took three rounds
to enforce. The argument for revising once: every field in that payload was designed by someone
imagining a client, and the M6 reviews demonstrated four times that imagined enumerations miss the
member that matters. **The owner's judgement is needed on whether "frozen" means frozen before or
after the first real reader** — and the answer should be decided now, in the abstract, rather than
in the moment when a specific field is inconvenient.
