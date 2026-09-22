# Refusals — decisions NOT to build 

> **Purpose:** a refusal is a decision, and a decision that is not written down gets
> re-litigated every quarter. Each row below was refused by a council with a reason and a
> re-open trigger. **A refusal is not "not yet" — it is "no, until the trigger fires."**
>
> Ratified 2026-07-30 (9-seat council, unanimous adopt — "highest ROI in the batch").
> COST LINE: zero recurring; consulted when a proposal arrives; ~1 minute.

| # | Refused | Why (at OUR scale: one owner + agents, no platform team, no SRE rotation) | Re-open trigger |
|---|---|---|---|
| 1 | **Any workflow/durable-execution engine** — Temporal, Restate, Hatchet, Inngest, Argo Workflows, Prefect, Dagster, LangGraph-as-dependency | Three independent research passes rejected all of them for this scale. The deciding argument is **failure ownership, not licence cost**: a service you run at 2am alone is a liability. And none of them addresses our actual failure mode, which is *"a step was skipped and nothing noticed"*, not *"a process crashed mid-run"*. | Measured, recurring loss of in-flight work OR duplicated external side effects, ≥3 incidents in one cadence |
| 2 | **Durable execution's replay model** | Replay requires determinism; LLM steps are not deterministic. Copying the mechanism without the precondition yields a system that *looks* resumable and silently diverges. We keep the salvageable half: run IDs + an append-only journal. | LLM steps become deterministic (they will not) |
| 3 | **Any new configuration or policy language** — CUE, Pkl, Dhall, Rego/OPA | The operators are language models and **fluency is an operational requirement**. A schema an agent can author and repair unassisted beats a more expressive schema it will subtly get wrong twice a year, debugged by an owner who last saw the language six months ago. | ≥3 stable cross-record rules that provably cannot be expressed in `check_records.py` |
| 4 | **A memory/vector service for exact state** — mem0, Letta | Approximate retrieval answers "what might be relevant"; governance state needs "which record is at which stage, and what was decided". Vector retrieval is unauditable and uncitable. At a corpus of dozens of markdown files, `grep` is more precise and free. | Corpus exceeds what grep can serve AND an audit trail is preserved |
| 5 | **Any hosted trace/observability backend that receives transcripts** — Langfuse Cloud, LangSmith, self-hosted Langfuse | Shipping source — and via error output sometimes credentials — to a third party, in a system whose entire credential design is "CI holds them". Metrics and event *names* are fine; trace *bodies* are not. | Never for transcripts; a metrics-only, no-body integration may be proposed separately |
| 6 | **Chasing an SLSA level, or an SBOM of process artifacts** | SLSA's ladder is designed for consumers who verify your builds; we have none. A "process SBOM" is a list of ~96 markdown filenames with hashes, which `git ls-tree` already produces. We adopt **one** attestation predicate for one unforgeable claim if and when we need it — never the ladder. | An external consumer contractually requires attested provenance |
| 7 | **Prose linting** (Vale-class) and **commit-derived semver** (conventional-commits → release-please) | The first spends owner attention enforcing things no reader benefits from; the second lets an agent's word choice bump a constitution's MAJOR version. Version semantics are an owner decision. | Never for semver-from-commits; prose linting re-openable if a reader complains twice |
| 8 | **Third-party apps with repo write access** — Renovate self-hosted/hosted, OpenSSF Allstar | Standing infrastructure or org-wide write scope, to replicate one behaviour: compare a recorded pin to upstream and warn. That is ~15 lines of the Python we already run. | Never at this scale |
| 9 | **Any low-star tool on a governance path** — the round's most transferable empirical result | Verified dead or dormant: `adr-tools` (5.5k★, dead since 2020), `log4brains` (dormant), `remark-lint-frontmatter-schema` (no commit since Aug 2024), `kyverno-json` (93★, dormant). Meanwhile MADR, JSON Schema, AGENTS.md, markdown and git are alive and will outlive every CLI built on them. **Adopt FORMATS; write your own 150 lines; never adopt a 10-star dependency for governance.** | Never — this one is structural, not situational |
| 10 | **Taskfile as a Makefile replacement** (8 REJECT of 9) | Make is present, zero-dependency, universally known to agents, and load-bearing in hooks + CI. Our defect was never the runner — it was **untested recipes** (a ratified gate that had never executed once). Replacing the layer that works while the layer that is broken stays broken is misdirected effort. | A Windows-native operator joins, or Make becomes the measured bottleneck |
| 11 | **Rung 5 of the maturity ladder** — an executed, stateful, traced governance engine | **Refused by decision, not deferred by budget** (stopping rule, 9/9 concur). No published project governs its own process on a rung-5 engine; rung 5 is where vendors build products, not where anyone governs a process. | Owner ADR only, with measured evidence that rung 4 is insufficient |
| 12 | **Empirical A/B evaluation of process artifacts:** (Tessl task-evals direction). Adopted as a doc-class pilot, owner-settled on the technical-side rule | **Refused now, by ruling, rather than carried a third time.** Its condition — *one A/B result attached to the next intake* — lapsed twice; the council telemetry caught it, and the **PM seat converted the recommendation into a ruling**: *"REFUSE to carry it a third time in its current open-ended form."* The reason it never ran is structural, not effort: an A/B needs a **held-out task set**, enough runs for signal, and an outcome metric not judged by the same agent that produced the output. At one owner plus agents, **N is too small for a split to say anything.** Our working evidence engine is field harvest at N=1–3 with root-cause analysis — which found 48 findings and two live security defects this cycle, while the A/B lane produced nothing in two increments. Carrying a doc-class adopt indefinitely is how it becomes permanent decoration. | **≥3 projects running the same package concurrently** (enough N for a held-out split), **OR** a process-artifact change whose effect two seats dispute with no field evidence available to settle it |

