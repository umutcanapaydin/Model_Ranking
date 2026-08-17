# Wave 3 Security Review (m6)

**Reviewer:** Security-Reviewer subagent (plan-tagged pulled-forward pass, V3C-68 / F15)
**Date:** 2026-08-17
**Risk tier:** HIGH (schema migration — auto-escalated per V3C-78; the plan also names untrusted-input parsing and a network-facing security config)
**Source:** A (baseline profile, `subagent-profiles/Security-Reviewer.md`)
**Scope:** `git diff 67fd92b..HEAD` — `afcae35`, `915e97b`. The reviewer authored none of this code.

## Verdict

**BLOCKING** — 2 blocking, 3 minor, 5 notes.

Both blocking findings are the same shape and it is the shape this pass exists to catch: **a control
that was written, unit-tested, checklisted, and never attached to the path it protects.** One is the
startup validator, which no process calls. The other is the YAML guard, which was installed on the
three inputs that have no untrusted producer and left off the one that does.

---

## Findings

### BLOCKING

#### BLOCKING-1 — `src/app/adapter/main.py:115` — `validate_startup_config` is defined and never invoked; REQ-API-006's startup clause is UNMET

**OWASP A05:2021 Security Misconfiguration. V3C-51 (baseline item 4), V3C-73 (built is not wired).**

`validate_startup_config` has no production caller anywhere in the repository:

```
grep -rn "validate_startup_config" src tests docs scripts Makefile pyproject.toml
  src/app/adapter/main.py:115:def validate_startup_config(...)          <- definition
  tests/unit/test_api_config.py:13,60,73,86,98                          <- tests only
```

`make serve` (`Makefile:126`) runs `uvicorn app.adapter.main:app`, which imports the module. The
import executes `cors_origins()` at `main.py:148` — so the **CORS half of the clause is genuinely
wired** — but it never executes the validator, and there is no `lifespan`, no `on_event("startup")`,
and no deploy entrypoint of any kind (`grep` for `lifespan`/`on_event` returns nothing; there is no
`Dockerfile` and no `deploy/`).

Measured, in the environment the clause names:

```
APP_ENV=production, MODEL_RANKING_DB unset, APP_BUILD unset
  import app.adapter.main   -> SUCCEEDS
  GET /health               -> 200 {"status":"ok","version":"0.1.0","build":"unknown"}
  GET /v1/recommendations   -> 503 evidence_unavailable
```

REQ-API-006 requires that "security-relevant config is validated at startup and **the process
refuses to serve in production if it is wrong**." The process serves. `/health` answers 200 while
declaring it does not know which code is live, which is the exact condition `main.py:128-132` was
written to refuse and the exact condition Stage 4.3's `curl /health | jq .build` check depends on.

The per-request 503 is not a substitute. `ConfigError`'s own docstring (`main.py:78-82`) states the
reason: *"a process that boots with a broken security config and fails per-request has already
served the request that mattered."* The code is right about itself; nothing calls it.

**Why this is blocking rather than minor, on two independent grounds:**

1. Permission-matrix §11, first row: *REQ-ID unmet (acceptance criteria not green)*. REQ-API-006 is
   a plan acceptance criterion and one of its four clauses does not hold on the live process.
2. Permission-matrix §11: *PASS verdict without `file:line` evidence per acceptance criterion*.
   `docs/plans/m6-wave-3-close.md:21` (row 6) marks REQ-API-006 green under the heading *"citing
   test entering through the LIVE entrypoint (not a unit shim) — V3C-02 + V3C-73/F6 (built is not
   wired)"*, and `docs/plans/m6-wave-3-close.md:22` (row 7c) lists *"production fails CLOSED at
   startup on missing security config"* as a hardened invariant with a negative test. The cited
   tests (`tests/unit/test_api_config.py:53-73`) call `validate_startup_config(env="production")`
   directly. They are unit shims by the row's own definition. **The checklist rows are a finding in
   their own right**, independent of the code: row 6's one genuine live-entrypoint test is
   `test_no_cors_header_is_served_when_no_allowlist_is_configured` (`test_api_config.py:101-116`),
   which covers the CORS clause and nothing else.

