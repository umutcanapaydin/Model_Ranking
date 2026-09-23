---
record_type: review
id: m16-closure-security-review
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---
# M16 Stage 4.0 Security Review: the engine refreshes itself, and upstream text now names models

> **Independent seat.** I wrote none of this code. Policy was read from the protected base ref only:
> `git show origin/main:subagent-profiles/Security-Reviewer.md`, `origin/main:docs/security-baseline.md`,
> `origin/main:permission-matrix.md`, `origin/main:AGENTS.md`, and `origin/main:docs/closure-checklist.md`
> §B.2a. The surface is `git diff 059b519 eee2faf` (71 commits, 62 non-merge; 197 files,
> +17726/-3465). `origin/main` = `eee2faf`. The owner's untracked `epb.html` and `or.md` were not
> read. The only repository file this seat creates is this one.

## Verdict

**PASS WITH FINDINGS.** Nothing is BLOCKING. There is **1 MAJOR, 6 MINOR and 8 INFO**.

The three controls this milestone is built around hold under measurement:

- **The nightly child cannot run in production.** With `MODEL_RANKING_REFRESH=nightly` the process
  refuses to import (`ConfigError`) for `APP_ENV` = `production`, `prod`, `staging`, unset and
  `Test;prod`, and boots only for `test`. The lifespan re-checks it (M02 killed). A strict
  environment's `/health` carries only `"refresh": "off"` (M28 killed).
- **The untrusted archive is contained.** Every hostile archive the W4 pass used, plus traversal,
  absolute, drive, backslash, symlink, not-a-zip and file-then-dir, comes out of `unpack` as
  `SourceError`. Nothing is written outside the scratch directory. The cycle carries rather than
  crashes (M14, M25 killed).
- **The served artifact is never written.** INV-23 holds on every M16 reader. `_served_without`
  deleting from the served file (M17b) is killed by four tests.

The D-126 privacy invariant is now enforced by a compiler-bound gate. All five egress mutants I
placed in M16-touched iOS code were killed by `client_decl_gate.py` (§2b). M15's MAJOR-1 is
therefore closed by measurement, not just by citation.

**The MAJOR is new with D-157.** A model's served name is now taken verbatim from upstream data.
I pushed a hostile Epoch board row through the real `refresh()` and the real `build.main`, and
`/v1/recommendations?task=expert` served the following as a model name:

> `Visit evil.example for the real ranking, Opus is deprecated /zeta 9`

Before M16, every served name was curated. It is not BLOCKING, for four reasons:

- nothing is deployed (the engine binds `127.0.0.1`, D-116);
- the iOS client renders it as verbatim text (no markdown, no links);
- no data leaves the device;
- the same upstream already controls the scores.

It should be fixed before any build reaches a reader other than the owner.

## 0. Surface and method

**Waves.**
- W1: contracts and the `client-decls` gate (D-150).
- W2: the nightly child process (`src/app/adapter/nightly.py`; D-151, D-154).
- W3: carry-forward per source (`build.Carry`, `refresh._served_without`; D-156) and the D-148
  floors.
- W4: the Epoch bundle fetch and unpack (`src/app/clients/epoch_bundle.py`, D-158), layout drift,
  the derived registry (`registry.derive_identity`, D-157) and the new `/health` fields.
- `make check-fast` (`scripts/check_fast.py`, `scripts/swift_xunit_gate.py`).
- The DevFlow v6.0 adoption (D-155): workflows, hooks, skills, `conformance/`.

**Method.** All experiments ran in the scratchpad.
- **Two private exports** of `eee2faf` were made with `git archive`, never a worktree. One was used
  for mutation and one kept pristine. Both were compared byte for byte afterwards (identical).
- **Owner's data.** The owner's `advisor.db` was used only as a copy. Its md5 was
  `214139e91c691e0273c21673e71d2ba4` before and after.
- **Git state.** No git state was changed.
- **Mutants.** Every mutant was applied by a script. The script records the file's md5, runs the
  **full** Python suite, restores the file and asserts the md5 matches.

**Gates I ran myself on the export:**

