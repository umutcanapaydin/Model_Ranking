---
record_type: register
id: owner-iphone
status: ratified
process_version: v6.6
date: 2026-09-29
---
# Running the app on your iPhone (M18-W1, D-171)

The engine stays on your Mac. The phone reaches it over your home network, by opt-in. Six steps, once:

1. **Open the engine to your home network.** On the Mac, from the repository:
   `scripts/install_engine_service.sh --lan`
   It binds the engine to your network and allows only your Mac's own names
   (`Umut-MacBook-Pro-2.local` and its address). If macOS asks whether Python may accept incoming
   connections, allow it.
2. **Point the app at your Mac.** Create `ios/Config/Engine.local.xcconfig` with one line:
   `ENGINE_URL = http:/$()/Umut-MacBook-Pro-2.local:8080`
   The file is git-ignored; it never leaves your Mac.
3. **Sign the app with your Apple ID.** Open `ios/ModelRanking.xcodeproj` in Xcode. On the ModelRanking
   target, under Signing & Capabilities, pick your Personal Team. If Xcode rejects the bundle id, change
   it to something unique, such as `com.ilgar.modelranking.umut`.
4. **Connect the iPhone.** Use a cable the first time. On the phone, turn on Developer Mode
   (Settings → Privacy & Security → Developer Mode) when iOS asks.
5. **Run.** Choose the iPhone as the destination and press Run. On the phone, trust your developer
   certificate (Settings → General → VPN & Device Management) if iOS asks.
6. **Allow local network.** On the first launch the app asks to find devices on your local network.
   Allow it: that is how it reaches the engine.

**Keep in mind:**
- The phone must be on the same Wi-Fi as the Mac.
- An app signed with a free Apple ID stops opening after 7 days. Run it from Xcode again.
- The engine answers anyone on your home network: the data is public, and the Host check stops a
  browser page, not a person on your network (D-171).
- To close it again, run `scripts/install_engine_service.sh` without `--lan`.
