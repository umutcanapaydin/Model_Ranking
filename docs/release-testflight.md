---
record_type: register
id: release-testflight
status: draft
process_version: v6.6
date: 2026-10-07
---
# The first release: the engine on Fly.io, the app on TestFlight (M19-W5, D-185)

Your steps, in order. Everything the code could do is done: the image, `fly.toml`, the public
artifact, the deploy script, the app's icon, privacy manifest and Release address. What is left
needs your accounts, your card or your signing identity. **Deploy only after you have merged the
release's pull requests and the release's security verdict of record,
`docs/reviews/release-security.md`, is PASS or MINOR (not BLOCKING).** The first release was M19's
(TestFlight build 1); the next is v2, build 4, below.

## v2 (M20 + M21), in this order

This replaces the build-3 list: build 3 was never uploaded, and v2 ships M20 and M21 together as build 4.
The M21 closure security seat says the release verdict stands for v2, on six conditions
(`docs/reviews/m21-closure-security-review.md`, "The release re-read"); each step below names its condition.

1. **Merge** the one combined pull request from `closure/m21`, with **Create a merge commit** (not squash
   or rebase). It carries every commit of #213, #215, #217, #221, #224, #225, #229 (the M20 closure),
   #236, #240, #250 and #251, so GitHub marks those merged too, and the close checks, which read the
   commit history (D-192), keep the history they read. Then `git checkout main && git pull`, and restart
   every Claude Code session open in the clone (close it, then `cd ~/Desktop/ILGAR/model_ranking && claude`):
   the pull brings a changed guard and its new pin, and a session keeps the hooks it started with, so an old
   session blocks every Bash call and every write (`INSTALL.md`, "Changing the Bash guard").
