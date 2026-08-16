---
record_type: register
id: m5-security-review
status: ratified
date: 2026-08-16
---
# M5 Stage 4.0 — Security Review (fresh eyes, milestone closure, BLOCKING gate)

Reviewer: independent Security-Reviewer subagent. I authored none of this code and none of
these records. Surface: `38eaa17..HEAD` — 17 commits, 55 files, +7035/-210. Date: 2026-08-16.

Effective risk tier: **HIGH** for the milestone surface, not the plan's LOW-MED product label.
Three of four waves self-declared HIGH (`docs/plans/m5-plan.md:207-209`), and the milestone adds
a schema **migration command**, which auto-escalates under P-005 and is a named
`permission-matrix.md:153` human-review trigger.

## VERDICT: PASS (conditional) — 1 BLOCKING, 7 MINOR, 8 NOTE

The BLOCKING finding is a disclosure defect on live seed data, not a code-execution, credential,
network, or data-destruction hole. See §5 for the exact condition and the owner gate it attaches to.

---

## 1. Scope + method

**Commits walked** (`git log --oneline 38eaa17..HEAD`):

| commit | wave |
|---|---|
| `57de98e`..`265126d` | M5 plan approval + Epoch freshness corrections |
| `0e38a6d`..`96ba91d` | W1 Epoch client, board measurement, Gemini disclosure |
| `964a389`..`de7cb0e` | W2 effort as data, `scores.effort`, migration |
| `62a9166`..`5eb3e15` | W3 DeepSWE board application, `agentic-coding` |
| `bc55bd4`, `828f623` | W4 attribution, `migrate` command, carried ledger |

**Read in full:** `src/app/clients/{epoch,deepswe,arena,fakes}.py`,
`src/app/workflows/{schema,epoch,coverage,rank,recommend,subscribe,categories,ingest,registry,board_measurement}.py`,
`data/epoch-source.yaml`, `.github/workflows/contract-tests.yml`, `.language-allow`,
`README.md`, and the entire `tests/` diff.

**Read first, to stay in shape and not re-litigate:** `docs/plans/m5-plan.md`,
`docs/plans/m5-wave-{1,2,3,4}-close.md`, `docs/plans/m5-wave-4-implementation.md`,
`docs/reviews/m4-security-review.md`, `docs/reviews/m5-w1-board-measurement.md`,
`docs/reviews/m5-w3-board-application.md`, `docs/security-baseline.md`, `AGENTS.md`,
`permission-matrix.md` §11, `docs/warnings.ledger.md`, `docs/decisions.md` D-100..D-111,
`subagent-profiles/Security-Reviewer.md`.

**Commands actually run** (no git write command was issued at any point):

- `make deps` (pip-audit) — §4
- `make secrets` (gitleaks 8.28.0, installed to `/tmp`, nothing in the tree touched) — §4
- `.venv/bin/python -m pytest` — **266 passed, 12 skipped**
- `EPOCH_DATA_DIR=<owner bundle> .venv/bin/python -m pytest` — **273 passed, 5 skipped**
  (the 5 are the network contract self-skips, reported not silent — V3C-44); coverage 84% -> 90%
- `ruff check src tests` clean · `mypy src` clean (27 files) · `make check-records` PASS
- `bash scripts/bootstrap-check.sh` — PASS, 0 fail / 2 warn (both pre-existing)
- `bandit -r src -q` — 1 Medium, the known allowlist-gated identifier, unchanged from M3/M4

**Live probes executed against the code.** The owner's unpacked Epoch bundle is present at
`/mnt/user-data/uploads/terminal_output/model_ranking/epoch_data`, so every probe below ran on
real data through real entry points. `git status --porcelain` was clean before and after.

1. Built a full database from `data/plans.yaml` + `data/rosters.yaml` + the real Epoch
   SWE-bench and DeepSWE boards + the pinned SWE-bench baseline, then drove
   `python -m app.workflows.recommend --subscription` and `python -m app.workflows.coverage`
   through their real `main()` entry points for `coding` and `agentic-coding` at all three budgets.
2. Reproduced both published measurement records end to end via
   `python -m app.workflows.board_measurement` (§3, licence/number spot checks).
3. Symlinked a file outside the bundle directory over `swe_bench_verified.csv` and drove
   `EpochClient.fetch_raw()` (MINOR-4).
4. Drove `coverage --db` with a path containing a `?`, and separately compared the URI that
   `coverage.main` builds against the one `schema.main` builds (MINOR-3).
5. Drove `python -m app.workflows.schema migrate --db` against six database shapes: a populated
   pre-M5 legacy schema, a foreign SQLite file with a look-alike `scores` table, a non-database
   file, a missing path, an empty SQLite file, and a directory (§2 migration rows).
6. Ran an alias-expansion document through `parse_epoch_source_doc` (NOTE-3).
7. Fault-injected `_pick(effort=...)` in `subscribe.py` and `recommend.py` to establish test
   coverage of BLOCKING-1. Restored **in place**, verified byte-identical by `md5sum -c`
   (`54f16ae3d7f00e9339d6854f35a0c46f`, `504d4425fb18382217137b228f92fc86`), tree clean,
   266 passed again. No `git checkout`/`restore` was used.

---

## 2. Baseline walk (`docs/security-baseline.md` + project invariants)

