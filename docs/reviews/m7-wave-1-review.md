---
record_type: review
id: m7-wave-1-review
status: proposed
date: 2026-08-17
---
# Wave 1 Code Review (m7)

**Reviewer:** Code-Reviewer subagent (fresh eyes — authored none of this wave; K.7)
**Date:** 2026-08-17
**Commit range:** `9f4471d..fa87fbf` (f8e4445, 422455d, fa87fbf) — 9 files, +1145/-114
**Source:** A (baseline `subagent-profiles/Code-Reviewer.md` v4.0, read from the protected base ref)
**Risk tier:** HIGH (new production entry point + untrusted network input — plan §2 W1)

**V4C-03/04 fields:** author-family / reviewer-family — author is the lead agent (Claude family);
this seat is the same family, so cross-family routing was NOT achieved (fallback reason: no second
family available to this dispatch). Recorded, not waived; advisory only. Fresh-context assertion:
this seat authored no line of the wave, read `subagent-profiles/Code-Reviewer.md`,
`docs/plans/m7-plan.md` and `docs/decisions.md` from the base ref before opening the diff, and
treated the wave's own commit bodies as claims to falsify rather than as summary.

---

## Verdict

**BLOCKING** — 7 BLOCKING, 12 MINOR.

The engineering here is better than the wave's own history predicts. The heredoc is genuinely gone
with no second copy, the identifier guard in `_read_back` is a real control with a mutant that dies,
the "leaves no artifact behind" unlink is a real control with a mutant that dies, and the
default-argument injection defect the wave caught in itself twice is genuinely fixed at both sites.

What it does not have is proof for most of what it declares. **Six of eight mutants I planted
survived a full green suite**, and every survivor sits on a line this wave's own commit message
names as its point: the optional-source flag that D-121 exists for, the local-bundle ingestion that
`agentic-coding` was fixed by, and three of REQ-ING-013's floors including the `px_median` floor
that is Trap 1. And the CI step the wave installed to replace the unrun heredoc **cannot exit 0** —
it is not an unrun control any more, it is an unrunnable one.

---

## Findings

### BLOCKING (must fix before the next wave)

**B1 — `.github/workflows/contract-tests.yml:81`: the replacement CI step can never pass, and it
takes the rest of the job down with it.**

`main()` returns `3` whenever `required_operator_actions` is non-empty
(`src/app/workflows/build.py:377`). With no `--epoch-dir`, `_ingest_bundles` returns *every* local
bundle as missing, unconditionally (`build.py:196-197`), and the workflow never passes `--epoch-dir`
(`build.py:359` reads it from the CLI only; the workflow line is bare
`python -m app.workflows.build --db ci_advisor.db`). The bundle is owner-placed by D-101 and is not
available to a GitHub runner, so there is no argument the workflow could pass.

Proof, from the wave's own test: `tests/unit/test_build.py:204-223`
(`test_cli_reports_three_when_a_surface_lost_its_evidence`) asserts exactly this — no `--epoch-dir`
⇒ `code == 3`. GitHub Actions fails a step on any non-zero exit and the step carries no
`continue-on-error`, so the `live-contracts` job is red on its first-ever run, and the three steps
after it never execute: the coverage/source-health report (`:84-85`) and the recommend smoke
(`:88-97`) — **including the D-118 budget fix this same wave just made**, which is therefore still
never exercised. Trap 2 asked for the heredoc to be replaced by something governed; this replaced an
unrun step with an unrunnable one.

Fix shape (not prescriptive): the step must accept 3 as a documented outcome, or CI must supply a
bundle, or the bundle-missing degradation must not be an operator action in an environment where the
bundle is by design absent.

**B2 — `src/app/workflows/build.py:240-247` + `src/app/workflows/sources.py:144`: D-121's entire
mechanism is dead to the test suite.**

Coverage from `.venv/bin/python -B -m pytest`: `build.py` lines **246-247 never execute**. Two
mutants, both **GREEN (survived), 396 passed / 12 skipped**:

- `sources.py:144` `required=False` → `required=True` (arena becomes mandatory again — D-121 undone)
- `build.py:240` `if source.required:` → `if True:` (the optional branch deleted outright)

