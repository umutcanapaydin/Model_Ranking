# Web / API Security Baseline

> The single home for the web/API security baseline. Apply it to any service that exposes an
> HTTP/API surface. It is walked at Stage 0 (`docs/closure-checklist.md` §0) and by the release
> **Security review (Stage 5.1, BLOCKING before deploy)**, and referenced from `AGENTS.md` §5.
>
> **enforced-by: `scripts/bootstrap-check.sh` @ `docs/closure-checklist.md` §0**
>
> The cheap, grep-checkable parts (no default-admin / no plaintext creds, CORS allow-all with
> credentials, destructive defaults ON) are **BLOCKING at Stage 0 close** via `make bootstrap-check`
> legs C7, C9 and C10. **That script is NOT a leg of `make gate` and does not run in CI**, on purpose:
> it fails on unfilled placeholders, so wiring it into `make gate` would make every fresh install red
> on day one and teach the team that red means nothing. Its one caller is the Stage-0 checklist.

---

## The baseline (six items)

### 1. No plaintext credentials / no default-admin password — **GATE**

- **Rule:** credentials are **hashed from day one** (even in prototypes); there is **no hardcoded
  default-admin password** and **no plaintext credential** in source. Secrets come from the
  environment / a secrets manager, never an inline string literal.
- **Why a gate:** catastrophic, total blast radius, and cheaply grep-checkable: plaintext passwords
  and a literal default admin password have both shipped in real projects.
- **Enforcement (Stage 0 close, BLOCKING — not CI):** `make bootstrap-check` C7 fails on an obvious
  default-admin / plaintext-credential pattern in `src/`/`app/`/`server/`/... (a deliberately simple
  heuristic). The release Security review confirms hashing (e.g. bcrypt/argon2) on every credential store.
- **Fix shape:** read from `os.getenv` + a typed Settings object (seed K.2); hash with a vetted KDF;
  for an unavoidable bootstrap admin, force a first-login rotation and never ship a known default.

### 2. Server-side authz on every mutating route — guardrail

- **Rule:** **every mutating route enforces authentication + authorization server-side.** Client-side
  checks (hidden buttons, disabled fields, route guards in the SPA) are **UI sugar only** — assume
  the client is hostile and replays the raw request.
- **Why a guardrail, not a gate:** it is **not cheaply statically checkable per route** (you can't
  grep "is this route authorized?"). The cheap part — "an auth middleware/guard exists at all" — may
  be added to `bootstrap-check` as a warning if desired.
- **Review check (Stage 5.1):** enumerate every mutating route (POST/PUT/PATCH/DELETE) and name the
  server-side guard that protects it; a route with no server-side authz is BLOCKING.

### 3. CORS allowlist — never allow-all + credentials — guardrail

- **Rule:** in prod, restrict CORS to an **explicit origin allowlist**. **Never** ship
  `cors()` allow-all (`Access-Control-Allow-Origin: *`) **together with credentials**
  (`Access-Control-Allow-Credentials: true`) — that combination leaks authenticated responses to any
  origin.
- **Review check:** confirm the prod CORS config is an allowlist; flag any wildcard origin, and treat
  wildcard-origin + credentials as BLOCKING.
- **enforced-by: `scripts/bootstrap-check.sh` @ `docs/closure-checklist.md` §0** — leg `[C9]`. The
  check reads a +/-6-line window around each wildcard origin, because the multi-line
  `add_middleware(...)` form is what this actually looks like in the wild. A window that also holds a
  FALSY credentials flag is a `warn`, never a `fail`: a file may hold two CORS configurations, and a
  check that cannot tell them apart may report what it saw but may not block.

### 4. Validate security-critical config at startup; fail the prod process — guardrail

- **Rule:** validate **security-critical configuration at startup** (auth secrets present, CORS set,
  TLS/keys configured, `ENFORCE_PRODUCTION`-style flags consistent) and **fail the process in prod
  mode** if a required value is missing or invalid — never silently default to an insecure value
  (e.g. auth-off, empty key, `0`). Extends `bootstrap-check` and the L.6 boot guard / config-doctor.
- **Review check:** there is a startup validator; in prod it refuses to boot on a missing/invalid
  security-critical value, and it prints all problems at once (pairs with L.6).

### 5. Encrypt credentials / PII at rest with a rotation-friendly key chain — guardrail

- **Rule:** encrypt stored **credentials and PII at rest** using a **multi-key chain** designed for
  rotation: **decrypt tries all keys; encrypt uses the first (current) key.** This makes key rotation
  a config change, not a migration.
- **Review check:** stored secrets/PII are encrypted at rest; the key chain supports rotation
  (current-key-encrypts / any-key-decrypts); keys themselves are not committed (gitleaks + §6 of the
  permission matrix).

### 6. Generic client errors; log detail server-side — guardrail

- **Rule:** return **generic error messages to clients** (no stack traces, SQL, internal paths,
  or "user not found vs wrong password" oracles); log the detail **server-side** for debugging.
- **Review check:** error responses are generic; verbose detail is server-side only.

---

## Where this is enforced

