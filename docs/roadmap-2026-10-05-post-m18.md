---
record_type: register
id: roadmap-2026-10-05-post-m18
status: ratified
process_version: v6.6
date: 2026-10-05
---
# Roadmap snapshot — after M18 (2026-10-05)

A snapshot, never edited after it is written (seed I.1).

**Where the product is.** One application on the owner's Mac, and an iOS app on the owner's iPhone:
- **The engine** runs as a launchd service from a deployed release. By opt-in it serves the home
  network and checks every Host (D-171). It refreshes nightly within three limits: a 20-minute fetch
  budget, its own 27-minute end, and the engine's kill at 30 (D-154 as amended). Every install reads
  a hash-checked lock (D-177).
- **The app** reads the question on the device. A question that is not a search for a model gets a
  note or a one-tap question back (D-169 as amended; #134, pending the owner's answer). The screen
  speaks Turkish throughout, and a committed UI target drives it (D-175).
- **The security invariants** are one list, each row with the tests that fail without it
  (`docs/security-invariants.md`).

Nothing is deployed beyond the owner's devices. Three M18 pull requests are open, stacked in order:
#134 (W3), #135 (W6), #136 (W7).

**What the owner decides next.**
- Whether to ship W3's reading as it is: #66's catch bar and #113's bars are missed (#134).
- The data licences, six questions, before any public release (#88, #135).

**What is next, not yet planned (M19).**
- The compiler-level gates W6's valve moved: #110, #107, #60 and #85, the last a privacy sink.
- What the owner's answers on #134 and #88 call for.
- A stranger's first use, by the protocol in `docs/research/stranger-first-use-protocol.md` (#91).
  Its questions become the next held-out set.
- The open backlog: #112's 68 names, #122's child processes, and #125 to #133.
- The first deploy beyond the owner's devices, and the Stage 5 release review, if the owner calls a
  release.
