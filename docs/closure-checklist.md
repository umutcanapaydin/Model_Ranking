# Closure Checklist (Pipeline)

> Two-tier operational checklist. Walk it explicitly at every closure point.
> Updated: Quality Gate at milestone closure (§B.1), Quarterly Handover via /quarterly-handover skill.
> Updated: §B.3 Deploy verification (Stage 4.3) — "is the new code actually live?" (L.7 + K.10); Handoff is §B.4.
> Updated: §0 Stage-0 gate (`make bootstrap-check`, FB-1); §B.3 extended to "deploy + go-live readiness" (L.8/L.9/E.6).
> Updated for (2026-07-27, — the post-prod dataset): §B.3 adds the
> outward-facing checks — check-templates, cold-start, human-path, journey tester,
> the provisioning-ownership table; wave checklist gains the invariant-hardening
> producer-enumeration row; cadence rebinds to outward deliverables.
> Updated for (2026-07-17): NEW §D — Stage 5 maintenance loop (fix waves +
> fixpack deploy gate + owner out-of-sandbox verification). Fixpack lessons feed EXPERIENCE
> mechanically; the standalone memory-based harvest is RETIRED.
> Updated for (2026-07-05, — mode A0.5): the OWNER's review moves to MILESTONE
> cadence — waves close agent-side (§B.0); the owner's milestone session (60–90 min): closure
> report + per-wave diffs + HIS OWN local `make test`/smoke tests + the milestone commits.
> Every slice reaches the protected branch as a pull request a human merged (replaces the per-wave owner checkpoint commit). Escalate-NOW list in AGENTS.md §3.
> Milestone cap ~4–6 waves / ~2k net lines. RETIRED: the per-wave owner review requirement.
> Updated for (2026-07-03): §B.2 generates the OWNER REVIEW PACK (`docs/closure-report.template.md`) from raw referents — it REPLACES the separate §B walkthrough output and note.txt's milestone summary; trust telemetry appended per task type; spike-lane check; autonomy level + streak recorded (`docs/autonomy-protocol.md`).
> Updated for (2026-07-03): §B.0 wave-close is checklist-gated (`docs/wave-checklist.template.md` + `make wave-check`) with risk-tiered review depth (P-005); §B.2 adds the living-EXPERIENCE line and the carried retro question; §B.2a adds security-invariant negative tests, built≠wired, the domain-scoped money sweep, and a skipped/waived-checks ledger.
> Updated: per-wave gate is Code-Reviewer + **Tester** (§B.0); **Security review is BLOCKING at closure, before deploy** (§B.2a, runs ahead of §B.3); (every acceptance criterion has a citing test) is gate-BLOCKING in §B.1; `bootstrap-check` adds the plaintext-credential / default-admin check (§0); canonical-mock + contract-test convention in §A. Security baseline: `docs/security-baseline.md`.

---

## §0 — Stage-0 bootstrap gate (run once, at the end of Stage 0; FB-1)

The Stage-0 checklist is enforced, not just documented. Stage 0 may not close until:

- [ ] `make bootstrap-check` exits 0 — **this checklist is its only caller; it is deliberately not a leg of `make gate`, because it fails on unfilled placeholders and a fresh export would be red on day one**. — no stray `<PLACEHOLDER>`s, `/health` is L.7 `{status,version,build}`, prd/decisions/architecture are filled (not templates), universal ADRs D-001..D-005 present, **and no default-admin / plaintext-credential pattern in source (GATE)**
- [ ] **Web/API security baseline reviewed** — walk `docs/security-baseline.md`: no plaintext creds / no default-admin (gate above); server-side authz on mutating routes; CORS allowlist, not allow-all + credentials; security-critical config validated at startup, fails prod; creds/PII encrypted at rest with a rotation-friendly key chain; generic client errors
- [ ] ADR-IDs reconciled — project ADRs at `D-100+`, process ADRs `P-00x` (seed B.6); mapping written in `process-log.md`
- [ ] `docs/license-review.md` completed IF the project wraps/forks an OSS engine (FB-4); AGPL/GPL/SSPL ⇒ wrap-not-fork + legal sign-off
- [ ] `.gitignore` in place and committed before the first real commit (venv/caches/`environment.md` never tracked)
- [ ] git finished host-side (Cowork mounted-FS lock footgun; clear `.git/*.lock` host-side if stale — seed C.12)

---

## §A — Per-slice closure (every feature ships through this)

