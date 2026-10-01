---
record_type: review
id: m18-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-01
---
# M18-W1 Code Review, round 3: the app on the owner's iPhone

**Reviewer:** Code-Reviewer seat, fresh eyes. This is the third round. I wrote none of this wave's
code, tests or records, and I wrote neither earlier verdict.
**Independent:** yes
**Date:** 2026-10-01
**Commit range:** `e82011b..a04fdd5`: 13 commits, 26 files, +1112 / -17. `e82011b` is the merge-base
with `origin/main`; the M17 closure PR #93 merged it as `159ec9e`. Round 1 is `e05ae15` (reds
`b718f70`, fix `8e54068`). D-172 is `cc78cb7`. Round 2 is `78aa6d1` (reds `a7f4b3b`, fix `a04fdd5`).
I reviewed the whole range, not only the last fix.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:39`, `:137`; `docs/plans/m18-wave-1-plan.md:11`)
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus (fallback: no second family available)
**Fresh context:** this seat started with none of the authoring context and none of the first two
seats' context. I read the plans, then the code and tests, and only then the commit messages and the
earlier verdicts.

**Summary.** Nothing blocks. Every finding from rounds 1 and 2 is fixed, and each code fix is held
by a test that goes red when I break it. The engine's network surface is right: with no list only
loopback is served, with a list a foreign Host gets 400, and the installer keeps the mode it finds.
What is left is on the owner's side of the wave. The page's "if the phone stops reaching the engine"
fix is only half a fix (**M9**). The one refusal this wave adds, the Host check, is the one failure
the screen shows no address for (**M10**). The view's source pin holds the call, not the line on
screen (**M11**). Three smaller items are in M12 to M14.

**Policy.** The profile (`.claude/agents/Code-Reviewer.md`), `.agents/rules/practices.md` and the
permission matrix were read from `e82011b`. At that ref the matrix is `permission-matrix.md` at the
repository root; `docs/permission-matrix.md` does not exist. `git diff --stat e82011b..a04fdd5 --
.claude .agents permission-matrix.md .github Dockerfile fly.toml epb.html or.md` is empty.

**How I worked.**
- **Gate.** `make check-fast` at `a04fdd5`, with `PYTHONDONTWRITEBYTECODE=1`: **PASS** in 52.0 s.
  - test: 1558 passed, 23 skipped.
  - swift-test: 361 tests, exactly the manifest.
  - lint, typecheck, records and client-decls: PASS.
- **The app compiles.** No gate compiles `ContentView.swift`: `ios/Package.swift` builds only
  `ModelRanking/Engine`. So I typechecked all 15 app sources with `swiftc -typecheck` against the
  iPhoneOS SDK (`arm64-apple-ios18.0`). Exit 0, no errors, two warnings that predate the wave. This
  is a compile only: no build, no xcodebuild, no simulator.
- **A real engine, on loopback only.** uvicorn 0.54.0 on 127.0.0.1:8137 with no list, and on
  127.0.0.1:8138 with a list, the nightly switch unset. Each was stopped with SIGTERM, then SIGKILL,
  and no listener was left.
  - With no list, every Host got 200: `127.0.0.1`, `evil.example`, mixed case, empty.
  - With the list: `evil.example` and an empty Host got 400; `UMUT-MACBOOK-PRO-2.LOCAL:8080`
    against a mixed-case entry got 200.
- **Mutants: 29.** Each was applied in place, run against its named tests, and restored from the
  original bytes. After each one I checked `git hash-object` against `HEAD:<file>` and
  `git diff --quiet`.
  - **23 on the Python side.** 21 were killed. Two survived:
    - `B2a-view-computed-not-shown` (**M11**);
    - `M2-no-lan-ignored`, which drops the `NO_LAN = no` test from the keep block. It is equivalent,
      because `install_engine_service.sh:52` closes the mode anyway.
  - **6 on the Swift side, through macOS `swift test --filter`.** All were killed.
  - The installer mutants ran only through `tests/unit/test_engine_service.py`, with its temporary
    HOME and its stubs. I did not run the preflight-off mutant against the real launcher test. With
    the preflight off, the launcher would start uvicorn's lifespan, and with it the nightly refresh,
    before the bind fails.
- **Red first.** On a `git archive` of `a7f4b3b`, the view pin fails and the rest pass. The commit's
  Swift stubs (`addressNote` returns nil, `engineAddress` returns "") are what make the Swift tests
  red there. I read them; I did not run them.
- **Host case under Unicode.** A macOS Swift probe: Foundation's `URL` maps a Kelvin-sign `K` in a
  host to ASCII `k` by IDNA before `.host` returns. Cyrillic lookalikes become punycode. So the
  case-free compare cannot be fooled into a host that resolves elsewhere.
- **Read only:** GitHub issues #94, #95 and #89 and their comments.
- **Not done, by this seat's rules:**
  - no run of either installer script outside the pytest file;
  - no `launchctl`, `xcodebuild`, `xcrun` or `simctl`;
  - nothing on the simulator;
  - nothing read in `~/Library`, the keychain included.
- **Tree.** Clean apart from this file. My harness and logs are in the scratchpad.

## Verdict
PASS-WITH-MINORS

**Nothing blocks.** Every earlier finding is fixed. Every code fix has a test that a mutant turns
red. The engine, the installer, the build settings and the D-126 gates hold.

**Six are MINOR.** I recommend fixing M9 to M11 in this wave rather than filing them. They are a few
lines each, and the page is what the owner acts on next.
- **M9.** The owner's page has two steps that do not work as written:
  - After the Mac is renamed, the page says to change only the app's address. The engine's Host
    list still names the old name until the installer runs again, so the phone is refused.
  - Steps 1, 2 and 4 assume the local checkout already holds the merged `main`, and the page never
    says to pull it.
- **M10.** `addressNote` leaves out the two failures where the address is the cause: the engine's
  own `unknown_host` refusal, which is new in this wave, and `insecureTransport`.
- **M11.** The source pin on the failure view holds the call to `addressNote`, not the line on
  screen. A mutant that computes the line and drops it compiles and passes the whole gate.
- **M12.** The installer's keep-the-mode block runs in every mode, and the deploy tests run it with
  the real HOME. On the owner's Mac in LAN mode they read his live wrapper and query `scutil` and
  `ipconfig`.
- **M13.** Records drift:
  - a doc comment is misplaced;
  - two evidence files do not cite REQ-DEV-001;
  - the wave plan still promises a security pass;
  - the PRD overstates what is pinned to loopback.
- **M14.** Five commits in the range carry no `GP-Agent:` / `GP-Task:` trailers.

**K.9:** K4 (failure sentences English only) and K5 (no gate compiles the app target).
**Risks:** R4 (step 2 assumes Xcode is signed in to the Apple ID) and R5 (which error a refused
local-network permission gives for a `.local` name is unmeasured).

## The earlier rounds' findings, one by one

| id | fixed? | held by a test? (mutant → the test that goes red) |
|---|---|---|
| B1 | **Yes.** With no list, `_known_host` refuses whatever arrives on a non-loopback socket address (`main.py:568-578`, `:751-762`). `make run` binds 127.0.0.1 (`Makefile:267`). | **Yes.** Arrival check off → `test_engine_host.py:72`. A name counted as a network → `:53`. Startup check off → `:58`. `make run` back on `0.0.0.0` → `test_engine_service.py:420`. |
| M1 | **Yes (text).** Notes 2-4 and 7 (`decisions.md:3326-3335`, `:3346-3348`); page `:50-57`. | n/a |
| M2 | **Yes.** The mode is kept (`install_engine_service.sh:46-52`) and printed (`:193-194`). `app.sh` pins the address and the bundle id (`ios/app.sh:115`). | **Yes.** Keep block off → `test_engine_service.py:398`. Either `app.sh` setting dropped → `:428`. |
| M3 | **Yes.** The bundle id lives in `Engine.xcconfig:9`. The page says "after the merge" (`:11-12`) and how to undo "Don't Allow" (`:36-37`). It still does not say to pull the merge (**M9**). | **Yes.** The id out of the xcconfig → `test_engine_address.py:59`. The `#include?` dropped → `:19`. |
| M4 | **Yes.** The plist key is held. The address is in `.unreachable`'s detail (`EngineClient.swift:275`, `:278`), and since round 2 it is on screen (B2). | **Yes.** Key misspelt, or nil read → `test_engine_address.py:46`. Detail without the address → `EngineClientTests.swift:290`. |
| M5 | **Yes.** | **Yes.** Header case → `test_engine_host.py:81`. List case → `:81`. Empty Host served → `:90`. Installer not lower-casing the name → `test_engine_service.py:355`. The launcher test binds TEST-NET-1 (`:378-381`, read). |
| M6 | **Yes.** `prd.md:551`. All 20 evidence line numbers point at the right test definitions (checked one by one). Two evidence files do not cite the id (**M13**). | n/a |
| K1 | Filed as **#94** (open; read). | n/a |
| K2 | Filed as **#95** (open; read). | n/a |
| R1 | **In part.** Note 6 (`decisions.md:3339-3340`) and page `:58-60` cover the app's address and not the engine's list, though R1 named both (**M9**). | n/a |
| R2 | A comment on **#89** (read). | n/a |
| B2 (a) | **Yes.** `addressNote` (`EngineClient.swift:138-153`), `UIText.engineAddress` (`Language.swift:424-427`), the view (`ContentView.swift:671-674`). Step 6 (`owner-iphone.md:38-45`) and note 8 (`decisions.md:3349-3351`) describe what the code does. | **Yes, with one gap.** Only `.unreachable` keeps the line → `EngineClientTests.swift:559`. Turkish line changed → `LanguageTests.swift:444`. View line removed or commented out → `test_engine_address.py:77`. Line computed and not shown: survives (**M11**). |
| B2 (b) | **Yes (text).** Page `:56-57`; note 7 (`decisions.md:3346-3348`) supersedes the cost's last sentence and note 3's pointer, and the body stays append-only. It is correct: the macOS application firewall filters by application, not by device. | n/a |
| M7 | **Yes.** | **Yes.** `[ -f "$WRAPPER" ]` in place of the `grep` → `test_engine_service.py:398`. `:145` now asserts `"starting on" not in`, and the launcher's echo (`engine_service.sh:74`) contains that text, so the assertion can fail again (read). |
| M8 | **Yes (text).** Step 2 gives `security find-certificate -c "Apple Development" -p \| openssl x509 -noout -subject` (`owner-iphone.md:25-26`). The author says it was measured on this Mac. I did not read the keychain (**R4**). | n/a |
| K3 | **Yes.** `EngineClient.swift:134` compares lower-cased hosts. The Unicode probe above shows it cannot be fooled. | **Yes.** Case-sensitive again → `EngineClientTests.swift:53` and the source pin `test_ios_client_contract.py:504`. |
| R3 | Note 9 (`decisions.md:3352-3354`) and a comment on **#94** (read). | n/a |

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M9** `docs/owner-iphone.md:58-60`, `:10-15`; `docs/decisions.md:3339-3340`; `scripts/install_engine_service.sh:57`, `:61`, `:70-71`; `src/app/adapter/main.py:757-759`. **Two of the owner's steps do not work as written.**

  **(a) The rename recovery fixes the app and not the engine.** The page says: "macOS can rename it;
  put the new name in step 2's file and run the app from Xcode again". Note 6 says the same.

  The engine's Host list is written into the wrapper when the installer runs. It reads
  `scutil --get LocalHostName` at `:57`, lower-cases it at `:61` and exports it at `:70-71`. Nothing
  rewrites it until the installer runs again.

  So, after a rename, the owner follows the page. The phone now asks `<new-name>.local`, which
  resolves to the Mac. The engine refuses it with 400 `unknown_host` (`main.py:757-759`), because the
  list still says `<old-name>.local`. The screen says "This engine does not answer to that host.",
  with no address line (**M10**), and step 6 has no case for it.

  Round 1's R1 named both halves: "the app's baked address and the installer's list both miss". The
  name is already `-2`, so a rename has happened on this Mac once.

  **The fix:** one more clause on the page and in a note. After a rename, also run
  `scripts/install_engine_service.sh`. A plain rerun keeps the LAN mode (`:46-52`) and reads the new
  name (`:57`).

  **(b) The page assumes the merged `main` is in the local checkout.** It says "after the M18-W1 pull
  request is merged" (`:10-12`) and then "On the Mac, from the repository". The installer deploys
  `origin/main` by `git fetch`, but the script that runs is the one on disk. In a checkout that has
  not pulled the merge:
  1. `--lan` gets the old script's usage line and exit 2 (`e82011b:scripts/install_engine_service.sh:115`);
  2. step 2's file is read by nothing, because the old project has no `Engine.xcconfig`;
  3. step 4 builds an app with no address line.

  It fails loudly, so nothing is harmed. **The fix:** one line, "with `main` checked out and pulled".

  **Why MINOR.** `permission-matrix.md` §11 classes doc drift as MINOR. Neither statement is a safety
  claim, and each fails with a message rather than silently.

