# Closure Checklist

> Walk it explicitly at every closure point. **Stage 0 (§0)** closes the bootstrap. **Stage 4 (§B)**
> closes a milestone: its waves merged, capture done, and — only if the owner turned it on — the
> Quality Gate. **Stage 5 (§E)** is the release, once, when the work is done: security review, deploy
> and go-live, and one optional retrospective. Nothing deploys at a milestone close. **Stage 6 (§D)**
> is the maintenance loop. No retrospective or handover is written during the work.

---

## §0 — Stage 0: bootstrap (once)

Stage 0 may not close until:

- [ ] `/setup-project` asked the setup questions and wrote the answers to `docs/project-brief.md` (from `docs/project-brief.template.md`); the owner merged the PR that adds it
- [ ] The project name and description are filled in `pyproject.toml`; `make install` is green
- [ ] `make hooks` ran in every clone — `make gate` runs before every push
- [ ] `.devflow-stack` names the product's stack; any stack but `python` binds its four legs in `stack.mk` (`INSTALL.md`), and none of them says `BIND ME:`
- [ ] `make labels` created the issue-label vocabulary (once per repository)
- [ ] Branch protection on the default branch requires the jobs in `docs/branch-protection.md`, or the brief records that the repository cannot enforce it
- [ ] `docs/EXPERIENCE.md` exists (copied from `docs/EXPERIENCE.template.md`)
- [ ] `make bootstrap-check` exits 0 — **this checklist is its only caller; it is deliberately not a leg of `make gate`, because it fails on unfilled placeholders and a fresh install would be red on day one.** It checks: no stray `<PLACEHOLDER>`s, `/health` is L.7 `{status,version,build}`, prd/decisions/architecture are filled (not templates), universal ADRs D-001..D-007 present, the project brief is filled and every customer-reachable repository is declared, `make hooks` ran in this clone unless the brief records both GitHub Actions and branch protection, and no default-admin / plaintext-credential, CORS allow-all-with-credentials or destructive-default-ON pattern in source
- [ ] **Web/API security baseline reviewed** — walk `docs/security-baseline.md`: no plaintext creds / no default-admin; server-side authz on mutating routes; CORS allowlist, not allow-all + credentials; security-critical config validated at startup, fails prod; creds/PII encrypted at rest with a rotation-friendly key chain; generic client errors
- [ ] ADR-IDs reconciled — project ADRs at `D-100+`, process ADRs `P-00x` (seed B.6); mapping written in `process-log.md`
- [ ] `docs/license-review.md` completed IF the project wraps/forks an OSS engine; AGPL/GPL/SSPL ⇒ wrap-not-fork + legal sign-off
- [ ] `.gitignore` in place and committed before the first real commit (venv/caches/`environment.md` never tracked)
- [ ] git finished host-side (mounted-filesystem lock footgun; clear `.git/*.lock` host-side if stale — seed C.12)

Then Stage 1: `/plan-milestone`. The owner approves the plan by merging its PR.

---

## §A — Per-slice closure (every feature ships through this)

Tick each box. Skipped on purpose: leave `[ ]` with a one-line reason in the same reply.

- [ ] `make lint` clean
- [ ] `make typecheck` clean
- [ ] `make test` green
- [ ] `make secrets` (gitleaks) green
- [ ] `make deps` (pip-audit) green
- [ ] New code covered by ≥1 test citing REQ-ID/D-ID with `file:line` evidence (seed E.2 + D-006)
- [ ] **Every acceptance criterion the slice touched has a citing test; a reported symptom was reproduced with a failing test before the fix (red→green)**
- [ ] **Each external integration uses the one canonical mock/fake-client + has a contract test against the real API** — no bespoke per-test stubs; parallel mocks consolidated (`/wiring-an-integration`)
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

### B.0 — Every wave was closed (Stage 3)