| Item | Enforced / checked at |
|---|---|
| No default-admin / plaintext creds | **`make bootstrap-check` C7 (GATE)** + release Security review |
| Server-side authz on mutating routes | release Security review (Stage 5.1); `permission-matrix.md` §7 |
| CORS allowlist (no allow-all + creds) | **`make bootstrap-check` C9 (GATE)** + release Security review |
| Validate config at startup, fail prod | release Security review; pairs with L.6 |
| No destructive default ON | **`make bootstrap-check` C10 (GATE)** + release Security review |
| Encrypt creds/PII at rest (key chain) | release Security review; `permission-matrix.md` §6 |
| Generic client errors | release Security review |

## Control-class fail direction

Security controls have a fail direction. **Auth/safety controls fail CLOSED** (deny on error/timeout,
with a *tested* disable switch and correct domain scope); **fairness controls (rate-limit) fail OPEN**
(serve on limiter failure rather than block legitimate traffic). This paired rule lives in
`.agents/rules/practices.md` and `permission-matrix.md` §5; it is part of the release Security review.

## Invariants and wiring

- **"Built ≠ wired" (guardrail).** An implemented, unit-green control not attached to the live request path is an UNSHIPPED control. Phrase acceptance criteria end-to-end ("an exhausted tenant receives 402 on the live route"), make the citing test enter through the live entrypoint, and ask per control at the security review: "is this reachable from the request path?"
- **Negative test per security invariant (guardrail).** Keep the release's invariants list (deny-path resource release; tenant derived from the credential, never request params — IDOR; redaction). Each row cites the test that FAILS if the invariant is removed. Correct code without that test is one refactor from a silent hole.
- **Idempotency test pattern.** Same key, DIFFERENT payload, assert first-write-wins — re-sending the same payload passes even on a last-write-wins store.
- **Money (guardrail; only for projects handling money).** Integer minor units + currency end-to-end; round half-up exactly once at the boundary; the Money type raises on float; sweep money modules for float at the security review.
- **Sharpenings:** the fail-direction table (control → direction → switch → citing test) is reviewed at the security review and every disable switch is TESTED · deny-service enforcement defaults OFF-in-code/ON-in-prod-profile with a boot preflight that refuses enforce-ON on an unsafe datastore, failing loud · contract-test self-skips are reported, never silent.
- **Reporting principle.** Customer-facing progress artifacts stay separate from the internal truth tracker — internal risk debates never leak to the customer; reporting optimism never corrupts internal state.

## Semantic-security review items (the agent's pass on a HIGH wave)

- **What to look for (HIGH waves full, MED lightweight):** weakened/removed validation; broadened permissions or scopes; disabled or "temporarily" bypassed checks; debug flags left on; suspicious error-handling changes on auth paths.
- **No agent suppression:** agents may NEVER waive, baseline, or suppress a gitleaks/SCA/slopsquat finding — any suppression escalates to the owner immediately.
- **Diff-vs-plan sensitive-file flag:** any auth/crypto/secrets/CI-config/dependency-manifest file touched outside the wave's declared slice is hard-flagged.
- **⛔-glob mid-milestone ping:** a ⛔-zone touch notifies the owner async immediately (non-blocking); the line-by-line owner review still happens before the release deploys.

## Fixpacks — the anti-hotfix-bypass floor (Stage 6)

- **Every fixpack, unconditionally:** gitleaks + SCA; **full security-invariant negative suite
  green before deploy**; diff-scoped security read on the REACHABLE diff; ⛔-glob intersection →
  mechanical full HIGH review + owner line-by-line; built≠wired re-check on touched/mediating controls.
- **Exploitability triage at intake:** every prod bug flagged "attacker-relevant?" by the
  fresh-eyes reviewer (never the author); security-class → escalate-NOW + invariant negative test.
- **Emergency floor (never skipped at any urgency):** red repro test · secret scan · diff-scoped
  fresh-eyes read · ⛔ owner approval · the owner reviews and merges the fix + deploy · build-hash
  verify + fix probe. Deferred items → 48h retroactive full close (blocking debt). More than one
  emergency a month → process review.

## Outward-facing security

- **Diagnosable fail-closed, without an attacker oracle:** the operator-actionable
  reason (which dependency, which failure mode) goes to server-side structured logs + an
  AUTHENTICATED diagnostic endpoint ONLY; the unauthenticated response carries a generic status +
  opaque correlation ID. Acceptance: an operator distinguishes not-ready from dead in ≤1 command.
- **Producer enumeration is a SECURITY duty on auth/attribution-class invariants:**
  every producer of the invariant's inputs is a trust input; unenumerated = unaudited. Security
  signs the producer+citing-test list on ⛔-class invariants.
- **Journey-tester credential custody:** the `make journey` script mints its own short-TTL token at
  runtime from environment identity, under a dedicated least-privilege synthetic principal
  (filterable in audit logs); tokens memory-only; NEVER a stored secret; fails rather than falls
  back. The shipped boot path contains no default credentials or permissive fallbacks.

## A verifier may not share its implementation with what it verifies

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
