---
record_type: ratification
id: closure-report-m6
status: draft
date: 2026-08-17
---
# Closure Report — M6: The HTTP API

> Owner's A0.5 milestone-session review pack, generated 2026-08-17 from committed artifacts.
>
> **Status: PENDING the owner's ruling on §0.** Everything agent-side is closed: four waves, three
> HIGH-tier review seats, ten BLOCKING findings all fixed and re-verified. The Stage-4.0 closure
> security review is the one gate still running at the time of writing and its verdict is required
> before this report can read PASS.
>
> **Read §0 first.** It is what needs you.

## 0. What needs the owner

| # | Item | What it is |
|---|---|---|
| 1 | **Sign this closure report** | The milestone's out-of-sandbox verification is yours: `make check` and the Epoch-mounted suite on your machine. Expected **354 passed / 12 skipped** and **361 passed / 5 skipped**. |
| 2 | **W-021 — `CODEOWNERS` assigns nobody** | Every rule owns its path to `<DEVOPS_HANDLE>`, which is not a handle, so the review request goes to no one. Documented and untrue since bootstrap; it matters now because W4 created the first files those rules point at. Delete the rules for a solo repo, or set a real handle AND enable "Require review from Code Owners" — without the second half the file is advisory whatever it says. |
| 3 | **W-017 — the deploy condition** | The serving snapshot copies the whole database into memory per unauthenticated GET. D-116 names it a CONDITION of go-live, not a follow-up. The Stage-4.0 pass is required to re-derive the amplification independently rather than cite W1 or W3. **No first deploy before that measurement.** |
| 4 | **Deploy proposals** | `Dockerfile` and `fly.toml` ship as proposals under the plan's Trap 3, not as adopted files. They are a K.10 cross-team surface and nothing treats them as settled until you say so. |
| 5 | **The carried question** | M6's retrospective poses it: should M7 spend a wave making "does this control actually execute" mechanically checkable, or is a control about controls the same bet at one remove? Ten of ten BLOCKING findings this milestone were reachability failures. |

**Already ruled on this milestone, recorded so the gate is not re-litigated:** Ruling A (both coding
answers, neither leading) · GP v5.0 as the process baseline · D-114 then D-117 on git authority ·
D-118 the English contract · W-001's gitleaks waiver · the REQ-API-005 criterion amendment ·
D-119 written at closure rather than mid-wave.

---

## 1. What shipped (from the signed plan)

Nine acceptance criteria, all traced in `docs/coverage-by-req.md` with derived `file:line` evidence.

| REQ-ID | Verdict |
|---|---|
| REQ-API-001 versioned read-only surface, no mutating route | COVERED |
| REQ-API-002 **Ruling A** — both coding answers, nothing ranks them | COVERED |
| REQ-API-003 one serializer, three renderings | COVERED (narrowness in trace §2.1) |
| REQ-API-004 undated evidence disclosed in the payload | COVERED |
| REQ-API-005 error contract | COVERED — **criterion amended at this gate** (trace §2.2) |
| REQ-API-006 CORS allowlist + startup validation + read-only handle | COVERED (trace §2.3) |
| REQ-REC-014 `equivalent_plans` group structure (W-002) | COVERED |
| REQ-LIC-002 CSV attribution (M5 deferral) | COVERED |
| REQ-SUB-008 roster's own staleness window (W-008) | COVERED |

**The number this milestone existed to move** is not a coverage figure: it is that the engine became
consumable. Nothing outside this repository could read an answer before M6; `/v1` serves both coding
surfaces with neither leading, and D-115 makes that a contract rather than an implementation detail.

## 1a. Per-wave table

| Wave | Tier | Delivered | Reviews | Elapsed |
|---|---|---|---|---|
| W1 | MED + security | `/v1` envelope, Ruling A frozen, error contract | 2 BLOCKING, 3 rounds | 52 min |
| W2 | MED | one serializer; D-118 English contract; W-002, W-010, REQ-LIC-002 | 2 BLOCKING, 2 rounds | 74 min |
| W3 | **HIGH** | roster window + migration, YAML guard, single migration entry, CORS/startup | **4+3+2 BLOCKING**, 4 rounds | ~34 min to code-complete, then reviews |
| W4 | LOW-MED | D-116/OQ-3, L.8 smoke gate wired, deploy proposals | closure review | — |

## 1b. Decisions made on the owner's behalf

Three, all recorded where they were made rather than here:

1. **The English migration translated at the SOURCE, not the API boundary** (D-118). Translating in
   the adapter would give one run two texts, which is the plan's Trap 1. The consequence — the CLI
   became English too — was stated in the ADR rather than discovered later.
2. **`plan_config`'s `cap_dusuk`/`cap_orta` columns kept their spelling** behind the new English
   vocabulary. Internal identifiers, and renaming them needs a migration; recorded as a tracked gap.
3. **The Arena smoke probe is not retried.** 4 of 5 attempts pass in 5–10 s and one exceeded the
   client's 30 s read. A gate that retries until green reports a reliability the deploy will not have.

