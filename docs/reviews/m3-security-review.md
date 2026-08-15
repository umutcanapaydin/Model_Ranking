---
record_type: ratification
id: m3-security-review
status: ratified
date: 2026-08-15
---

# M3 Stage 4.0 — Security Review (fresh eyes, milestone closure, BLOCKING gate)
Reviewer: independent Security-Reviewer subagent. Date: 2026-08-15. Surface: d703a77..1b61429 (W1-W3). Risk tier: LOW (m3-plan §risks).

## VERDICT: PASS — 0 BLOCKING, 2 MINOR (owner action at this closure), 3 NOTE

## Invariants INV-1..11: ALL HOLD (spot-checked by grep + execution)
- INV-1 inert payloads: only `yaml.safe_load` (plans.py:134); zero `yaml.load`/`Loader=`/`eval`/`exec`/`pickle` in src+tests (grep).
- INV-2 parameterized SQL: bandit -r src = 1 Medium, the KNOWN allowlist-gated identifier (schema.py:150, negative test tests/unit/test_schema.py:54); all M3 SQL (plans.py, subscribe.py, registry.py) uses `?` placeholders — curated `limits`/`source_url` strings never reach SQL text.
- INV-4 rollback fail-closed: verified by fault injection this review — injected IntegrityError after DELETE; old plans row AND old plan_config survived (`with conn:` at plans.py:178).
- INV-5 schema CHECKs: plans/plan_config CHECKs (schema.py:63,72-75) + SQLite-layer negative test tests/unit/test_plans_ingest.py:198.
- INV-6 network-free default suite: tests/unit uses respx mocks only; all live tests skipif RUN_CONTRACT_TESTS!=1 (tests/integration/*:14). No new unit test does outbound HTTP.
- INV-8 endpoints: no new fetch target — plans are curated in-repo (zero network); ArenaClient `url=` param removed (arena.py:59, M2 NOTE cleanup, security-positive).
- INV-9 executed: test_arena_client.py::test_rows_fallback_page_cap_exhaustion_fails_loudly PASSES.
- INV-10: ci.yml:18, contract-tests.yml:24, governance-contract.yml:29 all `contents: read`; plan-staleness job UNCONDITIONAL (no `if:`, no `continue-on-error`); no `${{ }}` in any run body; no `pull_request_target` anywhere (grep). See NOTE-3 on issue-agent.yml.
- INV-11 executed: grep `verify=False|trust_env|ssl._create` across repo = zero hits. Full unit suite: 141 passed.

## New M3 surface
- Parser fails loud on every field (plans.py:40-124); staleness_days/budget caps required as data; https-only source_url (plans.py:66); the shipped data/plans.yaml carries only 4 provider pricing-page URLs.
- SHA pins verified via `git ls-remote` (2026-08-15): checkout 11d5960a=v4.4.0, 08c6903c=v5.0.0 (governance); setup-python a26af69b=v5.6.0; gitleaks-action ff98106e=v2.3.9. Every comment claim matches upstream.
- Secrets in workflows: only pre-existing `secrets.GITHUB_TOKEN` (ci.yml:50) + dormant issue-agent keys; NO secret referenced in the new M3 jobs.

### MINOR
- docs/warnings.ledger.md:11 — gitleaks now reports 2 findings, not the recorded 1: the W-001 ledger row itself quoted the trigger prose verbatim (the ADR compliance label after the word "APIs") and re-tripped `generic-api-key` (commit d703a77, M3-W0). Same zero-entropy false-positive class, NOT a secret — but it is UNLEDGERED. Escalated (agents never waive scanner findings): add a W-002 row; the W-001 remedy (scoped `.gitleaks.toml` allowlist for the `D-\d+` label pattern, owner decision) closes both. W-001 row verified present, status ESCALATED, owner M3.
- .github/workflows/issue-agent.yml:44 — `anthropics/claude-code-action@v1` is the ONE unpinned action (mutable tag) in a workflow holding ANTHROPIC_API_KEY + `contents: write`. Carried in-file TODO since M1; workflow dormant (labels + secret not provisioned). Owner MUST SHA-pin before provisioning the secret/labels.

### NOTE
1. plans mid-transaction rollback has no in-repo citing test — tests/unit/test_plans_ingest.py:133 fails at PARSE (DB untouched). Verified correct here by fault injection; commit the IntegrityError-injection test (mirror tests/unit/test_litellm_ingest.py:85) to ratify INV-12.
2. V4C-49 gap: M3-W3 pinned SHAs but shipped no grep gate banning `uses: *@vN` refs; enforcement today = owner K.10 diff review. Add the gate (e.g. in governance-contract.yml) before ratifying INV-14.
3. issue-agent.yml:24-27 is `contents: write` by documented Layer-2 design (label-gated, draft-PR-only, unchanged in M3 except the checkout pin). Restate INV-10 as "the 3 CI workflows read-only; issue-agent write-scoped by design".

## Allowlist spot-check (3 of 17): src/app/workflows/subscribe.py — Turkish confined to user-facing output strings (lines 168-236), matches reason; pyproject.toml:45 — allowed-confusables glyph list, functional, matches; docs/closure-report-m1.md — pre-V4C-79 ratified record, matches. Every entry carries a reason.

## New invariants proposed
- INV-12 curated-data loud-fail + atomic replace: invalid doc aborts at parse before any delete; mid-transaction violation rolls back the whole set incl. plan_config. Tests: tests/unit/test_plans_ingest.py:75,89,133,213 (parse-time) — mid-transaction citing test PENDING (NOTE-1).
- INV-13 staleness fails toward disclosure: corrupt DB date raises SourceError, never renders fresh (plans.py:249); missing staleness_days fails parse. Negative tests: tests/unit/test_plans_staleness.py:102, tests/unit/test_plans_ingest.py:102.
- INV-14 workflow actions SHA-pinned to ls-remote-verified tags; exception ledgered (MINOR-2). Automated negative test: NONE yet (NOTE-2) — ratify only with the grep gate.

## Owner K.10 checklist at milestone commit
1. Decide the scoped gitleaks allowlist (closes W-001 + new W-002); ledger W-002 either way.
2. SHA-pin claude-code-action@v1 before provisioning ANTHROPIC_API_KEY/labels.
3. Commit the mid-transaction rollback test + the unpinned-`uses:` grep gate (ratifies INV-12/INV-14).
