---
record_type: plan
id: m17-wave-2-plan
status: draft
process_version: v6.6
date: 2026-09-24
---
# M17-W2 plan — Arena's category slices become boards

**Working plan for the `wave/m17-w2` pull request**, deleted before merge. Issue #22. Milestone plan:
`docs/plans/m17-plan.md` §2 W2. Risk: **MED**, with a security look at the new read (P1): it adds a
native-code dependency that parses a file downloaded from the internet.

## Goal

Every meaningful category slice of the Arena dataset the product already reads is stored in the
artifact as its own BOARD (a source id with its own benchmark label), published by the nightly
refresh and guarded like the boards surfaces rank on, so W4 can serve and combine them. No new
surface, no `/v1` change, no app change.

## Ruled by the owner, 2026-09-24 (in session, translated from Turkish)

1. **Read path: the dataset's own parquet file, one per config, through `pyarrow`**, chosen over
   paging the whole split through `/rows` (about 110 requests a night against today's 4-5, the
   pattern that rate-limited this client before, W-007). Adding the dependency is the "ASK" row of
   `permission-matrix.md`; this is that answer.
2. **Scope: every meaningful slice, 35 boards**, chosen over the plan's 19.

## What the data looks like (measured 2026-09-24)

- `text/latest-00000-of-00001.parquet` is 588,920 bytes: 10,606 rows, 29 categories, all on one
  publish date (2026-09-13). The columns are the eleven `arena.py` already documents.
- `vision/latest-00000-of-00001.parquet` is 56,113 bytes: 1,029 rows, 11 categories.
  `vision/creative_writing` has 34 rows and none on the newest date.
- The datasets-server `filter` endpoint still answers 500 for `text` (W-024) and 200 for `vision`.
- The dataset now also carries six `agent_*` configs of 46 rows each (not slices: separate configs).

**The 35 boards** (rows on 2026-09-13):

| config | slices |
|---|---|
| `text` (26) | `english` 402, `non_english` 402, `hard_prompts` 402, `instruction_following` 402, `creative_writing` 400, `multi_turn` 400, `coding` 397, `math` 384, `longer_query` 380, `expert` 352, `chinese` 373, `russian` 366, `german` 299, `spanish` 283, `french` 281, `korean` 269, `japanese` 265, `polish` 222, and the eight `industry_*` slices: software and IT 402, writing and literature 401, entertainment and media 400, life and social science 400, business and finance 395, mathematical 379, legal and government 375, medicine and healthcare 371 |
| `vision` (9) | `english` 152, `chinese` 117, `diagram` 108, `ocr` 108, `homework` 102, `creative_writing_vision` 90, `humor` 84, `entity_recognition` 48, `captioning` 34 |