`tests/unit/test_build.py:204` reaches exit 3 through the *bundle* path, not the optional-remote
path, so it does not cover this. `tests/unit/test_sources.py` asserts floors and uniqueness but
never `required`. Concrete failure permitted: an edit that removes the flag, or that makes an
optional failure fatal (exit 2) or silent (exit 0), ships green — and D-121's operative sentence
("downgrades to exit 3 … never to a silent exit 0") is asserted nowhere in the suite.

For the record, I verified by hand that the path *works*: driving `main()` with a `required=False`
fake that raises returns exit 3 and leaves the artifact. So this is a proof gap, not a logic bug —
but V3C-02 makes a criterion without a citing test BLOCKING, and D-121 + REQ-ING-013 are exactly
such criteria.

**B3 — `src/app/workflows/build.py:206-212`: the local-bundle ingestion SUCCESS path — the whole
content of commit `fa87fbf` — is executed by no test.**

Coverage misses **206-208 and 212**. Mutant: `build.py:212` `results.append(result)` → `pass`,
i.e. the builder ingests both Epoch bundles and throws the reports away — **GREEN, survived**.

Concrete failure permitted: `report.sources` silently loses `epoch_swe_bench_verified` and
`epoch_deepswe_external`; nothing detects that the DeepSWE board was never actually stored; and
`agentic-coding` returns to answering with zero picks while `required_operator_actions` is `[]` and
the CLI exits **0**. That is the 200-with-no-picks failure this wave was created to end, arriving
with a clean exit code. The only evidence for this feature is the commit body's manual measurement
("epoch_swe_bench_verified 33 rows, epoch_deepswe_external 49"), which is a measured-once claim —
Trap 3, verbatim.

The two existing bundle tests (`test_build.py:292`, `:302`) both assert the *failure* shape.

**B4 — REQ-ING-013's floors: three of them have no citing test and all three mutants survive.**

| Control | Line (HEAD) | Mutant | Result |
|---|---|---|---|
| price medians built 0 models | `build.py:303-305` | `if False:` | **GREEN, survived** |
| read-back per-table emptiness | `build.py:311-313` | `if False:` | **GREEN, survived** |
| curated stage stored nothing | `build.py:146-148` | `if False:` | **GREEN, survived** |

Coverage independently confirms 304-305, 312-313 and 147-148 are never executed.

The first is **Trap 1's floor** — the plan (§0 Trap 1, §2 W1 item 5) pre-declares "`px_median` left
unbuilt" as a mandatory fault-injection case. The second is **Trap 3's floor** — the module docstring
(`build.py:12-15`) says "the final act is to read the counts back OUT of the file", and the check
that makes that read-back mean anything can be deleted with the suite green. The third means a
well-formed but empty `rosters.yaml` is untested (`test_empty_plans_fail_the_build`,
`test_build.py:179`, goes through the `SourceError` arm at `build.py:143`, not this one).

`test_build.py:118-133` asserts the *happy* values are `> 0`; that is not the same control and
cannot catch the removal of the floor.

**B5 — D-121's binding condition, checked against the code rather than its prose: half of it does
not hold. `src/app/adapter/main.py:729-733`.**

D-121 says arena may be optional "**only because** the serving path already discloses a missing
source", and that if that disclosure is ever weakened the ADR "is invalidated, not merely
inconvenienced".

The disclosure half is real and I verified it: with no arena rows, `_source_health_json`'s
`entries` list is empty (`main.py:487-493` selects `DISTINCT source FROM scores WHERE benchmark =
'Arena text'`), so `main.py:521-531` returns `"stale": true` with
`"No evidence source for Arena text is present in the served database, so freshness cannot be
established."` Good.

But the same payload carries, from `main.py:729-733`:

> `"unavailable_reason": "No model on this surface's benchmark fits the requested budget, so this
> answer ranks nothing. It is shown rather than hidden."`

When the cause is a missing source, that sentence is not thin — it is **false**, and it is the
human-readable field. A client that renders `unavailable_reason` tells a user asking about
`assistant` that **nothing fits their budget**, which is precisely the "different and false
statement" D-121's own Context paragraph says must not be produced. D-121 records the empty-`picks`
gap and asserts the rest was "verified against the real artifact at this wave"; that verification
did not cover this field.

`main.py` is outside the diff, but D-121 is inside it and is the sole authority for shipping without
arena. Either the ADR's condition is met or the ADR is not usable — this seat finds it not met.

