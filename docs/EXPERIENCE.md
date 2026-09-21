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

## 2026-08-17 — M6: the HTTP API, and four proofs that a typed-out list is a denylist

**What shipped.** `/v1`, read-only, freezing the owner's Ruling A: a coding request returns BOTH
coding answers and nothing in the payload ranks them. Plus one serializer behind three renderings,
the product's user-facing text and query vocabulary in English (D-118), a persisted roster staleness
window with a migration, an alias-expansion guard on every YAML input, the CORS and startup-
validation baseline, and Fly.io recorded as the deploy target with an ADR that exists (D-116).

**The lesson, and it cost ten BLOCKING findings to learn properly.** This project already knew that
*a guard that cannot fail is worse than no guard*. M6 adds the harder half: **an enumeration that is
typed out is a denylist wearing better clothes**, and it recurred four times in one milestone.

- The guard protecting Ruling A was a nine-name denylist. Renaming the field `primary_surface`
  walked past it. Its replacement was a sixteen-stem regex; `display_order` and `suggested` walked
  past that. The third formulation freezes the key set — an allowlist — and holds.
- The test written to prove *"a guard on two of three inputs is a guard on none"* enumerated three
  filenames in a literal, so it was itself a guard on three of four. The missing one,
  `src/app/clients/aider.py`, is the only YAML input this project fetches over a network — the exact
  case W-005's deferral condition had named two milestones earlier.
- That test's replacement derived the FILE SET and kept a four-word predicate, which detected 1 of 7
  ways to reach PyYAML.
- The L.8 smoke gate typed its endpoints in and reported a 404 for a working dependency, because it
  said `main/` where the client says `master/`. Its own docstring said a smoke test against a URL
  nobody calls proves the network works and nothing else.

**Operational form:** when you write a list of things to check, write the code that produces the
list. If you cannot derive it, name in the same sitting the member you would most regret missing,
and check that one by hand.

**The second lesson, from the reviewers rather than the code.** All ten BLOCKING findings were the
same shape: *a control that existed, was cited, and did not run.* A startup validator called by
nothing that let production boot with no database. A CORS block whose complete deletion changed no
test. A rollback whose test executed zero statements. A migration reporting success on a database it
had left unservable. **Reachability, not logic** — and reachability is the property this project's
citing tests are worst at, because a test of a function nobody calls passes exactly as well as a
test of one that ships.

**A fix inherits the risk class of the bug it fixes (V4C-50), demonstrated the hard way.** The cycle
guard added to close a denial-of-service kept its state at module scope and never cleared it on the
raise path; one hostile document then poisoned later parses, measured at 159 of 160 legitimate loads
refused — and the same commit had just routed the remote-fed input through that guard. **A denial of
service introduced by the fix for a denial of service.** Only a Tester running the guard twice in one
process could find it; no mutant can.

**Friction (V4C-13):** W3 needed four review rounds and W1 three. No control was skipped under
pressure and none was waived. The cost was real and it was the right cost — but the author's own
fault-injection sets killed 100% of the author's own mutants while reviewer mutants stayed green 22
times across the milestone, which is a measurement of imagination, not of discipline.

**W-001 closed after surviving four milestone closes.** Its diagnosis was right on day one and its
remedy never changed. What blocked it was that the remedy is a waiver only the owner may grant, and
every closure session filled before he was asked for a decision rather than shown a status. **A
control whose only remedy requires the owner will survive every close until someone asks.**

**Numbers:** 12 commits · 354 tests (+83; 361 with the Epoch bundle) · 10 BLOCKING across three
review seats, all closed · 47 author mutants all killed, 52 Tester mutants with 16 initially green ·
5 carried ledger rows paid, W-001 closed, 4 new rows · 7 ADRs (D-113..D-120) · 1 criterion amended at
the gate · 5 findings handed back to GP.

## M7 — 2026-08-18 — The engine feeds itself, and stops writing while it reads

