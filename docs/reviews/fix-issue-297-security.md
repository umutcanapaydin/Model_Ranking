---
record_type: review
id: fix-issue-297-security
status: draft
seat: independent
process_version: v7.1.2
date: 2026-10-17
---
# Security Review: fix-issue-297 (draft PR #315, `fix/issue-297-keep-provenance`)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`; policy read from `main`)
**Independent:** yes. I wrote none of this change's code, tests or records.
**Seat and method:** a fresh worktree detached at `700a8f0` under a `mktemp -d` directory, with its own venv
(`make install`), per D-174. The author worktree (`scratchpad/gn-297`) and the session tree were read only
through git. `advisor.db` was copied in, as the owner allowed for this run. The range was read in full. Then
11 gate mutants were fault-injected in place, 5 probe plants were made in the shipping `ContentView.swift`
and `StandingsStore.swift`, and 21 compiled probes were judged by the gate. Every file was restored
byte-identical: gate md5 `70ee14d0…`, `ContentView.swift` `3e81710b…`, `StandingsStore.swift` `e4860da2…`,
and `git status` was clean after each one.
**Date:** 2026-10-17
**Release range:** `58e9f21..700a8f0`. The merge-base with `origin/integration/run-golden-night` is `58e9f21`.
The range has 2 commits: `e3e9eba` (red) and `700a8f0` (fix).
**Reviewed head:** 700a8f04384ae20686eebc53e1e0e655b1206561
**Risk tier:** MEDIUM. The brief declares no HIGH paths. The change edits a privacy control over what the phone
keeps beside the standings. That is the same tier the #288 seats used.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 4 · NIT 1.

The gate now holds what #297 asked for, in the shapes the fixture plants:
- `keep` is refused outside `ContentView.load()`, in that file and in another.
- P5 is refused at the decode, directly and through a type that holds a `[Category]`.
- The kept types cannot be built by an initialiser.
- INV-73 reads as `EngineClient.address(configured:onDevice:)` behaves.

Nothing that existed before was weakened. R-m1 (P5) is **narrowed, not closed**. Three spellings that need no
`typealias` keyword still put the typed question into `answers.json`, and each passes `make client-decls` and
the whole unit suite on the shipping client (M1). This is a deliberate forgery, which no shipped code does,
and INV-67 states it honestly ("by the shapes the fixture holds"). That is the calibration the #288 re-review
gave the original P5, so it is MINOR, not BLOCKING.

## Your four questions

1. **Does the gate hold what #297 asks, including P5?** It holds the `keep` call site and the initialisers. P5
   is held only partly. Planted in the shipping `ContentView.load()` (`ContentView.swift:1117`):
   - Plain P5, `decode([Category].self, from: Data(question.utf8))`, makes `make client-decls` FAIL in all 4
     configurations with "decodes `Category`, a kept answer's type".
   - P5 behind an inferred associated type, an enum case or an existential metatype gets client-decls PASS
     and the unit suite 3131 passed (M1).
   - P5 behind an explicit `typealias` gets client-decls PASS. It is caught only by the text pin
     `\btypealias\b` (`tests/unit/test_router_hints.py:723`), which scans every client file.
2. **Can it fail open?**
   - Spellings the gate misses: M1 and NIT N1.
   - An empty derived set: yes for the compiled leg (M2). Rename `keep` and the rule matches nothing, and
     client-decls passes. A text pin still fails.
   - A file it does not read: no. `main()` derives the file set from `CLIENT.rglob("*.swift")` and refuses a
     dump with a missing file. `kept_answer_facts` runs on every file's tree.
   - A compiler-format drift (`SUBSTITUTION` no longer matching) fails closed: mutant 2 is killed by the
     fixture's self-test.