Tick each box. Skipped on purpose: leave `[ ]` with one-line reason in same reply (AGENTS.md §3.6).

- [ ] `make lint` clean
- [ ] `make typecheck` clean
- [ ] `make test` green
- [ ] `make secrets` (gitleaks) green
- [ ] `make deps` (pip-audit) green
- [ ] New code covered by ≥1 test citing REQ-ID/D-ID with `file:line` evidence (seed E.2 + D-006)
- [ ] **Every acceptance criterion the slice touched has a citing test; a reported symptom was reproduced with a failing test before the fix (gate — red→green)**
- [ ] **Each external integration uses the one canonical mock/fake-client + has a contract test against the real API ** — no bespoke per-test stubs; parallel mocks consolidated
- [ ] Every new `import X` matched by `X>=N` in pyproject.toml (seed C.6)
- [ ] No `# noqa` to silence lint (seed H.5)
- [ ] No hard-coded paths (use `_repo_root`; seed F.4)
- [ ] No unused `# type: ignore` (seed C.8)
- [ ] If customer-facing artifact touched: discipline followed (B.4 snapshot, B.5 stable IDs, G.5 visible flag, A.4 numbered conflicts)
- [ ] If new ADR captured: status/rationale/mitigation/revisit-when filled (via `/log-decision`)
- [ ] If new playbook seed candidate spotted: drafted for milestone closure audit
- [ ] Final reply includes Done Evidence (per AGENTS.md §7; PASS verdicts cite file:line)

---

## §B — Per-milestone closure (Stage 4)

### B.0 — Per-wave review was completed for every wave (Stage 3)

Confirm each wave in this milestone passed its fresh-eyes gate before closing the milestone:

- [ ] Each implementing agent ran a per-agent **dev-test loop** on its slice (implement → write/run tests → self-review → fix)
- [ ] **Stage 3a Code-Reviewer** verdict per wave (fresh eyes, never own code) — `docs/reviews/m{N}-wave-{W}-review.md`
- [ ] **Stage 3b Tester** verdict per wave (fresh eyes) — `docs/reviews/m{N}-wave-{W}-tester.md`; every acceptance criterion the wave touched has a passing citing test 
- [ ] All wave-level BLOCKING/MINOR fixes flushed before the wave closed
- [ ] every wave has its committed wave-close checklist (`docs/plans/m{N}-wave-{W}-close.md` from `docs/wave-checklist.template.md`, `make wave-check` green) — fresh evidence referents; skipped/waived rows ledgered
- [ ] **P-005:** each wave's risk tier was recorded in the plan and review depth matched it (LOW/MED → one combined reviewer; HIGH → Code+Tester + pulled-forward security-on-slice); tripwire did not fire

### B.1 — Quality Gate (Stage 4.1) ★ moved from per-wave

- [ ] Done Evidence assembly: combine each wave's Done Evidence block into milestone log
- [ ] REQ-ID coverage trace: every REQ-ID has ≥1 test citing it (write `docs/coverage-by-req.md`)
- [ ] **GATE, BLOCKING: EVERY acceptance criterion has a citing test, and any reported symptom was reproduced with a failing test before its fix red→green .:** A criterion without a citing test → milestone does NOT close.
- [ ] Coverage delta on new/modified code
- [ ] Strict mypy clean across all modules
- [ ] Strict ruff clean across all modules
- [ ] LOC budget: cumulative milestone LOC reasonable (no surprise bloat)
- [ ] Write `docs/cost-log.md` entry (token spend vs Stage 1 estimate)
- [ ] **If BLOCKING per D-006/§11 taxonomy → milestone DOES NOT close.** Dispatch mini-fix wave, return to B.1.

### B.2 — Capture (Stage 4.2)

- [ ] Append `process-log.md` S{N} entry (G.1; 3-10 lines; ends with `Lesson:` tag)
- [ ] Add any new ADRs via `/log-decision` skill
- [ ] List proposed seeds → user approves → mark active in `.agents/rules/playbook-seeds.md`
- [ ] **If M ≥ 3:** run `/cycle-close` skill (G.12 PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY)
 - Stage 4 hook fails closure if `docs/retrospectives/m{N}-retrospective.md` is missing
