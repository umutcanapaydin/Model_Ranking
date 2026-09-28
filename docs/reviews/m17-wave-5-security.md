---
record_type: review
id: m17-wave-5-security
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-28
---

# M17-W5 security review: the question selects its boards, and the combined list on the screen (#64, D-168)

**Independent:** yes. I wrote none of the code under review, and I am neither of the wave's
Code-Reviewers nor its Tester. I changed no repository file except this one, and I made no git
state change. Every mutant was restored in place and checked with sha256. Temporary test files were
copied into `ios/EngineTests/` for one run each and deleted, and `git status` was clean after each.
Probe scripts live in the session scratchpad, outside the worktree. `PYTHONDONTWRITEBYTECODE=1` was
set, and no `.pyc` file was written or changed. I used no network. No probe called `build()`, and
`RUN_CONTRACT_TESTS` was not set. No probe of mine called the on-device model.

## Scope

Range `c02fe0d..96214aa` on `wave/m17-w5`: 24 commits, one of them the merge of `main`
(`9979324`), whose content is already on the base. Risk tier HIGH
(`docs/plans/m17-wave-5-plan.md:11`). This is the `/close-wave` pass on a HIGH wave's slice
(checklist row 4). The release review (Stage 5.1) still runs.

- **The on-device model's output selects boards.**
  - The schema: `ModelRouter.schema(for:)` (`ios/ModelRanking/Engine/Router.swift:421-435`).
  - The call: `route` (`:436-476`).
  - The boundary: `ModelOutputBoundary.refinements` / `.outcome` (`:518-557`).
  - The table: `Refinements.swift`.
- **The screen.**
  - `AnswerPlan.swift`.
  - The `place` in `Combine.swift:84-90`.
  - The chip names and sentences in `Language.swift:514-626`.
  - In `ContentView.swift`: the combined list (`:143-160`, `:253-343`), the reset on each question
    (`:717`), the standings refresh (`:770-787`) and `CombinedDetail` (`:1219-1266`).
- **The server:** `primary_board` on `/v1/categories` (`src/app/adapter/main.py:1346`).
- **The controls:**
  - `tests/unit/test_router_hints.py:120-204`;
  - `tests/unit/test_refinements.py`;
  - `tests/unit/test_uncertainty_contract.py:316-317`.
- **The probe harness and question sets** under `scripts/router_probe/`, and the two
  `.language-allow` entries.

## Verdict

PASS-WITH-MINORS. As shipped, nothing a reader types can make the on-device model's output reach
anything but a declared surface or a declared refinement. Nothing derived from the question beyond
the surface id, which D-126 has sent since M13, reaches a request. The refinements, the chips and the
reader's removals stay on the device. `primary_board` exposes only public board ids. Nothing in
the slice is exploitable in its current scope.

Three minors, none exploitable today:

- **S1:** the D-126 gates pin the schema's two closed sets but not that the schema holds nothing
  else. They also do not pin what the model tier may put in `alternatives`. A two-edit mutant in
  `Router.swift` shows the model's free text on screen, and a tap sends it to the engine. Every gate
  I ran against it passed.
- **S2:** `combine` is quadratic. W5 calls it from the view's body, so a hostile standings
  payload under the 4 MiB cap freezes the screen for about 6 s per keystroke.
- **S3:** D-160 clause 1, as D-168 amends it, says no part of the intent leaves the device. The
  surface, which is part of that intent, is still sent as `task`. The records should say so.

S4 and S5 are nits.

## Findings

**S1: MINOR. The D-126 gates hold the schema's closed sets by presence, not closure, and nothing
holds the model tier's `alternatives`. A two-edit mutant in `Router.swift` puts the on-device model's
free text on the screen, and one tap sends it to the engine as `task=`. Every gate I ran against it
passed.**
Exploitable in the current scope: **no.** It needs a code change. The shipped schema is closed (see
"Checked and clean").

- **The mutant.** Two edits in `Router.swift`, nothing else:
  1. In `schema(for:)`, after the refinement fields (`:426-431`):
     ```swift
     + [DynamicGenerationSchema.Property(name: "note", description: "The question, word for word",
                                         schema: DynamicGenerationSchema(type: String.self))]
     ```
  2. In `route`, the outcome (`:473-475`) became a `var`, followed by
     `outcome?.alternatives = [(try? content.value(String.self, forProperty: "note")) ?? ""]`.
