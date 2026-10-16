---
record_type: review
id: enhancement-issue-288-phone-security
status: draft
seat: independent
process_version: v7.1
date: 2026-10-16
---
# Security Review: enhancement #288, the app works on the owner's iPhone (draft PR #296)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`)
**Independent:** yes. I wrote none of this change's code, tests or records.
**Seat and method:** a fresh Security-Reviewer seat, Claude model family (Opus). Own worktree detached at
`1cb49b7` under a `mktemp -d` directory with its own venv (`make install`), per D-174; the author tree and
the owner's launchd service were not touched. Policy read from `main` (`main:docs/security-invariants.md`,
`main:docs/security-baseline.md`, `main:permission-matrix.md`). Diff read in full, then 7 mutants
fault-injected in place and 4 gate probes run, each file restored byte-identical (md5 checked).
**Date:** 2026-10-16
**Release range:** `d99d0e7..1cb49b7` (9 commits, `0effabb` through `1cb49b7`; the branch's own range)
**Reviewed head:** 1cb49b7556f6896a614a299521e568c3aac9f221
**Risk tier:** MEDIUM. The brief declares no HIGH paths; the change adds a parse of a file on the device
(`JSONDecoder` over `answers.json`) inside a privacy sink (`StandingsStore.swift`, INV-62, INV-66), and
changes where a device build sends its requests.

## Verdict

PASS WITH FINDINGS: BLOCKING 0 · MAJOR 1 · MINOR 3 · NIT 2.

Nothing typed is stored today, the address a phone reaches is a compile-time HTTPS constant or the build's
own setting, and the kept answer cannot be shown for another surface or budget, past a week, or undated.
The MAJOR is a control hole, not a present leak: the new write door into the privacy sink takes free text
and no gate holds what reaches it (probe P1 below). It should be closed before merge, or filed and the
owner told; closing it needs a gate edit, which is the owner's (AGENTS.md section 3, Escalate NOW).

## Findings

### BLOCKING
- none

### MAJOR
- **MJ1** `ios/ModelRanking/Engine/StandingsStore.swift:189` and `:195`. `keep(route:task:budget:payload:)`
  and its dated form `keep(...at:)` take any `String` and any `Data` from any file in the module and write
  them to `Caches/Standings/answers.json`. Neither is in `PROVENANCE` (`scripts/client_decl_gate.py:285`),
  and no `REQUEST_ARGUMENTS`-style rule pins their arguments. INV-67 says the typed question is kept only
  in the gap register (protected while locked, excluded from backup, bounded in bytes); before this change
  the screen had no door into `StandingsStore` that took text (`save` takes only a `FetchedStandings`,
  whose initialiser `PROVENANCE` holds). The dated form is also the 64-bit screen-chosen-date channel #170
  closed for the standings; the code comment at `:187` claims #170's rule but nothing enforces it.
  **Failure scenario (demonstrated, probe P1):** adding
  `StandingsStore.onDevice.keep(route: KeptAnswers.recommendationsRoute, task: asked, budget: budget, payload: Data())`
  to `ContentView.load()` writes the reader's typed question to disk. `make client-decls` stayed PASS in all
  four configurations, the 328 router/contract/address/client-decl text pins passed, and the whole Python
  suite passed (3133 passed). A later change, an agent's or a merge's, can therefore store typed text, or
  any value at all, without a gate failing (REQ-RTR-004, INV-67).
  **Remedy:** make the sink take only what the engine sent: `keep(_ recommendation: Recommendation)` and
  `keep(_ categories: [Category])`, deriving the key from the engine's own `query` echo, encoding inside
  `StandingsStore.swift`, dated only by the store's clock; then add `StandingsStore.keep(` dated and raw
  forms to `PROVENANCE` (only `StandingsStore.swift`), with a fixture case the gate refuses. The gate edit
  is the owner's to approve. Until then, the PR body's assumption 6 should say this door is unguarded.

### MINOR
- **M1** `docs/security-invariants.md` INV-73 (row at line 139) and `ios/ModelRanking/Engine/EngineClient.swift:221`.
  INV-73 still says the address "is loopback unless an http(s) URL with a host is given". On a device it is
  now the hosted engine in that case. The behaviour is safe (a fixed HTTPS constant, held equal to the
  Release line by `tests/unit/test_engine_address.py`; probe P4), but the registry describes a property the
  code no longer has and does not cite `DeviceAddressTests`. **Remedy:** amend INV-73 (device: hosted unless
  a non-loopback address is given; simulator: as built) and cite the six `DeviceAddressTests` and the two new
  Python pins.
- **M2** `ios/ModelRanking/Engine/StandingsStore.swift:83` (read) and `:180` (decode). `answers.json` is read
  whole with `Data(contentsOf:)` and decoded with no byte ceiling, where INV-74 bounds the standings payload
  at 4 MiB and INV-71 bounds every network read. The decode fails closed (any corrupt entry gives `[]`, and
  the next `keep` rewrites the file; `testAnUnreadableFileIsNothingKept`), but a file grown or planted large
  (only by something with write access to the app container) is read into memory on every fresh answer,
  because `keep` reads before it writes. The write side is bounded only indirectly (32 entries, each a
  re-encoded answer of at most 1 MiB on the wire, base64 in the file). **Remedy:** refuse a file over a
  stated ceiling (for example `maxKeptAnswers` times the recommendations ceiling times 4/3) before decoding,
  with a test like `testAPayloadOverTheCeilingIsNeverAccepted`.
- **M3** `ios/ModelRanking/Engine/StandingsStore.swift:195` and `:99`. Retention and protection: an entry
  past `KeptAnswers.maxAge` is never shown but stays on disk until 32 newer entries push it out, so the file
  is a dated history of the surfaces the reader asked; it is written `.atomic` only, under the default
  protection class, where the gap register uses `.completeFileProtection` (`FrontDoor.swift:308`). Caches is
  not backed up. Low sensitivity (the surface already leaves the phone in the request), hence MINOR.
  **Remedy:** drop entries past `maxAge` inside `keep`; consider a protection class for the answers file
  (the write expression is text-pinned, so that is a reviewed gate change).

### NIT
- **N1** `ios/ModelRanking/Engine/StandingsStore.swift` `KeptAnswer`: a kept answer is not keyed by the engine
  it came from. After the owner switches `Engine.local.xcconfig` between the Mac and the hosted engine, an
  answer from one can stand in, dated, for the other. Remedy: key by `baseURL.host`, or clear on change.
- **N2** `ios/ModelRanking/ContentView.swift:1123`: the kept surfaces list is used undated, and it is now part
  of what "the engine lists" means for INV-69 and INV-70 (`select`'s guard) for up to a week. It is still a
  list the engine sent, so no surface is invented; say so in INV-70's text.

### PASS
- **The address cannot be chosen by an attacker.** `EngineClient.address(configured:onDevice:)`
  (`EngineClient.swift:221`) only ever returns the build's own `EngineURL` (unchanged validation,
  `engineURL(from:)`) or the compile-time constant `hosted` (`:208`, `https://model-ranking.fly.dev`). The
  `EngineOnDevice` plist value can only switch loopback to that constant. The Info plist is in the signed
  bundle and was already the source of `EngineURL`. A screen cannot pick the flag: probe P2
  (`EngineClient(onDevice: false)` in `ContentView`) is refused by `make client-decls` in all four
  configurations (`ENGINE_CLIENT_REACHABLE`, #244).
- **Release stays HTTPS.** `ENGINE_URL[config=Release]` is set after `#include? "Engine.local.xcconfig"`
  (`ios/Config/Engine.xcconfig:18-23`), so a Release build is given the hosted address and `address` keeps it.
  Probe P4 (`hosted` set to `http://attacker.example`) fails
  `test_the_hosted_engine_a_phone_falls_back_to_is_the_release_address`.
- **An invalid address fails safe.** No host, an unparseable value, or any loopback on a device goes to the
  HTTPS constant, never to a value derived from the bad input; `127.`-prefixed names that are not addresses
  also go there, which is the safe direction. On the simulator the address is as built (INV-73 simulator
  pin unchanged).
- **The kept answer is the engine's, and only for its own key.** It is re-encoded from the decoded types,
  so an undecoded field is never kept (`testAKeptAnswerIsWhatTheAppDecoded`); shown only for the same route,
  surface and budget and only when its own `query` echo agrees (`KeptAnswers.swift:246-255`); only after
  `.unreachable`, `.timedOut` or `.offline`, never after a refusal, an undecodable answer or a cleartext
  refusal (`:224-231`); only younger than a week and not dated in the future (`:276-278`); always under the
  dated line (`ContentView.swift:201-207`), cleared on every fresh answer and every failure.
- **INV-66 as written holds.** The answers are in `answers.json`, never in `standings.json`
  (`testKeepingAnAnswerNeverTouchesTheStandingsFile`); both files go through the one `isFileURL`-guarded read
  and write (Security S1; `testAStorePointedAnywhereButAFileKeepsNothing`).
- **REQ-APP-001.** No JSON in `ios/ModelRanking/` outside the asset catalog; the project file is unchanged in
  the range; the test payloads live in `ios/EngineTests/` only.
- **Fault injection: 7 of 7 mutants killed, each restored byte-identical (md5).** M1 future-dated answer
  allowed (`KeptAnswers.swift` md5 `c040f6a5…`): `testAKeptAnswerOlderThanItsLimitIsNotShown` fails. M2 the
  query-echo check removed: `testAnAnswerKeptUnderOneSurfaceButSentForAnotherIsNotShown` fails. M3
  `.insecureTransport` stands in: 2 failures. M4 `127.` dropped from `isLoopback` (`EngineClient.swift` md5
  `794c91f2…`): 8 failures. M5 `onDevice` ignored: `testTheSimulatorKeepsTheAddressItsBuildWasGiven` fails.
  M6 answers written to `standings.json` (`StandingsStore.swift` md5 `0b9dfe61…`): 4 failures. M7 no
  replacement of an older answer: 1 failure. Probes on `ContentView.swift` (md5 `b6f373f4…`): P1 survives
  every gate (MJ1); P2 refused.

## Gates passed
- [x] `make check` on `1cb49b7`, own worktree: exit 0. pytest 3135 passed, 27 skipped; coverage-floor PASS;
  check_records PASS; self-test PASS; wave-check-all PASS; conformance PASS (26); swift-test PASS (661, each
  in the manifest; SlowTierTests 7 of 7); client-decls PASS (22 files, 4 configurations). A first run failed
  one test only because this seat had made its copied `advisor.db` read-only; with the copy writable it passed.
- [x] `make secrets` (gitleaks): no leaks found, 1212 tracked files.
- [x] `make deps` (pip-audit, strict, four locks): no known vulnerabilities.
- [x] `make slopsquat`: PASS, 20 declared dependencies, 0 suspect. No new Python dependency (only `re`,
  `plistlib`); Swift imports only Foundation.
- [x] Default-deny preserved for new external surfaces: no new route; the only new egress destination is the
  owner's own HTTPS engine, asked only for the surface and budget (INV-64 unchanged, held by the gate).
- [x] Permission matrix not violated: no destructive operation, no CI, hook or gate file in the range.
- [x] Prompt-injection hygiene: no fetched text is executed or followed; the kept file is parsed by the same
  `Decodable` types as the network answer.
- [ ] Auth/PII checks: not applicable (no auth, payment or migration path; no PII beyond the surface asked).
- [x] SAST: the change is Swift and Python tests; no Python product code changed, so bandit has nothing new.

## The implementer's assumptions, graded
1. **Answers in `answers.json` beside the standings, under `StandingsStore`:** holds for INV-66 as written
   (the standings file and the boards request are untouched; M6 is killed). It does not hold as a privacy-sink
   argument, because the new door is unguarded: MJ1.
2. **Device detection by a build setting in the plist:** holds. The flag selects between the build's address
   and a constant; Release is pinned after the local include; the screen cannot pick the flag (P2).
3. **Any loopback on a device means no override:** holds and fails safe to HTTPS; the registry text lags (M1).
4. **A week, only when unreachable, at most 32:** holds (M1, M3, M7 killed); retention and protection, M3.
5. **The day in the device's time zone:** display only; no security effect.
6. **`keep(...)` not under `PROVENANCE`:** does not hold. P1 shows typed text reaching the device's disk with
   every gate green: MJ1.
7. **`advisor.db` copied read-only into the worktree:** gitignored, not in the range; no effect.

## Acceptance criteria evidence
- REQ-APP-001 (no fixture data in the app) → `ios/ModelRanking/Engine/KeptAnswers.swift:1-8` (no payload);
  no `*.json` under `ios/ModelRanking/` outside `Assets.xcassets`.
- REQ-RTR-004 / INV-64 (nothing typed reaches a request) → `scripts/client_decl_gate.py:336-347`, client-decls
  PASS; the kept-answer keys are `ContentView.task` and `ContentView.budget` (`ContentView.swift:1134-1136`).
  Storage of typed text is not held by any gate: MJ1.
- INV-66 → `ios/EngineTests/KeptAnswerTests.swift::testKeepingAnAnswerNeverTouchesTheStandingsFile` (M6 killed).
- D-202 clause 4 → `ios/EngineTests/EngineClientTests.swift::DeviceAddressTests` (M4, M5 killed);
  `tests/unit/test_engine_address.py::test_the_hosted_engine_a_phone_falls_back_to_is_the_release_address` (P4).
- D-202 clause 5 → `ios/EngineTests/KeptAnswerTests.swift` (14), `KeptAnswerScreenTests` (2) (M1, M2, M3, M7 killed);
  `tests/unit/test_engine_address.py::test_the_screen_shows_the_kept_answer_and_its_day_when_the_engine_cannot_be_reached`.

## Risks queued
- **R1** MJ1's remedy is a gate edit (`PROVENANCE`), which is the owner's; if it is not made in this PR, it is
  filed as an issue and the PR body's assumption 6 names the open door.
- **R2** The hosted engine is now reached by every Debug device build too, so its availability is what the
  owner's phone shows; nothing here deploys it (D-202 clause 7).