| # | Control | Verdict | Evidence |
|---|---|---|---|
| 1 | No plaintext creds / no default-admin (**GATE** V3C-11) | **PASS** | `bootstrap-check.sh` C7 `[ ok ]`. Grepped the whole M5 added-line set for `api[_-]?key\|secret\|password\|token\|bearer\|authorization\|aws_\|PRIVATE KEY\|client_secret`: every hit is prose or the linguistic sense of "token" (`registry.py:150` "Preview/date tokens remain aliases"; `rank.py:34` "licence token"; `test_epoch_ingest.py` writes the four-letter word `secret` as a decoy CSV body proving the client does not read a non-allowlisted file). Zero credential-shaped literals. |
| 2 | Server-side authz on every mutating route (V3C-12) | **N/A** | No HTTP surface beyond `/health` (D-100); `src/app/adapter/` is untouched in the M5 diff. The mutating surface is local CLIs — see the write-capability table below. |
| 3 | CORS allowlist (V3C-13) | **N/A** | No CORS config, no browser-reachable API. Unchanged since M2. |
| 4 | Validate security-critical config at startup, fail prod (V3C-51) | **PASS (analogue)** | The project's equivalent — *thresholds and clocks live as DATA and their absence must abort* — is extended correctly. `epoch.py:44-61` rejects an unexpected key set, a wrong `schema:`, a non-positive or boolean `staleness_days`, an incomplete `source:` block, a wrong source id, a `source_url` that is not the documented bundle, and a non-canonical `last_verified`. `epoch.py:111-121` fails loud if the committed clock is unreadable. No silent default anywhere in the new parser. |
| 5 | Encrypt creds/PII at rest (V3C-56) | **N/A** | No credential and no PII is stored. SQLite holds public benchmark scores, public list prices, public URLs. The Epoch bundle is public CC-BY data. |
| 6 | Generic client errors; detail server-side | **PASS (scoped)** | The only "client" is the operator at a terminal, so path detail is appropriate. All new CLIs return typed exit codes with no traceback: `schema.py:376,397` (2 = not found / unusable), `coverage.py:270,277,290,310` (2 = usage/DB, 1 = zero coverage), `epoch.py:85,92,97,102` (2 = usage/parse, 1 = stale), `board_measurement.py:609` (2). Filesystem paths do appear in `SourceError` text (`epoch.py:84,89`, `deepswe.py:60,65`) — appropriate for an operator CLI, and no file *content* is ever echoed, so a symlinked target's bytes cannot leak through an error string. |
| — | Control-class fail direction (V3C-33/45) | **PASS** | Every M5 control fails CLOSED. `ingest.py:167-172,193-198` — a source without `last_verified` aborts that source; `epoch.py:177-179`, `deepswe.py:103-105` — missing or non-HTTPS provenance aborts; `epoch.py:197-199`, `deepswe.py:150-151` — a board with zero usable rows aborts rather than storing nothing silently; `ingest.py:114-118` — an out-of-domain effort value aborts before the write; `_store_scores` writes inside `with conn:` so a failed ingest leaves the prior working set intact (`tests/unit/test_deepswe_workflow.py` proves this); `subscribe.py:269,276` — a selected roster link with incomplete provenance raises rather than printing an undisclosed pick. The one place the direction is arguably not held is MINOR-5 (undated evidence produces no notice). |
| — | V3C-73 built != wired | **PASS with one exception** | Every new control is reachable from a real entry point: `epoch --check-staleness` runs unconditionally in CI (`contract-tests.yml:51-54`); `schema migrate` has a real module-entry test; `coverage` and `recommend` are driven through `main()` in tests. The exception is `rank.export_ranking`, which has **no production caller anywhere** in `src/`, `scripts/`, `Makefile`, or `.github/` — only tests call it. That is what keeps MINOR-2 at MINOR. |
| — | V3C-74 negative test per security invariant | **PASS with one exception** | `tests/unit/test_epoch_ingest.py` rejects a URL, a bad clock, a missing board, a bad shape and a non-allowlisted file; `test_deepswe_workflow.py` rejects missing/non-local boards, invalid clocks, release-date promotion, and proves an ingest failure preserves the prior working set; `test_schema.py` covers legacy migration, refusal, idempotence and rollback; `test_coverage.py` covers the four-state partition, the 59/60 boundary and unparseable selected dates. The exception is the Trap-2 guard — MINOR-7, a test that cannot fail for the reason it documents. |
| — | INV-1 inert payloads | **PASS with a caveat** | Zero `yaml.load` / `Loader=` / `eval(` / `exec(` / `pickle` / `os.system` / `subprocess` / `shell=True` in `src/` (grep). Only `yaml.safe_load`, now at four sites: `plans.py:134`, `rosters.py:99`, `clients/aider.py:66`, and new this milestone `workflows/epoch.py:41`. No parse path can construct an arbitrary object or import a module. Caveat = NOTE-3 (resource exhaustion, not code execution). |
| — | INV-2 parameterised SQL | **PASS with one exception** | I read every SQL string added in M5. `coverage.py:105,109,114,119-130,171,240` bind with `?`; `rank.py:115-117,131-133,144-146,162-216` use `?` and named parameters, and the new `(:effort IS NULL OR effort = :effort)` predicate is a bound parameter, not interpolation; `subscribe.py:121,134-191,228,256,262` are all named/`?`; `board_measurement.py` issues no SQL of its own; `registry.py:270-290` binds `?`. The f-string SQL in `schema.py:229,233,324` interpolates only values derived from the module's own `_MIGRATIONS` constant and `_ddl_columns()` (parsed from the module's own `DDL` constant) — no runtime or data value reaches them. **The one exception is `schema.py:171`**, `PRAGMA index_info({row[1]})`, where the identifier comes from the *database under inspection*. That is MINOR-6. `bandit -r src -q` = 1 Medium, the same known allowlist-gated `reset_source` identifier at `schema.py:365`, unchanged from M3/M4. |
| — | INV-6 network-free default suite | **PASS, improved** | The two new clients make **no** outbound call: they read one allowlisted filename from a local directory (`epoch.py:80-90`, `deepswe.py:56-66`). `EPOCH_BUNDLE_URL` is provenance metadata only — grep confirms it is never fetched. Egress *shrank* this milestone: W-007 removed Arena's `/rows` fallback (`arena.py:143-152`), and three tests now assert the `/rows` endpoint is never called. `pytest` = 266 passed / 12 skipped, the skips being `RUN_CONTRACT_TESTS`- and `EPOCH_DATA_DIR`-gated. |
| — | INV-8 documented endpoints only (D-101) | **PASS** | No new endpoint. Epoch acquisition is deliberately out of runtime: `epoch.py:1-6` states it, `data/epoch-source.yaml` records the acquisition clock, and CI ages it (`contract-tests.yml:51-54`). Artificial Analysis is absent from the diff (grep: zero hits). |
| — | INV-10 CI least-privilege | **PASS** | The single new CI step is an unconditional step of the already-unconditional `plan-staleness` job (`contract-tests.yml:51-54`), carries no secret and no `${{ }}` in its run body, and inherits `permissions: contents: read`. `make pin-check` green. |
| — | INV-11 tests never disable TLS | **PASS** | grep `verify=False\|trust_env\|ssl._create` across the repo = zero hits. |
| — | No LLM in the data or scoring path (D-104) | **PASS** | Every number and string in the M5 output is derived from DB values, module constants, or pure arithmetic. `effort_disclosure` (`recommend.py:151-171`), `_budget_notice` (`subscribe.py:322-326`), and the roster staleness sentence (`subscribe.py:279-288`) are f-strings over DB columns. No model call anywhere in the diff. |
| — | Unmatched names dropped AND counted, never guessed | **PASS, strengthened** | The M5 closure probe found and fixed a live swallow: `kimi-k2.5` (73.8) and `kimi-k2.6` (76.7) both folding into `kimi-k2`, so `MAX()` published the newer model's score under the older model's name (`registry.py:113-118`, guarded variant rules). Verified on the real board: the DeepSWE reconciliation drop list is exactly `muse-spark-1.1` and `kimi-k3_max` — both counted, neither guessed. |
| — | Migration: can it destroy or truncate data? | **PASS** | Probed on a populated pre-M5 legacy database. `migrate` returned exit 0, applied 4 changes, **preserved every row**, stamped `effort='unspecified'`, and left **no** `scores__m5_effort` table behind. Re-run returned `applied: []` — idempotent. The rebuild widens the `scores` UNIQUE key from 5 to 6 columns (`schema.py:207`), and a widened UNIQUE cannot produce an INSERT conflict, so the `INSERT ... SELECT` at `schema.py:210-218` is structurally incapable of silently dropping rows. |
| — | Migration: atomic under failure? | **PASS** | `main()` runs `_apply_ddl` + `_migrate` inside an explicit `BEGIN IMMEDIATE` (`schema.py:390-393`) with `rollback()` on `sqlite3.Error` (`schema.py:394-396`) and `close()` in `finally` (`schema.py:399-401`) — and SQLite rolls back an open transaction on close, so a non-`sqlite3.Error` exception is also safe. SQLite DDL is transactional, so the `DROP TABLE scores` at `schema.py:219` is undone by rollback. Verified: the foreign-database probe left the target file **byte-identical** (md5 unchanged). |
| — | Migration: does it refuse a database it should refuse? | **PASS** | All six probes fail closed with exit 2 and a JSON error, never a traceback: foreign look-alike `scores` -> `unsupported scores schema; missing columns: [...]` and the file was not modified; non-database file -> `file is not a database`; missing path -> `db not found`; **empty SQLite file -> `not a model_ranking database`, size 0 before and after** (it refuses to bootstrap a schema into an unknown file); directory -> `db not found`. The validator derives its requirement from the shipped DDL (`schema.py:269-301`) rather than a hand-written list, so a column added tomorrow is covered tomorrow — this is the W4 BLOCKING-1 fix and it is structurally correct. |
| — | Migration: read-write only when it must? | **PASS with a note** | `schema.py:381-382` opens `mode=rw` (**not** `rwc`, so it cannot create) and only after `path.is_file()`. It builds the URI with `path.resolve().as_uri()`, which percent-encodes `?`, `#` and `%` — I verified this is immune to the query-injection that defeats `coverage` (MINOR-3). Note: validation reads through the already-rw handle before `BEGIN IMMEDIATE` (NOTE-6). |
| — | Migration: can a half-migrated state escape? | **PASS** | `schema.py:328-329` refuses outright if `scores__m5_effort` exists, naming it an incomplete prior migration. On the `connect()` path the leftover table makes the bare `CREATE TABLE` at `schema.py:192` raise, which rolls back and re-raises (`schema.py:349-352`). Both directions fail closed. `schema.py:330-338` additionally refuses a database whose `scores.effort` already carries a value outside the six-value domain. |
| — | Read paths cannot write | **PARTIAL — MINOR-3** | `coverage.main` does open `mode=ro` (`coverage.py:285`) and the intent is right; the URI is string-built rather than encoded, so a `?` in the path defeats it. `recommend.main` opens a plain read-write handle (`recommend.py:357`) — correctly, because `recommend()` genuinely writes (`build_price_medians` does `DELETE FROM px_median` + `INSERT`, `rank.py:143-151`). See NOTE-7 on the wave-4 checklist wording. |
| — | Epoch CC-BY attribution ships where the data is served | **PASS on the required surfaces** | Verified verbatim against the bundle's own `README.md` `### Citation` block. The string at `rank.py`/`epoch.py:36-40` reproduces Epoch's prescribed text exactly, with the project's `(CC-BY-4.0)` token appended. Present in: the model recommendation payload's `sources` (probed live), the subscription payload's `sources` (probed live, `coding` and `agentic-coding`), the export JSON's `attribution` (probed live), and `README.md:90`. Written once, in one spelling (`epoch.py:30-40`) — the W4 MINOR-8 fix holds. Gaps: the CSV half of the export (MINOR-2) and secondary-benchmark sources generally (MINOR-1). |
| — | Published numbers reproduce from the code | **PASS** | Re-ran `python -m app.workflows.board_measurement` against the owner's bundle. Every headline number in `docs/reviews/m5-w1-board-measurement.md` reproduces exactly: baseline 1/10 via Google AI Pro / Gemini 3 Pro / 77.4 / `live-SWE-agent` / 2025-11-20; Epoch 35 CSV rows, 33 stored, 2 skipped, 5/10, **2 fresh 3 stale 5 unscored**; DeepSWE 50/13 stored/37 filtered, 6/10, 6 undated; FrontierCode 25/20/5, 3/10; TerminalBench 204/181/23, 5/10, 5 stale; Aider 77/71/6, 0/10. Gemini contradiction: 75.6 vs 11.8, ratio 6.4. Every headline number in `docs/reviews/m5-w3-board-application.md` reproduces from the live database: effort distribution high 13 / low 8 / max 9 / medium 9 / xhigh 10 (sum 49); zero non-null `run_date`; drop list exactly `muse-spark-1.1` and `kimi-k3_max`; all six selected `high` rows and their `max` comparables (Perplexity Max 72.8 -> 73.6; ChatGPT Pro 69.4 -> 72.7; Perplexity Pro 53.8 -> 69.6; three Google plans 11.8 with no comparable); coding 2/3/0/5 and agentic 0/0/6/4. **No published number failed to reproduce.** |
| — | Security-invariant test modified or deleted? | **PASS — none weakened** | `git diff 38eaa17..HEAD -- tests/` is **+2171/-22**, no test file deleted. Three Arena tests were *renamed and strengthened*, not weakened: each now additionally asserts `rows_route.call_count == 0`, i.e. the removed W-007 fallback endpoint is never touched (`test_arena_client.py:74-107`). The one loosened-looking assertion, `assert tuple(payload["attribution"]) == ATTRIBUTIONS` -> `== (ARENA_ATTRIBUTION, PRICING_ATTRIBUTION)` (`test_categories.py:166-176`), is **stricter**: it now also asserts `"Epoch AI" not in attributions` and `"swebench.com" not in attributions`, which is the W4 BLOCKING-2 fix. `set(CATEGORIES) == {...}` gained a member and an extra assertion. Nothing was removed without a replacement that says more. |
| — | V4C-79 English-only | **PASS** | The four `.language-allow` additions each carry a written reason and each is genuine: two are test files asserting Turkish product strings, two are records quoting a shipped or rejected Turkish sentence verbatim as measured evidence. Spot-checked all four against their stated reason; each matches. `make check-records` PASS. |
| — | V4C-61 verifier != implementation | **PASS** | `coverage.plan_evidence_health` deliberately reuses `subscribe.plan_ranking` so that health is computed on the *same* selected row the engine ranks (`coverage.py:153-163`) — that is a correctness requirement, not a self-check, and the independent verification is `board_measurement._engine_measurement`, which cross-checks `coverage.scoreable_plans == len(plan_ranking(...))` and raises if they disagree (`board_measurement.py:383-384`). |