- **The results:**
  - `test_router_hints.py`, `test_ios_client_contract.py` and `test_refinements.py`: **44 passed**.
  - `swift test --filter RefinementBoundaryTests`: **13 passed**. This includes
    `testTheModelsSchemaBuildsForTheServedSurfaces`, which built the widened schema without
    complaint.
  - `make client-decls`: **PASS**, 15 client files in 4 configurations.
  - I did not run `RouterBoundaryTests` against the mutant, because it calls the model. It asserts
    only that `categoryID` is served (`ios/EngineTests/RouterBoundaryTests.swift:106-117`), so it
    would not catch the mutant either.
  - `Router.swift` was restored, and its sha256 matched.
- **Where the text goes** (read, and type-checked by `client-decls`):
  - `ContentView.swift:425-434` shows each alternative as a button titled `surfaceTitle(id)`. That
    falls back to the id itself (`:519-521`).
  - A tap calls `select(id)` (`:729-735`), which sets `task = id` and loads.
  - `EngineClient.swift:178` sends `URLQueryItem(name: "task", value: task)`.
  - The model can copy the question into a free field, so this carries the question's words off the
    device (D-160 clause 1, REQ-RTR-004).
  - `test_nothing_typed_by_the_reader_reaches_the_engine` accepts `select(id)` and `task = id` by
    design (`test_router_hints.py:253-260`, `:234-245`).
- **Why the pins miss it.**
  - `test_router_hints.py:132` and `:139` assert that the surface field and each refinement field
    are `anyOf` the right sets. Neither asserts that the schema has no other field.
  - `:169-204` pins `RoutingOutcome`'s field names and the types of `alternatives` and
    `refinements`, but not what the model tier may put in `alternatives`.
  - `:166` bans assigning `.refinements` after an outcome is built, not `.alternatives`.
- **What is and is not new.**
  - The `alternatives` sink is older than this wave (M13-W3).
  - What W5 adds is the object schema: a free field is now one more array element, where before it
    meant replacing the single-string schema that `:132` held.
  - This is not #60's class. #60 is about spellings and an appended `.filter`. Here every pin
    matches correctly, and the schema still holds more than they check.
- **Fix, cheap:**
  1. A Swift test that encodes `ModelRouter.schema(for:)` with `JSONEncoder` and asserts:
     - `properties` is exactly `surface` plus `RefinementKind`'s raw values;
     - `additionalProperties` is `false`;
     - every leaf is an `enum` of declared values.

     I checked that `GenerationSchema` encodes to JSON Schema without the model, wherever
     FoundationModels exists, the same condition as the schema-builds test. This pin is on the
     declaration, not the spelling, so it would also kill #60's `.filter` mutant.
  2. A boundary test that a model-tier outcome carries `alternatives == []`.
  3. `select(_:)` refuses an id that `categories` does not list: one `guard`, as defence in depth
     for D-160 clause 1.

  File (1) and (2) as an issue if they are not fixed in this wave.

**S2: MINOR. A hostile standings payload under the 4 MiB cap freezes the screen: `combine` is
quadratic per chosen board, and W5 runs it inside the view's body, which SwiftUI re-evaluates on
every keystroke.**
Exploitable in the current scope: **no.**
- Only the configured engine can supply standings. That is `http://127.0.0.1:8080` by default
  (`EngineClient.swift:144`), and a remote host sits behind ATS and `SameHostOnly`.
- The served artifact's largest board ranks 189 models.

This is the O(n²) half of W4's S7. W4 called it unreachable because nothing called `combine`, and
W5 gives it a caller on the main thread.

- **Evidence.**
  - `Combine.swift:72`: `shared.filter { $0.position < standing.position }.count` runs inside the
    loop over `shared`.
  - `ContentView.swift:145-149` calls `answerPlan` in the body. The body reads `question` (`:379`),
    so every keystroke recomputes it.
  - The `.restorable` path calls `combine` again (`AnswerPlan.swift:101`), so removing the chip does
    not escape the cost.
  - The list renders every entry in a non-lazy `VStack` (`ContentView.swift:261-267`,
    `CombinedDetail` `:1246`).
  - The stored copy serves the payload for up to a day (`StandingsStore.swift:79-82`).
