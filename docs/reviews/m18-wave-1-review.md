---
record_type: review
id: m18-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-29
---
# M18-W1 Code Review: the app on the owner's iPhone

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-09-29
**Commit range:** `e82011b..ab0eebe`: 6 commits, 16 files, +436 / -7. The base is the head of the
M17 closure branch (PR #93, not merged), which carries the M18 plan and D-170. I review only W1's
commits.
**Risk tier:** HIGH (`docs/plans/m18-wave-1-plan.md:11`; `docs/plans/m18-plan.md:39`, `:137`)
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second family is available to this seat.
- Fresh context: this seat had none of the authoring context.

**What I read first.** `git diff --stat e82011b..ab0eebe -- .claude .agents AGENTS.md
permission-matrix.md .github Makefile Dockerfile` is empty, so the policy I applied is the base
ref's. I read, in order:
- `.claude/agents/Code-Reviewer.md`, `AGENTS.md`, `.agents/rules/practices.md` and
  `permission-matrix.md` §11;
- the wave plan, and `m18-plan.md` §1 to §5;
- D-171 (`docs/decisions.md:3287-3317`), D-170 (`:3254`), D-168 note 9 (`:3248`), D-160 (`:2774`)
  and D-126 (`:1022`);
- the M17 closure security seat's I-4 and MINOR-4 (`docs/reviews/m17-closure-security-review.md:355`,
  `:274-298`), which are the origins of #87's Host check and of #86.

I read the code before the commit messages.

**How I worked.**
- **Gate.** `make check-fast` at `ab0eebe` with `PYTHONDONTWRITEBYTECODE=1`: **PASS** in 48.7 s.
  - lint, typecheck and records: PASS.
  - test: 1549 passed, 23 skipped.
  - swift-test: 356 tests, exactly the manifest.
  - client-decls: PASS, 15 client files in 4 configurations.
- **The Host check, measured two ways, on loopback only.**
  - Through `TestClient`, with 24 Host values.
  - Through a real uvicorn bound to `127.0.0.1` on a random port, once with httptools and once with
    h11. I sent raw requests: HTTP/1.0 and 1.1 without a Host, two Host headers, absolute-form, tab
    padding, and an OPTIONS preflight.
- **`make run`'s environment.** I imported the app in a fresh interpreter with it; the import is the
  boot.
- **The installer's parsing** under `/bin/bash` 3.2.57 with `set -u`:
  - the script itself, with `--print-wrapper` and `--print-plist` and `HOME=/Users/probe`;
  - its parse block alone, for the empty and the spaced cases.

  The full installer ran only inside the test harness, with its temporary HOME and stubs.
- **The Xcode project.** `xcodebuild -showBuildSettings` (no build), on the worktree and on a scratch
  copy with three variants of `Engine.local.xcconfig`.
- **What URLSession sends as the Host.** A Swift script on this Mac fetched `http://LocalHost:<port>/`
  from a loopback listener.
- **Mutants: 20.** Each was applied in place, restored by copy, and verified by sha256: `main.py`
  53881a6e…, `engine_service.sh` cc17145a…, `install_engine_service.sh` 372ff243…,
  `EngineClient.swift` 83e640fb….
  - **Killed (12):**
    - N3, N4 and N9 (the bind check off, `0.0.0.0` counted as loopback, the variable ignored), by
      `test_engine_host.py:57`;
    - N5 (the port kept), by `:35`;
    - N7 (a prefix match), by `:42`;
    - S1 (a second `--host`), by `test_engine_service.py:364`;
    - S3 and S4 (`--lan` adds no address, or no names), by `:355`;
    - S5 (the wrapper `755`), by `:385`;
    - S6 (no Host list exported), by `:349` and `:355`;
    - S7 (LAN on by default), by `:349`;
    - W4 (any URL scheme), by `EngineClientTests.swift:540`.
  - **Survived (7):** N1, N2, N6 and S8 (**M5**); W1 and W2, which pass the whole `make check-fast`
    (**M4**); and N8, which removes the middleware's own `nosniff` line and is equivalent, because
    the outer `_no_sniff` sets the header.
  - **Not run under the real test (1):** S2, the launcher's preflight disabled. Under the real test
    it would bind `0.0.0.0:8080` (**M5**). I ran it with a stand-in interpreter that prints the
    server start instead of binding.
