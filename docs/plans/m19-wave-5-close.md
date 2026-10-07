---
record_type: wave
id: m19-wave-5-close
status: draft
process_version: v6.6
date: 2026-10-07
---
# Wave-Close Checklist — M19 Wave 5, a first release: the engine hosted, the app on TestFlight

**Called by the owner on 2026-10-07; nothing is deployed or uploaded by the agent.** The engine is
ready for Fly.io (D-116, D-185) with a public artifact of the sources whose terms permit it (#88), and
the app is ready for TestFlight. The owner's steps are `docs/release-testflight.md`.

**What the wave delivers.**
- #94: the image tells its startup check where it binds, so with no Host list it refuses to boot; a
  `hosted` stage carries the artifact; `fly.toml` names `model-ranking.fly.dev` as the one Host and its
  health check sends it. `scripts/deploy_hosted_engine.sh` deploys only `origin/main`'s tip, on one
  machine, stamped with the commit and the data's digest, and reads `/health` back.
- #88: `app.workflows.public` derives the public artifact offline, without seven sources, LiteLLM's
  copies of OpenRouter's prices, the vendor plans, or any byte of them; the pricing credit follows the
  sources served (D-185, with the licence table and the cost: four surfaces dark, `coding` 32 of 54).
- TestFlight: an app icon (a placeholder), a privacy manifest, the encryption answer, a scheme that
  archives in Release, and a Release `ENGINE_URL` that no local file can replace (an unsigned archive
  was made and carries `https://model-ranking.fly.dev`).
- #145 (the launcher's preflight by exit status), #141 (the base by digest), #147 (a placeholder Mac
  and documentation addresses), `make journey` and `make cold-start` wired.
- #142 and the security review's S5, S6: the Bash guard, widened, in four commits marked OWNER
  APPROVAL (`9a793ed`, `d385074`, `0b8ae4a`, `fb2040d`); what it still misses is #189.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m19-wave-5-plan.md` (deleted in this close) and `docs/plans/m19-plan.md` §2 W5: **HIGH**, since the serving image, the launcher (`scripts/*engine_service*.sh`, a security glob) and the Host list change, a public surface is prepared, and `.claude/settings.json` changes (§3); the owner reviews the wave (AGENTS.md §3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #145 (`b5beea9`, `5040948`), #141 (`6fb3289`, `160e1a7`), #94 (`5ea0254`, `ff7205a`; `c70d2bf`, `1a8aabb`), #88 (`8879619`, `941d770`), TestFlight (`fe1bd13`, `96f6010`), #142 (`48dc201`, `9a793ed`; `2dc5b9f`, `d385074`; `331aed0`, `0b8ae4a`; `73a8624`, `fb2040d`), the release gates (`f2a5de3`, `7fde40d`), the reviews (`92dd862`, `dea39c8`; `f84114f`, `ff940b9`), the security review (`31fff71`, `60735c9`) and the Tester (`6b0234e`, `fdf6701`). The release re-read's findings were records and holds, with their tests in the fix (`0a80b65`). #147 is a scrub with no red commit; the Tester's scan now holds it. Each red commit's only failures were its own tests (measured with `make check-fast`), except `2dc5b9f`, committed without the run (its fix `d385074` ran green; a row in `docs/control-events.csv`, recorded at the M19 closure); one red commit failed lint first and was corrected before it was pushed (`f84114f`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m19-wave-5-review.md` (`662b4ab`): **MINOR**, M1–M7, K1, R1–R5, on `6c9ce17..1307a00`, after round 1 (`docs/reviews/m19-wave-5-review-round-1.md`, MAJOR). `docs/reviews/m19-wave-5-tester.md` (`ab0a8f3`): **MINOR**, M1–M3, on `6c9ce17..6c98dd7`. The Stage 5.1 security review (`docs/reviews/m19-closure-security-review.md`, MAJOR) and its re-read (`docs/reviews/m19-release-security-reread.md`, MINOR: the owner may deploy after the owner's account steps) ran on the release. Each seat had its own worktree, venv and artifact copy, behind stubs refusing `launchctl`, `simctl` and `xcodebuild` (D-174) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | The milestone plan's W5 required the Stage 5.1 review before any deploy: it ran (`0b2ed00`) and was re-read after the fixes (`8fc5ca0`); both are also M19's closure seat (D-172) | ✅ |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 59 faults: 35 caught as delivered, all 59 with its twenty test functions (`ab0a8f3`); every file restored byte-identical (sha256). The security seats planted 27 and 22, and the second review 25; each survivor is a finding fixed or filed. The author's own plants (the VACUUM, the uncommitted-tree check) are in their commits | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | #94 through the Dockerfile's stages and `fly.toml` (`test_hosted_engine.py`), the startup check (`::test_the_image_refuses_to_boot_beyond_loopback_with_no_host_list`) and the deploy script with stand-ins (`test_deploy_hosted.py`). #88 through `public.derive` and `/v1` on the derived file (`test_public_artifact.py`). TestFlight through the app's files and scheme (`test_testflight_ready.py`). #145 through the launcher (`test_engine_service.py::test_a_preflight_that_dies_without_a_word_stops_the_start`). #141 (`test_dependency_locks.py::test_the_serving_image_names_its_base_by_digest`). #147 (`test_security_surface.py::test_no_tracked_file_names_a_mac_or_home_address_beyond_the_placeholders`). #142 through the guard itself (`conformance/test-hook-claims.py`). The gates through `docs/journey.sh` and `docs/cold-start.sh` (`test_release_gates.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: INV-86 (the hosted engine) and INV-87 (its public artifact), each with its tests; G-8 closed by #141; G-7 narrowed and cites #189 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python, restored from saved bytes in a `finally` and compared. The session started outside the repository, so its hooks were not loaded (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | INV-86's producers: the Dockerfile's `serve` and `hosted` stages, `fly.toml`, the startup check and the deploy script. INV-87's: `app.workflows.public` (every table with a `source` column) and the pricing credit (`rank.served_pricing_sources`). Gaps tracked: #187 (no rate limit), #188 (the budget argument), #189 (the guard), #190 (the owner's settings) | ✅ |