**B6 — plan §5 assigns "Coverage / roster-staleness CI legs, never run" to W1; nothing in the diff
addresses it. `.github/workflows/contract-tests.yml:14-17`.**

The wave rewrote the *content* of the one workflow those legs live in and left the trigger block
byte-identical to `9f4471d`: `workflow_dispatch` + `cron: "0 6 * * 1"`. The plan's own §0 states that
cron **has never fired in this repository's history**. So `plan-staleness` (`:32`), roster staleness
(`:47`), epoch staleness (`:52`) and the coverage report (`:84`) still never run — the exact defect
class this milestone is named after, in the exact file the wave was already editing. A task dropped
without a plan amendment (profile §1).

**B7 — plan §1 criterion 8 and §2 W1 item 4 make W-023 the wave's stated exit condition; it is not
closed and the diff contains no artifact.**

Plan §2 W1 item 4: *"Produce `advisor.db` with it and read the result back from the file (Trap 3) —
**W-023 closes here or the wave does not close.**"* Measured now, from the file rather than from the
commit body:

```
advisor.db        models=72  pricing=2565  scores=630  px_median=0   plans=10
owner_advisor.db  models=42  pricing=2565  scores=630  px_median=41  plans=9
```

`advisor.db` still has an **empty `px_median`** — the pre-W1 state, and the exact condition that
makes `rank.py:225`'s JOIN return zero rows. Commit `f8e4445`'s body correctly says W-023 "cannot
close until the owner rules"; the owner has since ruled (D-121, commit `422455d`), and commit
`422455d` claims a real build producing "73 models and 72 price medians" — but no such artifact is
in the tree, and the one that is there is not it. The wave's own exit condition is unmet.

### MINOR (queue for K.9 gap-fill or next-M)

- **M1 — `build.py:167`** derives blinded surfaces from `CategorySpec.primary_source`, which
  `categories.py:23` annotates *"informational"* and which `main.py:475-483` documents at length as a
  join it already had to *remove* for exactly this purpose: `rank.py:52` registers
  `epoch_swe_bench_verified` as a second first-class source for the `SWE-bench Verified` benchmark and
  `rank.py:173-235` selects by benchmark with no source predicate. Unreachable today only because
  `swebench` is `required=True`. D-121's Revisit-when explicitly anticipates a second optional source,
  at which point this mapping starts producing false "this surface is blind" claims. The same defect,
  re-introduced in a new file two milestones after it was fixed in an old one.
- **M2 — `build.py:165`** `entry.split(":", 1)[0]` is in fact robust *as written*: `maxsplit=1` means
  a colon inside the error text is harmless, and all three producers use `f"{name}: {msg}"`
  (`build.py:197`, `:210`, `:246`). But nothing pins that contract — `RemoteSource.name` and
  `LocalBundle.name` are free-form strings, no test asserts the format, and a name containing a colon
  would silently mis-derive the surface. A `(name, reason)` tuple removes the parse entirely.
  Cosmetic side effect: an optional source that fails its floor produces
  `"arena: arena: stored 0 rows…"` (`build.py:234` wraps, `:246` re-prefixes).
- **M3 — `build.py:239`** catches only `(SourceError, BuildError)`, so `required=False` is an escape
  hatch for *two exception types*, not for failure. `ArenaClient` does normalise HTTP failures to
  `SourceError` (`src/app/clients/arena.py:107-115`), so W-024's real shape is covered — but a
  `sqlite3.IntegrityError` out of `ingest_arena`, or a `ValueError` out of a parser, aborts the whole
  build regardless of the flag. D-121 promises more than the code delivers.
- **M4 — `build.py:201`** `committed_last_verified()` runs outside the per-bundle `try`, so an
  unreadable or malformed `data/epoch-source.yaml` turns a *bundle* problem into a total build failure
  (exit 2), contradicting the function's own docstring that bundle absence is a reported degradation.
- **M5 — `build.py:230-248`** does not roll back partial writes from a failed optional source: rows
  stored before the floor check stay in the committed artifact while `required_operator_actions`
  declares the surface has no evidence. Not reachable for arena (`minimum_rows=1`); reachable for any
  optional source with a floor > 1.
