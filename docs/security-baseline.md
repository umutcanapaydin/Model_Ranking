# Web / API Security Baseline (Pipeline v3)

> **NEW in v3 (V3C-11..13/51/56).** GP's inherited security posture was abstract and backend-Python
> (the permission-matrix catastrophe-class, gitleaks, pip-audit). v3 makes it **concrete and
> web/API-facing**, because the v3 harvest's two ad-hoc projects (Reimbursement-App, Poyraz-Dekorasyon) independently
> re-derived these gates the hard way, and a mature gateway (one-api) shipped a literal default
> admin password. This file is the single home for the web/API security baseline. It is referenced
> from `docs/closure-checklist.md` §0 and `AGENTS.md` §5, and the cheap, grep-checkable part
> (no default-admin / no plaintext creds) is enforced by `scripts/bootstrap-check.sh` (C7 / V3C-11).
>
> Apply this baseline to any service that exposes an HTTP/API surface. The closure **Security
> review (Stage 4.0, BLOCKING before deploy)** walks it.

---

## The baseline (six items)

### 1. No plaintext credentials / no default-admin password — **GATE (V3C-11)**

- **Rule:** credentials are **hashed from day one** (even in prototypes); there is **no hardcoded
  default-admin password** and **no plaintext credential** in source. Secrets come from the
  environment / a secrets manager, never an inline string literal.
- **Why a gate:** catastrophic and cheaply grep-checkable. Reimbursement-App shipped plaintext passwords;
  one-api shipped a hardcoded default admin password (catastrophic, total blast radius).
- **Enforcement:** `make bootstrap-check` C7 fails on an obvious default-admin / plaintext-credential
  pattern in `src/`/`app/`/`server/`/... (a deliberately simple heuristic). The closure Security
  review confirms hashing (e.g. bcrypt/argon2) on every credential store.
- **Fix shape:** read from `os.getenv` + a typed Settings object (seed K.2); hash with a vetted KDF;
  for an unavoidable bootstrap admin, force a first-login rotation and never ship a known default.

### 2. Server-side authz on every mutating route — guardrail (V3C-12)

- **Rule:** **every mutating route enforces authentication + authorization server-side.** Client-side
  checks (hidden buttons, disabled fields, route guards in the SPA) are **UI sugar only** — assume
  the client is hostile and replays the raw request.