- **M10** `ios/ModelRanking/Engine/EngineClient.swift:138-153`, `:270-271`; `ios/EngineTests/EngineClientTests.swift:569-574`. **The address is left off the two failures where it is the cause.**

  `addressNote` returns nil for `.insecureTransport`, `.refused` and `.undecodable`, on the premise
  that "the address is not what went wrong there" (`:142-144`). That premise is false for two cases
  this setup can produce.

  1. **`.refused` with code `unknown_host`.** This is the refusal this wave adds. The engine got the
     request and refused the Host, which is the address's own name. It is what the owner sees in
     M9(a), and whenever the address the app asks is not on the engine's list. Two examples: a
     hand-typed IP after the Mac's address changed, or another spelling of the name.
  2. **`.insecureTransport`.** On this setup it fires only because of the address. Either the URL is
     `http` to a name that is neither `.local` nor unqualified, which ATS refuses despite
     `NSAllowsLocalNetworking`. Or it is `https` against the plain-HTTP engine, which fails as
     `.secureConnectionFailed`. That maps here (`:270-271`), and the recovery sentence then tells
     the owner the connection "is not encrypted", which is the opposite of what happened.

  `testAnAnswerTheEngineGaveCarriesNoAddress` (`EngineClientTests.swift:569-574`) pins today's
  choice, so the fix changes that test too. The address is not secret, so showing it under every
  failure is the simplest correct rule. The narrower rule is to add `.refused` where
  `code == "unknown_host"`, and `.insecureTransport`. Either way, step 6 gains a case: "It says the
  engine does not answer to that host: rerun the installer (M9)."