- **M6 — `build.py:361-371`** catches `(BuildError, SourceError, sqlite3.Error, OSError)` and unlinks
  inside that `except`; the `finally` closes the connection but never unlinks. Any other exception
  escapes as a traceback (exit 1) and **leaves the partially-populated `--db` on disk**, against
  REQ-ING-013's "leaves no artifact behind". I could not reach it from the CLI's own inputs — three
  forced malformed-YAML faults all returned exit 2 with no file — so this is MINOR, but the unlink
  belongs in `finally`.
- **M7 — `build.py:326-332`** invents `--epoch-dir` as a third convention for locating the Epoch
  bundle. The project's existing convention is the `EPOCH_DATA_DIR` env var
  (`tests/unit/test_epoch_ingest.py:137`, `test_effort.py:392`, `test_deepswe_workflow.py:160`,
  `test_m5_board_measurement.py:28`). The CLI reads neither it nor anything in
  `data/epoch-source.yaml`, so an operator following the documented convention silently builds a
  blinded artifact and gets exit 3.
- **M8 — `scripts/smoke_deps.py:74-80`** ignores `RemoteSource.required`, so `make smoke-deps` stays
  red on arena while `build.py` treats the same outage as exit 3. Defensible (L.8 is about dependency
  reachability, not buildability) but unstated in either file, and plan §4's Definition of Done reads
  "`make smoke-deps` exit 0 or an owner ruling on W-024" — D-121 rules on the build, not on the gate.
- **M9 — `scripts/` is outside both gates:** `Makefile:77` is `ruff check src tests` and `Makefile:83`
  is `mypy src`. So `_probe_for`'s `rows, skipped = source.parse(...)` against
  `parse: Callable[..., object]` (`sources.py:57`) is type-unchecked. It happens to be correct — all
  seven `parse_*` functions are `(raw, *, …) -> tuple[list[...], int]`. Also verified: removing the
  `# noqa: BLE001` was *correct*, not a regression — `BLE` is not in `pyproject.toml:46-57`, so the
  directive was an unused-noqa (RUF100) and `ruff check scripts/smoke_deps.py` is now clean (the 24
  errors under `scripts/` are all pre-existing, in other files).
- **M10 — `docs/coverage-by-req.md` has no entry for REQ-ING-012 / REQ-ING-013** (grep finds them only
  at `docs/prd.md:278` and `:285`). Plan §4 makes the trace a closure gate, so this is a carry rather
  than a wave defect — but V3C-02 is evaluated against that file.
- **M11 — `tests/unit/test_ci_argument_drift.py:26`** globs `*.yml` only; a workflow added as `.yaml`
  is silently unchecked. The file's own `test_the_workflows_are_actually_parsed` (`:49`) guards the
  "found nothing" case for the current four files but not for this dimension.
- **M12 — process note, not a code defect.** During this review `src/app/workflows/build.py` twice
  appeared modified in `git status` with edits this seat did not make (a `return []` injected at the
  top of `_surfaces_left_without_evidence`); another seat is fault-injecting the same file
  concurrently. Every measurement above was taken with the file at HEAD content, and each surviving
  mutant is independently corroborated by pytest's own coverage report naming the same lines as never
  executed. The tree was clean again at the end of this run. Flagged so no stray edit is attributed to
  this review.

### PASS (what genuinely holds, with evidence)

- **The heredoc is gone and there is no second copy.**
  `git diff 9f4471d..HEAD -- .github/workflows/contract-tests.yml` removes the whole `python - <<'EOF'`
  block; `grep -rn "executescript(DDL)\|ci_advisor" .github/` returns only the five CLI invocations at
  `contract-tests.yml:81,85,94,95,97`. `conformance/test-ci-yaml.py` still passes: *"25 step(s)
  checked, 0 mismatch(es)"*.
- **`_read_back`'s identifier guard is sufficient, reachable AND tested.** `re.fullmatch` is fully
  anchored, so `build.py:63`'s `[A-Za-z_][A-Za-z0-9_]*` cannot be satisfied by a name carrying a quote,
  a semicolon or a newline; the value is interpolated inside double quotes only after the check
  (`build.py:124-127`). `tests/unit/test_build.py:281-286` creates `"weird-name!"` and asserts the
  `BuildError`. Mutant: `fullmatch` → `search` at `build.py:124` turns the suite **RED**. One of only
  two controls in this wave whose mutant died.
- **"No partial artifact survives a failure" is a real control on the paths I could reach.** Forced
  faults through `main()` — empty rosters document, malformed rosters YAML, scalar plans document —
  all returned exit **2** with the target file **absent**. Mutant: removing
  `target.unlink(missing_ok=True)` (`build.py:366`) turns the suite **RED**.