**What the milestone was.** The product's data-production pipeline existed only as a ~30-line
heredoc inside a CI workflow on a cron that had never fired. That is why the shipped `advisor.db`
answered zero picks for every query: nothing rebuilt it. M7 lifted the pipeline into `src/`, moved
the price-median build off the read path, deleted the in-memory snapshot that the write had forced,
and packaged the result. It did not deploy — the owner moved go-live to ship with the iOS client
(D-123).

**The lesson, and it corrects M6's.** M6 concluded that reachability is where this project's tests
are weakest — ten of ten BLOCKING findings were controls that never ran — and asked whether to build
a gate for it. M7's headline defect was the opposite shape:

> **A control that runs on every request can still be the defect, and no reachability tool will say
> so. The question is not "does this execute" but "should this exist".**

`serving_snapshot` executed perfectly, on every request, for an entire milestone. It was cited,
tested, measured by three separate security passes, and given a memory budget with five declared
constants. A reachability gate would have called it healthy. Deleting the *reason* it existed — a
write on the read path — removed the control, the constants, the budget, three tests and the whole
class of finding in one move. And the Stage-4.0 pass then showed the deleted ceiling had been
measuring the wrong quantity all along: it would have refused a harmless 121 MB artifact while
admitting a 6 MB one that used 58% of the VM.

**Second lesson, paid twice in one milestone.** *Deleting a test is a decision needing the same care
as writing one.* Three tests guarded the memory budget and went with it; one of them also guarded
the concurrency agreement, which is live and has nothing to do with snapshots. Two mutants walked
through the gap. The test written to replace them says, in its own docstring, that quiet deletion is
how a control disappears.

**Third, about records.** The D-121 amendment claimed a test file asserted something it did not —
a record asserting a control that was not there, committed in the sentence documenting a fix. Fifth
milestone for this class. And W-023 taught a variant: **a correct diagnosis can carry an
insufficient remedy for two milestones because nobody re-reads the remedy.** Its ledger row
prescribed a one-line `schema migrate`, which cannot populate a table.

**What the reviews cost and returned.** Thirty BLOCKING in W1 alone, none found by the author,
across three seats and three rounds — rounds two and three finding defects the author introduced
while fixing round one. That is also what produced **D-122**: the owner ruled that review depth
follows blast radius rather than wave number, after one wave consumed a whole session on a project
with no users. He had given the same instruction in M6 and it had not been applied.

**Numbers.** 396 → 511 tests. W-017 and W-023 closed, both the oldest open rows, and neither the way
its own row proposed. 0 deploys.

## M8 — 2026-08-19 — The engine gets a reader, and the product stops being about coding

**Scope changed mid-milestone and the architecture held.** D-126 widened the product from coding
models to all AI tools, with a boundary the owner stated as a rule: the free LLM in the middle may
route a question to a pre-existing category and may **never** say a model is good. D-127 set nine
categories. Six were added by writing six `CategorySpec` entries and one parameterised board reader
— **no branch anywhere in the scoring path.** "Categories are data, not code" had been asserted
since M2 and had never been tested at more than three.

**The defect that mattered lived between two correct things.** `ranking_effort` is served by the
engine, decoded by the client, and was displayed by nothing. Every server test passed; every client
structure was right. A score shown without the effort level it was measured at invites a comparison
against one measured elsewhere, which is the entire reason the field exists. Neither side's reviews
could see it, because the gap was between them.

> **The lesson, in the form it will recur: a control whose SCOPE is narrower than the rule it cites
> is not a gate.** The same milestone produced it twice more. An attribution guard asked only about
> each category's `primary_source`, so a mutant deleting `epoch_mmlu`'s citation walked through —
> `epoch_mmlu` is nobody's primary source, it is served as evidence, which is exactly the population
> the control covers and the test did not. Rebasing it on the source registry then made it too WIDE,
> demanding citations from two pricing sources. The fix was to make the codebase say out loud which
> sources are evidence (`writes_scores`), because the distinction had been implicit and cost a test
> its meaning.