Fault-injection row 5 (`m6-wave-3-close.md:20`) reports the mutant *"production booting without a
database"* as killed. It was killed by a test of a function nobody calls, which is the failure mode
V3C-73 describes: mutation testing cannot see an unreachable control, because mutating unreachable
code and mutating its caller are indistinguishable when there is no caller.

**Remedy (small):** call `validate_startup_config()` at module scope beside `cors_origins()` at
`main.py:148`, and add a citing test that imports the module under `APP_ENV=production` with the
database unset and asserts the import raises. Nothing else in the design needs to change.

#### BLOCKING-2 — `src/app/clients/aider.py:66` — the only YAML input with an external producer is not routed through the W-005 guard

**OWASP A05:2021 / resource exhaustion. W-005's own deferral condition, inverted.**

W-005 was accepted at M4 on a stated trigger, quoted from `docs/warnings.ledger.md:24`: *"Accepted
because both YAML inputs are repo-committed data with no untrusted producer today. Owning milestone:
M6 — the API surface is what changes this boundary."* The wave shipped the guard on
`plans.py:135`, `rosters.py:100` and `epoch.py:42` — the three repo-committed files — and left
unguarded the one YAML input in the project whose producer is a remote host:

```
src/app/clients/aider.py:38-45   AiderClient.fetch_raw()
                                 httpx.get(AIDER_URL, timeout=30, follow_redirects=True)
                                 return resp.text            <- whole body, no size limit
src/app/clients/aider.py:66      entries = yaml.safe_load(raw)   <- unguarded
src/app/workflows/ingest.py:241  parse_polyglot(source.fetch_raw(), ...)   <- wired, production
```

There is no size bound, no expansion bound, and no timeout on the parse anywhere on that path.
Measured through the real wired function, on a document in the exact shape `parse_polyglot`
accepts (a list of run mappings — not a synthetic worst case):

```
8,516,890 bytes of well-formed leaderboard YAML
  parse_polyglot -> 120,000 rows in 14.5 s, RSS 17 MB -> 835 MB   (about 96x the input bytes)
  extrapolated: a 100 MB upstream response needs roughly 9.6 GB
MAX_YAML_BYTES (1,048,576) would have refused this before the parser saw it.
```

The upstream is a raw file served from a third-party repository over a followed redirect chain. The
project does not control it, does not pin it, and does not bound it. That is precisely the "untrusted
producer" the ledger row deferred against, and it existed before this wave — the wave simply did not
look for it.

**The reason it was not found is itself the finding.** `tests/unit/test_yaml_guard.py:93-106`
(`test_every_yaml_entry_point_goes_through_the_guard`) is the wave's producer-enumeration control,
and it enumerates by iterating a hardcoded literal:

```python
for name in ("plans", "rosters", "epoch"):
    source = Path(f"src/app/workflows/{name}.py").read_text()
```

It can never see a fourth producer, and it cannot see one outside `src/app/workflows/` at all.
`docs/plans/m6-wave-3-close.md:24` (row 9c) claims the producer list was *"enumerated FROM CODE ...
asserted from source ... rather than by a list in this row"*. The list was moved from the row into
the test; it was not derived. V3C-101 is explicit that unenumerated equals unaudited, and this is the
case it describes. A repository-wide grep finds the fourth site in one command:

```
grep -rn "yaml\.\(safe_\)\?load" src/ scripts/ conformance/
  src/app/clients/aider.py:66          <- unguarded, network-sourced
  src/app/workflows/yaml_guard.py:99   <- the guard itself
  conformance/test-ci-yaml.py:104,192  <- test tooling, out of scope
```