- **The injection-point fix is real at both sites.** `build.py:272` and `build.py:195` read
  `REMOTE_SOURCES` / `LOCAL_BUNDLES` at call time, and `tests/unit/test_build.py:212,230-232`
  monkeypatch the module attributes and take effect (proved by `test_cli_reports_zero_…` reaching exit
  0, which is unreachable with the real registry).
- **The D-118 drift is fixed and the drift check is a derivation, not an enumeration.**
  `contract-tests.yml:94-97` now passes `unlimited`/`low`/`medium`, all three present in
  `recommend.py:39` `BUDGETS`. `tests/unit/test_ci_argument_drift.py:55-64` reads the vocabulary from
  the code and the arguments from the YAML; `:67-72` pins the negative case. (Subject to B1: those CI
  lines are unreachable in practice.)
- **Frozen contracts untouched.** `git diff --stat 9f4471d..HEAD` lists 9 files, none of which is
  `src/app/adapter/main.py`, `rank.py` or `recommend.py` — so D-104, D-105, D-109 and D-115's frozen
  payload are intact, and `build_price_medians` is still called at `recommend.py:285` exactly as plan
  §2 W1 item 1 requires W1 to leave it.
- **The registry-coverage test is a real derivation.** `tests/unit/test_sources.py:22-30` walks
  `src/app/clients/` with `ast`; `:33-36` guards against a walk that finds nothing and passes
  vacuously.
- **D-117's five conditions are met on all three commits.** Author and committer
  `Claude <noreply@anthropic.com>`, `GP-Agent: claude-code/lead` and `GP-Task: M7-W1` trailers on each,
  no catastrophe-class git in the range, and `make check` re-run by this seat at HEAD: **exit 0**,
  396 passed / 12 skipped, `check_records PASS`, self-test PASS, install-check PASS.

---

## 2a-bis — hardened-invariant producer section (V3C-101)

**Hardened invariant:** *a partial or hollow build never leaves a servable artifact behind*
(REQ-ING-013).

**Producers of the invariant, enumerated from the code:**

| # | Producer | Line (HEAD) | Citing test | Mutant |
|---|---|---|---|---|
| 1 | curated stage stored nothing | `build.py:146-148` | **none** | survived |
| 2 | curated stage raised `SourceError` | `build.py:143-145` | `test_build.py:179` | n/a |
| 3 | empty source registry | `build.py:224-226` | `test_build.py:167` | n/a |
| 4 | source below `minimum_rows` | `build.py:233-238` | `test_build.py:154`, `:192` | n/a |
| 5 | required source unusable | `build.py:240-242` | `test_build.py:160` | n/a |
| 6 | optional source degrades to exit 3 | `build.py:243-247` | **none** | survived |
| 7 | bundle stored nothing / unreadable | `build.py:206-212` | failure arm only; success arm **none** | survived |
| 8 | reconciliation floor | `build.py:291-296` | `test_build.py:173` | n/a |
| 9 | `px_median` floor (Trap 1) | `build.py:303-305` | **none** | survived |
| 10 | read-back per-table floor (Trap 3) | `build.py:310-313` | **none** | survived |
| 11 | table-name guard before interpolation | `build.py:124-127` | `test_build.py:281` | killed |
| 12 | failed build leaves no file | `build.py:366` | `test_build.py:242` | killed |
| 13 | destructive default OFF (`--force`) | `build.py:341-343` | `test_build.py:261` | n/a |

**Citing test per producer:** as above — 8 of 13 producers have one.
**Gaps (tracked):** producers 1, 6, 7-success, 9, 10 — B2, B3, B4. Producer 13's `--force` *overwrite*
arm (`build.py:349-350`) is uncovered; only its refusal arm is tested.

---

## Acceptance-criteria evidence

