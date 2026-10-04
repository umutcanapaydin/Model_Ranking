---
record_type: plan
id: m18-wave-6-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W6 plan — first-release preparation

**Working plan for `wave/m18-w6`**, deleted before merge. Milestone plan: `docs/plans/m18-plan.md`
§2 W6, with the W5 amendment that moved #60 and #85 here. The branch is stacked on `wave/m18-w3`,
which changes the same client gates (`tests/unit/test_ios_client_contract.py`).

**Risk: HIGH**, as the milestone plan says. The wave writes the release's security invariants list,
changes how dependencies are installed, and changes the gates that hold D-126 and D-160. By D-172 no
security pass runs on the slice; the milestone closure's security seat reads it.

## Issues

| Issue | What | Phase |
|---|---|---|
| #89 | One security-invariants list, each row citing its negative test, held by a gate (W-131) | P1 |
| #90 | W-125, W-126 and W-130 re-measured, then fixed red-first or ruled | P2 |
| #35 | A lock file, so every install gets the tested versions | P3 |
| #26 | pyarrow off the serving image: an ingest-only extra | P3 |
| #88 | The data licence table and its options; the owner rules | P4 |
| #91 | A protocol for a stranger's first use, whose questions become the next held-out set | P4 |
| #110 | Text pins and the declaration gate accept code under `#if false` | P5 |
| #107 | More ways to make a URL from text pass the compiler gate | P5 |
| #60 | The arithmetic and sort tripwires match names, not what the names are | P5 |
| #85 | The refinement and question privacy sinks hold by spelling, not by data flow | P5 |
| #81, #115 | The owner's: workflow edits (the agent proposes the diff), and the Turkish prompt seen on a phone | PR |

## What was measured before planning (at `8a18324`)

- **W-125 still holds.** Importing `app.adapter.main` loads `app.workflows.ingest`, every
  `app.clients` module (`arena_slices` and `parquet_reader` among them) and `httpx`. It does not load
  pyarrow.
- **W-130's premise has changed, and the risk has not.** The refresh child now starts a grandchild:
  the parquet reader (D-165, `arena_slices.py:293`). That grandchild gets its own stdout pipe and a
  temporary file for stderr, so it does not hold the pipe the engine reads. But a timeout kill takes
  only the child, and leaves the reader running on its own watchdog (65 s).
- **W-126** is the same kill path from the other end: an engine killed hard leaves its child running
  and holding the lock.
- **No lock tool** is installed (`uv` and `pip-compile` are absent); `pyproject.toml` has lower bounds
  only.

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan |
| P1, invariants | #89 | `docs/security-invariants.md` lists every invariant from the M16 and M17 closure reconstructions and the M18 waves. Each row cites the negative test that fails without it. A gate refuses a row whose test does not exist, and a test that names an invariant no row lists. A sample of rows is mutated, and each mutant is killed by the test its row names |
| P2, the cycle's limits | #90 | W-125: the server imports no client and no ingest module, held by the import test extended to them (red first). W-126 and W-130: the cycle runs in its own process group, the timeout kills the whole group, and the cycle carries its own wall-clock limit inside `refresh.main`, each red first. Or each one is ruled, with the reason, in the ledger |
| P3, installs | #35, #26 | `pyarrow` moves to an `ingest` extra. Lock files with hashes are generated from `pyproject.toml`; `make install` and the release venv install from them. A gate fails when a lock is stale against `pyproject.toml`. The Dockerfile installs the serving lock. The CI change is the owner's, proposed as a diff |
| P4, records | #88, #91 | A licence table for every served source, with options and their cost to the product; the owner's ruling is the PR's question, and an ADR follows it. A written protocol for a stranger's first use, with consent and nothing leaving the device unasked |
| P5, compiler gates | #110, #107, #60, #85 | `#if false` code is invisible to the pins, or a dropped declaration fails the gate. A declaration of type `URL` outside the allowed files fails the compiler gate. An aliased position and a second same-named sort each fail. A value derived from typed text that reaches the boards request or the standings file fails |

**The valve.** P5 is the part to cut if the wave runs long. Each of its issues needs a compiler-level
design, and none blocks a first release on the owner's own devices. If it is cut, its issues move to
M19, and the milestone plan records the move.

**Not in this wave.**
- The owner's workflow edits (#81): proposed as a diff only, since `.github/workflows/**` is the
  owner's.
- The prompt seen on a phone (#115): it needs the owner's phone.

## K.8 contracts (grep at `8a18324`)

```
src/app/adapter/nightly.py:73:TIMEOUT_SECONDS = 30 * 60.0
src/app/adapter/nightly.py:263:            proc = await asyncio.create_subprocess_exec(
pyproject.toml: [project] dependencies, [project.optional-dependencies]
Makefile:81:install: $(VENV)/.installed
```

No `/v1` change.

## The one alternative

**Leave all of this for a commercial launch.** The milestone's aim is the app in the owner's hands
and ready for a first reader. A first reader is a stranger (#91). A deploy beyond the owner's Mac
needs the invariants list (Stage 5.1), a tested install (#35) and the licences ruled (#88), so the
wave goes ahead.
