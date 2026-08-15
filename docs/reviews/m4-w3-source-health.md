---
record_type: register
id: m4-w3-source-health
status: ratified
date: 2026-08-15
---
# M4-W3 — Source health, plan coverage, and the fresh-benchmark investigation

## 1. What is now measured (REQ-SUB-005, REQ-ING-011)

`python -m app.workflows.coverage --db advisor.db` reports both numbers and exits 1 when a
category can answer nothing at all. It runs in the weekly CI job. Measured on live data,
2026-08-15 (LiteLLM + SWE-bench + Aider live, Arena from the owner's fetch):

| Category | Scoreable plans | Cannot rank — no link at all | Cannot rank — linked, no score on this benchmark |
|---|---|---|---|
| assistant | **5 / 9** | ChatGPT Go, Claude Max, Claude Pro | ChatGPT Plus |
| coding | **1 / 9** | ChatGPT Go, Claude Max, Claude Pro | ChatGPT Plus, ChatGPT Pro, Google AI Ultra, Perplexity Max, Perplexity Pro |

The two failure modes are deliberately separated because they have different fixes: *no link*
is a curation/roster problem (W2 closed what evidence allowed), *no score* is a benchmark-coverage
problem — which is what the rest of this record is about.

| Source | Rows | Newest evidence | Age | Verdict |
|---|---|---|---|---|
| arena | 389 | 2026-08-12 | 3 days | ok |
| swebench | 173 | 2026-02-26 | **170 days** | **STALE** |
| aider | 68 | 2025-10-03 | **316 days** | **STALE** |

Both tables were recomputed independently by the wave's reviewer, with their own SQL, from a DB
rebuilt from the same live sources — every figure matched. The scoreable plans themselves:
assistant = ChatGPT Pro, Google AI Pro, Google AI Ultra, Perplexity Max, Perplexity Pro;
coding = Google AI Pro alone. The report's "scoreable" set was also checked against what the
ENGINE can actually rank (`subscribe.plan_ranking`) — identical, so the metric measures the
product rather than a parallel definition of it.

**Which clock:** this report ages evidence against TODAY. The engine's own `stale_notice` ages it
against the ingest stamp instead (deterministic by design, D-104). Same 90-day window, two clocks,
stated here so the two numbers are never read as a contradiction.

## 2. The finding this wave exists to state plainly

**The coding category rests on a source that has stopped publishing.** SWE-bench's newest entry
is 2026-02-26 — and not only on Verified: every board in the same file (bash-only, Multilingual,
Test, Lite, Multimodal) tops out between 2025-09-11 and 2026-02-26. Aider has been dead since
2025-10-03 and was already documented as such at M1. Meanwhile the assistant category's source is
three days old.

Consequence for the product, in one line: **coding answers are honest about the past and silent
about the last six months.** The engine already discloses this (`stale_notice` fired in the owner's
verification run); the fix is a fresher source, not a louder warning.

## 3. Fresh-benchmark investigation — what exists, and where it can be reached from

| Candidate | Documented machine-readable form | Licence | Reachable from the build sandbox? |
|---|---|---|---|
| **Epoch AI Benchmarking Hub** | `https://epoch.ai/data/benchmark_data.zip` (CSV bundle, stated on epoch.ai/benchmarks/use-this-data, updated 2026-08-14); also a `pip install epochai` client over the Airtable API | CC-BY, attribution required; embedded Aider + Terminal-Bench data keep Apache-2.0 | **NO** — epoch.ai returns proxy 403 here |
| **Terminal-Bench 2.0 leaderboard** | HF dataset `harborframework/terminal-bench-2-leaderboard` (same datasets-server API the Arena source already uses) | per dataset card | **NO** — huggingface.co returns proxy 403 here |
| SWE-bench Pro (`scaleapi/SWE-bench_Pro-os`) | repo exists; no leaderboard JSON located at a documented path | — | GitHub raw reachable, but no documented data file found |
| Artificial Analysis | — | — | **BANNED** (D-101, internal-use-only free tier) |

Guessed paths were probed and rejected rather than assumed: four candidate raw-GitHub URLs for a
Terminal-Bench leaderboard returned 404, and `api.github.com` is 403 from here, so the repo tree
could not be listed. **No parser was written against an unseen shape** — that is the FP-M2-2 defect
this project paid for twice, and the rule is unchanged: probe the live source for any value you put
in a fixture, before the wave closes.

## 4. What that means for REQ-ING-010 / REQ-ING-011

Both candidates need exactly one out-of-sandbox fetch, the same pattern that closed REQ-CAL-001 at
the M3 gate. The two commands were delivered to the owner on 2026-08-15 (chat), writing into
`terminal_output/model_ranking/`. **Until the real shapes are on disk, the criteria stay OPEN and
visible here rather than being satisfied by an invented fixture.** If the fetch does not happen
this milestone, the closure report carries them as an acknowledged criteria diff to M5 — with this
record as the reason.

## 5. Standing consequence

Source health is no longer something an owner notices during a demo. It is computed on every run,
printed by the coverage command, and carried in the closure report. A source that goes quiet now
shows up as a number with a date next to it, in the same place the coverage figure lives.
