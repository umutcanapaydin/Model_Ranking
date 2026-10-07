---
record_type: review
id: m19-wave-5-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19-W5 Code Review: a first release, the engine hosted and the app on TestFlight

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-07
**Commit range:** `ae2c528..d9f4e74` (18 commits besides the merge; 31 files, +959 / -80). The merge
`d62f044` only brings in wave W4, which another seat reviews.
**Risk tier:** HIGH (`docs/plans/m19-plan.md:110`, `docs/plans/m19-wave-5-plan.md:13`). The diff
touches `scripts/engine_service.sh` and `.claude/settings.json`, both security globs
(`m19-plan.md:125`, `:132`).
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the profile and
`.agents/rules/practices.md` from `origin/main`. Then I read the milestone plan (§2 W5, §3, §5), the
wave plan, issues #94, #88, #141, #145, #147 and #142, D-116, D-123, D-185 and the runbook. Then I read
the diff. I read the commit messages last.
**Verdict:** MAJOR

**Summary.** The wave does what its plan says, and most of it holds up when run. I could not build
the image (no Docker here either), so I rebuilt its path by hand: the build stage's install, done
offline from a copy of what the image copies; the public artifact, derived from the copy of the
served one; and the engine, started in the image's environment against a read-only directory. It
boots and serves `model-ranking.fly.dev`. It refuses any other Host. Without the Host list it refuses
to boot. Every `fly.toml` key the wave uses is in Fly's configuration reference. The deploy script
stops at each failure. The launcher fix is right, and the TestFlight pieces are right. `make
check-fast` passes. I planted eleven faults and the tests caught nine.

One finding is MAJOR, and it goes to the point of #88. **OpenRouter is left out in name only.** The
hosted engine still credits OpenRouter's catalogue on every priced answer. OpenRouter's prices also
still reach the public medians, through LiteLLM's own copy of them: seven models are priced only that
way. Eight MINORs follow:

1. **M1.** The widened force-push guard still passes `git push -4f` and `git push --mirr`, and git
   runs both (measured).
2. **M2.** No test holds the `VACUUM` that wipes the removed rows from the file. Without it, the
   shipped file still holds ARC-AGI's rows 573 times. The removal is also a closed list of two
   tables.
3. **M3.** `.dockerignore` leaves out the `Dockerfile`. Fly's reference says not to do that.
4. **M4.** A first `fly deploy` places two machines, not the "one machine" the records describe and
   price.
5. **M5.** The build stamp names the commit, not the data. Redeploying after a refresh gives two
   different images the same stamp.
6. **M6.** `owner-iphone.md` tells the owner to set `ENGINE_URL` in the local file, and that line
   overrides the Release address. A TestFlight build would then ask his Mac.
7. **M7.** #147's acceptance is not met: two review records still name the Mac and its LAN address.
8. **M8.** Records drift: D-116 has no "Amended by D-185" line, the `Dockerfile` header still says
   "not yet adopted", and three smaller items.

## Verdict

MAJOR

`scripts/wave_check.py:580` reads only PASS, MINOR or BLOCKING under this heading. So until MJ1 is
fixed and a seat confirms it, or the owner rules on it, this verdict holds the close.

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MAJOR (fix before the wave closes, or the owner rules)

