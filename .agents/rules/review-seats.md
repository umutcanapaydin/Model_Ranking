# Review seats (K.7) and shared contracts (K.8) — the reasons

The rules are in `AGENTS.md` §4. This file keeps their full wording and history, moved out of
`AGENTS.md` at the M16 closure to hold D-003's 150-line cap.

- **K.7** — fresh eyes preserved: the reviewer/tester never authored the wave's code. **In the
  LOCAL single-agent lane this means a SEPARATE SESSION** (owner ruling, 2026-08-22): the reviewing
  seat receives the diff and reads its policy from the PROTECTED BASE REF (V4C-06), never from the
  authoring session's context. **The review is a FILE.** A review that exists only as a report in a
  conversation is not evidence, and `scripts/wave_check.py::review_seat_problems` enforces both
  halves — a wave-close review row that passes must cite a `docs/reviews/*.md` record, and that
  record must declare `seat: independent` in its frontmatter. `seat: author` forces the row to be
  WAIVED, which forces it to name a ledger row, which puts the bypass in front of the owner
  (V4C-13). **The gate does not prove independence and does not claim to** — it makes a self-review
  unable to close a wave green. K.7 was bypassed four times in the open before this existed, and
  every one of them was recorded and closed green anyway (W-055, W-056).
- **K.8** — Shared contracts grep-verified in plan (paste `grep -n` output). **D-150 clause 2
  (2026-09-22):** a plan that builds a SCREEN also lists, fact by fact, which published field
  each fact comes from. Three K.8 acceptances in this project were the same thing — a plan line
  written before anyone checked what the API carries (W-009, W-020, W-112) — and the check
  belongs in the plan the owner signs, not in the wave that discovers it.
