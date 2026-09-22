---
record_type: review
id: m16-wave-2-rereview
status: ratified
seat: independent
date: 2026-09-23
---
# M16-W2 — independent re-review of the fix round: the nightly refresh, the floor line and the price notes

**Seat:** independent (Code-Reviewer + Tester + Security; I wrote none of this code). **Base:** acef579, with
everything uncommitted. **Subject:** the fixes made after `docs/reviews/m16-wave-2-review.md` (0/2/5/2)
and `docs/reviews/m16-wave-2-security.md` (0/1/4/4), plus the new code those fixes added.

**Snapshot I tested** (md5): `src/app/adapter/nightly.py` `24ef756a...`, `src/app/adapter/main.py`
`6ce66612...`, `tests/unit/test_nightly_refresh.py` `5c68a70b...`, `tests/unit/test_ios_client_contract.py`
`d6935f15...`, `ios/ModelRanking/ContentView.swift` `dad79be3...`, `scripts/retire_refresh.sh`
`a4c731b5...`. These were unchanged from my first run to my last.

**Hygiene.** Every mutant was applied to a copy of the repository in the session scratch directory,
then restored, and each restore was md5-checked. The real cycle ran on a copy of `advisor.db` and
`advisor.db.refresh.json`. The repository's own copies kept the same md5 before and after
(`ef9e48a9...` / `7e0355ed...`). I started nothing on :8080 and made no launchd call. `make install` was
not run: I ran `make -o install -o .venv/bin/python check`, which skips the install. Every process
I started was stopped, and `pgrep` found none left over. `git status` was the same before and after,
apart from this file.

## Verdict

**PASS WITH FINDINGS — 0 BLOCKING, 0 MAJOR, 3 MINOR, 9 NIT.**

Of the 18 findings from the first round, all 3 MAJORs are resolved: 2 are CLOSED in code and 1 is
OPEN-RECORDED (W-125). I re-ran each failure scenario and each surviving mutant, and they are RED or
behave correctly now. A real cycle through `NightlyRefresh.run_once` **published in 8.3 s**. It ran
under the allowlisted environment, from `cwd=/`, with `-P`. The counts above cover what is still
open: two items carried from the first round, now MINOR, and the new findings below. The most
important new finding is that the new 12-hour "already ran tonight" rule also skips the night after
any daytime refresh. That lets the data reach about 36 hours old, and D-151 states a cost of "up to a
day".

**`make check` (install skipped): every gate is green except `wave-check-all`.** Results: ruff clean;
mypy clean on 34 files; pytest **1013 passed, 15 skipped**; coverage-floor PASS; check-records PASS;
check-records-selftest PASS; install-check PASS; conformance-gate PASS; swift-test **PASS, 268 tests**;
client-decls PASS in 4 configurations. `wave-check-all` FAILS on only one record,
`docs/plans/m16-wave-2-close.md` (created 01:16, while this review ran): "2 of 12 row(s) carry no
evidence". One of those rows is the `REVIEW_VERDICT` placeholder that this record fills. The failure
belongs to the close record and is not a code defect. Once row 3 carries evidence and the other bare
row is fixed, the gate should pass. I also built the iOS app from the copy with
`xcodebuild ... -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO`, and the result
was **BUILD SUCCEEDED**. That build compiles `ContentView.swift`, including the new preview note.

## Disposition of every earlier finding

