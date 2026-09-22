# Web / API Security Baseline (Pipeline)

> ** (..13/51/56).** GP's inherited security posture was abstract and backend-Python
> (the permission-matrix catastrophe-class, gitleaks, pip-audit). makes it **concrete and
> web/API-facing**, because the harvest's two ad-hoc projects (Project-I, Project-H) independently
> re-derived these gates the hard way, and a mature gateway (Project-C) shipped a literal default
> admin password. This file is the single home for the web/API security baseline. It is referenced
> from `docs/closure-checklist.md` §0 and `AGENTS.md` §5, and the cheap, grep-checkable part
> (no default-admin / no plaintext creds) is **BLOCKING at Stage 0 close** via `make bootstrap-check`
> C7.
>
> **enforced-by: `scripts/bootstrap-check.sh` @ `docs/closure-checklist.md` §0**
>
> **It is NOT a leg of `make gate` and does not run in CI, and this sentence used to imply it did.**
> Three council seats found that independently (condition): the table below
> said **GATE** in bold for a script with no caller anywhere. The control was never missing — its
> home is the Stage-0 checklist, which has required it since FB-1 — but the word "enforced" without
> a place is the failure class this release adopted a rule about. It stays at Stage 0 on purpose:
> `bootstrap-check` fails on unfilled placeholders, so wiring it into `make gate` would make every
> fresh export red on day one and teach the team that red means nothing.
>
> Apply this baseline to any service that exposes an HTTP/API surface. The closure **Security
> review (Stage 4.0, BLOCKING before deploy)** walks it.

---

## The baseline (six items)

### 1. No plaintext credentials / no default-admin password — **GATE **

- **Rule:** credentials are **hashed from day one** (even in prototypes); there is **no hardcoded
 default-admin password** and **no plaintext credential** in source. Secrets come from the
 environment / a secrets manager, never an inline string literal.
- **Why a gate:** catastrophic and cheaply grep-checkable. Project-I shipped plaintext passwords;
 Project-C shipped a hardcoded default admin password (catastrophic, total blast radius).
- **Enforcement (Stage 0 close, BLOCKING — not CI):** `make bootstrap-check` C7 fails on an obvious default-admin / plaintext-credential
 pattern in `src/`/`app/`/`server/`/... (a deliberately simple heuristic). The closure Security
 review confirms hashing (e.g. bcrypt/argon2) on every credential store.
- **Fix shape:** read from `os.getenv` + a typed Settings object (seed K.2); hash with a vetted KDF;
 for an unavoidable bootstrap admin, force a first-login rotation and never ship a known default.

### 2. Server-side authz on every mutating route — guardrail 

- **Rule:every mutating route enforces authentication + authorization server-side.** Client-side
 checks (hidden buttons, disabled fields, route guards in the SPA) are **UI sugar only** — assume
 the client is hostile and replays the raw request.