3. **Did anything weaken?** No.
   - Old gate on the old snapshot: 133 refusals. New gate on the new snapshot: 139, the 6 new ones only. **0
     refusals gone**, with line numbers normalised.
   - The new gate on the old snapshot refuses exactly what the old gate did.
   - The snapshot's declarations: 263, now 292, 0 gone.
   - The 154 deleted snapshot lines are line-number shifts and closing parentheses at file ends where content
     was appended. Every one of them reappears with only its numbers changed, except 5 tail lines.
   - Fixtures: additions only. `FIXTURE_REFUSALS` and `FIXTURE_RULES`: additions only.
   - `KEPT_TYPES` grows by `Recommendation`, `Category` and `KeptAnswer`. That is a strengthening: they now
     fall under "a kept type extended" (`client_decl_gate.py:895`).
   - INV-67 keeps every citation and gap, and adds 4 tests.
   - INV-73 keeps all 4 old citations and adds 8. All 7 Swift tests and the 2 Python pins it cites exist. Its
     new text matches `EngineClient.swift:221-230` and `:174-180`.
4. **Is the skip budget increase justified, and is the test really CI-only?** Yes.
   `scripts/coverage_floor.py --derive` on the head prints "CI will skip 87 of 3221 (… xcode 3)", equal to
   the budget. The new test is `@pytest.mark.needs("xcode")`. `tests/skips.py:67` gives `xcode` `in_ci=False`
   because CI's test job runs on `ubuntu-latest` (`.github/workflows/ci.yml:30`). Here, with Xcode, it ran
   and passed (`-rs -v`: PASSED, not skipped). Its rule also runs in CI through the committed dump and the
   measured lines (`test_kept_answer_provenance.py:98`, `:105`).

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **M1** `scripts/client_decl_gate.py:1828-1836` (`_decoded`), `:1839-1851` (`_owned`), docstring `:49-52`.
  The decode rule reads the substitution as the compiler *prints* it, sugar included. It sees no decode in an
  enum's synthesised decoder, and none behind an existential. P5 was re-planted in the shipping
  `ContentView.load()` and kept, and each form below passed `make client-decls` (4 configurations) and
  `pytest tests/unit` (3131 passed, 61 skipped):
  - (a) `decode(ProbeShape.Item.self, …)`, where `struct ProbeShape: ProbeShaped { func sample() -> [Category]? }`
    infers `associatedtype Item: Decodable`. The dump prints `T -> ProbeShape.Item`. The implicit
    `(typealias implicit "Item" … type="[Category]")` is in the dump but unread.
  - (b) `enum ProbeEnvelope: Decodable { case surfaces([Category]) }`. Its synthesised `init(from:)` is printed
    untyped (`type="<null>"`, no `substitution_map`), so the enum is never "held".
  - (c) `let t: any Decodable.Type = [Category].self; decode(t, …) as? [Category]`.
  - An explicit `typealias Cats = [Category]` (also `[C]`, `Array<Category>`, `[KeptAnswer]`) passes
    client-decls too. Only the text pin's `typealias` ban stops it.

  The docstring and the PR's "Not covered" name only the app-protocol helper. **Remedy:**
  - Expand each substituted type through every `typealias` decl in `main`, explicit or `implicit`, by its
    `type=`, to a fixed point.
  - Take an enum's held kept types from its cases' payload types, since its synthesised decoder is not typed
    in the dump. Or fail closed on a synthesised decoder with no typed decode.
  - Name the existential form in the docstring and as a G-gap in INV-67's row.
  - Plant (a), (b) and the typealias in the fixture.
- **M2** `scripts/client_decl_gate.py:1952-1975` (`unseen_permissions`). The new rules' allowed sides are not
  required to be *seen*. Renaming `StandingsStore.keep` to `remember` (`StandingsStore.swift:206`, `:214`;
  `ContentView.swift:1119`, `:1131`) and adding `StandingsStore.onDevice.remember(categories)` in `submit()`
  gives `make client-decls PASS` in 4 configurations: `CALLED_ONLY_IN` matches nothing. Only the text pins
  `test_engine_address.py::test_the_kept_answers_store_takes_only_what_the_engine_sent` and
  `::test_the_screen_shows_the_kept_answer_and_its_day_when_the_engine_cannot_be_reached` fail, so the system
  as a whole held. A rename of `Category` or `Recommendation` would silence `KEPT_ANSWER_TYPES` and
  `PROVENANCE_BY_TYPE` the same way. This is the empty-derived-set case AGENTS.md §3.5 says must fail.
  **Remedy:** in `unseen_permissions`, require the `ContentView.load` call to `StandingsStore.keep` and at
  least one allowed decode of each `KEPT_ANSWER_TYPES` entry on the shipping client, as the W2 review's R3
  does for arithmetic and sorts.
