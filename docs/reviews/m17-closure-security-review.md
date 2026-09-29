---
record_type: review
id: m17-closure-security-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-29
---
# M17 Stage 4.0 Security Review: boards to the phone, and a question that picks them

> **Independent seat.** I wrote none of M17's code, and I am not any of its wave reviewers. Policy
> was read from the protected base only: `git show origin/main:` for
> `.claude/agents/Security-Reviewer.md`, `docs/security-baseline.md`, `permission-matrix.md`,
> `AGENTS.md` and `docs/closure-checklist.md` (§B and §E.1). The surface is `git diff cf00ec7 3f2e91d`:
> 209 commits, 183 of them non-merge, 283 files, +25467/-6649. `origin/main` = `3f2e91d`. The only
> repository file this seat creates is this one.

## Verdict

**Independent:** yes.

**PASS WITH FINDINGS.** Nothing is BLOCKING and nothing is MAJOR. There are **5 MINOR and 10 INFO**.
No finding is exploitable in the current scope: the engine binds `127.0.0.1`, nothing is deployed
to another reader, the routes are GET only and public, and every hostile path found needs either a
code change or control of an upstream that already controls the numbers.

What M17 is built around holds under measurement:

- **The untrusted downloads are contained.** The W2 reader's controls still hold on `main` after W3
  widened the read to six more configs and #29 rewrote the download helper. All 10 mutants I placed
  in the reader (A1-A6) and the helper (D1-D4) were killed.
- **The board guards hold.** The D-159 and D-164 guards are each killed by a test when removed
  (F3-F7), and so is the #47 fix (G1).
- **`/v1/boards` serves positions and no score, within its boot bound** (B2, B3 killed). The W5
  schema fix holds: the W5 seat's free-text mutant, replayed on `main`, now fails three controls (P4).

M17's weak point is its negative tests, not its code. The shipped code is clean on every invariant
I checked, but 13 of my 41 mutants survived every test that reaches them. Four clusters matter:

- **INV-23 has no negative test on the readers M17 added** (MINOR-1). A `/v1/boards` that opens the served
  artifact read-write and writes to it on every GET passes all 1515 tests. This is M16's MINOR-2
  again: its remedy was applied to one reader only.
- **D-168 clause 9 ("its refinements … never leave the device") is held by spelling, not by data
  flow** (MINOR-3). A three-edit relay sends a question's refinement, such as `medicine`, on the
  day's `/v1/boards` request. It passes the text gate, `client-decls` and `swift test`.
- **The launchd service's loopback bind and its preflight are held by substring tests** (MINOR-4).
  Appending `--host 0.0.0.0` to the launcher passes every test.
- **Upstream dates reach the phone verbatim** (MINOR-2). Validation was fixed in one client at a
  time, and M17's new consumers (`/v1/boards`, the combined detail) read the clients that were not
  fixed.

## 0. Surface and method

**Waves and changes.**
- W1: the derived floor (D-159, `app.workflows.floors`), served on `/v1/categories`, and the board
  axis of the refresh guards.
- W2: the Arena slice parquet read (D-164, D-165), in four security rounds.
- W3: Epoch boards, the six Agent Arena configs through the W2 reader, accessibility
  (`app.workflows.access`) and the moving aliases (D-166). This wave had no security pass.
- W4: `GET /v1/boards` (D-167), `StandingsStore.swift`, `FetchedStandings`.
- #61/#65: `Combine.swift`.
- W5: `Refinements.swift`, `AnswerPlan.swift`, the router schema, the combined list in
  `ContentView.swift`, and `primary_board` (D-168).
- Fix PRs: #29, #46, #47 and #49.
- Enhancements: #36 (the launchd engine service), #31 (branch protection), #30 (the Epoch CI step)
  and #18 (DevFlow v6.4 under D-161).

**Method.**
- **Worktree.** A detached worktree at `3f2e91d`, with its own venv. No other seat used it.
- **Mutants.** Every mutant was applied by a script (`sec-m17-scratch/mut.py`). The script records
  each touched file's sha256 and makes an exact single-match edit. It then runs the full Python
  suite (`pytest -n auto -x`) or, for phone mutants, the three D-126 gates:
  - the text gate (`test_router_hints.py`, `test_ios_client_contract.py`, `test_refinements.py`,
    `test_ios_payload_contract.py`);
  - `scripts/client_decl_gate.py`;
  - `swift test --skip RouterBoundaryTests`, with an external `--scratch-path`.

  Afterwards the script restores the bytes in place and asserts the sha256. Every restore matched.
  `PYTHONDONTWRITEBYTECODE=1` was set throughout.