- [ ] `docs/EXPERIENCE.md` has a dated entry for THIS milestone (from `docs/EXPERIENCE.template.md`; no secrets/PII; findings cite evidence)
- [ ] the retrospective answers the previous retro's carried question and poses one for the next
- [ ] **Verified with `make closure-check FILE=docs/closure-report-m{N}.md`** — the pack is a record, and an unfilled record is not a close. `docs/closure-report-m{N}.md` generated from raw referents (criteria table hash-checked, annotated commits, telemetry, ledgers); §6 architecture-delta prose present — **BLOCKING if the agent cannot explain what shipped**
- [ ] trust-telemetry rows computed (script, vs the protected closure tag) and appended to cost-log; autonomy streak/tripwires recorded
- [ ] `git log` shows no `spike-*` merged into mainline; spike branches deleted at close (secrets scanning ran on spikes too)
- [ ] **Mode A0.5:** criteria diffs since plan-sign rendered in the report (hash-freeze); the OWNER ran the milestone session personally — his own `make test` + smoke tests + checks, per-wave diff review via the report's per-wave table, milestone commits — and signed off
- [ ] every slice reached the protected branch as a pull request a human merged —
 not as a direct commit. `conformance/test-commit-identity.py` verifies the range.
- [ ] Snapshot roadmap: `docs/roadmap-{YYYY-MM-DD}-post-m{N}.md` (seed I.1; never edit prior)
- [ ] AGENTS.md diet check: `wc -l AGENTS.md` ≤ 150 (D-003); if over, extract to `.agents/rules/`
- [ ] Disciplines-retired count: any THEORETICAL after N≥3 with no PULLED-WEIGHT → propose retirement (D.4)
- [ ] If external article absorbed: update `external-influences-impact.md`

### B.2a — Security review (Stage 4.0) — BLOCKING, runs BEFORE B.3 deploy

Moved from the per-wave gate to milestone closure; reviews the whole milestone's surface at once. **Must PASS before any B.3 deploy step.** (Run via `subagent-profiles/Security-Reviewer.md` + the Security-Reviewer profile (`subagent-profiles/Security-Reviewer.md`); fresh eyes.)