| 9b | Scope & draft PR | Delivered: #94, #88 (the public artifact; the ruling taken on the standing instruction, the owner may overrule), #141, #145, #147, the TestFlight files. #142 delivered for the owner's approval; its second half (a session started outside the repository) and the remaining spellings are #189. Not this wave: #81, #115 (the owner's). Filed: #185, #187, #188, #189, #190. Draft PR on `wave/m19-w5` against `wave/m19-w4` (merge W4's first) | ✅ |
| 9a | Economy | `git diff --shortstat d324669 HEAD`: 51 files changed, 4213 insertions(+), 107 deletions(-) before this close's own records. Over the ~400-line guide: the code and configuration are about 600 lines; the rest are tests (each check with its planted cases), five review records and the runbook | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · make gate · xcodebuild (an unsigned Release build and archive) · gates SKIPPED: a Docker build (the daemon was not running; Fly's builder builds the image at deploy, and make cold-start builds it locally) · tokens/cost: not measured · outcome: shipped as a draft PR`. Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-07 · Wave commit range: `6c9ce17..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `ff940b9` (the script takes no argument but --dry-run); the guard's spellings are #189 |
| review M2 | fixed `0b8ae4a` (the --mirror false positive); the guard's other spellings are #189 |
| review M3 | fixed `ff940b9` |
| review M4 | fixed `ff940b9` |
| review M5 | fixed `ff940b9` |
| review M6 | fixed `ff940b9` |
| review M7 | fixed `ff940b9` |
| review K1 | #189 |
| review R1 | refused — whether Fly's health check sends its Host header shows only at the first deploy; the runbook names the TCP check to fall back to |
| review R2 | refused — the image builds on Fly's builder at deploy and with make cold-start where Docker runs; no Docker daemon ran in this session |
| review R3 | fixed `8fc5ca0` (the release security re-read) |
| review R4 | fixed `ff940b9` |
| review R5 | fixed `ff940b9` |
| tester M1 | fixed `fb2040d` |
| tester M2 | fixed `fdf6701` |
| tester M3 | fixed `fdf6701` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        Dockerfile fly.toml .dockerignore .claude/settings.json conformance/test-hook-claims.py scripts/deploy_hosted_engine.sh scripts/engine_service.sh src/app/workflows/public.py src/app/workflows/rank.py src/app/workflows/recommend.py src/app/workflows/standings.py docs/journey.sh docs/cold-start.sh docs/release-testflight.md docs/owner-iphone.md docs/decisions.md docs/warnings.ledger.md docs/security-invariants.md docs/plans/m19-wave-5-plan.md docs/reviews/m19-wave-5-review-round-1.md docs/reviews/m19-wave-5-review.md docs/reviews/m19-wave-5-tester.md docs/reviews/m19-closure-security-review.md docs/reviews/m19-release-security-reread.md docs/reviews/m18-wave-1-review.md docs/reviews/m18-wave-1-tester.md ios/Config/Engine.xcconfig ios/Config/Info.plist ios/ModelRanking/Assets.xcassets ios/ModelRanking/PrivacyInfo.xcprivacy ios/ModelRanking.xcodeproj/xcshareddata/xcschemes/ModelRanking.xcscheme ios/EngineTests/EngineClientTests.swift ios/EngineTests/LanguageTests.swift tests/unit/test_hosted_engine.py tests/unit/test_public_artifact.py tests/unit/test_deploy_hosted.py tests/unit/test_release_gates.py tests/unit/test_testflight_ready.py tests/unit/test_engine_service.py tests/unit/test_dependency_locks.py tests/unit/test_engine_host.py tests/unit/test_security_surface.py tests/unit/test_router_hints.py tests/unit/test_ios_client_contract.py tests/unit/test_recommend.py tests/unit/test_board_standings.py tests/unit/test_refresh_attribution_fingerprint.py tests/unit/test_serializer_parity.py tests/unit/test_readonly_uri.py docs/plans/m19-wave-5-close.md (and the plan deleted)
Mutant set author: the Tester seat (59), the two security seats (27, 22) and the second review (25); the author's plants are supporting evidence only
Observed RED:   the Tester's 24 survivors die on its twenty functions; the security review's S4 mutants on test_hosted_engine.py and test_public_artifact.py; the second review's M4 and M6 holds
Owner instruction: "we need to deploy the engine to a real supabase or something and we need to go for testflight" and "you do not need to wait for the merges ... solve the bugs as issues triaged medium and above" (owner, 2026-10-07); the standing instruction of 2026-09-29, under which #88's public artifact was taken
K.8 contracts:  no /v1 field or route changes; the pricing credit in `sources` and `attributions` names only the price sources served; fly.toml and the Dockerfile's hosted stage are new deploy contracts (K.10, the owner's review)
Stopped at three attempts: NONE
Hand-kept lists: public.LEFT_OUT (each source with its licence reason), the guard's patterns (#189), `.dockerignore`'s allow list
```