- **Bytecode.** The first baseline run left `__pycache__` in five source directories, written by
  the suite's own child processes, which do not inherit the variable. I deleted them, and the
  harness deletes any after each run. `git status --ignored` matched the starting state after every
  batch.
- **The served artifact.** `advisor.db` (a copy of the served artifact) was only ever read in place.
  Every probe that needed a changed artifact used a copy in the scratch directory. Its sha256 was
  `005855fa79ec729c5834c9504c3d62d6cf0de30e367c9cb4bfd14218a87aa5b9` before and after.
- **Network.**
  - No product upstream was contacted, no `build()` ran against a real source, and
    `RUN_CONTRACT_TESTS` was not set.
  - GitHub was read four times. Three were `gh issue list` / `gh pr list`, for the filed-issue check.
  - The fourth was a mistake: I ran `scripts/bootstrap-check.sh` twice, and its advisory C12 leg
    calls `scripts/ci_liveness.py`, which runs `gh run list`. I did not expect that call.
- **The owner's machine.**
  - One read-only `git config --get core.hooksPath` was run against the Desktop checkout by
    mistake. Nothing was written there, and its result is not used below.
  - No launchd job was loaded, unloaded or kick-started.
  - `scripts/engine_service.sh` was run once, in development mode, against a scratch copy with a
    lowered bound. It refused before starting uvicorn, so nothing listened.
- **Model calls.** The full `swift test` ran once, with its six existing on-device calls. No probe
  of mine called the model.

**Gates I ran myself:**

| Gate | Result |
|---|---|
| `pytest -n auto` (full, `MODEL_RANKING_REQUIRE_ARTIFACT=1`) | **1515 passed, 23 skipped** in 22 s |
| `swift test` (external `--scratch-path`) | **354 executed, 0 failures**. The manifest has 354 lines |
| `scripts/client_decl_gate.py` | `client-decls PASS: 15 client file(s) in 4 configuration(s)` |
| The D-126 text gate (four files above) | 52 passed |
| `gitleaks detect --log-opts=cf00ec7..3f2e91d` | 183 commits, **no leaks** |
| `git diff cf00ec7 3f2e91d \| gitleaks stdin`, repository config and default ruleset | **no leaks** (both). A random `ghp_` token fires under both configs, so the scan is live |
| `ruff check src tests scripts` | All checks passed |
| `ruff check --select S,BLE src` (the SAST substitute, see §5) | 9 hits, all deliberate. The ones M17 added: an `assert` on `Popen`'s pipes (`arena_slices.py:308`), and three documented catch-alls (`parquet_reader.py:80`, which fails closed; `parquet_reader.py:160`, where the reader answers an error; `protocols.py:124`, which hands the exception to the caller) |
| `bash scripts/bootstrap-check.sh` | C7, C9 and C10 pass. One FAIL: this detached worktree has no `core.hooksPath`, and the brief says branch protection "no" (I-3) |

## 1. Findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

**MINOR-1: INV-23 (the served artifact is read-only) has no negative test on any reader M17 added.
A `/v1/boards` that writes to the served artifact on every GET passes all 1515 tests.**

