---
record_type: retrospective
id: m9-retrospective
status: ratified
date: 2026-08-22
---
# M9 Retrospective — the milestone where the product started keeping itself current

## The carried question, answered

> **M8 asked: the engine has been ready to deploy since M7 and has now not deployed twice. At what
> point does "deploy-ready and not deployed" stop being a schedule fact and become an architectural
> claim we have never tested?**

**M9 answered it by accident, in the one place it could not be argued away: REQ-REF-007.**

The criterion says ingestion never runs on the serving host — D-116, ratified three milestones ago,
one of this project's load-bearing separations. Writing the refresh made it concrete for the first
time, and it could not be met. Not because the code is wrong; because **there is one host.** The
owner's Mac serves the engine and builds the artifact, and no amount of structural care changes
that. The row is marked PARTIAL and says so.

**So the answer is: it already has.** The moment a requirement was written that depends on there
being two machines, "deploy-ready and not deployed" stopped being a schedule fact. D-116 is
currently a claim about a topology that does not exist. Everything downstream of it — that
ingestion cannot touch a serving process, that a refresh hands over an artifact rather than
reaching into a server — is enforced structurally and has never been tested the only way it could
be, which is by there being somewhere else for it to run.

The honest form of the answer, for M10 to carry: **a separation you cannot violate because you only
have one machine is not a separation you have verified.** W-030 and W-031 have said something like
this for three milestones about the platform surface. REQ-REF-007 is the same sentence arriving
from inside the product rather than from the deploy checklist.

## What this milestone taught

### 1. The measurement before the plan was worth more than the plan

M9 was scoped expecting to build artifact hand-over: a running engine keeps a replaced file's
inode, so a refresh would serve stale data until someone restarted it, and this project had been
bitten by that shape twice. The experiment took two minutes and **a third of the milestone
evaporated** — the adapter opens a read-only connection per request, so a swap lands immediately.

The two earlier "stale artifact" incidents turned out to be stale CODE wearing the same symptoms.
Two beliefs, both held on the strength of a real incident, both about the wrong mechanism.

### 2. Every serious defect in this milestone was found by fault injection or by someone else

Not one was found by reading. The tally is stark:

| Wave | Found by | What |
|---|---|---|
| W1 | the author's own mutants and tests | a corrupt candidate publishing over a working artifact; a fingerprint masking visible price moves; two JSON documents on one stdout; the injection seam binding at definition time **for the fourth time in this project** |
| W2 | an independent seat | a crashed cycle reporting as healthy; a guard that compared row counts and nothing else; **a refresh structurally incapable of publishing a freshness update** |
| W3 | writing the SIGKILL test | a killed cycle wedging the refresh for two hours |

The independent seat wrote 40 mutants and 8 survived, against the author's report of 24 with none
surviving. **That ratio is the milestone's most reusable number**, and it is the same lesson M8
recorded: a mutant set written by the author of the code tests the author's model of the code.

### 3. The failure that looks like success needed naming before it could be designed against

The plan's §0 named it: an unattended refresh that FREEZES the product is worse than one that
publishes something bad, because a freeze is invisible — every gate green, every cycle exiting 0,
the artifact quietly ageing. Naming it in advance is why D-128 did not choose a zero threshold, and
why the review's verdict on the threshold was *"the direction is right; I would not move the number;
I would add axes."*

It arrived anyway, through a door nobody was watching: **the fingerprint**. A refresh that cannot
detect a freshness improvement publishes nothing, forever, while reporting health — the §0 freeze
exactly, reached through the comparison rather than through the guard. The trap was correctly
identified and incompletely defended.

### 4. A test that reaches the wrong branch proves the wrong rule

Three mutants on the 25% threshold survived because the fixture's surface had THREE models, so
"loses more than a quarter" and "loses everything" were the same event and the shrinkage branch
never executed. Later, a missing-surface test passed because the BUDGET axis caught what the count
branch was meant to catch.

Both read identically to tests that work. This is the fixture-reachability class M8 first recorded,
and M9 produced four more instances — which suggests it is not a lapse but a default failure mode
of writing tests after the code.

## What went badly, plainly

- **Two waves closed with no independent seat**, and the one that ran found three BLOCKING. W1 and
  W3 still have none.
- **I committed on a red gate**, reading `make check`'s exit code after the commit rather than
  before. Third time in this project; recorded both previous times.
- **D-130 claimed to answer a plan question it does not address**, and the W2 wave record repeated
  the claim. Caught by the independent seat, not by me.
- **D-128's worked arithmetic was off by one in both examples** — the ADR's entire justification
  for its number, wrong in the direction that made the rule look tighter than it is.

## The question carried to M10

> **Every control this project trusts was verified on one machine, by one agent, against data it
> fetched itself. The refresh now runs unattended on a schedule, which removes the last human from
> the loop — and the human was the error-detection mechanism for everything the gates do not
> cover.**
>
> So: **what does this system do when it is wrong and nobody is looking?** Not "what does it do when
> a source is down" — that is designed for. The question is what happens to a defect that no gate
> catches, in a product that now updates itself, when the person who used to notice is no longer in
> the path. M9 added a status file and an escalation counter. Is that the answer, or is it the
> smallest thing that let this milestone close?