- **Measured.** A temporary test decoded each payload through `FetchedStandings(payload:)`, then
  timed one `answerPlan` call. The question was "assistant" plus the French refinement, and every
  model sat on both boards.

  | shared models | payload bytes | debug build | release build (`-c release`) |
  |---:|---:|---:|---:|
  | 1,000 | 139,022 | 0.17 s | 0.010 s |
  | 2,000 | 282,134 | 0.66 s | 0.035 s |
  | 4,000 | 570,134 | 2.57 s | 0.127 s |
  | 8,000 | 1,146,134 | 9.80 s | 0.497 s |
  | 28,905 (the most that fits the cap) | 4,194,264 | not run | **6.42 s** |

  - The machine is this Mac; a phone is slower.
  - A payload that omits the models still pays for both loops, because `combine` throws
    `unknownModel` only after them, and the screen then falls back to the cards. With 28,905 models
    at one equal position, it measured 0.74 s.
  - The engine's own ceiling is 25,000 standings rows (`main.py:220`). Two chosen boards of 12,500
    each fit inside it, and by the n² fit that costs about 1.2 s per keystroke in release on this Mac.
  - The real artifact holds 63 boards, 7,135 rows and 557,078 bytes. That costs well under a
    millisecond.
- **Fix:**
  - In `Combine.swift:66-78`, sort each board's shared rows by position once and assign competition
    ranks in one pass. That is O(n log n), stays inside the one file allowed position arithmetic, and
    the property test holds the rule.
  - Compute the plan when `routing`, `standings`, `removedRefinements` or `categories` change, and
    keep it in state, instead of in `body`.
  - Optionally, bound the rows per board in `FetchedStandings.init`, next to the byte cap.

**S3: MINOR (records, privacy). The router's surface, derived from the question, still leaves the
device as the `task` of `/v1/recommendations`. D-160 clause 1 says "not an intent", and D-168
redefines the intent as "surface plus refinement". The records now state a stronger privacy
boundary than the code keeps.**
Exploitable in the current scope: **no.** The surface is one of 14 public ids, and D-126 and
REQ-RTR-004 have sent it since M13. W5 widens nothing: the refinements and removals stay on the
device.

- **Evidence:**
  - D-160 clause 1 (`docs/decisions.md:2783-2785`): "Nothing derived from the question leaves the
    device, not the text and not an intent."
  - D-168 "amends D-160's 'intent' wording" (`:3154`; plan `:121`).
  - The M17 plan's shared contract says "Nothing typed, and nothing derived from it, leaves the
    device", beside "D-126 untouched" (`docs/plans/m17-plan.md:97`).
  - The code:
    - `ContentView.swift:711-712` sets `task = outcome.categoryID` and loads;
    - `EngineClient.swift:174-181` puts `task` in the query string;
    - the day's first `/v1/boards` fetch can follow it (`ContentView.swift:772`).
- **Why it matters.** The code review (`docs/reviews/m17-wave-5-review.md:295`) and this wave's
  plan (`:22-23`) cite clause 1 as met, which is true only of what W5 added. A later seat that trusts the clause could remove the one sanctioned exception's
  pins as redundant, or build on a guarantee that does not exist.
- **Fix, a record only:** a D-168 note, ruled by the owner, saying:
  - clause 1 covers the typed text, the refinements and the removals;
  - the surface id is still sent as `task`, as D-126 allows.

  If the owner wants clause 1 literal instead, the cards themselves must come from the kept
  standings. That is a design change for a later milestone.

**S4: NIT. The effort notice and the list disagree on a board that lists a model twice.**
- `combine` counts a model's first row only (`Combine.swift:67-69`, W4 S7's fix).
- `mixedEfforts` reads every row of a listed model (`AnswerPlan.swift:62`).
- Probe: model `a` was listed twice on the French board, at `high` and at `low`. The list counted
  its `high` row (positions `[1, 1]`), and the notice named `["high", "low"]`.

