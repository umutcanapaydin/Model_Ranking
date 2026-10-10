---
record_type: register
id: roadmap-2026-10-10-post-m21
status: ratified
process_version: v6.6
date: 2026-10-10
---
# Roadmap snapshot — after M21 (2026-10-10)

A snapshot, never edited after it is written (seed I.1).

**Where the product is.**
- **Live:** the engine on Fly.io (`https://model-ranking.fly.dev`) and the app on TestFlight (0.1.0),
  as the first release and its hotfix (#207) left them; `main` carries build number 2. Neither M20
  nor M21 is merged or deployed.
- **v2 (0.2.0, build 4)** waits on one merge. It ships M20 and M21 together:
  - our own list for every question, combined from the surface's family of boards (D-188), with a
    refinement in place of its vote's board;
  - one model per release its maker names (D-189), and `web-dev` on LMArena's own WebDev board (D-190);
  - model comparisons answered from `everyday` (D-191);
  - the engine's refusals in the reader's language, a boards screen laid out lazily, and Apple
    Intelligence's state read again when the app returns to the front;
  - a rate limit in which standings never block questions, and a deploy that refuses data another
    release built.
- **The controls** (D-192): the close checks read the wave's commit range, the decision log's pointer
  pairs and the ledger. A pre-commit hook runs `make check-fast`, or `make check-records` for a
  docs-only commit, once the owner runs `make hooks` (the owner's ruling, 2026-10-10). The Bash guard
  has a second reading, pinned by its sha256.
- **Measured:** no new held-out measurement at M21. W2's three reading rules came out, so every
  held-out row reads as it did at `972b55e`.

**Open pull requests.** One combined pull request from `closure/m21` into `main` carries #213, #215,
#217, #221, #224, #225, #229, #236, #240, #250 and #251. Merging it with a merge commit marks them
merged.

**What the owner decides next.**
- Merge the combined pull request. It carries these OWNER APPROVAL commits: the Bash guard's second
  reading (`c3b8b9a`, `64b862a`, `36e74fa`, `bd55823`), the pre-commit hook (`d466923`), and the guard's
  timer, sha256 pin and write refusals (`3143da4`, `419d5dc`).
- Then the v2 steps in `docs/release-testflight.md`: `make hooks`, `/hooks` once, `make check`, one
  published night, the deploy, the two header checks, build 4.
- #122's CI patches are on the issue; `.github/workflows/` is the owner's to change.
- #220's on-device glow measurement and #226's judgement sheet need the owner's phone and judgement.
- Licences per source before external testers or the App Store (D-185, D-186), unchanged.

**What is open (no next milestone planned yet).**
- **The reading:** #66 (too few non-searches to measure), #194, #218, #222 (each taken out at its
  third verdict), #237 to #239.
- **The phone's promises:** the compiled gate holds in full only on a Mac with Xcode (#243), and the
  gaps #241, #242, #244 to #247.
- **The data:** #230, #232 to #235.
- **The controls:** #108 (its measurement traps a process), #122, #252 (a review pointer that never
  moves).
- Delivered issues close when the combined pull request merges.
