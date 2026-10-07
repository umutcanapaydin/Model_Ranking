---
record_type: review
id: m19-release-security-reread
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19 release: the short security re-read before the deploy (S12)

> **Independent seat.** The M19 closure and Stage 5.1 security review
> (`docs/reviews/m19-closure-security-review.md`, MAJOR, S1 to S16) asked for this read in its S12:
> fixes made after it changed the release surface, so the release owes a short security read of
> that change before anything is deployed. I wrote none of this code and did not sit in that review
> or in either W5 code review. I followed the Stage 5.1 profile (`.claude/agents/Security-Reviewer.md`,
> read from `origin/main`), narrowed to the change, and I write this file under the name the dispatch
> gave.
>
> **The change I read.** The review was committed at `0b2ed00`, but it measured `7fde40d`. Two
> commits between them (`92dd862`, `dea39c8`, the first W5 review's fixes) already changed the
> release surface, so I read `7fde40d..6c98dd7` on that surface: `Dockerfile`, `fly.toml`,
> `.dockerignore`, `scripts/deploy_hosted_engine.sh`, `src/app/workflows/{public,rank,recommend,standings}.py`,
> `ios/Config`, the Xcode project and scheme, the privacy manifest, `.claude/settings.json`,
> `docs/security-invariants.md`, `docs/release-testflight.md` and `docs/decisions.md`. The fix
> commits are `dea39c8`, `60735c9`, `d385074`, `ff940b9` and `0b8ae4a`. W4's fixes in the same range
> change only how the phone reads a question (`Router.swift`, `Reading.swift`); I checked that they
> add no path to a request. No lock or `pyproject.toml` changes in the range.
>
> Nothing has been deployed. Docker was not running. The only repository file I write is this one,
> and it is not committed.

## Verdict

**Independent:** yes.

**Verdict:** MINOR

Nothing is BLOCKING. There are **3 MINOR** findings (N1 to N3) and **5 INFO** notes (N4 to N8).
Every fix the review asked for before the deploy holds, and nothing new opens a hole in what goes
public.

**May the owner deploy the engine to Fly.io and upload to TestFlight, once his account steps are
done? Yes.** Three conditions and habits come with that yes:
- **When.** The deploy script ships only the tip of `origin/main`. So the deploy happens after W4
  and W5 have closed and merged. W4's re-review was BLOCKING, and its fixes have no confirming seat
  yet; neither wave has a Tester record. This read covers the release surface as it is at
  `6c98dd7`. If anything on that surface changes before the merge, that change needs the same
  short read.
- **Two habits on the Mac, until N1 and N2 are fixed.**
  - Run `fly auth logout` after each deploy (N1). While the Mac holds a Fly login, an agent session
    in the repository can run `fly` with no permission prompt.
  - Fly has no billing alerts and no spending cap (N2). The runbook's "set a billing alert" step
    cannot be done. Check the usage in the Fly dashboard while people are testing.
    `fly scale count 0` stops the engine, and its cost, at once.
- **TestFlight.** Archive only after the deploy has succeeded: the script's `/health` check proves
  that he holds `model-ranking.fly.dev` (S10). Then do the runbook's `plutil` readback (step 2.3)
  on his own archive before uploading. That readback is the check of record for S1 on his Mac.

## The earlier findings, on `6c98dd7`

- **S1: fixed.** The Release address now comes after the local file
  (`ios/Config/Engine.xcconfig:12` and `:17`), so a later, matching assignment wins for Release.
  Two tests hold it: `tests/unit/test_testflight_ready.py:92` (the Release line follows the
  include) and `:115` (nothing assigns `ENGINE_URL` or includes a file after it). I planted an
  `[sdk=iphoneos*]` http line, a second include, and the old order; each was killed (X5 to X7).
  `docs/owner-iphone.md` now writes the home address for Debug only. The runbook has the archive
  readback (`docs/release-testflight.md:63-65`). The author's unsigned Release archive (scratchpad
  `w5.xcarchive`, 03:30) has `EngineURL` = `https://model-ranking.fly.dev`, and its ATS block has
  only `NSAllowsLocalNetworking`. The only address string in its binary is the loopback fallback
  `http://127.0.0.1:8080`, with no Mac name and no LAN address. The shared scheme now archives the
  app in Release (`:102`; X8 and X9 killed).