**Measuring the wrong population is not a mistake you make once.** Three calibrations against three
different wrong sets — CSV rows, parsed board rows, then the full board instead of the
reconciled-and-priced subset the engine actually ranks (58 of 521 on ECI). Each caught by measuring,
none by reading. The recurrence has one cause: **the ranked population has no name in the codebase**,
so the question gets answered from whatever data is nearest.

**Sometimes the honest answer is the untidy one.** `expert` admits 25 value candidates against
`coding`'s 7, and it stays that way: on GPQA the top twelve priced models span 1.8 points against a
2.52 standard error, and on AIME three tie at exactly 100. Narrowing the window below `close_call`
would let the product call a model "level with the leader" and refuse to consider it in the same
breath — ranking noise as quality. **The tidier number was the dishonest one.**

**Two operational lessons paid for in debugging time:**

1. **A seam is only a seam if it reaches the caller.** Third instance of this project's most-repeated
   defect, in a new half: `_ingest_boards` read its `boards` parameter at call time — correctly —
   while `build()` exposed no way to pass one. The previous two instances were about when a default
   was bound; this one was about whether the parameter was reachable at all.
2. **Restart is not rebuild, and the build stamp is the only witness.** `app.sh restart` restarted
   the app and not the engine. A running process keeps the replaced file's inode, so `/health`
   answered 200 the whole time: nine categories in the artifact, three on the wire, every gate
   green. Only `dev-60cce36` against a HEAD of `d47a379` gave it away.

**What was accepted rather than solved:** three waves closed with no fresh-eyes review, each an
explicit owner ruling under D-122, each recorded as a `control-bypass`. The third fires `C2b` — the
CONTROL goes for review at M9, not the seat. And go-live did not happen for the second milestone
running; W-030 and W-031 have now been UNVERIFIED for three.

## M9 opening note — 2026-08-21 — two measurements that changed a plan before it was written

Recorded here rather than in a retrospective because both were made while PLANNING, and both
replaced a belief the records already held.

**The hot swap was never a problem.** M9 was scoped expecting to build artifact hand-over: a running
engine keeps the replaced file's inode, so a refresh would serve stale data until someone restarted
it — and this project had been bitten by exactly that shape twice. The experiment took two minutes:
`advisor.db` was atomically replaced under a live engine with a modified copy, and the very next
request returned the new data. The adapter opens a read-only connection **per request**, so a swap
lands immediately and an in-flight request finishes on the inode it started on. **A third of the
milestone did not need building; it needed a test.**

The two earlier "stale artifact" incidents were stale CODE wearing the same symptoms — the process
was running an older commit, which the build stamp said and nothing else did.

**arena was never down.** For an entire milestone the records said an upstream dependency was
returning 500 and a user-facing surface shipped blind because of it. The dataset was healthy the
whole time: `/is-valid` reports filter support, `/splits` lists the split, `/first-rows` returns the
rows, `/rows` serves them. **Only the `filter` endpoint fails, and it fails with no `where` clause
at all** — so it was never our query, and the remedy is a bounded read of a different endpoint.

> **The lesson is about how a dependency gets written off.** One endpoint returned an error, the
> error was reproduced twice minutes apart, and that was enough to record "the source is down" and
> carry it as an accepted condition through a whole milestone. Reproducing a failure proves the
> failure is real; it proves nothing about its SCOPE. Nobody asked the dataset whether it was there,
> and asking took four commands.

Both findings share a shape with the milestone that produced them: a claim that was true when
measured, held as true long after the thing it described had changed or been misread.

## M9 — 2026-08-22 — The product starts keeping itself current, and finds out what that costs

**A refresh cycle now builds a candidate, decides whether anything a reader would notice changed,
and publishes or refuses.** `launchd` will run it every twelve hours once the owner loads it. The
artifact is never left worse than it was found — proven against a failed build, a raising builder,
an unreadable candidate, a build that fails while leaving something readable, and **a real SIGKILL
in a subprocess**.

