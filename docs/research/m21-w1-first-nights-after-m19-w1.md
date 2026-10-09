---
record_type: register
id: m21-w1-first-nights-after-m19-w1
status: draft
process_version: v6.6
date: 2026-10-09
---
# The first real nights after M19-W1, against its first-night simulation (#166)

**Read on 2026-10-09**, read-only, from the owner's Mac:
- the engine service's log (`~/Library/Logs/model-ranking-engine.log`);
- the served artifact's refresh record (`~/Library/Application Support/model-ranking/engine/data/advisor.db.refresh.json`);
- the installed releases (`engine/releases/`).

Nothing was written there.

## What M19-W1 predicted for the first night (#166)

- The night publishes.
- The board nearest a limit is `epoch_frontiermath`: 18 of 114 rows changed (16%), against the 25% limit.
- The record's `renamed` holds about 97 display changes and no board re-spelling.
- About 26 model ids join or split.

## What the nights did

M19-W1 is merge `1843437` (#167). The service ran it from 2026-10-06 21:24, then `133a525` (M19-W2,
with the home-network bind) from 22:41 that day, then `45d72e8` (the M19 closure) from 2026-10-07
13:27. Each holds M19-W1.

| night (log line) | release | outcome | surfaces answering | models | scores | prices |
|---|---|---|---:|---:|---:|---:|
| before M19-W1 (390) | `3f2e91d` | published | 14 | 315 | 14,174 | 3,669 |
| 1st after (434) | `133a525` | **published** | 14 | 305 | 14,174 | 3,676 |
| 2nd after (471) | `45d72e8` | **published** | 14 | 305 | 14,174 | 3,700 |
| 3rd after (494, 2026-10-08 20:18 UTC) | `45d72e8` | **published** | 14 | 306 | 14,174 | 3,705 |

**Read against the prediction.**
- **Every night published, and no night refused.** There was no "would lose N of M rows" refusal, so
  D-179's case of link churn did not occur.
- **The models went from 315 to 305 on the first night,** with the score rows unchanged (14,174).
  That is ids joining (#129) and splitting (#130, #162), the direction the simulation predicted. The
  net change of 10 is not the 26 joins and splits the simulation counted, because a join and a split
  can offset each other in the total. No record keeps the gross figure.
- **The third night's record:**
  - `renamed` holds 0 entries;
  - 213 models are derived and 20 names are unmatched;
  - nothing is carried and nothing has expired;
  - there is no layout drift.

**What could not be read.**
- The first night's `renamed` count (about 97 predicted).
- The first night's board nearest the limit (`epoch_frontiermath`, 16% predicted).

The refresh record is rewritten each night, and the service log keeps only the outcome line and
the tail of the build report. The prediction's two finer numbers are therefore not checkable after
the fact. What is checkable, that the nights published with no refusal, holds.

## What would make the next first night readable

Keep each night's `renamed` count and its largest board change in the outcome line the service logs.
That would be one line per night, in the log the owner already keeps. It is noted here and left as a
follow-up rather than built in M21-W1.

## The M21-W1 release's own first night, simulated

This wave's changes move model ids and add a board:
- DeepSeek V3-0324 and R1-0528 split from V3 and R1 (D-189);
- the two rerouted xAI ids drop (D-189);
- `web-dev` moves to `arena_webdev` (D-190).

A refresh of a copy of the served artifact, run with this wave's code (in the wave's worktree, on
2026-10-09), **published on its first cycle** with 14 surfaces answering. `arena_webdev` arrived with
140 rows, and V3-0324 and R1-0528 hold 31 and 34 rows of their own. `web-dev` passes the turnover
guard as a surface returning: the served artifact holds no row of its new board. A second cycle also
published, after Anthropic's Haiku 5.5 got its curated name.

## The query that finds a family a board ranks under two releases (the review's B3)

Run on an artifact, it lists each curated model a board ranks under two release names; effort, search and
thinking variants are read as one name. On the artifact refreshed with this wave's code it found the
families D-189 splits here (Mistral Large, Claude Sonnet 4.6, GLM-4.6V), the snapshots that stay gathered
(GPT-4o, the Gemini 2.5 previews) and the candidates #232 holds.

```python
import sqlite3, re, collections
from app.workflows.registry import MODEL_RULES, split_harness, resolve_effort
curated = {r.canonical_id for r in MODEL_RULES}
conn = sqlite3.connect("advisor.db")
def key(raw):
    _, m = split_harness(raw)
    m = resolve_effort(m, None).model_name.lower()
    m = re.sub(r"[-_ ](search|grounding|thinking[-_ ]?\d*k?|no thinking|non[-_ ]?reasoning|reasoning|preview"
               r"|instant|customtools|\d+k)\b.*$", "", m)
    m = re.sub(r"\s*\((?:no )?thinking.*?\)|\s*\(default.*?\)|\s*\(\d+k think\)", "", m)
    m = re.sub(r"[-_ ]?(?:high|low|medium|max|xhigh|minimal|none|unknown)$", "", m)
    return re.sub(r"[\s_]+", "-", m.strip())
groups = collections.defaultdict(set)
for mid, src, raw in conn.execute("SELECT model_id, source, raw_name FROM scores WHERE model_id IS NOT NULL"):
    if mid in curated:
        groups[(mid, src)].add(key(raw))
for (mid, src), keys in sorted(groups.items()):
    if len(keys) > 1:
        print(mid, src, sorted(keys))
```

**The refresh trial after the review's fixes** (this worktree's artifact, 2026-10-09) published, with 14
surfaces answering:
- 313 models;
- Mistral Large 1.0, 2, 2.1, 3 and 4 hold 30, 30, 29, 38 and 29 rows;
- Claude Sonnet 4.6 holds 65 rows, apart from Sonnet 4's 88;
- R1-0528 holds 32 rows, and its Qwen3-8B distill holds 3 of its own;
- GLM-4.6V holds 27 rows apart from GLM-4.6.