| Source | Finding | Status | Evidence I ran |
|---|---|---|---|
| review MAJOR-1 | A killed cycle is shown as the previous "published" | **CLOSED** | Scenario (`scen.py killed`): the record said `published` an hour earlier, and a child printed a line and then hung, with a 3 s timeout. Result: `run_once -> None`; `report()` -> `refresh_last: "killed"` with the kill's own time; the log got the line `nightly refresh \| stuck in build step X` before the kill line. Mutants M26 and M28 are RED. The timeout-path tail is not pinned (M27 survived, NIT-1 below). |
| review MAJOR-2 | The home preview had no price note, and the card and list notes were unpinned | **CLOSED in code. The evidence part is STILL OPEN (MINOR-2)** | M18, M19 and the new M24 (the preview drops its note) are all RED through `tests/unit/test_ios_client_contract.py::test_every_place_that_prints_a_search_price_says_what_it_leaves_out`. A grep for `priceTag\|priceInPages\|figuresLine\|RankedRow(` finds no fourth place that prints a price. The Xcode build succeeds. However, the REQ-PRC-002 row in `docs/prd.md:534` still cites only `DetailTests`, and it names three places, not four (see MINOR-2). |
| review MINOR-1 | A Mac asleep through the window ran at 08:01 | **CLOSED** | `_due` now runs after the window only on data at least a day old, and the D-154 amendment states that rule. M33 (always run late) and M46 (the window taken from `now()`) are RED. M34 (`>=` changed to `>` at the exact close) survives (NIT-1). |
| review MINOR-2 | "Once a night" was counted per process | **CLOSED for the scenarios reported; the fix overreaches (new MINOR-1)** | M35 (`recently_good` always False) is RED. In `due.py`, a start at 23:10 with stale data gives one catch-up and no second run. |
| review MINOR-3 | A hard kill of the engine orphans a stuck child | **OPEN-RECORDED** | W-126 (`docs/warnings.ledger.md`), owned by the M16 closure. Not re-run. |
| review MINOR-4 | A crash before `refresh.main` was logged as "unchanged" | **CLOSED** | Scenario: `import no_such_module` logs `exit 1 (crashed)`. A child that writes its own record reads `unchanged`, and exit 4 is not a crash (M31 and M32 RED). The classification now depends on whether a record was written, which is sensitive to clock steps (NIT-2). |
| review MINOR-5 | M12 survived, and no test cited REQ-REF-008 | **CLOSED** | M12 is RED through `test_a_relative_database_path_is_resolved_before_the_child_gets_it`. The module docstring of `tests/unit/test_nightly_refresh.py` cites REQ-REF-008. |
| review NIT-1 | `/health` shows a missing record and a torn record the same way | **STILL OPEN (NIT)** | `read_record` and `report()` are unchanged for this case: both show `"none"`. It is not in the ledger. |
| review NIT-2 | The child's `cwd` is an equivalent mutant | **STILL OPEN (NIT)** | There is no comment at `nightly.py:222`. With `-P` and `PYTHONPATH`, the child's cwd is even less relevant than before. |
| security MAJOR-1 | "Network code never loads into the server" is false, and its test was green anyway | **OPEN-RECORDED** | W-125. The claim is corrected in the D-154 amendment and in the `nightly.py` docstring. The test now imports the server in a fresh interpreter and checks `sys.modules`. New mutant M47 (`main.py` imports `app.workflows.build`) is RED, so the test can now fail. |
| security MINOR-1 | The child's whole output was buffered in the server | **CLOSED** | `scen.py flood`: with 50 MB and 200 MB of output, the parent's peak RSS stayed at **26 MB** in both runs (it was 974 MB before the fix), and `LAST LINE` still reached the log. M38 (keep the head) and M39 (unbounded) are RED. |
| security MINOR-2 | The switch was not re-checked at lifespan (TOCTOU) | **CLOSED** | With `APP_ENV=production` and the switch set in-process, `from_environment` returns `None` and logs the D-116 refusal. With `APP_ENV=test` it returns a schedule. M44 is RED. |
| security MINOR-3 | `retire_refresh.sh` trusts whatever answers on :8080 | **STILL OPEN (MINOR-3), narrowed** | I copied the script with its port changed to 18778, stubbed `launchctl` and `rm`, and used a fake HOME. With nothing listening it refused. A fake server started as `python3 fake.py plain` was refused. **A fake server started as `python3 fake.py app.adapter.main:app` passed the check**: the script printed "safe to retire", went on to the launchd step, and ran `rm` on both files (both stubbed). |
| security MINOR-4 | The child inherited the whole shell environment | **CLOSED** | The child saw only `HOME, LANG, LC_CTYPE, PATH, PYTHONPATH, TMPDIR, __CF_USER_TEXT_ENCODING`. The `FAKE_SECRET_TOKEN` and `AWS_SECRET_ACCESS_KEY` I set did not reach it. M41 is RED. The real cycle published under this environment. |
| security NIT-1 | The working directory could shadow `app.workflows.refresh` | **CLOSED** | `refresh_command` passes `-B -P -m`. M40 (drop `-P`) is RED. The real cycle ran with `-P` and published. M42 (no `PYTHONPATH` for the child) is also RED. |
| security NIT-2 | Each uvicorn worker runs its own schedule | **STILL OPEN (NIT)** | There is no single-worker note or guard in `nightly.py` or D-154, and the ledger does not mention it. `app.sh` runs one worker. |
| security NIT-3 | `/health` shows the refresh timing without authentication | **No action asked** | The seat asked for no remedy while this stays dev-only. It is unchanged. |
| security NIT-4 | `HOME=""`, and "removed:" is printed even when nothing existed | **HOME part CLOSED; message part STILL OPEN (NIT)** | `retire_refresh.sh:19` refuses an empty `HOME`. Lines 48-49 still run `rm -f ... && echo removed:`, which prints even when there was nothing to remove. |

