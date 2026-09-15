---
record_type: review
id: m13-security-rereview
status: ratified
seat: independent
date: 2026-09-15
---
# M13 Stage 4.0 Security Re-review - the fix round, verified by running the same reproductions

> **Same independent seat as `docs/reviews/m13-security-review.md`.** I wrote none of the fix.
> Policy was read from the protected base ref only (V4C-06): `HEAD` is still `cda57b1`, and the
> profile, baseline, closure checklist, `AGENTS.md` and permission matrix are read at `HEAD`, not
> from the delta. Every claim below is measured, and each measurement names its command.

## 0. How this record was produced, and the tree it is pinned to

**The tree, built rather than accepted.** `git archive cda57b1` into a private scratch directory,
then `git apply` of the W4 round-2 diff (`m13-w4-r2.diff`). That gives the W4-r2 tree. Then I copied the seven files
the coordinator named from the working tree. **I then proved the working tree equals W4-r2 plus the
delta, rather than assuming it:**
1. I normalised the delta's `a/` paths and ran `git apply` on a second copy of the W4-r2 tree. It
   applied cleanly.
2. I compared the result with `cmp` against the working tree. Six of the seven files are
   byte-identical, and so is `tests/unit/test_health_memo.py`.
3. The one difference is `docs/warnings.ledger.md`. The working tree carries one more row than the
   delta: **W-091**, the ESCALATED row for MINOR-3, which the coordinator announced ("an
   ESCALATED ledger row at closure"). I read all of it (section 2).
4. I compared every other tracked file in the working tree with the fixed tree, and every one is
   byte-identical.

**The gate at this tree.** `make check` on the working tree gives `EXIT=0`: **874 passed, 12 skipped**
(the same 12 environment skips as before: `RUN_CONTRACT_TESTS` and `EPOCH_DATA_DIR`),
`check_records PASS`, `wave-check-all PASS: 28`, `conformance-gate PASS`, `swift-test PASS: 215`.

**Method.** I re-ran every reproduction from the first record against the fixed tree, with the same
script repointed at the fixed tree. Every mutant ran in a further private copy (`fixmut`), and every
Swift mutant in a private copy of `ios/` (`swiftfix`). I modified nothing in the repository except
this file.

---

## 1. Dispositions, verified

| Finding | Claimed | How I verified it | Result |
|---|---|---|---|
| **MAJOR-1** `/health` memo | FIXED: key is `_artifact_key` = path, `st_dev`, `st_ino`, `st_mtime_ns`, `st_ctime_ns`, `st_size`, `st_mode`, `st_uid`, `st_gid` (`src/app/adapter/main.py:338`, used at `:358`) | My two-row reproduction, re-run unchanged: after `chmod 000` (mtime and size verified unchanged) `/health` reads **`unavailable`** (was `servable`) beside a 503. After overwriting the SQLite header at the same size, with `os.utime` restoring the mtime, `/health` reads **`unavailable`** (was `servable`). The memo still does its job: it held **1** entry across the timing run, and `test_the_memo_still_spares_a_poll_against_an_unchanged_artifact` pins that 3 polls run the probe once. **Mutants:** K1, the key restored to `(path, mtime, size)`, turns **2 tests red**. K2, every field except `st_ctime_ns`, turns **1 test red** (the utime case), so `ctime` is load-bearing and not decoration. The chmod test is not skipped here; it skips only as root (`test_health_memo.py:42`). | **CLOSED** |
| **MAJOR-2** REQ-RTR-004 test | FIXED: data flow (`test_router_hints.py:125-172`) | My mutant `task: asked.isEmpty ? task : asked` now turns **1 test red**. Unmutated: **5 passed**. The test now kills the reported shape. **Four further shapes still pass it: new MINOR-4.** The shipped code still holds the invariant (`ContentView.swift:497`, `:539`). | **CLOSED for the reported shape; residual MINOR-4** |
| **MAJOR-3** waivers invisible to C2b | LEDGERED + CONTROL REVIEW | `docs/warnings.ledger.md:134-136` (W-088, W-089, W-090), each with `V3C-78` in the path column. I counted the rows the checker counts: W-016, W-018, W-020, W-087, W-088, W-089, W-090, **7**. W-090 carries `C2b-reviewed: D-141 @7`, and `check_records` passes on the fixed tree, so the anchor equals the count. D-141 (`docs/decisions.md:1751`) is PROPOSED and names the owner as the one who ratifies. The row dates match the commits (`3440abe` 2026-09-06; `10a521c` and `cda57b1` 2026-09-15). D-141 does not instruct this seat and does not change a base-ref file; it is a proposal through the documented ADR path, **not an injection-class change**. | **CLOSED, with MINOR-5 on how it discharges** |
| **MINOR-1** per-request warning | FIXED: `_warn_once` keyed on (artifact identity, message), bounded at 8 (`main.py:1200-1210`, called at `:1180`, `:1189`) | My corrupt-artifact run, re-run: **101 requests, 1 warning** (was 101). Still type names only, still 200 with every age `null`. The key is derived from the file, so no caller can mint new entries. **Mutant K3** (the early return removed) turns **1 test red**. | **CLOSED** |
| **MINOR-2** `let`-only field regex | FIXED: stored `let`/`var`, expected set includes `alternatives` as `[String]` (`test_router_hints.py:98-123`) | **Mutant M1** (`var praise: String = "the best model is X"`) turns **1 test red**. | **CLOSED** |
| **MINOR-3** Swift floor | ESCALATED, not changed: W-091 (`docs/warnings.ledger.md:137`) | I agree with the disposition. The floor decides what the gate accepts, and `AGENTS.md` section 3 lists gate-definition changes as escalate-now, not as agent work. W-091 gives the owner a one-line action and the count (215, matching the `make check` above). The window stays open until the owner acts: up to 94 tests can vanish with the gate green. | **ACCEPTED AS ESCALATED** |
| **NIT-1** `firstWithin` trap | FIXED: `seconds.isFinite ? min(max(seconds, 0), 3_600) : 0` (`Router.swift:492`) | `swift test --filter SlowTierTests` on the fixed tree: **6 tests, 0 failures**. **Mutant**, the clamp reverted to `max(seconds, 0)`: the test process dies with `Fatal error: Double value cannot be converted to UInt64 because it is either infinite or NaN`, `signal code 5`. The new test `testADeadlineThatIsNotASensibleNumberDoesNotTrap` (`FrontDoorTests.swift:481`) can fail. | **CLOSED** |
| **NIT-2** stacked model calls | QUEUED to M14 in the closure report's risks | Nothing to verify in code. The queue entry is the closure report's to carry. | **ACCEPTED AS QUEUED** |

**Regression check on what the fix touched.**
- **Cost.** The wider key adds no request-controlled input, and `/v1/categories` stays cheaper than
  `/v1/recommendations`: re-timed at 2.1 ms against 10.5 to 11.6 ms. A Swift build was running
  beside it, so every figure is higher than in the first record, and the ratio is what I rely on.
- **Rare re-probes.** `ctime` also moves on events the old key ignored, such as a hard link or a
  rename of the inode. Each costs one re-probe, not a wrong answer, and no request can cause one.
- **Everything else the first record checked out.** It is unchanged by this delta: the delta
  touches no route, no refresh code, no `runner` and no client request path.

---

## 2. New findings

### MINOR-4 - The new data-flow test still passes four ways of sending typed text to the engine

`tests/unit/test_router_hints.py:142-167` · `ios/ModelRanking/ContentView.swift:508`

The test checks the arguments of `client.X(...)` and the right-hand side of each `task = ...`, and it
allows `id` because `select(_ id:)` assigns `task = id`. Each mutant below was inserted into
`ask()` in the private copy. Every one compiles as Swift, sends the reader's words to the engine,
and leaves the test file **5 passed**:

| Mutant | Why the test cannot see it |
|---|---|
| B1 `select(typed)` | `id` is an allowed right-hand side, and no rule constrains what is passed to `select(` |
| B2 `task += typed` | the assignment regex needs `=` directly after `task` |
| B3 `_ = try? await EngineClient().recommendation(task: typed, budget: budget)` | only calls on the name `client` are read |
| B4 `let outcome = RoutingOutcome(categoryID: typed, tier: .manual, unmeasured: true)` | `outcome.categoryID` is an allowed right-hand side, whatever built the outcome |

**Why MINOR and not a re-opened MAJOR.** The invariant holds in the shipped code. The reported
shape and its two siblings are now killed. Each survivor is a deliberate change rather than a
refactor slip. But B1 and B4 are the natural next shapes for "use the typed text as a surface",
and V3C-74 asks that the invariant's test fail when the invariant is removed.

**Remedy, in the same test:**
- Every `select(` argument in `ContentView.swift` must be `id` inside `ForEach(outcome.alternatives`,
  or `choice.id` inside the surface sheet. Today those are the only two call sites (`:269`, `:295`).
- `RoutingOutcome(` may not be constructed in `ContentView.swift`.
- `task` may change only through plain `=`: ban `task\s*[-+*/]=`, `task\.` mutation and `&task`.
- `EngineClient(` appears exactly once, at `ContentView.swift:64`.

Keep B1 to B4 as the test's own proof that it can fail.

### MINOR-5 - A PROPOSED ADR discharges C2b, and nothing re-arms the trigger if the owner rejects it

`scripts/check_records.py:110`, `:802` · `docs/warnings.ledger.md:136` · `docs/decisions.md:1751`

The coordinator asked me directly whether a proposed ADR should discharge C2b. **My answer: it
should discharge the REVIEW, not the TRIGGER, and today the checker cannot tell the two apart.**
`C2B_REVIEWED` matches `C2b-reviewed: D-nnn @N`, and the discharge tests only the anchor against the
count (`:802`). It never opens the cited ADR, so it reads neither its existence nor its status.

For this closure that is acceptable. The control review V4C-13 asks for was done, its
recommendation is written, and D-141 names the owner as the one who ratifies it at sign-off.

The general shape is not acceptable. Any row can silence the 3x trigger by pointing at a proposal nobody reads.
If the owner rejects D-141, W-090 stays discharged at `@7`, because nothing re-arms on a rejected
decision. That is the "a trigger discharged by a coincidence is not a trigger" class the checker's own comment
(`:798-801`) was written against, reached by a different road.

**Remedy.**
- **At M13 sign-off:** the owner either ratifies D-141, or W-090's marker is removed so C2b fires at the
  next acceptance.
- **Queued to M14:** the C2b discharge requires the cited ADR to exist with status `accepted` or `ratified`.
  A `proposed` citation reports as `pending owner`, visibly, not as discharged.

---

## 3. Acceptance criteria evidence for what this round changed

- REQ-FIX-002 / MAJOR-1: `main.py:338`, `:358` · `test_health_memo.py:45`, `:61`, `:82`
- REQ-UNC-002 / MINOR-1: `main.py:1180`, `:1189`, `:1203` · `test_health_memo.py:101`
- REQ-RTR-004 / MAJOR-2: `ContentView.swift:497`, `:539` · `test_router_hints.py:125` (residual MINOR-4)
- D-126 boundary / MINOR-2: `Router.swift:43` · `test_router_hints.py:98-123`
- NIT-1: `Router.swift:492` · `FrontDoorTests.swift:481`

## 4. Risks queued

- MINOR-4's four assertions, with B1 to B4 kept as mutants (M14, or the closure fix round if it is cheap).
- MINOR-5: owner ratifies or rejects D-141 at sign-off; C2b reads ADR status (M14).
- W-091: the owner sets the Swift floor to 215 at sign-off.
- NIT-2: stacked on-device model calls (M14, already queued).

---

**VERDICT: PASS WITH FINDINGS - no BLOCKING and no MAJOR left open.**
- MAJOR-1, MINOR-1, MINOR-2 and NIT-1 are closed, each verified by re-running the original
  reproduction or mutant against the fixed tree and by a mutant of the fix itself.
- MAJOR-2 is closed for the reported shape, with residual MINOR-4: four untested shapes still pass.
- MAJOR-3 is closed through ledger rows and a control review, with MINOR-5: a proposed ADR
  discharges C2b.
- MINOR-3 is accepted as ESCALATED to the owner, and NIT-2 as queued.
- `make check` is green at the fixed tree.