Only a malformed payload does this; the engine's `GROUP BY` makes (board, model) unique. Fix: keep
each model's first row in `mixedEfforts` as `combine` does.

**S5: NIT. The probe harness traps on a malformed question set.**
`scripts/router_probe/RefinementProbe.swift:37` reads `$0[0]`, so an inner array that is empty stops
the test process with a crash report instead of failing. The committed sets are well-formed. Use
`$0.first`, and fail when a row has no question.

## Checked and clean

- **Prompt injection, as shipped.**
  - **The schema.** I encoded `ModelRouter.schema(for: ["assistant", "coding"])` with
    `JSONEncoder`, and no model ran. The schema carries `"additionalProperties": false` and
    `"required": ["surface", "language", "domain"]`. Every property is `anyOf` single-value string
    `enum`s: the served ids plus `__none__`, the 8 languages plus `none`, and the 8 domains plus
    `none`.
  - **The boundary** (`Router.swift:536-557`):
    - The surface must be in `known` (`:554`), and a decline carries no refinement.
    - Each refinement is looked up by equality in `Refinements.allowed(for:)`, and the *table's*
      entry is returned (`:538-540`). So no string the model generated is kept: only which declared
      entry it named.
    - `Refinements.boards` checks the surface again (`Refinements.swift:106`).
    - A value that cannot be read, or a schema that cannot be built, drops to the next tier or to no
      refinement (`:441`, `:470-472`). Both fail closed.
  - **The rest of the screen.**
    - `refinementName`'s fallback returns `refinement.value` (`Language.swift:538-541`), which is
      only ever a table value.
    - The echo (`FrontDoor.swift:68-76`) is unchanged. It shows the reader's own words and the
      surface title in a verbatim `Text`, and no refinement.
    - Every new `Text` that shows served or table text takes a `String`, which SwiftUI shows
      verbatim, so nothing is read as markdown. The one literal, `Text("\(entry.place)")`,
      interpolates an `Int`.
    - The attribution sentence is not a link.
  - A reader can steer which *declared* refinement is chosen. That changes only their own screen,
    and the chip shows it and removes it.
- **D-160 clause 1 for what W5 adds.**
  - **The fetch.** `client.boards()` takes no argument. Its request carries no query and no header
    of its own, as W4 pinned, and `EngineClient.swift` is unchanged in this range.
  - **When it fires.** `refreshStandings` fires after any `load()` (`ContentView.swift:772`),
    whatever refinements were chosen, and the day's first one usually fires at launch (`:113`).
  - **The chips and removals.** A chip only edits `@State removedRefinements` (`:320-325`). It is
    reset on each question (`:717`), never stored, and never passed to `client`.
  - **What is stored.** `StandingsStore.save` writes only the engine's payload and the time.
  - **Logs.** There is no log, `print` or `os_log` in the client. The text gate and `client-decls`
    refuse them, and both pass on HEAD.
- **The D-126 gates reach the new files.**
  - The text gate reads every file under `ios/ModelRanking` (`test_router_hints.py:429`).
  - `client-decls` type-checks 15 files; W4 had 13, so `AnswerPlan.swift` and `Refinements.swift`
    are in.
  - The source pin that only `ModelOutputBoundary` builds an outcome with refinements holds.
  - The check that no file but the table constructs a `Refinement` matches the spelling
    `Refinement(`. A spelling around it is #60's class, and I do not raise it again.
- **Standings as an input, beyond S2 and S4.** A temporary test:
  - Duplicate board ids: the first wins, and the chosen ids are de-duplicated, so every
    `ForEach(id:)` key is unique.
  - Duplicate model ids: the first wins (`Combine.swift:57`).
  - An empty primary id gives the cards.
  - Removing every refinement gives `.restorable`.
  - `boardTitle` returned ` · French` for a refinement board whose benchmark is `   (x)`. A
    benchmark of `(` alone splits into nothing and falls back to itself (`AnswerPlan.swift:50-51`).
    Neither crashes.
  - An empty `observed_at` reads as `readOn("")`.
  - `priceTag` refuses a non-finite or non-positive price (`Scores.swift:77`), and JSON cannot carry
    NaN.
  - The engine already names every board and model on screen, so a hostile benchmark or effort
    string adds no new trust.
