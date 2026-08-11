# Pipeline v4.1 — Full Design

> **Version:** v4.1
> **Date:** 2026-07-30
> **Status:** Active baseline (increments v2.2; replaces v2.1/v1.1)
> **Audience:** Engineering teams adopting this starter package for any new LLM-powered project (greenfield or migration).
> **Authoring history:** Derived from EF-AI Phase-1 lived experience (9 milestones, 301 tests, playbook seeds across themes A-L, G.12 retrospectives) + the AI-native Claude Code harness model. v2.0 consortium-merged 2026-06-02; **v2.1 (2026-06-12)** added Theme L distributed-correctness + Stage 4.3 deploy-verification (EF-AI M12 + S34); **v2.2 (2026-06-19)** folded in feedback from two live projects (HCS-MaaS bootstrap + EF-AI S35) ratified by a 7-role blind council. **v3 increment (2026-06-26)** is a clean superset of v2.2: a cross-project harvest of 7 projects (Reimbursement-App, Poyraz-Dekorasyon, aop-portal, BotIm-AOP, aop_growth, HSC-MaaS, one-api), ratified by a 13-seat blind council. It adds 2 gates (web/API security baseline + tests-citing-each-criterion), a review-loop restructure (per-wave Code+Tester + per-agent dev-test loop; Security → milestone closure, BLOCKING before deploy), a concrete web/API security baseline, safety/build guardrails, the canonical-mock convention, and charters an **Agent-Native / LLM-Ops** theme as a CANDIDATE container. Evidence: `General_Pipeline/v3-ratification.md`, `General_Pipeline/v3-candidate-register.md`. **v3.1 increment (2026-07-03)** folds in the FIRST field run of v3 itself (hcs_maas_vib, 19 findings; all six v3-adopt validations confirmed) + two owner directives, ratified by an 11-seat blind council: executable wave-close checklists (V3C-69), a living per-project EXPERIENCE doc (V3C-81), risk-tiered review depth (V3C-78/P-005), the day-0 OSS license gate (V3C-70/71), Tester fault-injection (V3C-72), built≠wired + security-invariant negative tests (V3C-73/74), and the domain-scoped money rule (V3C-77). 0 new gates. Evidence: `General_Pipeline/v3.1-ratification.md`. **v3.2 increment (2026-07-03)** folds in the first fully EXTERNAL evidence class (a 9-doc agentic-engineering research curriculum, archived in `research/`) + owner directive OD-3, via a 2-phase council (6 core → 3 domain seats, chair-decided under owner delegation): the **autonomy ladder** as a recorded NORTH-STAR candidate (`docs/autonomy-protocol.md` — NOT active; A0/owner-in-the-loop is the only mode), the **owner review pack** (`docs/closure-report.template.md`), **trust telemetry**, the **Explorer** profile + context economy, AI-aware review smells, the declared L0 spike lane, and scoped plan interrogation. 0 new gates. Evidence: `General_Pipeline/v3.2-ratification.md`. **v3.3 increment (2026-07-05)** activates operating mode **A0.5** (owner directive OD-4, 7-seat chair-delegated council): waves close agent-side; the owner's review, personal test runs, and commits move to milestone cadence with checkpoint commits, an escalate-NOW list, milestone size caps, and an automatic reversion tripwire (PROVISIONAL). Evidence: `General_Pipeline/v3.3-ratification.md`. **v3.4 increment (2026-07-17)** adds
**Stage 5 — Maintenance Loop** (owner directive OD-6; 5-seat council): post-deploy bugs run as
fix WAVES through the existing wave machinery, close through a **fixpack** deploy gate with the
owner's out-of-sandbox verification, and every fix line feeds EXPERIENCE mechanically — the
standalone memory-based harvest is RETIRED. Evidence: `General_Pipeline/v3.4-ratification.md`.
**v3.5 increment (2026-07-27)** was cut on the first REAL post-production dataset (7 escaped
boundary defects, zero caught by gates) and answers with OUTWARD-FACING checks: boot-from-shipped-
template + cold-start, human-path criterion, producer enumeration, ready≠alive + diagnosable
fail-closed, and the black-box journey tester. Evidence: `General_Pipeline/v3.5-ratification.md`.
**v4.0 increment (2026-07-30, MAJOR)** is the first EXTERNALLY-INFORMED cut: three independent AI
market scans, cross-checked, confirmed GP's four core mechanics are market-empty and supplied the
absorb candidates — base-pinned policy invariant (constitution, both lanes), advisory mutation
kill-rate + cross-model review at HIGH, scheduled journey monitoring, friction/bypass telemetry,
named versioning semantics + propagation checklist, and upgraded council machinery (verdict set
with abstention, council pricing, council telemetry). 9-seat council; owner settled splits; 0 new
gates. Evidence: `General_Pipeline/v4.0-ratification.md`.
>
> **Architecture:** the structural specification — component catalog, enforcement tiers, trust
> boundaries, record data model, threat model and traceability — now lives in
> **`pipeline-architecture.html`** (ratified with v4.1). It supersedes the architectural parts of
> §2 and §11 here; those sections remain as the rule-level reference.
>
> **Read time:** ~40 minutes end-to-end. Skip ahead to §3 (workflow) and §12 (bootstrap recipe) if you only have 5. **New in v3: 2 gates (V3C-11 security baseline in `make bootstrap-check` + V3C-02 tests at the Quality Gate), the V3C-68 review-loop restructure, `docs/security-baseline.md`, the `Tester` subagent profile, control-class fail-direction + agent-least-privilege guardrails, and the Agent-Native / LLM-Ops candidate theme.** Full list in §0.

---


## §0 — Changelog

### v4.2 vs v4.1 (this increment — MINOR + a REPAIR cut, and the audit turned on its author)

v4.2 is a **clean superset** of v4.1. It carries **two adopted guardrails** and **six repairs**, and
the single most important fact about it is that **the chair's own filing was the largest defect
found.**

**WHAT HAPPENED.** The Increment-12 scoped council convened on two candidates. Before it sat, the
chair filed the two instruments the previous council's gate had demanded — `council-telemetry.md`
(V4C-25: trace an escaped defect back to the ruling that admitted it) and `friction-ledger.md`
(V4C-13: was a control ever skipped?) — 28 and 42 days ahead of their deadlines. The telemetry
document then stated, in the present tense, that a new check called **C1** *"is added to
`scripts/check_records.py`"*. **It was not. It was a paragraph.**

**All six seats found that sentence independently** — three by reading the 317-line file, one by
running the validator, one by importing `governed_records()` and observing that neither instrument
filed that day was even in its glob. It is Cluster A of the telemetry report's own taxonomy — *a
control ratified without a fixture proving it fires* — committed inside the document written to name
Cluster A. It is recorded as **TB-008**, and it is the largest single entry in the instrument.

**ADOPTED (2, both guardrail weight, both provisional until the 2026-09-16 pilot report):**
- **V4C-49** — mechanical rule installation: ship the grep gate in the same change that writes the
  rule; replay the last N harvest rules against each NEW standalone artifact rather than assuming a
  lesson travelled; any standalone tool goes to a zero-context external reviewer before its first
  customer-facing use. From field finding F45, N=2.
- **V4C-50** — a fix inherits the risk class of the bug it fixes: a concurrency fix is a concurrency
  change and takes harsher verification than the original defect. Every load-bearing path needs at
  least one test **through the real entry point** — a suite that bypasses the layer where the bug
  lives is correctly green and completely uninformative. From F44, severity CRITICAL.

**REPAIRS (six, every one found by a seat reading code, none by its author):**
- **C1a/C1b now exist as code** — a condition's closure artifact must be *nameable* (forward-only
  from v4.2), and a **due** condition whose named artifact is absent fails as `EVAPORATED`. This is
  the check whose absence let V4C-25 **and** V4C-12 lapse in silence. Two fail fixtures; falsified
  before shipping. Its first draft was circular and could never have fired.
- **`--self-test` could not reach P2 or P3** — `self_test()` never called `package_invariants()`, so
  the two rules the validator is actually credited with were unasserted regardless of fixture count.
  Now probed directly against a deliberately broken throwaway package.
- **R3's duplicate-id branch was dead code** — `collect()` keyed records by id, so two records
  sharing an id collapsed into one *before* the uniqueness check could see them. Now a list.
- **X2 and duplicate-id had no fixtures at all**, despite both being named in V4C-32's own adopted
  scope. Added; 13 fail fixtures total.
- **`sec_pat2` in `bootstrap-check.sh` was never wired** — declared in v3, never passed to `grep`,
  across **eight cuts** and into every project that copied the package. Now wired and scoped;
  measured at **0 false positives** against a 576-test production codebase before shipping.
- **`D1`** — the shipped copy of the validator and the copy CI runs must be byte-identical. Nothing
  checked that before.

**REFUSED, not carried:** V4C-12 (process-artifact A/B) → `docs/refusals.md` row 12. Adopted at
v4.0, never piloted, condition lapsed twice. At one owner plus agents, N is too small for a held-out
split to say anything; carrying a doc-class adopt is how it becomes permanent decoration.

**NOT REGENERATED, stated plainly:** the deck remains the **v4.1** edition
(`GP-v4.1-presentation.html` + `-TR`). v4.2 adds one row to its version narrative and regenerating a
21-slide bilingual pair for one row is not warranted. The v4.1 handover once claimed a deck was not
regenerated and that claim went stale the moment it was — so: **the deck is v4.1, deliberately.**

**The doctrine this cut is named for:** *a control nobody has watched fail is a rumour.* v4.1 said a
declared control that silently passes is worse than an absent one. v4.2 adds the corollary the
council proved on the chair: **that includes the control you wrote this morning.**

### v4.1 vs v4.0 (previous increment — MINOR + the first repair cut)

v4.1 is a **clean superset** of v4.0 with two halves. The second half is unprecedented in this
project's history and is recorded plainly: **the Increment-11 council audited the repo instead of
the briefing and found that several controls we had ratified did not work.**

**PHASE 0 — REPAIRS (what the council found, all chair-verified):**
- `make check-templates` (ratified as V3C-99 in v3.5) was a **shell syntax error** —
  `for f in … 2>/dev/null` — and had therefore **never executed once** across two cuts. Repaired,
  and it now FAILS LOUDLY when unwired instead of `|| true`-ing to success.
- `make journey` (V3C-106, a default-expected deliverable) called `scripts/journey.py`, **which did
  not exist**. The script is now SHIPPED: stdlib-only, four QM-bar steps, unwired steps exit 2 —
  never a silent pass.
- `make cold-start` was echo-only and always exited 0. It now fails until wired, with the wiring
  instructions in the failure output. **A declared control that silently passes is worse than an
  absent one** — that sentence is the whole of Phase 0.
- (GDF repo, same day) `gdf-check.sh` **failed open**: with `enabled: True` (capital T) it printed
  "deploy disabled" and skipped the owner-required-reviewer assertion — a declared non-negotiable.

**PHASE 1 — RECORDS AS VALIDATED DATA (rung 2 → 3 of the architecture ladder):**
- **`scripts/check_records.py` (V4C-30)** — one stdlib-only validator, `python/peps` idiom:
  per-record required fields + closed enums + id format, cross-record reference resolution,
  supersession-cycle and status-flow ordering, propagation rows, and fake-pin detection. **No
  dependencies, ever** — this file sits on a governance path (V4C-41 refusal 9).
- **`schemas/record.schema.json` (V4C-29/31)** + validated frontmatter on every root governance
  record. Prose stays canonical markdown; only the frontmatter is validated.
- **`conformance/` (V4C-32)** — pass fixtures plus one fail fixture per blocking rule, each
  declaring its expected diagnostic; `make check-records-selftest` runs the fail corpus and fails
  if a rule stops firing. This is V3C-72 fault-injection applied to the validator itself, and it
  earned its place immediately: it found a real bug in the validator on first run (cross-record
  rules never fired in single-file mode).
- **`.github/workflows/governance-contract.yml` (V4C-34) — ADOPTED AS A GATE.** One unconditional
  aggregate check, SHA-pinned actions (both SHAs API-verified at adoption), self-test first.
  GitHub reports a SKIPPED required job as SUCCESS, so conditional checks are advisory in disguise.
  **The six-cut zero-gate streak (v3.1–v4.0) ends here by decision, not by relabelling** —
  Increment 11 §2, 7 seats to 2.
- **Schema-narrowness rule (V4C-35):** a field may exist only if a check consumes it; every
  required field must answer *"which concrete failure does its absence permit?"*; unused fields are
  deleted after two cuts. This is the anti-bloat control for everything above.
- **Mechanical propagation (V4C-36)** — the v4.0 propagation checklist stops being prose: P2 asserts
  every package keeps its §0 changelog heading (**the one verified field incident: v3.3 lost it and
  nothing noticed for two weeks**), P3 asserts the executive-overview file count matches reality.
  Blocking scope is the CURRENT package only; prior versions are FROZEN, so findings there are
  history, surfaced by `--historical`.
- **`docs/refusals.md` (V4C-41)** — eleven recorded refusals with reasons and re-open triggers,
  including **rung 5 refused by decision, not deferred by budget**.
- Cost lines (V4C-13, binding condition of Increment 11): every new control states
  minutes-when-it-fires, who may bypass, and where the bypass is recorded.

