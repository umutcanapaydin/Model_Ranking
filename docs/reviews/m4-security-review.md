---
record_type: register
id: m4-security-review
status: ratified
date: 2026-08-15
---
# M4 Stage 4.0 — Security Review (fresh eyes, milestone closure, BLOCKING gate)

Reviewer: independent Security-Reviewer subagent (authored none of this code).
Surface: `0f840a9..HEAD` — 4 wave commits. Date: 2026-08-15. Risk tier: LOW
(curated data + derived read-only metrics + output formatting; no authz, no crypto,
no new egress).

## VERDICT: PASS — 0 BLOCKING, 6 MINOR, 4 NOTE

---

## 1. Scope + method

**Commits walked** (`git log --oneline 0f840a9..HEAD`):

| commit | wave |
|---|---|
| `17eec69` | M4-W1 registry expansion + self-defending rule table (REQ-CAN-004) |
| `bc9c6de` | M4-W2 provider model rosters (REQ-ING-009) |
| `ee5a582` | M4-W3 coverage + source health (REQ-SUB-005 / REQ-ING-011) |
| `20312a1` | M4-W4 rounding + equivalence + the $4.99 row |

24 files, +2042/-46. Read in full: `src/app/workflows/{coverage,rosters,subscribe,registry,schema,recommend,plans}.py`,
`data/{plans.yaml,rosters.yaml}`, `.github/workflows/contract-tests.yml`, `.language-allow`,
and the whole `tests/` diff.

**Read first, to stay in shape and not re-litigate:** `docs/security-baseline.md`,
`docs/reviews/m3-security-review.md`, `docs/reviews/m2-security-review.md`, `AGENTS.md`,
`docs/decisions.md` D-100..D-108, `docs/warnings.ledger.md`, and the three wave records
(`m4-w1-registry-droplist.md`, `m4-w3-source-health.md`, `m4-w4-equivalence.md`).

**Commands actually run** (all read-only against git; no `git` write command was issued):

- `make secrets` (gitleaks 8.28.0) — §4
- `make deps` (pip-audit) — §4
- `bandit -r src -q` — 1 Medium, the known allowlist-gated identifier; unchanged from M3
- `.venv/bin/python -m pytest` — **191 passed, 5 skipped** (the 5 are the network contract
  self-skips, reported not silent — V3C-44)
- `.venv/bin/python -m ruff check src tests` — clean; `mypy src` — clean (23 files)
- `bash scripts/bootstrap-check.sh` — PASS, 0 fail / 2 warn (both pre-existing: C5 ADR band,
  C6 no license review needed — no OSS engine wrapped)
- `make check-records` — PASS on the tree before this record was added

**Live probes executed against the code (no repo file was modified at any point;
`git status --porcelain` clean before and after — only the untracked `docs/coverage-by-req.md`
belonging to Stage 4.1, which I did not touch):**

1. Built an in-memory DB from `plans.yaml`-shaped + `rosters.yaml`-shaped fixtures and ran
   `recommend_subscription` to read the real `equivalence_note` a roster-linked plan produces
   (evidence for MINOR-1).
2. Ran a YAML alias-expansion bomb through `parse_rosters` under a 1 GiB `RLIMIT_AS`
   (evidence for MINOR-5).
3. Built a pre-M4-shaped `plan_models` table and drove `recommend.main --subscription` against it
   through the real CLI entry point (evidence for MINOR-3).

---

## 2. Baseline walk (`docs/security-baseline.md`)