- **M11** `tests/unit/test_engine_address.py:77-85`, `:70-74`; `ios/Package.swift`. **The pin on the failure view holds the call, not the line on screen.**

  `ContentView.swift` is compiled by no gate: the Swift package's target path is
  `ModelRanking/Engine`. So this regex is the only guard on the B2 fix's last step. It asks only that
  `error.addressNote(client.baseURL, language)` appears in `failure(_:)`.

  The mutant `let _ = error.addressNote(client.baseURL, language)` replaces the `if let … { Text(…) }`
  block. It typechecks for iOS (I ran `swiftc -typecheck` on it) and passes the whole Python suite,
  so the owner would see no address while every gate is green.

  Separately, `_code` keeps a `//` comment on any line where a `"` comes before it (`:73`). So a
  call commented out after a string on the same line still counts as code.

  **The fix:** pin the shape that shows it, for example
  `if let (\w+) = error\.addressNote\(client\.baseURL, language\) \{\s*Text\(\1\)`. A view test would
  be better; it belongs to #69.

- **M12** `scripts/install_engine_service.sh:33-35`, `:46-62`, `:140`; `tests/unit/test_engine_service.py:103-106`. **The deploy tests run the keep-the-mode logic against the owner's real HOME.**

  The keep-and-LAN block runs before the mode dispatch at `:140`, so it runs for `--deploy-only` and
  `--print-plist` too, where it has no use. The `_deploy` helper passes the real environment and
  overrides no HOME.

  On the owner's Mac with `--lan` on, every deploy test therefore:
  1. reads his live wrapper in `~/Library/Application Support`;
  2. takes the LAN branch;
  3. calls `scutil --get LocalHostName` and `ipconfig getifaddr` for real;
  4. prints "home network: kept".

  The installer's own comment says the opposite (`:34-35`: "Tests pass ENGINE_LAN_NAME and
  ENGINE_LAN_IP instead of asking this Mac").

  All of it is read-only, so nothing is harmed today. But a test's path now depends on the state of
  the owner's service. Where `scutil` is missing or denied, the deploy tests exit 1 at `:59` for a
  reason outside the code. I established this by reading. Running it would have meant running the
  installer outside the pytest file, or reading `~/Library`.

  **The fix:** `_deploy` sets HOME to a temporary folder (one line). Better still, the block runs
  only when installing.