**Remedy (small):** route `aider.py:66` through `safe_load_bounded`, and rewrite the enumeration
test to walk `src/` for `yaml.safe_load` rather than to iterate three names, so the next producer
fails the test instead of escaping it. The guard's module docstring should stop saying "the
project's three curated inputs" — that phrase is what scoped the control away from the one input
that needed it.

---

### MINOR

#### MINOR-1 — `src/app/workflows/yaml_guard.py:40-51` — the cycle memo undercounts a recursive anchor, so the node bound does not hold for the cyclic case

`_expanded_size` writes `memo[key] = 1` before recursing and calls it a cycle guard. For a
self-referential anchor that is not a guard, it is an undercount of an unbounded quantity. Measured:

```
document:  a: &a [*a,*a,*a,*a,*a,*a,*a,*a,*a]      (39 bytes)
_expanded_size(...) -> 12          true expansion: unbounded
safe_load_bounded(...) -> PASSES; d["a"][0] is d["a"] -> True
consumer json.dumps(d)   -> ValueError: Circular reference detected
consumer naive walker    -> RecursionError
```

Not exploitable in current scope: all three guarded callers validate structure before walking it and
reject this with a clean `SourceError` (verified through `parse_rosters`). But the guard's stated
invariant — bound the expanded node count — is false for this input class, and the comment on
line 45 describes the undercount as if it were correctness.

**This one is explicitly NOT ledgerable.** It is a hole in the control this wave shipped, in the
control's own core function, and the fix is one line (raise on re-entry rather than memoize 1).
Accepting it with a trigger would reproduce the exact W-005 pattern — a known gap in a parsing
guard, deferred to a milestone where the boundary changes — that BLOCKING-2 above shows this project
already got wrong once.

#### MINOR-2 — `src/app/workflows/yaml_guard.py:88-91` and all three callers — `RecursionError` escapes the refusal contract

`yaml.compose` recurses per nesting level. A deeply nested document raises `RecursionError`, which is
not a `yaml.YAMLError`, so it passes through the guard's `except yaml.YAMLError` at `yaml_guard.py:89`
and through the identical handler in every caller (`plans.py:134`, `rosters.py:99`, `epoch.py:41`).
Measured at the default recursion limit of 1000, through the real caller:

```
"schema: 1\nplans:\n- " + "["*900 + "1" + "]"*900      (about 1.8 KB)
  parse_plans_doc(...) -> RecursionError: maximum recursion depth exceeded
  (depth 200 and 400 correctly return SourceError)
```

`_expanded_size` is recursive for the same reason and inherits the same limit. The module's stated
contract is that a refusal names the artefact it refused; for this input class there is no refusal,
only a stack overflow with an unhandled traceback. Fix: catch `RecursionError` alongside
`yaml.YAMLError` and re-raise as `YamlGuardError`, or bound depth during the walk.

#### MINOR-3 — `src/app/workflows/schema.py:164` vs `src/app/workflows/schema.py:79-81` — migrated and fresh databases get different constraints on the new column

The DDL declares `CHECK (roster_staleness_days IS NULL OR roster_staleness_days > 0)`. The migration
entry declares only `("plan_config", "roster_staleness_days", "INTEGER")`, and SQLite's
`ALTER TABLE ... ADD COLUMN` cannot carry a table CHECK. So a migrated pre-M6 database — the only
kind the migration exists for — has no constraint at all. Measured:

```
migrated database:  INSERT ... roster_staleness_days = -5   -> ACCEPTED
fresh database:     same INSERT                             -> IntegrityError: CHECK constraint failed
rosters.roster_staleness_days(migrated_conn)                -> returns -5
```

`rosters.py:242-252` checks `row is None` and `row[0] is None` but never `> 0`, so a nonsensical
window is read straight into the staleness disclosure — a negative window makes every roster link
report stale, on exactly the databases the operator upgraded rather than rebuilt. Not exploitable
(nothing untrusted writes `plan_config`), but a disclosure control reading an unvalidated number is
one class away from the W1 finding. Fix belongs in the read, since ALTER cannot carry it: validate
`> 0` in `roster_staleness_days()` and fail with the same loud message.

