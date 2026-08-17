---
record_type: review
id: m7-wave-1-rereview
status: proposed
date: 2026-08-18
---
# Wave 1 Code Re-Review — fix delta (m7)

**Reviewer:** Code-Reviewer subagent (fresh eyes — authored no line of the wave or of the delta)
**Date:** 2026-08-18
**Commit range:** `fa87fbf..HEAD` (`6952a55`, `48e0bb7`) — 18 files, +1664/-24
**Prior verdict:** `docs/reviews/m7-wave-1-review.md` — BLOCKING, 7 BLOCKING / 12 MINOR
**Risk tier:** HIGH (V4C-50 — a fix inherits the risk class of its bug; both bugs fixed here
destroyed or fabricated the artifact this milestone exists to produce)

**Method note (W-022 + concurrency).** The working tree was modified by another seat twice during
this review (`except BaseException` → `except Exception` in `build.py`, mid-run). Every measurement
below was therefore taken against a pristine `git archive HEAD` snapshot with `PYTHONPATH`
isolation — the editable install is a plain path file
(`.venv/lib/python3.14/site-packages/__editable__.model_ranking-0.1.0.pth`), not a meta-path finder,
so `PYTHONPATH` wins; verified by printing `app.workflows.build.__file__` before running anything.
All pytest runs used `python -B`. Snapshot baseline: **461 passed, 13 skipped**.

---

## Verdict

**BLOCKING** — 2 BLOCKING, 9 MINOR.

This delta is a large real improvement and the numbers say so honestly: **14 of the 17 mutants I
planted died**, including every one of the five that survived my first round. The floors are floors
now, the artifact is genuinely rebuilt and genuinely serves, `--force` no longer eats the operator's
database, and the `unresolvable_modules` extraction is exactly the right response to a predicate
that could not fail.

But the lens you asked me to apply finds the same shape twice more, and both times on the line the
commit message names as the fix:

- **The B1 fix does not run.** GitHub Actions runs `run:` blocks under `bash -e`. The step's own
  `set -o pipefail` guarantees the shell exits at the pipeline with status 3, before
  `code=${PIPESTATUS[0]}` is ever evaluated. The entire `if` block is unreachable. The step still
  fails on exit 3, exactly as before. I reproduced it.
- **The B5 fix has no guard, and D-121 says it does.** The mutant that collapses both reasons back
  into one sentence survives a green 461-test suite, because `main.py:752` — the budget sentence —
  is executed by no test in this repository. The ADR amendment asserts a citing test that asserts
  that; it does not.

---

## Findings

### BLOCKING

**RB1 — `.github/workflows/contract-tests.yml:90-100`: the exit-3 handling is unreachable. The step
still fails on 3.**

GitHub Actions runs a `run:` block with no `shell:` key as **`bash -e {0}`** (with an explicit
`shell: bash` it is `bash --noprofile --norc -eo pipefail {0}` — `-e` either way). No workflow in
this repository sets `shell:` or `defaults.run.shell`:

```
$ grep -rn "shell:|defaults:" .github/workflows/   →  no matches
```

So `errexit` is on. Line 91 turns on `pipefail`, which makes the pipeline at line 92 carry the
builder's status 3 rather than `tee`'s 0 — and a standalone command returning non-zero under
`errexit` **terminates the script immediately**. Line 93 (`code=${PIPESTATUS[0]}`) and the whole
`if`/`elif` at lines 94-100 never execute.

Reproduced verbatim, substituting a stub that prints the payload and exits 3:

```
$ bash -e ci_step.sh                # GitHub's default shell
{"required_operator_actions": ["arena is unavailable"]}
exit=3                              # ← step FAILS; notice never printed

$ bash ci_step.sh                   # same script without -e
{"required_operator_actions": ["arena is unavailable"]}
::notice::built with degraded evidence (expected on a runner: no Epoch bundle)
  ACTION: arena is unavailable
REACHED-END-OF-STEP
exit=0
```

