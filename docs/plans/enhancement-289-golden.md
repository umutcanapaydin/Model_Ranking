# Enhancement #289 — a golden question set

**Goal.** For the first time, a test checks that a real question routes to the right surface and
yields sensible models (D-202 clause 2).

**Scope in.**
- A pinned snapshot of the hosted engine's `/v1/categories` and `/v1/boards`, a test fixture under
  `ios/EngineTests/` (never in the app target, REQ-APP-001).
- A golden file (golden-questions.json, beside the Engine tests): 30 to 50 questions in English and Turkish. Each has an
  expected surface and an expected top 3 derived from the snapshot's boards, or is marked `disputed`
  with a reason.
- An Engine test that routes each question through the wording tier, builds the answer plan from
  the snapshot, and checks the surface and the top 3 (as a set, since ties share a place). It prints
  a report of every miss.

**Scope out.** Tuning a reading rule to the golden set (D-191, D-196). The golden questions are kept
apart from the held-out sets in `scripts/router_probe/`. The on-device model tier, which needs iOS 26
with Apple Intelligence and does not run in `swift test`.

**Open decisions.** None left: D-202 clause 2 resolves them. The owner corrects the set in the morning.

**Phases.**
1. The snapshot and the golden file, with expectations derived by a script from the snapshot. The
   script is kept, so the owner can re-derive after a correction.
2. The golden test runs and fails where the app is wrong today; each miss is listed in the PR.
3. Each miss that one rule explains is fixed, red first. Any other miss is filed as an issue.