### CLI write-capability table

| entry point | file:line | writes to the DB? | verified |
|---|---|---|---|
| `app.workflows.coverage --db` | `coverage.py:262-312` | **No** — SELECT only, opened `mode=ro` | Read of the module confirms no INSERT/UPDATE/DELETE/DDL. The *mechanism* is defeatable — MINOR-3. |
| `app.workflows.schema migrate --db` | `schema.py:368-408` | **Yes, by design and only here** | `mode=rw`, never `rwc`; refuses six wrong shapes; atomic; idempotent; rows preserved (probed) |
| `app.workflows.epoch --check-staleness` | `epoch.py:76-104` | **No** — never opens a database at all | `epoch.py:94` reads one file and returns; pure over the file text |
| `app.workflows.board_measurement --bundle-dir` | `board_measurement.py:587-612` | **No** — every database is `:memory:` via `connect()` (`board_measurement.py:359`) | Docstring claim "No files or databases are mutated" verified by read; all outputs go to stdout |
| `app.workflows.recommend --db` | `recommend.py:329-392` | **Yes** — `build_price_medians` rewrites `px_median` | `rank.py:143-151`. Not a read-only CLI — NOTE-7 |

---

## 3. Findings

Ordered by how close each comes to the product's actual security property: that the engine may
never assert something false to the user.

### BLOCKING-1 — the shipped coding answer publishes a max-effort score with the effort qualifier nulled
`src/app/workflows/subscribe.py:308` · `src/app/workflows/recommend.py:188` · `src/app/workflows/categories.py:32-43`