The consequence is unchanged from my first round: a runner has no Epoch bundle (`build.py:387`
passes `bundle_dir=None` without `--epoch-dir`), so `main()` returns 3 (`build.py:423`), the step
fails, and the three steps below it — the coverage/source-health report and the recommend smoke
carrying this wave's own D-118 argument fix — never run.

The irony is load-bearing and worth stating: `set -o pipefail` was added to make the exit code
visible, and it is the single line that makes the handler unreachable. Without it the pipeline
would have returned `tee`'s 0, `-e` would not have fired, and the logic would have worked.

Two shapes that do work under `errexit` (both make the command part of a compound, which `-e`
exempts):

```bash
code=0
python -m app.workflows.build --db ci_advisor.db > build-report.json || code=$?
cat build-report.json
```

or `set +e` around the pipeline before reading `PIPESTATUS`. **And per V4C-50 this fix needs a
citing test of its own**: `tests/unit/test_ci_argument_drift.py` already parses these `run:` blocks,
so the cheapest real control is to execute the step's script under `bash -e` with a stubbed
`python` on `PATH` and assert the notice line appears and the status is 0. A YAML-text assertion
would not have caught this one — the text is correct; the shell is not.

**RB2 — `src/app/adapter/main.py:743` + `docs/decisions.md` (D-121 amendment): the fix for B5
replaced one blanket explanation with another, and the guard the ADR names does not exist.**

Mutant, run against the pristine snapshot:

```
GREEN(SURVIVED) | main.py:743  `if not health.get("sources"):` → `if True:`  | 461 passed, 13 skipped
red(killed)     | main.py:743  `if not health.get("sources"):` → `if False:` | 1 failed
```

`if False:` dies (`test_empty_answer_reasons.py:125`), so the *new* sentence is pinned. `if True:`
survives, so **nothing pins that the other sentence still exists**. Corroborated independently by
coverage: `src/app/adapter/main.py:752` — the `return` carrying *"No model on this surface's
benchmark fits the requested budget"* — is reported as **never executed** by the full 462-test run.
The budget branch is dead to the suite.

The concrete failure this permits: a user asks `assistant` with `--budget low` against an artifact
that has 389 Arena rows and nothing under $2/M. The honest answer is "nothing fits your budget".
Under the mutant — i.e. under any future edit that widens this predicate — they are told *"This
surface has no evidence at all: no Arena text source is present in the served database."* That is a
**worse** false statement than the one B5 removed: it accuses the artifact of being empty when it is
full, and a user's rational response is to go looking for a data outage that does not exist.

What makes this BLOCKING rather than a test gap is the ADR. `docs/decisions.md`, D-121's amendment,
states:

> pinned by `tests/unit/test_empty_answer_reasons.py`, **which also asserts that a surface WITH
> evidence still gets the budget sentence** — the fix must not replace one blanket explanation with
> another.

That assertion is not in the file. `test_the_two_reasons_are_not_the_same_sentence`
(`tests/unit/test_empty_answer_reasons.py:141-158`) asserts that `coding` has picks — which means
`rec is not None` and `unavailable_reason` is `None`, so the budget sentence is never produced — and
then re-asserts the *no-evidence* sentence, duplicating the test above it. The string "fits the
requested budget" appears in no test in the repository:

```
$ grep -rn "fits the requested budget" tests/   →  no matches
```

So a governance record now asserts the existence of a control that does not run. That is the same
defect class as the original finding, one round later, in the document written to close it. Fix:
make the second test build an artifact with evidence and an unsatisfiable budget, assert the budget
sentence, and assert the two sentences differ — then `if True:` dies.

### MINOR