- **Read, not changed:** the Mac's firewall state (`socketfilterfw --getglobalstate`) and
  `scutil --get LocalHostName`.
- **Not touched:** the simulator, the engine on 8080, launchd, `~/Library`, the Desktop checkout and
  the network beyond loopback.
- **Clean-up.** One `.pyc` that my import wrote was deleted. The tree is clean apart from this file.

## Verdict
BLOCKING

**One finding blocks.**
- **B1.** D-171's fail-closed bind is a check on a variable, not on the bind. The repository's own
  by-hand command, `make run`, binds `0.0.0.0` with no Host list. It boots with no warning and
  serves every Host on every interface. D-171 says that configuration refuses to start.

**Six are MINOR.**
- **M1.** D-171's cost and the owner's page describe a smaller exposure than the code makes:
  - the bind follows the laptop to every network;
  - the Mac's firewall is off;
  - the phone's requests, with their `task`, cross Wi-Fi in cleartext;
  - "parameterless" is wrong.
- **M2.** A plain reinstall, which D-170 runs after every merge, silently drops the LAN mode. The
  owner's override also reaches `ios/app.sh`'s simulator builds.
- **M3.** Three of the owner's six steps can fail, or dirty the tracked project.
- **M4.** Nothing tests that the client reads the plist key: two mutants pass the whole gate. A
  mistyped override falls back to loopback without a word.
- **M5.** The Host check's case handling and its refusal of a missing Host are unpinned. The new
  launcher test's failure mode binds all interfaces.
- **M6.** The milestone plan promised REQ-DEV-001, and it was not written.