## 2. Git record

17 commits, `1faaf77..HEAD`, **58 files changed, +8342 / −270**. Every commit authored
`Claude <noreply@anthropic.com>` — **zero authored as the owner**, which is the check W-011 exists
because M5 failed. Twelve are wave-boundary commits under D-117; none is catastrophe-class.

## 3. Trust telemetry

Ten BLOCKING findings, none found by the author. Author fault-injection: 47 mutants, 47 killed —
a set measuring its own blind spot at zero by construction. Reviewer mutants that stayed green
against author code: **22 across the milestone** (3 at W1, 3 at W2, 16 at W3). Every one received
its mandatory V3C-72 test.

## 4. Security & invariants

Stage-4.0 verdict pending. Within the milestone, the W1 and W3 pulled-forward passes produced three
BLOCKING between them: a disclosure failing OPEN, an unguarded network-fed YAML input, and an
unwired startup validator. New invariants, each with a negative test and a RED mutant: no mutating
route exists (proven by enumeration, not claimed); the serving path never writes the operator's
database; no filesystem path reaches an error body; curated YAML is bounded by EXPANDED size;
a wildcard CORS origin is refused in every environment; production fails closed at startup.

`gitleaks` clean at HEAD for the first time in the project's history (W-001).

## 5. Ledgers

**Paid this milestone:** W-002, W-005, W-008, W-009, W-010 — all five deferred to "the API
milestone" with reasons, all five closed. **W-001 closed** after four surviving closes.
**W-012/W-013/W-014/W-016/W-018/W-020 closed.** **Open and carried:** W-017 (escalated; a go-live
condition), W-019 (`L1` detects an alphabet, not a language), W-021 (`CODEOWNERS`).
**Handed back to GP:** GPF-001..005 in `docs/gp-field-findings.md`, three of which are the same
records-versus-instructions blind spot in three different checks.

## 6. Architecture delta — PROSE

Before M6 this repository was a pipeline with a CLI. The engine ingested public benchmark and
pricing data, reconciled names into a canonical registry, and printed a deterministic answer to
whoever ran `python -m app.workflows.recommend`. Nothing outside the repository could obtain an
answer, and the only consumer was a person at a terminal.

M6 adds a second consumer that cannot be reasoned with. **The architectural change is not "an HTTP
route was added" — it is that the product acquired a contract**, and a contract is the set of
promises that survive after everyone who remembers why has moved on. Three structural consequences
follow, and each of them changed code that predates the API.

**The answer became a shape, and the shape became enforceable.** The owner's Ruling A says the
product presents both coding surfaces with neither leading. As long as the only consumer was a
person, that was a presentation choice. As a contract it needs a representation — `answers` as an
array whose order is documented as meaningless, every answer structurally symmetric, no field
anywhere that could be read as precedence — and it needs a gate, because the milestone proved three
times that intent does not survive an edit. The gate that holds is a frozen key set, which is the
project's third attempt and the first one that states what is allowed rather than what is forbidden.

**Serialization moved from three places to one.** The CLI printed `asdict`, the adapter built a
dictionary by hand, and the CSV export wrote a different object; M5's security review had already
caught two of those disagreeing about the same run. `serialize.recommendation_json` is now the only
function that turns a recommendation into data, it imports no engine module, and it enumerates
nothing — a field added to `Pick` reaches every rendering because no rendering lists fields. The
guarantee is temporal rather than structural: a hand-written mirror can still exist, but it cannot
stay correct.

**The trust boundary moved, and several controls that were theoretical became load-bearing.** The
engine's inputs were repo-committed files and documented endpoints fetched by an operator. A network
surface in the same process changes what "untrusted" means: the YAML expansion guard W-005 deferred
for two milestones is now installed on all four inputs including the one fetched over HTTP; the
database is opened read-only and copied per request because the engine writes while it reads;
configuration that was a developer convenience now fails the process closed in production. **The
serving path deliberately contains no ingestion** — D-116 puts the pipeline on the owner's machine
and ships the database as an artifact, so the code that talks to third parties never runs where the
public can reach it.

What did not change is worth stating too. The recommendation engine is untouched: the same
deterministic, rule-based path that produced M5's answers produces M6's, and the API adds no number
of its own. Every disclosure the API serves was already computed by the engine — the API's only
original contributions are which surface an answer belongs to, how fresh its source is on a wall
clock, and why it has no picks. **The product got a mouth, not a new opinion.**

## 7. Definition of done

`make check` exit 0 · 354 passed / 12 skipped, 361 / 5 with the Epoch bundle · `make smoke-deps`
PASS (first real pass; L.8 was a loud failure until W4) · `gitleaks` clean · `make conformance` 6 of
7, the one RED leg being GPF-001 handed back to GP · every criterion traced with a citing test shown
able to fail · D-113..D-120 ratified · retrospective answers Ruling A's carried question and poses
the next · dated EXPERIENCE entry · **`docs/handovers/handover_q2.txt` generated (M % 3 == 0)** ·
Stage-4.0 security verdict **pending**.
