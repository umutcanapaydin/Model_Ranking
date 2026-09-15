---
record_type: review
id: m13-security-review
status: ratified
seat: independent
date: 2026-09-15
---
# M13 Stage 4.0 Security Review - a probe that runs the serving path, and a memo that stopped asking

> **Independent seat.** I wrote none of this code. Policy was read from the protected base ref only
> (`git show HEAD:subagent-profiles/Security-Reviewer.md`, `HEAD:docs/security-baseline.md`,
> `HEAD:docs/closure-checklist.md` section B.2a, `HEAD:AGENTS.md`, `HEAD:permission-matrix.md`,
> format from `HEAD:docs/reviews/m12-security-review.md`) per V4C-06. Every claim below is measured;
> where a claim rests on running something, the command and its result are named.

## 0. How this record was produced, and the surface it covers

**Surface.** The whole milestone: `335d844..cda57b1` (three commits: W1 `3440abe`, W2 `10a521c`,
W3 `cda57b1`; 58 files, +8182/-595) read with `git diff 335d844..cda57b1`, plus the uncommitted W4
diff (406 lines, display and records only) handed to me as a file. I did not take the W4 tree on
trust: `git archive cda57b1` extracted into a private scratch directory, `git apply --check` then
`git apply` of the W4 diff, and `cmp` of every W4-touched path against the owner's working tree -
all eight byte-identical. The only other difference in the working tree is an untracked owner note,
`model_ranking_suggestions_coku`, which is not part of any commit or of the W4 diff and is outside
this surface.

**Method.** Read every changed line of `src/`, `runner`, `scripts/runner_verdict.sh` and the iOS
Engine and `ContentView`; ran the gate targets; then ran every exploit and mutant in a PRIVATE copy
(`<scratchpad>/w4tree`, `<scratchpad>/w4mut`) against private copies of `advisor.db`, importing the
private tree's own `src` (verified: `app.__file__` resolves inside the scratch directory). Nothing ran
against the owner's live artifact in a way that writes.

**What I modified.** This file, and nothing else. `make check` was run in the owner's tree (a
permitted gate target); it writes only its usual ignored build outputs.

---

## 1. The section B.2a walk (one line per item)

| Item | Referent or skip reason | Result |
|---|---|---|
| Secrets | `gitleaks detect --log-opts=335d844..cda57b1`: 3 commits, 530 KB, **no leaks found**; `gitleaks detect --no-git` over the private W4 tree with the repo's `.gitleaks.toml`: 4.8 MB, **no leaks found** | PASS |
| Dependency hygiene | `git diff --stat 335d844..cda57b1 -- pyproject.toml ios/Package.swift` is empty; the one new import in the range is stdlib (`import datetime as _dt`, `recommend.py`); `pip_audit`: **No known vulnerabilities found**; `scripts/slopsquat_check.py`: **15 declared, 0 suspect** | PASS |
| V3C-11 no plaintext creds / default admin | `make bootstrap-check`: C7 **ok**, `0 fail / 1 warn` (the warn is C6, license review N/A) | PASS |
| V3C-12 server-side authz on mutating routes | No mutating route exists or was added: the only routes are `GET /health`, `/v1/categories`, `/v1/budgets`, `/v1/recommendations` (`main.py:1117`, `:1181`, `:1257`) | N/A, holds |
| V3C-13 CORS | Unchanged by the range: wildcard refused at `main.py:270-297`, `allow_credentials=False` at `main.py:604`, methods `GET` only | PASS |
| V3C-51 startup config validation | `validate_startup_config` still runs at import (`main.py:585`) and is STRONGER: it now runs the serving path per surface (`main.py:429-448`) | PASS |
| V3C-56 creds/PII at rest | Nothing stored: no credential, no account; the client persists only the language choice (`ContentView.swift:50`); the typed question is never persisted | N/A |
| Generic client errors | Unchanged `_unhandled` (`main.py:619`); `/v1/categories` never errors (fails open to `null`, logs type names only); `/health` returns only `servable`/`unavailable`. The probe's full SQLite message reaches the boot log only (V3C-103 shape) | PASS |
| Control-class fail direction | Serving path fails CLOSED on an unreadable artifact (503). The `/health` evidence signal now fails OPEN in two states it used to catch - **MAJOR-1** | FINDING |
| External-surface defaults | `/v1/categories` gained a per-request read-only open (D-138); measured cheaper than `/v1/recommendations` (section 3); no new route, no new parameter | PASS |
| Prompt-injection hygiene | On-device model constrained by a schema over the engine's ids plus a sentinel (`Router.swift:299`, `:356`), output re-checked (`Router.swift:372`); the only third-party strings in reach are bounded (`label`, `Language.swift:101-108`); no injection-class text in the range's records (section 3) | PASS |
| Built is not wired (V3C-73) | Every guard added this milestone traced to its live call site - section 4. All wired; one unguarded by any test (MAJOR-1) | PASS with findings |
| Negative test per invariant (V3C-74) | Two invariant tests pass mutants that remove the invariant - **MAJOR-2**, **MINOR-2** | FINDING |
| Skip ledger | `make check` -> **exit 0**: 869 passed, **12 skipped** (5 network contract tests gated on `RUN_CONTRACT_TESTS`, 7 gated on `EPOCH_DATA_DIR`), same 12 as M12 and as every M13 wave-close row; `swift-test PASS: 211`. Pulled-forward HIGH security pass WAIVED in 3 of 3 code waves - **MAJOR-3** | FINDING |
| Gate at the W4 tree | `make check` -> `EXIT=0`; `check_records PASS`; `wave-check-all PASS: 28`; `conformance-gate PASS: 6, all exempted and still firing` | PASS |