**A third of the milestone evaporated before it was planned, because of one two-minute experiment.**
M9 was scoped expecting to build artifact hand-over: a running engine keeps a replaced file's inode,
so a refresh would serve stale data until restarted — a shape this project had been bitten by twice.
The measurement: `advisor.db` replaced under a live engine, and the very next request returned the
new data. The adapter opens a read-only connection per request. **The two earlier "stale artifact"
incidents were stale CODE wearing the same symptoms.** Two beliefs, both grounded in a real
incident, both about the wrong mechanism.

> **The lesson that generalises: measure the thing you are about to build BEFORE you plan it.** The
> experiment cost two minutes and removed a wave.

**Every serious defect this milestone was found by fault injection or by someone else. Not one by
reading.** An independent seat wrote 40 mutants where the author reported 24; 8 survived where the
author reported none. It returned three BLOCKING, and the worst of them is worth carrying:

> **The refresh was structurally incapable of publishing a freshness update.** `evidence_date`,
> `vendor`, `input_per_m` and `output_per_m` were all served to readers and none was in the
> fingerprint, so the same scores republished with FRESH EVALUATION DATES read as "nothing a user
> would notice changed". The artifact would keep disclosing `stale: true` forever while every cycle
> exited 0 and every gate stayed green.

That is the failure the plan had NAMED in advance — a refresh that freezes the product is worse
than one that publishes something bad, because a freeze is invisible — arriving through the door
nobody was watching. **The trap was correctly identified and incompletely defended**, and the fix
was to stop hand-listing the hashed fields and derive them from the row, so a field added tomorrow
is covered by default.

**A guard that compares one quantity sees one kind of damage.** The refusal rule compared row
counts, so a pricing feed multiplying every price left every surface exactly the same SIZE while
two of three budget tiers answered nothing on all nine surfaces. The ADR had reasoned that prices
are not damage because a price is a reported number — **true of a score, false of a price, because
the price is also a hard filter applied before scoring.** The reviewer's verdict on the threshold
is the reusable part: *the answer to a guard that misses things is more axes, not more stringency.*

**Writing a test changed a design, in the order this project keeps saying it wants.** The SIGKILL
test showed that a killed cycle left its lock behind and wedged the refresh for two hours — a
skipped cycle for a process already gone. The lock holder writes its pid, so a lock whose holder no
longer exists is now reclaimed at once.

**And the carried question got answered by a requirement rather than by an argument.** REQ-REF-007
says ingestion never runs on the serving host. It cannot be met: there is one machine. **A
separation you cannot violate because you only have one host is not a separation you have
verified** — which is what W-030 and W-031 have been saying about the platform for three
milestones, arriving this time from inside the product.

**What went badly:** two of three waves closed with no independent seat, and the one that ran found
three BLOCKING. An ADR claimed to answer a plan question it does not address, and the wave record
repeated the claim. Another ADR's worked arithmetic was off by one in both examples, in the
direction that made its rule look tighter than it is. And I committed on a red gate for the third
time in this project, having recorded the same mistake twice before.

## M10 closure — 2026-08-22 — the milestone whose carried question was answered against it

M9 asked what this system does when it is wrong and nobody is looking, and wondered aloud whether a
status file and an escalation counter were the answer. M10 produced two receipts saying they were
not.

**A counter fired and nothing consumed it.** `C2b` exists so that the third bypass of a control
sends the CONTROL for review rather than the seat. It fired at M8 over K.7, named M9, and M9 closed
without doing it; M10 bypassed K.7 a fourth time. The telemetry was flawless. **Being written down
is not the same as being read** (W-055, escalated to the owner).

**A defect survived a milestone with every gate green.** `f"file:{path}?mode=ro"` returns a WRITABLE
connection — measured against four path shapes, all four wrote into the artifact. It shipped in M9's
refresh on the path that opens the LIVE database, passed M9's Stage 4.0 (which found three real
blocking findings, so not a lazy pass), and passed every gate through M10-W3. It was found by typing
the expression into a Python process and watching it write.

