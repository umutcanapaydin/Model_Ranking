---
record_type: review
id: m15-wave-1-review
status: ratified
seat: independent
date: 2026-09-22
---
# Independent review: M15 Wave 1 (the board survey, and W-094)

**Reviewer:** Code-Reviewer seat, fresh eyes (K.7, D-133). I authored none of this wave.
**Commit under review:** `17e6554`: `scripts/survey_boards.py`, `docs/research/m15-board-survey-2026-09-21.md`.
**Policy read from:** `855b44a` (`subagent-profiles/Code-Reviewer.md`, `AGENTS.md`). None was read from the change.
**Evidence used:** a copy of the live `advisor.db` (built 2026-09-22T11:33Z, worktree at `d8cd650`), and the raw runs in `terminal_output/model_ranking/m15-runs/` (read-only). I had no network access.

## Verdict

**PASS WITH FINDINGS: 0 blocking, 2 major, 6 minor.**

**The numbers are right.** I wrote my own code to recompute every cell of the W-094 table and every Arena row of the survey table. Every value matches the record to 0.1. `survey.json` is transcribed into the record correctly. The script writes nothing to the artifact, and it calls the engine's own `ranked_population`, `_store_scores`, `reconcile` and `parse_arena`.

**The interpretation needs one correction before D-148 is carried out.** The six M8 surfaces were not floored on "the top third of the whole board over *distinct models*" (D-145, as the survey computes it). Their floors match the top third of the board's **rows**, one row per raw name, to 0.1 on four of six boards and within 0.3 on the other two. The two definitions differ by up to 6.7 points (`abstract`: 72.8 against 79.5). So the directional W-094 answer stands, and is stronger than the record claims: 10 of 11 surfaces sit on a board rule, not the ranked rule. But "board third for every surface" (D-148) moves six shipped floors by 0.3 to 6.7 points if it is applied with D-145's distinct-model count. The record does not say this, and it names `everyday` as an exception when it is not one.

## Findings

### MAJOR

**M-1: The record names the wrong board rule as "the rule the product actually shipped".**
`docs/research/m15-board-survey-2026-09-21.md:112-119`
- **What is wrong.** The record says the rule the product actually shipped "is D-145's — the top third of the whole board over distinct models", and that the two surfaces that do not fit (`agentic-coding`, `everyday`) are "the two thinnest boards".
- **What the data shows.** The M8 floors equal the top third of the board's rows, one row per raw name as `parse_board` emits them. This matches `docs/reviews/m8-category-calibration.md:44-58`, which counts ECI at 521 "models", which is the row count. It does not match D-145's count, which collapses raw names to canonical ids through `canonicalize(resolve_effort(...))` and gives 295 for ECI. See the three-rule table below:
  - `abstract`, `computer-use`, `mathematics` and `web-dev` reproduce exactly under the rows rule, and not under D-145.
  - `everyday` is 149.6 under the rows rule against 149.9 shipped. It is not an exception, and ECI is not thin: 295 distinct models, 521 rows.
  - `coding` is 65.4 on the `swebench` source's rows against 65.0 shipped.
  - Only `agentic-coding` (50.0) fits no rule.
- **Why it matters.** D-148 was ruled on this record. Applying "board third" with D-145's population would move these floors:

  | surface | shipped | D-145 floor | change |
  |---|---|---|---|
  | `abstract` | 72.8 | 79.5 | +6.7 |
  | `computer-use` | 53.4 | 57.3 | +3.9 |
  | `mathematics` | 84.4 | 86.4 | +2.0 |
  | `coding` | 65.0 | 66.6 | +1.6 |
  | `web-dev` | 1478.9 | 1480.0 | +1.1 |
  | `everyday` | 149.9 | 144.6 | −5.3 |
  | `expert` | 83.6 | 83.3 | −0.3 |

  Some of these moves are larger than the surface's own `close_call` (for example abstract 1.0, computer-use 0.8). That is not "correct the comment". It is a recalibration of six surfaces, and the owner should know it before it lands.