---

## 2. Findings

### MAJOR-1 - The `/health` memo reports `servable` for an artifact the engine cannot read

`src/app/adapter/main.py:340-356` (memo), `:1117-1143` (`health`)

M13-W1 memoised `_database_unusable` on `(str(path), st_mtime_ns, st_size)` so that `/health` would
stop running nine rankings per poll. The key answers "is this the same file content?" and the probe
answers "can this process serve it?" - and those differ whenever the file becomes unreadable without
its mtime or size moving. **The cheap check that used to run on every `/health` (open read-only)
went into the memo along with the expensive one.**

**Reproduced** on private copies, through `fastapi.testclient` against the W4 tree:

| Step | `/health` evidence | `/v1/recommendations?task=expert` | Uncached `_probe_database` |
|---|---|---|---|
| Fresh copy | `servable` | 200 | `None` |
| `chmod 000` (key verified unchanged) | **`servable`** | **503** `evidence_unavailable` | `cannot be opened read-only: OperationalError` |
| First 16 bytes overwritten, size kept, `os.utime` restores the old `mtime_ns` | **`servable`** | 200 with every surface disclosed unreadable | `is unreadable: DatabaseError` |

The uncached column is exactly what `/health` said before M13. `grep -rn _UNUSABLE_MEMO tests/` is
empty: no test covers the memo at all, including the replacement case its own comment
(`main.py:325-328`) says the key exists for.

**Why it matters.** `health()`'s own docstring (`main.py:1124-1130`) says `evidence` exists because
Stage 4.3 verifies a deploy by curling `/health`, and the W-023/W-058 shape - "healthy to every
existence check, answering nothing" - is what it closes. A `chown` or `chmod` during a volume
migration, or a permissions-hardening pass, now reproduces that shape.

**Why MAJOR and not BLOCKING.** It is not attacker-reachable (it needs write or chmod on the host's
filesystem); the serving path still fails closed (503, or an honest per-surface disclosure); and M13
does not deploy. It is a diagnostic that lies, on a control whose whole purpose is to not lie.

