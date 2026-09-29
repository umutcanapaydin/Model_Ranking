---
record_type: review
id: m18-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-29
---
# M18-W1 Code Review, round 2: the app on the owner's iPhone

**Reviewer:** Code-Reviewer seat, fresh eyes. This is the second round. I wrote none of this wave's
code, tests or records, and I did not write the first round's verdict.
**Independent:** yes
**Date:** 2026-09-29
**Commit range:** `e82011b..8e54068`: 9 commits, 20 files, +1082 / -12. The base is the head of the
unmerged M17 closure branch (PR #93). The first verdict is `e05ae15`. The red tests for it are
`b718f70` and the fix is `8e54068`. I reviewed the whole range, not only the fix.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:39`, `:137`; `docs/plans/m18-wave-1-plan.md:11`)
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus
(fallback: no second family available). Fresh context: this seat started with none of the authoring
context or the first seat's context. I read the code before the commit messages and before the first
verdict.

**Incident during this review.** One of my installer probes ran
`scripts/install_engine_service.sh --lan` for real. I had meant to pass `--print-wrapper`, and I had
set `HOME` to a scratch folder. The owner's own files were not touched:
`~/Library/LaunchAgents/com.ilgar.modelranking.engine.plist`, the wrapper and `engine/current`
(`releases/3f2e91d`) are all unchanged. But the installer did two things to launchd:
- it booted out the owner's loaded `com.ilgar.modelranking.engine`;
- it bootstrapped the same label from a plist in my scratch folder
  (`…/scratchpad/cr2-probe/h1/Library/LaunchAgents/…`).

That job now serves `release-159ec9e` (today's `origin/main`) from a scratch deploy. It listens on
**127.0.0.1:8080 only**: that release's launcher still hard-codes `--host 127.0.0.1` (measured with
`lsof` and `/health`). So nothing is exposed. The rules for this seat forbid any launchd action, so I
did not restore the job. The fix is in the hand-back, and the scratch folder must stay until then.

**Policy.** `git diff --stat e82011b..8e54068 -- .claude .agents AGENTS.md permission-matrix.md .github
Dockerfile fly.toml` is empty. The profile, `practices.md` and `permission-matrix.md` §11 were read
from `e82011b`.

**How I worked.**
- **Gate.** `make check-fast` at `8e54068`: **PASS** in 83.9 s.
  - test: 1557 passed, 23 skipped.
  - swift-test: 357 tests, exactly the manifest.
  - lint, typecheck, records and client-decls: PASS.
  - The first run failed only because this checkout had no `advisor.db` (W-108). I copied the
    artifact from the author's worktree; it is git-ignored and untracked.
  - That run's install step pointed the shared venv's editable install at this worktree. I pointed it
    back at `w18-1` with `pip install --no-deps -e`.
- **A real engine, on loopback only.** uvicorn 0.54.0 on 127.0.0.1:8123 and [::1]:8124 with no list,
  and on 127.0.0.1:8125 with a list. I sent raw requests and killed each server afterwards.
- **The arrival check, called directly** with IPv4, IPv6, IPv4-mapped, link-local, `testserver` and
  `None` server values, under Python 3.14.0.
- **The installer's parse** under `/bin/bash` 3.2.57 with `set -u`, through `--print-wrapper` and
  `--print-plist`:
  - with a scratch `HOME` holding no wrapper, a LAN wrapper, or a loopback wrapper;
  - with flags in each order;
  - its parse block alone, with no arguments.
- **Xcode:** `xcodebuild -showBuildSettings` only, no build. I checked the worktree, and a scratch copy
  with three versions of `Engine.local.xcconfig`, with and without `app.sh`'s command-line settings.
- **Mutants: 21.** Each was applied in place and restored from a byte copy. I checked each restore with
  `git hash-object` and `git diff --quiet` (`main.py` 35171db…, installer b020300…, launcher 522a1b5…,
  `EngineClient.swift` 50857b5…, `project.pbxproj` 9710da6…, `Engine.xcconfig` 81ee48b…).
  - **20 killed.** They are listed per finding below.
  - **1 survived:** a reinstall that opens the LAN over a loopback wrapper (**M7**).
- **Red first.** At `b718f70`, the five new tests for B1, M2 and M3 fail, and pass at `8e54068`. I ran
  them on a `git archive` copy.

## Verdict
BLOCKING

**One finding blocks.**
- **B2.** The owner's page, and D-171's review notes, tell the owner two things that are not so:
  - that the app's error message names the address it tried (no screen shows it);
  - that turning the Mac's firewall on and allowing Python keeps other devices out (it lets every
    device in).

  The code under the page holds. The engine, the installer and the build settings are right, and
  every first-round code finding is fixed and tested. This is a text fix of a few lines, unless the
  author chooses to show the address.

**Two are MINOR:**
- **M7.** One direction of the reinstall rule is untested, and one old assertion can no longer fail.
- **M8.** Step 2 sends the owner to a place for his team id that I could not confirm exists.

**What holds.**
- With no list, an engine refuses whatever arrives off loopback, whatever started it.
- The installer keeps the mode it finds.
- The simulator build is pinned to loopback and to the checked-in bundle id.
- The bundle id resolves from the xcconfig, and the owner's file overrides it.
- REQ-DEV-001 is written and cited.

## The first round's findings, one by one

| id | fixed? | tested? (mutant → the test that goes red) |
|---|---|---|
| B1 | **Yes.** With no list, `_known_host` refuses a request whose socket address is not loopback (`main.py:568-578`, `:751-762`). `make run` binds 127.0.0.1 (`Makefile:267`). | **Yes.** Arrival check off, and the middleware ignoring it → `test_engine_host.py:72`. A name counted as a network → `:53`. Bind check off → `:58`. `make run` back on `0.0.0.0` → `test_engine_service.py:414`. |
| M1 | **In part.** Notes 2-4 (`decisions.md:3326-3335`) and the page (`owner-iphone.md:43-48`) now state every-network, firewall-off and cleartext `task`. The firewall line added for it claims a control that does not exist (**B2**). | n/a (text) |
| M2 | **Yes.** The mode is kept (`install_engine_service.sh:46-52`) and printed (`:193-194`). `app.sh` passes `ENGINE_URL` and `PRODUCT_BUNDLE_IDENTIFIER` (`ios/app.sh:115`). | **Yes, one half.** Keep-mode off and `--no-lan` ignored → `test_engine_service.py:398`. Each `app.sh` setting dropped → `:422`. A loopback wrapper turned into LAN survives (**M7**). |
| M3 | **Yes.** The page says "after the merge" (`:11-12`) and how to undo "Don't Allow" (`:35-36`). The bundle id moved into `Engine.xcconfig:9`, and the project no longer sets it. | **Yes.** The id back in the project, or dropped from the xcconfig → `test_engine_address.py:60`. The `#include?` dropped → `:18`. Measured: the owner's file sets the team and the id, and `app.sh`'s command line beats it. |
| M4 | **In part.** The key link is held. The address was added to `.unreachable`'s detail (`EngineClient.swift:257`, `:260`), but no view shows that detail (**B2**). | **Yes, for what changed.** `localDefault` reading nil, or the key misspelt → `test_engine_address.py:45`. The address dropped from the detail → `EngineClientTests.swift:290`. Nothing tests the screen. |
| M5 | **Yes.** The launcher test binds TEST-NET-1 (`test_engine_service.py:379-381`), so a regressed preflight cannot serve this Mac. | **Yes.** Header or list case kept → `test_engine_host.py:81`. Empty Host served → `:90`. The installer not lower-casing the name → `test_engine_service.py:355`. |
| M6 | **Yes.** `prd.md:551`. It is cited at `test_engine_host.py:1`, `test_engine_address.py:1` and `EngineClientTests.swift:542`, and the row's evidence line numbers are right. | n/a |
| K1 | Filed as **#94**. I read it: it states the consequence below (green HEALTHCHECK, outside requests 400). | n/a |
| K2 | Filed as **#95**. | n/a |
| R1 | Written: page `:51-53`, note 6 (`decisions.md:3339-3340`). | n/a |
| R2 | Written: a comment on **#89** (read). | n/a |

## Findings

### BLOCKING (must fix before this wave closes)

- **B2** `docs/owner-iphone.md:37-38`, `:49-50`; `docs/decisions.md:3313-3314`, `:3330-3331`,
  `:3336-3338`; `ios/ModelRanking/ContentView.swift:662-672`;
  `ios/ModelRanking/Engine/EngineClient.swift:92-96`.
  **The owner's page and D-171's notes describe an error message and a firewall that do not behave as
  written.**

  **(a) No screen shows the address.** Step 6 says: "If the app says the engine is not answering, the
  message names the address it tried". Note 5 says the same.
  - The failure screen (`ContentView.swift:662-672`) renders `errorDescription` ("The engine is not
    answering.") and `recovery` ("…not reachable right now. Try again in a moment.") only.
  - The address is in `.unreachable`'s detail. Only `diagnostic` (`EngineClient.swift:94-96`) reads
    that detail, and nothing in `ios/ModelRanking` renders or logs `diagnostic`. I grepped for it.
  - The new test (`EngineClientTests.swift:282-291`) holds the string, not what the phone shows.
  - So the round-one M4 symptom stands on the phone. A mistyped `ENGINE_URL` falls back to loopback,
    and the owner sees no address. Step 6 is the only diagnosis the page gives him.
  - One more point, not measured (there is no device here): on iOS, a refused local-network permission
    is commonly reported as "not connected to the internet". This client maps that to `.offline`
    (`EngineClient.swift:254`), so the phone would say "This device has no network connection", which
    step 6 does not mention.

  **(b) The firewall keeps no one out.** The page (`:49-50`) says: "To keep other devices out while it
  is on, turn the firewall on … and allow Python." Note 3 points the owner to this as the alternative
  control, and the cost (`decisions.md:3313-3314`) still names the firewall as one.
  - The macOS application firewall allows or blocks per application. It does not filter by device or
    by network.
  - Allowing Python admits every device on every network the Mac joins, a café's included. Blocking
    Python shuts the phone out too.
  - No setting on that screen lets the phone in and keeps others out. While `--lan` is on, the only
    control is `--no-lan`.

  **Why it blocks, and is not a MINOR.**
  - This is a HIGH wave, and this page is the thing the owner acts on next.
  - (b) is a safety claim about the very exposure this wave opens. An owner at a café would believe he
    is covered.
  - The record now says the code does what it does not. That is the defect this project has recorded
    most often.
  - Both halves come from round-one fixes (M1, M4) that the notes record as done.
  - `permission-matrix.md` §12 triage: "MINOR but could ship and pass review → BLOCKING". A MINOR here
    could be deferred to an issue while the page ships.

  **The fix.**
  - For (a), either:
    - show the address on the failure screen for `.unreachable`, for example `diagnostic` in a
      footnote, with a test on the text the view is given; or
    - reword step 6 and note 5 to what the phone shows. Step 6 would then say what to check: step 2's
      file, the Mac awake and on the same Wi-Fi, the local-network switch.
  - For (b), reword the firewall line: it cannot keep other devices out while the phone is let in, and
    `--no-lan` is how to close. Add a line to D-171's notes. The body's cost sentence stays, since it
    is append-only, and the new note supersedes it.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M7** `tests/unit/test_engine_service.py:398-411`, `:145`; `scripts/install_engine_service.sh:48`;
  `scripts/engine_service.sh:74`.
  **One direction of the reinstall rule is untested, and one old assertion can no longer fail.**

  D-171 note 2 says a routine redeploy "does not close it by accident, nor open it". The test covers
  only "does not close it". A mutant that treats any existing wrapper as LAN survives all 27 tests in
  the file: `[ -f "$WRAPPER" ]` in place of the `grep`. With it, a plain reinstall over a loopback
  wrapper would open the engine to the network without being asked. The code is right today: my probe
  with a loopback wrapper stayed on loopback.

  Separately, `:145` asserts `"starting on :" not in done.stdout`. The launcher now prints
  `starting on ${MODEL_RANKING_BIND:-127.0.0.1}:`, which never contains `on :`, so that line can no
  longer fail.

  **The fix:** in `test_a_reinstall_keeps_…`, add a wrapper with `MODEL_RANKING_BIND="127.0.0.1"` and
  assert that the reinstall stays on loopback. Change `:145` to `"starting on" not in`.

- **M8** `docs/owner-iphone.md:25`.
  **I could not confirm where step 2 sends the owner for his team id.** It says: Xcode → Settings →
  Accounts → your Apple ID → the team (10 characters). As far as I know, that pane lists a free
  Personal Team by name and role, not by id. This seat has no Apple ID session, so this is unverified.
  If the owner cannot find the id there, the page gives him no other way.

  **The fix:** confirm it on this Mac, or add a fallback that works for a Personal Team. One is the
  `OU` field of the Apple Development certificate. Another is Build Settings → `DEVELOPMENT_TEAM`,
  after choosing the team once, with the project change then undone. Pick whichever the author can
  measure.

### PASS (what looks good)

- **With no list, only loopback is served, on every launch path.**
  - uvicorn fills `scope["server"]` from the accepted socket's own address
    (`uvicorn/protocols/utils.py:30-44`, used at `h11_impl.py:99` and `httptools_impl.py:108`). So the
    rule reads the real bind, not a variable.
  - **Measured on a real engine.** On 127.0.0.1 and on [::1] with no list, every Host gets 200, a
    missing Host included. With a list: a foreign Host gets 400, `UMUT-MACBOOK-PRO-2.LOCAL:8080` gets
    200 against a mixed-case entry, and `[::1]` and a missing Host get 400.
  - **Called directly.**
    - `192.168.0.26`, `::ffff:192.168.0.26`, `fe80::1%en0` and `0.0.0.0` are refused.
    - `127.0.0.1`, `::1` and `::ffff:127.0.0.1` (Python 3.14) are served.
    - `testserver`, a Unix socket path and `None` are served, which is what keeps `TestClient` tests
      working (`test_engine_host.py:53`).
    - On Python 3.11 and 3.12, `::ffff:127.0.0.1` is not loopback. So a hand-typed dual-stack
      `--host ::` there would refuse its own loopback. That fails closed, and nothing starts that way.
  - **`Dockerfile:46` now fails closed.** Its HEALTHCHECK on 127.0.0.1 stays green while every outside
    request gets 400. #94 says exactly this, and nothing deploys the image.
- **The installer is right under bash 3.2.57 with `set -u`.**
  - No arguments, and a wrapper that does not exist yet, give loopback.
  - A LAN wrapper is kept, and the script says so on stderr.
  - `--no-lan` closes, in either order and when both flags are given.
  - `--lan` can come anywhere, more than once.
  - `--deploy-only` keeps a spaced path and `--no-venv`.
  - A bad flag gives the usage line and exit 2.
  - An empty `LocalHostName` stops with `FAIL`.
  - The mixed-case name is lower-cased (`umut-macbook-pro-2.local`).
- **The bundle id and the build settings agree** (`-showBuildSettings`, measured).
  - Debug and Release resolve `PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking`,
    `ENGINE_URL = http://127.0.0.1:8080` and `INFOPLIST_FILE = Config/Info.plist`.
  - The xcconfig is the base of the app target's own configurations (`project.pbxproj:159`, `:180`,
    list `194A6D5B…`), and it is the only target.
  - The owner's file overrides the address, the team and the id.
  - `app.sh`'s command line then puts the address and the id back to loopback and `$BUNDLE`
    (`ios/app.sh:18`, `:115`, `:126-127`), so `simctl launch` finds what it built.
  - The plain `//` mistake resolves to `ENGINE_URL = http:`, which the client turns into loopback, as
    the page warns.
  - `swift test` has no bundle id, and its `Bundle.main` has no key, so it keeps loopback.
- **#86 stays resolved.**
  - A second `--host` → `test_engine_service.py:364`.
  - The wrapper is mode 700 (`:387-395`).
  - The preflight is run for real on an address the Mac cannot bind (`:373-384`).
- **D-126 and D-160 as amended: nothing new leaves the phone.**
  - The Swift diff changes where requests go, and the text of a local error. It adds no query item or
    header.
  - `test_router_hints.py:229` passes in the gate.
  - The redirect guard follows the configured host (`EngineClient.swift:243`).
- **Discipline.**
  - The red tests (`b718f70`) came before the fix (`8e54068`).
  - The fix touched the tests only in their headers (REQ-DEV-001, and one docstring). No assertion was weakened.
  - `docs/decisions.md` only gains lines.
  - No commit carries AI attribution.
  - No drive-by edits: every file maps to the plan's P0-P4 or to a round-one finding.

## Producers of hardened invariant(s)

The wave hardens four invariants:
1. The engine is reachable beyond loopback only by opt-in. With no list, whatever arrives off loopback
   is refused, and a bind beyond loopback with no list does not start (D-171 clause 2, note 1).
2. With a list, a foreign Host gets 400 (clause 1).
3. The app's engine address is set per build, with loopback as the fallback. The simulator build is
   always loopback (clause 4, note 5).
4. Nothing new leaves the phone (D-126; D-160 as amended by D-168 note 9).

| producer | invariant | citing test | gap |
|---|---|---|---|
| `main.py:568-578`, `:751-762` (arrival rule, middleware) | 1 | `test_engine_host.py:53`, `:72` | none |
| `main.py:646-653` (startup check), `scripts/engine_service.sh:57-67`, `:75` | 1 | `test_engine_host.py:58`; `test_engine_service.py:364`, `:373` | none |
| `Makefile:267` (`make run`) | 1 | `test_engine_service.py:414` | none |
| `scripts/install_engine_service.sh:36-62` (wrapper, keep-mode) | 1, 2 | `test_engine_service.py:349`, `:355`, `:398`, `:387` | loopback-stays-loopback (**M7**) |
| `Dockerfile:46`, a hand-typed uvicorn | 1 | covered by the arrival rule (`test_engine_host.py:72`) | a list for a hosted engine: #94 |
| `main.py:554-565` (list, Host parse) | 2 | `test_engine_host.py:36-50`, `:81`, `:90` | none |
| `Engine.xcconfig`, `Info.plist`, `project.pbxproj` | 3 | `test_engine_address.py:18`, `:27`, `:36`, `:60` | none |
| `EngineClient.localDefault`, `engineURL` (`EngineClient.swift:144-154`) | 3 | `test_engine_address.py:45`; `EngineClientTests.swift:544`, `:551` | none |
| `ios/app.sh:112-116` (simulator build) | 3 | `test_engine_service.py:422` | none |
| `EngineClient`'s requests (`EngineClient.swift:184-215`) | 4 | `test_router_hints.py:229`; client-decls | none (unchanged) |

## Acceptance criteria evidence

REQ-DEV-001 (`docs/prd.md:551`), which comes from `m18-plan.md:30`:
- **Opt-in, loopback the default** → `test_engine_service.py:349`, `:355`; `install_engine_service.sh:54-62`.
- **A reinstall keeps the mode it finds** → `test_engine_service.py:398`, for LAN kept and closed.
  Loopback kept is untested (**M7**).
- **With no list, a request arriving on a network address is refused** → `test_engine_host.py:72`, and
  the real-engine probes above.
- **An exposed engine refuses a Host not on its list** → `test_engine_host.py:45`, `:81`, `:90`.
- **A bind beyond loopback with no list does not start** → `test_engine_host.py:58`;
  `test_engine_service.py:373`.
- **The address per build, loopback when unset** → `test_engine_address.py:18`, `:45`;
  `EngineClientTests.swift:544`, `:551`.
- **The simulator build is always loopback** → `test_engine_service.py:422`, and `-showBuildSettings`.
- **The app declares local networking** → `test_engine_address.py:27`.
- **Nothing new leaves the phone** → `test_router_hints.py:229`.
- **The app runs on the owner's iPhone** → the owner's own run, which the row honestly marks
  **PARTIAL**. The page that guides it has two false statements (**B2**).

## K.8 contract drift check

`grep -n` at `8e54068`:
```
ios/ModelRanking/Engine/EngineClient.swift:144:    static let localDefault = engineURL(from: Bundle.main.object(forInfoDictionaryKey: "EngineURL") as? String)
ios/ModelRanking/Engine/EngineClient.swift:148:    static func engineURL(from raw: String?) -> URL {
ios/ModelRanking/Engine/EngineClient.swift:168:    init(baseURL: URL = EngineClient.localDefault, session: URLSession? = nil) {
ios/Config/Info.plist:5:	<key>EngineURL</key>
scripts/engine_service.sh:75:exec "$REPO/.venv/bin/python" -m uvicorn app.adapter.main:app --host "${MODEL_RANKING_BIND:-127.0.0.1}" --port "$PORT"
Makefile:267:	$(PY) -m uvicorn app.adapter.main:app --host 127.0.0.1 --port 8080 --reload
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
  - `localDefault` keeps its name and type.
  - `validate_startup_config` keeps its signature.
  - The launcher's `exec` line changes only as the plan says.
- The two variable names match across the engine, the installer and the launcher.
- `/v1` gains one error code, `unknown_host`, in the one error shape, under D-171. No route changes
  shape.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K3** `ios/ModelRanking/Engine/EngineClient.swift:133` (`SameHostOnly`). The redirect guard compares
  hosts case-sensitively (`request.url?.host == host`), but DNS names are not case-sensitive. The page's
  own example address is mixed-case (`Umut-MacBook-Pro-2.local`). URLSession sends the Host
  lower-cased (round one measured it), so a same-host redirect built from that Host would be refused
  as off-host. It is latent: the client asks no path with a trailing slash, and the engine sends no
  redirect today. The fix would compare lower-cased hosts, with a test. Enhancement (robustness).

## Risks queued to next M

- **R3** `src/app/adapter/main.py:568-578`. The no-list rule reads the socket's local address. So
  anything that forwards to the engine's loopback re-exposes an engine with no list, with every Host
  served: a reverse proxy on the same machine, `ssh -L`, `tailscale serve` or a tunnel.

  A listed engine behind a forwarder is exposed only as far as its list. D-171 note 1's "whatever
  started it" is true of the bind, not of what sits in front of it. What would show it: the owner
  reaching the engine from outside the house by a tunnel with no list set. The hosted-engine work
  (#94, Stage 5.1) should require a list whatever the bind.
