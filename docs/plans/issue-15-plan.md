---
record_type: plan
id: issue-15-plan
status: draft
process_version: v6.6
date: 2026-09-24
---
# #15 — the out-of-100 anchor is the surface's derived floor

**Working plan for the `enhancement/issue-15-anchor-follows-floor` pull request**, deleted before
merge. Risk: **MED** (a served `/v1` value changes meaning; no field is added or removed).

## Goal

Owner ruling, 2026-09-23 (translated from Turkish): "move the reference with the floor". On every
Elo surface, `/v1/categories`' `score_anchor` is the surface's `min_quality`, the floor D-159
derives from the served board, so the app's sentence "50 is at the bar" is true again.

## Measured before (owner's artifact, 2026-09-24)

| surface | pinned | floor | leader /100 before -> after |
|---|---|---|---|
| assistant | 1400.0 | 1406.7 | 65.0 -> 64.1 |
| web-dev | 1478.9 | 1478.9 | 79.3 -> 79.3 |
| document | 1467.5 | 1470.7 | 57.0 -> 56.5 |
| factuality | 1450.6 | 1451.5 | 57.2 -> 57.0 |
| vision | 1248.2 | 1253.3 | 61.0 -> 60.3 |
| search | 1206.9 | 1206.9 | 57.2 -> 57.2 |
| search_factuality | 1203.7 | 1202.1 | 56.3 -> 56.5 |

## Scope

**In:** a new ADR superseding D-146 clause 2; `score_anchor` served from the derived floor on Elo
surfaces (`null` elsewhere, and `null` without an artifact); `CategorySpec.score_anchor` and
`PINNED_SCORE_ANCHORS` removed; the tests that pinned anchors restated as the rule; REQ-SCR-003;
W-133 FIXED; the comments in `adapter/main.py` and `Uncertainty.swift`.

**Out:** the app's sentences (they already say "50 is at the bar", which becomes true); the
conversion itself (D-143, `Uncertainty.swift`); D-146 clause 4 (the 2000 Elo guard); ECI (rank-only).

## Phases

- **P1 — red:** the served anchor equals the served floor on every Elo surface, moves with the board,
  and is `null` off Elo and without an artifact.
- **P2 — green:** the endpoint serves the floor; the pinned field and table go.
- **P3 — records:** the ADR, REQ-SCR-003, W-133, comments.