- **M3** `scripts/client_decl_gate.py:328`, `:351`, `:357-359`, `:1876`, `:1866-1869`. Half the new rule has
  no planted refusal. These mutants all survived `tests/unit/test_kept_answer_provenance.py` and
  `tests/unit/test_client_decl_gate.py` (142 passed, the compiled self-test included):
  - `Recommendation.init(` removed from `PROVENANCE_BY_TYPE`;
  - `Recommendation` decodable in `ContentView.swift`/`Detail.swift`;
  - `KeptAnswer` decodable in `ContentView.swift`;
  - the `.init(from:)` branch disabled;
  - the fixed point cut to one pass.

  The rules work today: probes V7, V16, V18 and V15 (two-level holder) are refused. But nothing holds them.
  The `KeptAnswer` one matters most. A `[KeptAnswer]` decoded from typed text outside the store could be
  laundered through `KeptAnswers.categories(_:now:)` (`ios/ModelRanking/Engine/KeptAnswers.swift:50-56`, an
  allowed decode) into `keep`. **Remedy:** plant each of these in the fixture and add them to
  `FIXTURE_REFUSALS`:
  - a `Recommendation` decode and initialiser outside the allowed files;
  - a `[KeptAnswer]` decode outside the store;
  - a `CategoryList.init(from:)` reference;
  - a two-level holder.