| # | Control | Verdict | Evidence |
|---|---|---|---|
| 1 | No plaintext creds / no default-admin (**GATE** V3C-11) | **PASS** | `bootstrap-check.sh` C7 `[ ok ]`; the whole M4 diff contains zero credential-shaped literal (grep for `api[_-]?key\|secret\|token\|password\|bearer\|authorization\|aws_\|PRIVATE KEY` over `git diff 0f840a9..HEAD` returns only prose in wave checklists, e.g. `docs/plans/m4-wave-4-close.md:299` "no authz/secrets/crypto/egress"). No new file reads or holds a credential. |
| 2 | Server-side authz on every mutating route (V3C-12) | **N/A** | No HTTP surface exists beyond `/health` (D-100); `src/app/adapter/main.py` unchanged in M4. The mutating surface is three local CLIs, and only one of them writes (see §3 CLI table). |
| 3 | CORS allowlist (V3C-13) | **N/A** | No CORS config in the repo; no browser-reachable API. Unchanged from M2/M3. |
| 4 | Validate security-critical config at startup, fail prod (V3C-51) | **PASS (analogue)** | No auth/TLS config exists to validate. The project's equivalent — *thresholds live as DATA and their absence must abort* — is enforced loudly and was extended this milestone: `rosters.py:104` rejects a missing/non-positive `staleness_days`; `rosters.py:106` rejects an empty `rosters` list ("an empty file is a bug, not an empty market"); `rosters.py:96` rejects a wrong `schema:` version. Mirrors `plans.py` (D-107). No silent default anywhere in the new parser. |
| 5 | Encrypt creds/PII at rest, rotation-friendly key chain (V3C-56) | **N/A** | No credential and no PII is stored. SQLite holds public benchmark scores, public list prices, and public URLs. `data/rosters.yaml` is entirely public provider documentation. |
| 6 | Generic client errors; detail server-side | **PASS (scoped)** | The only "client" is the operator/CI at a terminal, so detail is appropriate, not a leak. All three new CLIs return typed exit codes with no traceback: `coverage.py:132-151` (2 = usage/DB-unusable, 1 = zero coverage, 0 = reported), `rosters.py:190-217` (2 = bad path/date/parse, 1 = stale, 0 = fresh). Parse failures surface as `SourceError` text, never a stack. |
| — | Control-class fail direction (V3C-33/45) | **PASS** | Every M4 control fails CLOSED. `rosters.py:130-133` — a roster naming an unknown plan aborts the whole ingest; `rosters.py:135-149` — the roster working set is replaced inside `with conn:` so an `IntegrityError` rolls the set back whole; `coverage.py:118` — a source with rows but an unparseable newest date is reported **stale**, not fresh (the W3 reviewer's MINOR-1, correctly fixed toward disclosure); `coverage.py:157-159` — zero coverage in any category exits 1. |
| — | V3C-73 built ≠ wired | **PASS with one exception** | New controls are reachable from real entry points: the roster staleness gate runs in CI (`contract-tests.yml:47-48`), coverage runs in CI (`contract-tests.yml:117-120`), and `test_cli_exit_codes_through_real_entrypoint` (`tests/unit/test_rosters.py:204`) + `test_cli_reports_json_and_fails_loud_on_zero_coverage` (`tests/unit/test_coverage.py:120`) enter through `main()`. The exception is `schema.migrate` — see MINOR-3. |
| — | V3C-74 negative test per security invariant | **PASS** | Every new invariant has a test that fails if it is removed: unknown-plan roster (`test_rosters.py:127`), invalid roster row per field (`test_rosters.py:143`, parametrised), empty/duplicate roster (`test_rosters.py:152`), atomic partial replace (`test_rosters.py:165`), drops counted not guessed (`test_rosters.py:117`), unparseable date → stale (`test_coverage.py:147`), coverage is read-only (`test_coverage.py:137`), equivalence never names an excluded plan (`test_subscribe.py`), equivalence keyed by `plan_id` not name (`test_subscribe.py`). |
| — | V3C-77 money | **PASS (scoped)** | The project displays list prices, it does not transact, so integer-minor-units is not required (the baseline scopes V3C-77 to "projects handling money"). The new float exposure is display-only: `subscribe.py:294-296` formats a price *span*, it does not compute one. `monthly_usd` is parser-gated finite and > 0 (`plans.py:59-65`) and the schema CHECK enforces it. `test_sub_dollar_price_survives_the_seed_exactly` (`tests/unit/test_plans_ingest.py:181`) pins $4.99 through parse **and** store — the first fractional sub-$10 row, and the one every budget answer lands on. |
| — | V3C-101 producer enumeration | **PASS** | The producers of `plan_models` are now exactly two and both are named in the row itself: `link_source='plan-page'` (`plans.py` ingest) and `link_source='roster'` (`rosters.py:137-141`). `schema.py:80-86` documents the column as the provenance discriminator. Nothing else writes the table. |
| — | V4C-61 verifier ≠ implementation | **PASS** | `coverage.plan_coverage` is an independent reader over the same DB, and the W3 record states its "scoreable" set was cross-checked against what `subscribe.plan_ranking` can actually rank, by a reviewer with their own SQL — a second implementation, not a self-check. |
| — | V4C-49 ship the gate with the rule | **PASS** | `make pin-check` (Makefile:74) still green; the two new CI steps are unconditional steps of the already-unconditional `plan-staleness` job. |
| — | INV-1 inert payloads | **PASS with a caveat** | Zero `yaml.load` / `Loader=` / `eval(` / `exec(` / `pickle` / `os.system` in `src/`. Only `yaml.safe_load`, at exactly three sites: `plans.py:134`, `rosters.py:99` (new this milestone), `clients/aider.py:66`. No parse path can construct an arbitrary object or import a module. Caveat = MINOR-5 (resource exhaustion, not code execution). |
| — | INV-2 parameterised SQL | **PASS** | Every new query binds with `?`: `coverage.py:63,65,71,75-79` , `rosters.py:130,136,138-146,150-152`, `subscribe.py:122-149` (the new `ORDER BY (pm.link_source = 'plan-page') DESC` is a hardcoded literal inside the query text, not interpolation), `registry.py:160-171`. `bandit -r src` = **1 Medium**, the same known allowlist-gated identifier at `schema.py:183`, unchanged from M3. The two new f-string SQL sites in `schema.py:155,159` interpolate only elements of the module constant `_MIGRATIONS` (`schema.py:144-148`) — no runtime or data value reaches them. Note that bandit does **not** flag them (B608 does not match `PRAGMA`/`ALTER`), so this one was reasoned by hand rather than by scanner — see NOTE-3. |
| — | INV-6 network-free default suite | **PASS** | No new outbound call anywhere in M4: `git diff 0f840a9..HEAD -- src/app/clients/` is **empty**. No URL is built from data; roster `source_url` values are stored and printed for provenance and are **never fetched** (grep: `source_url` appears in `rosters.py` only in validation, INSERT, and the staleness message at `rosters.py:176`). No redirect handling, no SSRF shape. `pytest` = 191 passed / 5 skipped, the 5 being `RUN_CONTRACT_TESTS`-gated integration tests. |
| — | INV-8 documented endpoints only (D-101) | **PASS** | Endpoint set unchanged at 5. Artificial Analysis is absent from the entire diff (grep: zero hits). `rosters.yaml` adds a *human-curated transcription* of one documented help-centre page, not a fetch target; its PROBE LOG (`data/rosters.yaml:16-26`) records the three providers that publish nothing and therefore get **no roster** — the honest outcome, not a papered-over gap. |
| — | INV-10 CI least-privilege | **PASS** | `contract-tests.yml:24` `permissions: contents: read`; the two new steps carry no secret, no `${{ }}` in any run body, and both live inside the existing SHA-pinned, timeout-bounded jobs. `contract-tests.yml:118` uses `set -o pipefail` before the `tee`, so a coverage failure cannot vanish behind the pipe. |
| — | INV-11 tests never disable TLS | **PASS** | grep `verify=False\|trust_env\|ssl._create` across the repo = zero hits. |
| — | No LLM in the data or scoring path (D-104) | **PASS** | Every number and every string in the M4 output is derived from DB values or module constants. `round_score`/`shown_gap`/`lead_phrase` (`recommend.py:47,57,66`) are pure arithmetic; `equivalence_note` (`subscribe.py:288-306`) is an f-string over DB columns. No model call, no heuristic text generation, anywhere in the diff. |
| — | Unmatched names dropped AND counted, never guessed | **PASS** | `rosters.py` links only through the registry; `registry.reconcile_plans:150-176` leaves `model_id` NULL and appends to `dropped_names` on a miss. `test_roster_links_reconcile_through_the_registry_and_count_drops` (`tests/unit/test_rosters.py:117`) is the citing test. `data/rosters.yaml:53-55` names the four roster entries that are expected to drop (Sonar 2, Kimi K3, Nemotron 3 Ultra, GLM 5.2 variants) — a drop is documented in the data, not discovered in production. |
| — | Security-invariant test modified or deleted? | **PASS — none** | `git diff 0f840a9..HEAD -- tests/` is **+919 / -16**, no file deleted, no test function removed. Every removed line is an assertion *value* updated for the W1 registry split (`gemini-3-pro` → `gemini-3.1-pro`) or a count re-baselined and **replaced by a stricter assertion**: `test_seed_dataset_ingests_and_reconciles_end_to_end` swapped a bare `COUNT(*) == 3` for a full ordered `(plan_id, raw_name, model_id)` tuple list (`tests/unit/test_plans_ingest.py:190-203`). The drop-counting invariant keeps its own citing test with a non-empty drop list (`tests/unit/test_plans_ingest.py:145-165`). Nothing was weakened. |
| — | V4C-79 English-only | **PASS** | The four `.language-allow` additions each carry a written reason and are genuine: three are test files asserting the Turkish product strings, one is `docs/reviews/m4-w4-equivalence.md` quoting the shipped `equivalence_note` verbatim as measured evidence — paraphrasing it would break the record-vs-referent rule. Spot-checked all four; each matches its stated reason. |

---

## 3. Findings

No finding rises to BLOCKING. Every M4 control fails closed, no secret entered the tree, no new
network surface exists, and no security-invariant test was weakened. The six MINORs below are
ordered by how close each comes to the product's actual security property — that the engine may
never assert something false to the user.

### CLI write-capability table (asked for explicitly, and it checks out)

| entry point | file:line | writes to the DB? | verified |
|---|---|---|---|
| `app.workflows.coverage --db` | `coverage.py:127-165` | **No** — SELECT only | `test_coverage_is_read_only` (`tests/unit/test_coverage.py:137`); read of the module confirms no INSERT/UPDATE/DELETE/DDL. See MINOR-4 on how the claim is *enforced*. |
| `app.workflows.rosters --check-staleness` | `rosters.py:182-217` | **No** — never opens a DB at all; reads one file and returns | `rosters.py:205` calls `stale_rosters`, which is pure over the file text |
| `app.workflows.plans --check-staleness` | `plans.py` (M3, unchanged) | No | M3 review |
| `rosters.ingest_rosters` | `rosters.py:120-166` | **Yes, by design** | Not a CLI. Only `link_source='roster'` rows are deleted and re-inserted (`rosters.py:136`), so plan-page links survive; citing test `test_reingest_replaces_only_roster_links` (`tests/unit/test_rosters.py:165`) |

### MINOR-1 — `equivalence_note` asserts a page provenance the roster case does not have
`src/app/workflows/subscribe.py:301`

The headline sentence's verb is **`listeliyor`** (*"[it] lists"*) — the note states that N plans *list*
the same model — and it says this of every member of an equivalence group, including members whose link
came from a roster rather than from the plan's own page. For a roster-linked plan the plan page lists
nothing; the provider's *separate* documented model list names the model. The same payload gets the
provenance right 30 lines away, in the per-pick `why` (`subscribe.py:328-334`) and in the new
`scored_via` / `link_source_url` fields — so the product contradicts itself within one response.

**Failure scenario, reproduced deterministically this review.** Two plans, one linked from its own
page and one linked only from a roster, same model, same score. Output:

```
equivalence_note: "2 plan ... (Gemini 3.1 Pro) listeliyor, ... : Page Plan, Roster Plan. ..."
                  -> "2 plans LIST the same model (Gemini 3.1 Pro), so they are
                      indistinguishable in quality: Page Plan, Roster Plan. ..."
best_quality why: -> "...is named in the provider's PUBLISHED PLAN MODEL LIST."
```

(Turkish product strings elided to the one load-bearing verb, `listeliyor` = *"lists"*; the English
under each arrow is the translation of the full shipped sentence.)

The note says *Roster Plan lists Gemini 3.1 Pro*; the `why` in the same object says the **provider's
separate list** does. On the shipped data this is asserted about Perplexity Pro, whose pricing page
does not name Gemini 3.1 Pro (`data/rosters.yaml:31-56` is where the name actually comes from). A user
who does the honest thing — open the plan page to check — finds nothing, and the product's whole trust
claim ("we link plans to evidence") is damaged by its own headline sentence.

**Why MINOR and not BLOCKING:** the *substance* is true — the provider does document the inclusion,
the link is evidence-backed and never guessed, and the score/price/cheapest claims are all correct.
One verb is imprecise about which document carries the statement.

**This is finding L-1 of `docs/reviews/m4-w4-equivalence.md` §5, and its declared owning milestone is
"M4 closure" — i.e. now.** It may not be deferred a second time silently.

**Remedy:** make the verb source-neutral when any group member is roster-linked — replace *"N plans
**list** model X"* with a construction meaning *"model X **appears in** N plans"*, which is true of both
link sources — or append the provenance split to the note. One phrasing decision (the exact Turkish
wording is the owner's call), one line, plus a citing test that builds a mixed
`plan-page` / `roster` group and asserts the sentence.

### MINOR-2 — a stale roster link produces a recommendation with no staleness disclosure
`src/app/workflows/subscribe.py:385` · `src/app/workflows/subscribe.py:193-202` · `src/app/workflows/schema.py:86`

`_stale_notice` (REQ-REC-008) reads **only** the `plans` table. `plan_models.last_verified` — the
column M4-W2 added precisely because "roster rows age on their own clock" (`schema.py:86`) — is written
by `rosters.py:141` and then **never read again by anything in `src/`** (grep confirms: every other
`last_verified` reference resolves to `plans`). So a plan whose sole evidence link is a 200-day-old
roster entry is recommended with `stale_notice: null`, while a plan whose *price* is one day past
window is loudly disclosed. The output implicitly asserts "the evidence behind this pick is inside the
verification window" when for roster-linked picks it has not checked.

This is the identical failure direction the W3 reviewer corrected in `coverage.py:118` (unknown age
must read as stale) — applied there, not applied here.

**Why MINOR and not BLOCKING:** a real control does exist, just not in the output. The unconditional
weekly CI leg `python -m app.workflows.rosters --check-staleness data/rosters.yaml`
(`.github/workflows/contract-tests.yml:47-48`) turns a stale roster red, and because roster data is
committed and only ages by wall clock, the maximum exposure past the 30-day window is one cron
interval (7 days).

**Remedy:** extend `_stale_notice` to also age `plan_models.last_verified` against the same
`observed_at` stamp it already uses for plans, for rows where `link_source='roster'`. The columns are
already there; this is a second SELECT and one more sentence. Citing test: a roster row dated outside
the window must make `stale_notice` non-null and name the plan.

### MINOR-3 — `schema.migrate()` is built but not wired to either read-path CLI (V3C-73)
`src/app/workflows/schema.py:151-163` · `src/app/workflows/recommend.py:308` · `src/app/workflows/coverage.py:146`

`migrate()` exists so "a disposable-but-persisted `advisor.db` from an earlier milestone would
[not] fail with *no such column*" (`schema.py:139-142`). It runs only inside `schema.connect`
(`schema.py:168-171`). Both CLIs that *read* a caller-supplied `--db` call bare `sqlite3.connect`
and therefore skip it.

**Failure scenario, reproduced this review** — a pre-M4-shaped `plan_models` (3 columns), populated,
driven through the real entry point:

```
$ python -m app.workflows.recommend --db old.db --subscription --task assistant
{"error": "db unusable: no such column: pm.link_source"}   exit 2
```

The migration's own citing test (`tests/unit/test_rosters.py:302`) calls `migrate()` directly — a unit
shim, exactly the shape V4C-50 asks you not to rely on ("at least one test through the real entry
point"). The control is unit-green and unreachable from the path it was written for.

**Why MINOR:** it **fails closed** — exit 2, loud, no wrong answer produced, no partial output. This is
a wiring/robustness defect, not a correctness hole.

**Remedy:** call `migrate(conn)` after opening in `recommend.main` (and see MINOR-4 for why `coverage`
wants a different fix), then move the citing test to enter through `main()` against a legacy-shaped DB.

### MINOR-4 — `coverage`'s read-only claim is asserted by convention, not enforced by the connection
`src/app/workflows/coverage.py:13` · `src/app/workflows/coverage.py:146`

The module docstring states the report reads the database and "never write[s] it", and that property is
load-bearing: a metric that mutates what it measures is not a metric. But `main` opens an ordinary
read-write handle (`sqlite3.connect(args.db)`), so the guarantee rests entirely on nobody adding a write
later. The citing test (`tests/unit/test_coverage.py:137`) only re-counts `plan_models` rows, so a write
to `scores`, `models`, or a schema change would pass it. Additionally, a read-write open of a database
with a hot journal can trigger recovery writes before a single SELECT runs.

**Remedy (cheap, turns the claim into a mechanism — the V4C-49 shape):**
`sqlite3.connect(f"file:{path}?mode=ro", uri=True)`. Any future write then raises
`sqlite3.OperationalError: attempt to write a readonly database`, which the existing
`except sqlite3.Error` already converts to exit 2. This also resolves the tension with MINOR-3:
`coverage` must **not** be routed through `schema.connect`, because that executes DDL — i.e. a write.

### MINOR-5 — `yaml.safe_load` is not resource-bounded; alias expansion exhausts memory
`src/app/workflows/rosters.py:99` (new this milestone) · `src/app/workflows/plans.py:134` (pre-existing, same class)

`safe_load` blocks arbitrary object construction and module import — correctly, and that is the part
that matters most — but it does **not** bound alias expansion. Measured this review: a ~1 KB document
with nested anchors driven through `parse_rosters` under a 1 GiB `RLIMIT_AS` raised `MemoryError`
after 9.96 s. Both the size check and the schema check happen *after* the parse, so no validation
protects the parse itself.

**Why MINOR:** the trust boundary is not crossed today. Both files are committed repository data
reviewed at every closure, and the only other way in is an operator typing a path into
`--check-staleness`. There is no untrusted producer.

**Why it is worth writing down anyway:** the boundary is exactly what M5 changes. The moment an API
milestone accepts an uploaded or fetched YAML document, this becomes a one-request DoS, and the fix is
much cheaper now than as a retrofit.

**Remedy:** a length guard before the parse in both loaders
(`if len(raw) > MAX_DOC_BYTES: raise _fail(...)`) — one line, one citing test, and it holds whatever
M5 does to the trust boundary.

### MINOR-6 — ledger row W-001 is accurate, but its owning milestone has closed unresolved
`docs/warnings.ledger.md:11`

Verified against this review's scan: gitleaks reports **exactly one** finding, at
`docs/reviews/m2-security-review.md:8` — the same zero-entropy false positive (the ADR compliance
label following the word "APIs" in prose), at the path and line the row records. The row's content is
**correct and current**, and the second finding the M3 review reported (the ledger row's own earlier
wording re-tripping the rule) is genuinely gone — the M3 rewording worked, so M4 introduced no new
finding and cleared one.

What has drifted is the row's *accountability*: status is `ESCALATED` with owning milestone **M3**, and
M3 closed on 2026-08-15 with the proposed remedy (a scoped `.gitleaks.toml` allowlist for the `D-\d+`
label pattern) not landed — `.gitleaks.toml` is unchanged since commit `8152490` (M1) and contains no
such allowlist. V4C-77 says a warning may not survive the close it was raised in.

**I do not waive, baseline, or suppress this finding, and no agent may** (AGENTS.md §3 / v3.3 "no agent
suppression"). **Remedy — owner decision at this closure:** either land the scoped allowlist, or
re-stamp the row's owning milestone to M4 with a fresh reason. Either way the row must not be carried
into M5 still stamped M3.

### NOTE-1 — `equivalent_plans` is a flat name list over a table with no UNIQUE name
`src/app/workflows/subscribe.py:288`

Group *membership* is correctly resolved by `plan_id` (`subscribe.py:274-283`, with the citing test the
W4 record names), and the reasoning in `subscribe.py:257-263` is sound. But the *rendered* output —
both `equivalent_plans` and the names inside the note — uses `r.plan`, and `plans.name` carries no
UNIQUE constraint. Two same-named plans would print a duplicated name in the sentence and collapse to
one entry in `equivalent_plans` (it is built through a `set`). Not false, but lossy. This overlaps
finding L-2 in `m4-w4-equivalence.md` §5, already owned by M5 with the API contract — flagging only
that the display side, not just the machine-consumer side, is affected.

### NOTE-2 — the note's "indistinguishable in quality" clause is a category-scoped claim
`src/app/workflows/subscribe.py:302`

*"They are indistinguishable in terms of quality"* is true on the category's primary benchmark, which is
what D-105 defines quality to mean here. It is not a claim about breadth: a plan that includes the same
top model **plus** several others is genuinely better and the sentence flattens that. The scoping is
consistent with D-105 and correctly documented in the field's docstring, so this is a NOTE rather than a
finding — but if M5 widens what "quality" means, this sentence must be revisited with it.

### NOTE-3 — the two new f-string SQL sites are invisible to bandit
`src/app/workflows/schema.py:155,159`

Both are safe (module constants only, `_MIGRATIONS` at `schema.py:144-148`), but bandit's B608 does not
match `PRAGMA` or `ALTER TABLE`, so unlike the M3-era `reset_source` at `schema.py:183` they carry no
scanner signal and no `# noqa: S608` marker explaining why they are acceptable. A future reader has
nothing telling them the interpolation was deliberate and audited. Suggest adding the same
`# noqa: S608` + one-line justification the existing site carries, so the pattern is uniform and the
next person does not have to re-derive it.

### NOTE-4 — validators ignore unknown keys
`src/app/workflows/rosters.py:53-91` · `src/app/workflows/plans.py:40-93`

Both validators read known keys and silently ignore the rest (`data/rosters.yaml`'s `note:` field relies
on this). A misspelled **required** key is caught loudly, which is the important half. A misspelled
optional key is not. Low impact at present because there is effectively one optional key; worth strict
rejection if the schema grows.

---

## 4. Tooling output (verbatim)

### `make secrets` — gitleaks

`gitleaks` was not on PATH in this container (`make secrets` exits 1 with
`Install gitleaks: brew install gitleaks` — a tool-availability failure, not a scan result). I installed
gitleaks **8.28.0** to `/tmp` (outside the repo; nothing in the working tree was touched) and re-ran the
Makefile target so the invocation is the real one — `gitleaks detect --source . --no-git -v`:

```
Finding:     ...oth documented data APIs, D-101-compliant; arena.ai site never...
Secret:      D-101-compliant
RuleID:      generic-api-key
Entropy:     3.640224
File:        docs/reviews/m2-security-review.md
Line:        8
Fingerprint: docs/reviews/m2-security-review.md:generic-api-key:8

8:44PM INF scanned ~2441780 bytes (2.44 MB) in 380ms
8:44PM WRN leaks found: 1
make: *** [Makefile:88: secrets] Error 1
```

**Result: 1 finding, 0 secrets.** It is the ledgered W-001 false positive, unchanged — the "secret" is
the literal string `D-101-compliant`, an ADR compliance label in English prose, zero entropy in
substance. **M4 introduced no new gitleaks finding and cleared one** (2 findings at M3 closure → 1 now).
Accountability follow-up in MINOR-6. Not waived.

### `make deps` — pip-audit

```
.venv/bin/python -m pip_audit
No known vulnerabilities found
Name          Skip Reason
------------- ----------------------------------------------------------------------------
model-ranking Dependency not found on PyPI and could not be audited: model-ranking (0.1.0)
```

**Result: 0 vulnerabilities, 0 advisory IDs.** The single skip is this project's own editable local
package, which by definition has no PyPI advisory record — expected, not a gap. M4 added no dependency:
`pyproject.toml` is not in the milestone diff.

### `bandit -r src -q` (supplementary, for comparison with the M3 record)

```
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through
   string-based query construction.
   Severity: Medium   Confidence: Medium
   Location: src/app/workflows/schema.py:183:19
183  conn.execute(f"DELETE FROM {table} WHERE source = ?", (source,))  # noqa: S608

Total issues (by severity): High: 0  Medium: 1  Low: 0
```

Identical to M3: the one known allowlist-gated identifier, which has its own negative test
(`tests/unit/test_schema.py:54`). **No new bandit finding in M4.** See NOTE-3 for the two sites bandit
structurally cannot see.

### Gate suite

`pytest` 191 passed / 5 skipped (contract self-skips reported, V3C-44) · `ruff` clean · `mypy` clean
(23 files) · `bootstrap-check` PASS (0 fail / 2 pre-existing warn) · `make check-records` PASS.

---

## 5. Verdict

## **PASS** — 0 BLOCKING, 6 MINOR, 4 NOTE. M4 may close Stage 4.0.

Nothing in this milestone can execute code, reach the network, leak a credential, take an unbounded
input from an untrusted party, or write a database it claims to only read. Every new control fails
closed and carries a negative test that fails if the control is removed. No security-invariant test was
weakened or deleted; the test diff is +919/-16 and every removed line was replaced by a **stricter**
assertion. The secret-scan surface improved (2 findings → 1) and the dependency surface is clean and
unchanged.

The honest summary of the risk that remains: this product's real security property is that it never
tells the user something false, and the two findings closest to that line are both **disclosure**
defects rather than fabrications — one sentence that names the wrong document as the source of a true
fact (MINOR-1), and one staleness clock that is measured in CI but never surfaced in the answer
(MINOR-2). Both are small code changes with obvious citing tests, and both were already visible to the
waves that shipped them, which is a good sign about the review chain rather than a bad one.

### Owner K.10 checklist at the milestone commit

1. **MINOR-6 / W-001 (do not skip — scanner accountability):** land the scoped `.gitleaks.toml`
   allowlist, or re-stamp the ledger row's owning milestone from M3 to M4 with a reason. It may not
   enter M5 stamped with a milestone that has closed.
2. **MINOR-1:** decide the one phrasing for `equivalence_note` when a group mixes plan-page and roster
   links. This is m4-w4 L-1 and its owning milestone is this closure.
3. **MINOR-2:** either wire roster `last_verified` into `_stale_notice`, or ledger the gap explicitly
   with an owning milestone — the CI leg alone is a control the user never sees.
4. **MINOR-3 / MINOR-4:** one line each — `migrate(conn)` in `recommend.main`; `mode=ro` URI in
   `coverage.main`. Move the migration's citing test to the real entry point.
5. **MINOR-5:** a document-size guard before both `safe_load` calls, before M5 opens an input surface
   that changes the trust boundary.

### Invariants proposed for the register

- **INV-15 roster ingest is fail-closed and source-scoped:** a roster naming an unknown plan aborts the
  whole ingest; a constraint violation rolls the roster set back whole; only `link_source='roster'` rows
  are replaced, so plan-page links survive independently. Citing tests: `tests/unit/test_rosters.py:127`,
  `:152`, `:165`.
- **INV-16 link provenance is mandatory and enumerable:** every `plan_models` row records which producer
  created it (`link_source`), and there are exactly two producers (V3C-101). Citing tests:
  `tests/unit/test_rosters.py:101`, `:266`, `:290`.
- **INV-17 health and coverage fail toward disclosure:** unknown evidence age reads as stale, never
  fresh; zero coverage in any category exits non-zero. Citing tests: `tests/unit/test_coverage.py:147`,
  `:120`.
- **INV-18 rounding happens once, at the output boundary:** ranking, Pareto and threshold comparisons
  use raw scores; every user-facing delta is computed from the rounded values the JSON carries, so prose
  can never contradict a field. Citing tests: `test_rounding_never_reaches_the_pareto_comparison`,
  `test_a_sub_rounding_gap_never_prints_as_a_zero_delta` (`tests/unit/test_subscribe.py`).
- **INV-19 (proposed, NOT yet ratifiable) roster evidence ages in the output:** blocked on MINOR-2 —
  there is no citing test today because there is no behaviour to cite. Ratify only once
  `_stale_notice` reads the roster clock.
