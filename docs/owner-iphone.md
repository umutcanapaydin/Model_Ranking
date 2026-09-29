---
record_type: register
id: owner-iphone
status: ratified
process_version: v6.6
date: 2026-09-29
---
# Running the app on your iPhone (M18-W1, D-171)

The engine stays on your Mac. The phone reaches it over the network the Mac is on, by opt-in. Do these
once, **after the M18-W1 pull request is merged** (step 1 deploys `main`; before the merge the deployed
engine does not have the change).

1. **Open the engine to the network.** On the Mac, from the repository:
   `scripts/install_engine_service.sh --lan`
   It binds the engine to every network the Mac is on, and answers only to your Mac's own names
   (`umut-macbook-pro-2.local` and its address). It prints `home network: on`.
2. **Point the app at your Mac, and sign it.** Create `ios/Config/Engine.local.xcconfig`:
   ```
   ENGINE_URL = http:/$()/Umut-MacBook-Pro-2.local:8080
   DEVELOPMENT_TEAM = <your team id>
   ```
   - Write `http:/$()/` exactly: a plain `//` starts a comment in this file, and the app would then
     look for the engine on the phone itself.
   - Your team id is in Xcode → Settings → Accounts → your Apple ID → the team (10 characters).
   - If Xcode says the bundle id is taken, add `PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking.umut`.
   - The file is git-ignored; it never leaves your Mac. Do not set the team or the bundle id in
     Xcode's Signing screen: that edits the tracked project.
3. **Connect the iPhone.** Use a cable the first time. On the phone, turn on Developer Mode
   (Settings → Privacy & Security → Developer Mode) when iOS asks.
4. **Run.** Open `ios/ModelRanking.xcodeproj`, choose the iPhone as the destination and press Run. On
   the phone, trust your developer certificate (Settings → General → VPN & Device Management) if iOS
   asks.
5. **Allow local network.** On the first launch the app asks to find devices on your local network.
   Allow it: that is how it reaches the engine. If you tapped "Don't Allow", turn it on in Settings →
   Privacy & Security → Local Network → ModelRanking.
6. **Check.** Ask a question. If the app says the engine is not answering, the message names the
   address it tried: it should be your Mac's name.

**Keep in mind:**
- The phone must be on the same Wi-Fi as the Mac.
- An app signed with a free Apple ID stops opening after 7 days. Run it from Xcode again.
- **While it is on, the engine answers on every network the Mac joins,** a café's included, and your
  Mac's firewall is off. The data is public and nothing can be changed, but anyone on that network can
  read what the engine serves, and what the phone asks (the kind of task and the budget, never your
  question's text) crosses Wi-Fi unencrypted.
- **To close it:** `scripts/install_engine_service.sh --no-lan`. A plain reinstall keeps whichever mode
  it finds, so updating the engine after a merge does not close it, and does not open it.
- To keep other devices out while it is on, turn the firewall on (System Settings → Network →
  Firewall) and allow Python when macOS asks.
- **If the phone stops reaching the engine** after it worked, check the Mac's name (System Settings →
  General → Sharing → Local hostname). macOS can rename it; put the new name in step 2's file and run
  the app from Xcode again.
- The simulator build from `ios/app.sh` always talks to `127.0.0.1`, whatever step 2's file says.