- [ ] Each implementing agent ran a per-agent **dev-test loop** on its slice (implement → write/run tests → self-review → fix)
- [ ] Every wave was closed by `/close-wave`: **Code-Reviewer** (`docs/reviews/m{N}-wave-{W}-review.md`) **then Tester** (`docs/reviews/m{N}-wave-{W}-tester.md`), two separate fresh-eyes subagents that never wrote the wave's code, each verdict declaring `**Independent:** yes`; every acceptance criterion the wave touched has a passing citing test
- [ ] Every wave has its committed wave-close checklist (`docs/plans/m{N}-wave-{W}-close.md` from `docs/wave-checklist.template.md`) and `make wave-check` is green on it; skips and bypasses are rows in `docs/control-events.csv`
- [ ] Every wave's BLOCKING findings were fixed before it closed, and every MINOR/K.9/risk finding is in its checklist's findings table — fixed, filed as an issue, or refused with a reason; each wave's risk tier recorded in the plan (HIGH waves also had a security pass on the slice)
- [ ] `/repo-review` ran across the **whole milestone** (`git diff <base of the first wave>...<default branch>`) and wrote `docs/reviews/m{N}-repo-review.md`: what no single wave could see — one fact changed in one wave and not in another, documentation drift, a rule applied in one wave and not the next. Each finding fixed (a PR) or filed with `/file-issue`, none left in the file alone
- [ ] Every wave's draft PR was reviewed and merged by a human

### B.1 — Quality Gate (Stage 4.1) — OPTIONAL, off by default

> Only if the owner turned it on in the project brief. Off: skip to B.2 — the per-wave Tester already
> requires a citing test for every criterion a wave touched. On: every box below, plus the owner
> review pack `docs/closure-report-m{N}.md`, which `make closes` grades inside `make check` and CI.

- [ ] Done Evidence assembly: combine each wave's Done Evidence block into the milestone log
- [ ] REQ-ID coverage trace: every REQ-ID has ≥1 test citing it (write `docs/coverage-by-req.md`)
- [ ] **EVERY acceptance criterion has a citing test, and any reported symptom was reproduced with a failing test before its fix (red→green).** A criterion without a citing test → the milestone does NOT close.
- [ ] Coverage delta on new/modified code
- [ ] Strict mypy clean across all modules
- [ ] Strict ruff clean across all modules
- [ ] LOC budget: cumulative milestone LOC reasonable (no surprise bloat)
- [ ] Write `docs/cost-log.md` entry (token spend vs Stage 1 estimate)
- [ ] `docs/closure-report-m{N}.md` filled from raw referents (criteria table, annotated commits, telemetry, ledgers) with its §6 architecture-delta prose, and `make closure-check FILE=docs/closure-report-m{N}.md` green — **BLOCKING if the agent cannot explain what shipped**
- [ ] Trust-telemetry rows computed from git against the protected closure tag and appended to `docs/cost-log.md`
- [ ] Criteria diffs since plan approval rendered in the report; the OWNER ran the milestone session personally — his own `make test` + smoke tests + checks, per-wave diff review via the report's per-wave table — and signed off
- [ ] **If BLOCKING per the D-006 taxonomy → the milestone DOES NOT close.** Dispatch a mini-fix wave, return to B.1.

### B.2 — Capture (Stage 4.2)

- [ ] Append `process-log.md` S{N} entry (G.1; 3-10 lines; ends with `Lesson:` tag)
- [ ] Add any new ADRs via the `/log-decision` skill
- [ ] List proposed seeds → owner approves → add its row to `.agents/rules/playbook-seeds.md`
- [ ] `docs/EXPERIENCE.md` has a dated entry for THIS milestone (from `docs/EXPERIENCE.template.md`; no secrets/PII; findings cite evidence)
- [ ] `git log` shows no `spike-*` merged into mainline; spike branches deleted at close (secrets scanning ran on spikes too)
- [ ] Every slice reached the protected branch as a pull request a human merged — not as a direct commit
- [ ] Snapshot roadmap: `docs/roadmap-{YYYY-MM-DD}-post-m{N}.md` (seed I.1; never edit prior)
- [ ] AGENTS.md diet check: `wc -l AGENTS.md` within its 150-line hard cap (D-003; `make gate` fails over it); if it nears the cap, extract to `.agents/rules/`

### B.3 — Pipeline readiness audit (only at milestone N-2 from final)