- **MR1 — `src/app/workflows/build.py:299`: the `bundles=` injection parameter is unproven.**
  Mutant `_ingest_bundles(conn, bundle_dir, run, bundles)` → `_ingest_bundles(conn, bundle_dir, run)`
  **survives green**. The parameter added at `build.py:273` to answer B2 is forwarded by no test that
  depends on the forwarding: the only caller passing it (`test_empty_answer_reasons.py:105`,
  `bundles=()`) has `bundle_dir=None`, so both paths produce the same served database. The
  artifact-safety tests inject by monkeypatching `build_mod.LOCAL_BUNDLES` instead. An injection
  point that no test proves is honoured is the shape this wave has now shipped three times.
- **MR2 — `src/app/workflows/build.py:322`: `conn.commit()` is dead, and the test written to pin it
  says otherwise.** Mutant `conn.commit()` → `pass` **survives green**, because every `ingest_*`
  commits internally via `with conn:` and `reconcile`/`build_price_medians` do the same, so the
  outstanding DELETE from the new rollback is committed before this line is reached. The new
  `test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims` (`tests/unit/test_build.py`)
  states in its docstring that *"Deleting `conn.commit()` at build.py:307 — and even replacing it
  with `conn.rollback()` — left the whole suite green"* and presents itself as the fix. It is not:
  the mutant still survives. Either the call is load-bearing and needs a test that dies, or it is
  redundant and the docstring's claim should go. **A test whose stated rationale is false is worse
  than no test, because it retires the question.**
- **MR3 — `src/app/workflows/build.py:252`: half the rollback is untested.** Mutant
  `for table in ("pricing", "scores")` → `for table in ("scores",)` **survives green**. A rejected
  optional source's PRICING rows would survive into the committed artifact and be fed to
  `build_price_medians` at `build.py:317` — the reference price of REQ-CAN-003 computed partly from
  evidence the build itself declared unusable. Unreachable today (`litellm` and `openrouter` are both
  `required=True`), reachable the moment D-121's own Revisit-when clause is exercised.
- **MR4 — `src/app/workflows/build.py:209`: the rollback is on one of the two paths that need it.**
  `_ingest_sources` now calls `reset_source`; `_ingest_bundles` does not. The comment justifying the
  rollback (`build.py:240-251`) argues that leaving truncated rows behind stops the serving path's
  "no evidence source is present" branch from firing — and that argument applies with *more* force to
  `epoch_deepswe_external`, which is `agentic-coding`'s sole primary evidence. Low reachability
  today (`ingest_epoch`/`ingest_deepswe` parse before they store), but `LocalBundle.ingest` is an
  arbitrary callable and the new tests themselves inject lambdas into it
  (`tests/unit/test_build_artifact_safety.py:240,274,306`).
- **MR5 — `tests/unit/test_build_artifact_safety.py:356-396` proves less than it says.** The fixture
  registers **two sources both named `aider`**: the healthy one from `_sources()` (`:87-93`,
  `minimum_rows=1`) and the hollow one (`:372-379`, `minimum_rows=10_000`). `reset_source` deletes by
  NAME, so the rollback wipes the healthy source's rows too, and the closing assertion
  `count(*) WHERE source = 'aider' == 0` (`:396`) cannot distinguish *"the rejected source was rolled
  back"* from *"a healthy source's evidence was destroyed by a different source's failure"*. The
  repository already treats duplicate source names as a defect
  (`tests/unit/test_sources.py:80 test_source_names_are_unique`). Give the hollow source its own name
  and assert both that its rows are gone and that `aider`'s survive.
