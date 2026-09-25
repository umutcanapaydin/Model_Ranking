---
record_type: plan
id: m17-wave-3-plan
status: draft
process_version: v6.6
date: 2026-09-25
---
# M17-W3 plan — Epoch's own boards, the Agent Arena boards, model accessibility, no ids from moving aliases

**Working plan for the `wave/m17-w3` pull request**, deleted before merge. Issue #37 (and #24).
Milestone plan: `docs/plans/m17-plan.md` §2 W3. Risk: **MED**. The pull request opens only after the
wave's reviews and `/pre-merge` (the owner's rule), not at this plan.

## Goal

More boards for W4 to combine, and an honest registry for them: five Epoch-run boards and six Agent
Arena boards are stored and published as boards (D-164); every model carries its accessibility from
Epoch's `model_metadata.csv`; and no model is derived from an undated API alias whose meaning moves.
No surface, `/v1` route or app change.

## Ruled by the owner, 2026-09-25 (in session, translated from Turkish)

1. **Epoch classes A and B:** `simpleqa_verified.csv`, `frontiermath_tiers_1_3_v2.csv`,
   `frontiermath_tier_4_v2.csv`, `chess_puzzles.csv`, `mystery_game_puzzles.csv`. Class C stays out
   (`docs/research/source-expansion-2026-09-23.md` §2.1 gives each one's reason).
2. **The six `agent*` configs become boards** (#24), on their own metric.
3. **`model_metadata.csv` now**, as an attribute, not a board.
4. **No derived model from a moving alias.**

## What the data looks like (measured 2026-09-25)

- The five Epoch files have GPQA Diamond's shape exactly: `Model version`, `mean_score` (0-1),
  `Started at`, `Release date`, `stderr`. Rows: 80, 108, 64, 224, 129. Evaluations to 2026-09-18.
- `model_metadata.csv`: 1,089 rows, 14 with no `model_version`, 152 with no `accessibility`. The key
  is Epoch's model name, the same spelling its boards use. Values: API access 511, Open weights
  (unrestricted) 253, (restricted use) 120, (non-commercial) 28, Hosted access (no API) 12,
  Unreleased 10, Limited access 3.
- The six `agent*` parquet files: 43 rows each, one category (`overall`), published 2026-09-24,
  columns `model_name, organization, license, score, score_ci_lower, score_ci_upper,
  observation_count, session_count, rank, category, leaderboard_publish_date`. IPS scores (τ̂), not
  Bradley-Terry: the dataset card says so. 29 of 43 rank on the served artifact (#24). Higher is
  better on all six (read from the dataset's own `rank`).
- Moving aliases registered today as derived ids (`docs/reviews/m16-wave-4-rereview.md` MINOR-1):
  `claude3.5-sonnet`, `mistral7b-instruct`, `deepseek-chat`, `deepseek-reasoner`, `command-r`,
  `command-r-plus`, `mistral-medium`, `gpt4-turbo`, `gpt4o-mini`, `o1`, `o1-mini`, `yi-large`,
  `claude-instant`.

## Shared contracts (K.8), grep-verified at c04ec4f

```
src/app/workflows/registry.py:413:def derive_identity(name: str) -> DerivedIdentity | None:
src/app/workflows/registry.py:592:def reconcile(conn: sqlite3.Connection) -> ReconcileReport:
src/app/workflows/refresh.py:467:    for board in sorted(ARENA_SLICES, key=lambda b: b.source_name):
src/app/clients/parquet_reader.py:44:_COLUMNS = ("model_name", "rating", "category", "leaderboard_publish_date")
src/app/clients/arena.py:41:METRIC = "elo"
src/app/clients/arena.py:356:def score_rows(
src/app/workflows/schema.py:25:CREATE TABLE IF NOT EXISTS models (
```

## Decisions made on the owner's behalf (implementation)

1. **D-164 covers every board no surface ranks on, not only the slices.** Its clause 1 says "each
   declared board"; the code fingerprinted `ARENA_SLICES` only. The board set becomes the declared
   boards (Arena slices, Epoch boards, Agent boards) minus the ones a surface ranks on as primary or
   secondary evidence, derived from `CATEGORIES`, never listed by hand.
2. **The Epoch boards are five rows in `EPOCH_BOARDS`**, the existing reader and parser, `fraction`
   scale, dated by `Started at`, each with its own source id and benchmark label.
3. **The agent boards read through the D-165 reader**, which learns a column map:
   `score` for the value and the metric `ips`. `score_rows` takes the metric and harness as
   parameters, so no Arena Elo assumption leaks into them. A test fails if an `ips` board and an `elo`
   board could ever meet in one ranking.
4. **Accessibility is a new table, `model_access(model_id, accessibility, source)`**, additive: no
   existing column changes. Epoch's names reconcile to model ids through the registry, as scores do.
   Where two names of one model disagree, the model gets no value, and the disagreement is counted in
   the build report, never guessed. It is part of the fingerprint, so a change publishes.
5. **Moving aliases are one declared list in `registry.py`** (`MOVING_ALIASES`), each with its reason.
   `derive_identity` returns None for them, so their rows stay unmatched and show in `/health`'s
   unmatched list, which is the honest place for them. A curated rule (the list wins, D-157) still
   takes a name when one is written; the list only stops derivation. Recorded as **D-166**.

## Phases

- **P1: the Epoch boards and D-164 over every uncovered board.** Red first:
  - each new board ingests under its own source and benchmark;
  - a change on an Epoch board no surface ranks on publishes, and a quarter lost is refused;
  - the board set is derived from `CATEGORIES`.
- **P2: the Agent Arena boards.** Red first:
  - the reader's column map;
  - `ips` rows under their own metric;
  - the six boards declared with floors and ceilings;
  - an `ips` board never joins an `elo` ranking;
  - the stale-date and hostile-file rules hold for them.
- **P3: accessibility.** Red first:
  - the table, the reconcile join, the disagreement counted;
  - the fingerprint moves with it;
  - no column of an existing table changes.
- **P4: moving aliases (D-166).** Red first:
  - each listed alias derives no id;
  - a curated rule still wins over the list;
  - the unmatched report names them.
- **P5: measured and recorded.**
  - The survey of the new boards' rankable population on a copy of the served artifact.
  - The served change: derived models before and after, surfaces moved.
  - `smoke_deps` gains the agent configs.

## Risks

- **The first night after merge.** The derived-model count falls by the moving aliases. A surface
  that ranked one of them loses it, and D-128's quarter-loss guard could refuse the night. P5 measures
  it on the served artifact before the pull request opens. If a surface would lose a quarter, the
  first publish is the owner's, by hand (as D-132's roster jump was).
- **Reader generalisation (D-165)** touches the untrusted-input path. The security look of W2 is
  repeated on the changed reader.
- **Accessibility joins through name reconciliation**, so an unmatched Epoch name gives no value.
  That is counted, not guessed.