---

### NOTE

#### NOTE-1 — the guard's stated attack mechanism is not reproducible on the shipped PyYAML; the control is right for a different reason

`yaml_guard.py:3-6` and `docs/warnings.ledger.md:24` both justify the control with a measurement:
alias expansion causes `MemoryError` in about ten seconds under a 1 GiB limit. That does not
reproduce on PyYAML 6.0.3 / Python 3.14. `SafeConstructor.construct_object` caches by node, so
aliases become shared Python references and nothing expands during the load:

```
yaml.safe_load(BILLION_LAUGHS)  ->  succeeded in 0.001 s, peak RSS 21 MB
                                    d["h"][0] is d["h"][1]  ->  True
```

The expansion is real but it happens in the **consumer**, not in the parser:

```
json.dumps(that same parsed object)  ->  254,244,728 bytes in 1.49 s, from a 300-byte document
```

The guard is still the correct control — the logical expanded size is exactly what any consumer that
walks or serializes the structure pays, and this project serializes. But the justification on record
cannot be re-run, and a control whose stated reason does not reproduce is a control a future wave
deletes as unnecessary. Restate the rationale against the consumer-side measurement above.

#### NOTE-2 — the guard genuinely doubles the parse, and the doubling should be on record

Measured on an 877,779-byte flat document:

```
yaml.compose      1.31 s
_expanded_size    0.03 s
yaml.safe_load    1.40 s
guard overhead    about 95% on top of the unguarded load
```

So yes, this is a real doubling rather than a rounding error, and `yaml.compose`'s cost is bounded
only by `MAX_YAML_BYTES`. Worst case at the current limit is roughly 2.8 s of CPU and about 200 MB
for a single load. Acceptable — the guarded inputs are operator-run and not network-reachable — but
it is the reason `MAX_YAML_BYTES` must not be raised casually, and it is the reason BLOCKING-2's
1 MiB cap matters on the network-sourced input.

#### NOTE-3 — CORS ordering, the 500 handler, and the preflight surface: verified, all correct

Checked rather than assumed, since the task asked. `app.user_middleware` is
`[BaseHTTPMiddleware(_no_sniff), CORSMiddleware]`; Starlette inserts at index 0, so **`_no_sniff` is
the outer middleware and CORS is inner** — preflight responses therefore do carry
`X-Content-Type-Options: nosniff`. The `Exception` handler at `main.py:171` runs on
`ServerErrorMiddleware`, outside both, so a 500 carries the header set by hand at `main.py:184` and
carries **no** CORS header at all, which is the fail-closed direction. Measured surface:

```
no allowlist configured:
  OPTIONS/POST/PUT/DELETE/HEAD/PATCH on /v1/categories  -> 405, Allow: GET
  OPTIONS with Origin + Access-Control-Request-Method   -> 405, nosniff present, no ACAO
allowlist = https://app.example.com:
  preflight, allowed origin, GET     -> 200 from CORSMiddleware, ACAO echoed, never reaches a route
  preflight, other origin            -> 400 "Disallowed CORS origin", no ACAO
  preflight, allowed origin, DELETE  -> 400 "Disallowed CORS method"
  GET with Origin                    -> 200, ACAO echoed, no ACAC header (credentials off)
  unhandled 500                      -> generic JSON body, no exception text, nosniff, no ACAO
```

A preflight reaches CORSMiddleware and nothing behind it. The surface is exactly the three declared
GET routes (`main.py:66-68`), confirmed against `app.routes` at runtime. `allow_credentials=False`
is hard-coded at `main.py:157`, so the V3C-13 catastrophic combination is unreachable by
configuration rather than merely unset. The wildcard refusal at `main.py:102-108` fires at import in
every environment and is genuinely wired — it is the one clause of REQ-API-006 that BLOCKING-1 does
not touch.