- **MR6 — W-023's citing test does not run anywhere but this machine.** In a pristine
  `git archive HEAD` snapshot the suite reports **461 passed, 13 skipped** against 462/12 locally, and
  the extra skip is:
  `SKIPPED tests/unit/test_api_config.py:691: advisor.db is not present in this checkout`.
  `advisor.db` is gitignored (`.gitignore:50 *.db`) and the `Dockerfile` copies only `pyproject.toml`
  and `src` (`Dockerfile:11-12`), pointing `MODEL_RANKING_DB` at `/data/advisor.db`
  (`Dockerfile:23`). So the artifact this wave produced exists on one disk, is in neither the
  repository nor the image, and its pin is a silent skip in CI — the quietest form of a control not
  running, and the exact hazard AGENTS.md §5 names for skipped required checks. **The substance IS
  closed and I verified it independently** (below), and the *portable* half is genuinely pinned by
  `tests/unit/test_empty_answer_reasons.py:72-110,156`, which builds through `build()` and serves the
  result. What is missing is a check that fails when the shipped artifact is stale. This is W4's
  problem more than W1's — the deploy has to produce the artifact anyway — so I am not blocking on it,
  but it must not be inherited as "done".
- **MR7 — untracked build litter.** Neither `build-report.json` (written by
  `contract-tests.yml:92`) nor `advisor.db.building` (the new workspace, `build.py:385`) is ignored:
  `git check-ignore build-report.json advisor.db.building` exits non-zero for both, because
  `.gitignore:50`'s `*.db` does not match `advisor.db.building`. A SIGKILLed build leaves a ~970 KB
  untracked file next to the artifact that looks committable.
- **MR8 — drive-by edits outside the plan's scope (profile §2b).** `scripts/check_records.py:82`
  (`__slots__` reordered), `scripts/slopsquat_check.py:20-26` and `scripts/wave_check.py:13-15`
  (imports split, a `# noqa` removed) are ruff-fix drive-bys in files no gate lints
  (`Makefile:77` is `ruff check src tests`) — including the governance validator itself. They are
  harmless (`check_records --self-test` still passes) but they also silently invalidate the ledger
  row written the same day: **W-026 records "24 pre-existing errors" and `ruff check scripts/` now
  reports 18.** Either finish the job under W-026 or leave the file alone; a partially-fixed
  directory makes the escalation's own measurement wrong.
- **MR9 — `scripts/smoke_deps.py` vs `RemoteSource.required` — my answer to your question:
  CARRY, do not close in W1.** Closing it means deciding whether L.8 is a *dependency-reachability*
  gate (arena down ⇒ red, correct today) or a *buildability* gate (arena optional ⇒ amber), and that
  is a gate-definition question, which AGENTS.md §3 makes an escalate-now / owner call — the same
  reason W-026 was escalated rather than fixed. What W1 *should* do is one line of comment in
  `smoke_deps.py` naming the divergence and pointing at D-121, so the next reader does not read the
  silence as agreement. Carry the decision to the W4 deploy gate, where `make smoke-deps` is already
  a Definition-of-Done item with an owner ruling attached.

### PASS — what the delta genuinely fixed, with evidence

**Mutation summary: 17 planted, 14 killed.** Every mutant that survived my first round now dies:

| Mutant | First round | Now |
|---|---|---|
| `sources.py:144` arena `required=False` → `True` | survived | **killed** (`test_sources.py:80`) |
| `build.py:317` px_median floor → `if False:` | survived | **killed** (`test_build.py`, `test_an_unbuilt_px_median_fails_the_build`) |
| `build.py:325` read-back floor → `if False:` | survived | **killed** (`test_build_artifact_safety.py:321`) |
| `build.py:146` curated `stored<=0` → `if False:` | survived | **killed** (`test_build_artifact_safety.py:203`) |
| `build.py:254` `if source.required:` → `if True:` | survived | **killed** (`test_build.py`, `test_a_failed_optional_source_names_the_surface_it_blinds`) |
| `build.py:212` bundle `results.append` → `pass` | survived | **killed** (`test_build_artifact_safety.py:252`) |

New controls, all with dying mutants:

- **`--force` no longer destroys the artifact.** `build.py:385,411` (workspace + `replace`);
  mutant `workspace = target` **killed** by `test_build_artifact_safety.py:115-129`, which asserts
  the previous file's bytes *and* mtime are unchanged after a failed rebuild.