Three shapes worth keeping:

1. **A fix that lives in one module is not a fix.** The correct construction and a docstring
   describing this exact defect had been in `adapter/main.py` since M6. `workflows/refresh.py`
   rebuilt the broken form under a comment arguing the copy was "not a second definition of any
   project behaviour". The comment's premise (do not import the adapter — D-116) was right; its
   conclusion did not follow, because the third option — move the definition where both may reach
   it — was never considered. **A boundary rule and a single-definition rule collide eventually,
   and the collision is resolved by moving the definition.**
2. **A control that runs and cannot trigger.** The first aggregate row bound was 5,000, which is
   exactly `_MAX_PAGES * _PAGE`. Coverage sees it covered; review sees a sensible constant; only an
   attempt to REACH it sees anything.
3. **A name is not a control until something is required to call it.** REQ-EVI-002's accessor
   existed from M9 and the calibration script still sized thresholds off the raw board — the exact
   defect W-037 records three times, alive inside the tool written to recompute W-037's record.

**What was accepted rather than solved:** nothing deployed, third milestone running (D-123, W-030,
W-031); the iOS app has never been opened by a human, so every router claim is from a probe; the
12-hour refresh has never run unattended (W-054).

**Carried to M11:** the defects that mattered here were found by EXECUTION, not by gates, records or
review. What is the smallest amount of running this project could add to its close — a suspect
expression in isolation, or the product in front of a person — and what does it cost? Not a tenth
gate in `make check`.

## M11 closure — 2026-08-23 — a control in the path that does not execute

M10 asked what the smallest amount of RUNNING to add to a close would be. M11 answered it twice and
the answers were not equal.

**Executing code** found a `runner` section calling commands that do not exist (ALL PASS over a red
suite), a Make recipe that passed on zero tests, and a CI workflow that had run twice in its life
and failed both times — not for source drift, but because it enforced the full suite's coverage
floor on a step running 14 network tests. Structurally unpassable from the day it was written, and
because step 1 failed, the three steps below it had never executed once. **A badge that has always
been red carries no information**, which is why the week it went red for a real reason reached
nobody.

**A person using the app for twenty minutes** found six defects that eleven milestones of gates had
not, and then produced five product requirements no one inside the project would have written. The
tally is the argument.

Three shapes worth keeping:

1. **A control in the path that does not execute is not a control.** The router's three tiers put
   the "we do not measure this" disclosure in the SIMILARITY tier's floor. On a device carrying the
   on-device model that tier runs second and therefore almost never runs, and the tier that DOES
   run was schema-constrained to the nine ids and had no way to decline. Every question in the
   world came back as a confident measured match. The requirement was satisfied in a path nobody
   reaches — the purest form yet of a shape this project has recorded four times.
2. **Proving one half of a change proves nothing about the other half.** The Makefile recipe was
   proven by breaking a test and watching it go red, with a comment recording the lesson; four
   lines below, the runner half shipped the same class of defect by different mechanics, because
   the lesson had been learned as a fact about pipes rather than as a habit of executing what you
   just wrote. A third instance in the same wave is what made it a habit.
3. **The escalated pile said twenty-two and it was seven.** Eleven rows had been resolved by later
   work that never closed them; five described things that cannot be undone. Every close in the
   audit was verified by RUNNING something, which is the only reason it was trustworthy and also
   why it had not been done before — reading twenty-two rows is cheap and tells you nothing.

**And one that is not about code.** Asked for Turkish, the obvious reading was a string file.
Measurement said otherwise: every sentence on screen is generated by the engine in English. Eleven
milestones of localisation debt with nobody to name it, because there was no second language to
reveal it. **Prose in an API is a localisation trap, and this one was sprung long before anyone
asked.**