- **`primary_board`.**
  - Probe through `TestClient` on a seeded database: the 14 values are the static `primary_source`
    constants of `categories.py` (`arena`, `swebench`, `epoch_eci`, ...). These are the same public
    ids `/v1/boards` serves. There is no path, no row id and no host.
  - A query string (`?primary_board=x&task=../../etc`) returned byte-identical bodies.
  - The served key set is pinned exactly (`test_uncertainty_contract.py:313-318`).
  - `ruff --select S` is clean on `main.py`.
- **The instructions change.** Medical and legal questions are no longer declined. A side effect is
  that the model tier no longer writes them to the on-device gap register, which records only
  unmeasured outcomes of the model and wording tiers (`FrontDoor.swift:332-334`). So less sensitive typed text is kept. The
  register's code and file protection are unchanged.
- **The question sets.**
  - `refinement_questions.json` (45 rows) and `refinement_heldout_questions.json` (40 rows) are
    synthetic questions.
  - I read both in full. They hold no names, addresses, emails, phone numbers or credentials, only
    public place names.
  - gitleaks finds nothing.
- **The `.language-allow` entries are a justified exemption, not a suppression.**
  - Each names one file with a written reason.
  - The files are data, and their Turkish questions are the measurement's evidence. JSON has no
    inline-code form that L1 exempts.
  - L1 is a language rule, and no secret-scan, SCA or other allowlist changed.
  - The entries are path prefixes (`scripts/check_records.py:1344`), so a file named with the same
    prefix would inherit the exemption. That is harmless here.
- **The harness.**
  - The package does not build it (the test target's path is `ios/EngineTests`), and the app cannot:
    it sits outside `ios/ModelRanking`.
  - It opens no network connection. It reads one file and writes one, each at a path the operator
    passes, and it calls only the on-device model.
  - Its header says to run it in a copy of `ios/`, never in this checkout.
- **Secrets and dependencies.**
  - `gitleaks detect --no-git` on the tree: no leaks. On the range's commits: no leaks.
  - No manifest changed (`pyproject.toml`, `Package.swift`), and there is no new third-party
    import.
  - `deps` and `slopsquat` need the network and were not run; nothing they read changed.
  - Bandit is not installed in the venv.
- **Sensitive files.** None touched: no CI, plist, `pbxproj`, `.claude/settings.json` or
  dependency manifest.
- **Tests on HEAD.** `make check-fast` PASS in 70.5 s:
  - pytest: 1,514 passed, 23 skipped;
  - `swift-test`: 351 tests, exactly the manifest;
  - `client-decls`: 15 files, 4 configurations;
  - the records, lint and typecheck legs.

## Gates

- [x] Secret scan: gitleaks, no leaks on the tree or the range's commits.
- [x] No new dependency, so `deps` and `slopsquat` are unaffected. They were not run, because both
  need the network.
- [x] Default-deny on the changed surface. `/v1/categories` gains one read-only field, takes no
  parameter, and the route set is unchanged.
- [x] Permission matrix not violated. No new file is allowed the network, the file system or
  position arithmetic.
- [x] Prompt-injection hygiene. The schema is closed and the boundary keeps only table entries. The
  gates' blind spot is S1.
- [x] SAST: `ruff --select S` clean on `main.py`. Bandit is not installed.
- [ ] Auth, PII and payment: not applicable. The typed question's path to storage and the network is
  unchanged, and S3 is a record.

## Note on the run

- `make check-fast` ran the existing `RouterBoundaryTests`, which routes six questions through the
  real tiers, as it always does. No probe of mine called the model.
- The S1 mutant was checked only with tests that do not call the model.
- The temporary Swift tests are in the scratchpad, not the tree:
  - the standings timings and payload shapes;
  - the release-build timing, `swift test -c release -Xswiftc -enable-testing`, which writes only
    under the ignored `ios/.build`;
  - the schema encoding.
- The served artifact `advisor.db` was read once with `?mode=ro`. Its sha256 was unchanged, and no
  journal file appeared.
