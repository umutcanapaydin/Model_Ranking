# M6 Plan — The HTTP API: serve both coding answers, freeze the contract

**Status:** **SIGNED** by the owner on 2026-08-16. Wave dispatch is authorized once the process
baseline below is settled.
**Date:** 2026-08-16 · **Risk tier:** MED (W3 auto-escalates to HIGH — schema migration)
**Mode:** A0.5 + **D-114** (the agent stages, the owner commits — D-106 superseded)
**Process baseline:** **GP v5.0 (D-113)**, adopted in the signing session and installed before W1.
**Quarterly obligation:** M6 is `M % 3 == 0`. Its closure MUST generate
`docs/handovers/handover_q2.txt` (V3C-81; the quarterly handover BLOCKS without a dated EXPERIENCE
entry for this milestone).

**Owner decision locked 2026-08-16 (this session) — the carried question is answered:**

> **Ruling A: the product presents BOTH coding answers.** Neither surface is relegated to evidence.
> A user asking for a coding recommendation receives the `coding` answer and the `agentic-coding`
> answer, each labelled with its own weakness — `coding` is dated but narrower (5/10 plans),
> `agentic-coding` is broader (6/10 plans) but carries no evaluation dates at all.

That ruling is the reason this milestone exists in the shape below. The HTTP API freezes it into a
contract, so §1 states exactly what "both" means in the payload before any of it is built.

---

## 0. Why this milestone exists

M1–M5 built an engine that answers honestly and a CLI that prints the answer. Nothing outside this
repository can consume it. M6 turns the engine into a **read-only, versioned HTTP surface** — the
one an iOS advisor client can call — and in doing so it converts several things that were prose into
contract:

- **Ruling A** has no representation today. `recommend(conn, budget, task)` returns exactly one
  `Recommendation`. Serving two answers is a contract shape, not a loop.
- **Five ledger rows were deferred to "the API milestone" on purpose** — W-002, W-005, W-008, W-009,
  W-010 — because each of them is a question about a boundary that only exists once there is an API.
  This is where they are paid.
- **Two M5 security deferrals** were ledgered against the export contract: the CSV half of
  `export_ranking` carries no attribution, and the `agentic-coding` answer does not say *in the
  payload* that its evidence is undated. Both are disclosure defects, and an API multiplies them.
- **OQ-3 has never been closed with a valid ADR.** The deploy target is recorded as a preference in
  `m4-plan.md` whose citation collides with the ratified D-110, while PRD OQ-3 still reads "not
  chosen yet". A serving milestone cannot leave that open.

### The three traps this milestone must not walk into

**Trap 1 — the contract that says less than the CLI already says.** M5's closure security review
found the single highest-value class of defect in this project by reading two artifacts of *the same
run* against each other: the JSON payload published the effort *policy* while the CSV export of that
run published the effort *evidence*. They disagreed and every gate was green. M6 adds a third
rendering of the same run. Three renderings that drift is not a hypothetical here — it has already
happened once with two. **The countermeasure is structural: one serializer, every rendering derived
from it, and a citing test that asserts field-for-field parity between the JSON payload, the CSV
export, and the CLI's printed disclosures.** A disclosure that exists in one rendering and not
another is BLOCKING, not MINOR.

**Trap 2 — "both answers" quietly becoming "two answers with a winner".** Ruling A says neither
surface leads. Every one of the following would re-introduce a ranking the owner did not make: an
array whose order is stable and therefore read as precedence; a `primary` / `default` / `recommended`
flag; a single top-level `pick` field alongside the array; documentation whose every example shows
`coding` first. Intent does not enforce this. **A citing test must assert that no field in the
envelope ranks one surface above the other, and the surfaces must be emitted in a documented,
deliberately non-semantic order with the envelope stating that the order carries no meaning.**

**Trap 3 — deploy files are a cross-team contract surface (K.10).** There is no `Dockerfile`, no
`fly.toml`, no `CODEOWNERS`, and no deploy directory in this repository today. Creating them is not
"overwriting a DevOps-owned file", but they become that surface the moment they exist. They ship in
W4 as **proposals for the owner's review**, and the ADR that names the target is ratified before any
of them is treated as settled.

---

## 1. What Ruling A means in the contract (signature item)

This section is the part of the plan the owner's signature is really approving. Everything else is
consequence.

1. **`task=coding` returns two answers.** The response carries an `answers` array with two members,
   `surface: "coding"` and `surface: "agentic-coding"`.
2. **Neither leads.** No `primary` flag, no top-level winner, no semantic ordering. The envelope
   carries an explicit statement that the two surfaces are not ranked against each other and that
   their memberships differ.