`_pick` sets the pick's effort field from the **policy** (`spec.ranking_effort`) instead of from the
**evidence** (`row.effort`). For `coding`, whose `CategorySpec` carries `ranking_effort=None`, that
means the answer reports `effort: null`, `higher_effort: null`, `higher_effort_score: null` and
`effort_note: null` — for a score that was measured at an explicit effort level. The correct value
is already in hand: `plan_ranking` selects it into `PlanRank.effort` (`subscribe.py:174,209`) and
`category_ranking` into `RankingRow.effort` (`rank.py:199,227`). It is then discarded.

**Failure scenario, reproduced this review on the shipped seed data.** Real
`data/plans.yaml` + `data/rosters.yaml` + the owner's real Epoch SWE-bench board, driven through
the real CLI `python -m app.workflows.recommend --db <db> --subscription --task coding
--budget sinirsiz`:

```
"ranking_effort": null,
"picks": [ { "label": "best_quality", "plan": "Perplexity Pro", "score": 78.7,
             "scored_by_model": "GLM-5.2", "harness": "inspect_ai",
             "effort": null, "higher_effort": null, "effort_note": null } ]
```

and the row that 78.7 comes from:

```
raw_name      effort  score  harness      source                      run_date
glm-5.2_max   max     78.7   inspect_ai   epoch_swe_bench_verified    2026-06-25
```

The headline number of the milestone's headline category is GLM-5.2's **max reasoning-effort**
result, and the answer says nothing about that. This is verbatim Trap 2 of the signed plan
(`docs/plans/m5-plan.md:95-103`): *"MAX() silently publishes the best-case number — advertising a
performance level the buyer's plan may not even offer."*

Three things make it a finding rather than a nuance:

1. **The product contradicts itself across its own artifacts.** `rank.export_ranking` writes
   `effort,max` for the same model in the same run (`rank.py:275`, verified: the CSV row reads
   `GLM-5.2,Zhipu,78.7,inspect_ai,epoch_swe_bench_verified,max,...`), while the recommendation
   payload for that model reads `effort: null`. Same engine, same score, two different statements
   about what produced it.
2. **The comparison itself spans effort levels.** The `coding` ranking has no effort predicate, so
   `MAX(score) GROUP BY model_id` compares rows measured at different settings. Measured on the
   real Epoch board: `claude-opus-4-7_max` 83.5 (max), `gpt-5.5-pre-release_xhigh` 80.6 (xhigh),
   `gemini-3.5-flash_high` 79.3 (high), `glm-5.2_max` 78.7 (max), `gpt-5-mini-..._medium` 64.7
   (medium), plus 24 rows at `unspecified`. Five levels ranked against each other as one scale.
   The owner's Q1 ruling was *"comparisons happen at a single level so they stay fair"*
   (`docs/plans/m5-plan.md:14-16`); `agentic-coding` holds that, `coding` does not.
3. **Nothing tests it.** I fault-injected `effort=row.effort` into both `_pick` functions and the
   full suite stayed **266 passed / 0 failed**. Every REQ-REC-011 citing test in
   `tests/unit/test_effort.py:245,272` drives `--task agentic-coding`; no test exercises the effort
   field of the `coding` answer in either direction. (Injection reverted in place; md5 verified
   byte-identical; suite re-run green.)

**Why BLOCKING and not MINOR.** It fires on shipped seed data today, on the top pick of the
category this milestone exists to rescue; the plan names this exact scenario as the condition on
which the ingestion is honest; and `permission-matrix.md:190` says *"if unsure between BLOCKING and
MINOR, default UP"*. It is not exploitable in a memory-safety sense — it is exploitable in the only
sense this product has.

**Remedy (small, and the code already holds the value).** Two lines plus a decision:

- `subscribe.py:308` and `recommend.py:188`: publish `row.effort` (the evidence), and keep
  `spec.ranking_effort` where it belongs, on the `Recommendation`/`SubscriptionRecommendation`
  policy field it already occupies (`recommend.py:318`, `subscribe.py:526`).
- Extend `effort_disclosure` (`recommend.py:151-171`) with the effort-free branch: when
  `spec.ranking_effort is None` and `row.effort != 'unspecified'`, emit a sentence naming the level
  the published row was measured at. The exact wording is the owner's call (Turkish product string).
- Citing test: build a `coding` fixture whose selected row carries `effort='max'` and assert the
  payload names it. That test is red today.
- Owner decision, separate from the code: whether `coding` should acquire a `ranking_effort` so the
  cross-model comparison is at one level, per the Q1 ruling. That is a data edit to
  `categories.py:32-43`, not an engine change.

### MINOR-1 — `attributions_for` never sees the secondary benchmark, so a served score can go uncited
`src/app/workflows/rank.py:57-71` · `src/app/workflows/rank.py:284` · `src/app/workflows/recommend.py:320`

W4 BLOCKING-2 correctly stopped payloads claiming sources they never read. The fix derives the
citation list from `{r.evidence_source for r in rows}` — but `evidence_source` is the **primary**
benchmark's source only (`rank.py:198,228`). The payload also serves `secondary_score` and, in the
export, `secondary_cost`, which come from a *different* source (`rank.py:182-195`), and that source
is never passed to `attributions_for`. The `raise` at `rank.py:67-69`, written precisely so that
"an unattributed source raises rather than silently dropping a CC-BY obligation", cannot fire on a
source it is never handed.

**Failure scenario, reproduced this review.** A database carrying the real Epoch SWE-bench board as
the only primary coding evidence, plus Aider polyglot rows as the secondary:

```
primary evidence sources in ranking: {'epoch_swe_bench_verified'}
sources: [ "Pricing data: ...", "Epoch AI, 'AI Benchmarking Hub'. ... (CC-BY-4.0)" ]
pick: secondary_score 65.0 | confidence High
      | confidence_basis "two independent benchmarks (SWE-bench Verified + Aider polyglot)"
```

The payload names *Aider polyglot* in a user-facing string, upgrades its own confidence to **High**
on the strength of it, ships its number — and omits its citation. Apache-2.0 attribution is carried
by the same `SWEBENCH_ATTRIBUTION` string that is missing here.

**Why MINOR and not BLOCKING.** It does not fire on the current seed. On the full live database the
citation is present — but only by coincidence: some models' best primary rows still come from
`swebench`, and one citation string happens to cover both `swebench` and `aider`. The coincidence
is fragile in the direction the milestone is travelling: `category_ranking` breaks ties by
`run_date DESC` (`rank.py:175`) and Epoch's dates (2026-06-25) beat swebench.com's (2026-02-26),
so the more Epoch coverage grows, the closer this gets to firing. The plan itself says the
swebench.com feed has stopped publishing (`docs/plans/m5-plan.md:36-40`).

**Remedy.** Collect the secondary source alongside the primary in `category_ranking` (one extra
correlated subselect, next to the six already there at `rank.py:196-203`), add it to
`RankingRow`, and union it into the set passed to `attributions_for` at `rank.py:284` and
`recommend.py:320`. Citing test: an Epoch-primary + Aider-secondary ranking must carry both
citations.

### MINOR-2 — the CSV half of the export ships CC-BY data with no attribution and no blend note
`src/app/workflows/rank.py:276-289`