- **Why a guardrail, not a gate:** the council found it is **not cheaply statically checkable
  per-route** (you can't grep "is this route authorized?"). The cheap part — "an auth
  middleware/guard exists at all" — may be added to `bootstrap-check` as a warning if desired.
- **Origin:** Reimbursement-App F2 (catastrophic — client-only auth).
- **Review check (Stage 4.0):** enumerate every mutating route (POST/PUT/PATCH/DELETE) and name the
  server-side guard that protects it; a route with no server-side authz is BLOCKING.

### 3. CORS allowlist — never allow-all + credentials — guardrail (V3C-13)

- **Rule:** in prod, restrict CORS to an **explicit origin allowlist**. **Never** ship
  `cors()` allow-all (`Access-Control-Allow-Origin: *`) **together with credentials**
  (`Access-Control-Allow-Credentials: true`) — that combination leaks authenticated responses to any
  origin.
- **Origin:** Reimbursement-App F6 + one-api F13 (two ecosystems).
- **Review check:** confirm the prod CORS config is an allowlist; flag any wildcard origin, and treat
  wildcard-origin + credentials as BLOCKING.

### 4. Validate security-critical config at startup; fail the prod process — guardrail (V3C-51)

- **Rule:** validate **security-critical configuration at startup** (auth secrets present, CORS set,
  TLS/keys configured, `ENFORCE_PRODUCTION`-style flags consistent) and **fail the process in prod
  mode** if a required value is missing or invalid — never silently default to an insecure value
  (e.g. auth-off, empty key, `0`). Extends `bootstrap-check` and Theme L's L.6 boot guard / config-doctor.
- **Origin:** BotIm-AOP F9 (startup config validation) + one-api F15 (fail loud on parse error, never
  silently default to zero).
- **Review check:** there is a startup validator; in prod it refuses to boot on a missing/invalid
  security-critical value, and it prints all problems at once (pairs with L.6).

### 5. Encrypt credentials / PII at rest with a rotation-friendly key chain — guardrail (V3C-56)

- **Rule:** encrypt stored **credentials and PII at rest** using a **multi-key chain** designed for
  rotation: **decrypt tries all keys; encrypt uses the first (current) key.** This makes key rotation
  a config change, not a migration.
- **Origin:** BotIm-AOP F7 + one-api F11 (plaintext upstream creds = total-blast-radius breach; 2 ecosystems).
- **Review check:** stored secrets/PII are encrypted at rest; the key chain supports rotation
  (current-key-encrypts / any-key-decrypts); keys themselves are not committed (gitleaks + §6 of the
  permission matrix).

### 6. Generic client errors; log detail server-side — guardrail

- **Rule:** return **generic error messages to clients** (no stack traces, SQL, internal paths,
  or "user not found vs wrong password" oracles); log the detail **server-side** for debugging.
- **Origin:** Reimbursement-App F10 (no stack/internal leak).
- **Review check:** error responses are generic; verbose detail is server-side only.

---

## Where this is enforced

| Item | Enforced / checked at |
|---|---|
| V3C-11 no default-admin / plaintext creds | **`make bootstrap-check` C7 (GATE)** + closure Security review |
| V3C-12 server-side authz on mutating routes | closure Security review (Stage 4.0); `permission-matrix.md` §7 |
| V3C-13 CORS allowlist (no allow-all + creds) | closure Security review; `.agents/rules/practices.md` |
| V3C-51 validate config at startup, fail prod | closure Security review; pairs with Theme L L.6 |
| V3C-56 encrypt creds/PII at rest (key chain) | closure Security review; `permission-matrix.md` §6 |
| Generic client errors | closure Security review |

## Control-class fail direction (cross-reference, V3C-33/45)

Security controls have a fail direction. **Auth/safety controls fail CLOSED** (deny on error/timeout,
with a *tested* disable switch and correct domain scope); **fairness controls (rate-limit) fail OPEN**
(serve on limiter failure rather than block legitimate traffic). This paired rule lives in
`.agents/rules/practices.md` and `permission-matrix.md` §5; it is part of the closure Security review.

## v3.1 additions (first GP-v3 field run — hcs_maas_vib, 2026-07-03)

- **V3C-73 — "built ≠ wired" (guardrail).** An implemented, unit-green control not attached to the live request path is an UNSHIPPED control. Phrase acceptance criteria end-to-end ("an exhausted tenant receives 402 on the live route"), make the V3C-02 citing test enter through the live entrypoint, and ask per control at security close: "is this reachable from the request path?"
- **V3C-74 — negative test per security invariant (guardrail).** Keep a per-milestone invariants list (deny-path resource release; tenant derived from the credential, never request params — IDOR; redaction). Each row cites the test that FAILS if the invariant is removed. Correct code without that test is one refactor from a silent hole.
- **V3C-75 — idempotency test pattern (doc).** Same key, DIFFERENT payload, assert first-write-wins — re-sending the same payload passes even on a last-write-wins store.
- **V3C-77 — money (guardrail; only for projects handling money).** Integer minor units + currency end-to-end; round half-up exactly once at the boundary; the Money type raises on float; sweep money modules for float at security close.
- **Sharpenings (v3 adopts, field-validated):** the V3C-33/45 fail-direction table (control → direction → switch → citing test) is reviewed at security close and every disable switch is TESTED · deny-service enforcement defaults OFF-in-code/ON-in-prod-profile with a boot preflight that refuses enforce-ON on an unsafe datastore, failing loud (V3C-53) · contract-test self-skips are reported at closure, never silent (V3C-44).
- **Reporting principle (V3C-80, doc).** Customer-facing progress artifacts stay separate from the internal truth tracker — internal risk debates never leak to the customer; reporting optimism never corrupts internal state.

## v3.3 additions (OD-4/A0.5 — the owner leaves the wave loop, 2026-07-05)

- **Semantic-security review items (agent pass; HIGH waves full, MED lightweight):** weakened/removed validation; broadened permissions or scopes; disabled or "temporarily" bypassed checks; debug flags left on; suspicious error-handling changes on auth paths. These were implicitly covered by the owner's wave-level eyes — now explicit.
- **No agent suppression:** agents may NEVER waive, baseline, or suppress a gitleaks/SCA/slopsquat finding — any suppression escalates to the owner immediately.
- **Diff-vs-plan sensitive-file flag:** any auth/crypto/secrets/CI-config/dependency-manifest file touched outside the wave's declared slice is hard-flagged.
- **⛔-glob mid-milestone ping:** a ⛔-zone touch notifies the owner async immediately (non-blocking); the line-by-line owner review still happens before deploy at closure.

## v3.4 additions (Stage 5 fixpacks — the anti-hotfix-bypass floor, 2026-07-17)

- **Every fixpack, unconditionally:** gitleaks + SCA; **full security-invariant negative suite
  green before deploy**; diff-scoped security read on the REACHABLE diff; ⛔-glob intersection →
  mechanical full HIGH review + owner line-by-line; built≠wired re-check on touched/mediating controls.
- **Exploitability triage at intake:** every prod bug flagged "attacker-relevant?" by the
  fresh-eyes reviewer (never the author); security-class → escalate-NOW + invariant negative test.
- **Emergency floor (never skipped at any urgency):** red repro test · secret scan · diff-scoped
  fresh-eyes read · ⛔ owner approval · owner commit + deploy · build-hash verify + fix probe.
  Deferred items → 48h retroactive full close (blocking debt). >1 emergency/month → process review.

## v3.5 additions (post-prod dataset — outward-facing security, 2026-07-27)

- **Diagnosable fail-closed, without an attacker oracle (V3C-103):** the operator-actionable
  reason (which dependency, which failure mode) goes to server-side structured logs + an
  AUTHENTICATED diagnostic endpoint ONLY; the unauthenticated response carries a generic status +
  opaque correlation ID. Acceptance: an operator distinguishes not-ready from dead in ≤1 command.
- **Producer enumeration is a SECURITY duty on auth/attribution-class invariants (V3C-101):**
  every producer of the invariant's inputs is a trust input; unenumerated = unaudited. Security
  signs the producer+citing-test list on ⛔-class invariants.
- **Journey-tester credential custody (V3C-106):** the script mints its own short-TTL token at
  runtime from environment identity, under a dedicated least-privilege synthetic principal
  (filterable in audit logs); tokens memory-only; NEVER a stored secret; fails rather than falls
  back. The shipped boot path contains no default credentials or permissive fallbacks (V3C-99 rider).

## Not in scope here (deferred — Agent-Native / LLM-Ops candidate theme)

Gateway/LLM-ops security candidates (circuit-breaker tri-state, classify-by-stable-signal, streaming
rate-limit accounting, etc.) are CANDIDATE pending a 2nd independent ecosystem — see
[`pipeline-design.md`](https://github.com/SADCAIVibe/General_Pipeline/blob/v5.0/general_pipeline_v5.0/pipeline-design.md) §3.6 and the candidate block in `.agents/rules/playbook-seeds.md`.

## A verifier may not share its implementation with what it verifies (V4C-61, v4.3)

**Measured, in a customer-facing console.** `store.js` minted an audit hash chain with a function its
own comment called *"demo-grade"*, then **"verified" the chain with the same function**, and printed a
green `PASS`. The verifier and the prover shared **both the implementation and the state** (browser
storage, editable by the party being audited). No stronger hash fixes that — it is tautological at any
key length.

**The rule.** A verification path may not share an implementation with the production path it
verifies, and **a client may never be the verifier of record.** Withdrawal fixes an instance; this
fixes the class.

**Corollary, binding:** audit-chain integrity may not be claimed — demo or live — until a
**server-side** chain exists for a client to *display* and never to compute or self-check.