Two cosmetic edges, both failing closed and neither worth a finding: `cors_origins` accepts
`http://` origins, and it does not normalize case or a trailing slash — a mismatched entry simply
never matches.

#### NOTE-4 — the migration's fail direction is correct, and the divergence the task asked about does not exist

Two questions were posed and both check out.

*Is raising correct?* Yes. `roster_staleness_days()` (`rosters.py:230-253`) refuses to fall back to
the plan window on an unset policy. Under V3C-33/45 the staleness sentence is a **disclosure**
control, not a fairness control, so it fails CLOSED; a silent fallback would reinstate the exact
W-008 coupling and would do it on the oldest databases. The availability cost is also narrower than
it looks: `subscribe._stale_notice` is reached only through `recommend_subscription`, whose sole
caller is `recommend.py:407-418` **inside `main()`** — the CLI. The `/v1` surface calls
`recommend()`, which has its own unrelated `_stale_notice` at `recommend.py:245`. So the raise is
CLI-scoped and cannot 500 the network surface today. The early return at `subscribe.py:294-302`
(no roster rows means no roster policy is demanded) is the right narrowing and stops the loud
failure from firing on databases that never ask the question.

*Can links and policy disagree about which roster file they came from?* Not through the shipped
paths. `ingest_rosters` writes the policy in the same `with conn:` block as the link delete and
insert (`rosters.py:137-152`), so they commit or roll back together. The one route that could split
them — re-ingesting `data/plans.yaml` afterwards — does not, because `ingest_plans` issues
`DELETE FROM plan_models` before `INSERT OR REPLACE INTO plan_config` (`plans.py:180-186`): the
REPLACE nulls `roster_staleness_days`, and the DELETE removes the roster links in the same
transaction, so the database lands consistently at "no links, no policy". The remaining case is a
pre-M6 database that already holds roster links and is then migrated; that lands at "links, no
policy" and raises loudly, which is the intended direction. Queue for M7: if a later wave puts
`recommend_subscription` on `/v1`, this raise becomes a 500 on a network route and needs to be
converted into a disclosed unavailability the way `main.py:474-479` already does for unreadable
evidence.

#### NOTE-5 — `docs/plans/m6-wave-3-close.md:25` cites the wrong authority for the W-017 deferral

Row 9b states that W-017 is deferred "which the plan lists here", citing `docs/plans/m6-plan.md`
§3 W3. `grep -n "W-017" docs/plans/m6-plan.md` returns nothing; the plan's own intake table
(`m6-plan.md:224-226`) lists W-005, W-008 and W-009 for W3 and no more. W-017 was raised at M6-W1 on
2026-08-16, after the plan was signed, and its W3 assignment comes from
`docs/plans/m6-wave-1-close.md:56` and from the ledger row itself. The deferral is real and properly
recorded; only its cited source is wrong. Worth correcting because a deferral that cites a signed
plan reads as pre-authorized when it was in fact a post-hoc reviewer assignment.

---

## Ruling on W-017 (asked explicitly: is deferring past W3 defensible, or is this the reviewer grading their own finding?)

**Deferring past W3 is defensible. It is not the reviewer grading their own finding — but only
because the deferral leaves the gate exactly where the finding put it, and that is the entire test.**

First, an independent re-derivation, because inheriting my own W1 number is the failure mode the
question is pointing at. Measured today against the repository's own `live.db`:

```
live.db = 761,856 bytes
20 sequential serving_snapshot() copies -> RSS 61 MB -> 83 MB
  about 1.1 MB of process memory per roughly 120-byte unauthenticated GET
  amplification about 9,100x at today's database size
```

That reproduces the mechanism and, more importantly, reproduces its **shape**: amplification is
database size divided by request size, linear in the database and independent of anything W3
touched. The W1 figure of about 450,000x at 51 MB is the same line extrapolated. So the measurement
stands on a second, independent run.

