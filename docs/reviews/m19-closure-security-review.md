---
record_type: review
id: m19-closure-security-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19 closure security review and Stage 5.1 release review: the engine on Fly.io, the app on TestFlight

> **Independent seat, two jobs in one.** This record is both the M19 closure security seat (D-172)
> and the **Stage 5.1 release security review** that the M18 closure seat said was still owed. The
> owner called a first release on 2026-10-07: the engine hosted on Fly.io and the iPhone app on
> TestFlight (D-185). This review is BLOCKING before any deploy. I wrote none of M19's code and sat in
> none of its wave seats. I used the Stage 5.1 profile (`.claude/agents/Security-Reviewer.md`, read
> from `origin/main`). I write this file under the name the dispatch gave, not the profile's default
> name, as the M18 seat did.
>
> Policy was read from the base, `0198eb3` (`main` before M19): `docs/security-baseline.md`,
> `permission-matrix.md`, `docs/security-invariants.md`, `AGENTS.md`. None of them changes in the
> range. `.claude/settings.json` changes only in its Bash guard (#142), and
> `conformance/test-hook-claims.py` adds three blocked and one allowed case to match.
>
> The surface is `git diff 0198eb3 7fde40d`: 180 commits (164 not merges), 192 files,
> +63,189/−706. About 45,000 of those lines are W4's measurement files and fixtures. `7fde40d` is the
> head of the stacked waves W4 and W5; W1 to W3 are on `main`. Nothing has been deployed, and Docker
> was not running here, so the image was not built. The only repository file this seat writes is this
> one, and it is not committed.

## Verdict

**Independent:** yes.

**Verdict:** MAJOR

Nothing is BLOCKING. There is **1 MAJOR, 6 MINOR and 9 INFO**.

**May the release be deployed once the owner's steps are done?**
- **The engine on Fly.io: yes,** once W4 and W5 have closed with their own Code-Reviewer and Tester
  (S12). No finding here blocks the engine deploy. Each MINOR can be fixed after it, or filed.
- **The app on TestFlight: not before S1 is fixed.** As the owner's Mac is set up today, a Release
  archive does not carry the hosted HTTPS address. It carries his Mac's cleartext address. The fix is
  a one-line move in `ios/Config/Engine.xcconfig` with a test. If the owner uploads before that fix,
  he must first remove `ENGINE_URL` from his `ios/Config/Engine.local.xcconfig` and read the archived
  Info.plist back (S1).

The scale is the M18 seat's:
- **BLOCKING:** ships and can be exploited now, or the permission matrix §11 human-review trigger fires.
- **MAJOR:** not exploitable for real harm today, but a release control is weaker than its record
  says, in a way that would hide an exploitable state. Fix before the step it guards.
- **MINOR:** an invariant or a control that a code change could break with every gate green, or a
  claim wider than its test. Not exploitable in the current scope.
- **INFO:** checked and recorded; no action unless stated.

**What holds, measured:**
- **What goes public is what D-185 says.** I derived the public artifact from the served copy and
  served it in process in the hosted configuration: `APP_ENV=production`, the Host list
  `model-ranking.fly.dev`, bind `0.0.0.0`. Every route and every task and budget answered 200 on that
  Host. No row of the seven left-out sources is in the file or in any answer, and no left-out-only
  model appears anywhere. The file's bytes hold no local path, Mac name or LAN address. `/health`
  says only status, version, build, `evidence` and `refresh: off` (S8).
- **The hosted engine fails closed.** The image tells its startup check where it binds, so with no
  Host list it refuses to boot. `fly.toml` names the one Host, forces HTTPS, and its health check
  sends that Host. Production refuses to boot without a build stamp. CORS is unset. No route mutates.
  The mutants of these that I ran were killed (§3: F1-F3, D1); the rest are INV-30 to INV-32's tests.
- **The deploy path holds.** The script refuses an uncommitted tree. It ships the derived artifact,
  never the Mac's, and it fails unless `/health` answers the build it deployed. Cold start publishes
  the container on loopback only. The build context is an allow list (R1-R4 and I1 in §3 killed).
- **The phone.** The session keeps and sends no cookie (#144; C1 killed by the Swift test's own
  assertion). A Release build cannot use cleartext to any host but a local one: ATS has only
  `NSAllowsLocalNetworking` (X2 killed). The privacy manifest declares no tracking and no collected
  data (X3 killed). `make client-decls` passes on the real client in all four configurations.
- **M18's open items in this range are closed or narrowed:** the base image by digest (#141; D5
  killed), the launcher judged by exit status (#145; R5 killed), cookies (#144), the Mac's name out of
  the tracked tree (#147), and the three force-push spellings (#142; G1, G2 killed).
- **`make check-fast` passes on `7fde40d`, and no secret is in the range.**

**What does not hold:**
- **S1 (MAJOR).** The owner's local xcconfig, set up the way `docs/owner-iphone.md` tells him,
  replaces the Release address. A TestFlight archive would then send requests in cleartext to a
  `.local` name that any device on a tester's network can answer to. The test reads only the tracked
  file.
- **S2.** One line in `ContentView.swift` sends what the reader typed to the engine, now a public
  host, with every gate green: a local `budget` shadows the property (Q1b, measured).
- **S3.** Nothing caps what the public engine costs or serves. `/v1/boards` is 511 KB to a client that
  does not ask for gzip, and Fly bills egress per GB with no cap on its pricing page.
- **S4.** Five mutants of the hosted image's least privilege and of the artifact's scrub pass the
  full suite. The invariants list has no row for the hosted engine, and two of its gap rows are stale.
- **S5.** The force-push and protected-branch guard still passes quoted, abbreviated and
  config-driven spellings, and `HEAD:refs/heads/main`. Branch protection on `main` holds (read).
- **S6.** Nothing stops an agent session from running `fly` with the owner's login.
- **S7.** The deploy script ships whatever commit is checked out, not `origin/main`.

## 0. Surface and method

**Waves.**
- W1 (on `main`): model names in each maker's spelling, one release as one model, attribution (#112,
  #129, #130, #124, #162), board guards by id (D-179).
- W2 (on `main`): the phone's privacy sinks and arithmetic rules checked on the compiled module
  (D-180, D-181), the cookie-less session (#144), `model_id` on each pick (D-182).
- W3 (on `main`): the gates before the push: CI's skips counted, the test run offline on macOS
  (`scripts/offline.sb`, D-183), the plan's security globs read.
- W4 (stacked): reading a question, second round (D-184). Only the Engine's reading rules change
  (`Router.swift`, `Reading.swift`), with their measurement files.
- W5 (stacked): the first release (D-185): `fly.toml`, the `Dockerfile`'s `hosted` stage,
  `.dockerignore`, `scripts/deploy_hosted_engine.sh`, `src/app/workflows/public.py`, the app's Release
  config, privacy manifest and icon, `docs/cold-start.sh`, `docs/journey.sh`, and #141, #142, #145,
  #147.

**Method.**
- **Worktree.** My own, detached at `7fde40d`, with its own venv and a copy of the served
  `advisor.db`. Every command ran behind the guard stubs for `launchctl`, `simctl` and `xcodebuild`.
- **The served artifact.** Read only. sha256 `dac97873…9344` before and after. The public artifact
  was derived into my scratch folder, never into the worktree.
- **Mutants.** A script applies each mutant as an exact, single-match edit. It saves the file's bytes
  and sha256 first, runs the cited tests, and, for a survivor, the full Python suite inside
  `scripts/offline.sb`, as `make test` runs it. It restores the bytes in a `finally` and asserts the
  sha256. Every restore matched, and `git status` was empty after each batch. My first survivor batch
  ran the full suite outside the sandbox, where the suite refuses to start (#122), so those five
  results were void. I re-ran them inside the profile, after a baseline run there (2100 passed).
  The cookie mutant was read back to its own assertion message, not just its exit status.
- **Network.** I made no request except `gh` reads (branch protection, issue states) and public
  documentation: Fly's configuration, `fly deploy` and pricing pages, Apple's xcconfig page, and
  `swift-build`'s source for how XCBuild picks a setting. So `make deps` (pip-audit) and
  `make slopsquat`, which reach PyPI, were not run (§6). No product upstream was contacted, and
  `RUN_CONTRACT_TESTS` was not set.
- **The owner's machine.** No `fly`, Docker, deploy, installer, `launchctl`, simulator or browser. I
  ran the deploy script only through the tests, with stand-ins first on its PATH. Nothing of mine is
  still running. No process ended in SIGABRT, SIGSEGV or SIGBUS.
- **Model calls.** `make check-fast`'s `swift test` ran the on-device model tests once. The Swift
  mutant ran one test class.

**Gates I ran myself:**

| Gate | Result |
|---|---|
| `make check-fast` at `7fde40d` | **PASS.** lint, typecheck, records (conformance included), pytest 2100 passed and 25 skipped, `client-decls` 19 files in 4 configurations, `swift-test` 476 tests, each in the manifest |
| `make secrets` (gitleaks over the tree) | **no leaks** |
| `gitleaks detect --log-opts=0198eb3..7fde40d` | 164 commits, **no leaks** |
| `git diff 0198eb3 7fde40d \| gitleaks stdin` | **no leaks**. A random `ghp_` token fires, so the scan is live |
| `ruff check --select S,BLE src scripts` (the SAST stand-in) | 18 hits, the same 18 as at `0198eb3` and at M18: documented catch-alls and an `assert`. No new rule class |
| The Bash guard, run on payloads (`/bin/sh`, `/usr/bin/grep`) | 26 payloads; holes listed in S5 |
| Branch protection on `main` (`gh api`, read) | `enforce_admins` on, force pushes and deletions off, pull request reviews required |
| The public artifact served in the hosted configuration (in process) | §2 |
| `make deps`, `make slopsquat` | **Not run**: the seat may not reach PyPI (§6) |

## 1. Findings

### BLOCKING

None.

The permission matrix §11 human-review trigger does not fire. No auth, payment or migration path is
in the range. The hosted engine receives no personal data: only a surface id and a budget (INV-64).
The phone's store of typed questions has no code change in the range: `FrontDoor.swift`,
`StandingsStore.swift` and `ContentView.swift` are unchanged, and only the gates around them grew. The public derivation is a copy, not a schema migration. The deploy
to a real cloud service (permission matrix §3) has its ADR, D-185, which the owner reviews by
merging, and he runs it himself.

### MAJOR

**S1 (MAJOR): A Release archive built on the owner's Mac reaches his Mac in cleartext, not the hosted
engine over HTTPS. D-185 clause 4 and its test say the opposite, and the test cannot see it.**

**Where.**
- `ios/Config/Engine.xcconfig:9` sets `ENGINE_URL[config=Release] = https:/$()/model-ranking.fly.dev`.
  Line 15, below it, is `#include? "Engine.local.xcconfig"`.
- `docs/owner-iphone.md:23`, ratified at M18, tells the owner to put an unconditional
  `ENGINE_URL = http:/$()/My-Mac.local:8080` in that local file. His phone runs that way today (M18
  seat, S13).
- `docs/release-testflight.md:50-53` says "Do not set `ENGINE_URL` there for a TestFlight build, or
  it replaces the hosted address". The same step says to create the file only "if
  `docs/owner-iphone.md` has not", so the file already has the line.
- `tests/unit/test_testflight_ready.py:37-41` and `:77-81` parse the tracked file's own lines only.

**How Xcode resolves it.** Apple's xcconfig page: "If you add the same setting multiple times, Xcode
uses the last instance of the setting". XCBuild's `MacroValueAssignmentTable.push` puts each new
assignment ahead of the earlier ones. `firstMatchingCondition` returns the first match, and
"unconditional macro value assignments are considered to match any conditions". So the included
unconditional line, read after line 9, wins for Release too.

**What happens.** The owner archives as `docs/release-testflight.md` §2.3 says. Then:
- The TestFlight build asks `http://<his Mac>.local:8080`. ATS allows it, because the plist keeps
  `NSAllowsLocalNetworking`. Testers get the local-network prompt, whose text names "the engine on
  your Mac".
- On any tester's network, any device that answers mDNS for that name becomes their engine. It reads
  each request's `task` and `budget` in cleartext, and it can serve any rankings and messages, within
  the phone's byte ceilings and closed sets.
- On the owner's own network, internal testers get his Mac's full artifact, the seven left-out
  sources included. That is against D-185 clause 3.
- The binary carries his Mac's name to every tester (#147's concern).
- Nothing catches it before upload. The only check is `docs/release-testflight.md:70-71`, which is the
  failure screen.

**Why MAJOR, not BLOCKING.** The data is public, nothing can be written, and the reader's text still
never leaves the phone. But the release's own record (D-185 clause 4, the test, the doc's step 3: "A
Release build reaches `https://model-ranking.fly.dev`") does not hold on the one machine that builds
the archive, set up exactly as the project told him to.

**Fix.**
1. Move `#include? "Engine.local.xcconfig"` above line 9. A local file then overrides Debug and never
   Release.
2. Add a test that nothing sets `ENGINE_URL` after the Release line: no assignment and no include.
3. Change `docs/owner-iphone.md:23` to `ENGINE_URL[config=Debug] = …`.
4. Add a step to `docs/release-testflight.md` after Archive: run `plutil -extract EngineURL raw` on
   the archived app's `Info.plist`. It must print `https://model-ranking.fly.dev`.
5. Optional: a Release-only build phase that fails when `EngineURL` is not `https://`.

### MINOR

**S2 (MINOR): INV-64 has an open route. One line in the view sends what the reader typed to the
engine, and every gate passes. The engine is now a public host whose access log keeps the query
string.**

- **Measured (Q1b).** In `ContentView.swift` `load()`, before line 958, I added
  `let budget = asked.isEmpty ? self.budget : asked`. The call stays `client.recommendation(task:
  task, budget: budget)`, so the text pin is satisfied. `asked` holds the last question typed.
  - The text gates passed (`test_router_hints.py`, `test_ios_client_contract.py`,
    `test_client_decl_gate.py`: 144 passed).
  - `client-decls` passed, so the mutant compiles, in all four configurations.
  - The full Python suite passed (2100). `swift test` does not compile the view.
- **Why the gates miss it.**
  - `tests/unit/test_router_hints.py:453-467` refuses any assignment to `task`, a shadowing `let task`
    included, but it has no rule for `budget`.
  - `tests/unit/test_ios_client_contract.py:891` pins the property's spelling
    (`private let budget = "unlimited"`), which a shadow leaves alone. My first variant, Q1, made the
    property a `var`, and that pin killed it.
  - D-180 trusts a sink's parameters, so `client-decls` never looks at what the view passes in.
- **The pair no wave could see.** W5 made the engine public: the request now reaches a third-party
  host, and uvicorn logs each request line, query string included. W3's security globs
  (`docs/plans/m19-plan.md` §3) do not include `ContentView.swift`. So the change that would leak is
  not even a HIGH wave.
- **Why MINOR.** It needs a code change. The shipped view passes the constant, and
  `/v1/recommendations` would refuse the value (`unknown_budget`) after it had arrived.
- **Fix.**
  - In the text pin: refuse any local declaration named `task` or `budget` in the view, and any
    assignment to `budget`.
  - Better, in `client-decls`: each argument of `EngineClient.recommendation` must resolve to the
    view's stored `task` or `budget`, not a local.
  - Add `ios/ModelRanking/ContentView.swift` to the security globs.

**S3 (MINOR): Nothing caps what the public engine costs or serves.**

- **Measured.**
  - `/v1/boards` on the public artifact is 511,346 bytes uncompressed and 38,226 gzipped. GZip runs
    only when the client asks for it (`src/app/adapter/main.py:666`).
  - There is no rate limit or per-client bound in `main.py`. The edge cap is 8 concurrent requests on
    one machine (`fly.toml:43-49`).
- **Fly, documented.** Egress is "$0.02/GB in North America and Europe", $0.04 in Asia Pacific,
    Oceania and South America, and $0.12 in Africa and India. The pricing page names no spending cap
    or billing alert.
- **What an attacker does.** A loop of `/v1/boards` with `Accept-Encoding: identity` costs the owner
  about $0.02 per 2,000 requests. Each sustained 50 MB/s is about $3.60 an hour, or $85 a day, at the
  cheapest rate, and nothing alerts. The same flood fills the 8 slots, so the phone gets queued or
  refused. This is OWASP API4:2023, unrestricted resource consumption.
- **Why MINOR.** It costs money and availability; no data leaks, and nothing is changed.
- **Fix.**
  - A billing alert or prepaid limit on the Fly organisation, before the deploy.
  - Serve `/v1/boards` compressed only, or refuse it uncompressed past a size.
  - `Cache-Control` and `ETag` on `/v1/boards`, which changes once a day.
  - A per-client fairness limit keyed on `Fly-Client-IP` that fails OPEN, as the baseline's control
    class requires.

**S4 (MINOR): The hosted image's least privilege and the public artifact's scrub hold as written, but
no test holds them. The invariants list has no row for the hosted engine.**

- **Survivors**, each with the targeted tests and then the full suite inside `scripts/offline.sb`
  (2100 passed every time):
  - D2: `USER root` added to the `hosted` stage (`Dockerfile:66-68`).
  - D3: `USER appuser` removed (`Dockerfile:48`).
  - D4: `COPY --chown=10001`, so the engine's user can write the served file (`Dockerfile:67`).
  - P4: no `VACUUM` (`src/app/workflows/public.py:75`). Measured on a scratch copy: the shipped file
    would still hold 471 copies of OpenRouter's source URL and 266 `swebench` strings in free pages.
    SQLite's `secure_delete` is off.
  - P5: the derived file mode 0o666, world-writable, instead of 0o644 (`public.py:80`). The test checks
    only the read bit.
- **The list.** `docs/security-invariants.md` says Stage 5.1 needs it before any deploy. It has no
  row for any of these:
  - the hosted Host list taken from the app name;
  - the boot refusal beyond loopback with no list (#94);
  - the public artifact having no row or byte of a left-out source;
  - a Release build reaching HTTPS;
  - a non-root engine reading a file it cannot write.
- **Stale rows.** The first four have tests (`test_hosted_engine.py`, `test_public_artifact.py`,
  `test_testflight_ready.py`), but no row cites them, so the list's gate would not notice one
  removed. And two gap rows and one paragraph are stale:
  - G-8 (`:177`) still says "by tag", but `160e1a7` closed it.
  - G-7 (`:176`) still names `-uf`, `-fu` and `--mirror`, which are now blocked. S5 lists what still
    passes.
  - The "Related, not a gap. #94" paragraph (`:189`) describes the image before W5.
- **Why MINOR.** The shipped files are right. The image is private, and the file is never served
  whole.
- **Fix.**
  - New rows, each with a test:
    - the serving and hosted stages' last `USER` is not root, and the `COPY` into `/srv` has no
      `--chown`;
    - after `derive`, `PRAGMA freelist_count` is 0, no left-out source name is in the file's bytes,
      and the mode is exactly 0o644.
  - Rewrite G-7 and G-8, and the #94 paragraph.

**S5 (MINOR): #142 closes the three spellings M18 measured. The guard still passes others, and the
protected-branch rule passes a full ref name.**

- **Where.** `.claude/settings.json:49`.
- **Measured: exit 0 (allowed).**
  - `git push origin '+wave/x'` and `"+wave/x"`: the shell removes the quote, git gets a force
    refspec.
  - `git push '-f' origin wave/x`.
  - `git push --mirr origin` and `--mirro`: git accepts a unique prefix of a long option.
  - `git -c remote.origin.mirror=true push origin`, and the same set with `git config … && git push`.
  - `git -c 'remote.origin.push=+refs/heads/*:refs/heads/*' push origin`.
  - `git push origin HEAD:refs/heads/main` and `git push origin refs/heads/main`: the main rule wants
    a space or `:` right before `main`.
  - `git push --delete`, `-d` and `:x`: a remote branch deleted. Not in the policy list.
- **Measured: exit 2 (blocked).** `-uf`, `-fu`, `--mirror`, `--force`, `-f`, `+wave/x`,
  `--force-w…`, `origin main`, `reset --hard`. G1 and G2 (§3) kill the #142 fix if it is reverted.
- **What still holds `main`.** Branch protection, read with `gh`: `enforce_admins` on, force pushes
  and deletions off, reviews required. So a direct push is refused even with the owner's credentials.
  What is exposed is a wave branch's history, as at M18.
- **Why MINOR.** As M18's S6.
- **Fix.**
  - Match after removing quotes, and match `--mi` prefixes, `mirror=` and `push=+` in `-c`, and
    `refs/heads/(main|master|trunk)`.
  - Or say plainly that the guard is best effort. Then hold wave branches on GitHub with a ruleset
    that refuses force pushes to `wave/*`, and narrow INV-82's "cannot".
  - A hook change is the owner's.

**S6 (MINOR): Once the owner runs `fly auth login`, an agent session on his Mac can deploy or destroy
the hosted engine. The only thing in the way is a permission prompt.**

- **What the rules say.**
  - Permission matrix §3: "Connect to real cloud services: ❌ DENY".
  - D-185 clause 5: "Nothing is deployed or uploaded by the agent".
  - Agents run with the owner's credentials (D-161).
- **What enforces them.** Only the absence of `fly` from `.claude/settings.json`'s `permissions.allow`.
  There is no `deny` entry and no guard pattern.
- **What could happen.** A session run with wider user-level permissions, or a prompt approved in a
  hurry, could run `fly deploy`, `fly ssh console` or `fly apps destroy model-ranking`. The last one
  frees the global name; see S10.
- **Fix.** Add `permissions.deny` entries for `Bash(fly:*)`, `Bash(flyctl:*)` and
  `Bash(scripts/deploy_hosted_engine.sh:*)`, and the same words in the Bash guard (the owner's change).

**S7 (MINOR): The deploy script ships whatever commit is checked out.**

- **Where.** `scripts/deploy_hosted_engine.sh:27-32` checks that the tree is clean and stamps
  `release-<sha>`. Nothing checks that HEAD is `origin/main`.
- **Compared with the Mac.** The Mac's service runs only a deployed release of `origin/main` (D-170,
  INV-29). The hosted engine, the one the public reads, has no twin of that rule.
  `docs/release-testflight.md:17` asks for `git checkout main && git pull`, and nothing holds it.
- **What could happen.** A wave branch, unreviewed code or an unpushed local commit goes public,
  stamped with a sha that may exist nowhere else.
- **Fix.** After `git fetch`, refuse unless `HEAD` equals `origin/main`, or `--allow-unmerged` is said
  out loud. Add a test in `tests/unit/test_deploy_hosted.py`.

### INFO (verified; no action unless stated)

**S8: The hosted surface, measured.**
- I served the public artifact in the hosted configuration: 5 routes, then every task with every
  budget. Every answer was 200 on `model-ranking.fly.dev`.
- The derivation removed 815 score rows and 439 price rows. `px_median` was rebuilt from LiteLLM's
  prices.
- One model is left with no evidence. It appears in no answer.
- The surfaces whose only source is left out answer `no_evidence` (D-121's path).
- `/health`: `{"status","version","build","evidence","refresh"}`. It names no path and no source.
- uvicorn 0.54.0 trusts forwarded headers only from `127.0.0.1,::1`. So the access log records Fly's
  proxy address, never a tester's.

**S9: Licence residue (#88, the owner's ruling, not a security hole).**
- `/v1/boards`, and every answer that carries prices, still credits "OpenRouter's public model
  catalog" (`src/app/workflows/rank.py:41-44`), though no OpenRouter row is served.
- LiteLLM's own table carries 456 `openrouter/…` alias rows. 273 of them link to 179 models, and 7
  models are priced only by them. These are OpenRouter's prices as LiteLLM records them, under MIT.
- Whether either needs to change is the licence ruling's question, not this seat's.

**S10: The Fly app name is global, first come first served, and published in a public repository.**
- The rename path at creation is tied by tests: `fly.toml`'s app, the Host list, the health check's
  Host and the Release URL (`test_hosted_engine.py:92`, `test_testflight_ready.py:77`).
- What is left is a dangling name. If the app is ever destroyed while builds are installed, anyone can
  claim `model-ranking`, and every installed build talks to them over valid TLS.
- TestFlight builds expire after 90 days, which bounds this.
- Do not destroy the app while builds live. A domain the owner controls would remove the risk.

**S11: The privacy manifest's "nothing collected" holds today.**
- Requests carry only `task` and `budget` (INV-64, with S2's caveat), and no tester address is logged
  (S8).
- A common setup behind a proxy sets `FORWARDED_ALLOW_IPS='*'` to log real client addresses. That
  would pair each tester's address with the surface their question went to. Revisit the App Store privacy answers if
  that ever changes.

**S12: W4 and W5 have no Code-Reviewer or Tester record at `7fde40d`.**
- The profile trusts the wave seats for correctness and test completeness. For W4 and W5 they have
  not run, so this review does not replace them.
- If their fixes touch the release surface (§0, W5's list), the release is owed a short security read
  of that change before the deploy.

**S13: `fly deploy --ha` defaults to true** ("Create spare machines…", per Fly's docs). The first
deploy places a spare machine. `fly.toml`'s "One machine always up" and the doc's "about two dollars a
month" then understate it about twice. Cost, not security. `--ha=false` matches the file.

**S14: `.dockerignore` lets in everything under `src/`, ignored files included.**
- `git status --porcelain` does not see ignored files. So an ignored file under `src/`, such as a
  `.env`, would reach Fly's remote builder.
- It would not reach the final image, which copies only the installed package.
- Adding exclusions for `.env*`, `*.pem`, `*.key` and `__pycache__` after the `src` line would close it.

**S15: Dependencies.**
- One new dependency, `httpx2` 2.13.1, with `httpcore2` and `truststore`, in `requirements/dev.lock`
  only.
- `requirements/serve.lock`, the one the image installs, is unchanged since M18.
- Starlette 1.7.0's own test client imports `httpx2` first. Its dist-info names Pydantic Services as
  maintainer and Tom Christie as author.
- I could not run `make deps` or `make slopsquat` (§6). They must pass on the release commit; the
  pre-push hook (`.githooks/pre-push`) runs `make gate`, which includes both.

**S16: Carried, unchanged.**
- G-1 (#172) and G-2 (#171, #173), as D-180 and D-181 state them.
- CI's half of #122 and CI's unlocked install (#81) are the owner's.
- M18's S13: the owner's phone runs a Debug build.

## 2. The M18 closure seat's findings, on this head

| M18 finding | Status | Evidence |
|---|---|---|
| S1-S4, S16 | Closed at M18 | M18 dispositions; INV-80, -4, -67, -74, -33, -84 rows |
| S5 (unpinned pip, base by tag) | **Closed** | `make install` (M18); `Dockerfile:12`, `:24` by digest; D5 killed |
| S6 (force-push guard) | **Narrowed** | The three spellings are blocked (G1, G2 killed); others remain (this review's S5) |
| S7 (home network) | Unchanged | D-171 |
| S8 (proxy) | Closed (#143); #150 adds macOS system proxies | `tests/conftest.py`; the run is offline under `scripts/offline.sb` |
| S9 (redirect by host only) | Unchanged | On HTTPS, a redirect to cleartext on the same host is refused by ATS |
| S10 (cookies) | **Closed** (#144) | INV-85; C1 killed |
| S11 (preflight by output) | **Closed** (#145) | `scripts/engine_service.sh:59-75`; R5 killed |
| S12 (scratch the sweep missed) | Closed (#146) | INV-49's row |
| S13 (Debug on the phone) | Unchanged | This review's S16; this review's S1 depends on it |
| S14 (Mac name in the tree) | **Closed in the tree** (#147) | Placeholders `my-mac.local`, `probe-mac`; git history keeps the old name |
| S15 (G-1) | **Narrowed** (D-180) | P2, P3 and the W2 reviews' relays refused; #172 for the rest. INV-64's view route is this review's S2 |
| S17, S18 | Unchanged | — |

## 3. Mutants

Each was one exact edit, restored by bytes and checked by sha256. "Killed" means a cited test failed.

| # | Row or claim | The edit | Result | Killed by |
|---|---|---|---|---|
| F1 | #94 | `fly.toml` sets no Host list | KILLED | `test_hosted_engine.py::test_the_hosted_engine_answers_to_its_own_name_and_is_checked_by_it` |
| F2 | HTTPS at the edge | `force_https = false` | KILLED | same |
| F3 | #94 | the health check sends no Host | KILLED | same |
| D1 | #94, INV-25 | the image tells its check it binds loopback | KILLED | `::test_the_image_tells_its_startup_check_where_it_binds` |
| D2 | non-root | `USER root` in the `hosted` stage | **SURVIVED** | none; 2100 passed (S4) |
| D3 | non-root | `USER appuser` removed | **SURVIVED** | none (S4) |
| D4 | read-only file | `COPY --chown=10001` into `/srv` | **SURVIVED** | none (S4) |
| D5 | #141, INV-81 | the serving stage's base by tag | KILLED | `test_dependency_locks.py::test_the_serving_image_names_its_base_by_digest` |
| I1 | build context | `.dockerignore` loses its `*` | KILLED | `test_deploy_hosted.py::test_the_build_context_carries_what_the_image_copies_and_little_else` |
| P1 | #88 | OpenRouter not left out | KILLED | `test_public_artifact.py::test_the_left_out_sources_are_the_ones_the_licence_review_named` |
| P2 | #88 | no price row removed | KILLED | `::test_the_price_medians_are_rebuilt_from_the_kept_prices` |
| P3 | #88 | medians kept from the built artifact | KILLED | same |
| P4 | #88 | no `VACUUM` | **SURVIVED** | none; free pages keep the rows (S4) |
| P5 | #88 | the file world-writable (0o666) | **SURVIVED** | none (S4) |
| R1 | deploy | an uncommitted tree deploys | KILLED | `test_deploy_hosted.py::test_an_uncommitted_tree_is_refused_before_anything_is_built` |
| R2 | deploy, #88 | the Mac's full artifact is shipped | KILLED | `::test_a_deploy_stamps_the_commit_ships_the_public_artifact_and_checks_health` |
| R3 | deploy, L.7 | any build on `/health` passes | KILLED | `::test_a_health_answer_from_another_build_fails_the_deploy` |
| R4 | cold start | the container published on every interface | KILLED | `test_release_gates.py::test_a_cold_start_boots_the_hosted_image_on_loopback_and_journeys_it` |
| R5 | #145, INV-27 | the preflight judged by output only | KILLED | `test_engine_service.py::test_a_preflight_that_dies_without_a_word_stops_the_start` |
| X1 | D-185 cl. 4 | the Release URL over `http` | KILLED | `test_testflight_ready.py::test_a_release_build_reaches_the_hosted_engine_over_https` |
| X2 | INV-73 | ATS allows arbitrary loads | KILLED | `test_engine_address.py::test_the_partial_plist_carries_the_address_and_only_the_local_network_exception` |
| X3 | D-126 | the manifest declares tracking | KILLED | `test_testflight_ready.py::test_the_privacy_manifest_gives_a_reason_for_every_required_reason_api_the_app_calls` |
| G1 | #142, INV-82 | `--mirror` dropped from the guard | KILLED | `conformance/test-hook-claims.py` |
| G2 | #142, INV-82 | the option-cluster rule back to a lone `-f` | KILLED | same |
| C1 | #144, INV-85 | `httpShouldSetCookies = false` removed | KILLED | `EngineCookieTests.testTheShippedSessionNeitherStoresNorSendsACookie` ("the session attaches stored cookies to requests") |
| Q1 | INV-64 | the view's `budget` made a `@State var`, set to the typed text | KILLED | `test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on`, by spelling |
| Q1b | INV-64 | a local `let budget = asked.isEmpty ? self.budget : asked` before the call | **SURVIVED** | none: text gates 144, `client-decls` 4 configurations, 2100 passed (S2) |
| — | S1 | a local xcconfig's unconditional `ENGINE_URL` | Not a mutant: XCBuild's documented order; no test reads the effective value | — |

**Score.** 27 mutants: 21 killed and 6 survived. Every survivor is in a finding: D2, D3, D4, P4 and P5
in S4, and Q1b in S2. The W2 reviews replayed the M17 and W2 privacy relays across three rounds. I did
not repeat them; I tried a route of my own (Q1b).

## 4. Pairs no single wave could see

| Pair | What I found |
|---|---|
| W5's public engine × M18's phone setup (`docs/owner-iphone.md`) | The local xcconfig made for the Debug phone replaces the Release address (S1) |
| W5's public engine × the view's text pin × W3's security globs | A request that reaches a public, logging host can carry the typed question through a view the globs do not watch (S2) |
| W5's public engine × M18's opt-in gzip (D-173) × no rate limit | 511 KB per uncompressed `/v1/boards`, billed per GB with no cap (S3) |
| W5's derivation × SQLite's free pages | Only `VACUUM` scrubs the left-out rows from the shipped bytes, and no test holds it (S4) |
| #142's guard × git's option parsing × D-161's credentials | Quotes, abbreviations and config pass. `main` is held by GitHub, not by the guard (S5) |
| D-185 cl. 5 × the owner's `fly` login × the allow list | A prompt is the only thing between an agent and `fly` (S6) |
| D-170's `origin/main` rule × W5's deploy script | The Mac's rule has no hosted twin (S7) |
| The Host check (D-171) × Fly's health check | Fly's check reaches the machine over the private network with its own headers (Fly's docs), and it names the Host, so the list does not refuse it |
| `model_id` on `/v1` (D-182) × the field allowlist | Added to `PUBLIC_PICK_FIELDS` (`main.py:956-958`) under INV-35; the phone uses it only to group cards and never shows it |

## 5. The baseline and the profile, walked

| Item | Status | Evidence |
|---|---|---|
| §1 Secrets | **PASS** | §0 scans; no `.env`, key or provisioning file in the diff; `Engine.local.xcconfig` is ignored |
| §2 Dependency hygiene | **PASS, with a skip** | One dev-only dependency (S15); `serve.lock` unchanged; `make deps` and `make slopsquat` not run here |
| §3 External surface, default deny | **PASS, with S3** | No new route; one additive field (`model_id`) in the allowlist; the Host list required to boot beyond loopback; HTTPS forced |
| §4 Prompt injection | **PASS** | W4 changes the reading rules only (`Router.swift:704-721`): a question of fact now counts as a doubt and is held, and the image rule reaches every surface but the two coding ones. Whatever is sent is still one of the engine's surface ids (INV-69, INV-70). The engine has no model (INV-77) |
| §5 Auth, PII, payment, migration | **Not triggered** | §1, BLOCKING |
| §6 Destructive operations | **FINDING** | S5; no `rm -rf`, `reset --hard` or `DROP` in the range's code. `public.py` writes only a temporary file beside its target |
| §7 SAST | **Stand-in ran** | `ruff --select S,BLE`: 18, unchanged. bandit and semgrep are not installed |
| §8 PII and logging | **PASS** | No log carries typed text. uvicorn logs the proxy's address, not the tester's (S8, S11) |
| Baseline 2: authz on mutating routes | **PASS** | No mutating route (INV-30) |
| Baseline 3: CORS | **PASS** | Unset in `fly.toml` and the image; a wildcard is refused (INV-31) |
| Baseline 4: startup config, prod refuses | **PASS** | `APP_ENV=production`; build stamp, database, bounds and Host list checked at import (`main.py:509-598`); D1 killed |
| Baseline 5: creds and PII at rest | **N/A on the server**; the phone's register as INV-67 | — |
| Baseline 6: generic errors | **PASS** | INV-34; `unknown_host` is a generic 400 |
| Fail direction | **PASS** | The Host check, boot checks and ceilings fail closed. No rate limiter exists to fail either way (S3) |
| Built is wired | **PASS** | Each control reached from its live entry: the FastAPI app imported in production mode, the deploy and cold-start scripts run as scripts, the compiled client, the shipped session's configuration |
| Invariants list | **FINDING** | S4 |
| Senior human review trigger | **Not triggered** | §1 |

**Gates passed (the profile's list).**
- [x] Secret scan green: `make secrets` on the tree, and gitleaks on the range.
- [ ] `make deps`: not run by this seat (no network); owed on the release commit.
- [ ] `make slopsquat`: not run by this seat (no network); owed on the release commit.
- [x] Default deny preserved for new external surfaces.
- [x] Permission matrix not violated by the code. S6 is a control the matrix names but nothing
  enforces.
- [x] Prompt-injection hygiene.
- [x] Auth and PII: the trigger does not fire.
- [x] SAST stand-in.

**Acceptance criteria with a security side (file:line).**
- **#94** (the hosted engine fails closed and names its Host):
  - `tests/unit/test_hosted_engine.py:64`, `:71`, `:92`, `:105`.
- **#88** (the public artifact):
  - `tests/unit/test_public_artifact.py:27`, `:32`, `:45`, `:61`, `:77`;
  - `tests/unit/test_deploy_hosted.py:62`, with S4's survivors.
- **The deploy path:**
  - `tests/unit/test_deploy_hosted.py:62`, `:78`, `:84`, `:92`, `:102`;
  - `tests/unit/test_release_gates.py:35`, `:43`, `:51`, `:70`.
- **#141:** `tests/unit/test_dependency_locks.py:334`, `:341`.
- **#145:** `tests/unit/test_engine_service.py:604`.
- **#142:** `conformance/test-hook-claims.py:281-290`, with S5's holes.
- **#144:** `ios/EngineTests/EngineClientTests.swift:841`.
- **TestFlight readiness (D-185 cl. 4):**
  - `tests/unit/test_testflight_ready.py:43`, `:56`, `:71`;
  - `:77`, whose claim does not hold on the owner's Mac (S1).
- **INV-64** (nothing typed reaches a request):
  - `tests/unit/test_router_hints.py:426`;
  - `ios/EngineTests/EngineClientTests.swift:457`;
  - with S2's open route.
- **INV-65** (the boards request carries nothing): `ios/EngineTests/EngineClientTests.swift:489`.

## 6. Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| `make deps`, `make slopsquat` | Both reach PyPI; this seat may not | The serving lock is unchanged since M18's clean audit; the release commit's gate must run both (S15) |
| The image build, `make cold-start`, a container run | Docker was not running, and the seat may not run it | The Dockerfile was read and mutated as text; the artifact was served in process with the image's environment |
| `fly`, the deploy for real, the Fly health check | Out of bounds | Fly's behaviour comes from its documentation pages (§0) |
| An Xcode archive, `xcodebuild -showBuildSettings` | `xcodebuild` is stubbed | S1 rests on Apple's documented rule and XCBuild's source, not on a measured archive. The owner's step 4 in S1's fix measures it |
| `make ui-test`, the app on a device | Needs the simulator | Q1b was judged by the text gates, `client-decls` and the suite; nothing ran the view |
| A live probe of `model-ranking.fly.dev` (taken or not) | No network | S10 |
| A replay of every W2 relay | The W2 reviews ran three rounds of them | One new route tried (Q1b) |

## 7. What I did not check

- Whether the seven left-out sources are the right seven (the licence ruling, #88).
- What the owner's Fly organisation, billing and App Store Connect settings are.
- How a hostile engine's answer looks on screen.
- W4's reading changes beyond their security side (§5, item §4); W4's own seats will judge them.
