---
record_type: review
id: m19-repo-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-07
---
# M19 repo review -- the whole milestone, `119b885...bd6213a`

**Seat:** independent `/repo-review` across the whole of M19, as `docs/closure-checklist.md` §B.0
requires. I wrote none of M19's code, tests, reviews or fixes.
**Independent:** yes
**Range:** `git diff 119b885...bd6213a`. `119b885` is the M18 closure merge on `main` (#148). `bd6213a`
is the head of W5. The range holds all five waves:
- W1 (#167), W2 (#176) and W3 (#184) are merged on `main` (`main` is at `3426ff3`).
- W4 (#196) and W5 (#197) are draft PRs; W5 carries W4's commits.

That is 263 files, +117,120/-749. About 94,000 of those lines are probe run JSON under
`docs/research/`; without it, 180 files, +22,653/-749. The milestone's security seat (D-172) ran as
the Stage 5.1 release review (`docs/reviews/m19-closure-security-review.md`, MAJOR) and its re-read
(`docs/reviews/m19-release-security-reread.md`, MINOR). I did not redo it; M2 is about its condition.
**Grounded in:** `.agents/rules/practices.md`, `.agents/rules/issues.md`, seeds A.2, B.1, B.2, E.1,
E.2, G.1 and L.7 of `.agents/rules/playbook-seeds.md`, `AGENTS.md` §1, §3.4 to §3.6, §5 and §6, the
M19 plan (`docs/plans/m19-plan.md`) with its amendments, D-175 and D-179 to D-185, the five wave
closes and their reviews, the two security records, `docs/closure-checklist.md` §B.0 and §E, and the
documents a reader is sent to (`README.md`, `AGENTS.md`, `docs/architecture.md`, `docs/prd.md`,
`docs/security-invariants.md`, `docs/release-testflight.md`, `docs/owner-iphone.md`).
**Method:**
- I read the diff by area (registry and refresh, the client gate, the Engine layer, the gates and the
  Makefile, the hosted image and deploy path, the iOS release config, the records), every M19 ADR, the
  plan and its amendments, the five closes, and the security records in full; the wave reviews for
  what they dispositioned.
- `make check-fast` passes on `bd6213a` in this worktree: 6 of 6 legs in 64.8 s; pytest 2169 passed
  and 25 skipped; `coverage_floor.py --derive`: CI will skip 83 of 2194, and the budget is 83.
- `make wave-check FILE=docs/plans/m19-wave-{1..5}-close.md`: PASS on all five.
- `gh`, read only: the open issue list; the state, base, closing references and CI checks of #167,
  #176, #184, #196 and #197 (every check green; no bug in any closing list); labels and states of 25
  M19 issues; `Triage verdict` lines on #163 to #195; the two GitHub milestones; the bodies of #187,
  #188, #190 and #191; #149's comments.
- **Probe 1 (Swift).** A temporary test file in `ios/EngineTests` routed the six questions of the UI
  target's scripted table (`ios/UITests/ScreenPathTests.swift:14-22`) through `TieredRouter` with that
  table, by `swift test --filter`. The file was deleted after the run; `git status` was empty. Result in M1.
- **Probe 2 (Python).** I derived the public artifact from the worktree's copy of the served artifact
  into my scratch folder and ran the four steps of `scripts/journey.py` in process (Starlette's
  `TestClient`, `APP_ENV=production`, the Host list `model-ranking.fly.dev`), inside
  `scripts/offline.sb`. 4 of 4 passed. The copy's sha256 was `dac97873…9344` before and after.
- No simulator, `xcodebuild`, Docker, `fly`, installer, `launchctl` or browser; no network beyond the
  `gh` reads; no fault planted in a tracked file. I changed nothing but this file.

**Not raised again:** #66, #81, #85, #88, #94, #108, #113, #115, #122, #124, #132, #141, #142, #145,
#147, #163 to #166, #168 to #175, #177 to #183, #185 to #195 are already filed. Where one of them is
worse than filed, the finding says so (#142 in M12, #191 in M9).

## Verdict

MINOR

## Summary

Sixteen findings: one MAJOR, fifteen MINOR, none BLOCKING. Each wave was reviewed on its own; these
are what lie between them.
- **M1 (MAJOR)** is correctness: W4's question-of-fact signal turns three committed UI tests red, the
  three the PRD cites for REQ-ASK-005, and no M19 run of the UI target saw it. It ships to TestFlight.
- **M2 to M4** are the release path: a change after the security re-read that no seat read, a deploy
  that does not say which code built its data, and two runbook steps the wave's own gates refuse.
- **M5 to M11** are drift: one fact changed in one wave and not in another document or ADR.
- **M12 to M16** are process: the ledger, the process log, the plan, the issue pipeline and one
  untested release gate. M12, M13 and M14 repeat M18's M16, M15 and M12.

## The plan's criteria (`docs/plans/m19-plan.md` §1 and its amendments), against what shipped

| Wave | Criterion | State | Evidence |
|---|---|---|---|
| W1 | Makers' spellings, one release one model, effort never a model, attributions current or waiting on #88 | **met**; #124 in part | `docs/plans/m19-wave-1-close.md:12-30`; #88 is now D-185 |
| W2 | Nothing derived from the question reaches a request or the file, by any route; no arithmetic outside the named files | **not met as worded**, narrowed by the W2 amendments | `docs/plans/m19-plan.md:214-224`; G-1 and G-2 open in part (#171 to #173) |
| W3 | Skips, wave and tier gates and a child's network seen before a push | **met** | D-183; CI's half of #122 is the owner's; #108 by its guard |
| W4 | Knowledge and image-making read better than M18, on a fresh set, by bars set after the baseline | **not met**: bars missed, the owner asked on #196 | D-184; and M1 |
| W5 | The W5 list done or ruled, then the Stage 5.1 review | **review ran; list in part** | #81 and #115 neither done nor ruled (M14) |

## Correctness

- **M1 -- MAJOR: W4's question-of-fact signal turns three committed UI tests red, and no M19 run of
  the UI target saw it.**
  - **Where.** W4 made a question of fact a doubt in code (`ios/ModelRanking/Engine/Router.swift:716-719`,
    `InputSignals.asksAFact`, `ios/ModelRanking/Engine/Reading.swift:169`). With the model's own doubt
    that is now the note, not a question back (D-184; `ReadingTests.swift::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote`).
  - The UI target scripts the model's doubt for "what is the capital of australia"
    (`ios/UITests/ScreenPathTests.swift:18`) and three tests wait for the question back on it:
    `testADoubtIsAskedAndNoIsTheNote` (`:144`), `testAHeldSecondQuestionClearsTheFirstAnswer`
    (`:255`), `testATurkishReaderIsAskedBackInTurkish` (`:276`).
  - W4 saw the change in the unit tests: `ios/EngineTests/ReadingTests.swift:255-256` replaced exactly
    this question, "a question of fact is now a doubt in code too, so with the model's it is the note".
    `ios/UITests` was not touched in M19 after #133 (`7575645`).
  - **Measured (probe 1).** With the UI target's table, the shipping Engine reads that question as
    `.notASearch` (`asksAFact` true). The other five scripted questions read as their UI tests expect.
    So the three tests wait 20 s for `askBack`, which never comes. I did not run the UI target
    (`simctl` and `xcodebuild` are out of bounds); the failure is read from the code and measured on
    the Engine.
  - **Why no gate saw it.** `swift test` does not compile `ios/UITests`. D-175 clause 2 asks a wave
    that changes a screen to cite a `make ui-test` run (`docs/decisions.md:3675`), and D-174's
    amendment lets that wave's Tester run it (`:3649-3650`). W4's close lists no UI run
    (`docs/plans/m19-wave-4-close.md:38`), nor does W5's (`docs/plans/m19-wave-5-close.md:43`). The last
    run was W2's, 18 of 18 at `fc369d5`.
  - **What it costs.** The PRD cites all three as REQ-ASK-005's evidence (`docs/prd.md:532`). The
    owner's next `make ui-test` is red on 3 of 18. The TestFlight build carries a reading change that
    no screen test has run on, so "full regression, once, on the exact bundle" (`/going-live` §6)
    cannot pass as the tree stands.
  - **Fix belongs:** on W4's branch (#196), before it merges: give the three tests a question no code
    signal reads (W4's own unit test uses "a playlist for a long drive"), run `make ui-test` and cite it
    in the W4 close. Then file an enhancement: the UI target's routing table and the reading each test
    expects move into one fixture that an Engine test also reads, so `swift test` (in `check-fast`)
    fails when a reading change flips a UI path.

- **M2 -- MINOR: the release surface changed after the security re-read, which asked for a read of
  any such change, and none is recorded.**
  - The re-read covered `7fde40d..6c98dd7` and set the condition: "If anything on that surface changes
    before the merge, that change needs the same short read" (`docs/reviews/m19-release-security-reread.md:44-48`).
  - Three commits after it change that surface: `0a80b65` (`.dockerignore:15-16`, the runbook, G-7),
    `fdf6701` (`src/app/workflows/public.py:45`, `:58`, `:89`: the `access` table's left-out rows;
    INV-86 and INV-87) and `fb2040d` (the Bash guard, `.claude/settings.json:49`). The W5 Tester's
    range also ends at `6c98dd7`, so no seat read these three.
  - Each one tightens what it touches. But W5's close marks the security row ✅ on the re-read
    (`docs/plans/m19-wave-5-close.md:35`) without the condition, so a regression there would reach the
    public deploy under a record that says it was read.
  - **Fix belongs:** a short read of `6c98dd7..bd6213a` on the re-read's surface list before the
    deploy, as an addendum record; or one line in W5's close saying why it is not owed.

- **M3 -- MINOR: the deploy names the code it ships and the data's bytes, but not the code that built
  the data.**
  - `scripts/deploy_hosted_engine.sh:22`, `:54-56` derives the public artifact from the Mac service's
    artifact and stamps `release-<HEAD>-data-<digest>`. Neither the artifact's tables nor its refresh
    record (`src/app/workflows/refresh.py:861-897`) name the release that built it.
  - What W1 fixed (makers' spellings, one release one model, attribution) is done at build time. It
    reaches the public only through a nightly build by a service that runs a W1 release.
  - The runbook's first step updates the checkout and the development venv, not the service
    (`docs/release-testflight.md:17`). If the service runs an older release, the first public deploy
    serves the older build's names and ids while `/health` names `HEAD`. That is seed L.7's question
    ("which code is live", `.agents/rules/practices.md:107-111`) answered for the code only.
  - Today it holds: the worktree's copy passes W1's artifact test in `check-fast`. The check is absent,
    not failing.
  - **Fix belongs:** now, the runbook's step 1.1 adds `scripts/install_engine_service.sh` and one
    refresh before the first deploy. Then file an enhancement: the refresh record keeps the cycle's
    `APP_BUILD`, and the deploy refuses an artifact built by a release other than `HEAD`, or puts it in
    the stamp.

- **M4 -- MINOR: two runbook steps contradict the wave's own gates.**
  - **The fallback.** `docs/release-testflight.md:83-85` says that if Fly's check fails, replace
    `[[http_service.checks]]` with a TCP check and deploy again. INV-86's test requires a Host-sending
    HTTP check (`tests/unit/test_hosted_engine.py:98-100`), and the deploy ships only `origin/main`'s
    tip (`scripts/deploy_hosted_engine.sh:42-46`). So the fallback cannot deploy without a PR whose CI is
    red, at the moment the owner needs it.
  - **Step 1.3.** `:22-26` says "Merge that change to `main`" and then "Commit the change". The order is
    reversed, and a merge to `main` needs a branch and a PR (branch protection), which the step does not
    say.
  - **The route in.** `README.md:33-42` lists the documents a reader is sent to; the release runbook is
    not among them, and neither `AGENTS.md` nor `docs/architecture.md` names it (M5, M6).
  - **Fix belongs:** the closure PR: a fallback INV-86 accepts (or an amended INV-86 with its test,
    through a PR); step 1.3 as branch, commit, PR, merge, pull; the runbook in README's list.

## Drift and duplicated knowledge

- **M5 -- MINOR: `docs/architecture.md` still describes the code "after M18's seven waves", and the
  release is its first deploy.**
  - `AGENTS.md:19` sends a reader here for the deployment topology. M19 changed none of it:
  - `:432-436` says `fly.toml` and the `Dockerfile` "remain as D-116's target", nothing has been
    deployed, and a hosted engine waits for the Stage 5.1 review and #88. W5 built the hosted stage, the
    public artifact and the deploy script (D-185); Stage 5.1 ran.
  - `:428-431` says a git-ignored `Engine.local.xcconfig` overrides the engine address. Since S1's fix
    it overrides Debug only, and Release reaches `https://model-ranking.fly.dev`.
  - `:65`: "Prices: LiteLLM and OpenRouter. Both are required." The public artifact has no OpenRouter
    price (D-185 clause 3).
  - `:109` lists `/v1/recommendations` without `model_id` (D-182); `:271` keys cards on four shown
    values (D-175), not on the id (D-182 clause 2).
  - `:234-240` lists the code signals without the question of fact (D-184).
  - `:249` describes the session without its cookie rule (#144, INV-85).
  - `:294-296` says arithmetic happens only in two named files and the declaration gate holds the
    network. D-181 adds `priceInPages` in `Router.swift` and `Language.swift`, and D-180 and D-181 now
    hold the sinks and arithmetic on the compiled module.
  - `:478` (conflict row 4) and `:502-507` (open items): "Stage 5.1 and #88 come first", #66 and #113
    "(PR #134)", #122 "beyond the suite's network guard", "The Stage 5.1 release review has not run".
  - The rules: "Prune stale docs that contradict current decisions" (`.agents/rules/practices.md:200`),
    seed A.2. The M18 review's M5 was the same finding.
  - **Fix belongs:** the closure PR, rewriting the affected sections in place.

- **M6 -- MINOR: `AGENTS.md` §1 and the headers W5 rewrote say what W5 changed, or what has not held
  since M6.**
  - `AGENTS.md:16`: "Nothing is hosted yet: Fly.io stays the target (D-116, D-123), after the Stage
    5.1 review." The review has run; D-185's hosted path, public artifact and TestFlight build are not
    named. The line is true until the owner's step 1.5 and wrong the day after.
  - `Dockerfile:1-2`, rewritten by W5, and `fly.toml:1-2` say `.github/CODEOWNERS` marks them as a
    cross-team surface. That file has had no rules since M6 (W-021, ruled by the owner); K.10's
    boundary is only `AGENTS.md`'s §5 rule.
  - **Fix belongs:** the closure PR: §1 names the hosted engine and its runbook; the two headers point
    at `AGENTS.md` §5, not at an empty file.

- **M7 -- MINOR: the Stage 5.1 verdict is not where, nor in the word, the release rules look for it.**
  - `AGENTS.md:114`, `docs/closure-checklist.md:111`, `permission-matrix.md:90` and
    `.claude/agents/Security-Reviewer.md:84`, `:130` put the verdict in `docs/reviews/release-security.md`.
    The checklist says it "must PASS before any E.2 step", and "PASS → proceed, BLOCKING → nothing
    deploys" (`:123`).
  - M19's verdicts are `docs/reviews/m19-closure-security-review.md` (MAJOR) and
    `docs/reviews/m19-release-security-reread.md` (MINOR, with "yes" to the deploy). No
    `release-security.md` exists, and `.path-refs-allow:11` exempts that path, so the dangling name
    stays quiet.
  - The runbook says "after the Stage 5.1 security review of this wave has passed"
    (`docs/release-testflight.md:12-13`). Read against the checklist, nothing has passed; read against
    the re-read, it has.
  - **Fix belongs:** the closure PR: amend the checklist's E.1 in one place, with the others pointing
    to it: a MINOR verdict whose findings are all fixed or filed permits the deploy, and the verdict of
    record is named per release. Or write `docs/reviews/release-security.md` as that record, naming
    both files.

- **M8 -- MINOR: the PRD has no requirement for what W5 built, and the rows the release discharges were
  left as they were.**
  - No REQ row states D-185 clause 3 (the public artifact) or clause 4 (a Release build reaches the
    hosted engine over HTTPS). INV-86 and INV-87 hold them as security rows only, so the citing-test
    rule (`.agents/rules/practices.md:38-40`) cannot reach them as requirements.
  - REQ-API-009 (`docs/prd.md:408`): "Nothing is deployed", "No gate runs it". W5 wired `make journey`
    and `make cold-start` (`Makefile:318-336`), and the runbook's step 1.6 runs the journey after the
    deploy. W-030 (`docs/warnings.ledger.md:39`) is still ESCALATED to "M8 go-live".
  - REQ-REF-007 (`docs/prd.md:450`): "the physical half is unmet because nothing is deployed", and
    "W-125 (accepted)". W-125 was fixed in M18-W6 (`docs/architecture.md:482` says so), and W5's hosted
    stage is the physical half.
  - W5's `tests/unit/test_deploy_hosted.py` and `tests/unit/test_release_gates.py` cite no REQ-ID or
    D-ID (seed E.2, `.agents/rules/practices.md:42`).
  - **Fix belongs:** the closure PR: one row for the public artifact and the Release address, citing
    `test_public_artifact.py` and `test_testflight_ready.py`; REQ-API-009 and W-030 restated as owed by
    the owner's first `make journey URL=...`; REQ-REF-007 restated.

- **M9 -- MINOR: W4's reading measures are told in several places, and four were not updated.**
  - **Knowledge questions.** REQ-ASK-005 (`docs/prd.md:532`) and D-184 give W4's measure, 5 and 5 of 20
    on a fresh set. REQ-ASK-003 (`:531`) still gives "M18-W3's reading caught 1 of 10". REQ-RTR-005
    (`:468`) and REQ-ASK-003 say "W-123 (accepted, owned by M19 with #66)". W-123
    (`docs/warnings.ledger.md:177`) says "Owning milestone: M19, with #66" and "1 time in 10". M19 ends,
    and its owning milestone passes with no line.
  - **Requests to make an image.** W4's close (`docs/plans/m19-wave-4-close.md:16-19`), D-184 and
    REQ-IMG-003 say 2 and 1 of 20 as the code ships. #191's body says "4 and 3 of 20", written before
    the fourth review took `yap` out.
  - The M18 review's M8 was the same pattern on W-123.
  - **Fix belongs:** the closure PR: W-123 re-measured from W4's record, with a new owner; REQ-ASK-003
    and REQ-RTR-005 point at REQ-ASK-005 instead of restating its numbers; #191's body corrected in place
    (issue bodies are live documents, `.agents/rules/practices.md:193`).

- **M10 -- MINOR: W2's two ADRs left five amended ADRs without a pointer; W1, W4 and W5 marked theirs.**
  - D-180 amends D-126's enforcement (`docs/decisions.md:3926`). D-181 amends D-104, D-138, D-160
    clause 2 and D-167 clause 4 (`:4018`). None of D-104 (`:308`), D-126 (`:1026`), D-138 (`:1638`),
    D-160 (`:2816`) or D-167 (`:3145`) carries an "Amended by" line for them.
  - W1 marked every ADR D-179 amends (`:2810`, `:3065`, `:3615`), W4 marked D-169 (`:3413`), and W5
    marked D-116 (`:690`).
  - A reader of D-160 clause 2 or D-167 clause 4 sees the text gate that once held it, not the compiled
    rule that holds it now, nor G-2's remainder.
  - The rules: seed B.2, "update the canonical file AND every cached pointer"
    (`.agents/rules/practices.md:184-189`). The M18 review's M6 was the same.
  - **Fix belongs:** the closure PR: one dated pointer under each of the five. Then file an
    enhancement: `make check-records` pairs every `**Amends** D-n` with an "Amended by" line under
    D-n (`AGENTS.md:64`, derive, don't enumerate).

- **M11 -- MINOR: four of seven M19 ADRs first appear with or after their code; the M18 review named
  this and proposed no gate.**
  - D-179 first appears in `6d19e1f`, a `fix:` commit, with its code. D-181 in `dc68029`, also with its
    code. D-183 in `f47231b`, the W3 review's fix commit, "written at the W3 review's M10"
    (`docs/decisions.md:4131`), after all six W3 fixes. D-184 in `ae2c528`, after `de8c3f8`'s code.
  - D-180 and D-182 were written first, as the rule asks. W5's plan carried D-185's decisions in prose
    before its code.
  - The M18 review's M17 found the same and said: "No gate is proposed: an ADR's timing is cheap to
    keep by hand once it is named" (`docs/reviews/m18-repo-review.md:294-295`). Named, and missed in
    four of five waves.
  - The rules: "Open the capture file BEFORE the work starts" (`.agents/rules/practices.md:180`, seed
    G.1) and seed B.1.
  - **Fix belongs:** file an enhancement: `make wave-check` refuses a close whose new D-ID first appears
    in a commit that changes `src/`, `ios/` or `scripts/`, unless the wave's plan commit names it.

## Process

- **M12 -- MINOR: no M19 skip or bypass reached the ledger, and the gate cannot see the ones the closes
  wrote.**
  - `docs/control-events.csv` has no M19 row.
  - Every close's row 8 says the session started outside the repository, so its hooks did not load
    (W1 `:41`, W2 `:44`, W3 `:40`, W4 `:34`, W5 `:39`). Five waves ran without the Bash guard and the
    post-edit `check-fast`. The M18 closure's lesson was this one ("start the session in the
    repository", `docs/process-log.md:623`). One control recorded five times would have gone under
    review at the third (`AGENTS.md:105`, `scripts/wave_check.py:549-556`).
  - This is worse than #142 says in one way: W5 rests part of D-185 clause 5 ("nothing is deployed by
    the agent") on that guard (`.claude/settings.json:49`), and every M19 session ran without it.
  - W4's run line declares "gates SKIPPED: the plan's coding-set guard"
    (`docs/plans/m19-wave-4-close.md:38`) and W5's "a Docker build" (`docs/plans/m19-wave-5-close.md:43`).
    The template asks each to be a row (`docs/wave-checklist.template.md:44`). The release seats' skip
    ledgers (the image build, `make cold-start`, `xcodebuild`, `make ui-test`) are not rows either,
    and E.1 asks for them before a deploy (`docs/closure-checklist.md:122`).
  - `scripts/wave_check.py:489` reads only a row's status cell, so a skip written in a ✅ row's run
    line passes `make wave-check`, as all five did.
  - **Fix belongs:** the closure PR: one row per event, the hook-less sessions as one control. Then file
    an enhancement: `make wave-check` reads row 9's `gates SKIPPED:` list and requires a ledger row for
    each entry that is not `none`.

- **M13 -- MINOR: M19 wrote no process-log entry, the second milestone in a row.**
  - The last entry is the M18 closure, 2026-10-05 (`docs/process-log.md:613-623`). Five waves ran on
    2026-10-05 to 10-07 with none. `/start-session` and `make standup` read this file, so a new session
    starts from M18's closure.
  - The rules: "process-log per session" (`.agents/rules/practices.md:181-182`, `:187`; `AGENTS.md:67`;
    seed G.1). The M18 review's M15 was the same, fixed by one entry at the closure.
  - **Fix belongs:** the closure PR: the M19 entries, from the five closes. Then file an enhancement:
    `make wave-check` requires a process-log heading dated inside the wave's commit range.

- **M14 -- MINOR: the plan was not reconciled with what ran, and its W5 is not the W5 that shipped.**
  - `docs/plans/m19-plan.md:4` is still `status: draft`. The amendments end at W4's (`:234-243`); none
    records the owner's release call of 2026-10-07 or W5's scope.
  - §2 W5 (`:110-118`) lists #141, #147, #142 and #88 as the owner's. W5 did #141 and #147, changed the
    hook for his approval (#142), and took #88's ruling on the standing instruction (D-185).
    TestFlight readiness, the deploy script and the public artifact are on no plan line.
  - §1's W5 criterion (`:42`) is every prerequisite on the W5 list done or ruled. #81 and #115 are
    neither; W5's close says "not this wave" (`docs/plans/m19-wave-5-close.md:41`). No record states
    the criterion met or missed.
  - §3's security globs (`:120-132`) do not name the deploy surface W5 created: `Dockerfile`,
    `fly.toml`, `.dockerignore`, `scripts/deploy_hosted_engine.sh`, `src/app/workflows/public.py`,
    `ios/Config/**`. #188 adds `ContentView.swift` only.
  - The GitHub milestone the plan names (`:17-18`) holds no issue, open or closed. M18's milestone is
    still open and holds #88.
  - The M18 review's M12 was the same finding.
  - **Fix belongs:** the closure PR: a W5 amendment (the call, the scope, who did what, the criterion's
    state) and a closing status. The deploy surface goes into the next plan's globs. Close or empty the
    two GitHub milestones.

- **M15 -- MINOR: two issue-pipeline steps W1 to W3 kept were dropped later.**
  - #185 to #195, eleven issues filed in W4 and W5, the bugs #191 (medium) and #192 (low) among them,
    carry no `Triage verdict:` line. Every issue W1 to W3 filed (#163 to #183) has one.
    `.agents/rules/issues.md:29-31`: every filed issue is triaged before anyone works it, and the
    verdict is the routing every lane reads.
  - #149 (a bug, W3) was closed on 2026-10-06 with its comment but without `dev:done`. W1's bugs
    (#112, #129, #130, #162) carry it, and D-178 asks for both (`.agents/rules/issues.md:86-88`).
  - **Fix belongs:** `/triage-issue` on the eleven; `dev:done` on #149.

- **M16 -- MINOR: the release's Stage 5.2 verdict, `scripts/journey.py`, has no committed test; W5's
  tests replace it with a stand-in.**
  - `tests/unit/test_release_gates.py:1-5`, `:35-40` and `:85-93` test `make journey` and
    `make cold-start` with stand-ins for Docker and for the journey itself. `scripts/journey.py` last
    changed at M7-W4 (`ec09883`); no test imports or runs it.
  - **Measured (probe 2):** its four steps pass on the public artifact in the hosted configuration:
    both coding surfaces answer, and each of the 14 tasks answers or says why. It holds today.
  - **What could happen.** A `/v1` change that breaks what the journey asserts (a pick's `why` or
    `blended_per_m`, both coding surfaces in one answer) passes every gate, and the owner finds it
    after his deploy. "Every load-bearing path has at least one test through the real entry point"
    (`AGENTS.md:102`).
  - **Fix belongs:** file an enhancement: a unit test runs `journey.STEPS` against the app through
    `TestClient`, on an artifact `public.derive` makes from a fixture, as probe 2 did.

## Dispositions, at the closure

Left for the lead agent after the seat closed. Each finding is fixed, filed, or stated, and none is
left in this file alone (`docs/closure-checklist.md` §B.0).

| finding | severity | disposition |
|---|---|---|
| M1 | MAJOR | |
| M2 | MINOR | |
| M3 | MINOR | |
| M4 | MINOR | |
| M5 | MINOR | |
| M6 | MINOR | |
| M7 | MINOR | |
| M8 | MINOR | |
| M9 | MINOR | |
| M10 | MINOR | |
| M11 | MINOR | |
| M12 | MINOR | |
| M13 | MINOR | |
| M14 | MINOR | |
| M15 | MINOR | |
| M16 | MINOR | |