`export_ranking` writes two artifacts. The JSON carries `note` (the blend formula) and
`attribution`. The CSV carries neither — only the ranking rows, including
`evidence_source=epoch_swe_bench_verified`. Verified: the generated
`coding_ranking.csv` contains zero occurrences of `Epoch` or `CC-BY`.

Two shipped claims are false about that file. `rank.py:6-7`: *"Blended price = ... (documented in
every export)"*. `README.md:91-92`: *"This citation also travels in every ranking export and
recommendation payload source list (REQ-LIC-001)."* The CSV is half of every ranking export.

**Why MINOR and not BLOCKING.** `export_ranking` has **no production caller** — grep across `src/`,
`scripts/`, `Makefile` and `.github/` returns only its own definition. Nothing is served from it
today, so no licence obligation is currently breached; what is wrong today is the documentation
claim, and what would be wrong tomorrow is the licence.

**Remedy.** Prepend the attribution and blend note as CSV comment lines (or emit a sibling
`*_ATTRIBUTION.txt` written by the same function so it cannot be forgotten), and add the assertion
to `tests/unit/test_rank.py:243`, which currently checks the JSON only.

### MINOR-3 — `coverage`'s `mode=ro` mechanism is defeated by a `?` in the path, and can create a database
`src/app/workflows/coverage.py:285`

The M4 review's MINOR-4 asked for `mode=ro` so that "this report never writes" became a mechanism
rather than a convention. The mechanism shipped, but the URI is built by string concatenation:

```python
conn = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
```

`as_posix()` does not percent-encode, so any `?` in the operator-supplied path opens a query string
that SQLite parses **before** the appended `mode=ro`, and the earlier parameter wins.

**Failure scenario, reproduced this review.** A file literally named
`cov.db?mode=rwc&z=` was placed next to the real database and passed to the real CLI:

```
$ python -m app.workflows.coverage --db '/tmp/sec/cov.db?mode=rwc&z=' --today 2026-08-16
error: evidence unusable: no such table: plans          exit 2
$ ls -la /tmp/sec/cov.db
-rw-r--r-- 1 root root 8192 ...        <- created by the "read-only" report
```

The report failed loudly, which is good, but only after `mode=rwc` had **created a new database
file**. Driving the same URI construction directly:

```
coverage-style URI: file:/tmp/sec/cov.db?mode=rwc&z=?mode=ro   -> CREATE TABLE succeeded
schema-style  URI: file:///tmp/sec/cov.db%3Fmode%3Drwc%26z%3D?mode=ro
                                                               -> attempt to write a readonly database
```

Two sibling CLIs in the same milestone build the same URI two different ways, and only one is
correct. A second, more mundane consequence: a legitimate database whose filename contains `%`
(say `report%20final.db`) is percent-decoded by SQLite and silently fails to open.

**Why MINOR.** The `--db` value comes from the operator, so this is self-inflicted rather than
attacker-supplied, and the failure is loud. But the whole point of the M4 remedy was to convert a
convention into a mechanism, and the mechanism has a hole.

**Remedy — one line, and the correct form is already in this repo.** Use what `schema.py:381` uses:
`sqlite3.connect(Path(args.db).resolve().as_uri() + "?mode=ro", uri=True)`. `as_uri()` percent-encodes
`?`, `#` and `%`. Citing test: a database whose filename contains `?` must still open read-only, and
a write attempt through that handle must raise.

### MINOR-4 — the Epoch and DeepSWE clients follow symlinks out of the bundle directory
`src/app/clients/epoch.py:82-90` · `src/app/clients/deepswe.py:58-66`

Both clients resolve `bundle_dir / <constant filename>` and call `path.is_file()` then
`path.read_text()`. Both operations follow symlinks. The filename itself is a module constant, so
there is no traversal from *data* — the traversal is through the *filesystem*, inside the directory
the operator points at.

**Failure scenario, reproduced this review.** With `swe_bench_verified.csv` inside the bundle
directory replaced by a symlink:

```
symlink -> /tmp/sec/outside.csv : fetch_raw() returned that file's contents (rows entered the parser)
symlink -> /etc/shadow          : fetch_raw() returned that file's contents (running as root)
```

The relevant threat is not a local attacker; it is the acquisition step. The bundle arrives as a ZIP
(`EPOCH_BUNDLE_URL`) that the operator unpacks, and `unzip` recreates symlink entries by default. A
tampered or mirrored archive whose `swe_bench_verified.csv` is a symlink gets an arbitrary local file
read into the process, and — if that file happens to parse — its rows are stored, reconciled, ranked
and served to users stamped with Epoch's source name and Epoch's URL. The M5 plan's own
data-boundary invariant (`docs/plans/m5-plan.md:200-203`) says Epoch ingestion "reads only an
explicitly local, unpacked, allowlisted CSV bundle"; a symlink means that sentence is not enforced.

Content leakage is limited: no error message echoes file content, and `csv.DictReader(strict=True)`
plus the required-column check reject anything that is not shaped like the board.

**Remedy.** In both `fetch_raw` methods, resolve and contain:

```python
root = self.bundle_dir.resolve(strict=True)
path = (root / EPOCH_SWE_BENCH_FILE).resolve()
if not path.is_file() or root not in path.parents:
    raise SourceError(...)
```

or open with `os.open(..., os.O_RDONLY | os.O_NOFOLLOW)`. Citing test: a symlinked board must be
refused with the same loud `SourceError` as a missing one. Note the test suite already writes a
decoy `other.csv` proving non-allowlisted *names* are not read; this extends the same invariant to
non-allowlisted *targets*.

### MINOR-5 — the `agentic-coding` answer never says its evidence is undated
`src/app/workflows/recommend.py:201-230` · `src/app/workflows/subscribe.py:245-289`

REQ-ING-010 requires Epoch staleness to be "disclosed like every other source", and REQ-ING-011b
makes undated a first-class state. `coverage` does this correctly — it partitions plans into
fresh/stale/undated/unscored and reports `0 fresh / 0 stale / 6 undated / 4 unscored` for
`agentic-coding`. The recommendation, which is what a user actually reads, does not.

**Failure scenario, reproduced this review** through the real CLI on the real DeepSWE board:

```
$ python -m app.workflows.recommend --db <db> --subscription --task agentic-coding --budget sinirsiz
"stale_notice": null
picks: best_quality Perplexity Max score 72.8 evidence_date null harness mini-swe-agent
       best_value   ChatGPT Pro    score 69.4 evidence_date null
       budget_pick  Perplexity Pro score 53.8 evidence_date null
```

`recommend._stale_notice` reads `MAX(run_date)` on the primary benchmark; every DeepSWE `run_date`
is NULL by design, so `latest_run is None` and the function returns `None` at `recommend.py:215-216`.
`subscribe._stale_notice` never looks at evidence age at all — it disclose plan-price and roster
clocks only. The result is a category whose entire evidence base has no evaluation date, presented
with no notice and a null date field.

This is the same failure *direction* the W3 reviewer corrected in `coverage.py:249-253` — "unknown
age is now treated as stale; a health check must never fail in the fresh direction". Applied there,
not applied in the answer. It is also the M4 MINOR-2 shape recurring: a control that exists and is
measured, but that the user never sees.

**Why MINOR.** Nothing false is stated — `evidence_date: null` is accurate, and no release date has
leaked in as an evaluation date (I verified: zero non-null `run_date` on the DeepSWE source, and the
W3 tester killed a mutant that promoted them). The defect is silence where the milestone promised
disclosure.