- **MJ1** `src/app/workflows/rank.py:41-44`, `:128`; `src/app/workflows/public.py:28-43`;
  `docs/decisions.md:4270`; `docs/release-testflight.md:36-37`. **OpenRouter is left out in name
  only.** D-185 leaves `openrouter` out because "its terms forbid use of its data unless authorised".
  The runbook tells the owner that "OpenRouter's prices" are left out.
  - **The credit stays.** I derived a public artifact from the copy of the served one, then queried it
    through the API in the image's environment. All ten surfaces with picks list this source in
    `sources`: `"Pricing data: BerriAI/litellm (MIT) and OpenRouter's public model catalog,
    https://openrouter.ai/api/v1/models"`. `/v1/boards` carries it too. The cause:
    `attributions_for` adds `PRICING_ATTRIBUTION` to every priced payload (`rank.py:128`), whatever
    `pricing` holds.
    - On the hosted engine, that credits a source whose rows were removed. `rank.py:33-38` and
      REQ-ING-008 (`docs/prd.md:227`, "names only the sources it carries") exist to stop exactly
      this false provenance claim.
    - It also tells App Review that the app uses the data D-185 says it may not use.
  - **The prices stay.** LiteLLM's price file carries OpenRouter's catalogue under
    `openrouter/<vendor>/<model>` aliases, and those are `source = 'litellm'` rows.
    - 456 of them survive in the public artifact, linked to 179 models.
    - Seven models are priced **only** that way, for example `minimax-m1`
      (`openrouter/minimax/minimax-m1`), `step3.5-flash` and `solar-pro4`.
    - Neither D-185 nor the licence research mentions this
      (`docs/research/data-licences-2026-10-04.md:251` says "LiteLLM prices all 313").
  - **Failure scenario.** The owner deploys and invites external testers. Every answer credits
    OpenRouter's catalogue, and prices from that catalogue rank seven models.
    - If OpenRouter's terms forbid this use, the derivation did not achieve its purpose.
    - If LiteLLM's MIT copy is acceptable, the credit is still false: the hosted engine never read
      OpenRouter's API.
    - Either way, D-185 and the runbook say something the artifact does not do.
  - **Why not BLOCKING:** nothing is deployed, and the Stage 5.1 review runs before any deploy. But
    this is the claim #88's derivation exists to make, so it should not wait for another wave.
  - **Fix.**
    - (a) Make the pricing credit follow the rows. Build it from `SELECT DISTINCT source FROM
      pricing`, one credit per pricing source; on the public artifact that is LiteLLM's alone. Add a
      test on a derived artifact that no answer's `sources` names a `LEFT_OUT` publisher.
    - (b) Rule on LiteLLM's `openrouter/` aliases. Either `derive` also removes the `pricing` rows
      whose `alias LIKE 'openrouter/%'` (the seven models then have no price and leave the
      rankings), or D-185 records that LiteLLM's MIT copy stays, and why.
    - (b) is the owner's call. To be consistent with the reason D-185 gives for leaving OpenRouter
      out, I recommend (a) plus removing the aliases.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `.claude/settings.json:49` (the push alternative); `conformance/test-hook-claims.py:281-289`.
  **The widened guard still passes a force push with a digit in the option cluster, and an
  abbreviated `--mirror`.** The new pattern is `[[:space:]]-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$)`
  plus the literal `--mirror`. But `git push` has two digit short options, `-4` and `-6`, and git
  accepts any unique prefix of a long option.
  - **Measured: the guard's own command on 23 payloads.**
    - Exit 2 (blocked) for `-uf`, `-fu`, `--mirror`, `-fq`, `origin x -f`, `--force-if-includes`.
    - Exit 0 (passed) for `git push -4f origin x`, `-f4`, `-6f`, `--mirr`, `--mirro`, `--mi`.
  - **Measured: git 2.50.1, pushing to a local bare repository in the scratchpad.**
    - `git push -4f <bare> main:x` printed `+ 692d35d...eb207db main -> x (forced update)`.
    - `git push --mirr <bare>` printed `- [deleted] x`.
    - `--forc` is refused by git as ambiguous, so `--force` needs no prefix rule.
  - The plan's acceptance (P5) is "any short-option cluster after `push` holding `f`, and
    `--mirror`". A push to `main` stays blocked, by the guard's main-branch rule and by branch
    protection.
  - **Fix.**
    - Use `[[:space:]]-[a-zA-Z0-9]*f[a-zA-Z0-9]*([[:space:]]|$)` and `--mi[a-z]*([[:space:]]|$)`
      (no other `git push` option starts with `mi`).
    - Add `git push -4f origin x` and `git push --mirr origin` to `MUST_BLOCK`.
    - It is a hook change, so it goes to the owner for approval again.