- **Remedy.** Add a correction section to the record with the three-rule table. Take the population question back to the owner as one line inside D-148: "board rows (what M8 shipped) or distinct canonical models (what D-145 and the three W3 surfaces use)". Until that is answered, do not re-derive any M8 floor under D-148. Drop the "two thinnest boards" sentence.

**M-2: No script in the commit reproduces 8 of the 11 W-094 rows. The script's docstring claims it does.**
`scripts/survey_boards.py:17-20`, `docs/research/m15-board-survey-2026-09-21.md:14-18, 95-96`
- **What is wrong.** The docstring says the survey prints both rules "so the owner can rule once, on eleven surfaces' worth of evidence". The script only reads LMArena configs, so it covers `assistant`, `document` and `factuality`. The other eight rows are Epoch and SWE-bench boards: `coding`, `agentic-coding`, `everyday`, `expert`, `mathematics`, `computer-use`, `abstract`, `web-dev`. The record says only that they were "computed … from the live artifact", with no command, and the reproduction section points only at the survey.
- **Why it matters.** An ADR now rests on eight numbers that nothing in the repository reproduces. W-037's doctrine is that this is how the wrong number keeps coming back. I did reproduce all eight exactly, so this is a gap in provenance, not an error.
- **Remedy.** Add a `--shipped` mode, or a small companion script, that reads `scores` from the artifact read-only. For each `CATEGORIES` entry it should print all three candidate floors: rows, distinct-canonical, and ranked through `ranked_population`. Cite it in the record. Also fix the docstring.

### MINOR

- **m-1: The style-control claim is wrong.** `docs/research/m15-board-survey-2026-09-21.md:51-53`. The record says floors are "within 5 Elo" of the base board. `survey.json` shows gaps of 5 Elo or more on every base/style-control pair:

  | pair | board ⅓ gap | ranked ⅓ gap |
  |---|---|---|
  | `text` | 0.8 | **15.4** (1450.6 against 1466.0) |
  | `search` | 9.6 | 9.1 |
  | `vision` | 7.2 | 6.1 |
  | `document` | 5.1 | 4.7 |

  `search` spreads also differ: 251.1 against 174.8. The claims of identical row counts and ranked populations are true. **Remedy:** restate with the real gaps. The "variant, not a new question" judgement may still hold, but it has to be argued on those gaps, not on "within 5".
