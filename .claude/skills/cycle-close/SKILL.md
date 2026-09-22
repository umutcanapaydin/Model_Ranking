---
name: cycle-close
description: Use at the end of a milestone, a quarter, a sprint or a phase of work — when asked to wrap up, close out, retrospect, hand over, or take stock. Covers what must be written down while it is still known, and the periodic question nobody asks on their own: which of our own controls and skills have stopped earning their place.
---

Two jobs. Neither survives being done later.

## 1 · Capture, while the context still exists

- What was learned goes into the experience record **now**. Two days of high-value work in one
 project produced zero entries, because the writing was left for afterwards and afterwards is a
 reconstruction. A diary loses its value the moment it becomes a memoir.
- Every non-trivial choice made under uncertainty is a recorded decision, with what was decided,
 why, and when to revisit. Append; never edit one in place.
- Anything knowingly skipped, bypassed or deferred is a row with an owner, not a silence.

## 2 · The diet — and this is the part that gets skipped

Count the controls, the gates, the hooks and the skills. Then, for each one, ask the only
question that matters: **has it fired?**

- A skill that has not been invoked in 90 days is retired. Not archived, not "kept just in case"
 — retired, with its evidence, so it can come back if the failure recurs.
- A gate that has never been shown to refuse anything is not a gate.
- A rule proposed twice and never built is either built this cycle or withdrawn.

**Include the controls THIS project wrote itself**, not only the ones it inherited. List them
(`ls scripts/`, walk the CI steps) and grade each with the same verdicts. One project ran this
pipeline for five weeks, grew **74 local controls**, retired none, and an outside engineer then
deleted 88% of them in a single commit. The instrument that should have caught it already blocked
closure — it had simply never been run against the population it was for.

Retirement trigger, borrowed rather than invented: **a project-grown control that is NEVER-FIRED
at two consecutive closes is retired at the second**, or this record names why it stays.

Removing a control is relaxing the safety floor to zero. Say what now catches what it caught,
or say plainly that nothing does.

## Why this is one skill and not three

It was three — a retrospective, a quarterly handover and a harness diet. They ran at the same
moment, on the same evidence, and the diet is the only one that ever removed anything. Keeping
them apart meant two of the three fired and the useful one did not.
