---
record_type: register
id: m17-w3-boards-and-first-night-2026-09-25
status: ratified
process_version: v6.6
date: 2026-09-25
---
# M17-W3: the new boards' rankable populations, and the first night after the merge, measured

**Measured 2026-09-25.** A candidate artifact was built from live sources with the branch's code
(`wave/m17-w3`) and compared against a byte-identical copy of the artifact the engine service
serves (`~/Library/Application Support/model-ranking/engine/data/advisor.db`, published 2026-09-25
16:24, confirmed with `cmp`). The served file was not written. The comparison used the nightly
refresh's own decision functions: `serving_summary`, `degradations` and `upward_anomalies`. Issue #37,
and #24 for the agent boards.

## 1. A defect this measurement found, fixed before the pull request

`serving_summary` raised `no such table: access` on the served artifact. That artifact predates
the `access` table, like every artifact built before this wave. The refresh fingerprints the live
artifact as well as the candidate, and it treats a live artifact that raises as unreadable, so
every night after the merge would have failed. `access.served` now returns no values when the table
is absent. The red test, `test_an_artifact_from_before_the_table_still_fingerprints`, went in first
(8ea2532), then the fix (333542c).

## 2. The first night publishes

| check | result |
|---|---|
| `degradations(live, candidate)` | `[]` |
| `upward_anomalies(live, candidate)` | `[]` |
| digests equal | no, so the night publishes |
| boards fingerprinted (D-164) | 46 on both sides: 35 Arena slices, 6 agent boards, 5 Epoch boards |
| new boards on the live side | 0 rows each. D-164 counts a board's first night as returning, not as a quarter new |

The candidate registers 306 models, against 317 on the served artifact. Twelve derived ids are gone,
each one a moving alias under D-166: `claude3.5-sonnet`, `command-r`, `command-r-plus`,
`deepseek-chat`, `deepseek-reasoner`, `gpt4-turbo`, `gpt4o-mini`, `mistral-medium`,
`mistral7b-instruct`, `o1`, `o1-mini`, `yi-large`. The thirteenth, `claude-instant`, was not
registered on the served artifact. One model is new, `hy4-preview`. Its only scores are on the six agent boards.

## 3. What each surface loses and gains

Only surfaces where something moved are listed. The largest loss is 5 of 190 (assistant), far
below the quarter D-128 refuses.

| surface | served | candidate | models gone (D-166) |
|---|---:|---:|---|
| assistant | 190 | 185 | `command-r`, `command-r-plus`, `mistral-7b-instruct`, `mistral-medium`, `o1-mini` |
| coding | 55 | 54 | Claude 3.5 Sonnet |
| everyday | 151 | 147 | Claude 3.5 Sonnet, GPT-4o mini, `o1`, `o1-mini` |
| expert | 148 | 146 | `deepseek-chat`, `deepseek-reasoner` |
| mathematics | 138 | 136 | `deepseek-chat`, `deepseek-reasoner` |

**A display-name change, by an existing rule.** Five derived models change their served name:
`GLM-5.3-Flash` becomes GLM 5.3 Flash, and the same happens to Qwen3.7 Plus, Hy3, Mimo V2.5 Pro and
Solar Pro 4. The Agent Arena boards spell these names with spaces. `_derived_display` (D-157)
already prefers a board's spaced spelling, and until now no board had one for these models. The
model ids are unchanged, so no ranking moves. In the table on each surface, the change shows as one
name lost and one name gained.

## 4. How many models each new board can rank

`rankable` means `ranked_population`: reconciled to the registry and priced (REQ-EVI-002). Scores
are on each board's own scale. Epoch's fractions are converted to percent, and the agent boards
report IPS (τ̂), which can be negative. D-105 keeps IPS and Elo apart.

| board | metric | rows | linked | rankable | range | leader |
|---|---|---:|---:|---:|---|---|
| `epoch_simpleqa` | % correct | 80 | 65 | 65 | 6.0 to 75.6 | GPT-6 Astra |
| `epoch_frontiermath` | % correct | 108 | 69 | 69 | 0.0 to 93.7 | GPT-6 Astra |
| `epoch_frontiermath_t4` | % correct | 64 | 51 | 51 | 0.0 to 97.6 | GPT-6 Astra |
| `epoch_chess` | % correct | 224 | 113 | 113 | 0.0 to 72.0 | GPT-6 Astra |
| `epoch_mystery` | % correct | 129 | 61 | 61 | 0.0 to 84.0 | GPT-6 Astra |
| `arena_agent` | ips | 43 | 30 | 30 | -0.164 to 0.134 | Claude Fable 5.1 |
| `arena_agent_bash_recovery_steps` | ips | 43 | 30 | 30 | -0.253 to 0.126 | Claude Opus 5 |
| `arena_agent_praise_complaint` | ips | 43 | 30 | 30 | -0.220 to 0.347 | Claude Fable 5.1 |
| `arena_agent_steerability` | ips | 43 | 30 | 30 | -0.122 to 0.116 | Claude Fable 5 |
| `arena_agent_task_outcome_explicit` | ips | 43 | 30 | 30 | -0.236 to 0.170 | Claude Fable 5.1 |
| `arena_agent_tool_hallucination` | ips | 43 | 30 | 30 | -0.029 to 0.004 | GPT-5.5 |

`rows` counts parsed rows, which include effort variants. `linked` counts distinct registered
models. On the agent boards 30 models rank, one more than the 29 #24 measured on the served
artifact. The difference is `hy4-preview`, which only the agent boards name (§2).

## 5. Accessibility

The build linked 647 of Epoch's names to a model, and 290 names linked to none. Six models get no
value because their names disagree: `deepseek-v3`, `gpt-5.4`, `gpt-5.5`, `grok-4`, `kimi-k2` and
`mistral-large`. The candidate serves an accessibility value for 219 models.

## 6. The dependency smoke test covers the agent boards

`scripts/smoke_deps.py` probes every config in `SLICE_CONFIGS`, and those now include the six agent
configs. They were run live through the script's own `_probe` and `_slice_probe`, and all six
returned `ok`, one board with 43 rows each.

## Method, re-runnable

- **Candidate:** the refresh's build with live fetches, written to a scratch path. Its JSON report
  was kept beside the candidate.
- **Comparison:** `serving_summary`, `degradations` and `upward_anomalies` from
  `app.workflows.refresh`, run on the two read-only connections.
- **Populations:** `ranked_population` with a `CategorySpec` whose `primary_source` is the board,
  the same construction `scripts/survey_boards.py` `measure_slices` uses.
