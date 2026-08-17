---
record_type: review
id: m7-wave-1-security-rereview
status: proposed
date: 2026-08-18
---
# Wave 1 Security RE-REVIEW (m7) — the fix delta

**Reviewer:** Security-Reviewer subagent (fresh eyes; authored no line of this wave or its fixes — K.7)
**Date:** 2026-08-18
**Commit range:** `fa87fbf..HEAD` (6952a55, 48e0bb7) — 18 files, +1664/-24
**Source:** A (baseline `subagent-profiles/Security-Reviewer.md` v2.0, read from the protected base ref)
**Risk tier:** HIGH — inherited, not re-derived down. A fix inherits the risk class of the bug it
fixes (V4C-50), and this delta rewrites the artifact-publication path, the builder's exception
contract, an untrusted-input parser, and the unauthenticated `/v1` explanation field.

**Method.** Every claim below is a reproduction against this tree with `python -B` (W-022), not a
reading of the diff. Where I could not reach a defect I say so and say what stopped me.

---

## Verdict

**BLOCKING**

Two BLOCKING. Both are in the new code, and both are the *original* finding surviving through a
narrower door than the one that was closed — which is the failure mode a re-review exists to catch.

Credit where it is due first, because it is substantial: BLOCKING-1 and BLOCKING-2 are genuinely
fixed for the sequential, single-process case, and I verified them adversarially rather than
accepting the summary.

---

## What I confirmed FIXED

### BLOCKING-1 — the target is no longer the workspace ✅
`build.py:387-411`. Reproduced the original data-loss exploit against the new code: a 970 KB
working artifact, `--force`, and a `MemoryError` injected mid-build.

```
RE-RAISED MemoryError simulated OOM on a 4GB body
previous artifact byte-identical: YES
files present: art.db
```

The previous artifact is byte-identical, no `.building` residue survives, and the failure re-raises
instead of being dressed as exit 2. The original exploit is dead.

### BLOCKING-2 — the envelope guard and the `BaseException` cleanup ✅
`litellm.py:65-80`. All five hostile envelopes now become `SourceError`, and `{}` still parses:

```
'[]' '"x"' 'null' '123' 'true'  -> SourceError: litellm payload is valid JSON but not an object
'{}'                            -> ok
```

The annotation-as-assertion diagnosis in the commit body is correct and worth keeping: `data:
dict[str, Any] = json.loads(raw)` made mypy call the missing guard unreachable, so the type system
was actively defending the hole. `Any` plus an `isinstance` is the right shape.

`main.py:395-408`'s `except BaseException` + selective re-raise is correct and not over-broad: the
workspace is unlinked *before* the branch, so every exit path is clean before control leaves.
Confirmed no leak on the re-raise path — a Python traceback carries no local values, only the
exception message, and the target is untouched.

### MINOR-1 — the rejected-source rollback works, and the SAVEPOINT reasoning is right ✅
`build.py:240-253`. Reproduced the original leak and confirmed it is gone. The "a SAVEPOINT cannot
do this" note is correct and I verified the cause: every `ingest_*` writes through `with conn:`
(`ingest.py:63`, `ingest.py:126`), which commits and discards outstanding savepoints.

**On the coordinator's question — can the reset miss a table a source writes to?** No, today.
`ingest.py` writes to exactly two tables: `_store_pricing` → `pricing` (`ingest.py:64-66`) and
`_store_scores` → `scores` (`ingest.py:127-129`). Nothing else. The two-table loop is complete.
See MINOR-6 for the join *key*, which is a different question and is not safe.

### MINOR-3 — directory target ✅
`build.py:356-359`. Refused up front with the declared code 2.

---

## BLOCKING

### BLOCKING-4 — the verified database and the published database are not the same file
`src/app/workflows/build.py:387-388` and `src/app/workflows/build.py:411`

The workspace name is deterministic — `target.with_name(target.name + ".building")` — and every run
begins by unconditionally deleting whatever is at that path (`workspace.unlink(missing_ok=True)`).
`_read_back` (`build.py:309`) validates the **open connection**; `workspace.replace(target)`
(`build.py:411`) acts on the **path**. Nothing binds the two.

So a second invocation against the same `--db` can put its own file at that path while the first
build is finishing, and the first build then publishes it — having verified something else.

**Reproduced.** Two builders, same `--db`. Builder A ran a complete, successful build and printed
`"built": true` with `verified_from_artifact` showing 73 models / 323 scores / 72 medians read back
out of *its* file. What A published:

```
=== what landed at the TARGET? ===
-rw-r--r--  77824  /tmp/sec_race/art.db
tables: 7
  models: 0    scores: 0    pricing: 0    px_median: 0
```