**What holds.**
- No browser can get past the Host check.
- #86's three mutants are killed.
- The installer's parsing is right under bash 3.2.
- The pbxproj edit is correct.
- Nothing new leaves the phone.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `src/app/adapter/main.py:633-640`, `Makefile:267`, `docs/decisions.md:3302-3303`,
  `docs/plans/m18-wave-1-plan.md:30-31`.
  **The bind check reads `MODEL_RANKING_BIND`, and only the launcher sets it. Every other way of
  starting the engine passes the check, whatever it binds.**

  **What D-171 says.** Clause 2: "A bind that is not loopback with no allowed Hosts refuses to
  start." The plan says the same.

  **What the code does.** `validate_startup_config` reads `os.environ.get(BIND_VAR, "127.0.0.1")`.
  An unset variable counts as loopback. So when the check has no information, it passes.

  **Each path, with no Host list:**

  | path | how it binds | what happens |
  |---|---|---|
  | the service: wrapper, then launcher | `--host "${MODEL_RANKING_BIND:-127.0.0.1}"` | refuses: `REFUSED`, exit 1 (`test_engine_service.py:373`; measured by hand) |
  | the launcher by hand, or `ios/app.sh` | the same | refuses when `MODEL_RANKING_BIND` is not loopback (measured) |
  | `make run` (`Makefile:267`) | `--host 0.0.0.0` on the command line; the variable unset | **boots and serves every Host** (measured through the import, see below) |
  | `uvicorn … --host 0.0.0.0` typed by hand | the variable unset | passes the bind check the same way (read from the code) |
  | `uvicorn` with `MODEL_RANKING_BIND=0.0.0.0` and `APP_ENV=test` | the variable set | boots: the relaxed lane only logs the problem (`main.py:712-720`, read from the code) |

  **`make run` is the documented path.** `README.md:19` calls it the local dev server. The client's
  diagnostic tells a developer to use it (`EngineClient.swift:95-96`). I imported the app with its
  environment: `APP_ENV` unset, so the strict lane. `STARTUP_WARNINGS` was `()`, and a request with
  `Host: rebound.evil.example:8080` got 200.

  **Why it blocks.**
  - This is the safety control the wave adds, on a HIGH wave.
  - On the documented by-hand path it fails open. The engine answers on every interface. With no
    list the Host check is off, so the DNS-rebinding read that I-4 named works too.
  - The Mac's firewall is off (measured), so nothing else stands in the way.
  - `permission-matrix.md` §11 makes a safety control that fails open BLOCKING. The data is public,
    which is why the fix is small, not why this passes.

  **It is not a regression.** `make run` bound `0.0.0.0` before this wave. What the wave adds is the
  ADR sentence saying it cannot.

  **The fix, either of two.**
  - **(a) Check the bind where it is known.** uvicorn fills `scope["server"]` from the accepted
    socket's own address (`uvicorn/protocols/utils.py:30-44`, `httptools_impl.py:108`). With no
    list, the middleware can refuse a request that arrived on a non-loopback IP address.
    - This holds for every launch path.
    - It must leave a `server` that is not an IP alone, because `TestClient` reports `testserver`.
    - `Dockerfile:46` would then need a list, which is right for a hosted engine (**K1**).
  - **(b) Keep `make run` on loopback, and narrow clause 2.**
    - `make run` binds `--host "$${MODEL_RANKING_BIND:-127.0.0.1}"`, in step with the launcher.
      The simulator shares the Mac's loopback, so nothing run by hand needs `0.0.0.0`.
    - A note on D-171 says that the launcher is what refuses, and names a hand-typed
      `uvicorn --host 0.0.0.0` as outside the control.

  Either is a few lines, with a test through the path it covers.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `docs/decisions.md:3307-3317`; `docs/owner-iphone.md:10`, `:14-16`, `:33-34`.
  **D-171's cost, and the owner's page, describe a smaller exposure than `--lan` makes.** Four
  points.

  *Every network, not only the home one.* `--lan` binds `0.0.0.0`
  (`install_engine_service.sh:48`): every interface, on every network the MacBook joins, until the
  installer runs again without `--lan`. The list includes `umut-macbook-pro-2.local`, and the Mac
  announces that name by mDNS on each of those networks, so in a café anyone can read
  `http://umut-macbook-pro-2.local:8080/v1/…`. The cost says "on the home network". The revisit
  clause's trigger, "the app leaves the home network", fires every time the laptop does.

  *The firewall is off.* `socketfilterfw --getglobalstate` on this Mac says "Firewall is disabled".
  So "The Mac's firewall and the opt-in are the controls" names a control that is not on, and step
  1's "If macOS asks whether Python may accept incoming connections, allow it" describes a prompt
  that will not appear.

  *What the phone sends now crosses Wi-Fi in cleartext.* Clause 4 calls the requests "the same
  parameterless ones". But `/v1/recommendations` carries `task` and `budget`
  (`EngineClient.swift:184-191`), and `task` is the surface the question routed to (D-168 note 9).
  Before this wave, that request went over the Mac's loopback. Now anyone who can see the network's
  traffic can read it. D-160 as amended allows sending `task` to the engine; the cost should say
  that it travels in the clear.

  *Config baked into the build.* AGENTS.md §5 says "runtime config never build-baked". Clause 4
  bakes into the build an address that differs by environment, and does not name the exception. M2
  and M4 are that rule's "nothing says so" in practice. A phone has no process environment, so the
  exception is defensible; it should be written down.

  **The fix:** a note on D-171 that states these four points, and one line on the owner's page for
  each: what is reachable while `--lan` is on, and how to close it, or to turn the firewall on.

- **M2** `scripts/install_engine_service.sh:36-50`, `:158`, `:164-165`; `ios/app.sh:112-115`;
  `ios/Config/Engine.xcconfig:7`.
  **Two ways the setup breaks after the owner follows the page.**

  *A plain reinstall drops the LAN mode.* D-170 clause 3 has the installer rerun after every merge,
  by the owner or by the agent on his standing instruction. Without `--lan`, the installer rewrites
  the wrapper to loopback and restarts the service with `kickstart -k`, and the phone then says "The
  engine is not answering". Nothing prints that the mode changed. The page says only "To close it
  again, run … without `--lan`", which a routine redeploy does by accident.

  *The override reaches the simulator.* `ios/app.sh` builds the same project, so once
  `Engine.local.xcconfig` exists, its simulator build also asks `Umut-MacBook-Pro-2.local:8080`. I
  measured this with `-showBuildSettings` on a scratch copy. Suppose the service is on loopback, or
  the engine was started by hand (bound `127.0.0.1`). Then the simulator app fails while `app.sh`
  reports "engine: up", because `app.sh`'s check curls `127.0.0.1`. This is the symptom the owner
  hit at the M17 closure.

  **The fix:** `app.sh` passes `ENGINE_URL=http://127.0.0.1:8080` on its `xcodebuild` line (a
  command-line setting beats the xcconfig; measured). The installer keeps the mode it finds in the
  existing wrapper unless told otherwise, or at least prints which mode it installed. The page says
  both.