**What was accepted rather than solved:** nothing deployed, fourth milestone (D-123, W-030, W-031);
the refresh has still never run unattended and a signed plan promise for it was never written into
the PRD (W-071); K.7's seat is a separate session, not a separate person, and D-133 says so itself.

**Carried to M12:** every requirement written before a user arrived was written by someone who
already knew what a benchmark was. The fixes are easy once stated; the question is why none of them
was ever stated. **A correctness culture measures whether a number is right and has no instrument
at all for whether it is understood.**

## M12 closure — 2026-08-25 — you cannot gate comprehension, but you can staff it

M11 asked what this project would have to MEASURE to catch a comprehensibility defect before a user
does. M12 answered it twice and only one answer is a measurement.

A gate can be built and it is weaker than it sounds: `test_category_titles.py` refuses two surfaces
beginning with the same word, and refuses a title containing a term from inside this field. It
caught a real defect on its first run — the lead agent renaming a surface against an explicit owner
ruling — and what it tests is a proxy: *does this text contain something we already know is
jargon*. It cannot ask whether a sentence lands.

The honest answer is not a gate. **The 28-row comprehensibility inventory that drove this entire
milestone came from a council seat told to read the product as a stranger and given no other job.**
The CFO had found five of those rows; the seat found twenty-eight. Nothing mechanical produced it,
and what made it repeatable was a CHAIR, created because every existing seat was accountable for
correctness.

Three engineering shapes worth keeping:

1. **Two parallel computations that agree today are two sources of truth.** D-136 claims the prose
   is derived from the fact; the first implementation computed both separately and did not manage
   to agree even today — `3x cheaper` beside a fact carrying `3.1`, then `84` beside `84.4`, then
   `6` beside `6.0`. One test caught all three on its first run, because it held the PROPERTY the
   design claimed rather than checking an output.
2. **Rounding the claim is not rounding the display.** The obvious fix for `84` beside `84.4` was
   to round the fact. Wrong: the bar really is 84.4, and `84` states a bar the engine does not
   apply. A number a product rounds is a claim it makes.
3. **A test that pins WHERE logic lives is a tax on improvement.** Three times in two waves a test
   went red on a change that kept every word of its intent. Pin the claim and the audience, never
   the offset — a test that fails when text moves teaches people to leave text where it is, which
   is how a user-facing string ends up explaining App Transport Security to a CFO.

**And a rule pointed at its own foot.** `L1` keeps this repository English, and it blocked the
records DOCUMENTING non-English defects — a finding that cannot explain itself without naming the
letter that causes it. Fourth occurrence, fixed by narrowing the rule to prose. The proof of the
narrowing was nearly a defect too: the first attempt tested a file already exempt, and would have
"passed" against a rule that never read it.

**What was accepted rather than solved:** the notices are not localised, so a Turkish reader gets
Turkish sentences and English disclosures; the flag has never been tapped by a human; nothing
deployed, fifth milestone; and a fifth commit landed on a red gate, the fourth with the identical
cause — edit a RECORD after a green check and commit without re-running.

**Carried to M13:** every wave of this milestone discharged findings from outside the people doing
the work, and it produced the largest usability gain in twelve milestones. **The work the team
chose for itself, across eleven milestones, was correctness — and correctness was never what stood
between this product and a user.** What else is the team not choosing?

## M13 closure — 2026-09-15 — a ruling is a hypothesis until someone measures it

M12 asked what else the team was not choosing. M13 answered with evidence: every defect that
mattered this milestone was found by a seat outside the work, and each KIND of seat found a
different kind. A second opinion with no brief found four defects in the scoring path and its
instruments that five briefed council seats had missed, including Pareto dominance, wrong in both
engines since M2. The council was right about direction and wrong three times in detail. Each time a
measurement overturned it, and the third overturn is the one the product now shows: the greedy tie
bands printed 47 within-margin pairs as ordered, and the owner chose rank ranges (`#1–27 of 50`).

Engineering shapes worth keeping:

1. **A fixture's clock is part of the fixture.** The gate went red on 2026-09-15 with no code
   change: a fixture's wall-clock stamp aged its literal dates past a 30-day window. Pin the clock at
   the source (`RunContext(observed_at=...)`), and sweep the suite under a future clock once.
2. **When a criterion is about a relation, check whether the relation is transitive first.** "Within
   the margin" is not, so no single rank number can avoid ordering a tied pair. A range can, by
   construction, and a property test can prove it.
3. **Structural tests must pin arguments, not names.** A source-contract test that checked only that
   the Engine functions were CALLED let every argument-level change through, twice. The test now
   checks the arguments that carry the engine's facts.
4. **Reproduce a defect in the system's own component before calling it the app's.** The simulator
   raised no software keyboard for the app's field, and none for Safari's address bar either.
5. **A memo must key on everything its answer depends on.** The `/health` memo keyed on mtime and
   size, and a `chmod` left it reading `servable` over a 503. `st_ctime` moves on every chmod, chown
   and write, and `os.utime` cannot set it.

**Control bypass (`control-bypass`):** the HIGH-tier pulled-forward security pass was waived in all
three code waves (W-088..W-090), and the waived W1 slice shipped the memo defect in point 5. The
waivers were local, so the repetition counter could not see them. The control is under review as
D-141 (proposed).

**What was accepted rather than solved:** the software keyboard and typing were never exercised, in
an environment where synthetic keystrokes do not arrive (owner action); the artifact predates the
terminalbench date fix because the refresh is stopped on a launchd spawn fault (owner action); ECI's
exact number is no longer printed, only its rank (D-140); nothing deployed, sixth milestone.

**Carried to M14:** what would it take for the next milestone's evidence to come from the product as
a reader meets it — refreshed data, a real keyboard, a real device — rather than from the
instruments around it?

## M14 closure — 2026-09-21 — a proof is scoped to the file it reads, not to the invariant it names

M13 asked what it would take for the evidence to come from the product rather than from the
instruments around it. M14's answer was: the owner's machine, and only it. Nine probes in the agent
lane cleared the Desktop paths, the interpreter, the plist and the registration by measurement, and
every one of them was wrong — they ran Apple-signed programs, and macOS decides privacy protection
per program. One run on his machine with the real wrapper produced the first honest error of the
hunt. The inverse is now the standing risk: `ContentView.swift` is compiled by nothing in this
project's suite, so the one file holding the reader's typed words carries the least proof, and the
closure seat found exactly that.

Engineering shapes worth keeping:

1. **Scope a structural test to the invariant, not to the section.** REQ-GAP-001 says nothing the
   reader types leaves the device; its test searched the register's own section of one file while
   the recording happens in another. A four-line `URLSession` POST of the typed question survived
   every gate. Ban the egress spellings across every file the data can reach, and leave one
   sanctioned door whose arguments are pinned.
2. **A remedy named in a record is a deliverable with a path.** A ledger row closed a 24-day outage
   citing an installer script that existed only in the owner's scratch folder, while the
   repository's own install path was left writing a plist whose program was absent — the same
   outage, reinstated by its fix.
3. **A pin that passes by coincidence is not a pin.** Four pinned anchors happened to equal four
   thresholds, so serving the wrong one passed every test. Move one and not the other.
4. **Diff the criteria table at closure; do not read it.** Two REQ-IDs left the milestone with no
   disposition anywhere. `grep` found them in a minute; three reviews had not.
5. **A stop condition is worth more than a plan.** The milestone's centrepiece surface was refused
   in its first wave by its own measurement — a ranked population of zero — and two surfaces the
   data supported were built instead.

**What was accepted rather than solved:** Elo surfaces read 57–79 against percentage surfaces'
73–100, on the owner's ruling; the detail screen the plan leaned on does not exist; two gates
reproduce only on the owner's machine; the HIGH-tier security pass was waived twice more while its
ADR stays proposed — fifth and sixth occurrence of `control-bypass`.
