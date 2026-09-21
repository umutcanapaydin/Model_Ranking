---
record_type: retrospective
id: m14-retrospective
status: draft
date: 2026-09-21
---
# M14 Retrospective — the product started answering, and the proofs started drifting from the claims

## The carried question, answered

> **M13 asked: what would it take for the next milestone's evidence to come from the product as a
> reader meets it — refreshed data, a real keyboard, a real device — rather than from the
> instruments around it?**

**It took the owner's machine, and that is the whole answer.** Three things in M14 could only be
known there, and each of them overturned something the agent lane believed:

- **The refresh.** Nine probes in the agent lane cleared the Desktop paths, the interpreter, the
  plist and the registration by measurement. All of it was wrong, because the probes used
  Apple-signed programs and macOS decides privacy protection per program. One run on his machine
  with the real wrapper produced the first honest error message of the hunt (W-096).
- **Apple Intelligence.** Whether tier 1 emits the decline sentinel was "probable, not measured" for
  three milestones. He typed one question into the app and it was measured.
- **`swift test`.** 241 tests, of which this lane has never compiled one. Every Swift claim in every
  M14 record rests on his run.

**And the inverse is now the standing risk:** what only his machine can run, only he can run, so any
defect in the Swift half lives until he runs the runner. The closure seat's B-1 is exactly that —
`ContentView.swift` is compiled by nothing in this project's test suite, so the one file holding the
reader's typed words is the file with the least proof around it.

## What went well

- **A measurement killed the milestone's headline feature, in W1, cheaply.** The image-editing
  surface was the plan's centrepiece. Its ranked population was zero and the wave stopped instead of
  arguing. Two surfaces the data supported were built instead, and the milestone came out ahead.
- **The independent seats kept being right.** W1's seat refuted three of the author's measurements.
  W2's seat found a mutant that merged two boards under 905 green tests. W3/W4's seat found the
  anchor was the recalibrated floor. The closure seat found a privacy test that could not fail and a
  refresh job that could not be installed. Four seats, four findings nobody inside had.
- **The owner's rulings arrived as data, not as arguments.** D-143 ("one score, and the reader
  should not have to know the unit") was a product decision he made in one message, and the whole of
  W4 follows from it. The cost was written down beside it rather than argued away.

## What went badly

- **The records drifted from the code, in the direction that flatters.** A wave row said a criterion
  was tested through the live entry point; the test read four dataclass fields. A ledger row named an
  installer script that did not exist. The prd still stated a display rule the product had stopped
  obeying. None of these was a lie anybody told: each was written while the thing was true or about
  to be, and nothing re-reads a record after its subject moves.
- **Four carried requirements had no home for a whole milestone** (W-105), including the detail
  screen that was the stated mitigation for taking the unit off the card. The plan's §1 table is
  supposed to be frozen and diffed at closure; two IDs simply evaporated.
- **The security pass was waived twice more** (W-106), in the milestone that inherited a ledger row
  about waiving it three times, and neither waiver reached the ledger that counts. D-141 has been
  `proposed` since M13.
- **A sync tool reported success on files that never arrived**, and the owner's commit script did
  exactly what it should — it refused to commit a wave whose decision record still said "proposed".
  The failure was silent; the gate was not. Files are now verified by checksum after every sync.

## Playbook seeds

1. **A structural test is scoped to the file it reads, not to the invariant it names.** REQ-GAP-001
   says "nothing leaves the device" and the test searched one section of one file. Scope such a test
   to every file the data can reach, and name the egress spellings rather than the sections.
2. **When a record names a remedy, the remedy is part of the change.** W-096 named a script that
   lived only in the owner's scratch folder; the repository's install path was left broken by the
   fix for it. A remedy named in a ledger row is a deliverable with a path.
3. **A pin that passes by coincidence is not a pin.** Every `score_anchor` equals its `min_quality`
   today, so serving the floor passed every test. Move one and not the other, and the decision gets
   a test instead of an agreement.
4. **A milestone's criteria table needs a diff at closure, not a reading.** Two REQ-IDs left M14
   with no disposition because nobody compared §1 to the prd line by line. The closure seat did it
   with `grep`.

**Control bypass (`control-bypass`):** fifth and sixth occurrence — the HIGH-tier security pass was
waived on both M14 code waves, locally, while D-141 sits unratified (W-106). This is now the
longest-running open control problem in the project and it is in §0 of the closure report.

**What was accepted rather than solved:** Elo surfaces read 57–79 against percentage surfaces'
73–100, knowingly (D-146); the detail screen does not exist (W-105); two gates reproduce only on the
owner's machine (W-108); no Tester seat was convened in any wave; nothing deployed, seventh
milestone.

**Carried to M15:** the gap register will, for the first time, tell this project what people
actually ask instead of what we think they ask. What should the product do with a question it can
see is common and cannot answer — find a board for it, say plainly that nobody measures it, or
answer it from something other than a benchmark?
