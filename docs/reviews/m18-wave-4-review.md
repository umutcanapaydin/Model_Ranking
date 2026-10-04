---
record_type: review
id: m18-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W4 Code Review, round 2: the engine and data backlog

**Reviewer:** a second Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or
records, and I am not the round-1 seat.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `d528fd3..77d3b2f`, the whole wave: 13 commits, 33 files. `d528fd3` is the head of
`wave/m18-w1` (PR #99, unmerged), which this wave is stacked on. Round 1 read `d528fd3..5623f4b`
and wrote its verdict at `5807fbe`. The fix round is red `81a3942`, then fix `77d3b2f`.
**Risk tier:** HIGH (`docs/plans/m18-wave-4-plan.md:11`). By D-172 there is no security seat on the
wave.
**Model routing (HIGH, advisory):** author-family: claude-opus / reviewer-family: claude-opus (fallback: no second model family is available to this seat)
**Fresh context:** this seat started with none of the authoring context and none of round 1's. The
brief told me to check round 1's verdict rather than trust it, so I read it after the plans and
D-173 and before the code. I then re-derived each of its claims from the code, the tests and my own
probes. The commit subjects were visible in `git log` from the start. `81a3942`'s message was
printed with its test diff. I read `77d3b2f`'s message only after the source diff.

**Summary.** Round 1's BLOCKING finding is fixed, and a test holds it.
1. **B1.** The nightly child's allowlist now carries the three bound variables
   (`nightly.py:92`).
   1. Its test drives a real child through `NightlyRefresh.run_once` with all three overridden
      (`test_nightly_refresh.py:581`).
   2. That test is red on `81a3942` and green on `77d3b2f`.
   3. A mutant that drops `*BOUND_VARIABLES` turns it red.
2. **M1, M3, R2 and R3** are fixed and held the same way.
3. **The rest of the wave holds up again.**
   1. `/v1` is unchanged except for tie order and negotiated compression. I measured that myself,
      base against head.
   2. The server loads no new cycle module.
   3. `docs/decisions.md` only gains lines.

Nothing blocks. Seven findings are MINOR:
1. **M6.** The bound variables are named twice, so B1 can come back unnoticed.
2. **M7.** D-173 clause 3 promises a count in the refresh record that is not there.
3. **M8.** Round 1's M4(3) is still open, and a citation sits on the wrong test.
4. **M9.** The new M3 test checks the installed tree, not the tree under test.
5. **M10.** The wave's test edits moved eight of the PRD's evidence lines.
6. **M11.** Some of D-173's text and notes are still off.
7. **M12.** R3's wider rule has an unpinned edge and no record.

**Policy.** I read the profile (`.claude/agents/Code-Reviewer.md`) and `.agents/rules/practices.md`
from `d528fd3`. `docs/permission-matrix.md` does not exist at that ref. The matrix is
`permission-matrix.md` at the root, which I read from `d528fd3`. Two checks came back empty:
1. `git diff --stat d528fd3..77d3b2f -- .claude .agents permission-matrix.md .github Dockerfile fly.toml epb.html or.md AGENTS.md`.
2. The removed lines of `git diff d528fd3..77d3b2f -- docs/decisions.md`, which is 63 added and 0
   removed.

**How I worked.** Everything ran in this worktree (`77d3b2f`, its own `.venv`), plus `git archive`
copies of other commits in the scratchpad (`cr2-trees/`). `make` was not used, so that `install`
writes nothing.
1. **Gate at `77d3b2f`.**
   1. `MODEL_RANKING_REQUIRE_ARTIFACT=1 pytest -n auto`: **1590 passed, 25 skipped**, total
      coverage 91.70%.
   2. The skips match `docs/skip-budget.txt`'s owner's-Mac figure of 25.
   3. ruff, mypy (strict, 42 files), `module_coverage_floor.py`, `check_records.py` and its
      self-test, `wave_check_all.py`, `shell_dialect_check.sh` and `conformance/run-all.py` (16)
      all PASS.
   4. I ran no Swift leg: the range changes no file under `ios/`.
2. **Red first, round 2.** I ran `81a3942`'s tree with `PYTHONPATH` set to that tree.
   1. Three tests fail there and pass at `77d3b2f`: the B1 child test, the M1 publish-during-build
      test and R3's `gpt-4o-latest-v2` case.
   2. B1 fails for the stated reason: the child saw `500 / 25000 / 5000` against the parent's
      `1000 / 30000 / 10`.
   3. The M3, M4 and R2 tests pass on the red tree, as the commit message says. They hold
      behaviour that was already there.
3. **R2.** I ran the #71 test 15 times against `d528fd3`'s `protocols.py` placed in `77d3b2f`'s
   tree. It failed all 15 runs. On `77d3b2f` it passed all 15. It no longer depends on timing.
4. **Mutants: 18.**
   1. Each was applied in place with a scripted exact-string replace (`cr2-mutants.py`) and
      restored from the original bytes.
   2. After each, `git hash-object <file>` equalled `git rev-parse HEAD:<file>` and
      `git diff --quiet` held. All 18 checks were True.
   3. 14 were killed. 4 survived: `b1-drift` (**M6**), `m1-second-read` (below, PASS),
      `r3-loose` (**M12**) and `m-42-baseline` (**M8**).
5. **Probes**, all in-process with a TestClient or plain Python, against copies of the served
   artifact in the scratchpad. Nothing bound a socket.
   1. `/v1` at base and head: 46 answers.
   2. The modules a fresh interpreter loads for `app.adapter.main` and for `app.adapter.nightly`, at
      base and head.
   3. The boards memo under `chmod 000` and under an `os.replace` publish.
   4. The accessibility guard on an expiry night.
   5. The refresh record's keys on a publishing and on a refusing night.
   6. `derive_identity` on eleven `-latest` spellings.
   7. Every `-latest` name in the served artifact.
   8. The M3 test against a mutated tree, with and without `PYTHONPATH`.
6. **Contract test, once.** `RUN_CONTRACT_TESTS=1` on `tests/integration/test_epoch_bundle_contract.py`:
   2 passed.
7. **Read only:** GitHub issues #100 to #104.
8. **Not done, by this seat's rules.**
   1. I ran neither installer, and only `tests/unit/test_engine_service.py` runs them, with its stubs.
   2. No `launchctl`, `xcodebuild`, `simctl` or simulator, and nothing under `~/Library`. So
      D-173 clause 7's "no such job is installed on the owner's Mac (measured 2026-10-04)" is not
      verified here.
   3. No server, and no commit, push or GitHub write.
9. **Tree.** Clean apart from this file. Probes, extracted trees and logs are in the scratchpad
   (`cr2-*`).

## Verdict
PASS-WITH-MINORS

**No BLOCKING, seven MINOR, one K.9, one risk.** Every finding below is a test-strength,
record-accuracy or hermeticity gap. I probed every behaviour the wave promises and each is correct.
The first five MINORs are a line or two each. I recommend fixing them in this wave, because
`make wave-check` needs a disposition for each anyway.
- **M6** `serving_bounds.py:35-39` and `:64-68` spell the three variable names twice, and the B1 test lists them literally. A fourth bound read only by `bounds_from_env` would reopen B1 with every test green (mutant `b1-drift` survived).
- **M7** D-173 clause 3 (`decisions.md:3427-3428`) and plan decision 3 put the accessibility count "in the refresh record". The record has no such key. Only a refusal's reason names the counts.
- **M8** Round 1's M4(3) was neither fixed nor filed: the accessibility guard on an expiry night is still untested (mutant `m-42-baseline` survived). REQ-REF-009 is cited on a test that exercises neither carry nor expiry, and REQ-ING-004 is cited by no W4 test.
- **M9** The new subprocess test for M3 (`test_refresh.py:293`) imports the interpreter's installed `app`, not the tree under test. Run on a mutated tree without `PYTHONPATH`, it passed (false green).
- **M10** The wave's test edits moved eight `file:line` evidence pointers in `docs/prd.md`. Four now land on helper functions.
- **M11** D-173 still has residual text: its second mitigation bullet contradicts the corrected clause 2. The D-164 note amends nothing D-164 holds, and two notes sit outside their ADR's closing rule.
- **M12** R3's fix widened the derivation rule (`-latest-v<digit>` now derives). Its boundary is not pinned (mutant `r3-loose` survived), and no ADR records the rule.

**K.9:** K4 (no gate checks the PRD's `file:line` pointers, which is why M10 was invisible).
**Risk:** R4 (a `-latest-v<N>` name that does move would now derive a fixed id).

## Round 1, re-checked one id at a time

"Broken on purpose" names the mutant I applied, or "n/a" for a record-only finding.

| Round-1 id | Fixed? | Held by a test? | Broken on purpose |
|---|---|---|---|
| B1 child never sees the bounds | **Yes.** `nightly.py:46`, `:92`; `serving_bounds.py:35-39` | `test_nightly_refresh.py:581`, through `run_once` and a real child | `b1-allowlist` (drop `*BOUND_VARIABLES`): **killed**. Drift between the two spellings is not held: **M6** |
| M1 memo files a retired payload | **Yes.** Key read before the open (`main.py:1410`), `.get` (`:1411`), identity re-read before storing (`:1421`) | `test_board_standings.py:274` | `m1-order` (key after the open again): **killed**. `m1-second-read` survived; see PASS for why that is expected |
| M2 D-173 vs the ADRs it amends | **Mostly.** (1) The clause-1 fingerprint text is now correct. (2) Clause 2 is narrowed and #100 is filed. (3) D-154 is in the header and clause 7 records the measurement. (4) Notes are appended | n/a (records) | n/a. Residuals: **M11**. Clause 3 is also off (**M7**), which round 1 did not raise |
| M3 boundary checked one level deep | **Yes.** `test_refresh.py:293` | itself | `m3-transitive` (`serving_bounds` imports `app.adapter.nightly`): **killed**. Not hermetic: **M9** |
| M4 three untested acceptance cases | **Two of three.** (1) The standings bound: `test_refresh.py:1766`. (2) The first artifact: `:1781`. (3) The expiry night: **not done and not filed** | (1), (2) yes. (3) no | `m4-standings`: **killed**. `m4-first`: **killed**. `m-42-baseline`: **survived**. See **M8** |
| M5 records drift | **Mostly.** (2) The docstring is rewritten. (3) The README line is now a fact. (1) REQ-API-001 and REQ-CAN-001 are cited aptly | n/a | n/a. REQ-REF-009 is cited on a test that does not exercise it, and REQ-ING-004 not at all: **M8** |
| K1 subscription ties by plan name | Filed as **#101**, open | n/a | n/a |
| K2 picks compared by display | Filed as **#102**, open | n/a | n/a |
| K3 coverage register cites deleted files | **Yes.** A dated "Read as of M9" note (`coverage-by-req.md:9-13`) | n/a | n/a |
| R1 `run.reports` keeps the old count | Filed as **#103**, open | n/a | n/a |
| R2 the #71 red rests on a sleep | **Yes.** `close()` joins the worker (`test_fetch_bounds.py:301-307`) | `test_fetch_bounds.py:310` | `r2-71`: **killed**. 15 of 15 red on the old `protocols.py`, 15 of 15 green on the fix |
| R3 `-latest-v2` derives nothing | **Changed to derive** (`registry.py:446`) | `test_moving_aliases.py:102` (`gpt-4o-latest-v2`) | `r3-revert`: **killed**. `r3-loose` (`(?!v)`): **survived**. See **M12**, **R4** |

#100 (D-173 clause 2's board-guard limit) is filed and open. #104 is outside this range: the range
does not touch `scripts/engine_service.sh`.

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M6** `src/app/workflows/serving_bounds.py:35-39`, `:64-68`; `tests/unit/test_nightly_refresh.py:589-591`. **The fix names the bound variables twice, and the test that holds B1 lists them a third time.**

  `BOUND_VARIABLES` is a tuple of three strings. `bounds_from_env` does not read through it: it
  spells the same three strings again in its own `os.environ.get` calls. The B1 test then sets
  three literal names. Today all three spellings agree.

  The failure mode is B1 itself. Someone adds a fourth bound to `ServingBounds` and
  `bounds_from_env` and forgets the tuple. The engine then enforces the bound and the child checks
  against its default, and nothing goes red. I simulated that: mutant `b1-drift` makes
  `bounds_from_env` read one more variable that the tuple does not name. It **survived**
  `test_nightly_refresh.py`, `test_refresh.py` and `test_board_standings.py` (169 passed).

  Round 1's fix asked for exactly this: "a `BOUND_VARS` tuple that `bounds_from_env` reads", or a
  test "derived rather than listed". The practice is the corpus's most reproduced one: one fact in
  two places drifts (`.agents/rules/practices.md`, K.5).

  **The fix**, either of:
  1. `bounds_from_env` reads each value through `BOUND_VARIABLES` (for example
     `dict(zip(BOUND_VARIABLES, defaults))`);
  2. or the B1 test sets every name in `BOUND_VARIABLES` to a distinct non-default value and
     asserts that every `ServingBounds` field moved. Then a field read from a name the tuple lacks
     fails the test.

- **M7** `docs/decisions.md:3426-3428`; `docs/plans/m18-wave-4-plan.md:29-31`; `src/app/workflows/refresh.py:728-765`. **D-173 clause 3 says the accessibility count is in the refresh record. It is not.**

  The plan's decision 3 reads "The count goes in the refresh record". D-173 clause 3 reads "and the
  count is in the refresh record". `ServingSummary.accessible` is computed (`refresh.py:523`), but
  neither `RefreshOutcome` nor `write_status`'s payload carries it.

  Probe (`cr2-probe/record_probe.py`, driving `refresh()` on the test fixtures):
  1. A publishing night (8 → 12 values) writes these keys: `at`, `at_iso`, `candidate_fingerprint`,
     `carried`, `consecutive_refusals`, `derived`, `drift`, `exit_code`, `expired`,
     `last_published_at`, `live_fingerprint`, `outcome`, `reason`, `renamed`,
     `sources_last_ok`, `surfaces_answering`, `unmatched`. None of them is about accessibility.
  2. A refusing night (12 → 1) names "from 12 to 1" only inside `reason`.

  So on a normal night nobody can see the count move, which is what the decision promised. The
  guard itself is right (see PASS).

  **The fix:** either write the count into the record, with one assertion next to
  `test_refresh.py:1697`'s `renamed` check, or correct clause 3 to say that a refusal names the
  counts.

- **M8** `tests/unit/test_refresh.py:1733-1736`; `src/app/workflows/refresh.py:900`, `:1161`; `docs/plans/m18-plan.md:33`. **Round 1's M4(3) is still open, and the REQ-REF-009 citation landed on a test that does not exercise it.**

  1. **The expiry night is untested.** The fix commit covered M4(1) and M4(2) and said nothing of
     M4(3). No issue was filed for it either (I read #100 to #104). The behaviour is right. I
     probed the served artifact: live 225 values, baseline after `epoch_access` expires 0. Against
     the live artifact the guard refuses ("225 to 0"). Against the baseline it says nothing. But no
     test holds it. Mutant `m-42-baseline` adds the accessibility reasons judged against `live`
     rather than the baseline. It **survived** `test_refresh.py`, `test_refresh_carry.py` and
     `test_carry_forward.py` (119 passed). So a change that makes an `epoch_access` expiry refuse
     every night would pass the suite. That is the freeze D-128 calls the failure to fear, on the
     one path REQ-REF-009 exists for.
  2. **The citation.** M5(1) asked for the scoped REQ-IDs to be cited. REQ-REF-009 went onto the
     accessibility test as "REQ-REF-009's guards" (`test_refresh.py:1736`). That test builds two
     artifacts with no failed, carried or expired source, so it cannot fail for a REQ-REF-009
     reason. Round 1 named the expiry-night test as the citation's natural home. The practices
     name this exact shape: a test that certifies a requirement it never drives.
  3. **REQ-ING-004**, also scoped to W4 (`m18-plan.md:33`), is cited by no test in this range.

  **The fix:** one test drives `_cycle` with `epoch_access` expired and asserts that the night
  publishes. Move the REQ-REF-009 citation there. Cite REQ-ING-004 where the wave touches
  provenance (the contract tests are the nearest), or record why it is out of scope. The close
  should account for M4 part by part, not as "fixed".

- **M9** `tests/unit/test_refresh.py:293-305`. **The new M3 test checks whatever `app` the interpreter has installed, not the tree under test.**

  The probe runs `[sys.executable, "-c", "import app.workflows.refresh ..."]` with no `PYTHONPATH`.
  pytest's `pythonpath = ["src"]` changes only the test process's `sys.path`, and the child does not
  inherit it. So the child resolves `app` through the venv's editable install. Its sibling test
  pins this explicitly: `env={..., "PYTHONPATH": "src"}` (`test_nightly_refresh.py:369`).

  Measured: I applied the M3 mutant (`serving_bounds` imports `app.adapter.nightly`) to an extracted
  copy of `77d3b2f` and ran the test from that copy with this worktree's venv.
  1. Without `PYTHONPATH`: **passed**. It imported the clean worktree.
  2. With `PYTHONPATH=src`: failed.

  CI installs the checkout editable (`pip install -e`), so CI is not fooled today. Any run whose
  interpreter was installed from a different tree is.

  **The fix:** pass `env={**os.environ, "PYTHONPATH": "src"}` (and keep `cwd`), as the sibling test
  does.

- **M10** `docs/prd.md:405`, `:407`, `:408`, `:410`, `:411`, `:430`, `:432`, `:544`. **The PRD's evidence pointers no longer point at their tests.**

  The PRD's MET rows cite tests as `file:line`. Two edits moved the lines:
  1. `81a3942` inserted the M3 test at `test_refresh.py:293`, so every later test moved down 15
     lines.
  2. `5623f4b` removed a 15-line test at `test_nightly_refresh.py:439`, so later tests moved up 15
     lines.

  I compared the enclosing `def` at each cited line at `d528fd3` and at `77d3b2f`:
  1. REQ-REF-001, `test_refresh.py:1348`: was `test_a_sigkilled_cycle_leaves_the_live_artifact_byte_identical`, now the helper `improving` (the test is at `:1363`);
  2. REQ-REF-003, `:660`: was `test_a_candidate_that_blinds_a_surface_is_refused`, now the helper `_sized` (the test is at `:675`);
  3. REQ-REF-004, `:802`: now `test_every_cycle_records_what_it_did` (the cited test is at `:817`);
  4. REQ-REF-006, `:1400`: now the helper `slow` (the test is at `:1415`);
  5. REQ-REF-007, `:293`: now the new M3 test. It is still apt, but the cited test is at `:308`;
  6. REQ-GRD-001, `:1509`: now the helper `_injected` (the test is at `:1524`);
  7. REQ-GRD-003, `:1636`: now a different test (the cited one is at `:1651`);
  8. REQ-REF-009, `test_nightly_refresh.py:557`: now `test_health_says_nothing_is_carried_when_nothing_is` (the cited test is at `:542`).

  Practices.md makes `file:line` evidence load-bearing. This wave's own coverage note now sends
  readers to the PRD for current status (`coverage-by-req.md:12-13`).

  **The fix:** update the eight numbers. **K4** is the gate that would have caught them.

- **M11** `docs/decisions.md:3448`; `:3027`; `:1204-1206`, `:2425-2427`. **D-173 and its notes still have residual text.**

  1. **The mitigation contradicts the corrected clause 2.** Clause 2 now says the board guards
     "still compare a board's raw names", so an upstream re-spelling "still reads as names lost and
     gained there (#100)". The mitigation bullet is unchanged: "If a guard compares names again, a
     cosmetic re-spelling can refuse a night". But two guards compare names today, by design, and a
     cosmetic re-spelling can refuse a night today. Round 1 cited this line (`:3434` then) under
     M2(2), and the fix did not touch it. It should read "If a surface's roster guard compares
     names again".
  2. **The D-164 note amends nothing D-164 holds.** The note reads "the order of tied rows is by
     model id (clause 1); the board guards still compare raw names (clause 2)" (`:3027`). D-164
     says nothing about a ranking's tie order. Its fingerprint clause covers board standings, and
     corrected clause 1 now says no night publishes for the tie change. Its guard clause is
     explicitly unchanged. So D-173's header still lists D-164 as amended when, after the
     corrections, nothing in it is. Either drop D-164 from the header and the note, or say the
     note is a pointer to #100.
  3. **Placement.** The D-128 and D-154 notes sit after their ADR's closing `---`, directly above
     the next heading (`:1204-1206` before `## D-129`; `:2425-2427` before `## D-155`). So they
     read as a preface to D-129 and D-155. The project's own notes sit inside the section, before
     the rule (D-154's "*Amended 2026-09-29 …*", `:2421-2422`). The D-132, D-164 and D-167 notes
     are placed correctly.

  The notes are otherwise within the append-only rule (see PASS).

- **M12** `src/app/workflows/registry.py:443-446`; `tests/unit/test_moving_aliases.py:91-104`. **R3 was fixed by widening D-166's derivation rule. The new edge is unpinned and no ADR records it.**

  Round 1 queued R3 as a risk ("unmeasured whether any upstream spells one"). The fix changed
  behaviour: `-latest-` followed by `v<digit>` now derives an id. It is consistent with `-latest-2`,
  which already derived at the base. But two things are missing.
  1. **The edge is unpinned.** The lookahead is `(?!v\d)`. The mutant `(?!v)` would let a word that
     starts with `v` derive. `-latest-vision` is a word, so it should move and derive nothing, as
     `-latest-mini` does. The mutant **survived** `test_moving_aliases.py` and `test_registry.py`
     (60 passed), because no test has a `-latest-v<word>` name. Measured at head:
     `gpt-4o-latest-vision` → None and `gpt-4o-latest-v2` → `gpt4o-latest-v2`, which is right
     today, but nothing holds the line.
  2. **No record.** D-166's "Clause 3 applied (#40, 2026-09-25)" note says that a date after
     `-latest` derives (`decisions.md:3098-3102`). D-173 says nothing about versions. The rule now lives only in
     a code comment that cites "W4 review R3". A derivation rule decides which names become models
     on `/v1`, which is what D-166 governs.

  **The fix:** add `gpt-4o-latest-vision` to the word list at `test_moving_aliases.py:91`, and one
  sentence in D-173, or a note on D-166, that a `v`-numbered version after `-latest` derives, as a
  date does.

### PASS (what looks good)

- **B1 is fixed where it was broken.**
  - The child's environment is built from `CHILD_ENV` (`nightly.py:261`), which now includes
    `*BOUND_VARIABLES` (`:92`).
  - The comment above it is now true (`:85-89`). The only environment reads anywhere in
    `app.workflows` or `app.clients` are the three bounds (`serving_bounds.py:65-67`) and
    `arena_slices.py:113`, which forwards its own subset to its own reader.
  - Nothing else in the allowlist is new. The original fifteen names are unchanged, and the
    secret-stripping test still passes (`test_nightly_refresh.py:377`).
  - Only the engine runs the refresh: no `make` target, script or `ios/app.sh` path runs
    `app.workflows.refresh` by hand (`git grep`). So the engine and the child now always read one
    environment.
- **`nightly.py` importing `serving_bounds` keeps its rule.**
  - A fresh interpreter importing `app.adapter.main` loads the same `app.*` set as at `d528fd3`
    plus `app.workflows.serving_bounds`, and nothing else. None of `app.workflows.refresh`,
    `.build`, `.sources`, `.epoch` or `.rosters` loads.
  - `test_nightly_refresh.py:352` holds that.
  - `app.adapter.nightly` alone now loads 15 more `app.*` modules and `httpx` (it loaded 2 before).
    Every one arrives through `rank` and `standings`, which `main.py` already loaded before this
    wave, so the server pays nothing new.
  - The direction is the allowed one: the adapter imports a workflow. M3's mutant shows the reverse
    is caught.
- **The boards memo's two identity reads are right, and the first one is what fixes M1.**
  - The key is read before the open (`main.py:1410`). A publish between that read and the open
    stores the new payload under the retired key, which no later request can produce: the key
    carries inode, mtime_ns, ctime_ns, size and mode (`:329-338`).
  - A publish after the open is caught by the re-read (`:1421`) and stores nothing.
  - So the second read guards a state nothing can observe today. That is why `m1-second-read`
    survives. It costs one `stat` on a miss, and it is defence in depth, not a gap.
  - A hit now returns before the open. That changes nothing observable:
    1. `chmod 000` changes the key, and the route answered 503 with the memo full (probe);
    2. a vanished file fails `is_file()` first;
    3. after an `os.replace` publish the new payload is served at once (probe: the removed board
       was gone on the next request).
  - `.get` removes round 1's `KeyError` window.
- **`/v1` is unchanged except for tie order and encoding.** I measured this myself, base against
  head, on a copy of the served artifact, in-process.
  - `/health` keys, `/v1/categories`, `/v1/budgets` and `/v1/boards` give identical JSON.
  - 33 of the 42 recommendation answers are identical. The other 9 (`abstract`, `expert`,
    `mathematics` at each budget) are equal once every list is sorted. Inside them only `ranking`
    differs, and every pick names the same model.
  - With a Host list set, a foreign Host gets 400 with `nosniff` and no `content-encoding`. So the
    Host check runs before compression.
  - A gzip request to `/v1/boards` gets `content-encoding: gzip`, `vary: Accept-Encoding` and
    `x-content-type-options: nosniff`.
- **D-173's corrected clause 1 is true.**
  - The fingerprint is computed by the running code on both sides (`refresh.py:1164`, `:920`).
  - Stored fingerprints are written to the record and never read back to decide anything (`git
    grep`).
  - So the tie order changes when the engine restarts on this code, and no night publishes for it
    alone.
- **D-173 clauses 2, 4, 5, 6 and 7 match the code.**
  - Clause 2's narrowing is accurate: the surface rosters use ids (`refresh.py:492-493`), and the
    board guards use raw names (`:494`, `board_names`; `:501-508`).
  - Clause 4 holds on the production path now.
  - The clause-5 memo and gzip behave as probed.
  - Clause 6 is a ruling.
  - Clause 7's deletions leave no live reference: `git grep` over `src`, `scripts`, `ios`,
    `Makefile`, README, AGENTS, INSTALL, architecture and the PRD finds none.
- **The amendment notes keep the append-only rule.**
  - All five are pure insertions. `decisions.md` is 63 added and 0 removed across the wave.
  - No amended ADR's body changed.
  - Each note points forward to D-173, as `superseded by D-NNN` does. The project has used dated
    amendment notes on accepted ADRs before (D-154's "*Amended 2026-09-29 …*", D-121's
    "AMENDED 2026-08-17", D-166's "Clause 3 applied (#40, 2026-09-25)").
  - D-173's own text changed inside the wave, but D-173 is new in this range and unmerged.
  - Placement and the D-164 note are **M11**.
- **The accessibility guard is right on an expiry night.** It is untested (**M8**).
- **Round 1's remaining PASS claims re-check.** Mutants for #39, #42, #44 (rank and picks), #45,
  #48 and #55 (gzip) were each killed by the wave's tests.
  - `m-39`: `test_refresh.py:1682`, `:1697`;
  - `m-42-gone`: `:1733`;
  - `m-44`: `test_rank.py:262`;
  - `m-44-picks`: `test_pareto_dominance.py:196`;
  - `m-45`: `test_build.py:498`;
  - `m-48`: `test_moving_aliases.py:93`;
  - `m-55-gzip`: `test_board_standings.py:306`.
- **Discipline in the fix round.**
  - The red commit precedes its fix, and each red test fails for its stated reason.
  - No assertion was weakened. The only edits to existing tests add REQ citations or replace the
    #71 sleep.
  - No drive-by: every changed file maps to a round-1 id.
  - Both commits carry `GP-Agent:` / `GP-Task:` and no AI attribution.
  - No new `noqa`, `type: ignore` or hard-coded path in `src`.

## Producers of hardened invariant(s)

Producers of hardened invariant(s), from the code at `77d3b2f`, with the citing test for each and
the gaps:

| producer | invariant | citing test | gap |
|---|---|---|---|
| `serving_bounds.py:54-68`, `:149-175`; `refresh.py:893-895` | the candidate is checked against the bounds the engine serves under (#57) | `test_refresh.py:1749`, `:1766`, `:1781` | none in-process |
| `nightly.py:90-92`, `:261`; `serving_bounds.py:35-39` | the child sees the engine's bound values (B1) | `test_nightly_refresh.py:581` | the names are spelled twice (**M6**) |
| `main.py:208-233`, `:464-470` | the engine boots on the same bounds and messages | `test_board_standings.py` boot tests (`m4-standings` killed three) | none |
| `main.py:1410-1426` | `/v1/boards` built once per artifact, never filed under the wrong key (#55, M1) | `test_board_standings.py:237`, `:251`, `:274` | the second read is unobservable (PASS) |
| `main.py:666` | compression changes the encoding only, and the headers are kept (#55) | `test_board_standings.py:306` | none |
| `rank.py:332`; `recommend.py:320-334`, `:507`, `:511` | a tie's order never follows a spelling (#44) | `test_rank.py:262`; `test_pareto_dominance.py:181`, `:196` | subscriptions (#101) |
| `refresh.py:492-493`, `:251-258`, `:764` | surface rosters compare ids; re-spellings are recorded (#39) | `test_refresh.py:1682`, `:1697` | board guards keep raw names (#100) |
| `refresh.py:296-304`, `:900` | accessibility loses less than a quarter, judged against the expiry baseline (#42) | `test_refresh.py:1733` | expiry night (**M8**); count not recorded (**M7**) |
| `build.py:167-192`, `:750-752` | unknown efforts are counted after the reconcile (#45) | `test_build.py:498`, `:516` | `run.reports` (#103) |
| `registry.py:446`, `:474` | a `-latest` token derives no model; a date or `v`-version after it does (#48, R3) | `test_moving_aliases.py:93`, `:102` | the `v<word>` edge (**M12**) |
| `protocols.py:129-137` | "late" is decided at the deadline (#71) | `test_fetch_bounds.py:310` | none (15/15 each way) |
| the deleted refresher scripts and plist | nothing installs the retired refresher (#76) | `test_engine_service.py:509` | none |
| `refresh.py:41-52`; `serving_bounds.py:22-25` | nothing the refresh loads imports `app.adapter` (REQ-REF-007) | `test_refresh.py:293`, `:308` | the subprocess is not hermetic (**M9**) |

## Acceptance criteria evidence

The W4 criterion is "Every engine and data bug the waves filed is fixed red-first or ruled"
(`m18-plan.md:33`). Line numbers are at `77d3b2f`.
- **#44** → `rank.py:332`, `recommend.py:320-334` → `test_rank.py:262`, `test_pareto_dominance.py:181`, `:196`. Red `6858d30`/`e4e2695`, fix `293c918`.
- **#45** → `build.py:167-192`, `:750-752` → `test_build.py:498` (REQ-CAN-005), `:516`.
- **#48** → `registry.py:446` → `test_moving_aliases.py:93` (REQ-CAN-001), `:102`.
- **#39** → `refresh.py:251-258`, `:492-493` → `test_refresh.py:1682` (REQ-CAN-001), `:1697`.
- **#42** → `refresh.py:296-304` → `test_refresh.py:1733`. Expiry night untested (**M8**); the count is not in the record (**M7**).
- **#57** → `serving_bounds.py`, `refresh.py:893-895`, `nightly.py:92` → `test_refresh.py:1749`, `:1766`, `:1781`; `test_nightly_refresh.py:581`. Met on the production path now.
- **#55** → `main.py:666`, `:1410-1426` → `test_board_standings.py:237`, `:251`, `:274`, `:306` (REQ-API-001).
- **#77** → ruled by D-173 clause 6 (`decisions.md:3437-3440`). No code.
- **#71** → `protocols.py:132` → `test_fetch_bounds.py:310`.
- **#79** → `tests/integration/test_epoch_bundle_contract.py:30`, `:52`. Skipped without `RUN_CONTRACT_TESTS=1`; 2 passed live here once.
- **#76** → the deleted scripts and plist; `scripts/README.md:27-38`; `docs/prd.md:409` → `test_engine_service.py:509`.
- **#74, #56** → moved to W2 (`m18-plan.md:200-202`).

The scoped REQ-IDs:
- **REQ-CAN-001** → `test_moving_aliases.py:94`, `test_refresh.py:1683`.
- **REQ-API-001** → `test_board_standings.py:238`, `:307`.
- **REQ-REF-009** → only a misplaced citation (`test_refresh.py:1736`); the behaviour is probe-only (**M8**).
- **REQ-ING-004** → no W4 test cites it (**M8**).

## The trace from D-173, clause by clause

- **Clause 1** (ties by id) → `test_rank.py:262`, `test_pareto_dominance.py:181`, `:196`. The corrected fingerprint sentence is true (PASS).
- **Clause 2** (roster guards by id) → `test_refresh.py:1682`, `:1697`. The narrowing to ranked rosters is true; its mitigation bullet is not (**M11**(1)).
- **Clause 3** (accessibility loss guard) → `test_refresh.py:1733`. "The count is in the refresh record" is false (**M7**). The expiry night is untested (**M8**).
- **Clause 4** (bounds at refresh) → `test_refresh.py:1749`, `:1766`, `:1781`; `test_nightly_refresh.py:581`. True on the production path.
- **Clause 5** (memo, gzip, no ETag) → `test_board_standings.py:237`, `:251`, `:274`, `:306`. True (probes).
- **Clause 6** (unselectable boards stay) → a ruling, coherent with D-167 clause 1.
- **Clause 7** (retired installer removed) → `test_engine_service.py:509`. The owner's-Mac measurement is not verifiable by this seat.
- **Header** "Amends … D-164" → nothing in D-164 is amended after the corrections (**M11**(2)).

## K.8 contract drift check

`git grep -n` at `77d3b2f`, for the plan's symbols (`m18-wave-4-plan.md:62-70`) and the ones this
wave added:
```
src/app/adapter/main.py:464:def _egress_problems(db: Path) -> list[str]:
src/app/adapter/main.py:666:app.add_middleware(GZipMiddleware, minimum_size=1024)
src/app/adapter/main.py:1392:_BOARDS_MEMO: dict[tuple[str | int, ...], dict[str, Any]] = {}
src/app/adapter/main.py:1396:def boards() -> Any:
src/app/adapter/nightly.py:90:CHILD_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ", "SSL_CERT_FILE",
src/app/adapter/nightly.py:92:             "no_proxy", *BOUND_VARIABLES)
src/app/clients/protocols.py:129:    worker.join(total)
src/app/clients/protocols.py:132:    timed_out = worker.is_alive()
src/app/workflows/rank.py:332:        ORDER BY b.best DESC, m.id  -- #44 (D-173): a tie is ordered by id, never by a spelling
src/app/workflows/refresh.py:399:    models: dict[str, frozenset[str]]
src/app/workflows/registry.py:446:_LATEST_TOKEN = re.compile(re.escape(_LATEST_SUFFIX) + r"(?:-(?!v\d)|\Z)")
src/app/workflows/serving_bounds.py:35:BOUND_VARIABLES = (
src/app/workflows/serving_bounds.py:54:def bounds_from_env() -> ServingBounds:
src/app/workflows/serving_bounds.py:149:def egress_problems(db: Path, bounds: ServingBounds) -> list[str]:
```
- `_egress_problems(db)`, `boards()` and `category_ranking` keep their signatures.
- `ServingSummary.models` keeps its name and type, and holds ids now.
- `/v1` adds no field and no route.
- The three environment variable names are unchanged.
- `CHILD_ENV` keeps its name and grows by the three bound names.

**Verdict: OK.**

## K.9 candidates spotted outside this wave's scope

- **K4** `scripts/check_records.py` (`C1b`, about `:600-645`); `docs/prd.md` evidence cells. **No gate checks that a cited `file:line` still lands on the test it names.** `check_records` resolves a cited path and an `#anchor`, never a line number. So M10's eight moved pointers passed every leg of the gate. A test inserted near the top of a heavily cited file silently re-points every MET row below it. A check could resolve each `test_x.py:N` in the PRD to its enclosing `def` and compare it with a name kept beside it, or the PRD could cite `test_x.py::test_name` instead of a line. Enhancement.

## Risks queued to next M

- **R4** `src/app/workflows/registry.py:446`. **A `-latest-v<N>` spelling that does move would now derive a fixed id.** The R3 fix treats a `v`-numbered version after `-latest` as naming one release. No such name exists in the served artifact today: I listed every `-latest` value in every table, and none is followed by `-v`. But "latest of v2" is a plausible upstream meaning, and that pointer moves. If one appears, its scores would attach to an id whose meaning drifts, which D-166 exists to prevent. Unlike an unmatched name, it would not show in `unmatched`. What would show it: an id matching `latest-v\d` in the refresh record's `derived` list.