## Mutants (applied to a copy, run, restored, md5-checked)

Run set: `test_nightly_refresh.py`, `test_ios_client_contract.py` and `test_router_hints.py`, with
`-x` and a 180 s alarm. The baseline was 76 passed.

| # | Mutation | Result |
|---|---|---|
| M12 | Drop `.resolve()` on the DB (previously survived) | RED |
| M18 | The pick card drops its price note (previously survived) | RED |
| M19 | The full ranking drops its footer (previously survived) | RED |
| M24 | The home preview drops its note | RED |
| M25 | The pick card computes the note but renders `let _ = excluded` | **SURVIVED** (NIT-1) |
| M26 | The timeout path records no failure | RED |
| M27 | The timeout path does not log the tail | **SURVIVED** (NIT-1) |
| M28 | `report()` ignores `last_failure` | RED |
| M29 | `report()`: `<` changed to `<=` (equal timestamps) | **SURVIVED** (NIT-1) |
| M30 | `wrote`: `>=` changed to `>` (equal timestamps) | **SURVIVED** (NIT-1) |
| M31 | Busy exit 4 counted as a crash | RED |
| M32 | The `wrote` check is always true | RED |
| M33 | A late wake always runs | RED |
| M34 | The late check: `>=` changed to `>` at the close | **SURVIVED** (NIT-1) |
| M35 | `recently_good` is always False | RED |
| M36 | `RECENT` = 24 h | RED (hang, stopped by the alarm) |
| M37 | `RECENT` = 2 h | **SURVIVED** (MINOR-1 / NIT-1) |
| M38 | The tail keeps the head | RED |
| M39 | The tail is unbounded | RED |
| M40 | Drop `-P` | RED |
| M41 | The child inherits the whole environment | RED |
| M42 | No `PYTHONPATH` for the child | RED |
| M43 | A cycle that fails to start records no failure | **SURVIVED** (NIT-1) |
| M44 | `from_environment` skips the re-check | RED |
| M45 | The next pick is seeded from `now()` | RED |
| M46 | The late branch takes the window from `now()` | RED |
| M47 | `main.py` imports `app.workflows.build` | RED |

Kill rate: 19 of 27. None of the 8 survivors is equivalent. M29 and M30 matter only at an exact
float tie.

## New findings