## The rule this file encodes

> *Do not climb a rung because the ladder has another rung.* Advance only when a measured failure
> in the current rung demands it — and record the refusal so the argument is made once.

## R-2026-09-01 — Class-specific trigger (3→2 for config-bound-to-nothing)

Proposed by the Project-G field harvest (2026-08-26); refused 6/6 by the council and
the chair, ratified by the owner. Grounds: (1) 1/4 recurrence — below the adoption bar; (2)
class-specific thresholds require a class taxonomy nobody maintains, and are rule proliferation by
another name; (3) the field evidence shows the uniform trigger is a ceiling, not a floor — Project-G
acted at 2 by local discretion and it worked, needing no GP change; (4) (Security) a uniform
escalation threshold is itself a security property: predictable and un-gameable under pressure.
Do not re-litigate; a new proposal must bring cross-project recurrence of the TRIGGER failing, not
of projects succeeding early.

## R-2026-09-20 — Re-deriving GP's control set from an outsider's grading (§3)

**REFUSED, unanimously, seven seats, seven independent routes.** Recorded under the harvest-disposition rule (.1):
a REFUSE is as complete a resolution as an adoption, and this one is the council's, not the
harvest's.

**What was proposed.** The Project-B/Project-C field harvest (2026-09-15) §7 dispositioned its F1 as
`GP CHANGE`: *"Treat this as the first independent grading of the control set and open the next
increment by re-deriving the set from it, rather than defending the count."* An outside engineer,
handed a project, kept 8 of 74 controls; every survivor answered *can this leak, widen or grant*.

**Why refused.**

1. **It graded a different set.** The 74 are files in one project's `scripts/`. **GP's own inventory
 is 45**, and none of the nine named removed controls ships in either of the last two cuts
 — 9/9 absent, measured. The harvest's *"GP's control set is 11% product and 89% process"* is a
 category error, and the chair's packet repeated it.
2. **It produced zero running controls.** The transcription check measured the survivors: 8 kept,
 **0 with callers.** `make check` was `lint typecheck test`; the strip commit deleted the
 `check-gates` target itself. A selection criterion whose output is eight uninvoked files has not
 been shown to survive contact with a build system.
3. **Its axis does not predict catch rate.** The backtest found ≥33% of the removed set on the
 record having caught something, and **roughly two thirds of those are process controls** — the
 class the grading removed wholesale.
4. **Half the ledger was never measured.** Cost — which is the half the removal was actually made
 on. Benefit measured, cost absent.
5. **Scale.** MAJOR, proposed on the thinnest corpus any GP increment has run.

**What the grading earned, and is kept.** Three findings survive the refusal: the **11%/89% ratio**,
measured from outside for the first time in this lineage; that **71% of the removed controls were
born carrying the failure they describe**; and that the removal of the plumbing-integrity tier
(`check-gates-are-invoked`, `gate-tally`) is what made the survivors hollow. The first is now a
standing measurement, not a one-time shock.

**What replaces it (condition).** The council adopted the PM seat's relocation: the defect is
not in GP's inventory, it is in **GP's output**. GP induces a project to accumulate ~74 local
controls in five weeks, 71% retrofitted from local accidents, and nothing in GP screens, bounds or
retires them. `docs/watchlist.md` gains a row-type for a control a project invented.

**RE-OPEN TRIGGER, so this is not re-litigated from prose.** This refusal is void and the question
returns on **a second independent outsider grading, performed against a WIRED tree, by someone who
is not an author of the control set** — and each keep/drop decision must cite the control's
last-fired evidence or record `NO-TRACE` explicitly. Grading a roster whose callers were deleted in
the same commit measures nothing.
