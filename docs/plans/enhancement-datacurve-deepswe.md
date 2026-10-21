# Enhancement plan: `agentic-coding` ranks on Datacurve's CC BY 4.0 DeepSWE dataset (#265)

**Issue:** #265. Its last triage (2026-10-21) routed it to `work-enhancement`, and the owner told us to work it now, so
the approval step is given. **Branch:** `enhancement/issue-265-datacurve`, cut from `main` at `c29317c`. This plan is
deleted before the push (an enhancement's plan never lands on the default branch).

## Goal

`agentic-coding` ranks on Datacurve's own DeepSWE dataset (`datacurve/deep-swe-leaderboard` on Hugging Face, CC BY 4.0),
read with the owner's Hugging Face read token, instead of Epoch's copy of the board (`epoch_deepswe_external`, no
licence published). This is the last move D-194 clause 1 left waiting for the token, and it serves Golden Rule 1.

## Scope

**In:**
- A declared remote source, `datacurve_deepswe`, with a client and a parser in `app.clients`. It reads the newest job
  directory under `raw/jobs/` (the tree API lists them), then that job's result.json (the scores) and config.json
  (each run's stated reasoning effort). A later job needs no code change.
- The token: from `HF_TOKEN`, or else from the owner's file `~/Library/Application Support/model-ranking/hf-token`.
  It is never logged, printed, stored in the artifact or committed. Without it the source fails loudly with a message
  that names where the token goes, and the build reports the surface as having no evidence. It never serves an empty
  board.
- One canonical test double (`respx` on the bounded fetch, as for every remote client), a parser test on a recorded
  fixture trimmed to the means and counts (no token), and a contract test (`RUN_CONTRACT_TESTS=1` and the token).
- Effort per D-194 clause 1: the surface ranks at `high`. Harness `mini-swe-agent`.
- `agentic-coding` recalibrated on the new board (D-148, D-194 clause 4), with its record and a calibration note.
- Credits: Datacurve, CC BY 4.0, with its link. `epoch_deepswe_external` stays a retired attribution row and credit
  (D-194 clause 6), so an artifact an older release built still boots.
- D-185's table records the move, as D-194 annotated it. The decision is an ADR, committed before the code.
- The id-linking count of the board's 27 rows, and any alias the rows need.

**Out:** `web-dev` (D-190); `terminalbench_4` and `arena_agent` in the family; every other surface; `public.LEFT_OUT`
(stays empty, D-194 clause 1); the hosted engine's deploy (the owner's); the M5 pinned measurement's replay of Epoch's
DeepSWE file (`board_measurement.py`), which describes that snapshot.

## Open decisions, each taking its most conservative answer

1. **The effort of a row the job's key leaves without one.** The result file names an effort only for a model run at
   several (16 of its 27 rows carry none). The job's own config.json states each run's `reasoning_effort`, and four
   of those 16 were run at a stated effort: GPT-5.4 and GPT-5.4 mini at `xhigh`, Claude Opus 4.6 at `max`, Gemini 3.5
   Flash at `medium`. **Answer:** a stated effort is always kept, so no `xhigh`, `max` or `medium` run is ranked as a
   `high` one. The 11 runs with no stated effort (the model's default setting) are stored at `high`, the rule the
   re-triage wrote for effortless rows, and the level Epoch's copy of the same board gave Gemini 3.1 Pro's default run.
   A run whose effort the config does not state at all, or states outside the schema, is skipped and counted, never
   guessed.
2. **Required or optional.** **Answer:** optional, as every sole-evidence board fetched from Hugging Face is (D-121).
   A failure, a missing token included, carries the last good rows (D-156) or makes the build exit 3 with the surface
   named; it never fails the other sources' night. CI's contract job has no token, and a required source would fail
   its build every run.
3. **Where the token comes from.** **Answer:** `HF_TOKEN` first, then the owner's file. A token file that its group or
   others can read is refused. The `Authorization` header goes only to `huggingface.co`: the fetch refuses any other
   host, on the first URL and on every redirect.
4. **Which job.** **Answer:** the newest directory whose name starts with a date (`YYYYMMDD-`); none is a failure.
   A partial job would fall below the source's row floor and fail, carrying the last good rows.
5. **The old client.** **Answer:** `DeepSWEClient` and its local-bundle entry go, so no build writes
   `epoch_deepswe_external` again. The CSV parser stays: the M5 measurement and its tests replay that file.
6. **The benchmark label.** **Answer:** `DeepSWE`, unchanged. It is the same benchmark, and the app's sentences name it.
7. **The board's standard error for calibration.** **Answer:** Datacurve's own, from each run's published 95%
   run-to-run interval (summary.json, `ci_half` / 1.96), median over the runs, read once for the record. The nightly
   source does not read those 27 files.
8. **The ADR id.** **Answer:** the id after the next free one, because #376's open branch has already taken the next free one.

## Phases

1. **The decision.** The new ADR, committed alone, before any code.
   *Check:* `make check-records` green.
2. **The source.** Red: the parser on the recorded fixture (efforts, harness, scores, run date, skipped rows), the
   client against the double (the newest job, the token sent only to the hub, a missing or loose token refused with no
   request made), and the registry (the source is declared and optional). Green: `app.clients.datacurve`, its ingest,
   its `RemoteSource`, the bounded fetch's request headers, the `hf_token` need for the contract test.
   *Check:* the new tests green; `make check`.
3. **The move.** Red: `agentic-coding` ranks on `datacurve_deepswe`, its family names it, no build declares
   `epoch_deepswe_external`, Datacurve is credited under CC BY 4.0, and the retired source still boots an older
   artifact. Green: categories, families, sources, attributions, credits; `DeepSWEClient` removed (a removal).
   *Check:* `make check`.
4. **Calibration.** The live board ingested through the registered source into a copy of the artifact,
   `scripts/calibrate_surface.py` run on it; the record, the note under `docs/reviews/`, and the surface's thresholds.
   Red first: the calibration test names the new record. *Check:* `make check`.
5. **Records.** D-185's table, D-194's amendment line, the PRD row (REQ-SRC-012), the skip budget, the process log;
   this plan deleted. *Check:* `make gate` on the clean committed tree; `make review-need-branch`.
