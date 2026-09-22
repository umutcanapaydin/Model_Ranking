---
name: writing-a-control
description: Use when writing or changing anything that CHECKS something — a gate, a rule, a lint, a CI step, an assertion, a validator, a guard, a hook, a self-test, a conformance test. Also when writing a rule in prose that bans a shape, or when a review finds a defect and you are about to write the thing that stops it recurring. Covers: does it fail when it should, can it fail at all, does it read the tree you think, and does the fact live in two places.
---

Five questions. Each one is a defect this project has measured, most of them more than once.
Answer them out loud in the change itself, not in your head.

## 1 · Does a gate ship with the rule?

A rule without a mechanical gate is a rumour — including one you wrote this morning. If the
change writes a rule that bans a specific literal or shape, the check goes in the SAME change.
Not the next one.

Measured in five projects, including two that never installed this pipeline.

## 2 · Have you watched it fail?

Plant the violation and confirm it goes red. A gate nobody has watched fail is a gate nobody
knows works — and one shipped here for eight cuts, greping source for hardcoded credentials, was
never once proven to fire because its falsification asserted only a non-zero exit that the
unfilled package produced anyway.

Then ask the other half, which is the one that gets skipped: **does it stay quiet when it
should?** A control that fires on correct input is not a strict control, it is a control someone
disables. Write both cases.

## 3 · Is its subject the tree you think it is?

Three defects in one cut, all this shape: a gate whose docstring said `main` and whose code read
`HEAD`; one that looked for `cwd/.git` and so never ran in the repository it graded; one that
printed "base ref" while reading the ref the agent rewrites.

Name the tree, the ref and the file set in the output itself. If it cannot say what it graded, it
did not grade anything you can rely on.

## 4 · Derived, or enumerated?

If the check's scope is a hand-kept list sitting beside the thing it guards, that is itself the
finding. Walk the ORM, the route table, the tracked tree, the manifest. An enumeration that must
stay hand-kept is a **named entry with a written reason**, never an absence.

This has bitten here at least six times, most recently in the register the anonymisation gate
derives its forbidden names from: the column was right about what it held and silent about what
it did not.

## 5 · Does it fail closed?

An empty derived set, an unreadable config, a tool that is not installed, a crash — every one of
these must be a FAILURE, never a vacuous pass. `exit 2` is "I could not evaluate", and a runner
that counts it as success is the founding defect of this lineage wearing its final costume.

## Before you finish

- Register it where the suite can find it, and make sure the suite DERIVES its list rather than
 being told.
- Give it a caller. A gate whose only caller already knew its name is not wired.
- If you removed or relaxed a control, that is a change to the safety floor: say so, and say what
 now catches what it caught.
