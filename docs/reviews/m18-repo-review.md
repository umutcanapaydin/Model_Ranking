---
record_type: review
id: m18-repo-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# M18 repo review -- the whole milestone, `159ec9e...a259ed0`

**Seat:** independent `/repo-review` across the whole of M18, as `docs/closure-checklist.md` §B.0
requires. I wrote none of M18's code, none of its reviews and none of its fixes.
**Independent:** yes
**Range:** `git diff 159ec9e...a259ed0`. `159ec9e` is the M17 closure merge on `main`. `a259ed0` is
the head of W7. The range holds all seven waves:
- W1, W4, W5 and W2 are merged on `main`: #99, #109, #111 and #116 (`main` is at `d8093e8`).
- W3 (#134), W6 (#135) and W7 (#136) are draft PRs, stacked in that order.

That is 250 files, +57,868/-1,114 lines. About 36,000 of them are W3's probe run files and 2,600
are W6's generated locks.
**Grounded in:** `.agents/rules/practices.md`, `.agents/rules/issues.md`, seeds B.2, E.1, E.5, G.1,
K.5 and L.8 of `.agents/rules/playbook-seeds.md`, `AGENTS.md` §3.4, §3.5, §4 and §5, the M18 plan
(`docs/plans/m18-plan.md`) with its amendments, D-169 as amended and D-170 to D-177, the seven wave
closes, `docs/security-invariants.md`, and the documents a new reader is sent to (`README.md`,
`AGENTS.md`, `docs/architecture.md`).
**Method:**
- I read the diff by area (adapter, refresh, nightly, clients, the Swift Engine layer and
  `ContentView.swift`, the scripts, the build files, the records). I read every M18 ADR, the plan and
  its amendments, the seven close records, and skimmed the wave reviews for what they found.
- `make check-fast` passes on `a259ed0` in this worktree: 6 of 6 legs in 129.5 s. It runs no live
  contract test and no skip budget, so it cannot see M1 or M2.
- I used `gh` read-only: the open issue list; the closing references of the seven M18 PRs (every bug
  PR is clean); the CI checks of #134, #135 and #136 and the failed logs of the two runs on `a259ed0`;
  the events and last comments of eight closed M18 bugs; the triage verdicts of 21 issues M18 filed
  (all present).
- I read `pip_audit/_dependency_source/pyproject.py` in this worktree's venv to see what `make deps`
  audits.
- No simulator, no installer, no network from a test. I changed nothing but this file.

**Not raised again:** #60, #66, #81, #85, #88, #94, #100, #101, #105, #106, #107, #108, #110, #112,
#113, #115, #117, #119, #122, #124 to #133 are already filed. Where one of them is worse than filed,
the finding says so.

## Verdict

**PASS WITH FINDINGS.** There are 17 findings: 13 defects and 4 improvements.
- **M1 and M2 are correctness, and both turn W7's PR red today.** CI on `a259ed0` fails two ways.
  W7's network guard stops every live contract test, W4's new Epoch contract tests among them. And
  W7's one new artifact test puts CI over its skip budget. Neither is in W7's close record.
- M3 is a control that lost its scope when W6 moved pyarrow to an extra.
- M5 to M14 are drift between waves: one fact changed in one wave and not in the next.
- M15 to M17 are process. M18 wrote no process-log entry at all.

## The plan's criteria (`docs/plans/m18-plan.md` §1 and its amendments), against what shipped

| Wave | Criterion | State | Evidence |
|---|---|---|---|
| W1 | The app runs on the owner's iPhone, by opt-in; an exposed engine refuses a foreign Host | **met, except the owner's own run** | REQ-DEV-001 is PARTIAL (`docs/prd.md:588`); the steps are `docs/owner-iphone.md` |
| W2 | #63 reproduced and fixed or ruled; a committed UI test drives the screen | **met** | D-175; `make ui-test` runs locally only, by design |
| W3 | Not-a-search input and coding questions read better than the baseline, by the bar set after it | **met for #73 only** | #66 missed its catch bar; #113 missed both bars (D-169 amendment, `docs/decisions.md:3380-3392`). PR #134 asks the owner |
| W4 | Every engine and data bug filed is fixed red first or ruled | **met** | 11 issues; #74 and #56 moved to W2 and were done there |
| W5 | Every gate gap filed is closed with a gate shown red | **met for its scope** | #60 and #85 moved to W6, then to M19 (plan amendments) |
| W6 | One invariants list with a negative test per row | **not fully met** | INV-66 has no test (gap G-1, #85) and six rows hold in part (`docs/security-invariants.md:160-161`) |
| W6 | The licences are ruled | **not met** | the table is written; the ruling is the owner's (#88, open) |
| W6 | W-125, W-126, W-130 re-measured; a stranger's first use has a protocol | **met** | `docs/warnings.ledger.md:179-185`; `docs/research/stranger-first-use-protocol.md` |
| W7 | The open backlog the amendment names | **10 of 13 delivered, 3 in part** | but its PR is red in CI: M1, M2 |

## Correctness

- **M1 -- defect, MAJOR: W7's network guard stops every live contract test, and W4's Epoch contract
  tests with them.**
  - W7 (#122) blocks the network for the whole suite in `tests/conftest.py`. Its comment says "the
    one way out is a live contract test (`tests/integration`, with `RUN_CONTRACT_TESTS=1`)".
  - The way out does not work. The lift is a `threading.local()` (`tests/conftest.py:57`), set by a
    function-scoped autouse fixture (`:125`). Every source fetch runs on a worker thread
    (`src/app/clients/protocols.py:163`, the deadline design of #29 and #71), which never sees the
    lift. W4's Epoch contract fixture is module-scoped (`tests/integration/test_epoch_bundle_contract.py:22`),
    so it fetches before the function fixture runs at all.
  - Measured in CI on `a259ed0` (run 37240354469, job `live-contracts`): 16 failed, 9 passed, 2
    errors. The errors are W4's two Epoch contract tests (#79), at setup:
    `NetworkReachedError: a unit test looked up 'epoch.ai' (#122)`.
  - Once W7 merges, the weekly contract run is red every Monday, and source drift can no longer be
    told from the guard. This is the seed L.8 failure: configured is not working. No seat could see
    it, because no seat runs with the network.
  - **Fix belongs:** on W7's branch (#136), before it merges. Make the lift process-wide and set it
    before any fixture runs (for example in `pytest_configure`, when `RUN_CONTRACT_TESTS=1`). Add an
    offline test that a lifted check passes on another thread and inside a module-scoped fixture.

- **M2 -- defect: W7's PR is over CI's skip budget, the same miss W2 made and fixed.**
  - W7 adds one artifact test (`tests/unit/test_display_names.py:86`). It skips where there is no
    `advisor.db`, as in CI.
  - `docs/skip-budget.txt` still says 77. CI on `a259ed0` (run 37240354477, both `test` jobs):
    "78 test(s) skipped of 1791, budget is 77".
  - W2 hit the same failure on #116 and recorded it with its fix (`docs/plans/m18-wave-2-close.md:49`).
    W7's close (`docs/plans/m18-wave-7-close.md:47`) says "gates SKIPPED: none". The close commit is
    the commit CI ran on, so the close could not know. Nothing since records it.
  - The budget is a hand-kept number checked only in CI. `make check-fast` cannot see it, because the
    owner's Mac has the artifact. Twice in one milestone a PR opened red on it.
  - **Fix belongs:** on W7's branch: raise the budget to 78 with its reason, as W2 did. Then file an
    enhancement: a local check that derives the expected skips from the markers (`artifact`, the
    contract gate, the Epoch directory, Xcode) and compares them with the budget (`AGENTS.md:64`,
    derive, don't enumerate).

- **M3 -- defect: since W6, no gate the agent owns audits pyarrow, the library that parses untrusted
  downloads.**
  - W6 (#26) moved pyarrow from `[project].dependencies` to the `ingest` extra
    (`pyproject.toml:31-32`).
  - `make deps` runs `pip_audit --strict .` (`Makefile:254-255`). pip-audit reads only
    `project.dependencies` from a `pyproject.toml` (`pip_audit/_dependency_source/pyproject.py:73`).
    So pyarrow left the audit in the same change that moved it.
  - INV-80 says "Declared dependencies have no known advisory" and cites `make deps`
    (`docs/security-invariants.md:152`). The slopsquat half reads every extra; the advisory half does
    not.
  - The locks pin every version that deploys, so an advisory against a pinned pyarrow would now be
    noticed by nobody. D-177's own revisit trigger ("a dependency must be upgraded for a security
    advisory") then never fires.
  - The W6 review's K1 caught the CI half, and it is in the owner's patch on #81. The `Makefile` half is
    the agent's, and it was not changed.
  - **Fix belongs:** a fix PR, or W6's branch (#135): `make deps` audits the locks
    (`pip-audit --require-hashes -r requirements/serve.lock -r requirements/ingest.lock`), and INV-80
    cites that. The closure security seat may weigh this too.

- **M4 -- improvement: the engine and the phone now decide "the same model" by two different rules.**
  - W7 (#102) made the engine decide that a pick is the leader by its row, because display names are
    not unique (`src/app/workflows/recommend.py`, `value is quality`).
  - W2 (#63 finding 1) merges picks into one card when display name, vendor, score and price are all
    equal (`ios/ModelRanking/Engine/AnswerPlan.swift:185-188`). `/v1` picks carry no model id, so the
    phone cannot follow the engine's rule. The merged card shows only the lead pick's trade-off.
  - A collision needs all four values equal, so it is unlikely today. #129 (one release served under
    two ids) is the case where the name and the vendor already match.
  - **Fix belongs:** file an enhancement: serve a pick's model id (an additive `/v1` field, under an
    ADR), and key the cards on it.

## Drift and duplicated knowledge

- **M5 -- defect: `docs/architecture.md` describes the code "after M18-W4", and four waves changed it
  since.**
  - W5 (#80) rewrote it (`docs/architecture.md:3-4`). W6 then updated `AGENTS.md` §1 for its locks, but
    not this file.
  - It lists as open what M18 closed: W-125 at `:441` and `:461`, W-131 at `:462`, #35 at `:463`, and
    #66 and #73 as future M18-W3 work at `:464`.
  - It says the refresh "is killed after 30 minutes" (`:152`). W6 added a 20-minute fetch budget, a
    27-minute kernel limit and a process-group kill (D-154 as amended).
  - It describes the client as a 10-second ephemeral session (`:227`), with no streamed read and no
    per-route ceiling (#56, W2). It says the model's schema has surface, language and domain (`:208`),
    and that unmeasured questions go to the gap register (`:218`). W3 added the closed `request`
    verdict, the code signals, the note and the question back, and keeps only searches.
  - It has no accessibility filter (#78) and no `Notices.swift` (D-176).
  - The rule is "Prune stale docs that contradict current decisions" (`.agents/rules/practices.md:200`).
  - **Fix belongs:** the closure PR, rewriting the affected sections in place. If it does not fit
    there, file it as documentation.

- **M6 -- defect: W4 marked every ADR it amended; W1, W2, W3, W6 and the D-172 ruling did not.**
  - W4 appended "Amended by D-173" under D-128, D-132, D-154, D-166 and D-167.
  - D-170 is amended by D-171 and D-177 and carries no pointer. Its clause 1 still says "bound to
    127.0.0.1:8080" (`docs/decisions.md:3407-3408`), and its cost still says "The installer installs
    from PyPI without a lock (#35)" (`:3420`).
  - D-116 is amended by D-177, and has no pointer.
  - D-161 still says "the per-milestone security seat [is] retired" (`docs/decisions.md:2905`). D-172
    brought that seat back, and D-161 does not point to it.
  - D-126's closed set (amended by D-169) and D-136's recorded English remainder (ended by D-176) carry
    no pointer either.
  - This breaks "Supersede, never edit ... the old ADR ... is marked" (`.agents/rules/practices.md:184`,
    seed B.2) and "update the canonical file AND every cached pointer" (`:189`). The M17 review's M3 was
    the same defect on D-160.
  - **Fix belongs:** the closure PR: one dated pointer line under each of the five, bodies untouched.

- **M7 -- defect: the PRD lags `/v1` and one reader feature.**
  - REQ-API-001 (`docs/prd.md:377`) still names `/v1/budgets` as the latest route. It does not name
    `/v1/boards`, which the M17 review's M11 already said. M18 re-pointed the row's two line numbers
    and left its text as it was.
  - The plan named REQ-API-001 for W4 (`docs/plans/m18-plan.md:33`). W4 changed the route (built once
    per artifact, gzip on every route, D-173 clause 5), and W2 added three fields (D-176). The row
    says none of it.
  - No REQ row states the reader's filter "Only models with an API or open weights" (#78, D-175). So
    the citing-test rule (`.agents/rules/practices.md:38-40`) cannot reach it, and no coverage trace
    shows it.
  - **Fix belongs:** the closure PR: restate REQ-API-001's status with its evidence, and add one row
    for the filter, citing its tests.

- **M8 -- defect: two ledger rows still name a milestone that is over.**
  - W-123 (`docs/warnings.ledger.md:177`) is ACCEPTED, owned by M18, and no M18 record touches it. W3
    measured the nearest thing ("knowledge questions are the gap, 1 of 10") and W6 wrote its protocol
    (#91). REQ-RTR-005 and REQ-ASK-003 still say "owned by M18" (`docs/prd.md:460`, `:523`).
  - W-129 (`docs/warnings.ledger.md:183`) still says "Owning milestone: M17". W6 wrote its licence table
    (#88), and the row does not say so.
  - The M17 review's M10 was the same pattern.
  - **Fix belongs:** the closure PR: measure each again, or give it a new owner with its reason.

- **M9 -- defect: W3's close says W6's list holds W3's invariants, and it holds half of them.**
  - `docs/plans/m18-wave-3-close.md:43` names four invariants and says "W6's
    `docs/security-invariants.md` lists them".
  - The verdict test and the enum pin are in INV-69. The held-out gate
    (`tests/unit/test_ios_client_contract.py:165`) and the tracked-link refusal
    (`tests/unit/test_no_tracked_links.py:21`) are rows nowhere. The second came from a BLOCKING review
    finding (the committed `.venv` link).
  - The gap count is told three ways: "six named gaps" (`docs/warnings.ledger.md:185`), "Five gaps"
    (`docs/plans/m18-wave-6-close.md:29`), and four in the list today.
  - **Fix belongs:** the closure PR: add a row for the tracked-link refusal, decide in one line whether
    the held-out gate is a security invariant, and correct W3's sentence.

- **M10 -- defect: D-174 and D-175 disagree for a screen wave's Tester, and the waves settled it in
  prose.**
  - D-174 clause 3 puts every seat behind stubs that refuse `simctl` and `xcodebuild`
    (`docs/decisions.md:3606`).
  - D-175 clause 2 asks a screen-changing wave to cite a `make ui-test` run (`:3640`), and that run
    needs both.
  - W2's Tester "was allowed the simulator" (`docs/plans/m18-wave-2-close.md:40`), and W3's first
    Tester ran it (`docs/plans/m18-wave-3-close.md:39`). D-174 was in force for both: W5 merged it
    before W2 began.
  - **Fix belongs:** the closure PR: an amendment to D-174 clause 3 that names the exception (a screen
    wave's Tester may run `make ui-test`, never the installer or `launchctl`).

- **M11 -- improvement: `make ui-test` defaults to the checkout's artifact, which D-174 found stale.**
  - `scripts/ui_test.sh:14` copies `$REPO/advisor.db` unless `MODEL_RANKING_DB` is set.
  - D-175 clause 2 says the engine starts "from a copy of the served artifact" (`docs/decisions.md:3636`).
  - W7's amendment to D-174 (`:3614-3619`) records that the owner's checkout holds a copy from
    2026-09-24, before the refinement boards, and that a test fails on it.
  - So the owner's own `make ui-test` would drive the combined list on boards the phone no longer gets.
  - **Fix belongs:** file an enhancement: default to the service's artifact
    (`~/Library/Application Support/model-ranking/engine/data/advisor.db`) when it exists, or refuse an
    artifact without the refinement boards.

- **M12 -- defect: the milestone plan was never reconciled with what ran.**
  - It is still `status: draft` (`docs/plans/m18-plan.md:4`), and it says "Six waves" (`:21`).
  - W7 exists only as an amendment paragraph (`:240-243`), with no `### W7` heading.
  - W2, W4 and W5 are headed MED (`:54`, `:89`, `:106`), and §3 lists three HIGH waves (`:137`). All
    seven waves ran HIGH. Only W2's amendment says so; W4's and W5's reasons were in wave plans that
    were deleted.
  - The amendments are not in date order: D-172's, dated 2026-09-29, sits after three of 2026-10-04.
  - The M17 review's M15 was the same finding on the M17 plan.
  - **Fix belongs:** the closure PR: a `### W7` heading, the tiers as run, and a closing status.

- **M13 -- improvement: the two M18 wave gates read less than the plan says.**
  - #82's check counts a milestone's waves from its `### W<n>` headings
    (`scripts/wave_check_all.py:63`, `:95`). W7 has no heading (M12), so the check cannot require
    W7's close. W7's close exists, so nothing is missing today; the next wave added by amendment is
    invisible.
  - #83's HIGH rule reads one glob, `src/app/clients` (`scripts/wave_check.py:369`). The plan lists
    seven security globs (`docs/plans/m18-plan.md:139-146`), and `AGENTS.md:77` gives a third,
    shorter list of auto-HIGH areas. A MED wave that touches `src/app/adapter/main.py` or
    `EngineClient.swift` passes.
  - The rule is `AGENTS.md:64`: a control whose scope is a hand-kept list beside the thing it guards
    is a finding.
  - **Fix belongs:** file an enhancement: count waves from amendments too (or require a heading for
    each), and have the HIGH rule read the plan's own glob list.

- **M14 -- improvement: the GitHub milestone does not match the plan's amendments.**
  - #107 and #110 moved to M19 by amendment (`docs/plans/m18-plan.md:230-233`) and still carry the M18
    milestone. #60 and #85 moved the same way and carry none.
  - #94, #100, #101, #106 and #108 were filed during M18, are in no wave, and carry the M18 milestone.
  - Closing the milestone as it stands would drop them from the M19 plan, which `/plan-milestone`
    builds from the open queue.
  - **Fix belongs:** the closure: move each to M19, or name it in the closure report.

## Process

- **M15 -- defect: M18 wrote no process-log entry, and `note.txt` drifted again.**
  - The last entry is "2026-09-28/29 -- M17 closed" (`docs/process-log.md:584`). Seven waves ran from
    2026-09-29 to 2026-10-05 with no entry. Each M17 wave close wrote one.
  - `/start-session` and `make standup` read this file, so a new session starts from the M17 closure.
  - `note.txt` still says "Talk to him in Turkish" (`note.txt:4`), though the owner switched to
    English on 2026-10-04. It still points at the M17 closure branch (`:7`) and says "Next: M18"
    (`:14`). The M17 review's M14 asked to retire this second copy of the session state.
  - The rules are "process-log per session" (`.agents/rules/practices.md:181-182`, seed G.1) and
    "Session state lives in `docs/process-log.md`" (`:187`).
  - **Fix belongs:** the closure PR: the M18 entries, from the close records, and a decision on
    `note.txt` (retire it, or record in `docs/refusals.md` why it stays).

- **M16 -- defect: four bypasses are written in prose and none in `docs/control-events.csv`.**
  - The ledger has no M18 row. `AGENTS.md:105` makes it "the only ledger a gate counts".
  - W5 pushed `90ead9d` with `make check-fast` red (`docs/plans/m18-wave-5-close.md:38`).
  - W7 amended the pushed merge `58e8bf4` and force-pushed it (`docs/plans/m18-wave-7-close.md:43`),
    against `AGENTS.md:40` ("never force-pushes, never `--amend`s anything pushed").
  - W2's and W3's Testers ran the simulator outside D-174 clause 3 (M10).
  - Thirteen merged bugs were closed on 2026-10-04 "on the owner's instruction", with `dev:done` and
    no `qa:passed` (for example #67 and #86). `.agents/rules/issues.md:65-85` says a bug closes only
    after a verifier's `qa:passed`. The owner may waive it, but the waiver is in issue comments only.
    If it is now his standing rule, `issues.md` still says the opposite.
  - **Fix belongs:** the closure PR: one row each. If the bug-closing rule changed, record it where
    `issues.md` is read.

- **M17 -- defect: two of the milestone's ADRs were written with or after their code.**
  - The plan allows `/v1` fields only "under an ADR written before the wave that serves them"
    (`docs/plans/m18-plan.md:169-170`).
  - D-176 first appears in W2's feature commit `88e0ea3`, the same commit that serves
    `close_call_fact`.
  - D-177 first appears in W6's review-fix commit `4f6d025`. W6's locks, its `Dockerfile` change and
    its new install path shipped in `d894ab5` with no ADR, until the review's M7 asked for one
    (`docs/reviews/m18-wave-6-review.md:205-225`).
  - W1 (`f52cb9e`), W4 (`faf3242`) and W2's D-175 (`1c72725`) wrote theirs in the plan commit, as the
    rule asks ("Open the capture file BEFORE the work starts", `.agents/rules/practices.md:180`; seed
    B.1).
  - **Fix belongs:** state it in the closure report. No gate is proposed: an ADR's timing is cheap to
    keep by hand once it is named.

## Dispositions, at the closure

Written by the lead agent after the seat closed, not by the seat. Each finding is fixed, filed, or
stated, and none is left in this file alone (`docs/closure-checklist.md` §B.0).

| finding | disposition |
|---|---|
| M1 | fixed on W7's branch, `d749403`; CI on #136 green, `live-contracts` included |
| M2 | fixed `d749403` (the budget is 78, with its reason); the local check is #137 |
| M3 | fixed `c256864`: `make deps` audits the locks; the closure security seat's S1 is the same |
| M4 | #138 |
| M5 | fixed `c256864` |
| M6 | fixed `c256864` |
| M7 | fixed `c256864` |
| M8 | fixed `c256864`: W-123 to M19 with #66, W-129 to the first public release with #88 |
| M9 | fixed `c256864`: INV-84; the held-out gate is stated not to be a security row |
| M10 | fixed `c256864`: D-174 amended |
| M11 | #139 |
| M12 | fixed `c256864` |
| M13 | #140 |
| M14 | done on GitHub on 2026-10-05: #94, #100, #101, #106, #107, #108 and #110 no longer carry the M18 milestone, so the M19 plan reads them from the open queue; #60 and #85 carried none |
| M15 | fixed: the process-log entry is `361ba16`; `note.txt` retired in `c256864` |
| M16 | fixed `c256864`: five rows in `docs/control-events.csv`, and D-178 for the owner's bug-closing rule |
| M17 | stated in `docs/EXPERIENCE.md`'s M18 entry and the closure pull request. There is no closure report: the Quality Gate is off, and the plan writes one only when it is on |