A schema-valid database with **zero rows in every table, including `px_median`** — Trap 1's
artifact exactly, at the target path, published by a builder that reported success and whose
read-back proved 73 models. `rank.py:225` JOINs `px_median`; every surface answers 200 with zero
picks. This is worse than the original BLOCKING-2, whose residue at least came from a run that
*failed*.

**Honesty about the repro:** I won a *synchronised* race — I held A at the `replace` call until B
had re-created the workspace. I did **not** win it on natural timing; in the natural interleaving I
ran, SQLite detected its file had been unlinked, the loser died with `attempt to write a readonly
database` → exit 2, and the target kept the good build. That mitigation is real and I credit it. It
is also incidental: it protects the *loser*, not the target, and it does not fire in the ordering
that matters — B merely has to *start* (reaching `connect(workspace)`, which is the first thing
`main()` does after argument checks) inside A's finishing window.

**Why this is BLOCKING and not a theoretical race.** Nothing prevents or detects concurrent
invocation: no lock, no `O_EXCL`, no unique name. The overlapping-build scenario is ordinary — the
Monday cron in `contract-tests.yml` overlapping a manual rebuild, two CI jobs, an operator retrying
a slow build. The measured build takes ~60 s of network I/O, so "two builds overlap" is the common
case, not the rare one; only the final ordering decides whether the target gets a good file or an
empty one, and neither the exit code nor the printed report can tell an operator which happened.
This is V4C-61's shape at the file layer: the verifier and the published object share a name but
not an identity.

**Fix shape.** Create the workspace with a unique name in the target's directory
(`tempfile.mkstemp(dir=target.parent)`), keep the handle, and `os.replace` *that* path — then no
other process can be holding it. An `O_EXCL` lock file beside the target would additionally make a
concurrent build fail loudly instead of silently racing. Both are small.

### BLOCKING-5 — `health.get("sources")` is the wrong predicate; the false budget sentence still serves
`src/app/adapter/main.py:744` (the new `if not health.get("sources")` branch)

The fix closes "the source is absent from the database entirely". It does not close "the source is
present but nothing usable reached the ranking", and in that state `/v1` serves the *original* false
sentence. Reproduced on the real artifact by adding one arena row whose `raw_name` does not resolve
to a registered model:

```
"source_health": { "sources": [ {"source":"arena","rows":1,"stale":true} ], "stale": true,
                   "notice": "Evidence behind Arena text may be out of date past the 90-day window..." },
"eligible_count": 0,
"picks": [],
"unavailable_reason": "No model on this surface's benchmark fits the requested budget,
                       so this answer ranks nothing. It is shown rather than hidden."
```

One row in `scores` is enough to make `health["sources"]` truthy, the new branch does not fire, and
the answer again asserts a budget exclusion that never happened. No budget was applied; nothing was
ranked; there is no usable evidence.

**Reachability is not exotic — it is this dependency's documented failure mode.** The build's floors
do not check *resolvability*: `minimum_rows` (`sources.py:58`) counts rows stored, and the
reconciliation floor (`build.py:291`) is **global** (`models_registered >= 20`), not per-benchmark.
A source whose naming convention drifts delivers rows that `reconcile` drops, the global floor still
passes on the other five sources' models, and the surface serves the false sentence. That is exactly
the "the feed answered but its shape has changed" case `minimum_rows` was written for, and
`arena.py:38-46` records that this dependency has already done it once (FP-M2-2: the `category`
value changed and the filter returned 0 rows).

The honest predicate is not "did any row land in `scores` under this benchmark" but "did any
evidence survive into the ranking" — rows that JOIN to `models`, and (from W2) to `px_median`.

**Why BLOCKING rather than deferred to W2.** D-121 as amended now states this was *"Closed in W1
rather than deferred"* (`docs/decisions.md`, D-121 amendment). It is not closed; it is narrowed. The
amendment is otherwise exactly right and I want to say so plainly — recording that the ADR was
signed on an incomplete reading of the surface it cites is the correct response to the finding, and
better than a code-only fix. But an ADR that claims closure it does not have is the same defect one
level up. Either complete the predicate or amend the claim to name the surviving case.

---

## MINOR

### MINOR-6 — the rollback's join key is not the key the rows were written under
`src/app/workflows/build.py:252` — `reset_source(conn, table, source.name)`

The rollback deletes `WHERE source = <RemoteSource.name>` (the registry entry). The rows were
written under `<client.name>` — every `ingest_*` keys its write off the `RawSource` it was handed
(`ingest.py:89`, `ingest.py:99`, `ingest.py:157`, `ingest.py:172`, `ingest.py:241`). Two
independently-typed strings that happen to agree today:

```
litellm/openrouter/swebench/aider/arena — registry name == client.name — match=True (all five)
```

Nothing enforces it. `test_sources.py` checks class existence (`:58-65`), the category join key
(`:92-107`) and uniqueness (`:110-112`), but **never** `RemoteSource.name == source.client().name`.
When they diverge the `DELETE` matches zero rows and raises nothing — MINOR-1 returns silently.
Demonstrated with a registry entry named `arena` whose ingest writes under `arena-text`:

```
missing: arena: stored 3 rows, below its floor of 10000 ...
rows surviving the rollback: [('arena-text', 1)]
```

This re-creates, inside the fix, the "two enumerations of one set" defect `sources.py`'s docstring
exists to end — and `test_sources.py:96-97` already documents this exact class for the *other* join
key. Fix: one assertion in `test_sources.py`, or key the reset off the client the ingest was handed.

### MINOR-7 — the CI fix does not work: `set -o pipefail` under `bash -e` aborts before the check
`.github/workflows/contract-tests.yml:88-98`

GitHub Actions runs a `run:` block with no `shell:` key as `bash -e {0}`. With `set -o pipefail`
added inside, the pipeline `python -m app.workflows.build ... | tee` exits 3, `-e` fires, and the
script aborts **before** `code=${PIPESTATUS[0]}` is ever assigned. Simulated exactly:

```
=== as GitHub Actions runs it: bash -e {0} ===
{"required_operator_actions": ["x"]}
STEP EXIT = 3                       # ::notice:: never printed, actions never echoed

=== for contrast, without -e ===
REACHED-THE-CHECK code=3
::notice::degraded (expected)
STEP EXIT = 0
```

So the step still fails on exit 3 — the normal case on a runner with no Epoch bundle — which is
precisely the defect MINOR-2 raised, now with a comment above it asserting it is solved. The added
`set -o pipefail` is what breaks it: without pipefail the pipeline would report `tee`'s 0, `-e`
would not fire, and `PIPESTATUS[0]` would still hold 3.

No test could see this. The new `test_ci_argument_drift.py:80-129` resolves module names and checks
flag vocabularies against the YAML text; it never executes the block. V3C-02: this fix has no citing
test able to fail.

Fix: `set +e` around the pipeline (or drop `pipefail` and rely on `PIPESTATUS`), and add
`shell: bash` explicitly so the flags are not implicit.

### MINOR-8 — `workspace.replace(target)` is outside the `try`, and leaves a complete database behind
`src/app/workflows/build.py:411`

The one line the fix added is the one line not covered by the new cleanup. When the rename fails,
the exception is uncaught → traceback, exit 1 (an undeclared code — the same D-120 class the delta
just fixed for the directory target one screen above), and a **fully-built** database survives at
the workspace path. Reproduced with the rename failing the way an EPERM does:

```
UNCAUGHT PermissionError [Errno 13] ... '/tmp/sec_ws2/art.db.building' -> '/tmp/sec_ws2/art.db'
art.db            970752   <- previous artifact, intact
art.db.building   929792   <- complete, valid, orphaned
```

The target is never corrupted, which is why this is MINOR and not a repeat of BLOCKING-1. Reachable
triggers: a sticky directory (`/tmp`) where the target is owned by another user, an immutable flag,
`EBUSY` on some network filesystems, or a directory that lost write permission during the ~60 s
build. Move the `replace` inside the try.

### MINOR-9 — `ValueError` in the exit-2 tuple contradicts the comment beside it
`src/app/workflows/build.py:399`

The new comment says *"Anything else is a bug in this builder rather than a bad input... rather than
dressing an unknown failure as a clean exit 2"* — and `ValueError` is in the tuple that gets exit 2.
`ValueError` is raised by builder bugs as readily as by bad input (`schema.py:414`'s
`reset_source` guard is a `ValueError`, and it fires only on a programming error). It is the one
member of that tuple that is not an input-class error. Either drop it or name why it is there.

### MINOR-4 (carried, re-affirmed) — no response-size bound. I now agree it is hygiene.
`litellm.py:43`, `openrouter.py:34`, `swebench.py:38`, `aider.py:41`, `arena.py:95`

Asked directly, so answered directly: **I do not disagree.** With BLOCKING-2's chain closed, an OOM
mid-build now unlinks the workspace and re-raises, leaving the previous artifact byte-identical — I
verified exactly that above with an injected `MemoryError`. The consequence has dropped from
"publishes a Trap 1 artifact" to "the build dies and nothing changes", which is the correct fail
direction. It stays worth doing (`timeout=30.0` is per-operation, not total, so a slow-drip response
still holds a build open indefinitely), but as hardening, not as a gate. Queue to M8.