- **M2** `src/app/workflows/public.py:39-44`, `:75`; `tests/unit/test_public_artifact.py:32-42`.
  **The public artifact's "no row of a left-out source" rests on two things no test holds.**
  - **The `VACUUM` is what removes the deleted rows' bytes from the file** (`public.py:75`).
    - I planted its removal and restored the file afterwards (sha256 checked). All 14 tests in
      `test_public_artifact.py` and `test_deploy_hosted.py` still passed.
    - I derived from the copy of the served artifact that way. The shipped file still held
      `ARC-AGI` 573 times, `epoch_arc_agi` 568, `WebDev Arena` 291, `DeepSWE` 131 and
      `TerminalBench` 104. Anyone who pulls the image can read them. With the `VACUUM`: 0 of each.
  - **The removal is a closed list.** `_REMOVE` names two tables, and `_SURVIVORS` checks one
    (`scores`).
    - Nothing leaks today: no other table carries a left-out source (measured; `access` is all
      `epoch_access`).
    - A later table with a `source` column, or a left-out publisher feeding `access`, would ship
      whole.
  - **Related: two rows of the licence research are missing from D-185's table.** Rows 12 and 13
    (`docs/research/data-licences-2026-10-04.md:75-76`) cover the vendor plan pages, and
    Perplexity's terms "do not" permit a free or paid app.
    - The public artifact still carries all 10 plans and 40 plan links.
    - `/v1` serves none of them. I found only CLI readers: `workflows/coverage.py:106-172` and
      `plans.py:235-241`. So they ride in the image unread.
  - **Fix.**
    - Build the delete list from `PRAGMA table_info`, taking every table with a `source` column,
      and check for survivors in each.
    - Add a test that the derived file's bytes hold no `LEFT_OUT` id, and that `PRAGMA
      freelist_count` is 0.
    - Drop the plan rows from the public copy, or say in D-185 why they stay.
- **M3** `.dockerignore:3-8`; `tests/unit/test_deploy_hosted.py:100-108`. **The build context
  leaves out the `Dockerfile`, and Fly's configuration reference says not to.**
  - `*` excludes everything, and `Dockerfile` is never re-included. The `[build]` section of Fly's
    reference says: "When specifying a local Dockerfile, make sure it's not excluded from the Docker
    build context in your `.dockerignore`."
  - The docker CLI puts an excluded Dockerfile back on its own. I could not check offline whether
    `flyctl`'s remote builder does the same, and no image was built in the wave.
  - The context test checks a hand-written list of five paths, not the `COPY` lines. A new `COPY`
    would not be held.
  - **Failure:** the owner's first `fly deploy` stops at the build ("cannot locate Dockerfile"). It
    fails closed, but on the first try.
  - **Fix.** Add `!Dockerfile`, which costs nothing either way. Derive the test's list from the
    Dockerfile's `COPY` sources (leaving out `--from=`) plus the `Dockerfile` itself.
- **M4** `fly.toml:38-41`; `docs/decisions.md:4252`; `docs/release-testflight.md:19-20`;
  `scripts/deploy_hosted_engine.sh:46`. **A first `fly deploy` places two machines, not one.**
  - Fly's documentation (`docs.fly.io/reference/app-availability`): "If a process group has
    services defined, two Machines are automatically created and started when you deploy an app for
    the first time using `fly launch` or `fly deploy`". `fly deploy --ha` is "default true".
  - With `auto_stop_machines = false`, both machines run all the time.
  - D-185 clause 1 and the `fly.toml` comment say "one machine always up". The runbook prices "the
    declared machine ... about two dollars a month". The real bill is about twice that, and it is
    the owner's card.
  - **Fix.** Pass `--ha=false` in the script, with a test that the stand-in `fly` received it. Or
    keep two machines for availability and correct D-185, the comment and the cost.
- **M5** `scripts/deploy_hosted_engine.sh:27-32`, `:46-63`; `docs/release-testflight.md:32-34`.
  **The build stamp names the code, not the data, so the readback cannot tell a new image from the
  old one.**
  - `BUILD="release-$(git rev-parse --short HEAD)"`. The runbook says to redeploy "after each
    nightly refresh you want public", from the same commit.
  - Each of those images carries different data under the same `APP_BUILD`. If the new machines
    never take traffic, the old machine's `/health` answers the expected stamp, and the script
    prints "serves release-<sha>". (`fly deploy` normally fails on its own in that case, so the
    readback adds nothing there.)
  - The practices rule "Releases are immutable and uniquely identified" (L.7) asks for more.
  - The script also accepts any committed HEAD, including a local branch never pushed. The Mac's
    service runs only exports of `origin/main` (#32).
  - **Fix.**
    - Stamp the data too, for example `release-<sha>-<first 8 hex of sha256(build/hosted/advisor.db)>`.
      `/health`'s `build` is a free string.
    - Refuse a HEAD that `git merge-base --is-ancestor HEAD origin/main` rejects.
    - Add a test: two derivations with different data give two stamps.
- **M6** `docs/owner-iphone.md:20-24`; `docs/release-testflight.md:46-49`;
  `ios/Config/Engine.xcconfig:9`, `:15`; `tests/unit/test_testflight_ready.py:77-81`. **The two
  owner documents disagree about `ENGINE_URL`, and the one the owner follows first wins.**
  - `owner-iphone.md` tells the owner to put an unconditional
    `ENGINE_URL = http:/$()/My-Mac.local:8080` in `Engine.local.xcconfig`.
  - That file is included last (`Engine.xcconfig:15`), so its line replaces
    `ENGINE_URL[config=Release]`. The runbook says so itself: "or it replaces the hosted address".
  - The owner's steps put the phone test before the deploy. So when he archives, that file will most
    likely exist, with that line in it.
  - **Failure:** the TestFlight build asks for `http://<his Mac>.local:8080`. Every tester sees
    "cannot reach the engine", and the failure screen shows them his Mac's name (#147's concern).
    The test reads only the tracked file, so nothing catches it.
  - **Fix.**
    - Have `owner-iphone.md` write `ENGINE_URL[config=Debug] = http:/$()/My-Mac.local:8080`. Then
      one file serves both builds.
    - Add a check to the runbook after the archive:
      `plutil -extract EngineURL raw <the archive>/Products/Applications/ModelRanking.app/Info.plist`
      must print the hosted URL.
