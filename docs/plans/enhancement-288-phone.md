# Enhancement #288 — the app works on the owner's iPhone

**Goal.** The owner installs from Xcode on their own iPhone in the morning (D-202 clause 3), and the
app shows rankings: it reaches the hosted engine, and it shows the last answer when it cannot.

**Scope in.**
- The engine address on a physical device with no `Engine.local.xcconfig` override: the hosted
  engine. Today that build points at loopback (`ios/Config/Engine.xcconfig:6`), and an invalid
  address falls back to loopback (`ios/ModelRanking/Engine/EngineClient.swift:173-179`).
- A kept last answer per surface (`/v1/recommendations` for the task and budget, and `/v1/categories`),
  in Caches, dated. When a fetch fails it is shown with an "as of <date>" line instead of the failure
  sentence (`ios/ModelRanking/ContentView.swift:1113-1127`).

**Scope out.** TestFlight, build numbers and deploys (D-202 clause 7). A bundled snapshot
(REQ-APP-001). The simulator's Debug default.

**Open decisions.** None left: D-202 clauses 4 and 5 resolve them.

**Phases.**
1. The address choice is a pure function in the Engine layer (device, simulator, override), with red
   tests first. The client uses it. Check: `swift test` covers all three cases.
2. The kept answer is a store beside `StandingsStore`, written on success and read on failure, with
   red tests first. Check: tests cover the store, the date, a surface mismatch and an expired entry.
3. The screen uses the kept answer and shows its date. Check: the app builds for a device
   (`xcodebuild ... -destination 'generic/platform=iOS'`) and runs in the simulator.