- **M3** `docs/owner-iphone.md:12-13`, `:20-22`, `:27-28`.
  **Three of the six steps can fail, or leave the owner's checkout dirty.**

  *Step 1 works only once this wave is on `origin/main`.* The installer deploys `origin/main`
  (`install_engine_service.sh:93-99`). Before the merge, the deployed launcher still passes
  `--host 127.0.0.1`, and the engine has no Host check: the wrapper written from the branch asks for
  `0.0.0.0`, but the engine listens on loopback only. The page does not say "after the pull request
  is merged".

  *Step 3 edits a tracked file.* Choosing a team under Signing & Capabilities writes
  `DEVELOPMENT_TEAM` into `project.pbxproj`. Agents stage tracked changes with `git add -u`
  (AGENTS.md §3), so that line can reach an agent's commit. Changing the bundle id there does more
  harm. It breaks `tests/unit/test_engine_address.py:38-40`, which finds the app's configurations by
  the exact string `PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking;`, and it breaks
  `ios/app.sh:18` (`BUNDLE`). Measured on a scratch copy: `DEVELOPMENT_TEAM` set in
  `Engine.local.xcconfig` is honoured, but `PRODUCT_BUNDLE_IDENTIFIER` set there is not, because the
  target sets it.

  *No way back from "Don't Allow".* Step 6 does not say where to turn local-network access back on
  (Settings → Privacy & Security → Local Network). None of the app's error texts names the
  permission or the address.

  **The fix:** say when step 1 works. Put the team in the git-ignored file, and the bundle id too if
  it must change, after moving it from the target into `Engine.xcconfig`. Add the recovery line.

- **M4** `ios/ModelRanking/Engine/EngineClient.swift:144-154`; `ios/Config/Info.plist:5`;
  `tests/unit/test_engine_address.py`; `ios/EngineTests/EngineClientTests.swift:533-546`.
  **Nothing holds the link from the plist key to the client, and a mistyped address falls back
  without a word.**

  *Two mutants pass the whole `make check-fast`:* W1, `static let localDefault =
  engineURL(from: nil)`, and W2, the key spelt `"EngineUrl"`. The key is one fact in two files
  (`Info.plist:5`, `EngineClient.swift:144`), and no gate compares them (AGENTS.md §3.5). Only the
  scratch Xcode build verified it, and that build is not committed.

  *A present but invalid value becomes loopback.* The natural line
  `ENGINE_URL = http://Umut-MacBook-Pro-2.local:8080`, without `$()`, resolves to
  `ENGINE_URL = http:` (measured), and `engineURL` turns that into `http://127.0.0.1:8080`. On a
  phone, loopback is never the engine, so the app says "The engine is not answering". Its diagnostic
  (`EngineClient.swift:95-96`) suggests `make run` and names no address.

  **The fix:** a test that reads the key from `Info.plist` and asserts that the client asks
  `Bundle.main` for that key, which kills W1 and W2. Fall back only when the key is absent, or put
  `baseURL` in the `.unreachable` diagnostic. The Tester's citing-test rule may treat the untested
  link as BLOCKING at the next seat.

