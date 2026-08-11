# HANDOVER — Material for cutting Pipeline v2.1

> **Read this if you are a fresh session whose job is to produce Pipeline v2.1.**
> Written 2026-06-11 at the end of the session that ran EF-AI **M12** (production
> hardening) + the **S34** first-prod-deploy follow-on. Those two events are the
> raw material for v2.1. This file is self-contained: you do not need the prior
> session's memory, but you DO have read access to the EF-AI project repo (the
> live case study) at `~/Desktop/ef_ai_vibe` for evidence/citations.
>
> Current framework version: **v2.0** (see `pipeline-v2-design.md`). Your task is
> a **v2.1 increment**, not a rewrite. Promote what's proven, graduate the right
> candidates, keep the anti-bloat discipline (retire as you add).

---

## 0. How to use this file

1. Read `pipeline-v2-design.md` (the current v2.0 design) + `START_HERE.md`.
2. Read `.agents/rules/playbook-seeds.md` — the seeds below are **already written
   into it** this session; your job is to PROMOTE the proven ones into the design
   doc + templates, not re-derive them.
3. Read the EF-AI evidence (optional but recommended): `~/Desktop/ef_ai_vibe/docs/m12-retrospective.md`, `docs/process-log.md` (S32–S34), `docs/reviews/m12-review-{code,security}.md`.
4. Run a Stage-1 plan for "v2.1 cut", decide each candidate with the user, then
   edit `pipeline-v2-design.md` → v2.1, bump version + add a short changelog.

---

## 1. The two events that generated this material

