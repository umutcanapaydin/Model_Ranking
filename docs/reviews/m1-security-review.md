# M1 Stage 4.0 — Security Review (fresh eyes, milestone closure, BLOCKING gate)
Reviewer: independent Security-Reviewer subagent. Date: 2026-08-11.

## VERDICT: PASS — 0 BLOCKING, 2 MINOR (closed same-session), 2 NOTE (1 closed)

Baseline walk (10 items): secrets=PASS (no keys, only APP_BUILD env read) · default-admin=N/A ·
untrusted payloads=PASS (yaml.safe_load/json.loads, no eval/exec/pickle, typed field checks) ·
SQLi=PASS (parametrized everywhere; single f-string identifier allowlist-gated + negative test) ·
subprocess=PASS (list args, no shell, timeout) · HTTP=PASS (30s timeout, HTTPS constants, no creds)
· deps=PASS (canonical names, floor pins, pip-audit in dev) · paths=PASS (local CLI context) ·
fail-direction=PASS (typed excepts, loud SourceError, rollback keeps old set) · licensing=PASS
(exactly 3 documented raw endpoints; no scraping; no Artificial Analysis).

MINOR-1 unused deps (structlog/orjson/pydantic-settings) → moved to "planned" comment in pyproject.
MINOR-2 .gitignore lacked *.db before owner git init → appended (*.db, *.sqlite3).
NOTE connect-outside-try in CLI → moved inside try (exit-2 contract holds for unopenable paths).
NOTE follow_redirects w/o scheme pin → accepted (no credentials attached); optional M2 hardening.

## Security invariants (each with its negative test)
1. Remote payloads are inert data (yaml.safe_load/json.loads) — invalid-payload tests both parsers
2. SQL parametrized; sole interpolated identifier allowlist-gated — test_reset_source_rejects_unknown_table
3. Every request: 30s timeout + fixed HTTPS constant + no creds — respx 500/ConnectError tests
4. Failing source aborts loud+closed; old working set survives rollback — rollback/propagation tests
5. Missing/zero/bool prices-scores skipped, never zeroed — parser edge tests + schema CHECKs
6. Default suite zero-network; live tests env-gated — pytestmark skipif
7. CLI structured errors, distinct exit codes (0/1/2) — corrupt-db / invalid-budget / no-match tests
8. Only 3 documented endpoints, no scraping (D-101) — RawSource boundary + review grep

Test-integrity: no test weakens an invariant; no TLS-verify bypass anywhere.