- **S4: fixed**, with one narrow test gap (N3). INV-86 and INV-87 are rows with tests
  (`docs/security-invariants.md:166-167`). G-8 is closed, and the #94 paragraph is rewritten. I
  re-ran the review's five survivors on this head, and the cited tests now kill each one: D2
  (`USER root`), D3 (no `USER`), D4 (`--chown`), P4 (no `VACUUM`) and P5 (mode 0o666).
- **S5: narrowed, not fixed** (#189, #142 open). Measured on the guard's own command, now blocked:
  `--mi`/`--mirr`, a quoted `-f` or `+x`, `refs/heads/main`, and a continued line. Measured, still
  allowed (exit 0):
  - quoted main refspecs: `'HEAD:main'`, `"x:main"`, `"wave/x:refs/heads/main"`;
  - `\+x` and `''+x`;
  - `(git push -f …)` and `$(…)`;
  - a CRLF continued line;
  - `-c remote.origin.mirror=true`;
  - `--delete`, `-d` and `:x`.

  `main` is held on GitHub (read with `gh`): `enforce_admins` on, force pushes and deletions off,
  reviews required. Wave branches are not held there (N6).
- **S6: partly fixed** (#189 open), and weaker than both earlier records say (N1).
  - Blocked: `fly … deploy` and `fly … destroy` where a command starts, and the deploy script
    without `--dry-run`. The script itself now refuses any argument but exactly `--dry-run`
    (`scripts/deploy_hosted_engine.sh:28-32`; D8 and D9 killed).
  - Measured, still allowed:
    - `env`, `command`, `time` or `nohup` before `fly deploy`, and `FLY_API_TOKEN=x fly deploy`;
    - `(…)`, `$(…)` and `bash -c`;
    - `fly launch`, `secrets set`, `scale count 0`, `machine stop` and `machine update`,
      `ssh console`, and `apps create`;
    - `MODEL_RANKING_SERVED=… scripts/deploy_hosted_engine.sh`, `bash -x …` and `source …`.
  - No `permissions.deny` entry was added.
- **S7: fixed, and stronger than asked.** The script fetches `main` and deploys only when `HEAD` is
  the tip of `origin/main` (`scripts/deploy_hosted_engine.sh:42-46`). An ancestor check (D6) and the
  fetch removed (D7) are each killed by `test_deploy_hosted.py::test_only_the_tip_of_origin_main_deploys`.
- **S9: fixed.**
  - The price credit follows the price sources the served file holds
    (`src/app/workflows/rank.py:125-151`; `recommend.py:636`; `standings.py:141`).
  - The derivation drops LiteLLM's 456 `openrouter/` alias rows and the vendor plans
    (`src/app/workflows/public.py:47-51`). D-185 records both, and what they cost.
  - On my derivation, none of the 42 answers and not `/v1/boards` names OpenRouter. The credit
    reads "Pricing data: BerriAI/litellm (MIT)". The word `openrouter` is not in the file's bytes.
  - Whether the remaining LiteLLM data is fine to show is still the licence ruling's question
    (#88), not this seat's.
- **S13: fixed.** `fly deploy … --ha=false` (`scripts/deploy_hosted_engine.sh:62`), held by
  `test_deploy_hosted.py::test_a_deploy_places_one_machine`.
- **S14: fixed** for what it named. `.dockerignore:10-14` leaves out `**/.env*`, `**/__pycache__`,
  `**/*.pyc`, `**/*.pem` and `**/*.key` after `!src`. Dropping `*.pem` is killed (I4). The rest is
  N8.
- **Filed and still open, as the review allowed:** S2 is #188 (the budget argument) and S3 is #187
  (no rate limit). Both stay true on this head, and N2 changes what S3's mitigation is worth.

## New findings

### BLOCKING

None. The permission matrix §11 trigger does not fire: no auth, payment or migration path is in the
range. The hosted engine still receives only a surface id and a budget.

### MINOR

**N1 (MINOR): The project's allow list lets an agent run `fly` with no permission prompt and no
guard hit. S6 assumed that a prompt always stands in front of `fly`.**
- **Where.** `.claude/settings.json:14-19` allow `Bash(make check:*)`, `make check-fast:*`,
  `make test:*`, `make lint:*`, `make typecheck:*` and `make standup:*`. `Makefile:35` sets `PY`
  with `:=`, and a variable given on the command line overrides it.
- **Measured.**
  - `make -n lint PY='fly deploy --remote-only #'` prints
    `fly deploy --remote-only # scripts/write_install_marker.py`, then
    `fly deploy --remote-only # -m ruff check src tests scripts`. `make typecheck` and
    `make check-fast` do the same. Only the `test` leg runs inside the offline sandbox.
  - The Bash guard returns exit 0 (allowed) for `make lint PY='fly apps destroy model-ranking --yes #'`
    and for the same with the deploy script.
  - Claude Code's permissions page says that `:*` is a trailing wildcard. A prefix rule matches
    "whatever comes after", and a `deny` rule "isn't a security boundary around the program". So
    the deny entries that S6 and #189 propose would not stop this spelling. I did not run it in a
    live session. The same page says `find -exec` is never auto-approved, so `Bash(find:*)` is not a
    route.
- **What could happen.** The owner runs `fly auth login`, and the token stays on the Mac. An agent
  session reads a hostile web page during research, or makes a mistake. It runs one allow-listed
  `make` line, and the public engine is replaced, stopped or destroyed with no prompt. Destroying it
  frees the global name `model-ranking`. Anyone can then claim the name and answer every installed
  build over valid TLS (S10).
- **Why MINOR.** An agent must choose to do it, and today the Mac holds no Fly login. Nothing an
  outsider controls reaches it directly.
- **Fix.**
  1. Now, the owner: `fly auth logout` after each deploy, so no Fly token sits on disk for an
     agent's process.
  2. Make the six `make` allow entries exact (`"Bash(make check-fast)"`, with no `:*`), so a
     variable override asks first. This is a settings change, so it is the owner's.
  3. Rewrite G-7 (N5). Add this spelling to #189.

**N2 (MINOR): S3's only mitigation in this release is a Fly feature that does not exist.**
- `docs/release-testflight.md:38` tells the owner to "Set a billing alert in the Fly dashboard
  (Billing → alerts) before you share the app". #187 repeats that premise.
- Fly's cost-management page (docs.fly.io/about/cost-management) says: "We don't support billing
  alerts (yet), so budget accordingly". It also says: "there's no soft ceiling. If you go over,
  we'll bill you". Egress is $0.02/GB in North America and Europe.
- So the owner would believe that a ceiling or an alarm exists when there is none. The hostname is
  in a public repository, so the cost exposure starts at the deploy, whether or not anyone has the
  app. `/v1/boards` is 502,108 bytes without gzip on today's public artifact.
- **Why MINOR.** It costs money and availability, never data.
- **Fix.** Replace the runbook's line: Fly has no alerts or cap; check the usage in the dashboard
  while testing; `fly scale count 0` stops it. Correct #187's premise. Treat #187 (a cap per
  client, gzip by default or cache headers on `/v1/boards`) as the real control before external
  testers.

**N3 (MINOR): INV-86's non-root test reads the `USER` line literally. `USER 0:0` and
`USER root:root` pass.**
- `tests/unit/test_hosted_engine.py:116-130` takes the word after the last `USER` and refuses
  only `root`, `0` and nothing.
- Measured: `USER root:root` in the serving stage (K5), and `USER 0:0` added to the hosted stage
  (K6), each pass `test_hosted_engine.py`. Both would run the public engine as root.
- **Fix.** Take the part before `:`, and refuse `root` and any number equal to 0.

### INFO (checked; no action unless stated)

**N4: two backstops have no test.**
- Removing the pricing half of `_SURVIVORS` (`public.py:52-55`) passes (P6). The `DELETE` that it
  double-checks is held (P2 in the review).
- Making `pricing_sources` default to `None` again (`rank.py:136`, the second W5 review's R4)
  passes the whole unit suite (A4: 2110 passed). Both priced `/v1` callers pass the argument, and
  their credits are tested on a derived artifact.
- Today each is defence in depth.

**N5: G-7 claims more than the guard does.**
- `docs/security-invariants.md:183` says the guard blocks "an agent's deploy or destroy of the
  hosted engine". The only gap it names is a push set through `-c` or `git config`.
- S5, S6 and N1 measure many more spellings that pass. #189 lists most of them.
- The row should say that the guard is best effort, and cite #189.

**N6: wave branches have no protection on GitHub.**
- The repository's only ruleset, "protection" (deletion, non-fast-forward), has an empty include
  list. GitHub's rules endpoint returns no rules for `main` or for `wave/m19-w5`.
- `main` is held by its classic branch protection. A wave branch is held only by the text guard
  (S5).
- Pointing the ruleset at `wave/*` is the server-side fix that S5 offered. It is the owner's
  setting.

**N7: runbook step 1.3 is out of date since R5.**
- `docs/release-testflight.md:25` says "Commit the change: the deploy refuses an uncommitted tree".
  Since `ff940b9`, the deploy also refuses anything but the tip of `origin/main`.
- So a rename must be merged to `main` before it deploys. A confused owner might reach for
  `fly deploy` by hand. That skips the derivation and the build stamp, and production then refuses
  to boot without the stamp.

**N8: S14's rest.**
- Other kinds of file that git ignores, if they sit under `src/`, still reach Fly's remote builder:
  `*.db`, `*.sqlite3`, `notes/` and `*.local.md`.
- They do not reach the image. The build stage installs with setuptools, and there is no
  `MANIFEST.in` or package-data setting, so only the Python modules are installed.
- The builder belongs to the owner's Fly organisation.

## What goes public, measured on `6c98dd7`

- **The public artifact.** I derived it from the worktree's copy of the served artifact (sha256
  `dac97873…9344` before and after) into my scratch folder.
  - The derivation removed 815 score rows, 439 OpenRouter prices, 456 alias prices, 40 plan links
    and 10 plans.
  - The file is 6,524,928 bytes, mode 0644, journal `delete`, freelist 0.
  - Tables with a `source` column: `scores`, `pricing` (LiteLLM only), and `access` (`epoch_access`
    only). The plan tables are empty.
  - The file's bytes contain none of these: any `LEFT_OUT` id, `ARC-AGI`, `DeepSWE`,
    `TerminalBench`, `Terminal-Bench`, `WebDev Arena`, `MMLU`, `openrouter`, `/Users/`, `.local`,
    `192.168`.
- **The hosted engine, in process.** I served it with `APP_ENV=production`, bind `0.0.0.0`, the Host
  list `model-ranking.fly.dev`, and a build stamp.
  - `/health` answers only `status`, `version`, `build`, `evidence` and `refresh`.
  - Any other Host gets 400, loopback included.
  - All 14 tasks × 3 budgets and `/v1/boards` answer 200.
  - POST, PUT, DELETE and PATCH get 405.
  - A cross-origin request gets no CORS header.
  - The only left-out names in any answer are the four surfaces' benchmark names, inside their
    `no_evidence` text (D-121's path). Those come from code, not data.
- **The image** is unchanged since the review, except for comments. INV-86's tests hold it, with
  N3's gap.
- **The TestFlight build.** The address is in S1 above.
  - The manifest declares no tracking, no tracking domains and no collected data. Its one
    required-reason API is UserDefaults, CA92.1, in the tree and in the author's archive.
  - The Info plist answers the encryption question.
  - The Release plist still carries the local-network exception and its usage text. With the
    hosted address, they are unused.
- **W4's change.** The reading still ends in one of the engine's surface ids. `client-decls`
  passes. No request path is added.
- **The Mac's name and LAN address.** Counted with `git grep` at `6c98dd7`: neither appears in a
  tracked file (#147). I did not print them.

## Method and gates

| Check | Result |
|---|---|
| `make check-fast` at `6c98dd7`, with the guard stubs first on `PATH` | **PASS**: lint, typecheck, records (conformance included), test 2119 passed and 25 skipped, swift-test, client-decls |
| `conformance/test-hook-claims.py` | PASS (2 claims, 18 legs, 0 unbacked) |
| `gitleaks detect --log-opts=7fde40d..6c98dd7` and the range's diff through `gitleaks stdin` | 23 commits, **no leaks** |
| `ruff --select S,BLE src scripts` (the SAST stand-in) | 18, the same 18 as before |
| The Bash guard, run on 85 payloads (`guard_probe.py`, the hook's own text) | S5, S6 and N1 above; compared with the guard at `0b2ed00` |
| `make -n` with a `PY` override | N1 |
| Branch protection and rulesets (`gh api`, read) | S5 and N6 |
| The served artifact | read only; sha256 unchanged |
| `make deps`, `make slopsquat` | **not run** (no PyPI access). No lock and no `pyproject.toml` changes in the range, so the review's S15 stands |

## Mutants

Each one was an exact, single-match edit or an appended line. The file's bytes and sha256 were saved
first, and the bytes were restored in a `finally` with the sha256 asserted. The cited tests ran
inside `scripts/offline.sb`, as `make test` runs them. `git status --porcelain` was empty after each
batch.

| # | The edit | Result | Killed by |
|---|---|---|---|
| X5 | `ENGINE_URL[sdk=iphoneos*] = http://…local` after the Release line | KILLED | `test_testflight_ready.py::test_nothing_after_the_release_address_can_replace_it` |
| X6 | a second `#include?` after it | KILLED | same |
| X7 | the include moved back after the Release line | KILLED | `::test_a_release_build_reaches_the_hosted_engine_whatever_the_local_config_says` |
| X8 | `buildForArchiving = "NO"` | KILLED | `::test_the_shared_scheme_archives_the_app_in_release` |
| X9 | the Archive action in Debug | KILLED | same |
| D2 | `USER root` in the hosted stage | KILLED | `test_hosted_engine.py::test_the_hosted_engine_runs_as_no_root_and_cannot_write_its_artifact` |
| D3 | `USER appuser` removed | KILLED | same |
| D4 | `COPY --chown=10001` | KILLED | same |
| K5 | `USER root:root` | **SURVIVED** | none (N3) |
| K6 | `USER 0:0` after the hosted `COPY` | **SURVIVED** | none (N3) |
| D6 | the tip check back to an ancestor check | KILLED | `test_deploy_hosted.py::test_only_the_tip_of_origin_main_deploys` |
| D7 | the `git fetch` removed | KILLED | same |
| D8 | `*--dry-run*` read as a dry run | KILLED | `::test_the_script_takes_no_argument_but_dry_run` |
| D9 | any argument accepted | KILLED | same |
| I4 | `**/*.pem` dropped from `.dockerignore` | KILLED | `::test_the_build_context_leaves_out_what_git_ignores_under_src` |
| I5 | `!build/hosted/advisor.db` widened to `!build` | KILLED | `::test_the_build_context_carries_what_the_image_copies_and_little_else` |
| P4 | no `VACUUM` | KILLED | `test_public_artifact.py::test_no_byte_of_a_left_out_row_survives_in_the_file` |
| P5 | the file 0o666 | KILLED | `test_public_artifact.py::test_the_public_artifact_carries_no_row_of_a_left_out_source` (`:44`, no group or other write bit) |
| P6 | `_SURVIVORS` without its pricing half | **SURVIVED** | none (N4) |
| P7 | the `openrouter/` alias delete removed | KILLED | `::test_no_openrouter_price_rides_in_under_another_source` |
| A4 | `pricing_sources` defaults to `None` | **SURVIVED** | none; 2110 passed (N4) |
| G4 | the guard's `fly` rule removed | KILLED | `conformance/test-hook-claims.py` |

**Score:** 22 mutants, 18 killed and 4 survived. Each survivor is in a finding.

## Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| The image build, `make cold-start` | Docker was not running, and the seat may not run it | Read and mutated as text, as the review did (R2 of the W5 reviews stands) |
| `fly`, the deploy, a probe of `model-ranking.fly.dev` | Out of bounds | Fly's behaviour comes from its documentation pages |
| `xcodebuild`, a signed archive | Stubbed | I read the author's unsigned Release archive with `plutil` and `strings`. The owner's readback (runbook step 2.3) is the check on his own build |
| N1 in a live Claude Code session | It would mean running `fly` | I rest on Claude Code's documented rule and on `make -n` |
| `make deps`, `make slopsquat` | No PyPI access | The locks are unchanged in the range |

**Not checked:** whether the left-out sources are the right ones (#88); the owner's Fly, billing and
App Store Connect settings; W4's reading rules beyond their security side.