**Remedy.** In both `_stale_notice` functions, when the selected rows for the category carry no
evaluation date, emit an "evidence is undated" sentence naming the board — the same information
`coverage` already computes. Citing test: an `agentic-coding` answer must carry a non-null notice.

### MINOR-6 — a database-derived identifier is interpolated into SQL text
`src/app/workflows/schema.py:171`

```python
indexed = tuple(item[2] for item in conn.execute(f"PRAGMA index_info({row[1]})").fetchall())
```

`row[1]` is an index **name read from the database under inspection** (`PRAGMA index_list(scores)`
at `schema.py:168`). It is the only non-constant value that reaches SQL text anywhere in the M5
diff — every other f-string SQL site interpolates module constants only. Because
`sqlite3.Connection.execute` refuses multiple statements, escalation to a second statement is
blocked, and a name that produces a parse error surfaces as `sqlite3.Error` -> exit 2, which is the
right direction. The realistic impact is therefore an incorrect schema verdict (a crafted index name
makes `_scores_effort_schema` return `False`, triggering an unnecessary full rebuild of the `scores`
table) or a refusal — not injection. Verified by creating a `scores` table carrying a quoted hostile
index name and calling `_scores_effort_schema`: it returned `False` and no table was harmed.

Bandit does not flag it (B608 does not match `PRAGMA`), so unlike `schema.py:365` this site carries
no scanner signal and no marker explaining that the interpolation was audited — the same gap M4's
NOTE-3 raised about the sites that have since become `schema.py:229,233`.

**Remedy.** Use the table-valued form, which accepts a bound parameter:
`conn.execute("SELECT name FROM pragma_index_info(?)", (row[1],))`. If the f-string is kept, add
`# noqa: S608` plus the one-line justification the sibling site carries, so the next reader does not
have to re-derive it.

### MINOR-7 — the guard test installed against Trap 2 cannot fail for the reason it documents
`tests/unit/test_effort.py:400-448`

`test_no_effort_free_category_can_see_more_than_one_effort_level` was added by the W4 review as a
"structural guard" making Trap 2 "unrepeatable". Its docstring says the rule is: *"an effort-free
category may only be fed by evidence that carries a single non-`unspecified` effort per (model,
benchmark, metric, harness, source)."* The body does not test that rule. It:

1. selects `effort_free = [spec for spec in CATEGORIES.values() if spec.ranking_effort is None]`;
2. inserts two clashing rows and asserts `clash == 2` — i.e. asserts that **SQLite accepts** them,
   which the comment itself concedes ("SQLite has no opinion");
3. asserts `spec.ranking_effort is None` for each `spec in effort_free` — which is the predicate the
   list was filtered on.

Step 3 is a tautology. The test never queries the *real* score table, never checks whether any
actual source feeds an effort-free category at more than one level, and therefore passes
unconditionally. It passed while the real Epoch board was feeding `coding` at five distinct effort
levels (max, xhigh, high, medium, unspecified — measured this review), and it passed while
BLOCKING-1 was live.

**Why MINOR and not a test-integrity escalation.** No pre-existing security-invariant test was
modified, loosened or deleted anywhere in `38eaa17..HEAD` — I checked the whole test diff and the
opposite is true (see §2). This is a *new* test that does not do what it says, which is a weaker
problem than a weakened one, but it matters because it is the only thing standing between this
milestone and a Trap-2 recurrence.

**Remedy.** Make the assertion query the database the product actually builds:

```sql
SELECT model_id, harness, source, COUNT(DISTINCT effort)
FROM scores WHERE benchmark = ? AND metric = ? AND effort != 'unspecified'
GROUP BY model_id, harness, source HAVING COUNT(DISTINCT effort) > 1
```

against a real ingested board, and fail if the result is non-empty for a category with
`ranking_effort is None`. Better still, extend it to the cross-model form that BLOCKING-1 exposes:
fail if an effort-free category's ranking spans more than one non-`unspecified` effort at all.

---

### NOTE-1 — the URL guard is type-conditional
`epoch.py:74` and `deepswe.py:50` guard with `isinstance(bundle_dir, str) and "://" in bundle_dir`.
`EpochClient(Path("https://epoch.ai/x.zip"))` is therefore accepted (verified). Impact is nil today
— a `Path` built from a URL is just a directory that does not exist, and the next step fails loudly
— but the guard reads as "a URL is refused" and it is really "a `str` containing `://` is refused".
Drop the `isinstance` and coerce first, so the invariant does not depend on the caller's type choice.

### NOTE-2 — `csv.field_size_limit` bounds field size, nothing bounds row count or file size
Verified: a 200 KB single field is rejected as `CSV payload malformed: field larger than field limit
(131072)` (`epoch.py:136-138`) — good, and that is the sharpest CPU/memory vector closed by default.
Row count is explicitly unbounded (`epoch.py:121` documents "complete, unbounded row set"), and
`path.read_text()` loads the whole file into memory before any size check, so peak memory is a small
multiple of the on-disk file. The producer is the operator's unpacked bundle, the same trust class as
the repo-committed YAML, so this is not a new boundary — but a `path.stat().st_size` guard before
`read_text` is one line and would pair naturally with the W-005 remedy.

### NOTE-3 — `data/epoch-source.yaml` does **not** widen W-005's trust boundary, but it does widen its surface
Asked explicitly, so answered explicitly. `workflows/epoch.py:41` adds a **fourth** `yaml.safe_load`
site (after `plans.py:134`, `rosters.py:99`, `clients/aider.py:66`). It is the same class W-005
records: `safe_load` blocks object construction and module import — the part that matters — but does
not bound alias expansion, and the schema checks run *after* the parse. The **producer** is
unchanged: `data/epoch-source.yaml` is repo-committed data reviewed at every closure, and the only
other way in is an operator typing a path into `--check-staleness`. So the trust boundary is
identical and W-005's `ACCEPTED / owning milestone M6` disposition remains correct and does not need
re-stamping for M5. What did change is scope: the M6 remedy (a length guard before the parse) must now
be applied at four sites, not two, and `epoch.py` should be named in the row when M6 opens it. I ran
a nested-alias document through `parse_epoch_source_doc`: it was rejected in 0.0 s by the strict key-set
check at `epoch.py:52-53` before expansion could bite, because this document's schema is narrow — which
is luck of the schema, not a bound on the parser.

### NOTE-4 — `higher_effort_evidence` reports the highest *level*, not the highest *score*
`rank.py:113-121` walks `reversed(EFFORT_LEVELS[current+1:])` and returns the first level that has
any row. If a model's max-effort run scored *lower* than its ranked run, the disclosure would read
(translated) *"this model reaches N points at max effort"* with N below the score just published —
true in the literal sense, misleading in framing. I queried the live database for this inversion
across every model, harness and source: **zero instances**. Nothing in the code prevents it, so it is
worth a comment or a guard, but it asserts nothing false today.