3. **Each answer carries its own weakness, in the payload.** `coding` carries its effort-mix notice
   (D-112) and its per-plan freshness; `agentic-coding` carries `evidence_dating: "undated"` and the
   sentence that says so. This is the M5 deferral, paid here.
4. **An explicit single-surface request is honoured.** `task=agentic-coding` returns that surface
   alone. Ruling A binds the *coding intent*, not every possible request — a caller that names one
   surface has already chosen.
5. **`task=assistant` is unaffected** — one category, one answer, as today.

If any of the five is not what the owner meant, this is the place to amend it before it becomes a
`/v1` contract that needs a version bump to change.

**Two further signature items:**

- **Does M6 deploy, or only become deployable?** This plan proposes **deploy-readiness + the ADR,
  and no go-live**: Stage 4.3 is walked, the artifacts exist and are reviewed, and the first public
  deployment is M7's opening act. The reason is scope — this milestone already carries a contract
  freeze, five ledger rows and two security deferrals. Amend to "M6 deploys" and W4 grows.
- **Wave cap.** Four waves. If W1's contract work shows that the ledger carries do not fit, **W4
  moves to M7 and this milestone closes at three** — close early, never stretch (A0.5).

---

## 2. Acceptance criteria (REQ-IDs)

New REQ-IDs are assigned only where a **contract or a schema** changes. A defect against an existing
REQ is intake for a red test, not a new requirement — the ledger rows below say which is which.
New REQs land in `docs/prd.md` as well as here (the M3 rule).