- **`except BaseException` cleanup.** `build.py:397`; mutant → `except Exception` **killed** by
  `test_a_keyboard_interrupt_leaves_no_artifact_behind` (`:182`). Workspace cleanup mutant
  (`workspace.unlink` → `pass`) **killed** by `test_no_workspace_file_survives_either_outcome` (`:144`).
- **Directory target.** `build.py:358`; mutant → `if False:` **killed** by `:344`.
- **`parse_pricing` envelope guard.** `src/app/clients/litellm.py:69,78`; mutant → `if False:`
  **killed**. The test is a derivation, not a case list: `tests/unit/test_parser_envelopes.py:39-41`
  parametrises `REMOTE_SOURCES` × 8 hostile payloads and guards against vacuity at `:34`. The
  `data: Any` change is the right diagnosis — an annotation over `json.loads` is an assertion, and
  mypy was correctly calling the guard unreachable under the old one. `mypy src` still clean.
- **Exit 3 fires on ONE action, not two.** `build.py:423`; mutant `len(...) > 1` **killed** by
  `test_cli_exit_three_fires_on_a_single_missing_action`.
- **Rejected-source rollback.** `build.py:252-253`; mutant `pass` **killed** by
  `test_build_artifact_safety.py:356` (see MR3/MR5 for what it does *not* cover).
- **`unresolvable_modules` extracted from the test body.** `tests/unit/test_ci_argument_drift.py:85`
  + `test_the_module_check_can_fail` at `:120`, which drives the real predicate with a known-bad
  block rather than re-implementing it. This is the correct response to your own stay-green
  survivor, and it is the pattern RB1 now needs applied to the shell.
- **W-023's substance is real, verified from the artifact rather than from the report (Trap 3).**
  I served `advisor.db` through `TestClient` myself:

  ```
  agentic-coding | picks=3 | stale=True
  coding         | picks=3 | stale=True
  assistant      | picks=0 | stale=True | "This surface has no evidence at all: no Arena text
                                          source is present in the served database, so nothing was
                                          ranked and no budget was applied."
  ```

  and read the file directly: 73 models, 72 `px_median`, sources `aider`/`swebench`/
  `epoch_swe_bench_verified`/`epoch_deepswe_external` in `scores`. **D-121's binding condition now
  holds at runtime** — that half of the amendment is true and I confirmed it against the artifact,
  not the prose.
- **Test inversion done right.** `tests/unit/test_api_config.py:673-695` used to assert the artifact
  was broken and now asserts it is servable, with the remedy command in the failure message. A test
  pinning a known defect that cannot notice the defect's removal becomes a test that *requires* the
  defect; this one noticed. (Its reach is MR6.)
- **Gates green on the pristine snapshot:** `ruff check src tests` clean · `mypy src` — *"Success:
  no issues found in 31 source files"* · 461 passed / 13 skipped.
- **B6 handled honestly.** W-027 (`docs/warnings.ledger.md`) states the plan promise was not
  delivered, names the one-line owner remedy, and does not claim otherwise. That is the right
  disposition; I have nothing to add to it.

---

## 2a-bis — hardened-invariant producer section (V3C-101)

