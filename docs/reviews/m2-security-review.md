# M2 Stage 4.0 — Security Review (fresh eyes, milestone closure, BLOCKING gate)
Reviewer: independent Security-Reviewer subagent. Date: 2026-08-11.

## VERDICT: PASS — 0 BLOCKING, 2 MINOR (both replica artifacts — device repo verified), 4 NOTE

M1 invariants 1-8: ALL HOLD (spot-checked by execution + grep). Invariant 8 amended:
documented endpoints 3 → 5 (adds datasets-server.huggingface.co/rows + openrouter.ai/api/v1/models,
both documented data APIs, D-101-compliant; arena.ai site never fetched).

NEW invariants:
- INV-9: Arena pagination bounded, never truncates silently — cap → SourceError; negative test
  test_arena_client.py::test_page_cap_exhaustion_fails_loudly
- INV-10: CI workflow least-privilege (contents:read, no secrets, dispatch+weekly-cron only,
  15-min timeout, quoted heredoc, no ${{ }} in run bodies) — enforcement = owner K.10 diff review
- INV-11: tests never disable TLS; respx transport-level mocks only (grep-verified)

MINOR-1 (.gitignore absent) + MINOR-2 (ci.yml absent): both were CONTAINER-REPLICA artifacts;
the device repo has .gitignore (incl. *.db, appended M1) and the starter ci.yml. Parity restored
in the replica; OWNER VERIFIES both files exist in the repo at the milestone commit.

NOTES: actions tag-pinned not SHA-pinned (carried TODO — pin before enabling cron live);
ArenaClient url param is provenance-only (fetch target is a module constant — security-positive,
API-misleading; M3 cleanup candidate); f-string url never fetched (real request uses encoded
params=); head-pipe verified safe with pipefail.

## Owner K.10 checklist at milestone commit
1. Read contract-tests.yml in full (entire file NEW) — permissions/triggers/no-secrets as diffed.
2. Confirm .gitignore (*.db) and ci.yml present in repo; no *.db staged.
3. SHA-pin checkout/setup-python before the weekly cron goes live (in-file TODOs).
