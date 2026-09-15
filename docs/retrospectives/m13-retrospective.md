---
record_type: retrospective
id: m13-retrospective
status: ratified
date: 2026-09-15
---
# M13 Retrospective — the question became the front door, and the numbers stopped overstating

## The carried question, answered

> **M12 asked: what else is the team not choosing? The council was convened once, by the owner, on
> a hunch, and found a defect class nobody inside had named. Should an outside seat be a thing this
> project HAS — scheduled, budgeted, with a standing question — or a thing it reaches for when
> somebody remembers?**

**M13 ran an outside seat at every step, and the answer is that each KIND of seat catches a
different kind of defect — so the project should have all three, on a schedule.**

- **A second opinion with no brief** read the code before the council's framing and found four
  defects in the scoring path and its instruments: Pareto dominance wrong in both engines since M2,
  a startup probe that admitted an unservable database, a refresh fingerprint blind to attribution,
  and a runner scoring an unrun leg as a pass. Five council seats, briefed on the product question,
  had found none of them. **A brief is a lens, and a lens is also a blind spot.**
- **The council, with a brief,** was right about direction: remove the controls, keep the numbers.
  It was wrong three times in detail, and each time a measurement overturned it: the D-128 ruling,
  the undated-primary notice, and the greedy tie bands (D1), which printed 47 within-margin pairs
  as ordered. **A ruling is a hypothesis until someone measures it.**
- **The per-wave independent seats** caught the author. The W2 Code-Reviewer returned BLOCKING on a
  criterion the author believed met. The W2 Tester showed that a structural test checking function
  NAMES let every argument-level change through, twice.

So the answer is yes, and more specifically: **a no-brief second opinion at every milestone
opening, a briefed council when the product question is open, and independent seats per wave.**
The first is the one this project did not have and would not have chosen. It was the owner's
request, not the process's, and it found the defects in the part of the system the team believed it
owned.

## What this milestone taught

### 1. A fixture that claims a property does not have it

Three test fixtures called themselves "a servable artifact" and ranked nothing on any surface; each
docstring already asserted what it lacked. They passed for years because the probe they were written
against asked only whether tables existed. Correcting the probe exposed all three at once.

### 2. A fixture's clock is part of the fixture

`make check` went red on 2026-09-15 with no code change. A roster fixture took `observed_at` from
the wall clock while its dates were literals, so every fixture date expired thirty days after it
was written. The product was right, since staleness is data-owned; the fixture was a test with a
use-by date. A full-suite run under a clock moved to 2027 found no second instance.

### 3. No single rank can say "tied", because "tied" is not transitive

The D1 bands were the obvious design and they could not satisfy their own criterion. Inside the
margin, A ties B and B ties C while A and C are separable, so any single position number must order
some tied pair. **When a criterion is about a relation, check whether the relation is transitive
before choosing a representation.** Ranges satisfy it by construction, and the property test
asserts it over every shipping margin.

### 4. A tripwire that matches spellings is blind by design: say where, and name the crossing

REQ-APP-005's arithmetic gate matched `.score -` and could not see `other - score`. The rank ranges
crossed it, D-138 permits the crossing, and the gate now matches local score arithmetic and names
the one file allowed to do it. **An exemption is a record, not a silence.**

### 5. Before calling a defect the app's, reproduce it in the system's own component

The software keyboard never appeared on the simulator. The obvious reading was an app defect, and
the handover recorded it as one. Safari's own address bar, in edit mode on the same simulator,
raised no keyboard either. That one control experiment moved the defect from the app's list to the
environment's, and it kept a wave from "fixing" something that was not broken.

### 6. When no threshold separates two groups, choose the error and make it cheap

The wording tier's decline hints fixed one false answer and created another. A photo QUESTION and a
website task that INVOLVES a photo score the same way against the hints, and a 26-question probe
showed that no threshold divides them. Two rewordings made it worse. Tuning would have been fitting
the probe. So the choice was made in the open: a false decline is labelled and puts the closest
surfaces one tap away. The other error, a measured-looking answer to an unmeasured question, is the
one the criterion forbids. The independent seat endorsed the choice after re-probing it. **When
measurement says a classifier cannot be right both ways, the design question is which wrong costs
the reader less.**

### 7. A memo answers the question its key asks

W1 memoised the `/health` probe on `(path, mtime, size)`. The key asked whether the content was
the same, and the probe answered whether the process could serve it. A `chmod`, or a same-size
rewrite with the mtime set back, separated the two, and `/health` read `servable` over a 503. The
security pass most likely to have questioned it at W1 was waived there, and waived again in W2 and
W3. Each waiver was honest, and none was written where the counter reads. **A cache claims that
nothing its answer depends on has changed, so list what the answer depends on and key on all of
it. A waiver recorded only locally is recorded where nobody counts.**

## The question carried to M14

> Every verdict in M13 was reached on an artifact the refresh has not rebuilt since 2026-08-27, on
> a simulator whose keyboard never appeared, for a phone the app has never run on. The terminalbench
> dates are fixed and invisible; the question field has never been typed into by anyone.
>
> **What would it take for the next milestone's evidence to come from the product as a reader
> meets it — refreshed data, a real keyboard, a real device — rather than from the instruments
> around it?**

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-09-15
