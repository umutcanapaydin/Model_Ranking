# Assumptions — run queue-1021

Questions the run met that are reversible, local to one issue and outside a ⛔ zone, each with the most conservative answer it took. The owner reads them in the morning; each is undone by a commit.

| When | Issue | Question | Answer taken |
|---|---|---|---|
| 2026-10-21 | #378 | A media board's models are registered on a score alone, in a pass of their own. D-157 needs a price and a score, and none of these models is priced per token. | Within D-218 clause 1: an image or video board's names are read by the derive grammar, with no modality guard and bracketed variants kept as name tokens. A curated rule wins only if it declares a media modality, so `kling-o3-pro` is never OpenAI's `o3-pro`. An id the text pass registered keeps its row. Undone by removing `registry._reconcile_media`. |
| 2026-10-21 | #378 | What vendor does a media model show? The board's `organization` column is not stored. | The grammar's family prefixes, else `Other` (FLUX, Seedream, Kling and Veo show `Other`). Storing the column is a schema change for its own issue. |
| 2026-10-21 | #378 | How does `/v1` say a surface is not priced, without breaking a client already installed? | `/v1/categories` gains `priced`. Answers keep their field sets, with null prices and a single `best_quality` pick. `/v1/boards` lists the unpriced models under a new `unpriced_models` key with no price field. That way every `models` entry keeps a number, and today's app still decodes the payload. An installed app that opens a media surface fails on that one answer only. |
| 2026-10-21 | #378 | `video_edit` ranks 10 models. | It opens anyway, because D-218 clause 1 names it. Clause 3's 15-model rule is for #379's new boards. |
| 2026-10-21 | #378 | The run order of phases 3 and 4. | Phase 3 lands the engine together with the router's reach (hints, examples, keyword rules, the retired image decline, probes), because `test_router_hints.py` pairs every served surface with a hint. Phase 4 is the screens: no price shown, the price note, and the Turkish titles. |
| 2026-10-21 | #378 | Truncation floors for the five boards. | About half of each overall board as recorded on 2026-10-21: 30, 40, 24, 24 and 5. |
