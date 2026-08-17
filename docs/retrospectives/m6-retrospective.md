# M6 Retrospective (G.12 — fourth retrospective; answers M5's carried question)

Date: 2026-08-17 · Scope: M6 (W1–W4 + closure, commits `1faaf77..HEAD`) · Author: the lead agent,
which authored every line of this milestone's code and none of its reviews. Verdicts cite committed
artifacts, not memory.

## Answer to M5's carried question

M5 asked: *two coding surfaces now exist — `coding` (dated evidence, 5/10 plans, mixed effort) and
`agentic-coding` (6/10 plans, one effort level, no evaluation dates at all). Should the product
present both to a user, or choose one and relegate the other to evidence?*

**The owner ruled A: present both, neither leading.** M6 is the machinery for meaning it.

What the ruling cost, precisely, is the part worth carrying forward. "Both, neither leading" is
trivial to *say* and turned out to be the hardest thing in the milestone to *enforce*. The guard
protecting it went through three formulations:

1. a nine-name denylist — killed by renaming the field `primary_surface`;
2. a sixteen-stem regex — killed by `display_order`, `suggested`, `authoritative`, and by rewriting
   the ordering note's PROSE with no key change at all;
3. a frozen key set — which holds, because it states what is allowed instead of what is forbidden.

**A denylist can only forbid the words its author thought of.** That sentence is the milestone's
transferable lesson and it recurred in four unrelated places: the precedence guard, the YAML wiring
predicate (a four-word list that detected 1 of 7 entry-point forms), the enumeration of YAML inputs
(three names typed out, missing the only remote-fed one), and the smoke-test endpoints (typed out,
one saying `main/` where the client says `master/`). Same instrument, four contexts, one milestone.

## Discipline verdicts

| Discipline | Verdict | Evidence |
|---|---|---|
| **Fresh-eyes review (K.7)** | **PULLED-WEIGHT, and it is the only reason this milestone is honest** | Ten BLOCKING across three seats, in code whose gates were green every time. W1: two, including the denylist guard. W2: two, including a migration that had followed the GATE's signal rather than the policy. W3: four + three + two, including an unwired startup validator and an unguarded remote-fed YAML input. **Nothing on that list was found by the author, and the author had run fault injection before every dispatch** |
| **HIGH tier at W3 (V3C-78)** | **PULLED-WEIGHT — measured, not assumed** | The Tester ran **52 mutants across three rounds** against the author's 11 in the first; **16 stayed green**. One combined reviewer would have shipped an unwired validator, an unguarded remote input, a broken exit-code contract, and a denial of service the author introduced while fixing a denial of service |
| **Fault injection (V3C-72)** | **PARTIAL, and the gap is the finding** | The author's mutants killed 100% of the author's mutants — a set measures its own blind spot at zero by construction. Across the milestone, reviewer mutants that stayed green: W1 three, W2 three, W3 sixteen. The rule the project already had (*every stay-green fault gets its mandatory test*) worked perfectly; what failed was the imagination generating the set |
| **Citing-test discipline (V3C-02)** | **PARTIAL — third milestone running** | Every criterion had a citing test at every gate, and ten defects shipped past them. The recurring shape, in the reviewers' words: **a control that existed, was cited, and did not run.** A CORS block whose deletion changed nothing; a rollback that executed zero statements; a validator no path called |
| **The warnings ledger** | **PULLED-WEIGHT — five carried rows closed** | W-002, W-005, W-008, W-009, W-010 were all deferred to "the API milestone" with reasons, and all five were paid. **W-001 closed after four surviving closes**, and its diagnosis had been right on day one — what blocked it was that the remedy is a waiver only the owner may grant |
| **Deferral with a stated trigger** | **PULLED-WEIGHT and simultaneously the milestone's worst defect** | W-005's deferral said "when an untrusted producer becomes possible". That trigger was met, the ledger was right, and the guard was installed on the three repo-committed files and NOT on the one input fetched over the network. **A correct deferral does not survive an implementation that does not re-read it** |
| **A0.5 + D-117 inter-wave commits** | **PULLED-WEIGHT** | Twelve attributable commits, zero catastrophe-class operations, no work lost across four waves. D-114 removed agent commit authority and D-117 returned a narrower form of it one day later — recorded as a tension rather than smoothed over |
| **GP v5.0 adoption mid-project** | **PULLED-WEIGHT** | The conformance suite found three real defects on its first run, including 20 wave records that had never been governed by anything. It also produced five findings about GP itself, three of which are the same blind spot |
| **The owner's escalate-now rule** | **PULLED-WEIGHT** | Four escalations, all answered same-session: Ruling A, the v5.0 baseline, W-001's waiver, and the REQ-API-005 criterion amendment. **The two that had gone stale — W-001 and OQ-3 — were both things the owner had been SHOWN rather than ASKED** |

## The milestone's transferable lesson

**A denylist can only forbid the words its author thought of — and an enumeration that is typed out
is a denylist wearing better clothes.**

This project already knew the first half. What M6 adds is that the second half is the same defect,
and it is much harder to see: a list of three filenames, four function names, or five endpoint URLs
reads as thoroughness. Every one of them in this milestone was missing exactly the member that
mattered, and in three of the four cases the missing member was the only one with real exposure.

Operational form: **when you write a list of things to check, write the code that produces the
list.** If you cannot derive it, say in the same sitting which member you would most regret
missing — and then check that one by hand.

## Numbers

4 waves + closure · +83 tests (271 → 354; 361 with the Epoch bundle) · **10 BLOCKING** across three
review seats, all closed · 4 review rounds at W3 alone · 47 fault-injection mutants by the author,
all killed · 52 by the Tester, 16 of which stayed green on the author's code · 5 ledger rows paid,
W-001 closed after four surviving closes, 4 new rows opened (W-017 escalated, W-019, W-021, plus
GPF-001..005 handed back to GP) · 7 ADRs ratified (D-113..D-120) · 1 criterion amended at the gate ·
0 catastrophe-class git operations.

## Carried question (answer due M7)

M6 froze `/v1` and proved, four times over, that this project's tests are good at catching drift and
bad at catching absence — a control that never runs passes every gate it has.

**Question: should the next milestone spend a wave on making "does this control actually execute"
mechanically checkable, or is that a control about controls that will itself go unrun?**

The concrete shape would be a coverage-derived gate: every function in `src/` that no production
path reaches is either deleted or declared. The argument for is that all ten BLOCKING findings this
milestone were reachability failures, not logic failures, and reachability is the one property a
tool can decide. The argument against is that this project has now shipped four controls that read
as installed and did not run, and a fifth that checks the other four is the same bet at one remove —
`make bootstrap-check`, `make smoke-deps`, `make check-templates` and `CODEOWNERS` were all exactly
that. **The owner's judgement is needed on whether the pattern is worth automating or worth
staffing**, because M6's answer to it was three review seats and that is expensive but it worked.
