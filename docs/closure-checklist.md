# Closure Checklist (Pipeline v3)

> Two-tier operational checklist. Walk it explicitly at every closure point.
> Updated for v2.0: Quality Gate at milestone closure (§B.1), Quarterly Handover via /quarterly-handover skill.
> Updated for v2.1: §B.3 Deploy verification (Stage 4.3) — "is the new code actually live?" (L.7 + K.10); Handoff is §B.4.
> Updated for v2.2: §0 Stage-0 gate (`make bootstrap-check`, FB-1); §B.3 extended to "deploy + go-live readiness" (L.8/L.9/E.6).
> Updated for v3.5 (2026-07-27, Increment 9 — the post-prod dataset): §B.3 adds the
> outward-facing checks — check-templates, cold-start, human-path, journey tester (V3C-99/100/106),
> the provisioning-ownership table (V3C-107); wave checklist gains the invariant-hardening
> producer-enumeration row (V3C-101); cadence rebinds to outward deliverables (V3C-105).
> Updated for v3.4 (2026-07-17, OD-6/V3C-98): NEW §D — Stage 5 maintenance loop (fix waves +
> fixpack deploy gate + owner out-of-sandbox verification). Fixpack lessons feed EXPERIENCE
> mechanically; the standalone memory-based harvest is RETIRED.
> Updated for v3.3 (2026-07-05, OD-4/V3C-90 — mode A0.5): the OWNER's review moves to MILESTONE
> cadence — waves close agent-side (§B.0); the owner's milestone session (60–90 min): closure
> report + per-wave diffs + HIS OWN local `make test`/smoke tests + the milestone commits.
> Owner checkpoint commits per wave (`wip: NOT reviewed`). Escalate-NOW list in AGENTS.md §3.
> Milestone cap ~4–6 waves / ~2k net lines. RETIRED: the per-wave owner review requirement.
> Updated for v3.2 (2026-07-03): §B.2 generates the OWNER REVIEW PACK (`docs/closure-report.template.md`, V3C-83) from raw referents — it REPLACES the separate §B walkthrough output and note.txt's milestone summary; trust telemetry appended per task type (V3C-84); spike-lane check (V3C-87); autonomy level + streak recorded (V3C-82, `docs/autonomy-protocol.md`).
> Updated for v3.1 (2026-07-03): §B.0 wave-close is checklist-gated (V3C-69, `docs/wave-checklist.template.md` + `make wave-check`) with risk-tiered review depth (V3C-78/P-005); §B.2 adds the living-EXPERIENCE line (V3C-81) and the carried retro question (V3C-79); §B.2a adds security-invariant negative tests (V3C-74), built≠wired (V3C-73), the domain-scoped money sweep (V3C-77), and a skipped/waived-checks ledger.
> Updated for v3 (V3C-68): per-wave gate is Code-Reviewer + **Tester** (§B.0); **Security review is BLOCKING at closure, before deploy** (§B.2a, runs ahead of §B.3); V3C-02 (every acceptance criterion has a citing test) is gate-BLOCKING in §B.1; `bootstrap-check` adds the V3C-11 plaintext-credential / default-admin check (§0); canonical-mock + contract-test convention in §A (V3C-44). Security baseline: `docs/security-baseline.md`.

---

## §0 — Stage-0 bootstrap gate (run once, at the end of Stage 0; FB-1)

The Stage-0 checklist is enforced, not just documented. Stage 0 may not close until:

- [ ] `make bootstrap-check` exits 0 — no stray `<PLACEHOLDER>`s, `/health` is L.7 `{status,version,build}`, prd/decisions/architecture are filled (not templates), universal ADRs D-001..D-005 present, **and no default-admin / plaintext-credential pattern in source (V3C-11, GATE)**
- [ ] **Web/API security baseline reviewed** — walk `docs/security-baseline.md`: no plaintext creds / no default-admin (V3C-11, gate above); server-side authz on mutating routes (V3C-12); CORS allowlist, not allow-all + credentials (V3C-13); security-critical config validated at startup, fails prod (V3C-51); creds/PII encrypted at rest with a rotation-friendly key chain (V3C-56); generic client errors
- [ ] ADR-IDs reconciled — project ADRs at `D-100+`, process ADRs `P-00x` (seed B.6); mapping written in `process-log.md`
- [ ] `docs/license-review.md` completed IF the project wraps/forks an OSS engine (FB-4); AGPL/GPL/SSPL ⇒ wrap-not-fork + legal sign-off
- [ ] `.gitignore` in place and committed before the first real commit (V3C-27 — venv/caches/`environment.md` never tracked)
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
- [ ] **Every acceptance criterion the slice touched has a citing test; a reported symptom was reproduced with a failing test before the fix (V3C-02, gate — red→green)**
- [ ] **Each external integration uses the one canonical mock/fake-client + has a contract test against the real API (V3C-44)** — no bespoke per-test stubs; parallel mocks consolidated
- [ ] Every new `import X` matched by `X>=N` in pyproject.toml (seed C.6)
- [ ] No `# noqa` to silence lint (seed H.5)
- [ ] No hard-coded paths (use `_repo_root()`; seed F.4)
- [ ] No unused `# type: ignore` (seed C.8)
- [ ] If customer-facing artifact touched: discipline followed (B.4 snapshot, B.5 stable IDs, G.5 visible flag, A.4 numbered conflicts)
- [ ] If new ADR captured: status/rationale/mitigation/revisit-when filled (via `/log-decision`)
- [ ] If new playbook seed candidate spotted: drafted for milestone closure audit
- [ ] Final reply includes Done Evidence (per AGENTS.md §7; PASS verdicts cite file:line)

---

## §B — Per-milestone closure (Stage 4)

### B.0 — Per-wave review was completed for every wave (Stage 3; V3C-68)

Confirm each wave in this milestone passed its fresh-eyes gate before closing the milestone:

- [ ] Each implementing agent ran a per-agent **dev-test loop** on its slice (implement → write/run tests → self-review → fix)
- [ ] **Stage 3a Code-Reviewer** verdict per wave (fresh eyes, never own code) — `docs/reviews/m{N}-wave-{W}-review.md`
- [ ] **Stage 3b Tester** verdict per wave (fresh eyes) — `docs/reviews/m{N}-wave-{W}-tester.md`; every acceptance criterion the wave touched has a passing citing test (V3C-02)
- [ ] All wave-level BLOCKING/MINOR fixes flushed before the wave closed
- [ ] **v3.1 (V3C-69):** every wave has its committed wave-close checklist (`docs/plans/m{N}-wave-{W}-close.md` from `docs/wave-checklist.template.md`, `make wave-check` green) — fresh evidence referents; skipped/waived rows ledgered
- [ ] **v3.1 (V3C-78, P-005):** each wave's risk tier was recorded in the plan and review depth matched it (LOW/MED → one combined reviewer; HIGH → Code+Tester + pulled-forward security-on-slice); tripwire did not fire

### B.1 — Quality Gate (Stage 4.1) ★ moved from per-wave in v2.0

- [ ] Done Evidence assembly: combine each wave's Done Evidence block into milestone log
- [ ] REQ-ID coverage trace: every REQ-ID has ≥1 test citing it (write `docs/coverage-by-req.md`)
- [ ] **V3C-02 (GATE, BLOCKING): EVERY acceptance criterion has a citing test, and any reported symptom was reproduced with a failing test before its fix (red→green).** A criterion without a citing test → milestone does NOT close.
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
- [ ] **If M ≥ 3:** run `/retrospect` skill (G.12 PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY)
  - Stage 4 hook fails closure if `docs/retrospectives/m{N}-retrospective.md` is missing
