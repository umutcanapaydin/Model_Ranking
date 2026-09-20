---
record_type: review
id: m14-category-calibration
status: ratified
date: 2026-09-20
---
# Threshold calibration for `document` and `factuality` (M14-W2)

Measured on the artifact built 2026-09-18 and published by the refresh (`advisor.db`), with
`scripts/calibrate_board.py`, which calls the engine's `ranked_population` (REQ-EVI-002).

| Surface | Board models (distinct) | Ranked | Leader | `min_quality` (board third, D-145) | Ranked third (not used) | Admitted | `close_call` | `value_window` | Candidates |
|---|---|---|---|---|---|---|---|---|---|
| `document` | 36 | 29 | 1516.3 | **1467.5** | 1471.0 | 10 of 29 | **8.7** | **35** | 7 |
| `factuality` | 143 | 59 | 1500.7 | **1450.6** | 1460.7 | 32 of 59 | **4.0** | **20** | 6 |

- `min_quality` — the top third of the whole board over distinct models (each model's best rating):
  the rule the nine shipped surfaces were measured by (W-094), adopted for new surfaces by the
  owner's ruling D-145. Reproduced by the script's `board_third_D145` field.
- `close_call` — the median rating gap across pairs whose published 95% intervals overlap (155 pairs
  on `document`, 613 on `factuality`), measured on the owner's machine on 2026-09-18 because the
  intervals are not stored in the artifact. This differs from M8's "2 x stderr, else the median
  adjacent gap", and pairs include a model's own effort variants (review m8).
- `value_window` — sized by candidate count on the ranked population (M8's rule). The script's
  "4 x close_call" is a candidate, not the rule.
- Registry drift seen on these boards and not given rules, because none carries a price: the
  `muse-spark` family, `gpt-6-astra`, `kimi-k3`, `gemma-4`, `qwen3.7-plus`, `glm-5.3`, `glm-5v`.