| REQ-ID | Criterion | Closes |
|---|---|---|
| **REQ-API-001** | A versioned, **read-only** HTTP surface: `GET /v1/recommendations`, `GET /v1/categories`, and the existing `/health` (L.7 build stamp untouched). M6 ships **no mutating route**, and a citing test asserts that absence — this is how V3C-12 server-side-authz is satisfied, by having no mutating surface rather than by claiming one is protected | §0 |
| **REQ-API-002** | **Ruling A.** `task=coding` returns two answers, neither flagged, ordered non-semantically, with the envelope stating the order carries no meaning. Citing test asserts two members AND asserts that no field ranks them | Ruling A / Trap 2 |
| **REQ-API-003** | **Rendering parity.** Every disclosure the engine produces — `close_call`, `stale_notice`, `effort_mix_notice`, the budget notice (D-111), D-110 equivalence, per-pick `effort` — is present in the JSON payload, the CSV export and the CLI output, derived from ONE serializer. Citing test compares all three renderings of a single run field-for-field; a disclosure in one and not another is BLOCKING | Trap 1 |
| **REQ-API-004** | **Undated evidence is disclosed in the answer, not only in the report** (INV-24). An answer whose evidence carries no evaluation date says so in the payload. Citing test on the `agentic-coding` answer | M5 security deferral |
| **REQ-API-005** | **Error contract.** Unknown task, unknown budget, an unhealthy source, and a missing database each produce a stable, documented error shape that fails loud and closed and **leaks no filesystem path** into the response body. Citing test per case | §0 |
| **REQ-API-006** | **Security baseline for the surface** (V3C-11/12/13/51/56, `docs/security-baseline.md`): CORS is an allowlist and never allow-all-with-credentials; security-relevant config is validated at startup and the process refuses to serve in production if it is wrong; the API's database handle is opened read-only; no plaintext credential exists in source. Citing test per clause | New external surface |
| **REQ-REC-014** | `equivalent_plans` carries **group structure** — a machine consumer can tell which pick each plan is equivalent to, and at what price. Prose already carries it; the field does not | W-002 |
| **REQ-LIC-002** | The **CSV half** of `export_ranking` carries the same attribution and blend note the JSON half carries (CC-BY obligation ships where the data is served — REQ-LIC-001's rule, applied to the rendering it missed) | M5 security deferral |
| **REQ-SUB-008** | The roster-link staleness sentence reads the **roster's own** window, persisted, not the curated plan table's. Citing test proves the two windows can diverge and the correct one is used | W-008 |

---

## 3. Waves

**W1 — The envelope (REQ-API-001, -002, -005) · tier MED, with a pulled-forward security pass**

1. `src/app/adapter/` grows the `/v1` routes over the existing engine. **No engine change** — if a
   route needs the engine to behave differently, that is a finding, not an implementation detail.
2. The Ruling A envelope, built to §1: two answers for the coding intent, no precedence field, the
   non-semantic ordering documented in the response itself.
3. The error contract and its four cases.
4. Fault-injection targets stated up front: add a `primary` flag → REQ-API-002's citing test RED;
   return one answer for `task=coding` → RED; let a path reach an error body → REQ-API-005's RED.
5. A pulled-forward security pass on this wave's slice. This is the project's first surface that
   answers to a network, and the closure review is too late to learn the shape of it.

**W2 — One serializer, three renderings (REQ-API-003, -004, REQ-LIC-002, REQ-REC-014)**

1. Extract the single serializer the JSON payload, the CSV export and the CLI all derive from.
   The parity test is written **before** the extraction, against today's behaviour, so it can be
   shown failing on the current CSV/JSON disagreement.
2. `evidence_dating` into the payload (REQ-API-004); CSV attribution and blend note (REQ-LIC-002).
3. `equivalent_plans` group structure (REQ-REC-014) — the contract shape W-002 was deferred for.
4. **W-010 intake (red test first):** the effort counter under-reports suffix-bearing rows it could
   not classify. This is a defect against REQ-CAN-005, not a new requirement — reproduce it with a
   failing test, then fix it. Citing test: `tests/unit/test_effort.py`.

**W3 — The boundaries the API creates (REQ-SUB-008, REQ-API-006) · tier HIGH (migration)**

1. **REQ-SUB-008** — the roster window becomes persisted config. This is a schema change, therefore
   a migration, therefore this wave auto-escalates to HIGH: Code + Tester + a pulled-forward security
   pass, and V3C-72 fault injection performed in place with md5 identity verified after restore.
2. **W-005 intake** — the YAML alias-expansion / size guard. The ledger deferred it to "when an
   untrusted producer becomes possible"; an HTTP surface is the milestone where that stops being
   theoretical. Citing test: a hostile fixture that exhausts the guard, not the process.
3. **W-009 intake** — two migration entry points: the public `migrate()` (SAVEPOINT) is called by no
   production path, so the atomicity the tests exercise is not the transaction production runs.
   `migrate` is a K.8 frozen contract name; reconciling the paths must not rename it.
4. REQ-API-006's baseline clauses, each with its own citing test.

**W4 — Deploy readiness and the ADR that was never written (OQ-3)**

1. **A real ADR closing OQ-3** — `D-114` (the next free project ID after `D-113`, see §4). It names
   the target, states why, and **supersedes the `m4-plan.md` citation whose ID collides with the
   ratified D-110**; PRD OQ-3 moves from "open" to closed with the ADR ID next to it. An ADR that
   merely records a preference does not close this — the collision is the defect.
2. Deploy artifacts as **proposals** (Trap 3): container/deploy config and `CODEOWNERS`, reviewed by
   the owner, not treated as settled before D-114 is ratified.
3. Stage 4.3 readiness walked without going live: `curl /health | jq .build` returns the intended
   SHA (L.7 — restart is not rebuild), `make smoke-deps` invokes each external dependency once
   (configured is not working — L.8), config is read back from the running process (L.9).
4. CI: the coverage and roster-staleness legs have **never had a first run**. Watch them here; a leg
   that has never run is a leg whose failure mode is unknown.

**Cap:** 4 waves / ~2k net lines. W4 drops to M7 before this milestone stretches.

---

## 4. Shared contracts (K.8)

**Frozen — M6 consumes these and does not change them:** `recommend()`'s signature; the
`Recommendation` and `Pick` field names; the D-105 category contract (a category ranks on its
primary benchmark's native scale, no cross-scale averaging); D-109 rounding at the output boundary
only; D-110 equivalence disclosure; D-111 budget exclusion; D-112 unequal-effort disclosure; the
`RawSource` protocol; registry first-match semantics; CLI exit codes; the `migrate` contract name.

**New shared surface, frozen by this milestone:** the `/v1` path prefix and envelope; the `surface`
field and its two coding values; `evidence_dating`; the `equivalent_plans` group shape; the error
body shape. Changing any of them after M6 closes is a public-contract change and needs an ADR
(AGENTS.md §5). `grep -n` output for each is pasted at the wave that touches it.

**ADRs this milestone is expected to produce:**

- **D-115 — Both coding surfaces are served; neither leads.** The Ruling A contract, recorded as an
  ADR because it is a public-contract decision and because a future agent will otherwise re-litigate
  it exactly as D-112 was nearly re-litigated.
- **D-116 — Deploy target (closes OQ-3),** superseding the `m4-plan.md` citation collision.

(D-113 and D-114 were taken by the v5.0 baseline move recorded in §8, which was ratified first.)

**Effective wave review tiers:** W1 **MED + pulled-forward security**, W2 **MED**, W3 **HIGH**
(migration, auto-escalated), W4 **LOW-MED** unless its final diff crosses an auto-HIGH boundary.
Milestone product-risk label: **MED**.

---

## 5. Token budget estimate

W1 ≈ 90k (envelope + error contract + pulled-forward security pass) · W2 ≈ 80k · W3 ≈ 100k (HIGH:
migration + two intakes) · W4 ≈ 60k · reviews ≈ 120k (including a second fresh-eyes pass over every
fix delta — M4's escaped-blocker lesson, still budgeted rather than improvised) · closure ≈ 80k
(closure report + retrospective + **handover_q2.txt**) → **≈ 530k**.

---

## 6. Issue inventory

Every row below is either a REQ-backed criterion (§2) or a red-test intake against an existing REQ.
Nothing here is fixed without a test that was shown able to fail.

| id | What | Wave | Kind |
|---|---|---|---|
| W-002 | `equivalent_plans` loses group structure with 2+ groups | W2 | REQ-REC-014 |
| W-005 | `yaml.safe_load` blocks code execution, not alias expansion (measured: MemoryError in ~10 s under 1 GiB) | W3 | intake |
| W-008 | Roster staleness window borrowed from the plan table; both are 30 today and will diverge silently | W3 | REQ-SUB-008 |
| W-009 | Two migration entry points; the atomicity the tests exercise is not production's transaction | W3 | intake |
| W-010 | The effort counter under-reports rows it cannot classify (defect against REQ-CAN-005) | W2 | intake |
| — | CSV export half carries no attribution or blend note | W2 | REQ-LIC-002 |
| — | `agentic-coding` payload does not say its evidence is undated | W1/W2 | REQ-API-004 |
| **W-001** | gitleaks false positive — fires at **two** paths while the ledger row records **one**. Has survived THREE closes. **Owner action; an agent may never waive a scanner finding.** The ledger row's path count is corrected in the same session the owner rules | owner | escalation |

---

## 7. Definition of done

`make check` green on all eight gates · every criterion in §2 has a citing test that was **shown able
to fail** · Ruling A enforced by a test, not by intent · JSON / CSV / CLI parity proven on one run ·
the five carried ledger rows closed or re-ledgered with a reason and an owning milestone · security
review **PASS** at Stage 4.0 · D-113 and D-114 ratified, PRD OQ-3 closed with an ADR ID ·
`docs/closure-report-m6.md` with its §6 architecture-delta prose · retrospective that **answers**
Ruling A's carried question and **poses** the next one · dated `docs/EXPERIENCE.md` entry ·
**`docs/handovers/handover_q2.txt` generated (M % 3 == 0 — blocking).**

---

## 8. Process-baseline amendment: GP v5.0 — CLOSED 2026-08-16

Both items below were ruled on in the signing session and are recorded as **D-113** (baseline moves
to v5.0, superseding D-108) and **D-114** (local-lane git authority, superseding D-106). The
installation was performed the same session via `make export-project`; `make check` is green
(271 passed / 12 skipped) on the new baseline. Three conformance findings are open and ledgered.

*The two questions as they stood at signature:*

1. **Git authority.** v5.0's `AGENTS.md` §3 states the local-lane rule in as many words: *agents
   never commit and never push; they may stage and write a commit message for the owner to run.*
   This repository runs under **D-106**, an owner directive that says the opposite for wave and
   milestone boundary commits. v5.0's rule is not a general tightening — it is the direct answer to
   the failure this project logged as **W-011**, and v5.0 ships `conformance/test-git-authority.py`
   to enforce it mechanically. **Either D-106 is superseded by a new ADR, or it is re-ratified as a
   named exception to v5.0.** It cannot simply stay unstated: a plan whose mode line cites a
   superseded directive is exactly the citation collision W4 exists to repair for OQ-3.
2. **`D-108` pins GP v4.3.1.** Adopting v5.0 supersedes it and needs its own ADR, with the
   installation performed through v5.0's `make export-project` rather than a directory copy — v5.0
   is the first cut that distinguishes the distribution package from an installation, and copying
   the package would import GP-internal records this repository must not carry.

Neither changed the milestone's scope, its criteria, or Ruling A.

**Open before W1 dispatches — the three findings v5.0's conformance suite made on first run:**
W-012 (`.governed-records` glob matches no file, so four wave-close records were never governed),
W-013 (the `pin-check` target removed by v5.0, still named by three historical records), and W-014
(the Cowork handover document still instructs agents to commit under D-106). All three are gate-definition or
record questions and are therefore the owner's, per the escalate-now rule.

---

*Owner signature: **APPROVED — Umut Can Apaydin, 2026-08-16.** Signed in the session that also
directed the move to GP v5.0; §8 records what that directive leaves open.*