- [ ] **v3.1 (V3C-81):** `docs/EXPERIENCE.md` has a dated entry for THIS milestone (from `docs/EXPERIENCE.template.md`; no secrets/PII; findings cite evidence)
- [ ] **v3.1 (V3C-79):** the retrospective answers the previous retro's carried question and poses one for the next
- [ ] **v3.2 (V3C-83):** `docs/closure-report-m{N}.md` generated from raw referents (criteria table hash-checked, annotated commits, telemetry, ledgers); §6 architecture-delta prose present — **BLOCKING if the agent cannot explain what shipped**
- [ ] **v3.2 (V3C-84):** trust-telemetry rows computed (script, vs the protected closure tag) and appended to cost-log; autonomy streak/tripwires recorded
- [ ] **v3.2 (V3C-87):** `git log` shows no `spike-*` merged into mainline; spike branches deleted at close (secrets scanning ran on spikes too)
- [ ] **v3.3 (V3C-90, mode A0.5):** criteria diffs since plan-sign rendered in the report (hash-freeze); the OWNER ran the milestone session personally — his own `make test` + smoke tests + checks, per-wave diff review via the report's per-wave table, milestone commits — and signed off
- [ ] **v3.3 (V3C-90):** every wave has its owner checkpoint commit (`wip(...): NOT reviewed`); no escalate-NOW event was batched silently to this boundary; fix-rate-vs-baseline line generated (tripwire check)
- [ ] Snapshot roadmap: `docs/roadmap-{YYYY-MM-DD}-post-m{N}.md` (seed I.1; never edit prior)
- [ ] AGENTS.md diet check: `wc -l AGENTS.md` ≤ 150 (D-003); if over, extract to `.agents/rules/`
- [ ] Disciplines-retired count: any THEORETICAL after N≥3 with no PULLED-WEIGHT → propose retirement (D.4)
- [ ] If external article absorbed: update `external-influences-impact.md`

### B.2a — Security review (Stage 4.0) ★ NEW in v3 (V3C-68) — BLOCKING, runs BEFORE B.3 deploy

Moved from the per-wave gate to milestone closure; reviews the whole milestone's surface at once. **Must PASS before any B.3 deploy step.** (Run via `subagent-profiles/Security-Reviewer.md` + `/security-review`; fresh eyes.)

