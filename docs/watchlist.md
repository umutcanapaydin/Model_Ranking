---
record_type: register
id: watchlist
status: ratified
process_version: v6.0
date: 2026-09-01
---
# Watch list — controls removed, and what brings each one back

**The owner's rule, translated:** *"if it happens again we bring it back in, based on how many times it
recurs. That way we learn which ones actually earn their place and which one we added because we hit it
once in a million and it's now just dead weight."*

**This is the first time this lineage has ever asked whether a control earns its place.** Every rule we
have was added after something went wrong, and not one was ever revisited. A list that only grows is
not a policy, it is a sediment.

## Two counters, and why one was never enough (.1)

Until this list kept **one** number, and it answered the wrong question twice over.

- **It could not see inside a project.** GPF-006 measured a project where a watch-listed failure mode
 recurred three times in one milestone. The counting rule said *"two occurrences in the same project
 count once"*, so the list read **1**. A mode that fires three times in eleven days and a mode that
 fires once in three projects are not the same fact, and one number could not tell them apart.
- **It did not count the control groups.** Two of 's four harvests came from projects that
 never installed GP. They reproduced GP-catalogued failure modes anyway — the strongest external
 validity evidence this lineage has ever received — and the old rule threw it away.

So each row now carries two counters, and **each increment cites the harvest record id that moved it,
so a poisoned harvest can be backed out without re-deriving the whole row.**

| counter | question it answers | counting rule |
|---|---|---|
| **`intra`** | *did bringing it back actually work?* | recurrences **since this row's `epoch`**, within a single project, counted individually. This is a repair-efficacy measurement, not all-time density — occurrences before the epoch belong to the case for the return, not to the case against it. |
| **`cross`** | *is the failure mode general?* | **distinct projects** since the epoch. **Non-GP projects count** (.1 — an explicit rule change, adopted by the owner, not smuggled in as an instrument repair). |

`epoch` is the date the row last changed state — removed, or returned. A returned row's counters reset
at its return, because the question changes: before the return we are asking *should this come back*,
and after it we are asking *did the return fix anything*.

## How a row returns

A removed control comes back when `cross` reaches its `returns at` — counted **in real projects, not
here.** It returns with field evidence and a falsification recipe, or it does not return.

If both counters stay at zero, that is a result too, and a valuable one: it means we correctly
identified something we had over-fitted to a single incident.

**A returned row is not a closed row.** `intra` keeps counting after the return, and a mode that keeps
recurring after coming back is evidence about the *repair*, not about the mode — which is exactly the
state both returned rows are in today.

