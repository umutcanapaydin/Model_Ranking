---
record_type: review
id: m19-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19-W5 Code Review, round 2: a first release, the engine hosted and the app on TestFlight

**Reviewer:** Code-Reviewer subagent, a new seat with fresh eyes. I wrote none of this wave's code,
tests or records. I was not the first reviewer, and I was not the security seat.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `6c9ce17..1307a00`. That is W5's own 30 commits, besides the two merges of W4,
on top of W4's head `6c9ce17`, which another seat reviews. The range has 44 files, +2454 / -102.
1,076 of those lines are the two earlier review records.
**Risk tier:** HIGH (`docs/plans/m19-plan.md:110`, `docs/plans/m19-wave-5-plan.md:13`). The diff
touches `.claude/settings.json` and `scripts/engine_service.sh`, both security globs
(`m19-plan.md:122-131`).
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family is available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`, then the milestone and wave plans and the two earlier
reviews. I read the code next and the commit messages last.

## Verdict
MINOR

**Summary.** The fixes for the first review and the security review mostly hold, and I checked them
by running things, not by reading them:
- **The public artifact is clean.** I derived it from this worktree's copy of the served artifact
  and served it in process in the hosted configuration. Every route, task and budget answered 200.
- **The credit is right.** Every priced answer credits "BerriAI/litellm (MIT)" alone. The full
  artifact still credits OpenRouter.
- **No left-out data survives.** Not one byte of any `LEFT_OUT` id, `openrouter.ai` or `ARC-AGI` is
  in the file. There is no plan row, the freelist is 0 and the journal mode is `delete`.
- **The gates pass.** `make check-fast` passes (2114 passed, 25 skipped) and so does
  `conformance/test-hook-claims.py`.
- **The tests bite.** I planted 25 faults in the fixed surfaces. The cited tests killed 20 of them.

What is left is MINOR:
1. The new guard against an agent deploying the hosted engine (S6) misses ordinary spellings. One is
   the env-prefixed form the script's own error message suggests. Its `--dry-run` exemption is also
   wider than the script's parsing: I measured three commands that the guard allows and that deploy.
2. The shared Xcode scheme does not build the app for Archive. The runbook's TestFlight step depends
   on Archive.
3. S1's fix is right, but its test is narrower than its claim.
4. Records drift: D-185 does not record the second half of the MJ1 fix. Also, this record's `id`
   collides with the round-1 record's `id`, so `make check-records` fails (measured).

Nothing here is deployed, and the permission prompt still stands in front of every `fly` call. Each
other finding fails closed or is cheap to fix. So none is BLOCKING.

## Status of the earlier findings

### The first W5 review (`docs/reviews/m19-wave-5-review-round-1.md`)

| Id | Status | Evidence |
|---|---|---|
| MJ1 | **Fixed** | `rank.py:125-151` (`served_pricing_sources`, credit follows the rows); `recommend.py:636`, `standings.py:140-141`; `public.py:48` drops LiteLLM's `openrouter/` aliases. Measured: 456 alias rows removed; public answers credit LiteLLM only. Mutants A1, A2, A3 and P1 were killed (`test_recommend.py:189`, `test_board_standings.py:168`, `test_public_artifact.py:88`, `:102`). The ADR does not say so: M5 below |
| M1 | **Fixed**, with a new false positive | `-4f`, `-f4`, `--mi`, `--mirr` are blocked (`settings.json:49`, `test-hook-claims.py:290-291`); G2 killed. `--mi[a-z]*` has no right boundary: M2 below |
| M2 | **Mostly fixed** | The `VACUUM` is held by a planted marker (`test_public_artifact.py:121-135`; P4 killed). The plans are dropped (`public.py:49-50`; P2 killed). The removal list and the survivor check are still closed (`public.py:40-52`): M6 below |
| M3 | **Fixed** | `.dockerignore:4`; the test now reads the `COPY` lines (`test_deploy_hosted.py:144-157`); I1 killed |
| M4 | **Fixed** | `--ha=false` (`deploy_hosted_engine.sh:53`; `test_deploy_hosted.py:114`); D1 killed. The runbook (`:19-21`) and D-185 clause 1 agree |
| M5 | **Fixed** | Stamp `release-<sha>-data-<8 hex>` (`deploy_hosted_engine.sh:46-47`; D3 killed). Measured: four derivations of the same data gave the same digest. HEAD must be an ancestor of `origin/main` (`:34`; D2 killed). R5 below has a note on this |
| M6 | **Fixed** | `docs/owner-iphone.md:24` is now Debug only (`test_testflight_ready.py:84-89`); the security review's S1 fix makes this structural |
| M7 | **Fixed in the M18 records**, and reopened by this wave's own record | `m18-wave-1-review.md:51`, `m18-wave-1-tester.md:112`, `:419` now use placeholders. The round-1 record's search pattern (`m19-wave-5-review-round-1.md:221`) spells the Mac's name fragment and its LAN address: M7 below |
| M8 | **Fixed**, one comment left | D-116 has its `Amended by D-185` line (`decisions.md:690`). The `Dockerfile` header, the runbook's "four places" (`:22-24`), the build number (`:64-66`) and the plan's counts are fixed. `fly.toml:9-10` still names two of the four places: M5 below |
| K1 | **Fixed** for `\` + LF | The continued line is joined before matching (G1 killed). `\` + CRLF is not joined (measured; M2) |
| K2 | **Fixed** | `test_router_hints.py:654-670`: a catalog may hold images and `Contents.json` only |
| R1 | **Open, carried** | No offline way to see whether Fly's checker sends the `Host` header. The runbook has the TCP fallback (`release-testflight.md:76-78`) |
| R2 | **Open, carried** | The image has never been built |
| R3 | **Fixed** | `PRAGMA journal_mode=DELETE` before the `VACUUM` (`public.py:88`; `test_public_artifact.py:153-162`; P3 killed) |

### The M19 closure and Stage 5.1 security review (`docs/reviews/m19-closure-security-review.md`)

| Id | Status | Evidence |
|---|---|---|
| S1 | **Fixed in the config; the test is narrower than the claim** | `Engine.xcconfig:17`: the Release line now comes after the include. Under the documented rule ("the last instance wins") a local `ENGINE_URL` can no longer replace it for Release. X1 (include moved after) and X4 (an http Release line appended) were killed. X2 (`ENGINE_URL[sdk=iphoneos*]` appended) and X3 (a second `#include?` appended) **survive**: M4. The runbook still says the opposite of the new order (`release-testflight.md:57-58`), and has no readback of the archived `EngineURL` (fix item 4): M4 |
| S4 | **Fixed** | INV-86 and INV-87 (`security-invariants.md:166-167`), each citing existing tests. The `USER` and `COPY --chown` mutants were killed (K1, K2), and so were the `VACUUM` and 0o664 mutants (P4, P5). G-8 is closed and the #94 paragraph is rewritten. Two narrow survivors (K3, K4) are in M6 |
| S5 | **Narrowed** | These are now blocked: a quoted `-f` or `+refspec`, `--mirr`, a continued line, `HEAD:refs/heads/main`. These still pass: a quoted main refspec (`'HEAD:main'`), `\+x`, `''+x`, `-c remote.*.mirror/push=+` (G-7 declares this one), and a push inside `( … )` or `$( … )`. M2 lists them |
| S6 | **Partly fixed** | Blocked: `fly deploy`, `fly … destroy`, and the script without `--dry-run`. No `permissions.deny` was added (`settings.json` `permissions` has `allow` only). Ordinary spellings pass: M1 |
| S7 | **Fixed** | `deploy_hosted_engine.sh:34-37` refuses a HEAD that is not on `origin/main` (`test_deploy_hosted.py:134-141`; D2 killed) |
| S13 | **Fixed** | `--ha=false`, as round-1 M4 |
| S14 | **Partly fixed** | `.dockerignore:10-12` leaves out `**/.env*`, `**/__pycache__` and `**/*.pyc` (I2 killed). It does not leave out `*.pem` and `*.key`, which S14 named and `.gitignore:32-33` ignores: M6 |

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `.claude/settings.json:49` (the `fly`/`flyctl` and `deploy_hosted_engine.sh`
  alternatives); `scripts/deploy_hosted_engine.sh:26`; `conformance/test-hook-claims.py:289-299`.
  **The guard that keeps the hosted engine's deploy for the owner (S6) misses ordinary spellings.
  Its `--dry-run` exemption is wider than the script's parsing.**
  - **How it reads a command.** It looks for `fly`, `flyctl` or the script only where a line or a
    `;&|` segment starts. For `fly`, it blocks only the words `deploy` and `destroy`.
  - **Measured: allowed (exit 0)**, each run through the conformance harness's own `run_hook`:
    - `FLY_API_TOKEN=x fly deploy`, `env fly deploy`, `command fly deploy`, `time fly deploy`.
    - `(fly deploy)`, `{ fly deploy; }`, `$(fly deploy)`, `bash -c 'fly deploy'`.
    - `fly launch --now` ("deploy now without confirmation", Fly's reference).
    - `fly secrets set A=b` (deploys unless `--stage`, Fly's reference).
    - `fly scale count 0 --yes`, `fly machine stop abc`, `fly machine run .`,
      `fly machine update abc --image x`.
    - `fly ssh console`, which S6 named.
    - `MODEL_RANKING_SERVED=/tmp/a.db scripts/deploy_hosted_engine.sh`. This is the form the
      script's own refusal suggests ("set MODEL_RANKING_SERVED", `:40`).
    - `bash -x scripts/deploy_hosted_engine.sh`, `source scripts/…`, `. scripts/…`.
  - **Measured: the guard allows these as a dry run, and the script deploys.** I ran the script
    with the test's stand-ins for `fly` and `curl` first on `PATH`, against a scratch repository,
    so no request left the machine. Each of these reached `fly deploy --build-arg
    APP_BUILD=release-…-data-f1d31979 --remote-only --ha=false`:
    - `scripts/deploy_hosted_engine.sh now --dry-run`;
    - `scripts/deploy_hosted_engine.sh --dry-run-no`;
    - `scripts/deploy_hosted_engine.sh --dry-run=false`.

    The reason: the script reads only `$1` (`:26`), and the guard's exemption accepts `--dry-run`
    anywhere on the line.
  - **What still stands in the way:** the permission prompt, as before. `fly` is not in
    `permissions.allow`. S6's first fix item, `permissions.deny` for `Bash(fly:*)`, `Bash(flyctl:*)`
    and the script, was not taken. The new G-7 row says the guard blocks "an agent's deploy or
    destroy of the hosted engine" (`security-invariants.md:183`), and that is wider than what it
    does.
  - **Failure scenario.** After `fly auth login`, an agent session runs
    `MODEL_RANKING_SERVED=… scripts/deploy_hosted_engine.sh` to "check the artifact", or runs
    `fly scale count 0`. If someone approves the prompt in a hurry, the public engine is replaced or
    stopped. D-185 clause 5 and permission matrix §3 say no agent does this.
  - **Fix.**
    1. Make the script refuse any argument other than none or exactly `--dry-run`: `case "$#:${1:-}"
       in 0:|1:--dry-run) ;; *) echo usage >&2; exit 2;; esac`. Add a test that `now --dry-run`
       exits 2 before `fly` is called. This alone closes the three measured deploys.
    2. Add the `permissions.deny` entries S6 asked for.
    3. In the guard, refuse every `fly`/`flyctl` call except a read-only list (`status`, `logs`,
       `checks`, `releases`, `version`, `auth whoami`, `apps list`, `config show`). Accept a command
       start after `(`, `{`, `` ` ``, `$(`, after `VAR=value ` assignments and after
       `env|command|exec|time|nohup|sudo`. Apply the same start rule to the script.
    4. Add the measured spellings to `MUST_BLOCK`.
    5. It is a hook change: its own commit, for the owner.
- **M2** `.claude/settings.json:49` (the push alternatives); `docs/security-invariants.md:183`
  (G-7). **The push guard has holes that G-7 does not list, and two new false positives.**
  - **Measured: allowed (exit 0)**, before and after this wave:
    - `git push origin 'HEAD:main'` and `git push origin "x:main"`. The unquoting reaches only a
      token that starts with `-` or `+`, and the main rule wants a space or line end after `main`.
    - `git push origin \+x` and `git push origin ''+x`.
    - `(git push -f origin y)` and `$(git push -f origin y)`. `(` and `$(` are not command starts
      to the guard.
    - A continued line ending in CRLF: `\` + `\r\n`.

    Branch protection still holds `main` on GitHub (security review, S5). What is exposed is a wave
    branch's history.
  - **G-7 is out of date.** It says the guard "does not see a push set through `-c` or
    `git config`", and lists nothing else.
  - **New false positives (blocked, exit 2; each allowed at `6c9ce17`):**
    - `git push origin wave/m19--minor` and `git log --grep push --min-parents=2`. The cause:
      `--mi[a-z]*` has no boundary on either side.
    - This wave's own commit subjects, written with `-m`. For example: `git commit -m "fix: the
      force-push guard blocks any option cluster holding f, and --mirror (#142)"`. Any `-m` message
      that says "push" and then `--mirror` or `-uf` is now blocked with "destructive command …
      escalate to the owner".
  - **Fix.**
    1. Anchor the abbreviation: `[[:space:]]--mi[a-z]*([[:space:]=]|$)`.
    2. Let the main rule end at a quote as well (`([[:space:]'"]|$)`).
    3. Count `(`, `` ` `` and `$(` as command starts for every alternative (K1 below).
    4. Rewrite G-7 to list what the guard still passes.
    5. Add the false positives above to `MUST_ALLOW`. It is a hook change, for the owner.
- **M3** `ios/ModelRanking.xcodeproj/xcshareddata/xcschemes/ModelRanking.xcscheme:13`, `:54`;
  `docs/release-testflight.md:61-62`. **The shared scheme does not build the app for Archive. The
  TestFlight runbook's step 2.3 is Product → Archive.**
  - The only `BuildActionEntry` has `buildForArchiving = "NO"`, and the scheme has no
    `<ArchiveAction>`. This file came from M18-W2 (`82fec62`), which wrote it for Run and Test.
  - The "Archive" checkbox in the scheme editor's Build tab is that attribute. Reports of a target
    left out of an archive are fixed by checking it (Bitrise discussion 3265: "scheme does not
    contain buildable target", fixed by toggling "Build for Archiving").
  - I could not run `xcodebuild` here, so this is read, not measured. Xcode may also add a default
    `ArchiveAction` (Release) when it loads the file.
  - **Failure scenario.** The owner archives as the runbook says. Organizer shows an archive with no
    app, or none, and "Distribute App" is not offered. The first TestFlight attempt stops on a
    checkbox the runbook never mentions.
  - **Fix.**
    1. Set `buildForArchiving = "YES"` on the app's entry.
    2. Add `<ArchiveAction buildConfiguration = "Release" revealArchiveInOrganizer = "YES">`.
    3. Add a test to `test_testflight_ready.py` that parses the scheme and holds both. It also holds
       Release, which is what puts the hosted URL in the archive (D-185 clause 4).
- **M4** `tests/unit/test_testflight_ready.py:92-99`; `ios/Config/Engine.xcconfig:13-17`;
  `docs/release-testflight.md:55-58`, `:61-62`. **S1's config fix is right, but its test holds less
  than its comment claims, and the runbook still describes the old order.**
  - The comment says "no local ENGINE_URL can send an archive elsewhere". The test checks only that
    the Release line comes after the first `#include?`.
  - **Survivors, each with `test_testflight_ready.py` and `test_engine_address.py` green:**
    - X2: `ENGINE_URL[sdk=iphoneos*] = http:/$()/my-mac.local:8080` appended after the Release
      line. On a device build it is the newest matching assignment, so it wins.
    - X3: a second `#include? "Engine.release.local.xcconfig"` appended after it.

    That is exactly the security review's fix item 2: "nothing sets `ENGINE_URL` after the Release
    line: no assignment and no include".
  - **The runbook is stale.** `release-testflight.md:57-58` still says a local `ENGINE_URL` "replaces
    the hosted address". That is no longer true.
  - **No readback.** The archive step has no check of the archived app's `EngineURL` (S1 fix item
    4). The commit `60735c9` says a planted local file "was checked to carry" the hosted URL, but no
    record or test keeps that check.
  - **Fix.**
    1. Assert that the Release line is the last line of the file that assigns `ENGINE_URL` in any
       form, and that no `#include` follows it.
    2. Replace `:57-58` with what is now true.
    3. Add after step 2.3: `plutil -extract EngineURL raw <archive>/Products/Applications/ModelRanking.app/Info.plist`
       must print `https://model-ranking.fly.dev`.
- **M5** `docs/decisions.md:4270-4300` (D-185); `fly.toml:9-10`. **D-185 does not record half of
  what the MJ1 and M2 fixes changed in the public artifact.**
  - Clause 3's table lists `openrouter` as "the second price of 168 models". The derivation now also
    removes:
    - LiteLLM's `openrouter/` alias rows (456);
    - every vendor plan (10 plans, 40 links).
  - Seven models lose their only price and leave every ranking: `minimax-m1`, `solar-pro4`,
    `step3.5-flash` and four more. `px_median` goes from 303 to 296.
  - "The cost" names only `coding`, 32 against 54. Measured on the copy of the served artifact
    (public / full): `assistant` 194/198, `everyday` 153/155, `expert` 152/154, `factuality`
    112/116, `mathematics` 142/144.
  - The round-1 review said the aliases were the owner's call, "or D-185 records … why". The agent
    took the recommendation on the standing instruction, which is allowed, but the ADR is where the
    owner reads it. INV-87 says it; D-185 does not.
  - `fly.toml:9-10` still says to rename in two places. The runbook and the tests say four.
  - **Fix.**
    1. Add a row or a sentence to D-185: LiteLLM's `openrouter/` aliases and the plans are left out,
       and why.
    2. Add the dropped-model effect to "The cost".
    3. Make the `fly.toml` comment name all four places.
    4. The ADR is new in this wave, so it can still be edited.
- **M6** `src/app/workflows/public.py:40-52`; `.dockerignore:9-12`; `Dockerfile:65-67`;
  `tests/unit/test_hosted_engine.py:121-130`. **Three closed lists still let a new case through.
  Nothing leaks today.**
  - **The public derivation.** The `DELETE`s name `scores` and `pricing`, and `_SURVIVORS` checks
    only `scores`. A later table with a `source` column, or a left-out publisher feeding `access`,
    would ship whole. This was the second half of round-1 M2. Today `access` is all `epoch_access`,
    and the derived file's bytes hold no `LEFT_OUT` id (measured).
  - **The build context.** It leaves out `.env*` and bytecode under `src/`, but not `*.pem` and
    `*.key`, which S14 named and `.gitignore` ignores. Such a file would reach Fly's remote builder.
    It would not reach the final image.
  - **The image.** INV-86 ("cannot write its artifact") is held on the last `USER` and on `COPY`
    flags only. Two mutants survived:
    - K3: `USER root` / `RUN chmod 666 /srv/advisor.db` / `USER appuser` passes.
    - K4: dropping the `hosted` stage's `ENV MODEL_RANKING_DB=/srv/advisor.db` passes, because
      `fly.toml` sets it. `make cold-start`, which passes no such variable, would then boot against
      the empty `/data`.
  - **Fix.**
    1. Delete by `PRAGMA table_info`, from every table with a `source` column, and check survivors
       in each.
    2. Add `**/*.pem` and `**/*.key` after `!src`.
    3. In the hosted-stage test, refuse any `RUN` that touches `/srv`, and require the stage's own
       `MODEL_RANKING_DB` to equal its `COPY` target.
- **M7** `docs/reviews/m19-wave-5-review-round-1.md:3`, `:221`. **The round-1 record kept the id this
  record must carry, and its search pattern names what #147 removed.**
  - `d80ae16` renamed the file but kept `id: m19-wave-5-review`. This record carries the same id, so
    `check_records.py`'s R3 fires (`scripts/check_records.py:258-261`). Measured with this file in
    place: `make check-records` fails with "[R3] duplicate id `m19-wave-5-review` (also
    docs/reviews/m19-wave-5-review-round-1.md)". The wave cannot close green until this is fixed.
  - The earlier round-1 renames changed the id as well: `m18-wave-3-review-round-1`,
    `m19-wave-2-review-round-1`.
  - Line 221 of the same record quotes the `git grep` pattern it searched with. That pattern spells
    the owner's Mac-name fragment and his LAN address. #147's acceptance ("No tracked file names the
    owner's Mac or home address", wave plan P1) is again unmet, by a file this wave adds.
  - **Fix.**
    1. Set the round-1 record's id to `m19-wave-5-review-round-1`.
    2. For line 221, do one of these, with the owner's say since it is another seat's ratified
       record: replace the literal with a reference to #147, or narrow #147's acceptance to "outside
       review records quoting the search", and say so on the issue before it closes.

### PASS (what looks good)

- **The public artifact, measured end to end.**
  - I derived it from the worktree's copy of the served artifact. The copy's sha256 was `dac97873…`
    before and after.
  - The derivation removed 815 score rows, 439 OpenRouter prices, 456 alias prices, 40 plan links
    and 10 plans.
  - The file is 6.5 MB, mode 0644, freelist 0, journal `delete`.
  - In the hosted configuration (`APP_ENV=production`, bind `0.0.0.0`, Host list
    `model-ranking.fly.dev`, the file read-only), every route and all 14 tasks × 3 budgets answered
    200.
  - `abstract`, `agentic-coding`, `computer-use` and `web-dev` answer `no_evidence`, and `coding`
    ranks 32, as D-185 says.
- **The credit follows the rows.**
  - `served_pricing_sources` reads `SELECT DISTINCT source FROM pricing`, so the hosted credit is
    LiteLLM's alone. The Mac keeps the full credit.
  - Both priced `/v1` callers pass it (`recommend.py:636`, `standings.py:140`). The CLI export
    (`rank.py:450`) keeps the full credit on the Mac.
  - No `/v1` field changes shape.
- **The deploy script fails closed and stamps code and data.** It refuses:
  - a dirty tree;
  - a HEAD that is not on `origin/main`;
  - a missing artifact;
  - a failed derivation;
  - a `/health` from another build.

  One machine. Every test uses stand-ins for `fly` and `curl`.
- **The commits are in order.**
  - Red-then-green pairs for every fix (`92dd862`→`dea39c8`, `31fff71`→`60735c9`,
    `2dc5b9f`→`d385074`).
  - The hook change is in its own commit, labelled for the owner's approval.
  - No AI attribution. The owner's identity and the `GP-Agent` trailer are on every commit.
  - S2 and S3 are filed as #188 and #187, both open.
- **No drive-by edits.**
  - `test_router_hints.py` and `test_ios_client_contract.py` change for K2 and the asset catalog.
  - `test_readonly_uri.py` lists `public.derive`'s writable open.
  - The two M18 records change for M7.
- **The quote-unwrapping step regresses nothing.** `rm '-rf' build`, `git reset '--hard'` and
  `git checkout -- f` are blocked. `git restore --staged`, `git stash push -m wip`,
  `git push -o ci.skip`, `--set-upstream`, `--porcelain` and `--signed=if-asked` pass (probe,
  132 payloads).

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **INV-87: the hosted artifact carries no left-out row or byte, no OpenRouter price, no plan. Its
  credits name only what it serves.**
  - `public.derive`, through `scripts/deploy_hosted_engine.sh:45`:
    - `test_public_artifact.py::test_the_public_artifact_carries_no_row_of_a_left_out_source`;
    - `::test_no_openrouter_price_rides_in_under_another_source`;
    - `::test_no_byte_of_a_left_out_row_survives_in_the_file`;
    - `::test_the_public_artifact_carries_no_vendor_plan`;
    - `test_deploy_hosted.py::test_a_deploy_stamps_the_commit_ships_the_public_artifact_and_checks_health`.
  - `public.derive`, through `docs/cold-start.sh:21`:
    `test_release_gates.py::test_a_cold_start_boots_the_hosted_image_on_loopback_and_journeys_it`.
  - The `/v1/boards` credit (`standings.py:140`):
    `test_public_artifact.py::test_a_public_answer_credits_only_the_prices_it_serves`,
    `test_board_standings.py:157-168`.
  - The `/v1/recommendations` credit (`recommend.py:636`): `test_recommend.py:175-189`.
- **INV-86: a non-root engine that cannot write its artifact, boot refusal with no Host list, and
  the deployment's one Host.** Held by `test_hosted_engine.py:64`, `:71`, `:92`, `:105`, `:121`.
- **INV-82: the agent's destructive and protected-branch commands.** Held by `MUST_BLOCK` and
  `MUST_ALLOW` in `conformance/test-hook-claims.py:281-299`.
- **D-185 clause 4: a Release build reaches HTTPS.** Held by `test_testflight_ready.py:77`, `:84`,
  `:92`.

Gaps:
- INV-87: a table outside the closed list, M6. Also, any new priced caller of `attributions_for`
  credits OpenRouter by default, R4.
- INV-86: a `RUN` in the `hosted` stage, M6.
- INV-82: M1 and M2.
- D-185 clause 4: an assignment or include after the Release line (M4), and the scheme's Archive
  action (M3).

## Acceptance criteria evidence (REQUIRED for PASS verdict)

The wave scopes no REQ-IDs. Its tests cite issues and D-IDs. By phase
(`docs/plans/m19-wave-5-plan.md`, "Phases"):

- **P1, #147:** `tests/unit/test_engine_host.py`, `ios/EngineTests/*` and `docs/owner-iphone.md:19-24`
  use placeholders, and so do the two M18 records. Hole: M7.
- **P1, #145:** `scripts/engine_service.sh:59-75`, `tests/unit/test_engine_service.py` (the silent
  preflight kill).
- **P1, #141:** `Dockerfile:11`, `:23`; `tests/unit/test_dependency_locks.py` (base by digest), in
  INV-81's row.
- **P2, #94:**
  - Changed: `Dockerfile:36`, `:56-57`, `:65-67`; `fly.toml:20-25`, `:51-60`;
    `scripts/deploy_hosted_engine.sh`; `.dockerignore`.
  - Tests: `tests/unit/test_hosted_engine.py:64-130`; `tests/unit/test_deploy_hosted.py:63-167`.
  - Holes: M6; R1, R2.
- **P3, #88:**
  - Changed: `src/app/workflows/public.py`; `rank.py:125-151`; D-185.
  - Tests: `tests/unit/test_public_artifact.py:27-164`.
  - Holes: M5, M6.
- **P4, TestFlight:**
  - Tests: `tests/unit/test_testflight_ready.py:43`, `:56`, `:71`, `:77`, `:84`, `:92`.
  - The runbook is `docs/release-testflight.md`.
  - Holes: M3, M4.
- **P5, #142:** `.claude/settings.json:49`; `conformance/test-hook-claims.py:281-299` (PASS, run).
  Holes: M1, M2.
- **P6:** this record. Then the Tester; a security read of the post-review fixes is owed (R3).

## K.8 contract drift check

`grep -n` at `1307a00` for the milestone plan's contracts (`m19-plan.md:140-154`) and the wave's
own names:

```
src/app/adapter/main.py:476:ALLOWED_HOSTS_VAR = "MODEL_RANKING_ALLOWED_HOSTS"
src/app/adapter/main.py:478:BIND_VAR = "MODEL_RANKING_BIND"
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
src/app/workflows/registry.py:567:DISPLAY_NAMES: dict[str, str] = {
src/app/workflows/registry.py:699:def claude_word_order(name: str) -> str:
src/app/workflows/rank.py:41:PRICING_ATTRIBUTION = (
src/app/workflows/rank.py:48:PRICING_ATTRIBUTION_LITELLM = "Pricing data: BerriAI/litellm (MIT)"
src/app/workflows/rank.py:51:ATTRIBUTIONS = (
src/app/workflows/rank.py:63:SOURCE_ATTRIBUTION: dict[str, str] = {
src/app/workflows/rank.py:125:def served_pricing_sources(conn: sqlite3.Connection) -> frozenset[str]:
src/app/workflows/rank.py:130:def attributions_for(
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:526:enum ModelOutputBoundary {
ios/ModelRanking/Engine/FrontDoor.swift:278:public struct GapRegisterStore {
ios/ModelRanking/Engine/AnswerPlan.swift:174:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
tests/conftest.py:226:def pytest_configure(config: pytest.Config) -> None:
```

- `git diff --stat 6c9ce17 1307a00 -- src/app/adapter ios/ModelRanking/Engine tests/conftest.py
  src/app/workflows/registry.py ios/ModelRanking/ContentView.swift` is empty.
- `ATTRIBUTIONS` and `SOURCE_ATTRIBUTION` are unchanged.
- `attributions_for` gains a keyword argument with a default, so every existing caller still works.
- `/v1` changes no field or route. Only the text of one credit changes, on the public artifact.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `.claude/settings.json:49` (every alternative's `(^|[;&|[:space:]])` start). **A command
  inside `( … )`, `` ` … ` `` or `$( … )` passes every rule of the guard.** These predate the wave.
  - Measured, allowed: `(rm -rf ~/work)`, `` `rm -rf x` ``, `$(git reset --hard HEAD~1)`,
    `(git push -f origin y)`.
  - `{ rm -rf x; }`, `sudo rm -rf` and `xargs rm -rf` are blocked.
  - A bug in INV-82's guard: add `(`, `` ` `` and `$(` to the command-start set. It is a hook
    change, for the owner.

## Risks queued to next M

- **R1** `fly.toml:51-60`. **Carried from round 1. Whether Fly's HTTP check sends the `Host` from
  `headers` is unverified.**
  - What would show it: the first `fly deploy` timing out on health, or `fly checks list`.
  - The runbook's TCP fallback (`release-testflight.md:76-78`) is the answer.
- **R2** `Dockerfile:11-67`; `.dockerignore`. **Carried. The image has never been built.**
  - These are read, not run: the digest, the re-include of `build/hosted/advisor.db` under `*`, and
    the install with no `README.md`.
  - What would show it: `make cold-start` on the owner's Mac (runbook step 1.4) before the first
    deploy.
- **R3** The fix commits `dea39c8`, `60735c9` and `d385074` change the release surface after the
  Stage 5.1 review: the guard, `public.py`, the pricing credit, the xcconfig order, the deploy script
  and `.dockerignore`.
  - The security review's S12 says "the release is owed a short security read of that change before
    the deploy". This record is a code review, not that read.
  - What would show it is missing: a deploy with no security record dated after `d385074`.
- **R4** `src/app/workflows/rank.py:130-142`. **`pricing_sources=None` means "credit OpenRouter".**
  - A new priced `/v1` caller that forgets the argument credits OpenRouter on the hosted engine
    again. No test would notice unless it ran against a derived artifact.
  - What would show it: a new payload with `priced=True` and no `pricing_sources`.
  - A cheap guard: make the argument required for `priced=True`.
- **R5** `scripts/deploy_hosted_engine.sh:34`. **The `origin/main` check reads the local tracking
  ref and accepts any ancestor.**
  - It never fetches. So a stale `origin/main`, or an older `main` commit (a rollback, deliberately
    or not), deploys.
  - The runbook's `git pull` (step 1.1) is what keeps it current.
  - What would show it: a `/health` build whose sha is behind `origin/main` on GitHub.

## Gates and probes run

- **`make check-fast` at `1307a00`:** **PASS** in 63 s, run with the guard-bin stubs on `PATH`.
  - lint, typecheck, records (conformance included), test (2114 passed, 25 skipped), client-decls
    and swift-test all passed.
- **`python3 conformance/test-hook-claims.py`:** PASS ("2 enforcement claim(s) derived, 18 gate
  leg(s), 0 unbacked").
- **Guard probe.**
  - 132 payloads of my own, plus 7 for K1, through the harness's `run_hook` and `runnable_bash`, on
    the hook text read from `.claude/settings.json` (M1, M2, K1).
  - 10 of them were also run on the hook at `6c9ce17`, to separate the new false positives from the
    old holes.
- **Deploy-script probe:** four argument shapes, with the test's own `_scratch` and `_deploy` (the
  stand-ins `fly` and `curl` first on `PATH`, a scratch bare origin). No request left the machine.
- **Public artifact:** derived into my scratch folder and served in process in the hosted
  configuration. I compared all 42 task-and-budget answers and `/v1/boards` with the full
  artifact's. The worktree's `advisor.db` had sha256 `dac97873…9344` before and after.
- **Mutants: 25.**
  - Each one was an exact single-match edit or an appended line. The file's bytes and sha256 were
    saved first, and the bytes were restored in a `finally` with the sha256 asserted.
  - `git status --porcelain` was empty after the batch.
  - The targeted tests ran with `--no-cov`. My first batch ran without it, and the coverage floor
    turned every partial run red, so that batch was void and I re-ran it.
  - Killed: A1-A3, P1-P5, X1, X4, D1-D3, K1, K2, I1, I2, G1-G3.
  - Survived:
    - X2 and X3 (M4);
    - K3 and K4 (M6);
    - I3, a deliberate `!src/app/secret.pem` re-include, which shows only that the context test
      checks three patterns.
- **Network:** `gh issue view` for #187, #188, #142, #94, #88 and #147. Fly's reference pages for
  `apps destroy`, `machine destroy`, `secrets set`, `launch` and `scale count`. One web search and
  one forum page on scheme archiving (M3).
- **Not run:** I did not run `fly`, docker, the deploy script without stand-ins, the service
  installer, launchctl, `xcodebuild`, `simctl`, anything that opens an app or a browser, or
  `os.abort()`.

*Filled by: Code-Reviewer seat (independent, round 2) · Date: 2026-10-07 · Commit range: `6c9ce17..1307a00`*