**Where.**
- The M17 readers:
  - `src/app/adapter/main.py:1409` (`boards()`, W4);
  - `:1262` (`_artifact_facts`, every `/v1/categories`, W1);
  - `:228` (`_standings_problem`, boot, W4);
  - `src/app/workflows/refresh.py:516` (`fingerprint_of`, which now reads the floor and the boards);
  - `refresh.py:944` (`_served_without`, #47);
  - `scripts/survey_boards.py:427` (`--floors`, W1).
- `scripts/calibrate_board.py:151` (`_self_check`, which reads the served floor since W1) already
  opens the artifact with a plain `sqlite3.connect(db)`.
- The controls:
  - `tests/unit/test_readonly_uri.py:75` refuses only `file:` f-strings;
  - `tests/unit/test_carry_forward.py:315` watches `sqlite3.connect` for one reader, `Carry.restore`;
  - `tests/unit/test_api_v1.py:727` compares bytes for `/v1/recommendations` only.

**Measured.** Each mutant replaced `open_readonly(x)` with `sqlite3.connect(x)`:

| Mutant | Reader | Result |
|---|---|---|
| I1 | `/v1/boards` | SURVIVED |
| I1w | `/v1/boards`, read-write plus `CREATE TABLE probe_written_by_a_get` and a commit, on every request | **SURVIVED** (1515 passed) |
| I2 | `/v1/categories` (`_artifact_facts`) | SURVIVED |
| I3 | the boot standings bound | SURVIVED |
| I6 | `fingerprint_of` | SURVIVED |
| I4 | `_served_without` | SURVIVED |
| I8 | `survey_boards --floors` | SURVIVED |
| I7 | `Carry.restore` | KILLED (`test_the_carry_opens_the_served_artifact_read_only`) |
| I4w | `_served_without` read-write, deleting the expired source's rows from the live file | KILLED (the refresh notices that its live artifact changed) |

With I1w applied, one `GET /v1/boards` against a scratch copy of the artifact returned 200 with
509,719 bytes, and the copy changed: `probe_written_by_a_get` was in it. `_self_check` pointed at
a missing path created a 0-byte database there before failing; on an existing copy it changed
nothing.

**Why MINOR.** No reader writes today, every query is a constant, and nothing is exploitable. But
this is M16's MINOR-2 recurring:
- M16's remedy was an AST gate over `sqlite3.connect`. The closure instead added one reader's test.
- M17 then added three readers and changed three more, and none of them is held.
- The route the phone calls daily can be made to write the artifact the engine serves, and CI would
  stay green.

**Remedy.**
1. Adopt M16's gate. Refuse any `sqlite3.connect(` in `src/` and `scripts/` whose argument is not
   `":memory:"`, with a named allowlist and one reason per entry:
   - `schema.connect`;
   - the build workspace;
   - the survey and calibrate scratch copies;
   - `recommend.py`'s CLI (or move it to `open_readonly`).

   Show it red on I1.
2. Turn the carry test's `sqlite3.connect` watcher into a fixture, and run it through `/v1/boards`,
   `/v1/categories`, the boot check, `fingerprint_of` and `_served_without`.
3. Add a before-and-after bytes test through `/v1/boards` and `/v1/categories`, the shape of
   `test_api_v1.py:727`.
4. Open `_self_check`'s database with `open_readonly`.

**MINOR-2: Upstream dates reach the phone verbatim. The sibling parsers were never given the
validation one client got, and M17's new consumers read them.**

**Where.**
- `src/app/clients/arena.py:400` keeps `str(pub)[:10]` as `run_date`.
- `src/app/clients/swebench.py:104` keeps `entry.get("date")` whole.
- `src/app/workflows/standings.py:116` and `:121` serve `max(run_date)` as `evidence_date`.
- `ios/ModelRanking/Engine/AnswerPlan.swift:41`, `Language.swift:594` and `ContentView.swift:1238`
  show it as "Newest evaluation: …".

The same defect was fixed in `epoch_board.py:196-201` ("`<script>alert(1)</script>` became the
evidence date `'<script>al'`"). W2 also fixed it for the same Arena column in the slice parser
(`arena_slices.py:372-380`, S-R4). The overall parser that reads that column of that dataset was
left as it was.

**Measured (offline, scratch copies).**
- `parse_arena` with five rows dated `<script>alert(1)</script>` kept all five, with `run_date` =
  `<script>al`.
- `parse_verified` kept a 3,960-character date and a `resolved` of `Infinity`.
- On a copy of the artifact with those dates, `/v1/boards` returned 200 (513,669 bytes). It served
  `"evidence_date": "<script>al"` for `arena` and the 3,960 characters of prose for `swebench`.
- `arena` is `assistant`'s primary board, and `assistant` takes refinements
  (`Refinements.swift:43-91`). So that date is shown on the combined list's detail screen.
- The `swebench` date is served and kept on the phone. It is not shown today, because coding takes
  no refinement (D-168 clause 2), but #73 is about exactly that path.

**The same pattern for non-finite values.** M15's fix (`arena.py:379`) covers Arena only.
`swebench.py:88-102` accepts `Infinity` (measured), and `aider.py:91-100` has the same check
(read, not run). With half the coding board infinite on a copy:
- `/v1/categories` answered 200 with coding's `min_quality: null`. W1's derived floor silently
  became "no floor", because the framework serialises an infinite float as `null`.
- `/v1/recommendations?task=coding` answered 500, which is the pre-existing M15 shape.

**Why MINOR.** It is text only, shown verbatim by `Text(String)`, and at most 10 characters on the
board that is displayed. The engine is loopback-bound, and the attacker class (whoever controls a
board file) already controls the scores. It is M16 MAJOR-1's class in a date field, and much
smaller.

**Remedy.**
- Validate once, where every client meets: in `ScoreRow` or in `ingest._store_scores`.
  - `run_date` must parse with `date.fromisoformat`, or become `None`.
  - `score` must be finite.
  - The next client then inherits the rule instead of re-deriving it.
- Add negative tests through `parse_arena`, `parse_verified` and `/v1/boards`.

**MINOR-3: The privacy invariants for M17's two new phone sinks are held by spelling and by file
scope, not by data flow. A relay sends a refinement off the device, and every D-126 gate passes.**

- **P2 (the refinement, on `/v1/boards`).** Three edits:
  - in `EngineClient.swift`, `nonisolated(unsafe) static var tag = ""`;
  - in `boards()` (`:201`), `URLQueryItem(name: "t", value: Self.tag)` when `tag` is not empty;
  - in `ContentView.swift` after `:717`,
    `EngineClient.tag = outcome.refinements.map(\.value).joined(separator: ",")`.

  Results:
  - the text gate: 52 passed;
  - `client-decls`: PASS (15 files, 4 configurations);
  - `swift test`: 345 executed, 0 failures (the model-calling `RouterBoundaryTests` skipped).

  `testTheBoardsRequestCarriesNothing` (`EngineClientTests.swift:470`) runs with the tag empty. The
  day's parameterless request would then carry `medicine` or `legal`, against D-168 clause 9 ("its
  refinements and the reader's removals never leave the device").
- **P3 (the typed question, on disk).** One line in `ContentView.swift` after `:717`:
  `FetchedStandings(payload: JSONEncoder().encode(Standings(apiVersion: typed, …)))`, saved through
  `StandingsStore.onDevice.save`.
  - The text gate and `client-decls` pass.
  - The question is then kept in Caches, under the default protection class, outside the gap
    register's `.completeFileProtection`.
  - `StandingsStore.swift:5` says "Nothing the reader typed ever reaches it".
- **Known, and bigger now.** `scripts/client_decl_gate.py:28-31` documents this class (B19, B31).
  M17 raises the stakes in two ways:
  - the device now holds a sensitive attribute derived from the question (D-168 clause 5 answers
    medical and legal questions);
  - a request no user action asks for now fires once a day, right after a question
    (`ContentView.swift:786`).

**Why MINOR.** It needs a code change. The shipped client is clean: the unmutated control run (P0)
passes the text gate and `client-decls`, the baseline `swift test` passes, and P1 (a refinement assigned to `task`) is killed by
`test_nothing_typed_by_the_reader_reaches_the_engine`.

**Remedy.** Pin the declarations, as `Refinement(` already is:
- `EngineClient.swift` declares no mutable static or global state (`static var`,
  `nonisolated(unsafe)`);
- `boards()` calls exactly `fetch("v1/boards", query: [])`;
- `Standings(` is constructed nowhere in the client;
- `FetchedStandings(` appears only in `EngineClient.swift` and `StandingsStore.swift`.

**MINOR-4: The engine service's loopback bind and its fail-closed preflight are held only by
substring tests.**

**Where.**
- `scripts/engine_service.sh:73` (the `exec` line) and `:57-67` (the W-042 preflight);
- `scripts/install_engine_service.sh:137` (`chmod 700` on the wrapper);
- the test, `tests/unit/test_engine_service.py:177-181`, checks only that `--host 127.0.0.1` and
  `validate_startup_config` appear in the text.

**Measured.** Every one of these mutants passed all 1515 tests:
- L1: ` --host 0.0.0.0` appended to the `exec` line. uvicorn's own parser returns
  `host = 0.0.0.0` for that argument list: the last `--host` wins.
- L2: the preflight's `if` made `if false`.
- L3: `chmod 777` on the wrapper that launchd runs at every login.

L4 (the service running a non-release tree) is killed by
`test_the_service_runs_only_a_deployed_release`, so the right shape of test already exists here.

**Why it matters.** Every "not exploitable" rating in M16's closure, in M17's wave passes and in
this file rests on the loopback bind (D-116). #36 made the engine a login service that restarts
itself from a deployed copy.

**Remedy.**
- Parse the launcher's `exec` line and assert exactly one `--host`, with the value `127.0.0.1`.
- Run the launcher against an artifact that fails a bound, and assert `REFUSED` and exit 1. By
  hand, it does that.
- Assert the wrapper's mode through an install-style test.

**MINOR-5: M17 closes with four ledger rows it owned, and none is resolved or re-owned.**

`docs/warnings.ledger.md` rows W-125, W-126, W-130 and W-131 each name M17 as their owning milestone.

- **W-131: there is no security-invariants list.** `docs/security-invariants.md` does not exist. §3
  below is, again, a seat's reconstruction. Checklist §E.1 asks for this list at the release.
- **W-125 grew.** Importing `app.adapter.main` in a fresh interpreter now also loads
  `app.clients.arena_slices`, which starts the reader, and `app.clients.parquet_reader`, the reader
  itself (measured).
  `pyarrow`, `refresh`, `build` and `epoch_bundle` are not loaded, so D-154 still holds.
- **W-126: there is no time budget inside the child.** W3 makes this sharper. Every Hugging Face
  request is bounded at 120 s:
  - 6 `overall` boards (at least one page each) plus 8 parquet configs is 14 × 120 s = 28 minutes
    of the child's 30-minute kill (`nightly.py:71`);
  - before W3 it was 8 × 120 s = 16 minutes.

  So a uniformly slow Hugging Face night can now be killed whole, which loses every other source's
  night too. That is the outcome W2's S1 existed to prevent. This is derived from the constants; I
  did not run it.
- **W-130** is unchanged.

**Remedy.**
- Fix each row, or give it a new owning milestone with a reason.
- For W-131, adopt §3 as `docs/security-invariants.md`, with a gate that each cited test exists.
- For W-126, give the refresh a cycle budget, so that the sources left when it runs out carry
  (D-156) instead of the whole cycle being killed.

### INFO (verified; no action unless stated)

- **I-1: Policy, hooks and CI under D-161. No weakening found.**
  - Hooks and the matrix:
    - The PreToolUse guards now exit 2, which is what actually blocks.
    - They fail closed without `python3`, `python` or `grep`.
    - A push to the default branch is now blocked.
    - The post-edit check is `make check-fast`, which carries no security leg. That is documented.
    - The matrix's MINOR row on maintainer age was replaced by the rule that a dependency's first
      release is at least 90 days old.
  - `.gitleaks.toml` lost two path exemptions.
  - CI: the workflow diff is deletions only.
    - The Epoch-age step went (#30, owner-approved, D-158 clause 4).
    - A duplicate `pull-requests: write` key went.
  - Every `uses:` is SHA-pinned, and `ci.yml` keeps `contents: read`.
  - A scan of the added policy lines found no instruction aimed at a reviewer.
- **I-2: #31 × the issue agent.** Branch protection was applied with 0 required approvals
  (`docs/branch-protection.md`). `issue-agent.yml:13` and `:31` still say that branch protection
  stops a self-merge by that agent, whose token has `contents: write` and `pull-requests: write`.
  - What actually stops it now is the required status checks: pushes made with `GITHUB_TOKEN` start
    no workflow, so those checks never report.
  - `enforce_admins` is on.
  - Not measured (no GitHub reads). The comment should name the real barrier.
- **I-3: The project brief is stale after #31.** `docs/project-brief.md:53` still says "GitHub repo
  + branch protection | owner | proposed". `bootstrap-check` reads the brief as "branch protection:
  no" and fails a clone without `make hooks`, even though protection is on.
- **I-4: The always-on service has no Host check.** A web page could use DNS rebinding to read the
  public GET responses on `127.0.0.1:8080`.
  - There is no mutating route and no credential.
  - CORS is an allowlist, with credentials off (`main.py:694-699`).
  - Nothing sensitive is readable, so no action is needed while nothing is deployed.
- **I-5: A consequence to add to #57** (not re-raised).
  - The launcher's preflight refuses an artifact past a boot bound. Measured: with the standings
    bound lowered to 5,000, the launcher printed `REFUSED` and stopped before uvicorn.
  - The refresh runs inside the engine (D-154).
  - So an artifact the engine's own refresh publishes past a bound is served until the next
    restart. After that, launchd's `KeepAlive` restarts a refusing engine every 60 s, and no refresh
    can run to repair it.
- **I-6: Install-script hygiene.**
  - `--deploy-only DIR` prunes all but the three newest entries under `DIR/releases` with `rm -rf`
    (`install_engine_service.sh:100-102`).
  - Each deploy installs dependencies from PyPI with no lock (#35).
  - A look-alike listener is killed on command-line match. This affects the owner's own processes
    only (`:126-129`).
  - `origin/main` is resolved three times (fetch, `rev-parse`, `archive`) across one deploy.
- **I-7: W3 widened the W2 read path without a security pass. The W2 controls hold on `main`.**
  Killed:
  - A1 (`-P` removed), by `test_a_module_planted_in_the_working_directory_is_not_imported`;
  - A2 (the whole environment), by `test_the_reader_gets_no_secret_from_the_environment`;
  - A3 (an uncapped answer), by `test_the_parent_stops_reading_at_the_bound_rather_than_after_it`;
  - A4 (the value-length cap removed);
  - A5 (the watchdog failing open), by `test_the_watchdog_fails_closed`;
  - A6 (an unprintable reason).

  The #29 hop and deadline controls are killed too (D1-D4, §3).
- **I-8: The W5 S1 fix holds, but its third layer has no test.** The replayed free-text mutant (P4)
  fails three controls:
  - `test_only_the_wording_tier_builds_an_outcome_with_alternatives`;
  - two assertions of `testTheModelsSchemaOffersExactlyTheDeclaredChoicesAndNothingElse`.

  The third layer, the guard in `select` (`ContentView.swift:733`), has no test: removing it (P5)
  passes every gate.
- **I-9: Accessibility.** Values are allowlisted (E2 killed), and conflicting names serve no value
  (E3 killed). The raw names are unbounded but never served. #42 covers the missing loss guard.
- **I-10: A policy file changed within the reviewed range.** `.claude/agents/Security-Reviewer.md`
  moved from `subagent-profiles/` under D-161. It now names a Stage 5.1 release review, and it
  writes to `docs/reviews/release-security.md`. This Stage 4.0 seat keeps the M16 path and shape,
  as instructed. The release review is still owed before any deploy.

## 2. Per-wave security records: do their fixes still hold on `main`?

**W2 (four rounds).**

| Finding | Status on `3f2e91d` | Evidence (measured) |
|---|---|---|
| S1 (a non-`SourceError` ends the night) | **Holds** | The read is total, and `fetch_bounded_bytes` turns any failure into a `SourceError` (S-R3) |
| S2 / S-R1 (memory) | **Holds, by D-165** | The reader runs in a child under a 512 MiB ceiling that fails closed (A5 killed), with the value cap (A4 killed) |
| S-R2-1 (the parent reads unbounded) | **Holds** | The answer cap (A3 killed), a stderr tail, and a printable reason (A6 killed) |
| S-R2-4 (environment, working directory) | **Holds** | A1 and A2 killed |
| S3 (time before the body; any host) | **Holds, by #29** | https to declared hosts only, with a deadline over the whole fetch (D1-D4 killed) |
| S4 / S-R4 (stray dates in slices) | **Holds for slices** | `arena_slices.py:372-380`. Not for the `overall` parser: MINOR-2 |
| S-R3-1, S-R3-2, S-R3-4, S-R3-5 | **Holds** | The cap is 8 MiB (`:83`), the answer is split as bytes (`:347-351`), the tempfile is inside the `try` (`:287-290`), and a slice has a 4x ceiling (`:164-175`) |

**W4.**

| Finding | Status | Evidence |
|---|---|---|
| S1 (the store took any URL) | **Holds** | `url.isFileURL` guards `load` and `save` (`StandingsStore.swift:54`, `:67`). The gate gap is #58 |
| S2 (the cap and the stored fields) | **Holds as written** | `FetchedStandings` checks the cap and re-encodes. But a producer can still put typed text into a decoded field: MINOR-3, P3 |
| S3 | Filed | #56 |
| S4 | Filed | #60 |
| S5 | Filed | #55 |
| S6 | Filed | #57 (see I-5) |
| S7 (duplicates) | **Holds** | First row only (`Combine.swift:67-69`). The O(n²) half is #74 |

**W5.**

| Finding | Status | Evidence |
|---|---|---|
| S1 (a free-text field in the schema) | **Holds** | P4 killed by three controls. The `select` guard is untested (I-8) |
| S2 (quadratic combine) | Filed | #74 |
| S3 (the records overstated the boundary) | **Holds** | D-168 clause 9. What the code does not enforce: MINOR-3 |
| S4, S5 | **Hold** | Fixed in `bea72ff` |

## 3. M17 security invariants and their negative tests

Each row was checked by removing the invariant with an in-place edit and running the suite or the
phone gates (§0). KILLED means at least one named test failed; SURVIVED means everything passed.

| # | Invariant (producer) | Negative test that fails when it is removed | Mutant |
|---|---|---|---|
| 1 | D-165: the parquet file is read in a child, under a ceiling that fails closed | `test_arena_slices.py::test_the_watchdog_fails_closed` | A5 KILLED |
| 2 | D-165 clause 4: the parent reads a capped answer | `::test_the_parent_stops_reading_at_the_bound_rather_than_after_it` | A3 KILLED |
| 3 | The reader gets an allowlisted environment and `-P` | `::test_the_reader_gets_no_secret_from_the_environment`, `::test_a_module_planted_in_the_working_directory_is_not_imported` | A2, A1 KILLED |
| 4 | A text value is at most 256 characters | `::test_the_reader_answers_rows_or_an_error_in_process` | A4 KILLED |
| 5 | A reason is short and printable | `::test_only_the_tail_of_the_readers_stderr_is_quoted_and_it_is_printable` | A6 KILLED |
| 6 | #25/#29: every hop is https to a declared host; `.hf.co` is a domain, not a substring | `test_fetch_bounds.py::test_a_redirect_to_another_host_is_refused`, `::test_a_redirect_down_to_plain_http_is_refused`, `::test_a_suffix_entry_is_a_domain_not_a_substring` | D1, D2, D4 KILLED |
| 7 | #25/#29: one deadline bounds the whole fetch | `::test_the_deadline_bounds_the_whole_fetch` | D3 KILLED |
| 8 | D-159: a surface's own board is guarded (a quarter new or a quarter lost), and its floor is in the digest | `test_floor_served.py::test_a_board_flooded_with_rows_it_has_never_seen_is_refused`, `::test_a_board_that_loses_a_quarter_of_its_names_is_refused`, `::test_every_surfaces_floor_is_hashed_to_its_published_precision` | F3, F4, F7 KILLED |
| 9 | D-164: every declared board is guarded the same way | `test_refresh_boards.py::test_a_board_whose_names_are_a_quarter_new_is_refused`, `::test_a_board_that_loses_a_quarter_of_its_names_is_refused` | F5, F6 KILLED |
| 10 | #41/#47: the expiry baseline drops every carried table | `test_refresh_carry.py::test_the_expiry_baseline_drops_an_expired_attributes_values` | G1 KILLED |
| 11 | D-166: a moving alias derives no model | `test_moving_aliases.py::test_a_moving_alias_derives_no_model` | E1 KILLED |
| 12 | Accessibility is an allowlisted value, and disagreeing names get none | `test_access.py::test_rows_with_no_name_or_no_value_are_skipped_and_counted`, `::test_names_link_to_the_models_their_scores_link_to_and_a_disagreement_gives_no_value` | E2, E3 KILLED |
| 13 | An Epoch board refuses non-finite scores | `test_epoch_board.py::test_a_non_finite_score_is_skipped_and_counted` | E4 KILLED |
| 14 | D-157, as amended at M16: a derived display is bounded and carries no prose | `test_registry_derived.py::test_a_spelling_the_grammar_accepts_is_still_bounded_for_display` | E5 KILLED |
| 15 | D-167 clause 2: `/v1/boards` carries no score | `test_board_standings.py::test_the_payload_carries_no_score_at_all` | B2 KILLED |
| 16 | D-167: the standings egress bound refuses boot | `::test_an_artifact_that_would_publish_too_many_standings_refuses_to_boot` | B3 KILLED |
| 17 | INV-23 on `Carry.restore` | `test_carry_forward.py::test_the_carry_opens_the_served_artifact_read_only` | I7 KILLED |
| 18 | INV-23 on `_served_without` (a write that changes the live file) | `test_refresh_carry.py::test_a_secondary_sources_expiry_publishes_through_the_real_cycle` (+1) | I4w KILLED |
| 19 | **INV-23 on `/v1/boards`, `/v1/categories`, boot, `fingerprint_of`, `_served_without` and `survey --floors`** | **None** | I1, I1w, I2, I3, I6, I4, I8 **SURVIVED** (MINOR-1) |
| 20 | D-126: `task` is only a surface id | `test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine` | P1 KILLED |
| 21 | D-168 / W5 S1: only the wording tier sets alternatives, and the schema is closed | `::test_only_the_wording_tier_builds_an_outcome_with_alternatives`; `RefinementBoundaryTests.testTheModelsSchemaOffersExactlyTheDeclaredChoicesAndNothingElse` | P4 KILLED |
| 22 | **D-168 clause 9: refinements never leave the device (relay through `main`)** | **None** | P2 **SURVIVED** (MINOR-3) |
| 23 | **REQ-GAP-001: typed text is kept only in the register** | **None beyond spelling** | P3 **SURVIVED** (MINOR-3) |
| 24 | W5 S1 defence in depth: `select` takes only a listed surface | **None** | P5 SURVIVED (I-8) |
| 25 | #36: the service runs only a deployed release | `test_engine_service.py::test_the_service_runs_only_a_deployed_release` | L4 KILLED |
| 26 | **#36 / D-116: the service binds loopback; the preflight refuses; the wrapper is 700** | **Substring presence only** | L1, L2, L3 **SURVIVED** (MINOR-4) |
| 27 | D-154: the server never loads pyarrow | `test_arena_slices.py::test_neither_the_server_nor_the_slice_module_loads_pyarrow` | Measured, not mutated. W-125 grew (MINOR-5) |
| 28 | `/v1/boards` ignores its query string; the route set is exact | `test_board_standings.py::test_a_query_string_changes_nothing`, `test_api_v1.py::test_the_shipped_surface_is_exactly_the_declared_surface` | Not re-mutated. The W4 seat showed the route-set test red |
| 29 | No secret in M17's commits | gitleaks over the range and the combined diff | n/a (scan) |

**Score.** 41 mutants: 36 in Python and shell, and 5 in the phone. **28 were killed and 13
survived.** Every survivor is named in a finding: 7 are INV-23 (MINOR-1), 3 are the launcher
(MINOR-4), 2 are phone sinks (MINOR-3) and 1 is the `select` guard (I-8). The unmutated control
passed the text gate and `client-decls`, and the baseline `swift test` passed.

## 4. Security baseline and §E.1 walk (from `origin/main:docs/security-baseline.md`)

| Item | Status | Evidence |
|---|---|---|
| Secret scan green across all waves; no `.env` committed | **PASS** | §0. `git diff --name-only` has no `.env*` |
| Dependency hygiene | **PASS as far as it could be checked here** | The only new dependency is `pyarrow>=21.0`. The W2 seat ran pip-audit and slopsquat on it. They were not re-run here (§5) |
| No plaintext credentials or default admin | **PASS** | `bootstrap-check` C7 |
| Server-side authz on every mutating route | **N/A (vacuous)** | Routes are `GET /health`, `/v1/categories`, `/v1/budgets`, `/v1/boards` and `/v1/recommendations`. `/v1/boards` refuses POST, PUT and DELETE (405, W4) |
| CORS allowlist, never allow-all with credentials | **PASS** | `main.py:694-699`; C9 |
| Security config validated at startup; prod refuses | **PASS in code, weakly tested at the launcher** | The boot bound joins the validator (B3 killed). The service's preflight is substring-tested (MINOR-4) |
| Destructive defaults OFF | **PASS** | C10. The install prune is scoped to its own release directory (I-6) |
| Credentials or PII encrypted at rest | **N/A server-side** | The phone's new store holds public data in Caches. The typed text stays in the register as long as the invariant in MINOR-3 holds |
| Generic client errors | **PASS** | `/v1/boards` answers 503 `evidence_unavailable` or a generic 500 (W4 probes; unchanged) |
| Control-class fail direction | **PASS** | Safety controls fail closed: the reader's watchdog (A5), the hop allowlist, and the boot bounds. Source availability fails open per source (D-156). The cycle-level exception is MINOR-5 (W-126) |
| External-surface defaults | **PASS** | One new route, parameterless and read-only. The route set is exact |
| Prompt-injection hygiene | **PASS** | The on-device schema is closed and held as encoded (P4 killed). Fetched content is parsed as data, with no LLM in the engine path |
| SAST (MEDIUM or higher) | **Substitute ran** | `ruff --select S,BLE`, §0 |
| PII at log boundaries | **PASS** | No PII. Reader reasons are printable and bounded (A6 killed) |
| Built is not wired | **PASS** | Every M17 guard above is reached from its live entry: `refresh.main`, `_ingest_slices`, the routes and the launcher |
| Invariants list current, each with a NEGATIVE test | **FINDING** | MINOR-1, MINOR-3, MINOR-4 and MINOR-5. §3 is the reconstruction |
| Money | **N/A** | Prices are displayed; nothing is paid |
| Senior human review trigger (auth, PII, payment, migration) | **Not triggered** | None of those paths is in the diff. The new `access` table is additive and built, not migrated |

## 5. Skip ledger (checks that legitimately did not run)

| Check | Why it did not run | Consequence |
|---|---|---|
| `make deps` (pip-audit), `make slopsquat` | They need the network, which this seat was told not to use | `pyarrow` was checked by the W2 seat. The CI `dep-audit` job is a required check (`docs/branch-protection.md`), but I did not read its runs |
| 16 contract tests (`RUN_CONTRACT_TESTS`) and 7 `EPOCH_DATA_DIR` tests | Network and the owner's bundle | Upstream shape drift is not re-verified. The weekly contract workflow owns it |
| bandit, semgrep | Not installed. This seat installs nothing | Replaced by `ruff --select S,BLE` |
| `make gate` as one command | Its targets `pip install -e` into the venv | The legs were run one by one (§0) |
| The service under launchd | Out of bounds for this seat | The launcher's refusal was run by hand (I-5). Bind and preflight are judged by mutation (MINOR-4) |
| The simulator, the on-device model in probes | Out of bounds | The phone was judged by the three gates. The six existing on-device calls ran once in the full `swift test` |

## 6. What I did not check

- The iOS app on a simulator or a device, and how a hostile date or display actually renders.
- A real slow Hugging Face night. The 28-minute figure in MINOR-5 is arithmetic from the constants.
- Whether the owner's GitHub settings still match `docs/branch-protection.md` (I-2, I-3).
- Whether a hostile but well-formed upstream can move a ranking inside the D-128, D-132 and D-164
  limits. Upstreams are authoritative for their numbers by design.
- The Code-Reviewer and Tester verdicts beyond the security records in §2.
