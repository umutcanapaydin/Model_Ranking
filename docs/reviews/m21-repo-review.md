---
record_type: review
id: m21-repo-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-10
---
# M21 repo review -- the whole milestone, `origin/closure/m20...9cbba60`

**Seat:** independent `/repo-review` across the whole of M21, as `docs/closure-checklist.md` §B.0
requires. I wrote none of M21's code, tests, reviews or fixes.
**Independent:** yes
**Range:** `git diff origin/closure/m20...9cbba60`. `origin/closure/m20` (`972b55e`) is the M20 closure,
not yet on `main` (`main` is at `bd273bc`). `9cbba60` is the head of W4. The range holds all four waves,
each a stacked draft PR against `main`: W1 #236, W2 #240, W3 #250, W4 #251. That is 144 files,
+31,099/-1,652; about half of the insertions are probe-run JSON under `docs/research/m21-w2-runs/`,
which I skimmed by name only.
**Grounded in:** `.agents/rules/practices.md`, `.agents/rules/issues.md`, `AGENTS.md` §3.5 and §5, the
M21 plan (`docs/plans/m21-plan.md`), D-189 to D-192 and the ADRs they amend, the four wave closes and the
wave reviews (for what they dispositioned), `docs/security-invariants.md`, `docs/prd.md`,
`docs/architecture.md`, `docs/release-testflight.md`, `INSTALL.md` and `docs/control-events.csv`.
**Method:**
- I read the diff by area: the registry and the family-word generator, the rate limiter and the error
  sentences, the deploy stamp and the refresh record, the Engine and screen changes, the close and
  record checks (`scripts/wave_check.py`, `scripts/check_records.py`), the Makefile's Swift legs and
  the watchdog, the Bash guard, and the records.
- `scripts/wave_check_all.py`: PASS, 68 records. `scripts/check_records.py`: PASS. `scripts/wave_check.py`
  on each M21 close: PASS on all four.
- pytest on the 27 unit files M21 touched, minus those that run the deploy script, the engine service
  or the simulator: 729 passed, 2 skipped (the offline-profile tests, as on any non-sandboxed run).
- **Probe 1 (history rules).** In process, with `HISTORY_RULES_FROM` lowered to 2026-10-01 so that
  D-192 clause 2 reads every M21 close: result in M2.
- **Probe 2 (Bash guard).** `.claude/hooks/bash_guard.py` fed 24 ordinary agent commands as hook
  payloads (here-documents, `$( )`, loops, `gh pr create --body "$(cat <<'EOF' ...)"`, branch
  switches): no false block beyond the documented zsh glob qualifiers. Not raised.
- `gh`, read only: the issue list, the bodies of #230 to #249, #236's base.
- No simulator, `xcodebuild`, Docker, `fly`, installer, `launchctl` or browser; no `make check-fast`
  (its Swift and compiled-gate legs); no held-out file or probe question opened; no fault planted. I
  changed nothing but this file.

