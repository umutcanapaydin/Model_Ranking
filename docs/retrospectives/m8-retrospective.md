---
record_type: retrospective
id: m8-retrospective
status: ratified
date: 2026-08-19
---
# M8 Retrospective — the milestone where the product got a reader and stopped being about coding

## The carried question, answered

> **M7 asked: `/v1` was frozen by D-115 with no consumer in existence. Does "frozen" mean frozen
> before or after the first real reader?**

**Answered by D-124 before W1: `/v1` may move ONCE during M8, in response to what the client
actually needs, and re-freezes at close.**

**The window was SPENT, by D-125, which added the `ranking` array so the client could show the full
list beside the three picks.** The ruling was made in the abstract precisely so it could not be bent
around a specific inconvenient field, and it worked as designed: one revision, written as an ADR,
with the frozen allowlist requiring a human edit on both sides before `ranking` could be published.

**An earlier version of this retrospective said the opposite** — that the move was never spent and
that a payload designed by people imagining a consumer proved sufficient for a real one. That was
false, and worse than false: it was a CONCLUSION drawn from a fact nobody checked, in the document
whose job is to say what was learned. It survived into a closure report, two wave records and a
commit message before three independent reviewers read the range. **The lesson is not about `/v1`.
It is that a retrospective is the easiest place in this process to launder an unverified premise
into a finding**, because nothing downstream re-derives it.

## What this milestone actually taught

### 1. A contract can be complete and the product still incomplete, and no test on either side can see it

`ranking_effort` is served by the engine, decoded by the client, and was mentioned by no view.
`agentic-coding` ranks at a named comparable level, so a score displayed without it invites a
comparison against a score measured somewhere else — which is the whole reason the field exists.

Every server test passed. Every client structure was correct. **The defect lived in the space
between two correct things**, which is exactly where the reviews of both could not look. It was
found by a test that derives the disclosure set from the client's own model and asserts each is
referenced — that is, by refusing to let a hand-written list of five fields be the definition.

This is the same lesson as M6's four denylists and M7's `serving_snapshot`, arriving in a new form:
not "a control that does not run", but **a control whose scope is narrower than the rule it cites.**

### 2. Measuring the wrong population is not a mistake you make once

Three calibrations, three different wrong sets: CSV rows, then parsed board rows, then the full board
instead of the reconciled-and-priced subset the engine actually ranks. Each was caught by measuring,
none by reading, and each produced materially different thresholds — `expert` and `mathematics` were
admitting two thirds of everything above the floor as "within reach of the leader".

The reason it recurs is that **the ranked population has no name in the codebase.** There is no
function to call and no term to look up, so the question gets answered from whatever data is nearest
to hand. W-037 carries the remedy: a named helper the calibration work is required to call.

### 3. The honest answer was sometimes the wide one

`expert` admits 25 candidates and `mathematics` 28, against `coding`'s 7, and they were left that
way. On GPQA the twelve highest-scoring priced models span 1.8 points against a 2.52 standard error;
on AIME three models tie at exactly 100.0. Narrowing the window below `close_call` would have made
the product disclose "level with the leader" about a model and in the same breath refuse to consider
it — **ranking noise as though it were quality, which is the one thing this engine exists not to
do.** The tidier number would have been the dishonest one.

### 4. A seam is only a seam if it reaches the caller

Third instance of this project's most-repeated defect, in a half nobody had checked. `_ingest_boards`
took a `boards` parameter and read it at call time — correctly, the lesson learned — while `build()`
exposed no way to pass one. Eight tests believed they controlled the source set and ran the real
board list against a directory that did not exist.

The two previous instances were about WHEN the default was bound. This one was about whether the
parameter was reachable at all. The lesson generalises: *the injection point is not the parameter, it
is the path from the caller to it.*

### 5. Restart is not rebuild, and the build stamp is the only witness

`app.sh restart` restarted the app and not the engine while `up` advertised it as the thing to run
after a code change. A running process keeps the replaced file's inode, so `/health` answered 200
throughout. Nine categories in the artifact, three on the wire, every check green. **The only
evidence was the build stamp**, which exists because L.7 said it should.

## What went badly, plainly

- **No fresh-eyes review ran on any of the three waves.** Each was a deliberate owner ruling under
  D-122, each was recorded as a `control-bypass` under V4C-13, and the third fires `C2b`: the
  CONTROL now goes for review, not the seat. M6-W1 measured what this costs; M8 accepted that cost
  three times without measuring it again.
- **Four of this milestone's mutants were killed only after the test was corrected**, and one only
  after the mutant was re-aimed at the right lines. Reporting 23/23 without that sentence would have
  been the kind of clean number this project has learned to distrust.
- **REQ-APP IDs reached the PRD at W2, not W1.** The F-1 drift the M4 gate raised, repeated by the
  agent that cites it.
- **A shell heredoc ate backticked words out of a PRD row for the third time in this project.** It
  was caught by reading the file back. The fix is procedural and has now been adopted: never embed
  markdown containing backticks in a `python3 -c "..."` string.

## The question carried to M9

> **The engine has been ready to deploy since M7 and has now not deployed twice, each time for a
> good reason. At what point does "deploy-ready and not deployed" stop being a schedule fact and
> become an architectural claim we have never tested?**
>
> W-030 and W-031 have been UNVERIFIED for three milestones. Everything we believe about the
> platform surface is inference from a local container. The question is not "when do we deploy" —
> that is the owner's and it costs money. It is: **what are we entitled to say is true about a
> system whose deployment has never happened, and where in the records are we currently saying more
> than that?**