If the project's final milestone count is known (e.g., M9 closes), at M(N-2) run:
- [ ] Write `docs/pipeline-readiness-audit.md` — every required-for-deploy artifact marked PRESENT / PARTIAL / MISSING
- [ ] Plan how to convert PARTIAL/MISSING to PRESENT before the final milestone

---

## §E — Stage 5: Release (once, when the work is done)

Runs once, after the final milestone closes, or at a release the owner calls: E.1 → E.2 → E.3.

### E.1 — Security review (Stage 5.1) — BLOCKING, before any deploy

Runs once, on the whole release, before anything deploys. A fresh-eyes subagent from `.claude/agents/Security-Reviewer.md` writes its verdict to `docs/reviews/release-security.md`. **It must PASS before any E.2 step.**

- [ ] Secret scan green across all waves (gitleaks in CI and in `make gate`); no `.env`/secret committed
- [ ] Dependency hygiene: every new dep exists on PyPI and its first release is ≥ 90 days old (`make slopsquat`) + pip-audit clean
- [ ] **Web/API security baseline (`docs/security-baseline.md`):** no plaintext creds / no default-admin; server-side authz on every mutating route; CORS allowlist, not allow-all + credentials; security-critical config validated at startup, fails prod; creds/PII encrypted at rest, rotation-friendly key chain; generic client errors
- [ ] Control-class fail direction: auth/safety fail CLOSED (tested disable switch + correct scope); fairness/rate-limit fail OPEN
- [ ] External-surface defaults: new endpoints default-deny; RLS/authz at every boundary
- [ ] Prompt-injection hygiene (MEDIUM+); auth/PII/payment/migration senior human review trigger fired (HIGH); SAST (MEDIUM+); PII redaction at log boundaries
- [ ] The release's security-invariants list is current — every invariant cites the NEGATIVE test that fails if it is removed (deny-path release; credential-derived tenant, never request params [IDOR]; redaction asserts ABSENCE in the actual sink)
- [ ] Every guard/limit/enforcement component in the release is WIRED — reachable from the live request path, proven by an end-to-end citing test ("built ≠ wired")
- [ ] **Only if the project handles money:** integer minor units + currency end-to-end; Money type rejects float; float sweep of money modules clean
- [ ] **Skip ledger:** every check that legitimately did NOT run for this release (contract-test self-skips, N/A rows) is a row in `docs/control-events.csv` with its reason — silent non-execution is indistinguishable from PASS
- [ ] **Verdict PASS** → proceed to E.2. **BLOCKING → nothing deploys.**

### E.2 — Deploy + go-live readiness (Stage 5.2)

> **Precondition: E.1 is PASS.** Run `/going-live`; it walks the rows below.

**A. Which code is live (L.7):**
- [ ] The deploy references a NEW image tag / git SHA (not a cached one) — confirm the build actually rebuilt
- [ ] `curl <target>/health | jq .build` equals the tag/SHA you intended to ship (L.7); if not, the old image is still running — fix the build pipeline, do NOT just restart the pod (restart != rebuild != re-pull)
- [ ] DevOps-owned build/deploy files (`Dockerfile`, `/deploy/**`, CI config) were not clobbered by the release's merges (CODEOWNERS should have flagged it; K.10)
- [ ] `/health` still returns `{status, version, build}` and the liveness contract is unchanged (additive fields only)

**B. Is the pipe actually working — go-live readiness:**
- [ ] L.8 dependency liveness: `make smoke-deps` — invoked EACH external dependency once for real (model / queue / store / callback) and inspected the RESULT, not the config screen (configured != working). `binds: <the dependency endpoints the RUNNING process resolves, not the ones in the repo's config>` — name them on the line
- [ ] L.9 config reaches the process: read each critical config value back from INSIDE the running process (in-pod env / safe echo: SET/EMPTY + length, never the value) — "set in the values file" != "set in the process"
- [ ] E.6 pipe attribution: one real request confirmed in the downstream's own run log, attributed to this service (proves auth + connectivity + routing; isolates any blocker to its node)
- [ ] `make cold-start` green — one boot against ZERO persisted state, **through the deployment's actual mechanism** (fresh volume / fresh container / the real image), never a repo-local approximation. `binds: <the artefact the deployment consumes>` — name it on the line. **FAILS CLOSED.** It catches a readiness probe on a DB-free path reporting Ready against a dead database, and an unlocked migration racing on first boot.
- [ ] Human-path done — a named person who did NOT build it, using only shipped docs, obtained a credential and made an authorized call
- [ ] `make journey URL=<deployed>` green — **one recorded walkthrough at human speed**: cold entry · credential lifecycle · paying-customer round trip asserting CONTENT · one cross-wave sequence. `binds: <the deployed URL / artefact>` — name it on the line. **FAILS CLOSED.** It catches what only the deployed artefact shows: an ingress misroute, a page that answers 500, a placeholder username, stripped security headers.
- [ ] Provisioning-ownership table current — every boot prerequisite is IN THE IMAGE or a named-owned row; no third category

