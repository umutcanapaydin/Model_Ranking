---
record_type: register
id: m17-w4-standings-payload-2026-09-25
status: ratified
process_version: v6.6
date: 2026-09-25
---
# M17-W4: the standings payload, and what the combination rule does on real boards, measured

**Measured 2026-09-25.** `app.workflows.standings.board_standings` was run with the branch's code
on two read-only artifacts:
- the artifact the engine service served that day, built before M17-W3;
- a candidate built from live sources with `main` at 7d7a9ac, which holds M17-W3's boards.

The combination rule (D-167 clause 3) was replayed in Python on the candidate's payload, so each
result can be checked by hand against the boards' own positions. The Swift implementation of the rule
left M17-W4 at the three-attempts stop and returns with #61; the replay records what the rule does,
not what shipped. Issue #50.

## 1. The payload

| artifact | boards | models | positions | bytes | gzip |
|---|---:|---:|---:|---:|---:|
| served (before W3) | 52 | 314 | 6,563 | 324,613 | 30,352 |
| candidate (main, with W3) | 63 | 303 | 6,962 | 346,112 | 31,769 |
| the same candidate, after the review round (effort per standing, D-112) | 63 | 303 | 6,955 | 499,633 | 36,407 |
| served after the first nightly refresh with W3 (2026-09-25 23:05 local) | 63 | 303 | 6,955 | 499,633 | 36,408 |

- **Raw size.** About 500 KB since each standing carries its evidence's effort (the review round's
  B1). The engine does not compress its responses today, so this is what a phone downloads once a
  day (#55). D-167 first stated about 250 KB; the difference is each board's repeated attribution
  sentence, the JSON keys and the effort strings. Compressed, the payload is 36 KB.
- **Bounds.** The phone's ceiling is 4 MiB (`EngineClient.maxStandingsBytes`), about eight times
  what is measured here. The engine's is 25,000 positions (`MAX_PUBLISHED_STANDINGS_ROWS`), about
  3.6 times.
- **Board sizes.** The smallest boards rank 18 models (`epoch_deepswe_external`, at `high` since the
  review round), 27 (`arena_search_factuality`) and 28 (`aider`); the largest rank 185.

## 2. The rule on real boards

Each line shows a model's sum of ranks among the models the chosen boards share, and its
position on each chosen board as that board published it.

**Arena text (coding) + SWE-bench Verified (Epoch): 30 models in common.**

| model | sum | positions |
|---|---:|---|
| Claude Opus 4.7 | 3 | 4, 1 |
| Claude Opus 4.6 | 5 | 1, 4 |
| GPT-5.5 | 9 | 14, 2 |
| Gemini 3.5 Flash | 11 | 15, 3 |
| Qwen3.7 Max | 12 | 11, 7 |

**Arena text (math) + FrontierMath Tiers 1-3 + AIME: 51 models in common.**

| model | sum | positions |
|---|---:|---|
| Claude Fable 5.1 | 4 | 2, 2, 1 |
| Claude Fable 5 | 7 | 3, 5, 1 |
| Claude Opus 5 | 14 | 1, 7, 10 |
| GPT-5.5 | 19 | 12, 8, 1 |
| Qwen3.8 Max | 19 | 8, 13, 1 |

GPT-5.5 and Qwen3.8 Max tie on 19 and are ordered by id. On AIME, every model scoring 100% shares
position 1, so that board separates the leaders only through the other two.

**Arena text (coding) + Agent Arena + TerminalBench: 3 models in common.**

| model | sum | positions |
|---|---:|---|
| GPT-5.5 | 4 | 14, 7, 1 |
| GPT-5.4 | 5 | 13, 15, 2 |
| Gemini 3.1 Pro | 9 | 27, 24, 3 |

## 3. What this means for W5

**The all-present rule is strict on small boards.** Three boards that each rank 30 or more
models share only 3, because each small board ranks a different set. That is D-167's stated cost
("the list is at most as long as the smallest chosen board"), and in practice the list is often
much shorter. The owner ruled it knowing the cost.

What W5 chooses decides how often it bites:
- W5 chooses the boards from the question. Choosing fewer, larger boards for a question keeps the
  list useful.
- The detail screen must say how many models the chosen boards share (D-160 clause 3).

## Method, re-runnable

`board_standings(open_readonly(<artifact>))`, serialised with `json.dumps(..., separators=(",",
":"))`, then `gzip.compress`. The replay keeps the models every chosen board ranks, re-ranks each
board among them with competition ranking, and sorts by (sum of ranks, model id).
