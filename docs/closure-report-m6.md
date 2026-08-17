---
record_type: ratification
id: closure-report-m6
status: draft
date: 2026-08-17
---
# Closure Report — M6: The HTTP API

> Owner's A0.5 milestone-session review pack, generated 2026-08-17 from committed artifacts.
>
> **Status: PENDING the owner's signature on §0.** Everything agent-side is closed: four waves,
> three HIGH-tier review seats, plus a Stage-4.0 closure security review that ran twice. **Fifteen
> BLOCKING findings in total, every one fixed, each with a citing test shown able to fail and a RED
> mutant.**
>
> **On Stage 4.0 and what it actually gates.** AGENTS.md §6 binds it precisely: *"BLOCKING; must
> PASS before 4.3 deploy"*, and 4.3 itself is conditioned *"if the milestone deploys"*. **M6 does
> not deploy** — D-116 ships `Dockerfile` and `fly.toml` as proposals and puts nothing on a host.
> The security gate therefore binds **go-live, not this closure**, and it is carried forward as a
> deploy precondition in §0 rather than held over the milestone. This is a correction: the agent
> had been treating the seat's verdict as a closure blocker, which is stricter than the rule and
> stalled the milestone at a gate whose own text points at a step M6 never takes.
>
> What that carry costs is stated plainly: the second security round's findings were fixed but its
> **re-verification was not re-run**, so no seat has signed the post-fix tree. Three independent
> records already block the first deploy on it — this §0, D-116, and W-023 — and none of them can
> be satisfied by an agent.
>
> **Read §0 first.** It is what needs you.

## 0. What needs the owner

| # | Item | What it is |
|---|---|---|
| 1 | **Sign this closure report** | The milestone's out-of-sandbox verification is yours: `make check` and the Epoch-mounted suite on your machine. Expected **365 passed / 12 skipped** and **372 passed / 5 skipped**. |
| 2 | **W-021 — `CODEOWNERS` assigns nobody** | Every rule owns its path to `<DEVOPS_HANDLE>`, which is not a handle, so the review request goes to no one. Documented and untrue since bootstrap; it matters now because W4 created the first files those rules point at. Delete the rules for a solo repo, or set a real handle AND enable "Require review from Code Owners" — without the second half the file is advisory whatever it says. |
| 3 | **W-017 — the deploy condition, STILL OPEN** | The serving snapshot copies the whole database into memory per unauthenticated GET. Its three Stage-4.0 conditions are closed — the amplification was re-derived independently, the ceiling now subtracts the serving process's own baseline (`PROCESS_BASELINE_MB`), and `fly.toml` ties concurrency to the budget — but **the snapshot itself is unchanged**. D-116 names it a CONDITION of go-live, not a follow-up. **No first deploy before this is answered.** |
| 3b | **W-023 — the shipped database is pre-M5, and it fails silently** | `advisor.db` and `owner_advisor.db` carry the pre-M5 schema (no `effort` column), and the serving path is read-only by design so it cannot migrate them. Deployed as-is the process starts, `/health` returns 200 with a correct build stamp, and **every query returns 200 with zero picks** — while Stage 4.3 verifies deploys via `/health`. Before any deploy: `cd /Users/umutcanapaydin/Desktop/ILGAR/model_ranking && .venv/bin/python -m app.workflows.schema migrate --db advisor.db` (expect **exit 3** + `required_operator_actions` if rosters need re-ingesting — D-120 — then re-ingest and re-run for exit 0). |
| 3c | **Stage 4.0 re-verification — carried, not waived** | The second security round's two BLOCKING and one MINOR are fixed (§4), but no seat has reviewed the post-fix tree. Per AGENTS.md §6 this gates **deploy**, not this closure, and M6 deploys nothing. Re-run `/security-review` before go-live, alongside items 3 and 3b. |
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

**Stage 4.0 ran twice and produced five BLOCKING, all closed; its re-verification is carried to the
deploy gate (§0 item 3c).** Round one found three: a publication allowlist that was a denylist in
disguise, a memory ceiling derived from a budget the serving process itself was spending, and a
guard that matched a CI step as prose so commenting the step out left the guard green. Round two
found that **two of those three fixes were partial** — the allowlist covered 10 of 29 fields
because `picks` was one allowed key carrying 19 more, and the database check `stat`-ed the file
without ever opening it. Both are now whole, and the second produced **W-023**, a live finding
about the shipped artifact (§0 item 3b).

The round-two lesson is the milestone's own lesson turned on the fixes: **a fix written to close a
finding is new code and inherits the finding's risk class (V4C-50)** — here, twice, the fix
implemented the first half of a remedy whose own text described both halves.

Within the milestone, the W1 and W3 pulled-forward passes produced three
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

`make check` exit 0 · **365 passed / 12 skipped, 372 / 5 with the Epoch bundle** · `make smoke-deps`
PASS (first real pass; L.8 was a loud failure until W4) · `gitleaks` clean · `make conformance` 6 of
7, the one RED leg being GPF-001 handed back to GP · every criterion traced with a citing test shown
able to fail · D-113..D-120 ratified · retrospective answers Ruling A's carried question and poses
the next · dated EXPERIENCE entry · **`docs/handovers/handover_q2.txt` generated (M % 3 == 0)** ·
**fifteen BLOCKING closed across five review rounds, none of them found by the author** ·
Stage-4.0 re-verification, W-017 and W-023 carried to the **deploy** gate per AGENTS.md §6, which
binds go-live rather than closure — M6 deploys nothing.

**Not claimed green, said plainly:** the coverage and roster-staleness CI legs have still never run
(`contract-tests.yml` is a Monday cron); the contract test against the live scores API stays skipped
without `RUN_CONTRACT_TESTS=1`; and no seat has reviewed the tree as it now stands.
