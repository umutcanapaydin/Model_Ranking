---
record_type: wave
id: m18-wave-1-close
status: draft
process_version: v6.6
date: 2026-10-01
---
# Wave-Close Checklist — M18 Wave 1, the app on the owner's iPhone

**The engine can serve the owner's phone on the network the Mac is on, by opt-in, and checks every
Host** (D-171, its ten notes, and REQ-DEV-001).
- **The engine.**
  - With a Host list (`MODEL_RANKING_ALLOWED_HOSTS`), a request to any other Host gets 400
    `unknown_host`, on every path.
  - With no list, a request that arrived on a network address rather than loopback is refused,
    whatever started the engine.
  - `make run` binds 127.0.0.1.
- **The installer.**
  - It binds loopback by default; `--lan` opens every interface, with the Mac's own names on the
    list.
  - A reinstall keeps the mode it finds and says so, and `--no-lan` closes it.
- **The app.**
  - Its engine address is a build setting (`ENGINE_URL` → the Info plist), loopback when unset or
    invalid, and set by the owner in a git-ignored file with his team and bundle id.
  - `ios/app.sh` always builds its simulator app for loopback.
  - A failure to reach the engine shows the address the app asked, in both languages.
- **The owner's steps** are `docs/owner-iphone.md`.

**The owner ruled once during the wave** (D-172, 2026-09-29): no security pass per wave; one security
seat per milestone, at its closure.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md:39` "W1 — The app on the owner's iPhone (risk: **HIGH**; #87, #86)": the engine listens beyond loopback for the first time. The wave plan `docs/plans/m18-wave-1-plan.md` is deleted in this close, as DevFlow requires | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red first, in pairs: the engine `41be53a`→`eccd5b1`, the app `e94cd7c`→`fee46fd`, review round 1 `b718f70`→`8e54068`, round 2 `a7f4b3b`→`a04fdd5`, round 3 `456eac2`→`8cfdd98`. The Testers' missing tests, for code already right, are `ed8b7e7` and `c709983`. `make check-fast` PASS before every commit, its exit code read, not piped; each red commit carried only its intended failures. The LAN path was driven end to end on the simulator before the owner stopped simulator runs on 2026-10-01 (a scratch engine through the `.local` name) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m18-wave-1-review.md`: the third Code-Reviewer's **PASS-WITH-MINORS** at `8e6232a`, after two BLOCKING rounds (`e05ae15`: B1, the bind rule read a variable, not the bind; `78aa6d1`: B2, the page and D-171 described an error message and a firewall that did not behave as written). `docs/reviews/m18-wave-1-tester.md`: the second Tester's **PASS-WITH-MINORS**, after the first seat's BLOCKING (`90109a7`: T1, the plain-reinstall path untested; T2, coverage dropped on `main.py`). Five seats, one after another, each in its own worktree | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (the owner's ruling, 2026-09-29), recorded in the M18 plan's amendment. The milestone's closure seat reads this slice; the second Tester's N11 (loopback answers every Host with no list) is queued to it | N/A |
| 5 | Tester fault-injection, restore byte-identical | First Tester: 68 faults, 58 killed, 1 equivalent, 9 survived; each survivor got its test in `ed8b7e7`. Second Tester: 63 faults, 54 killed, 2 equivalent, 7 survived (kill rate 88.5 %); five got tests in `c709983`, and C5 and C9 (the view's line hidden or never reached) are on #69, since no test runs `ContentView`. Replays: the third Code-Reviewer's 29 faults (28 killed, 1 equivalent) and the first Tester's eight survivors, all killed by `ed8b7e7`. Every fault restored in place and checked by sha256, `git hash-object` and `git diff --quiet`; all tracked files matched the baseline after each run | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-DEV-001's evidence row in `docs/prd.md`, 31 tests by line. The Host rule through the FastAPI app (`tests/unit/test_engine_host.py`, every path). The installer and launcher run as scripts, with stubs for launchd (`tests/unit/test_engine_service.py`). The app's address and its failure line through `EngineClient` (`EngineClientTests.swift`, `LanguageTests.swift`). Gaps, named: the view's behaviour is held by a source pin (#69); `client-decls` typechecks it but nothing runs it, and no gate builds the app, so the owner's first run on his phone is the end-to-end proof | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | "The engine's network surface is loopback unless the owner opted in, and an exposed engine answers only its listed Hosts" (D-171). Negatives: a foreign Host refused on every path (`test_every_path_is_behind_the_host_check`), a network arrival refused with no list (`test_without_a_list_a_request_arriving_on_a_network_address_is_refused`), the launcher refusing a bind beyond loopback with no list, the default wrapper on loopback. There is still no single invariants list; this row is on #89 (R2) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, attested by each seat in its file. The author's reverts of hand-made faults were in place, checked with `git hash-object` | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a response: one `http` middleware (`_known_host`, `src/app/adapter/main.py`) before every route, held on `/health`, `/v1` and an unknown path. Producers of the bind: the launcher's one `--host` (`scripts/engine_service.sh:75`), `make run`, and `Dockerfile:46` (#94). Producers of the wrapper: the installer's `wrapper()` only. Producers of the app's address: `EngineClient.localDefault` only | ✅ |
| 9b | Scope & draft PR | Draft PR on `wave/m18-w1`, closing #87 and #86. Delivered as planned, plus the owner's page and D-172. Filed and triaged: #94, #95, #96, #98 (#97 filed, then closed as measured wrong). Noted on #69 (T4, T12), #84 (D-172), #89 (R2). The PR opens after the reviews and `/pre-merge`, as the owner asked | ✅ |
| 9a | Economy | `git diff --shortstat e82011b HEAD`: 27 files, +1846/−20 before this close. Code (`src/`, `scripts/`, `ios/ModelRanking/`, `ios/Config/`, `ios/app.sh`, `Makefile`, the project file, `.gitignore`): 12 files, +185/−12. The rest is tests, five review rounds, D-171/D-172 and the owner's page. VARIANCE noted: three code-review rounds and two Tester seats | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. Not run, by the owner's instruction (2026-10-01, NO-ENVIRONMENT): the simulator and any app build after `a04fdd5`; the seats typechecked the app with `swiftc` instead. **Incident:** the second Code-Reviewer seat ran the installer for real by mistake (2026-09-29), replacing the owner's launchd job with a scratch copy; nothing was exposed (loopback only), and the owner's own job was reloaded on 2026-10-01. Later seats ran behind command guards. Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-01 · Wave commit range: `e82011b..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M9 | fixed `8cfdd98` |
| review M10 | fixed `8cfdd98` |
| review M11 | fixed `456eac2` |
| review M12 | fixed `8cfdd98` |
| review M13 | fixed `8cfdd98` |
| review M14 | fixed `8e6232a` |
| review K4 | #96 |
| review K5 | refused — measured: `make client-decls` (in `check-fast` and `make gate`) typechecks `ContentView.swift` against the iOS SDK, and failed (exit 2) on a type error injected into the address line; #97 is closed with that |
| review R4 | fixed `8cfdd98` |
| review R5 | fixed `8cfdd98` |
| tester T8 | fixed `c709983` |
| tester T9 | fixed `c709983` |
| tester T10 | fixed `c709983` |
| tester T11 | fixed `c709983` |
| tester T12 | #69 |
| tester K6 | #98 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        src/app/adapter/main.py · scripts/{engine_service,install_engine_service}.sh · Makefile
                ios/ModelRanking/Engine/{EngineClient,Language}.swift · ios/ModelRanking/ContentView.swift
                ios/Config/{Engine.xcconfig,Info.plist} (new) · ios/ModelRanking.xcodeproj/project.pbxproj
                ios/app.sh · .gitignore · AGENTS.md (§4, D-172)
                tests/unit/test_engine_{host,address}.py (new) · test_engine_service.py ·
                test_ios_client_contract.py · ios/EngineTests/{EngineClient,Language}Tests.swift ·
                test-manifest.txt
                docs/decisions.md (D-171 and its notes, D-172) · docs/prd.md (REQ-DEV-001) ·
                docs/owner-iphone.md (new) · docs/plans/m18-plan.md (amendment) ·
                docs/reviews/m18-wave-1-{review,tester}.md
Mutant set author: the independent seats (three Code-Reviewers, two Testers); the lead agent's own
                faults are supporting evidence only
Observed RED:   the first Tester's I15 (the plain-install branch of the keep-the-mode check dropped)
                turned test_a_plain_reinstall_writes_the_mode_it_found_and_says_so red on ed8b7e7
Owner instruction: "from now on proceed with what you recommend, don't ask me; I want to see it,
                it's been two weeks, let this version of the app come out" (2026-09-29, translated
                from Turkish), with the M18 plan he approved by merging #93: W1 puts the app on his
                iPhone. Delivered: the engine opens to his phone by one flag, and a page of steps
K.8 contracts:  EngineClient.localDefault now reads the Info plist key EngineURL (was a literal).
                The launcher's --host reads MODEL_RANKING_BIND. /v1 unchanged; a new 400 code,
                unknown_host, before any route
Stopped at three attempts: none
Hand-kept lists: _LOOPBACK in src/app/adapter/main.py (127.0.0.1, ::1, localhost); the installer's
                default Host list (127.0.0.1,localhost); the Swift literal "unknown_host", held
                against the engine's by test_the_app_matches_the_code_the_engine_sends_for_an_unknown_host
```