- **M7** `docs/reviews/m18-wave-1-review.md:51`; `docs/reviews/m18-wave-1-tester.md:112`, `:419`.
  **#147's acceptance is not met: "No tracked file names the owner's Mac or home address" (wave
  plan, P1).**
  - `git grep -i -E "umut-macbook|192\.168\.0\.26"` finds the Mac's name and its LAN address in two
    ratified review records.
  - The four files #147 named are clean. The git history keeps the name in any case, and the
    repository is public.
  - **Fix.** Either scrub the two records, which needs a ruling because they are `ratified`, or
    narrow the acceptance in the plan and on #147 to "outside ratified records and the history", and
    say so on the issue before it closes.
- **M8** Records drift. **Each item is small, and they share one fix: a records commit.**
  - `docs/decisions.md:637-688`: D-185 says it "Amends D-116" (`:4239`), but D-116 has no
    `**Amended by D-185**` line. D-116 has one for D-177 (`:688`).
  - `Dockerfile:1-3` still reads "PROPOSAL — M6-W4, not yet adopted ... not treated as settled until
    he says so". `fly.toml:1-4` and D-185 adopt it.
  - `docs/release-testflight.md:22` says "change it in three places" and then names four: `app`,
    the Host list, the check's `Host` and `ENGINE_URL[config=Release]`. `fly.toml:9-10` names two of
    the four. The tests hold all four equal, so a partial rename fails `make test`, but the comments
    give the owner the wrong count.
  - `docs/plans/m19-wave-5-plan.md:32-34` says six sources are left out and three surfaces go dark.
    D-185 and the code have seven and four (`epoch_webdev`, `web-dev`). The plan was not amended.
  - `docs/release-testflight.md:50-55` says nothing about the build number.
    `CURRENT_PROJECT_VERSION = 1` (`ios/ModelRanking.xcodeproj/project.pbxproj:239`, `:260`), and App
    Store Connect refuses a second upload with the same build number.

### PASS (what looks good)

- **The hosted path boots as configured.** I rebuilt it by hand:
  - The build stage's install, done offline from a copy of the context: `pyproject.toml` and `src`.
    setuptools only warns that `README.md` is missing.
  - The package imported from `/`, with the image's environment: `APP_ENV=production`, an
    `APP_BUILD`, `MODEL_RANKING_BIND=0.0.0.0` and `MODEL_RANKING_ALLOWED_HOSTS=model-ranking.fly.dev`.
    The artifact sat in a 0555 directory, as `/srv` is to `appuser`.
  - Results:
    - `STARTUP_WARNINGS` was empty.
    - `/health` answered 200 with `servable`. `/v1/categories`, `/v1/boards` and
      `/v1/recommendations` answered 200 on Host `model-ranking.fly.dev`.
    - Host `other.example` and Host `127.0.0.1` got 400.
    - Without the list, the import raised `ConfigError` naming `MODEL_RANKING_ALLOWED_HOSTS`.
- **The public artifact matches D-185's numbers.** Derived from the copy of the served artifact:
  - 815 score rows and 439 price rows were removed, and no left-out source is in `scores`,
    `pricing` or `access`.
  - Freelist 0, journal mode `delete`. The median is rebuilt (`px_median` 303 rows).
  - `abstract`, `agentic-coding`, `computer-use` and `web-dev` answer `no_evidence` through D-121's
    path. `coding` ranks 32 models, against 54 on the full artifact, as D-185 says. None of the 14
    tasks answered a 5xx.
