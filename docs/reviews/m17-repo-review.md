---
record_type: review
id: m17-repo-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-29
---
# M17 repo review -- the whole milestone, `cf00ec7...3f2e91d`

**Seat:** independent `/repo-review` across the whole of M17, as `docs/closure-checklist.md` §B.0
requires. I wrote none of M17's code, none of its reviews and none of its fixes.
**Independent:** yes
**Range:** `git diff cf00ec7...3f2e91d`, from the M17 plan's merge (PR #10) to the merge of the last
wave (PR #75). It covers waves W1 to W5 (#11 and #12, #23, #43, #62, #75) and the fix and
enhancement PRs #18, #19, #20, #21, #29, #30, #31, #34, #36, #46, #47, #49 and #65. That is 283 files,
+25,467/-6,649 lines.
**Grounded in:** `.agents/rules/practices.md`, `.agents/rules/issues.md`, seeds E.1, E.2, E.5 and
K.5 of `.agents/rules/playbook-seeds.md`, `AGENTS.md` §3.5 and §4, `docs/closure-checklist.md`,
`docs/wave-checklist.template.md`, and the M17 plan's definition of done
(`docs/plans/m17-plan.md` §4).
**Method:**
- I read the diff, every M17 ADR (D-159 to D-168), the wave closes for W2 to W5, the wave review
  records, the ledger rows M17 owns, and the documents a new reader is sent to.
- `make check-fast` passes on `3f2e91d` in this worktree: 6 of 6 legs in 81.8 s.
- I used `gh` read-only: the issue list, PR #11's body and merge time, the closing references of 16
  M17 PRs (all bug PRs are clean), and issues #16, #57 and #72.
- I changed nothing but this file.

**Not raised again:** #26, #33, #35, #38 to #42, #44, #45, #48, #51 to #61, #63 and #66 to #74 are
already filed. Where one of them is worse than filed, the finding below says so.

## Verdict

**PASS WITH FINDINGS. Nothing BLOCKING in the shipped code.** There are 21 findings: 16 defects
(M1 to M16) and 5 process findings (K1 to K5).
- M1 to M3 are correctness. Two were built across waves, and one is a privacy statement that the
  milestone corrected in one ADR and not in the others that say it.
- M4 to M16 are drift and duplicated knowledge.
- K1 is the one breach of the plan's definition of done: W1 was merged while its review was
  pending, and it has no close record.

## The definition of done (`docs/plans/m17-plan.md` §4), against what shipped

| DoD bullet | State | Evidence |
|---|---|---|
| `make check` exit 0 on the owner's machine | **not shown yet** | `note.txt:18` records only `check-fast`. In this worktree `make check-fast` passes on `3f2e91d`. The closure must cite the owner's `make check`. |
| Every wave close written at its close, citing a review dated after the code; no PR merged while its review or `/pre-merge` is pending | **not met for W1** | K1 |
| The HIGH waves (W4, W5) have their security pass before merge | **met** | `m17-wave-4-security.md` is dated 2026-09-25 and #62 merged on 2026-09-26. `m17-wave-5-security.md` is dated 2026-09-28 and #75 merged at 17:43 that day. K4 covers #65, which carried W4's HIGH slice with no security pass. |
| W-127 and W-128 end FIXED or ruled | **met** | `docs/warnings.ledger.md`: both are FIXED |
| The launchd job is retired, or the closure report says why not | **met, with a caveat** | The owner's comment on #16 (2026-09-24) records that `com.hcs.modelranking.refresh` was unloaded. #32 then installed a new launchd job, `com.ilgar.modelranking.engine`, with no ADR (M6), and the retired job's installer still ships (M5). The closure report should say both. |

## Defects

- **M1 (MAJOR): a board with a new metric takes `/v1/boards` down for every phone, and nothing
  before the route checks for it.** W2 and W3 declare boards and their metrics in the client
  modules. W4 keeps the direction of each metric as a separate hand-kept set. The two meet only at
  request time.
  - Where the metrics are declared: `src/app/workflows/sources.py:276-386` (`EpochBoard(... metric=)`),
    `src/app/clients/arena.py:41` and `:103`, `aider.py:24`, `swebench.py:21`, `deepswe.py:23` and
    `epoch.py:28`.
  - Where the direction is kept: `src/app/workflows/standings.py:34` (`HIGHER_IS_BETTER`).
  - What happens on a mismatch: `standings.py:93-95` raises for the whole payload, not for the one
    board, and `src/app/adapter/main.py:1415-1423` turns that into a 503 for every board. A
    benchmark that two surfaces rank at two efforts takes the same path (D-167 amendment).
  - What checks it: only the boot check and the per-request 503
    (`tests/unit/test_board_standings.py:177`, `:332`). No CI test derives the declared metrics and
    compares them with the set, and the refresh never builds the standings before it publishes.
  - The seed that applies is K.5: a data dictionary with consumers and no walker test.
  - #57 is worse than filed. Its impact line reads "Low: the bounds are runaway guards". The same
    publish path also carries this refusal, which a routine new board trips.
  - **Disposition:** fix now. Add a test that walks every declared board (`SOURCES`,
    `ARENA_SLICES`, the Epoch boards) and asserts its metric has a declared direction. Add a
    comment on #57 that the refresh's pre-publish check must run `board_standings`.

- **M2 (MINOR): the phone combines on standings of any age, and says nothing.**
  - `ios/ModelRanking/Engine/StandingsStore.swift:79-89` serves the last good payload after every
    failed fetch, with no upper age. `maxAge` (`:32`) only decides when to fetch again.
  - `ios/ModelRanking/ContentView.swift:786-787` records nothing about the failure or the age.
  - Behind M1's 503, a phone would keep showing a frozen combined list while its cards update.
  - #72 is worse than filed. It calls the missing stale warning "latent", because the boards in
    the 2026-09-28 artifact are recent. That measures the artifact, not the copy the phone keeps.
  - **Disposition:** file (bug), or widen #72. Either bound the age of the stored copy or disclose
    it on the combined list.

- **M3 (MAJOR): D-160's privacy clause is corrected only in a note under a later ADR, and three
  documents still state the original.**
  - `docs/decisions.md:3240-3244` (D-168 note 9) records that the routed surface leaves the
    device as `task`.
  - D-160's title and clause 1 (`docs/decisions.md:2771` and `:2783`) still say "nothing derived
    from the question leaves the device", with no pointer to the note.
  - The same wording stands in `docs/plans/m17-plan.md:97-98` and on the first page of the W5 close,
    `docs/plans/m17-wave-5-close.md:23`. Row 4 of that same close says the opposite: "nothing
    beyond the surface id".
  - This breaks two rules: "update the canonical file AND every cached pointer"
    (`.agents/rules/practices.md:189`), and "the old ADR ... is marked"
    (`.agents/rules/practices.md:184`).
  - **Disposition:** fix now. Append an amendment line under D-160 that points at D-168 note 9,
    leaving D-160's body untouched, and correct the wording in the W5 close and the plan.

- **M4 (MINOR): branch protection is on, but the project brief does not say so, so
  `make bootstrap-check` C11 fails in any clone without `make hooks`.**
  - The D-161 amendment (`docs/decisions.md:2902`) said C11 fails "until `main` is protected and
    the brief says so (issue #13)".
  - #31 closed #13 but touched only `docs/branch-protection.md`.
  - `docs/project-brief.md` has neither field that `scripts/bootstrap-check.sh:333-334` reads
    ("GitHub Actions run here", "The default branch can be protected"). Its row at `:53` still
    reads "branch protection | owner | proposed".
  - In this worktree `core.hooksPath` is unset, so C11 takes its fail branch
    (`scripts/bootstrap-check.sh:353-354`).
  - **Disposition:** fix now. Record both answers in the brief, as
    `docs/branch-protection.md:35-37` instructs.

- **M5 (MINOR): the retired refresher can still be installed, and it would run the development
  checkout.**
  - The owner retired the launchd refresher under #16, and #32 replaced it with a service that
    runs a deployed release.
  - `scripts/enable_refresh.sh:14-15`, `scripts/install_refresh_wrapper.sh:14-15`,
    `scripts/refresh_job.sh` and `deploy/com.hcs.modelranking.refresh.plist` all still ship. They
    install a second nightly refresher that runs the checkout on the Desktop, which is the hazard
    that `docs/reviews/issue-32-review.md` B2 closed. Only the shared `flock` keeps the two apart.
  - `scripts/README.md` lists neither the three new service scripts nor the retired ones. Its own
    rule says a project script is "reached through a `make` target".
  - The rule that applies is "Prune stale docs that contradict current decisions"
    (`.agents/rules/practices.md:200`).
  - **Disposition:** file (enhancement). Retire the installer, or make it refuse while
    `com.ilgar.modelranking.engine` is loaded. List the service scripts.

- **M6 (MINOR): running the engine as a launchd service has no ADR, and D-154 describes the old
  launcher.**
  - #32's shape is: the service runs a deployed `origin/main` release with its own venv,
    `KeepAlive`, rollback, and `APP_ENV=test` with a strict preflight. It was an owner ruling
    recorded only in a script header (`scripts/install_engine_service.sh:10-17`) and an issue
    comment.
  - D-154 clause 2 (`docs/decisions.md:2376`) still says `ios/app.sh` sets
    `MODEL_RANKING_REFRESH=nightly`. It is set in `scripts/engine_service.sh:71` now.
  - The revisit triggers of D-116 and D-149 were not read again.
  - D-154 is also one of #33's "still proposed" ADRs.
  - The rule that applies is "Capture every assumption as an ADR" (`.agents/rules/practices.md:183`).
  - **Disposition:** fix now with `/log-decision`. The ADR records #32's ruling and amends D-154
    clause 2.

- **M7 (MINOR): 33 of the 63 boards published are ones no question can select.**
  - I measured this on this worktree's `advisor.db`. `board_standings` serves 63 boards. The
    refinement table (`ios/ModelRanking/Engine/Refinements.swift`, 16 boards) and the 14 primary
    boards together make 30 selectable boards.
  - The other 33 cannot be selected. They include every vision slice, `arena_text_creative_writing`,
    `arena_text_instruction_following`, `arena_text_multi_turn`, `arena_text_hard_prompts`, all six
    agent boards and seven Epoch boards.
  - They still cost the phone's daily download, the nightly board guards (D-164's cost: "A glitch
    on one thin board can now hold back a night's publish", `docs/decisions.md:3006`) and the
    parquet reader.
  - The plan named several of them as boards "a combination can use" (`docs/plans/m17-plan.md:63-65`).
  - D-168 clause 5 (`docs/decisions.md:3178`, #53) rules on `epoch_swe_bench_verified` being
    counted twice, but that board cannot be selected.
  - **Disposition:** file (enhancement). Either publish and guard only the boards a question can
    reach, or state in the closure report why the rest stay.

- **M8 (MINOR): W3's accessibility attribute reaches the phone and nothing uses it.**
  - The plan read `model_metadata.csv` "as a FILTER ... open weights, commercial use"
    (`docs/plans/m17-plan.md:71`), and W5's intent was to carry "constraints"
    (`docs/plans/m17-plan.md:85`).
  - W3 built the `access` table and W4 serves it on `/v1/boards`. The phone decodes it at
    `ios/ModelRanking/Engine/Models.swift:380`, and no Swift file reads it.
  - D-168 replaced the intent schema and does not say that the filter was dropped.
  - **Disposition:** file (enhancement, for M18), and record the deferral in the closure report.

- **M9 (MINOR): the contract-test rule was applied to Arena's new files and not to Epoch's.**
  - Rule: "One canonical mock per integration + a contract test" (`.agents/rules/practices.md:44`).
  - W2 and W3 added live checks for every Arena parquet config (`docs/skip-budget.txt:19-22`).
  - W3's five Epoch boards and `model_metadata.csv` are tested only with fixtures, for example
    `tests/unit/test_access.py:116`. `tests/integration/` has no Epoch test, and the skip budget's
    Epoch line stays at 7.
  - Since D-158 the Epoch bundle is a nightly network fetch. The seven-value vocabulary at
    `tests/unit/test_access.py:29` is held only against a fixture.
  - **Disposition:** file (enhancement): a contract test over every declared Epoch board and the
    metadata file.

- **M10 (MINOR): four ledger rows owned by M17 were never worked, and two of their premises
  changed during the milestone.**
  - W-125, W-126, W-130 and W-131 (`docs/warnings.ledger.md:179`, `:180`, `:184`, `:185`) name
    M17 as their owner. No wave took them, and none was given a new owner.
  - W-125 grew. `src/app/workflows/rank.py:19` now loads `app.clients.arena_slices` into the
    serving process, and with it `parquet_reader`, the fetcher that starts a child process.
    Measured: `import app.adapter.main` loads both.
  - W-130's premise, "Not reachable today, because `refresh.py` starts no subprocess", has been
    false since D-165. The cycle now starts a reader at `src/app/clients/arena_slices.py:293`, and
    no M17 record mentions W-130.
  - W-131 says "the closure checklist asks for it every milestone". The D-161 amendment retired
    that seat.
  - **Disposition:** fix now at closure. Measure each row again and give it a new owner with its
    reason.

- **M11 (MINOR): the PRD has no requirement for anything M17 built.**
  - There is no REQ row for the Arena slices, the Epoch and agent boards, accessibility, moving
    aliases, `/v1/boards`, the combination, refinements or the engine service. `docs/prd.md` ends
    with the M16 section at `:535`.
  - REQ-API-001's status names `/v1/budgets` and not `/v1/boards`.
  - M8 to M16 each added a section "at W1" or "at the wave". M17's tests cite D-IDs and issues
    only, and `tests/unit/test_prd_status.py` (#28) grades only the rows that exist.
  - **Disposition:** fix now at closure. Add an M17 section with a status for each row.

- **M12 (MINOR): `docs/architecture.md` was last changed in M6, and `AGENTS.md` §1 still describes
  the M1 product.**
  - `git log -- docs/architecture.md` ends at `164d79f` (M6-W3). The diagram has no iOS app, no
    `/v1`, no nightly refresh, no engine service and no on-device combination, and its §4 still
    reads "M1: no deploy".
  - `AGENTS.md:14-17` still says "FastAPI (health-only until M6)" and "a future iOS AI-advisor
    app", and gives a REQ prefix list without APP, REF, RTR or FLR.
  - `AGENTS.md:19` sends readers to the architecture document "for deployment topology".
  - **Disposition:** file (documentation).

- **M13 (MINOR): `docs/branch-protection.md`, "the single list", no longer describes `main`, and
  D-161's owner part has no issue.**
  - `docs/branch-protection.md:49` records `strict` on. It was turned off at the owner's request
    (`docs/process-log.md:562`, `note.txt:4-5`).
  - It still requires `governance-contract` (`:48`). D-161 clause 4 (`docs/decisions.md:2850`)
    said that requirement goes once the owner applies the proposed workflow change. That change
    has no issue, only the body of the merged #18.
  - `.github/workflows/issue-agent.yml:9` still cites `METHODOLOGY.md`, which v6.4 deleted.
  - Turning `strict` off relaxes a control, and it was done without the named judgement that
    `docs/closure-checklist.md:184-190` asks for and without a `docs/control-events.csv` row.
  - **Disposition:** fix now for the document. File the owner's workflow part. Workflows are not
    the agent's to edit.

- **M14 (MINOR): `note.txt` is a second copy of the session state, and it has drifted.**
  - `note.txt:18` says "main at c02fe0d"; `main` is now `3f2e91d`.
  - `note.txt:6` says W5 is a "draft PR"; it merged as #75.
  - `note.txt:13` says #66 and #73 come "before M17 closes"; the owner moved both to M18.
  - `note.txt:24` says "W1 done, W2 next".
  - `note.txt:26` lists W-123 to W-129 and misses W-130 to W-133. `:25` sends a new agent to a
    handover written on 2026-09-21.
  - `/start-session` reads `docs/process-log.md`, not `note.txt`. The rule is "Session state lives
    in `docs/process-log.md` ... no separate handover files" (`.agents/rules/practices.md:187`).
  - **Disposition:** fix now at closure. Then decide whether to retire the file, or record that it
    stays in `docs/refusals.md`.

- **M15 (MINOR): the M17 plan was never reconciled with what shipped.**
  - It is still `status: draft` and `process_version: v6.0` (`docs/plans/m17-plan.md:4-5`).
  - Its W5 line lists "Stage 4.0 security seat, closure report, retrospective"
    (`docs/plans/m17-plan.md:87-88`). The D-161 amendment (`docs/decisions.md:2868`) retired the
    per-milestone security seat, and `.agents/rules/practices.md:187` retired the per-milestone
    retrospective.
  - W5's intent schema was superseded by D-168 (see M8).
  - The cap was "~2k net lines" (`docs/plans/m17-plan.md:17`). Product code in `src/`,
    `ios/ModelRanking/` and the engine scripts came to +3,225/-330, and W3, "the one to drop", was
    kept.
  - **Disposition:** fix now at closure. The closure report walks `docs/closure-checklist.md` §B
    rather than the plan's list, and states the overrun.

- **M16 (NIT): `scripts/calibrate_board.py` still prints a retired floor as "the floor the
  product SHIPS".**
  - `scripts/calibrate_board.py:225-237` computes the D-145 distinct-model third under that label.
    Since D-148 and D-159, the floor that ships is the third of every row, from
    `app.workflows.floors`.
  - The docstring at `:75` still cites the 1400 floor.
  - Two private copies of the quantile remain (`:83`, `:237`), beside D-159 clause 2's "one
    function" promise.
  - **Disposition:** fix now. Call `floors.top_third` and correct the label.

## Process

- **K1: W1 was merged under its own "Review pending, do not merge" line, and it has no close
  record.**
  - PR #11's body opens "**Review pending, do not merge.**" It merged at 2026-09-23T12:18Z.
  - Its review, which was BLOCKING (`docs/reviews/m17-wave-1-review.md:64-66`), was first
    committed four minutes later in `9cf2b0d`. BLOCKING-1 was fixed in #12, merged on 2026-09-24
    at 00:48.
  - There is no `m17-wave-1-close` record in `docs/plans/`, and no process-log entry between
    `docs/process-log.md:455` and `:466`.
  - This breaks DoD bullet 2, `docs/closure-checklist.md` §B.0 and
    `.agents/rules/practices.md:147` and `:181`.
  - **Disposition:** fix now in the closure report, which states it. The ledger rule "never
    reconstructed later" means no row is back-filled.

- **K2: `make wave-check-all` cannot see a wave that has no close.**
  - `scripts/wave_check_all.py:48` globs the closes that exist, so W1's gap passed every gate,
    this worktree's `make check-fast` included.
  - The list of expected waves is already in the plan's `### W<n>` headings.
  - The rule that applies is `AGENTS.md` §3.5, derive, don't enumerate.
  - **Disposition:** file (enhancement, control). Derive the expected closes from the plan, and
    fail on a missing one.

- **K3: the auto-HIGH rule for input parsing was applied in neither W2 nor W3, and the two waves
  were treated differently.**
  - `docs/wave-checklist.template.md:33` makes a wave HIGH automatically when its diff touches
    input parsing. W2 and W3 both parse untrusted downloads, and the plan tagged both MED.
  - W2 still got four security rounds, three of them BLOCKING.
  - W3 added parsers for `model_metadata.csv`, five Epoch boards and a second parquet value
    column. It folded its security look into the Code-Reviewer's brief and scoped it to the
    reader's column map (`docs/plans/m17-wave-3-close.md:26`). #42 came from that surface.
  - **Disposition:** file (enhancement): make the plan's risk tag follow the template's
    auto-HIGH list.

- **K4: #65 brought back W4's HIGH slice through `/fix-issue`, and only the Tester reviewed it.**
  - The plan says itself "Risk: HIGH, inherited from W4" (`docs/plans/issue-61-plan.md:12`), and
    `AGENTS.md` §5 says a fix inherits the risk class of the bug it fixes. No Code-Reviewer or
    security seat read the restored `Combine.swift` or its arithmetic permission before the merge.
    W5's security seat later found #74 in that code.
  - The W4 close marks security S7 as fixed (`docs/plans/m17-wave-4-close.md:28`), but only its
    duplicate-row half was. The quadratic half was neither fixed nor filed until it came back as
    #74.
  - `docs/plans/issue-61-plan.md` (draft) stayed on `main`, while every wave plan was deleted at
    close "as DevFlow requires".
  - **Disposition:** fix now in the closure report. Name the lane rule in the M18 plan.

- **K5: three documents give two answers about per-wave security.**
  - `AGENTS.md:76` says the security review is "never per wave", and `AGENTS.md:77` says a HIGH
    wave "also gets a security pass on its slice".
  - The D-161 amendment (`docs/decisions.md:2868`) says "the security review runs once, at
    Stage 5.1".
  - The M17 DoD requires a pass for each HIGH wave.
  - The text is DevFlow's.
  - **Disposition:** file as a DevFlow field finding (hand-back), and state this project's rule in
    one place.