**Remedy.** Add `st_ino` and `st_ctime_ns` to the key. `ctime` changes on every chmod, chown and
content write, and `os.utime` cannot set it. Also add `st_mode` and `st_uid`, or keep the
0.06 ms `open_readonly` + `SELECT count(*) FROM sqlite_master` on every call and memoise only the
nine-ranking part. Add two negative tests through `/health`: `chmod 000` after a first `servable`
must read `unavailable`, and a same-size in-place corruption with the mtime restored must read
`unavailable`.

### MAJOR-2 - REQ-RTR-004's citing test passes a client that sends the typed question to the engine

`tests/unit/test_router_hints.py:114-135` · `ios/ModelRanking/ContentView.swift:539`

The shipped code holds the invariant - I read the whole path: `submit` -> `ask`
(`ContentView.swift:469-503`) routes on-device, assigns `task = outcome.categoryID` (`:497`), keeps
the typed text only for the on-screen echo (`asked = typed`, `:501`), and `load` sends `task` and
`budget` only (`:539`, `EngineClient.swift:173-174`). **The test that is supposed to fail if that
stops being true does not.**

**Reproduced.** In the private mutant tree I changed `ContentView.swift:539` to
`client.recommendation(task: asked.isEmpty ? task : asked, budget: budget)`, which compiles and sends
the reader's words to the engine on every reload after a question. `pytest tests/unit/test_router_hints.py
tests/unit/test_ios_client_contract.py` -> **20 passed**, same as the unmutated baseline. The test
looks for `question` beside `URLQueryItem` and for the word `question` in `EngineClient.swift`; the
milestone's rewrite of this exact path (W3: `asked`, `typed`, two request gates) routes the text
through variables neither regex names.

It would not stay on the device if leaked. The engine answers an unknown `task` with a 400 that echoes the
first 40 characters (`_echo`, `main.py` `recommendations`), and the query string lands in any
access log in front of it.

**Why MAJOR.** It is a privacy invariant, REQ-RTR-004, and V3C-74 requires its citing test to FAIL when the
invariant is removed. The milestone rewrote the path the test guards and left the test as it was. It is
not exploitable today.

**Remedy.** Make the test assert data flow, not vocabulary. Every argument at every `client.` call
site in `ContentView.swift` must be the bare identifiers `task` / `budget` / `[]`, and every
assignment `task = ...` must have a right-hand side in `{outcome.categoryID, id}`. Keep the mutant
above as the test's own proof that it can fail.

### MAJOR-3 - The HIGH-tier pulled-forward security pass was waived in all three code waves, and the 3x trigger cannot see it

`docs/plans/m13-wave-1-close.md:19` · `m13-wave-2-close.md:27` · `m13-wave-3-close.md:32`

The signed plan tags every code wave HIGH (`docs/plans/m13-plan.md:4`, `:86`, `:109`, `:125`), and
V3C-78 (`AGENTS.md` section 4; `docs/decisions.md:167`) makes a pulled-forward security pass part
of the HIGH tier. All three rows read WAIVED with the same reason: no auth, PII, payment, crypto or
migration surface. That is the Security-Reviewer profile's narrower MAY-trigger, not the tier
definition the plan used. The waivers are honest and each names a local ledger row, so V4C-13's
"recorded, never hidden" is met at the wave level. But:

- `grep -n M13 docs/warnings.ledger.md` returns nothing, so C2b, which reads that ledger, cannot
  count three bypasses of one control in one milestone. That count is exactly what V4C-13's 3x trigger is for.
- `docs/EXPERIENCE.md` carries no M13 `control-bypass` entry yet. This is due at 4.2, and it is listed so
  the capture does not miss it.
- **The waiver had a cost.** W1 is the wave that shipped MAJOR-1. A security read of that slice
  at W1 is where a memo on a readiness probe is most likely to be questioned.

**Remedy.** Add one ledger row in `docs/warnings.ledger.md` per waiver, naming `V3C-78` in the path
column so C2b can count them. Then either run the 3x control review, or write an ADR that reconciles the
profile's MAY with V3C-78's tier definition, so the next plan's HIGH tag means one thing.

### MINOR-1 - `/v1/categories` writes one warning per unauthenticated request against an unreadable artifact

`src/app/adapter/main.py:1164`, `:1173`

Against a corrupt private copy, 101 requests produced **101** `WARNING` lines
(`/v1/categories could not read ages from the artifact: DatabaseError`), all answering 200 with every
age `null`. The content is safe: a fixed sentence plus an exception type name, with no path and no message.
The volume is attacker-driven, though, and while MAJOR-1's memo says `servable` the operator sees a
log flood that `/health` contradicts. **Remedy:** log once per artifact identity by reusing the
memo key, or rate-limit the line.

### MINOR-2 - The D-126 boundary test reads only `let` fields, and W3 added a `var`

`tests/unit/test_router_hints.py:98-111` · `ios/ModelRanking/Engine/Router.swift:43`

The test asserts `RoutingOutcome`'s fields are exactly `{categoryID, tier, unmeasured}` by matching
`let (\w+):`. W3 added `var alternatives: [String] = []`, which the regex does not see, and the set
was never updated. **Mutant:** adding `var praise: String = "the best model is X"` beside it ->
**20 passed**. Today `alternatives` holds only the router's own hint ids for surfaces the engine
advertised (`Router.swift:186`, `:248-251`, `:264`), so it is not a channel for an opinion. The
guard can be walked around with one keyword, though. **Remedy:** match `(?:let|var) (\w+):`,
excluding computed properties, and name `alternatives` in the declared set.

### MINOR-3 - The Swift test floor was not raised when M13 added 90 tests

`Makefile:132`

`SWIFT_TEST_FLOOR = 121`, and the suite runs **211**. The recipe's own comment says "Raise when
tests are added; never lower without a ledger row". As it stands, up to 90 tests can stop being
discovered with the gate green. That covers this milestone's deadline tests (`FrontDoorTests.swift:451-482`), the
unmeasured-question tests (`:197`), the request-gate tests (`:63`) and the hostile-score tests in
`ScoresTests.swift`. **Remedy:** raise the floor to 211 in the closure commit.

### NIT-1 - `firstWithin` would trap on a non-finite or astronomical deadline

`ios/ModelRanking/Engine/Router.swift:493`: `UInt64(max(seconds, 0) * 1_000_000_000)` traps on NaN
(Swift's `max` returns the NaN) and on anything above about 1.8e10 seconds. `modelTimeout` is a
source constant of 8 (`:439`) and no wire value reaches it, so this is hygiene, the M12 BLOCKING-1
class in a place nobody can currently feed. **Remedy:** `guard seconds.isFinite`, and clamp.

### NIT-2 - An abandoned on-device model call is not waited for, so they can stack

`Router.swift:488-500`. After the 8-second deadline the send button re-enables, and the abandoned
`LanguageModelSession` is only asked to cancel (`:497`). A reader who repeats a question into a hung
model can stack calls on their own device. Nothing leaves the device. **Remedy:** skip the model
tier while a previous model call is still outstanding.

---

## 3. What checks out, with the evidence I ran

| Question I was asked | How I checked | Verdict |
|---|---|---|
| `/health` cost per unauthenticated request, memo growth or poisoning | Mean of 200 requests via `TestClient`: memo hit **0.87 ms**, forced miss **11.9 ms** (the nine-ranking probe). The key is `(configured path, mtime_ns, size)`: no request input reaches it, so no caller can force a miss or plant an entry. The memo is bounded (`main.py:354`, cleared above 4) and held **1** entry after about 900 requests. A TOCTOU replacement between `stat` and open stores the new file's verdict under the old key, which the next `stat` never matches again. | CLEAN (except MAJOR-1) |
| `/v1/categories` cost against `/v1/recommendations` | **1.36 ms** against **4.68 ms** (`expert`) and **7.73 ms** (`coding`). `EXPLAIN QUERY PLAN` on `secondary_age_days` (`recommend.py:207`): two `SEARCH scores`. The SQL is parameterised and read-only through `open_readonly`. Every error class a replaced or corrupt file raises is `sqlite3.Error` and is caught; `ValueError` from a malformed date is caught inside. A `null` age renders honestly on the client (`Uncertainty.swift:240-255`) and is bounded (`:232`). | CLEAN (except MINOR-1) |
| Can a third-party string reach `_evidence_dating`? | The argument is `spec.primary_benchmark` (`main.py:965`), a module literal (`categories.py:70-200`). I enumerated all five dating notes served across nine surfaces: each names one of those literals. | CLEAN |
| Can an upstream force or suppress a refresh publish through `evidence_source`? | `evidence_source` is `scores.source`, set by the build from our own board config (`build.py:231`), never from upstream text, and chosen deterministically (`rank.py:268`, `ROW_NUMBER` over run date, harness, source, raw name), so a tie cannot make it flap. Removing a field from `UNHASHED_ROW_FIELDS` (`refresh.py:247`) can only turn `unchanged` into `changed`, never the reverse, so suppression is impossible. Every such publish still passes `_reason_to_refuse` (`refresh.py:677`, called at `:800`) and the baseline re-read (`:710`). | CLEAN |
| `runner` and `runner_verdict.sh` quoting and spoofing | No `eval`; reasons are printed through `printf '%s'` (`runner_verdict.sh:53`); every expansion is quoted; names and reasons are script constants. The verdict comes from exit codes, never from grepping tool output, so a test cannot print its way to green. If the library is missing, `. "$REPO/scripts/runner_verdict.sh"` fails, `runner_verdict` is then command-not-found at `runner:323`, and the run exits 1: fail closed. `test_runner_accounting.py:191` pins that a skip path never also records a pass. | CLEAN |
| `ResumeOnce`: can the continuation be resumed twice, or never? | The lock plus nil-out (`Router.swift:503-516`) resumes at most once; both racers always call `resume`; both are unstructured tasks, so a parent cancellation cannot strand the continuation; `Task.sleep`'s cancellation error is swallowed by `try?` and still resumes. Covered by `FrontDoorTests.swift:451` and `:472`. | CLEAN |
| On-device prompt and schema, `ModelOutputBoundary` | Schema `anyOf` = the engine's ids plus `__none__` (`:299`, `:356`); output re-validated against the fetched ids (`:372`). The prompt interpolates only client hint text for ids the client knows. A hostile engine can at most steer routing among its own ids, which it already controls. | CLEAN |
| Does anything typed leave the device? (REQ-RTR-004) | Read, not grepped: the model tier is `LanguageModelSession` and the wording tier is `NLContextualEmbedding`, both on-device. `ContentView.swift:469-549` sends only `task`/`budget`; no `print`, `Logger`, `UserDefaults` or pasteboard write of the question anywhere in `ios/ModelRanking`; the echo renders via `Text(String)`, verbatim, with no Markdown. | HOLDS (its test does not - MAJOR-2) |
| `EngineClient` after `budgets()` removal | The range's only change to `EngineClient.swift` is the deletion; `SameHostOnly` (`:119`, used at `:204`) is unchanged. | CLEAN |
| New request and routing gates in `ContentView` | `gate` ticket compared at apply time (`:520`, `:533`, `:540-546`); `routingGate` retired by `select` (`:510`) and checked after routing and after load (`:492`, `:499`); `routingInFlight` is set synchronously in `submit` (`:469-473`), so a double tap cannot route twice. | CLEAN |
| W4 display code | `scoreText` refuses NaN, infinity, negatives, `1e19` and above-ceiling percentages (`Scores.swift:42-47`, `ScoresTests`); `priceTag` refuses non-finite and negative values (`:62`); `money` returns `nil` rather than `$0` and both callers handle it. No network, no persistence, no new input. | CLEAN |
| Injection-class content in the range | `git diff 335d844..cda57b1 -- docs note.txt` grepped for text addressed to this seat: the only hits are the three WAIVED rows saying Stage 4.0 covers the wave, which is a statement and not an instruction (it is MAJOR-3's subject). W4's `.language-allow` line uses the mechanism `AGENTS.md` section 5 documents, with a written reason. No policy file is changed by the range or by W4. | NONE FOUND |

---

## 4. Built is not wired: every guard this milestone added, and its live call site

| Guard | Live call site | Citing test | Verdict |
|---|---|---|---|
| Probe runs the serving path, refuses zero surfaces | `main.py:429-448`, reached at import (`:585`) and per `/health` (`:1117`) | `test_startup_schema_validation.py:107` | WIRED |
| Probe memo | `main.py:340-356`, reached per `/health` | **none** | WIRED, UNTESTED (MAJOR-1) |
| D-139: stale or undated second board does not upgrade | `recommend.py:268`, fed at `:511` into every pick | `test_secondary_evidence_age.py` (6 tests) | WIRED |
| Pareto dominance on ties (`_dominates`, `_plan_dominates`) | `pareto_frontier`, `subscribe._pareto` | `test_pareto_dominance.py` | WIRED |
| `evidence_source` hashed | `_row_digest` -> `serving_summary` -> `fingerprint_of` -> `refresh.py:788` | `test_refresh_attribution_fingerprint.py:61` | WIRED |
| Skip is never a pass | `runner:43` sources the library; `runner:323` is the verdict | `test_runner_accounting.py:191` | WIRED |
| `/v1/categories` ages fail open to `null` | `main.py:1147-1177`, called by `categories` (`:1181`) | `test_uncertainty_contract.py:115-126` (through the live route) | WIRED |
| Request gates (REQ-ASK-004) | `ContentView.swift:490-499`, `:510`, `:520-546` | `FrontDoorTests.swift:63`, `test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on` | WIRED |
| Model-tier deadline | `Router.swift:454` | `FrontDoorTests.swift:451-482` | WIRED |
| Wording-tier decline hints | `Router.swift:234-252` | `FrontDoorTests.swift:197` | WIRED |
| Hostile score and price refusal (W4) | `figuresLine` in `PickRow` / `RankedRow` (W4 diff, `ContentView.swift`) | `ScoresTests.swift` | WIRED |

---

## 5. Acceptance criteria evidence (the security-relevant criteria this milestone touched)

- REQ-RTR-004 -> `ContentView.swift:497`, `:539`; `EngineClient.swift:173-174` (holds; test weak, MAJOR-2)
- REQ-FIX-002 -> `main.py:429-448`; `test_startup_schema_validation.py:107`
- REQ-FIX-003 -> `refresh.py:247`; `test_refresh_attribution_fingerprint.py:61`
- REQ-FIX-004 -> `scripts/runner_verdict.sh:40-70`; `test_runner_accounting.py:191`
- REQ-UNC-002 -> `main.py:1147-1177`, `recommend.py:207`, `:268`; `test_secondary_evidence_age.py`
- REQ-UNC-003 -> `main.py:660`, `:965`; benchmark is a module literal (`categories.py:70-200`)
- REQ-ASK-004 -> `FrontDoor.swift:24`; `ContentView.swift:520`; `FrontDoorTests.swift:63`
- REQ-CMP-004 -> `Scores.swift:42-62`; `ScoresTests.swift`

## 6. Risks queued to the next milestone

- MAJOR-1's remedy and its two negative tests, before any Stage 4.3 relies on `/health` evidence.
- MAJOR-2 and MINOR-2: rewrite the two router-boundary tests to assert data flow, with their mutants
  kept as proof.
- MAJOR-3: ledger rows plus the V3C-78 control review, and the 4.2 `control-bypass` entry.

---

**VERDICT: PASS WITH FINDINGS - no BLOCKING. Three MAJOR (a `/health` memo that reports a
permission-revoked or in-place-corrupted artifact as servable; REQ-RTR-004's citing test passing a
client that leaks the typed question; the HIGH-tier pulled-forward security pass waived in all three
code waves without reaching the ledger C2b counts), three MINOR, two NIT. The web/API baseline holds,
the gates are green, and nothing typed by the reader leaves the device in the shipped code.**