### Event 1 — EF-AI M12: durable-delivery / multi-node hardening milestone
Made an async-callback adapter correct under multiple replicas + rolling deploys
(Redis idempotency with atomic `SET NX`, durable dispatch queue, recovery worker,
SIGTERM drain, readiness/liveness split, backpressure). **Headline:** the K.7
fresh-eyes Code-Reviewer returned its **first-ever BLOCKING on the project, and it
was correct on a defect the author's own green tests masked** — the "durable"
enqueue ran in a fire-and-forget task scheduled *after* the sync ack, so durability
was illusory (commit-after-ack loses the message). Also caught: a `requeue` LREM
bug that grew a duplicate per retry, and **missing hard-acceptance tests because a
Wave-1 subagent died before writing them** (code landed, proof didn't). All fixed
same session. Evidence: `ef_ai_vibe/docs/m12-retrospective.md`.

### Event 2 — S34: first prod deploy of the M12 image (the "is it even live?" hour)
After pushing M12, the running pod was STILL the old version behind a green
`/health`. Root causes, both generalizable:
- A **feature merge clobbered DevOps's `Dockerfile`** customizations on master, so
  CI never rebuilt the expected image (cross-team file-ownership collision).
- **A pod restart ≠ a rebuild/redeploy** — restarting re-runs whatever image the
  deployment already references; it does not pull new code. Diagnosing it took
  three exec-and-grep checks because `/health` had no version stamp.
Fixes shipped: a `/health` **build stamp** (`APP_BUILD` env → `{version,build}`),
a root **`CODEOWNERS`** marking DevOps-owned build/deploy files, and AGENTS.md +
deploy-README ownership notes.

---

## 2. What was ALREADY added to v2.0 this session (do not duplicate)

These are **already in `.agents/rules/playbook-seeds.md`** (and mirrored in
`practices.md`). v2.1's job is to decide which graduate into the **design doc +
AGENTS.template + Stage checklists**, not to re-author the seeds.

**New Theme L — Distributed correctness, durability & multi-node safety:**
- **L.1** Commit the durable record BEFORE you return the ack (enqueue-then-ack).
- **L.2** Release what you reserved when you reject (idempotency-slot rollback).
- **L.3** Promise at-least-once with a stable idempotency key, never exactly-once.
- **L.4** Cross-node election is one atomic op (`SET NX`), never check-then-act.
- **L.5** Bound the durable queue + load-shed (backpressure); soft bound only rejects, never drops.
- **L.6** The process can't know its replica count → scale-out preconditions are a boot guard + fail-fast config-doctor.
- **L.7** Version-stamp the health/readiness probe (graduated the long-standing S28 candidate).

**Theme extensions:**
- **E.5** Acceptance-criterion tests ship in the same wave as the feature; verify they exist on subagent death.
- **C.10** When the sandbox runtime lags the target, shim the version-only-missing names and run the FULL gate.
- **K.10** DevOps-customized files in a shared repo are a contract surface; mark the boundary (CODEOWNERS) or a feature merge will clobber them.

---

## 3. v2.1 candidate changes (the actual decisions to make)

### A. Graduate / re-evaluate existing CANDIDATE seeds (per the graduation rule)
- **L.7 version-stamped probe** — already promoted from candidate to ACTIVE this
  session (S28→S34). **v2.1 question:** make it a **Day-1 baseline** (like C.1
  day-1 green) — i.e., the project-brief/bootstrap template ships `APP_BUILD` in
  the Dockerfile + a `{version,build}` health body from the first commit?
- **L' specialised subagent profiles** — still CANDIDATE. M12 added a *third lens*
  informally (the "council" — see B). Decide whether council/extra profiles graduate.
- **E.4 TDD-with-AI** — M12 gave a sharp data point FOR it (the dead-subagent test
  gap, E.5): tests written in the same wave as code would have closed it. Consider
  promoting E.4 from CANDIDATE → ACTIVE, scoped to "new module + locked contract."
- **F.5 SAST** — unchanged; still risk-tiered candidate.

### B. New disciplines observed — decide promote / watch / drop
- **Council planning (multi-role adversarial Stage-1)** — PM + QM + Senior + DevOps
  voices voted the M12 plan; a non-voting chair represented the user. It caught a
  *scope-level* gap (durable delivery, not just Redis idempotency) the single-author
  plan missed. **Verdict so far: PULLED-WEIGHT but TOO-EARLY (N=1).** v2.1 option:
  add it as an **optional Stage-1 variant** for contested/MEDIUM+ milestones; full
  promotion after a 2nd payoff.
- **Config-doctor + scale-out boot guard (L.6)** — bought down a measured M11
  bring-up pain (one-crash-per-redeploy). v2.1 option: standard pattern for any
  service with required env / >1 replica; add to AGENTS.template + a Stage-0 seed.
- **Cross-team file ownership / CODEOWNERS (K.10)** — v2.1 option: ship a baseline
  `CODEOWNERS` in Stage-0 bootstrap whenever app + DevOps share a repo.
- **Subagent-death test-gap drill (E.5)** — v2.1 option: add an explicit controller
  step to Stage-2/closure: "after any subagent death, grep that each acceptance
  criterion has its citing test." (death-tolerance for code ≠ for proof.)
- **Sandbox runtime-shim full gate (C.10)** — fold into the C.7 sandbox-as-canary
  guidance: when the sandbox runtime lags prod, shim the missing names and run the
  WHOLE suite, not a subset.
- **Deploy verification (restart ≠ rebuild)** — NEW gap v2.0 doesn't cover: Stage 4
  closes at "image built + Mac green" but has no **"is the new code actually live in
  the target?"** step. v2.1 option: add a **Stage 4.3 deploy-verification** sub-step
  — one curl to the version-stamped `/health` (L.7) confirming the deployed build ==
  the intended build; plus the checklist fact "a pod restart does not pull new code."
- **"Is anything left?" honest scope accounting** — when the user asks "is the patch
  complete?", enumerate open *code* items vs *ops* items explicitly rather than
  declaring done. M12's backpressure close-out came from this. Candidate for the
  Done-Evidence / closure narrative.
- **PM-status snapshot format** — the `ef_ai_vibe/docs/pm-status-2026-06-11.md`
  table (✅/🟡/⛔, plain language, "what's there / what's missing", external blocker
  called out) worked well. Candidate for a `/pm-status` skill or a template (pairs
  with G.9 PM-friendly risk register).

### C. Retirement review (anti-bloat)
- **0 disciplines retired** in the M12/S34 cycle — all fired pulled weight or are
  too early to judge. v2.1 should still run the retirement pass: anything in v2.0
  not fired across M10–M12 is a retirement candidate.

---

## 4. Where the evidence lives (for citations in the v2.1 cut)

- `~/Desktop/ef_ai_vibe/docs/m12-retrospective.md` — G.12 N=6, per-discipline verdicts.
- `~/Desktop/ef_ai_vibe/docs/process-log.md` — S32 (M12 build), S33 (backpressure close-out), S34 (deploy + build-stamp + CODEOWNERS).
- `~/Desktop/ef_ai_vibe/docs/reviews/m12-review-code.md` — the BLOCKING verdict + remediation addendum.
- `~/Desktop/ef_ai_vibe/docs/decisions.md` — D-043 (at-least-once), D-044 (Redis topology/atomic NX/boot guard).
- `~/Desktop/ef_ai_vibe/CODEOWNERS`, `deploy/cce/README.md`, `AGENTS.md §8` — the K.10 / ownership artifacts.
- `~/Desktop/ef_ai_vibe/src/ef_ai/adapter/{main.py(/health stamp, /ready, config_doctor wiring),config_doctor.py}`, `workers/dispatch_queue.py`, `workers/dispatch_worker.py`, `clients/task_status.py` — the L.* reference implementations.
- THIS folder: `.agents/rules/playbook-seeds.md` (Theme L + E.5/C.10/K.10/L.7), `practices.md` (narrative subset).

---

## 5. Suggested method for the v2.1 session

1. Stage-1 plan: list each candidate from §3 with a promote / watch / drop recommendation.
2. Get the user's decisions (this is a framework cut — the user is the product owner).
3. Edit `pipeline-v2-design.md`: add a **§ Production-hardening (Theme L)** block,
   a **Stage 4.3 deploy-verification** sub-step, and any promoted disciplines.
   Bump the header to **v2.1** + add a one-screen changelog (what changed vs v2.0).
4. Update `AGENTS.md` (the UNIVERSAL template part) + `docs/project-brief.template.md`
   + Stage-0 bootstrap if you make CODEOWNERS / version-stamp Day-1 baselines.
5. Update `.agents/rules/practices.md` "See also" + any new consolidated rules.
6. Keep seeds append-only; do NOT edit historical seeds (supersede per B.2).
7. Run the retirement pass (§3.C).

---

## 6. Open questions for the user (decide during the v2.1 cut)

1. Is **version-stamped /health (L.7)** a Day-1 baseline, or opt-in per service?
2. Does **council planning** graduate to an optional Stage-1 variant now, or wait for a 2nd payoff?
3. Should **CODEOWNERS** ship in Stage-0 bootstrap by default (app+DevOps shared repos)?
4. Promote **E.4 TDD-with-AI** to ACTIVE (scoped), given the E.5 dead-subagent evidence?
5. Add a **Stage 4.3 deploy-verification** sub-step (the restart≠rebuild gap)? (Strong recommend: yes.)
6. Turn the **PM-status snapshot** into a `/pm-status` skill/template?

---

## 7. Do-not-lose summary (if you read nothing else)

- v2.1 is an **increment** over v2.0; promote proven material, don't rewrite.
- The seeds are **already captured**; the work is promoting them into the design +
  templates + Stage checklists, plus deciding the candidates in §3.
- The single biggest **new gap v2.0 missed**: a **deploy-verification step** — "code
  green + image built" is not "the new code is live in the target." Close it with the
  version-stamped probe (L.7) + a Stage 4.3 check + the "restart ≠ rebuild" fact.
- Keep the anti-bloat discipline: retire as you add; nothing was retired this cycle,
  so run that pass deliberately.