**Not raised again:** these are already filed: #108, #122, #142, #194, #218, #222, #230 to #235, #237 to
#239, #241 to #244, #246, #247. Where one is worse than filed, or a delivered issue is not fully
delivered, the finding says so (#202 in M1, #223 in M4, #200 in M5, #245 in M7).

## Verdict

MINOR

## Summary

Eleven findings: two MAJOR and nine MINOR, none BLOCKING.
- **M1 and M2 (MAJOR)** are W4's new close rules meeting the rest of the milestone. A control the
  ledger counts was bypassed twice in M21 with no ledger row, and D-192's skip rule does not read the
  field that names a bypass. And the range rule refuses a first wave stacked on an unmerged closure,
  which is how the owner's "keep going" practice stacks every next milestone.
- **M3** is the security-glob list the range rule now depends on: it holds none of the gates.
- **M4** is a failure the phone names itself, still in English for a Turkish reader after #223.
- **M5 to M11** are drift: where the ADR pointers sit, the runbook, an issue no record carries, stale
  issue provenance, and three live records.

## The plan's criteria (`docs/plans/m21-plan.md` §1), against what shipped

| Wave | Criterion | State | Evidence |
|---|---|---|---|
| W1 | Releases, rerouted ids and fine-tunes stay apart; `web-dev` on LMArena's board; the deploy names the data's release; a missed copy refused | **met in code; not deployed** | `src/app/workflows/registry.py:181-235`; `src/app/workflows/categories.py:208-224`; `scripts/deploy_hosted_engine.sh:55-98`; `src/app/workflows/public.py:89-94` |
| W2 | #194 (the fact doubt's model words); held-out checks; harness tests; #66 measured | **in part, as D-191 records**: #194, #218, #222 taken out after three verdicts; #66 carried | D-191; `docs/research/m21-w2-reading-probe.md` §8 |
| W3 | The compiled gates follow the routes the reviews found; the held reading in the Engine | **met as worded, held in part** (G-1, G-2, G-10 to G-15) | `ios/ModelRanking/Engine/HeldReading.swift`; `docs/security-invariants.md:177-198` |
| W4 | The close checks see ADR pointers and timing, skips, the process log, the range's diff; CI's list derived; Swift legs offline | **met as worded**; see M1, M2, M3, M5 | `scripts/wave_check.py:355-597`; `scripts/check_records.py:1539-1572` |

## Correctness

- **M1 -- MAJOR: two M21 bypasses of `commit-after-check-fast` have no ledger row, the ledger row the
  closes cite does not exist, and D-192's new skip rule does not read the field that names a bypass.**
  `docs/plans/m21-wave-2-close.md:47`, `docs/plans/m21-wave-4-close.md:48`, `docs/control-events.csv:15,18`,
  `scripts/wave_check.py:553-597` (`skip_ledger_problems`), `scripts/wave_check.py:795-815`.
  - **What is wrong.** W2's row 9 says `Bypass: 9613a2b, recorded with the M20 closure's pending
    ledger row for the same control`; W4's says `Bypass: 9cf8e12 (the owner's ruling on the
    commit-after-check-fast control is pending from the M20 closure)`. The ledger holds two
    `commit-after-check-fast` rows (m18-w5, m19-w5), on `origin/closure/m20` and at `9cbba60` alike.
    The M20 closure wrote that the control "reached its third row" (`docs/process-log.md:683`), but no
    third row was written. So five events are named, two are counted, and the three-strikes rule
    (`wave_check.py:810-815`) stays green. The ledger's own header says a row is appended "at the
    moment it happens, never reconstructed later". D-192 clause 3 (#202) reads `gates SKIPPED:` and
    the SKIPPED, WAIVED and N/A statuses. It does not read row 9's `Bypass:` field, the one field
    that names a bypass.
  - **What could happen.** Every later bypass of this control is written as "pending" prose, and the
    gate meant to put the control in front of the owner never fires. This is the defect #202 was
    filed for, in the field #202's fix does not read. #202 would close on merge with it still open.
  - **Fix.** Write the missing rows (M20's third event, `9613a2b` for m21-w2, `9cf8e12` for m21-w4).
    The three-strikes rule then turns red, which is the designed outcome: the owner rules (fix,
    re-scope or refuse in `docs/refusals.md`). Extend `skip_ledger_problems` to read `Bypass:` as it
    reads `gates SKIPPED:`, with a planted close as its red test.

- **M2 -- MAJOR: D-192's range rule refuses a first wave stacked on a closure that is not yet on
  `main`, so the next milestone's W1 cannot pass `make wave-check`.**
  `scripts/wave_check.py:396-408` (`_wave_base`), `:478-481`.
  - **What is wrong.** For wave 1, `_wave_base` is the merge base with `origin/main`. A W1 stacked on
    an unmerged closure starts its range at that closure. The merge base on `main` is older than
    that, so the rule reports "a range narrower than the wave is refused". Probe 1 ran the rules over
    M21-W1's own close. Its range `origin/closure/m20...HEAD` starts at `972b55e`, and the wave base
    is `bd273bc`, so the close was refused. If the author widens the range to `origin/main...HEAD`,
    the range takes in every unmerged ADR of the earlier milestones. The #201 rule then reports
    D-189 and D-190 ("first appears in `5bcae05` / `47f0c6c`, which also changes code") and D-191
    ("after the range's code commit `f976da7`"). Those three are exempt today only because W1's and
    W2's closes are dated 2026-10-09.
  - **What could happen.** M21's PRs wait for the owner, who merges everything at once. So M22-W1
    will start on `closure/m21` with M20 and M21 both off `main`. Its close is dated after
    2026-10-10, and it fails `make wave-check` with either range. Nothing in the close can make it
    pass, short of waiting for the merge or bypassing the gate.
  - **Fix.** Let wave 1's base be the previous milestone's closure (its last wave's close, or the
    closure record) when that commit is an ancestor of the end. Read ADRs and globs only from that
    base. Add a planted two-milestone stack as the red test.

- **M3 -- MINOR: the security-glob list the range rule now trusts holds none of the gates that hold
  the invariants.** `docs/plans/m21-plan.md:79-89`; `scripts/wave_check.py:489-494`.
  - **What is wrong.** Since D-192 clause 2 (#183), a wave is HIGH when its commit range touches the
    plan's globs. The list holds the client's sink files, `ContentView.swift`, `.claude/hooks/**` and
    the deploy surface. It does not hold the code that holds the invariants: `scripts/client_decl_gate.py`,
    `scripts/client_decl_fixtures/**` (which `docs/security-invariants.md` calls the definition of what
    the compiled gate refuses, nine times), the text pins `tests/unit/test_router_hints.py` and
    `tests/unit/test_ios_client_contract.py`, `scripts/offline.sb` (INV-6), `scripts/wave_check.py`,
    `scripts/check_records.py` and `Makefile`. W4's own row 1 names the gates it changed as the reason
    it was HIGH. None of those files is on the list.
  - **What could happen.** A later wave weakens a fixture shape or a pin, which is exactly what
    `practices.md` says the security pass looks for ("weakened validation ... disabled checks"). Its
    footprint says MEDIUM, and the range rule agrees, because no glob is touched.
  - **Fix.** Add these paths to the globs in the next plan, or let `plan_globs` add the files the
    invariant rows cite, so the list is derived (AGENTS.md §3.5).

- **M4 -- MINOR: a failure the phone names itself, `unexpected`, is still shown in English to a
  Turkish reader, and #223 closes on merge.** `ios/ModelRanking/Engine/EngineClient.swift:328-331`,
  `ios/ModelRanking/Engine/Language.swift:809-822`, `tests/unit/test_error_codes.py:16-35`.
  - **What is wrong.** W3 gives every code the engine's `_error(...)` sends a sentence in both
    languages, and the test reads only those calls. A non-200 answer in any other shape becomes
    `refused(code: "unexpected", message: "The engine answered N in a shape this app did not
    recognise.")`. `errorDescription(.turkish)` returns that English message.
  - **What could happen.** The hosted engine runs on one machine (`--ha=false`). During a deploy or a
    crash, Fly's proxy answers 502 or 503 with its own body. A Turkish reader then sees the English
    sentence #223 was filed to remove.
  - **Fix.** Add an `unexpected` case to `refusalSentence` (the status is the useful part). Make the
    test require one sentence per code the phone can name, the engine's codes plus `unexpected`.

## Drift and records

- **M5 -- MINOR: eleven Amended-by pointers added in M21 sit under the next ADR's separator, so a
  reader sees them as the next ADR's.** `docs/decisions.md:639, 872, 1719, 1780, 1954, 1956, 2178, 2224,
  2582, 2734, 2736`; `scripts/check_records.py:1548-1572`.
  - **What is wrong.** Each pointer was inserted after the amended ADR's closing `---` and directly
    above the next `## D-n` heading. "**Amended by D-124**" (it amends D-115) reads as the first line
    of D-116. "**Amended by D-151**" (D-149) reads as D-150's. "**Amended by D-189** ... clause 2" and
    "**Amended by D-166**" (D-157) read as D-158's. A1 splits sections at headings, so it accepts each
    one.
  - **What could happen.** A reader of D-116, D-122, D-139, D-141, D-144, D-149, D-150, D-156 or D-158
    believes that ADR was amended. A reader of the ADR actually amended does not see the pointer
    under its own text.
  - **Fix.** Move each pointer above the `---`. Have A1 refuse an `**Amended by` line that follows a
    `---` with no text between them. Three older pointers (lines 322, 1091, 1717) share the defect.

- **M6 -- MINOR: the runbook contradicts W1's deploy refusal and does not say how M21 ships.**
  `docs/release-testflight.md:19-32`, `:40-41`, `:55-57`; `scripts/deploy_hosted_engine.sh:81-88`;
  `src/app/workflows/refresh.py:789-797`.
  - **What is wrong.**
    - Step 1.1 still says "Nothing yet records which release built the data (#198)". Step 2 of the
      build-3 list, and the script, now refuse on that record.
    - The build-3 list merges only M20's PRs and cites M20's closure verdict. M21 changes the hosted
      engine (the rate limiter's two counts, the deploy stamp, `web-dev`'s board) and the app (W3's
      screen changes), and the build number is still 3 (`ios/ModelRanking.xcodeproj/project.pbxproj:239`).
      Nothing says whether M21's four PRs merge before build 3, in what order, or which security
      verdict covers them.
    - Step 1.5 says the deploy "stamps the build with the commit". The stamp is now
      `...-data-<digest>-from-<sha>`.
    - The refusal says "let the Mac's engine refresh once with this release". A night whose candidate
      matches the served digest exits UNCHANGED, and `_builds` keeps the old `served_built_by`. A
      refresh run by hand has no `APP_BUILD`, so it records `unknown`, which the script describes as
      "a record from before #198".
  - **What could happen.** The owner follows the build-3 list as written, deploys an engine and
    uploads a build that no security verdict has read. Or the owner waits for nights that cannot
    change the record.
  - **Fix.** Rewrite the build-3 section for M20 plus M21: the merge order, which verdict covers it,
    and the build number. Drop the stale sentence in step 1.1 and name the stamp's three parts. Say
    in the refusal and the runbook that an unchanged night keeps the old builder, and that a hand
    refresh records `unknown`.

- **M7 -- MINOR: #245, a security finding the issue addresses to the closure seat, is carried by no
  plan or record.** `docs/security-invariants.md:193` (G-10), `docs/plans/m21-wave-3-close.md:51, 57-83`.
  - **What is wrong.** #245 (the module allowlist has no text pin, so CI's Linux lane holds it with
    nothing) is named nowhere in the repository. G-10 describes the condition but names only #243.
    INV-62 does not name #245, and the W3 close's finding map does not either. The close covers it
    only as part of "Filed: #241 to #249". The issue's own pointer is stale too (M8).
  - **What could happen.** The closure security seat reads the register, as D-172 has it, and never
    meets #245.
  - **Fix.** Name #245 beside #243 in G-10's issue column, or in INV-62's row.

- **M8 -- MINOR: the "Found in" pointers of ten M21 issues name a review file whose findings
  are now another round's.** #230, #237, #241, #242, #243, #244 (in part), #245, #246, #247, #248 (in
  part); the
  renames `d776a1e`, `f33935e`, `7e8deaf`, `011f15d`, `929e97a`, `659374c`, `15ebc57`.
  - **What is wrong.** Each round's review is written as `m21-wave-N-review.md` and renamed
    `-round-K.md` when the next round lands. The issues filed from a round keep the old name.
    #241's "`m21-wave-3-review.md`, K1" is the NSExpression finding, now in `-round-1.md:324`. Today
    `m21-wave-3-review.md` K1 (`:312`) is a different finding. #245's source is
    `-round-2.md:197`.
  - **What could happen.** A triager or a fixer opens the cited file and reads the wrong finding,
    or none.
  - **Fix.** Correct the ten issue bodies in place. Then write every round under its final name
    from the start (`-round-K.md`), so a pointer never moves.

- **M9 -- MINOR: `docs/architecture.md` does not describe D-191's rule or the file the registry
  writes into the app.** `docs/architecture.md:242-245`; `scripts/model_family_words.py`;
  `ios/ModelRanking/Engine/ModelFamilies.swift`; `ios/ModelRanking/Engine/HeldReading.swift`.
  - **What is wrong.** The wording tier is described as surface words, then the embedding. Before
    both, a question made only of ranked families' names, tiers and Turkish particles is answered
    from `everyday` (D-191 clause 1, `Router.swift:541-549`). Its names come from a Swift file
    generated from the engine's registry. That is a new build-time dependency from `src/` into
    `ios/`. Neither the dependency nor `HeldReading.swift` is named.
  - **What could happen.** A registry change is made without regenerating the file, or without
    knowing it changes the phone's routing. The byte-for-byte test catches the first case, but only
    in a run that includes it. A reader of the architecture cannot learn either fact.
  - **Fix.** One bullet under the Router: the comparison rule, the generated file, how to regenerate
    it, and that the phone's family words change only with an app build.

- **M10 -- MINOR: `AGENTS.md`'s hooks paragraph predates W4's hook, and the Claude Code version
  appears in two places with no gate.** `AGENTS.md:107`; `INSTALL.md:16-19`;
  `docs/security-invariants.md:191`.
  - **What is wrong.**
    - `AGENTS.md` says "a hook blocks only by exiting 2", and lists two fail-closed cases. Since W4
      the Bash hook also blocks on a timeout (`onFailure: "block"`, from Claude Code 2.1.295 on), and
      blocks every command when `.claude/hooks/bash_guard.py` is missing.
    - The version 2.1.295 is written in `INSTALL.md` and in G-7, and nothing compares the two or
      checks the installed version.
  - **What could happen.** An agent reading `AGENTS.md` cannot explain a block caused by a missing
    guard file. A later edit to one copy of the version leaves the other wrong.
  - **Fix.** Update the paragraph and point it at `INSTALL.md`. Let G-7 cite `INSTALL.md` rather
    than restate the version.

- **M11 -- MINOR: REQ-ASK-005 reports model-tier counts measured on rules that were later taken
  out, without the caveat D-191 carries.** `docs/prd.md:533`.
  - **What is wrong.** The row says "the model tier asked about 3 to 5 of 71 searches ... and 3 to 5
    of its 7 non-searches were caught". Those runs (`docs/research/m21-w2-reading-probe.md` §2) were
    made before the reviews, with #194's fact-doubt words in place. §6 to §8 say the model tier was
    not run again. D-191 says "The model tier was measured only before the reviews (§2)". The PRD
    row presents the counts as the shipping state.
  - **What could happen.** #66's carry and the next plan start from counts no shipped code produced.
  - **Fix.** Add D-191's caveat to the row, or measure the model tier on the head.

## Dispositions, at the closure

| finding | severity | disposition |
|---|---|---|
| M1 | MAJOR | to be fixed or filed at the closure |
| M2 | MAJOR | to be fixed or filed at the closure |
| M3 | MINOR | to be fixed or filed at the closure |
| M4 | MINOR | to be fixed or filed at the closure |
| M5 | MINOR | to be fixed or filed at the closure |
| M6 | MINOR | to be fixed or filed at the closure |
| M7 | MINOR | to be fixed or filed at the closure |
| M8 | MINOR | to be fixed or filed at the closure |
| M9 | MINOR | to be fixed or filed at the closure |
| M10 | MINOR | to be fixed or filed at the closure |
| M11 | MINOR | to be fixed or filed at the closure |
