---
record_type: retrospective
id: m10-retrospective
status: draft
date: 2026-08-22
---
# M10 Retrospective — the milestone that got its own carried question answered against it

## The carried question, answered

> **M9 asked: what does this system do when it is wrong and nobody is looking? M9 added a status
> file and an escalation counter. Is that the answer, or is it the smallest thing that let the
> milestone close?**

**It was the smallest thing that let the milestone close, and M10 has the receipt — twice, from
two independent directions.**

**Receipt one: a counter fired and nothing consumed it.** `C2b` exists for precisely one purpose —
the third bypass of a control sends the CONTROL for review instead of the seat. It fired at M8 over
K.7, named M9 as when the review would happen, and M9 closed without it. M10 then bypassed K.7 a
fourth time. The escalation counter worked perfectly: it counted, it fired, it wrote itself down,
and **being written down turned out not to be the same as being read.** A status file and a counter
answer "did anything notice?"; the question was "did anything ACT?", and nothing did (W-055).

**Receipt two: a defect survived a milestone with every gate green, and reading did not find it.**
`f"file:{path}?mode=ro"` returns a WRITABLE connection. It shipped in M9's refresh, on the path
that opens the LIVE artifact, under a comment defending the choice. It survived M9's Stage 4.0
security review — a review that found three genuine blocking findings, so it was not a lazy pass.
It survived every gate at M10-W1, W2 and W3. It was found by typing the expression into a Python
process and watching it write into a file it had just promised not to touch.

So the honest answer to M9's question, in a form M11 can use:

> **What this system does when it is wrong and nobody is looking is: keep going, greenly, with the
> evidence of the fault already written down somewhere nobody re-reads.** The gates catch the class
> of defect they were written for. The residue is caught by EXECUTION and by nothing else — not by
> review, not by records, and not by a counter that has no consumer.

## What this milestone taught

### 1. A fix that lives in one module is not a fix

The correct read-only construction, and a docstring explaining exactly what breaks without it,
existed in `adapter/main.py` from M6. Three milestones later `workflows/refresh.py` wrote the
broken form back — deliberately, with a comment arguing that the copy was *"not a second definition
of any project behaviour."*

The comment's premise was right: the refresh must not import the adapter (D-116, REQ-REF-007). Its
conclusion did not follow. **A boundary rule and a single-definition rule will eventually collide,
and the collision is always resolved by moving the definition, never by duplicating it.** The third
option — put it where both may reach it — was available the whole time and was never considered,
because the choice had been framed as two options.

This generalises past this project: *"avoiding a dependency"* is a reasonable-sounding justification
that quietly authorises a private copy of security-relevant code, and it is at its most persuasive
in exactly the modules where the boundary is real.

### 2. A bound placed where nothing can reach it

The first aggregate row cap was 5,000. `_MAX_PAGES` is 50 and `_PAGE` is 100 — the page walk cannot
produce 5,000 rows, so the new guard was decorative from the moment it was written. Nothing found
this by reading it, including the person who wrote it minutes earlier. It was found by trying to
write a test that FIRES it.

This is one level past the project's existing "a control cited but not run": **a control that runs
on every call and cannot trigger.** Coverage sees it as covered. Review sees a sensible constant.
The only thing that sees it is an attempt to reach it.

The correction had a second-order cost worth recording: once the row bound was reachable, the PAGE
bound became unreachable for an all-`overall` payload, because full pages trip 2,000 rows at page
21 and a short page ends the walk. The test now raises the row bound to reach the page cap and says
in place that this is the only honest way to exercise a backstop — rather than a fixture quietly
shaped to make a dead guard look live, which is the *fixture blindness* defect this project has now
recorded seven times.

### 3. A name is not a control until something is required to call it

REQ-EVI-002 asked for the ranked population to have a name. `ranked_population()` was added at M9.
At M10-W3, `scripts/arena_calibration.py` — the script whose entire purpose is to make a
calibration record recomputable — was still computing its cut table and value-window sizing from
the raw board, which is the exact defect W-037 records happening three times.

The accessor existed. The requirement was satisfied on its face. **Nothing was required to call it,
so nothing did.** The remedy was not a better name; it was a gate that fails any script sizing a
threshold without importing it (V4C-49: ship the gate with the rule).

### 4. What the router taught, which is not about routers

Two implementations were built and measured and rejected before the third worked: `NLEmbedding`
scored 1 of 9, raw `NLContextualEmbedding` cosine scored 3 of 8 with everything collapsing onto one
category. Centring fixed the collapse. Sharpening the HINTS — with no code change at all — took it
from 5 of 8 to 7 of 8.

The lesson is the last step. **The final gain came from the data, not the algorithm**, and it would
have been invisible without a probe that could report a score. Two implementations were discarded
on evidence rather than argued about, which is only possible because a number existed.

## What went well, in the specific rather than the general

- The **measurement before the ruling**: ordinary upstream movement (0% new names, 0.0% median
  price move) was measured BEFORE D-132's thresholds were chosen, so the numbers describe the
  system rather than a guess about it.
- The **arena diagnosis**: it was never down. Only its `filter` endpoint fails, and it fails with
  no `where` clause at all. Nine surfaces answer because someone tried a different endpoint instead
  of accepting a standing warning.
- The **refusal to loosen a failing test** at W3. The obvious move was to widen the fixture until
  it passed; the honest one was to work out that two bounds now overlap and say so.

## What did not

- **K.7, four times.** See W-055. The lead agent reviewed its own code and found a BLOCKING defect,
  which is an argument for self-review being better than nothing and not an argument for it being
  the control.
- **Nothing was deployed, for the third milestone.** D-123, W-030, W-031. Every one of the three had
  a good local reason.
- **The iOS app has still never been opened by a human.** The router's score comes from a probe.

## The question carried to M11

> M10 built a feature whose best tier runs on hardware nobody has tested it on, behind a screen
> nobody has opened, in a product that has not deployed for three milestones — and closed with
> every gate green.
>
> The gates are not lying. They measure what they measure, and this milestone's real defects were
> found by *execution*: running the expression, running the probe, trying to reach the bound.
>
> So: **what is the smallest amount of RUNNING that this project could add to its close, and what
> would it have to run?** Not more tests — tests are execution the gates already have. The two
> defects that mattered here were found by running something the gates do not run: a suspect
> expression in isolation, and the product in front of a person. M11 should decide which of those
> becomes part of closing, and admit the cost, rather than adding a tenth gate to `make check`.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-22