- **Why a guardrail, not a gate:** the council found it is **not cheaply statically checkable
 per-route** (you can't grep "is this route authorized?"). The cheap part — "an auth
 middleware/guard exists at all" — may be added to `bootstrap-check` as a warning if desired.
- **Origin:** Project-I F2 (catastrophic — client-only auth).
- **Review check (Stage 4.0):** enumerate every mutating route (POST/PUT/PATCH/DELETE) and name the
 server-side guard that protects it; a route with no server-side authz is BLOCKING.

### 3. CORS allowlist — never allow-all + credentials — guardrail 

- **Rule:** in prod, restrict CORS to an **explicit origin allowlist**. **Never** ship
 `cors` allow-all (`Access-Control-Allow-Origin: *`) **together with credentials**
 (`Access-Control-Allow-Credentials: true`) — that combination leaks authenticated responses to any
 origin.
- **Origin:** Project-I F6 + Project-C F13 (two ecosystems).
- **Review check:** confirm the prod CORS config is an allowlist; flag any wildcard origin, and treat
 wildcard-origin + credentials as BLOCKING.
- **enforced-by: `scripts/bootstrap-check.sh` @ `docs/closure-checklist.md` §0** — leg `[C9]`, v6.0. For eight cuts this rule was prose
 and nothing else, and two corpus projects shipped the exact combination it names; one of them had
 the rule written down. The gate reads a +/-6-line window around each wildcard origin, because the
 multi-line `add_middleware` form is what this actually looks like in the wild. A window that
 also holds a FALSY credentials flag is a `warn`, never a `fail`: a file may hold two CORS
 configurations, and a check that cannot tell them apart may report what it saw but may not block.

### 4. Validate security-critical config at startup; fail the prod process — guardrail 

- **Rule:** validate **security-critical configuration at startup** (auth secrets present, CORS set,
 TLS/keys configured, `ENFORCE_PRODUCTION`-style flags consistent) and **fail the process in prod
 mode** if a required value is missing or invalid — never silently default to an insecure value
 (e.g. auth-off, empty key, `0`). Extends `bootstrap-check` and Theme L's L.6 boot guard / config-doctor.
- **Origin:** Project-F F9 (startup config validation) + Project-C F15 (fail loud on parse error, never
 silently default to zero).
- **Review check:** there is a startup validator; in prod it refuses to boot on a missing/invalid
 security-critical value, and it prints all problems at once (pairs with L.6).

### 5. Encrypt credentials / PII at rest with a rotation-friendly key chain — guardrail 

- **Rule:** encrypt stored **credentials and PII at rest** using a **multi-key chain** designed for
 rotation: **decrypt tries all keys; encrypt uses the first (current) key.** This makes key rotation
 a config change, not a migration.
- **Origin:** Project-F F7 + Project-C F11 (plaintext upstream creds = total-blast-radius breach; 2 ecosystems).
- **Review check:** stored secrets/PII are encrypted at rest; the key chain supports rotation
 (current-key-encrypts / any-key-decrypts); keys themselves are not committed (gitleaks + §6 of the
 permission matrix).

### 6. Generic client errors; log detail server-side — guardrail

- **Rule:** return **generic error messages to clients** (no stack traces, SQL, internal paths,
 or "user not found vs wrong password" oracles); log the detail **server-side** for debugging.
- **Origin:** Project-I F10 (no stack/internal leak).
- **Review check:** error responses are generic; verbose detail is server-side only.

---

## Where this is enforced

| Item | Enforced / checked at |
|---|---|
| no default-admin / plaintext creds | **`make bootstrap-check` C7 (GATE)** + closure Security review |
| server-side authz on mutating routes | closure Security review (Stage 4.0); `permission-matrix.md` §7 |
| CORS allowlist (no allow-all + creds) | **`make bootstrap-check` C9 (GATE)** + closure Security review |
| validate config at startup, fail prod | closure Security review; pairs with Theme L L.6 |
| no destructive default ON | **`make bootstrap-check` C10 (GATE)** + closure Security review |
| encrypt creds/PII at rest (key chain) | closure Security review; `permission-matrix.md` §6 |
| Generic client errors | closure Security review |

## Control-class fail direction (cross-reference)

Security controls have a fail direction. **Auth/safety controls fail CLOSED** (deny on error/timeout,
with a *tested* disable switch and correct domain scope); **fairness controls (rate-limit) fail OPEN**
(serve on limiter failure rather than block legitimate traffic). This paired rule lives in
`.agents/rules/practices.md` and `permission-matrix.md` §5; it is part of the closure Security review.

## additions (first GP-v3 field run — Project-B, 2026-07-03)

- **"built ≠ wired" guardrail .:** An implemented, unit-green control not attached to the live request path is an UNSHIPPED control. Phrase acceptance criteria end-to-end ("an exhausted tenant receives 402 on the live route"), make the citing test enter through the live entrypoint, and ask per control at security close: "is this reachable from the request path?"
- **Negative test per security invariant guardrail .:** Keep a per-milestone invariants list (deny-path resource release; tenant derived from the credential, never request params — IDOR; redaction). Each row cites the test that FAILS if the invariant is removed. Correct code without that test is one refactor from a silent hole.
- **Idempotency test pattern doc .:** Same key, DIFFERENT payload, assert first-write-wins — re-sending the same payload passes even on a last-write-wins store.
- **Money guardrail; only for projects handling money .:** Integer minor units + currency end-to-end; round half-up exactly once at the boundary; the Money type raises on float; sweep money modules for float at security close.
- **Sharpenings (adopts, field-validated):** the fail-direction table (control → direction → switch → citing test) is reviewed at security close and every disable switch is TESTED · deny-service enforcement defaults OFF-in-code/ON-in-prod-profile with a boot preflight that refuses enforce-ON on an unsafe datastore, failing loud · contract-test self-skips are reported at closure, never silent.
- **Reporting principle (doc).** Customer-facing progress artifacts stay separate from the internal truth tracker — internal risk debates never leak to the customer; reporting optimism never corrupts internal state.

## additions (A0.5 — the owner leaves the wave loop, 2026-07-05)

- **Semantic-security review items (agent pass; HIGH waves full, MED lightweight):** weakened/removed validation; broadened permissions or scopes; disabled or "temporarily" bypassed checks; debug flags left on; suspicious error-handling changes on auth paths. These were implicitly covered by the owner's wave-level eyes — now explicit.
- **No agent suppression:** agents may NEVER waive, baseline, or suppress a gitleaks/SCA/slopsquat finding — any suppression escalates to the owner immediately.
- **Diff-vs-plan sensitive-file flag:** any auth/crypto/secrets/CI-config/dependency-manifest file touched outside the wave's declared slice is hard-flagged.
- **⛔-glob mid-milestone ping:** a ⛔-zone touch notifies the owner async immediately (non-blocking); the line-by-line owner review still happens before deploy at closure.

## additions (Stage 5 fixpacks — the anti-hotfix-bypass floor, 2026-07-17)

- **Every fixpack, unconditionally:** gitleaks + SCA; **full security-invariant negative suite
 green before deploy**; diff-scoped security read on the REACHABLE diff; ⛔-glob intersection →
 mechanical full HIGH review + owner line-by-line; built≠wired re-check on touched/mediating controls.
- **Exploitability triage at intake:** every prod bug flagged "attacker-relevant?" by the
 fresh-eyes reviewer (never the author); security-class → escalate-NOW + invariant negative test.
- **Emergency floor (never skipped at any urgency):** red repro test · secret scan · diff-scoped
 fresh-eyes read · ⛔ owner approval · owner commit + deploy · build-hash verify + fix probe.
 Deferred items → 48h retroactive full close (blocking debt). >1 emergency/month → process review.

## additions (post-prod dataset — outward-facing security, 2026-07-27)

- **Diagnosable fail-closed, without an attacker oracle :** the operator-actionable
 reason (which dependency, which failure mode) goes to server-side structured logs + an
 AUTHENTICATED diagnostic endpoint ONLY; the unauthenticated response carries a generic status +
 opaque correlation ID. Acceptance: an operator distinguishes not-ready from dead in ≤1 command.
- **Producer enumeration is a SECURITY duty on auth/attribution-class invariants :**
 every producer of the invariant's inputs is a trust input; unenumerated = unaudited. Security
 signs the producer+citing-test list on ⛔-class invariants.
- **Journey-tester credential custody :** the script mints its own short-TTL token at
 runtime from environment identity, under a dedicated least-privilege synthetic principal
 (filterable in audit logs); tokens memory-only; NEVER a stored secret; fails rather than falls
 back. The shipped boot path contains no default credentials or permissive fallbacks (rider).

## Not in scope here (deferred — Agent-Native / LLM-Ops candidate theme)

Gateway/LLM-ops security candidates (circuit-breaker tri-state, classify-by-stable-signal, streaming
rate-limit accounting, etc.) are CANDIDATE pending a 2nd independent ecosystem — see
[`METHODOLOGY.md`](METHODOLOGY.md) §3.6 and the candidate block in `.agents/rules/playbook-seeds.md`.

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