### NOTE-5 — the gitleaks finding count is 2, and only one of the two paths is in the ledger
Both are the same zero-entropy false positive: an ADR compliance label immediately following the word
"APIs" in English prose. (Described, not quoted — quoting the literal is exactly how the second
occurrence was created, and how the M3 reviewer created a third before rewording it.) The first is at
the path W-001 records. The **second** is at `docs/reviews/m4-security-review.md:310`, the M4 security
record quoting its own scan output verbatim. `git log` confirms that file's only commit is `9ac2663`
("M4 closure"), and `git diff 38eaa17..HEAD` does not touch it — so **M5 introduced no new gitleaks
finding**; the second occurrence entered at the M4 closure commit, one commit before this milestone's
baseline. What is not accurate is the ledger: W-001's `path` column names one file, and there are now
two. I do not waive, baseline, or suppress this finding, and no agent may (AGENTS.md §3). Owner action:
land the scoped `.gitleaks.toml` allowlist for the ADR-label pattern — which would close both at once —
or extend W-001's path column and re-stamp its owning milestone, which is currently "M4 closure (owner
action)" and has now survived a second close.

### NOTE-6 — `migrate` validates through the read-write handle, before the transaction opens
`schema.py:382-389` opens `mode=rw` and then runs `_validate_migration_input` *before*
`BEGIN IMMEDIATE` at `schema.py:390`. Two small consequences: a database that will be refused is
nonetheless opened read-write first (SQLite may perform hot-journal recovery writes on such an open),
and there is a TOCTOU window between validation and the transaction. Neither is reachable in a
single-operator CLI, and the failure direction is safe. Cheap hardening: validate on a `mode=ro`
handle, close it, then reopen `mode=rw` inside the transaction. Related: `connect()` (`schema.py:341`)
runs `_migrate` without `_validate_migration_input` — it still fails closed on every path I probed,
but the two entry points do not share the same guard. This is adjacent to ledgered **W-009** (two
migration entry points, `migrate()` vs `_migrate`), which I am not re-litigating.

### NOTE-7 — `recommend` is described as a read CLI in the wave record, but it writes
`docs/plans/m5-wave-4-close.md` row 5 says "both read CLIs stay migration-free (`recommend` plain
connect, `coverage` `mode=ro`)". Migration-free is accurate. Read-only is not: `recommend()` calls
`build_price_medians`, which executes `DELETE FROM px_median` followed by an `executemany` INSERT
(`rank.py:143-151`) on every invocation. This is pre-existing M1 design, not an M5 regression, and it
is correct behaviour — but the phrase "read CLI" in a security checklist row should say so, because
the next reader will assume `--db` is safe to point at a database they care about.

### NOTE-8 — `board_measurement`'s argparse default runs I/O outside the error handler
`board_measurement.py:596` sets `--last-verified`'s default to `committed_last_verified()`, which
reads and parses `data/epoch-source.yaml`. That call happens during `add_argument`, i.e. *before* the
`try` at `board_measurement.py:598`, so a missing or malformed committed record produces an uncaught
`SourceError` traceback instead of the module's own `exit 2` contract. The one-clock design it
implements (W4 BLOCKING-3) is right; only the placement is. Move it inside the `try`, or default to
`None` and resolve after parsing.

---

## 4. Tooling output (verbatim)

### `make secrets` — gitleaks

`gitleaks` was not on PATH in this container (`make secrets` exits 1 with
`Install gitleaks: brew install gitleaks` — a tool-availability failure, not a scan result). I
installed **gitleaks 8.28.0** to `/tmp` (outside the repository; nothing in the working tree was
touched) and re-ran the Makefile target so the invocation is the real one —
`gitleaks detect --source . --no-git -v`. The two `Finding`/`Secret` lines are reproduced with the
matched literal replaced by `[ADR-LABEL]`, because reproducing it verbatim is what created the second
occurrence in the first place:

```
Finding:     ...oth documented data APIs, [ADR-LABEL]; arena.ai site never...
Secret:      [ADR-LABEL]
RuleID:      generic-api-key
Entropy:     3.640224
File:        docs/reviews/m2-security-review.md
Line:        8
Fingerprint: docs/reviews/m2-security-review.md:generic-api-key:8

Finding:     ...oth documented data APIs, [ADR-LABEL]; arena.ai site never...
Secret:      [ADR-LABEL]
RuleID:      generic-api-key
Entropy:     3.640224
File:        docs/reviews/m4-security-review.md
Line:        310
Fingerprint: docs/reviews/m4-security-review.md:generic-api-key:310

3:37PM INF scanned ~3277080 bytes (3.28 MB) in 354ms
3:37PM WRN leaks found: 2
make: *** [Makefile:88: secrets] Error 1
```

**Result: 2 findings, 0 secrets.** Both are the same known zero-entropy false positive: an ADR
compliance label following the word "APIs" in English prose. Rule ID `generic-api-key`, entropy 3.64
on a string that has none in substance. **M5 introduced neither of them** — `git diff 38eaa17..HEAD`
touches neither file, and the second entered at the M4 closure commit `9ac2663`. Accountability
follow-up in NOTE-5. Not waived, not baselined, not suppressed.

### `make deps` — pip-audit

```
.venv/bin/python -m pip_audit
No known vulnerabilities found
Name          Skip Reason
------------- ----------------------------------------------------------------------------
model-ranking Dependency not found on PyPI and could not be audited: model-ranking (0.1.0)
```

**Result: 0 vulnerabilities, 0 advisory IDs.** The single skip is this project's own editable local
package, which by definition has no PyPI advisory record — expected, not a gap. M5 added **no**
dependency: `pyproject.toml` is not in the milestone diff (`git diff 38eaa17..HEAD --stat` has no
`pyproject.toml` row), so the slopsquat and maintainer-age questions do not arise.

### `bandit -r src -q` (supplementary, for comparison with the M3/M4 records)

```
>> Issue: [B608:hardcoded_sql_expressions] Possible SQL injection vector through
   string-based query construction.
   Severity: Medium   Confidence: Medium
   CWE: CWE-89
   Location: src/app/workflows/schema.py:365:19
365     conn.execute(f"DELETE FROM {table} WHERE source = ?", (source,))  # noqa: S608

Total issues (by severity): High: 0  Medium: 1  Low: 0
Total lines of code scanned: 4216
```

Identical to M3 and M4: the one known allowlist-gated identifier (`schema.py:362-364` validates
`table` against a two-element tuple), which has its own negative test. **No new bandit finding in
M5.** See MINOR-6 for the one site bandit structurally cannot see.

### Gate suite

`pytest` 266 passed / 12 skipped; with the owner's bundle mounted, 273 passed / 5 skipped (the 5
being the `RUN_CONTRACT_TESTS`-gated network contracts, reported not silent, V3C-44). Coverage 84%
without the bundle, **90%** with it. `ruff check src tests` clean. `mypy src` clean, 27 files.
`bash scripts/bootstrap-check.sh` PASS, 0 fail / 2 warn (both pre-existing: C5 ADR band, C6 no
license review needed — no OSS engine wrapped). `make check-records` PASS.

---

## 5. Verdict

## **PASS (conditional)** — 1 BLOCKING, 7 MINOR, 8 NOTE.

