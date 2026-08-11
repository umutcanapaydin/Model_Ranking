# START HERE — Fresh Agent Orientation (Pipeline v4.2)

> If a user just pointed you at this repo and said "this is our general pipeline, read it," you're in the right place. (Owner: your paste-ready kickoff prompts live in `Project_Implementation_Prompt.md` — new-project and mid-project variants with the echo-back gate.) This file is your 5-minute orientation. `pipeline-design.md` (~900 lines) is the 40-minute reference; **`pipeline-architecture.html` is the Architecture & Technical Design Document** — components, interfaces, enforcement tiers, trust boundaries, data model and traceability, for when you need to know *how the machine is built* rather than *what to do*; read this file first. New in v3 (a clean superset of v2.2): 2 gates (a web/API security baseline in `make bootstrap-check` + every acceptance criterion has a citing test), the V3C-68 review-loop restructure (per-wave Code + Tester with a per-agent dev-test loop; Security review moves to milestone closure, BLOCKING before deploy), `docs/security-baseline.md`, safety/build guardrails, and a CANDIDATE Agent-Native / LLM-Ops theme — see §0 changelog in the design doc. **v3.1 adds:** wave-close checklists you fill and commit (`docs/wave-checklist.template.md`, `make wave-check`), a living `docs/EXPERIENCE.md` (BLOCKING at quarterly handover), risk-tiered review depth (P-005), and the Tester fault-injection protocol. **v4.2 adds (the audit turned on its author):** two guardrails and six repairs, every one found by a reviewer reading code rather than prose — **V4C-49** ship the grep gate in the same change that writes the rule, and replay the last N harvest rules against each NEW standalone artifact (a lesson does not travel between artifacts by itself); **V4C-50** a fix inherits the risk class of the bug it fixes, and every load-bearing path needs one test **through the real entry point** — a suite that bypasses the layer where the bug lives is correctly green and completely uninformative. Repairs: `C1a`/`C1b` catch a condition whose promised artifact never arrived (the check whose absence let two of our own conditions lapse silently); `--self-test` can now actually reach `P2`/`P3`; the duplicate-record check was dead code and now fires; `sec_pat2` in `bootstrap-check.sh` had been written down but never connected to `grep` for eight cuts. **The largest defect in this cut was the chair's own filing** — a document claiming a check was installed when it was still a paragraph, caught by all six seats independently and recorded as `TB-008` in `council-telemetry.md`. Doctrine added: **a control nobody has watched fail is a rumour — including the one you wrote this morning.** **v4.1 added (repair + records-as-data):** the dead controls are fixed and now FAIL LOUDLY when unwired (`check-templates` was a syntax error that never ran; `journey`'s script did not exist) · `make check-records` + `make check-records-selftest` validate the governance records themselves · `governance-contract` is the FIRST GATE (one unconditional required check) · `docs/refusals.md` records what we have decided NOT to build. Doctrine: **a declared control that silently passes is worse than an absent one.** **v4.0 (MAJOR, market-informed) adds:** the base-pinned policy invariant (reviewers/gates read policy ONLY from the protected base ref — never from the change under review), advisory mutation kill-rate + cross-model review at HIGH tier, the journey script running on a SCHEDULE after deploy, friction telemetry (bypassed controls are recorded findings; same control bypassed 3× → review the control), and named version semantics — see §0. **v3.5 adds outward-facing checks (post-prod dataset):** `make check-templates` + `make cold-start` + `make journey URL=…` + human-path criterion — the gates now test the SHIPPED artifact against the real world, not the repo against imagination. **v3.4 adds Stage 5 (OD-6):** post-deploy bugs = fix waves (red-test intake) shipping via the fixpack deploy gate with the owner's out-of-sandbox verification — see `docs/fixpack.template.md`. **v3.3 mode: A0.5 (OD-4)** — waves close AGENT-side; the owner reviews/tests/commits at MILESTONE boundaries (escalate-NOW list in AGENTS.md §3 halts mid-wave; owner checkpoint commits per wave). A1/A2 in `docs/autonomy-protocol.md` stay NOT active. **v3.2 added:** the owner review pack generated at every closure (`docs/closure-report.template.md`), trust telemetry, the read-only Explorer profile for all repo exploration, and the `spike-*` L0 lane. **Before code: write the design notes + a short gap-analysis (what exists vs what to build) — V3C-50.**

---

## What you're looking at

This is a **vibe-engineering starter package** distilled from a real 9-milestone customer project (EF-AI — Emirates Foundation AI Financial Education Platform) and merged with the AI-native Claude Code harness pattern via a 6-agent consortium deliberation on 2026-06-02.

It is opinionated by design. The opinions come from measurement (N=9 milestones, 301 tests, 4 G.12 retrospectives, 64 playbook seeds) plus industry research consensus.

---

## Your first question (ask the user)

> "Are we bootstrapping a brand new project from this starter, or are we resuming a project that already uses this pipeline?"

- **Brand new project** → walk Stage 0 (Bootstrap) with the user. Start with §"Day-0" in `pipeline-design.md` §12.
- **Resuming** → read `docs/process-log.md` latest entry, latest `docs/plans/m{N}-plan.md`, latest `docs/retrospectives/m{N}-retrospective.md`. Resume at the relevant Stage.

Do not start coding before you've asked this.

### ★ For brand-new projects: ask for the Project Brief

If the user is starting a brand-new project, ask: *"Do you have a filled-in Project Brief?"*

The template lives at `docs/project-brief.template.md`. A filled brief covers: customer business context, stack, HIGH-risk paths inventory, senior human reviewer name, external dependencies, pipeline opt-in choices, budget + cadence, greenfield-vs-migration, M1 expectations. Saves ~30-40 minutes of Stage 0 back-and-forth.

If they have it: read it before the PRD. If they don't: walk them through filling it out before drafting `m1-plan.md`. The brief §10 contracts what you must deliver before any wave dispatches.

---

## 30-second mental model

Two layers:

1. **Layer 1 — Starter Package** (~60 files in this repo) — pre-filled scaffolding from Phase-1 + AI-native harness.
2. **Layer 2 — Workflow** (5 stages):
   ```
   Stage 0 — Bootstrap  (once per project)
   Stage 1 — Milestone Plan  (per milestone; design notes + gap-analysis first, V3C-50)
   ┌─ Stage 2 — Wave Execution  (parallel subagents + commit-gate hooks + per-agent dev-test loop)
   │  Stage 3 — Per-Wave Review  (Code Review + Tester, fresh-eyes; V3C-68)
   └─ loop until all waves done
   Stage 4 — Milestone Closure  (Security review BLOCKING before deploy + Quality Gate + Capture + Handoff)
   ```

You'll spend most of your time in Stages 2-4. Stage 0 happens once per project.

Open `pipeline-schema.html` in a browser for the visual.

---

## 5 things to know before touching anything

1. **`AGENTS.md` (≤80 lines target, ≤150 hard cap) is canonical.** `CLAUDE.md` is a symlink to it. Industry standard (60k+ public repos use AGENTS.md). Both names work; same file.

2. **`permission-matrix.md` is default-deny.** §11 has the BLOCKING taxonomy locked in writing. **PASS verdicts without `file:line` evidence are automatic BLOCKING.** No false-pass surface.

3. **The user is the milestone-plan authority.** You can dispatch waves only AFTER the user signs off on `docs/plans/m{N}-plan.md` §13 dispatch checklist. Agent opens drafts; human approves.

4. **Fresh-eyes review profiles are MANDATORY (K.7 — you do not review your own code).** v3 (V3C-68): the **per-wave** gate is **Code-Reviewer + Tester** (`subagent-profiles/`, via `/review` + the Tester profile); the **Security-Reviewer** runs once at **milestone closure and is BLOCKING before deploy** (via `/security-review`). Each implementing agent also runs a dev-test loop on its own slice during the wave.

5. **Quality Gate runs at MILESTONE CLOSURE (Stage 4.1), not per-wave.** Per-wave is Code Review + Tester only. Quality picks up REQ-trace + coverage + Done Evidence at the milestone boundary; **every acceptance criterion must have a citing test (V3C-02, gate-BLOCKING)**, and the closure Security review (Stage 4.0) must pass before any deploy.

---

## Calibration — what's MEASURED vs INHERITED

This matters because not every part of the pipeline has equal evidence weight. Calibrate accordingly:

**MEASURED in Phase-1 (N=9 milestones, direct observation):**
- K.4 parallel subagent dispatch → 4-6x wall-clock speedup
- K.5 drift-guard pattern → caught issues every milestone M6-M9
- K.7 fresh-eyes review → BLOCKING catches at every milestone where it ran
- K.8 contract lock + grep-verify → zero cross-subagent contract drift
- G.12 retrospective → hypothesis-confirmed twice (K.8 M7→M8, K.7-MINOR M8→M9)
- AGENTS.md diet (250 → 218 → 170 lines) → measurably improved task success

**INHERITED from industry research (Phase-1 didn't exercise these directly):**
- Veracode 45% AI-code OWASP findings → security gates (gitleaks, pip-audit, SAST)
- Lovable CVE-2025-48757 (May 2025) → default-deny external surfaces
- Replit DB-deletion (July 2025) → no LLM-revert / no force-push (catastrophe-class)
- METR -19% slowdown on mature codebases → context discipline + AGENTS.md diet
- ETH Zurich AGENTbench → AGENTS.md ≤80 ideal (LLM-generated context >200 lines lowers task success)

**Implication:** if you're working in a domain Phase-1 never exercised (auth, PII, payment, compliance), the security gates are hypotheses to validate in YOUR project — capture results in milestone retrospect. If you're in a domain Phase-1 measured (subagent dispatch, contract lock, retrospective format), trust the pattern.

---

## Cowork-blocked files (one-time footgun if this was generated by Cowork)

If this folder was produced by a Cowork session, three files COULD NOT be written during generation:
- `.claude/settings.json` — content at `docs/claude-harness-config.md` "File 1"
- `.mcp.json` — content at `mcp.json.template` (also in `docs/claude-harness-config.md` "File 2")
- `.claude/skills/<10 skills>/SKILL.md` — content at `docs/claude-skills-content.md`

The user must manually create these once. If `.claude/` directory is empty or missing, walk the user through `docs/claude-harness-config.md` steps. This is a Day-0 task, done once per project.

Once created: `.claude/settings.json` enables 2 baseline hooks (PreToolUse block .env writes + PostToolUse make check). Without them, the Stage 2 commit-gate runs in honor mode (less safe).

**Commit `.gitignore` first (V3C-27 — bootstrap hygiene):** before the first real commit, make sure `.gitignore` is in place and committed, so the venv, caches, and the per-developer `environment.md` never get tracked. The starter ships a `.gitignore`; confirm it covers your stack before `git add -A`.

**Git in a Cowork mounted sandbox (seed C.12 / FB-3):** in a Cowork mounted folder, git CANNOT remove its own lock files (`.git/index.lock`, `HEAD.lock`) — EPERM — so the first commit succeeds but leaves stale locks that block the next commit with a confusing "another git process seems to be running." **Finish git host-side:** prefer running `git init` + commits from the user's real terminal; if you hit stale locks, clear them with `rm -f .git/*.lock .git/objects/maintenance.lock` (host-side) and retry.

---

## The routing index (V3C-52 — token economy)

`AGENTS.md` is thin on purpose; its §8 "Detail docs" block is the **routing index** — it points you to the right `.agents/rules/*.md` or `docs/*.md` for the task at hand. Read the pointer, then **lazily load only the doc you need** (don't pull every rule file into context). Two external gateway projects independently re-derived this exact pattern, validating GP's own design. The read-order list below is that index for a fresh agent.

## Files to read in order (after this one)

1. **`AGENTS.md`** (≤80 lines) — house rules
2. **`permission-matrix.md`** — what you may/may not do + BLOCKING taxonomy §11
3. **`docs/decisions.md`** — D-001..D-007 universal + P-001 process ADRs (your project starts at D-100; seed B.6)
4. **`.agents/rules/practices.md`** — engineering practices
5. **`pipeline-design.md`** — full spec (~900 lines; reference, not linear read)
6. **`.agents/rules/playbook-seeds.md`** — 64 + 8 seeds (search-as-needed)
7. **`docs/onboarding.md`** — Pazartesi-başla / Cuma-milestone-bitir rehberi (Monday-to-Friday playbook)
8. **`docs/tool-suitability.md`** — what tasks fit AI agents (Strong / Medium / Weak fit)

---

## Catastrophe-class anti-patterns (DENY always, ADR cannot override)

Per `permission-matrix.md` §11:

- ❌ `git reset --hard` / `git push --force` / `git checkout --` (Replit DB-deletion class)
- ❌ `rm -rf` on untracked directories
- ❌ `DROP TABLE` / destructive DB op in production
- ❌ Commit `.env` / API key / secret to git
- ❌ Log customer PII without redaction
- ❌ Self-merge your own PR (humans only; branch protection enforces)

If you find yourself about to do any of these, STOP and ask the user.

---

## When to ask the user vs proceed

**Ask the user (proposer/approver pattern):**
- Before dispatching any Wave (Stage 2 K.4 wave or `/fix-issue-implement`)
- Before adding a new dependency to `pyproject.toml`
- Before editing AGENTS.md UNIVERSAL section
- Before editing `permission-matrix.md` (requires ADR)
- Before merging a PR (agent opens drafts only)
- When in doubt about BLOCKING vs MINOR classification

**Proceed without asking (already authorized):**
- Reading any file in the repo
- Running `make check`, `make standup`, `make test`
- Drafting plans / ADRs / retrospectives (status: proposed; user approves to accept)
- Writing tests for behavior already in the code
- Refactoring within a module if `make check` stays green

---

## Common first-session pitfalls

1. **Skipping the user's "brand new vs resuming" question.** Determines which stage you start at.
2. **Reading `pipeline-design.md` linearly first.** It's 900 lines; read this orientation + AGENTS.md instead. Reference v2-design as needed.
3. **Assuming hooks are active when `.claude/settings.json` is missing.** Verify with `cat .claude/settings.json` before trusting the commit-gate.
4. **Dispatching a wave before Q1-Q4 in the milestone plan are locked.** Plan §13 sign-off is your gate.
5. **Confusing "Quality Gate" (Stage 4.1, milestone closure) with per-PR CI.** They're complementary, not duplicate.

---

## What this pipeline is NOT

- ❌ A finished product. v2.2 has known gaps documented in `pipeline-design.md` §15 (several narrowed/closed across v2.1 + v2.2).
- ❌ A replacement for human judgment in HIGH-risk paths (auth / PII / payment / migration).
- ❌ A guarantee. Calibration matters (see "Measured vs Inherited" above).
- ❌ Frozen. New milestones that learn something propose seeds back; v3 incorporates them.

---

## Welcome

The pipeline is meant to compound. Each milestone you run with this pipeline adds measurement; the retrospective format turns that measurement into seeds; seeds get audited at quarterly handovers (`/quarterly-handover` skill).

Read `AGENTS.md` next. Then walk Stage 0 (if brand new) or resume at the relevant Stage (if continuing).

Ask the user good questions. Propose; let them approve. Don't run before they nod.

— Pipeline v3.5 increment · 2026-07-27 (v3.4 · 2026-07-17; v3.3 · 2026-07-05; v3.2 · 2026-07-03; v3.1 · 2026-07-03; v3 · 2026-06-26; v2.2 · 2026-06-19; v2.1 · 2026-06-12; baseline v2.0 · 2026-06-02)