**Why the deferral is defensible:**

1. **The remedy is genuinely outside this wave's permission envelope.** Bounding the snapshot means
   changing `build_price_medians` so the read path stops writing (`rank.py:143-170`), and the signed
   plan forbids exactly that: *"if a route needs the engine to behave differently, that is a
   finding."* The alternative — a control in front of the surface — is a deployment-topology
   decision that D-116/OQ-3 has not made yet. W3 could not have closed this without breaking the
   plan it was executing.
2. **The control class does not force the timing.** Rate limiting is a fairness control, and under
   V3C-33/45 fairness controls fail OPEN. Its absence therefore violates no fail-direction rule.
   This is what separates W-017 from the W1 disclosure finding, which failed OPEN on a safety
   control and could not be deferred at any price.
3. **W3 did not widen the exposure.** The surface is unchanged at three GET routes, and W3's CORS
   default narrows cross-origin reach rather than widening it.
4. **The deferral is written down where it will be read.** `m6-wave-3-close.md:25` names it, names
   the reason, and names the gate. F15 is a plan-tagged control disappearing quietly; a deferral
   carried in the wave record with its owning gate intact is the opposite of that.

**Why it is not me grading my own finding:** the severity was fixed on 2026-08-16 in
`docs/warnings.ledger.md:17`, with a measurement, a named gate (Stage 4.3), and an explicit
non-closure condition (*"may not be closed by the engine fix alone"*). W3 declining to fix it does
not move any of those. What **would** be grading my own finding is relaxing the 4.3 gate now,
accepting the engine fix as sufficient later, or letting the row close on my say-so. This review
does none of those and re-states all three. Note also that the ledger row was already amended once
against precisely this drift: its original wording ("its cost grows with the database size") would
have let W3 fix the engine write and close the row with the amplification standing.

**Conditions, all of which must hold or the deferral expires:**

- **(a)** The W-017 ledger row's status changes from `ACCEPTED` to a status that cannot be read as
  settled. `ACCEPTED` is the same word W-005 carried for two milestones, and BLOCKING-2 above is
  what that produced.
- **(b)** The Stage 4.0 closure security review — a different pass, already scheduled — **re-derives
  the amplification independently** rather than citing W1 or citing this review. The honest answer to
  "who decides this finding's severity" is a second measurement, not a stronger adjective from the
  person who found it. My run above is the first half of that; closure owes the second.
- **(c)** M6 does not go live before 4.3 closes. If the deploy shape turns out to put `/v1` in front
  of the public internet with nothing between, the deferral is void the moment that is known, not at
  the next scheduled gate.

---

### PASS — security hygiene worth recording

- `main.py:171-185` — the 500 handler keeps exception text out of the body and sets `nosniff` by
  hand precisely because `ServerErrorMiddleware` sits outside user middleware. Verified: a route
  raising `RuntimeError("SECRET=... /Users/...")` returns a generic body with neither string.
- `main.py:157` — `allow_credentials=False` is a literal, not a default. The V3C-13 catastrophic
  combination is unreachable by configuration.
- `main.py:102-108` — the wildcard refusal is not environment-gated, and
  `test_a_wildcard_is_refused_in_development_too` pins that. The reasoning on record (a wildcard is a
  contract decision that gets committed in a dev config and inherited by production) is correct.
- `main.py:231-239` — no working-directory-relative database default. Unset is refused rather than
  guessed.
- `main.py:188-199, 202-228` — read-only URI built through `Path.resolve().as_uri()` (INV-23), and
  the serving snapshot keeps the engine's writes off the operator's bytes. The containment is sound;
  W-017 is about its cost, not its correctness.
- `main.py:242-249, 548-552` — attacker-controlled echo bounded at 40 characters, no filesystem path
  in any error body, one error shape throughout.
