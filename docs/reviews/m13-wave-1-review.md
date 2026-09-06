---
record_type: review
id: m13-wave-1-review
status: ratified
seat: independent
date: 2026-09-06
---
# M13-W1 — Code-Reviewer seat

**How this record was produced, stated first because D-133 turns on it.** The review was performed
by a separate session that did not author the code, received the frozen diff, and read its policy
from `subagent-profiles/Code-Reviewer.md` at the base ref rather than from the authoring session.
That seat was READ-ONLY by instruction, so it could not write this file; the verdict below is its
report, transcribed by the lead agent without softening. **The judgement is the reviewing seat's;
only the transcription is the author's.** If that distinction is not acceptable to the milestone
review, the correct disposition is WAIVED with a ledger row, not a quiet acceptance.

**Diff reviewed:** frozen copy of the W1 working-tree diff plus the five new files
(`m13-w1.diff`, 933 lines). The tree moved under the seat during the review (W2 work); it judged
the diff.

**Baseline the seat established before reviewing:** 810 passed / 7 skipped on `tests/unit`;
`mypy src` clean; `ruff check` clean on the nine touched files; the four new test files 51 passed.

## Verdict at submission: BLOCKING

### BLOCKING-1 — the probe ran the serving path and discarded the answer

`src/app/adapter/main.py`. The per-surface loop caught `sqlite3.Error` and never inspected the rows,
so it caught a MISSING table (which raises) and missed an EMPTY one (which returns nothing).
Reproduced against copies of the shipping artifact — `DELETE FROM models`, `DELETE FROM scores`, and
a `px_median` holding one row that joins no model all returned `None` (usable). In each state the
process boots, `/health` answers `evidence: servable`, and every `/v1` surface returns 200 with *"no
evidence to rank"*. That is W-023/W-058 exactly, produced by the wave that cites them.

The seat also refuted the comment's own claim to be *"the last way this probe can say yes"* — a
universal claim broken by a three-line reproduction.

**Disposition: FIXED.** The loop now reads the result and refuses when **zero** surfaces rank
anything. Zero rather than any, deliberately: an artifact serving eight of nine is degraded and the
engine already answers the ninth honestly per request, so refusing to boot on it would convert a
partial outage into a total one. Citing test:
`tests/unit/test_startup_schema_validation.py::test_an_artifact_that_ranks_nothing_is_refused`.

### MAJOR-1 — `/health` pays the probe on every request

`_database_unusable` is not only the startup probe; `health()` calls it per request. The wave
reasoned about boot cost alone. Measured by the seat: old checks ~0.06 ms, new probe ~11 ms on the
shipping artifact, ~75 ms at the largest artifact this process will boot, ~910 ms at the
`MAX_RANKED_ROWS` ceiling. `health()` is a sync handler on the same bounded worker pool `/v1` uses,
and both `fly.toml` and `Dockerfile` poll it every 30 s, unauthenticated.

**Disposition: FIXED.** The probe is memoised on `(path, st_mtime_ns, st_size)` — the artifact's
identity, not its path, because the refresh publishes by REPLACING the file (D-129) and a
path-keyed memo would keep answering for the artifact that was retired.

### MAJOR-2 — the blast radius was measured for one engine and applied to two

The wave reported *"9 of 27 combinations, picks unchanged"*, reproduced exactly for the model
engine. For `subscribe._pareto` the seat measured **15 of 27** combinations changing `frontier_size`
and **10** changing or losing the published `close_call` sentence — because plans sharing a model at
a dearer price are the equal-score case, which is the norm in a plan catalogue rather than an edge.

**Disposition: RECORDED.** The behaviour is correct; the omission was the measurement. Both figures
now appear in `recommend._dominates`'s docstring.

### MAJOR-3 — the docstring's reason was false

The claim *"a wrongly-retained row is never strictly cheaper than its dominator, so the value pick
lands on the same model"* is not sound: the value key is `(blended_per_m, model)`, so a price tie
breaks on NAME. The seat built the counterexample (`aaa-worse 80.0 @ $3`, `zzz-better 84.0 @ $3`,
`leader 86.0 @ $9`) and the pick moves. The conclusion holds on today's data — zero pick changes
across all 27 combinations — but "did not move here" and "cannot move" are different claims.

**Disposition: FIXED.** The docstring now states the measurement and names the counterexample.

### MAJOR-4 — the accept-half test never ran outside the owner's machine

`test_the_real_artifact_is_accepted` gated on `Path("advisor.db").exists()` with the comment *"the
repo ships it; CI may not"*. `.gitignore` is `*.db`: the repo does not ship it, so the only guard
against the new probe failing closed on a good artifact skipped on every fresh clone and in CI.

**Disposition: FIXED.** The guard is now built from the canonical seed and runs unconditionally;
the shipping-artifact check is kept in addition, and it is the one allowed to skip.

## MINOR findings and their disposition

| Finding | Disposition |
|---|---|
| `UnbuiltEvidenceError` rationale describes a path `category_ranking` cannot reach | Accepted; comment left, it is a true statement about a boundary |
| `_largest_surface_row_count` already ran nine rankings and swallowed the error — boot now runs 18 | **Open.** Real duplication; deferred to W5 with a ledger row rather than restructured mid-wave |
| The predicate is written twice again, mitigated by a shared test table | Accepted as a named tradeoff, now stated in `subscribe._plan_dominates` |
| CWD-relative paths in two new test files | **FIXED** — `Path(__file__).resolve().parents[2]` |
| `LEGACY_PROBE_SCHEMA` declared `value` not `score`, so the fixture isolated a typo | **FIXED** |
| `runner_verdict.sh` absent from `INSTALL-MANIFEST.md` and `scripts/README.md` | **FIXED** |
| Brittle single-character assertion; `split("passed")[1]` | Accepted; superseded by the wiring tests added for the Tester seat's BLOCKING |
| No test asserts the `skipped` line is absent on a clean run | **Open**, MINOR |

## What the seat checked hardest and found sound

- **The `"is level"` branch is not dead and did not lose coverage.** Two pre-existing tests still
  exercise it. The fixture change in `test_close_call_is_disclosed` is a legitimate correction, not
  a test bent to fit the code: the old "near-tie" was a tie against a dominated row.
- **The dominance predicate** on empty lists, single rows, exact ties, NaN scores, and sort-order
  invariance of `frontier[0]`. Exactly two producers exist (`recommend`, `subscribe`); both fixed.
- **REQ-FIX-003 churn risk quantified**: `evidence_source` is deterministic across rebuilds and the
  digest is stable across a `VACUUM`ed copy. This is not a refresh that publishes every cycle.
- **`runner` accounting**: all eight legs reach exactly one of `record`/`skip`; variables survive
  the brace group; `set -u` without `set -e` fails CLOSED if the library cannot be sourced; no
  consumer reads `runner`'s exit code, so the new exit-1-on-skip breaks nothing.