**Hardened invariants:** (1) *a partial or hollow build never leaves a servable artifact behind*;
(2) *a surface that cannot answer states the true reason* (D-121's binding condition).

**Producers of (1), enumerated from the code, with citing test and mutant outcome:**
`build.py:146` curated floor → `test_build_artifact_safety.py:203`, killed ·
`build.py:157` curated SourceError → `test_build.py:179`, n/a ·
`build.py:224` empty registry → `test_build.py:167`, n/a ·
`build.py:233` source floor → `test_build.py:154`, n/a ·
`build.py:254` required source → `test_build.py:160`, n/a ·
`build.py:258` optional source → `test_build.py`, `test_a_failed_optional_source_…`, killed ·
`build.py:252` rejection rollback → `test_build_artifact_safety.py:356`, killed (half — MR3) ·
`build.py:206-212` bundle floor + success → `:223`, `:252`, killed ·
`build.py:305` reconcile floor → `test_build.py:173`, n/a ·
`build.py:317` px_median floor → `test_an_unbuilt_px_median_fails_the_build`, killed ·
`build.py:325` read-back floor → `test_build_artifact_safety.py:321`, killed ·
`build.py:124` identifier guard → `test_build.py:281`, killed ·
`build.py:385/397/411` workspace+rename+BaseException → `:115`, `:144`, `:160`, `:182`, killed ·
`build.py:358` directory target → `:344`, killed ·
`litellm.py:78` envelope guard → `test_parser_envelopes.py:41`, killed.

**Producers of (2):** `main.py:743` no-evidence branch → `test_empty_answer_reasons.py:125`, killed
on `if False:` · `main.py:752` budget branch → **no producer test; coverage reports the line never
executed; `if True:` survives** (RB2).

**Gaps:** RB2, MR1, MR2, MR3, MR4 — tracked above.

## K.8 contract drift check

```
$ git show HEAD:src/app/workflows/build.py | grep -n "bundles|reset_source|workspace|BaseException"
183:    bundles: Sequence[LocalBundle] | None = None,     # _ingest_bundles
252:            for table in ("pricing", "scores"):
253:                reset_source(conn, table, source.name)
273:    bundles: Sequence[LocalBundle] | None = None,     # build()
299:    bundle_reports, bundle_missing = _ingest_bundles(conn, bundle_dir, run, bundles)
385:    workspace = target.with_name(target.name + ".building")
397:    except BaseException as exc:
411:    workspace.replace(target)

$ grep -rn "reset_source" src/
src/app/workflows/schema.py:406:def reset_source(...)   # table allowlist ("pricing","scores")
src/app/workflows/build.py:52 (import), :253 (call)
src/app/workflows/ingest.py  (existing callers, unchanged)
```

**Verdict: OK.** `build()`'s signature widened by one optional keyword with a default, so no caller
breaks; `reset_source` is reused rather than re-implemented, and its own table allowlist
(`schema.py:412`) still bounds the interpolation. No frozen contract moved: `git diff --stat
fa87fbf..HEAD` touches `main.py` only inside `_answer_for`, and `rank.py`/`recommend.py`/
`categories.py` not at all — D-104/D-105/D-109/D-115 intact.

## K.9 candidates outside this delta's scope

- `src/app/adapter/main.py:752` being unexecuted by 462 tests means the *entire* "evidence present,
  budget excludes everything" scenario is untested at the API layer. W2 owns REQ-API-008 and will be
  editing exactly this block.
- `conn.commit()` at `build.py:322` being a no-op (MR2) suggests the whole transaction model here is
  implicit — every `ingest_*` owning its own `with conn:` means `build()` cannot roll back a stage
  once it has run. That is why the B-round rollback had to be a `reset_source` DELETE rather than a
  savepoint, and the comment at `build.py:248-251` says so. Worth a deliberate decision in M8 rather
  than an inherited one.
- The `Dockerfile` ships no evidence database (MR6). W4 must decide whether the image carries the
  artifact or the deploy builds it, and `fly.toml`'s volume story has to match.

## Risks queued to next M

- Three rounds in, the same defect has now appeared four times in this wave alone: `build()`'s
  default argument, `_ingest_bundles`' default argument, the CI step's unreachable branch, and the
  budget sentence with no test. **All four are "the code is right, the path to it is not".** M8's
  carried question about mechanically checking reachability now has four in-milestone instances plus
  M6's ten; that is no longer a hypothesis.
- Mutation testing found what three green gates did not, in both rounds, on both sides. Whatever M8
  builds, an in-repo mutant registry for the load-bearing predicates is the cheapest form of it.