- [ ] Secret scan green across all waves (gitleaks via Stage 2 hooks + CI); no `.env`/secret committed
- [ ] Dependency hygiene: every new dep verified on PyPI + maintainer-age (slopsquat) + pip-audit clean
- [ ] **Web/API security baseline (`docs/security-baseline.md`):** no plaintext creds / no default-admin (V3C-11); server-side authz on every mutating route (V3C-12); CORS allowlist, not allow-all + credentials (V3C-13); security-critical config validated at startup, fails prod (V3C-51); creds/PII encrypted at rest, rotation-friendly key chain (V3C-56); generic client errors
- [ ] Control-class fail direction (V3C-33/45): auth/safety fail CLOSED (tested disable switch + correct scope); fairness/rate-limit fail OPEN
- [ ] External-surface defaults: new endpoints default-deny; RLS/authz at every boundary
- [ ] Prompt-injection hygiene (MEDIUM+); auth/PII/payment/migration senior human review trigger fired (HIGH); SAST (MEDIUM+); PII redaction at log boundaries
- [ ] **v3.1 (V3C-74):** the milestone security-invariants list is current — every invariant cites the NEGATIVE test that fails if it is removed (deny-path release; credential-derived tenant, never request params [IDOR]; redaction asserts ABSENCE in the actual sink)
- [ ] **v3.1 (V3C-73):** every guard/limit/enforcement component built this milestone is WIRED — reachable from the live request path, proven by an end-to-end citing test ("built ≠ wired")
- [ ] **v3.1 (V3C-77, only if the project handles money):** integer minor units + currency end-to-end; Money type rejects float; float sweep of money modules clean
- [ ] **v3.1 (skip ledger):** every check that legitimately did NOT run this milestone is listed with a reason (contract-test self-skips, tier-downs, N/A rows) — silent non-execution is indistinguishable from PASS
- [ ] **Verdict PASS** → proceed to B.3. **BLOCKING → milestone does NOT deploy.** (Safe: waves don't deploy, so security-at-closure always precedes go-live.)

### B.3 — Deploy + go-live readiness (Stage 4.3) ★ v2.1 deploy-verify + v2.2 go-live — only if this milestone deploys

> **v3 precondition (V3C-68): §B.2a Security review must be PASS before any step below.**

**A. Which code is live (L.7):**
- [ ] The deploy references a NEW image tag / git SHA (not a cached one) — confirm the build actually rebuilt
- [ ] `curl <target>/health | jq .build` equals the tag/SHA you intended to ship (L.7); if not, the old image is still running — fix the build pipeline, do NOT just restart the pod (restart != rebuild != re-pull)
- [ ] DevOps-owned build/deploy files (`Dockerfile`, `/deploy/**`, CI config) were not clobbered by this milestone's merges (CODEOWNERS should have flagged it; K.10)
- [ ] `/health` still returns `{status, version, build}` and the liveness contract is unchanged (additive fields only)

**B. Is the pipe actually working — go-live readiness (NEW v2.2):**
- [ ] L.8 dependency liveness: `make smoke-deps` — invoked EACH external dependency once for real (model / queue / store / callback) and inspected the RESULT, not the config screen (configured != working)
- [ ] L.9 config reaches the process: read each critical config value back from INSIDE the running process (in-pod env / safe echo: SET/EMPTY + length, never the value) — "set in the values file" != "set in the process"
- [ ] E.6 pipe attribution: one real request confirmed in the downstream's own run log, attributed to this service (proves auth + connectivity + routing; isolates any blocker to its node)
- [ ] ~~**v3.5 (V3C-99):** `make check-templates` green — every SHIPPED config template instantiates the settings parser (CI run cited) ~~ — **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything.
- [ ] ~~**v3.5 (V3C-99):** `make cold-start` green — boot against ZERO persisted state reaches serve-ready or an honest not-ready (CI run cited) ~~ — **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything.
- [ ] **v3.5 (V3C-100):** human-path done — a named person who did NOT build it, using only shipped docs, obtained a credential and made an authorized call
- [ ] ~~**v3.5 (V3C-106):** `make journey URL=<deployed>` green (default-expected; skip recorded in the closure report) — cold entry · credential lifecycle · paying-customer round trip asserting CONTENT · one cross-wave sequence ~~ — **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything.
- [ ] **v3.5 (V3C-107):** provisioning-ownership table current — every boot prerequisite is IN THE IMAGE or a named-owned row; no third category

### B.4 — Handoff (Stage 4.4) ★ quarterly

- [ ] `note.txt` refreshed (≤30 lines; G.7)
- [ ] **If M%3 == 0:** run `/quarterly-handover` skill → `docs/handovers/handover_q{M/3}.txt`
  - Tag commit: `git tag handover-q{M/3}`
- [ ] If a `when_<event>.txt` playbook was triggered or completed this milestone: archive or refresh
- [ ] Harness diet (at handover_qN): count hooks/skills/MCPs; retire any skill not fired in 90 days

### B.5 — Pipeline readiness audit (only at milestone N-2 from final)

If project's final milestone count is known (e.g., M9 closes), at M(N-2) run:
- [ ] Write `docs/pipeline-readiness-audit.md` — every required-for-deploy artifact marked PRESENT / PARTIAL / MISSING
- [ ] Plan how to convert PARTIAL/MISSING to PRESENT before final milestone

---

## §D — Stage 5: Maintenance loop (post-deploy fix waves) ★ v3.4 (V3C-98)

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

## Before you relax anything: the backtest rule (V4C-70, v4.3)

**A proposal to relax a gate, a bar or a review depth must carry a backtest against the previous
milestone's REAL defect list, naming which defects would pass.** No backtest, no relaxation.

**Why this is first among the v4.3 adopts.** The owner opened a session convinced the process was too
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
