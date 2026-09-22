---
record_type: review
id: m16-wave-2-review
status: ratified
seat: independent
date: 2026-09-23
---
# M16-W2 — independent review: the engine's own nightly refresh, the floor line and the search-price note

**Seat:** independent (Code-Reviewer + Tester; authored none of this wave). **Base:** acef579, all of
it uncommitted. Policy read from `git show HEAD:subagent-profiles/Code-Reviewer.md` and
`git show HEAD:subagent-profiles/Tester.md` only. Author-family / reviewer-family: not recorded to
this seat (fallback: same session tooling); fresh context asserted.

**The tree moved while I reviewed it.** The security seat's fixes landed at 00:52-00:54 (env allowlist,
bounded output tail, `-P`, switch re-check in `from_environment`, transitive import test). I
re-snapshotted after the tree had been quiet for three minutes and re-ran everything below against
that snapshot: `nightly.py` md5 `9c2b1346...`, `main.py` `6ce66612...`, `test_nightly_refresh.py`
`bca5ef4b...`, `ContentView.swift` `cbad74cd...`, `Detail.swift` `c189ed07...`,
`retire_refresh.sh` `a4c731b5...`.

Worked in copies under the session scratch directory. Nothing was started on :8080; the owner's
`advisor.db` / `.refresh.json` md5s were identical before and after (`ef9e48a9...` / `7e0355ed...`);
no launchd call; every process I started was stopped and `pgrep` confirmed none left. Every mutant
was applied by script to a copy of the repository, run, restored, and checked byte-identical.

## Scope

`src/app/adapter/nightly.py` (new), `src/app/adapter/main.py` (validator, `_lifespan`, `/health`),
`ios/app.sh`, `scripts/retire_refresh.sh` (new), `tests/unit/test_nightly_refresh.py` (new),
`ios/ModelRanking/Engine/{Detail,Models}.swift`, `ios/ModelRanking/ContentView.swift`,
`ios/EngineTests/{DetailTests,EngineClientTests}.swift`, `tests/unit/test_ios_client_contract.py`,
D-152/D-153/D-154, REQ-REF-008 / REQ-FLR-002 / REQ-PRC-002, ledger W-112/W-119/W-124.

## Verdict

**PASS WITH FINDINGS — 0 BLOCKING, 2 MAJOR, 5 MINOR, 2 NIT.**

The core claim holds and I measured it: a hanging child does not hold a request, is killed at the
timeout, and is killed on a real uvicorn shutdown by SIGTERM and by SIGINT; a real cycle through the
current `run_once` published on a copy of `advisor.db` from `cwd=/` with a stripped environment. The
gaps are in what `/health` says after the timeout fires, in the "once a night" arithmetic around
restarts and sleep, and in the search-price note, which is proven on the detail screen only.

## Suite result (run by me, on the snapshot)

- `pytest -n auto` (the `make test` command, run directly because `make test` depends on `install`):
  **1004 passed, 15 skipped** (the author reported 1000/15 before the security fixes added four).
- `make swift-test`: **PASS, 268 tests, each named in the manifest.**
- `ruff check src tests scripts`: clean. `mypy src`: no issues in 34 files.
- `scripts/client_decl_gate.py`: **PASS**, 11 client files in 4 configurations.
- `tests/unit/test_router_hints.py` + `tests/unit/test_ios_client_contract.py`: green (part of the
  mutant baseline, 67 passed).

## Findings

### MAJOR-1 — A cycle killed at the timeout is reported on `/health` as the previous outcome, usually "published"

`src/app/adapter/nightly.py:216-220` returns `None` on `TimeoutError` and the parent records
nothing; the child is SIGKILLed, so `refresh.py`'s `BaseException` recorder (`refresh.py:651`) never
runs; `report()` (`nightly.py:262-270`) reads only the refresh's own record.

*Measured* (scratch `exp1.py`): record `{"exit_code": 0, "at_iso": "2026-09-20T23:10..."}`, then a
child that enters `refresh()` with a builder that sleeps 30 s, `timeout=3`. `run_once` returned `None`,
the record was unchanged, and `report()` returned
`{"refresh": "scheduled", "refresh_last": "published", "refresh_last_at": "2026-09-20T23:10:00+00:00"}`.
A cycle that hangs every night therefore reads "published" on `/health` indefinitely, and only the
date ages. The timeout path also returns before the tail loop (`nightly.py:221`), so the killed
cycle's own output never reaches the log either: the log gets one line saying it was killed and
nothing about where it was stuck. D-151 / D-154 clause 3 make `/health` and the log the *only* two
places a failed night shows; this is the "silence reported as success" class that `refresh.py`'s B1
comment records fixing once already.