- **M4** #297, comment 1, and the PR body ("The default file protection stays"). The #288 review's M3 second
  half, `.completeFileProtection` for `answers.json`, was moved *into* #297. This PR leaves it undone, says
  "Closes #297", and files no follow-up: an issue search for it finds only #297. Merging would close the
  finding with no disposition. **Remedy:** before merge, file it as its own issue, with the gate edit it
  needs (`SINK_FOUNDATION_ALLOWED` and the write's text pin), or drop "Closes" for "Part of".

### NIT
- **N1** `scripts/client_decl_gate.py:688` (`FUNCTION` captures the base name `\w+`), `:694` (`TYPE_DECL` has
  no `actor_decl`), `:1843` (owner is the simple name). `CALLED_ONLY_IN` is matched by the base name and the
  simple type name. In compiled probes, two `keep` calls outside the load path got no #297 refusal:
  - V4: an overload `func load(later:)` in `ContentView`;
  - V8: a nested `enum Elsewhere { struct ContentView { func load … } }` in `ContentView.swift`.

  An actor nested in `ContentView` would pass the same way. This is defence in depth only: the argument still
  has to be an allowed decode. **Remedy:** match `load()` by its full name and the owner by its full path,
  and add `actor_decl`.

### PASS
- **Red to green.** The 8 new assertions fail on the pre-fix gate, fixtures and snapshot (8 failed, 2
  passed), and pass at the head (10 passed, the compiled probe included).
- **Fault injection.** These gate mutants were killed:
  - `kept_answer_facts` removed from `references`;
  - `SUBSTITUTION` broken: the compiler-format drift fails closed;
  - `CALLED_ONLY_IN` emptied;
  - the function ignored in the call-site check;
  - synthesised decodes counted as decodes.
- **The fail-closed directions hold.**
  - A `keep` in a computed property (V22), a function nested in `load` (V23) or another file (the fixture's
    `Detail.swift`) is refused. A closure inside `load` is allowed (V24); its argument is still held to a
    decode.
  - An extension-declared `Decodable` conformance whose synthesised decoder holds a kept type is held (V14).
  - Generic wrappers `Box<[Category]>`, `[String: Category]`, `Optional<Recommendation>`,
    `PropertyListDecoder`, `T: Codable` helpers and a two-level holder are all refused (V6, V7, V10, V12,
    V15, V21).
  - A function value of `keep` taken outside `load` is refused (V9).
- **The `Category.CodingKeys` exclusion** keeps the engine's own synthesised decoders allowed, and the shipping
  client passes: `make client-decls` PASS, 22 files, 4 configurations.
- **Text pins.** The text pins hold `keep`'s two declarations and refuse `typealias` in every client file. That
  is a second layer under M1 and M2.

## Gates passed
- [x] Secret scan green (`make secrets` on the reviewed head): see "Gate runs" below
- [x] `make deps` (pip-audit) green: see below
- [x] `make slopsquat` green: no new import or dependency in the range (no `pyproject.toml` or `requirements/` change)
- [x] Default-deny preserved for new external surfaces: no route, endpoint or network surface in the range
- [x] Permission-matrix not violated: the gate change is owner-approved (D-206 clause 4). No CI, hook,
  `.claude/` or `.githooks/` file is touched. No destructive operation is in either commit.
- [x] Prompt-injection hygiene: N/A. No fetched or LLM content is consumed by the range.
- [x] Auth/PII checks and the human-review trigger: the typed question is PII-adjacent. The control change has
  the owner's approval on record (D-206 clause 4), and a human merges the draft PR.
- [x] SAST: no product source (`src/`, `ios/ModelRanking/`) changed in the range. The gate script is covered
  by `make lint`/`make typecheck` inside `make check`.

### Gate runs (own worktree, reviewed head)
- `make check`: exit 0.
  - ruff "All checks passed!"; mypy "no issues found in 49 source files".
  - pytest **3194 passed, 27 skipped**, coverage 92.19%.
  - check_records PASS; install-check PASS; wave-check-all PASS; conformance PASS (29).
  - **swift-test PASS (685, each in the manifest; SlowTierTests 7 of 7)**.
  - **client-decls PASS** (22 files, 4 configurations).
- `make secrets deps slopsquat`: exit 0.
  - gitleaks "no leaks found".
  - pip-audit "No known vulnerabilities found".
  - slopsquat PASS, 20 declared dependencies, 0 suspect.
- No change in the range to `pyproject.toml`, `requirements/`, `.github/`, `.claude/` or `.githooks/`.
- The new test data holds no secret-shaped string: only `/x/` paths and Swift source.

## Acceptance criteria evidence
- #297 "the client-decls gate refuses a `keep` call outside the load path (a planted call fails it)":
  - `scripts/client_decl_gate.py:340-345` and `:1879-1892`;
  - `tests/unit/test_kept_answer_provenance.py:39` (fixture: `ContentView.keepElsewhere`, `Detail.swift`
    `fixtureDetailKeeps`);
  - `:151` (compiled probe: `ContentView.keepLater`);
  - mutant M7 (function ignored) killed;
  - compiled probes V9 (a function value of `keep`), V22 (a computed property) and V23 (a function nested in
    `load`) are each refused.
- #297 comment 2 / R-m1 (P5), "limit where `Recommendation` and `Category` values are built or decoded":
  - held in the fixture's shapes: `client_decl_gate.py:350-360`, `:1854-1881`, `:326-333`;
  - `test_kept_answer_provenance.py:48`, `:55`, `:98`, `:151`;
  - plain P5 planted at `ContentView.swift:1117` makes `make client-decls` FAIL in 4 configurations;
  - partial, see M1.
- #297 "INV-73 reads as the code behaves": `docs/security-invariants.md:139`, against
  `ios/ModelRanking/Engine/EngineClient.swift:174-180` and `:221-230`. Held by
  `tests/unit/test_engine_address.py:171`.
- INV-67 updated: `docs/security-invariants.md:128`. Its 4 new citations exist and pass.
- Skip budget: `docs/skip-budget.txt` (87). `coverage_floor.py --derive` gives 87 (xcode 3).

## Risks queued
- **R1** INV-67's row should name M1's three forms (inferred associated type, enum payload, existential
  metatype) as a gap, until the gate expands sugar and enum payloads. Until then, R-m1 is narrowed, not
  closed, and #297's closing comment should say so.
- **R2** M4: the `answers.json` protection class has no open issue once #297 closes.
