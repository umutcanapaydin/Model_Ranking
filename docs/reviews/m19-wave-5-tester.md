---
record_type: review
id: m19-wave-5-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# Wave 5 Tester Review (m19)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer, and it is not the Stage 5.1 security seat.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `6c9ce17..6c98dd7`. That is W5's own 35 commits (`git log --no-merges`, less W4's
four), over W4's head. The diff read is `git diff ec5159e 6c98dd7`, without W4's `Reading.swift`,
`Router.swift`, `ReadingTests.swift` and `docs/research`: 49 files, +3033 / -108. It includes both
Code-Reviewer verdicts, the security review, and the fixes up to `0b8ae4a`.
**Risk tier:** HIGH (`docs/plans/m19-wave-5-plan.md:13`). The serving image, the launcher, the guard
and a public surface change.
**Code-Reviewer verdict:** MINOR, M1 to M7, K1, R1 to R5 (`docs/reviews/m19-wave-5-review.md`, the
review of record). Not BLOCKING, so this seat runs.
**Model routing (HIGH, advisory):** author family: Claude (every commit carries `GP-Agent:
claude-code/local-lane`) / reviewer family: Claude (Opus 5.5). Fallback reason: no second model family
is available to this seat. Fresh context: I read the profile and the rules first, then the plan,
D-185, the runbook and the issues, then the reviews, then the code and tests, and the commit
messages last.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75dac85...`) on
`origin/main` and in the tree. The range does not touch it or `.agents/rules/practices.md`. Nothing in
the diff tries to change this review's policy.

## Verdict

MINOR

**Nothing blocks now.** Every phase's acceptance check has a citing test that exercises it, and every
red commit of the wave fails on its own tree and passes on its fix (13 pairs, below). Two checks had
no full test before this review, and I wrote both:
- **#147 (P1) had no test at all, and it broke twice inside the wave.** `f1dc3d1` left the Mac's
  name in two M18 records, and the round-1 review record spelled it again in a search pattern
  (`8997937`). Reviewers found both by reading. The new scan fails on each of those commits and
  passes from `ff940b9` on.
- **P3's "each affected surface says it has no evidence" was tested on one surface of four.** The new
  test gives all four surfaces rows, checks that each answers before the derivation and says "no
  evidence" after it, and checks that `coding` keeps Epoch's board.

**Fault injection: 35 of 59 faults were caught before this review (59%). All 59 are caught now.**
The 24 that got through were in the shell scripts, the image, `fly.toml`, the Xcode project, the
records, and the derivation's own safety checks (the survivor check, the "no price left" refusal,
the cleanup after a failure, R4's refusal). I wrote 20 test functions (39 cases) that catch all 24.

**The three findings are holes and records, not failures:**
- M1: the guard lets a dry run chained to a real deploy through.
- M2: G-7 is out of date and cites only #142.
- M3: the derivation's list of tables is still closed. Nothing leaks today.

## Acceptance-criterion coverage (REQUIRED)

The wave scopes no REQ-IDs. Its tests cite issues and D-IDs. By phase (`m19-wave-5-plan.md:47-54`):

- **P1, #147** (no tracked file names the owner's Mac or home address): **no citing test before this
  review.** Written: `tests/unit/test_security_surface.py:225`,
  `test_no_tracked_file_names_a_mac_or_home_address_beyond_the_placeholders`. It reads every tracked
  text file, review records included. It flags:
  - any `.local` host name other than the placeholders;
  - any RFC 1918 address other than the probe values, a regex-escaped one included;
  - any hyphenated token that holds "MacBook".

  It names neither the Mac's name nor its address. `:243` checks the scan on planted spellings. I
  replayed the scan on each commit's tree: RED at `5040948` (57 hits, the issue's own files), RED at
  `f1dc3d1` (6, the M18 records), RED at `8997937` and `f84114f` (the round-1 record), GREEN at
  `ff940b9` and `6c98dd7`. GREEN.
- **P1, #145** (the launcher refuses a preflight that dies silently):
  `tests/unit/test_engine_service.py:604`. RED at `b5beea9`, GREEN at `5040948`. Faults E1 and E2
  caught. GREEN.
- **P1, #141** (both `FROM` lines by digest, a test refuses a tag):
  `tests/unit/test_dependency_locks.py:334`, `:341`. RED at `6fb3289`, GREEN at `160e1a7`. K8 caught.
  GREEN.
- **P2, #94** (the bind told to the startup check; the hosted stage; `fly.toml`'s Host; the deploy
  script):
  - Tests: `tests/unit/test_hosted_engine.py:64-139`, `tests/unit/test_deploy_hosted.py:63-190`.
  - Red to green: RED at `5ea0254` (4 failed), GREEN at `ff7205a`; RED at `c70d2bf` (8 failed), GREEN
    at `1a8aabb`.
  - **Partial before this review:** ten faults got through (K1, K3 to K7, D1 to D3, D7). The new
    tests are listed below. GREEN.
- **P3, #88** (the public artifact, each affected surface dark, a test that no left-out row
  survives, the ADR):
  - Tests: `tests/unit/test_public_artifact.py:28-163`. RED at `8879619` (5 failed), GREEN at
    `941d770`.
  - **Partial before this review:** the "no evidence" answer was tested on `agentic-coding` only, the
    ADR's table on nothing, and the derivation's own refusals on nothing.
  - Written: `:232`, the four surfaces and `coding`; `:219` and `:273`, D-185 and the runbook against
    the code; `:169` and `:188`, the derivation's refusals; `:201`, R4.
  - I also measured the real artifact. I derived a public copy of the worktree's served artifact
    (sha256 `dac97873...9344`, unchanged after) and served both in process:
    - every task and budget answered 200;
    - `abstract`, `agentic-coding`, `computer-use` and `web-dev` say `no_evidence`;
    - `coding` ranks 32 against 54, and `assistant`, `everyday`, `expert`, `factuality` and
      `mathematics` rank 2 to 4 fewer, as D-185 says;
    - no byte of any `LEFT_OUT` id, `openrouter.ai`, `ARC-AGI`, `DeepSWE`, `MMLU` or `WebDev` is in
      the file;
    - the freelist is 0 and the journal mode is `delete`.

  GREEN.
- **P4, TestFlight** (icon, privacy manifest, encryption answer, Release URL, runbook):
  - Tests: `tests/unit/test_testflight_ready.py:43-121`. RED at `fe1bd13` (4 failed), GREEN at
    `96f6010`. The S1 and M3 follow-ups were also red first (`31fff71`, `f84114f`).
  - **Partial before this review:** a build setting on the app target outranks its xcconfig. So an
    `ENGINE_URL`, or an empty icon name, set in `project.pbxproj` passed every test (X1, X2).
  - Written: `:134`. GREEN.
- **P5, #142** (`-uf`, `-fu`, `--mirror`): `conformance/test-hook-claims.py:281-301`. RED at `48dc201`,
  GREEN at `9a793ed`. The later guard pairs were RED at `2dc5b9f` and `331aed0`, GREEN at `d385074`
  and `0b8ae4a`. Faults G1 to G5 caught. GREEN, with M1 and M2 below.
- **P6 / Stage 5.2** (`make journey`, `make cold-start`):
  - Tests: `tests/unit/test_release_gates.py:35-75`. RED at `f2a5de3` (3 failed), GREEN at `7fde40d`.
  - **Partial before this review:** the stand-in journey always passed and the stand-in `curl`
    always answered, so a failing journey and a container that never answered were both untested
    (J1, J2, J4).
  - Written: `:85`, `:98`, `:111`. GREEN.

## Red→green on reported symptoms

Each commit was exported with `git archive` into the scratchpad and run on its own tree with the
worktree's venv. pytest's `pythonpath = ["src"]` puts the exported `src` first. Nothing in the
worktree was checked out.

| Pair | Red commit | Fixed at | Checks |
|---|---|---|---|
| #145 | `b5beea9`: 1 failed | `5040948`: 1 passed | the silent preflight |
| #141 | `6fb3289`: 1 failed, 1 passed | `160e1a7`: 2 passed | the base by digest |
| #94, image | `5ea0254`: 4 failed | `ff7205a`: 4 passed | `test_hosted_engine.py` |
| #88 | `8879619`: 5 failed | `941d770`: 5 passed | `test_public_artifact.py` |
| #94, deploy | `c70d2bf`: 8 failed, 1 passed | `1a8aabb`: 9 passed | `test_deploy_hosted.py` |
| P4 | `fe1bd13`: 4 failed | `96f6010`: 4 passed | `test_testflight_ready.py` |
| #142 | `48dc201`: 3 unbacked | `9a793ed`: 0 unbacked | the conformance harness |
| Stage 5.2 | `f2a5de3`: 3 failed, 1 passed | `7fde40d`: 4 passed | `test_release_gates.py` |
| Review 1 | `92dd862`: 10 failed, 134 passed | `dea39c8`: 144 passed | six files |
| Security S1, S4, S14 | `31fff71`: 2 failed, 33 passed | `60735c9`: 35 passed | four files |
| Guard, S5 and S6 | `2dc5b9f`: 11 unbacked | `d385074`: 0 unbacked | the conformance harness |
| Review 2 | `f84114f`: 4 failed, 26 passed | `ff940b9`: 30 passed | three files |
| Guard `--mirror` | `331aed0`: 2 unbacked | `0b8ae4a`: 0 unbacked | the conformance harness |

#147 had no red commit. The replay above stands in for one.

## Suite result

- **`make check-fast` at `6c98dd7`, with the guard stand-ins first on `PATH`: PASS** in 73.1 s. Lint,
  typecheck, records (conformance included), test, swift-test and client-decls all passed.
  - Test leg (inside `scripts/offline.sb`): `2119 passed, 25 skipped`.
  - `CI will skip 83 of 2144`; the budget is 83.
- **Again with this seat's tests: PASS** in 70.8 s. `2157 passed, 25 skipped`, and `CI will skip 83 of
  2182`. None of the new tests needs a skip, so the budget does not move.
- **Final run, with every new test and this record in the tree: PASS** in 68.8 s. `2158 passed, 25
  skipped`; `CI will skip 83 of 2183`, the budget 83. `wave-check-all` passed, and this record's MINOR
  section reads as M1, M2 and M3, with no finding left without an id.
- **Coverage on touched code:** `src/app/workflows/public.py` 75.4% → 85.5%. What is still missing is
  the CLI `main`, which the deploy tests run in a child process. `rank.py` 95.9% → 97.6%: R4's refusal
  is now covered. `standings.py` stays at 100%. Total 91.73% → 91.88%. The module floor passes.
- **Mutation runner (advisory):** none is wired. Hand-planted kill rate: 35 of 59 before this review,
  59 of 59 after.

## Mocks / contract tests

- **`fly` and `curl` (the deploy script).** `test_deploy_hosted.py`'s `_scratch` is the one set of
  stand-ins, and my four deploy tests reuse it. The `fly` stand-in only records its arguments; it
  enforces no rule. The flags it is checked for (`--build-arg`, `--remote-only`, `--ha=false`) are
  flyctl's, as the second review cited from Fly's reference. No contract test can run without
  deploying. That is by design (D-185 clause 5).
- **`docker`, `curl` and the journey's `python` (the release gates).** `test_release_gates.py`'s
  `_stand_ins` is the one set. My two cold-start tests change one stand-in each, in their own
  `tmp_path`.
- **Not provable here:** whether Fly's check sends the `Host` header (the second review's R1), and
  whether the image builds at all (its R2). No test can see either. The owner's `make cold-start` is
  the first check of the second.

## Test integrity

- **Weakened or deleted to green:** none. I read every changed test file in the range.
  - The credit tests in `test_recommend.py:189` and `test_board_standings.py:168` now expect
    LiteLLM's credit alone. Their fixtures hold only LiteLLM prices, so that is MJ1's design. The
    full credit stays held by `test_public_artifact.py:103` on a built artifact.
  - Two tests allow a catalog's own `Contents.json`: `test_ios_client_contract.py:546` and
    `test_router_hints.py:654`. A data asset is still caught (K2).
  - `test_readonly_uri.py` allows `public.derive` one writable open: the copy it writes. F10, which
    opens the source writable, is caught by that same test.
- **Mirror tests:** most of the wave's tests plant inputs and read exits or files. Some read
  configuration as text: the `Dockerfile`, `fly.toml`, the xcconfig and the scheme. Those tests held
  each line they read, but not how the lines relate. That is where K1, K3 to K7, X1 and X2 got
  through. The new tests check the relation: the stage the hosted image is built on, the port Fly
  reaches against the port the engine listens on, and the target's settings against the xcconfig. The
  HEALTHCHECK is run, not read.

## Fault-injection protocol

How each fault ran: `w5-tester-logs/plant.py` in the scratchpad read the file's bytes and sha256 and
planted one exact edit. It asserted that the edit matched once, or appended a line. It ran the named
tests with `--no-cov`, or the conformance harness for the guard. Then it restored the bytes in a
`finally` and compared both the bytes and the sha256 with the pre-plant read. Each step is one record
in `faults.jsonl`.

Every fault was restored byte for byte. After every batch, `git status --porcelain` was empty, apart
from this seat's own test files once they existed. Each of the 22 first-batch survivors was then run
against the whole suite inside `scripts/offline.sb`: `2119 passed, 25 skipped` every time. F11 was run
against `tests/unit` with this seat's tests deselected: 2107 passed. C4's first edit was a syntax
error, so it is void; C4b replaces it.

| # | Fault (file) | Before this review | Now |
|---|---|---|---|
| F1 | the scores delete matches nothing (`public.py`) | caught: 13 tests, e.g. `test_deploy_hosted.py::test_the_build_stamp_names_the_data_as_well_as_the_code` | caught |
| F2 | the survivor check made a no-op (`left = 0`) | **got through** | caught: `test_public_artifact.py:169` |
| F3 | an artifact with no price left is let through (`<= 0` → `< 0`) | **got through** | caught: `:188` |
| F4 | the pricing delete removed | caught: `:103` (the survivor check raised) | caught |
| F5 | file mode 0o664 | caught: `:33` | caught |
| F6 | a failed derivation leaves its `.deriving` workspace | **got through** | caught: `:169`, `:188` |
| F7 | the alias pattern `openrouter:%` | caught: `:89` | caught |
| F8 | the plans kept | caught: `:138` | caught |
| F9 | no `VACUUM` | caught: `:122` | caught |
| F10 | the source opened writable | caught: `test_readonly_uri.py::test_each_named_writer_opens_as_many_times_as_it_is_allowed` | caught |
| F11 | delete by benchmark, not by source (`coding` loses Epoch's rows) | **got through** | caught: `:232` |
| F12 | a `LEFT_OUT` key misspelt | caught: `:28` | caught |
| C1 | the credit always the full one (`rank.py`) | caught: `test_board_standings.py:155`, and 2 more | caught |
| C2 | R4's refusal removed (`rank.py`) | **got through** | caught: `test_public_artifact.py:201` |
| C3 | `recommend.py` passes `None` | caught: `test_recommend.py:172` | caught |
| C4b | `standings.py` passes `None` | caught: `test_board_standings.py:155` | caught |
| C5 | `served_pricing_sources` returns LiteLLM alone | caught: `test_public_artifact.py:103` | caught |
| D1 | untracked files ignored (`deploy_hosted_engine.sh`) | **got through** | caught: `test_deploy_hosted.py:195` |
| D2 | a failed derivation ignored, an older artifact beside it | **got through** | caught: `:208[unreadable]` |
| D3 | `--remote-only` dropped | **got through** | caught: `:233` |
| D4 | any `/health` build accepted | caught: `:79` | caught |
| D5 | no fetch | caught: `:179` | caught |
| D6 | `--dry-run*` accepted | caught: `:170` | caught |
| D7 | the missing-artifact refusal removed. It still fails, through `set -e`, with a traceback instead of the refusal | **got through** | caught: `:208[missing]` |
| D8 | the stamp hashes the served file, not the derived one | caught: `:121` | caught |
| D9 | the ancestor check back, in place of the tip | caught: `:179` | caught |
| E1 | #145 reverted (`engine_service.sh`) | caught: `test_engine_service.py:604` | caught |
| E2 | the preflight's status forced to 0 | caught: `:604` | caught |
| J1 | the cold start swallows the journey's verdict (`cold-start.sh`) | **got through** | caught: `test_release_gates.py:85` |
| J2 | a container that never answers exits 0 | **got through** | caught: `:98` |
| J3 | the port published on every interface | caught: `:51` | caught |
| J4 | `${URL:?}` removed (`journey.sh`). `set -u` still refuses an unset URL, but an empty one runs | **got through** | caught: `:111` |
| K1 | `FROM build AS hosted` (`Dockerfile`): root, no `CMD`, no production lane | **got through** | caught: `test_hosted_engine.py:144` |
| K2 | the hosted `MODEL_RANKING_DB` dropped | caught: `:133` | caught |
| K3 | the HEALTHCHECK without its `Host` header | **got through** | caught: `:175` |
| K4 | `fly.toml` scales to zero | **got through** | caught: `:167` |
| K5 | `internal_port = 8000` | **got through** | caught: `:155` |
| K6 | `!src/app/.env` appended to `.dockerignore` | **got through** | caught: `test_deploy_hosted.py:282[src/app/.env-False]` |
| K7 | `CMD … --port 8000` | **got through** | caught: `test_hosted_engine.py:155` |
| K8 | the serve stage by tag | caught: `test_dependency_locks.py:334` | caught |
| K9 | `USER root` in the hosted stage | caught: `test_hosted_engine.py:121` | caught |
| K10 | `*` added to the Host list | caught: `:92` | caught |
| X1 | `ENGINE_URL` set on the app target's Release configuration (`project.pbxproj`) | **got through** | caught: `test_testflight_ready.py:134` |
| X2 | `ASSETCATALOG_COMPILER_APPICON_NAME = ""` on the target | **got through** | caught: `:134` |
| X3 | `ENGINE_URL[sdk=iphoneos*]` after the Release line | caught: `:115` | caught |
| X4 | `NSPrivacyTracking` true | caught: `:56` | caught |
| X5 | the Archive action in Debug | caught: `:102` | caught |
| X6 | the encryption answer true | caught: `:71` | caught |
| X7 | the Release URL over `http` | caught: `:77` | caught |
| G1 | the option-cluster alternative removed (`.claude/settings.json`) | caught: the conformance harness (6 unbacked) | caught |
| G2 | `--mi…` without its right anchor | caught: `wave/m19--minor` blocked | caught |
| G3 | `destroy` dropped | caught: `flyctl apps destroy` allowed | caught |
| G4 | the dry-run exemption on any mention | caught: the script allowed | caught |
| G5 | no join of a continued line | caught: `git push \` + newline + `--force` allowed | caught |
| R1 | D-185's `epoch_mmlu` row deleted (`decisions.md`) | **got through** | caught: `test_public_artifact.py:219` |
| R2 | INV-87 cites a test that does not exist | caught: `test_security_invariants.py:154` | caught |
| R3 | the Mac's former name and LAN address, as #147 removed them, added to `docs/owner-iphone.md` | **got through** | caught: `test_security_surface.py:225` |
| R4 | the runbook names two of the four dark surfaces | **got through** | caught: `test_public_artifact.py:273` |
| R5 | D-185 names three of the four | **got through** (the record tests) | caught: `:273` |

**Planted inputs that pass (holes, not faults):**
- an `access` row of a left-out source survives the derivation (M3);
- a dry run chained to a real deploy passes the guard (M1).

**What I ran, and what I did not.**
- Network: none of my probes sent a packet off this machine. The deploy tests' `git fetch` reaches a
  local bare repository, and the stand-ins for `fly`, `docker` and `curl` were first on `PATH`.
  `fly`, `flyctl` and `docker` stand-ins that refuse were also on `PATH` for every run.
- Reads only: `gh issue view` (#94, #88, #141, #142, #145, #147, #189) and `gh issue list`.
- Not run: `fly`, docker, `xcodebuild`, the service installer, launchctl, anything that opens an app
  or a browser, and `os.abort()`.
- The guard was probed by piping payloads into its own command text from `.claude/settings.json`. No
  payload was executed.

## BLOCKING

- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `.claude/settings.json:49` (the deploy script's alternative and its `--dry-run` exemption);
  `conformance/test-hook-claims.py:281-301`. **The guard lets a dry run chained to a real deploy
  through, because its exemption reads the whole line, not each command.** Measured on the hook's own
  text at `6c98dd7`:
  - allowed (exit 0): `scripts/deploy_hosted_engine.sh --dry-run && scripts/deploy_hosted_engine.sh`.
    That is the runbook's step 1.5 (a dry run "first, then" the script) written on one line;
  - allowed (exit 0): `scripts/deploy_hosted_engine.sh --dry-run | scripts/deploy_hosted_engine.sh`;
  - blocked: `scripts/deploy_hosted_engine.sh --dry-run; fly deploy`, by the `fly` rule.

  #189 lists the guard's other holes but not this one. Also, `--mi` still has no left boundary:
  `git push origin fix--mi` is blocked. The second review's fix item 1 asked for `[[:space:]]--mi…`,
  and only the right side was anchored. **Failure scenario:** after `fly auth login`, an agent runs
  the runbook's two steps as one line. The guard passes it, and only the permission prompt stands
  before a deploy that D-185 clause 5 keeps for the owner. **Fix:**
  1. Judge each occurrence: block unless every `deploy_hosted_engine\.sh[^;&|]*` match is the script
     followed by exactly `--dry-run`.
  2. Add both measured spellings to `MUST_BLOCK`.
  3. Add them to #189.

  It is a hook change: its own commit, for the owner.
- **M2** `docs/security-invariants.md:183` (G-7), `:166-167` (INV-86, INV-87). **G-7 claims more than
  the guard does, and it cites only #142.** It says the guard blocks "an agent's deploy or destroy of
  the hosted engine". It says the guard does not see "a push set through `-c` or `git config`", and
  names nothing else. The second review's M2 fix item 4 ("Rewrite G-7 to list what the guard still
  passes") was not done. Since then, #189 records 14 or more spellings the guard passes. Measured
  still allowed at `6c98dd7`: `git push origin 'HEAD:main'`, `(git push -f origin y)`,
  `FLY_API_TOKEN=x fly deploy`, and M1's two. Also, INV-86 and INV-87 cite none of the tests added
  after the security review, and none of this seat's. So the list's own gate would not notice if one
  were removed. **Fix:**
  1. Make G-7 say the guard blocks the plain spellings only, and point to #189 for the rest. Its
     issue column becomes "#142, #189".
  2. Add `test_hosted_engine.py::test_the_hosted_stage_only_copies_and_points_at_its_artifact`,
     `::test_the_hosted_stage_builds_on_the_stage_that_runs_the_engine` and
     `test_deploy_hosted.py::test_the_build_context_holds_what_the_image_copies_and_no_secret` to
     INV-86.
  3. Add `test_public_artifact.py::test_a_left_out_row_the_deletes_miss_stops_the_derivation` and
     `::test_each_surface_whose_only_source_is_left_out_goes_dark_and_coding_keeps_epochs_board` to
     INV-87.
- **M3** `src/app/workflows/public.py:40-55`; INV-87 (`docs/security-invariants.md:167`). **The
  derivation's list of tables is still closed. The second review's M6 item 1 was done only in part,
  and the rest was not filed.** It asked for every table with a `source` column to be deleted from and
  checked. `ff940b9` added `pricing` to the survivor check, but `access` also has a `source` column
  (with `scores` and `pricing`, read from `PRAGMA table_info`). **Measured** on the seeded fixture: I
  planted an `access` row with `source = 'openrouter'` and
  `source_url = 'https://openrouter.ai/api/v1/models'`. `derive` returned without error, and the
  public file still holds the row. Nothing leaks today: the served artifact's `access` rows are all
  `epoch_access` (982). But INV-87 says the hosted artifact carries "no row … of a source left out",
  and the code holds that for two tables of three. **Failure scenario:** a refresh starts to record
  access from a left-out publisher (OpenRouter lists availability as well as prices). The next deploy
  ships those rows, and every test passes. **Fix:**
  1. Find the tables that have a `source` column from `sqlite_master` and `PRAGMA table_info`. Delete
     the left-out sources from each, and count survivors in each.
  2. Add a test that plants an `access` row. It fails today, which is why this seat records it and
     does not commit it.

  Or narrow INV-87 to scores and prices, and file the rest.

## Tests added/extended this review

Uncommitted in this seat's worktree, beside this record, for the author to commit unedited. Each one
has a comment that names this record and the fault it catches. In the order of the files:

- `tests/unit/test_public_artifact.py`:
  - `:169`, `test_a_left_out_row_the_deletes_miss_stops_the_derivation`, for `scores` and `pricing`.
    It proves the survivor check refuses a missed delete, writes nothing and leaves no workspace
    (#88, INV-87). It catches F2 and F6.
  - `:188`, `test_an_artifact_left_with_no_price_is_refused_and_nothing_is_written`. It catches F3 and
    F6.
  - `:201`, `test_a_priced_payload_must_say_which_price_sources_it_serves`. It proves R4 of the
    second review and catches C2.
  - `:219`, `test_the_adr_names_every_source_the_public_artifact_leaves_out`. It proves P3's "the
    licence table and the ruling are an ADR" and catches R1.
  - `:232`, `test_each_surface_whose_only_source_is_left_out_goes_dark_and_coding_keeps_epochs_board`.
    It proves P3's "each affected surface" and D-185's `coding` claim. It catches F11. It is not
    vacuous: each surface answers on the built artifact first.
  - `:273`, `test_the_adr_and_the_runbook_name_the_surfaces_that_go_dark`. It catches R4 and R5.
- `tests/unit/test_deploy_hosted.py`:
  - `:195`, `test_an_untracked_file_is_refused_before_anything_is_built`. It proves the script's step
    1 and catches D1.
  - `:208`, `test_a_derivation_that_cannot_run_stops_the_deploy_beside_an_older_artifact`, for a
    missing and an unreadable artifact. It catches D2 and D7.
  - `:233`, `test_the_image_is_built_on_flys_builder`. It proves the runbook's step 1.5 and catches D3.
  - `:241` and `:282`, `_dockerignore_keeps` and
    `test_the_build_context_holds_what_the_image_copies_and_no_secret`, 18 cases. They read
    `.dockerignore` as Docker does, the last matching rule winning (S14, the second review's M6 and
    its I3). They catch K6.
- `tests/unit/test_release_gates.py`:
  - `:85`, `test_a_cold_start_whose_journey_fails_fails`. It catches J1.
  - `:98`, `test_a_container_that_never_answers_fails_the_cold_start`. It catches J2.
  - `:111`, `test_the_journey_refuses_an_empty_url`. It catches J4.
- `tests/unit/test_hosted_engine.py`:
  - `:144`, `test_the_hosted_stage_builds_on_the_stage_that_runs_the_engine`. It proves INV-86's
    premise and catches K1.
  - `:155`, `test_fly_reaches_the_port_the_engine_listens_on`. It catches K5 and K7.
  - `:167`, `test_one_machine_is_always_up`. It proves D-185 clause 1 and catches K4.
  - `:175`, `test_the_images_own_health_check_asks_by_the_deployments_host`. It runs the HEALTHCHECK
    against a stand-in `urlopen` and catches K3.
- `tests/unit/test_testflight_ready.py:134`,
  `test_no_target_setting_overrides_what_the_engine_config_or_the_local_file_sets`. It proves D-185
  clause 4 against the project file and catches X1 and X2.
- `tests/unit/test_security_surface.py`:
  - `:225`, `test_no_tracked_file_names_a_mac_or_home_address_beyond_the_placeholders`. It proves #147
    (P1) and catches R3. It is red on four of the wave's commits (above).
  - `:243`, `test_the_network_name_scan_reads_each_spelling`. Its planted values are written in two
    pieces, so the tree scan does not find them.

*Filled by: Tester seat (independent) · Date: 2026-10-07 · Commit range: `6c9ce17..6c98dd7`*