- **M13** `ios/EngineTests/LanguageTests.swift:440-443`; `tests/unit/test_engine_service.py:346`; `docs/plans/m18-wave-1-plan.md:11-12`, `:67`; `docs/prd.md:551`. **Records drift, four small items.**

  (a) `EngineAddressLanguageTests` was inserted between the M17-W5 doc comment and the class it
  describes. That comment ("a board added by a refinement is named as its chip is…") now heads the
  new class, and `CombinedListLanguageTests` has lost it.

  (b) REQ-DEV-001's evidence cites `test_engine_service.py:349-428` and `LanguageTests.swift:444`,
  but neither file cites the id (seed E.2). The section header at `test_engine_service.py:346` names
  `#87, D-171; #86`, and the Swift class comment names the review.

  (c) The wave plan still says "so a security pass runs before merge" (`:11-12`) and "the security
  pass" (`:67`). D-172 removed per-wave passes and amended `m18-plan.md` (`:200-203`), but not this
  file.

  (d) The PRD row says "the simulator build is always loopback". That is true of `ios/app.sh`'s build
  (`test_engine_service.py:428`). It is not true of a simulator chosen in Xcode, which reads the
  owner's override. The page says it precisely (`owner-iphone.md:61`).

  **The fix:** move the comment back, cite the id in the two files, align the wave plan with D-172,
  and say "the simulator build from `ios/app.sh`" in the PRD.

