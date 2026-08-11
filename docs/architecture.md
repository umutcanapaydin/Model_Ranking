# Architecture — model_ranking

> What the system looks like + the contract with adjacent systems. Per seed A.2: treat PRD and architecture as **adversarial sources of truth** until proven consistent. §5 conflict table below.

---

## 1. System diagram

```
[ GitHub raw data endpoints ]          (LiteLLM pricing / SWE-bench JSON / Aider YAML)
        │  scheduled or manual fetch (httpx, no scraping — D-101)
        ▼
[ src/app/clients/ ]   ── Protocol-typed source clients (D-001); one fake per client for tests
        ▼
[ src/app/workflows/ingest ]  ── parse → validate → canonicalize aliases (REQ-CAN) → provenance stamp
        ▼
[ SQLite (M1) ]        ── models / pricing / scores / px_median tables; disposable, rebuildable
        ▼
[ src/app/workflows/rank ]    ── coding ranking + median prices + CSV/JSON export (REQ-RANK)
        ▼
[ src/app/workflows/recommend ] ── deterministic 3-answer engine (REQ-REC, D-104)
        ▼
[ src/app/adapter/ ]   ── FastAPI: /health (L.7) only in M1; ranking/recommend endpoints in a later milestone
        ▼
[ future iOS app / CLI consumers ]
```

## 2. Component responsibilities

| Component | Owns | Does not own |
|---|---|---|
| `src/app/adapter/` | HTTP surface: `/health` (M1); future read-only rankings API | Business logic, persistence |
| `src/app/clients/` | Source fetch Protocols (LiteLLM, SWE-bench, Aider) + fakes (D-001 / K.1) | Parsing rules, scoring |
| `src/app/workflows/` | Ingest, canonical registry, ranking, recommendation logic | External fetches, HTTP |
| `src/app/workers/` | (M1: unused) future scheduled refresh | — |

## 3. Cross-cutting concerns

- **AuthN / AuthZ:** none in M1 (no mutating routes, no user data); revisit at the API milestone.
- **Logging:** JSON via structlog; per-run source row/drop counts; no secrets, no PII exists in domain.
- **Tracing:** single-process pipeline; run-id stamped into export metadata.
- **Configuration:** pydantic-settings + .env (source URLs overridable for tests); K.2.
- **Error handling:** a failing source aborts ITS ingestion with a loud report; other sources proceed; partial runs are labeled partial (fairness-class fail OPEN, per V3C-33/45 this is not an auth control).

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