### MINOR-5 (carried) — `scripts/` outside the linter, escalated as W-026 ✅
Correct call. Widening `make lint` mid-wave would turn the build red on 24 findings the owner has
not seen, and a gate-definition change is not a security fix's business. Escalation accepted.

---

## NOTE

- **`workspace.replace()` across filesystems — safe by construction.** The workspace is always
  `target.with_name(...)`, i.e. a sibling, so `os.replace` is same-device and atomic. Verified there
  is no WAL to orphan: `PRAGMA journal_mode` on a `connect()`ed database returns `delete`, so no
  `-wal`/`-shm` sidecar exists to be left behind by the rename.
- **`replace()` over a target open elsewhere.** Safe on POSIX — the rename succeeds and an existing
  reader keeps the old inode. Two consequences worth stating, neither a defect here: a serving
  process holding the old handle keeps serving the *previous* evidence until it reconnects (D-116
  keeps ingestion off the serving host, so this is an ops note); and on Windows `os.replace` over an
  open file raises, which does not apply to this project's Linux CI and Fly deploy.
- **SIGKILL leaves a `.building` file.** Confirmed: `SIGKILL` mid-build leaves a 77 KB
  `art.db.building`. Unhandleable in any language, and it self-heals — the next run's
  `workspace.unlink(missing_ok=True)` (`build.py:388`) clears it, and nothing in the serving path
  reads that name. Recorded only because the delta summary claims "no workspace file survives either
  outcome", which is true for every *handled* outcome and not for this one.
- **A new false-cause of the BLOCKING-3 class, thin reachability.** If `_source_health_json` raises
  `sqlite3.DatabaseError`, `main.py:722-728` builds a fallback health dict with `"sources": []` and
  the notice *"could not be read"*. If `recommend()` then returns `None` cleanly, the new branch
  fires and asserts *"no Arena text source is present in the served database"* — contradicting the
  notice beside it. I could not construct a live case (it needs the health query to fail while the
  ranking query succeeds on the same connection) and am reporting it as unreached, not confirmed.
- **SQL construction (carried from the first pass).** Unchanged by this delta and still sound.
  `_IDENTIFIER.fullmatch` (`build.py:63,124`) admits only `[A-Za-z_][A-Za-z0-9_]*`, which cannot
  escape the quoting at `build.py:127`; citing test at `test_build.py:281-286`. Reachability is now
  *narrower* than before: with the workspace fix the connection `_read_back` runs on is always a
  file this process just created. I attempted no successful injection and report it as
  not-exploitable, not as untested.
- **Bundle symlink escape (carried).** Unchanged and still holding on the path `build.py` uses.
- **Fault-injection survivor.** The self-reported survivor — a predicate living inside its own test —
  is the right diagnosis and the extraction to `unresolvable_modules()` with a second driving test
  (`test_ci_argument_drift.py:118-129`) is the right fix. Noting that the *same* class is present
  one file over: MINOR-7's fix has no executing test at all, so it is not merely
  unfalsifiable-in-principle, it is wrong in fact.

---

## Gates

- [x] Secret scan green — gitleaks, 73 commits, 3.39 MB, 0 findings
- [x] `make check` exit 0 — ruff clean, mypy clean (31 files), **462 passed / 12 skipped**
- [x] No new third-party import in the delta; no SCA/slopsquat surface added
- [x] No secret can reach the rewritten workflow — `permissions: contents: read`, no `secrets.*`,
      `build-report.json` is written to the runner and not uploaded as an artifact
- [x] Prompt-injection hygiene — no fetched content is interpreted as instruction
- [x] Destructive-defaults (V3C-06/53) — **BLOCKING-1 closed**, verified adversarially
- [ ] **Artifact integrity** — FAILS: BLOCKING-4
- [ ] **Control-class fail direction (V3C-33/45)** — FAILS: BLOCKING-5
- [ ] **V3C-02 citing test per fix** — FAILS: MINOR-7 has no test able to fail

---

## Disposition

**BLOCKING.** Both findings are small fixes to new code, and both are the original defect surviving
through a narrower door — BLOCKING-4 publishes Trap 1's artifact from a *successful* build, and
BLOCKING-5 leaves D-121 asserting a closure it does not have. MINOR-7 should ride along because the
step it fixes is still red on every run.

Nine of the eleven items from the first pass are genuinely closed, several of them better than I
asked for. This wave does not need a third full round — it needs a unique workspace name, a
predicate that asks whether evidence reached the ranking, and `set +e`.