**Left out, each with its reason:** `overall` (already read, unchanged by this wave);
`exclude_ties` (the same votes with ties dropped, a method variant, not a question);
`hard_prompts_english` (the intersection of two slices already taken); `vision/creative_writing`
(no current snapshot); every `*_style_control` config (a second answer to the same question,
`docs/research/source-expansion-2026-09-23.md`); the `agent_*` configs (filed as an issue: new
configs, not slices, and not in this wave's scope).

## What the code does today (from the read of 2026-09-24)

- `ArenaClient` reads only the `overall` prefix of each config through `/rows` and stops at the
  first other category (`arena.py:217-246`); the caps (`_MAX_PAGES`, `_MAX_MERGED_ROWS`) forbid the
  whole split. `ARENA_BOARDS` has one board per config and no category field.
- Rankings join on `benchmark` and `metric`, not on source (`rank.py:268-281`): a slice stored under
  the label `Arena text` would merge into `assistant`, which is what `document` did at M14-W2.
- **A board no surface names never reaches the live artifact.** `serving_summary`
  (`refresh.py:409-436`) fingerprints surfaces only, so a candidate that adds boards reads as
  "nothing a user would notice changed" and is discarded, while `sources_last_ok` records the
  source as served. The D-128/D-132 guards iterate surfaces too, so boards are unguarded.
- The serving process imports `app.clients.*` (W-125), so a module-level `import pyarrow` would load
  in the server.
- The Epoch boards are the precedent for many boards through one reader: `EPOCH_BOARDS` data rows,
  one `EPOCH_BOARD_CLIENT`, `_ingest_boards` (`build.py:361-410`), each board failing and carrying
  (D-156) on its own.

## Decisions made on the owner's behalf (implementation; each goes into D-164)

1. **One fetch per config, one board per slice.** The slices of a config are read from one download,
   so a failed download fails every slice of that config, and each slice then carries on its own
   clock (D-156). A slice that downloads but falls under its row floor fails alone.
2. **A slice is served only on its config's newest publish date.** A slice with no rows on that date
   (today, `vision/creative_writing`) is refused and counted, never served old (FP-M2-2's rule, per
   slice).
3. **Each board has its own source id and benchmark label**: source `arena_<config>_<slice>`,
   benchmark `Arena <config> (<slice>)`, both derived from one table (`ARENA_SLICES`), as is its
   attribution in `SOURCE_ATTRIBUTION`. A test fails when two boards share a benchmark label.
4. **Row floors are half the measured count, stated per board with its date.** The table carries the
   measured count; the floor is derived from it, and a test holds `floor < measured`.
5. **Boards are published content, and guarded as boards.** The fingerprint hashes each slice
   board's standings, so a board change alone publishes, and D-132's board-name guard (a quarter of
   raw names new) and D-128's (a quarter lost) apply to each slice board. A board appearing for the
   first time passes as returning (the existing empty-set rule), so the first publish is not refused.
   Written as **D-164**.
6. **`pyarrow` is imported inside the parse function only**, and a test fails if the serving process
   can import it through any path (extending the D-154 guard to name it).
7. **The download is capped while it is read**: 8 MB per file (today 0.6 MB), the same streamed cap
   `arena.py` applies per page. A file that is not parquet, lacks a column, or carries a non-finite or
   out-of-band rating is a `SourceError` or a counted skip, as every Arena row is today.

## Scope

**In:** `pyarrow` in `pyproject.toml` (slopsquat and pip-audit clean); `ArenaSliceClient` and the
parse; `ARENA_SLICES` (35 rows); build ingest and per-slice carry; derived attribution; the
fingerprint and guards (D-164); `survey_boards.py` able to measure a slice (rankable rows, reconciled
and priced), run once on the owner's artifact into a research record; `smoke_deps` gains one probe per
config, not per slice.

**Out:** serving the boards (W4, D-160's `/v1` route); the per-slice confidence interval
(`rating_lower`, `rating_upper`: the schema has no column for it, and W4, which combines by position,
decides whether ties need it); moving the `overall` boards to the parquet read; the `agent_*` configs;
any surface, `/v1` or app change.

## Phases

- **P1 — the read.** `pyarrow` declared; `ArenaSliceClient(config)` downloads
  `<config>/latest-00000-of-00001.parquet`; `parse_arena_slices(raw, slices)` returns rows per slice.
  Red first:
  - a small parquet built in the test yields each declared slice's rows;
  - the newest-date rule per slice;
  - a file over the cap, a file that is not parquet, a missing column, and an `Infinity` rating;
  - the serving process does not import `pyarrow`.
  - `ARENA_SLICES` and the client's registry entry (`ARENA_SLICE_CLIENT`) land here, not in P2: the
    registry mirror test refuses a client nobody declares.
- **P2 — the boards.** The build's ingest of each config and each slice, per-slice
  carry, derived attribution. Red first:
  - no slice's rows reach `assistant` or `vision`;
  - one slice under its floor fails alone, while a failed download fails its config's slices;
  - every board has a distinct benchmark label;
  - `floor < measured` for every board.
- **P3 — published and guarded (D-164).** Red first:
  - a candidate that changes only a slice board publishes;
  - a slice board that loses a quarter of its names, or gains a quarter new, is refused;
  - a board seen for the first time is not refused.
- **P4 — measured and recorded.**
  - `survey_boards.py` measures slices, and is run on the owner's artifact: how many models each
    board can rank, in a research record.
  - `smoke_deps`.
  - The `agent_*` issue.
  - D-164 accepted by the owner in the PR.

## Risks

- **A native parser of a downloaded file.** Bounded by the size cap before parsing, by pyarrow being
  loaded only in the refresh child (D-154), and by the security look at P1.
- **Thin slices.** A slice has fewer votes than `overall` and so wider intervals. This wave stores
  standings only, and W4 decides how a combination treats them.
- **About 12,000 more score rows** in the artifact (35 boards × about 350). Measured on the build in
  P4, and reported against today's artifact size.
- **Derived registration (D-157) sees the new rows.** A slice's models are a subset of its config's
  `overall` board (measured 2026-09-24: no slice of either config names a model its `overall` lacks), so no new model is expected. P4 measures `refresh_derived` before and after.