**How `cold-start` and `journey` fail, and the only two ways to skip them.** Unfilled is FAIL: both
targets refuse until the project writes the script each one runs. The two legitimate outs are
written down, never left blank:

- **Ledgered waiver.** A row in `docs/control-events.csv` (`wave: release`, `kind: skip` or `bypass`)
  with its reason. The same control waived three times puts the CONTROL under review, not the person.
- **Written N/A.** Only when the release ships **no runnable surface at all** — no deploy, no artefact
  a human could enter. The N/A is a `skip` row in `docs/control-events.csv` with that sentence. A
  release that deploys anything has a runnable surface, and "we did not have time to stand it up" is a
  waiver, not an N/A. Refusing a gate for good goes in `docs/refusals.md`.

**`binds:` — a deployment-facing gate names the artefact it reads.** Every `make` row in this section
carries a `binds:` declaration naming what it inspects and whether that is **what the deployment
actually consumes**; `conformance/test-binds-declared.py` (a leg of `make gate`) refuses a row without
one.

- A green gate bound to an artefact the cluster does not run is **NOT-BINDING** — a green check against
  a manifest nobody deployed proves nothing about the deployment.
- **"The deployed artefact is not in any readable repository" is BLOCKING.** Not a warning, not an
  N/A: if nothing readable describes what is running, the gate has nothing to bind to and the release
  does not go live.

### E.3 — Retrospective (Stage 5.3) — OPTIONAL, once

- [ ] If the owner wants one: `/cycle-close` writes `docs/retrospective.md` — what we did right, where we got stuck, which controls earned their place (retire what never fired; record it in `docs/watchlist.md`)
- [ ] Final roadmap snapshot (e.g., `roadmap-final-phase{N}.md`)

## §D — Stage 6: Maintenance loop (post-deploy fix waves)

Per FIX WAVE: the normal wave close applies (`/close-wave`, §B.0) + red-test intake.
Per FIXPACK (the deploy gate — walk `docs/fixpack.template.md`):

- [ ] Every fix row complete (bug ref · red test · commit · CR + Tester verdicts · gate-attribution lesson)
- [ ] Security floor: gitleaks/SCA · full invariant suite GREEN · diff-scoped read · ⛔ auto-escalation honored
- [ ] Full regression GREEN once on the exact final bundled build
- [ ] **Owner out-of-sandbox verification signed** (reproduce pre-fix → gone post-fix → local tests) — BLOCKING
- [ ] Deploy: the E.2 gates + fix probe in prod + watch window clean
- [ ] Capture coupling: lesson lines appended to EXPERIENCE.md (deploy condition) · 3-strikes + N=3 checks run
- [ ] Emergency pack? "why now" line present + 48h retroactive close scheduled

## Before you relax anything: the backtest rule

**A proposal to relax a gate, a bar or a review depth — and removing a control is relaxing it to
zero — must carry a backtest against the previous milestone's REAL defect list, naming which defects
would have passed.** No backtest, no relaxation.

**The threshold:** removing **five or more controls in one change** requires a written backtest
artefact linked from the PR; below five, a named judgement in the PR suffices. Nothing executes this
rule: the human who merges the change asks for the backtest.

Why: a relaxation that feels necessary is often aimed at the wrong cost. A proposed severity bar,
applied backwards to one milestone's real defects, let only a small fraction through and would not
have shortened the milestone at all — the time had gone to a review loop and to controls that were
never installed. **A relaxation proposal without a backtest is a feeling, not a measurement.**