- **`fly.toml` uses only keys Fly's configuration reference lists:** `[build] build-target`, and
  `[[http_service.checks]]` with its `headers` subsection. Removing the top-level `[checks.health]`
  is right too: that check reached the machine with no Host header, which the Host list refuses.
- **The deploy script fails closed** on a dirty tree, a missing artifact, a failed derivation
  (`set -e`), a failed `fly deploy`, and a health answer from another build. Its tests use stand-ins
  for `fly` and `curl`, so no request leaves the machine.
- **#145's fix is right.** `engine_service.sh` runs with `set -u` only, so `$?` right after the
  assignment is the substitution's status. The test plants a `python` that exits 137 with no output
  (`test_engine_service.py:604`), and reverting the condition turns it red.
- **The tests are real.** I planted faults and restored each file byte-identical (sha256 checked).
  These were caught:
  - `ENV MODEL_RANKING_BIND` removed (2 failures);
  - the check's `Host` header removed;
  - #145 reverted;
  - a `FROM` by tag;
  - the encryption key removed;
  - the Release URL removed;
  - the pricing `DELETE` removed (caught by the medians test);
  - the median rebuild removed;
  - the `chmod` removed.
  The `VACUUM` removal survived (M2). So did the survivor check switched off, a defence that cannot
  fire unless a `DELETE` fails.
- **The TestFlight pieces are right.**
  - The icon is 1024 × 1024 RGB with no alpha. I looked at it: a placeholder bar chart.
  - The target is a file-system-synchronized group (`project.pbxproj:9-14`), so the asset catalog
    and the privacy manifest are built in without editing the project file.
  - The privacy manifest's single reason, `CA92.1` for UserDefaults, matches `@AppStorage`
    (`ContentView.swift:71`). It is the only required-reason API I found in a wider grep (file
    timestamps, boot time, disk space, keyboards).
  - `ITSAppUsesNonExemptEncryption = false` is right for an app whose only encryption is HTTPS
    through `URLSession`. The client accepts `https` (`EngineClient.swift:171-172`).
- **The guard does not over-block.** `-u`, `--follow-tags`, `--no-verify -u` and `-d` still pass.
  The only extra block is `-of`, a push option named `f`, which does no harm.
- **The commits are in order.** Red-then-green pairs. The hook change is in its own commit,
  labelled for the owner's approval. The commits carry the owner's identity and the `GP-Agent`
  trailer, with no AI attribution. There are no drive-by edits: the three test edits outside the
  wave's own files are what the new asset catalog, privacy manifest and writable open need.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), enumerated from code:

- **D-171, now at boot: a process that serves beyond loopback names the Hosts it answers to.**
  - The launcher with `--lan`: the preflight refuses, now on its exit status too.
    `test_engine_host.py::test_a_bind_beyond_loopback_needs_a_list_of_hosts`,
    `test_engine_service.py::test_a_preflight_that_dies_without_a_word_stops_the_start`.
  - The image's `serve` and `hosted` stages (`CMD --host 0.0.0.0`): `ENV MODEL_RANKING_BIND`.
    `test_hosted_engine.py::test_the_image_tells_its_startup_check_where_it_binds`,
    `::test_the_image_refuses_to_boot_beyond_loopback_with_no_host_list`.
  - The Fly deployment: `MODEL_RANKING_ALLOWED_HOSTS` and the check's `Host`.
    `test_hosted_engine.py::test_the_hosted_engine_answers_to_its_own_name_and_is_checked_by_it`.
  - `make run`, or uvicorn started by hand: no boot check. The request-time fallback holds it
    (`test_engine_host.py::test_without_a_list_a_request_arriving_on_a_network_address_is_refused`).
  - A container started with `-e MODEL_RANKING_BIND=127.0.0.1` while its `CMD` binds every
    interface passes the boot check. Only the same request-time fallback holds it. This is not a
    new hole.
- **#88: the public artifact carries no left-out source's data.**
  - `derive`'s `DELETE`s: `test_public_artifact.py::test_the_public_artifact_carries_no_row_of_a_left_out_source`,
    `::test_the_price_medians_are_rebuilt_from_the_kept_prices`.
  - The deploy script ships what `derive` wrote:
    `test_deploy_hosted.py::test_a_deploy_stamps_the_commit_ships_the_public_artifact_and_checks_health`.
  - The deleted rows' bytes (`VACUUM`): none (M2).
  - Other tables, present or future: none (M2).
  - The served credit text, and LiteLLM's `openrouter/` aliases: none (MJ1).