**The day-1 falsification test (Skeptic's pre-registered condition) was RUN and PASSED:** the
validator was pointed at four cuts of real historical records before the build was finished. It
found the v3.3 §0 loss in under a second, and caught a live file-count discrepancy in v4.1 itself
while v4.1 was being assembled. Pre-registered failure condition — *"if four cuts of real history
yield no finding the prose process missed, Phase 1 has no field basis"* — did not trigger.

**Deferred with triggers (Increment 11):** CI-signed wave-close attestation (V4C-37, unanimous
defer — "a signature configured by the record-writers is not independence") · `rules_loaded[]`
hashes (V4C-39) · the resume contract at full width (V4C-38 — adopted MINIMAL: six consumable
fields, not fourteen) · presence gate and pre-commit harness moved to Phase 2 · permission-matrix
reconciliation (V4C-46, Phase 2). **Rejected:** Taskfile (8 of 9 seats).

### v4.0 vs v3.5 (previous increment — MAJOR)

v4.0 is a **clean superset** of v3.5 and the first cut informed by EXTERNAL MARKET EVIDENCE:
three independent AI market-landscape scans (59/197/12 verified sources, cross-checked; archived
in `research/market-landscape/`) confirmed that GP's four core mechanics — git-derived trust
telemetry, blind council + evidence-ratified process versions, owner out-of-sandbox verification,
backpressure/auto-freeze — are EMPTY across ~25 surveyed players. 9-seat blind council; owner
settled the splits (technical-side rule); **0 new gates (fifth consecutive 0-gate cut); 14
adopts**. MAJOR because the cut exits the v3.0 scope (external evidence class, constitution
mechanics, both lanes in one council — OD-7). Skeptic's MAJOR dissent is on the record verbatim.
Evidence: `General_Pipeline/v4.0-ratification.md` + `v4-candidate-register.md` (Increment 10).

**Versioning semantics (V4C-11 — named at last):** **MAJOR** = lane/stage topology or governance
change · **MINOR** = additive rules within existing topology · **PATCH** = wording/fixes. Every
cut runs the **propagation checklist**: `pipeline-schema.html` body (not banner-only),
`pipeline-design.md` §0 + touched §s, `AGENTS.md`, `README.md` version row, executive-overview
regenerated LAST, `HANDOVER-vX-material.md`, GDF constitution pin review. Amendments between cuts
get a dated amendment record in §0 — never silent edits.

- **V4C-06 (constitution invariant, BOTH lanes):** base-pinned policy — any rule/profile/policy a
  reviewer, gate, or agent consumes is read from the protected base ref, never from the
  change/comment/task under evaluation. Grounded in three 2026 exploit classes (comment-driven
  credential theft; head-branch review-policy override; one-PR→RCE on a review bot). Gate
  promotion committed for re-table at v4.1.
- **V4C-01 (advisory):** at HIGH tier, mutation kill-rate (Stryker/PIT class) reported beside the
  Tester's fault-injection verdict, separate from coverage — the mechanical form of test-integrity
  judgment. No thresholds until field baselines exist.
- **V4C-03 (advisory) + V4C-04 fields:** at HIGH tier, ≥1 fresh-eyes seat on a DIFFERENT model
  family than the author when known/available; author/reviewer family + fresh-context assertion
  recorded in the verdict; never blocks on unavailability.
- **V4C-07:** the journey script (V3C-106) gains a SCHEDULED post-deploy life — monitoring-as-code
  with a named on-call owner, flake/mute policy, prod-safe synthetic execution, CI-held scoped
  credentials; results land in the watch-window record.
- **V4C-08 (doc, stack-conditional):** canary/pre-post verify + mechanical rollback for fixpacks
  where the platform supports it; a rollback that has never fired is a doc, not a control —
  rehearse once per supported stack.
- **V4C-13:** friction budget + bypass telemetry — wave-checklist row 9 becomes the
  skipped/waived/BYPASSED ledger with cost lines; bypasses are first-class EXPERIENCE findings
  (`control-bypass` category); the same control bypassed 3× triggers review of the CONTROL.
  Field origin: HIGH/auth fix shipped unreviewed under support-phase pressure.
- **Council machinery (root `council-design.md`):** V4C-22 verdict set (ADOPT-WITH-CONDITIONS
  needs owner+date+closure artifact; INSUFFICIENT-EVIDENCE abstention for every seat) · V4C-27
  council pricing (timebox per class; timeout = INSUFFICIENT-EVIDENCE + owner escalation, never
  tacit approval) · V4C-25 council telemetry (escaped defects traced to the ruling that admitted
  them; spec due v4.1) · V4C-12 process-artifact A/B pilot (one artifact).
- **V4C-14 (repo root):** `differentiator-ledger.md` — the four market-empty mechanics, nearest
  challenger each, quarterly review clock; the same clock carries the standing multi-AI market
  re-scan (V4C-15 merged).
- **GDF lane (sibling repo):** V4C-05 identity-grade credential isolation (v1: permission-matrix
  records identity+scope+expiry per credential NAME; enforcement at pilot exit) · V4C-10 injection
  defense becomes a TESTED control in the first pilot (blocking precondition for scale-out) ·
  V4C-06 invariant applies constitution-wide.
- **Chartered theme (candidate, NOT adopted): PROCESS-ENGINE** — machine-readable
  constitution/config schemas, resumable workflow state, schema-validated records, agent-run
  tracing ("declared means machine-checked", generalized). Waits for evidence like Agent-Native did.
- Operating mode UNCHANGED: **A0.5 (PROVISIONAL)**; autonomy ladder remains NORTH STAR, NOT
  ACTIVE; nothing in v4.0 touches commit rights.

### v3.5 vs v3.4 (previous increment)

v3.5 is a **clean superset** of v3.4, cut on the FIRST REAL post-production dataset (HCS MaaS:
7 defects after green gates; ZERO caught by automated gates; 100% boundary defects — the gates
were "excellent at correctness of what we imagined and blind to the shape of the world we
deployed into"). 5-seat council; **0 new gates; net new package files: 0** — every adopt is a
placement into existing files. Skeptic's dissent recorded: two cuts in one week must not become
precedent.

- **V3C-99** `make check-templates` (every SHIPPED config template instantiates the settings
  parser) + `make cold-start` (boot against zero persisted state → serve-ready or honest
  not-ready); template-owned CI job (~1–2 min); §B.3 rows. *[2 total outages]*
- **V3C-100** human-path criterion (general form; credentials instance mandated): a person who
  did NOT build it, using only shipped docs+artifacts, completes the surface's primary journey.
- **V3C-101** producer enumeration on hardened invariants: checklist row (produce) + required
  HIGH-verdict section (verify) + citing test per producer; security sign-off on auth-class invariants.
- **V3C-102 (narrow)** never parse a bounded prefix; diagnostics print revision stamps.
- **V3C-103** ready≠alive (readiness probes its dependency; liveness stays dependency-free) +
  diagnosable fail-closed with the disclosure channel IN the criterion (logs + authenticated diag
  endpoint only; client gets generic + correlation ID).
- **V3C-104 (split)** the "touches build/CI/k8s: NO" boundary-grep line adopts now; the full
  patch-package format stays candidate (one partner).
- **V3C-105** cadence rebind: every OUTWARD deliverable = a wave close (fixes the wave-less-phase
  capture death, FIX-07).
- **V3C-106** black-box journey tester (`make journey URL=…`, stdlib, shipped in-package, authored
  during build; QM bar: cold entry + credential lifecycle + paying-customer round trip asserting
  CONTENT + one cross-wave sequence; Security custody: short-TTL minted tokens, never stored
  secrets) — DEFAULT-EXPECTED deploy deliverable, runs at 4.3 and every fixpack.
- **V3C-107** every boot prerequisite is in the image OR a named-owned provisioning row — no third
  category (cold-start is its executable audit).

### v3.4 vs v3.3 (this increment)

v3.4 is a **clean superset** of v3.3 — one addition, written as REUSE (Skeptic ruling): **Stage 5,
the Maintenance Loop** (V3C-98, owner directive OD-6). Field basis: the first GP production
project accumulated ~5 ad-hoc fix deployments post-go-live; GP's stages previously ended at
go-live. **0 new gates.** The genuinely new elements are exactly three:

- **Red-test intake:** a fix wave cannot open until the prod bug is reproduced as a FAILING test —
  the red test IS the frozen spec. Fix waves only turn red tests green, never add behavior.
  Exploitability triage per bug at intake (fresh-eyes; security-class → escalate-NOW + invariant test).
- **The fixpack** (NEW `docs/fixpack.template.md`) — one-page release unit AND deploy gate: per-fix
  evidence rows, caps (≤5 fixes/~400 lines; HIGH ships solo), patch version bump, migration +
  rollback plan, security floor (gitleaks/SCA + full invariant suite + diff-scoped read + ⛔
  auto-escalation), full regression once on the final bundled build, fix probe + watch window at
  deploy, emergency path (compressed scope, never-skipped floor, 48h retro-close debt, >1/month alarm).
- **The owner's out-of-sandbox gate** (BLOCKING): reproduce the original bug pre-fix locally →
  confirm gone on the fixpack build → local tests + smoke → sign. No signature, no deploy.

**Capture coupling + RETIREMENT:** fixpack lesson lines append to EXPERIENCE.md as a deploy
condition — the mechanical harvest. The standalone memory-based harvest session is retired
(3 md5-identical uploads proved it was aspiration). 3 same-gate misses in 2 packs → mandatory
gate-change proposal. N=3 fixes on one surface → surface locks, refactor goes through a normal
milestone. Debt line honored: the v3.1 retirement count remains owed to the first v3.3+ retro.

### v3.3 vs v3.2 (this increment)

v3.3 is a **clean superset** of v3.2 — one change, deeply wired: **owner directive OD-4** moves the
owner's review from wave cadence to milestone cadence, ratified as ladder rung **A0.5 (ACTIVE —
PROVISIONAL)** by a 7-seat blind council with all decisions chair-delegated. Also closed: the
hcs_maas_vib final harvest (md5-identical to the interim → zero new findings; obligation closed).

- **A0.5 operating mode (V3C-90, guardrail+template):** waves close AGENT-side (fresh-eyes reviews
  per risk tier, `make` checks green pinned to the closing tree, committed evidence-cited wave
  checklist, HIGH-tier pulled-forward security pass); the OWNER runs a 60–90 min milestone session —
  closure report + per-wave diffs + his OWN local tests/smoke tests + the milestone commits.
- **Checkpoint commits:** owner-made, per wave, labeled `wip(...): NOT reviewed` (commit ≠ approval;
  agents never run git). Kills the F17 uncommitted-loss class; keeps per-wave diffs decomposable.
- **Escalate-NOW list** (AGENTS.md §3): secrets, scanner-suppression, HIGH BLOCKING, stay-green
  faults, CI/gate changes, critical deps, invariant-test edits, ⛔/criteria questions, scope breaks.
- **Milestone cap:** ~4–6 waves / ~2k net lines — close early, never stretch (anti skim-with-a-signature).
- **Tripwire (automatic):** an escaped blocker an owner wave-pass would plausibly have caught →
  fallback to wave-cadence review; A0.5 PROVISIONAL until it survives 2 milestones on the next project.
- **Activated:** the assumption ledger (assume-and-log below the ⛔/criteria line). **Added:**
  per-wave table + "decisions on your behalf" + fix-rate-baseline line in the closure report;
  reviewer countersign of checklist rows; semantic-security items (security-baseline §v3.3).
- **Retired (net ceremony down):** the owner-reviews-every-wave rule; owner per-wave test runs;
  per-wave owner sign-off. **Bright line:** an agent commit reaching main = A1 = explicit owner ADR.


### v3.2 vs v3.1 (this increment)

v3.2 is a **clean superset** of v3.1. Source: the first fully EXTERNAL evidence class — a 9-document agentic-engineering research curriculum (METR RCT, Veracode 2025, GitClear, USENIX slopsquatting, CodeRabbit, DORA, Anthropic context-engineering evals, Ronacher's harness-loop analysis; archived under `research/agentic-engineering-curriculum/`) — plus **owner directive OD-3** (PRD → sign → autonomous run → owner reviews results + git). Ratified 2026-07-03 by a 2-phase council (Phase 1: 6 core seats blind-parallel; Phase 2: AgentOps/DX/LLM domain seats separately; splits chair-decided under owner delegation). **0 new gates.** The batch's central rule, converged on blind by all 9 seats: **anything feeding trust, promotion, or a gate is computed from git/CI/hook artifacts against protected refs — agent-asserted content is context, never a gate input.**

- **V3C-82 autonomy ladder (NORTH-STAR CANDIDATE — NOT ACTIVE; owner decision 2026-07-03):** NEW `docs/autonomy-protocol.md` records the A0/A1/A2 design (telemetry-gated promotion, automatic demotion, ⛔ glob carve-outs, scope grants, halt-and-notify, backpressure, "continuity is files, not sessions") — **A0 is the only operating mode: the owner reviews every wave and milestone, runs tests/smoke tests/checks, and makes all commits.** Activation only by a future owner-initiated ADR.
- **V3C-83 owner review pack (template):** NEW `docs/closure-report.template.md` — script-derived from raw referents, 2-page cap, BLOCKING prose architecture-delta; REPLACES the separate closure walkthrough output + note.txt milestone summary (net-zero artifacts); absorbs the agent-authorship commit trailer (V3C-89).
- **V3C-84 trust telemetry (template):** mechanical per-task-type fields (post-closure fix rate via path-overlap vs the protected closure tag, churn, reverts, findings w/ security ×2) appended at closure; any regression blocks promotion.
- **V3C-85 context economy (doc+profile):** NEW `subagent-profiles/Explorer.md` (read-only, ≤2k-token summary cap); one task/session; fresh subagents per wave; compaction anchored to wave close (preserves open findings, re-injects security invariants); token budget as a live circuit breaker in cost-log.
- **V3C-86 AI-aware review smells (template, one home per check):** duplication-vs-reuse / drive-by edits / swallowed exceptions → Code-Reviewer; mirror-implementation + weakened-to-green tests → Tester (BLOCKING at HIGH); ~≤400-line diff WARN → wave checklist.
- **V3C-87 declared L0 spike lane (doc+backstop):** `spike-*` exempt from gates except secrets scanning; never merged (branch-guard + closure row); productionize = rebuild.
- **V3C-88 plan interrogation (doc, MED/HIGH only):** one alternative + trade-offs per plan; absence is mechanically checkable.
- **External corroboration (B1–B7):** first independent confirmation of V3C-69 executable-discipline, the security gates (Veracode: 45% vulnerable, no improvement with scale), slopsquat defense (USENIX 19.7%), the AGENTS.md diet, fresh-eyes isolation, red-test-first, and the ⛔ rows.


### v3.1 vs v3 (this increment)

v3.1 is a **clean superset** of v3 — nothing removed. Source: the first project run ON GP v3 (hcs_maas_vib, M0–M4, 171 tests; all six v3-adopt field validations CONFIRMED, five sharpened, none contradicted) + two owner directives. Ratified 2026-07-03 by an **11-seat blind council** (`General_Pipeline/v3.1-ratification.md`). **0 new gates — the reserve slot is preserved.** New meta-rule: validates-GP evidence from GP-run projects cannot alone escalate past template weight (self-validation cap).

- **V3C-69 executable discipline (guardrail+template, owner):** NEW `docs/wave-checklist.template.md` — wave close is gated by a committed, evidence-cited checklist derived from the plan's risk tags; skipped/waived checks ledgered; `make wave-check`.
- **V3C-81 living EXPERIENCE.md (guardrail+template, owner):** NEW `docs/EXPERIENCE.template.md` — appended at every milestone closure; the quarterly handover BLOCKS without a dated entry for the latest closed milestone.
- **V3C-78 risk-tiered review depth (template, amends V3C-68 → P-005):** LOW/MED wave → one combined reviewer; HIGH → Code+Tester + pulled-forward security-on-slice; auto-escalation rubric + escaped-blocker tripwire. Measured ~11→~5 reviewer runs per milestone.
- **V3C-72 Tester fault-injection (template):** break → RED → revert-in-place (md5-verified); a stay-GREEN fault is the finding → mandatory new test (`subagent-profiles/Tester.md`).
- **V3C-70+71 day-0 OSS gate (guardrail):** license/commercial-use review + explicit consumption posture (wrap|fork|port, wrapper never touches the wrapped datastore) BEFORE architecture depends on the engine.
- **V3C-73/74/75/77 security-baseline additions:** built≠wired · negative test per security invariant · idempotency different-payload pattern · integer-minor-units money rule (domain-scoped). `docs/security-baseline.md` §v3.1.
- **V3C-79 carried retro question (template):** each retrospective answers the previous carried question and poses one; twice-proposed-never-built rules are built or dropped.
- **Sharpened v3 adopts:** V3C-44 (live-contract leg, loud skips) · V3C-33/45 (tested disable switch, fail-direction table) · V3C-53 (OFF-in-code/ON-in-prod + preflight) · V3C-68 (checklist-gated passes) · V3C-10/C.6 (hermetic gate) · V3C-06 (in-place revert).
- **Deferred:** V3C-76, V3C-80 generator; **Agent-Native theme unchanged** (hcs is gateway-family, not a 2nd independent ecosystem).


### v3 vs v2.2 (this increment)

v3 is a **clean superset** of v2.2, not a rewrite — every v2.2 file, stage, seed, and gate stands, and v3 only adds. It is a cross-project harvest: 7 projects (Reimbursement-App, Poyraz-Dekorasyon, aop-portal, BotIm-AOP, aop_growth, HSC-MaaS, one-api) were triaged into 68 candidates (`v3-candidate-register.md`) and ratified by a **13-seat blind council** (`v3-ratification.md`, budget §5.5: ~15 adopts, ≤3 BLOCKING gates). The through-line, named by the skeptic and echoed by 5 other seats: **the largest new gap is agent-native/LLM-ops + gateway, but most of that evidence is one ecosystem (Botim AOP/growth/portal + the one-api/NewAPI gateway family), so it is chartered as a candidate, not adopted wholesale.** Only the items that also cross an ecosystem boundary or re-derive GP's own (independent) design were adopted now.

**Added — 2 gates (BLOCKING; 2 of the ≤3 budget, 1 in reserve):**

- **V3C-11 — web/API security baseline (gate).** `make bootstrap-check` now FAILS on a hardcoded default-admin password / obvious plaintext-credential pattern (catastrophic + grep-checkable). Two ad-hoc projects independently re-derived GP's inherited security gates the hard way; one-api shipped a literal default admin password. Housed in the new `docs/security-baseline.md`.
- **V3C-02 — tests cite each acceptance criterion (gate).** Sharpened and made BLOCKING at the Quality Gate (and in the per-agent dev-test loop): every acceptance criterion has a citing test, and a reported symptom is reproduced with a *failing* test before diagnosing (red→green). Mostly formalizes the existing REQ-coverage gate.

**Added — V3C-68 review-loop restructure (the biggest structural change; template):**

- **Stage 2** — each implementing agent runs a tight **dev-test loop** on its own slice (implement → write/run tests → self-review → fix), owning the quality of its slice.
- **Stage 3 (per-wave, fresh-eyes)** — **Code-Reviewer + Tester** review the wave's combined output (never their own code) and flush all fixes before the wave closes. **Security is REMOVED from the per-wave gate.**
- **Stage 4 (closure)** — **Security review is BLOCKING and runs before the Stage 4.3 deploy/go-live step**, reviewing the whole milestone's surface at once, alongside the Quality Gate. Safe because nothing ships mid-milestone (waves don't deploy). Always-on catastrophe-class guardrails (no committed secrets, no destructive ops) still apply during every wave. New `subagent-profiles/Tester.md` (mandatory per-wave fresh-eyes tester, red→green against the wave's acceptance criteria).

**Added — web/API security baseline (guardrails; grouped in `docs/security-baseline.md`):** V3C-12 server-side authz on every mutating route (client checks are UI sugar); V3C-13 CORS allowlist, never allow-all + credentials; V3C-51 validate security-critical config at startup and fail the prod process; V3C-56 encrypt credentials/PII at rest with a rotation-friendly key chain; plus generic client errors (log detail server-side). GP's security was abstract/backend-Python; v3 makes it concrete and web-facing.

**Added — safety guardrails:** V3C-06+53 no destructive ops / reseed-on-boot defaults OFF or is loud; V3C-08+36 agent least-privilege tool allowlist + human-confirm on all writes (CI and runtime) — LLM proposes, deterministic code acts; V3C-33+45 control-class fail direction as ONE paired rule — auth/safety fail CLOSED (with a tested disable switch), fairness/rate-limit fail OPEN.

**Added — build guardrails:** V3C-03 runtime config, never build-time baked; V3C-05 every dependency saved to the manifest; V3C-10 pin the toolchain version in CI; V3C-65 race detector as a recommended CI step (not a universal gate — evidence is Go-only).

**Added — canonical-mock convention (template):** V3C-44 — one canonical mock per external integration, built before integration code, parallel mocks consolidated, with a contract test against the real API (extends K.1 fake-client; noted in design §testing).

**Added — Agent-Native / LLM-Ops theme (CANDIDATE container):** a new design section charters the theme and lists its candidate seeds (V3C-32/34/35/37/38/39/40/41/42/43/46/47/48/58/59/61/62/66) as CANDIDATE (not active) pending a 2nd independent ecosystem. A matching candidate block is added (append-only) to `.agents/rules/playbook-seeds.md`.

**Confirmed / folded (doc):** V3C-50 design-docs + gap-analysis before code (into Stage-0/1 planning + START_HERE); V3C-52 `.agents/rules/` + a PROCESS.md routing index for token economy (re-derives GP's own design); V3C-01 version-stamped `/health` validated (confirms L.7); V3C-27 commit `.gitignore` first folded into bootstrap notes.

**Retirement pass:** 0 disciplines retired this cycle (v3 is a superset harvest). The ~20 deferred Agent-Native candidates and the rejected single-quirk findings (V3C-24/26/28/29/30/54/57/67) are recorded in `v3-ratification.md` §3; promote candidates on a 2nd independent ecosystem.

### v2.2 vs v2.1 (prior increment)

v2.2 is an **increment**, not a rewrite. Through-line, named independently by 6 of 7 council roles: **documented discipline is not self-enforcing — make it an executable gate, at Stage 0 and at go-live.** All of v2.1 (5-stage workflow, Theme L L.1–L.7, Stage 4.3, BLOCKING taxonomy) stands.

**Added:**

- **Executable Stage-0 gate — `make bootstrap-check` (FB-1, seed C.11).** `scripts/bootstrap-check.sh` FAILS Stage-0 closure on stray `<PLACEHOLDER>`s, a non-L.7 `/health`, still-template prd/decisions/architecture, missing universal ADRs, or a wrapped OSS engine without a license review. Wired into the Stage-0 closure checklist. (Origin: a real bootstrap shipped partial v2.1 discipline — even the starter shipped a v2.0 `{status:ok}` health test contradicting the L.7 day-1 claim.)
- **Starter health fixed to the L.7 contract (FB-1).** `src/app/adapter/main.py` + `tests/unit/test_health.py` now return/assert `{status, version, build}` out of the box (`APP_BUILD` env, defaults `"unknown"`) — the starter finally matches the design doc's L.7 claim.
- **Stage 4.3 extended: deploy + go-live readiness (L.8, L.9, E.6).** Beyond "is the new code live?" (L.7), now also: **L.8** invoke every external dependency once (`make smoke-deps`) — configured ≠ working; **L.9** read config back from inside the *process*, not the values file (injection layers drop keys); **E.6** prove the pipe up to a blocked dependency via the downstream's run-log attribution.
- **OSS-engine license gate at Stage-0 (FB-4, seed F.10).** "License & commercial-use review of any wrapped/forked OSS engine" — AGPL/GPL/SSPL ⇒ wrap-not-fork + legal sign-off; unreviewed = BLOCKING (permission-matrix). Added to Stage-0 gates + project-brief.
- **ADR-ID convention (FB-2, seed B.6).** Process/universal ADRs use `P-00x`; projects start at `D-100` (D-001..D-099 reserved). Stage-0 reconciliation recipe for inherited projects.
- **Cowork git-in-mount caveat (FB-3, seed C.12)** added to START_HERE: finish `git` host-side; `rm -f .git/*.lock`.
- **K.11 — agent-driven prod UI (capability CANDIDATE, N=1; guardrails ACTIVE).** Per the council synthesis: the guardrails (never enter credentials; state-changing clicks per-action & visible; no secret transcription) are written into the permission matrix NOW; the capability itself stays candidate until a 2nd payoff.
- **Manager-facing Executive Overview (`docs/executive-overview.md` + `.pdf`).** A plain-language overview of the pipeline for non-technical stakeholders, rendered from a single source (`docs/executive-overview.gen.py`, which emits both the Markdown and the PDF and auto-counts the package). Refresh it at each version cut — update VERSION/stats and re-run the generator.

**Promoted:**

- **Council planning graduated (FB-5).** v2.1 §15.8 deferred it pending a 2nd payoff; EF-AI delivered two more blind councils and this v2.2 cut was itself decided by a 7-role blind council. Now a **standing OPTIONAL Stage-1 variant**; the blind-parallel-subagent ballot is captured as the reusable recipe.

**Retirement pass:** 0 disciplines retired this cycle (deliberate sweep; all fired pulled-weight or are too-early). Recorded in §15.

### v2.1 vs v2.0 (prior increment)

v2.1 promoted proven material from the EF-AI M12 + S34 cycle into the design, templates, and Stage checklists. Nothing was rewritten; v2.0's 5-stage workflow, two-layer package, and BLOCKING taxonomy are unchanged.

**Added:**

- **Theme L — distributed correctness, durability & multi-node safety (§3.5).** Seven seeds (L.1-L.7) graduate from the M12 ADDENDUM into the design as a first-class production-hardening discipline: enqueue-then-ack, reserve-then-release, at-least-once + stable idempotency key, atomic cross-node election, bounded queue + load-shed, scale-out boot guard, version-stamped probe.
- **Stage 4.3 deploy-verification sub-step.** Closes the single biggest gap v2.0 missed: "code green + image built" is not "the new code is live in the target." One curl to the version-stamped `/health` confirms deployed build == intended build. Includes the checklist fact "a pod restart does not pull new code." (Grounded in 12-factor build/release/run: releases are immutable, uniquely-IDed, and the run stage only launches a *selected* release.)
- **L.7 version-stamped `/health` is now a Day-1 baseline** (like C.1 day-1-green): the starter ships `APP_BUILD` in the Dockerfile + a `{status, version, build}` health body from the first commit. Defaults to `"unknown"` so dev/test are unaffected.
- **K.10 CODEOWNERS is now a Stage-0 bootstrap default.** The starter ships a template `CODEOWNERS` (Dockerfile, `/deploy/**`, CI config under the DevOps handle) + an AGENTS.md "do not overwrite DevOps-owned build/deploy files" rule, active whenever app + DevOps share a repo. (Grounded in GitHub CODEOWNERS: owners are auto-requested for review and can be required to approve before merge.)
- **E.5 subagent-death test-gap drill** added to Stage 2 / closure: after any subagent death, the controller greps that each acceptance criterion has its citing test (death-tolerance for code is NOT death-tolerance for proof).
- **Council planning (optional Stage-1 variant).** Multi-role adversarial Stage-1 (PM + QM + Senior + DevOps voices, non-voting chair) is an OPT-IN variant for contested/MEDIUM+ milestones. Full promotion deferred until a 2nd payoff (currently PULLED-WEIGHT but N=1).
- **`/pm-status` template + candidate skill.** The M12 PM-status snapshot format (status emoji + plain language + "what's there / what's missing" + external blockers) is captured as `docs/pm-status.template.md`; pairs with G.9.

**Promoted (CANDIDATE -> ACTIVE):**

- **E.4 TDD-with-AI**, scoped to "new module + locked K.8 contract": write the acceptance-criterion tests first, subagent implements to green. M12's dead-subagent test gap (E.5) is the evidence.

**Folded / consolidated:**

- **C.10 sandbox runtime-shim** folded into C.7 (sandbox-as-canary): when the sandbox runtime lags the target, shim the version-only-missing stdlib names (`datetime.UTC`, `StrEnum`) via `sitecustomize.py` and run the FULL gate, not just lint.

**Retirement pass (§3.C of the handover):** 0 disciplines retired this cycle (all fired pulled-weight or are too-early to judge); the deliberate retirement sweep is recorded in §15.

---

## §1 — TL;DR (30-second version)

Pipeline v3 is a **vibe-engineering starter package** for LLM-powered API projects. It ships:

1. **Layer 1 — Starter Package (~60+ files)** that you clone, fill PROJECT placeholders, run `make check` (Day-1 green) and `make bootstrap-check` (the Stage-0 gate). Day-1 baselines: a version-stamped `/health` (L.7), a `CODEOWNERS` boundary (K.10), and now an **executable bootstrap gate** that won't let Stage 0 close partially done.
2. **Layer 2 — Workflow (5 stages)** — Bootstrap → Plan → Wave Execution → Per-Wave Review → Closure. **v3 (V3C-68):** each agent runs a dev-test loop in the wave; the per-wave gate is **Code-Reviewer + Tester** (fresh-eyes); **Security review moved to milestone closure (BLOCKING, before deploy)**. Quality Gate at milestone closure; quarterly handover every 3rd milestone. **Stage 4.3 is "deploy + go-live readiness"**: which code is live (L.7) + dependency liveness (L.8) + config-reaches-process (L.9) + pipe-attribution (E.6). Council planning is a standing optional Stage-1 variant.

**New in v2.2:** executable Stage-0 gate (`make bootstrap-check`, FB-1) + L.7-correct starter health; Stage 4.3 go-live readiness (L.8/L.9/E.6); OSS-license Stage-0 gate (FB-4); ADR-ID convention `P-00x`/`D-100` (FB-2); Cowork git caveat (FB-3); K.11 agent-UI guardrails; council planning graduated (FB-5). Full list in §0. (v2.1 added Theme L §3.5 + Stage 4.3 deploy-verification.)

What's **NEW vs v1.1**:
- **Hooks** (`.claude/settings.json`) enforce 2 baseline rules deterministically: block writes to `.env`, run `make check` after edits.
- **Skills** (`.claude/skills/*/SKILL.md`) — 10 runtime-invokable workflows including `/triage-issue`, `/fix-issue-prepare`, `/fix-issue-implement`, `/file-issue`, `/quarterly-handover`, `/log-decision`, `/retrospect`.
- **`.agents/rules/`** directory replaces `docs/discipline-*.md`. `environment.md` is per-developer gitignored.
- **MCP** server (`mcp.json`) — GitHub or GitLab host MCP committed; tokens in `.env`.
- **3-layer issue management** — pure CI / CI-triggered agent / scheduled + interactive. Headless Claude Code in CI (label-gated, draft-only, hardened YAML).
- **AGENTS.md canonical**, CLAUDE.md → AGENTS.md symlink (industry convergence + Claude Code compat).
- **BLOCKING taxonomy locked in writing.** Structured PASS / MINOR / BLOCKING verdicts with `file:line` evidence requirement.
- **Quality gate at MILESTONE CLOSURE** (not per-wave), supplemented by per-PR CI checks.
- **Quarterly handover** (`docs/handovers/handover_q{N}.txt`) at M3 / M6 / M9 / M12 ...
- **Gitleaks** replaces TruffleHog mention in seed F.6.

What **STAYS the same vs v1.1**:
- 5 visible stages (no Stage 2.5).
- Mandatory fresh-eyes review subagent profiles (v3: Code-Reviewer + **Tester** per wave; Security-Reviewer at milestone closure — V3C-68).
- 64 inherited seeds (themes A-K) + 8 new seeds (5 ACTIVE + 3 CANDIDATE).
- D-001..D-005 universal ADRs.
- Permission matrix as a separate file (default-deny).
- Three-file handoff pattern (handover_q{N}.txt + note.txt + when_<event>.txt).
- G.12 retrospectives at M≥3 with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts.

---

## §2 — Two-layer architecture

```
╔═════════════════════════════════════════════════════════════════════════╗
║                       PIPELINE v2.0 PACKAGE                             ║
║                                                                         ║
║   ┌─────────────────────────────────┐  ┌────────────────────────────┐   ║
║   │   LAYER 1 — STARTER FILES       │  │  LAYER 2 — WORKFLOW (5     │   ║
║   │   (~60 files)                   │  │           stage process)   │   ║
║   │                                 │  │                            │   ║
║   │   AGENTS.md (canonical)         │  │  Stage 0 — Bootstrap       │   ║
║   │   + CLAUDE.md symlink           │  │     ↓                      │   ║
║   │   Makefile + pyproject.toml     │  │  Stage 1 — Milestone Plan  │   ║
║   │   permission-matrix.md          │  │     ↓                      │   ║
║   │   .gitleaks.toml + .gitignore   │  │  ┌─ WAVE LOOP ────────────┐│   ║
║   │   note.txt + .pre-commit-config │  │  │ Stage 2 — Wave Exec    ││   ║
║   │   .mcp.json (GitHub/GitLab)     │  │  │   + Internal Commit    ││   ║
║   │                                 │  │  │     Gate (HOOKS!)      ││   ║
║   │   .claude/                      │  │  │   + dev-test loop      ││   ║
║   │     settings.json (hooks++)     │  │  │     ↓                  ││   ║
║   │     skills/ (×10 starter)       │  │  │ Stage 3 — Per-Wave     ││   ║
║   │                                 │  │  │   3a Code Review       ││   ║
║   │   .agents/rules/                │  │  │   3b Tester (V3C-68)   ││   ║
║   │     practices.md                │  │  │     ↓ verdict          ││   ║
║   │     playbook-seeds.md (72+)     │  │  └────────────────────────┘│   ║
║   │     environment.md (.gitignored)│  │     ↓                      │   ║
║   │     README.md                   │  │  Stage 4 — Closure         │   ║
║   │                                 │  │     4.0 Security (BLOCK)   │   ║
║   │   .github/workflows/            │  │     4.1 Quality Gate       │   ║
║   │   CODEOWNERS (DevOps boundary)  │  │     4.2 Capture            │   ║
║   │     ci.yml (hardened)           │  │     4.3 Deploy-verify      │   ║
║   │     issue-agent.yml (gated)     │  │     4.4 Handoff (M%3==0?)  │   ║
║   │                                 │  │  Cross-cutting (always on):│   ║
║   │   docs/                         │  │  • Customer + Process cap. │   ║
║   │     decisions.md (D-001..D-007) │  │                            │   ║
║   │     prd.md + architecture.md    │  │  Issue management — 3      │   ║
║   │     handovers/handover_q1.txt   │  │  layers:                   │   ║
║   │     retrospectives/             │  │  L1 pure CI hygiene        │   ║
║   │     plans/ + reviews/           │  │  L2 CI-triggered agent     │   ║
║   │     onboarding.md               │  │     (gated, draft-only)    │   ║
║   │     tool-suitability.md         │  │  L3 scheduled + interactive│   ║
║   │     external-skills/ (×4)       │  │                            │   ║
║   │                                 │  │                            │   ║
║   │   subagent-profiles/            │  │                            │   ║
║   │     Code-Reviewer.md (MAND.)    │  │                            │   ║
║   │     Security-Reviewer.md (MAND.)│  │                            │   ║
║   │                                 │  │                            │   ║
║   │   src/app/ skeleton             │  │                            │   ║
║   │   tests/unit/test_health.py     │  │                            │   ║
║   │   scripts/standup.sh            │  │                            │   ║
║   └─────────────────────────────────┘  └────────────────────────────┘   ║
║                                                                         ║
║   New engineer: clone → fill markers → make check GREEN → ~30 min       ║
║                                                                         ║
╚═════════════════════════════════════════════════════════════════════════╝
```

---

## §3 — Layer 2: Workflow (5 stages)

### Stage 0 — Bootstrap (once per project, ~4-8 hours)

**Inputs:** Customer PRD, architecture brief, target environment.

**Two paths:**
- **Path A (recommended for greenfield):** Paste `repo-starter.md` prompt into a fresh Claude Code session in the new repo. Claude inspects, asks ≤4 questions (stack / test framework / run command / repo host), then scaffolds files from this starter package.
- **Path B (recommended for non-greenfield or non-Claude environments):** Clone this starter package directly. `cp -r general_pipeline_v2.2 ~/path/to/<new-project>` then fill PROJECT placeholders, then run `make bootstrap-check` until it exits 0.

**Actions:**
- Fill PROJECT markers in AGENTS.md §1-2 (name, customer, stack, REQ-ID prefix).
- Update `pyproject.toml` (name, deps).
- Update `README.md` (one-paragraph project intro).
- Adapt `permission-matrix.md` if project has extra sensitive areas.
- Update `.mcp.json` if project uses non-default MCP servers.
- Configure host-side **branch protection** on `main` (one-time admin action).
- Configure `ANTHROPIC_API_KEY` as secret + set 90-day rotation calendar.

**Gates before Stage 0 closes:**
- `make check` GREEN (Day-1 baseline, seed C.1)
- AGENTS.md ≤80 target / ≤150 hard cap
- `pyproject.toml` + project name + initial deps
- `permission-matrix.md` adapted; OS-aware patterns confirmed
- `subagent-profiles/Code-Reviewer.md` + `Security-Reviewer.md` in place
- PRD numbered with REQ-IDs + Open Questions §9 (seed A.1, A.3)
- Branch protection on `main` configured at host (the one-time gate that makes CI load-bearing)
- **NEW v2.1 — version-stamped `/health` baseline (L.7):** the starter's `/health` returns `{status, version, build}`; `APP_BUILD` is wired in the Dockerfile (`ENV APP_BUILD=<tag>`) and defaults to `"unknown"`. One test asserts the three fields exist (additive only — don't break the liveness contract).
- **NEW v2.1 — `CODEOWNERS` boundary baseline (K.10):** if app + DevOps share the repo, ship `CODEOWNERS` (in `.github/`) marking `/Dockerfile`, `/deploy/**`, and CI config under the DevOps handle, plus an AGENTS.md "do not overwrite DevOps-owned build/deploy files" rule. Skip only for solo / no-DevOps repos (leave the template with a `# TODO: real DevOps handle` placeholder rather than a fake owner).
- **NEW v2.2 — `make bootstrap-check` is the GATE, not a reminder (FB-1, C.11):** the Stage-0 checklist above is now *enforced* by `scripts/bootstrap-check.sh`. Stage 0 cannot close until `make bootstrap-check` exits 0 — it FAILS on stray `<PLACEHOLDER>`s in must-fill files, a non-L.7 `/health`, still-template prd/decisions/architecture, missing universal ADRs (D-001..D-005), and a wrapped OSS engine without a license review. (The unfilled starter intentionally fails it — it is a template.)
- **NEW v2.2 — OSS-engine license gate (FB-4, F.10):** if the project wraps or forks an OSS engine, complete a license & commercial-use review (`docs/license-review.md`) BEFORE building. AGPL/GPL/SSPL on a network service ⇒ **wrap-not-fork** (run an unmodified copy as a separate service behind your proprietary control plane) + legal sign-off; an unreviewed copyleft wrap is BLOCKING (permission-matrix catastrophe-class).
- **NEW v2.2 — ADR-ID convention (FB-2, B.6):** process/universal ADRs use `P-00x`; project ADRs start at `D-100` (D-001..D-099 reserved). For an inherited project that already numbered its own D-ids, run the Stage-0 reconciliation recipe (keep the project's D-ids; represent the pipeline's process ADRs as `P-00x`; write the mapping down before the first commit).

**New for v2.0:** Hooks fire from `.claude/settings.json`. Block writes to `.env` (PreToolUse). Run `make check` after edits (PostToolUse).

### Stage 1 — Milestone Plan (per milestone, ~1 hour)

**Output:** `docs/plans/m{N}-plan.md` in superpowers writing-plans format.

**V3C-50 (design-docs + gap-analysis before code, NEW in v3 — keep light):** before the first line of code, the plan states *what already exists vs what must be built* — a one-paragraph gap analysis per acceptance area (reuse / extend / build-new). For a non-trivial milestone, link the design notes it rests on. This extends Stage-0/1 planning; keep it to a few lines (ceremony risk — do not turn it into a separate design phase for small milestones).

Required sections:
1. **Goal** — one sentence preferred.
2. **REQ-ID acceptance criteria.**
3. **Risk tier** — LOW / MEDIUM / HIGH (drives Stage 3 depth + Stage 4.1 Quality Gate intensity).
4. **Wave decomposition** — parallel + sequential waves, each task ≤5 min subagent scope (K.6).
5. **K.8 contract surfaces** — declared upfront WITH `grep -n <symbol>` evidence pasted into plan.
6. **Token budget estimate** — single line `Estimated subagent spend: ~$X` (PM cost cap).
7. **Subagent profile source** — A / B / C / D per profile (default A: superpowers baseline).
8. **Issue inventory** — list of GitHub Issues this milestone resolves (Layer 2 vs K.4 wave routing).
9. **Closure tasks.**

**Subagent profile source choices (Stage 1 user decision):**
- **A** — Superpowers SKILL baseline (default; lowest friction).
- **B** — Claude generates fresh (milestone-specific domain).
- **C** — Codex generates fresh (A/B test or Codex platform).
- **D** — Mix per profile.

If B/C/D, regenerate profile file at `subagent-profiles/m{N}/Code-Reviewer.md` before wave dispatch. Plan records source + rationale + generation prompt.

**Optional variant — Council planning (NEW in v2.1; opt-in for contested or MEDIUM+ milestones):**

For a milestone whose *scope itself* is contested (subtle correctness, multi-node behaviour, cross-team surface), run Stage 1 as a multi-role adversarial deliberation instead of a single-author plan: convene a **PM / Quality-Manager / Senior-Software / DevOps** set of voices that vote the plan, with the controller as a **non-voting chair** representing the user. The council debates failure modes before any code is dispatched and votes the acceptance criteria.

- **When to use:** risk-tier MEDIUM+ AND the plan's *scope* (not just its implementation) is in doubt. Skip for LOW-risk or mechanically-obvious milestones.
- **Why it earns a slot:** at EF-AI M12 the council caught a scope-level gap — "the real milestone is durable *delivery*, not just Redis idempotency" — that a single-author plan missed; without it M12 would have shipped idempotency and still lost callbacks at >1 replica. Two live repo footguns were also retired during the debate at zero cost.
- **Status:** PULLED-WEIGHT but N=1, so this stays an **optional** variant. Full promotion (standing discipline) is deferred until a 2nd independent payoff; record the verdict in the milestone retrospective (G.12) either way.

**Gates:** User approval REQUIRED before dispatch (council vote does not replace user sign-off).

**v3.2 additions to Stage 1 (V3C-88/82):** MED/HIGH-tier plans must present ONE alternative approach + its trade-offs ("which would a senior object to, and why") — absence fails plan-completeness; the signed plan carries the **security-globs** list and its acceptance criteria are **hash-frozen** at signature; the scope-grant mechanics stay north-star-only (autonomy-protocol §3–5 — NOT active; at A0 the owner's live approvals govern).

### Stage 2 — Wave Execution (per wave, parallel)

**Dispatch pattern:** K.4 parallel waves of subagents (≤5 min scope each).

**Two execution modes:**
- **K.4 wave dispatch** (planned milestone work) — multiple parallel subagent tasks per wave; the default for new-feature deliverables.
- **`/fix-issue-implement` skill** (reactive single-issue fix) — one-issue → one branch (`fix/issue-<n>-<slug>`). Use for inbound bug fixes triaged via `/triage-issue`. Same K.6 rules apply (bar explicit, ≤5 min scope).

**Internal Commit-Gate fires automatically on every commit (HOOK now, not convention):**

```
PostToolUse hook (.claude/settings.json):
  ✓ make check (lint + type + test) — C.1
  ✓ gitleaks (secret scan)           — F.6 (v2 names gitleaks explicitly)
  ✓ pip-audit (dep CVE)              — F.7
  ✓ slopsquat check                  — F.8 (PyPI existence + maintainer-age)

PreToolUse hook:
  ✗ Write to .env / *.env*           — F.6 + permission-matrix.md
  ✗ Run git reset --hard / git push --force / rm -rf — C.9
```

Hooks exit non-zero with visible log on violation. Subagent must fix before next commit.

**K.6 prompt skeleton (unchanged from v1.1):**
- Scope: one specific task from plan
- Time budget: 5 minutes
- Shared contracts honored (K.8)
- May: add tests beyond minimum, note follow-ups, spot cross-wave K.9 candidates
- May NOT: change shared contracts, add deps without ADR, edit AGENTS.md

**E.4 TDD-with-AI (NEW in v2.1; ACTIVE, scoped):** when a wave implements a **new module behind a locked K.8 contract**, the acceptance-criterion tests are written FIRST (citing REQ-IDs), and the subagent implements until green. Scope is deliberately narrow — only "new module + locked contract," never a blanket TDD mandate — because tests-first only pays when the contract is already frozen. This is the structural fix for the coverage-theater failure mode (AI writes test + impl in the same turn).

**E.5 subagent-death test-gap drill (NEW in v2.1):** death-tolerance for *code* is not death-tolerance for *proof*. If a subagent dies mid-task, the controller does NOT just confirm the code compiles — it greps, for each acceptance criterion in the plan, that the *citing test exists*. At M12 a Wave-1 subagent died after landing the atomic `SET NX` store but before writing the concurrency + survives-restart tests; the code looked done, the proof was missing, and K.7 caught it one stage later as BLOCKING. Catching it at the wave boundary is cheaper. The plan's acceptance criteria each name the test that will prove them (so the grep target is explicit).

**Per-agent dev-test loop (NEW in v3; V3C-68 + V3C-02):** during the wave, each implementing agent runs a tight loop on its own slice — **implement → write/run tests → self-review → fix** — and owns the quality of that slice. Every acceptance criterion the slice touches gets a **citing test** (V3C-02, gate); when the slice fixes a reported symptom, the agent reproduces it with a **failing test first**, then makes it green (red→green). This loop *adds to*, never replaces, the wave-exit fresh-eyes review (GP's measured win is K.7) — self-review is weaker than fresh eyes.

### Stage 3 — Per-Wave Review (sequential) — Code-Reviewer + Tester (V3C-68)

**v3.3 (OD-4/A0.5): the owner is NOT part of the per-wave gate** — these agent sub-gates + green pinned checks + the committed wave checklist ARE the wave close; the owner reviews per milestone (escalate-NOW events excepted) and makes a labeled checkpoint commit per wave. After every wave (K.4 or `/fix-issue-implement`), two **fresh-eyes** sub-gates fire in sequence. **v3 change (V3C-68):** the per-wave gate is now **Code-Reviewer + Tester** (the v2.2 per-wave Security sub-gate has MOVED to milestone closure, Stage 4 — see below). All wave fixes are flushed before the wave closes. The dev-test loop above runs *inside* the wave; this gate is the fresh-eyes pass *at wave exit*. **v3.1 change (V3C-78, P-005 — risk-tiered depth):** the review WEIGHT follows the wave's risk tier, recorded in the Stage-1 plan: **LOW/MED → ONE combined fresh-eyes reviewer** (code+test in a single pass); **HIGH** (auth/payment/crypto/migration/distributed-correctness — auto-escalated if the diff touches authz/secrets/crypto/input-parsing/egress) → **separate Code-Reviewer + Tester + a pulled-forward security pass on that slice**. Tripwire: the first escaped blocker on a tiered-down wave reverts the project to full per-wave review. **v3.1 change (V3C-69 — executable wave close):** the wave closes only when its checklist (`docs/plans/m{N}-wave-{W}-close.md`, copied from `docs/wave-checklist.template.md`) is filled, committed, and `make wave-check`-green — every row cites fresh, wave-scoped evidence; required passes derive from the plan's risk tags; skipped/waived checks are ledgered, never silent.

#### 3a — Code Review

- **Profile:** `subagent-profiles/Code-Reviewer.md`
- **Invocation:** `/review` skill (calls our profile content; built-in `/review` is the invocation surface, our profile is the content).
- **Fresh-eyes constraint (K.7):** the subagent doing the review MUST NOT be the one that authored any of the wave's code.
- **Checks:**
  - Plan compliance — every task in plan delivered?
  - Integration drift — anyone silently rename a public symbol?
  - K.8 contract grep-verify — paste `grep -n <symbol>` output and confirm.
  - K.9 cross-wave gap spot — flag issues outside scope (do NOT fix; queue to next M).

#### 3b — Tester (fresh-eyes) ★ NEW in v3 (V3C-68)

- **Profile:** `subagent-profiles/Tester.md`
- **Fresh-eyes constraint (K.7):** the Tester MUST NOT have authored any of the wave's code.
- **Mandate:** prove the wave against its acceptance criteria, red→green.
  - Each acceptance criterion the wave touched has a **citing test** (V3C-02); if any is missing, the Tester writes/extends it.
  - Reproduce any reported symptom with a **failing test first**, then confirm it goes green.
  - Run the wave's tests; report red/green, coverage on touched code, and any criterion left unproven.
  - Flush all wave fixes before the wave closes (the dev-test loop is per-agent; this is the wave-level fresh-eyes confirmation).
- **★ v3.1 — Fault-injection protocol (V3C-72; MANDATORY on HIGH-tier waves):** deliberately break each load-bearing behavior → confirm a test goes RED; a fault that STAYS GREEN is the finding — the missing test is written this wave (mandatory). Revert IN PLACE and verify byte-identical (md5) — never `git checkout`/`restore` on uncommitted work.
- **Why per-wave (not closure):** continuous testing every wave catches missing proof at the cheapest boundary (V3C-02 + zek F14 independently-testable milestones + E.5).

> **Security review is NOT in the per-wave gate anymore (V3C-68).** It runs once, at milestone closure (Stage 4), reviewing the whole milestone's surface BEFORE the deploy/go-live step (BLOCKING). This is safe because nothing ships mid-milestone — waves don't deploy. Always-on catastrophe-class guardrails (no committed secrets, no destructive ops — permission-matrix §5/§11) still apply during every wave regardless.

#### Verdict block (structured, mandatory)

Each sub-gate writes a verdict to `docs/reviews/m{N}-wave-{W}-{review|tester}.md`:

```markdown
**Verdict:** PASS | MINOR | BLOCKING
**Risk tier (from plan):** LOW | MEDIUM | HIGH

## BLOCKING
- file:line — issue — why blocking
  Evidence: <quoted lines OR test output OR grep output>

## MINOR (queue to next M)
- file:line — issue

## PASS (what looks good)
- bullet

## Acceptance criteria evidence (PASS verdicts MUST cite file:line for each REQ)
- REQ-XX-001 → tests/unit/test_xx.py:42 (cites `# covers REQ-XX-001`)
- REQ-XX-002 → src/app/foo.py:88 + tests/unit/test_foo.py:23

## K.8 contract drift check
- shared_symbol_X: `grep -n shared_symbol_X src/` output OK
```

**Verdict combination (3a Code-Reviewer + 3b Tester):**
- 3a PASS + 3b PASS → WAVE PASS → next wave or Stage 4
- 3a PASS + 3b MINOR → WAVE MINOR → next wave + MINOR queue
- Either BLOCKING → WAVE BLOCKING → fix-and-retry pair
- PASS without file:line evidence → **automatic BLOCKING** (Quality lens)
- Any acceptance criterion without a citing test (V3C-02) → **automatic BLOCKING** (Tester lens)

### Stage 4 — Milestone Closure

Substeps; all applicable ones must succeed for the milestone to close (4.3 deploy-verify applies only if the milestone deploys). **v3 change (V3C-68):** Security review moved here from the per-wave gate and runs as a BLOCKING step (4.0) that must pass **before** the 4.3 deploy/go-live step. Quality Gate (4.1) is unchanged.

#### 4.0 — Security review (BLOCKING; runs before deploy) ★ NEW in v3 (V3C-68)

- **Profile:** `subagent-profiles/Security-Reviewer.md` (unchanged content; the *timing* moved from per-wave Stage 3b to here).
- **Invocation:** `/security-review` skill.
- **Scope:** the whole milestone's combined surface at once (more context, fewer redundant passes than per-wave). Checks (depth by the milestone's highest risk tier from Stage 1):
  - Secret scan (gitleaks) — were the Stage 2 hooks green across all waves?
  - Dependency hygiene (pip-audit + slopsquat) — every new dep verified on PyPI + maintainer-age?
  - **Web/API security baseline (`docs/security-baseline.md`):** no plaintext creds / no default-admin (V3C-11); server-side authz on every mutating route (V3C-12); CORS allowlist, not allow-all + credentials (V3C-13); security-critical config validated at startup, fails prod (V3C-51); creds/PII encrypted at rest (V3C-56); generic client errors (detail logged server-side).
  - External-surface defaults — new endpoints default-deny? RLS / authz at every boundary?
  - Prompt-injection hygiene (MEDIUM+) — untrusted external content treated as untrusted?
  - Auth / authz / payment / migration (HIGH) — senior human review trigger fires.
  - Control-class fail direction (V3C-33/45) — auth/safety fail CLOSED (tested disable switch); fairness/rate-limit fail OPEN.
  - SAST scan (HIGH only, via bandit / semgrep / Veracode-class tool if budgeted); PII / logging redaction at boundary.
  - **★ v3.1 (V3C-74):** the milestone's security-invariants list is current — every invariant cites the NEGATIVE test that fails if it is removed (deny-path release; credential-derived tenant, never request params [IDOR]; redaction).
  - **★ v3.1 (V3C-73):** built ≠ wired — every guard/limit/enforcement component is reachable from the live request path, proven by an end-to-end citing test.
  - **★ v3.1 (V3C-77, only if the project handles money):** integer minor units + currency; the Money type rejects float; float sweep of money modules.
  - **★ v3.1 (skip ledger):** every legitimately-skipped check this milestone (contract-test self-skips, tier-downs, N/A rows) is listed with a reason — silent non-execution is indistinguishable from PASS.
- **Verdict:** PASS / MINOR / BLOCKING. **BLOCKING → the milestone does NOT proceed to 4.3 deploy.** Because waves never deploy, security-at-closure always precedes any go-live; the cost of an early-wave security-shaped flaw is rework, not a leak.
- **HIGH-risk per-wave trigger (escalation):** a wave that touches auth/PII/payment/crypto/migration MAY pull a security pass forward into Stage 3 (permission-matrix); the closure security review still runs regardless.

#### 4.1 — Quality Gate (the JUDGMENT gate; ≠ per-PR CI)

```
Done Evidence assembly:
  Combine each wave's Done Evidence block into milestone log

REQ-ID coverage trace (coverage-by-req.md):
  Every REQ-ID in milestone acceptance → ≥1 test citing it (E.2)
  V3C-02 (gate, BLOCKING): EVERY acceptance criterion has a citing test;
    a reported symptom was reproduced with a failing test before the fix (red→green).
  Table format: REQ-ID | Test file:line | Status

Coverage delta:
  pytest-cov report on new + modified code in this milestone

Strict mypy + ruff clean:
  Across all modules touched

LOC budget check:
  Cumulative LOC for milestone reasonable (no surprise bloat)

cost-log.md entry:
  Bu milestone's actual token spend vs Stage 1 estimate

Verdict: PASS / MINOR / BLOCKING
BLOCKING → milestone DOES NOT close. Mini-fix-wave dispatched. Return to 4.1.
```

**v2.0 difference from per-PR CI:** Per-PR CI catches mechanical (lint/type/test/secret/dep). Quality Gate catches **judgment** — REQ-trace, coverage delta on new code only, cost discipline, contract integrity end-to-end. They detect different classes; both required.

#### 4.2 — Capture

```
process-log.md S{N} entry (G.1, 3-10 lines, ends with Lesson: tag)
decisions.md new ADRs via /log-decision skill
playbook-seeds.md proposed seeds → user-approved → ACTIVE
retrospectives/m{N}-retrospective.md (M≥3, G.12 format)
  Hook fails closure if file is missing
  Verdict columns: PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY
roadmap-{date}-post-m{N}.md (I.1 snapshot)
AGENTS.md diet check (≤150 hard cap)
Disciplines-retired count (anti-bloat per PM)
★ v3.1: dated EXPERIENCE.md entry for THIS milestone (V3C-81, from docs/EXPERIENCE.template.md;
        no secrets/PII; findings cite evidence) — the quarterly handover BLOCKS without it
★ v3.1: the retrospective ANSWERS the previous retro's carried question and POSES one (V3C-79);
        a rule proposed twice but never built is BUILT or DROPPED
external-influences-impact.md update if article absorbed
```

**v3.2 (V3C-83/84):** §4.2 Capture now GENERATES the owner review pack — `docs/closure-report-m{N}.md` from `docs/closure-report.template.md` (raw-referent derived; BLOCKING prose architecture-delta) — and appends the mechanical trust-telemetry rows that drive the autonomy ladder (`docs/autonomy-protocol.md` §6).

#### 4.3 — Deploy + go-live readiness (v2.1: deploy-verify; v2.2: + go-live readiness — only if the milestone deploys)

**Precondition (v3, V3C-68):** the 4.0 Security review must be PASS before any step below runs. No deploy until security passes.

The gap v2.0 missed: Stage 4 closed at "image built + Mac green," which is **not** "the new code is live AND the dependencies actually work." A green `/health` proves the process is *up*, never *which code* it is, and never that downstream dependencies respond. v2.2 closes both halves:

```
IF this milestone produces a deploy (staging or prod):

  A. WHICH CODE IS LIVE (L.7 / v2.1):
  1. The deploy references a NEW image tag / git SHA, not a cached one.
     REMEMBER: a pod *restart* re-runs whatever image the deployment already
     references. Restart != rebuild != re-pull. A restart will NOT pick up new code.
  2. curl <target>/health | jq .build  — MUST equal the tag/SHA you intended to ship
     (from APP_BUILD, L.7). If not, the old image is still running (e.g. a feature merge
     clobbered the Dockerfile, K.10) — fix the build pipeline; do NOT just restart.
  3. DevOps-owned build/deploy files (Dockerfile, /deploy/**, CI) not clobbered (K.10).

  B. GO-LIVE READINESS (NEW in v2.2 — configured != working):
  4. L.8 dependency liveness: invoke EVERY external dependency once for real
     (`make smoke-deps`: model / queue / store / callback) and inspect the RESULT,
     not the config/catalog screen. "Listed with valid creds" != "serves requests."
  5. L.9 config reaches the process: read each critical config value back from INSIDE
     the running process (in-pod env / safe echo: SET/EMPTY + length, never the value).
     "Set in the values file" != "set in the process" (injection layers drop keys).
  6. E.6 pipe attribution: send one real request; even if a dependency is down, confirm
     the downstream's own run log shows the call arrived attributed to your service
     (proves auth + connectivity + routing; isolates the blocker to the named node).
```

Grounding: 12-factor "build / release / run" — releases are an append-only ledger with unique, immutable IDs; the run stage only launches a *selected* release. L.7 answers "which release is live?" in one HTTP call (the S34 hour); L.8/L.9/E.6 answer "is the pipe actually working end-to-end?" (the S35 hour: a model "listed but Invalid model," and an AppCode "set in values but `{}` in the pod").

#### 4.4 — Handoff

```
note.txt refresh (≤30 lines, every milestone)
when_<event>.txt update/archive (if applicable)

IF M%3 == 0 (quarter boundary):
  ★ v3.1 STEP 0 (BLOCKING, V3C-81): docs/EXPERIENCE.md must hold a dated entry keyed to the
    latest closed milestone — no handover without a current EXPERIENCE
  /quarterly-handover skill generates docs/handovers/handover_q{M/3}.txt
  Content: quarter range, shipped REQ-IDs, new ADRs, activated seeds,
           open risks queued, cumulative cost+tests+coverage, AGENTS.md state,
           next quarter plan skeleton, fresh-agent navigation map

Harness diet (every 90d, i.e., every quarter):
  Count hooks / skills / MCPs
  Retire any skill not fired in 90 days
```

---

### Stage 5 — Maintenance Loop (post-deploy; standing) ★ NEW in v3.4 (V3C-98)

Runs after Stage 4.3 go-live, for the life of the deployment. **A fix wave IS a wave** — Stage 2
dev-test loop, Stage 3 fresh-eyes Code-Reviewer + Tester, risk tiers with ⛔-glob auto-HIGH, and
the wave checklist all apply BY REFERENCE. What differs: intake is a reproduced RED TEST (the
frozen spec — no plan-signing); closure is the **fixpack** (`docs/fixpack.template.md`), not a
full closure report; and the owner's gate is **out-of-sandbox local verification** (reproduce →
confirm gone → local tests → sign; BLOCKING). Security floor, emergency path, fix probe + watch
window, capture coupling, 3-strikes gate-attribution, and the N=3 fix-on-fix refactor trigger are
specified in the fixpack template and `v3.4-ratification.md` §2. LOW-tier valve: combined
reviewer, batched owner verification, no red test for trivially-verifiable visual fixes.

## §3.5 — Theme L: Distributed correctness## §3.5 — Theme L: Distributed correctness, durability & multi-node safety (NEW in v2.1)

Most v2.0 disciplines target *single-node* correctness. The moment a service runs at `replicaCount > 1` behind rolling deploys, a new failure class appears: work the caller was told you *accepted* is silently lost, the same job is processed twice, or a load spike OOMs the shared store. These bugs pass every single-threaded green test and only surface under production pod churn. Theme L is the discipline for that class. It graduated from the EF-AI M12 milestone, where the K.7 fresh-eyes Code-Reviewer returned **its first BLOCKING on the project — and it was correct on a defect the author's own green tests masked**: the "durable" enqueue ran in a fire-and-forget task scheduled *after* the sync ack, so durability was illusory.

**Apply Theme L when** a service (a) runs more than one replica, (b) accepts work synchronously then completes it asynchronously (ack-then-callback / queue / webhook), or (c) shares state (idempotency, locks, sequence numbers) across replicas. Skip it for single-node, request/response-only services — but the version-stamped probe (L.7) and the boot guard (L.6) are cheap enough to keep on by default.

The nine seeds (full text + origin in `.agents/rules/playbook-seeds.md`):

- **L.1 — Enqueue, then ack.** The durable write (the cheap `LPUSH`/`INSERT`) happens *before* you return `accepted: true`, inline on the request path — never in a fire-and-forget task scheduled after the ack. "Ack, then enqueue" is a slower way to lose the message. The background worker does the slow work (AI call, callback); it never owns the durability commit.
- **L.2 — Reserve, then release on reject.** If the accept path reserves state early (an idempotency slot, a lock), and a later step sheds load or fails, roll the reservation back before returning the error — otherwise the caller's retry sees half-reserved state ("duplicate") and is stuck forever. Reserve -> on-failure-release is the invariant.
- **L.3 — Promise at-least-once, never exactly-once.** Exactly-once across a network boundary needs the receiver's cooperation, so declare **at-least-once**, carry a stable idempotency key (the customer's `taskId`) + a byte-identical signed body, and put "deduping on the key is your job" in the customer-facing API doc. (ADR D-043.)
- **L.4 — Cross-node election is one atomic op.** Electing a single winner across replicas (idempotency, leader, dedup) uses one atomic primitive — `SET key val NX EX`, `INSERT ... ON CONFLICT` — never `GET`-then-`SET`. The read-then-write form has a window where two replicas both think they won. Prove it with a concurrency test racing N callers at one shared backend (e.g. fakeredis `FakeServer`) asserting `sum(created) == 1`. (ADR D-044.)
- **L.5 — Bound the durable queue + load-shed.** An unbounded durable queue OOMs its store when the consumer wedges. Put a configurable depth cap on the producer; past it, reject the accept with a transient 503 (load-shed) rather than grow without bound. A soft `LLEN >= cap` check only ever *rejects*, never drops an accepted item. Pairs with L.2 (release the reservation on the 503). Off by default (0 = unbounded).
- **L.6 — Scale-out preconditions are a boot guard.** A process can't know its own replica count, so it can't self-detect "I'm multi-replica but configured for single-node." Make the operator *declare* scale-out via an explicit flag (`REQUIRE_REDIS=true`) and **refuse to boot** if its preconditions are absent. Pair with a fail-fast config-doctor that validates ALL required env at once and prints one readable block (instead of one-crash-per-missing-var). Gate the doctor to prod/staging so dev/CI on defaults aren't blocked; forgetting the flag fails *safe*.
- **L.7 — Version-stamp the health/readiness probe.** Bake the build identity (image tag / git SHA) into the app via `APP_BUILD` and surface it in `/health` as `{status, version, build}`. A green probe proves the process is *up*, never *which code* it is; the stamp closes that gap (one curl vs three exec-and-grep checks). **Day-1 baseline** — the starter ships it from the first commit (additive fields only; the liveness contract is untouched). See Stage 4.3.
- **L.8 — Configured ≠ working (NEW in v2.2).** A dependency in a provider catalog / config UI with accepted credentials does NOT mean it serves requests. Before calling an integration "ready," **invoke it once for real** (a Test Run / smoke call via `make smoke-deps`) and inspect the *result*. (EF-AI S35: a MaaS model listed with a valid token returned `ModelArts.81009 "Invalid model"` — nothing deployed; only a Test Run exposed it.) See Stage 4.3.
- **L.9 — Verify config reaches the *process* (NEW in v2.2).** Between "I set it in the values file" and "the process sees it" sits an injection layer (Helm chart, operator, secret mount) that can silently drop a key. **Read the value back from inside the running process** (its env / a safe echo that prints SET/EMPTY + lengths, never secret values) after every config change. (EF-AI S35/M11: an AppCode under `configMap.data` was never injected — the pod saw `{}`.) Pairs with L.6. See Stage 4.3.

**What Theme L is NOT:** it is not a mandate to build a distributed system. It is the checklist you run *before* a single-node-shaped service is scaled out, so the scale-out doesn't silently lose or double-process work. The cheapest place to apply it is the milestone plan (name the L.* seeds in the acceptance criteria); the most expensive is production.

---

## §3.6 — Theme: Agent-Native / LLM-Ops (CANDIDATE container — NEW in v3)

The v3 harvest's single largest coverage gap is **agent-native / LLM-orchestration + API-gateway** engineering — building systems where an LLM is in the request path (providers, prompts, tracing, guardrails, gateways, rate-limiting, fallbacks). GP was distilled from a backend/Python project, so it under-covers this.

**Why this is a *candidate container*, not an adopted theme.** Most of the evidence is **one ecosystem**: the Botim AOP / aop_growth / aop-portal platform (BotIm-AOP, aop_growth, aop-portal) plus the **one-api ≈ NewAPI** gateway family (one-api, HSC-MaaS). The council's load-bearing rule (skeptic + 5 seats): *down-weight intra-ecosystem agreement; a finding is strongly convergent only when it also appears outside one ecosystem or re-derives GP's own design.* So v3 **charters the theme as a holder** and adopts only the few seeds that cross an ecosystem boundary or validate GP — the rest wait for a 2nd independent ecosystem to graduate.

**Adopted now (these crossed a boundary or matched GP — see the guardrails/templates in §0, `docs/security-baseline.md`, and `.agents/rules/`):**
- **V3C-33 + V3C-45 — control-class fail direction (paired guardrail):** auth/safety fail CLOSED (with a tested disable switch + correct domain scope); fairness/rate-limit fail OPEN. The one genuinely cross-ecosystem agent-native pair.
- **V3C-08 + V3C-36 — agent least-privilege + human-confirm on writes (guardrail):** per-agent tool allowlist; LLM proposes, deterministic code acts; human-confirm all writes (CI and runtime). Cross-validated by GP's own issue-agent.
- **V3C-44 — one canonical mock per integration + contract test (template):** see §testing below.
- **V3C-56 — encrypt creds/PII at rest (guardrail):** in `docs/security-baseline.md`.

**CANDIDATE seeds (NOT active — promote on a 2nd independent ecosystem; full text in `v3-candidate-register.md` and the candidate block in `.agents/rules/playbook-seeds.md`):**
- LLM orchestration: **V3C-32** provider registry (runtime-swappable, probe-verified), **V3C-34** deterministic fallback tagged `source`, **V3C-35** machine-readable LLM output contract + neutral default on parse-fail, **V3C-37** dual-grounding (LLM judges, deterministic queries for checkable numbers), **V3C-38** number provenance (real/simulated/estimate, no silent imputation), **V3C-39** trace every LLM call from the first call, **V3C-40** new capability = new single-purpose agent (not a new router skill), **V3C-41** separate ephemeral AI/session state from durable business state, **V3C-42** rule-based retrieval over vectors on small corpora, **V3C-58** split read-only data plane from write/action plane, **V3C-59** prove "no side-effects" by tracing the path + a negative grep.
- MCP / tool-server: **V3C-43** MCP servers on stateless HTTP + a lazy process-lifetime connection pool.
- API-gateway / edge: **V3C-46** streaming token rate-limiting (pre-reserve, post-adjust), **V3C-47** structured 429 + `Retry-After` (sliding vs fixed window by precision), **V3C-48** multi-DB ORM abstraction encoded as rules before the first cross-DB bug, **V3C-61** circuit-breaker with tri-state status (enabled / manually-disabled / auto-disabled), **V3C-62** classify upstream failures by stable signals (status/type), never by error-message substrings, **V3C-66** one minimal lifecycle interface per backend (adaptor pattern).

When you build in this space and hit one of these *outside* the Botim/one-api ecosystems, capture it in the milestone retrospective so it can graduate at the next cut.

---

## §4 — Issue Management (3-layer model)

The pipeline's full GitHub-automated flow. Human review is required ONLY at PR merge.

### Layer 1 — Pure CI (no agent, deterministic)

Runs on every push / PR. No model. Fires on issue/PR events:
- **Tests** — project test suite
- **Lint** — ruff / equivalent (opt-in per Stage 0 choice)
- **Secret scan** — gitleaks
- **Dependency audit** — pip-audit
- **Auto-label by title keyword / changed paths**
- **Stale-issue bot** — close issues with no activity for 60 days
- **Link issue↔PR check** — every PR must reference an issue

CI hardening applied to every job:
- Least-privilege token (`permissions: contents: read` workflow level)
- Job timeouts (`timeout-minutes: 15`)
- Concurrency cancel (`concurrency:` block)
- Dependency caching
- **Pinned action SHAs** (not `@v1` tags) — supply-chain protection

### Layer 2 — CI-Triggered Agent (headless Claude, gated)

Runs Claude in headless mode when an issue event needs judgment:
- `agent:triage` label → `/triage-issue` skill → diagnosis comment
- `agent:fix` label → `/fix-issue-prepare` then `/fix-issue-implement` → draft PR

**Rollout:** Shadow-mode for first milestone (agent comments only, never opens PRs). Graduate to draft PR after 1 successful milestone of manual /fix-issue use.

**Safety rails (mandatory, from incoming team's §13.6):**
- Agent opens drafts, NEVER merges (branch protection on `main` enforces).
- Draft PRs only (cannot self-fast-merge).
- Label-gated triggering (`agent:triage` / `agent:fix` only; no firing on every drive-by issue).
- Least-privilege token (`contents: write`, `issues: write`, `pull-requests: write`; nothing more).
- Branch discipline (`fix/issue-<n>-<slug>` only, never `main`, never force-push, never `--no-verify`).
- Secret scan still gates the agent's PR like any other.
- Bounded scope (touches only files relevant to the issue; balloons → stop and ask).
- Idempotent + deduped (`concurrency:` + `/file-issue` searches for duplicates).
- Cost ceilings (`timeout-minutes: 20` per agent job; monthly cap per repo).
- ANTHROPIC_API_KEY rotation calendar (90 days).

### Layer 3 — Scheduled + Interactive

- **Scheduled** via `/schedule` (cron remote agent) or `CronCreate` (headless job): dependency hygiene sweeps, weekly "open issues for problems found" sweeps, backlog triage grooming.
- **Interactive** — engineer in a session, using GitHub/GitLab MCP server to read / open / comment / close issues during pairing.

### Routing rule (where to put the work)

```
New feature in milestone plan?            → K.4 wave (Stage 2)
Single bug found, label agent:fix?        → /fix-issue-implement (Stage 2 alternate mode)
Drive-by issue from external user?        → /triage-issue (Layer 2)
Periodic backlog hygiene?                 → Layer 3 scheduled sweep
Engineer pairing on tickets?              → Layer 3 interactive + MCP
```

---

## §5 — Hooks (new in v2.0)

`.claude/settings.json` ships with **2 baseline hooks** day-1. More earn their way in only after observed rule violations (≥3 times before promotion).

### Baseline hook 1 — PreToolUse: block .env writes

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT_FILE_PATH\" | grep -qE '\\.env($|\\.|/)'; then echo 'BLOCKED: writes to .env are denied per permission-matrix.md §6'; exit 1; fi"
          }
        ]
      }
    ]
  }
}
```

### Baseline hook 2 — PostToolUse: run `make check`

```jsonc
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$CLAUDE_PROJECT_DIR\" && make check 2>&1 | tee -a .claude/last-check.log"
          }
        ]
      }
    ]
  }
}
```

**Anti-pattern (per ai-native.md §11):** Hooks that silently rewrite output. All hooks must log + exit non-zero on failure.

**Hook promotion rule (PM lens):** A rule in AGENTS.md or `.agents/rules/practices.md` gets promoted to a hook ONLY after Claude violates it 3+ times in measured sessions.

---

## §6 — Skills (10 starter skills)

Each lives at `.claude/skills/<name>/SKILL.md`. Project-scoped (committed). Two-line frontmatter (name + description); the description is what Claude uses to auto-trigger.

### Issue management (4 skills)

1. **`/triage-issue`** — Read issue, attempt repro, label by real root cause, post diagnosis comment. Does NOT write code.
2. **`/fix-issue-prepare`** — Create branch `fix/issue-<n>-<slug>`, write failing test FIRST (red). Stop here for review. (Quality split from monolithic /fix-issue.)
3. **`/fix-issue-implement`** — On a prepared branch with a red test, implement smallest fix to green. Run lint + tests + Stage 2 commit-gate. Push branch + open DRAFT PR. Never merge.
4. **`/file-issue`** — Open well-formed issue with repro steps, observed/expected, severity. Search for duplicates first.

### Workflow (2 skills)

5. **`/test-and-commit`** — Run tests; if green, draft conventional commit matching repo style; ask before committing. Never `--amend` or `--no-verify`.
6. **`/repo-review`** — Load `.agents/rules/` then run `/review` against current diff. Flag violations of practices.md, missing tests, README drift.

### Lifecycle (3 skills)

7. **`/quarterly-handover`** — At M%3==0 milestone closure, generate `docs/handovers/handover_q{N}.txt` from process-log + decisions + retrospectives + cost-log.
8. **`/log-decision`** — Enforces ADR-lite format (D-NNN with Status/Decision/Rationale/Mitigation/Revisit-when). Append-only, never edit in place.
9. **`/retrospect`** — Walks G.12 retrospective format at M≥3 closure. Verdict columns PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY.

### Utility (1 skill)

10. **`/standup`** — LLM-free project state dump (calls `scripts/standup.sh`).

### Candidate (NEW in v2.1; template now, skill after a 2nd use)

11. **`/pm-status` (CANDIDATE)** — emit a PM-readable status snapshot: a status table (✅ / 🟡 / ⛔), plain language, "what's there / what's missing" per item, external blockers called out. Pairs with G.9 (PM-friendly risk register). Shipped first as `docs/pm-status.template.md`; graduates to a skill only after it's used + valued a second time (anti-bloat: don't add a skill on N=1). Origin: EF-AI `docs/pm-status-2026-06-11.md`.

**Skill anti-pattern:** Duplicating built-ins. Don't write a generic `/code-review` skill — Claude Code's `/review` already exists. Custom skills wrap built-ins with this-repo specifics.

**Skill diet:** Quarterly check at handover — retire any skill not fired in 90 days.

---

## §7 — `.agents/rules/` (canonical rulebook)

Replaces v1.1's `docs/discipline-*.md` files. Three files at bootstrap:

- **`practices.md`** (committed) — portable engineering rules: web search, code quality, knowledge sync, README maintenance, tests for new capabilities, logging at boundaries.
- **`environment.md`** (**gitignored**) — per-developer machine specifics: shell, language runtime, local services. Each new clone generates their own on first session.
- **`playbook-seeds.md`** (committed) — full 64+8 seed compendium. Themes A-K + v1.1 ADDENDUM (F.6/F.7/F.8/F.9/C.9 ACTIVE + F.5/E.4/L' CANDIDATE).

Optional files added as needed:
- `architecture.md`, `data-model.md`, `deploy.md`, `security.md`, `issues.md`, etc.
- `retrospectives/` directory contains G.12 entries (also remains discoverable from `docs/retrospectives/` per consortium decision).
- `handovers/` directory contains `handover_q{N}.txt` (per Quality lens; alternative committed location is `docs/handovers/`).

**Why gitignored `environment.md` matters:** the moment a Windows or NixOS developer joins, committed env paths break discipline. Per-developer means no cross-machine pollution.

**V3C-52 — `.agents/rules/` + a PROCESS.md routing index (NEW in v3; independent confirm).** Two external gateway projects (BotIm-AOP F3/F4) re-derived GP's own `.agents/rules/` directory **and** the AGENTS.md context-diet via a routing index — strong independent validation of GP's design (GP predates them). v3 makes the routing-index explicit: keep `AGENTS.md` thin (navigation, ≤80/150) and treat `PROCESS.md`/`AGENTS.md` §8 as a **routing index** that points to the right `.agents/rules/*.md` or `docs/*.md` for the task at hand, with lazy doc-loading — read the pointer, then load only the doc you need (token economy). This is what §8's "Detail docs" pointer block already is; v3 names it the routing index and keeps it the single discovery surface. For a forked codebase, V3C-60 (candidate) suggests a two-tier AGENTS.md (root = pipeline workflow; inner = code rules, inner wins for code).

**V3C-44 — canonical mock per integration + contract test (NEW in v3; testing convention).** For each external integration, build **one canonical mock/fake-client before the integration code** (extends K.1's Protocol-typed `clients/` fake), consolidate any parallel mocks into it, and keep **one contract test that runs against the real API** so the mock can't silently drift from the real contract. Tests drive the canonical fake (J.4 in-process pattern), never bespoke per-test stubs. A closure check confirms: one mock per integration + a live contract test exists (see `docs/closure-checklist.md` §A). Evidence crossed 3 gateways (BotIm-AOP F6/F8, HSC-MaaS F6).

---

## §8 — AGENTS.md design (PROJECT vs UNIVERSAL)

`AGENTS.md` is canonical. `CLAUDE.md` is a symlink to `AGENTS.md` (set up at bootstrap via `ln -s AGENTS.md CLAUDE.md`). One file, two names, zero drift.

**Size:** ≤80 lines target, ≤150 hard cap.

**Sections:**

```markdown
# AGENTS.md

<!-- ═══════════════ PROJECT-SPECIFIC (you fill) ═══════════════ -->
## 1. Project context
- Name, Customer, Stack (must match pyproject.toml — C.4), Target env, REQ-ID prefix scheme

## 2. Customer glossary
- Customer term → our term

<!-- ═══════════════ UNIVERSAL (do not edit) ═══════════════════ -->
## 3. Workflow
- Read order, plan before implement, tests non-negotiable, decision log discipline, capture discipline

## 4. Subagent dispatch
- K.4 paralel waves, K.6 prompt scope, K.7 fresh-eyes Code-Reviewer, Security-Reviewer per wave
- Quality at MILESTONE CLOSURE (Stage 4), not per-wave
- K.8 contracts grep-verified in plan

## 5. Sensitive areas (default-deny)
- See permission-matrix.md. Forbidden: production DB write, force-push, git reset --hard,
  LLM-driven revert, secret commit, /v2 contract change without ADR, auth/PII/payment without senior review

## 6. Milestone closure
- Walk closure-checklist.md
- Quality Gate (4.1) judgment + REQ-trace + Done Evidence
- Capture (4.2) process-log + ADRs + seeds + retrospect M≥3
- Deploy-verify (4.3) if milestone deploys: curl /health, build==intended (L.7), CODEOWNERS not clobbered (K.10)
- Handoff (4.4) note.txt always; if M%3==0 quarterly handover via /quarterly-handover

## 7. Final reply (Done Evidence template)
- Files changed / Tests run + outcomes / Assumptions / New ADRs (D-IDs) / Risks queued

## 8. Detail docs
- .agents/rules/practices.md
- .agents/rules/playbook-seeds.md
- docs/onboarding.md
- docs/tool-suitability.md

<!-- DIET DISCIPLINE -->
<!-- This file ≤80 target, ≤150 hard cap. Detail to .agents/rules/practices.md -->
<!-- Seed C.5: AGENTS.md is navigation, not encyclopedia. -->
```

---

## §9 — Memory system (scoped)

`~/.claude/projects/<slug>/memory/` indexed by `MEMORY.md`. v2.0 uses **only 2 types** (Quality lens kept the others out):

| Type | Use | Example |
|---|---|---|
| **`reference`** | Pointers to canonical files | "Pipeline bugs tracked in `docs/decisions.md` D-021; permission rules at `permission-matrix.md`" |
| **`feedback`** | BLOCKING-class lessons with WHY + file:line citation | "BLOCKING M3 W1 wave-1-security.md:14 — Secret committed in fixture; rule: any new test fixture grep'd for high-entropy strings before commit" |

Rejected types: `user` (use git config / handover.txt instead), `project` (use `docs/decisions.md` / process-log.md).

**Sync rule:** When memory contains a pointer to a canonical file, and the canonical file changes, the memory pointer must update in the same step.

---

## §10 — MCP server configuration

`.mcp.json` committed at repo root. Default install at Stage 0:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

(GitLab equivalent for GitLab projects.)

**Tokens stay in `.env` (gitignored).** Stage 0 baseline hook blocks writes to `.env`; rotation calendar set up for `GITHUB_TOKEN` quarterly.

**MCP promotion rule:** Other MCP servers (Linear / Notion / Slack / etc.) are opt-in per project. Add only when:
1. Team genuinely uses the tool daily.
2. ROI > maintenance cost (auth tokens, breaking changes, server uptime).

---

## §11 — Permission matrix (default-deny + BLOCKING taxonomy)

Lives at `permission-matrix.md`. 9 categories from v1.1, plus **two new sections** for v2.0:

### NEW Section 10 — OS-aware permission patterns

Permission patterns are keyed by **tool name**, not command. `Bash(...)` only matches Bash tool calls; `PowerShell(...)` only matches PowerShell. On Windows, carry both prefixes for shell-agnostic commands.

```jsonc
// In .claude/settings.json permissions.allow:
// Cross-platform shell-agnostic (e.g., git):
"Bash(git status:*)",       "PowerShell(git status:*)",
"Bash(git diff:*)",         "PowerShell(git diff:*)",
"Bash(git log:*)",          "PowerShell(git log:*)",
"Bash(git branch:*)",       "PowerShell(git branch:*)",
// Native unix:
"Bash(ls:*)",  "Bash(cat:*)",  "Bash(grep:*)",
// Native PowerShell:
"PowerShell(Get-ChildItem:*)",  "PowerShell(Test-Path:*)",
// GitHub CLI (read-only):
"Bash(gh issue list:*)",   "Bash(gh issue view:*)",
"Bash(gh pr list:*)",      "Bash(gh pr view:*)",
"Bash(gh label list:*)",
```

Write actions (`gh issue create`, `gh pr create`) stay OUT of allowlist — they remain prompts interactively, run unattended only inside CI (Layer 2) where rails enforce them.

### NEW Section 11 — BLOCKING taxonomy (verdict criteria)

**BLOCKING (must fix before next wave / milestone closes):**
- REQ-ID unmet (acceptance criteria not green)
- Test red
- Secret leak (gitleaks fires; secret committed to git)
- K.8 contract grep-verify miss (renamed symbol; broken contract surface)
- Coverage drop on touched module
- PASS verdict without file:line evidence for each acceptance criterion
- Auth/PII/payment/migration change without senior human review
- Permission matrix region touched without prior ADR

**MINOR (queue to next M):**
- Style / doc drift / non-critical lint
- Cross-wave K.9 candidates (gap-fill outside scope)
- AGENTS.md size approaching 150 cap (warning, not BLOCKING until > cap)

**Catastrophe-class (DENY always, ADR cannot override):**
- `git reset --hard` / `git push --force` / `git checkout -- <file>` outside controlled recovery
- `rm -rf` on untracked dirs
- `DROP TABLE` / equivalent destructive DB op
- Commit `.env` / API key / AppCode / HMAC secret to git
- Log customer PII without redaction
- Self-merge agent's own PR (humans only)

---

## §12 — How to bootstrap a new project from v2.0

### Day-0 (~30 minutes)

```bash
# Path A: clone the GPv3 starter
cp -r ~/Desktop/Company/General_Pipeline/general_pipeline_v3 ~/Desktop/<NEW_PROJECT>
cd ~/Desktop/<NEW_PROJECT>

# Replace symlink for CLAUDE.md to point at AGENTS.md
rm CLAUDE.md  # if it exists from a prior clone
ln -s AGENTS.md CLAUDE.md

# Initialize
git init && git add -A && git commit -m "chore: bootstrap from pipeline v2.0"

# Day-1 baseline
make install
make check         # MUST be GREEN; if not, fix before any feature code
```

### Day-1 (PROJECT placeholders, ~1-2 hours)

Edit these:
- `AGENTS.md` §1-2 (name, customer, stack, REQ-ID prefix, glossary)
- `pyproject.toml` name + initial deps (mirror in AGENTS.md per C.4)
- `README.md` one-paragraph intro
- `permission-matrix.md` — review §1-9; add project-specific sensitive areas if any (e.g., HIPAA path)
- `.mcp.json` — set token env vars correctly; verify GitHub/GitLab access
- `docs/prd.md` — start numbering customer requirements as REQ-IDs (seed A.1)
- `docs/architecture.md` — §5 PRD↔Arch conflict table (seed A.2)
- `docs/decisions.md` — your project decisions begin at **D-100** (D-001..D-099 reserved; D-001..D-005 universal; process ADRs use `P-00x`). For an inherited project that already uses low D-ids, run the FB-2/B.6 reconciliation recipe.

**Then run host-side one-time admin actions:**
- GitHub: Settings → Branches → Add rule for `main`:
  - Require status checks: `test`, `lint` (if opted in), `secret-scan`
  - Require pull request reviews before merge: 1+
  - Restrict who can push to matching branches
- Add `ANTHROPIC_API_KEY` to repo secrets (masked + protected for GitLab)
- Schedule 90-day rotation reminder for `ANTHROPIC_API_KEY` + `GITHUB_TOKEN`
- Create labels: `agent:triage`, `agent:fix`, `auto:fix`

### Day-2+ (first milestone)

Follow Stage 1 → Stage 4 normally. M1 is intentionally small (validate the pipeline mechanics).

---

## §13 — Workload estimation (v2.0 update)

| Phase | Time |
|---|---|
| Bootstrap (Stage 0 one-time) | 4-8 hours |
| Per milestone (Stages 1-4) | 1-3 days wall-clock + 50k-500k tokens |
| Per quarter (handover_qN.txt) | ~3 hours extra |
| Per retrospective (M≥3) | ~1 hour |
| Risk-tier HIGH (auth/PII/payment) | 2× review time multiplier |

**v2.0 NEW overhead:**
- Hook setup (one-time, ~30 min for 2 baseline hooks)
- Skill setup (one-time, ~3 hours for 10 starter skills)
- CI workflow setup (one-time, ~1 hour with hardening pass)
- MCP server setup (~30 min for GitHub/GitLab default)

**v2.0 NEW savings:**
- `/triage-issue` reduces manual issue triage from ~10 min/issue to ~3 min (review verdict + label)
- `/fix-issue-implement` for label-gated bug fixes: ~2-4 hours saved per issue once shadow-mode trusted
- `/quarterly-handover` reduces handover_q{N}.txt authoring from ~2 hours to ~20 min review

Example — 12-milestone project (rough):
```
Bootstrap         : 4-8 hours
12 × milestone    : 12 × 1-3 days   = 12-36 days wall-clock
4 × quarterly     : 4 × ~3 hours    = 12 hours overhead
4 × retrospective : 4 × ~1 hour     = 4 hours overhead
Phase exit        : ~4 hours
v2.0 setup        : ~5 hours one-time (hooks + skills + CI + MCP)
                  ────────────────────────────────
Total: ~13-38 days wall-clock + ~35-55 hours overhead
Tokens: ~3-5M total
```

After first 2-3 milestones, refine with measured velocity.

---

## §14 — Anti-patterns (consolidated from both sources)

### Bootstrap anti-patterns
- ❌ Skipping `make check` GREEN on Day-1
- ❌ Editing UNIVERSAL section of AGENTS.md without ADR
- ❌ Hard-coding `python3.11` literal in scripts (use range, seed C.2)
- ❌ Configuring no branch protection on `main` — defeats CI's purpose
- ❌ Hooking before measurement — promote to hook only after 3+ violations

### Plan anti-patterns
- ❌ Mixing planning with execution
- ❌ Skipping risk register because "we know this one" (G.9)
- ❌ Wave tasks >5 min scope (K.6 has upper bound)
- ❌ Not declaring subagent profile source

### Wave execution anti-patterns
- ❌ Subagent broadening own scope mid-flight (K.6 ceiling)
- ❌ Skipping commit-gate "just this once"
- ❌ Subagent committing secret (hook would catch; never test by trying)
- ❌ Pasting `gh` JSON parsing into a skill instead of using GitHub MCP

### Review anti-patterns (K.7)
- ❌ Same subagent reviewing its own code (defeats fresh-eyes)
- ❌ Mixing automated checks with judgment review (split by failure mode)
- ❌ Treating MINOR findings as "we'll get to it" (queue to next-M)
- ❌ PASS verdict without `file:line` evidence per acceptance criterion

### Closure anti-patterns
- ❌ Editing roadmap-N in place (snapshots not state, I.1)
- ❌ Auto-approving every proposed seed (user must approve)
- ❌ Skipping retrospective "because smooth"
- ❌ Editing existing ADRs (B.2 supersede-don't-edit)

### Issue management anti-patterns
- ❌ Layer 2 agent firing unlabeled (no cost control)
- ❌ Layer 2 agent auto-merging (must stay draft-only)
- ❌ Cross-PR sprawl in `/fix-issue-implement` (touch only the issue's files)
- ❌ Skipping shadow-mode (graduate L2 only after 1 milestone trusted)

### Catastrophe-class (always denied)
- ❌ `git reset --hard` / `git push --force` / `rm -rf`
- ❌ Drop database table
- ❌ Commit secrets
- ❌ Self-merge agent PR (only humans)

---

## §15 — Open Questions / Known Gaps (updated for v2.2)

Honest about what the pipeline does NOT yet handle. **[CLOSED]** / **[NARROWED]** tags mark what each increment changed.

1. **Real production environment proof — [NARROWED, x2].** EF-AI took the M12 image to a real multi-node prod deploy (Theme L + Stage 4.3); EF-AI S35 then brought up the external model via a UI (L.8/L.9/E.6) and HCS-MaaS bootstrapped a 2nd independent project from the starter. Prod-deploy evidence is now N=2 projects (still 1 org).
2. **Multi-team coordination — [NARROWED].** K.10 / CODEOWNERS marks the app/DevOps boundary. Full two-team handoff cadence still requires extension.
3. **Post-deploy operations — [NARROWED, x2].** Stage 4.3 now covers "which code is live" (L.7) AND "is the pipe working" (L.8/L.9/E.6 go-live readiness). Still open: SLA monitoring, alerting, on-call playbook — closure stops at go-live, not steady-state ops.
4. **Customer onboarding feedback loop.** Pipeline produces *for* the customer; their first 10 hours with the API is not modeled.
5. **F.5 Veracode-class SAST tooling.** CANDIDATE; first milestone touching auth/PII should exercise + graduate to ACTIVE.
6. **E.4 TDD-with-AI — [CLOSED, graduated v2.1].** ACTIVE, scoped to "new module + locked K.8 contract." Watch for over-application.
7. **L' BMAD additional *review* profiles (beyond Code + Security) — [NARROWED].** Still CANDIDATE. A standing third subagent-review profile graduates only after ≥2 milestones of PULLED-WEIGHT.
8. **Council planning — [CLOSED, graduated v2.2].** v2.1 deferred promotion pending a 2nd payoff; EF-AI ran two more blind councils and this v2.2 cut was itself decided by a 7-role blind council. Now a **standing OPTIONAL Stage-1 variant** (kept optional for anti-bloat); the blind-parallel-subagent ballot is the captured recipe.
9. **K.11 agent-driven prod UI — [NEW candidate v2.2].** Capability is N=1 (CANDIDATE); its **guardrails are ACTIVE** in the permission matrix now. Graduate the capability after a 2nd payoff (the council bar).
10. **Bootstrap-gate coverage — [NEW, v2.2].** `make bootstrap-check` enforces the deterministic Stage-0 invariants; some checks are still heuristic (e.g. "doc is still a template", license review existence). Tighten the detectors as more projects exercise them.
11. **Layer 2 cost ceiling enforcement at scale.** Manual monthly check; future: automated cost-anomaly alarm.
12. **Merge queue behavior under heavy /fix-issue load.** Observe queue depth in first quarter.

### Retirement pass (anti-bloat, run each cut)

v2.2 ran the deliberate retirement sweep: **0 disciplines retired this cycle.** Both projects exercised existing disciplines (Theme L, Stage 4.3, council, K.7) and added new ones; nothing went un-fired long enough to retire. The *retire-as-you-add* rule still holds: a future cut should retire any v2.x rule not fired across the prior three milestones. (Cheapest retirement signal: a recurring THEORETICAL verdict for the same discipline across G.12 retrospectives.) Note K.11's capability is deliberately held at CANDIDATE rather than promoted on N=1 — the same anti-bloat discipline.

When you exercise any of these in your project, capture in the milestone retrospective and propagate back via the discussions doc.

---

## §16 — File Map (where to find everything)

| Question | File |
|---|---|
| Pipeline visual? | `pipeline-schema.html` (open in browser) |
| Full design (this doc)? | `pipeline-design.md` |
| House rules per project? | `AGENTS.md` (PROJECT/UNIVERSAL markers) |
| Build / test commands? | `Makefile` (`make check`, `make test`, `make demo`) |
| What is + isn't allowed? | `permission-matrix.md` (9 categories + BLOCKING taxonomy + OS-aware) |
| Engineering practices? | `.agents/rules/practices.md` |
| All 64+8 seeds? | `.agents/rules/playbook-seeds.md` |
| Per-developer machine setup? | `.agents/rules/environment.md` (gitignored, generate own on first session) |
| What does Claude Code use? | `.claude/settings.json` (permissions + 2 hooks) |
| What skills are available? | `.claude/skills/<name>/SKILL.md` (10 starter) |
| MCP server config? | `.mcp.json` |
| Universal decisions? | `docs/decisions.md` (D-001..D-005 universal; your project starts at D-006) |
| Onboarding new engineer? | `docs/onboarding.md` |
| What tasks fit AI agents? | `docs/tool-suitability.md` |
| Per-milestone plan? | `docs/plans/m{N}-plan.md` |
| Per-wave review verdict? | `docs/reviews/m{N}-wave-{W}-{review,security}.md` |
| Per-milestone retrospect? | `docs/retrospectives/m{N}-retrospective.md` (M≥3) |
| Quarterly handover? | `docs/handovers/handover_q{N}.txt` (M%3==0) |
| Per-session log? | `docs/process-log.md` |
| Current state? | `note.txt` |
| Code Reviewer profile? | `subagent-profiles/Code-Reviewer.md` (MANDATORY, Stage 3a per wave) |
| Tester profile? | `subagent-profiles/Tester.md` (MANDATORY, Stage 3b per wave; v3 V3C-68) |
| Security Reviewer profile? | `subagent-profiles/Security-Reviewer.md` (MANDATORY; Stage 4.0 closure, BLOCKING before deploy — v3 V3C-68) |
| Web/API security baseline? | `docs/security-baseline.md` (V3C-11/12/13/51/56; v3) |
| Day-1 green test? | `tests/unit/test_health.py` (asserts `{status, version, build}` — L.7) |
| Stage-0 executable gate? | `scripts/bootstrap-check.sh` + `make bootstrap-check` (FB-1, v2.2) |
| Go-live dependency smoke? | `make smoke-deps` (L.8, v2.2) — invoke each external dependency once |
| OSS-engine license review? | `docs/license-review.template.md` → fill as `docs/license-review.md` (FB-4, v2.2; required if you wrap/fork OSS) |
| Why v2.2 exists (provenance)? | `docs/HANDOVER-v2.2-material.md` (sources + council ratification) |
| Why v3 exists (provenance)? | `docs/HANDOVER-v3-material.md` (6 source projects + 13-seat council + intra-ecosystem caveat) |
| DevOps file-ownership boundary? | `CODEOWNERS` (K.10; Dockerfile / `/deploy` / CI under DevOps handle) |
| PM-readable status snapshot? | `docs/pm-status.template.md` (v2.1; pairs with G.9) |
| Deploy actually live? | Stage 4.3 — `curl <target>/health \| jq .build` vs intended tag (L.7) |
| CI workflows? | `.github/workflows/ci.yml` + `.github/workflows/issue-agent.yml` |
| Project state dump? | `scripts/standup.sh` (LLM-free) |

---

## §17 — What this is NOT

- ❌ A finished product. v2.0 has known gaps (§15).
- ❌ A replacement for human judgment. Risk-tier HIGH (auth/PII/payment) still needs senior human review.
- ❌ A guarantee. Industry research backs many seeds; Phase-1 measured a subset.
- ❌ Frozen. New milestones in any project using this pipeline should propose seeds back; v3 will incorporate them.
- ❌ Claude-Code-only. AGENTS.md is the canonical name (industry std, 60k+ public repos, donated to Linux Foundation Dec 2025). CLAUDE.md is a symlink for Claude Code's native loading.

---

## §18 — Closing note

Pipeline v2.0 is the merger of measured discipline (Phase-1 N=9 milestones) with industry-converged tooling surface (Claude Code harness, AGENTS.md ecosystem, 3-layer issue automation). Neither alone is enough — your pipeline now has both.

Use it well. Capture what you learn. Bring back seeds. Run G.12 retrospectives. The pipeline is meant to compound.

— Pipeline v2.0 baseline shipped 2026-06-02
— Pipeline v2.1 increment shipped 2026-06-12 (Theme L distributed correctness + Stage 4.3 deploy-verification, from EF-AI M12 + S34). The biggest lesson of that cut: "code green + image built" is not "the new code is live."
— Pipeline v2.2 increment shipped 2026-06-19 (executable Stage-0 gate + go-live readiness + OSS-license gate, from HCS-MaaS bootstrap + EF-AI S35; ratified by a 7-role blind council). The lesson of this cut, named independently by 6 of 7 roles: **documented discipline is not self-enforcing.** v2.2 turns the two riskiest checklists — Stage-0 bootstrap and Stage-4.3 go-live — into executable gates a milestone cannot close without. And "configured" is not "working": invoke every dependency once and read config back from the process before you call it ready.
