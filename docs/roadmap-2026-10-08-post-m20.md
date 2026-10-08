---
record_type: register
id: roadmap-2026-10-08-post-m20
status: ratified
process_version: v6.6
date: 2026-10-08
---
# Roadmap snapshot — after M20 (2026-10-08)

A snapshot, never edited after it is written (seed I.1).

**Where the product is.**
- **The engine** runs on Fly.io (`https://model-ranking.fly.dev`) and on the owner's Mac. It serves
  every source on TestFlight (D-186). It names each surface's family of boards on `/v1/categories`
  (D-188 clause 1). On `wave/m20-w5` it limits one client to 120 requests a minute (#187); that is
  not deployed yet.
- **The app** is on TestFlight as build 1 (0.1.0) and on the owner's iPhone as a device build. On
  the M20 branches:
  - every question asked, and every surface the reader chooses, gets our own list. It is built from
    the surface's family of boards by mean percentile position, says which boards built it with
    their dates, and keeps the primary board's answer one tap away (D-188);
  - a language or a domain the question names adds its board: from the on-device model where it
    read the question, from the words otherwise;
  - while Apple Intelligence reads the question, the field glows, and a small line says who reads it
    (#208);
  - the build number is 3.
- **Measured** on a fresh held-out set (#195): the question reading on both tiers, before and after.
  About half of our list's top ten differs from the primary board's, and no set yet says which list
  is better.

**Open pull requests, stacked in order:** #213 (the M20 and M21 plans), #215 (W1), #217 (W2), #221
(W3), #224 (W4), #225 (W5), then the M20 closure.

**What the owner decides next.**
- D-188 (proposed): approve, amend or refuse it with the M20 plan (#213).
- Merge the stack, then deploy and upload build 3: `docs/release-testflight.md`, including the new
  check that Fly sets the client's address.
- The ledger's `commit-after-check-fast` control reached three events: fix it (the hooks, which load
  only when a session starts in the repository, #142), re-scope it, or refuse it (`docs/refusals.md`).
- Licences per source before external testers or the App Store (D-185, D-186).

**What is next (M21, planned in `docs/plans/m21-plan.md`, 47 issues in its milestone).**
- W1: the data a reader sees (#163 to #166, #124, #185, #198, #205, #214, #216), and the limit's
  shared-address case before external testers (#228).
- W2: reading what is not a search, and the wording tier's dead ends (#66, #194, #180, #186, #193,
  #199, #218, #222, and #226: the owner's judgement of answers, D-188's revisit).
- W3: the phone's promises held further (#85, #132, #168 to #175, #188, #219, #220, #223).
- W4: the controls (#122, #178, #179, #181 to #183, #108, #189, #200 to #203, #227).
