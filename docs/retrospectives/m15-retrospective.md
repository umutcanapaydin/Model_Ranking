---
record_type: retrospective
id: m15-retrospective
status: draft
date: 2026-09-22
---
# M15 Retrospective — the numbers held; the lists and the counts around them did not

## The carried question, answered

> **M14 asked: the gap register will, for the first time, tell this project what people actually
> ask. What should the product do with a question it can see is common and cannot answer — find a
> board for it, say plainly that nobody measures it, or answer it from something other than a
> benchmark?**

**The register could not ask the question yet, so the answer came from the boards instead.** Its
first read (`docs/research/m15-gap-register-first-read.md`) found one entry: the owner's own test,
an image-editing question, declined as designed. No stranger has used the app, so the register
cannot say what is common. What M15 did instead was the first half of the question's first option,
done by measurement: all 22 boards of the licensed dataset were read on one footing, and three of
them (`vision`, `search`, `search_factuality`) had a population the engine could rank. For the
rest, the product says plainly that nobody measures it — the decline groups D-147 made explicit.
Nothing is answered from something other than a benchmark, and nothing in M15 argued it should be.

**What that leaves:** the register becomes an instrument after the first strangers use the app,
and not before. Until then, public collections of real prompts are the only way to learn what
people ask, which is M16-W4.

## What went well

- **Every shipped number survived an independent recomputation.** The W1 seat recomputed all eleven
  W-094 floors with its own queries; every one matched to 0.1. What it corrected was the sentence
  around them (which rule they follow), and the owner ruled the right one in (D-148).
- **The owner ruled every question put to them, on one day** — D-141 (after five bypasses), D-147,
  D-148, D-149, and the three closure questions (the W-113 margins, W-112, W-111). Two of those had
  been open since M13. A plan whose §0 asks one question per ruling, each with a recommendation, got
  rulings.
- **The router was measured before it was tuned.** When W3's hints broke seven probe routes, a
  22-question held-out set was written BEFORE the first change, so D-147's result (21/21 probe,
  18/22 held-out) measures the method, not the tuning.

## What went badly

- **The privacy invariant's gate was a list of spellings, for the fifth time.** W-090, M13 MINOR-4,
  W-099, W-110 and then the Stage 4.0 seat's MAJOR-1: 10 of 12 privacy mutants passed a gate that
  its own wave had described as a ban "on the INVARIANT". The same milestone put "What you type stays
  on this device" in front of the reader. The gate is now an import allowlist plus an API ban with a
  string-aware comment stripper -- and the W4 seat bypassed THAT eleven ways, three of them by
  fooling the stripper. The next version strips nothing, and its re-review still found 27 more
  (markdown links, Handoff, file export). All 54 now die, and the lesson is the count: six rounds
  of a word list is the evidence that the gate must check what the compiler resolves (W-122, M16).
- **A file was written from a stale copy and deleted eleven screen strings** (W-114). The app would
  not have built; the Python suite stayed green because it greps the caller, and `swift test` never
  compiles the view. Found only because a seat read the tree after a red run. The original wording
  is lost.
- **Two scripts disagreed about one number for a day, and the explanation offered was wrong**
  (W-113). 41 against 64 on `vision` was put down to "a day of price movement" on the smaller
  boards. It was one script counting board NAMES where the other counted models, and the same
  mistake had moved two shipped tie margins. Re-running both on one artifact took ten minutes.
- **A planned item disappeared between two waves** (W-116). D-144's carry-forward was planned for
  W3; W3's commit does not mention it and no record says it was dropped. The closure found it by
  reading the plan against `src/`.
- **The lead agent put a false claim to the owner, and the owner ruled on it.** Asked how the Swift
  test floor should work, the owner was told that deriving it from the test declarations would turn
  the check red when a test is deleted. It would not: both numbers drop together. The W4 seat found
  it; the question went back to the owner in correct words the same day, and the answer changed
  (a committed list of test names, D-150 as amended). A recommendation is a claim like any other
  and needs the same check before it reaches the person deciding.
- **Two of four wave closes were written late.** W1 and W3 were committed without a close record;
  both were written at W4, W3's with a code review that ran after its commit. The HIGH wave's
  security pass also landed at closure rather than before the commit.

## Playbook seeds

1. **An invariant gate is an allowlist of what may, not a list of what may not.** Five times a ban
   written as spellings or paths let the next spelling through. Name the imports and the one door
   that may reach the network, and refuse everything else by its absence.
2. **Re-read the file on disk before writing it.** A write from a copy that predates someone else's
   edit is a silent revert, and checksums after a sync prove the write, not the merge.
3. **When two measurements of one thing disagree, run both on the same input the same day.** The
   difference is then the method, and it takes minutes. An explanation that has not been run is a
   guess, and this one was wrong twice (the count and the margins).
4. **Check a mechanism before recommending it.** "This catches a deletion" is testable in a minute
   by deleting something; the owner ruled on the sentence, not on the test.
5. **Diff the plan against the tree at every wave close.** A planned item that no record mentions
   has been dropped, whatever anyone intended.

**Control bypass (`control-bypass`):** one, and it is K.7. W3, the milestone's HIGH wave, was
committed with no code review, no Tester pass and no close record (W-120); its security pass came at
closure. The retroactive seat returned BLOCKING: the test cited for board isolation did not reach
the three new surfaces, and a truncation floor had been loosened to let them in (W-117). The count
W-106 kept stopped at five when the owner accepted D-141. `check_records` C2b stopped the closure
itself when V3C-02 and K.8 reached a third acceptance, which is the control working: D-150 is the
review it asked for.

**What was accepted rather than solved:** the gap register cannot answer until readers exist; the
router's speed on a phone is unmeasured (D-147's cost); image pricing and REQ-IMG-002/003 stay open;
nothing deployed, eighth milestone.

**Carried to M16:** once the reader can press "update now", freshness becomes something the product
promises a person rather than a job it runs at night. What must be true before the app is allowed
to show "last refreshed" as a claim about the data — and what should it say when a refresh ran but
one source failed?