- [ ] Secret scan green across all waves (gitleaks via Stage 2 hooks + CI); no `.env`/secret committed
- [ ] Dependency hygiene: every new dep verified on PyPI + maintainer-age (slopsquat) + pip-audit clean
- [ ] **Web/API security baseline (`docs/security-baseline.md`):** no plaintext creds / no default-admin; server-side authz on every mutating route; CORS allowlist, not allow-all + credentials; security-critical config validated at startup, fails prod; creds/PII encrypted at rest, rotation-friendly key chain; generic client errors
- [ ] Control-class fail direction: auth/safety fail CLOSED (tested disable switch + correct scope); fairness/rate-limit fail OPEN
- [ ] External-surface defaults: new endpoints default-deny; RLS/authz at every boundary
- [ ] Prompt-injection hygiene (MEDIUM); auth/PII/payment/migration senior human review trigger fired (HIGH); SAST (MEDIUM); PII redaction at log boundaries
- [ ] the milestone security-invariants list is current — every invariant cites the NEGATIVE test that fails if it is removed (deny-path release; credential-derived tenant, never request params [IDOR]; redaction asserts ABSENCE in the actual sink)
- [ ] every guard/limit/enforcement component built this milestone is WIRED — reachable from the live request path, proven by an end-to-end citing test ("built ≠ wired")
- [ ] **Only if the project handles money:** integer minor units + currency end-to-end; Money type rejects float; float sweep of money modules clean
- [ ] **Skip ledger:** every check that legitimately did NOT run this milestone is listed with a reason (contract-test self-skips, tier-downs, N/A rows) — silent non-execution is indistinguishable from PASS
- [ ] **Verdict PASS** → proceed to B.3. **BLOCKING → milestone does NOT deploy.** (Safe: waves don't deploy, so security-at-closure always precedes go-live.)

### B.3 — Deploy + go-live readiness (Stage 4.3) ★ deploy-verify + go-live — only if this milestone deploys

> **Precondition: §B.2a Security review must be PASS before any step below.:** 

**A. Which code is live (L.7):**
- [ ] The deploy references a NEW image tag / git SHA (not a cached one) — confirm the build actually rebuilt
- [ ] `curl <target>/health | jq .build` equals the tag/SHA you intended to ship (L.7); if not, the old image is still running — fix the build pipeline, do NOT just restart the pod (restart != rebuild != re-pull)
- [ ] DevOps-owned build/deploy files (`Dockerfile`, `/deploy/**`, CI config) were not clobbered by this milestone's merges (CODEOWNERS should have flagged it; K.10)
- [ ] `/health` still returns `{status, version, build}` and the liveness contract is unchanged (additive fields only)

**B. Is the pipe actually working — go-live readiness (NEW):**
- [ ] L.8 dependency liveness: `make smoke-deps` — invoked EACH external dependency once for real (model / queue / store / callback) and inspected the RESULT, not the config screen (configured != working). `binds: <the dependency endpoints the RUNNING process resolves, not the ones in the repo's config>` — name them on the line
- [ ] L.9 config reaches the process: read each critical config value back from INSIDE the running process (in-pod env / safe echo: SET/EMPTY + length, never the value) — "set in the values file" != "set in the process"
- [ ] E.6 pipe attribution: one real request confirmed in the downstream's own run log, attributed to this service (proves auth + connectivity + routing; isolates any blocker to its node)
- [ ] ~~`make check-templates` green — every SHIPPED config template instantiates the settings parser (CI run cited) ~~— **REMOVED at the control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything.
- [ ] **RETURNED, then bound (condition):** `make cold-start` green — one boot against ZERO persisted state, **through the deployment's actual mechanism** (fresh volume / fresh container / the real image), never a repo-local approximation. `binds: <the artefact the deployment consumes>` — name it on the line. **FAILS CLOSED.** Field evidence that brought it back: a readiness probe on a DB-free path reported Ready against a dead database, and a concurrent unlocked `alembic upgrade` on first boot.
- [ ] human-path done — a named person who did NOT build it, using only shipped docs, obtained a credential and made an authorized call
- [ ] **RETURNED, then bound (condition):** `make journey URL=<deployed>` green — **one recorded walkthrough at human speed**: cold entry · credential lifecycle · paying-customer round trip asserting CONTENT · one cross-wave sequence. `binds: <the deployed URL / artefact>` — name it on the line. **FAILS CLOSED.** Field evidence that brought it back: five root causes reached the CUSTOMER through this gap (ingress misroute, popup 500, 422 concat, placeholder username, stripped security headers) — the best catch ratio in the dataset, for ~60 lines and one URL.
- [ ] provisioning-ownership table current — every boot prerequisite is IN THE IMAGE or a named-owned row; no third category

**How the two returned rows fail, and the one way to skip them (condition, fail-closed).**
They are not "default-expected with a skip recorded" — that wording is what let `journey` sit unrun
for five versions. Unfilled is FAIL. There are exactly two legitimate outs, and both are written
down rather than left blank:

- **Ledgered waiver.** A skip goes in `docs/warnings.ledger.md` with a reason and an owning
 milestone, and the bypass count moves. The same control waived three times triggers review
 of the CONTROL, not of the person waiving it.
- **Written N/A.** Only when the milestone ships **no runnable surface at all** — no deploy, no
 artefact a human could enter. The N/A is written into the closure report with that sentence. A
 milestone that deploys anything has a runnable surface, and "we did not have time to stand it up"
 is a waiver, not an N/A.

**`binds:` — the gate must name the artefact it reads (condition, candidate F).**
Every deployment-facing gate above carries a machine-readable `binds:` declaration naming the
artefact it inspects and whether that artefact is **what the deployment actually consumes**. The
closure check greps for it (`conformance/test-binds-declared.py`), and `make check` runs that.

- A green gate bound to an artefact the cluster does not run is recorded as **NOT-BINDING** — its
 own annotation, never folded into NOT-INSTALLED. Four of six seats voted against that overload:
 one value meaning two things is the exact defect candidate E repairs, and rebuilding it in the
 same increment would have been comic.
- **"The deployed artefact is not in any readable repository" is BLOCKING by construction** (GPF-010).
 Not a warning, not an N/A. If nothing readable describes what is running, the gate has nothing to
 bind to and the milestone does not close.
- Field origin: a project's best new gate checked manifests **the cluster did not run**, and the
 go-live gate stayed stale straight through a customer deployment — last touched `9c5b225`,
 2026-08-18, verified by the chair. Every claim it made was true about a file nobody deployed.

### B.4 — Handoff (Stage 4.4) ★ quarterly

- [ ] `note.txt` refreshed (≤30 lines; G.7)
- [ ] **If M%3 == 0:** run `/cycle-close` skill → `docs/handovers/handover_q{M/3}.txt`
 - Tag commit: `git tag handover-q{M/3}`
- [ ] If a `when_<event>.txt` playbook was triggered or completed this milestone: archive or refresh
- [ ] Harness diet (at handover_qN): count hooks/skills/MCPs; retire any skill not fired in 90 days

### B.5 — Pipeline readiness audit (only at milestone N-2 from final)

If project's final milestone count is known (e.g., M9 closes), at M(N-2) run:
- [ ] Write `docs/pipeline-readiness-audit.md` — every required-for-deploy artifact marked PRESENT / PARTIAL / MISSING
- [ ] Plan how to convert PARTIAL/MISSING to PRESENT before final milestone

---

## §D — Stage 5: Maintenance loop (post-deploy fix waves) ★ 

Per FIX WAVE: the normal wave checklist applies (§B.0 machinery by reference) + red-test intake.
Per FIXPACK (the deploy gate — walk `docs/fixpack.template.md`):

- [ ] Every fix row complete (bug ref · red test · commit · CR + Tester verdicts · gate-attribution lesson)
- [ ] Security floor: gitleaks/SCA · full invariant suite GREEN · diff-scoped read · ⛔ auto-escalation honored
- [ ] Full regression GREEN once on the exact final bundled build
- [ ] **Owner out-of-sandbox verification signed** (reproduce pre-fix → gone post-fix → local tests) — BLOCKING
- [ ] Deploy: 4.3 gate + fix probe in prod + watch window clean
- [ ] Capture coupling: lesson lines appended to EXPERIENCE.md (deploy condition) · 3-strikes + N=3 checks run
- [ ] Emergency pack? "why now" line present + 48h retroactive close scheduled

## §C — Per-phase closure (project end / phase boundary)## §C — Per-phase closure (project end / phase boundary)

- [ ] Final roadmap snapshot (e.g., `roadmap-final-phase{N}.md`)
- [ ] Phase retrospective (cross-milestone G.12 compiled)
- [ ] Phase trigger for next phase
- [ ] Last quarterly handover (`handover_q{last}.txt`) doubles as phase handover
- [ ] If applicable: `docs/handover-to-prod-agent.md` (operator runbook)

## Before you relax anything: the backtest rule 

> **Clause: removing a control is relaxing it to zero.:** 
>
> 's text covered a *proposal to relax a gate or a bar* and said nothing about removing one,
> so the largest relaxation in this lineage's history — 66 controls deleted in a single commit —
> arrived with no backtest, none asked for, none produced. A second project silently dropped `mypy`
> in a restart commit that claimed to restore it; a third carried a control as EXPECTED_FAIL twice
> and then dropped it from the harness for eleven runs. **Two of those three were never recorded
> anywhere.**
>
> **The threshold, named so it can be violated:** removing **≥5 controls in one change** requires a
> written backtest artefact — take the previous milestone's real defect list, apply the looser bar
> backwards, name every defect that would have passed. Below five, a named judgement in the closure
> record suffices. The bare word *"proportional"* was struck at ratification: a proportionality with
> no number names nothing anyone can be shown to have violated, which is the unfalsifiable half of
> an otherwise clean repair.
>
> **This clause is a guardrail, not a gate.** Nothing in GP executes it; the chair enforces it at
> intake. What is mechanical is the record: a governance record declaring a removal carries a
> `backtest:` reference, validated the way `binds:` is. ** has been applied in the field five
> times and every application produced a number that moved a decision** — it is the most-used rule
> in the register, which is why this is a definitional repair rather than a new rule.


**A proposal to relax a gate, a bar or a review depth must carry a backtest against the previous
milestone's REAL defect list, naming which defects would pass.** No backtest, no relaxation.

**Why this is first among the adopts.** The owner opened a session convinced the process was too
strict — *"security findings eat too much time, let us set aside the one-in-a-million ones."* A
five-clause severity bar was designed to do exactly that, then applied backwards to the previous
milestone's **21 real defects. It let 3 through: 14%.** The bar would not have shortened the milestone
by a day. The time had gone to a **review loop** and to **controls that were never installed** — not to
strictness. Without that number the relaxation would have been signed and the expected relief would
never have arrived.

**A relaxation proposal without a backtest is a feeling, not a measurement.**

*(Open condition, recorded: the 14% figure's population is itself unreconciled — 21 vs 22 vs 23
depending on the counting. The conclusion survives every denominator; the precise figure must be
reconciled before it is cited again.)*