*Remedy:* keep this process's last outcome in memory (`trigger`, `at`, `killed` / `could not start`
/ exit code) and report it when it is newer than the record's `at`, e.g. `refresh_last: "killed"`;
log the tail on the timeout path too. Add a test: hanging child + an old `published` record →
`/health` does not say `published`.

### MAJOR-2 — REQ-PRC-002 is marked MET, but the home ranking preview prints search prices with no note, and the card and list notes are pinned by no test

1. `ios/ModelRanking/ContentView.swift:410-437`: `rankingPreview` renders `RankedRow`s on the home
   screen, each printing `figuresLine(... blendedPerM ...)` → `priceTag` (`Scores.swift:94-101`).
   It does not receive `priceExcludes` and prints no note. REQ-PRC-002 says "*wherever* the app
   shows a price"; the author's own reason for the full-list footer (`ContentView.swift:1025-1030`,
   "every row prints a price") applies to this card as well. Mitigation: the pick cards above it on
   the same screen carry the note.
2. Mutants M18 (delete the pick card's note, `ContentView.swift:832`) and M19 (delete the list
   footer, `:1028-1030`) **survived every suite**: the Swift package compiles only
   `ModelRanking/Engine` (`ios/Package.swift`), and the Python source pins in
   `test_ios_client_contract.py:871-876` check that `PickRow` is *given* `priceExcludes`, not that
   anything prints it. The PRD row cites `DetailTests` for "the pick card's price line ... and once
   under the full ranking"; those tests prove the wording and the detail fact only.

*Remedy:* give the preview card the same footer (or one line under it), and pin all three places in
`test_ios_client_contract.py` the way the detail doors are pinned (a regex that finds
`priceExclusion(priceExcludes, in: language)` inside `PickRow`'s body, `RankingList`'s `footer:`, and
the preview card). Amend REQ-PRC-002's evidence to what the tests actually prove.

### MINOR-1 — D-154 says a Mac asleep through the window "skips that night"; the code runs about a minute after wake