2. **Run `make hooks` once** in your clone. From then on the commit-msg gate runs before every commit
   (`make check-fast`; `make check-red` for a declared red test commit; `make check-docs` for a docs-only
   one; `docs/refusals.md` R-1) and every push runs `make gate`, which runs the compiled gate
   (`make client-decls`). Nothing runs that gate automatically until you do (G-10; condition 2).
   And start every Claude Code session in the repository (`cd ~/Desktop/ILGAR/model_ranking && claude`), so
   its hooks load: the Bash guard, the Write refusal and the post-edit check load in no other session (#142;
   your ruling of 2026-10-10 on `repository-hooks`). Then, once, in such a session, type `/hooks` and check
   that the Bash hook is listed; its `onFailure` needs Claude Code 2.1.295 or later (`INSTALL.md`; the seat's S8).
3. **Run `make check`** on `main`'s tip after the merges, before the archive: it includes
   `client-decls` (condition 2).
4. **Let the Mac's engine refresh once with the new release** (§1 step 1; condition 1). The data names
   `web-dev`'s board (D-190) and the split DeepSeek releases (D-189), and the deploy refuses data another
   release built (#198). Wait for a night that *publishes*: a night whose data is unchanged keeps the old
   builder's name, and a refresh run by hand without `APP_BUILD` records `unknown`. Then
   `<served>.refresh.json` names `release-<sha>` for `main`'s tip. Do not use `DEPLOY_ACCEPT_DATA_FROM`
   for v2.
5. **Deploy** (§1 steps 5 and 6). The build is stamped `release-<sha>-data-<digest>-from-<sha>`.
6. **Check the families are served:** `curl -s https://model-ranking.fly.dev/v1/categories | grep -c
   refined_board` must print a number above 0.
7. **Check that Fly sets the client's address** (below, after the cost note; condition 3).
8. **Archive and upload build 4** (§2 steps 3 and 4; condition 4). `MARKETING_VERSION` is 0.2.0 and
   `CURRENT_PROJECT_VERSION` is 4 in the project already. Archive only after the deploy's `/health`
   check passes; the `plutil` readback of the signed archive must say `https://model-ranking.fly.dev`.
9. **Keep the habits** (condition 5): `fly auth logout` after each deploy, watch the usage page while
   people test, and `fly scale count 0` stops the engine at once. **Before external testers**, rule on
   D-185's table (D-186 clause 3; condition 6).

## 1. The engine on Fly.io (once)

1. **Update your checkout and your Mac's engine.** `git checkout main && git pull`, then `make
   install`, then `scripts/install_engine_service.sh` (it keeps the home-network mode it finds). The
   hosted engine serves a copy of the data your Mac's engine built, so the Mac must run the code you
   deploy: let it refresh once after the install (the next night, between 23:00 and 01:00), and check
   that `curl -s http://127.0.0.1:8080/health` names the new release and a refresh after it. The refresh
   records which release built the served data (`<served>.refresh.json`, `served_built_by`, #198), and
   the deploy refuses data another release built: a night whose data is unchanged keeps the old
   builder's name, and a refresh run by hand without `APP_BUILD` records `unknown`.
2. **Log in and add a card.** `fly auth login`. Fly asks for a payment method before it places a
   machine, even the smallest (D-123): add one at https://fly.io/dashboard → Billing. The
   declared machine (`shared-cpu-1x`, 256 MB, always on; the script deploys one, `--ha=false`)
   costs about two dollars a month.
3. **Create the app.** `fly apps create model-ranking`. If the name is taken, choose another and
   ask the agent to rename it on a branch: four places (`app`, `MODEL_RANKING_ALLOWED_HOSTS` and the
   health check's `Host` in `fly.toml`, and `ENGINE_URL[config=Release]` in
   `ios/Config/Engine.xcconfig`) and the tests that read them. Merge that pull request, then `git
   pull`: the deploy ships only `main`'s tip, from a clean tree.
4. **Try the image on your Mac first** (optional, free): with Docker Desktop running, `make
   cold-start` builds the hosted image, boots it with nothing saved, and runs the customer journey
   against it on `127.0.0.1:18080`.
5. **Deploy.** From the repository: `scripts/deploy_hosted_engine.sh --dry-run` first (it derives
   the public artifact and checks the tree), then `scripts/deploy_hosted_engine.sh`. It builds on
   Fly's builder, stamps the build `release-<sha>-data-<digest>-from-<sha>` (the code's commit, the public
   artifact's digest, and the release that built the data), and stops with an error unless
   `https://model-ranking.fly.dev/health` answers that build.
6. **Check it.** `make journey URL=https://model-ranking.fly.dev` runs the customer journey against
   the hosted engine: `/health` names the build, a coding question gets real picks, and every
   surface answers or says why it cannot.

**Cost.** Fly bills traffic out of the public engine (a `/v1/boards` answer is about 0.5 MB), and
has no billing alert and no spending cap. Since M20-W5 (#187) the engine answers one client at most
`MODEL_RANKING_RATE_LIMIT` times a clock minute (120 in `fly.toml`; `/health` is never limited). A
client is one IPv4 address, or one IPv6 /64.
- A `/v1/boards` answer (about 0.5 MB, which a phone needs once a day) counts as thirty requests,
  in a window of its own so standings never block a question (#228), so one address draws at most
  four a minute: about 2 MB a minute, twice that across the turn of a
  minute (a fixed window), about 3 GB a day kept up all day. Every other answer is a few KB.
- Many addresses multiply it: the limit is per address, not a cap on the bill. One IPv6 /48, which
  one person can rent, holds 65,536 /64s, so to the engine it can look like that many clients.
  Check Fly's current outbound price on its pricing page to turn gigabytes into money.
- The limit is per Fly machine and kept in memory. It fails open: if it breaks, the request is
  served and the engine logs a warning.

Look at the dashboard's usage page now and then once the app is shared.

**After the first deploy with the limit, check that Fly sets the client's address** (the W5 review's
R1): a forged `Fly-Client-IP` header must not give each request a new address. From any computer:

```
cd ~/Desktop/ILGAR/model_ranking && seq 1 250 | xargs -P 25 -I{} curl -s -o /dev/null -w "%{http_code}\n" -H "Fly-Client-IP: 198.51.100.{}" https://model-ranking.fly.dev/v1/budgets | sort | uniq -c
```

The 250 requests go 25 at a time, so they finish in a few seconds, well inside a minute. The count
of `429` must be above 0: every request came from your one address, whatever the forged header said.
If every answer is `200`, Fly passed the forged header through: stop sharing the app and say so in
#187. (The repo review's M2: one request at a time could take longer than the window.)

**After each deploy, log out:** `fly auth logout`. While you are logged in, a coding agent on this
Mac could deploy or destroy the app (#190).

**Never destroy the Fly app while TestFlight builds are installed.** Its name would be free for anyone
to claim, and every installed build would then ask their server (the security review's S10). To stop
the engine, run `fly scale count 0`; `fly scale count 1` starts it again.

**After each nightly refresh you want public,** run `scripts/deploy_hosted_engine.sh` again: the
public artifact is derived from the one your Mac serves, and each deploy is one image of code and
data. Nothing refreshes on Fly (D-116).

**What the public artifact leaves out:** nothing but the vendor plans, which the app never shows
(D-186, your ruling of 2026-10-08). The hosted engine serves every source your Mac's does. Before
external testers or the App Store, D-185's licence table is ruled source by source; leaving one out
is one line in `LEFT_OUT` in `src/app/workflows/public.py`.

## 2. The app on TestFlight

You need an Apple Developer Program membership (99 USD a year) for TestFlight.

1. **Signing.** In `ios/Config/Engine.local.xcconfig` (git-ignored; create it if `docs/owner-iphone.md`
   has not), set `DEVELOPMENT_TEAM = <your team id>`. If App Store Connect says the bundle id is taken,
   set `PRODUCT_BUNDLE_IDENTIFIER` there too. An `ENGINE_URL` there reaches Debug builds only: a
   Release build always asks the hosted engine (the Release address comes after this file).
2. **The app record.** At https://appstoreconnect.apple.com → Apps → "+": New App, iOS, the bundle id
   from step 1, a name (for example "Model Ranking"), primary language English.
3. **Archive.** Open `ios/ModelRanking.xcodeproj` in Xcode, choose "Any iOS Device (arm64)" as the
   destination, then Product → Archive. A Release build reaches `https://model-ranking.fly.dev`.
   To check before uploading: in the Organizer, right-click the archive → Show in Finder, and in
   Terminal run `plutil -p <the .xcarchive>/Products/Applications/ModelRanking.app/Info.plist | grep
   EngineURL`; it must say `https://model-ranking.fly.dev`.
4. **Upload.** In the Organizer that opens: Distribute App → App Store Connect → Upload. The
   encryption question is already answered in the app (no non-exempt encryption). Each later upload
   needs a higher build number: raise `CURRENT_PROJECT_VERSION` (Xcode: the target → General →
   Build) before you archive again.
5. **Testers.** In App Store Connect → TestFlight, add yourself and anyone on your team as internal
   testers (up to 100); they install the TestFlight app and accept the invitation. External testers
   need a Beta App Review first, which may ask that you are permitted to show each source's data
   (App Review guideline 5.2.2): that is what the public artifact is for.

## 3. If something fails

- **The deploy stops on `/health`:** `fly logs` shows why the engine refused to boot. The usual
  causes are a missing `APP_BUILD` (deploy with the script, not `fly deploy` by hand) or a Host list
  that does not name the app (step 1.3). If the engine boots but Fly's health check fails, the check
  may not be sending its `Host` header. The fallback, a TCP check in place of
  `[[http_service.checks]]`, changes `fly.toml` and INV-86's test (`tests/unit/test_hosted_engine.py`),
  so ask the agent for it as a pull request, merge it, `git pull`, and deploy again.
- **The app says it cannot reach the engine:** the address it asked is on the failure screen. A
  TestFlight build must show `https://model-ranking.fly.dev`.
- **The upload is refused for the icon:** the icon must be 1024 pixels with no transparency
  (`ios/ModelRanking/Assets.xcassets/AppIcon.appiconset/AppIcon.png`, a placeholder you may replace).