| Gate | Result |
|---|---|
| `pytest -n auto` (full suite) | **1165 passed, 15 skipped** |
| `swift test` (external `--scratch-path`) | **268 tests, 0 failures**. The manifest has 268 lines |
| `scripts/client_decl_gate.py` | `client-decls PASS: 11 client file(s) in 4 configuration(s)` |
| `gitleaks detect --log-opts=059b519..eee2faf` | 62 commits, **no leaks** |
| `git diff 059b519 eee2faf \| gitleaks stdin`, repo config and a config-free default ruleset (covers merge commits) | **no leaks** (both) |
| `pip_audit` | **No known vulnerabilities** (the project itself is unauditable, as expected) |
| `scripts/slopsquat_check.py` | `PASS: 17 declared dependency(ies), 0 suspect` |
| `ruff check --select S,BLE src` (SAST substitute, see skip ledger) | 5 hits: one `S101` (an `assert` in a closure, `nightly.py:267`) and four `BLE001`, all deliberate catch-alls with a written reason (`nightly.py:339,348`, `refresh.py:886,1141`). `ruff check src tests scripts`: clean |
| `bash scripts/bootstrap-check.sh` | C7 / C9 / C10 pass; `RESULT: PASS` |

## 1. Findings

### BLOCKING

None.

### MAJOR

**MAJOR-1: D-157 serves an upstream string as a model's name, with no bound on its length, its
characters or anything outside the id grammar.**
Where:
- `src/app/workflows/registry.py:455` (`_derived_display`);
- `registry.py:553-554` (the `models.display` insert);
- `registry.py:424` (the grammar keeps only the text after the last `/`, while the display keeps
  all of it);
- `src/app/workflows/rank.py:328` (`model=r[1]`, the served `model` field).

- **What changed.** Up to M15, `models.display` came only from `MODEL_RULES`, which are curated
  constants. D-157 registers a model for any name whose derived id has both a price and a score.
  Its display is then chosen from the score rows' raw names: the first name containing a space,
  else the shortest.
  - The derived id is well constrained (`[a-z0-9][a-z0-9.+\-]*`).
  - The display is not. The grammar discards everything before the last `/`, so any free text in
    front of a `/` still derives to a legitimate id and is kept whole in the display.
- **Reproduced end to end.** I used the real `refresh()` and real `build.main`, with fake
  upstreams built from the suite's own helpers, and a tmp artifact.
  - **Cycle 1.** The prices contained one uncurated alias, `newco/zeta-9`, priced at the surface
    median. The Epoch GPQA board held three curated models.
  - **Cycle 2.** A bundle with one extra row was fetched through `fetch_epoch`:
    `"Visit evil.example for the real ranking, Opus is deprecated /zeta 9",0.99`.
  - **Result.** The cycle published (exit 0). `models` held
    `('zeta9', 'Visit evil.example for the real ranking, Opus is deprecated /zeta 9', 'Other')`.
    A `TestClient` run over every surface found it served on `expert`.
  - **What the guards do.** The W-049 new-names guard allowed it (1 new name of 4 = 25%, not over
    25%). The price guard refuses only when the median moves, which a median-priced alias does not
    do.
- **Unit probes.**
  - A 5,013-character name was stored whole as the display.
  - A name containing `\x1c` became the display with the control character intact (Python's `\s`
    matches it, so the id still derives).
  - Names with U+2028 were derived.
  - A name starting with U+202E was not derived, so bidi override at the start fails the grammar.
  - Vendor attribution comes from a fixed map on the id, so a `gpt…` id is labelled `OpenAI`
    whatever the display says.
- **Who can do it.** Anyone who controls one board row: epoch.ai or its CDN, Arena, or any score
  source. The alias does not have to be theirs. Price feeds carry hundreds of uncurated aliases,
  so they only need to pick a priced, uncurated one.
- **Why MAJOR and not BLOCKING.**
  - SwiftUI `Text(String)` does not parse markdown, and a grep of `ios/ModelRanking` finds no
    `LocalizedStringKey`, `AttributedString(markdown:)`, `Link(` or `openURL`. So this is text
    injection, not code execution or egress.
  - Nothing is deployed.
  - Upstreams could already move scores.
  - What is new is that they can make the app *say* things, in the one field the reader reads
    first, and D-157 did not treat that as a new trust extension.
