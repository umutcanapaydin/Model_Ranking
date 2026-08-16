---
record_type: experience
id: model-ranking-experience
status: ratified
date: 2026-08-11
---
# EXPERIENCE — model_ranking (living; V3C-81 — quarterly handover BLOCKS without it)

## 2026-08-11 — M1: Data Layer + Recommendation Engine (coding)

**What the pipeline caught that I would have shipped:**
- W3 fresh-eyes review FAIL: my curated regexes false-matched REAL aliases (gpt-5-pro → gpt-5,
  flash-lite → flash, grok-4-fast → grok-4…) — the exact bug class the spike had, one layer deeper.
  Redundancy (a second reader probing with a real-world corpus) caught what the author's own tests
  could not, because the author writes tests for the failures he can imagine.
- W4 review BLOCKING: the engine emitted a factually false "why" when the quality floor was unmet.
  Lesson: every fallback branch needs its own honesty check — silent degradation plus confident
  prose is the worst failure shape for a recommendation product.
- The first LIVE run failed loudly on Aider duplicate model entries — a data condition no fixture
  modeled. The control (UNIQUE + loud SourceError + rollback) worked exactly as designed.
  **Doctrine adopted: the first live run happens INSIDE the wave, not after it.** (Seed candidate.)

**Friction (V4C-13):** `make check`/gitleaks deferred host-side ×4 waves (sandbox has no venv/gitleaks;
same tools ran directly). Same control deferred 4× — per the rule this triggers review of the CONTROL:
proposal → CI runs `make check` on the owner's GitHub repo so the sandbox gap stops mattering (M2).
- Cowork device bridge dropped mid-commit once (W2-W4 files); recovered next session, no loss —
  cloud workspace held state. Continuity-in-files worked as advertised.

**Starter defect found:** stray `src/__init__.py` breaks `make typecheck` (mypy src) — removed here;
should be reported upstream to the General_Pipeline template (candidate for its next cut).

**Numbers:** 4 waves · 74 tests · coverage 88% · 6 fault-injections (all RED, md5 reverts) ·
reviews: 14 MINOR + 3 BLOCKING found, all closed · live run: 2154 prices, 173+68 scores,
42 canonical models · security close: PASS, 0 BLOCKING.

## 2026-08-11 — M2: New Sources + Everyday-Assistant Category

**Owner amendments worked:** no per-wave git (milestone-boundary only) and council-instead-of-owner
for questions. No council convened — no decision rose to that bar; the closest was Arena's dataset
shape, resolved by evidence (WebFetch of the dataset card) rather than deliberation. Lesson: most
"questions for the owner" are actually questions for a primary source.

**What the reviews caught this time:** thresholds as code-branches (a third category would have
silently inherited Elo thresholds on a % scale — latent-debt class, caught BEFORE the third
category exists); assistant export overwriting the coding artifact; Arena page-cap silent
truncation; a CI smoke step whose failures vanished behind `head` (no pipefail). Pattern across
M1+M2: reviewers keep catching *the failure the author's imagination didn't contain* — redundancy
pays on every wave.

**Honesty engineering:** REQ-REC-006's stale disclosure is a deterministic proxy, and its
limitation (a never-refreshed DB cannot self-report stale) is now WRITTEN IN THE DOCSTRING rather
than discovered later. Doctrine: when a control is a proxy, its blind spot ships in its docs.