- `rosters.py:137-152` — the roster policy is written in the same transaction as the links it
  governs, which is the right place and the comment says why.
- `schema.py:251-271` — the W-009 reconciliation went the correct direction: callers moved to the
  frozen `migrate()` name rather than the name moving to the callers.
- Migration is additive and nullable (`ALTER ... ADD COLUMN`), never `DROP`. No destructive DDL, no
  `DROP TABLE`, no reseed-on-boot anywhere in the diff.

---

## Gates passed

- [x] **Secret scan** — no secret in the wave diff (`git diff 67fd92b..HEAD` scanned for key/token/
      credential patterns: clean). **`gitleaks detect --source . --no-git` at HEAD is NOT clean: 2
      findings**, both the same false positive on a hyphenated decision-reference string, at
      `docs/reviews/m2-security-review.md:8` and `docs/reviews/m4-security-review.md:310` — both
      pre-existing, both outside this wave's range. Reported, **not suppressed** (v3.3: agents may
      never waive a scanner finding); the allowlist decision belongs to the owner.
- [x] **pip-audit** — `No known vulnerabilities found` (only the local `model-ranking` package
      skipped as not on PyPI).
- [x] **Slopsquat / new imports** — the wave adds exactly one import,
      `fastapi.middleware.cors.CORSMiddleware` (`main.py:150`), a submodule of an already-pinned
      dependency (`fastapi>=0.115`). `yaml_guard.py` imports only `yaml` (`pyyaml>=6.0`, pinned) and
      `typing`. No new third-party package; no manifest change needed.
- [ ] **Default-deny preserved for new external surfaces** — **FAILED.** CORS defaults to closed and
      is wired, but BLOCKING-1 leaves the production startup gate unattached, so a misconfigured
      production process serves instead of refusing.
- [x] **Permission matrix not violated** — no destructive operation in the diff; migration is
      additive; no `⛔` glob touched; §11's senior-human-review trigger for a migration change is
      what this pass is, and it returns BLOCKING.
- [x] **Prompt-injection hygiene** — no LLM prompt, no `eval`, no instruction-following from fetched
      text on this path. Fetched content (`aider.py`, `epoch.py`) is parsed as data only. Related but
      distinct from BLOCKING-2, which is resource exhaustion rather than injection.
- [ ] **Auth/PII/migration checks + human review trigger** — trigger fired (migration present);
      verdict is BLOCKING pending fixes and owner sign-off. No PII, no credentials, no crypto, and no
      authentication of any kind on this surface — V3C-12 is satisfied structurally, by there being
      no mutating route (`REQ-API-001`), confirmed at runtime: every non-GET verb returns 405.
- [x] **SAST-equivalent** — targeted dynamic testing rather than a generic scanner, since the risk
      classes here are expansion, wiring and fail direction. Eleven adversarial documents built and
      run against the guard, the surface probed with six HTTP verbs plus preflights in two CORS
      configurations, and the production boot path exercised under `APP_ENV=production`. Full suite
      green at HEAD: **336 passed / 12 skipped**.

---

## Acceptance criteria evidence

