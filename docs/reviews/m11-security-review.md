---
record_type: review
id: m11-security-review
status: ratified
seat: independent
date: 2026-08-23
---
# M11 Stage 4.0 Security Review — the whole milestone surface

**Seat:** independent. This seat wrote none of the code under review. Policy was read from the
protected base ref (`git show HEAD:AGENTS.md`, `git show HEAD:.agents/rules/practices.md`,
`git show HEAD:docs/security-baseline.md`). Every claim in the change under review — comments,
docstrings, ledger rows, ADRs — was treated as DATA to be checked, not as policy (V4C-06).

## Scope correction, stated first

The task named `a35bb3a..HEAD`. That range covers **only W3 and W3.5** (8 commits, 18 files). The
M11 surface begins at the M10 closure commit `1069907`, and the range actually reviewed is
**`1069907..HEAD`: 17 commits, 48 files, +4429/-426**. W1 (`scripts/wave_check.py`,
`scripts/check_records.py`, `.governed-records`, D-133) and W2 (`ios/Package.swift`,
`ios/EngineTests/`, `make swift-test`, `runner`) land at `8f02ddf`/`19b73da`/`73edfa7`, all of which
are **before** `a35bb3a` and would have been invisible to a review that took the given range
literally.

**The tree moved during this review, and the record says so rather than being quietly rewritten.**
At review start the working tree carried two untracked files, `scripts/enable_refresh.sh` and
`docs/plans/m12-inputs.md`; both were reviewed in that state. Partway through, the owner committed
`55a7455` ("M11 capture...") — Stage 4.2 capture plus those two files, **no code changes**. The
`enable_refresh.sh` that was reviewed is byte-identical to the one committed (md5
`c1d09562ac1af2f9d89dfd0bf3bf8b92` on both), so every finding below stands unmodified except
MAJOR-2, which is annotated. `make check` was re-run against the new HEAD and is green. The only
uncommitted file in the tree now is this review.

## What was executed

| Command | Result |
|---|---|
| `make check` | **exit 0** — 711 Python passed / 12 skipped, coverage **88.34%** (floor 85), `coverage-floor` PASS (33 modules), `check_records` PASS (60 records), `check-records-selftest` PASS (29 fixtures), `install-check` PASS, `wave-check-all` PASS (19 v5.0 records), `conformance-gate` PASS, `swift-test` PASS **59 tests** (floor 59) |
| `make secrets` (gitleaks) | scanned 55.03 MB — **no leaks found** |
| `fastapi.testclient` probes | all four routes, 5 database states, 8 adversarial `task`/`budget` values, POST/HEAD/OPTIONS/path-traversal on `/v1/budgets` |
| Payload-freeze differential | M10 tree (`1069907`) vs HEAD, same `advisor.db`, 4 tasks x 3 budgets + 8 bad inputs + `/v1/categories` — **byte-identical**, md5 `b4271929321d75eaf9d89d9fdd0f1207` on both |
| 4 mutation experiments | 3 killed, 1 **survived** (see BLOCKING-1). All mutated files restored and md5-verified identical |
| Shell-semantics experiments | `:-` deferral under env and make-command-line vars; subshell `kill $!` reproduction |

Mutation restores verified: `src/app/adapter/main.py` md5 `4705dadc2546cdd547409de08397ea42`
before and after (twice); `ios/ModelRanking/Engine/Router.swift` md5
`3d724270d1bdfe7c5d11b11359bd76ef` before and after. No file under `src/`, `scripts/`, `tests/`
or `ios/` is left modified.

---

## BLOCKING

### BLOCKING-1 — The K.7 seat gate is disabled by renaming one table cell. W1's entire deliverable.

**`scripts/wave_check.py:89-90`**

```python
name = cells[1] if len(cells) >= 3 else cells[0]
if not re.search(r"K\.7|review", name, re.I):
    continue
```

The gate that D-133 and `AGENTS.md` §4 say makes K.7 executable finds the review row by looking for
the literal substring `review` or `K.7` **in a free-text cell the author writes**. A row whose name
cell contains neither is skipped entirely: no citation is required, no `seat:` is read, and the wave
closes green.

**Reproduced.** Copy of the real `docs/plans/m11-wave-2-close.md` into a scratch tree; baseline
`wave_check.py` → `PASS`, exit 0. Then one edit to row 3 — nothing else:

