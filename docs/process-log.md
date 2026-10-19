# Process Log

> Append-only. One entry per session (typically per work-day or per slice). 3-10 lines each. Never edit historical entries; correct via a new entry.
>
> Each entry ends with a `Lesson:` tag — the seed candidates for `.agents/rules/playbook-seeds.md`. `/start-session` reads the latest entry first.
>
> Seed G.1: open this file BEFORE the work starts.

---

## S1 — Project bootstrap (TEMPLATE — replace with real entry)

**Date:** YYYY-MM-DD
**Agent:** <Claude / Codex / human>

What we did:
- Cloned pipeline v2.0 template into this project.
- Filled in AGENTS.md PROJECT section (name, customer, stack, REQ-ID scheme).
- Adapted `permission-matrix.md` for project context.
- Created `.claude/settings.json` from `docs/claude-harness-config.md` (Cowork-blocked file).
- Created `.mcp.json` from `mcp.json.template`.
- Ran `make check` — green on day 1.
- Wrote first REQ-IDs in `docs/prd.md`.

What surprised us:
- <e.g., "PostToolUse hook caught a stray edit while we were typing — instant feedback.">

What we'd do differently:
- <e.g., "Should have read tool-suitability.md before sizing M1.">

Lesson: <one-line generalizable principle, or "none today">

---

## S2 — <next session>

<continue here>

## 2026-08-10 — M1 W1: schema + LiteLLM ingestion (Claude, Cowork)
Stage 0 closed (bootstrap-check PASS on owner machine, 0 fail/2 warn). Owner signed m1-plan §13;
W1 implemented: schema.py (provenance columns, CHECK>0, UNIQUE widened pre-freeze), RawSource
Protocol + fake, LiteLLM client/parser (bool/negative guards), ingest run-context. 19 unit tests
+ 1 env-gated contract test (live PASS, 500+ aliases); ruff/mypy-strict clean. Fresh-eyes combined
review: PASS, 9 MINOR — all applied or ledgered. Fault-injection ×2: RED confirmed, md5 reverts.
Owner checkpoint commit OWED (repo not yet opened).
Lesson: the starter's own src/__init__.py breaks `make typecheck` (mypy src) — a Stage-0 gate gap;
candidate seed for the template upstream.

## 2026-08-10 (2) — M1 W2-W3-W4: full data layer + recommendation engine (Claude, Cowork)
Owner ratified A0.5 flow (no stops between waves) + M1-M5 roadmap written to deliverables-plan.
W2: SWE-bench Verified + Aider ingestion (review PASS, 5 MINOR applied). W3: canonical registry +
median prices + ranking + export — review FAIL (2 BLOCKING: mypy-on-tests; real-alias false
matches gpt-5-pro→gpt-5 class) → 5 new canonical models, 12 tightened lookaheads, deterministic
tie-break; re-verified green. W4: 3-answer engine + CLI — review CHANGES REQUIRED (false why on
floor-unmet fallback; exit-code collision) → fixed + tested. First LIVE run caught Aider dup-model
UNIQUE abort (fixture blind spot) → keep-best dedupe + regression. Final: 71 tests + 3 gated,
live e2e green (2154 prices, 173+68 scores, 42 canonical models; picks: Opus/MiniMax/DeepSeek).
Fault-injection ×6 across waves, all RED + md5 reverts. All owner checkpoint commits OWED.
Lesson: fixtures model imagined data; the first live run belongs INSIDE the wave, not after it —
candidate seed + closure-report item.

## 2026-08-11 — M1 Stage 4 closure (Claude, Cowork)
Security review (closure, BLOCKING gate): PASS, 0 BLOCKING; 2 MINOR closed (unused deps → planned;
.gitignore += *.db) + CLI connect moved into try. Quality Gate: 13/13 criteria ✅ with citing tests
(V3C-02), coverage 88%, criteria diffs NONE. Capture: EXPERIENCE.md M1 entry, closure-report-m1.md
generated, 2 seed candidates queued for owner. Owner opened GitHub repo (Model_Ranking); all
checkpoint commits collapse into owner's initial commit. Milestone closes at owner sign-off.
Lesson: closure telemetry (fix-rate/churn) needs git history from day one — starting M2, checkpoint
commits land per wave, so M2 will have real trust telemetry.

## 2026-08-11 (2) — M2 W1-W4 + Stage 4 closure (Claude, Cowork)
Owner signed m2-plan with 2 amendments (no per-wave git; council for questions). W1 OpenRouter +
median-of-medians (REQ-ING-006 fixes M1 carried risk). W2 Arena via documented datasets-server API
(shape pinned from dataset card via WebFetch; CC-BY attribution constant). W3 category layer:
categories-as-data, generalized RankingRow (documented in D-105), attribution in exports. W4
recommend --task coding|assistant, per-scale thresholds AS DATA, stale-notice disclosure,
contract-tests.yml CI workflow. Reviews pair-batched (economy, separate verdicts): 4× PASS,
11 MINOR + 2 PROCESS, all applied. Fault-injection ×4 RED + md5 reverts. Security close PASS
(2 MINORs = replica artifacts; device repo verified). Suite: 104+5, coverage 90%.
Lesson: "ask the owner" pressure mostly dissolves against a primary source (dataset card beat
deliberation); council stayed unconvened.

## 2026-08-11 (3) — FP-M2-1: Arena live catch → fixpack (Claude, Cowork; D-106 commit)
Owner's live run: OpenRouter contract PASSED (first live validation); Arena aborted loudly
(>5000 rows in text/latest — anti-truncation guard fired as designed), then 429 on retry burst.
Fix: server-side /filter (category='full', syntax from HF docs) + 429 backoff + /rows fallback
with preserved cap regression. 6 red→green respx tests; suite 106+5; fault-injection RED+revert.
Lesson: the "failure" was the control working — loud abort turned a wrong-leaderboard bug into
a same-day fixpack.

## 2026-08-11 (4) — FP-M2-2: Arena category value + snapshot semantics (Claude, Cowork)
Owner's run #3 showed FP-M2-1 applied but Arena still red. Live probes: category='full' → 0 rows
(invented fixture value; live value is 'overall'); with the right value, 386 rows spanning MULTIPLE
publish dates → keep-best-score would have published a stale-but-higher rating. Fixed both:
'overall' + newest-snapshot-only with counted drops; fixtures corrected in 5 test files.
107+5 green, fault-injection ×2 RED+revert.
Lesson: a fixture value invented without a live probe is an untested assumption in test clothing;
contract tests proved SHAPE but never VALUES. New doctrine candidate for EXPERIENCE/seeds.

## 2026-08-15 — M3 kickoff + W0 (GP v4.3.1 migration) — lead agent (Cowork), new session
Handover consumed (docs/HANDOVER-model-ranking.md); gate verified green on a fresh clone before any
change. Process baseline moved v4.2 → v4.3.1 (owner directive). m3-plan.md drafted, owner-signed
same day with Q1-Q4 locked (core-4 providers, USD-first, 30-day staleness, weekly CI cadence) and
one amendment (no stops between waves; owner tests post-milestone). Epoch → M4 (owner). W0 executed:
18 GP-INTERNAL files removed, 6 missing PROJECT paths added, tooling/templates synced to v4.3.1,
5 governed records got frontmatter, English rule adopted (L1 + reasoned .language-allow). Fresh-eyes
review caught the .gitignore *.db mitigation clobber (BLOCKING, fixed byte-identical) + 4 MINOR.
gitleaks run: 1 false positive, escalated (W-001), not suppressed.
Lesson: a template sync is a WRITE like any other — diff it against the mitigations history, not
just against the template; the reviewer, not the author, caught the one line that mattered.

## 2026-08-15 — M3 W1-W3 + closure (agent-side) — lead agent (Cowork), same session
W1: plans/plan_models schema + curated data/plans.yaml (9 plans, 4 providers; every value probed
live same-day; disputed Google AI Plus price EXCLUDED). W2: staleness window + budget caps as
data; weekly CI re-verification job (unconditional). W3: recommend --subscription (unscored plans
disclosed, stale rows named); ArenaClient url-param debt closed; ALL workflow actions SHA-pinned
+ pin-check grep gate (V4C-49). Closure: security PASS (0 BLOCKING; INV-12/13/14 candidates),
first retrospective (M>=3), EXPERIENCE entry, D-107/D-108 proposed, closure-report-m3 + Q1
quarterly handover generated. REQ-CAL-001 OPEN (Arena unreachable from here; owner fetch or
descope at the milestone session). Suite 107 -> 150 unit tests, make check = 7 gates green.
Lesson: describe a scanner trigger, never quote it — the ledger row about a false positive
re-tripped the scanner twice; documentation is also an input to the gates it documents.

## 2026-08-15 — M3 closure addendum: REQ-CAL-001 closed on live data — lead agent (Cowork)
Owner fetched the live Arena overall board (389 rows, one snapshot 2026-08-12) after two failed
command attempts (my URL bug: config=default vs text). Recalibrated the assistant thresholds as a
DATA edit: min_quality 1300→1400 (1300 admitted 57% of the board), close_call 5→8 (at 5 Elo 100%
of top-60 pairs still have overlapping 95% CIs), value_window 30 kept and justified. Fresh-eyes
review recomputed every published figure from the raw pages (all reproduced) and found the
calibration UNDEFENDED: reverting close_call left the suite green. Mandatory tests added, alias
constants asserted against the category record, analysis script committed, four documents that
still called the criterion open corrected. Gate: 152 unit + 5 gated, 7 gates green.
Lesson: a threshold that no test defends is a comment with a float attached.