- **INV-81 / #141: an image install fetches nothing beyond the locks.** Both `FROM` lines:
  `test_dependency_locks.py::test_the_serving_image_names_its_base_by_digest`,
  `::test_the_base_check_reads_tags_digests_and_stages`.
- **#142: no force or mirror push passes the guard.** `MUST_BLOCK` in
  `conformance/test-hook-claims.py:281-287`. A digit in the cluster, or an abbreviated `--mirror`:
  none (M1). A command continued onto a second line: none (K1).

Gaps: MJ1, M1, M2, K1.

## Acceptance criteria evidence (REQUIRED for PASS verdict)

The wave scopes no REQ-IDs. Its tests cite issues and D-IDs (D-121, D-126, D-171). By phase
(`docs/plans/m19-wave-5-plan.md`, "Phases"):

- **P1, #147.**
  - Changed: `tests/unit/test_engine_host.py:23`, `:37`, `:44`, `:75`, `:84-87`, `:111`, `:123`;
    `ios/EngineTests/EngineClientTests.swift:56`, `:720-750`;
    `ios/EngineTests/LanguageTests.swift:446-448`; `docs/owner-iphone.md:19-23`;
    `ios/Config/Engine.xcconfig:4`.
  - Hole: M7.
- **P1, #145.** `scripts/engine_service.sh:59-74`; `tests/unit/test_engine_service.py:604`. Red at
  `b5beea9`.
- **P1, #141.** `Dockerfile:12`, `:24`; `tests/unit/test_dependency_locks.py:334`, `:341`. Red at
  `6fb3289`.
- **P2, #94.**
  - Changed: `Dockerfile:37`, `:57-58`, `:66-68`; `fly.toml:15-18`, `:20-24`, `:53-60`;
    `scripts/deploy_hosted_engine.sh`; `.dockerignore`.
  - Tests: `tests/unit/test_hosted_engine.py:64`, `:71`, `:92`, `:105`;
    `tests/unit/test_deploy_hosted.py:62`, `:78`, `:84`, `:92`, `:102`. Red at `5ea0254` and
    `c70d2bf`.
  - #94's "serves that name and refuses another" was measured on the installed package (PASS above).
  - Holes: M3, M4, M5; R1, R2.
- **P3, #88.**
  - Changed: `src/app/workflows/public.py:28-85`; D-185 at `docs/decisions.md:4233-4292`.
  - Tests: `tests/unit/test_public_artifact.py:27`, `:32`, `:45`, `:61`, `:77`. Red at `8879619`.
  - Holes: MJ1, M2; R3.
- **P4, TestFlight readiness.**
  - Changed: `ios/ModelRanking/Assets.xcassets/AppIcon.appiconset/`;
    `ios/ModelRanking/PrivacyInfo.xcprivacy`; `ios/Config/Info.plist:7-8`;
    `ios/Config/Engine.xcconfig:9`, `:11`; `docs/release-testflight.md`.
  - Tests: `tests/unit/test_testflight_ready.py:43`, `:56`, `:71`, `:77`. Red at `fe1bd13`.
  - Holes: M6, M8.
- **P5, #142.** `.claude/settings.json:49`; `conformance/test-hook-claims.py:281-289`. Red at
  `48dc201`. Holes: M1, K1.
- **P6.** This file. The Tester and the Stage 5.1 review follow.

## Every file in the diff