`nightly.py:238-239` (`_sleep_until`) re-reads the wall clock after each 60 s poll and returns as
soon as `next_run` is in the past. *Measured* (`exp3.py`, injected clock, 10 h jump during a sleep
from 22:00): runs `['nightly@09-24 08:01', 'nightly@09-25 00:00']`. A run at 08:01 is outside the
23:00-01:00 window REQ-REF-008 states, and contradicts D-154's "The cost" paragraph. Either behaviour
is defensible; the ADR and the code must say the same one. *Remedy:* pick one (skip if `now` is past
the window's close, or amend D-154 and REQ-REF-008 to "or on wake"), and add the test.

### MINOR-2 — "Once a night" is per process, not per night

`nightly.py:249` seeds `after = self.now()` after a catch-up, and the nightly pick never consults the
record. *Measured* (`exp3.py`): a stale start at 23:10 runs `catch-up@23:11` and `nightly@00:05` the
same night; an engine restarted at 00:20 with a good record from earlier that night runs again at
00:40. `./ios/app.sh restart` inside the window therefore costs another full fetch from every
upstream per restart. *Remedy:* skip tonight's pick when the record shows a good cycle inside the
current window, and seed `after` from the window's close when the catch-up itself ran inside it.

### MINOR-3 — The 30-minute limit lives only in the parent; an engine that dies hard orphans a stuck child that holds the lock for good

*Measured* (real uvicorn on :8099, the schedule patched to start a child that takes
`advisor.db.refresh.lock` and sleeps): SIGTERM and SIGINT to uvicorn → child gone. **SIGKILL →
child alive with `ppid 1`**; the real `python -m app.workflows.refresh --db <copy>` then exited
**4 (busy) in 0 s** and wrote no record. Every later cycle is busy until someone kills the orphan by
hand, and `/health` keeps showing the last record (MAJOR-1's shape). Needs a hung cycle plus a hard
kill (OOM, `kill -9`, a crash), so MINOR. *Remedy:* give the child its own deadline (a
`signal.alarm` set by a tiny wrapper or a `--deadline` on `refresh.py`), or `start_new_session=True`
and have the child exit when its parent is gone.

### MINOR-4 — A child that dies before `refresh.main` runs is logged as "exit 1 (unchanged)"

*Measured* (`exp1.py`): command `-m app.workflows.refresh_typo` → log
`No module named app.workflows.refresh_typo` then `nightly refresh: exit 1 (unchanged)`. Python's own
exit code for an uncaught exception or a missing module is 1, which is `EXIT_UNCHANGED`; `refresh.main`
maps its own crashes to 2 precisely for this reason. A broken venv would log "unchanged" every night.
`test_a_cycle_that_raises_or_fails_reports_its_code_and_does_not_raise` (`test_nightly_refresh.py:200`)
asserts `== 1` for a raising child without noting the ambiguity. *Remedy:* name 1 "unchanged" only if
the last output line parses as the refresh's outcome JSON; otherwise log "crashed (exit 1)".

### MINOR-5 — Test gaps: a relative `MODEL_RANKING_DB`, and no test cites REQ-REF-008

- Mutant M12 (drop `.resolve()` at `nightly.py` `from_environment`) **survived**: the only test uses
  an absolute `tmp_path`. Without it, a relative DB would be refreshed relative to `_REPO` (the
  child's `cwd`) while the server serves it relative to its own cwd. The code is right today; nothing
  holds it. *Remedy:* one test with `MODEL_RANKING_DB=advisor.db` from a different cwd.
- `grep -rn REQ-REF-008 tests ios/EngineTests` returns nothing. REQ-FLR-002 and REQ-PRC-002 are
  cited (`DetailTests.swift:254`, `:280`). *Remedy:* cite it in the module docstring or the key tests.

### NIT-1 — `/health` cannot tell a missing record from a torn one

`nightly.py:262-270`: both read `refresh_last: "none"`, `refresh_last_at: ""`
(`test_the_record_is_the_refreshs_own_file` confirms `read_record` returns `None` for both). A torn
record is a fault; "none" reads as "never ran".

### NIT-2 — Mutant M13 (drop `cwd=_REPO`) survives, and is equivalent today

With `-P`, `PYTHONPATH=_SRC` and an absolute `--db`, the child's cwd has no effect I could find. Fine
to keep; worth a comment saying so, or drop it.

## Mutants (fault injection; applied to a copy, run, restored, byte-checked)

Run set: `tests/unit/test_nightly_refresh.py`, `test_ios_client_contract.py`, `test_router_hints.py`
(67 tests on the baseline), 120 s alarm.

| # | Mutation | Result |
|---|---|---|
| M1 | `window_around`: `<` → `<=` | RED |
| M2 | `needs_catch_up`: `>` → `>=` | RED |
| M3 | `GOOD_CYCLES = {0}` | RED |
| M4 | no `proc.kill()` in `finally` | RED (timeout test, 20 s) |
| M5 | next pick from `now()`, not the window's close | RED |
| M6 | `_lifespan` never cancels the task | RED (hang, killed by alarm) |
| M7 | `report()` running/scheduled inverted | RED |
| M8 | one long sleep instead of 60 s polls | RED |
| M9 | switch allowed in every environment | RED |
| M10 | no startup grace | RED |
| M11 | catch-up always | RED |
| M12 | drop `.resolve()` on the DB | **SURVIVED** (MINOR-5) |
| M13 | drop the child's `cwd` | **SURVIVED** (NIT-2, equivalent) |
| M14 | child output never logged | RED |
| M15 | `refresh_last` ignores the record | RED |
| M16 | `/health` omits `refresh` when off | RED |
| M17 | validator never asks `nightly` | RED |
| M18 | pick card drops the price note | **SURVIVED** (MAJOR-2) |
| M19 | full ranking drops the footer | **SURVIVED** (MAJOR-2) |
| M20 | `_lifespan` never starts the schedule | RED |
| M21 | child inherits the whole shell | RED |
| M22 | `from_environment` skips the re-check | RED |
| M23 | tail keeps nothing | RED |

Kill rate: 19 of 23 (one of the 4 survivors is equivalent).

## Acceptance-criterion evidence

- **REQ-REF-008** → `tests/unit/test_nightly_refresh.py:53, 66, 93, 140, 148, 183, 200, 210, 235, 312`
  (window, once-a-day arithmetic, catch-up, hang killed, killed mid-publish, answering while hanging
  through `TestClient(main.app)`, production refuses). GREEN. Not cited by ID (MINOR-5). Gaps:
  MAJOR-1, MINOR-1..3.
- **REQ-FLR-002** → `ios/EngineTests/DetailTests.swift:256` (anchored Elo floor = `Score 50 / 100`,
  the same call as the card), `:267`, `:272` (rank-only in its own unit), `:222` (the Turkish screen
  has the same lines, floor and price note included). GREEN. Code: `Detail.swift:211-228`.
- **REQ-PRC-002** → `DetailTests.swift:282`, `:292`; `EngineClientTests.swift:166`. GREEN for the
  detail screen and the wording only; card, list and preview unproven (MAJOR-2).

## Hardened-invariant producers ("a cycle cannot block or end the server")

Producers: `NightlyRefresh.run_once` (spawn, wait, kill), `NightlyRefresh.serve` (schedule loop),
`main._lifespan` (start, cancel), `main.health` (report). Citing tests: `run_once` →
`test_nightly_refresh.py:183, 200, 205, 210, 375, 389`; `serve` → `:140, 148, 156`; `_lifespan` →
`:235` (M6 and M20 RED); `health` → `:235, 270, 275`. Gaps: the parent-death case (MINOR-3) and what
`health` says after a kill (MAJOR-1).

## K.8 contract drift check

```
src/app/adapter/main.py:1290:                "min_quality": spec.min_quality,
src/app/adapter/main.py:1293:                "price_excludes": spec.price_excludes,
ios/ModelRanking/Engine/Models.swift:74:        case minQuality = "min_quality"
ios/ModelRanking/Engine/Models.swift:75:        case priceExcludes = "price_excludes"
src/app/adapter/main.py:594:    schedule = nightly.NightlyRefresh.from_environment(RELAXED_ENVS)
src/app/adapter/main.py:1190:    schedule = _NIGHTLY.get("schedule")
```

OK: the client reads exactly the two keys the plan's K.8 line names; `/v1` gains nothing from W2;
`/health` gains four string keys, additive.

## What looks right

- **Child process, awaited, killed.** Real uvicorn on :8099 with a hanging child: `/health` answered
  `"refresh": "running"`; SIGTERM → uvicorn exited and the child was gone; SIGINT → same.
- **A real cycle through the current code.** `from_environment(RELAXED_ENVS)` +
  `run_once("catch-up")` from `cwd=/`, under `env -i` with a planted `SECRET_TOKEN`, on a copy of
  `advisor.db` with the owner's Epoch directory: `-B -P -m app.workflows.refresh`, **exit 0
  (published) in 9.1 s**, `report()` → `published`.
- **A run that finishes after 01:00** (start 00:58, 30 min long): the next run is the following night
  at 00:58, not a second one that night (`exp7.py`).
- **The window arithmetic** at 12:00, 23:30, 00:30 and exactly 01:00 is right, and M1/M5/M8 are killed.
- **Pipe deadlock / large output:** the drain reads to EOF with a bounded tail; 20 MB of output
  passes (the flood test) and M23 is killed.
- **D-116 gate:** the switch is refused outside relaxed environments at import-time validation and
  again at start (M9, M17, M22 killed).
- **The floor line** goes through `scoreText` with the card's anchor, so an anchored Elo floor reads
  on the card's scale (`Score 50 / 100` when the floor equals the anchor), a bare Elo floor keeps
  `Elo`, and ECI states its own unit. Both languages have the line.
- **Privacy gates** hold: `client_decl_gate.py` PASS, `test_router_hints.py` green.
- `retire_refresh.sh` refuses unless `/health` says `scheduled` or `running`, and its label and
  wrapper path are pinned to the plist by a test. The app.sh Epoch default matches the launchd
  wrapper's path (read, not run).

## What I did not check

- Multiple uvicorn workers (each would run its own schedule; `flock` makes the loser `busy`). Not run.
- A real DST transition or a real Mac sleep; sleep and clock jumps were simulated on an injected
  clock only. The owner's zone (+03) has no DST.
- `scripts/retire_refresh.sh` was not executed (it would touch launchd).
- The app on a simulator: the preview/card/list layouts in MAJOR-2 were read from source, not seen.
- `make check` as one command, because it depends on `install`; its parts were run individually,
  except `wave-check-all`, `conformance-gate`, `install-check`, `coverage-floor` and
  `check-records-selftest`.
