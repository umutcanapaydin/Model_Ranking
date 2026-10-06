---
record_type: register
id: owner-iphone
status: ratified
process_version: v6.6
date: 2026-09-29
---
# Running the app on your iPhone (M18-W1, D-171)

The engine stays on your Mac. The phone reaches it over the network the Mac is on, by opt-in. Do these
once, **after the M18-W1 pull request is merged**.

0. **Update your checkout.** In the repository: `git checkout main && git pull`. The installer you run
   and the Xcode project you build are your checkout's; before the pull, the installer refuses `--lan`
   and nothing reads step 2's file.
1. **Open the engine to the network.** On the Mac, from the repository:
   `scripts/install_engine_service.sh --lan`
   It binds the engine to every network the Mac is on, and answers only to your Mac's own names
   (its local hostname, `my-mac.local` here, and its address). It prints `home network: on`.
2. **Point the app at your Mac, and sign it.** Create `ios/Config/Engine.local.xcconfig`, with your
   Mac's own name (System Settings → General → Sharing → Local hostname) for `My-Mac.local`:
   ```
   ENGINE_URL = http:/$()/My-Mac.local:8080
   DEVELOPMENT_TEAM = <your team id>
   ```
   - Write `http:/$()/` exactly: a plain `//` starts a comment in this file, and the app would then
     look for the engine on the phone itself.
   - Your team id is the `OU=` value this prints (10 characters):
     `security find-certificate -c "Apple Development" -p | openssl x509 -noout -subject`
   - If Xcode says the bundle id is taken, add `PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking.umut`.
   - The file is git-ignored; it never leaves your Mac. Do not set the team or the bundle id in
     Xcode's Signing screen: that edits the tracked project.
   - Xcode must know your Apple ID: Xcode → Settings → Accounts. Add it with `+` if it is not listed.
3. **Connect the iPhone.** Use a cable the first time. On the phone, turn on Developer Mode
   (Settings → Privacy & Security → Developer Mode) when iOS asks.
4. **Run.** Open `ios/ModelRanking.xcodeproj`, choose the iPhone as the destination and press Run. On
   the phone, trust your developer certificate (Settings → General → VPN & Device Management) if iOS
   asks.
5. **Allow local network.** On the first launch the app asks to find devices on your local network.
   Allow it: that is how it reaches the engine. If you tapped "Don't Allow", turn it on in Settings →
   Privacy & Security → Local Network → ModelRanking.
6. **Check.** Ask a question. If the app cannot reach the engine, the line under the error shows the
   engine address it asked.
   - It shows `127.0.0.1`: the app did not read step 2's file. Check the `http:/$()/` spelling, then
     run again from Xcode.
   - It shows your Mac's name: check that the Mac is awake, on the same Wi-Fi, that step 1 printed
     `home network: on`, and that the local-network switch is on (step 5).
   - It says the device has no network connection while Wi-Fi works: the local-network switch is off
     (step 5).

**Keep in mind:**
- The phone must be on the same Wi-Fi as the Mac.
- An app signed with a free Apple ID stops opening after 7 days. Run it from Xcode again.
- **While it is on, the engine answers on every network the Mac joins,** a café's included, and your
  Mac's firewall is off. The data is public and nothing can be changed, but anyone on that network can
  read what the engine serves, and what the phone asks (the kind of task and the budget, never your
  question's text) crosses Wi-Fi unencrypted.
- **To close it:** `scripts/install_engine_service.sh --no-lan`. A plain reinstall keeps whichever mode
  it finds, so updating the engine after a merge does not close it, and does not open it.
- The Mac's firewall cannot let the phone in and keep others out: it allows or blocks an app, not a
  device. Closing it (`--no-lan`) is the only way to shut others out.
- **If the phone stops reaching the engine** after it worked, check the Mac's name (System Settings →
  General → Sharing → Local hostname). macOS can rename it. Then run step 1 again, so the engine
  answers to the new name, put the new name in step 2's file, and run the app from Xcode again.
- The simulator build from `ios/app.sh` always talks to `127.0.0.1`, whatever step 2's file says.