- **M5** `src/app/adapter/main.py:554-565`, `:741`; `tests/unit/test_engine_host.py:35-49`;
  `tests/unit/test_engine_service.py:355-361`, `:373-382`.
  **The Host check's edges are unpinned, and one new test fails dangerously.**

  *Four mutants survive the new tests:* N1, the header is not lower-cased; N2, a request with no
  Host is served; N6, the list is not lower-cased; S8, the installer does not lower-case the name.

  *Why the case mutants matter.* httpx, which `TestClient` uses, lower-cases the host, so the
  mixed-case URL at `test_engine_host.py:36` tests nothing about case. URLSession lower-cases it
  too (measured: `LocalHost` was sent as `Host: localhost:…`). So the phone depends on the list side,
  where the two lower-casings (N6 and S8) each cover for the other, and neither is tested. The
  installer test uses `probe-mac`, while this Mac's name is `Umut-MacBook-Pro-2`.

  *The missing Host.* Both parsers refuse it today (measured), but nothing keeps it so.

  *The launcher test's failure mode.* `test_engine_service.py:373-382` runs the real launcher with
  `MODEL_RANKING_BIND=0.0.0.0`. If the preflight regresses (the closure seat's L2), the launcher
  execs a real uvicorn on `0.0.0.0:8080` for up to the test's 30-second timeout. With a stand-in
  interpreter, it printed `starting on 0.0.0.0:8080` and `uvicorn … --host 0.0.0.0 --port 8080`. So
  a regression caught by this test also exposes the developer's Mac. Use a non-loopback address the
  Mac cannot bind (TEST-NET-1, `192.0.2.1`), or the closure seat's own shape: an artifact past a
  bound.

  **The fix:** three assertions (a mixed-case Host header sent raw, a mixed-case list entry, a
  missing Host), a mixed-case `ENGINE_LAN_NAME` in the installer test, and the safer bind in the
  launcher test.

- **M6** `docs/plans/m18-plan.md:30`; `docs/prd.md`.
  **REQ-DEV-001 was not written.** The milestone plan says W1's ADR writes it. D-171 does not,
  `docs/prd.md` has no such row, and no test cites it. The wave plan drops it without an amendment.

  **The fix:** write the row from plan §1's criterion and cite it in the new tests, or amend the
  plan.

### PASS (what looks good)

- **No browser can get past the Host check.**
  - **Refused (measured):**
    - foreign names, `127.0.0.1.evil.example` and `….local.evil.example`;
    - trailing dots;
    - numeric IPv4 forms (`2130706433`, `127.1`, `0x7f.0.0.1`);
    - IPv6, which is not on the list;
    - a path without a port, and `user@…`;
    - a missing Host, on HTTP/1.0 and 1.1, with both parsers.
  - Case and ports are normalised.
  - **Values that parse to an allowed name are shapes no browser sends:** `localhost:evil.example`,
    `127.0.0.1:8080/evil`, a second Host header under httptools, and absolute-form. A client that
    can send them can send `localhost` anyway, which the cost already concedes.
  - An OPTIONS preflight with a foreign Host gets 400 before CORS runs.
  - The engine has only GET routes and no websocket, so the `http` middleware covers every route.
- **The service path fails closed, and #86 is resolved.**
  - The closure seat's L1 (a second `--host`) is killed by `test_engine_service.py:364` (my S1). L3
    (a looser wrapper mode) is killed by `:385`, which asserts exactly `0o700` (my S5 used `755`).
    L2 (the preflight disabled) is killed by `:373`; I showed this with the stand-in interpreter,
    not the real test, for the reason in **M5**.
  - By default the wrapper binds loopback and carries its list (`:349`). `--lan` is opt-in (`:355`).
  - Mutants S1 and S3 to S7 are killed.
- **The installer's parsing is right under bash 3.2 with `set -u`.**
  - `${ARGS[@]+"${ARGS[@]}"}` survives an empty array.
  - `--lan` is found in any position, and when repeated.
  - A space in `--deploy-only`'s path is kept.
  - A bad flag still gets the usage line and exit 2.
  - With no LocalHostName, `--lan` stops with `FAIL`.
- **The `engineURL` fallback fails safe.**
  - Anything that is not an http(s) URL with a host becomes loopback, including the unexpanded
    `$(ENGINE_URL)`.
  - So `swift test`'s bundle, which has no key, keeps its old address.
  - W4 (any scheme) is killed.
- **The pbxproj edit is correct.**
  - The new ID is unique: four uses, for the reference, the group and the two configurations.
  - The file reference resolves from the main group.
  - `Config/` is outside the synchronised `ModelRanking` group, so the partial plist is not copied as
    a resource.
  - `-showBuildSettings` resolves `ENGINE_URL = http://127.0.0.1:8080` and
    `INFOPLIST_FILE = Config/Info.plist` in both Debug and Release.
  - `#include?` works, and the override wins (measured).
  - `.gitignore:72` ignores the override (`git check-ignore`).
  - The ATS change is `NSAllowsLocalNetworking` only, and `test_engine_address.py:30` pins it against
    `NSAllowsArbitraryLoads`.
- **D-126: nothing new leaves the phone.**
  - The Swift diff changes only where the requests go (`EngineClient.swift:141-154`). No call site,
    query item or header is added.
  - `test_nothing_typed_by_the_reader_reaches_the_engine` (`tests/unit/test_router_hints.py:229`)
    passes unchanged.
  - No `NSBonjourServices` is declared, so the app browses nothing.
  - The usage text's "Nothing you type is sent" is true under D-168 note 9. The one change is the
    transport (**M1**).
  - `/health` shows a LAN peer no path.
- **Discipline.**
  - Red came first: `41be53a` before `eccd5b1`, and `e94cd7c` before `fee46fd`.
  - `docs/decisions.md` gains 32 lines and loses none.
  - No commit carries AI attribution.
  - No file falls outside the plan's P0 to P4.
  - The existing launcher test changed only to read the new default (`test_engine_service.py:181`).

## Producers of hardened invariant(s)

This wave hardens four invariants:
1. The engine binds loopback unless opted in, and a bind beyond loopback with no Host list does not
   start (D-171 clause 2).
2. With a list, a foreign Host gets 400 (clause 1).
3. The app's engine address is set per build, with loopback as the fallback (clause 4).
4. Nothing new leaves the phone (D-126; D-160 as amended).

| producer | invariant | citing test | gap |
|---|---|---|---|
| `scripts/engine_service.sh:57-67`, `:75` (the service, `ios/app.sh`) | 1 | `test_engine_service.py:364`, `:373`; `test_engine_host.py:57` | the failure mode of `:373` (**M5**) |
| `scripts/install_engine_service.sh:36-50`, `:58-59`, `:158` (the wrapper) | 1, 2 | `test_engine_service.py:349`, `:355`, `:385` | S8 and the mixed-case name (**M5**); the mode is not kept across reinstalls (**M2**) |
| `Makefile:267` (`make run`, `0.0.0.0`) | 1 | none | **B1** |
| a hand-typed `uvicorn --host 0.0.0.0`; `Dockerfile:46` | 1 | none | **B1**, **K1** |
| `main.py:633-640` (the startup check) | 1 | `test_engine_host.py:57` | reads the variable, not the bind (**B1**) |
| `main.py:554-565`, `:737-745` (the list, the parse, the middleware) | 2 | `test_engine_host.py:35-54` | N1, N2 and N6 survive (**M5**) |
| `ios/Config/Engine.xcconfig`, `Info.plist`, `project.pbxproj` | 3 | `test_engine_address.py:18`, `:27`, `:36` | none |
| `EngineClient.localDefault` and `engineURL` (`EngineClient.swift:144-154`) | 3 | `EngineClientTests.swift:533`, `:540` | W1 and W2 survive the gate (**M4**) |
| `EngineClient`'s requests (`EngineClient.swift:184-215`) | 4 | `test_router_hints.py:229`; client-decls | none; unchanged |

## Acceptance criteria evidence

From `m18-plan.md:30` and the wave plan's design (`m18-wave-1-plan.md:25-50`):
- **Opt-in, with loopback the default** → `tests/unit/test_engine_service.py:349`, `:355`, `:364`;
  `main.py:635`. `make run` is the exception (**B1**).
- **An exposed engine refuses a foreign Host** → `tests/unit/test_engine_host.py:42-49`, and the raw
  requests above.
- **A bind beyond loopback with no list refuses to start** → `test_engine_host.py:57` and
  `test_engine_service.py:373`, on the launcher's path only (**B1**).
- **#86** → `test_engine_service.py:364` (one `--host`), `:373` (the preflight run for real) and
  `:385` (mode 700).
- **The app's address per build, with loopback the fallback** →
  `tests/unit/test_engine_address.py:18`, `:27`, `:36`; `ios/EngineTests/EngineClientTests.swift:533`,
  `:540`. The client's read of the key is untested (**M4**).
- **The app declares local networking** → `test_engine_address.py:27`.
- **Nothing new leaves the phone** → `tests/unit/test_router_hints.py:229`, and the Swift diff.
- **The app runs on the owner's iPhone** → not testable in the suite.
  - The evidence is the author's spike and scratch Xcode build, which I did not re-run because this
    seat does not touch the simulator.
  - `docs/owner-iphone.md` covers the device step, with gaps (**M3**). That step is the owner's.
- **REQ-DEV-001** → not written (**M6**).

## K.8 contract drift check

`grep -n` at `ab0eebe`:
```
ios/ModelRanking/Engine/EngineClient.swift:144:    static let localDefault = engineURL(from: Bundle.main.object(forInfoDictionaryKey: "EngineURL") as? String)
ios/ModelRanking/Engine/EngineClient.swift:148:    static func engineURL(from raw: String?) -> URL {
ios/ModelRanking/Engine/EngineClient.swift:168:    init(baseURL: URL = EngineClient.localDefault, session: URLSession? = nil) {
ios/Config/Info.plist:5:	<key>EngineURL</key>
scripts/engine_service.sh:75:exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host "${MODEL_RANKING_BIND:-127.0.0.1}" --port "$PORT"
Makefile:267:	$(PY) -m uvicorn app.adapter.main:app --host 0.0.0.0 --port 8080 --reload
scripts/install_engine_service.sh:58:export MODEL_RANKING_BIND="$BIND"
scripts/install_engine_service.sh:59:export MODEL_RANKING_ALLOWED_HOSTS="$ALLOWED"
src/app/adapter/main.py:548:ALLOWED_HOSTS_VAR = "MODEL_RANKING_ALLOWED_HOSTS"
src/app/adapter/main.py:550:BIND_VAR = "MODEL_RANKING_BIND"
src/app/adapter/main.py:554:def allowed_hosts() -> frozenset[str]:
src/app/adapter/main.py:568:def validate_startup_config(env: str | None = None) -> tuple[str, ...]:
src/app/adapter/main.py:738:async def _known_host(request: Any, call_next: Any) -> Any:
src/app/adapter/main.py:742:        response = _error(400, "unknown_host", "This engine does not answer to that host.")
```
- **The plan's three symbols (`m18-wave-1-plan.md:54-58`) are present.** `localDefault` keeps its
  name and its type, `URL`, so its one caller, `init(baseURL:)` at `:168`, is unchanged.
- **The launcher's `exec` line** changes as the plan says. `validate_startup_config` keeps its
  signature.
- **The two new variable names** match across `main.py:548`, `:550`, the installer (`:58-59`) and
  the launcher (`:75`).
- **`/v1` gains one error code,** `unknown_host`, in the one error shape (`main.py:742`, `_error`),
  under D-171. The app shows it through `.refused`, with the engine's message.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K1** `Dockerfile:46` binds `0.0.0.0` and sets no Host list, so a hosted engine built from it
  would answer every Host. The file is DevOps-owned, and a hosted engine is D-171's revisit. The
  Stage 5.1 release review should require a list there. Enhancement (security).
- **K2** `ios/Config/Info.plist:12-13`: the local-network prompt is English only, while the app
  speaks Turkish (`Language.swift:21`). A Turkish `InfoPlist.strings` needs a `.language-allow`
  entry with its reason. It belongs with #91 (a stranger's first use). Enhancement.

## Risks queued to next M

- **R1** The Mac's `.local` name is not stable. macOS renames the Mac on a Bonjour name conflict;
  this one is already `-2`. After a rename, the app's baked address and the installer's list both
  miss, and the phone says the engine is not answering. What shows it: `scutil --get LocalHostName`
  differs from the name in `Engine.local.xcconfig`.
- **R2** While `--lan` is on, uvicorn's HTTP parser is reachable by every peer on whatever network
  the Mac is on. The first field that is not public, or the first route that changes anything,
  breaks D-171's cost, so the Stage 5.1 review should treat `--lan` as an exposed surface. What
  shows it: any `/v1` change that serves more than public, read-only data.
