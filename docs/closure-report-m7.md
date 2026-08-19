---
record_type: ratification
id: closure-report-m7
status: ratified
date: 2026-08-18
---
# Closure Report — M7: The engine feeds itself, and stops writing while it reads

> **RATIFIED by the owner on 2026-08-19.** Signed during M8, together with the three §0
> items that were waiting on him. The frontmatter carries `status: ratified` and nothing
> else: a `ratified_by` field was added here and removed the same minute, because no check
> consumes it and V4C-35 says a field may exist only if one does.

> Owner's A0.5 milestone-session review pack, generated 2026-08-18 from committed artifacts.
>
> **Status: PENDING the owner's signature on §0.** Everything agent-side is closed. The Stage-4.0
> security review returned **PASS with zero blocking findings**, so the deploy was never gated on
> it — the deploy is deferred by the owner's own ruling (**D-123**), not by a defect.
>
> **Read §0 first.** It is short this time.

## 0. What needs the owner

| # | Item | What it is |
|---|---|---|
| 1 | **Sign this closure report** | Your out-of-sandbox verification: `make check` on your machine. Expected **511 passed / 12 skipped**. |
| 2 | **The carried question** | The retrospective poses it: `/v1` was frozen by D-115 with no consumer in existence, and M8 writes the first one. Does "frozen" mean frozen before or after the first real reader? Better decided now than in the moment a specific field is inconvenient. |
| 3 | **W-026 / W-027** | Still yours, both gate-definition changes: `make lint` does not cover `scripts/` (18 pre-existing findings), and `contract-tests.yml` has still never run — `gh workflow run contract-tests.yml` is the one-line remedy. |

**Already ruled and recorded, so the gate does not re-litigate:** D-121 (a source may be optional,
but a blind surface may never be silent) · D-122 (review depth by blast radius) · D-123 (go-live
ships with the iOS app).

---

## 1. What shipped

| REQ-ID | Verdict |
|---|---|
| REQ-ING-012 one runnable entry point builds the artifact | COVERED |
| REQ-ING-013 a partial build is a failed build | COVERED |
| REQ-CAN-003 medians unchanged after leaving the read path | COVERED |
| REQ-API-007 no write, no full-database copy in the serving path | COVERED |
| REQ-API-008 an unbuilt artifact is refused, not answered empty | COVERED |
| REQ-API-009 the deployed service answers with correct content | **PARTIAL — W-030** |
| **W-017** amplification removed | **CLOSED** |
| **W-023** the shipped artifact serves real answers | **CLOSED** |

**The number this milestone existed to move** is not a coverage figure. At M6's close, the artifact
this product ships answered **zero picks for every query** and nothing in the repository could
rebuild it. It now answers **3 picks on `coding` and 3 on `agentic-coding`**, produced by code that
`ruff`, `mypy`, `pytest` and coverage can all see.

## 1a. Per-wave table

| Wave | Tier | Delivered | Reviews |
|---|---|---|---|
| W1 | HIGH | build pipeline out of CI YAML into `src/`; source registry; D-121 | **30 BLOCKING**, 3 seats, 3 rounds |
| W2 | HIGH | medians leave the read path; unbuilt artifacts refused at four boundaries | author, 11 mutants |
| W3 | HIGH | `serving_snapshot` deleted; **W-017 closed** | author, 5 mutants |
| W4 | plumbing (D-122) | journey wired and run; container verified fail-closed | Stage 4.0 |

## 2. Git record

`9f4471d..HEAD`, every commit authored `Claude <noreply@anthropic.com>` — **zero authored as the
owner**, which is the check W-011 exists because M5 failed. All under D-117; none catastrophe-class.

## 3. Trust telemetry

Thirty BLOCKING in W1, none found by the author. Rounds two and three found defects the author
introduced **while fixing round one** — including writing the identical default-argument bug into a
second function twenty minutes after fixing it in the first.

The Stage-4.0 pass then re-derived W-017 with a better experiment than any of the three before it:
it separated file **size** from ranked-row **count** by inflating the artifact to 121 MB while
holding the model count at 73. **Zero additional memory.** It also found the ceiling I deleted had
been measuring the wrong quantity all along — it would have refused that harmless 121 MB file while
admitting a 6 MB one that used 58% of the VM.

## 4. Security & invariants

**Stage 4.0: PASS, 0 BLOCKING, 8 MINOR.** Six fixed at closure, two carried as unverified-without-a-
deploy (W-030, W-031). The two worth naming:

- `slopsquat_check.declared()` returned **one dependency of five** and the gate printed PASS. A
  non-greedy bracket match stopped at the first `]` in the file — inside `uvicorn[standard]` —
  hiding four dependencies and every optional group, which is where a typo-squatted test helper
  would land and which CI installs on every run. Parsed with `tomllib` now: 1 became 15.
- Four of five clients had **no response bound**, and the fifth checked `len(resp.content)` — which
  httpx fills only after buffering and decompressing. The seat measured a 4.6 MB gzip body expanding
  to 434 MB in a 1.94 GB process. All five stream through one counted read now.

`gitleaks` clean. No new third-party dependency in the whole milestone.

## 5. Ledgers

**W-017 and W-023 closed** — the two oldest open rows, and **neither closed the way its own row
proposed.** W-023's recorded remedy was a one-line `schema migrate`, which could not have worked: a
migration adds a column, it cannot populate `px_median`. The diagnosis was right for two milestones
while the remedy was insufficient, and nobody re-read the remedy.

Open and carried: W-019, W-024 (arena's upstream 500), W-025, W-026, W-027, W-028, W-029, and the
two new deploy rows W-030 and W-031.

## 6. Architecture delta

The serving path changed shape. It used to be: open read-only → **copy the whole database into
memory** → let the engine write into the copy → discard. It is now: open read-only → read. The
engine's median build moved to a build-time entry point that did not exist when M7 opened, and the
five constants that sized the copy are gone with it.

The product also acquired something it never had: **a way to produce its own data that a human can
run and a tool can check.**

## 7. Definition of done

`make check` exit 0 · **511 passed / 12 skipped** (396 at milestone start) · `ruff`/`mypy` clean ·
`gitleaks` clean · every criterion traced with a citing test shown able to fail (V3C-02), with
REQ-API-009's gap named rather than smoothed · Stage 4.0 **PASS** · D-121/122/123 ratified ·
retrospective answers M6's carried question and poses the next · dated EXPERIENCE entry ·
`note.txt` refreshed. M7 is not `M % 3 == 0`, so no quarterly handover is due.

**Not claimed green, said plainly:** `make smoke-deps` exits 1 on arena's upstream 500 (W-024,
handled by D-121, not resolved) · `make conformance` is 5 of 7, both RED legs pre-existing GP
findings · the coverage and roster-staleness CI legs have **still never run** (W-027) · and
**nothing is deployed**, so REQ-API-009's network half and the entire Fly platform surface are
unverified (W-030, W-031). A local container is a good proxy for a platform and is not the platform.
