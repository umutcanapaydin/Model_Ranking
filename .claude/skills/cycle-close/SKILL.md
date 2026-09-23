---
name: cycle-close
description: Use once, when the work is done — at the end of the project or of a release (Stage 5.3), and only if the owner wants it. A short retrospective of what went right, where we got stuck, and which of our own controls and skills earned their place. Never during the work: no per-milestone retrospective, no handover.
---
Optional, and once (owner ruling, from experience: retrospectives written during the work tire the
people doing it). It writes one file, `docs/retrospective.md`, opening with its record header
(`record_type: retrospective`, `id: retrospective`, `status: draft`, `process_version:` set to
the version `.gp/installed` records, `date:`) so the record validator governs it. Everything that must be written
while it is still known — decisions, the process log, the EXPERIENCE entry — is Stage 4.2 Capture
at every milestone close, not this skill.

## 1 · What went right, and where we got stuck

A few lines each, with a referent (a PR, an issue, a decision). What would we do the same way; what
cost us time, and whether a control could have caught it earlier.

## 2 · The diet — and this is the part that gets skipped

Count the controls, the gates, the hooks and the skills. Then, for each one, ask the only
question that matters: **has it fired?**

- A skill that has not been invoked in 90 days is retired. Not archived, not "kept just in case"
  — retired, with its evidence, so it can come back if the failure recurs.
- A gate that has never been shown to refuse anything is not a gate.
- A rule proposed twice and never built is either built before the next release or withdrawn.

**Include the controls THIS project wrote itself**, not only the ones it inherited. List them
(`ls scripts/`, walk the CI steps) and grade each: **fired and caught something**, **fired, caught
nothing**, **never fired**, or **no opportunity yet**. One project ran this
pipeline for five weeks, grew **74 local controls**, retired none, and an outside engineer then
deleted 88% of them in a single commit. The instrument that should have caught it already blocked
closure — it had simply never been run against the population it was for.

Retirement rule: **a project-grown control that never fired by the end of the work is retired**, or
this record names why it stays.

Removing a control is relaxing the safety floor to zero. Say what now catches what it caught,
or say plainly that nothing does.