Nothing in this milestone can execute code, reach the network, leak a credential, or destroy data.
I probed the migration — the single highest-risk addition — against six database shapes and it
preserved every row, refused every wrong shape with exit 2 and a JSON error, rolled back atomically,
ran idempotently, left no rebuild table behind, and opened `mode=rw` rather than `rwc` only after
confirming the file exists. Egress *shrank*: W-007 removed Arena's full-pagination fallback and three
tests now assert the removed endpoint is never called. Both new clients are file-only, reject a URL,
refuse a missing or malformed board loudly, and are protected against oversized CSV fields by the
stdlib field limit. The dependency surface is clean and unchanged. No security-invariant test was
weakened or deleted anywhere in the milestone; the test diff is +2171/-22 and every removed line was
replaced by an assertion that says more. Both published measurement records reproduce number for
number from the shipped code against the owner's real bundle. Epoch's CC-BY citation is verbatim
correct against the bundle's own README and is present in every surface REQ-LIC-001 names.

The honest summary of the risk that remains: this product's real security property is that it never
tells the user something false, and the one BLOCKING finding is exactly there. The shipped coding
answer publishes a max reasoning-effort score with the effort qualifier nulled out, while its own CSV
export prints that same score's effort as `max`. The milestone's plan named this scenario, in these
words, as the condition on which the ingestion is honest — and the effort value the answer needs is
already sitting in the dataclass the answer is built from. Two lines, one disclosure sentence, one
citing test. The reason it survived four waves and two fresh-eyes reviews is MINOR-7: the guard test
written specifically to prevent it asserts a tautology, so it was green the entire time the defect
was live.

**Why "conditional" and not plain PASS.** `permission-matrix.md:153` lists *"Auth / PII / payment /
**migration** / RLS change without senior human review"* as BLOCKING, and `subagent-profiles/Security-Reviewer.md:59`
repeats it. M5 adds a schema migration and an operator migration command. My review is not a
substitute for that sign-off and no agent's can be. Stage 4.0 may close on this record once
BLOCKING-1 is fixed; Stage 4.3 deploy additionally requires the owner's own review of the migration
path, which under A0.5 happens at the milestone gate.

### Owner checklist at the milestone commit

1. **BLOCKING-1 (do not defer):** publish `row.effort` instead of `spec.ranking_effort` in both
   `_pick` functions, add the effort-free branch to `effort_disclosure`, and land the citing test —
   it is red today. Separately decide whether `coding` should acquire a `ranking_effort`, which is a
   one-field data edit to `categories.py` and is the only thing that makes the cross-model comparison
   satisfy the Q1 ruling.
2. **MINOR-7:** replace the tautological Trap-2 guard with the group-by query in §3. Without this,
   fixing BLOCKING-1 does not stop it recurring.
3. **Migration human review (permission-matrix §11):** your own pass over
   `schema.py:368-408` and `_migrate_scores_effort`, against a copy of any database you care about.
   Everything I could probe passed; the rule requires you, not me.
4. **NOTE-5 / W-001 (scanner accountability):** gitleaks now fires at two paths and the ledger row
   names one. Land the scoped `.gitleaks.toml` allowlist (closes both) or extend and re-stamp the row.
   It has now survived two closes.
5. **MINOR-3 and MINOR-4:** one line each — `resolve().as_uri()` in `coverage.main`, containment
   check in both `fetch_raw` methods. Both are cheap now and retrofits later.
6. **MINOR-1, MINOR-2, MINOR-5:** attribution for secondary sources, attribution in the CSV export,
   and an "undated evidence" sentence in the answer. All three are the same shape as M4's MINOR-1/-2:
   disclosure defects rather than fabrications, all visible to the waves that shipped them.

### Invariants proposed for the register

- **INV-20 a published score carries the effort it was measured at.** Every user-facing artifact that
  prints a score prints the effort of the row that produced it, or states that the row has none. No
  artifact may print the *policy* where the *evidence* is what the reader will assume. Citing tests:
  blocked on BLOCKING-1 — there is no behaviour to cite yet.
- **INV-21 a payload cites every source whose data it carries, primary and secondary.**
  `attributions_for` raises on an unattributed source; that guard is only as wide as the set handed to
  it, so the set must be the union of every source contributing a printed field. Citing test: blocked
  on MINOR-1.
- **INV-22 an allowlisted local input is contained, not merely named.** A source that reads a constant
  filename from an operator-supplied directory resolves the result and refuses a target outside that
  directory. Citing test: blocked on MINOR-4.
- **INV-23 a URI built from an operator-supplied path is encoded, never concatenated.** Any
  `sqlite3.connect(..., uri=True)` derives its path through `Path.resolve().as_uri()`. Citing test:
  blocked on MINOR-3. Ratify with the `schema.py:381` site as the reference implementation.
- **INV-24 unknown evidence age is disclosed in the answer, not only in the report.** The direction
  `coverage.py:249-253` already holds (unknown age reads as stale) applies to the recommendation
  payload too. Citing test: blocked on MINOR-5.


---

## 6. Disposition of this review's findings (added at closure by the lead agent, 2026-08-16)

The reviewer authored none of the reviewed code and the lead agent authored none of the M5
implementation either; the fixes below were written at closure and every one of them was
fault-injected before this line was added.

| Finding | Disposition |
|---|---|
| **BLOCKING-1** — `_pick` published the effort POLICY instead of the effort EVIDENCE, so the live `coding` best_quality pick served a max-effort score with `effort: null` while the same run's CSV export printed `effort,max` | **FIXED.** Both engines publish `row.effort`; the policy is still stated once per answer in `ranking_effort`. An effort-free category now also DISCLOSES the level its evidence came from instead of staying silent. Citing test covers BOTH engines (the first version covered only the model engine and the subscription mutant stayed green); 2 mutants RED. |
| MINOR — secondary-benchmark sources never reached `attributions_for`, so a payload could serve an Aider score, grade confidence "two independent benchmarks" on it, and cite only Epoch | **FIXED.** `secondary_evidence_sources` adds them when a secondary score is actually served. Citing test + mutant RED. |
| MINOR — `coverage`'s `mode=ro` was string-concatenated, so a `?` in the path dropped the mode AND created a database | **FIXED.** `as_uri()`, matching what the migrate command already did. Citing test with a `?` in the filename; mutant RED. |
| MINOR — both bundle clients followed symlinks out of the operator-supplied directory (reproduced reading /etc/shadow) | **FIXED.** The allowlisted name must resolve inside the bundle root. Citing test + mutant RED. |
| MINOR — the W4 "structural guard" against Trap 2 was tautological (it asserted the predicate it had filtered on) | **FIXED.** Replaced with the BLOCKING-1 citing test above, which fails on the real defect. The tautology is recorded in EXPERIENCE: a guard that cannot fail is worse than no guard, because it reads like coverage. |
| MINOR — the CSV half of `export_ranking` carries no attribution or blend note | **LEDGERED** as part of the export-contract work in M6; the JSON half is correct and is what the product serves. |
| MINOR — `PRAGMA index_info({row[1]})` interpolates a DB-derived identifier | **ACCEPTED, no change.** The value comes from `PRAGMA index_list` on a database the operator already owns; there is no attacker-controlled path to it that does not already imply write access to the file. Recorded here rather than silently dismissed. |
| MINOR — the `agentic-coding` answer never says its evidence is undated | **LEDGERED** to M6 with the disclosure work; the coverage report already carries the fact, and REQ-ING-011b's branch (b) is satisfied at the source level. |

**Verdict after disposition: PASS.** The reviewer's "conditional" stands as written — a schema
migration is BLOCKING until the OWNER's review at the milestone gate (permission-matrix §153), and
an agent's pass cannot substitute for it.