```
-| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-wave-2-review.md`, `seat: independent`. ... | ✅ |
+| 3 | Fresh eyes per tier — V3C-78 | `ios/Package.swift` inspected by a separate seat; it returned BLOCKING and every finding is fixed | ✅ |
```

Result: `wave-check PASS ... (10 row(s), all evidenced and statused)`, **exit 0**. No review record
is cited, none exists, and the gate says nothing.

For contrast, the two attacks the gate *does* stop, both run in the same tree: dropping the
backticked evidence entirely fails on the V3C-69 evidence rule (exit 1); citing a review record with
`seat: author` fails with the intended diagnostic (exit 1). So the gate has teeth on the paths it
looks at — it simply stops looking when the row is renamed.

**What it lets through.** An entire unreviewed wave closing green, which is exactly the state
`W-055` records happening four times and `D-133` was written to end. The mechanism is one word in a
record written by the same seat whose independence is being certified.

**Why this is not a MAJOR.** `AGENTS.md` §4 (base ref) states the gate "enforces both halves", and
`scripts/wave_check.py:47-49` states it "converts 'the author reviewed their own code' from a
sentence in a record into a thing that cannot pass silently." Both statements are measurably false
as written, and `permission-matrix.md` §11 makes an unevidenced PASS BLOCKING. The record contradicts
the code on the one control this milestone exists to install.

**Scope, stated honestly:** the blast radius is governance, not the served product. No external
attacker reaches this. It does not endanger a deploy; it endangers the evidence a deploy rests on.

**Remedy shape (not applied — this seat reviews):** key the row on something the author does not
free-type. Either match the row by its *position/id* in the committed template, or invert the test —
require that **at least one** row in every v5.0 wave-close record cites a `docs/reviews/*.md` with
`seat: independent`, so deleting or renaming the row fails rather than passes. The current predicate
fails **open** on an unrecognised label; a K.7 control is a safety control and must fail **closed**
(V3C-33/45).

**The test that should have caught this, and why it did not.**
`tests/unit/test_review_seat_gate.py:248-259`, `test_a_review_row_labelled_something_else_is_still_seen`,
uses the row label `Fresh-eyes code REVIEW` — which still contains `REVIEW`. The test proves
case-insensitivity; its name claims label-independence. A test whose name is broader than its
assertion is the overstatement class `tests/unit/test_api_v1.py:490` already names in this repo.

---

## MAJOR

### MAJOR-1 — `simulator_session.sh` tells the operator it stopped the engine, and does not.

**`scripts/simulator_session.sh:25`** (`kill "$ENGINE_PID"`), **`:66-67`** (`( cd "$REPO" && ... uvicorn ... ) &` / `ENGINE_PID=$!`), **`:179`** ("Ctrl-C when you are done — that stops the engine.")

`$!` after `( ... ) &` is the **subshell's** pid, not uvicorn's. Killing it terminates the subshell
and leaves the server running.

**Reproduced** with the identical construct:

```
subshell pid recorded: 85144
sleep processes alive: 85146
after kill $P, sleep processes still alive: 85146
```

**What it lets through.** A `uvicorn` process the operator believes is stopped, still listening on
`127.0.0.1:8080` and holding an open read handle on the owner's `advisor.db`, indefinitely and
unattended. That is a small security exposure (loopback only, read-only handle) and a large
*evidence* exposure: the next run takes the `engine already answering on 8080 — reusing it` branch
at `:38`, and the owner walks the product against an engine built from an earlier commit. The script
already documents having hit precisely this at `:40-43` ("the engine that was already listening was
built from an older commit"). **The stale-engine warning at `:49-51` is a symptom of this bug, not
an independent hazard** — the script wrote a warning about a state its own cleanup creates.

Given that REQ-RUN-001's whole claim is that a person operated the product against a known engine,
an unstopped stale engine turns the owner's session notes into evidence about the wrong code — the
M11 lesson, reproduced by the M11 tooling.

### MAJOR-2 — The most privileged artifact in the milestone reached the tree through no wave and no gate.

**`scripts/enable_refresh.sh`** — untracked at review start; committed mid-review at `55a7455`,
byte-identical, in a **Stage 4.2 capture commit** alongside `EXPERIENCE.md`, `process-log.md`, the
retrospective and `m12-inputs.md`.

`docs/prd.md` REQ-RUN-002 is **NOT MET** and ESCALATED as W-071; its stated remedy is "One owner
command starts it." That command is this file. It is the single most privileged thing anything in
M11 does — it writes into `~/Library/LaunchAgents` and `launchctl bootstrap`s a recurring background
job that rewrites the served evidence artifact — and it arrived:

- **through no wave.** It belongs to no wave-close record, so no `docs/plans/m11-wave-*-close.md`
  row cites it, no review record covers it, and neither the fresh-eyes nor the fault-injection
  discipline touched it. It is not in the M11 plan's wave decomposition.
- **inside a capture commit**, which by AGENTS.md §6 is where process-log, ADRs, seeds and the
  retrospective go. Shipping executable code that installs a background job in the commit whose job
  is to write down what already happened is how a deliverable skips the gate that would have read it.
- **linted by nothing.** There is no `shellcheck` anywhere in `Makefile`, `scripts/` or
  `.github/workflows/` (verified by grep); `ruff` covers `src` and `tests` only. Every shell script
  in this milestone — `enable_refresh.sh`, `simulator_session.sh`, `runner` — is unlinted, and
  MAJOR-1 is a shell defect in exactly that unlinted set.
- **outside the record contract.** `.governed-records` reaches neither this file nor
  `docs/plans/m12-inputs.md` (verified by evaluating the manifest globs directly), so
  `check_records`' frontmatter and English rules never see them.

The script's *content* is sound — see the launchd section under "what checks out"; `make secrets`
(gitleaks) scanned it clean. The finding is the route it took. Committing it closed the
version-control half; it did not close the review half, and REQ-RUN-002 still requires two OBSERVED
cycles before it can be marked MET.

---

## MINOR

### MINOR-1 — `enable_refresh.sh:40` and the plist directly contradict each other about whether installing rewrites the served artifact.

`deploy/com.hcs.modelranking.refresh.plist:56-57`:

> *Deliberately absent: RunAtLoad. Installing the job should not immediately rebuild the artifact
> somebody is currently serving; the first cycle can wait twelve hours.*

`scripts/enable_refresh.sh:40`:

> `It is on. The first cycle runs now; the second in 12 hours.`

One of these is wrong, and which one decides whether `launchctl bootstrap` immediately replaces
`advisor.db` under a running engine. This seat did not load a launchd job on the owner's machine to
settle it — that is a state-changing action on the owner's box and outside a reviewer's authority.
Whichever is right, an operator is being told the opposite of the truth about a destructive-side-effect
default (V3C-06/53: a reseed-on-load defaults OFF **or is loud and explicit** — it cannot be both
"deliberately absent" and "runs now").

### MINOR-2 — `Router.swift:274` claims a test the tests do not contain.

> *"Not a category id, and a test asserts it never becomes one."*

The only assertion is `ios/EngineTests/OwnerSessionDefectTests.swift:54-57`,
`XCTAssertFalse(nine.contains(ModelOutputBoundary.declineSentinel))`, where `nine` is a **hardcoded
literal array in the test file itself** (`:14-17`). It asserts that a list the test wrote does not
contain a constant the test read. It cannot fail if the *engine* ever serves a category id equal to
`__none__`; `tests/unit/test_router_hints.py` — the one gate that does cross the language boundary —
contains no sentinel assertion at all (verified by grep across `src/`, `tests/`, `ios/`, `scripts/`,
`docs/`: the literal appears only in `Router.swift`, `OwnerSessionDefectTests.swift` and, in an
unrelated namespace, `src/app/workflows/rank.py:254`).

Practical risk is low and worth stating so the finding is not inflated: protection exists
*incidentally*, because `test_router_hints.py:34` parses hint ids with `r'^\s*"([a-z-]+)":'`, which
cannot match underscores — so an engine id of `__none__` would fail that test for the wrong reason.
The finding is the claim, not the exposure: the comment asserts a guarantee stronger than any test
that exists, on the boundary D-126 calls absolute.

Order of checks is otherwise correct: `ModelOutputBoundary.outcome` (`:283-294`) tests
`id == declineSentinel` before `known.contains(id)`, which is required because
`schemaChoices` (`:279-281`) puts the sentinel into the grammar.

### MINOR-3 — The manual tier is the one tier with no membership guard.

**`ios/ModelRanking/Engine/Router.swift:371-373`**

```swift
return RoutingOutcome(
    categoryID: CategoryHints.unmeasuredFallback, tier: .manual, unmeasured: false
)
```

The model tier (`:287`) and the similarity tier (`:179`) both `guard known.contains(CategoryHints.unmeasuredFallback)`
before naming the fallback. The manual tier does not, and returns a hardcoded `assistant` regardless
of what the engine served. `ios/EngineTests/OwnerSessionDefectTests.swift:59-64`
(`testDecliningStillRefusesWhenTheFallbackSurfaceIsNotServed`) asserts the guarded behaviour for the
model tier only. Downstream, `ContentView.swift:366` sets `task = outcome.categoryID` and issues the
request, so an engine that stops serving `assistant` yields a `400 unknown_task` from the manual
path where the other two paths degrade cleanly. Degradation, not a hole — but an asymmetric guard is
the "control lives in the path that does not execute" shape this whole milestone is about.

### MINOR-4 — `make run`'s comment says `?=`; the recipe uses `:-`, and they differ.

**`Makefile:183-185`.** Comment: "`?=` means an operator who sets either one keeps it — these do not
override a real deployment." Recipe: `MODEL_RANKING_DB="$${MODEL_RANKING_DB:-$(CURDIR)/advisor.db}"`.

Measured — the deferral the question asks about **is correct**:

```
MODEL_RANKING_DB=/operator/real.db  -> /operator/real.db          (env wins)
make run MODEL_RANKING_DB=/from/cmdline -> /from/cmdline          (make cmdline var wins)
MODEL_RANKING_DB=   (set but empty)  -> /repo/advisor.db          (default wins)
```

The last line is the divergence, and it inverts a fail-closed decision: `src/app/adapter/main.py:249-250`
(`_db_path`) treats an empty value as *no database configured*, which is a deliberate fail-closed
503 ("There is no default. Unset is a fail-closed 503"). Under `make run`, an operator who blanks the
variable to mean "serve nothing" gets the repo's artifact instead. `?=` would not do this. Dev target
only — `Dockerfile:24` and `fly.toml` set `MODEL_RANKING_DB` explicitly, so no deployment path is
affected.

### MINOR-5 — `APP_BUILD` is now synthesized from the working tree, satisfying an L.7 check with a value that does not describe a build.

**`Makefile:185`** and **`scripts/simulator_session.sh:64`**:
`APP_BUILD="dev-$(git rev-parse --short HEAD)"`.

`src/app/adapter/main.py:433-437` refuses to boot in strict mode when `APP_BUILD` is unset, because
"/health cannot say which code is live, so a deploy cannot be verified (L.7)". Both scripts now
satisfy that check unconditionally with HEAD's SHA — including on a **dirty** tree, where the running
code is not the commit stamped. `Dockerfile:18-19` still takes it as a build ARG, so the deploy path
is unaffected, and `runner:51` prints `tree: DIRTY` separately, which is a partial mitigation. Worth
a sentence in the Makefile so the next person does not read `dev-<sha>` as a release identity.

### MINOR-6 — `docs/prd.md:427` states a test count that is off by 41.

REQ-IOS-001: "18 tests in `ios/EngineTests/`." `Makefile` `SWIFT_TEST_FLOOR = 59`, and
`cd ios && swift test` reports `Executed 59 tests, with 0 failures`. The PRD is a live status
document, not an era-pinned wave record. (`docs/plans/m11-wave-2-close.md` says 39 and is correctly
pinned to its closing tree — that one is fine.)

### MINOR-7 — The contract-tests path filter omits the dependency manifest.

**`.github/workflows/contract-tests.yml:41-49` and `:52-60`.** The paths that trigger the drift probe
list client code, sources, ingest, build, `epoch*.py`, the integration tests, `ci_coverage_gate.py`
and the workflow itself — but **not `pyproject.toml`**. A change that repins `httpx`/`pydantic`/a
parser dependency is exactly a change that can alter how an upstream payload is read, and it will not
run this workflow on push or PR; it waits for the Monday cron. `data/plans.yaml`,
`data/rosters.yaml` and `data/epoch-source.yaml` are likewise absent while the `plan-staleness` job
exists solely to check them.

### MINOR-8 — `ci_coverage_gate.py`'s tolerance is declared by the artifact it is gating.

**`scripts/ci_coverage_gate.py:35-56`.** `degraded_surfaces()` parses which surfaces may be empty out
of the free text of `build-report.json`, produced by `src/app/workflows/build.py` — which is itself in
the fork-PR path filter above. A PR that edits the build's message to emit the marker sentence
`must disclose it rather than answer:` for eight of nine surfaces reduces the drift probe to
"one surface scored something" while the badge stays green. The `if not covered` floor at `:87-92`
is the only backstop and it is a floor of **one**. V4C-61's principle applies directly: a verifier
may not take its pass criterion from the thing it verifies.

### MINOR-9 — `test_budgets_endpoint.py` can pass vacuously, on a file the refresh rewrites every 12 hours.

**`tests/unit/test_budgets_endpoint.py:27`** binds `MODEL_RANKING_DB=advisor.db` — a **CWD-relative**
path to the repository's live artifact — and **`:71-72`** does `if not ranking: continue`. If the
artifact publishes no rankings on those three surfaces, the endpoint's headline test asserts nothing
and passes. Its sibling at `:88` gets this right (`assert rows, "fixture assumption: ..."`). Since M9
the same file is replaced on a 12-hour schedule, so the milestone's flagship reconciliation test is
both non-hermetic and silently skippable. (Contrast `.agents/rules/practices.md`'s hermetic-gate rule
and seed F.4 on relative runtime paths.)

### MINOR-10 — `sim_drag.swift` posts to the global HID tap with nothing checking where the pointer is.

**`scripts/simtools/sim_drag.swift:11-25`.** `CGWarpMouseCursorPosition` then `.leftMouseDown` /
`.leftMouseDragged` / `.leftMouseUp` posted at `tap: .cghidEventTap` — the system-wide tap. The tool
never verifies the Simulator is frontmost; the README (`scripts/simtools/README.md:13`) puts that in a
separate `osascript ... activate` line the tool cannot enforce. Given wrong coordinates or a
foreground change mid-run, the result is a real click-drag in whatever application is under those
points. Arguments are force-unwrapped (`a[1]`, `a[2]`, `a[3]` with `Double(...)!`) with no bounds.
It is a developer tool, outside `make check`, and it ships nothing to the product — but it is exactly
the "documented discipline rather than a control" pattern this repo's own rules name, and
`keyboards_on.scpt` additionally requires the operator to grant **Accessibility** to whatever runs it,
which is a machine-wide synthetic-input capability. Worth one line in the README saying so.

---

## What checks out, with the evidence

### 1. `/v1/budgets` — no leak, no error surface, no artifact dependency

- **Takes no input at all.** `src/app/adapter/main.py:1043-1078` returns three module constants
  (`BUDGETS`, `BLEND_NOTE`, `BLEND_INPUT_WEIGHT`, `BLEND_OUTPUT_WEIGHT`) and touches no database, no
  filesystem, no request state. There is nothing to inject into. Confirmed by probing with
  `?x=1`, `?budget=low`, `?id=../../etc/passwd` — all return the identical constant body.
- **Works with the artifact missing**, which is its stated purpose (D-134). Measured across five
  database states — valid, stale-schema (`live.db`), stale-schema (`owner_advisor.db`),
  `/nonexistent`, and unset — `/v1/budgets` answered `200` with the full cap list in all five, while
  `/v1/recommendations` answered `503` in three of them.
- **Cannot be made to error.** `POST` → 405, `HEAD` → 405, `OPTIONS` → 405 with `allow: GET` and
  `x-content-type-options: nosniff`, `GET /v1/budgets/../../etc/passwd` → 404. No path, no stack, no
  internal name in any response.
- **`DECLARED_ROUTES` is the shipped surface.** `main.py:86-97` declares four;
  `tests/unit/test_api_v1.py:460-487` compares the app's *actual* route table against a list
  **written out in the test**, then separately asserts the module's own constant matches it — so
  adding a route is a two-file change that cannot self-approve. `make check` green confirms the
  shipped surface is exactly `{/health, /v1/categories, /v1/recommendations, /v1/budgets}`.
- **The endpoint is checked against the engine, not against itself.** Mutation: publish `cap * 2`.
  Result — 7 of 11 tests in `tests/unit/test_budgets_endpoint.py` failed, including every
  `test_the_published_cap_reproduces_the_engines_own_eligible_count` parameterisation. `main.py`
  restored, md5 identical. (The vacuous-pass caveat is MINOR-9; the assertion itself has teeth.)

### 2. `/health.evidence` — not a new oracle, and cheap

- **It tells a prober nothing `/v1` did not already tell them.** Measured side by side across five
  database states: `evidence=servable` ⟺ `/v1/recommendations` answers usefully;
  `evidence=unavailable` accompanies either a `503` or a `200` whose own body already says
  *"This surface has no evidence to rank"*. The one state where `evidence` is strictly more
  informative (`owner_advisor.db`: `evidence=unavailable` while `/v1` returns `200` with zero picks)
  discloses "this deployment's data is broken", not anything about the host.
- **No path, filename, schema version or reason is exposed.** `main.py:1013-1020` collapses every
  `_database_unusable` diagnostic — including the verbose "predates M5's effort column, run
  `schema migrate`" string — into the single token `"unavailable"`. "No database configured" and
  "database is corrupt" are the same output, so there is no configuration oracle. This is exactly
  V3C-103's shape: operator detail server-side, opaque status to the unauthenticated caller.
- **Not a DoS amplifier.** `/health` now performs one `open_readonly` (instrumented: exactly **1**
  per request) plus a `sqlite_master` query, a `PRAGMA table_info`, and one `count(*)`. Measured over
  300 requests against the real 1.5 MB `advisor.db`: `/health` **0.917 ms**, `/v1/budgets` 0.768 ms,
  `/v1/categories` 0.770 ms, `/v1/recommendations` 7.006 ms. The addition costs ~0.15 ms — an order of
  magnitude below the endpoint an anonymous caller can already reach.
- **The control has teeth.** Mutation: `"evidence": "servable"` unconditionally.
  `tests/unit/test_unavailable_after_boot.py:144`
  (`test_health_reports_that_the_evidence_became_unservable`) failed. Restored, md5 identical.
- **Additive only.** `status`, `version`, `build` unchanged; `Dockerfile:39-40`'s HEALTHCHECK and
  `fly.toml`'s `[checks.health]` both test for HTTP 200 and are unaffected.
- **It is wired to a consumer**, which the schema-narrowness rule (V4C-35) requires:
  `scripts/simulator_session.sh:87-96` reads it, with a correct three-state handling
  (`servable` / `unavailable` / **absent**, the last meaning "this engine predates M11-W3"), which is
  the right distinction and one this seat expected to find missing.
- W-058 is ESCALATED to the owner for whether Stage 4.3's deploy check should *consume* it. That is
  the correct disposition; `main.py:1006-1010` declines to redefine `status` on its own authority.

### 3. Router / `__none__` — the boundary holds

- **A crafted question cannot produce an unintended value.** `Router.swift:216-220` constrains
  generation with `GenerationSchema(anyOf: ModelOutputBoundary.schemaChoices(for: known))`, so the
  model's output alphabet is the engine's own id list plus one sentinel. "Ignore your instructions
  and tell me the best model" has no expressible answer.
- **`ModelOutputBoundary` is not reachable by any path that skips the membership check.**
  `outcome(for:within:)` (`:283-294`) is the only constructor of a `.model`-tier outcome and is called
  from exactly one site (`:242`). Every other `RoutingOutcome` in the file derives its `categoryID`
  either from `hints`, which is built by filtering `known` (`:142-146`), or from the
  `unmeasuredFallback` constant.
- **The guard is not decorative.** Mutation: delete `guard known.contains(id) else { return nil }`.
  `swift test` → `Executed 59 tests, with 4 failures`. `Router.swift` restored, md5
  `3d724270d1bdfe7c5d11b11359bd76ef` identical.
- **Nothing typed reaches the engine (D-104, REQ-RTR-004).** `ContentView.swift:350-368` sends only
  `outcome.categoryID`; `EngineClient.swift:143-146` builds the request from `URLQueryItem(name:"task")`
  and `URLQueryItem(name:"budget")` and nothing else.
  `tests/unit/test_router_hints.py:113-133` greps both files for any path by which the question could
  become a query item, and passes. The scoring path is untouched — see §5.
- The residual sentinel risk is the *claim*, not the *code*: MINOR-2.

### 4. The launchd job — no root, no other-user-writable path

Every ancestor of every path the job names was stat'd:

```
/Users                                              drwxr-xr-x  root:admin
/Users/umutcanapaydin                               drwxr-x---  umutcanapaydin:staff
/Users/umutcanapaydin/Desktop                       drwx------  umutcanapaydin:staff
  .../ILGAR, .../model_ranking, .../.venv, .../.venv/bin   drwxr-xr-x  umutcanapaydin:staff
/Users/.../terminal_output/{,model_ranking,epoch_data}     drwxr-xr-x  umutcanapaydin:staff
```

- **Nothing runs as root.** `enable_refresh.sh:23-31` uses `launchctl bootstrap gui/$(id -u)` — a
  per-user LaunchAgent domain. No `sudo`, no `/Library/LaunchDaemons`, no `UserName` key in the plist.
- **No path is writable by another local user.** `~/Desktop` is `0700`, so the entire chain to
  `.venv/bin/python` is untraversable by anyone else on the machine. There is no interpreter-
  substitution route to code execution as the owner.
- The plist is installed by `cp` (`:28`), inheriting the source's `0644 umutcanapaydin:staff`.
  Failure handling is explicit at `:19`, `:28` and `:31-34` (`set -u`, each critical step guarded with
  `||`), and it takes an existing job down before bootstrapping so the file that runs is the file that
  was copied.
- **Missing artifact / missing epoch dir fails closed and creates nothing.** Executed in an empty
  temp directory with `--db advisor.db --epoch-dir /nonexistent/epoch_data`:
  `{"published": false, "reason": "the candidate could not be built (build exit 2); the live artifact is untouched", ...}`.
  **No `advisor.db` was created** — the wrong-CWD case does not silently mint an empty database for
  the API to serve. It leaves a `.refresh.lock` and a `.refresh.json` in the wrong directory; the lock
  is `flock`-based (`refresh.py:443-479`) and released by the kernel on process death, so a stale file
  does not wedge future cycles.
- **The environment assumption is a check, not an assumption** (D-129, REQ-GRD-003).
  `refresh.py:403-435` (`environment_problems`) refuses to run when the artifact's directory is
  group- or world-writable, naming both consequences (a pre-created lock stops every refresh; a
  pre-seeded status record defeats the staleness signal). Pre-existing, still correct, and it is what
  makes the permission audit above enforced rather than observed.

### 5. Invariants

| Invariant | How it was checked | Verdict |
|---|---|---|
| **D-104** — no LLM in the scoring path | `git diff 1069907..HEAD -- src/` is **two files, +84/-3**: `adapter/main.py` (health field + the new route) and `workflows/schema.py` (**docstring only**). `rank.py`, `recommend.py`, `build.py`, `categories.py` are untouched across the whole milestone. The on-device model exists only in `ios/.../Router.swift`, produces only a `RoutingOutcome` whose fields are `{categoryID, tier, unmeasured}` (asserted structurally by `test_router_hints.py:98-111`), and nothing typed reaches the engine (§3). | **HOLDS** |
| **D-115 / D-125** — `/v1` payload frozen; no EXISTING response field changed | Differential: the M10 tree (`1069907`) and HEAD were each imported against the same `advisor.db` with `APP_BUILD` pinned, and `/v1/categories` plus `/v1/recommendations` were dumped over 4 tasks x 3 budgets and 8 adversarial inputs. Output **byte-identical**, md5 `b4271929321d75eaf9d89d9fdd0f1207` on both. D-134's reading — a sibling resource is not a payload revision — is therefore true as measured, not merely argued. | **HOLDS** |
| **D-116** — evidence database is a shipped, mounted artifact; ingestion never on a serving host | `Dockerfile:24` sets `MODEL_RANKING_DB=/data/advisor.db` with `VOLUME ["/data"]` and no database in the image; `:33-34` runs as `appuser` uid 10001, non-root; `main.py:284-296`/`schema.py:397+` open it **read-only** so an anonymous GET cannot migrate the operator's schema. The refresh job (`deploy/...plist:45-46`) is the owner's machine only and says so. M11 changed none of this. | **HOLDS** |
| **INV-23** — read-only URIs derived, never concatenated | `main.py:296` delegates to `schema.open_readonly`, which builds the URI via `Path.resolve().as_uri()`. Probed with a path containing `?` and `#` (`we?ird#name.db`) — `/health` returned `evidence: unavailable` and created nothing; no `mode=ro` was dropped. The M11 docstring addition at `schema.py:400-406` correctly documents that `resolve()` follows symlinks and states the condition under which that would stop being safe. The iOS half is derived too: `EngineClient.swift:161-168` uses `URLComponents` + `URLQueryItem`, never string concatenation, with a same-host redirect delegate at `:90-107`. | **HOLDS** |
| **D-129** — the refresh's record is a file; `runner` makes it visible | `refresh.py::write_status` + `environment_problems` unchanged this milestone; `runner` reads `advisor.db.refresh.json`. `enable_refresh.sh:41-43` correctly points the operator at the status file rather than at the job. The requirement it serves (REQ-RUN-002, two observed cycles) is honestly marked **NOT MET** in `docs/prd.md` and ESCALATED as W-071 — the record does not claim what has not happened. | **HOLDS** (implementation); requirement openly unmet |

### 6. Security baseline (`docs/security-baseline.md`), walked

1. **No plaintext creds / no default-admin** — this surface authenticates nobody and stores no
   credential. `make secrets` (gitleaks, 55 MB) clean; `bootstrap-check` C7 runs in `make check`, green.
2. **Server-side authz on every mutating route** — there are **no mutating routes**. All four are
   `GET`; `POST /v1/budgets` → 405. The one write path in the system (`workflows.refresh`) is an
   operator-invoked local process, never reachable from HTTP, and the serving handle is read-only.
3. **CORS allowlist** — `main.py:252-282` (`cors_origins`) **raises `ConfigError` on `*` in every
   environment**, rejects any non-`http(s)://` origin, and defaults to no cross-origin access at all;
   `allow_credentials=False` is hardcoded with `allow_methods=["GET"]`. Stronger than the baseline asks.
4. **Validate security config at startup, fail prod** — `validate_startup_config` runs at import
   (`main.py:481`), an unset/unrecognised `APP_ENV` takes the **strict** branch, and it reports all
   problems at once. `/health` under a missing database still boots in `development` and emits the
   warning to the log (observed in every probe run above).
5. **Encrypt creds/PII at rest** — not applicable; the artifact is public benchmark and pricing data.
   No credential and no PII is stored. Confirmed against the schema (`models`, `scores`, `pricing`,
   `px_median`, `plans`, `plan_models`, `plan_config`).
6. **Generic client errors** — the 400s echo the attacker's own input bounded to 40 chars by
   `_echo` (`main.py:539-541`), inside a JSON body with `X-Content-Type-Options: nosniff` — probed with
   `<svg onload=alert(1)>`, `'; DROP TABLE scores--` and `../../etc/passwd`, all reflected as JSON
   string literals, none executable. The 503s say only *"The evidence database is not available."*
   with no path, and `main.py:519-531` installs an explicit `Exception` handler because Starlette's
   `ServerErrorMiddleware` sits outside user middleware — so the 500 body carries no exception text
   and still carries the header. `tests/unit/test_api_v1.py:488+` asserts the header on all of them.

### 7. CI — fork PRs, pinning, `--no-cov`

- **No `pull_request_target`, no `workflow_run`, no self-hosted runners** anywhere in
  `.github/workflows/`. `contract-tests.yml` uses plain `pull_request`, which runs the fork's code
  with a read-only `GITHUB_TOKEN` and **no secrets** — and this workflow references no secret.
- **A malicious fork PR can change what runs** (it supplies the workflow file, `pyproject.toml` and
  `tests/integration/**`) — that is inherent to `pull_request`, and here the blast radius is a
  throwaway GitHub-hosted VM with a read-only token. `permissions: contents: read` at
  `contract-tests.yml:66-67` is correct and is the mitigation that matters. `concurrency` is keyed to
  `github.ref`, which is per-PR, so no cross-PR cancellation abuse. **Not blocking.** The residual
  self-declaring-tolerance issue is MINOR-8.
- **Action SHAs are pinned**, all of them: `actions/checkout@11d5960a…` / `@08c6903c…`,
  `actions/setup-python@a26af69b…`, `gitleaks/gitleaks-action@ff98106e…`,
  `anthropics/claude-code-action@9d7150bc…`. No floating tags in any of the four workflows.
- **`--no-cov` hides nothing that mattered.** `pyproject.toml` sets `fail_under = 85` for the **full**
  suite; the step runs only `tests/integration` (14 tests, five live endpoints), which measures ~18%
  of the application and made the workflow structurally unpassable. The coverage that matters is
  enforced elsewhere and was measured green here: `make check` → **88.34%** against the 85 floor, plus
  `scripts/coverage_floor.py` PASS across 33 modules at a 60% per-module floor. Removing `--no-cov`
  would re-break the workflow without adding a single covered line.
- **Known and already ledgered:** `make swift-test` is in `check:` but in **no CI job** —
  `ci.yml` runs `ruff`/`mypy`/`pytest` directly, never `make check`, and an `ubuntu-latest` runner has
  no Swift toolchain, so the 59 Swift tests are enforced only on a machine with Xcode. This is
  W-060, ACCEPTED, and the target degrades **loudly** (`swift-test SKIPPED NO-ENVIRONMENT`) rather
  than silently passing. Recorded here for completeness, not raised as a new finding.

### 8. Semantic-security sweep (v3.3)

No weakened or removed validation, no broadened permission or scope, no disabled or "temporarily"
bypassed check, no debug flag left on, and no error-handling change on any auth path (there is no
auth path) — with **one exception, which is BLOCKING-1**: `wave_check.py`'s row predicate is a new
check that fails open. `docs_url`/`redoc_url`/`openapi_url` remain `None` (`main.py:465-467`);
`raise_server_exceptions` is a test-client argument only; no `continue-on-error` was added to any
workflow; `.governed-records` was **widened**, not narrowed, and the era-scoping is argued from
GPF-001 rather than from convenience.

---

## Verdict

**CONDITIONAL PASS — the served `/v1` product surface is clean and D-104, D-115/D-125, D-116, INV-23 and D-129 all hold under measurement; BLOCKING-1 must be closed before this milestone's wave-close records can be treated as evidence, because the gate that certifies them passes a wave with no review at all after a one-word edit (reproduced, exit 0).**