| Criterion | Status | Evidence |
|---|---|---|
| REQ-ING-012 — one runnable production entry point | **partially met** | `src/app/workflows/build.py:318-381` (`main`, `__main__`); driven through the real entry point by `tests/unit/test_build.py:204,226,242,261,274`; typed/linted/covered (`make check` exit 0, 89% on `build.py`). **But** its only production caller (`contract-tests.yml:81`) cannot succeed — B1 — and no artifact was produced — B7. |
| REQ-ING-013 — a partial build is a failed build | **NOT met** | 8 of 13 producers cited (2a-bis table); 5 uncited, 4 mutants survived — B2, B3, B4. |
| W-023 closed | **NOT met** | `advisor.db` `px_median = 0` (measured now); B7. |
| D-120 exit-code mirror (0/2/3) | **met in the module, broken at the caller** | `build.py:377` (3 vs 0), `:343,:347,:368` (2); verified by hand: optional-source failure ⇒ 3, malformed inputs ⇒ 2 + no file. Caller: B1. |
| D-121 — arena optional | **NOT met as written** | Mechanism uncited (B2); the serving-path disclosure it is conditioned on is contradicted by `main.py:729-733` (B5). |
| D-118 — English budget vocabulary in CI | **met** | `contract-tests.yml:94-97` vs `recommend.py:39`; `tests/unit/test_ci_argument_drift.py:55`. |
| D-104 / D-105 / D-109 / D-115 unchanged | **met** | `git diff --stat 9f4471d..HEAD` — no scoring or adapter file in the 9. |

---

## K.8 contract drift check

```
$ grep -rn "build_price_medians" src/
src/app/workflows/build.py:44:from app.workflows.rank import build_price_medians
src/app/workflows/build.py:302:    report.price_models = build_price_medians(conn)
src/app/workflows/rank.py:143:def build_price_medians(conn: sqlite3.Connection) -> int:
src/app/workflows/recommend.py:31:    build_price_medians,
src/app/workflows/recommend.py:285:    build_price_medians(conn)

$ grep -rn "ci_advisor|executescript\(DDL\)" .github/
.github/workflows/contract-tests.yml:81,85,94,95,97   (CLI invocations only; no DDL, no heredoc)

$ git show HEAD:src/app/workflows/sources.py | grep -n "^REMOTE_SOURCES|^LOCAL_BUNDLES"
102:REMOTE_SOURCES: tuple[RemoteSource, ...] = (
148:LOCAL_BUNDLES: tuple[LocalBundle, ...] = (

$ grep -rn "REMOTE_SOURCES|LOCAL_BUNDLES" src/ scripts/ tests/
src/app/workflows/build.py:53   (import)   :195, :272  (call-time read)
scripts/smoke_deps.py:74        (function-local import), :77, :83
tests/unit/test_sources.py:17, :45, :46, :60, :64
tests/unit/test_build.py:212, :230, :231
```

**Verdict: OK.** The single-registry contract holds — two consumers, both deriving, neither
enumerating. `recommend.py:285` is untouched exactly as plan §2 W1 item 1 requires.

---

## K.9 candidates spotted outside this wave's scope

- `src/app/adapter/main.py:729-733` — `unavailable_reason` states a budget cause for every
  no-picks answer, including ones caused by absent evidence. W2 owns REQ-API-008 and should
  distinguish the two; D-121's known-gap paragraph already points at W2.
- `src/app/workflows/categories.py:23` — `primary_source` is annotated "informational" and now has
  three consumers treating it as authoritative to varying degrees (`build.py:167`, and the two places
  `main.py:475-483` warns about). Either it is a contract or it is a comment.
- `conformance/run-all.py` is **red at HEAD for pre-existing reasons** unrelated to this wave:
  `test-git-authority.py` flags `docs/reviews/m6-security-review.md:556,989` (a review *quoting* the
  forbidden commands), and `test-documented-commands.py` flags three docs citing a `make pin-check`
  target that does not exist. `make gate` cannot be green until these are ruled on.
- `scripts/` is covered by neither `make lint` nor `make typecheck` (`Makefile:77,83`) while
  `scripts/smoke_deps.py` is a Stage-4.3 gate and `scripts/check_records.py` is the governance
  validator. 24 ruff findings sit there today.

## Risks queued to next M

- The reachability question M6 carried and the owner deferred to M8 was answered empirically by this
  wave without anyone asking: **six of eight planted mutants survived a green suite, and every
  survivor was on a line the wave's own commit message called its point.** That is data for M8's
  decision, and it argues the mechanism is worth building.
- `advisor.db` and `owner_advisor.db` disagree with each other (72 vs 42 models; `px_median` 0 vs 41)
  and neither is the artifact commit `422455d` describes. Whichever ships, W4's go-live check must
  derive its claim from the file it deploys.