| File | What changed | Read |
|---|---|---|
| `.claude/settings.json` | push guard: option clusters holding `f`, `--mirror` | M1, K1 |
| `.dockerignore` | new: allow-list build context | M3 |
| `Dockerfile` | base by digest; `MODEL_RANKING_BIND`; health check sends a listed Host; `hosted` stage | M3, M8, R2 |
| `conformance/test-hook-claims.py` | three new `MUST_BLOCK`, one `MUST_ALLOW` | M1 |
| `docs/decisions.md` | D-185 | MJ1, M2, M4, M8 |
| `docs/owner-iphone.md` | placeholder Mac name | M6 |
| `docs/plans/m19-wave-5-plan.md` | the wave plan (new) | M8 |
| `docs/release-testflight.md` | the owner's runbook (new) | MJ1, M4, M5, M6, M8 |
| `docs/warnings.ledger.md` | W-129's M19-W5 note | ok |
| `fly.toml` | `hosted` target, the Host list, the check with `Host`, no volume | M4, R1 |
| `ios/Config/Engine.xcconfig` | Release URL, the app icon setting, placeholder Mac name | M6 |
| `ios/Config/Info.plist` | `ITSAppUsesNonExemptEncryption` false | ok |
| `ios/EngineTests/EngineClientTests.swift`, `LanguageTests.swift` | placeholder names and addresses | ok |
| `ios/ModelRanking/Assets.xcassets/**` | the icon (new) | ok |
| `ios/ModelRanking/PrivacyInfo.xcprivacy` | the privacy manifest (new) | ok |
| `scripts/deploy_hosted_engine.sh` | the deploy (new) | M4, M5 |
| `scripts/engine_service.sh` | #145 | ok |
| `src/app/workflows/public.py` | the public artifact (new) | MJ1, M2, R3 |
| `tests/unit/test_dependency_locks.py` | #141 check | ok |
| `tests/unit/test_deploy_hosted.py` | deploy tests (new) | M3 |
| `tests/unit/test_engine_host.py` | placeholder names and addresses | ok |
| `tests/unit/test_engine_service.py` | #145 test | ok |
| `tests/unit/test_hosted_engine.py` | #94 tests (new) | ok |
| `tests/unit/test_ios_client_contract.py` | catalog `Contents.json` exempt | K2 |
| `tests/unit/test_public_artifact.py` | #88 tests (new) | M2 |
| `tests/unit/test_readonly_uri.py` | `public.derive` listed as a writable open | ok |
| `tests/unit/test_router_hints.py` | catalogs skipped; `.xcprivacy` read as a plist | K2 |
| `tests/unit/test_testflight_ready.py` | TestFlight tests (new) | M6 |

## K.8 contract drift check

The milestone plan's contracts (`m19-plan.md:142-154`), `grep -n` at `d9f4e74`:

```
src/app/adapter/main.py:952:PUBLIC_PICK_FIELDS = frozenset(
src/app/workflows/registry.py:567:DISPLAY_NAMES: dict[str, str] = {
src/app/workflows/registry.py:699:def claude_word_order(name: str) -> str:
src/app/workflows/rank.py:47:ATTRIBUTIONS = (
src/app/workflows/rank.py:59:SOURCE_ATTRIBUTION: dict[str, str] = {
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:526:enum ModelOutputBoundary {
ios/ModelRanking/Engine/FrontDoor.swift:278:public struct GapRegisterStore {
ios/ModelRanking/Engine/AnswerPlan.swift:174:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/ContentView.swift:1480:struct HeldReading: Equatable {
tests/conftest.py:226:def pytest_configure(config: pytest.Config) -> None:
src/app/adapter/main.py:476:ALLOWED_HOSTS_VAR = "MODEL_RANKING_ALLOWED_HOSTS"
src/app/adapter/main.py:478:BIND_VAR = "MODEL_RANKING_BIND"
```

- Every declared symbol exists with the same name and signature. The lines moved in earlier waves.
- `git diff ae2c528 d9f4e74 -- src/app/adapter ios/ModelRanking/Engine tests/conftest.py
  src/app/workflows/rank.py src/app/workflows/registry.py` is empty. No `/v1` field or route
  changes.
- `MODEL_RANKING_BIND` and `MODEL_RANKING_ALLOWED_HOSTS` keep D-171's names. The image and `fly.toml`
  use the constants' spelling, and `test_hosted_engine.py` reads them through `adapter.BIND_VAR`
  and `adapter.ALLOWED_HOSTS_VAR`.
- Verdict: **OK**

## K.9 candidates spotted outside this wave's scope