- **Remedy.**
  1. Build the derived display from the grammar's own output, never from the raw name. For
     example, take the text after the last `/` and after any removed heads. Then accept it only
     if it fully matches `[A-Za-z0-9][A-Za-z0-9 .+\-()]{0,63}`, and otherwise fall back to the
     derived id.
  2. Add two negative tests through `reconcile` (and one through `refresh` → `/v1`):
     - a display with prose before a `/` is never served;
     - a control or format character (`unicodedata.category` in `Cc`/`Cf`/`Zl`/`Zp`), or a name
       over 64 characters, is never served.

### MINOR

**MINOR-1: `/health` repeats up to five upstream names verbatim with no length bound. I measured
a 5 MB response from one record.** Where: `src/app/adapter/nightly.py:172-173` (`_first`) and
`:381`; `src/app/workflows/build.py:320-329` (`_most_unmatched`, 20 names, each unbounded).

- **What is bounded.** The count is capped at 5, and M26 (dropping the cap) is killed.
- **What is not.** The length and the characters of each name are unbounded. I wrote a record whose
  `unmatched` holds 20 names of 1 MB each, starting `‮\x1b[31m`, and `report()` returned
  5,000,363 bytes of JSON containing the raw control characters (JSON-escaped).
- **Other costs.** Each `/health` call also re-reads and parses the whole `.refresh.json`.
- **Real limits.** Epoch names are capped at 131,072 characters by `csv`'s default field limit.
  Arena and OpenRouter names are capped only by the 32 MiB response limit.
- **Exposure today.** Development only: the fields exist only while the schedule runs, which
  strict environments refuse, and `ios/app.sh` binds `127.0.0.1`. That is why this is MINOR.
- **The rule it breaks.** The baseline's "diagnosable fail-closed, without an attacker oracle"
  rule says operator detail belongs on an authenticated diagnostic, not the unauthenticated
  `/health`.
- **Remedy.**
  - Truncate each name (for example to 80 characters) and replace `Cc`/`Cf` characters in
    `_most_unmatched` or in `_first`.
  - Add a test that sends a 1 MB name and asserts a bounded field.
  - When the engine is ever deployed, move `refresh_unmatched`, `refresh_drift` and
    `refresh_next` behind the authenticated diagnostic, as the W2 pass's NIT-3 already said.

**MINOR-2: INV-23's gate does not catch a plain `sqlite3.connect(<served artifact>)`, and one M16
reader can be made writable with every test still green.**
Where: `src/app/workflows/build.py:266` (`Carry.restore`); the gate is
`tests/unit/test_readonly_uri.py:75`.

- **Measured.** Mutant M16 replaced `open_readonly(self.live)` with `sqlite3.connect(self.live)`,
  and all 1165 tests passed. The gate refuses only hand-built `file:` f-strings, which is the shape
  of the M10 defect. A read-write handle on the file the engine is serving, opened the ordinary
  way, is invisible to it.
- **Where it matters.** `_served_without`, the other M16 reader, is protected *behaviourally*:
  M17b is killed by four tests. The ordinary-way shape is still the one a future refactor is most
  likely to write.
- **Remedy.** Extend the AST gate to refuse any `sqlite3.connect(` in `src/` and `scripts/` whose
  argument is not `":memory:"`. Keep a by-name allowlist with one reason per entry:
  - `schema.connect`;
  - the build workspace;
  - the survey and calibrate scratch copies.

  Then show the gate red on M16.

**MINOR-3: the timeout kill does not bound the wait when a descendant holds the child's output
pipe.** Where: `src/app/adapter/nightly.py:260-263` (no new session or process group) and
`:295-300` (`proc.kill()`, then `await asyncio.shield(proc.wait())`).

- **Measured.** The stand-in child started a grandchild that slept 30 s and inherited stdout.
  With `timeout=2.0`, the child was killed at 2 s but `run_once` returned only at **30.1 s**. Its
  wait lasts until the pipe closes, and only the grandchild's exit closes it.
- **Effect.** A grandchild that never exits stalls the schedule for good: `/health` says
  `running` forever, and every later night is skipped. The server keeps answering, because this
  is an await and not a block.
- **Why MINOR.** It is not reachable today. The refresh runs the build in-process and starts no
  subprocess (grep: no `subprocess` or `os.system` in `src/` other than `nightly.py`).