### MINOR-1 — The 12-hour rule skips the night after any good daytime cycle, so data can reach about 36 h old, while D-151 states "up to a day"

`nightly.py:63` and `:156-162`, and `_due` at `:285`. The rule was added to stop a second cycle in the
same night. But "a good cycle within 12 h" also covers cycles from the afternoon and evening.

*Measured* (`due.py`, the real `serve()` on an injected clock, stale record, fake cycle that writes a
record):
- **Engine started 13:00 or later with stale data:** it catches up at 13:01, and **tonight's run is
  skipped at every random minute in the window** (tested at rng 0.0, 0.5 and 0.99). The next run is
  the following night. The longest gap was **1 day 11:57**.
- A start at 11:00 or 12:00 is skipped whenever the pick falls less than 12 h after the catch-up.
- A start at 18:00 had a gap of 1 day 6:57. A start at 22:50 had a gap of 1 day 2:07.

**Consequence while launchd is still loaded:** the launchd plist has `StartInterval` 43200 (every 12 h).
While it is loaded, a good launchd cycle is almost always less than 12 h old at the engine's pick. So
the engine's own nightly cycle never runs before the owner retires launchd. `retire_refresh.sh` only
gates on `"scheduled"`, so the owner retires the launchd job without the engine's own cycle ever
having run.

*Is this acceptable under D-151?* In substance, mostly yes: D-151 says the boards move "on the order
of days", and a daytime catch-up is a real refresh. But it contradicts D-151's stated cost ("up to a
day old") and D-154's own amendment, which describes the rule only as stopping "a catch-up at 23:11
followed by 00:05". So a decision is recorded that the code does not match. M37 (2 h) survives, so
nothing pins the value.

*Remedy:* skip only when the good cycle falls inside the current window, for example
`at >= window_around(next_run)[0]`. That is exactly "once a night", and it closes the 23:11 → 00:05
case too. Otherwise, amend D-151's cost and D-154 to state the 36 h. Either way, add the 13:00-start
test.

### MINOR-2 (carried from review MAJOR-2) — REQ-PRC-002's evidence does not name what now proves it

`docs/prd.md:534` still reads "on the pick card's price line, the detail screen and once under the full
ranking. Cited by `DetailTests` ...". The home preview is missing from that list. The test that
actually holds the three views, `test_every_place_that_prints_a_search_price_says_what_it_leaves_out`,
is not cited. The first review's remedy asked for this amendment.

### MINOR-3 (carried from security MINOR-3) — the retirement script's listener check is a command-line grep, and D-154 claims more than that

