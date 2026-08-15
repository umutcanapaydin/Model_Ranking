---
record_type: ratification
id: m3-elo-calibration
status: ratified
date: 2026-08-15
---
# REQ-CAL-001 — Assistant-category Elo threshold recalibration (M3 closure)

**Why this existed:** M2 shipped the assistant thresholds as a FIRST CALIBRATION and said so —
`min_quality=1300`, `value_window=30`, `close_call=5` were chosen before anyone had seen the live
distribution (M2 closure report §1b; handover §9 named 1300 "arbitrary").

**Evidence.** Live overall board pulled by the owner out-of-sandbox on 2026-08-15 (this container
cannot reach the HF datasets-server): documented `/filter` endpoint, `config=text`, `split=latest`,
`where "category"='overall'`, 4 pages × 100.

- `num_rows_total` = **389**, all 389 fetched; one snapshot only (`leaderboard_publish_date`
  = 2026-08-12), so no stale-high risk in this sample (the FP-M2-2 guard still applies).
- Rating range **833.6 – 1507.8**, median **1335.6**; p75 1419.8, p90 1450.2, p95 1470.8.
- 95% CI width: median **10.8** (top-30 median 9.2).

| Cut | Models ≥ cut | Share of board | Distance below leader |
|---|---|---|---|
| 1500 | 3 | 1% | 8 |
| 1450 | 39 | 10% | 58 |
| 1425 | 85 | 22% | 83 |
| **1400** | **131** | **34%** | **108** |
| 1350 | 181 | 47% | 158 |
| 1300 (old floor) | 221 | **57%** | 208 |

**CI-overlap probe (all pairs in the top 60, by rating gap):**

| Gap (Elo) | 0–5 | 6–7 | 8–9 | 10–11 | 12–13 | ≥14 |
|---|---|---|---|---|---|---|
| Pairs whose 95% CIs still overlap | 100% | 92% | 64% | 23% | 5% | ~0% |

## Decisions (data edit in `categories.py`; the engine did not change)

1. **`min_quality` 1300 → 1400.** The Budget Pick floor must mean "still competitive with the
   frontier". 1300 admitted **57% of the live board** — a floor that excludes almost nothing is
   not a floor. 1400 keeps the top third (34%, leader−108) and cuts the long tail of older/smaller
   models. Effect on the product: on a thin budget the Budget Pick can now legitimately trip the
   quality-floor-unmet warning branch ("you are trading away quality", in the product's Turkish
   user-facing wording) — which is the honest outcome, and it is tested.
2. **`close_call` 5 → 8.** A near-tie should mean "the measurement cannot separate them". At a
   5-Elo gap **100%** of live top-60 pairs still have overlapping 95% CIs, so the old threshold
   under-disclosed real ties; at 8–9 Elo, 64% still overlap and at 10–11 only 23%. 8 is the
   **conservative lower edge of the last bucket whose overlap rate exceeds 50%**. Stated precisely
   (per-integer bands, review-recomputed): [8,9) = 69.8%, [9,10) = 54.3%, [10,11) = 23.5% — so 9
   would also satisfy "more likely than not indistinguishable"; we ship 8, which discloses fewer
   ties than the data would license rather than more.
3. **`value_window` 30 — KEPT, now justified rather than assumed.** 30 Elo is ≈4× the noise
   threshold (a real but modest quality difference) and admits 13 models within reach of the
   leader — enough choice for "cheapest in band" without pretending a 30-Elo gap is nothing.

**Coding category untouched** (different scale; D-105 forbids transferring these numbers).

**Revisit when:** the board's shape changes materially (new leader ≫ 1508, or median moving
> ~50 Elo), or a third category lands. Re-run the same probe; the thresholds are three numbers in
a data record, not code.

## Reproducing this record (conventions matter — state them, don't imply them)

Fetch (owner machine, ~10 s), N = 0,100,200,300:
`curl -s "https://datasets-server.huggingface.co/filter?dataset=lmarena-ai/leaderboard-dataset&config=text&split=latest&where=%22category%22%3D%27overall%27&offset=N&length=100"`

Analyse: `python3 scripts/arena_calibration.py <dir-with-the-4-json-files>` (committed with this
record — a calibration whose numbers cannot be recomputed is an assertion, not evidence).

Two conventions the numbers depend on, made explicit after the review recomputed them both ways:
- **Percentiles:** Weibull / R type-6 (`statistics.quantiles`, exclusive). NumPy's default `linear`
  method gives p90 1449.8 / p95 1470.2 instead of 1450.2 / 1470.8.
- **Overlap buckets:** floor-bucketed by gap (`k ≤ gap < k+2` labelled `k`). Round-bucketing or
  half-open variants shift the 8–9 cell between 64% and 76%; the decision boundary does not move,
  but the published figure does.