- **M14** `git log e82011b..a04fdd5`; `AGENTS.md:42`. **Five commits carry no agent trailers.**

  `8e54068`, `cc78cb7`, `78aa6d1`, `a7f4b3b` and `a04fdd5` have neither `GP-Agent:` nor `GP-Task:`.
  The eight commits before them have both. Under D-161, a session commit carries the owner's
  identity, and the trailers are the only mark of an agent's commit. `AGENTS.md:42` calls them a
  convention that nothing can check on the owner's identity.

  If these five were agent sessions, the range now holds commits that cannot be told from the
  owner's own. That is the property the convention exists for.

  History is not rewritten for this. **The fix:** the trailers resume on the next commit. The
  checklist row can say "refused — history is not rewritten; trailers resume from <sha>".

### PASS (what looks good)

- **The engine's network surface is right.**
  - The no-list rule reads the socket's local address, which uvicorn fills from the accepted
    connection. `make run`, a hand-typed uvicorn and the service are all held, and the real-engine
    probe agrees.
  - A non-IP `server` (TestClient's `testserver`, a Unix socket) is served (`main.py:577-578`). That
    is the only way the rule fails open, and note 9 and #94 record the forwarder case that follows
    from it.
  - With a list: the port is stripped, case is ignored on both sides, an empty or missing Host is
    refused, and the refusal comes before CORS, with `nosniff`.
  - The startup check refuses a bind beyond loopback with no list, and the launcher's preflight turns
    that into a refused start (`engine_service.sh:57-67`).
- **The installer's keep-the-mode logic holds, through its tests.**
  - A LAN wrapper is kept; `--no-lan` closes it; a loopback wrapper stays on loopback.
  - The name is lower-cased, and the wrapper is mode 700.
  - Each was shown by a mutant going red. The plist does not carry the mode, so a mode change is
    picked up by `kickstart -k` (`:176-177`), which reads the new wrapper.
- **#86 stays resolved.** A second `--host` → `test_engine_service.py:364`. Wrapper `755` →
  `:387`. The preflight is run for real on an address the Mac cannot bind (`:373`).
- **The failure screen's address line is right where it shows.**
  - It shows for `.unreachable`, `.timedOut` and `.offline`, in both languages. It is selectable, and
    it is the URL the requests used (`client.baseURL`).
  - Step 6's three cases each match a code path:
    - a loopback fallback from a missing or misspelt `ENGINE_URL` gives `127.0.0.1` (`EngineClient.swift:166-172`);
    - the Mac's name, with the engine unreachable or timed out;
    - "no network connection", from `.notConnectedToInternet` mapped to `.offline` (`:272-273`).
- **D-126 and D-160 as amended: showing a URL opens no way off the device.**
  - `addressNote` is a pure function, and the line is a `Text`.
  - `.textSelection(.enabled)` was already used on the detail facts at base (`ContentView.swift:1104`).
  - The egress gate (`test_router_hints.py:302`, scanning every client file raw) passes. The new
    `: URL` parameter sits in `EngineClient.swift`, the one permitted door.
  - The data-flow gate on `client.` arguments (`test_router_hints.py:229`) is untouched:
    `client.baseURL` is not a call.
  - No query item or header is added.
- **`SameHostOnly`, case-free, is sound.** Both sides are lower-cased, and nil still matches only nil
  (unchanged, held by `testARedirectWithNoHostAtAllIsRefused`). The IDNA probe shows that Unicode
  lower-casing cannot turn a foreign host into the engine's. The source pin moved with the code
  (`test_ios_client_contract.py:525-526`).
- **D-171's notes match the code, apart from note 6's missing half (M9).**
  - Note 7's firewall wording is correct.
  - Note 8 lists exactly the three cases the code shows.
  - Note 9 is the R3 forwarder case.
  - The body is append-only: `docs/decisions.md` only gains lines across the range.
- **The app compiles for a device target**, the B2 view change included.
- **Discipline.**
  - Each fix was red first (`b718f70` → `8e54068`; `a7f4b3b` → `a04fdd5`, the view pin measured).
  - The fixes changed no assertion to make it pass. M7 tightened one.
  - No AI attribution appears in commits.
  - No drive-by edits: every file maps to the plan's P0-P4, a review finding, or D-172.
  - AGENTS.md is 127 lines and changed only under D-172.

## Producers of hardened invariant(s)

The wave hardens five invariants:
1. The engine is reachable beyond loopback only by opt-in (D-171 clause 2, note 1).
2. With a list, a foreign Host gets 400 (clause 1).
3. The app's address is set per build, with loopback as the fallback, and the `app.sh` simulator
   build is pinned to loopback (clause 4, note 5).
4. Under a failure to reach the engine, the screen shows the address the app asked (note 8).
5. Nothing new leaves the phone (D-126; D-160 as amended by D-168 note 9).

| producer | invariant | citing test | gap |
|---|---|---|---|
| `main.py:568-578`, `:751-762` (arrival rule, middleware) | 1 | `test_engine_host.py:53`, `:72` | none (forwarders: note 9, #94) |
| `main.py:646-653` (startup check), `engine_service.sh:57-67`, `:75` | 1 | `test_engine_host.py:58`; `test_engine_service.py:364`, `:373` | none |
| `Makefile:267` (`make run`) | 1 | `test_engine_service.py:420` | none |
| `install_engine_service.sh:36-62`, `:70-71`, `:170` (wrapper, keep mode) | 1, 2 | `test_engine_service.py:349`, `:355`, `:387`, `:398` | tests read the real HOME (**M12**) |
| `main.py:554-565` (list, Host parse) | 2 | `test_engine_host.py:38`, `:45`, `:81`, `:90` | none |
| `Engine.xcconfig`, `Info.plist`, `project.pbxproj` | 3 | `test_engine_address.py:19`, `:28`, `:37`, `:59` | none |
| `EngineClient.swift:162-172` (`localDefault`, `engineURL`) | 3 | `test_engine_address.py:46`; `EngineClientTests.swift:552`, `:576` | none |
| `ios/app.sh:112-116` | 3 | `test_engine_service.py:428` | none |
| `EngineClient.swift:138-153`, `Language.swift:424-427` | 4 | `EngineClientTests.swift:559`, `:569`; `LanguageTests.swift:444` | `unknown_host`, `insecureTransport` (**M10**) |
| `ContentView.swift:671-674` | 4 | `test_engine_address.py:77` | holds the call, not the line (**M11**) |
| `EngineClient.swift:119-136` (`SameHostOnly`) | 5 | `EngineClientTests.swift:53`; `test_ios_client_contract.py:504` | none |
| `EngineClient.swift:202-297` (requests) | 5 | `test_router_hints.py:229`, `:302` | none (unchanged but for the error detail) |

## Acceptance criteria evidence

REQ-DEV-001 (`docs/prd.md:551`, from `m18-plan.md:30`), clause by clause:
- **The engine binds loopback unless the installer is told otherwise** → `test_engine_service.py:349`,
  `:355`; `install_engine_service.sh:54-62`.
- **A reinstall keeps the mode it finds** → `test_engine_service.py:398` (kept, closed, stays
  loopback).
- **With no Host list, a request arriving on a network address is refused** →
  `test_engine_host.py:72`, `:53`; the real-engine probe.
- **An exposed engine refuses a Host not on its list** → `test_engine_host.py:45`, `:81`, `:90`; the
  real-engine probe.
- **A bind beyond loopback with no list does not start** → `test_engine_host.py:58`;
  `test_engine_service.py:373`.
- **The address is set per build, loopback when unset** → `test_engine_address.py:19`, `:46`;
  `EngineClientTests.swift:552`, `:576`.
- **It is shown under a failure to reach it** → `EngineClientTests.swift:559`; `LanguageTests.swift:444`;
  `test_engine_address.py:77` (weak, **M11**).
- **The simulator build is always loopback** → `test_engine_service.py:428`, for `ios/app.sh`'s build
  (**M13**(d)).
- **Nothing new leaves the phone** → `test_router_hints.py:229`, `:302`.
- **The app runs on the owner's iPhone** → the owner's own run, honestly marked **PARTIAL**. The page
  that guides it is right for the first run; its rename recovery is not (**M9**).

## ADR trace

- **D-171.**
  - Clause 1 → `main.py:751-762`.
  - Clause 2 → `main.py:646-653`, `engine_service.sh:75`, and note 1's no-list rule.
  - Clause 3 → `install_engine_service.sh:56-62`.
  - Clause 4 → `Engine.xcconfig:6`, `Info.plist:5-13`, `EngineClient.swift:162-172`.
  - Notes 1-5 and 7-9 match the code. Note 6 is half of what R1 asked (**M9**).
  - The cost's last sentence and note 3's firewall pointer are superseded by note 7, in place, and
    the body stays append-only.
- **D-172** → `AGENTS.md` §4, `m18-plan.md:200-203`. No security seat ran on this wave, as ruled.
  The wave plan was not updated (**M13**(c)).
- **D-170** → amended by D-171, as its header says. The installer stays the owner's (or his
  standing instruction's) to run; this seat ran it only through its tests.
- **D-126 / D-160 / D-168 note 9** → the requests are unchanged, and the egress gates pass. Showing the
  address is local (PASS above). Clause 4's "parameterless" is corrected by note 4.

## K.8 contract drift check

`git grep -n` at `a04fdd5`:
```
ios/ModelRanking/Engine/EngineClient.swift:145:    func addressNote(_ address: URL, _ language: Language) -> String? {
ios/ModelRanking/Engine/EngineClient.swift:162:    static let localDefault = engineURL(from: Bundle.main.object(forInfoDictionaryKey: "EngineURL") as? String)
ios/ModelRanking/Engine/EngineClient.swift:166:    static func engineURL(from raw: String?) -> URL {
ios/ModelRanking/Engine/EngineClient.swift:186:    init(baseURL: URL = EngineClient.localDefault, session: URLSession? = nil) {
ios/ModelRanking/Engine/Language.swift:425:    public static func engineAddress(_ language: Language, _ address: String) -> String {
ios/Config/Info.plist:5:	<key>EngineURL</key>
Makefile:267:	$(PY) -m uvicorn app.adapter.main:app --host 127.0.0.1 --port 8080 --reload
scripts/engine_service.sh:75:exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host "${MODEL_RANKING_BIND:-127.0.0.1}" --port "$PORT"
scripts/install_engine_service.sh:70:export MODEL_RANKING_BIND="$BIND"
scripts/install_engine_service.sh:71:export MODEL_RANKING_ALLOWED_HOSTS="$ALLOWED"
src/app/adapter/main.py:548:ALLOWED_HOSTS_VAR = "MODEL_RANKING_ALLOWED_HOSTS"
src/app/adapter/main.py:550:BIND_VAR = "MODEL_RANKING_BIND"
src/app/adapter/main.py:554:def allowed_hosts() -> frozenset[str]:
src/app/adapter/main.py:581:def validate_startup_config(env: str | None = None) -> tuple[str, ...]:
src/app/adapter/main.py:751:async def _known_host(request: Any, call_next: Any) -> Any:
src/app/adapter/main.py:759:        response = _error(400, "unknown_host", "This engine does not answer to that host.")
```
- The plan's three symbols (`m18-wave-1-plan.md:54-58`) are present.
  - `localDefault` keeps its name and type, `URL`.
  - `validate_startup_config` keeps its signature.
  - The launcher's `exec` line changed only as the plan says.
- The two variable names agree across the engine, the installer and the launcher.
- `/v1` gains one error code, `unknown_host`, in the one error shape, under D-171. No route changes
  shape.
- The two new Swift symbols are internal (`addressNote`) or a `UIText` entry (`engineAddress`). No
  shared contract changes.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K4** `ios/ModelRanking/Engine/EngineClient.swift:39-87`; `ios/ModelRanking/ContentView.swift:664-674`. **The failure screen is half translated.** Its title and the new address line speak Turkish, but `errorDescription` and `recovery` are English only. On the phone, the `.offline` recovery ("This device has no internet connection") is also what a refused local-network switch produces, and it points the reader the wrong way. The strings predate this wave. It is an enhancement: check for an existing issue before filing (#95 is the plist prompt only).
- **K5** `ios/Package.swift`; `Makefile` (`swift-test`). **No gate compiles the app target.** `swift test` builds only `ModelRanking/Engine`. `ContentView.swift` and the app entry point are checked only by a simulator build, which the owner has paused, and by source regexes. `swiftc -typecheck` against the iPhoneOS SDK took about 4 seconds and starts no simulator. As a `check-fast` leg, it would have made M11's mutant a question of display, not of compiling. It may fold into #69.

## Risks queued to next M

- **R4** `docs/owner-iphone.md:18-29`. **Step 2 assumes Xcode is signed in to the owner's Apple ID.** The team-id command needs an Apple Development certificate in the login keychain. Automatic signing with `DEVELOPMENT_TEAM` set needs the account in Xcode → Settings → Accounts, and the page has no step for it. The author measured the command on this Mac, so a certificate exists today; I did not read the keychain. What would show it: the command printing "could not be found", or Xcode saying "No Account for Team".
- **R5** `ios/ModelRanking/Engine/EngineClient.swift:267-279`; `docs/owner-iphone.md:42-45`. **Which error a refused local-network permission gives is unmeasured.** Step 6's third case relies on iOS reporting it as no connection (`.offline`). For a `.local` name, the mDNS lookup may fail first, as `cannotFindHost` → `.unreachable`. The screen would then show the Mac's name, and the second case, which does not mention the switch. What would show it: the owner's first run after tapping "Don't Allow". If it reads as `.unreachable`, step 6's second case should name the switch too.