| REQ-ID / item | Status | Evidence |
|---|---|---|
| REQ-API-006 — CORS is an allowlist, never allow-all-with-credentials | **PASS** | `src/app/adapter/main.py:102-108` (wildcard refused), `:157` (`allow_credentials=False` literal), `:148-160` (middleware added only when an allowlist exists); `tests/unit/test_api_config.py:16-50, 90-98`; live-response assertion `tests/unit/test_api_config.py:101-116`; runtime probe in NOTE-3 |
| REQ-API-006 — config validated at startup, process refuses to serve in production | **FAIL — BLOCKING-1** | `src/app/adapter/main.py:115` defined, zero production callers; `Makefile:126` is the only entrypoint and it does not call it; measured boot under `APP_ENV=production` with the database unset returns `/health` 200 |
| REQ-API-006 — database handle opened read-only | **PASS** | `src/app/adapter/main.py:188-199` (`?mode=ro` via `Path.resolve().as_uri()`), `:202-228` (per-request in-memory copy); pre-existing W1 test `test_the_api_never_writes_to_the_database` |
| REQ-API-006 — no plaintext credential in source | **PASS** | diff scan clean; `gitleaks` findings at HEAD are two pre-existing false positives outside this range (see Gates) |
| REQ-SUB-008 — roster staleness reads the roster's own persisted window | **PASS with MINOR-3** | `src/app/workflows/schema.py:79-81` (DDL), `:164` (migration), `src/app/workflows/rosters.py:137-142` (write, in-transaction), `:230-253` (loud read), `src/app/workflows/subscribe.py:291-302` (consumer); `tests/unit/test_roster_window.py`. MINOR-3 is the constraint divergence between fresh and migrated databases |
| W-005 — alias-expansion guard on curated YAML | **FAIL — BLOCKING-2, and MINOR-1/MINOR-2** | `src/app/workflows/yaml_guard.py:1-99`; wired at `plans.py:135`, `rosters.py:100`, `epoch.py:42`; **not** wired at `src/app/clients/aider.py:66`, which is the only external producer, reached from `src/app/workflows/ingest.py:241` |
| W-009 — one migration entry point, the one production runs | **PASS** | `src/app/workflows/schema.py:251-271` (`migrate` keeps the K.8 frozen name and the SAVEPOINT), `:369` and `:414` (both callers moved onto it); `test_production_runs_the_migration_entry_point_the_tests_exercise` |
| W-017 — serving-snapshot DoS amplification | **DEFERRED, defensible under stated conditions** | `docs/warnings.ledger.md:17`; independent re-measurement in the ruling above; three conditions attached |

---

## Risks queued to next M

1. **W-017 conditions (a), (b), (c)** above — status change, independent re-derivation at Stage 4.0,
   and no go-live before 4.3.
2. **`AiderClient.fetch_raw` has no response size limit** (`aider.py:38-45`) even once BLOCKING-2 is
   fixed. `safe_load_bounded` refuses a document over 1 MiB, but `resp.text` has already
   materialized the whole body before the guard sees it. Bound the read at the client, not only at
   the parser. The same review is owed to every other client that reads a remote body.
3. **`follow_redirects=True` with no host allowlist** on the same fetch. Out of scope for this wave;
   worth one line in M7 given the file is parsed as configuration data.
4. **If `recommend_subscription` ever moves onto `/v1`**, `roster_staleness_days()`'s `ValueError`
   becomes a 500 on a network route (NOTE-4). Convert it to a disclosed unavailability at that point,
   matching `main.py:474-479`.
5. **The producer-enumeration pattern generalizes.** V3C-101 enumeration should be a repository-wide
   grep expressed as a test, not a hardcoded module list. BLOCKING-2 is the first time this project
   has paid for the difference; it will not be the last.

---

## Reviewer note on the checklist

`docs/plans/m6-wave-3-close.md` rows 6, 7c and 9c each assert something this pass could not confirm:
row 6 claims a live-entrypoint citing test for REQ-API-006's startup clause (BLOCKING-1), row 7c
claims a hardened fail-closed-at-startup invariant (BLOCKING-1), and row 9c claims a from-code
producer enumeration (BLOCKING-2). Those three rows must be corrected as part of the fix, not merely
re-ticked once the code changes — a checklist that was green while the control was unwired is a
second defect, and it is the one that would have let this ship.

Rows 5 and 9b are countersigned as accurate against the artifacts: the fault-injection protocol did
run in place with hash verification and no `git checkout`/`restore`/`stash`, and the scope row does
name the W-017 deferral honestly (with the citation error at NOTE-5).

**BLOCKING → the wave does not progress. A mini-fix-wave is required for BLOCKING-1, BLOCKING-2 and
MINOR-1, after which this pass re-runs on the fix.**
