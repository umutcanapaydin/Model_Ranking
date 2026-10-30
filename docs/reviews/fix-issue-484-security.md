---
record_type: review
id: fix-issue-484-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-29
---
# Security Review — fix-issue-484

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` printed `review-need: none` with the
signal `gate or control code changed: scripts/client_decl_gate.py`; the owner asked for this seat because the change
relaxes D-126's client controls)
**Independent:** yes. I wrote neither the red test, the ADR nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-29
**Release range:** a2650e0..79c513a (`78c0ef0` red tests, `8ae40f6` D-230 and its watchlist row, `79c513a` the code)
**Reviewed head:** 79c513a8dfc318ea234793a1b23688d9a09b9d21
**Risk tier:** MEDIUM (a privacy control relaxed by an owner ruling; the brief declares no HIGH paths, and no
auth/PII/payment/migration path is touched, so the senior-review trigger of permission-matrix §11 does not fire)

## Verdict
MINOR

The shipped door is sound: `SettingsDoor.showSettings()` takes no argument, its address is the system constant
`UIApplication.openSettingsURLString`, and no text the reader typed or the engine sent reaches it. The compiled gate's
exception is held to that file name and those five resolved declarations, and only while the pin matches; every probe
of the same call elsewhere, a second call in the door, a stale pin, a moved file, a twin file and a shadowed
initialiser was refused. `settings_door_problem` fails closed. What is weaker than D-230 says is the second gate: the
text gate's two exact expressions do not bind which URL `settings` holds (M1), so the whole of the protection against a
rebound door rests on one hex constant (`SETTINGS_DOOR_SHA256`), and D-230's mitigation clause overstates it (M2).

Worked in `/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/sec484`, a detached `git worktree` at 79c513a, own venv `.venv` installed from
`requirements/dev.lock` with `--require-hashes` (D-174), `advisor.db` copied in. Probes lived in
`/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/probe484` and ran against copies of `ios/ModelRanking` (and its `.xcodeproj`), never the tree; the
gate's mutants were applied to the review tree's `scripts/client_decl_gate.py` and restored by copy (`cmp` clean,
`git status` clean). Policy and this profile were read from `origin/main`.

## Findings

### BLOCKING
- none

### MINOR
- **M1** tests/unit/test_router_hints.py:776-777 — the text gate permits the door as two SEPARATE exact expressions, so
  it holds that `URL(string: UIApplication.openSettingsURLString)` and `UIApplication.shared.open(settings)` each occur
  once, not that the URL opened is the one made. Probe P9 (a copy of the client): keep both snippets, end
  `showSettings()` with `_ = settings`, and add in the same file
  `@MainActor static func relay(_ t: String) { guard let settings = Relay.address(t) else { return }; UIApplication.shared.open(settings) }`
  with `enum Relay { static func address(_ t: String) -> URL? { URL(string: "https://example.invalid/?q=" + t) } }`
  appended to `Engine/EngineClient.swift` (whose `URL(` is permitted file-wide, gap B19). Result:
  `text gate PASS` (`_assert_the_client_has_no_way_off_the_device`). The compiled gate refuses it only on the hash
  (`its bytes are not the ones D-230 pins`); probe P9b, the same change with `SETTINGS_DOOR_SHA256` re-pinned to the
  new bytes: `text gate PASS`, `compiled gate: 0 problem(s)`, and `test_settings_door_484.py` compares the file with
  that same constant, so it passes too. One hex constant is therefore the whole of the barrier between this file and
  opening an `https` address carrying the reader's words, and a re-pin is a gate edit that light-mode `review-need`
  routes to no reviewer (R1). Not exploitable as shipped, and the network route through `EngineClient.swift` (B19)
  already exists without any pin edit, so the marginal exposure is small: MINOR, latent, for a safety-class control
  that should fail closed. Remedy (cheap): permit the door as ONE exact expression, the guard and the open together,
  the way #276 pinned `FrontDoor.swift`'s guard and read —
  `("SettingsDoor.swift", "guard let settings = URL(string: UIApplication.openSettingsURLString) else { return }\n        UIApplication.shared.open(settings)")`
  — so a second `.open(` or a rebinding of `settings` is refused by the text gate on its own, in every lane, CI's
  included; and update `EXPRESSIONS` in `tests/unit/test_settings_door_484.py:20` to match.
- **M2** docs/decisions.md:6315-6316 and :6325-6326 — D-230 says the text gate "permits the file's two expressions
  exactly" and that "a change to `SettingsDoor.swift` ... fails `make client-decls` and the text gate". Measured: a
  change that keeps both expressions (probe P3, one byte; probe P9, a rebound `settings`) passes the text gate; what
  fails in the lanes with no Xcode is `tests/unit/test_settings_door_484.py:33`
  (`test_the_settings_door_is_one_file_pinned_whole`), a hash comparison against the compiled gate's own constant,
  which the ADR does not name. Clause 2 also says "the same declarations anywhere else stay refused, as before", which
  holds (P1, P7). Remedy: once M1 lands the text-gate sentence becomes true; until then, name the pytest pin as the
  CI lane's control and say the pin is one constant whose change is the reviewed edit. A new ADR is not needed for a
  wording fix of a `proposed` record made in this branch, but the record is the owner's to edit.
- **M3** scripts/client_decl_gate.py:3145-3146 and :618-619 — two load-bearing branches of the exception with no test
  that fails without them (mutation results under "Mutants" below): the door's line in `unseen_permissions` and the
  `OSError` branch of `settings_door_problem`, and nothing exercises `problems()` with the door at all (mutants B, C,
  D, E survive; only A, the exemption widened to every file, is killed, and by the fixture's pinned refusals rather
  than by a door test). The code is right today (probes P2-P6), and D and E are each covered by the other half of the
  logic, but a refactor that drops both halves, or the unseen line that would catch P6's shadowing if it ever
  type-checked, would pass every test. Remedy: pure-Python tests on a hand-built `found` dict (no Xcode needed, so
  they run in CI): the door's five declarations with the pin matching → no problem; with the pin stale → the pin
  problem AND the five refusals; the same five under `Elsewhere.swift` → refused; a `found` without them →
  `unseen_permissions` names each; `settings_door_problem` on an empty folder → a problem.
- **M4** ios/ModelRanking/Engine/FrontDoor.swift:227-228 — the comment above `OnDeviceGuide` still says "The screen
  draws no Settings button yet: opening one makes a URL outside EngineClient, which D-126's client-decls control
  refuses; the owner decides that exception." D-230 decided it. Doc drift in a file a privacy reviewer reads to learn
  what the client may open; reword to point at `SettingsDoor.swift` and D-230.

### PASS
- ios/ModelRanking/SettingsDoor.swift:8-11 — `showSettings()` has no parameter; the URL is
  `URL(string: UIApplication.openSettingsURLString)`, a read-only UIKit constant, and the open passes no options and no
  completion handler. ios/ModelRanking/ContentView.swift:801-805 calls it with no argument, under
  `if guide.opensSettings`, whose value is a literal per `OnDeviceState` in ios/ModelRanking/Engine/FrontDoor.swift
  (`opensSettings: true/false` at :265, :278, :289, :300), never engine data. No reader text or engine field can
  reach a URL or an open call in the shipped code (answer to question 1).
- Scope of the exception (question 2), each probe on a copy of the client, simulator Release configuration:
  - P1, the same two lines in a new `Elsewhere.swift`: text gate FAIL (`\bURL\s*\(`); compiled gate refuses
    `Foundation.URL.init(string:`, `URL.made`, `UIApplication.open`, `.openSettingsURLString`, `.shared` there.
  - P7, `extension SettingsDoor { static func leak(_ s: String) { ... UIApplication.shared.open(URL(string: s)!) } }`
    in another file: both gates refuse it in `Extend.swift`; the exemption keys on the file of the reference, not on
    the type.
  - P2, a second `URL(string: s)` + `open` inside `SettingsDoor.swift`, pin stale: text gate FAIL; compiled gate
    reports the pin mismatch and, because the exemption is dropped (`door is None` at :3420), refuses all five
    declarations as before D-230. P2b, the same with the pin updated: the compiled gate passes (its allow-list is by
    declaration, not by argument) but the text gate still fails on `URL(` — the dual control works for a second
    address made inside the door; it does not for one made elsewhere (M1).
  - P3, one byte changed (`open(settings) `): compiled gate refuses (pin mismatch, then the five declarations).
  - P4, the pinned bytes moved to `Engine/SettingsDoor.swift`: `cannot be read, so the door's exception (D-230) does
    not apply`, and the five declarations are refused.
  - P5, a second file named `SettingsDoor.swift` in `Engine/`: `filename "SettingsDoor.swift" used twice`, a type-check
    failure, which `main()` refuses (:3620). The basename key cannot be shared by two files.
  - P6, `extension URL { init?(string: String) }` in another file to change what the pinned bytes resolve to: the
    call becomes ambiguous and the client does not type-check, refused. Had it resolved to `main`, the door's line in
    `unseen_permissions` would report `Foundation.URL.init(string:` unseen.
- `settings_door_problem` fails closed (question 3): an unreadable or missing file returns a problem (:618-619), a
  different digest returns a problem (:620-623), and `problems()` both appends that problem (:3416-3417) and withholds
  the exemption (:3420), so either half alone still fails the gate (mutants D and E below). A door file absent from
  the client leaves all five declarations unseen (:3145-3146) and the text gate's two entries stale
  (test_router_hints.py:862), so the permission cannot outlive the file.
- No new dependency: the gate adds only `hashlib` (stdlib, already imported); no new Swift import (`SwiftUI` only).
  No secret, token or credential in the range (`git diff a2650e0..79c513a` grepped; the dispatcher's `make secrets`
  line: no leaks found). `ruff --select S` clean on the changed Python. No destructive operation in the three commits.
- Commits carry `GP-Agent: claude-code` and `GP-Task: issue-484` trailers; the red test precedes the fix.

## Gates passed
- [x] Secret scan green (`make secrets` on 79c513a: no leaks found, per the dispatcher)
- [x] `make deps` (pip-audit) green (dispatcher: No known vulnerabilities found)
- [x] `make slopsquat` green (no new import; part of `gate PASS` per the dispatcher)
- [x] Default-deny preserved for new external surfaces (the one new exit opens the system Settings page; every other
  file is refused as before, P1, P7)
- [x] Permission-matrix not violated (no matrix region touched; D-230 records the exception)
- [x] Prompt-injection hygiene (n/a: no untrusted content consumed by the change)
- [x] Auth/PII checks (n/a: no auth/PII/payment/migration path; the brief declares no HIGH paths)
- [x] SAST (`ruff --select S` on the changed Python; the client gate itself on 79c513a: `client-decls PASS: 23 client
  file(s) in 4 configuration(s)`, rerun here)

## Acceptance criteria evidence (the owner's scope of 2026-10-29, #484, D-230)
- The button shows when `OnDeviceGuide.opensSettings` is true → ios/ModelRanking/ContentView.swift:801-805;
  tests/unit/test_settings_door_484.py:23 (`test_the_guide_opens_settings_where_turning_it_on_is_the_remedy`)
- One new file makes the URL from `UIApplication.openSettingsURLString` and calls `UIApplication.shared.open` →
  ios/ModelRanking/SettingsDoor.swift:8-11; tests/unit/test_settings_door_484.py:50
- The compiled gate allows exactly `SETTINGS_DOOR_ALLOWED` in that file only, while its sha256 equals
  `SETTINGS_DOOR_SHA256` → scripts/client_decl_gate.py:605-624, :3415-3421, :3145-3146;
  tests/unit/test_settings_door_484.py:33, :42; probes P1-P7 above
- The text gate permits the two expressions in `EGRESS_EXACT` → tests/unit/test_router_hints.py:776-777;
  tests/unit/test_settings_door_484.py:50 (but see M1: the two expressions do not bind each other)

## Mutants (the cited tests: tests/unit/test_settings_door_484.py and tests/unit/test_client_decl_gate.py)
Each applied to scripts/client_decl_gate.py at 79c513a, run with `pytest -n 6 --no-cov`, restored by copy.

| id | mutant | result |
|---|---|---|
| A | :3420 `if name == SETTINGS_DOOR and door is None and ...` → `if door is None and ...` (exemption in every file) | killed: 11 failed, among them `test_375_a_pinned_refusal_removed_or_reworded_fails_the_pin` (test_client_decl_gate.py:1452) and `test_375_a_fixture_line_moved_by_an_insertion_keeps_the_pin` (:1432) |
| B | :3145-3146 the door's `unseen_permissions` line removed | survived: 276 passed |
| C | :619 an unreadable door returns `None` (fails open) | survived: 276 passed |
| D | :3420 `door is None and` removed (stale pin still exempts) | survived: 276 passed (the gate itself still fails: :3416-3417 report the pin) |
| E | :3416-3417 the pin problem not appended | survived: 276 passed (the gate itself still fails: :3420 withholds the exemption) |

The four new tests in tests/unit/test_settings_door_484.py do fail when what they cite is removed: the guard or the
button in ContentView.swift (`find` returns -1, :30), a changed byte (:38, :45-47), a third or missing `EGRESS_EXACT`
entry or an `EGRESS_PERMITTED` pattern for the file (:52-53). What they do not cite is `problems()` and
`unseen_permissions` (M3).

## Risks queued
- **R1** scripts/review_need.py (origin/main):251-253 with docs/project-brief.md:110 — in light mode a change to the
  client-decls tables, `SETTINGS_DOOR_SHA256` included, is reported as a signal and routed to no reviewer, and the
  brief declares no HIGH paths (.agents/rules/issues.md, "Two working modes": per change, light mode runs the
  Security-Reviewer only on declared HIGH paths and never the Code-Reviewer). This branch got a security seat only
  because the owner asked. A future re-pin of the door, which is the whole barrier M1 describes, would be read first
  at the release review, after it merged. For the owner: declare
  `ios/ModelRanking/SettingsDoor.swift` and `scripts/client_decl_gate.py` (and the egress tables in
  `tests/unit/test_router_hints.py`) as HIGH paths in the brief, or have `review_need.py` route a relaxed client
  control to `security`. An owner decision (the brief), not this branch's fix.
- **R2** scripts/client_decl_gate.py:3415 — `problems()` hashes `CLIENT / SettingsDoor.swift`, not the file the dump it
  is judging compiled. `main()` always dumps `CLIENT`, so the shipped gate is right; but probe P8 (a modified door
  compiled from a copy, `gate.CLIENT` left at the real tree) returned `compiled gate: 0 problem(s)`. A fixture that
  someday tests the door through `self_test()` would read the client's pin, not the fixture's bytes. Pass the
  compiled folder into `problems()` (or record the digest beside the dump).
- **R3** ios/ModelRanking/SettingsDoor.swift:3-4 and docs/decisions.md D-230 clause 1 — the door is described as "the
  system's own Settings page for this app, where Apple Intelligence is turned on", while
  ios/ModelRanking/Engine/FrontDoor.swift:226 says "iOS offers no public link to the Apple Intelligence page". The
  app's own Settings page is where `openSettingsURLString` lands; whether the reader finds the Apple Intelligence
  switch from there is a product question outside this seat (no security consequence), for the Code-Reviewer or the
  owner's device check.
- **R4** pre-existing, not this branch: the text gate does not see `init?(string:` (the `?` defeats
  `\binit\s*\(\s*string\s*:`) or `-> URL?` (probe P6 and P9 both passed it); the compiled gate held both. Recorded so
  the next text-gate review sees it.