`scripts/retire_refresh.sh:24-28`. The script accepts any listener whose `ps` command line contains
`app.adapter.main:app`. I measured this with an impostor server that passed the check. The check does
not look at the repository, the `.venv`, the build, or the `--db`. A second checkout's engine, or one
pointed at another database, also passes. The D-154 amendment says the script "checks that `:8080` is
this engine". *Remedy:* also require `build` from `/health` to equal `dev-$(git rev-parse --short
HEAD)`, and the listener's executable to be this repository's `.venv/bin/python`. Otherwise, reword the
amendment to what the script actually checks and record the gap.

### NIT-1 — Test gaps in the fix round

M25, M27, M29, M30, M34, M37 and M43 survive. Each one's behaviour is correct today (I checked the
`not started` case with a scenario: `report()` -> `"not started"`), but nothing pins these behaviours:
- the tail logged on the timeout path (the first review's remedy);
- the `not started` report;
- the exact window-close boundary;
- the 12 h value;
- that the pick card renders the note rather than only computing it.

### NIT-2 — A clock that steps back relabels a published cycle as "crashed"

`nightly.py:245`. `wrote` compares the child's recorded `at` with the parent's `started`. *Measured*:
a child that exits 0 with a record stamped 5 s before its start is logged `exit 0 (crashed)`, and
`/health` says `crashed`. `refresh.py` stamps `at` at the end of the cycle (`refresh.py:613`), so this
needs a backward clock step longer than the cycle (about 8 s). The wrong label clears at the next
cycle. An exact tie (`at == started`) is handled correctly (measured: `published`).

### NIT-3 — A grandchild that holds stdout makes a clean exit read as "killed", and it outlives the kill

`read_tail` waits for EOF, not for the child to exit. *Measured*: a child that starts a grandchild
sleeping 8 s and then exits 0 was reported `killed` at the 3 s timeout. The grandchild was left with
`ppid 1`. Nothing in `src/app` starts a subprocess today (a grep for
`subprocess|multiprocessing|os.fork|Popen` finds only `nightly.py`), so this is latent.

### NIT-4 — `busy`, and a failure from before a restart, are invisible on `/health`

A fresh engine whose cycles only ever return `busy` reports the old record's `published` with its old
time (measured). `last_failure` lives only in memory, so a restart after a killed night reverts
`/health` to the record's outcome. With W-126's orphan holding the lock, `/health` therefore reads
`published` every night while nothing refreshes. Only the ageing `refresh_last_at` shows it. This
belongs with W-126 when that is fixed.

### NIT-5 — `CHILD_ENV` omits `ALL_PROXY` / `all_proxy`

`nightly.py:84-86`. httpx honours `ALL_PROXY` when reading proxy settings from the environment. An
owner whose proxy is set only through `ALL_PROXY` would get a cycle that fetches directly. There is
no known user of this today.

## What I attacked and could not break

- **The real cycle under the restricted environment.** I copied `advisor.db` and its record to scratch.
  Then, from `cwd=/`, I ran `env -i HOME PATH LANG SECRET_TOKEN APP_ENV=test MODEL_RANKING_REFRESH=nightly
  MODEL_RANKING_DB=<copy> MODEL_RANKING_EPOCH_DIR=/Users/umutcanapaydin/Desktop/terminal_output/model_ranking/epoch_data`,
  then `from_environment(...)`, then `run_once("catch-up")`. The command was
  `.venv/bin/python -B -P -m app.workflows.refresh --db <copy> --epoch-dir ...`. It exited **0 (published)
  in 8.3 s**, the refresh's own outcome JSON reached the log, `last_failure` was `None`, and `report()`
  went from `unchanged` (11:41 UTC) to `published` (22:28 UTC). The real `-P` + `PYTHONPATH` resolution
  of the module works. No file in the repository changed.
- **`read_tail`**: `del tail[:-N]` is a no-op below N bytes and keeps the last N bytes above N. A UTF-8
  sequence cut at the boundary decodes as one replacement character. M38 and M39 are RED.
- **`report()` ordering**: a failure followed by a later `busy` keeps showing the failure. A later cycle
  that writes a record replaces the failure (test and scenario). The comparisons in `wrote` (`>=`) and
  in `report` (`<`) agree at a tie.
- **`_due` after a late wake**, over several windows, and the `after = window_close` seeding: M33, M45
  and M46 are RED.

## What I did not check

- A real Mac sleep, a real DST change or a real clock step. All of these were simulated on an injected
  clock or with stamped records.
- The real `retire_refresh.sh`, and anything that touches launchd. Only a port-changed copy ran, with
  `launchctl` and `rm` stubbed.
- `ios/app.sh up` end to end, and the app on a simulator. The preview note was checked by source,
  mutants and a successful `xcodebuild`, not by looking at it.
- Multiple uvicorn workers, and a SIGKILL of a real uvicorn (W-126), were not re-run.
- SAST (`bandit` / `semgrep` are not installed, and I installed nothing).
- The full `make check` as one command including `install`. I skipped `install`, and ran
  conformance-gate, swift-test and client-decls separately after `wave-check-all` stopped the chain.
- The contents of `docs/plans/m16-wave-2-close.md`, beyond the gate's message and its row 3
  placeholder.