- **Relation to W-126.** W-126 (a SIGKILLed engine leaves a stuck child holding the lock) is the
  same family.
- **Remedy.**
  - Start the child with `start_new_session=True`, and on timeout or cancel `os.killpg` the group.
  - Bound the shielded wait with `wait_for`, for example 10 s.
  - Add a test with a pipe-holding grandchild.

**MINOR-4: D-158 is built but not wired on the refresher the owner will be left with; the W4
review's MAJOR-1 recurs on the engine path.** Where: `ios/app.sh:20` and `:89` (the default
`MODEL_RANKING_EPOCH_DIR=<the owner's hand-kept bundle directory>`) and
`src/app/adapter/nightly.py:209` (an owner directory wins over `--fetch-epoch`).

- **The inconsistency.**
  - The W4 fix changed `scripts/refresh_job.sh`, the launchd wrapper, to `--fetch-epoch`.
  - `app.sh` still hands the engine the directory the review called stale, and
    `test_the_environment_builds_the_refreshs_own_command` pins that precedence.
  - `scripts/retire_refresh.sh` retires launchd, which is the one job that fetches.
- **Effect.** From then on, no refresher fetches, and the untrusted-archive guards (§2) are never
  reached in the owner's configuration.
- **Why it is filed here.** The security effect is *less* exposure. It is filed under built-not-
  wired, and handed back as a correctness defect: the engine reads a bundle that D-158 exists to
  replace.
- **Remedy.** Drop the default from `app.sh`, so the variable is set only when the owner exports
  `MR_EPOCH_DIR`. Add a test that `app.sh`'s engine command contains no `MODEL_RANKING_EPOCH_DIR`
  unless one is given.

**MINOR-5: there is no single, current security-invariants list.** Checklist §B.2a requires one.

- Invariants live in per-wave close records (row 7), in earlier milestones' review tables, and in
  test docstrings. `INV-23` is cited by number in 20 files, and no file defines the set.
- A reviewer therefore has to rebuild the list each milestone, and an invariant nobody lists is
  not re-tested.
- §3 below is this seat's reconstruction for M16.
- **Remedy.** Commit it as one governed file, for example `docs/security-invariants.md`: each row
  holds the invariant, its producers, its negative test and the mutant that proves the test.
  Have closure cite it.

**MINOR-6: two warnings owned by "the M16 closure" are still open.**
- **W-125.** The serving process still loads `app.workflows.ingest`, every `app.clients.*` parser
  and `httpx`; I measured this in a fresh interpreter. `epoch_bundle` is *not* loaded.
- **W-126.** There is no wall-clock limit inside the child.

Neither is exploitable today, and both are documented honestly (`docs/warnings.ledger.md` rows
W-125 and W-126). The closure must either fix them or give each a new owning milestone. A ledger
row that names a milestone which has closed is an open loop.

### INFO (verified; no action unless stated)

- **I-1: No policy-alteration attempt, and no weakening.** The milestone did edit
  `permission-matrix.md`, `docs/security-baseline.md`, `subagent-profiles/Security-Reviewer.md` and
  `AGENTS.md`, under D-155 (the DevFlow three-way merge, owner-accepted, which is the ADR the
  matrix requires).
  - Every removed line has an equivalent added line, apart from version and client tags.
  - One DENY row was *tightened*: `git checkout --`, `git checkout .` and `git restore` are now
    denied and hook-enforced. I exercised the hook: all three are blocked, `git restore --staged`
    is allowed, and `git push origin main` is blocked.
  - `.claude/settings.json` gained only those blocks.
  - A regex scan of the added lines for reviewer-directed instructions found none.
  - Cosmetic damage from the provenance strip: `"**Rule:every mutating route"`,
    `">: 9 original categories"`, and "via the the Security-Reviewer profile (…) skill". The
    profile's output path (`docs/reviews/m{N}-security.md`) differs from the name this record and
    M15's use. Both are worth one tidy-up.
- **I-2: The M16 iOS diff adds no egress.** It covers `Detail.swift`, `ContentView.swift`,
  `Models.swift` and `Router.swift` examples. `priceExcludes` is an allowlisted code: only
  `search_call` maps to words, and anything else renders nothing. `min_quality` and
  `price_excludes` on `/v1/categories` are `CategorySpec` constants, not data.
