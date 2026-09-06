# scripts/

Project state ops — LLM-free, deterministic, fast (seed C.7).

| Script | Purpose |
|---|---|
| `runner_verdict.sh` | Sourced by `runner`: how a leg is recorded, skipped, and what the run is allowed to claim. Separate from `runner` so it can be tested without running `make check` (REQ-FIX-004) |
| `standup.sh` | Print project state: latest process-log, open ADRs, latest plan/review/roadmap/retrospect/handover, AGENTS.md size, active skills/hooks count, git state |

Add more scripts as the project grows: `smoke.sh`, `deploy.sh`, `release.sh`, etc. Each should be LLM-free and runnable in <5 seconds.
