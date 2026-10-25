---
record_type: register
id: owner-iphone
status: ratified
process_version: v6.6
date: 2026-09-29
---
# Running the app on your iPhone (M18-W1, D-171; D-222)

Since D-222 the hosted engine on Fly.io is the only engine, and the Mac runs none. A build on your
iPhone asks the hosted engine over HTTPS (#288), so there is nothing to open on the Mac and no address
to set. Do these once.

0. **Update your checkout.** In the repository: `git checkout main && git pull`. The Xcode project you
   build is your checkout's.
1. **Sign it.** Create `ios/Config/Engine.local.xcconfig` with your team:
   ```
   DEVELOPMENT_TEAM = <your team id>
   ```
   - Your team id is the `OU=` value this prints (10 characters):
     `security find-certificate -c "Apple Development" -p | openssl x509 -noout -subject`
   - If Xcode says the bundle id is taken, add `PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking.umut`.
   - The file is git-ignored; it never leaves your Mac. Do not set the team or the bundle id in
     Xcode's Signing screen: that edits the tracked project.
   - Xcode must know your Apple ID: Xcode → Settings → Accounts. Add it with `+` if it is not listed.
   - Set no `ENGINE_URL` here. Should you ever need one, write it for Debug builds only,
     `ENGINE_URL[config=Debug] = ...`, so a Release build (TestFlight) still reaches the hosted engine.
2. **Connect the iPhone.** Use a cable the first time. On the phone, turn on Developer Mode
   (Settings → Privacy & Security → Developer Mode) when iOS asks.
3. **Run.** Open `ios/ModelRanking.xcodeproj`, choose the iPhone as the destination and press Run. On
   the phone, trust your developer certificate (Settings → General → VPN & Device Management) if iOS
   asks.
4. **Check.** Ask a question. If the app cannot reach the engine, the line under the error shows the
   engine address it asked. It should be `https://model-ranking.fly.dev`; check that the phone is
   online and that `https://model-ranking.fly.dev/health` answers.

**Keep in mind:**
- An app signed with a free Apple ID stops opening after 7 days. Run it from Xcode again.
- The simulator build from `ios/app.sh` always talks to `127.0.0.1`, where `make run` serves, whatever
  step 1's file says.