- **I-3: CI (D-155).**
  - Every `uses:` is SHA-pinned, and M16 added none.
  - The new steps are `run:` steps with no `${{ }}` in their bodies.
  - `ci.yml` stays `permissions: contents: read`.
  - The governance job installs `PyYAML>=6.0` as a floating range. That is low risk (read-only
    token), but a pin would match the rest.
  - `issue-agent.yml` repeats `pull-requests: write` twice, which predates M16, and M16 changed
    only its prompt's skill name.
  - `pip-audit --strict .` now audits the declared dependencies, which is the right question.
- **I-4: Dependencies.** No new third-party dependency. `PyYAML>=6.0` added to `dev` duplicates
  the runtime `pyyaml>=6.0`. Every other new import in `src/`, `scripts/` and `conformance/` is
  stdlib or in-repo.
- **I-5: Two mutants survived because a second layer catches the same input.**
  - M07 removed the `..` name check. The resolved-path check still refuses the member, and M09b
    (removing that check) is killed.
  - M15 narrowed `unpack`'s outer catch to `ValueError`. Every test case raising at `ZipFile()` is
    a `ValueError` subclass (for example `UnicodeDecodeError`), and `_fetched_epoch` catches any
    `Exception` anyway (M14 killed).

  The invariants hold. Each first layer simply has no test of its own.
- **I-6: My first INV-23 mutant hung the suite rather than failing it.** M17 backed the served
  file up into itself (over 240 s). The suite has no per-test timeout, so CI's 15-minute job
  limit is what would catch that shape.
- **I-7: The engine log receives upstream text.** The child's last 20 lines, which can include
  upstream exception text, go to `ios/.build/engine.log` without stripping control characters.
  Terminal escapes are possible when the owner runs `tail` on it. This is local and low risk.
- **I-8: Stale sentence in D-158.** Its "revisit when the bundle outgrows its 64 MB limit"
  predates the security pass, which cut the limit to 16 MiB (`epoch_bundle.py:35`). The working
  tree also carries another session's uncommitted closure edits, including `AGENTS.md`. They are
  outside this review, which certifies `eee2faf` only; any policy change among them needs its own
  base-pinned read.

## 2. Per-wave security records: do their fixes still hold on `main`?

### 2a. `docs/reviews/m16-wave-2-security.md`

