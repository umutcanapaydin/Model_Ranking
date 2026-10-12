---
record_type: register
id: terminalbench-4-feasibility-2026-10-12
status: draft
process_version: v6.6
date: 2026-10-12
---
# Terminal-Bench 4.0 for `computer-use`: can the board move from Epoch's 2.0 copy? (D-193)

> The owner asked on 2026-10-12 (translated from Turkish): "Terminal-Bench: the CSV is TB 2.0; only 4.0
> is Apache in the repo. Look at the feasibility of moving to 4.0." This record answers that. The move
> itself is the owner's ruling.

**Answer: feasible, and small to build, with one cost: the board ranks about 17 models today, against 42.**
A third way keeps TB 2.0 under a licence: rebuild it from its own Apache-2.0 submissions (below).

## What exists, read on 2026-10-12

- **Today's board.** `epoch_terminalbench` reads Epoch's `terminalbench_external.csv`, a copy of the
  Terminal-Bench **2.0** leaderboard (tbench.ai), which states no licence. In the served artifact it
  ranks **42 priced models**. Its newest run date is **2026-05-14**: TB 2.0 closed its submissions then,
  so the board is frozen. Its top models are GPT-5.5, GPT-5.4, Gemini 3.1 Pro and Claude Opus 4.7.
- **Terminal-Bench 4.0.** Its official leaderboard is defined and kept in the repository
  [`harbor-framework/terminal-bench`](https://github.com/harbor-framework/terminal-bench), licence
  **Apache-2.0** (GitHub's API: `Apache-2.0`).
  - `leaderboard/leaderboard.yaml` defines the board `4-0-0`, "The official leaderboard for
    Terminal-Bench 4.0", shown on Harbor Hub.
  - `leaderboard/submissions/` holds **21** submissions, one JSON file each. Their file names date them
    2026-08-26 to 2026-10-06, when they were added; their runs (`metadata.date`) are dated 2026-05-28 to
    2026-09-29. Each names its model (`source_filter.model_name`, e.g. `anthropic/claude-opus-5-5`), the
    agent, the reasoning effort, the run date and `metrics.accuracy`, a percentage with its 95 %
    interval over 330 trials.
  - The leaderboard is live: the newest submission was added on 2026-10-06, and the repository was pushed
    on 2026-10-09.
  - The task set `harborframework/terminal-bench` on Hugging Face (tag v4.0.0, 66 tasks) is Apache-2.0 too.
    The product needs no task, only the scores.
- **The licence reaches the scores.** The submission files are in the Apache-2.0 repository. Nothing in
  its README or `leaderboard/SUBMIT.md` excludes them. Apache-2.0 asks a redistributor for a copy of the
  licence and the notices kept. The Credits screen (#260) names the licence and links it.

## What the move costs

| | TB 2.0 (Epoch's copy, today) | TB 4.0 (the repository) |
|---|---|---|
| licence | none stated | Apache-2.0 |
| models | 59 on the board, 42 priced | 21 on the board, about 17 priced today |
| newest run | 2026-05-14 (closed) | 2026-09-29 (open) |
| agents | many scaffolds | one per model maker (Claude Code, Codex, Grok Build, mini-SWE-agent, Muse Code) |
| effort | mixed | named on every submission (`max`, `xhigh`, `high`, `none`) |

- **Fewer, newer models.** The 21 models are the frontier of 2026-08 to 2026-10, among them Claude Opus 5.5
  (64.8 %), GPT-6.1 Sol (58.2 %) and Claude Fable 5.1 (57.9 %). The older and cheaper models TB 2.0 ranks
  (GPT-5.4, Gemini 3.1 Pro, Claude Opus 4.6) are not on it.
- **Name matching.** In the served registry, 9 of the 21 match by exact id or display name. Most of the rest
  are there under another spelling (`claude-4.8-opus`, `claude-opus5.5`, `glm5.3`), which the registry's
  reconciliation already handles for other boards. Not priced today: the GPT-6 family and
  `qwen3.8-max-0902`.
- **The two scales differ.** A 4.0 score is not a 2.0 score: the task sets differ. Each version must be its
  own board (D-105), never one board.

## A third way: TB 2.0 from its own Apache-2.0 submissions

The licence review (`docs/research/data-licences-2026-10-04.md`, note 5) found the raw TB 2.0 submissions
in [`harborframework/terminal-bench-2-leaderboard`](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard),
tagged **apache-2.0**. On 2026-10-12 it holds **75** agent-and-model folders under
`submissions/terminal-bench/2.0/`, and its card says "SUBMISSIONS CLOSED".

- **What it keeps.** The models TB 2.0 ranks today, under a licence, where Epoch's copy states none.
- **What it costs.** It holds trials, not scores: each submission's accuracy is computed from its
  per-trial results (the research record's effort L). It is frozen at 2026-05, like Epoch's copy.
- **With 4.0.** Option (a) below can take this as its 2.0 board in place of Epoch's copy, so both
  versions are licensed.

## How it would be built

1. **A client** reading `leaderboard/submissions/*.json` from the repository at a pinned commit, through
   GitHub's contents API or `raw.githubusercontent.com`, with the bounded fetch the other clients use.
   About 21 small files, so no bundle is needed.
2. **A board declaration** `terminalbench_4` (metric `% resolved`, harness from the agent, effort from the
   submission), with a parser test on a recorded fixture and a contract test against the live repository
   (`RUN_CONTRACT_TESTS=1`).
3. **The surface.** Two options for the owner:
   - **(a) 4.0 primary, 2.0 kept in the family.** `computer-use` ranks on 4.0, and the combined list
     (D-188) draws on both. Recommended: the surface answers with current models, and no model 2.0 ranks
     disappears from the combined list.
   - **(b) 4.0 replaces 2.0.** The surface and the list rank about 17 models.
4. **Calibration.** `computer-use`'s window and tie margin were measured on 2.0's spread; 4.0's intervals
   (about ±3 points over 330 trials) set its own, as M21-W1 did for `web-dev` (#185).
5. **Credits.** One more credit, Terminal-Bench (Apache-2.0, the repository's link).

Size: one wave, about the size of M21-W1's move of `web-dev` to LMArena's board (#185).

## What I could not establish

- Whether Harbor Hub serves the same scores as the repository's files. The hub page renders by script.
  The repository's `leaderboard.yaml` is the board's definition, so its files are taken as the source.
- Whether every submission stays in the repository once a newer one replaces it. Two naming schemes sit side
  by side today (`2026-08-26-…` in `submissions/`, `tb-4-0-0-…` in `runs/`).
