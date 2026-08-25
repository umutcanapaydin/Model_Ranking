---
record_type: retrospective
id: m12-retrospective
status: draft
date: 2026-08-25
---
# M12 Retrospective — the milestone that stopped speaking in the language of the measurement

## The carried question, answered

> **M11 asked: what would this project have to measure to catch the next comprehensibility defect
> before a user does? Not a gate that checks wording — something that makes "would a stranger
> understand this" a question with an answer.**

**M12 found two answers, and only one of them is a measurement.**

The first is the one the question was fishing for and it is weaker than it sounds. Some of it CAN
be gated: `tests/unit/test_category_titles.py` asserts that no two surfaces begin with the same
word and that no title uses a term from inside this field. That is a real gate, it caught a real
defect on its first run — and it caught the lead agent, not a stranger's confusion. What it tests
is a proxy: *does this text contain something we already know is jargon*. It cannot ask whether a
sentence lands.

The second answer is the honest one and it is not a gate at all: **the council seat.** The
comprehensibility inventory that drove this entire milestone — 28 rows, of which the CFO had found
five — came from a seat that was told to read the product as a stranger and given no other job.
Nothing mechanical produced it. What made it repeatable was not a check; it was a CHAIR, and the
chair had to be created because every existing seat was accountable for correctness.

So the answer M12 carries forward is: **you cannot gate comprehension, but you can staff it.** A
jargon list is a gate that catches the words you already regret. A seat with no other job catches
the ones you do not.

## What this milestone taught

### 1. Two parallel computations that agree today are two sources of truth

D-136's entire claim is that the prose is DERIVED from the fact. The first implementation computed
both from the same inputs in two places — the textbook definition of consistent-by-coincidence —
and it did not even manage the coincidence: `3x cheaper` shipped beside a fact carrying `3.1`. Then
`84 points` beside a floor of `84.4`, then `6` beside `6.0`.

All three were caught by one test, on its first run, before any of it reached a screen. **The test
was written to hold a property the design claimed rather than to check the output**, and that is
the difference between it finding three defects and finding none.

### 2. Rounding the claim is not rounding the display

The obvious fix for `84` beside `84.4` was to round the fact. It is wrong: the bar really is 84.4,
and printing `84` states a bar the engine does not apply. **A number a product rounds is a claim it
makes**, and the cheap repair would have made the fact agree with a sentence that was lying
slightly.

### 3. A test that pins WHERE logic lives is a tax on improvement

Three times in two waves a green test went red on a change that kept every word of its intent: a
literal phrase (`"carries no meaning"`), a 600-character window after a specific `case`, and a grep
for a comparison that had moved into a tested function. Each cost a wave a red gate.

The rule that comes out of it: **pin the claim and the audience, never the offset.** A test that
fails when text moves teaches people to leave text where it is — which is precisely how a
user-facing string ends up explaining App Transport Security to a CFO.

### 4. A rule about English blocked the records that documented non-English defects

`L1` fired on a security finding that could not explain itself without naming the letter that
causes it, and on a ledger row quoting the sentence it was reporting. **Fourth occurrence.** Each
time the workaround was to paraphrase, which makes the record worse — a reader has to reconstruct
the defect from a description of it.

Fixed at the fourth by narrowing the rule to PROSE, the same repair `bootstrap-check.sh` needed for
the same reason. And the proof of the narrowing was itself nearly a defect: the first attempt
tested a file already in `.language-allow`, so it would have "passed" against a rule that never
read it. Caught only by asking why the answer was zero.

## What went well

- **The council's findings drove a whole milestone and one of them was wrong.** P-002 and P-003
  were reported as phantoms; they are documented reserved mirrors, and every "citation" was a
  substring inside `REQ-APP-002`. Caught by re-measuring before acting. A council whose findings
  are adopted unverified is worth less than no council.
- **Every wave screenshotted the running app.** Three defects came out of that and nowhere else:
  an unformatted `1500`, English units inside Turkish sentences, and a stale engine serving a
  payload two commits old.
- **The owner's ruling outranked the council's recommendation**, and a test enforced it: the
  `Agentic coding` rename went in against his explicit answer and the naming gate rejected it.

## What did not

- **A fifth commit on a red gate**, and the fourth with the identical cause: run `make check`, edit
  a RECORD, commit without re-running. Every one has been a record edit, because code edits feel
  like they need re-testing and record edits do not.
- **The notices are not localised.** A Turkish reader gets Turkish sentences and English
  disclosures. D-136 scopes it out in its own text, which is the honest form of an unfinished job,
  but it is unfinished.
- **The Turkish flag has never been tapped by a human.** Proven by tests and by forcing the stored
  setting; synthetic taps do not land on that control.
- **Nothing deployed, fifth milestone.**

## The question carried to M13

> This milestone was planned entirely from what four council seats and one CFO said. Every wave
> discharged findings that came from outside the people doing the work, and the result is the
> largest single improvement in this product's usability across twelve milestones.
>
> That is a good outcome and an uncomfortable one. **The work the team chose for itself, across
> eleven milestones, was correctness — and correctness was never the thing standing between this
> product and a user.**
>
> So: **what else is the team not choosing?** The council was convened once, by the owner, on a
> hunch. It found a defect class nobody inside had named. M13 should decide whether an outside seat
> is a thing this project HAS — scheduled, budgeted, with a standing question — or a thing it
> reaches for when somebody remembers.

---

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25
