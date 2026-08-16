# Architecture — model_ranking

> What the system looks like + the contract with adjacent systems. Per seed A.2: treat PRD and architecture as **adversarial sources of truth** until proven consistent. §5 conflict table below.

---

## 1. System diagram

```
[ documented network sources ]          [ owner-fetched local Epoch bundle ]
  LiteLLM / OpenRouter / Arena             SWE-bench Verified / DeepSWE
              │                                          │
              └─────────────── [ src/app/clients/ ] ─────┘
                                      │ parse + validate + provenance
                                      ▼
                         [ src/app/workflows/ingest ]
                                      │ canonical registry + effort identity
                                      ▼
 [ curated plans.yaml + rosters.yaml ] → [ disposable SQLite working set ]
                                      │
                   ┌──────────────────┼───────────────────┐
                   ▼                  ▼                   ▼
        [ rank + CSV/JSON ]   [ coverage + health ]   [ recommend ]
            coding and          selected evidence      model or plan,
          agentic-coding          per plan             deterministic
                   └──────────────────┬───────────────────┘
                                      ▼
                              [ CLI consumers ]
```

Epoch acquisition is deliberately outside runtime HTTP: an owner fetches and unpacks the documented
bundle, then the allowlisted clients read local CSV files. `data/epoch-source.yaml` is the separate
90-day acquisition clock used by CI; board evaluation dates remain row-owned evidence.

## 2. Component responsibilities

| Component | Owns | Does not own |
|---|---|---|
| `src/app/adapter/` | HTTP surface: `/health`; future read-only rankings API | Business logic, persistence |
| `src/app/clients/` | Protocol-typed network clients plus local Epoch board readers and fakes | Cross-source ranking policy |
| `src/app/workflows/` | Ingest, registry, effort-aware ranking, plan coverage/health, model and subscription recommendation | External fetches, HTTP |
| `data/` | Curated plan/roster facts, owner-tunable thresholds, Epoch acquisition metadata | Benchmark evaluation dates |
| `src/app/workers/` | (M1: unused) future scheduled refresh | — |

## 3. Cross-cutting concerns

- **AuthN / AuthZ:** none in M1 (no mutating routes, no user data); revisit at the API milestone.
- **Logging/observability:** per-run source row/drop/conflict counts plus source and selected-plan
  freshness; no secrets or PII exist in the domain.
- **Tracing:** single-process pipeline; run-id stamped into export metadata.
- **Configuration:** pydantic-settings + .env (source URLs overridable for tests); K.2.
- **Error handling:** a failing source aborts ITS ingestion with a loud report; other sources proceed; partial runs are labeled partial (fairness-class fail OPEN, per V3C-33/45 this is not an auth control).
- **Schema evolution:** read paths stay migration-free. Operators explicitly run
  `python -m app.workflows.schema migrate --db PATH`; the command refuses missing/unusable files,
  preserves rows, and is idempotent.

## 4. Deployment topology

```
M1: no deploy. Local run (owner machine / CI job).
Later (OQ-3): scheduled ingestion job + read-only API + CDN-cached JSON,
candidate targets per research: Supabase or Cloudflare Workers.
```

## 5. PRD ↔ Architecture conflict table (seed A.2)

| # | Conflict | PRD says | Architecture says | Severity | Status (D-NNN) |
|---|---|---|---|---|---|
| 1 | API surface in M1 | §8: API serving out of scope | starter ships FastAPI adapter | LOW | resolved: adapter stays /health-only in M1 (D-100) |
| 2 | Persistence | §7: SQLite disposable | research suggests Postgres for prod | LOW | resolved: SQLite M1, Postgres re-evaluated at API milestone (D-100) |
| 3 | Source freshness | REQ-ING-003 flags Aider staleness | no scheduler exists in M1 | LOW | accepted: manual runs in M1; scheduler is a later milestone (OQ-1) |

## 6. Out of bounds for this architecture

- Multi-region / high-QPS serving — the dataset is tiny (<5MB); a CDN JSON file will outperform a database for reads.
- Running our own benchmark evaluations — we aggregate published results only.
- Any write path from end users (no accounts, no votes) until a dedicated milestone with its own security review.
