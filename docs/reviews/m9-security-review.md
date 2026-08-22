---
record_type: review
id: m9-security-review
status: ratified
date: 2026-08-22
---
# Stage 4.0 Security Review — M9 (the refresh)

> **VERDICT AS RETURNED: BLOCKING — 3 blocking, 6 medium, 6 minor.** Run by an independent seat that
> authored none of the code, against `1fd9df4..04902b7`, risk tier HIGH.
>
> **All three blocking findings are fixed, and the seat's own summary of why they mattered is kept
> verbatim in the sections below rather than paraphrased.** Two of them were in code written during
> the same milestone that fixed two instances of the identical defect class.

## What it found, and what changed

### B1 — the lock did not hold

The `O_EXCL` + pid + staleness scheme failed three ways at once, demonstrated rather than argued:
the age rule was joined with `or`, so a lock past two hours was reclaimed **from a holder the pid
check had just proved alive**; the age was measured from acquisition and never refreshed, so any
cycle outliving it lost its own lock; and release was by PATH with no ownership check, so an
evicted cycle deleted the NEW holder's lock on the way out, cascading.

The comment beside it said the age rule was *"the fallback for the case the pid cannot answer"*.
The code applied it unconditionally. **That is the claim-disagrees-with-code defect this module had
already fixed twice in the same milestone**, written a third time by the same agent.

Reachable exactly where D-130's reasoning lives: a laptop asleep mid-cycle, or a slow upstream —
`_TIMEOUT_S` is per-read, not per-request, so a trickling response holds a socket indefinitely. The
next trigger evicts the live holder and both cycles run. **W-047, restored.**

**Fixed by removing the class rather than patching it.** `fcntl.flock` on a descriptor held for the
whole cycle: the kernel releases it when the process dies, for any reason including SIGKILL, so
there is no staleness rule to get wrong, no pid to parse, and no reclaim path to race. The seat's
own remedy, adopted as given. Three tests: a second cycle gets BUSY, a leftover lock file from a
dead process does not block, and a lock held by a real **subprocess** is respected — then released
when that subprocess is killed.

### B2 — the refusal rule turned itself off when the live artifact could not be read

`fingerprint_of` returned `None` for three different facts — no artifact, not a database, any error
while reading — and the cycle treated all three as "first artifact". So one unreadable read of the
LIVE file skipped the degradation guard **and** the pre-publish baseline check, and the candidate
published unconditionally, including one that blinded every surface. The record then said `first
artifact`, which was untrue.

The seat named the consequence precisely: a poisoning attack gains a cheap enabler — corrupt the
served file, then let the timer publish whatever the upstream is offering.

**This had already been raised**, as MAJOR-2 of the W2 code review, and was not fixed. It returned
as BLOCKING. Fixed by splitting the sentinel: a missing artifact still publishes; an unreadable one
raises `UnreadableArtifact` and the cycle exits FAILED. **If you cannot fingerprint what you would
replace, you cannot claim the replacement is not worse.**

### B3 — the arena change had no authorization the repository could show

The sharpest finding, and it is not about code. Reading only the protected base ref, the seat found
the signed plan §6 excluding the arena fix, the W-024 row saying NOT APPLIED for escalate-now
reasons, and **the only authorization anywhere being prose the implementing agent wrote inside the
range under review** — which V4C-06 excludes as evidence, for exactly this reason.

The seat was explicit that the code is sound: W-007's invariant is genuinely preserved, the
rewritten tests still assert it, and the floor moving 1 → 250 is a real strengthening. The BLOCKING
was on authorization alone.

**Fixed by D-131**, which records the owner's ruling of 2026-08-21 in his own words, translated and
marked, and supersedes plan §6 in place. The sequencing error is recorded rather than smoothed
over: the correct order is ruling → ADR → code, and what happened was ruling in chat → code → ADR
at review.

## Medium findings, and their disposition

| # | Finding | Disposition |
|---|---|---|
| M1 | A BUSY trigger wrote a full record **from a cycle holding no lock**, clobbering a refusal, resetting the escalation counter, and writing an outcome the map did not name — so `runner`'s busy branch was dead code and execution fell through to an implicit exit 0 = PASS | **FIXED.** A cycle that did nothing records nothing; `EXIT_BUSY` is in the map; the counter now resets only on published/unchanged, so refuse→fail→refuse still escalates |
| M2 | `os.kill(pid, 0)` raises `OverflowError` on an oversized pid, escaping every guard and wedging the refresh permanently | **GONE with B1.** `flock` parses no pid |
| M3 | A crash exits **1**, which the scheduler's own table calls "unchanged, not a failure" — reachable today from a hostile payload via an unguarded `entry.get` | **FIXED.** `main()` converts an escaped exception to `EXIT_FAILED`, and `_overall_prefix` guards the row type. mypy called that guard unreachable because the annotation claimed `list[dict]` about parsed JSON — **a type hint talking a guard out of existing** — so the boundary is typed `list[Any]` now |
| M4 | Nothing bounds what an upstream can publish **upward**: the automated defences are all shrinkage detectors, and a source that adds fabricated high-rated models or drops prices ships to users twice a day with every guard reporting healthy | **CARRIED — W-049.** The single most important thing M10 inherits |
| M5 | Aggregate allocation across pages is unbounded: 50 pages × 32 MB is ~1.6 GB of raw JSON, unattended, every 12 hours | **CARRIED — W-050** |
| M6 | Artifact age was printed and never thresholded, so a refresh that cycles happily and never publishes reports PASS forever | **FIXED.** `runner` escalates past 72 hours |

Minor findings N1–N6 are carried in **W-051** except N3 (refresh by-products not gitignored), fixed
here, and N6 (a stray indent in a test), fixed here.

## The seat's PASS observations, kept because they are evidence too

`make secrets` clean (33.86 MB, run by the seat itself). `make deps` clean; `pyproject.toml`
untouched, so the slopsquat surface is unchanged. **The frozen `/v1` did not move** — the whole
range touches exactly three files under `src/`, and `adapter/main.py` is not one of them. D-116 held
structurally. Publish is a rename, not a copy. The bundle readers already refuse traversal, which
matters more now that `--epoch-dir` is baked into an unattended job. And the nested-row shape is
read the same way by client and parser, so a de-nesting change fails closed end to end: parser drops
every row → `minimum_rows` trips → arena fails → `assistant` blinds → D-128 refuses.

**SAST gap, stated rather than skipped:** `bandit` is not installed, so the profile's §7 leg was a
targeted grep over the diff — no `eval`/`exec`/`subprocess`/`pickle`/`yaml.load`/`shell=True`/
`verify=False` in the changed source. Installing it is a one-line dev dependency and belongs to M10.

## Process finding, recorded because it is about how this milestone ran

The seat's tree check came back **NOT CLEAN**, and correctly identified why: Stage 4.2/4.4 capture
was being written in parallel, **before its Stage 4.0 verdict existed** — and `docs/closure-report-m9.md`
already cited this file, which did not yet exist. A forward reference rather than a false claim, and
the seat said so. It is still the wrong order: a closure report should not be able to cite a verdict
nobody has given. The commit was deliberately held until this record existed.

Filled by: an independent security seat · Date: 2026-08-22 · Tree at review: `04902b7`