**Sandbox boundary institutionalized:** HF/OpenRouter unreachable from the build sandbox → live
verification moved to CI (weekly cron + manual dispatch). First live Arena/OpenRouter run happens
in CI — treat its first green run as a milestone-closure condition analog (M1 doctrine: first live
run belongs inside the wave; here the wave's live half runs where the network is).

**Numbers:** 4 waves · 109 tests (104 unit + 5 gated) · coverage 90% · fault-injection ×4 (all RED,
md5 reverts) · reviews: 11 MINOR + 2 PROCESS found, all applied · security close: PASS, 3 new
invariants · D-105 recorded.

## 2026-08-15 — M3: Subscription-Plan Table + GP v4.3.1 Migration

**The install-completeness rule earned its keep on day one:** `make install-check` (new in
v4.3.1) found this repo's v4.2 install wrong in BOTH directions — 6 PROJECT paths missing and
18 GP-INTERNAL files leaked — before any product code moved. The v4.3 field story reproduced
here exactly. Doctrine confirmed: a copy step with no declared contract cannot be wrong.

**A template sync is a WRITE like any other:** the W0 migration clobbered the `.gitignore`
`*.db/*.sqlite3` lines added by the M1 security review — caught by the fresh-eyes reviewer,
not the author. Lesson: diff template syncs against the MITIGATIONS history, not just against
the template. (Pattern count now M1+M2+M3: every milestone, the reviewer catches the failure
the author's imagination didn't contain.)

**Curated data flips the parser discipline:** fetched sources skip-and-count; an AUTHORED
table fails loud on any invalid row — a curation error is a bug, not noise. Corollary paid
for immediately: a disputed price (Google AI Plus, two sources disagreeing) does NOT enter
the table; the dispute is recorded and re-probed instead. Honesty at data-entry time is
cheaper than a fixpack later (the FP-M2-2 lesson, applied upstream).

**Mutation probing caught what the suite could not name:** the reviewer's `<=`→`<` mutation on
the budget-cap filter SURVIVED 148 green tests — no fixture priced a plan exactly at a cap.
V3C-72's stay-green rule forced the boundary test. Seed candidate: "for every threshold in the
product, one fixture sits exactly ON it."

**Scanner findings self-replicate through documentation:** the gitleaks false positive's own
LEDGER ROW re-tripped the scanner by quoting the trigger literal; so did the security review
quoting the ledger. Rule adopted in both files: DESCRIBE a scanner trigger, never quote it.

**Friction (V4C-13):** live Arena distribution unreachable from this sandbox AND via WebFetch
(4 attempts, ledgered) → REQ-CAL-001 carried to the closure session (owner-side fetch or
descope). GP-upstream notes: `make wave-check` cited by the template but no such Makefile
target ships; `scripts/check_records.py`/`journey.py` fail their own repo-wide ruff/black.

**Numbers:** 4 waves · 150 tests (+43) · reviews: 2 BLOCKING + 8 MINOR found, all closed ·
fault-injection 7 faults, 6 RED + 1 stay-green → mandatory test added · security close: PASS,
3 new invariant candidates (INV-12/13/14) · gitleaks: 1 ledgered false positive · live e2e:
9 plans + 2176 prices + 173 SWE scores → three plan answers with 7 plans honestly unscored.

**Closure addendum (2026-08-15, same day):** REQ-CAL-001 closed on live data the owner fetched
out-of-sandbox — and the review of that data edit produced the milestone's sharpest lesson:
**a calibrated NUMBER needs a test that fails when the number changes.** Reverting `close_call`
8→5 left all 150 tests green; the value was written down, not defended. Second stay-green fault of
the same class in one milestone (the other: the budget-cap boundary). Doctrine adopted: every
threshold ships with (a) a fixture sitting exactly on it and (b) a citing test that dies if it
moves. Corollary for records: a calibration document must ship its analysis SCRIPT — percentile
method and bucketing convention silently shift the published figures, and this lineage has already
paid once for a report whose own arithmetic could not be reproduced.

## 2026-08-15 — M4: Make the Plan Answers Real (data depth)

**What the pipeline caught that I would have shipped:**
- W1 review, FOUR BLOCKING, all silent correctness: a new model folded into its base family
  (`deepseek-v4-flash` → the base rule), a coverage number quoted wrong inside the record that
  existed to defend it, a guard that blocked date stamps as if they were version tokens and so lost
  a live score, and `gpt-5-pro` swallowing four Pro variants. Not one of them would have failed a
  test I wrote, because I wrote tests for the failures I could imagine.
- W2 review BLOCKING: a new tie-break and its provenance output had **no citing test** — both
  mutants stayed green. My first replacement fixture then passed the "removed" mutant *by
  alphabetical luck*; the fixture had to be rebuilt so the two orderings actually disagree. A test
  that passes for a reason you did not intend is not evidence.
- W4 review BLOCKING: equivalence was computed only against the quality pick, so on live data it
  said **nothing** in the one case that mattered — the quality pick alone, both other labels
  collapsed onto a $4.99 plan that a $99.99 plan ties exactly. The most valuable sentence in the
  dataset was one comparison away from never being written.
- **The one that matters most — the second review pass:** the fixes I wrote to close W4's findings
  were themselves reviewed, and that pass found the display-delta fix shipped with **no citing test
  in either engine**, plus three more defects it had introduced or left (a budget-excluded plan
  could be advertised inside an equivalence group; group membership was re-resolved by display name
  in a table with no UNIQUE constraint on names; the group sentence claimed plan pages "list" a
  model when a roster-linked member's page lists nothing).

**Lesson (the milestone's transferable one): a fix authored in response to a review is NEW CODE and
inherits the review obligation.** "It was written to close a BLOCKING finding" feels like evidence
of correctness and is not. Fault-inject the FIX, not only the original defect; re-review the fix
delta with fresh eyes before the wave closes. This is V4C-49's shape (a rule shipped without its
gate) applied to fixes rather than to rules.

**Second lesson: a signed criterion can be wrong, and the honest move is to block on it.** M4's
headline criterion ("≥3 distinct plans, live") was written before anyone had measured the data.
The data said 4 of 5 scoreable plans run the same model — so the criterion could only be met by
recommending $99.99 over $4.99 across a difference of zero. Restating it in the open, writing the
ADR, and letting the quality gate go BLOCKING until the owner signs is the correct handling; the
cheaper move is to notice earlier. **Rule adopted for the next plan: any criterion containing a
number about live data gets a measurement task in the wave BEFORE it.**

**Third: the coverage metric earned its keep on day one** by measuring something uncomfortable —
the coding category can rank 1 plan in 10, because SWE-bench has published nothing since
2026-02-26 and Aider since 2025-10-03. A product risk that used to be a demo surprise is now a
number with a date next to it, in CI, on every run.

**Friction (V4C-13):** epoch.ai and huggingface.co are proxy-403 from this container, so
REQ-ING-010 and the fresh-benchmark ingestion could not be written without inventing a shape —
the FP-M2-2 defect this project has already paid for twice. Both stayed OPEN and visible, with
owner-fetch commands delivered, rather than being satisfied by a fixture. **Process gap found: the
warnings ledger has no answer for a warning whose remedy is an OWNER decision** — W-001 survived
its owning milestone's close because agents may never waive a scanner finding, which is the ledger's
own headline rule broken by a rule it does not model. GP-upstream note.

**Numbers:** 4 waves · 193 tests (+41) · 27 review findings (24 closed in-wave, 3 at closure,
5 ledgered with owning milestones) · 18 fault injections, 2 initially stay-green, 18 RED after fixes ·
security close PASS (0 BLOCKING, 6 MINOR) · quality gate BLOCKING on one owner signature ·
plan-name drops 2→0 · assistant coverage 3/9→5/9 · coding coverage 1/10, unchanged by design.

## 2026-08-16 — M5: Rescue the Coding Category (data depth, phase 2)

**This milestone was built by one agent and closed by another, with no handover** — the first ran
out of budget at a `wip: NOT reviewed` checkpoint with four files uncommitted and no review of any
kind having run. What made the recovery possible was not memory but FILES: wave-close checklists, a
W4 implementation plan, and review records for W1–W3. The second agent reconstructed the exact tree
from a bundle, ran the reviews the wave never got, and closed it.

**What the reviews that never ran would have caught — and did, at closure:**
- `schema migrate` printed exit 0 over a database it had NOT repaired. A pre-M3 `plans` missing
  `observed_at` "migrated", and the next recommend died with `no such column` — the exact symptom
  the command exists to eliminate, now hidden behind a success message. The validator carried a
  hand-written list of two tables; it now DERIVES the requirement from the shipped DDL.
- `sources` claimed sources the answer never read (an Arena-only answer citing SWE-bench, Aider and
  Epoch). A field named `sources` is a provenance claim in a machine contract.
- The Epoch acquisition clock existed twice; CI checked one and the ingest stamped the other.
- The picks published the effort POLICY instead of the effort EVIDENCE, so a max-effort score shipped
  with `effort: null` while the same run's CSV printed `effort,max`.
- Running the REAL bundle found what no review did: `kimi-k2.5` and `kimi-k2.6` both folding into
  `kimi-k2`, so MAX() published the newer model's score under the older model's name.

**Lesson 1 — a new SOURCE is a new corpus.** The registry's live-name property tests are only as
good as the names they have met. M4-W1 built that corpus from the boards we had; M5 added two boards
and the corpus was never extended, so the same swallow class walked straight back in. Rule adopted:
every milestone that adds a source replays the live-name expectations against it, and the corpus
grows in the same commit as the source.

**Lesson 2 — a guard that cannot fail is worse than no guard.** The W4 "structural guard" against
the effort trap filtered a list by a predicate and then asserted that predicate. It was green in
every gate while the defect it was named for was live in the shipped payload. **Third instance of
this class in this project** (after the vacuous `"Twin Plan" in note` and the undefended
`close_call=8`). It reads like coverage, which is precisely what makes it expensive. Rule: when you
write a guard, write the mutant that should kill it in the same sitting — and if you cannot describe
that mutant, you have not written a test.

**Lesson 3 — a green mutant means the MUTANT might be wrong.** Two injections stayed green: one
because first-match-wins meant reverting a base rule could not reproduce the swallow, one because
the citing test drove only one of the two engines that share the defect. The reflex "test is weak"
was wrong the first time and right the second. Check the mutant before rewriting the test.

**Lesson 4 — a criterion written before the data exists gets rewritten by the data.** M5's own plan
promised the coding evidence age would drop below 60 days. The fresher board turned out to publish
model RELEASE dates, not evaluation dates. The criterion was restated as a fork (age it, or refuse
to age it and SAY the evidence is undated) rather than satisfied by ageing on a launch date. This is
the second consecutive milestone whose headline criterion was corrected by measurement — M4's was
"≥3 distinct plans". The rule adopted at M4 (measure in the wave BEFORE the criterion) worked: W1
measured, and the board choice changed because of it.

**Friction (V4C-13):** the agent handover cost a full review cycle that a completed wave would not
have needed, and the closure had to re-derive numbers the previous agent had already computed.
Recorded, not hidden.

**Numbers:** 17 commits · 271 tests (+78) · coding coverage 1/10 → 5/10, plus a new agentic-coding
category at 6/10 (union 6/10) · 40 review findings (20 in-wave, 20 at closure) · 22 fault injections,
22 RED after fixes, 2 initially green · security close PASS (1 BLOCKING fixed at closure) · quality
gate BLOCKING on one owner ruling (D-112) · 5 warnings carried to M6.
