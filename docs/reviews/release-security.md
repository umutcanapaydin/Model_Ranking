---
record_type: review
id: release-security
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# Release Security Review: the first release (the engine on Fly.io, the app on TestFlight)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), Stage 5.1
**Independent:** yes. I wrote none of this release's code, tests, records or earlier reviews.
**Date:** 2026-10-07
**Release range:** `3426ff3..81af5ba`. `3426ff3` is `main` (the merge of #184), which already holds
M19's W1, W2 and W3. `81af5ba` is the head of the M19 closure branch (`enhancement/m19-closure`). It
carries W4 (#196, head `bd60265`) and W5 (#197, head `2d117d0`), both draft pull requests, and the
closure's own commits. That is 83 commits, 74 of them not merges.
**Risk tier:** HIGH (W5, `docs/plans/m19-plan.md` §2: the serving image, the launcher, the guard and a
public surface).

> **What this record is.** The release's verdict of record, in the file the release rules name
> (`AGENTS.md:114`, `docs/closure-checklist.md:111`, `permission-matrix.md:90`). This closes the M19
> repo review's M7. It builds on two earlier records and does not redo them:
> - `docs/reviews/m19-closure-security-review.md`: the release's first Stage 5.1 review, on
>   `0198eb3..7fde40d`. Verdict MAJOR, findings S1 to S16.
> - `docs/reviews/m19-release-security-reread.md`: its re-read, on `7fde40d..6c98dd7`. Verdict MINOR,
>   findings N1 to N8. It said yes to the deploy, on one condition: any later change to the release
>   surface needs the same short read.
>
> The M19 repo review (`docs/reviews/m19-repo-review.md`, M2) found that condition unmet: `0a80b65`,
> `fdf6701` and `fb2040d` changed the surface after `6c98dd7`, and no seat read them. **This record is
> that read**, for everything in `6c98dd7..81af5ba` (23 commits, 6 merges). It also confirms where
> each earlier finding stands at `81af5ba`.
>
> Nothing has been deployed. The only repository file I write is this one, and I do not commit it.

## Verdict
MINOR

## Summary

Nothing is BLOCKING. I found **2 MINOR** (RS1, RS2) and **3 INFO** (RS3 to RS5).

- **What changed since the re-read holds.** The public artifact now drops the `access` rows of a
  left-out source as well. The build context leaves out database files. The runbook now says what
  Fly can and cannot do, and it names this file as the condition for the deploy. Two new tests read
  the image's health check and the build context the way Docker reads them. W4's reading fixes still
  end in a surface id the engine serves, so no new request path exists.
- **RS1 (MINOR).** The guard change `fb2040d`, which the owner approves by merging, reopens four
  spellings of `git push --mirror` that were blocked at `6c98dd7`. Its new count of `--dry-run` runs
  can still be fooled by a mention in a comment or an `echo`. I checked a two-regex fix in memory: it
  closes all seven spellings and passes all 45 conformance cases.
- **RS2 (MINOR).** INV-86 says the hosted engine runs as non-root and cannot write its artifact. The
  test holds this only as the Dockerfile's text spells it today. `user root` in lower case, `USER 00`,
  and a lower-case `run chmod 666` each pass the full suite. Docker accepts instructions in any case.
  The shipped Dockerfile is correct.
- **Every earlier finding is fixed, filed or left with the owner** (the table below). S1, the earlier
  MAJOR, still holds fixed, and a new test now also refuses an address set on the app target itself.
- **Gates at `81af5ba`, all green:** `make check-fast`, `make secrets`, `make deps`, `make slopsquat`
  and `conformance/test-hook-claims.py`. This is the first seat to run `make deps` and
  `make slopsquat` on the release.

## Findings

### BLOCKING

None.

The permission matrix §11 human-review trigger does not fire. No auth, PII, payment or migration path
is in the range. The hosted engine still receives only a surface id and a budget (INV-64), and no
route mutates (INV-30, measured below). The deploy surfaces (`Dockerfile`, `fly.toml`,
`.claude/settings.json`) are the owner's to review under K.10 and AGENTS.md §3. He reviews them when
he merges #197 and the closure pull request.

### MINOR

**RS1 (MINOR): `fb2040d` reopens four spellings of `git push --mirror`, and its dry-run count can be
fooled by a mention of the flag.**

- **Where.** `.claude/settings.json:49`, the Bash guard. `fb2040d` ("OWNER APPROVAL") changed two
  rules:
  - The `--mirror` rule now needs whitespace right before `--mi`. This was so that a branch named
    `fix--mi` is not read as a mirror push.
  - The deploy rule now counts runs of the script against runs of `deploy_hosted_engine.sh --dry-run`.
    Before, the whole line was exempt if it held a dry run.
- **Measured.** I ran the hook's own command from each commit on JSON payloads with `/bin/sh`, as
  Claude Code does. Exit 2 means blocked; exit 0 means allowed.

  | Payload | `6c98dd7` | `81af5ba` |
  |---|---|---|
  | `git push origin \--mirror` | blocked | **allowed** |
  | `git push origin $'--mirror'` | blocked | **allowed** |
  | `git push origin ''--mirror` | blocked | **allowed** |
  | `git push origin ""--mirror` | blocked | **allowed** |
  | `git push origin fix--mi` (the false positive it fixes) | blocked | allowed |
  | `scripts/deploy_hosted_engine.sh --dry-run && scripts/deploy_hosted_engine.sh` | allowed | **blocked** |
  | the same with `\|`, `;`, a newline or `; bash …` | allowed | **blocked** |
  | `scripts/deploy_hosted_engine.sh # deploy_hosted_engine.sh --dry-run` | allowed | allowed |
  | `scripts/deploy_hosted_engine.sh; echo deploy_hosted_engine.sh --dry-run` | allowed | allowed |
  | `echo deploy_hosted_engine.sh --dry-run; scripts/deploy_hosted_engine.sh` | allowed | allowed |

  The shell turns each of the first four into `--mirror` before git sees it.
  - The last three run a real deploy with no argument, because the script refuses any argument except
    exactly `--dry-run` (`scripts/deploy_hosted_engine.sh:28-32`). They passed before `fb2040d` too.
    The dry-run count matches the flag anywhere on the line, not only where a run of the script begins.
  - So the commit message's claim, that every run must be "exactly `--dry-run`", is wider than the
    rule.
- **A fix, checked in memory.** I made the two changes below to the hook's text in a Python string,
  never in the file. The result kept all 45 cases in `conformance/test-hook-claims.py` (27 blocked,
  18 allowed). It blocked all seven spellings above and still allowed `fix--mi`, `wave/m19--minor`,
  `scripts/deploy_hosted_engine.sh --dry-run` and `bash scripts/deploy_hosted_engine.sh --dry-run`.
  1. Bound `--mi` by "not after a letter or digit", not by "after whitespace": `(^|[^[:alnum:]])--mi…`.
  2. Count a dry run only where a run of the script begins. Give the `--dry-run` count the same prefix
     as the run count, `(^|[;&|][[:space:]]*)((bash|sh|zsh|env)[[:space:]]+)?([^[:space:];&|]*/)?`.

  Add the seven spellings to the conformance lists.
- **Why MINOR.** The guard is a best effort over text, and G-7 says so (`docs/security-invariants.md:183`,
  #189).
  - `main` is held on GitHub. I read it with `gh`: `enforce_admins` is on, force pushes and deletions
    are off, and reviews are required. A mirror push can rewrite only branches that are not protected.
    No wave branch has a rule (N6, #190).
  - `\+x` and `''+x` already pass for force pushes. #189 lists those.
  - The guard did not load in any M19 session (`docs/control-events.csv`, row `repository-hooks`).
  - A deploy through a hole also needs the owner's Fly login on the Mac (N1).
  - Still, this is a guard that got weaker on the release surface, at the exact commit the owner
    approves by merging. He should know before he merges #197.
- **Disposition (the owner's: a hook change, AGENTS.md §3).** Either the two regex changes above, with
  their conformance cases, in the closure pull request for his approval, or a comment on #189 that
  adds these seven spellings.

**RS2 (MINOR): INV-86's two promises, a non-root engine and an artifact it cannot write, are held only
as the Dockerfile's text spells them. A lower-case instruction or a numeric root passes every gate.**

- **Where.** `tests/unit/test_hosted_engine.py:116-118` (`_user`), `:129`, `:130` and `:139`.
  - They match `USER`, `COPY ` and `RUN ` only in upper case.
  - They refuse a user only when its name, before any `:`, is the literal `root` or `0`.
  - The re-read's N3 fix (`0a80b65`) added the `:` split.
- **Measured.** Each mutant ran against the cited tests, then against the full Python suite inside
  `scripts/offline.sb` (2171 passed, 25 skipped each time):
  - K8: `user root` appended to the `hosted` stage. **Survived.** The public engine would run as root.
  - K7: `USER 00` appended to the `hosted` stage. **Survived.** Docker's reference: "Numeric IDs don't
    require this lookup", so `00` is uid 0. I did not build the image to confirm it.
  - K10: `user root`, `run chmod 666 /srv/advisor.db`, `user appuser` appended. **Survived.** The engine
    is non-root but can now write the file it serves.
  - Docker's reference (docs.docker.com/reference/dockerfile, read for this seat): "The instruction is
    not case-sensitive."
  - Upper-case `USER root:root` (K5), `USER 0:0` (K6), and a lower-case `copy --chown` (K9) were killed.
- **Why MINOR.** Each one needs a change to the Dockerfile. The shipped file is right:
  - `Dockerfile:46-47` creates `appuser` and switches to it.
  - `:65-67` has the hosted stage copy the artifact as root, with no `--chown`, and run nothing.
  - `public.py:101` makes the file 0644.

  It is the same class as N3, which the re-read rated MINOR.
- **Fix (tests only; it belongs in the closure pull request, or file it).**
  - Read every instruction case-insensitively.
  - Refuse a user whose name is `root`, whose part before `:` is all digits and equals 0, or that holds
    `$`.
  - Refuse `RUN` and `COPY --chown`/`--chmod` in the `hosted` stage in any case.
  - INV-86's row needs no new wording.

### INFO (checked; no action unless stated)

**RS3: the `access` third of the survivor check has no test of its own (P9).**
- The check is `src/app/workflows/public.py:58`. If I make it a no-op, the full suite still passes.
- The `access` DELETE that it double-checks is held: P8, the DELETE removed, is killed by
  `tests/unit/test_public_artifact.py:312`.
- This is defence in depth, the same class as the re-read's N4.
- The survivor check also names its three tables by hand. Measured on the real artifact, only `scores`,
  `pricing` and `access` have a `source` column. `plan_models` and `plans` are emptied whole.
- If a table is added later, building the survivor query from `sqlite_master` at run time would cover
  it without a list to keep.

**RS4: the runbook is safe to follow as written.** I read `docs/release-testflight.md` at `81af5ba`
step by step:
- **Step 1.1** reinstalls the Mac's service. The reinstall keeps the home-network mode it finds
  (INV-28). Then the owner waits a night for a refresh. So the Fly login (step 1.2) comes after the
  wait, and the token sits on disk only around the deploy.
- **Steps 1.3 and 3** send a rename, or the fallback to a TCP check, through a pull request. A by-hand
  `fly deploy` would skip the build stamp, and production refuses to boot without it.
- **Step 1.4** publishes the container on `127.0.0.1` only (R4, first review).
- **Step 1.5** runs `--dry-run` first, then the real deploy. Each is its own command.
- **Lines 44-49** say there is no billing cap, and to run `fly auth logout` after each deploy.
- **Step 2.1** says a local `ENGINE_URL` reaches Debug only, and that holds (S1, below).
- **Step 2.3** has the owner read back `EngineURL` from the signed archive before upload.

Two small gaps, neither a hole:
- **S10's advice is written nowhere the owner reads.** Never destroy the Fly app while TestFlight builds
  are installed, or anyone can claim the name and answer every installed build. One line in §3 of the
  runbook would carry it.
- **#187's body still asks for a billing alert.** A comment corrects it, but bodies are live documents
  (`.agents/rules/practices.md:193`).

**RS5: the closure's records on the release path.**
- `docs/closure-checklist.md:111` and `:124` now let a MINOR verdict, with each finding fixed or filed,
  proceed to Stage 5.2. That matches the profile (`.claude/agents/Security-Reviewer.md:132`), so it
  does not weaken the gate.
- The runbook's precondition (`docs/release-testflight.md:12-14`) names this file.
- `docs/control-events.csv` now records the skipped `make cold-start`, `make journey` and signed
  archive, and the sessions that ran without hooks.
- Not security: the profile does not itself say "each fixed or filed", although the checklist cites it
  for that.

### PASS (observations)

- **`fdf6701` closes the W5 Tester's M3.** `access` rows of a left-out source are deleted
  (`public.py:45`), and the survivor check reads all three tables (`:55-59`, `:89-91`). On the real
  artifact, no table with a `source` column holds a left-out source, and no byte of one is in the file
  (below).
- **`0a80b65` keeps database files under `src/` out of the build context.** It adds `**/*.db` and
  `**/*.sqlite*` (`.dockerignore:15-16`), and the hosted artifact is still re-included last (`:17`).
  I6, the line dropped, is killed. I7, `!src/**` appended to bring secrets back, is killed by the new
  test, which reads the list the way Docker does (`tests/unit/test_deploy_hosted.py:283`).
- **The Tester's new deploy tests hold real gaps.**
  - An untracked file stops the deploy (`:196`). D11, `--untracked-files=no`, is killed.
  - A failed derivation never ships an older artifact (`:209`).
  - The build runs on Fly's builder (`:234`).
- **`tests/unit/test_hosted_engine.py:176` runs the image's own `HEALTHCHECK` code** against a
  stand-in `urlopen`, and checks that it asks with the deployment's Host.
- **`tests/unit/test_testflight_ready.py:134` refuses an `ENGINE_URL` set on the app target.** That is
  an override the xcconfig tests could not see. X10, an `ENGINE_URL[sdk=iphoneos*]` planted in the
  Release target configuration, is killed.
- **`tests/unit/test_journey.py:78`** runs the Stage 5.2 journey in process on a derived public
  artifact. This closes the repo review's M16.
- **W4's three later fixes** (`d324669`, `3697d64`, `b38819b`; `Reading.swift`, `Router.swift`) narrow
  the image rule back to `vision`. They add no request path. The outcome is still the tier's surface
  id or the unmeasured fallback, and `client-decls` passes in all four build configurations.
- **No secret is in the range, and no dependency changed in it.** `pyproject.toml` and
  `requirements/` are unchanged in `3426ff3..81af5ba`.

## The change since the re-read, read (`6c98dd7..81af5ba`, on the re-read's surface list)

| Where | Commit | Judgement |
|---|---|---|
| `.claude/settings.json:49` (Bash guard) | `fb2040d` | Tighter on chained deploys, looser on four `--mirror` spellings (RS1) |
| `conformance/test-hook-claims.py` | `73a8624` | Adds the two chained deploys to the blocked list and `fix--mi` to the allowed list. G5 and G6 (each half of `fb2040d` reverted) are killed |
| `.dockerignore:15-16` | `0a80b65` | Tighter (PASS) |
| `Dockerfile:1-2`, `fly.toml:1-2` | `47da19a` | Comments only. They now point at AGENTS.md §5, not at an empty CODEOWNERS file |
| `src/app/workflows/public.py` | `fdf6701` | Tighter (PASS); RS3 |
| `scripts/deploy_hosted_engine.sh`, `scripts/engine_service.sh`, `ios/Config/` | none | Unchanged since `6c98dd7` |
| `ios/ModelRanking/Engine/{Reading,Router}.swift` | W4 fixes | Reading rules only; no request path (PASS) |
| `docs/release-testflight.md` | `0a80b65`, `47da19a` | Safe to follow (RS4) |
| `docs/security-invariants.md` | `0a80b65`, `fdf6701`, `fb2040d` | INV-86 and INV-87 cite the new tests. G-7 says "best effort" and cites #189. RS2 is a gap INV-86's tests do not see |
| `tests/` (eight files) | several | Each adds checks. No Python test was skipped. The one assert replaced (`test_hosted_engine.py:129`) is stronger. The Swift test changes follow W4's narrower image rule. The one new `exec` runs the image's health-check code in a test (`:176`), outside INV-1's `src/` and `scripts/` |
| `docs/closure-checklist.md`, `AGENTS.md`, `README.md`, `docs/control-events.csv` | `47da19a` | RS5 |

## The earlier findings, at `81af5ba`

| Finding | State | Evidence |
|---|---|---|
| S1 (MAJOR) | **Fixed**, holds | `ios/Config/Engine.xcconfig:12`, `:17`, unchanged in the range. `test_testflight_ready.py:92`, `:115`, `:134` (X10 killed). Runbook readback, `docs/release-testflight.md:71-75` |
| S2 | **Filed**, #188 (open) | The budget argument |
| S3 | **Filed**, #187 (open) | No rate limit. The runbook states there is no cap (`:44-46`) |
| S4 | **Fixed** | INV-86 and INV-87 rows (`docs/security-invariants.md:166-167`). D2 to D4, P4 and P5 killed (re-read). RS2 is a narrower remainder |
| S5 | **Narrowed**, #142 and #189 (open) | `main` is held on GitHub (read). RS1 |
| S6 | **Partly fixed**, #189 and #190 (open) | Plain `fly deploy`/`destroy` blocked. Runbook logout habit (`:48-49`) |
| S7 | **Fixed** | `scripts/deploy_hosted_engine.sh:42-46`, unchanged. `test_deploy_hosted.py:180` |
| S8 | Holds | Re-measured below |
| S9 | **Fixed** | `openrouter` is in no answer and in no byte of the file (below) |
| S10 | **Left with the owner** | Not written in the runbook (RS4) |
| S11 | Holds | No `FORWARDED_ALLOW_IPS` and no proxy-header setting in `Dockerfile`, `fly.toml`, `scripts/` or `src/` (grep) |
| S12 | **Closed** | W4: review of record MINOR (`c372e23`), Tester MINOR (`0bd4353`). W5: review MINOR, Tester MINOR (`ab0a8f3`). The short read it asked for is this record |
| S13 | **Fixed** | `--ha=false`, `scripts/deploy_hosted_engine.sh:62`. `test_deploy_hosted.py:115` |
| S14 | **Fixed** | `.dockerignore:10-16`; I4 and I6 killed |
| S15 | **Closed** | `make deps` and `make slopsquat` green at `81af5ba` (this seat) |
| S16 | Carried | G-1 #172; G-2 #171, #173; CI's half of #122; #81; M18's S13 (a Debug build on the owner's phone) |
| N1 | **Left with the owner**, #190 (open) | The `make …:*` allow entries are unchanged (`.claude/settings.json:14-19`). `make lint PY='fly apps destroy … #'` still passes the guard (measured). Runbook logout habit |
| N2 | **Fixed** | Runbook `:44-46`. #187 has a correcting comment (RS4) |
| N3 | **Fixed** | `test_hosted_engine.py:129`; K5 and K6 killed. RS2 is what is left |
| N4 | **Fixed** | P6 killed by `test_public_artifact.py:166` and `:194[pricing]`. A4 killed by `:181`, `:226` |
| N5 | **Fixed** | `docs/security-invariants.md:183` |
| N6 | **Left with the owner**, #190 | GitHub rules for `wave/m19-w5`: 0 (read) |
| N7 | **Fixed** | Runbook step 1.3 (`:28-32`) |
| N8 | **Narrowed** | `*.db` and `*.sqlite*` are left out. Other ignored files under `src/` (`notes/`, `*.local.md`) still reach Fly's builder, never the image |
| Repo review M2 | **Closed by this record** | — |
| Repo review M3 | **Filed**, #198; runbook step 1.1 (`:18-23`) | The stamp names the code and the data's digest, not the release that built the data |
| Repo review M4 | **Fixed** | The fallback goes through a pull request (`:87-92`). Step 1.3 is ordered. The runbook is listed in `README.md` |
| Repo review M7 | **Closed by this record** | — |

## What goes public, measured at `81af5ba`

- **The served artifact** (the worktree's copy) was only read. Its sha256 was `dac97873…9344` before
  and after.
- **The public artifact** was derived into my scratch folder with `public.derive`, inside
  `scripts/offline.sb`.
  - Removed: 815 score rows, 439 OpenRouter prices, 456 `openrouter/` alias prices, 40 plan links and
    10 plans. There were 0 `access` rows of a left-out source to remove.
  - The file: 6,524,928 bytes, mode 0644, journal `delete`, freelist 0.
  - Tables with a `source` column: `scores` (no left-out source), `pricing` (`litellm` only) and
    `access` (`epoch_access` only).
  - None of these is in the file's bytes, in any case: each `LEFT_OUT` id, `arc-agi`, `arc prize`,
    `deepswe`, `terminalbench`, `terminal-bench`, `webdev arena`, `mmlu`, `openrouter`, `/users/`,
    `.local`, `192.168`, `swebench.com`, `arcprize`.
- **Served in process** in the hosted configuration: `APP_ENV=production`, Host list
  `model-ranking.fly.dev`, bind `0.0.0.0`, a build stamp, and no CORS list.
  - `/health` answers 200 with only `build`, `evidence`, `refresh` (`off`), `status` and `version`.
  - Any other Host gets 400, loopback included.
  - POST, PUT, DELETE and PATCH get 405.
  - The routes are exactly the five declared GETs.
  - `/v1/boards` is 502,108 bytes without gzip. A cross-origin request gets no CORS header. Every
    response carries `nosniff`.
  - All 14 tasks × 3 budgets answer 200. No answer names OpenRouter, a left-out source id, a local
    path or a LAN address.
  - A 5,000-character budget gets a 156-byte 400.

## Mutants

Each mutant was one exact, single-match edit. The method:
1. Save the file's bytes and sha256.
2. Run the cited tests inside `scripts/offline.sb`, with no coverage floor.
3. Run every survivor again against the full Python suite.
4. Restore the bytes in a `finally` and assert the sha256.

Every restore matched, and `git status --porcelain` was empty after each batch. My first run of G5 used
the system Python 3.9, which cannot import the conformance library. That result was void, and I re-ran
G5 and G6 under Python 3.14.

| # | The edit | Result | Killed by |
|---|---|---|---|
| K5 | `USER appuser` → `USER root:root` | KILLED | `test_hosted_engine.py::test_the_hosted_engine_runs_as_no_root_and_cannot_write_its_artifact` |
| K6 | `USER 0:0` after the hosted stage's `ENV` | KILLED | same |
| K7 | `USER 00` after the hosted stage's `ENV` | **SURVIVED** (full suite) | none (RS2) |
| K8 | `user root` after the hosted stage's `ENV` | **SURVIVED** (full suite) | none (RS2) |
| K9 | the hosted `COPY` → `copy --chown=10001 …` | KILLED | `::test_the_hosted_image_carries_the_artifact_the_deployment_serves`, and the no-root test |
| K10 | `user root`, `run chmod 666 /srv/advisor.db`, `user appuser` | **SURVIVED** (full suite) | none (RS2) |
| P6 | the pricing third of `_SURVIVORS` made a no-op | KILLED | `test_public_artifact.py::test_a_left_out_price_that_survives_stops_the_derivation` |
| P8 | the `access` DELETE removed | KILLED | `::test_no_table_keeps_a_row_of_a_left_out_source` |
| P9 | the `access` third of `_SURVIVORS` made a no-op | **SURVIVED** (full suite) | none (RS3) |
| A4 | `pricing_sources` defaults to `None` | KILLED | `::test_a_priced_credit_must_say_which_prices_it_serves` |
| I6 | `**/*.db` dropped from `.dockerignore` | KILLED | `test_deploy_hosted.py::test_the_build_context_leaves_out_what_git_ignores_under_src` |
| I7 | `!src/**` appended to `.dockerignore` | KILLED | `::test_the_build_context_holds_what_the_image_copies_and_no_secret` |
| D11 | `git status --porcelain --untracked-files=no` | KILLED | `::test_an_untracked_file_is_refused_before_anything_is_built` |
| X10 | `ENGINE_URL[sdk=iphoneos*]` set on the app target's Release configuration | KILLED | `test_testflight_ready.py::test_no_target_setting_overrides_what_the_engine_config_or_the_local_file_sets` |
| G5 | the guard's `--mi` bound reverted | KILLED | `conformance/test-hook-claims.py` (`fix--mi` blocked) |
| G6 | the guard's dry-run count reverted to the whole-line exemption | KILLED | same (the chained deploys allowed) |

**Score:** 16 mutants, 12 killed, 4 survived. Each survivor is in a finding.

## Gates passed

- [x] Secret scan green. `make secrets` on the tree: no leaks. `gitleaks detect --log-opts` on
  `3426ff3..81af5ba` and on `6c98dd7..81af5ba`, and the range's diff through `gitleaks stdin`: no
  leaks. A random `ghp_` token fires, so the scan is live.
- [x] `make deps` (pip-audit over all four locks): "No known vulnerabilities found".
- [x] `make slopsquat`: 20 declared dependencies, 0 suspect. No dependency changed in the range.
- [x] Default deny preserved for new external surfaces. No new route. Host list, HTTPS and the boot
  refusal hold (INV-86 and measured).
- [x] Permission matrix not violated by the code. §3 (cloud services) rests on the owner's habit and
  the guard's best effort (N1, RS1). The owner holds the decision.
- [x] Prompt-injection hygiene. The engine has no model (INV-77). The phone's reading ends in a closed
  set of surface ids (INV-69, INV-70).
- [x] Auth and PII: the §11 trigger does not fire (above).
- [x] SAST stand-in. `ruff check --select S,BLE src scripts`: 18, the same 18 as both earlier seats.
  bandit and semgrep are not installed.
- [x] `make check-fast` at `81af5ba`, with the stand-ins first on `PATH`: all six legs PASS.
  - pytest: 2171 passed, 25 skipped.
  - `swift-test`: 496 tests, exactly the manifest.
  - `client-decls`: 19 files in 4 configurations.
  - The records leg ran conformance.
- [x] `python3 conformance/test-hook-claims.py`: PASS, 2 claims, 18 legs, 0 unbacked.

## Acceptance criteria evidence (file:line)

- **D-185 cl. 1 / #94** (fails closed, one Host, the health check names it):
  `tests/unit/test_hosted_engine.py:64`, `:71`, `:92`, `:156`, `:176`.
- **INV-86** (non-root, cannot write its artifact): `tests/unit/test_hosted_engine.py:121`, `:134`,
  `:145`, with RS2's gap.
- **D-185 cl. 3 / #88 / INV-87** (the public artifact): `tests/unit/test_public_artifact.py:33`, `:89`,
  `:122`, `:138`, `:166`, `:194`, `:257`, `:312`, and the measurement above.
- **D-185 cl. 4** (a Release build reaches HTTPS): `tests/unit/test_testflight_ready.py:77`, `:92`,
  `:102`, `:115`, `:134`.
- **D-185 cl. 5 and S7** (the owner deploys `main`'s tip only, stamped, checked):
  - `tests/unit/test_deploy_hosted.py:64`, `:80`, `:86`, `:171`, `:180`, `:196`, `:209`;
  - `.claude/settings.json:49`, with RS1.
- **Build context:** `tests/unit/test_deploy_hosted.py:104`, `:161`, `:283`.
- **Stage 5.2 gates:** `tests/unit/test_release_gates.py:52`, `:86`, `:99`, `:112`;
  `tests/unit/test_journey.py:78`, `:84`.

## Risks queued

- **RS1** for the owner: the two regex changes, or a comment on #189.
- **RS2**: tests only. Fix it in the closure pull request, or file it.
- **RS3 and RS4**: small follow-ups. The S10 line in the runbook; #187's body.
- **Open and filed:**
  - #187: rate limit and cost. This is the real control before external testers.
  - #188: the budget argument.
  - #189: guard spellings.
  - #190: allow list and wave rules, the owner's.
  - #198: which release built the data.
  - #142: the guard loads only in a session started in the repository.
  - #172, #171, #173: G-1 and G-2.
  - #122: CI's child processes.
  - #81: CI workflows.

## Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| Image build, `make cold-start`, a container run | Docker is off limits to this seat | The Dockerfile was read and mutated as text. K7's uid reading rests on Docker's reference, not on a built image. Runbook step 1.4 has the owner run `make cold-start` |
| `fly`, the deploy, a probe of `model-ranking.fly.dev` | Out of bounds | Fly's behaviour as the earlier seats read it in Fly's documentation |
| `xcodebuild`, a signed archive | Stubbed | The owner's `plutil` readback (runbook step 2.3) is the check of record |
| `make ui-test` | Needs the simulator | W4's UI fix (`bd60265`) is test-only. No screen ran |
| The guard in a live Claude Code session | It would mean running the payloads | Judged by running the hook's command on JSON, as Claude Code invokes it |

**Network.** I made only these calls:
- `gh` reads: issues #81, #122, #142, #171 to #173, #187 to #190, #198, #202; PRs #196 and #197;
  branch protection and branch rules.
- `make deps` and `make slopsquat`, which query PyPI's public metadata, as the dispatch asked.
- Docker's Dockerfile reference page.

No product upstream was contacted. Every test ran inside `scripts/offline.sb`. No process of mine is
still running, and none ended in SIGABRT.

## May the owner deploy to Fly.io and upload to TestFlight once the release's pull requests are merged and the owner's account steps are done?

**Yes.** Nothing in the release is BLOCKING. Every earlier finding is fixed, filed or left with the
owner by name. The verdict of record is MINOR, which the release rules accept.

The conditions:
1. **Merge first, then deploy.** Merge #196 (W4), #197 (W5) and the M19 closure pull request. Then
   follow `docs/release-testflight.md` in order. The deploy script ships only the tip of `origin/main`.
   This read covers the release surface as it is at `81af5ba`. If anything on that surface changes
   before the merge, the change needs the same short read. There are two exceptions: RS1's two regex
   changes (checked in memory here) and test-only fixes for RS2 do not need one.
2. **Before merging #197,** the owner should know that `fb2040d` reopens four `--mirror` spellings
   (RS1). Taking the fix or leaving it under #189 is his call. Either way it does not block the deploy.
3. **Keep the habits from the re-read** until #190 and #187 are done:
   - run `fly auth logout` after each deploy;
   - Fly has no billing alert or cap, so look at the usage page while people are testing;
   - `fly scale count 0` stops the engine, and its cost, at once.
4. **TestFlight.**
   - Archive only after the deploy script has succeeded. Its `/health` check proves that he holds
     `model-ranking.fly.dev`.
   - Run the runbook's `plutil` readback (step 2.3) on his own signed archive before uploading. It must
     say `https://model-ranking.fly.dev`.
   - Never destroy the Fly app while TestFlight builds are installed (S10).
5. **Before external testers** (Beta App Review), treat #187, a rate limit, as the cost control that
   is still owed.
