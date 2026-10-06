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
needs your accounts, your card or your signing identity. **Deploy only after the Stage 5.1 security
review of this wave has passed and you have merged its pull request.**

## 1. The engine on Fly.io (once)

1. **Update your checkout.** `git checkout main && git pull`, then `make install`.
2. **Log in and add a card.** `fly auth login`. Fly asks for a payment method before it places a
   machine, even the smallest (D-123): add one at https://fly.io/dashboard → Billing. The
   declared machine (`shared-cpu-1x`, 256 MB, always on) costs about two dollars a month.
3. **Create the app.** `fly apps create model-ranking`. If the name is taken, choose another, and
   change it in three places: `app` and `MODEL_RANKING_ALLOWED_HOSTS` in `fly.toml`, the health
   check's `Host` there too, and `ENGINE_URL[config=Release]` in `ios/Config/Engine.xcconfig`.
   Commit the change: the deploy refuses an uncommitted tree.
4. **Deploy.** From the repository: `scripts/deploy_hosted_engine.sh --dry-run` first (it derives
   the public artifact and checks the tree), then `scripts/deploy_hosted_engine.sh`. It builds on
   Fly's builder, stamps the build with the commit, and stops with an error unless
   `https://model-ranking.fly.dev/health` answers that build.
5. **Check it.** `curl https://model-ranking.fly.dev/health` shows `"build": "release-<sha>"`, and
   `curl https://model-ranking.fly.dev/v1/categories` lists the surfaces.

**After each nightly refresh you want public,** run `scripts/deploy_hosted_engine.sh` again: the
public artifact is derived from the one your Mac serves, and each deploy is one image of code and
data. Nothing refreshes on Fly (D-116).

**What the public artifact leaves out** (#88, D-185): SWE-bench's own board, ARC-AGI, DeepSWE,
Terminal-Bench, Epoch's web-dev copy, MMLU and OpenRouter's prices. `abstract`, `agentic-coding`,
`computer-use` and `web-dev` say they have no evidence on the hosted engine; your Mac's engine keeps
every source. To ship everything instead, remove a source from `LEFT_OUT` in
`src/app/workflows/public.py` only after you have the publisher's permission.

## 2. The app on TestFlight

You need an Apple Developer Program membership (99 USD a year) for TestFlight.

1. **Signing.** In `ios/Config/Engine.local.xcconfig` (git-ignored; create it if `docs/owner-iphone.md`
   has not), set `DEVELOPMENT_TEAM = <your team id>`. If App Store Connect says the bundle id is taken,
   set `PRODUCT_BUNDLE_IDENTIFIER` there too. Do not set `ENGINE_URL` there for a TestFlight build,
   or it replaces the hosted address.
2. **The app record.** At https://appstoreconnect.apple.com → Apps → "+": New App, iOS, the bundle id
   from step 1, a name (for example "Model Ranking"), primary language English.
3. **Archive.** Open `ios/ModelRanking.xcodeproj` in Xcode, choose "Any iOS Device (arm64)" as the
   destination, then Product → Archive. A Release build reaches `https://model-ranking.fly.dev`.
4. **Upload.** In the Organizer that opens: Distribute App → App Store Connect → Upload. The
   encryption question is already answered in the app (no non-exempt encryption).
5. **Testers.** In App Store Connect → TestFlight, add yourself and anyone on your team as internal
   testers (up to 100); they install the TestFlight app and accept the invitation. External testers
   need a Beta App Review first, which may ask that you are permitted to show each source's data
   (App Review guideline 5.2.2): that is what the public artifact is for.

## 3. If something fails

- **The deploy stops on `/health`:** `fly logs` shows why the engine refused to boot. The usual
  causes are a missing `APP_BUILD` (deploy with the script, not `fly deploy` by hand) or a Host list
  that does not name the app (step 1.3).
- **The app says it cannot reach the engine:** the address it asked is on the failure screen. A
  TestFlight build must show `https://model-ranking.fly.dev`.
- **The upload is refused for the icon:** the icon must be 1024 pixels with no transparency
  (`ios/ModelRanking/Assets.xcassets/AppIcon.appiconset/AppIcon.png`, a placeholder you may replace).