- **K1** `.claude/settings.json:49`. **The guard reads a command one line at a time, so a
  backslash line continuation hides any destructive flag from it.**
  - `grep` matches each line on its own, and the `git ... push` and the `--force` land on different
    lines. Measured: `git push \` + newline + `  --force origin x` exits 0, and so does `-uf` on the
    second line.
  - This is true of every alternative in the guard, and it predates the wave.
  - Remote deletes (`--delete`, `-d`, `origin :x`, `--prune`) are also not guarded; only `main` is.
  - An enhancement: join continued lines (`\` + newline → space) before matching.
- **K2** `tests/unit/test_router_hints.py:660`; `tests/unit/test_ios_client_contract.py:546-549`.
  **Anything inside an `.xcassets` folder now passes both client gates.** The "no way off the
  device" scan skips every file in a catalog. The client contract test refuses only JSON other than
  `Contents.json`. A data asset (`*.dataset/` with a non-JSON payload) would ship past both. An
  enhancement: inside a catalog, allow only `Contents.json` and image files.

## Risks queued to next M

- **R1** `fly.toml:51-60`. **Whether Fly's service check sends the `Host` header named in its
  `headers` subsection is not something I could confirm offline.** The reference lists `headers`
  with an `Authorization` example, and says nothing about `Host`.
  - If the checker sends the machine's address as Host instead, every check gets 400. The machine is
    then never routed to, and the first `fly deploy` fails waiting for health. That fails closed,
    but it stalls the release.
  - What would show it: `fly checks list` after the first deploy, or a deploy that times out on
    health.
  - A fallback that keeps D-171 whole: a TCP service check instead of the HTTP one, with the script's
    HTTPS readback as the build check.
- **R2** `Dockerfile:12`, `:24`, `:66-68`; `.dockerignore:8`. **The image has never been built.**
  - These have been read, not run:
    - the digest, "read 2026-10-07" by its comment;
    - the re-include of a file inside the excluded `build/` directory;
    - the artifact `COPY`;
    - `pip install .` with no `README.md` (setuptools 84 only warns, measured offline; the image
      uses `build.lock`'s version).
  - What would show it: the first remote build failing.
  - Before the first deploy, one `docker build --target hosted .` on the owner's Mac with Docker
    running would settle all four. That needs the network, so it is the owner's step.
- **R3** `src/app/workflows/public.py:58-75`. **The public copy keeps the source's journal mode.**
  - Measured: a WAL-mode source gives a WAL-mode public artifact. In WAL mode, a read-only open
    needs a `-shm` file beside the database. `appuser` cannot create one in the root-owned `/srv`, so
    the startup check would refuse to boot.
  - Today's served artifact is in `delete` mode, and no code in `src/app` sets WAL, so this is
    latent.
  - What would show it: a deploy whose logs say "cannot be opened read-only".
  - A one-line guard: `PRAGMA journal_mode=DELETE` before the `VACUUM`.

## Gates and probes run

- **`make check-fast`**, with the guard-bin stubs on `PATH`: **PASS** in 107.6 s.
  - The lint, typecheck, records, client-decls and swift-test legs passed.
  - Test leg: 2096 passed, 25 skipped. `--derive`: "CI will skip 83 of 2121", budget 83.
- The wave's ten test files: 220 passed. `conformance/test-hook-claims.py`: PASS.
- **Planted faults**, eleven, each restored byte-identical (sha256 checked), with `git status`
  empty after each:
  - in `public.py`: the `VACUUM`, the pricing `DELETE`, the median rebuild, the `chmod`, the
    survivor check;
  - in `Dockerfile`, `fly.toml`, `engine_service.sh`, `Info.plist` and `Engine.xcconfig`: one each,
    and a second in `Dockerfile` (the PASS list above).
- **Guard payloads:** 23 through the guard's own command, plus 4 multi-line ones.
- **git probe:** `-4f`, `--mirr` and `--forc` pushed to a local bare repository in the scratchpad.
  No remote was involved.
- **The public artifact:** derived from the worktree's copy of the served artifact, then served by
  the API in the image's environment from a 0555 directory. Every one of the 14 tasks was queried,
  and I compared the answers with the full artifact.
- **WAL probe** (R3) on a scratch copy.
- **One slip, mine, now undone.** The offline `pip install --prefix` that rebuilt the image's
  install also uninstalled the worktree venv's editable install of the project. pip does this when
  the distribution is already installed. I put it back with the Makefile's own line, offline:
  `pip install --no-index --no-deps --no-build-isolation -e .`. After that, `import app` resolved to
  the worktree's `src` again and `git status` was empty. The `make check-fast` above ran before the
  slip; every probe after it ran with the editable install back in place.
- **Network:** `gh issue view` for the six issues. WebFetch of three Fly documentation pages: the
  configuration reference, health checks, and app availability (plus `flyctl deploy`).
- I did not run `fly`, the deploy script without stand-ins, the service installer, launchctl,
  docker, `simctl` or `xcodebuild`. No `os.abort()`.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-07 · Commit range: `ae2c528..d9f4e74`*
