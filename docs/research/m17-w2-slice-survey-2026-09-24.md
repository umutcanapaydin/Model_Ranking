---
record_type: register
id: m17-w2-slice-survey-2026-09-24
status: ratified
process_version: v6.6
date: 2026-09-24
---
# M17-W2 — how many models each category slice can rank, measured

**Measured 2026-09-24** with `scripts/survey_boards.py --db advisor.db --slices`, on a copy of the
owner's artifact of 2026-09-24 01:17 (the served file was not written). Both configs' parquet files
were downloaded live; every slice's rows carry the publish date 2026-09-13. Issue #22, D-164.

`ranked` is the only column that decides what a later combination (W4) can use: the models the
engine can rank, meaning reconciled to the registry and priced. `floor` is the board's row floor,
half the count measured when the table was declared.

| board | rows | floor | ranked | leader |
|---|---:|---:|---:|---:|
| `arena_text_english` | 402 | 201 | 189 | 1511.8 |
| `arena_text_non_english` | 402 | 201 | 189 | 1504.6 |
| `arena_text_hard_prompts` | 402 | 201 | 189 | 1527.3 |
| `arena_text_instruction_following` | 402 | 201 | 189 | 1523.3 |
| `arena_text_creative_writing` | 400 | 200 | 188 | 1507.7 |
| `arena_text_multi_turn` | 400 | 200 | 188 | 1511.9 |
| `arena_text_coding` | 397 | 198 | 188 | 1535.3 |
| `arena_text_math` | 384 | 192 | 185 | 1537.3 |
| `arena_text_longer_query` | 380 | 190 | 188 | 1523.3 |
| `arena_text_expert` | 352 | 176 | 184 | 1557.2 |
| `arena_text_chinese` | 373 | 186 | 182 | 1605.3 |
| `arena_text_russian` | 366 | 183 | 186 | 1522.0 |
| `arena_text_german` | 299 | 149 | 168 | 1523.4 |
| `arena_text_spanish` | 283 | 141 | 163 | 1521.9 |
| `arena_text_french` | 281 | 140 | 163 | 1539.0 |
| `arena_text_korean` | 269 | 134 | 153 | 1532.1 |
| `arena_text_japanese` | 265 | 132 | 154 | 1515.1 |
| `arena_text_polish` | 222 | 111 | 136 | 1520.5 |
| `arena_text_industry_software_and_it_services` | 402 | 201 | 189 | 1528.9 |
| `arena_text_industry_writing_and_literature_and_language` | 401 | 200 | 189 | 1516.1 |
| `arena_text_industry_entertainment_and_sports_and_media` | 400 | 200 | 188 | 1495.5 |
| `arena_text_industry_life_and_physical_and_social_science` | 400 | 200 | 188 | 1530.7 |
| `arena_text_industry_business_and_management_and_financial_operations` | 395 | 197 | 188 | 1501.4 |
| `arena_text_industry_mathematical` | 379 | 189 | 184 | 1545.6 |
| `arena_text_industry_legal_and_government` | 375 | 187 | 185 | 1534.5 |
| `arena_text_industry_medicine_and_healthcare` | 371 | 185 | 186 | 1517.6 |
| `arena_vision_english` | 152 | 76 | 85 | 1324.3 |
| `arena_vision_chinese` | 117 | 58 | 77 | 1408.3 |
| `arena_vision_diagram` | 108 | 54 | 73 | 1359.1 |
| `arena_vision_ocr` | 108 | 54 | 73 | 1336.0 |
| `arena_vision_homework` | 102 | 51 | 73 | 1356.8 |
| `arena_vision_creative_writing_vision` | 90 | 45 | 68 | 1348.6 |
| `arena_vision_humor` | 84 | 42 | 63 | 1347.1 |
| `arena_vision_entity_recognition` | 48 | 24 | 39 | 1354.5 |
| `arena_vision_captioning` | 34 | 17 | 28 | 1333.8 |

## What it says

- **Every board clears its floor.** The thinnest is `arena_vision_captioning`: 34 rows, floor 17.
- **Each `text` slice ranks 136 to 189 models, and each `vision` slice ranks 28 to 85.** The
  language slices are the thinnest `text` boards (`polish` 136, `korean` 153).
- **No new model.** 316 models are registered before and after, so D-157's derived registration
  sees nothing new from the slices, as the plan expected (every slice's names are a subset of its
  config's `overall` board, measured on the same files).
- **The artifact grows from 2,097,152 to 7,110,656 bytes** with the 10,245 slice rows. Each score
  row repeats its source, benchmark and source URL as text, and the scores table is indexed. This is
  the engine's own file, which the phone never downloads. W4 decides what the standings route
  sends.

## Not measured here

- The per-slice confidence interval (`rating_lower`, `rating_upper`) is not stored (plan, "Out").
  W4 decides whether a combination by position needs it.
- The nightly refresh with the slices, end to end on the owner's machine. The owner runs that
  after merge: the first night the boards arrive is a publish (D-164 clause 3), not a refusal.
