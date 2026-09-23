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
knows works — one that grepped source for hardcoded credentials shipped for eight releases and
was never once proven to fire, because its only test asserted a non-zero exit that the unfilled
template produced anyway.

Then ask the other half, which is the one that gets skipped: **does it stay quiet when it
should?** A control that fires on correct input is not a strict control, it is a control someone
disables. Write both cases.

## 3 · Is its subject the tree you think it is?

Three defects in one release, all this shape: a gate whose docstring said `main` and whose code read
`HEAD`; one that looked for `cwd/.git` and so never ran in the repository it graded; one that
printed "base ref" while reading the ref the agent rewrites.

Name the tree, the ref and the file set in the output itself. If it cannot say what it graded, it
did not grade anything you can rely on.

## 4 · Derived, or enumerated?

If the check's scope is a hand-kept list sitting beside the thing it guards, that is itself the
finding. Walk the ORM, the route table, the tracked tree, the manifest. An enumeration that must
stay hand-kept is a **named entry with a written reason**, never an absence.

This is the most repeated defect in the projects this method was measured on: a forbidden-names
check that read its names from one hand-kept column was right about what the column held and
silent about everything it did not.

## 5 · Does it fail closed?

An empty derived set, an unreadable config, a tool that is not installed, a crash — every one of
these must be a FAILURE, never a vacuous pass. Know what your runner does with each exit code:

- **A Claude Code hook blocks ONLY on exit 2.** Exit 1 — including a crash — is a non-blocking
  error, and the tool call runs anyway. A guard that exits 1 has never blocked anything, and a test
  that grades `returncode != 0` will call it green. Test for exactly 2 to block, exactly 0 to allow.
- **A guard that cannot read its input allows everything.** `c=$(python3 … 2>/dev/null)` against a
  `python3` that is only a stub yields an empty string, no pattern matches, and every guard exits 0 —
  measured on Windows, where every guard in a project fell silent at once. "Could not read the call"
  blocks; "read it, and the field is empty" allows. Test the first with the interpreter broken.
- **The conformance runner** (`conformance/run-all.py`) reads exit 2 as NOT-EVALUABLE: printed
  loudly, and not a failure of the suite. Use it only when something else guards what this check
  cannot see — and say what that is. A "could not evaluate" that nothing else covers is a pass
  wearing a different word.

## Before you finish

- Register it where the suite can find it, and make sure the suite DERIVES its list rather than
  being told.
- Give it a caller. A gate whose only caller already knew its name is not wired.
- If you removed or relaxed a control, that is a change to the safety floor: say so, and say what
  now catches what it caught.