## 2026-08-15 — M4 waves W1-W4 + closure — lead agent (Cowork)
Four waves, no owner stops (standing amendment). W1 registry expansion (drops 2→0, 4 BLOCKING
found and fixed); W2 provider rosters as a second documented source (assistant coverage 3/9→5/9);
W3 coverage + source health as measured numbers (found: SWE-bench silent 170 days, Aider 316);
W4 boundary rounding + plan equivalence. W4 needed TWO fresh-eyes passes: the first round's fixes
shipped a defect class of their own and, worse, shipped undefended — caught only because the fix
delta was re-reviewed. Closure: security PASS (0 BLOCKING, 6 MINOR — 2 fixed here, 4 ledgered);
quality gate BLOCKING because I restated a SIGNED criterion ("≥3 distinct plans") after the live
data showed 4 of 5 scoreable plans run the same model. Escalated to the owner immediately per the
standing rule; D-109 (rounding boundary) and D-110 (equivalence disclosure) written; PRD §11 added
so M4's REQ-IDs are no longer only in the signed plan. Gate: 193 unit + 5 gated, 8 gates green.
Lesson: a fix written to close a review finding is new code and inherits the review obligation.

## 2026-08-15 — M4 sign-off + M5 plan + handover — lead agent (Cowork)
Owner verified M4 on his own machine and signed it; D-109/D-110 ratified, Epoch criteria accepted as
a diff to M5, W-001 carried. Drafted the M5 plan (coding-category rescue) against the Epoch bundle he
fetched, with two owner decisions locked: rank on ONE named effort level and disclose the range;
choose the primary benchmark only AFTER W1 measures it. Then wrote the agent-to-agent handover and
ran a fresh-eyes VERIFIER over the whole handover package before shipping it — which found 13 false
or misleading statements, three of them load-bearing: the plan claimed Epoch's SWE-bench would make
the coding evidence fresher (for OUR models it is a day OLDER, so W1's rationale was wrong), it
listed four effort levels where the data has five (`low` omitted — and `low` is where the spread's
bottom sits), and it named W-007 as a ledger row that had never been written. All 13 corrected;
W-007 added; W-002/W-005 re-assigned to M6 so the ledger and the plan agree.
Lesson: a handover is the one artifact where a wrong number compounds — verify it adversarially
before shipping, exactly like code.

## 2026-08-16 — M5 W1-W4 implementation — lead agent (Codex)
W1 ingested the owner-fetched Epoch SWE-bench board and measured selected-plan freshness rather
than substituting the source-global newest date. W2 made reasoning effort part of score identity and
locked same-harness/same-source range disclosure. W3 applied DeepSWE to a separate agentic-coding
category: 50 source rows became 49 stored, six plans scoreable, all six honestly undated. W4 added
the Epoch licence citation, an independent 90-day acquisition clock, explicit schema migration,
selected-roster staleness, budget-exclusion disclosure, and removed Arena's self-rate-limiting
fallback. The implementation is ready for fresh review; final M5 acceptance and D-111 remain the
owner's milestone-gate decisions.
Lesson: freshness is not one timestamp — acquisition, source telemetry, and selected evidence must
remain distinct clocks in code, tests, and user output.

## 2026-08-16 — M5 closure, inherited mid-milestone — lead agent (Cowork)
Took over M5 from another agent that ran out of budget at a `wip: NOT reviewed` W4 checkpoint with
four files uncommitted and no review of any kind. Reconstructed the tree from a bundle, verified
nothing was lost, then ran the reviews the wave never got: fresh-eyes code review (3 BLOCKING + 9
MINOR), security review (1 more BLOCKING + 7 MINOR), quality gate (BLOCKING on one criterion). Fixed
all four BLOCKING plus seven MINOR, ledgered five, and found one defect no review caught by running
the owner's real Epoch bundle through ingest: kimi-k2.5 and kimi-k2.6 folding into kimi-k2, so MAX()
published the newer model's score under the older model's name. Wrote D-112 with the measured trade
(no effort level keeps the coding board: 28 models today, 19 at best under any policy) so the owner's
ruling is a signature rather than an open question. M5 closes on two owner items: D-112 and the
migration review permission-matrix §11 requires.
Lesson: a guard that cannot fail is worse than no guard — the W4 structural guard asserted the
predicate it had filtered on and stayed green while the defect it named shipped in the payload.

## 2026-08-16 — M5 gate, owner session — lead agent (Cowork)
The owner pulled the closure bundle and ran the gate himself for the first time in this milestone:
`make check` 7/7 green, 271 passed / 12 skipped, and 278 / 5 with `EPOCH_DATA_DIR` mounted on his own
Epoch bundle — the first independent confirmation that the closing tree is green outside the agent
sandbox. He then ruled on all three §0 items in one sitting: D-112 and D-111 ratified, the schema
migration reviewed and approved (permission-matrix §11 discharged), and W-011 ruled RE-AUTHOR, so the
twelve placeholder-email commits are rewritten to the identity that actually wrote them BEFORE the
first push rather than after it. The quality gate's single BLOCKING item cleared on the ratification,
not on new code: the citing tests for D-112's rule already existed and had already been shown able to
fail. Two ledger rows closed with the ruling; W-001 survives into a fourth milestone.
Lesson: escalating a criterion-meaning question with the measured cost of each option attached turns
the owner's gate from an open question into a signature — the block cleared in one sitting because
the decision arrived with its price tag, not with a request for guidance.

## 2026-08-16 — M6 planning + GP v5.0 migration — lead agent (Claude Code, local lane)
A new agent took over at the M5/M6 boundary from `handover_rocky.txt`, verified the state itself
(`make check` exit 0, 271 passed / 12 skipped, tree clean, `main` = `origin/main`, W-011's re-author
confirmed executed across all 22 commits), and asked the carried question with the trade laid out.
The owner ruled **A — present BOTH coding answers**, then signed the M6 plan and, in the same
session, directed the move to **GP v5.0**. Two ADRs recorded it: D-113 (baseline, supersedes D-108)
and D-114 (local-lane git authority, supersedes D-106 — the agent stages, the owner commits). The
migration was done with v5.0's own `make export-project` into an empty tree and applied file-by-file,
because the export script refuses a non-empty destination by design and a directory copy would have
imported 23 GP-INTERNAL records. Two self-inflicted errors, both caught by the gate rather than by
review: copying the template `src/__init__.py` broke the project's src-layout (64 mypy errors), and
quoting the owner's ruling in its original Turkish tripped `L1` in the ADR that recorded it.
v5.0's new `conformance/` suite then produced three findings on first run — a `.governed-records`
glob that matched no file (so **20** wave-close records had never been governed by anything), a
removed Make target still named by three historical records, and a superseded handover still telling
agents to commit. The owner ruled all three: fix, hand back, banner. Fixing the glob surfaced `R1` on
all 20 records; frontmatter was added without altering one line of content.
Lesson: a control's first run is a measurement of the past, not of the change that installed it —
every one of these findings had been true for milestones, and the only new thing in the repository
was something finally looking. Budget the first run of a new gate as discovery work, not as setup.

## 2026-08-17 — M6 closure — lead agent (Claude Code, local lane under D-117)
Four waves closed, ten BLOCKING findings across three review seats, all fixed and re-verified.
Stage 4.1 traced nine criteria with DERIVED file:line evidence rather than transcribed — three seats
had caught this author transcribing numbers that did not hold, so the trace is generated. D-116
closed OQ-3 with an ADR that exists, repairing a citation that had pointed at D-110 for two
milestones; D-119 and D-120 recorded shapes that had shipped without one. W-001 closed after four
surviving closes, in one message, once it was put to the owner as a decision rather than a status.
The L.8 dependency gate ran green for the first time in the project's history, and its own first
version was wrong in exactly the way it exists to catch. `handover_q2.txt` generated (M % 3 == 0).
Lesson: an enumeration that is typed out is a denylist wearing better clothes — four instances in one
milestone, each missing precisely the member with real exposure; and ten of ten BLOCKING findings
were reachability failures, which is the property this project's citing tests are worst at.

## 2026-08-19 — M8 closure (agent-side)

- Nine categories wired end to end; six added as DATA with no branch in the scoring path. The iOS
  app fetches `/v1/categories` and reaches all of them; failure states verified by stopping the
  engine.
- Three seam gaps found by the agent's own tests, none by reading: a `boards` parameter that never
  reached the caller, an attribution guard narrower than the rule it cited, and a disclosure
  (`ranking_effort`) that no view mentioned.
- Calibration corrected for the THIRD time against a different wrong population; the ranked set is
  the reconciled-and-priced subset (58 of 521 on ECI), which has no name in the codebase — W-037.
- Records: `docs/closure-report-m8.md` (draft, awaiting signature), `m8-retrospective.md`,
  `m8-security-review.md` (self-review, PASS 0 BLOCKING), three wave-close records, W-035..W-039.
- Two DoD rows closed RED and were stated rather than absorbed: no fresh-eyes review on any wave
  (three PRESSURE bypasses, `C2b` fired), and no deploy (D-123 undischarged for a second milestone).
- Procedural fix adopted after a third recurrence: never embed markdown containing backticks in a
  `python3 -c "..."` shell string — the shell expands them and words vanish from the file silently.

Lesson: **a control whose scope is narrower than the rule it cites is not a gate** — and the space
between two individually correct components is where neither component's reviews can look.

## 2026-08-19 — M8-W5: the review the owner authorised after C2b fired

- Three independent seats read `bfd93bf..HEAD`, the fifteen commits no fresh eyes had seen. All
  three returned BLOCKING. Author's fault-injection claim (23/23) did not survive an independently
  designed set: **12 of 47**.
- Live defects closed: one model published with two different scores in one payload (D-109);
  `run_date` accepting any ten characters as a date, so `'<script>al'` was served as evidence
  dating; a client that followed server-chosen redirects; an ATS refusal reported as "the engine
  is not running".
- `epoch_board.py` went from 32% coverage and zero tests to 91% and 26. Its bundle-escape guard
  cited M5's `/etc/shadow` finding in prose while carrying no test — the check was inherited, the
  proof was not.
- Records that stated the opposite of reality were corrected in place with the error named: the
  closure report, two wave records and the retrospective all claimed D-124's `/v1` window was
  unspent when D-125 had spent it.
- Escalated rather than fixed: W-040 (unbounded ranking payload — bounding it honestly needs a
  second `/v1` revision D-124 no longer permits), W-041 (**no `--cov-fail-under`, the control that
  would have caught the 32% module**), W-042, W-043.

Lesson: **a test cannot fail if its fixture cannot reach what it asserts.** Three times in one wave
— scores already round, no secondary-benchmark rows at all, `stored == skipped == 2`. It is the
same defect as a control narrower than its rule, one level down: in the DATA rather than the code.

## 2026-08-21 — M8 closed, M7 carry-over worked, M9 planned

- Open warnings 22 -> 11. Five (W-002/-005/-008/-009/-010) had been FIXED at M6 with the rows never
  closed — the ledger denying controls that were present, for three milestones.
- Fixed here: W-019 (ASCII-Turkish guard; L1 detects an alphabet, not a language), W-025 (a 3.14 CI
  leg — the interpreter the authoritative run uses was the one no leg covered), W-028 (workspace
  sweep), W-029/W-032/W-015 closed on their real dispositions. GPF-006 filed.
- W-024 diagnosed and the diagnosis overturned the row: arena is not down, its `filter` endpoint is.
  Remedy prepared and REVERTED — it rewrites a security finding's citing test, which is escalate-now.
  Owner ruled to leave it, and W-027, open while nothing deploys.
- M8 ratified with two DoD rows red on purpose. M9 planned (`docs/plans/m9-plan.md`), unsigned.

Lesson: **reproducing a failure proves it is real and proves nothing about its scope.** A dependency
was written off for a milestone on one endpoint's word; asking the dataset directly took four
commands and four minutes.

## 2026-08-22 — M9 closed agent-side (the refresh), quarterly handover Q3

- Three waves: one cycle by hand, the refusal rule (D-128/-129/-130), then the lock, the escalation
  counter and the schedule. `launchd` plist ships and is NOT installed — the owner's command.
- An independent seat reviewed W2 and returned BLOCKING with three findings, all in rows that read
  COVERED. Worst: the refresh could not publish a FRESHNESS update, because the fingerprint
  hand-listed six fields where the payload published ten.
- It wrote 40 mutants where the author had written 24 and reported all killed; 8 survived. All
  eight now die.
- Out of band: W-024 closed. arena was never down — only its `filter` endpoint is, and it fails
  with no query at all. All nine surfaces answer for the first time.
- M8's carried question answered by REQ-REF-007 rather than by argument: there is one machine, so
  D-116 is currently a claim about a topology that does not exist.
- One commit went in on a red gate. Third time; the next commit says so in its subject.

Lesson: **the failure that looks like success is the one to design against.** An unattended process
that freezes is worse than one that publishes something bad — every gate green, every cycle exiting
0, the artifact quietly ageing. The plan NAMED that trap and it arrived anyway, through the
fingerprint rather than through the guard.

## 2026-08-22 — M10 W3+W4: the guards, and a fix that had already been made once

- W3 closed three carried warnings (W-037, W-050, W-051). The row bound was written twice: the
  first value, 5,000, is exactly `_MAX_PAGES * _PAGE` and therefore unreachable. Found by trying
  to write a test that fires it, not by reading it.
- REQ-EVI-002's accessor already existed; `scripts/arena_calibration.py` was still sizing
  thresholds off the raw board — W-037's own defect, alive in the script written to recompute
  W-037's record. Fixed, plus an `ast` gate so the next script cannot do it.
- Stage 4.0 returned BLOCKING: `f"file:{path}?mode=ro"` opens WRITABLE for four measured path
  shapes, on the path the refresh uses to read the live artifact. The correct construction had
  been in `adapter/main.py` with an explanatory docstring since M6. One definition now, in
  `app.workflows.schema`, with a gate.
- K.7 bypassed a fourth time; `C2b` fired at M8, named M9, and M9 closed without consuming it.
  ESCALATED as W-055 — a gate-definition change, so the owner's.
- 666 passed / 12 skipped, `make check` exit 0, 12 mutants across W3+W4, 12 killed.

Lesson: **a fix that lives in one module is not a fix.** A boundary rule and a single-definition
rule will collide, and the collision is resolved by moving the definition — never by duplicating
it. "Avoiding a dependency" is the justification that quietly authorises a private copy of
security-relevant code, and it is most persuasive exactly where the boundary is real.

## 2026-08-23 — M11: the reviewer became somebody else, and then a user arrived

- **W1** D-133: in the local single-agent lane K.7 means a SEPARATE SESSION reading policy from the
  protected base ref, and the review is a FILE. The first seat under the new rule returned BLOCKING
  on the machinery enforcing it. Two absences had cancelled into a green gate — `record_type:
  review` missing from the schema AND `docs/reviews/` missing from the manifest, so 44 files with
  an illegal type were never scanned. The gate then failed the one record in this project claiming
  K.7 was satisfied: it cited two review files that have never existed (W-056).
- **W2** 1,093 lines of Swift stop being unexecuted. `ios/Package.swift` compiles the SHIPPING
  sources. Nine of twenty mutants survived the first tests, all with the same shape: the assertion
  was made against a value the test built by hand.
- **W3** `/v1/budgets` (D-134) closes W-044 without spending a revision window. `contract-tests.yml`
  green for the first time in its life — it was structurally unpassable, not drifting.
- **W3.5** The design pass, and six defects the owner found by USING the app.
- **Closing audit** REQ-RUN-002 was a signed plan promise that never became a PRD row (W-071).
- 711 Python / 59 Swift, `make check` exit 0, 21 mutants across the milestone, 21 killed.

Lesson: **the smallest amount of running worth adding to a close is one person and one session.**
Execution of code found real defects this milestone and they were worth their cost; a person using
the app for twenty minutes found six that eleven milestones of gates had not, and five requirements
nobody inside the project would have written. A test suite cannot hold an opinion about what a
reader concludes from what they can see.

## 2026-08-25 — M12: the product stops speaking in the language of the measurement

- **W1** wrote D-119 and D-120, cited in 30 files and never written; `make gate` exited 2 on a
  clean tree and is what the post-edit hook runs; `C2b` had never fired in its life because it
  grouped on a column unique per row; the Turkish case-folding defect fixed before Turkish shipped.
- **W2** renamed six surfaces, put a RANK beside every score, priced in pages, and classified
  disclosures under D-135. Three council defects fixed: a false ordering note, `1x cheaper`, and an
  app telling end users to run `make run`.
- **W3** gave the app a budget picker. It had called itself budget-aware for a milestone while
  `ContentView` held `budget = "unlimited"` — a whole milestone of M11 work served a control that
  did not exist.
- **W4** D-136: `/v1` publishes the facts, the client writes the sentence. Turkish across the
  screen. `L1` narrowed to prose at the fourth occurrence of it blocking a record about Turkish.
- 781 Python / 121 Swift, `make check` and `make gate` both exit 0, 34 mutants across the
  milestone, 34 killed.

Lesson: **you cannot gate comprehension, but you can staff it.** A jargon list catches the words
you already regret; the 28-row inventory that drove this milestone came from a seat told to read
the product as a stranger and given no other job. Nothing mechanical produced it, and what made it
repeatable was a CHAIR rather than a check.

Corollary paid three times in two waves: **pin the claim, never the offset.** A test that fails
when text moves teaches people to leave text where it is.

## 2026-09-15 — M13: the question is the front door, and the numbers stop overstating

- **W1** (`3440abe`, 2026-09-06): four checks that said yes to things they should have refused —
  Pareto dominance, the startup probe, the refresh fingerprint, the runner's skip accounting. All
  four were found by a second opinion with no brief.
- **W2** (`10a521c`): D-138 publishes the margin and the second board's age on `/v1/categories`.
  The first review was BLOCKING (greedy bands ordered 47 tied pairs), the owner ruled rank ranges,
  and the re-review measured 0. M12 signed. A wall-clock fixture that expired on the day was pinned.
- **W3** (`cda57b1`): the question field is the only input; `Change` sheet, echo, alternatives,
  unmeasured statement, `RequestGate`; the budget strip and its code deleted. Focus verified on the
  simulator; the keyboard is the environment's, shown by a Safari control.
- **W4** (`3b13b11`): `Score 83.5 / 100`, `Score 1504.2 Elo`, rank-only ECI (D-140); `AFFORDABLE
  PICK`; a sub-dollar price no longer prints as `$0`. D-139 written late for council ruling A3.
- **W5** (`a5e3c89`): Stage 4.0 PASS WITH FINDINGS, and PASS WITH FINDINGS again on re-verification, with every MAJOR closed.
  - The `/health` memo keyed on everything the probe depends on.
  - Two invariant tests rewritten to assert data flow.
  - The three waived security passes ledgered, with D-141 proposed as the control review.
  - The Swift floor escalated.
  - `AGENTS.md` back under its cap: 156 → 149.
  - 874 Python / 215 Swift.

Lesson: **a ruling is a hypothesis until someone measures it.** Three council rulings were
overturned by measurement this milestone, the last one by a reviewer; the fix it forced (ranges)
is better than the ruling it replaced.

## 2026-09-22 — iOS visual refresh after the M15 handover

- Refreshed question, recommendation, ranking and detail presentation with shared adaptive tokens.
- Detected concurrent detail work after a quota pause; rebuilt the integration on a fresh snapshot,
  preserving its composer, tests, 257-test floor and governance records.
- Independent visual review passed; Python 922 passed / 12 skipped, Swift 257 passed, iOS build passed.
- Simulator verified both detail routes, Return/send, Turkish chrome and manual category correction;
  a Turkish coding-question routing mismatch was recorded in the new handover, not claimed fixed.
Lesson: after an interrupted session, compare the current owner tree before transferring a prepared patch.

## 2026-09-22 — W-115's owed router probe, and D-147

- Took the project over; `make check` was red only in `swift test`, six routing cases.
- Re-ran the M10 probe with a score-printing replica (`scripts/router_probe/`): 11 of 18 against
  18 of 18 at 855b44a; the two search hints had become hubs, and four rewordings did not converge.
- Wrote a 22-question held-out set BEFORE changing anything; the one-sentence tier scored 3 of 17.
- D-147 (owner-approved): six example questions per surface, scored as the mean of the two closest.
  Probe 21 of 21, held-out 18 of 22, Swift 257 of 257 with no test edited.
Lesson: write the held-out questions before the first change, or the probe measures the tuning.

## 2026-09-22 — M15-W4 closure

- W-113 resolved by running both scripts on one artifact minutes apart: `calibrate_board.py` counted
  board names (64), not models (41), and paired a model with its own snapshot in `close_call`.
  Owner ruled the corrected margins in: `vision` 7.8 / 31.2, `search_factuality` 4.9 / 19.5.
- Owner rulings: W-112 publish the floor on `/v1` in M16 under an ADR; W-111 derive the Swift floor.
- `check_records` C2b stopped the close at the third acceptance of V3C-02 and K.8; D-150 is the
  control review (clause 1 accepted, clause 2 proposed for the sign-off).
- Wave closes for W1 (late), W3 and W4, independent W3 and W4 seats, closure report, retrospective,
  EXPERIENCE, M16 plan.
Lesson: when two measurements disagree, run both on the same input before writing an explanation.

## 2026-09-23 — M16-W2 committed; DevFlow v6.0 adopted (D-155)

- M16-W2 pushed to `main` as 5fc3f02 on the owner's word, the last commit made that way.
- Owner adopted DevFlow v6.0 and ruled three options in session: the adoption itself goes through a
  draft PR; no AI attribution; the workflow changes ride in one separately marked commit.
- Installed by three-way merge (GP v5.0 tag as base): 36 files taken, 36 added, 23 merged by hand,
  15 retired. The project's own controls survived every conflict; D-155 clause 4 lists each place
  this project now differs from DevFlow, and why.
- `make gate` PASS: pytest 1015/15, Swift 268, client-decls 4 configurations, conformance 12 PASS + 2 NOT-EVALUABLE
  with every exemption a declared row, gitleaks clean, pip-audit clean, slopsquat clean.
- DevFlow defects found and reproduced on a clean clone before being written down:
  `docs/research/devflow-v6-field-findings-2026-09-23.md` (see the record for the count).
Lesson: merge a methodology upgrade three ways against the tag you installed, never copy over it.


## 2026-09-23 — M16 closed agent-side (W3, W4, check-fast, closure)

- W3 (#3): carry-forward (D-156) and D-148 floors; three independent rounds, the last PASS-WITH-MINORS.
- Plans re-verified (#4); ChatGPT's table counts as explicit (owner); a GPT-5 Thinking Mini leak fixed.
- W4 (#5, #6, #8) replaced "what people ask" on the owner's ruling: Epoch fetched by the refresh
  (D-158), layout drift, derived registry (D-157), Fable 5.1. The security pass and the full review
  each came back BLOCKING, and both were fixed; #6 merged before its review returned.
- `make check-fast` (#7), after the owner's hcs_maas_full: 89 s -> 33 s; `check` unchanged.
- Closure: Stage 4.0 security seat, coverage trace, closure report, retrospective, M17 plan.
Lesson: put "review pending, do not merge" where the owner decides, not in a checklist below it.

## 2026-09-23 — DevFlow v6.0 -> v6.4 (D-161)

- Applied `git diff v6.0 v6.4` three-way, as `UPGRADING.md` says; `src/`, `note.txt` and the
  handovers excluded. The conflicts in AGENTS.md, the Makefile, README.md and the ADR log were
  resolved by hand, keeping the project's own controls.
- Session commits now carry the owner's identity with `GP-Agent`/`GP-Task` trailers (owner ruling).
- v6.4's new gates found 82 text reads and writes with no encoding, and a `check-fast` without
  `--plan`; both fixed. `closes` stays out of `check:` (DevFlow finding 1).
- The workflow change is proposed in the PR for the owner, not made.
Lesson: an upgrade's new gates are the first review of the old tree; run them before resolving
anything else.

## 2026-09-23 — DevFlow v6.4 -> v6.6 on the same branch (D-161 amendment)

- Applied `git diff v6.4 v6.6` three-way; six conflicts, each resolved by hand. `check_fast.py` is
  DevFlow's now, with the project's legs in `stack.mk`; the coverage floor runs inside `test`.
- The v6.4 upgrade review (0/4/5/8) is answered: version scope derived, the date guard and the
  trailer check restored, wildcard allow rows removed. The owner ruled review depth "fully 6.4".
- v6.5's duplicate-key check found why the issue agent never ran: `pull-requests` twice in its
  workflow. The owner deletes the line; until then conformance is red on it.
Lesson: a new DevFlow gate is worth running against the owner-only files first -- it found a
workflow that had failed silently for six weeks.

## 2026-09-24/25 — #14, #15, #17 merged; M17-W2 (Arena's category slices) closed agent-side

- #19 (D-163), #20 and #21 (D-162) merged. #21's conflict with #19 in the ADR log and the ledger was
  resolved on its branch. Session commits carry the owner's identity (D-161, confirmed in session).
- M17-W2 (#22, draft PR #23) was built in a separate worktree, because the launchd refresher runs
  whatever branch the repository has checked out. It adds 35 boards from one parquet file per
  config (owner rulings: pyarrow; every meaningful slice). D-164: boards are fingerprinted and
  guarded.
- The untrusted parquet read took four security rounds and four code rounds. In-process checks
  could not bound pyarrow, which decodes whole column chunks. The owner ruled D-165 (a child
  process under a memory ceiling) and waived the three-attempts stop for one round.
- Mistakes found by others: CI was red on Linux while the Mac was green (`ru_maxrss`, mypy's
  platform narrowing); a crash test opened macOS crash dialogs on the owner's screen; the PR
  carried code before review; re-reviews were written beside the gated path, not to it.
Lesson: a limit on untrusted input is proven by the process that pays for it, on the platform
that runs it. Measure the parent as well as the child, and read CI before calling a round green.


## 2026-09-25 — #29-#36 merged, the engine runs as a service; M17-W3 closed agent-side

- #29, #30, #31, #34 and #36 merged. Branch protection is on (#13, applied with gh as the owner
  ruled). The engine now runs as a launchd service from a deployed copy (#32). Its first startup
  refresh published the 35 W2 boards.
- M17-W3 (#37, #24) adds eleven boards and the accessibility attribute, and ends derived models from
  moving aliases (D-166, owner ruling). It went red-first per phase.
- Measuring the first night against the served artifact found a real crash before merge: the
  refresh fingerprints the LIVE artifact, which predates the new table, so every night after the
  merge would have failed. Fixed red-first.
- The Code-Reviewer found six minors, the first Tester two BLOCKING items (the CI skip budget,
  and coverage of one module) and a second Tester two more minors. All were fixed on the branch;
  five issues were filed and triaged (#38-#42).
Lesson: a schema change is also a change to what the refresh reads from yesterday's artifact.
Measure the new code against the artifact actually being served, not only a fresh build.

## 2026-09-25/26 — M17-W3 merged and verified; three fixes; M17-W4 closed agent-side

- M17-W3 (#43) merged and deployed. Its first nightly refresh published and matched the pre-merge
  measurement exactly.
- On the owner's ruling, #38, #40 and #41 were fixed before W4 (draft PRs #46, #49, #47). Each fix
  was red first and had its own independent Tester.
- M17-W4 (#50, D-167, HIGH) adds `/v1/boards` (every board's standings as positions) and the
  phone's daily fetch and store.
  - The first Code-Reviewer was BLOCKING on effort: the standings departed from D-112 without an
    owner ruling. Fixed.
  - The security slice found nothing exploitable.
  - Four Tester verdicts in a row were BLOCKING on unproven behaviour, never on a defect. The code
    matched an independent implementation on 6,241 real board sets.
  - Three of those four were about the combination's ordering rule, so the owner applied the
    three-attempts stop. The combination left the wave (#61); a fifth Tester passed the rest.
- Mistakes found by others:
  - a red test read an https URL and reached the network (#59);
  - two review seats edited one worktree at once (#52);
  - a `make … | tail` hid a failing exit code before a commit;
  - a rename walked past a tripwire instead of going through it.

Lesson: one hand-picked fixture pins one wrong rule. For a rule whose mistakes can hide behind the
same output, write the property test against an independent implementation first, not after the
third reviewer finds the next coincidence.

## 2026-09-26 — issue 61, independent ordering proof before W5

- Owner approved restoring #61 separately and making tests green before the next stage.
- A temporary test-target-only whole-board mutant reproduced the proof gap with 130 assertion
  failures; it was committed red, then removed when the historical shipping implementation returned.
- The grouped-rank reference checks 1,200 seeded cases plus 300 metamorphic cases, including ties,
  duplicates and missing models. All ten injected wrong rules failed the new property tests.
- No UI, network, cache or served-score permission changed; the only position/sort permissions name
  Combine.swift under D-167. Final gate and independent Tester evidence live in the issue review.
Lesson: prove the oracle distinguishes competing rules before using its green result as evidence.

## 2026-09-27/28 — M17-W4 and #61 merged; a UI review parked as #63; M17-W5 closed agent-side

- M17-W4 (#62) and the combination with its independent proof (#65, for #61) merged. At the
  owner's request, "require branches to be up to date" came off branch protection.
- A UI review of the shipped screen found 14 findings. The owner parked them as one issue (#63),
  to reproduce once W5's screen settles.
- M17-W5 (#64, D-168, HIGH): the question selects a surface plus declared refinements, and the
  phone shows its own combined list when more than one board is chosen.
  - The owner ruled eleven questions, in Turkish. Two came from the on-device probe: a refinement
    is a language or a domain, never a "kind", because the model added kinds to most questions.
  - Driving the simulator with the real on-device model found two screen defects no gate could see:
    a removed chip that could not be restored, and a link that took no tap across most of its row.
  - The first Code-Reviewer was BLOCKING on three departures from settled rulings: D-112's effort
    notice lost, Ruling A lost on coding, and a `/v1` field with no ADR. All three were fixed.
  - A second Code-Reviewer, the Tester and the security pass each returned PASS-WITH-MINORS. Their
    findings were fixed or filed: #66-#74, each triaged.
- Mistakes found by others or by the gates:
  - the existing surface-schema pin had matched a doc comment since before this wave;
  - the probe record's figures mixed two schemas;
  - a flaky fetch test turned out to be a race in `bounded_get` (#71).
- My own mistake: a scripted edit broke `Router.swift`. It was reversed in place and checked
  byte-identical against `HEAD` before the edit was redone by hand.
Lesson: a text pin proves a spelling is present, not that the thing is closed. Where the value
itself can be read, as an encoded schema can, assert the value.

## 2026-09-28/29 — M17-W5 merged; #66 and #73 measured and moved to M18; M17 closed agent-side

- W5 (#75) merged and was deployed to the engine service (`release-3f2e91d`). The owner saw the app
  on the simulator after the install script's wrong-simulator bug was found and fixed.
- #66 (a note for input that is not a model search) was tried in five variants, and #73 (routing of
  coding questions) in three. Both were measured on independent held-out sets. Both fell short of
  the owner's bar, and the owner moved them to M18; the branches are kept as the record.
- M17 closure: the milestone security seat returned 0/0/5/10 and the repo review 16+5 findings.
  MINOR-1, MINOR-2 and review M1 were fixed red first, the records were corrected, and the rest were
  filed (#76-#86).
- From 2026-09-29 the owner asked the agent to proceed on its own recommendations.
Lesson: set a behaviour's bar after one baseline run, and verify on the real screen what no gate reads.

## 2026-09-29/10-05 — M18: the app on the owner's phone, the screen tested, the question read, a release prepared

- W1 put the app on the owner's iPhone over the home network, by opt-in, checking every Host
  (D-171). W4 and W5 cleared the engine's and the gates' backlogs (D-173). W2 gave the screen a
  committed UI test target (D-175) and Turkish throughout (D-176). All four are merged (#99, #109,
  #111, #116).
- W3 read the question: signals in code, a closed verdict from the model, and a one-tap question
  back. #73 met its bar. #66 held its false-positive bound and missed its catch bar. #113 missed both
  bars. The first held-out set was spoiled when the author read it; fresh sets came from a new seat.
  The pull request (#134) asks the owner whether to ship what holds.
- W6 wrote the security-invariants list (71 rows), locked every install (D-177), bounded the refresh
  in three limits, and put the data licences to the owner (#135). W7 took 13 open issues (#136). The
  three are stacked, open and unmerged.
- The owner asked the agent not to wait for merges, and to close issues once their fixes merged.
Lesson: a gate that matches a spelling is beaten by the next spelling; read the structure, and plant the violation.

## 2026-10-05 — the M18 closure: two independent reads, and a guard that never ran

- The repo review (17 findings) and the closure security seat (one MAJOR, five MINOR) both passed
  with findings. The MAJOR, which the review also found: `make deps` read no extra, so pyarrow left
  the audit with W6. It now audits the locks. Every finding is fixed (`d749403`, `c256864`) or filed
  (#137-#147).
- W7's CI was red on the live contract tests and the skip budget; fixed on its branch, now green.
- This session ran from the owner's home folder, so the repository's hooks never loaded. W7's
  force-push went through a guard that blocks it (#142, the owner's to change).
- The owner's bug-closing instruction is D-178; `note.txt` is retired; the M18 plan is reconciled.
Lesson: start the session in the repository, or the guards you cite are not running.

## 2026-10-05/07 — M19: what the reader sees, the phone's promises, the gates, the question again, a first release prepared

- W1 named 74 models as their makers spell them and made one release one model (#112, #129, #162,
  #130, #124; D-179, D-182). W2 held the phone's privacy and arithmetic promises on the compiled
  module (D-180, D-181; #85, #60, #107, #110). W3 put CI's skips, the plan's tier and an offline test
  run before the push (D-183). All three are merged (#167, #176, #184).
- W4 read the question a second time, on fresh held-out sets (D-184). #66 improved and missed its
  bars; #113 is where it was. The image rule's reach beyond `vision` drew three verdicts and came out
  (#191). Five review rounds; the pull request (#196) asks the owner whether to ship what holds.
- The owner called the release (W5): the engine ready for Fly.io with a public artifact (D-185, #88),
  the app ready for TestFlight, the force-push guard widened for the owner's approval (#142). The
  Stage 5.1 review was MAJOR, and its re-read MINOR. Nothing is deployed (#197).
- The owner asked the agent to stop waiting for merges, finish as draft pull requests, and fix the
  medium bugs and above.
Lesson: a rule that reads people's words meets the reviewer's next phrasing; measure its reach on a set, and stop at three.

## 2026-10-07 — the M19 closure: a reading change that broke the screen, and the release's verdict of record

- The repo review (MINOR: one MAJOR, fifteen MINOR) found W4's question-of-fact doubt had turned three
  UI tests red, unseen because no M19 wave ran `make ui-test`; fixed on W4's branch (`bd60265`, 19 of
  19). Its MINOR findings were drift (the architecture, AGENTS.md, the PRD, the plan, the ledger) and
  are fixed here or filed (#198 to #203).
- An independent seat read the release surface changed after the security re-read and wrote the
  verdict of record the release rules name (`docs/reviews/release-security.md`, MINOR: the owner may deploy once the pull requests merge).
- The 29 issues M19 took are in its GitHub milestone; M18's milestone is closed.
- The deploy, the TestFlight upload and the four OWNER APPROVAL hook commits wait on the owner.
Lesson: when what the reader is shown changes, run the screen's tests, even if only the reading moved.

## 2026-10-08 — the first release live, the owner's first session on it, and M20: our own list for every question

- The engine went live on Fly.io and TestFlight build 1 (0.1.0) was uploaded, both by the owner's
  hand. Their first session on the phone found "not measured" answers and a licence filter they had
  not asked for. They ruled D-186 (every source on TestFlight, licences before production) and D-187
  (an understood question is never "not measured"). The hotfix (#207) went through three review
  rounds and was merged and redeployed.
- The owner named the product's core: our own list for every question, built from many boards. M20
  planned it (D-188, proposed) in five waves:
  - W1: the engine names each surface's family of boards.
  - W2: the phone combines a family by mean percentile position.
  - W3: the question picks its family and its refinements.
  - W4: the combined list is the default answer, with Apple Intelligence's glow (#208).
  - W5: a rate limit on the hosted engine (#187), and a fresh labelled set (#195).
- Every wave closed on its seats. W3 and W4 each drew a BLOCKING first review: W3's code was
  reached by nothing, and W4's note claimed every model was on every board. Both were answered and
  re-reviewed MINOR. Draft PRs #213, #215, #217, #221, #224 and #225 are stacked in that order.
- The M21 plan takes the open queue, 44 issues, into its milestone.
Lesson: a sentence that describes an order is part of the order; test the words against the rule that made the list.

## 2026-10-08 — the M20 closure: one vote counted twice, and the release verdict for build 3

- The repo review was MINOR, with one MAJOR: W3's refinements, all Arena text slices, joined W1's
  families beside Arena's own text board, so one vote counted twice. Each wave was reviewed apart,
  so only the milestone review saw it. A refinement now takes the place of its vote's board
  (`refined_board`, D-188 clause 6), and a gate holds it. M2 to M9 are fixed or filed (#226).
- The closure security seat was MINOR. The release verdict of record stands for build 3. Its S1 to
  S4 are fixed: `/v1/boards` counts as thirty requests, the Host check runs before the limiter, a
  broken payload cannot trap the family path, and INV-88 and INV-89 are in the register.
- `make ui-test` on the closure: 18 of 19 and 2 of 2. The failing coding test passed alone (#227).
- The ledger's `commit-after-check-fast` control reached its third row, which is the owner's to rule.
Lesson: review the seams at the milestone's head; a wave reviewed alone cannot see what the next wave joins to it.


## 2026-10-09/10 — M21-W1 to W3: the data a reader sees, reading what is not a search, the phone's promises

- The owner asked for the open queue as drafts, then for the waves one at a time after a parallel run of
  three hit the usage limit. Each wave ran alone from then on.
- W1 (#236): one model per release (D-189), `web-dev` on LMArena's own board (D-190), the data's release
  named and checked before a deploy, standings that never block questions. Its first review was BLOCKING
  (releases still sharing scores), the second MINOR.
- W2 (#240): model comparisons from every registry family, the held-out gates, the UI fixture and the
  owner's judgement sheet ship; three reading rules (#194, #218, #222) came out after three verdicts each.
- W3 (#250): the compiled gate refuses more shapes and its fixture is its definition; five review rounds
  found records stating more than the gates hold, so the records now name the fixture's rules and point
  at the register (#248 sweeps the older ones).
- Every M21 session started outside the repository, so the hooks did not load (#142); the ledger row is
  the milestone's.
Lesson: a record that describes a gate in prose will be wider or narrower than the gate; point at its definition instead.

## 2026-10-10 — M21-W4: the controls

- The close checks read what the reviews said they missed: a close's commit range (the HIGH rule's diff,
  an ADR first written beside its code, a process-log heading inside the range; #183, #201, #203), the
  decision log's pointer pairs (#200), and a ledger row for each skipped gate and each session started
  outside the repository (#202). CI's needs are read from its workflow (#182), and the tests that read the
  checkout through git say so (#249).
- The Swift legs run inside the offline profile (#179), and the deadline tests again on a one-thread pool
  against a timer off the pool (#181). The fetch-deadline test's margin (#178) and the coding UI test's
  scrolling (#227) were too tight for a loaded machine.
- Fifteen cited test names and the records that restated a gated property were swept, with two narrow
  checks over hand-kept lists (#248).
- The Bash guard's second reading (#189) is in its own OWNER APPROVAL commit; CI's history and offline
  halves are patches on #122 for the owner; #108 is carried, since its measurement traps a process.
- D-192 was committed after `make check-records` but before `make check-fast` (`9cf8e12`); check-fast
  passed after it with no change.
- The wave's Code-Reviewer returned BLOCKING (`fa37f8e`): the guard's second reading stopped at a comment
  and took a redirection for a command (B1), and the range rules read whatever range a close typed (M3 to
  M8). The guard now has a lexer of its own (`64b862a`, for the owner's approval), the ranges start at the
  wave's base (`da6b95f`), and every `swift test` runs under a watchdog.
Lesson: a rule that reads history must say what a pruned history means as well as a missing one: a branch
deleted after its merge read as an unreadable range.


## 2026-10-10 — the M21 closure: two reviews, three rounds on the fixes, and the waves merged as one

- The repo review was MINOR, with two MAJOR findings: W4's close rules met the rest of the milestone.
  Two bypasses had no ledger row (M1), and a first wave stacked on an unmerged closure was refused (M2).
  Both are fixed, and M3 to M11 are fixed or filed (#252).
- The closure security seat was MINOR, and the release verdict of record stands for v2 on six
  conditions, which the runbook's v2 section follows. S1 to S6 are fixed, S7 narrowed #245, and S8 is
  the owner's `/hooks` check.
- The owner ruled on two controls at their third row:
  - `commit-after-check-fast`: fix it and narrow it. A commit-msg hook runs `make check-fast`,
    `make check-docs` for a docs-only commit, or `make check-red` for a declared red test commit
    (R-1).
  - `repository-hooks`: fix it. Sessions start in the repository, and `make hooks` is run once.
- The closure fixes review took three rounds. Round 1 was BLOCKING on the commit gate (it refused red
  commits), and round 2 was BLOCKING on the write refusal (linked worktrees left open). Round 3 was
  MINOR, and its fixes are in (#254 to #256 filed).
- Two fix commits were checked together with the commit after them, not on their own trees (`cd563f5`,
  `85f80e3`). They are two `bypass` rows after the ruling.
- The owner merged the waves as one pull request (#251, a merge commit), and 45 issues they delivered
  in full were closed. GitHub also closed #194 and #222 through `fix: #N` in two commit subjects; both
  were reopened (#255).
- v2 is 0.2.0, build 4. It is not deployed yet; the runbook's v2 section is the owner's.
Lesson: a gate's exceptions are part of the gate. A hook that the DevFlow's own red commits cannot pass would have been bypassed at the first fix.

## 2026-10-12 — v2 deployed, a startup refresh, and the owner's ruling on the licences

- The owner merged the M21 closure (#257) and asked for v2's steps. `make check` was red on two tests
  that read the clone's own `advisor.db`, built on 2026-09-24; a copy the new code built made it green.
- The Mac's engine would have waited a night for a refresh its release built, which the deploy needs
  (#198). At the owner's request it now refreshes at startup when the served data was built by another
  release (#258, #259); it published a minute after the install, and the owner deployed.
- Committing #258 found that the commit-msg hook refused every commit that ran the tests: git exports
  the commit's author and dates to the hook, and the identity self-test's throwaway commits took them.
  `scrubbed_env` drops them. The hook had never run a test-running commit before the owner's `make hooks`.
- The owner ruled on D-185's table (D-193): no source is left out, MMLU and SWE-bench are credited, and
  every publisher is credited on a Credits screen (#260). Terminal-Bench 4.0 is feasible in one wave,
  at about 17 models against 42 (`docs/research/terminalbench-4-feasibility-2026-10-12.md`).
- #260 took two review rounds and a Tester. Round 1 was BLOCKING (Epoch's CC BY claimed for its
  compilations), round 2 MINOR, and the Tester BLOCKING (the sheet's behaviour had no citing test). All
  are fixed; #261 and #262 are filed.
Lesson: a hook is tested by the commits it gates. The commit-msg gate passed its own tests and every
commit in the closure, and still refused the first ordinary commit in the owner's clone.


## 2026-10-13 — the unlicensed sources move to licensed data (D-194)

- The owner merged #263 (Credits), deployed it and uploaded build 5. They asked for each unsettled
  source's licensed alternative instead of waiting for permission (D-194, #265).
- models.dev (MIT) replaces OpenRouter's prices, read from each model maker's own entry. Its catalogue
  also resells other makers' models under a maker's name; the first build priced Zhipu's GLM at
  Alibaba's price until `registry.named_vendors` refused them. 314 models are priced, against 311.
- `computer-use` ranks on TB 4.0's Apache-2.0 leaderboard repository: 21 models, all priced. TB 2.0's
  Apache-2.0 raw submissions were measured and not taken: they keep submissions the official board took
  down for cheating.
- `abstract` ranks on ARC Prize's MIT public-evaluation runs. Hugging Face answered 429 a minute into
  reading them, so the scores are derived once at a pinned revision and committed, with a contract test
  on the revision. Only 32 of 70 settings carried a summary, so every setting is scored from its
  attempts, and the summary's own score is reproduced.
- The review was BLOCKING twice over. ARC Prize had left whole settings unmarked (`correct: null`), and
  the derivation read them as wrong: GPT-5 Pro and Claude Sonnet 4.5 were served at 0. They are scored
  against ARC-AGI-2's published solutions now. And the new code refused to boot on the artifact `main`
  built, so the install would have rolled back before the startup refresh could replace it; the
  retired sources stay attributed for that artifact. Round 2 was MINOR: the unmarked attempts were
  paired with solutions by position, and GPT-4.1 had answered a task set ARC Prize changed after it
  ran. Paired by index, the comparison agrees with every one of ARC Prize's 16,681 marks.
- The Tester was BLOCKING: no test ran the two new boards through the ingest the build registers, and
  ARC's "a task not run is 0" rule had none. Eleven of 28 planted faults survived; each has a test now.
- DeepSWE waits for the owner's Hugging Face token: the dataset is gated, and its format cannot be read.
- A worktree's `make install` through a `.venv` symlink had rewritten the owner's editable install, and
  their deploy failed until they reinstalled (#264). This wave's worktree built its own venv.
Lesson: a licence is a property of a copy, not of a benchmark. TB 2.0's licensed copy held what its own
maintainers had withdrawn, and models.dev's makers' catalogues held other makers' models.

## 2026-10-13 — the backlog's data wave: makers' releases, speed tiers, and the night's figures (D-195)

- The owner asked to finish the open backlog before any further release. This wave took the data issues:
  #234, #232, #233, #230, #264, #235, #262, #266 and #269. #124, #241, #239 and #220 were closed as already
  delivered, and #267 by ruling (thinking budgets stay `unspecified`).
- The makers' pages were read for #232's candidates. Seven releases are split (Kimi K2 Thinking and K2.7
  Code, Qwen3-Coder 30B-A3B and Next, DeepSeek V3.1-Terminus, V3.2-Exp and V3.2-Speciale), Fireworks' `p`
  spellings reach their point release, and the GPT Cyber models are their own. #266's fix was not taken:
  OpenAI's guide makes GPT-5.6 Pro a reasoning mode of each model, billed at its rates.
- Three Code-Reviewer rounds (BLOCKING, BLOCKING, MINOR) and a Tester (MINOR). The first speed-tier fix
  was a regex: it cut Arena's only spelling of Kimi K2 Thinking off its scores (round 2's B1). A speed
  tier is now refused only as a price (`registry.price_refusal`). D-195's first Consequence was written
  from a link-preserving reconcile and was wrong in four places; it is now measured with every link made
  again, which reproduces `main`'s artifact exactly.
- #218 was attempted and reverted the same day: D-191 clause 2 had already taken that very rule out after
  three verdicts. #194, #218 and #222 start again only from #237's fresh held-out set.
- On the relinked artifact both refresh gates pass; the night's largest board change is 6 of 232 rows.
  DeepSeek V3's median is 0.89/1.0 (was 0.56/1.25), Qwen3-Coder's 0.975/4.65 (was 0.712/3.157), and
  MiniMax M2.7's and M2.5's fall about 20%.
- DeepSWE (#265) still waits for the owner to accept the dataset's terms on Hugging Face; the token works.
Lesson: read the ADRs of an issue's area before writing its test. D-191 named this wave's #218 rule as
taken out, and its failures as the ones to avoid; a search of the decisions would have found it first.


## 2026-10-14 — the reading wave: Turkish read through the embedding (D-196)

- The owner merged #270; its nine issues were closed. The reading wave started on #237's fresh held-out
  set (147 questions), written by an independent seat and unread by the author.
- Before, the wording tier left 8 of 89 searches "not measured", all Turkish: it declines what the
  recogniser is sure is not English. Apple's contextual embedding turned out to be one multilingual model
  for Latin script, so a Turkish question is now compared against Turkish examples, with no word list
  (D-191's class does not arise). The review (MAJOR) found that it changed general questions answered
  before, and read Azerbaijani as Turkish; both are fixed. Held-out after the fixes: searches right 59
  to 62, not measured 8 to 0, none lost. The example vectors are now kept: 147 rows probe in 33 s.
- #194 was closed on its own sign (1 and 3 of 89 searches asked on the model tier), #238 ruled (the four
  core brands stay models), and #218 and #66 stay open with the fresh set's counts.
- The leak gate missed escaped text: a held-out question written `\u{...}` in Swift passed it. It now
  decodes escapes and reads plain letters. Two of the wave's own sentences equalled held-out rows; they
  were removed unread.
- Three Code-Reviewer rounds (MAJOR, MAJOR, MINOR). Round 2 found the leak check had never read the
  app's `Router.swift`: it keyed files by name, and a fixture of the same name replaced it. Round 3
  narrowed the letter rule to the five letters Azerbaijani and Turkmen write and Turkish never does.
  Filed: #271 (L1 and escapes), #272 (the leak check and `docs/`), #273 (unsure languages on the English
  path).
- DeepSWE (#265): the token lists the dataset's files but cannot read them; the owner's access request is
  not yet granted.

## 2026-10-14 — the gates and licences wave: the pins read the built code, and the Credits sheet carries the licences (D-197)

- #253: A1 reads the pointer pairs both ways; D-176 and D-179 gain the `Amends` they implied.
- #247 (G-15 closed): every Swift pin in `test_router_hints.py` and `test_ios_client_contract.py` reads through
  `_code` or `_swift`, a raw read says why on its line,
  and `_swift` blanks block comments. The three probes the M21-W3 review planted now fail their pins.
- #246 (G-13 narrowed): a store makes no URL by a URL initialiser or by a decode whose type prints as `URL`, and the gap register's file
  references only the Foundation declarations measured on the shipping client (`STORE_FOUNDATION_ALLOWED`,
  since the backlog-gates review round 1's M2); the M21-W3 review's round-3 probe and a parse strategy are refused in all four configurations. A
  decode through a generic helper or a `typealias` is not (G-13, rounds 2 to 4's M1; #276).
- #244 (G-11 narrowed): no key path may name what a request sends, and each other file reaches only the
  engine-client members measured on it, matched whole (since the backlog-gates review round 1's M1).
- #245 closed on its remainder, which only a compiler can hold (#243's macOS lane, the owner's).
- #261 (D-197): each Apache-2.0 or MIT credit carries its copyright notice, and the sheet carries those
  licences' texts, held word for word by hash.
- #242 stays open: an allowlist for what a served number may meet would start from 123 distinct calls on
  the shipping client, each to be justified; it is its own piece of work.

## 2026-10-14 — the hardening wave: the gates read what the last two waves found them blind to (D-198)

- D-198 was committed alone, before any code (`7e89544`), as #274 now asks.
- #276: a store's `isFileURL` guard and its one read are one permitted expression, so a clause binding
  another `url` between them fails the egress pin; a Swift test loads the on-device store under the tripwire.
- #271: rule L1 decodes JSON and Swift escapes; the five sets and tests that hold escaped Turkish name why
  in `.language-allow`.
- #272: the held-out check reads `docs/**/*.md`. `reading_heldout_m22` overlaps one record written before
  it (`m21-wave-2-review.md`, three questions), held by file and count; the age check needs the whole
  history, so CI's one-commit test job skips it and the skip budget rises by one.
- #275: every pin file reads the app's Swift through `_swift`, or says on the line why it reads raw; one
  guard (`test_swift_reads.py`) reads every file under `tests/unit/`.
- #274: `make wave-check-all` reads a backlog branch's decision order. Run on the two merged backlog waves,
  it names D-196 and D-197, each written beside its code.
- The owner capped review rounds at four (2026-10-14): a MAJOR still open after round 4 becomes an issue.
- After the first two reviews (round 2 MINOR): the #275 pins read through `_code`, which drops `//` comments
  too, and `_swift` needs its reason; the record scan reads wrapped lines, backticks and blockquotes, and
  holds two older records (`m20-wave-3-review.md`, `m21-wave-2-review.md`); CI cannot run the #274 rule or
  the #272 age check until the owner's workflow fetches the whole history (#278).
- Lesson: a check that reads text is held only as far as its plants reach; each review round found a
  spelling the last one's plants did not try, so a rule's limits go in its decision, not only its fix.
- The Tester (MINOR): of 75 planted faults, 39 Python ones passed the whole suite; its 20 added cases catch
  32 of them, and the other 7 are equivalent, a belt, or a deleted assertion. The two Swift plants each
  failed only their store's new on-device test.

## 2026-10-15 — DevFlow v6.6 to v7.1 (D-199)

- The owner merged the hardening wave (#280), and five issues were closed. The owner then asked for the
  DevFlow v7.1 upgrade and chose a merged guard, heavy mode, and both deploy commands gated.
- `git diff v6.6 v7.1` was applied three-way, with workflows left out; 17 files conflicted. Two subagents
  merged the guard and the two record checkers; every project rule was kept or replaced by a stricter one.
- The ledger's `ruling` and `within-scope` rows and its milestone-wide waves were rewritten to v7.1's
  kinds and shapes, each marked in place.
- `make session-check` is red in this session by design. The owner commits and pushes from a terminal.
- Lesson: an upgrade over a project that grew its own copies of a version's features is a merge of two
  designs, not a patch. The conflicts were where the project had got there first.


## 2026-10-15 — The v7.1 upgrade's reviews, and the queue triaged (D-200)

- A new session started in the repository passed `make session-check`, so the upgrade was committed and pushed
  from it (`27d2022`, `18ebafd`), with `make check` and `make gate` green, and opened as draft PR #281.
- `make review-need` asked for `code-reviewer+security`. The Code-Reviewer found the ledger merge had loosened
  the three-row rule (BLOCKING-1) and let one wave's skip row cover its whole milestone (MAJOR-1). The owner
  accepted v7.1's reset (D-200) and chose exact matching. MAJOR-1, M1, M3 and a later NIT were fixed red first.
  Round 2 found no BLOCKING, MAJOR or MINOR.
- All eleven untriaged issues were triaged: #242 goes to a wave, and the rest are `work-issue`. The review's K1
  is filed as #282: removing a parent of `.claude/` passes the guard.
- Lesson: "every project rule kept or replaced by a stricter one" is a claim a merge cannot check on itself.
  The reviewer found the one rule that got looser by running `main`'s deleted assertions against HEAD.

## 2026-10-16 — Run product-night (light): the phone, the guiding note, the golden set

- Three changes are stacked on #291: #296 (#288, a device build reaches the hosted engine and keeps the last
  answer), #300 (#66, more small talk and meaningless text get the note; 11 of 72 non-searches caught against
  10 on the fresh set) and #302 (#289, 49 golden questions with a top 3 derived from a pinned snapshot).
- Three reading rules are stops (#298, #299, #303). On the fresh m23 set each scored the same as the shipped
  rule, so D-202 clause 6 holds them back.
- Fresh worktrees have no gitignored `advisor.db`, so the commit hook's `test` leg cannot run there. Copying it
  was refused, rightly. Implementers committed red tests, and the green steps were applied in the one tree
  that has the artifact.
- Lesson: an implementer worktree needs everything the commit hook needs before the work starts. Decide where
  the artifact comes from at dispatch, not when the first green commit fails.

## 2026-10-17 — DevFlow v7.1.2 (D-205) and run golden-night (D-206)

- **The v7.1.2 upgrade (#306).** The guard was ported from v7.1.2 with the project's rules carried over. Its security review ran four rounds:
  - a redefined `pwd` let `rm -rf "$(pwd)"` through, twice;
  - all of `/var/folders` counted as scratch.

  The owner applied the `.claude/` half.
- **The run stacked seven PRs on #308.** They include the golden misses #293 and #292, both measured on a fresh set (m24) and shipping on D-206's bar. #295 stopped after four attempts. The owner-only rows ended as one owner bundle, with the agent half already committed, so that only one owner line is left.
- **The owner-bundle review found #321:** `bash -c '...' --help` passed the guard unread, on `main` since `64b862a`. It is fixed in the bundle.
- **Lesson:** every agent's Write or Edit runs the post-edit `make check-fast` in the session's project tree, whatever tree the agent works in. With seven agents writing, those runs overlapped my own commits there and failed them at random. Keep agents' scratch files in their own worktree's `build/`, and expect retries.

## 2026-10-17 — upgrade/devflow-v7.2: the agent half goes green (D-207)

- With the owner patch applied in a dry-run tree, `make check` failed 11 tests; `ad7c2ad` fixes them: review-need's `A...B` split, the light-mode routing test to D-207 clause 1, the ledger legend's new path, AGENTS.md's commit-msg sentences, and `docs/feature-catalog.md` kept for a security-invariant test the agent may not change.
- `scrubbed_env` now drops the outer make's MAKEFLAGS: under v7.2 the post-edit hook was red after every edit.
- The owner waived the guard-change security review (one bypass row in `docs/control-events.csv`).
- **Lesson:** a dry run of the owner patch is the only place an upgrade's agent half can be proven green; run it before calling the half done.

## 2026-10-17 — plan/run-bug-night

- The owner opened run bug-night (light). The queue was re-triaged on fe35bc3 after #308: nine issues closed as fixed, the rest re-verdicted, and #331 and #332 triaged.
- Every reserved decision was asked once, through the chat's choice picker, and is D-209. #115, #243 and #323 closed on the owner's ruling.
- **Lesson:** a decisions message reads faster as a picker with a reasoned default than as a numbered list; the owner answered nine questions in two rounds.
## 2026-10-17 — fix/issue-295-task-before-ai

- The owner chose option (a) for #295 (D-208): a Turkish active participle with its own object right before "yapay zeka" names the task, and the question is read by the examples without those two words.
- Red first (82efabc: the golden known_miss removed). The golden set passes 41 of 41. On m24 a measuring seat counted 83 of 173 against main's 82: one gained, none lost.
- `make next-adr` printed D-1000, because it counts the historical D-999; the ADR is D-208 (filed).
- **Lesson:** where a score cannot separate two kinds of question, the question's grammar can; gate the reading on it rather than on a margin.
## 2026-10-17 — fix/issue-326-encoded-ref

- The release security review's N1: `_in_submissions` judged the decoded path while httpx sends the raw one, so `%2e%2e` as the ref passed. It now refuses any `%` in the raw path; two parametrized cases went red first (25829bc).
- The same session re-triaged the open queue after #308: nine issues closed as fixed, 22 re-verdicted.
- **Lesson:** a URL allowlist judges the bytes that are sent, not a decoded view of them.

## 2026-10-18 — fix/issue-331-main-clone-marker

- The main clone's `.gp/installed` said v6.6: every upgrade since 2026-09-23 ran `make install` in a temporary worktree only. `make install` ran once in the main clone (D-209 clause 4); its marker reads v7.2 and `make install-check` passes there. Its missing `environment.md` was copied in.
- On the way: `scripts/ci_diff.py` anchored `^gp_version:` at the file's start, so under the real marker's comment lines `make ci-diff` always answered "no `.gp/installed`". Fixed with `re.M`; the conformance test now writes the marker as the installer does (red at 3c0c0cb).
- **Lesson:** a fixture that writes a simpler file than the producer does tests the simpler file; write it as the producer does.

## 2026-10-18 · fix/issue-332-mcp-json — `.mcp.json` stays removed; two record corrections

- `.mcp.json` left `main` with the v7.2 apply (`7c45a5b`). Its restore stayed staged in the upgrade worktree and made every push there report `gate stamp: none`. The owner chose to keep it removed (D-209 clause 3): every GitHub step runs through `gh`, and no guard hook covers MCP tools. The staged restore was dropped.
- Correction to D-207: its "Mitigation if violated" names the upgrade's security review, but that review was waived by the owner (the `guard-change-security-review` bypass row in `docs/control-events.csv`, 2026-10-17). Run bug-night's owner bundle is reviewed before handover (D-209 clause 2).
- Correction to the format: the entries headed `## 2026-10-17 — upgrade/devflow-v7.2: …` and later in this file use `—` where v7.2's format is `## <date> · <branch> — <what it did>` (`/pre-merge` §8). The entries stay as written; this one and the run's later ones use the format.
- Lesson: an upgrade that removes a file the project added (here `.mcp.json`) says so in its PR, so the owner decides before the file is gone.

## 2026-10-18 · fix/issue-325-ignored-documents — documents() grades no ignored, untracked scratch

- `conformance/lib_record.documents()` walked the disk, so a gitignored note under `build/` turned `test-documented-paths` red, though its targets already came from git. It now skips what `git ls-files --others --ignored --exclude-standard` lists; a tracked file under an ignore rule is still graded, and without git the walk stays whole (D-209 clause 5). Red first: `tests/unit/test_documents_skip_ignored.py`.
- Lesson: a gate's inputs and its targets come from the same source, or scratch on one side breaks it.

## 2026-10-18 · fix/issue-330-next-adr — next-adr reads the run of ids, not its far-off names

- `scripts/next_adr.py` took the highest project id, and this project's D-999 ("the agent opens drafts; a human merges") made `make next-adr` print D-1000 after D-207. It now follows the run of ids and stops at a step wider than 100: D-999 is a name. On this tree it prints the id after D-209. Red first: two cases in `conformance/test-next-adr.py`.
- Lesson: a number used as a name breaks every "highest plus one" rule; say which numbers are places.

## 2026-10-18 · fix/issue-328-guard-test-timeout — a timed-out hook call is a finding, not a dead test

- CI once showed `test-bash-guard.py (no output) (exit 1)`. A per-case `subprocess.run(..., timeout=120)` that raised `TimeoutExpired` inside the thread pool would kill the test that way, and `run-all.py` now prints a dead test's stderr (81c974e). The case now reports `the Bash guard timed out after 120 s on <case>`. Red first: `tests/unit/test_bash_guard_conformance_timeout.py`.
- Lesson: a check that runs many cases in a pool reports each case's failure; one exception must not end the run.

## 2026-10-18 · fix/issue-341-conflict-markers — a committed conflict marker fails the tests

- The merge of #333 into the integration branch left conflict markers in `docs/decisions.md`. The commit gate passed, and the run's bundle agent was the first to see them. `scripts/conflict_markers.py` lists every marker line in a tracked text file (Markdown fences excepted), and `tests/unit/test_conflict_markers.py` holds both polarities and the repository itself, so `make test` and the commit gate refuse one. Red first.
- Lesson: after a merge with a conflict, read every conflicted path in the merge's output, not only its last lines.

## 2026-10-18 · fix/issue-314-answers-size — the kept answers' file is refused by its size before it is read

- `StandingsStore.keptAnswers()` checked its 8 MiB ceiling after `contents()` had read the whole file. `contents(atMost:)` now reads the file's size from its attributes first, and the store's one read stays the one pinned expression. The client gate's sink list gains the three Foundation names the size check uses (D-209 clause 6). Red first: `tests/unit/test_answers_size_before_read.py`; `KeptAnswerTests` plants a file at and over the ceiling.
- Lesson: a ceiling bounds the step it sits before; put the check before the read, not before the decode.

## 2026-10-18 · fix/issue-309-whole-test-observer — the network watcher covers the whole Swift test

- A request made in a subclass's `tearDown` that skipped `super`, or in a class set-up, outlived its test: the next test's drain failed instead, or nothing did in a parallel run. `OfflineTestCase.invokeTest` now drains before and after the whole test and fails that test while its run is open (D-209 clause 8). Red first: `WholeTestObserverTests` runs a probe that skips `super` (the probe lives in the base's file, the one place the skip rule allows).
- Lesson: wrap the whole invocation when a check must not depend on subclasses calling `super`.
## 2026-10-18 · fix/issue-319-policy-scripts — review-need derives its policy scripts

- `POLICY_SCRIPTS` held three scripts by hand, so a change to `scripts/wave_check.py`, the Bash guard, the Makefile's `review-need` recipe or a plan's `security-globs:` line routed to `none` in light mode. A script under `scripts/`, `.claude/hooks/` or `.githooks/` that names a policy module, target, field or `security-globs` at either end of the range is now a policy script; in the Makefile and the plans only a changed line that names one is a policy edit (D-209 clause 5). Red first: `tests/unit/test_review_need_derived_policy.py`.
- Lesson: derive a gate's scope from what the code names, and keep a hand-kept seed only where the names are the seed.
- The security review (PASS WITH FINDINGS, `docs/reviews/fix-issue-319-security.md`): M1 and N3 a `-diff` attribute hid a policy line and a parser (every diff now runs with `--text --no-textconv --no-ext-diff`); M3 a non-ASCII path was quoted (`-z`, `core.quotePath=false`); M4 the searched places are derived from the gate code's (`GATE_ROOTS`, which `GATE_CODE` is built from too); M2's six surviving mutants each have a case now; N2 `git grep -F -e`. N1 (a name split across lines or written in another case) is refused: a policy reader names its module, and the review found none that does not.
## 2026-10-18 · fix/issue-322-kept-answer-rules — the kept-answer rules read aliases, enum payloads and an existential, and must see their allowed sides

- #297's security review (M1-M3, N1), approved as a gate change by D-209 clause 5. `kept_answer_facts` expands each substitution through every `typealias` in the dump by its `type=`, holds an enum by its cases' payloads, and refuses a decode through an existential in every file. `_owned` matches `ContentView.load()` by its full name and its type by its full path.
- `unseen_permissions` now requires the load path's `keep` and each allowed decode on the shipping client, so a renamed `keep` or kept type fails the gate (fail closed).
- The fixture plants each shape the review found, and the five surviving mutants are each killed. A synthesised `init(from:)` called by name prints no location, so the old `.init(from:)` branch never fired on one. Red first: `test_322_*` in `tests/unit/test_kept_answer_provenance.py`.
- Lesson: a rule over printed types must read the aliases the dump declares, or it holds only the spellings it was shown.

## 2026-10-18 · integration/run-bug-night — run bug-night ends: twelve PRs stacked, the owner bundle reviewed

- The queue of D-209, bugs first: #295 and #326 stacked as drafts; #331, #332, #325, #330, #328, #341 (found tonight), #314, #309, #319 and #322 fixed red-first and stacked on #335. #319 was a policy edit and had its own security review, whose findings were fixed on its branch.
- The owner bundle (#256, #287, #305, #317, #318, #320, #344, #81) took four review rounds. Round 1 was BLOCKING: the #287 fix made an unknown value read as safe, a loosening. Rounds 2-4 closed that, the minors, and #344. Its agent half is `f716219` on `owner/bug-night-bundle-v2`; the owner's half is one patch in the owner's clone.
- The merge of #333 left conflict markers in `docs/decisions.md` that no gate caught; #341 now catches them.
- Lesson: a guard change that turns "unknown" into "allowed" is a loosening even when every listed case passes; a reviewer probing the old guard against the new one finds it, a test list does not.

## 2026-10-19 · fix/issue-328-maintenance-lock — the guard test's flake was git's background maintenance

- #339 and #343 went red in CI on `test-bash-guard.py`. Now that run-all.py prints a dead test's stderr, both showed `shutil.Error` on a vanished `.git/objects/maintenance.lock`: each fixture commit starts a detached `git maintenance run --auto`, and `main()` copies the fixture while it runs.
- #340 (the `TimeoutExpired` handling) had targeted the timeout #328 suspected; it stays useful but did not close #328.
- The fixture's `git()` now passes `maintenance.auto=false` and `gc.auto=0`; red test `tests/unit/test_guard_fixture_maintenance.py` first. review-need: none.
- Lesson: hold a flake's fix until the traceback names its cause; a fix built on the suspect closes the issue without closing the flake.

## 2026-10-19 · enhancement/golden-rules — the owner's Golden Rules at the top of AGENTS.md (D-210)

- Shown where the product stands against its goals, the owner set four Golden Rules as the project's backbone: every source used lawfully, every question understood by an AI model (Apple Intelligence, or another LLM), the most correct list for every question (composed by an LLM when no board ranks it), and no empty work.
- D-210 records them with the v1 order and the owner's two answers: Apple Intelligence in every case, another LLM only where it is missing; an LLM-composed list takes every number from our boards (D-104 stands).
- Lesson: measure the product against the owner's goals at every run's end, not only the queue; a queue of green fixes can drift from what the product is for.

## 2026-10-20 · enhancement/issue-351-apple-intelligence — Apple Intelligence measured, then raised: 107-111 to 139 of m24's 173

- `make model-tier` scores the on-device model for the first time, beside the wording tier, and keeps every question's row so two runs compare by an exact McNemar test.
- Raised on m24 (tuning): the request paragraph by D-169/D-211, surface descriptions, greedy decoding (one answer per question on one model version; two runs agree on every row), and the verdict naming the kind of a non-search (D-213). Searches 81-85 to 88 of 112; non-searches caught 23-27 to 51 of 61.
- The owner's three research reports were read against each other; the named kinds had been tried on #66 under the old line, so they were measured before the ADR, and kept on 8 non-searches fixed and none broken.
- The glow is on while Apple Intelligence is available and livelier while it reads. Retrieved examples (#353), prewarm (#354) and the m25 verdict (#355) are their own issues.
- Lesson: on a small model, fix the decoder before the prompt; with random sampling the 3-7 row noise hid every change smaller than it.