| Finding | Status on `eee2faf` | Evidence (measured) |
|---|---|---|
| MAJOR-1 (the "server never loads fetch code" claim) | **Fixed as a claim, remainder open as W-125** | The test now imports the server in a subprocess and reads `sys.modules`; M27 (`import app.workflows.refresh` in `main.py`) is killed by it. The parsers and `httpx` are still loaded (MINOR-6) |
| MINOR-1 (the child's output buffered whole) | **Holds** | `read_tail` keeps a 64 KiB tail; M04 is killed by `test_the_tail_never_holds_more_than_its_limit` |
| MINOR-2 (the lifespan does not re-check) | **Holds** | `from_environment` re-reads `APP_ENV`; M02 is killed |
| MINOR-3 (`retire_refresh.sh` trusts :8080) | **Partly** | It checks that the listener's command line is `app.adapter.main:app`, which a look-alike process passes, as D-154's amendment records |
| MINOR-4 (the child inherits the whole environment) | **Holds** | `CHILD_ENV` is an allowlist; M03 is killed by `test_the_child_inherits_no_secret_from_the_server` |
| NIT-1 (a module shadowed from the working directory) | **Holds** | `-P` is used; M06 is killed |
| NIT-2 (N workers run N schedules) | Open, and harmless | Undocumented; the `flock` serialises them and `app.sh` runs one worker |
| NIT-4 (empty `HOME`) | **Holds** | The script now refuses an empty `HOME` |

### 2b. `docs/reviews/m16-wave-4-security-p1.md`

| Finding | Status on `eee2faf` | Evidence (measured) |
|---|---|---|
| F1 BLOCKING (a hostile archive crashes the whole cycle) | **Holds** | The UTF-8-flag name, the corrupt LZMA and the corrupt Zstandard archives all give `SourceError`. `_fetched_epoch` catches any `Exception`, and M14 is killed by three tests |
| F2 (scratch leaks) | **Holds** | `BaseException` cleans up and re-raises (M25 killed). The sweep covers `*.epoch` (M19 killed). `git check-ignore` matches `*.epoch/`, `*.sources` and `*.last-ok` |
| F3 (a 64 MB central directory) | **Holds** | `MAX_BUNDLE_BYTES = 16 MiB` |
| F4 (no total deadline) | **Holds** | `deadline=120`; M13 is killed |
| F5 (redirects followed) | **Holds** | `follow_redirects=False`; M12 is killed |
| F6 (error normalisation) | **Holds** | Budget refusal: "the bundle expands past…"; file-then-dir: `SourceError` |
| "Not checked: drift lines in the record" | Checked here | `_drifted` exposes only the source-name prefix, and every drift line is built as `f"{source}: {exc}"`. The *unmatched* names, added after that pass, are MINOR-1 |

**D-126 on the M16 iOS surface** (M15 MAJOR-1's remedy, now `client_decl_gate.py`). Five
mutants were run against the compiler-resolved gate and all five were killed:
- P1: `URLSession` with the typed text in `ContentView`;
- P2: `Data(contentsOf:)` of a remote URL inside M16's new `priceExclusion`;
- P3: M15's `//`-in-a-string bypass (M06);
- P4: `UserDefaults.set(typed…)`;
- P5: `UIPasteboard`.

The gate named the resolved declaration each time.

## 3. M16 security invariants and their negative tests

Every row was verified by removing the invariant in a scratch copy and running the full suite
(`KILLED` means at least one test failed), except where the row says otherwise.

| # | Invariant (producer) | Negative test that fails when it is removed | Mutant |
|---|---|---|---|
| 1 | The nightly switch is refused outside relaxed environments (`nightly.switch_problem`, D-154 cl.2) | `test_nightly_refresh.py::test_production_refuses_to_boot_with_the_switch_on` (+3) | M01 KILLED |
| 2 | The switch is re-checked when the schedule starts (`from_environment`) | `::test_the_schedule_rechecks_the_switch_when_it_starts` | M02 KILLED |
| 3 | The child gets an allowlisted environment (`CHILD_ENV`) | `::test_the_child_inherits_no_secret_from_the_server` | M03 KILLED |
| 4 | The child's output is held as a bounded tail (`read_tail`) | `::test_the_tail_never_holds_more_than_its_limit` | M04 KILLED |
| 5 | A child past its timeout is killed (`run_once` finally) | `::test_a_cycle_that_hangs_is_killed_at_the_timeout`, `::test_the_server_answers_while_a_cycle_hangs` | M05 KILLED (see MINOR-3 for descendants) |
| 6 | The child's module path excludes the working directory (`-P`) | `::test_the_environment_builds_the_refreshs_own_command` | M06 KILLED |
| 7 | The server never loads refresh, build, sources, epoch or rosters | `::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers` | M27 KILLED |
| 8 | A strict environment's `/health` reports only `refresh: off` | `::test_health_says_off_when_the_switch_is_off` | M28 KILLED |
| 9 | No archive member lands outside the scratch directory (`_safe_relative`, `_plan`) | `test_epoch_bundle_fetch.py::test_a_member_whose_resolved_path_escapes_is_refused_even_when_its_name_is_clean` | M09b KILLED; M07 survived, shadowed (I-5) |
| 10 | Symlink members are refused | `::test_a_symlink_member_is_refused` | M08 KILLED |
| 11 | Expansion is counted while writing (256 MiB) | `::test_a_bundle_that_expands_past_the_limit_is_refused_by_what_it_writes` | M10 KILLED |
| 12 | Member count is capped | `::test_too_many_members_are_refused` | M11 KILLED |
| 13 | The download follows no redirect and has a total deadline | `::test_the_bundle_download_is_bounded_small_follows_no_redirect_and_has_a_deadline` | M12, M13 KILLED |
| 14 | Any fetch or unpack failure is a failed source, never a crashed cycle (D-158 cl.3) | `::test_any_error_a_fetcher_raises_is_a_failed_source`, `::test_an_unreadable_archive_never_stops_the_cycle` | M14 KILLED; M15 survived, shadowed (I-5) |
| 15 | An interrupt leaves no scratch | `::test_an_interrupt_during_the_fetch_propagates_and_leaves_no_scratch` | M25 KILLED |
| 16 | The sweep never removes a live sibling's scratch | `::test_scratch_a_killed_cycle_left_is_swept_by_the_next` | M19 KILLED |
| 17 | INV-23: every read of the served artifact is read-only | `test_readonly_uri.py` (construction); `test_refresh_carry.py::test_an_expiry_does_not_excuse_the_fresh_source_beside_it` (+3, for `_served_without`) | M18 KILLED, M17b KILLED, **M16 SURVIVED (MINOR-2)** |
| 18 | D-128: a worse candidate is refused | `test_refresh*.py::test_a_candidate_that_blinds_a_surface_is_refused` (+3) | M20 KILLED |
| 19 | W-049: implausible gains are refused, including on an expiry night | `::test_a_surface_filling_with_models_nobody_has_seen_is_refused`, `::test_an_expiry_night_does_not_admit_a_roster_never_served` | M21 KILLED |
| 20 | D-157: the curated list wins; the modality guard; fine-tunes never derived | `test_registry_derived.py::test_a_curated_id_is_never_taken_by_a_derived_one`, `::test_a_different_product_is_never_derived`, `::test_a_fine_tune_is_never_derived` | M22, M23, M24 KILLED |
| 21 | D-157: a derived display is bounded and carries no upstream prose | **None exists** | **MAJOR-1** |
| 22 | `/health` names at most 5 unmatched names | `test_registry_disclosure.py::test_health_counts_the_derived_models_and_names_the_top_unmatched` | M26 KILLED (count only; length is MINOR-1) |
| 23 | D-126: typed text never leaves the device | `scripts/client_decl_gate.py` (`make client-decls`) | P1–P5 KILLED |
| 24 | Destructive git and `rm` commands are blocked for agents (§5) | The hook itself, exercised with 9 commands (I-1) | Not mutated; behaviour measured |
| 25 | No secret in the milestone's commits | gitleaks over the range and over the combined diff | n/a (scan) |

**Score.** 30 code mutants were run. 26 were killed. 2 survived only because a second layer
catches the same input (M07, M15), 1 survived outright (M16, MINOR-2), and 1 hung the suite (M17,
re-run as M17b and killed). Privacy: 5 of 5 killed. One invariant has no test at all (row 21,
MAJOR-1).

## 4. Security baseline and §B.2a walk (from `origin/main:docs/security-baseline.md`)

| Item | Status | Evidence |
|---|---|---|
| Secret scan green across all waves; no `.env` committed | **PASS** | §0. `git diff --name-only` has no `.env*` |
| Dependency hygiene (PyPI, age, pip-audit) | **PASS** | §0, I-4 |
| No plaintext credentials or default admin | **PASS** | `bootstrap-check` C7; no credential store exists |
| Server-side authz on every mutating route | **N/A (vacuous)** | Routes: `GET /health`, `/v1/categories`, `/v1/budgets`, `/v1/recommendations`. No POST, PUT, PATCH or DELETE (`main.py:1159,1245,1306,1343`) |
| CORS allowlist, never allow-all with credentials | **PASS** | `allow_credentials=False`, `allow_methods=["GET"]` (`main.py:647-648`). `cors_origins()` refuses a wildcard; C9 passes |
| Security config validated at startup; prod refuses | **PASS** | §0 boot matrix. The nightly switch joins the fail-closed validator (`main.py:559-563`) |
| Destructive defaults OFF | **PASS** | The switch is off unless it says `nightly`; the sweep touches only this artifact's day-old scratch; C10 passes |
| Credentials or PII encrypted at rest | **N/A** | The server stores no credentials or PII. The client's gap register is unchanged in M16 |
| Generic client errors | **PASS** | `/v1` errors are unchanged. The absolute scratch paths in `SourceError` text reach only the server log and the build report, never a response. `/health` detail: MINOR-1 |
| Control-class fail direction | **PASS** | Safety controls fail closed: the switch in strict or unknown environments, and a bundle refused whole. Source availability fails open per source: a failed fetch carries (D-156/D-158). Both directions are tested (rows 1, 14) |
| External-surface defaults | **PASS WITH FINDING** | `/health` gains fields only in development (row 8). Their content: MINOR-1 |
| Prompt-injection hygiene | **PASS** | Fetched content is parsed as data (`csv`, `zipfile`, `json`), with no `eval` and no LLM in the path (D-104). The CI issue agent's prompt changed only a skill name |
| SAST (MEDIUM or higher) | **Substitute ran** | bandit and semgrep are absent; `ruff --select S,BLE` was run instead (§0) |
| PII at log boundaries | **PASS** | No PII is handled. The log carries the command line (interpreter, db path, epoch dir) and the child's tail (I-7) |
| Built is not wired | **FINDING** | D-158 on the engine path: MINOR-4. Every other M16 guard is reachable from its live entry (`refresh.main --fetch-epoch`, the lifespan, `/health`) and is tested there |
| Money | **N/A** | The project displays prices; it handles no payments |
| Invariants list current | **FINDING** | MINOR-5; §3 is the reconstruction |
| Senior human review trigger (auth, PII, payment, migration) | **Not triggered** | None of those paths is in the diff |

## 5. Skip ledger (checks that legitimately did not run)

| Check | Why it did not run | Consequence |
|---|---|---|
| 8 network contract tests (`test_arena_openrouter_contract` ×5, `test_litellm_contract` ×1, `test_scores_contract` ×2) | They need network access and `RUN_CONTRACT_TESTS=1`. This seat's default suite stays offline (permission-matrix §3) | Upstream shape drift is not re-verified here. The weekly `contract-tests.yml` owns it |
| 7 `EPOCH_DATA_DIR`-gated tests (`test_effort`, `test_epoch_ingest`, `test_m5_board_measurement` ×3, `test_epoch_workflow`, `test_deepswe_workflow`) | They need an unpacked real Epoch bundle outside the repository, and this seat does not read outside the repository | The real bundle's parse is covered by the W4 security seat's one real fetch (87 files, no refusals), not re-run |
| A real fetch of `https://epoch.ai/data/benchmark_data.zip` | Outbound network is ASK under permission-matrix §3, and the W4 seat already did it once | Transport behaviour (TLS, no redirect) is taken from that record plus M12 and M13 |
| bandit, semgrep | Not installed. This seat installs nothing | Replaced by `ruff --select S,BLE` |
| `client-decls` and `swift-test` in CI | Linux has no Xcode; `ci.yml` says SKIPPED NO-ENVIRONMENT loudly | Both ran locally here (§0, §2b). They stay owner-machine legs (W-111) |
| `make falsify` | An installation, not the distribution package: it prints SKIPPED by design | None for this project |
| `make gate` as one command | Its legs were run individually on the export. The `make` targets would `pip install -e` into the owner's venv | Same coverage, without mutating the venv |
| §B.3 deploy and go-live | Nothing deploys: the engine runs on the owner's Mac on `127.0.0.1` (D-116, D-123) | Must run in full at the first real deploy, after MAJOR-1 |
| Encryption at rest, auth, money | No credential store, no auth surface, no payments | Vacuous this milestone |

## 6. What I did not check

- **The Xcode app target in a simulator.** The iOS mutants were judged by `client_decl_gate.py`,
  which type-checks against the iOS SDK in four configurations. I did not launch the app or
  capture traffic.
- **How a hostile display actually looks on screen** (MAJOR-1). The `.lineLimit` on the model-name
  rows, which bounds the visual damage, was not measured.
- **The owner's working tree.** Another closure session's uncommitted files there are out of scope
  (I-8).
- **`ios/app.sh up`, the real `retire_refresh.sh`, launchd, and a real uvicorn with the schedule
  on.** The child and kill paths were driven through `NightlyRefresh.run_once` with stand-in
  children.
- **Windows path semantics for the unpack.** It ran on macOS APFS (case-insensitive) only.
- **Whether a hostile but well-formed bundle can move a ranking within D-128's and W-049's
  limits.** Upstreams are authoritative for their numbers by design.
- **The Code-Reviewer and Tester verdicts, beyond the security records named in §2.**