| id | what it caught | why removed | epoch | `intra` | `cross` | returns at |
|---|---|---|---|---|---|---|
| `check-templates` | a shipped template that no longer parses | needs a built artifact; unfalsifiable here for 5 versions | 2026-08-12 (removed) | 0 | **0 — stays (.2).** Two field config defects occurred, but the SHIPPED body read only `.env.example` files and could not have caught either; this list counts *"the failure this control would have caught."* Superseded by the NEW config-binding control (Block B), which entered on its own field evidence with widened scope | — (superseded) |
| `cold-start` | a repo that cannot be built from scratch | needs a clean machine; never demonstrated to catch anything | 2026-08-20 (**returned**) | **not separated at source** — the P2 harvest records the mode as recurrent but does not break it into individually dated occurrences; the next harvest under the 3rd-edition prompt is the first that can. Recorded as unmeasured rather than as zero, because zero is a claim | **2** — `experience-harvest-Project-B-Project-C-deployment` (P2, GPF-006) · P3/P4 combined harvest §4b. Corrected down from the intake's 4/4 by the Skeptic | returned — still unwired, condition |
| `journey` | a deployed artifact failing the real human path | needs a deployed URL; unfalsifiable here for 5 versions | 2026-08-20 (**returned**) | **1** — `experience-harvest-Project-B-2026-09-15` §4b, dated 2026-09-14: the deployed console runs a pod-local patch and is therefore not the built artefact; the control meant to notice compares two directories and never a pod. Found by document review. *(The five PRE-epoch root causes that produced the return — ingress misroute, popup 500, 422 concat, placeholder username, stripped security headers — are the case FOR the return and are not counted here.)* | **3** — `experience-harvest-Project-B-Project-C-deployment` (P2, GPF-006) · P3 §4b (#352/#355/#378 back-nav; scope-reset ×6) · P4 §4b (`3fcc8f5`, `4e8de30`, `0db057c`, `2c65eae`) | returned — still unwired, condition |

**Read the two returned rows together and they say something uncomfortable:** both came back on field
evidence two cuts ago, both are still not wired into any gate, and both went on recurring in the
very next harvest window. Their counters are still moving **after** the decision to return them —
and as of 2026-09-14 `journey`'s `intra` is no longer unmeasured: it is 1, in the field, post-return,
found by a human reading a document, because every remaining check compares the repository against
itself. The control was never the thing that failed here — the wiring was, and condition is where
that debt is recorded.

## Deferred candidates — what brings each one back (condition)

The watch list has always tracked controls GP **removed**. It also tracks
candidates GP **declined to adopt**, with the same counters and the same discipline — because a
DEFER with no counter is a refusal that has not admitted what it is, and the next council
re-litigates it from prose.

Counts below are the ones a seat re-measured after the intake packet had already been scored. The
packet declared the corpus *"one project and GP"*; a `grep -n "^# "` found the combined record is
four documents spanning **two further non-GP projects** (Project-D, Project-G). Five counters were
too low, one candidate moved from DEFER to ADOPT, and the intake's own step 17-d — *"cross counters
unmoved by this corpus"* — was the consequence. Recorded as.

| id | the failure it would catch | verdict | `cross` (measured) | returns at |
|---|---|---|---|---|
| `D` status-claims | a claim about work IN PROGRESS, unmeasured — *"still running at roughly thirteen minutes"* shipped in a report; nothing had run, the log was 0 bytes | DEFER, 6/1 | **1** — and it is the one candidate the packet scored correctly. Self-reported by the harvester about his own error, which makes it honest rather than strong | 2 distinct projects |
| `E` no-named-consumer | a document produced with no defined consumer — one 214-line finding document plus its review, ~a full session, ruled not to be applied four days later | DEFER, 5 DEFER / 1 ADOPT / 1 REJECT | **≥2** — Project-G: 257 checklist boxes across five documents, **zero ticked**; Project-B twice | not a count. **E returns on a DETECTABLE form**, which is why it was deferred: nothing distinguishes a genuinely-named consumer from a filled-in box, and the PM seat's dissent (*"the only candidate that subtracts"*) is recorded against that |
| `H` merged≠deployed | a fix closed on merge read as a fix deployed — 35 items awaiting verification read as finished by the owner himself, two at the project's highest severity | DEFER, 7/7 | **≥2** — Project-D: 78 of 78 CI-triggering events produced no verification across ~20 merged PRs, inert 9 days, *"caught by nobody"*; Project-B at customer cost | **UNPARKED (§6; recorded here at).** The trigger used to be condition, which was REFUSED: two increments, zero lines, reporting GREEN the whole time because its artifact existed and carried no anchor. **The strongest single measurement in the corpus was parked behind a condition nobody had written a line of.** The trigger is now its own evidence, which already stands at `cross ≥ 2` and is therefore MET. H is not waiting on a count. It waits on an INSTRUMENT: GP cannot observe a forge, which is the same ground was refused on, and inventing an exception here would re-litigate that refusal. Record the evidence as sufficient so the next council does not re-derive it — and record that the blocker is capability, not doubt |

**Two of these three do not return on a number, and that is deliberate.** `E` needs a form that can
be shown to have been breached; `H` needs an instrument GP does not have. Writing a count beside
them would imply a threshold that means nothing — the same defect as *"proportional to the number of
controls affected"*, struck from candidate F at this same sitting for naming no threshold.

**`C` is not in this table because it was ADOPTED** on the corrected count (three non-GP projects),
as a clause on rather than a new class. It entered the register after the ballots were filed,
on evidence a seat produced by re-reading the corpus the chair had mis-summarised.

## What the counters do NOT mean

`intra` and `cross` are evidence about a failure MODE. Neither is evidence about a project, and
neither is a score. A project with a high `intra` is a project that reported honestly; the harvests
that produced these numbers are the ones that looked hardest.

**A counter with no cited record id is not a counter.** If you cannot name the harvest that moved it,
the increment did not happen — put it back.

## The list worked — record that too 

The mechanism's first full cycle completed: three controls were removed with counters, the failure
modes were watched for in the field, **two recurred and returned; one did not qualify under the list's
own counting rule and its successor entered on fresh evidence instead.** The owner's design — *"this is
how we learn which ones actually earn their place"* — produced exactly that knowledge in one increment.

 then found the counting rule itself defective (GPF-006), which is the same cycle running
one level up: the instrument that grades controls got graded, by the field, and lost.

## The honest caveat

All three of these are *outward-facing* checks: they test the shipped thing against the real world
rather than the repo against itself, which is the direction this methodology is weakest in. Removing
them makes the remaining set more inward-looking, and that is a real cost, not a rounding error.
They were removed for being unprovable, not for being unimportant.