- **m-2: The `agentic-coding` board third pools effort levels.** `docs/research/m15-board-survey-2026-09-21.md:102, 118-119`. The surface ranks only `effort='high'` (`categories.py`, `ranking_effort="high"`). The 67.2 board third mixes low through max. On the `high` rows the board third is **64.4**, the same as the ranked third. "50.0 against 67.2" overstates the gap the recommendation cites. **Remedy:** when `agentic-coding` is re-derived, state which efforts the board population includes.
- **m-3: "Nine of eleven" counts two rows that hold by construction.** `docs/research/m15-board-survey-2026-09-21.md:109-112`. `document` and `factuality` were floored on D-145, so the independent evidence is 7 of 9. The table marks them "(by construction)" but the headline does not. **Remedy:** one clause in the headline.
- **m-4: The rate parser keeps the last duplicate, not the best.** `scripts/survey_boards.py:166-168`. The Elo path keeps the best rating (`parse_arena`'s own docstring). The rate path keeps whichever duplicate comes last. This has no effect today: `skipped` is 0 on all six `agent_*` boards. **Remedy:** keep the max, or refuse duplicates.
- **m-5: Output formatting.** `scripts/survey_boards.py:305-307, 329-337`. The header prints a `metric` column that the rows never fill, so every column in `survey.txt` sits one place off its header. Lines 335-336 use truthiness, so a floor of exactly 0.0 prints as `-`, and the signed `agent_*` boards can produce one. `survey.txt` also prints D145 and ranked⅓ floors for the `agent_*` boards, where direction is undefined (the record says so itself). Those numbers mean nothing and should print `-`.
- **m-6: The script depends on private engine internals.** `scripts/survey_boards.py:96-104, 235`. It builds `ArenaClient` without calling `__init__` and calls `_get_page` and `_store_scores`. Reusing the engine's code is the right call, but a new attribute in `ArenaClient.__init__` would surface as a per-board `AttributeError` that line 316 records as a board "result". **Remedy:** a comment is enough. Better, add a small public `ArenaClient.for_survey(config)` so the bypass is tested.

### Notes that are not findings

- The "over two million observations" claim (record line 60-61) is backed by run `20260921-215005`: its `sample_row` shows `observation_count` 2,305,432 for `agent_tool_hallucination`. The run the record cites, `215558`, does not carry it. Cite both runs.
- The record's line "24 of 31 models on the board already carry a per-token price" (`search_factuality`) holds: 24 ranked of 31 distinct.
- The record's "53 ranked against Epoch's 49" also holds: the artifact ranks 49 on `WebDev Arena`.

## W-094 table: the record's numbers beside mine

In my columns, "rows ⅓" is the top third over board rows, which is what M8 did. "D-145 ⅓" is distinct canonical models, each at its best score, which is what the survey and `calibrate_board.py` do. "ranked ⅓" is the best score per `model_id`, joined to `models` and `px_median`, with the surface's effort filter applied. All three use the same quantile index, `round(n/3) - 1`, over the scores sorted from highest to lowest.

| surface | shipped | record board ⅓ | **mine D-145 ⅓** (n) | record ranked ⅓ | **mine ranked ⅓** (n) | **mine rows ⅓** (n rows) | nearest rule |
|---|---|---|---|---|---|---|---|
| coding | 65.0 | 66.6 | 66.6 (147) | 75.8 | 75.8 (44) | 70.0 (206, both sources); **65.4** (173, `swebench` only) | rows (`swebench`) |
| assistant | 1400.0 | 1394.9 | 1394.9 (357) | 1450.6 | 1450.6 (65) | 1406.7 (402) | round number, set at n=389 (M3) |
| agentic-coding | 50.0 | 67.2 | 67.2 (17); 64.4 on `high` only | 64.4 | 64.4 (13) | 64.4 (49) | none |
| everyday | 149.9 | 144.6 | 144.6 (295) | 153.2 | 153.2 (58) | **149.6** (521) | rows |
| expert | 83.6 | 83.3 | 83.3 (183) | 91.0 | 91.0 (50) | **83.4** (263) | rows / D-145 |
| mathematics | 84.4 | 86.4 | 86.4 (158) | 95.6 | 95.6 (51) | **84.4** (238) | rows, exact |
| computer-use | 53.4 | 57.3 | 57.3 (45) | 61.6 | 61.6 (33) | **53.4** (59) | rows, exact |
| abstract | 72.8 | 79.5 | 79.5 (82) | 87.2 | 87.2 (39) | **72.8** (168) | rows, exact |
| web-dev | 1478.9 | 1480.0 | 1480.0 (79) | 1522.9 | 1522.9 (49) | **1478.9** (102) | rows, exact |
| document | 1467.5 | 1467.5 | 1467.5 (36) | 1471.0 | 1471.0 (29) | 1470.7 (44) | D-145 (by construction) |
| factuality | 1450.6 | 1450.6 | 1450.6 (143) | 1460.7 | 1460.7 (59) | 1451.5 (171) | D-145 (by construction) |

**Every number in the record's W-094 table matches mine.** The record's "closer to" column is also right. On the record's two-rule comparison, `agentic-coding` and `everyday` really are closer to ranked. The third column is what the record is missing.

## The survey table: `survey.json` and the artifact against the record

- **Transcription.** Every row of the record's table matches `20260921-215558/survey.json`: rows, distinct models, ranked, leader, spread, D145, ranked⅓, plus the `agent_*` leader, last and median gap values. The "10–78" range is right: video_edit 10, image_to_video 48, text_to_video 48, image_edit 55, text_to_image 78.
- **Independent from the artifact.** I recomputed the seven Arena boards the artifact now holds from `scores` with my own code: text, factuality, document, vision, search, search_factuality, and the Epoch webdev board for comparison. Rows, distinct models, ranked count, leader, spread, both floors and the median neighbour gap all match `survey.json` exactly for the six LMArena boards.
- **Shipped reproductions.** The record says 65 / 29 / 59 ranked for text / document / text_factuality. That is confirmed. The artifact's `Arena factuality` has 60 distinct `model_id`s, one of them without a price median, so the ranked count is 59 as stated.

## The quantile question

The survey keeps one score per model, the **best**, in both populations:
- **Board:** `board_best[key] = max(...)` at `scripts/survey_boards.py:218-222`, keyed on `canonicalize(resolve_effort(raw).model_name)`, falling back to the raw name.
- **Ranked:** `MAX(score) GROUP BY model_id` in `category_ranking`.

This is the same key and the same quantile as `scripts/calibrate_board.py:213-222`. That script produced `document` 1467.5 and `factuality` 1450.6, and the survey reproduces both. **The survey is consistent with D-145 as it was applied in M14.** It is not consistent with how the M8 floors were made (M-1).

## What I verified, and how

1. **Recomputed W-094 with my own SQL.** I read the `scores` table and `px_median` directly and took the `CategorySpec` values from `17e6554:src/app/workflows/categories.py`. I did not import the script. The engine's `canonicalize` and `resolve_effort` were used only to build the D-145 key. Result: all 22 floor cells match. I also tested sensitivity to a `ceil(n/3)` index: none of the "closer to" calls change.
2. **Replayed `measure()` offline to test "writes nothing".** I patched `ArenaClient.fetch_raw` to serve a payload in the Hugging Face row format, built from the artifact's own rows for `document`, `vision`, `search_factuality` and `text`, then ran the real `survey_boards.measure` against `advisor.db`. Its outputs equal `survey.json` for all four boards. The SHA-256 and mtime of `advisor.db` were unchanged afterwards. All writes go to `shutil.copy` targets under a `TemporaryDirectory` (`scripts/survey_boards.py:190-201, 311`). Survey rows use their own `source` and `benchmark` (`survey_<config>`, `(survey) <config>`), so they cannot collide with the shipped `Arena *` rows inside the copy.
3. **Engine reuse.** The script calls the engine's own functions: `parse_arena`, `_store_scores`, `reconcile` and `ranked_population`, which calls `category_ranking`. Nothing is re-implemented except the rate parser. That parser sits outside `src/` by design and is documented as survey-only.
4. **The M8 provenance.** I compared rows ⅓ with the shipped floors (M-1) against `docs/reviews/m8-category-calibration.md`.

## What I did not verify

- **Anything that needs the dataset API.** I could not check the 16 boards that are not in the artifact (webdev LMArena, the style-control variants, the image and video boards, the `agent_*` boards) against upstream. For those I checked only the transcription from `survey.json`, and read the script path they go through.
- **Whether the snapshot drifted between the survey run and the artifact build.** The survey ran 2026-09-21 21:55 and the artifact was built 2026-09-22 11:33. For the six LMArena boards it holds, the numbers are identical, so drift did not affect them.
- **Whether M8's floors were meant to be over rows.** The rows rule reproduces them exactly. Whether that was the intent is for the owner to say, together with D-148.
- **Tests and `make check`.** I did not run them. The wave adds no `src/` code.

## Outside this wave's scope (K.9)

- **`scripts/calibrate_board.py:233` (W3) mislabels a count.** It writes `"ranked_population": len(rankable)`, which counts raw names whose display is ranked. It does not count ranked models. So `calib-20260922-142701/vision.json` says 64 where the engine ranks 41 (search 26 against 25, search_factuality 25 against 24). A reader comparing it with this record sees a contradiction that is not there. Rename the field to `rankable_raw_names`, or emit `len(population)`.
- **The `categories.py` comments for `everyday` and `computer-use`** say "sized on the RANKED population" (58, 33). Both the numbers and M8's own table say otherwise. Fold this into the D-148 comment correction.

## Risks queued

- D-148 carried out with the D-145 population silently recalibrates six shipped surfaces (M-1). Put the population choice to the owner before any M8 floor is edited.
