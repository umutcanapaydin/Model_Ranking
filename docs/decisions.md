---
record_type: register
id: model-ranking-decisions
status: ratified
process_version: v7.2
date: 2026-08-11
---
# Decisions

> ADR-lite log. Pre-seeded with universal decisions (D-001..D-007) from EF-AI Phase-1 + v2.0 consortium.
>
> **ADR-ID convention (v2.2, seed B.6 / FB-2):** to avoid colliding with an inherited project's own ADR history, **process/universal ADRs use the `P-00x` namespace; project ADRs start at `D-100`** (the `D-001..D-099` band is reserved). The existing universal `D-001..D-007` are grandfathered (supersede-don't-edit, B.2) and are equivalently addressable as their `P-00x` mirror (see P-001). **Your project starts at D-100.** For an inherited project that already numbered low D-ids, run the Stage-0 reconciliation recipe in P-001.
>
> **Discipline:**
> - When an assumption ossifies under uncertainty, add a new ADR with status `proposed` via the
>   `/log-decision` skill (seed B.1).
> - To reverse: mark the old one `superseded by D-NNN`. Never edit in place (seed B.2).
> - IDs are immutable; deletion leaves a gap (seed B.5).
>
> **Status legend** (the `**Status:**` line of an ADR, not the frontmatter above):
> `proposed` — captured, not yet ratified: on its branch until the owner merges the PR that carries it.
> That merge ratifies it — an ADR on the default branch is accepted, and no status line is edited for it.
> `accepted` — locked. Changing requires `superseded by`.
> `superseded by D-NNN` — old; do not follow.

---

## D-001 — Cloud-agnostic SDK boundaries (UNIVERSAL)

**Status:** accepted

**Decision:** All external cloud / vendor SDK calls (object storage, model endpoints, telemetry, identity providers, payment, etc.) live behind a typed Protocol in `src/<pkg>/clients/`. Production implementations are isolated; a fake implementation lives alongside for tests.

**Rationale:** A future cloud / vendor pivot is a `clients/` swap, not a feature rewrite. This one discipline has saved a whole milestone of rework when a cloud target shifted.

**Mitigation if violated:** Code calling a vendor SDK directly from `workflows/` or `adapter/` is a contract violation; refactor before merge.

**Revisit when:** Customer mandates a specific SDK in a way that breaks the Protocol abstraction.

---

## D-002 — ADR-lite format (UNIVERSAL)

**Status:** accepted

**Decision:** All non-trivial design decisions go in this file using this format: ID, Status, Decision, Rationale, Mitigation, Revisit. One paragraph per field. No full IETF-ADR ceremony. Use the `/log-decision` skill for format enforcement.

**Rationale:** An ADR-lite entry takes a few minutes; heavier formats take ~15 minutes per decision and get skipped under pressure, which leaves no record at all.

**Mitigation:** None — this is the format.

**Revisit when:** Project crosses ≥3 teams and needs a richer audit format.

---

## D-003 — AGENTS.md diet (UNIVERSAL)

**Status:** accepted

**Decision:** `AGENTS.md` is **navigation, not encyclopedia**. Hard cap 150 lines (seed C.5); the template ships at ≤120 lines so a project has room for its §1–§2. Anything longer goes to `.agents/rules/practices.md` or related concern files. `conformance/test-agents-cap.py` fails the gate when the file is over the cap it states.

**Rationale:** Phase-1 measurement: AGENTS.md trended 250 → 218 → 170 lines across M5-M9. Each diet pass increased agent task success. ETH Zurich AGENTbench (arxiv:2602.11988) corroborates: LLM-generated context files >200 lines LOWER task success by ~3% and raise cost 20%+. v2.0 lowers the target from v1.1's 170-line tolerance to 80.

**Mitigation:** At every milestone closure (Stage 4.2 Capture), check `wc -l AGENTS.md`. If it nears the cap, extract a section to `.agents/rules/`.

**Revisit when:** Multi-week milestones consistently need more than 150 lines of navigation.

**Amended at `v7.2`** (the body above is kept as written): the template ships at ≤140 lines, as `AGENTS.md` and the brief state.

---

## D-004 — Permission matrix default-deny (UNIVERSAL)

**Status:** accepted

**Decision:** `permission-matrix.md` defines what coding agents may and may not do. Default for any sensitive action is DENY; allowances require a new ADR. v2.0 extends this with §10 OS-aware patterns + §11 BLOCKING taxonomy.

**Rationale:** The Replit DB deletion incident (July 2025) and Lovable RLS CVE-2025-48757 (May 2025) both stemmed from agents acting beyond authority. A standing matrix removes the ambiguity.

**Mitigation:** `permission-matrix.md` is editable only via ADR. Commits violating it without a prior `accepted` ADR are reverted.

**Revisit when:** Permission categories themselves change.

---

## D-005 — Mandatory subagent profiles: Code-Reviewer + Tester per wave, Security-Reviewer per release (UNIVERSAL)

**Status:** accepted — **superseded in part by P-004 (v3, V3C-68):** the per-wave pair is now Code-Reviewer + Tester; Security-Reviewer moves to Stage-4 closure (BLOCKING before deploy). Decision body preserved below per B.2 (supersede, don't edit).

**Decision:** Every wave-end fires two subagent profiles in Stage 3: `subagent-profiles/Code-Reviewer.md` (3a) and `subagent-profiles/Security-Reviewer.md` (3b). These are MANDATORY. Other profiles (Architect, Docs, etc.) are project-specific and added per need. Profile content invoked via `/review` and `/security-review` skills.

**Rationale:** Fresh-eyes review (seed K.7) catches what an author cannot. Testing is needed on every wave; security reads the whole release surface at once, which is more complete. Nothing deploys before the release, so the security review always precedes go-live.

**Mitigation:** `make wave-check` refuses a wave close without both verdict files in `docs/reviews/`, or with a BLOCKING one. No deploy step in `docs/closure-checklist.md` §E.2 runs before §E.1 passes.

**Amended at `v7.1.2`** (the owner's ruling of 2026-10-16; the body above is kept as written): in heavy mode the **Security-Reviewer** runs once per milestone, on the plan's last wave, over the whole milestone, writing `docs/reviews/m{N}-security.md` (required by `make wave-check` and `closure_check.py`); no wave or fix in heavy mode is routed to security, and `make review-need` prints each range's signals for that review. Light mode, the deploy gate and Stage 5.1 are unchanged.

**Revisit when:** A release is harmed by late security feedback — then move a security pass earlier for that risk class.

**Amended at `v7.1`** (DevFlow v7.1's text for this record, mandatory subagent profiles: reviews computed from the change; kept as an amendment so the body above stays as written, B.2): **Decision:** Reviews are fresh-eyes subagents (`.claude/agents/`) and `make review-need` computes which a change gets. Heavy mode: every wave the **Code-Reviewer**; the **Tester** once per milestone, on the plan's last wave. Both modes: the **Security-Reviewer** on a slice the signals flag, before every deploy (the deploy gate), and on the whole release at Stage 5.1, writing `docs/reviews/release-security.md` with its reviewed head. The read-only Explorer is used for exploration. Other profiles are project-specific and graduate per `docs/subagents.md`. **Rationale:** Fresh-eyes review (seed K.7) catches what an author cannot. Measured across two field projects: the per-wave Tester was the costliest review per real defect (41M–57M tokens against 1.9M–5.2M for the Code-Reviewer) and security the cheapest and highest-yield; three deploys in one project went out unreviewed while the rule was prose. **Mitigation:** `make wave-check` refuses a wave close without the verdicts its range needs (recomputed), or with a BLOCKING one. The deploy gate refuses a deploy command while code changed after the reviewed head.

**Amended at `v7.1`** (the owner's ruling of 2026-10-13, DevFlow #16 D8; the body above is kept as written): the milestone **Tester** runs at every milestone close in both modes — in light mode once before each release, on everything merged since its last verdict, writing `docs/reviews/release-tester.md` with its reviewed head, which the deploy gate reads.

**Amended at `v7.2`** (the owner's ruling of 2026-10-17; the body above is kept as written): in light mode the Security-Reviewer runs per change only on the brief's declared HIGH paths; `make review-need` prints its other signals for the release review. Heavy mode is unchanged.

**Revisit amended at `v7.2`** (the line above is kept as written): since `v7.1.2` heavy mode's security pass is the milestone's; revisit when a milestone's late security finding costs more than the per-wave passes it replaced.

---

## D-006 — BLOCKING / MINOR / Catastrophe taxonomy locked (UNIVERSAL, v2.0)

**Status:** accepted

**Decision:** Per-wave verdicts (Code-Reviewer, Tester), Quality Gate verdicts (Stage 4.1, when on) and the release security review (Stage 5.1) MUST use these categories:

- **BLOCKING:** REQ unmet / test red / secret leak / contract-grep miss / coverage drop / PASS without `file:line` evidence / auth-PII-payment-migration without senior review / permission-matrix region touched without ADR / hook violation.
- **MINOR:** style / doc drift / cross-wave K.9 candidate / AGENTS.md approaching cap (not over).
- **Catastrophe-class (DENY always):** `git reset --hard` / `git push --force` / `rm -rf` / drop table / commit secret / log PII unredacted / self-merge agent's own PR / any `--force` on irreversible op without user confirmation.

Full taxonomy in `permission-matrix.md` §11.

**Rationale:** An undefined BLOCKING drifts from reviewer to reviewer. Writing it down once removes the reinterpretation.

**Mitigation:** PASS verdicts WITHOUT `file:line` evidence are automatically demoted to BLOCKING (no false-pass surface). All BLOCKING findings need an attached evidence path.

**Revisit when:** A milestone closes with a new BLOCKING class not covered.

**Amended at `v7.1`** (DevFlow v7.1's text for this record's Decision, kept as an amendment so the body above stays as written, B.2): Review verdicts (the Code-Reviewer, the milestone Tester, the Security-Reviewer), Quality Gate verdicts (Stage 4.1, when on) and the release security review (Stage 5.1) MUST use these categories: **The categories are `permission-matrix.md` §11** — BLOCKING, MINOR and Catastrophe-class, with their members. That list is the only one; this record fixes that it exists and who must use it, and does not repeat it. It once did, and the two copies had drifted to nine BLOCKING classes here against fourteen there.

---

## D-007 — Two baseline hooks ship day-1 (UNIVERSAL, v2.0)

**Status:** accepted

**Decision:** `.claude/settings.json` ships these hooks. Claude Code blocks a tool call only on exit 2, so every guard exits 2 to block and 0 to allow (`conformance/test-hook-claims.py` grades that):
1. PreToolUse on Write/Edit — block writes to `.env` / `*.env*`.
2. PreToolUse on Bash — block destructive git (`reset --hard`, forced push, `clean -f`), `rm -rf`, worktree-destroying git (`checkout --` / `checkout .`, `restore` without `--staged`) and any push to the default branch.
3. PostToolUse on Write/Edit — run `make check-fast` (the legs of `make check`, side by side) and exit 2 on failure, or when `make` is not installed.

Both guards fail closed: they read the tool call with the first working `python3` or `python`, and with neither they block it.

The full `make gate` runs before every push (`make hooks`) and at `/pre-merge`. Additional hooks earn their way in only after a rule in `.agents/rules/practices.md` or `permission-matrix.md` is violated 3+ times in measured sessions. Catastrophe-class items (`permission-matrix.md` §11) may ship as hooks day 1 without that prerequisite.

**Rationale:** Every hook is a maintenance liability. These catch the highest-leverage incidents (secret commits, destroyed work, direct pushes, lint drift) without pre-defining what has not broken.

**Mitigation:** The promotion rule is in `permission-matrix.md`. The end-of-work harness diet (`/cycle-close`) retires hooks that never fired.

**Revisit when:** A milestone surfaces a recurrent rule violation that would benefit from another hook.

**Amended at `v7.1`** (the body above is kept as written): the shipped set is five hooks — SessionStart (the session marker `make session-check` reads); PreToolUse Write/Edit (`.env`, `.env.*`, `<x>.env`, `.envrc`); PreToolUse Bash, the pinned `.claude/hooks/bash_guard.py` (destructive git, `rm -rf` and `find -delete` outside scratch, a skipped hook, a moved protected ref, a shell write to a secrets file, `gh pr merge`/`ready`, the deploy gate); PostToolUse (`make check-fast`). Every hook sets `timeout` and `onFailure: block`, so one that cannot run blocks too.

**Amended at `v7.2`** (the line above is kept as written): that set was four hooks, the four it names; `v7.2` adds a fifth, PreToolUse on the PowerShell tool, which refuses every command but the read-only listings `permissions.allow` names for it — the Bash guard never saw a PowerShell call (the owner's ruling of 2026-10-17).

---

## P-001 — ADR-ID namespace convention (PROCESS, v2.2)

**Status:** accepted

**Decision:** Pipeline/process ADRs use the `P-00x` namespace; project ADRs start at `D-100`. The `D-001..D-099` band is reserved so an inherited project's existing `D-006+` history cannot collide with the pipeline's universal decisions. The grandfathered universal ADRs `D-001..D-007` keep their IDs (B.2) and are mirrored conceptually as `P-001`(this), `P-002`≙D-006 (BLOCKING taxonomy), `P-003`≙D-007 (baseline hooks).

**Stage-0 reconciliation recipe (inherited project):** (1) keep the project's existing `D-ids` as-is; (2) do NOT renumber them; (3) record the pipeline's process ADRs under `P-00x` (or in `permission-matrix.md`); (4) write the mapping in `process-log.md` before the first commit; (5) new project ADRs continue from `D-100+`. `make bootstrap-check` C5 warns if project ADRs sit in the reserved `D-006..D-099` band.

**Rationale:** HCS-MaaS bootstrap — the pipeline's universal `D-006/D-007` collided with the inherited project's own `D-006+` (cited across its PRD + feature list). A namespace split removes the collision class permanently.

**Mitigation if violated:** ambiguous citations; a `D-0xx` reference could mean a universal or a project decision. The `bootstrap-check` warn + this recipe catch it at Stage 0.

**Revisit when:** a project legitimately needs >900 ADRs, or a multi-project monorepo needs a third namespace.

---

## P-004 — Review-loop restructure: per-wave Code+Tester, Security at closure (PROCESS, v3)

**Status:** accepted (v3, 2026-06-26) — supersedes D-005's reviewer composition. (`P-002`≙D-006 and `P-003`≙D-007 are reserved mirrors per P-001, so this new process ADR is `P-004`.)

**Decision:** Per V3C-68. **Stage 2 (wave):** each implementing agent runs a dev-test loop (implement → write/run tests → self-review → fix) on its own slice. **Stage 3 (per-wave, fresh-eyes, never own code):** Code-Reviewer (`subagent-profiles/Code-Reviewer.md`) + **Tester** (`subagent-profiles/Tester.md`) flush all fixes before the wave closes. The Security-Reviewer is REMOVED from the per-wave gate and runs at **Stage 4 milestone closure (BLOCKING, before the deploy/go-live step).** Catastrophe-class always-on guardrails (no secrets, no destructive ops) still apply during every wave.

**Rationale:** testing is needed continuously (every wave); security reviews the whole milestone surface at once, which is more efficient and complete. Safe because nothing ships mid-milestone (deploy is at closure), so security-at-closure always precedes go-live. Preserves K.7 fresh-eyes — the dev-test loop *adds to*, never replaces, the wave-exit Code+Tester. Ratified by the 13-seat v3 council.

**Mitigation:** QM caveat — the security move ships WITH its executable check (V3C-11 in `make bootstrap-check` + `docs/security-baseline.md`), so security discipline is enforced, not merely deferred.

**Revisit when:** a milestone is harmed by late security feedback (an early-wave security flaw caught only at closure) → reintroduce a HIGH-risk-path in-wave security trigger.

---

## P-005 — v3.1: risk-tiered review depth + executable wave-close (PROCESS, v3.1)

**Status:** ACTIVE (2026-07-03) — amends P-004; ratified by the v3.1 council (`General_Pipeline/v3.1-ratification.md`)

**Decision:** (1) Review depth is tiered by wave risk (V3C-78): LOW/MED → one combined fresh-eyes reviewer; HIGH (auth/payment/crypto/migration/distributed-correctness — auto-escalated if the diff touches authz/secrets/crypto/input-parsing/egress) → separate Code-Reviewer + Tester + a pulled-forward security pass on that slice. First escaped blocker on a tiered-down wave reverts the project to full per-wave review (tripwire). (2) Wave close is gated by a committed, evidence-cited checklist (V3C-69, `docs/wave-checklist.template.md`) whose required rows derive from the plan's risk tags.

**Rationale:** measured on hcs_maas_vib (first GP-v3 field run): ~11→~5 reviewer runs per MED milestone, zero escaped blockers; the one process miss (F15) was exactly a memory-held, un-gated required pass.

**Mitigation if violated:** the tripwire above; wave-checklist rows 3–4 block closure mechanically (`make wave-check`).

**Revisit when:** the tripwire fires twice in one project, or a second independent project contradicts the tiering economics.

---

## P-006 — v3.2: owner review pack + evidence rule; autonomy ladder held as NORTH STAR (PROCESS, v3.2)

**Status:** ACTIVE for items (2)–(3); item (1) **NORTH-STAR CANDIDATE — NOT ACTIVE** (owner decision 2026-07-03, overriding the delegated chair's activation: "we are not ready; I review every wave and milestone, run the tests/smoke tests/checks, and make the commits").

**Decision:** (1) The autonomy ladder (A0/A1/A2, `docs/autonomy-protocol.md`) is RECORDED as the north-star design; **A0 is the only operating mode** — owner reviews every wave + milestone, runs all tests/checks, performs all commits; activation only by a future explicit owner-initiated ADR. (2) Every closure generates the owner review pack (`docs/closure-report.template.md`) derived from raw git/CI referents — an AID to the owner's review, replacing duplicated closure outputs, never replacing the owner. (3) The evidence rule (ACTIVE): anything measured about the pipeline (telemetry, gate inputs) is computed against protected refs; agent-asserted content never gates.

**Rationale:** owner directive OD-3 names the destination; the owner's readiness call sets the pace. The 9/9-seat finding (agent-generated evidence must not certify agent autonomy) and the METR felt-vs-actual gap survive as the ACTIVE evidence rule.

**Stage-0 reconciliation recipe (inherited project):** (1) keep the project's existing `D-ids` as-is; (2) do NOT renumber them; (3) record the process ADRs under `P-00x` (or in `permission-matrix.md`); (4) write the mapping in `process-log.md` before the first commit; (5) new project ADRs continue from `D-100+`. `make bootstrap-check` C5 warns if project ADRs sit in the reserved `D-008..D-099` band.

**Rationale:** An inherited project's own `D-006+` decisions, cited across its PRD and feature list, collide with the universal `D-006/D-007`. A namespace split removes the collision class permanently.

---

## P-007 — v3.3: A0.5 milestone-cadence owner review (PROCESS, v3.3)

**Status:** ACTIVE — PROVISIONAL (2026-07-05); owner directive OD-4, shape ratified by a 7-seat council with all decisions chair-delegated (`General_Pipeline/v3.3-ratification.md`).

**Decision:** The operating mode is **A0.5**: waves close agent-side (fresh-eyes reviews per tier, green checks pinned to the closing tree, committed evidence-cited checklist); the owner reviews, runs his own tests/smoke tests, and performs the commits at every MILESTONE boundary (session time-boxed; milestone capped ~4–6 waves / ~2k net lines); owner makes labeled non-approval checkpoint commits per wave. Escalate-NOW list halts to the owner immediately (AGENTS.md §3). Assumption ledger active. **Bright line:** an agent commit reaching main = A1 = explicit owner ADR only.

**Rationale:** OD-4 + hcs_maas_vib field evidence (agent reviews caught the real blockers; owner wave passes rarely added catches — single-project evidence, hence PROVISIONAL). Skeptic's dissent recorded: 48-hour reversal pattern; answered with the tripwire.

**Mitigation if violated:** auto-reversion tripwire (first escaped blocker an owner wave-pass would plausibly have caught → wave-cadence review for rest of milestone + one full milestone); fix-rate-vs-baseline line generated in every closure report.

**Revisit when:** A0.5 survives (or trips) two full milestones on the next project.

---

## P-008 — v3.4: Stage 5 maintenance loop + fixpack deploy gate (PROCESS, v3.4)

**Status:** ACTIVE (2026-07-17) — owner directive OD-6; 5-seat council (`General_Pipeline/v3.4-ratification.md`).

**Decision:** post-deploy bugs run as fix WAVES through the existing wave machinery (red-test
intake — the failing test is the frozen spec; fixes only turn red tests green). Ship via the
FIXPACK deploy gate: per-fix evidence rows, caps, security floor, full regression on the bundle,
**owner out-of-sandbox verification (BLOCKING)**, fix probe + watch window, emergency path with a
never-skipped floor + 48h retro-close debt. Capture coupling: fixpack lessons append to
EXPERIENCE.md as a deploy condition; **the standalone memory-based harvest is RETIRED.**
3-strikes gate-attribution → gate-change proposal; N=3 fix-on-fix → refactor milestone.

**Rationale:** first GP prod project accumulated ~5 ad-hoc fix deployments; GP ended at go-live.
The Skeptic's finding: the deeper failure was capture (3 md5-identical harvest uploads) — hence
the mechanical coupling and the retirement.

**Mitigation if violated:** an unfilled fixpack row or missing owner signature blocks deploy;
emergency erosion alarmed at >1/month.

**Revisit when:** 3 fixpacks of field data (tune caps, watch windows, N=3 threshold).

---

## P-009 — v3.5: outward-facing deploy checks from the first post-prod dataset (PROCESS, v3.5)

**Status:** ACTIVE (2026-07-27) — 5-seat council on Increment 9 (`General_Pipeline/v3.5-ratification.md`).

**Decision:** adopt the boundary-defect countermeasures: check-templates + cold-start CI checks
(V3C-99), the human-path criterion (V3C-100), producer enumeration on hardened invariants
(V3C-101, with security sign-off on auth-class), narrow tooling rules (V3C-102), ready≠alive +
channel-constrained diagnosable fail-closed (V3C-103), the boundary-grep delivery line (V3C-104
split), artifact-bound cadence (V3C-105), the black-box journey tester as default-expected deploy
deliverable (V3C-106), and the boot-prerequisite ownership rule (V3C-107).

**Rationale:** 7 post-prod defects, zero caught by build gates, 100% boundary class — the suite
tested the system we built; the defects lived in its contracts with everything outside it.

**Mitigation if violated:** the checks are CI/checklist rows; a skipped journey run is recorded in
the closure report. **Revisit when:** a second project's post-prod dataset exists (cross-stack check).

---

## D-100 — Stack & M1 shape: Python 3.11 + FastAPI (health-only) + SQLite

**Status:** proposed

**Decision:** M1 runs on Python 3.11, pytest, ruff/black/mypy per the starter lock. Persistence is a disposable SQLite file rebuilt from sources on every run. The FastAPI adapter ships /health (L.7) only; ranking/recommend HTTP endpoints and any Postgres migration are deferred to the API milestone. The iOS/SwiftUI client is a later milestone and likely a separate repo.

**Rationale:** Smallest surface that exercises the whole pipeline discipline; dataset is tiny (<5MB) so SQLite is honest, not a shortcut. Matches the spike's proven shape.

**Mitigation if violated:** Any new HTTP route or DB engine before the API milestone is out-of-plan scope; halt and re-plan.

**Revisit when:** API milestone opens (OQ-3), or dataset outgrows single-file storage.

---

## D-101 — Data sources: free-and-legal core only; no scraping; provenance mandatory

**Status:** proposed

**Decision:** M1 ingests exactly three documented raw-data endpoints: LiteLLM pricing JSON (GitHub), SWE-bench leaderboard JSON (GitHub), Aider polyglot YAML (GitHub). HTML scraping is banned. Artificial Analysis is NOT integrated until a commercial agreement exists (their free tier is internal-use-only, 100 req/day — verified 2026-08-06). Every stored record carries source, source_url class, and observed_at; source licenses are tracked in the PRD/source register.

**Rationale:** Comparison verdict: licensing is the project's gating risk; the free/legal core is sufficient for M1 and keeps the App Store path clean.

**Mitigation if violated:** Any ingestion from an undocumented endpoint is BLOCKING at review; remove the data and the code path.

**Revisit when:** AA commercial quote lands; Arena HF dataset + OpenRouter join at M2 (OQ-1).

**Amended by D-215 (2026-10-21)**: the owner's licence rule -- a public leaderboard's numbers are served when their publisher is credited with a link and its terms do not forbid non-commercial use; a repository's code licence is not its numbers' licence (#376).

---

## D-102 — The Cowork spike is L0 throwaway; production code is rebuilt through the pipeline

**Status:** proposed

**Decision:** The 2026-08-06 prototype (pipeline.py, recommend.py, advisor.db) is treated as a spike-* L0 lane artifact (V3C-87): its findings (alias variant-before-parent bug, median-not-min pricing, harness retention) are encoded as REQ-CAN-002/003 and tests, but its code is NOT imported into src/. It may be kept read-only outside src/ for reference.

**Rationale:** V3C-87: productionize = rebuild through the pipeline; the spike bypassed reviews, tests, and gates by design.

**Mitigation if violated:** Any file copied from the spike into src/ without tests citing its REQ-IDs is BLOCKING at wave review.

**Revisit when:** never — spikes stay spikes.

---

## D-103 — Operating mode: A0.5 (owner-confirmed at kickoff echo-back)

**Status:** proposed

**Decision:** The project runs at autonomy A0.5 per OD-4: waves close agent-side with fresh-eyes Code-Reviewer + Tester; the owner reviews, runs his own checks, and performs ALL git commits at milestone boundaries plus labeled per-wave checkpoint commits. Agents never run git. Escalate-NOW list per AGENTS.md §3.

**Rationale:** The autonomy protocol's default for a new project is A0, but the repo-wide active mode is A0.5 (OD-4, binding) and the owner approved proceeding on this basis in the kickoff echo-back (2026-08-06). Recorded here so the choice is auditable.

**Mitigation if violated:** An agent commit reaching main = A1 without ADR → automatic demotion review per autonomy-protocol §2.

**Revisit when:** A0.5 tripwire fires (escaped blocker on an unreviewed wave) → fallback to wave-cadence review.

---

## D-104 — Recommendation engine is deterministic; no LLM in the scoring/data path

**Status:** proposed

**Decision:** Rankings and recommendations are computed by rule-based, tested code: hard budget constraints first, Pareto non-dominance for value picks, explicit confidence grades, disclosed near-ties. No LLM generates, adjusts, or explains-with-invented-facts any score, price, or availability claim. A future natural-language intake layer may only translate user text into engine filters.

**Rationale:** Both research docs converge on this; it is also the App Store 5.1.2(i) avoidance path and the neutrality moat.

**Mitigation if violated:** Any model-generated number in output is BLOCKING; trace and remove.

**Revisit when:** NL intake milestone opens (separate consent + privacy review).

**Amended by D-181 (2026-10-06)**: the rule that the phone does no arithmetic on a served number outside its named files is checked on the compiled module, through the names, operators and methods D-181 lists; gap G-2 in `docs/security-invariants.md` holds what it does not follow (added at the M19 closure, the repo review's M10).

---

## D-105 — Category layer: primary-benchmark-per-category; no cross-scale averaging; generic row contract

**Status:** proposed (owner pre-accepted in m2-plan §13, 2026-08-11; ratify at M2 closure)

**Decision:** Use cases live in `categories.py` as data (CategorySpec: primary benchmark, metric,
native-scale thresholds, optional evidence-only secondary benchmark). A category ranks ONLY on its
primary benchmark's native scale — Elo and % are never averaged; composite scores are out of scope
until a normalization design passes review (M3+). To serve this, the M1 RankingRow/Pick contracts
were GENERALIZED (swebench_verified_pct→score, swe_harness→harness, aider_*→secondary_*): a
deliberate, versioned break of the m2-plan §4 "frozen" note — no external consumers existed
(pre-API), all internal consumers + tests migrated in the same wave.

**Rationale:** Research rule (both M0 reports): averaging raw scales produces a meaningless number;
primary-benchmark ranking is honest and explainable. Data-driven thresholds prevent a third
category from silently inheriting the wrong scale (M2-W4 review finding).

**Mitigation if violated:** Any query mixing benchmarks in ORDER BY, or thresholds hardcoded on
category id, is BLOCKING at review (structural test: test_no_cross_scale_averaging_structural).

**Revisit when:** ≥4 categories exist and users demand a cross-category "overall" view.

---

## D-106 — OWNER DIRECTIVE: agent runs the test gate and performs git commits/pushes (scoped A1)

**Status:** accepted (OWNER-INITIATED, 2026-08-11 — "You will need to run the required tests and
make the commits on my behalf." (owner, translated from Turkish — V4C-79.) This satisfies the autonomy-protocol bright line: an agent
commit reaching main requires an explicit owner-initiated ADR, never erosion.)

**Decision:** From M2 closure onward the lead agent (a) runs the full test gate (pytest, ruff,
black, mypy) on the real repository state before every commit, and (b) authors and pushes the
milestone commits to github.com/umutcanapaydin/Model_Ranking on the owner's behalf. Scope limits:
commits only at wave/milestone boundaries with green gates; commit messages carry the agent
trailer; the owner's GitHub token is held ONLY as an environment variable for the push, never
written to any file or committed; catastrophe-class operations (force-push, history rewrite,
reset --hard) remain FORBIDDEN (permission-matrix §5 — this ADR does NOT override them).

**Rationale:** Owner wants hands-off operation between milestones; A0.5's owner-git touchpoint
was the last manual step. Autonomy ladder allows A1 by explicit owner ADR.

**Mitigation if violated:** Any commit outside green-gate boundaries, or any token persisted to
disk, is an integrity violation → automatic demotion to A0.5 per autonomy-protocol §2/§5.

**Revisit when:** first escaped blocker traceable to an agent-pushed commit (auto-fallback), or
owner reasserts git at any time (always his right, no cause needed).

---

## D-107 — Subscription plans are curated in-repo data with mandatory per-row provenance

**Status:** proposed (m3-plan §10; ratify at M3 closure)

**Decision:** The subscription-plan table lives in `data/plans.yaml` (schema-versioned, validated
by `parse_plans_doc`): provider, plan, monthly USD price, currency, region, verbatim limits,
`source_url`, `last_verified`, and ONLY explicitly page-named `included_models`. Thresholds ride
the document as data (staleness_days=30, budget_caps_usd dusuk 10 / orta 25). Curated data FAILS
LOUD on any invalid row (authored data never skip-and-counts); ingest replaces the whole set
atomically. Values are probed against a live source on entry day; disputed prices do NOT enter
the table (first case: Google AI Plus, 2026-08-15).

**Rationale:** No machine-readable feed for consumer AI subscriptions exists (M0 research — the
moat); prices are volatile, so verification cadence (weekly CI staleness job, REQ-SUB-004) is a
product feature, not bookkeeping.

**Mitigation if violated:** a row without provenance/last_verified cannot parse (citing tests in
tests/unit/test_plans_ingest.py); a stale row fails the weekly CI job loudly.

**Revisit when:** a machine-readable plan feed appears, or region scope widens beyond USD/US.

---

## D-108 — Process baseline moves to General Pipeline v4.3.1

**Status:** proposed (owner directive 2026-08-15; ratify at M3 closure)

**Decision:** GP v4.2 is replaced by v4.3.1 as this project's process baseline. The install was
repaired to manifest-correctness in M3-W0 (6 missing PROJECT paths added, 18 GP-INTERNAL files
removed); `make check` now runs check-records + selftest + install-check + pin-check; the English
rule (V4C-79) applies to everything committed from M3 on, with a reasoned `.language-allow`
(Turkish PRODUCT strings and pre-M3 records exempt); agent git carries V4C-64 trailers under D-106.

**Rationale:** Owner directive at the M3 kickoff; v4.3.1 is the first GP cut whose install-
completeness rules can actually fire, and this repo was field evidence for why they must.

**Mitigation if violated:** install-check/pin-check are wired into make check, pre-commit and CI —
a drifting install fails the build rather than a council.

**Revisit when:** GP ships its next version and the owner directs adoption.

## D-109 — Scores are rounded at the OUTPUT boundary only, to one decimal

**Status:** ratified (owner-signed at the M4 closure session, 2026-08-15)

**Decision:** every score reaching a JSON contract or a user-facing string is rounded to
`SCORE_DECIMALS = 1`, and the rounding happens exactly once, at the boundary (`round_score` /
`round_optional_score` in `recommend.py`). Ranking, the Pareto comparison and every threshold
comparison keep the raw value. Prose deltas are computed from the ROUNDED numbers (`shown_gap`)
and collapse to "same score" wording when the shown delta is zero (`lead_phrase`).

**Rationale:** Arena publishes `1481.5937567329202`. Rendering that claims precision the benchmark
does not have; rounding BEFORE a comparison invents ties that do not exist (a 0.04 gap would hand
the quality label to the cheaper plan). Computing a delta from raw values and printing it beside
rounded fields produces the opposite defect: prose that contradicts the JSON next to it.

**Mitigation if violated:** three citing tests, all mutation-verified — rounding inside
`plan_ranking`, rounding after subtracting instead of before, and `round_optional_score` turning
an absent score into 0.0 each turn a specific test red.

**Revisit when:** a source publishes a benchmark whose meaningful precision exceeds one decimal.

---

## D-110 — When plans rank on the same model, the product SAYS so instead of manufacturing variety

**Status:** ratified — owner-signed 2026-08-15 at the M4 closure session, after his own
out-of-sandbox verification run reproduced the measurement this decision rests on. This
formally retires the signed criterion named below.

**Decision:** where several plans within the budget rank on the same model at the same score, they
are declared indistinguishable on quality: `equivalent_plans` names them and `equivalence_note`
states the group, the cheapest member with its price, the monthly spread, and which members are
linked through a provider roster rather than their own plan page. Groups are computed for EVERY
plan a label picked (not only the quality pick), built from the budget-filtered rows only, and
keyed on `plan_id` rather than display name.

**Rationale:** M4's plan asked for "≥3 distinct plans" in the live answer. Measured 2026-08-15, 4
of the 5 scoreable plans rank on Gemini 3.1 Pro at 1479.6 — so "distinct" would have meant
recommending a $99.99 plan over a $4.99 plan on a difference of zero. Honesty is the product; the
criterion was restated in the open rather than met by fabrication. **This retires a signed
criterion and therefore requires the owner's signature, which the M4 closure report requests.**

**Mitigation if violated:** four citing tests, mutation-verified, including the live shape where
the quality pick is alone and only the other two labels collapse (the case the first
implementation silently missed).

**Revisit when:** plan coverage grows enough that distinct plans are genuinely distinct engines —
`coverage.plan_coverage` is the number that says when.

---

## D-111 — Budget exclusion is a separate, counted disclosure

**Status:** ratified — owner-signed 2026-08-16 at the M5 closure session, together with D-112

**Decision:** subscription recommendation payloads expose `excluded_by_budget`, the count of
otherwise scoreable plans removed by the selected monthly-price cap, and `budget_notice`, a
user-facing sentence narrating the same count. The count is computed as the complete category
ranking minus the budget-filtered ranking. It never includes unscored plans and never overloads
D-110's model-equivalence fields.

**Rationale:** `eligible_count: 1` did not explain that five scoreable plans were excluded in the
measured low-budget agentic-coding case. Counting all plans would incorrectly mix budget exclusion
with missing benchmark coverage; using `equivalence_note` would confuse price filtering with plans
that deliver identical model evidence.

**Mitigation if violated:** `REQ-REC-013` has a six-scoreable/one-unscored acceptance fixture and a
real-bundle CLI assertion. Removing the notice, counting the unscored plan, or computing after the
cap turns a citing test red.

**Revisit when:** the API milestone structures exclusion reasons into typed groups; preserve this
count's exact scoreable-before-cap meaning during that migration.

---

## D-112 — An unequal-effort comparison is DISCLOSED, not silently equalised

**Status:** ratified — owner-signed 2026-08-16 at the M5 closure session. The owner was shown the
measured coverage cost of the alternative (28 rankable models today; 19 / 4 / 3 at `unspecified` /
`high` / `max`) and ruled that Q1's single-effort rule binds a category that HAS an effort policy,
not every category: `coding` keeps the board and discloses the inequality.

**Decision:** a category with no `ranking_effort` policy keeps ranking on the best evidence each
board published, and the answer carries `effort_mix_notice` whenever the compared picks come from
different effort levels. Each pick also publishes the effort of its OWN evidence and says which
level that is. The alternative — forcing `coding` to one named effort — is measured below and is
rejected as the worse trade unless the owner rules otherwise.

**Rationale (measured on the owner's Epoch bundle, 2026-08-16, 28 canonical models on the coding
board):** no model carries both an `unspecified` and an explicit effort row, so `MAX()` never
inflates a single model — Trap 2's headline failure does not occur here. What DOES occur is a
cross-model comparison at unequal effort: Claude Opus 4.7 at `max` (83.5) ranks above Claude Opus
4.6 at an unstated level (78.7). Forcing one level costs almost the whole board:

| `coding.ranking_effort` | Rankable models |
|---|---|
| (none — today) | **28** |
| `unspecified` | 19 |
| `high` | 4 |
| `max` | 3 |
| `medium` / `xhigh` / `low` | 1 / 1 / 0 |

There is no level that keeps the board. Ranking 3 models is not a product; ranking 28 while
claiming they were compared fairly is not honest. Disclosure is the only option that is both.

**Mitigation if violated:** `test_comparison_across_unequal_effort_is_disclosed` fails if the notice
is suppressed, and `test_pick_publishes_the_effort_of_its_evidence_not_the_category_policy` fails if
a pick reports the policy instead of its evidence — the defect that shipped through four waves.

**Revisit when:** the coding board's sources publish effort systematically (as DeepSWE already
does — `agentic-coding` names `high` and needs none of this), or the owner rules that Q1 binds every
category, in which case `coding` takes a level and the coverage cost above is accepted.

---

## D-113 — Process baseline moves to General Pipeline v5.0

**Status:** ratified — owner directive, 2026-08-16, given in the M6 planning session.
**Supersedes:** D-108 (process baseline GP v4.3.1).

**Decision:** this project's process baseline is **GP v5.0**. The installation was produced with
v5.0's own `make export-project`, not by copying the distribution directory — v5.0 is the first cut
that distinguishes the DISTRIBUTION package from an INSTALLATION, and a directory copy would import
23 GP-INTERNAL records (GP's own version history and decks) that a customer tree must never carry.

**What the project takes from v5.0:** the git-authority rule (recorded separately as D-114), the
`conformance/` suite and `make conformance`, `make gate` as the canonical gate name, `docs/watchlist.md`,
and the repaired `check_records.py`, `bootstrap-check.sh` and CI workflows. Project-owned content —
`docs/decisions.md`, `docs/prd.md`, `docs/process-log.md`, `docs/architecture.md`, the warnings
ledger, `note.txt`, `README.md`, `pyproject.toml`, `.language-allow`, `src/**` and AGENTS.md §1–§2 —
was preserved; only GP-owned files were replaced.

**Rationale:** the owner directed the move before M6's first wave, and a milestone boundary with a
green, idle, pushed repository is the cheapest moment a baseline change will ever have. Changing it
mid-milestone would invalidate a signed plan.

**Consequence recorded honestly:** v5.0's gate no longer runs the `pin-check` target — action
pinning moved into `conformance/test-action-pins.py`. The project's "8 gates / 7 targets" figure is
therefore stale wherever it appears, and three historical records still name that removed target.
See the migration findings in `docs/warnings.ledger.md`.

**Mitigation if violated:** `make install-check` fails if a declared PROJECT path is missing or a
GP-INTERNAL path leaked; `conformance/run-all.py` fails if a documented command does not exist.

**Revisit when:** GP cuts v5.1 or later, or a conformance leg proves unworkable against this
project's records.

---

## D-114 — Local-lane git authority: the agent stages, the owner commits

**Status:** ratified — owner ruling, 2026-08-16: *"Do it — I am moving to 5.0 anyway. I support your
view."* (owner, translated from Turkish), in answer to the question of D-106's fate under v5.0.
**Supersedes:** D-106 (agent runs the test gate and authors/pushes boundary commits).

**Decision:** in the LOCAL lane — anything running on the owner's machine, including every skill in
`.claude/skills/` — the agent **never runs `git commit` and never runs `git push`.** It may stage
(`git add -u`) and it must write the commit message for the owner to run. The lead agent still runs
the full test gate; that half of D-106 is retained and is not what this ADR removes.

In the LAYER-2 CI lane the issue agent may commit under all four of: a machine identity that is not
the owner's, a `fix/issue-*` branch, a DRAFT pull request it cannot merge, and a `GP-Agent:` trailer
on every commit.

**Rationale:** this project already paid for the failure the rule exists to prevent. **W-011:**
twelve of sixteen M5 wave commits were authored under the owner's own name with an unset-git
placeholder as the email, and the owner had to run a scoped rebase before the first push to repair
it. GP v5.0 states the rule in as many words and ships `conformance/test-git-authority.py` to enforce
it mechanically — the rule was never "agents cannot use git", it is **"no commit may be mistaken for
the owner's."** An owner who cannot tell which commits he wrote cannot review his own history.

**Mitigation if violated:** `conformance/test-git-authority.py` scans `.claude/`, `scripts/`,
`.agents/`, `subagent-profiles/` and `docs/` for local-lane commit/push instructions and fails the
gate. The v4.3.1-era `test-and-commit` skill, which committed, is deleted and replaced by
`test-and-stage`, which stops at staging.

**Revisit when:** the owner explicitly re-delegates commit authority in a new ADR, which under
AGENTS.md §3 is an A1 mode change and cannot be assumed from convenience.

---

## D-115 — Both coding surfaces are served, and neither leads

**Status:** ratified — owner ruling "A", 2026-08-16, answering the carried question M5's
retrospective posed. Recorded at M6-W1 because that is the wave in which the contract froze;
AGENTS.md §5 forbids shipping a public contract without an ADR, and permission-matrix §11 makes a
contract widened without one BLOCKING.

**Decision:** a request for a coding recommendation returns **two** answers — the `coding` surface
and the `agentic-coding` surface — and **nothing in the payload ranks one above the other.**

Concretely, and these are contract terms, not implementation notes:

1. `task=coding` returns both surfaces. `task=agentic-coding` returns that surface alone: the rule
   binds the coding *intent*, and a caller naming one surface has already chosen.
2. There is no `primary` / `default` / `recommended` / `preferred` / `winner` flag, no top-level
   single answer, and no ranking key — **under any spelling.** The prohibition is on the property,
   not on a list of words. A citing test asserts the property.
3. The answers are ordered alphabetically by surface id and the envelope says, in the payload, that
   the order carries no meaning. Alphabetical is chosen *because* it is meaningless.
4. Each answer states its own weakness in the payload: `coding` carries its effort-mix notice
   (D-112) and dated evidence; `agentic-coding` carries `evidence_dating: "undated"` and the
   sentence explaining that its board publishes release dates, not evaluation dates.
5. The two answers are structurally symmetric — identical key sets — so that no asymmetry can be
   read as precedence.

**Rationale:** M5 shipped two honest coding surfaces and no rule saying which leads. `coding` has
dated evidence over 5 of 10 plans; `agentic-coding` covers 6 of 10 on evidence carrying no
evaluation date at all. Neither dominates. Choosing one would mean deciding whether
dated-but-narrow beats undated-but-broad — a product judgement about which weakness a buyer should
be exposed to. The owner was given the trade with both numbers and ruled that the buyer sees both,
each labelled. **This is the honesty doctrine applied to a contract:** the product does not resolve
an ambiguity the evidence does not resolve.

**Mitigation if violated:** `tests/unit/test_api_v1.py` asserts that no key in the envelope matches
the precedence pattern and that the two answers carry identical key sets. The first version of that
guard was a nine-name denylist and the M6-W1 fresh-eyes review killed it with one rename
(`primary_surface`), which is why clause 2 is written as a property. That review is the reason this
ADR exists in the form it does.

**Revisit when:** a coding board publishes dated evidence at `agentic-coding`'s coverage, which
would collapse the two surfaces into one and make the question moot — or the owner rules that one
surface leads, which is a public-contract change and needs a superseding ADR and a `/v2`.

**Amended by D-124 (2026-08-18)**: see D-124; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-116 — Deploy target: Fly.io, with the evidence database as a shipped artifact (closes OQ-3)

**Status:** ratified — the owner chose Fly.io on 2026-08-15 and it was recorded in
`docs/plans/m4-plan.md` §"Owner decisions locked". This ADR does not make that choice again; it
gives it an ID that exists, states what it commits to, and repairs the citation.

**Supersedes:** nothing. **Repairs:** `docs/plans/m4-plan.md:142`, which cites the decision as
"D-110". **D-110 is not that decision** — it is *"when plans rank on the same model, the product
SAYS so instead of manufacturing variety"*, ratified for a different purpose entirely. The M4 plan
named an ID that was later spent elsewhere, so for two milestones the deploy target was
simultaneously "recorded" in a plan and "not chosen yet" in `docs/prd.md` OQ-3. **A preference
written in a plan is not an ADR, and a citation that points at the wrong ADR is worse than no
citation, because it reads as settled.** That is the defect this milestone was told to close
properly, and closing it means the ID, not the sentence.

**Decision.** The serving target is **Fly.io**. The service is the read-only `/v1` surface from
D-115; the evidence database is a **build- or deploy-time artifact**, not a runtime dependency on
anything Fly.io provides:

1. **`MODEL_RANKING_DB` must point at a real file, and the process refuses to boot in production if
   it does not** (REQ-API-006). There is no managed database in this design and no network call in
   the serving path — the API reads one SQLite file read-only and never writes it (W-017's
   containment).
2. **Ingestion does not run on the serving host.** The pipeline that builds the database runs where
   the owner runs it today, and the artifact is shipped. This keeps the network-fetching code — and
   the untrusted-producer boundary W-005 guards — off the public surface entirely.
3. **`APP_BUILD` is set at build time** so `curl /health | jq .build` answers "which code is live"
   (L.7). Production refuses to boot without it, for the same reason.

**Rationale for recording it as-is rather than re-opening it.** The owner's stated reason in M4 was
operational simplicity for a single small read-only service, and nothing measured since contradicts
it. The PRD's original research named Supabase and Cloudflare Workers; both assume a managed
datastore or an edge runtime, and this service wants neither — it wants a filesystem and one
process. Re-litigating a settled owner choice to produce a more impressive ADR would be the kind of
motion this project has a rule against.

**What this ADR explicitly does NOT authorise:** a deployment. M6 ships deploy READINESS and the
owner signed the plan on that basis. **W-017 is a named condition of go-live, not a follow-up:** the
serving snapshot copies the whole database into memory per unauthenticated request, measured at
roughly 9,100x amplification at today's 761 KB and 450,000x at 51 MB, and the W3 security pass ruled
it BLOCKING at Stage 4.3 with the closure pass required to re-derive the number independently. **A
first deploy before that measurement is exactly the shape of decision this ADR exists to prevent
someone making from a plan sentence.**

**Mitigation if violated:** `validate_startup_config` fails the process closed in production on an
unset `MODEL_RANKING_DB` or `APP_BUILD`, with citing tests including a real subprocess import.

**Revisit when:** the service acquires state that a filesystem cannot hold, or the amplification in
W-017 is closed and the traffic shape is known — either of which changes the premise this choice
rests on.

**Amended by D-177 (2026-10-04)**: the serving image installs `requirements/serve.lock`, hash-checked, then the project with `--no-deps --no-build-isolation`; it carries no pyarrow.

**Amended by D-185 (2026-10-07)**: the hosted engine's artifact ships inside its image (the `hosted` stage), a public copy with the sources whose terms do not permit a public app left out; the owner's Mac keeps the full one.

**Amended by D-217 (2026-10-21, proposed)**: clause 2 -- ingestion for the hosted engine runs on a scheduled GitHub Actions runner in a job that holds no secret; it still never runs on the serving host (#387).

## D-117 — Scoped inter-wave commit and push authority for the lead agent

**Status:** ratified — owner directive, 2026-08-17: *"You may also use git to push between waves."*
(owner, translated from Turkish), given together with the instruction not to pause between waves.
**Narrows:** D-114, which remains in force for everything this ADR does not name.

**Decision:** the lead agent MAY commit and push at **wave boundaries** during a milestone, under
all five of the following, every one of which is a condition and not a preference:

1. **The agent's own git identity** — `Claude <noreply@anthropic.com>` in this repository, never the
   owner's name and never an unset placeholder.
2. **`GP-Agent` and `GP-Task` trailers** on every commit (V4C-64).
3. **Green gates only** — `make check` exit 0 at the committed tree. A red gate is not a commit.
4. **Catastrophe-class git stays forbidden** regardless of this ADR: no `reset --hard`, no
   `push --force`, no history rewriting, no `checkout`/`restore` over uncommitted work.
5. **The milestone-closing commit and the out-of-sandbox verification remain the OWNER's.** This
   ADR moves wave checkpoints, not the gate.

**Rationale, including the part that argues against it.** This re-creates, in narrower form, the
authority D-114 removed one day earlier — and D-114 was written because **W-011** happened here:
twelve M5 commits authored under the owner's own name with an unset-git placeholder as the email.
That risk is structurally different now: the agent's identity in this repository is distinct and
verified, so a commit cannot be mistaken for the owner's, which is the harm the rule names in as many
words. What the owner gains is that a five-wave milestone does not accumulate uncommitted work across
sessions, where a single mistake loses it — the F17 class.

**This is a project override of the GP v5.0 baseline** (D-113). v5.0's `AGENTS.md` §3 states that
local-lane agents never commit and never push, and ships `conformance/test-git-authority.py` to
enforce it. That check scans documents for local-lane git instructions, not the agent's own actions,
so it will stay green — **which is itself worth recording: the control does not detect the thing this
ADR permits.** The owner's directive governs; the divergence from the baseline is stated here rather
than discovered later.

**Mitigation if violated:** `git log --format='%an <%ae>'` over any milestone range must show no
commit authored as the owner that an agent wrote; the M5 gate ran exactly that check and it is how
W-011 was found.

**Revisit when:** the owner withdraws it, or a commit under this authority reaches `main` with a red
gate — either of which returns the project to D-114 unmodified.

---

## D-118 — The product's user-facing text and query vocabulary are ENGLISH

**Status:** SUPERSEDED IN PART by D-136 (2026-08-25) — see the closing note. Originally ratified — owner ruling, 2026-08-17: *"Let the payload be English, and the query values
too."* (owner, translated from Turkish), in answer to the M6-W1 review finding that one `/v1` answer
carried two languages.

**Decision:** every user-facing string the product emits, and every value a caller sends, is English:

1. **Query vocabulary.** `budget` takes `low` / `medium` / `unlimited`, not the Turkish tier names.
   `task` values were already English. The keys in `data/plans.yaml`'s `budget_caps_usd` change with
   them, because a curated-data key and a query value that mean the same thing may not differ.
2. **Payload strings.** `title`, `why`, `trade_off`, `close_call`, the effort disclosures, the budget
   notice, the staleness notices — all English. `CategorySpec.title_tr` becomes `title`.
3. **`.language-allow` loses its product-string exemptions.** Five test files and three source files
   were exempt because they carried deliberate Turkish; they are no longer exempt, which means `L1`
   now guards the whole product surface instead of stopping at its edge.

**Rationale.** The W1 code review found a single `/v1` answer carrying `ordering_note` in English
beside `why` and `close_call` in Turkish, and no gate caught it — `L1` looks for Turkish letters and
the adapter's strings are ASCII. The owner ruled English rather than translating the adapter back.

**The consequence worth stating plainly: the CLI becomes English too.** It prints what the engine
produces, and the alternative — translating at the API boundary — would give the product two sources
of user-facing text for one run. That is exactly Trap 1 of the M6 plan, the defect class M5's
security review caught by reading two artifacts of one run against each other. **One source, one
language.** If a Turkish-facing surface is wanted later it is a localization layer over structured
message keys, which is a milestone of its own and not a set of translated literals.

**Scope boundary held deliberately:** `plan_config`'s COLUMN names (`cap_dusuk`, `cap_orta`) keep
their spelling for now. They are internal identifiers, not contract, and renaming them is a schema
migration — which belongs in M6-W3 where a migration is already planned, not in a wave that would
have to acquire one for a cosmetic gain.

**Mitigation if violated — CORRECTED 2026-08-17, because the first version of this paragraph was
false.** It claimed that with the exemptions removed, "a Turkish string in any of them fails
`make check`". It does not. `L1` detects Turkish-SPECIFIC LETTERS, so it is silent on Turkish
written in pure ASCII, and the W2 fresh-eyes review found four such strings still shipping after the
migration was declared done — including a `trade_off` that rendered as one sentence in two languages.
**The migration had followed the gate's signal and stopped exactly where the gate stops**, and three
tests had been left pinning the surviving Turkish in a file whose exemption this ADR had just removed
on the grounds that it no longer carried any.

What is actually true: `L1` covers `recommend.py`, `subscribe.py`, `categories.py` and their tests,
and catches any Turkish carrying the alphabet's non-ASCII letters — the cedilla, breve, dotless-i
and umlaut forms, which this record deliberately DESCRIBES rather than lists, because `L1` has no
negation escape hatch and a record that spelled them would fail the gate it documents (GPF-005).
It cannot catch ASCII Turkish. The remaining
guard is the tests that assert exact English sentences, plus review. Recorded as **W-019** rather
than closed, because writing a stronger claim would repeat the mistake this paragraph is correcting.

**Revisit when:** the product acquires a real localization layer, at which point this ADR is
superseded rather than amended — the decision it records is "one language at a time", not "English
forever".

**SUPERSEDED IN PART by D-136, 2026-08-25 (M12-W5, on the Stage 4.0 seat's MAJOR-6).**

This ADR's Revisit-when read: *"the product acquires a real localization layer, at which point this
ADR is superseded rather than amended."* **M12-W4 shipped exactly that** — a localisation layer, a
language switch, and a Turkish rendering of titles, surfaces, budgets, pick badges, placeholders,
scales, prices and units. The marker was never applied, so for one milestone a ratified,
unsuperseded ADR forbade the product surface the milestone had just shipped, and the ADR that
authorised it (D-136) named neither this one nor the clause it overtook. That is the
record-contradicts-code class, occurring inside the decision log itself, which is the one place it
cannot be caught by running the software.

**Precisely which half falls, because the other half is still doing work.** The *"every user-facing
string the product EMITS is English"* clause is superseded: the client now emits Turkish, composed
from the engine's facts. The **payload** clause is NOT — `/v1` is English, the query vocabulary is
English, and D-136's architecture is what keeps it that way: the engine publishes facts and never a
translated sentence, so the localisation layer that overtook the first clause is the same mechanism
that enforces the second. Read together, the two ADRs say: **the product speaks the reader's
language; the contract speaks one language, and it is English.**

## D-121 — A source may be optional, but a blind surface may never be silent

**Status:** accepted · **Date:** 2026-08-17 (M7-W1) · **Decided by:** the owner, at the wave

**Context.** M7-W1 moved the build pipeline into product code. On its first real run the build
refused to produce anything: the Arena dependency has been returning an upstream HTTP 500 from the
HF datasets-server for hours (**W-024**), and every source was mandatory. One external incident
could therefore block a milestone indefinitely.

The tempting fix is a `try/except` around the fetch. That is the inverse of why the L.8 gate was
repaired in v4.3.2, and it would convert a loud outage into a quiet one.

**What made the decision non-obvious** is that Arena is not one input among many: it is the SOLE
primary evidence for the `assistant` category (`categories.py`). Dropping it does not thin that
surface's answers, it empties them — and an empty answer is indistinguishable from "nothing met
your budget", which is a different and false statement.

**Decision.** Sources carry a `required` flag. An optional source that fails does not stop the
build; it downgrades the run to **exit 3** — the same "done but not servable" code `schema migrate`
already uses under D-120 — with `required_operator_actions` naming, in surface terms rather than
operations terms, which categories now have no primary evidence. The mapping from a failed source
to the surfaces it blinds is derived from `CATEGORIES`, never typed out.

Arena is the only source marked optional. This is permitted **only because** the serving path
already discloses a missing source: `/v1` reports `source_health.stale = true` with a notice naming
the absent evidence. Verified against the real artifact at this wave rather than assumed.

**The condition this decision stands on.** If that disclosure is ever weakened, this ADR is
invalidated, not merely inconvenienced — the whole justification for letting a build succeed
without Arena is that a user asking about `assistant` is told there is no evidence rather than
shown an empty list.

**Known gap, recorded rather than smoothed:** a consumer reading only `picks` still sees an empty
array on a blind surface, and learns the difference only from `source_health`. Whether the payload
should refuse more loudly on a surface with no primary evidence is carried as an open question to
M7-W2, alongside REQ-API-008.

**AMENDED 2026-08-17, same day, by the M7-W1 review round — the paragraph above was incomplete and
the ADR was signed on an incomplete reading of the surface it cites.** The security seat and the
code-review seat independently found that a blind surface did not merely show an empty `picks`
array: it also served `unavailable_reason` = *"No model on this surface's benchmark fits the
requested budget"*. That sentence is false when the cause is a missing source — nothing was
excluded by budget, because nothing was ranked at all — and it sat in the same object as the
`source_health` notice correctly reporting that no evidence source was present. **One payload,
two contradictory accounts of itself, with the false one in the human-readable field.**

This did not inconvenience the decision above, it removed its justification: the ONLY reason a
degraded build may ship is that the surface tells the truth about the gap.

**Closed in W1 rather than deferred**, at `adapter/main.py`: when a surface has no evidence source,
the answer now says so and states explicitly that no budget was applied. Verified against the built
artifact, and pinned by `tests/unit/test_empty_answer_reasons.py`, which also asserts that a surface
WITH evidence still gets the budget sentence — the fix must not replace one blanket explanation
with another. The `picks: []` question genuinely does remain open for W2's REQ-API-008.

**Revisit when:** Arena returns and stays up for a full milestone, at which point `required=True`
should be restored rather than left optional by inertia; or when a second source becomes optional,
which would mean this is a pattern rather than an incident.

**Amended by D-135 (2026-08-25)**: see D-135; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-122 — Review depth is calibrated by what the code can get WRONG, not by wave number

**Status:** accepted · **Date:** 2026-08-18 (M7-W1 closure) · **Decided by:** the owner

**Context.** M7-W1 ran three review seats through three rounds and closed thirty BLOCKING findings.
The findings were real — the shipped artifact had never been built, a rebuild could destroy it, and
the CI step that was supposed to prove all of it could never pass. But the owner named the cost
plainly: *"we are not writing avionics"* (owner, translated from Turkish). One wave consumed an
entire session on a solo project with no users, nothing deployed, no authentication, no personal
data and no payments.

He had already given this instruction in M6 and the agent did not apply it: adapt the council when
process cost starts eating delivery, while still fixing anything root-cause.

**Decision.** Depth follows the blast radius of being wrong, not the wave's position in a plan.

**FULL depth — the scoring path.** `rank.py`, `recommend.py`, `categories.py`, `subscribe.py`, the
serializer, and the `/v1` contract. Separate Code-Reviewer and Tester, fault injection, a citing
test per criterion. Rationale: this product's entire value is that its advice is correct, and a
defect here makes a person buy the wrong subscription. The `/v1` contract joins this list rather
than sitting below it, because the iOS app is the NEXT piece of work and a frozen contract with a
real consumer is expensive to get wrong.

**SINGLE PASS — plumbing.** Build scripts, CI workflows, `Dockerfile`, `fly.toml`, deploy wiring,
governance tooling. One reviewer, one round. Findings that survive go to the warnings ledger with an
owning milestone instead of into another round. Rationale: a defect here costs a red build or a
failed deploy, both loud and both recoverable, neither of which reaches a user with a wrong answer.

**ROUND CAP — two.** If a second round's findings are located inside the first round's FIXES rather
than in new surface, the wave stops and the remainder is ledgered. Chasing a third round is how a
wave stops converging: M7-W1's rounds went 14 → 8 findings, and every round after the first found
defects the agent had introduced while fixing the previous one.

**What this does NOT relax**, so the boundary is not read as general permission: escalate-now still
binds (suspected secret, scanner suppression, plan-invalidating scope change); a stay-green mutant
still earns its mandatory test; a criterion still needs a citing test able to fail; and a root-cause
defect is fixed regardless of which category it was found in.

**Revisit when:** the product acquires real users, authentication, or payments — any of which moves
the plumbing into the full-depth column, because a failed deploy stops being recoverable in private.

---

## D-123 — Go-live moves to M8 and ships with the iOS app, not before it

**Status:** accepted · **Date:** 2026-08-18 (M7 closure) · **Decided by:** the owner

**Context.** M7's signed plan defined W4 as "deploy + go-live readiness", and everything up to the
deploy itself was completed and verified: the image builds, the container serves the mounted
artifact, `scripts/journey.py` passes 4/4 against it, and the process refuses to boot on an unbuilt
or pre-M5 database. `fly launch` then stopped on a payment method: Fly.io requires a card before it
will place a machine, including at the smallest size.

**The question that decided it was not cost but timing.** The iOS app is the next milestone, and
during its development the simulator can reach the engine on `localhost` — Xcode and the iOS
Simulator are free, and an Apple Developer membership is only needed to put the app on someone
else's device. A hosted endpoint becomes necessary at exactly one moment: when something outside
the owner's machine has to call the engine. Deploying earlier buys a monthly bill and a public
surface that no user reaches.

**Decision.** M7 closes with the engine **deploy-READY and not deployed**. Go-live moves to M8 and
happens alongside the iOS client, when the app needs an endpoint it cannot get from `localhost`.

**D-116 is NOT superseded.** Fly.io remains the target and `fly.toml` remains its declaration; only
the moment of execution moves. `fly.toml` and `Dockerfile` stay in the repository — a passing test
depends on `fly.toml`'s concurrency declaration, it carries W-017's closure record, and the
`Dockerfile` is what proved the container fails closed on a bad artifact. Nothing was created on
Fly.io, so nothing is left running or billing.

**What this defers, stated so it is not mistaken for verified.** The Stage-4.0 security pass marked
two things unverified BECAUSE no deployment existed, and they stay unverified: the over-the-network
half of REQ-API-009 (the journey ran against a local container, not a host), and Fly volume
permissions, OOM behaviour and `force_https`. **Neither may be reported as covered until a real
deploy exercises them.** They carry to M8 as ledger rows, not as footnotes.

**Revisit when:** the iOS client needs an endpoint off the owner's machine — a physical device, a
TestFlight build, or a second person. That is the trigger, and it is a product event rather than a
date.

---

## D-124 — `/v1` freezes AFTER its first real reader, not before

**Status:** accepted · **Date:** 2026-08-18 (M8 opening) · **Decided by:** the owner
**Amends:** D-115, which froze the `/v1` contract in M6.

**Context.** D-115 froze the payload while the only consumers were tests. M7's retrospective put the
consequence as a question: every field in that contract was designed by someone imagining a client,
and M6 demonstrated four separate times that an enumeration written from imagination misses the
member that matters. M8 writes the first real reader.

**Decision.** **The contract may move once, during M8, in response to what the client actually
needs.** After M8 closes it is frozen again under D-115's original terms.

**What this permits, narrowly.** A field the client genuinely cannot render correctly, a value the
client would otherwise have to compute itself (which Trap 1 forbids), or a disclosure the payload
carries in a shape no interface can present. Each one is an ADR, not an edit.

**What it does NOT permit**, because the reason D-115 exists is unchanged: re-opening **Ruling A**.
Both coding surfaces are served with neither leading, and no field may be added, renamed or ordered
in a way that ranks them. That took three review rounds to enforce against a denylist, a regex and
finally a frozen key set, and it is not a rendering convenience.

**Why "once" and why "during M8".** A contract that moves whenever a consumer complains is not a
contract. A contract frozen before anyone read it is a guess with a lock on it. Bounding the window
to the first client's construction is the narrowest form that gets the benefit: after M8 the payload
has been shaped by a real reader, and every later change goes back to being expensive on purpose.

**Operational rule for M8 (Trap 3).** A gap the client hits is recorded as a finding against `/v1`
**before** any client-side workaround, and the workaround is not written while the finding is open.
Otherwise "the contract may move once" becomes "the client quietly compensates", which is the
outcome both this ADR and D-115 exist to prevent.

**Revisit when:** M8 closes. At that point this ADR expires by its own terms and D-115 resumes.

---

## D-125 — `/v1` publishes the full ranking beside the three answers (the one D-124 change)

**Status:** accepted · **Date:** 2026-08-18 (M8-W1) · **Decided by:** the owner, from the running app
**Uses:** the single contract revision **D-124** permits during M8. **Closes:** W-033.

**Context.** The owner ran the app and asked for each category to show its recommendations plus the
top few models, and to open into the full list. `/v1` serves three picks. The engine already ranks
**44 models for `coding` and 13 for `agentic-coding`** — the data exists and the contract does not
publish it, which is precisely the gap D-124 held a window open for.

**The distinction that shapes the payload.** The three picks are not the top three of anything: they
answer three DIFFERENT questions — best quality, best value, budget pick — chosen by three different
rules. A ranked list answers ONE question, in score order. Serving "more picks" would collapse two
ideas into one and quietly invent a fourth and fifth label. So the payload gains a **separate
list**, and the picks keep their meaning.

Evidence that the difference is real rather than pedantic: on the current artifact the same model
(Grok 4.5) is both `best_quality` and `budget_pick`, and the score-ordered top 5 for `coding`
contains four models priced above $8/1M while `best_value` — MiniMax M2.5, 3.5 points off the leader
at 84% less — does not appear in it at all. A screen showing only the ranked list would lose the
product's actual claim.

**Decision.** Each answer gains a `ranking` array: every model the engine ranked for that surface,
in the engine's own order, each carrying the same fields a `Pick` carries minus the pick-specific
labelling (`label`, `why`, `trade_off`). `picks` is unchanged. The client renders the picks, then as
many ranking rows as its screen wants, and asks for nothing more to open the full list.

**What this does NOT change**, so the window is not read as wider than it is: **Ruling A stays
untouched** — both coding surfaces are served with neither leading, and `ranking` is per-answer, so
it cannot become a cross-surface leaderboard. No field is renamed or removed. The engine computes
the order; the client never re-sorts (M8 plan, Trap 1).

**The cost, stated.** The payload grows from 3 picks to 3 picks plus up to 44 rows per answer. That
is a real size increase on an unauthenticated GET, and it is why `ranking` carries fewer fields per
row than `picks` does rather than being a second copy of everything.

**This is the change D-124 permitted.** After it lands, `/v1` is frozen again for the rest of M8;
another gap becomes an M9 decision rather than a second revision.

---

## D-126 — The product is a dashboard over the world's measurements, for ALL AI tools

**Status:** accepted · **Date:** 2026-08-19 · **Decided by:** the owner
**Scope change:** the largest since Ruling A. Widens the product from text LLMs to every kind of AI
tool, and states what the product IS in a way the earlier ADRs only implied.

**The owner's framing, and it is the clearest statement of this product's identity so far:**

> *"We do not do benchmarking. We are like a weather app for the AI world."*

A weather app owns no thermometer. It reads the stations, presents what they measured, says when a
reading is old, and never offers an opinion of its own. That is exactly what this engine does with
SWE-bench, Aider, DeepSWE and Arena — and it is why every disclosure control built in M5–M7 exists.
The framing is not a metaphor for marketing; it decides what the product may and may not say.

**Decision 1 — scope: all AI tools.** Not only text LLMs. Image generation and editing, speech,
music, video, document understanding, agents — anything a person might reach for, wherever a public
and legally usable measurement of it exists.

**What that costs, stated now rather than discovered later.** The engine's price model is
`input_per_m` / `output_per_m` — tokens. An image model is priced per image, a speech model per
minute, a video model per second. `blended_per_m` is not a universal unit, and D-105 already forbids
averaging across scales. **Pricing becomes per-modality before this scope is real**, and that is
engine work, not a category row.

**Decision 2 — the router, and its absolute boundary.** A free model sits in front of the catalogue
with ONE job: read what the user actually wrote — not keyword-match it — and decide which of OUR
pre-existing categories to show first. It is a translator between the end user's language and this
product's menu, so that someone who wants to improve a profile picture types that instead of
hunting through fifteen headings.

> **It may never say a model is good.** Not "I recommend", not "this one is best for you", not a
> re-ordering, not a nudge. The owner's words: *"we do not do benchmarking, so we cannot let it
> choose either."*

The line is exact: **the router picks the QUESTION; the engine answers it.** Routing is a language
task and the model is good at it. Ranking is an evidence task and the model has no evidence — it
would be substituting its training for measurements, which is the one thing a weather app must
never do. **D-104 is unchanged and this ADR does not soften it**: no LLM in the scoring path.

**Two consequences that follow from the boundary, not from taste.** The router's choice is SHOWN to
the user and is correctable — a routing decision the user cannot see is one they cannot overrule.
And a routing failure degrades to the menu, never to a guess: if the model cannot tell what was
meant, the product shows the categories rather than picking one.

**Decision 3 — a category exists only where a measurement exists.** Inventing fifteen headings is
an afternoon's work; each one needs a public, free, legally usable source, plus a client, a parser
and an ingestion path. A category without evidence is a screen that says "I have nothing", which is
what `assistant` says today while Arena is down (W-024). **Demand does not create a category.
Evidence does.**

**Revisit when:** a modality the owner wants has no public measurement at all. That is a real case —
it is the "workaround" he has already anticipated — and it needs its own decision rather than a
quiet exception to this one.

**Amended by D-169 (2026-09-28; amended in M18-W3, 2026-10-04)**: the on-device model's closed output gains a yes/no field, whether the input is a search for a model at all, and an input that is not one gets a note or a question back, not a ranking.

**Amended by D-180 (2026-10-06)**: the enforcement of what leaves the phone reads what the compiler resolved, in all four build configurations: the two privacy sinks, `EngineClient.swift` and `StandingsStore.swift`, hold only values and call only what is listed; gap G-1 holds the rest (added at the M19 closure, the repo review's M10).

---

## D-127 — Nine categories to open with, `assistant` split, Tier-3 demoted to evidence

**Status:** accepted · **Date:** 2026-08-19 · **Decided by:** the owner
**Implements:** D-126's scope, using `docs/research/category-map-draft-2026-08-19.md`.

**The nine, with the evidence each rests on:**

| Category | Primary evidence | Models |
|---|---|---|
| Everyday questions | `epoch_capabilities_index`, `mmlu_external` | 819 / 249 |
| Expert reasoning | `gpqa_diamond`, `critpt`, `hle_external` | 263 / 139 / 51 |
| Mathematics | `otis_mock_aime_2024_2025`, `gsm8k_external` | 238 / 235 |
| Computer use | `terminalbench_external`, `os_world_external` | 204 / 58 |
| Coding *(exists)* | SWE-bench Verified (live) | 173 |
| Abstract reasoning | `arc_agi_external`, `arc_agi_2_external` | 191 / 172 |
| Web development | `webdev_arena_external` | 109 |
| Image generation | Arena mirror `text-to-image` | 76 |
| Image editing | Arena mirror `image-edit` | 53 |

**`agentic-coding` is retained, making ten.** It sits in the draft's Tier 2 and was therefore not
among the nine, but it already exists and **Ruling A is built on it** — a coding question returns
both coding answers with neither leading, frozen by D-115 and enforced only after three review
rounds walked past a denylist and then a regex. Dropping a surface to tidy a list would retire that
ruling as a side effect. Removing it needs its own decision; this ADR does not make one.

**`assistant` is SPLIT into "everyday questions" and "expert reasoning".** They are different needs
resting on different evidence: a model that is good at day-to-day questions is not necessarily good
at GPQA-level science, and merging them guarantees that one of the two answers is wrong for whoever
asked. The split also unblocks the category: `assistant` has answered nothing since Arena went down
(**W-024**), and both halves can be served from evidence already on disk.

**W-024 is NOT closed by this.** Arena's human-preference Elo measures something MMLU does not —
what people actually prefer, rather than what scores well on an exam — and the product keeps saying
Arena is down rather than quietly substituting a different measurement for it.

**Tier 3 becomes EVIDENCE, not headings.** `gdpval`, `the_agent_company`, `cad_eval`, `geobench`,
`spatialviz`, `mindcube`, `osworld_2`, `rli`, `algotune`, `cl_bench`, `blueprint_bench_2` carry 5 to
32 models each. A category with eight models spends its life answering "nothing fits your budget"
for reasons that have nothing to do with the user's budget, so they attach to a broader category as
secondary evidence — which REQ-REC-004 already pays for by raising confidence when a second
independent benchmark agrees.

**The twelve saturated academic instruments stay out entirely** as categories: `bool_q`,
`wino_grande`, `piqa`, `hella_swag`, `lambada`, `open_book_qa`, `trivia_qa`, `arc_ai2`,
`science_qa`, `superglue`, `common_sense_qa_2`, `adversarial_nli`. High model counts and the wrong
kind of thing — nobody asks which model is best at WinoGrande, and publishing them as headings
would fill the menu with questions no user asks, which is the problem D-126's router exists to
solve.

**What this obliges, and it is the expensive part.** Each category needs its own quality floor,
value window and close-call threshold. **These may not be borrowed across scales** (D-105): coding
uses 65 on a percent-resolved scale, an Elo category cannot inherit that number, and an ECI index
is a third scale again. A threshold copied from one scale to another is a wrong answer wearing a
correct-looking constant.

**Revisit when:** a category's evidence source stops updating. The ledger row is the mechanism, not
a rewrite of this ADR.

---

*Append new ADRs in sequence via `/log-decision` skill. IDs are immutable; deletion leaves a gap (seed B.5).*

## D-128 — A refresh refuses on a blinded surface or a quarter of a surface lost

**Status:** accepted · **Date:** 2026-08-21 · **Decided by:** the lead agent, under the owner's
instruction to proceed and decide. **Reversible in one constant; say the word and it moves.**
**Answers:** `docs/plans/m9-plan.md` §5 question 1. **Implements:** REQ-REF-003.

**Decision.** An unattended refresh REFUSES to publish a candidate when, compared with the artifact
it would replace, either:

1. a surface that was answering would answer nothing, or
2. any surface loses **more than a quarter** of its ranked models.

**Why a threshold at all, and why not zero.** The tempting rule is "refuse on any loss", and it is
the dangerous one. Boards drop models constantly — a provider retires a checkpoint, a leaderboard
prunes a stale entry — so "any loss" would refuse almost every real refresh. The product would then
freeze at whatever artifact happened to be current, **while every gate reported healthy and every
cycle exited cleanly.** That is the failure mode this milestone must fear most, because it looks
exactly like success: nothing breaks, nothing alerts, and the answers quietly stop being true.

The opposite error is cheaper to recover from. If the threshold is too loose, a bad upstream day
publishes a thinner artifact and the next good day publishes a full one back. **A refusal is
recoverable by waiting; a freeze is only recoverable by someone noticing.**

**Why 25%.** It is a judgement, not a measurement, and it is recorded as one. The reasoning: the
smallest surface this product ships ranks 13 models (`agentic-coding`), so a quarter is three — big
enough that routine churn does not trip it, small enough that a real outage cannot hide behind it.
On the largest (`everyday`, 58) it is fourteen, which no ordinary board movement produces.

**Explicitly NOT a refusal condition:** a surface gaining models, or scores falling. **A model
getting worse is news, not damage** — this product's job is to report what the measurements say,
and refusing to publish a decline would be the one thing worse than publishing it.

---

**AMENDED 2026-08-22, after an independent review landed three degradations on the product that
this rule did not object to.**

**1. Prices ARE a refusal condition, and the original reasoning here was wrong.** This ADR said
"prices moving in either direction" is not damage, on the ground that a price is a reported number.
That is true of a score and false of a price: `BUDGETS` is a **hard filter applied before any
scoring** (REQ-REC-002), so a feed that multiplies every price leaves every surface exactly the
same SIZE while `low` and `medium` answer nothing at all, on all nine surfaces. The reviewer built
that candidate and it published. A surface that answered a reader on `low` and now answers nothing
is "fewer surfaces answering" in the only sense a reader experiences.

So the rule gains a third condition: **a (surface, budget) pair that offered models and would now
offer none.** Row counts cannot see it — the rows are all still there, merely unaffordable.

**2. The boundary was `<` and is now `<=`**, so a loss of exactly a quarter refuses. A mutant
flipping it survived thirty-three tests: one character between routine churn publishing and a step
toward the freeze this ADR exists to prevent.

**3. The worked arithmetic above is off by one, in both examples.** `now <= was * 0.75` trips on
the smallest surface (13 models) at the **fourth** model lost — **30.8%**, not "a quarter is three"
— and on `everyday` (58) at the **fifteenth**, not the fourteenth. The reasoning stands and the
numbers do not: the effective threshold on the tightest surface is 31%, so *"small enough that a
real outage cannot hide behind it"* is weaker there than this ADR originally claimed.

**What did NOT change, and why.** The 25% figure itself. Every degradation the review actually
landed passes at any value of it, because none changes a row count — so tightening would catch none
of them while moving the product closer to the freeze. **The answer to a guard that misses things
is more axes, not more stringency.**

**Amended by D-173 (2026-10-04)**: the ranked roster is compared by model id (clause 2), accessibility values have the same quarter as a loss guard (clause 3), and the candidate is checked against the serving bounds (clause 4).

---

## D-129 — The refresh's record is a file, and `runner` is what makes it visible

**Status:** accepted · **Date:** 2026-08-21 · **Decided by:** the lead agent, under the owner's
instruction to proceed. **Answers:** `docs/plans/m9-plan.md` §5 question 3. **Implements:**
REQ-REF-004, and constrains REQ-REF-005.

**Decision.** Every cycle writes its outcome to a status file beside the artifact. `runner` reads
that file and reports it, including **how long ago** the last cycle ran, so a refresh that stopped
entirely is visible in the one command the owner already runs.

**The limit is stated rather than hidden: this only reaches him when he runs `runner`.** It is a
record he can find, not an alert that finds him, and REQ-REF-005 asks for the second thing.

**Why this and not a notification, today.** A desktop notification is the only option that arrives
unbidden, and it is also a thing that starts appearing on someone's screen because an agent decided
it should. That is not a reversible change in the way a constant is. The status file is the part
that is unambiguously right — nothing can alert on state it never recorded — so it ships first, and
W3 chooses the channel on top of it with the owner present.

**What this forbids:** treating a silent, absent status file as success. If the file is missing or
its timestamp is old, `runner` must say so loudly. **Silence is the failure mode, so silence is what
gets reported.**

---

## D-130 — The schedule is `launchd`, because a missed trigger must be caught up

**Status:** accepted · **Date:** 2026-08-21 · **Decided by:** the lead agent, under the owner's
instruction to proceed. **Answers:** `docs/plans/m9-plan.md` §5 question 2, in part.
**Implements:** REQ-REF-005. **Constrained by:** D-116 — ingestion never runs on a serving host.

**Decision.** The 12-hour schedule is a `launchd` agent on the owner's Mac, using `StartInterval`.

**Why not `cron`.** `cron` does not fire for triggers missed while the machine was asleep, and a
laptop is asleep for most of a night. On a 12-hour interval that is not a delayed refresh, it is a
**skipped** one — and two skipped triggers is a day of the product claiming freshness it is not
maintaining. `launchd` runs a missed `StartInterval` job when the machine wakes, which is the whole
reason to prefer it here.

**Why the owner's Mac at all.** D-116 forbids ingestion on the SERVING host, and nothing is
deployed, so there is exactly one host. When a deploy happens (D-123, still undischarged), the
refresh moves off the serving box and this ADR is superseded rather than amended.

**What ships in W3 and what does not.** The plist and an install command ship; **the agent does not
install it.** Loading a background job onto someone's machine is the owner's action, and it is one
command he can read before he runs it.

## D-131 — The arena restoration, and the authorization that was missing from the repository

**Status:** accepted · **Date:** 2026-08-22 · **Decided by:** the owner, in session on 2026-08-21
(*"you can close the ones left behind too"* — owner, translated from Turkish), recorded here at the
Stage-4.0 review's insistence. **Supersedes:** `docs/plans/m9-plan.md` §6's exclusion of the arena
fix, and the W-024 disposition of 2026-08-21.

**Why this ADR exists at all.** The work was authorised and the REPOSITORY could not show it. A
Stage-4.0 security seat, reading only the protected base ref as V4C-06 requires, found:

- the signed M9 plan §6 saying, still true at HEAD, *"Not the arena fix… it touches a security
  finding's citing test; it is the owner's call and is not smuggled in here"*;
- the W-024 ledger row at the range's base saying **NOT APPLIED** for the same reason;
- `CLAUDE.md` §3 listing "security-invariant test modified/deleted" as escalate-NOW;
- and the only authorization anywhere being prose the implementing agent wrote **inside the range
  under review**.

It returned BLOCKING on the authorization and explicitly not on the code. That is the correct
verdict and the finding is a real one: **an owner's ruling that lives only in a chat log is not
available to any reviewer, any future agent, or the owner himself in three months.** V4C-06 exists
because a change cannot be its own permission slip.

**Decision.** The arena restoration stands. The client reads the overall board as the ordered prefix
of `/rows` (394 rows, 394 models measured live), `minimum_rows` moves from 1 to 250, and the three
tests citing security finding **W-007 are RE-EXPRESSED rather than deleted** — each still asserts
that a failure of the primary read aborts loudly and touches no other endpoint, with the forbidden
endpoint now being the other one. W-007's invariant is preserved; only which endpoint is primary
changed, because the one it named stopped serving this dataset.

**What this ADR does not do.** It does not retroactively make the sequencing right. The correct
order was: owner ruling → ADR → code. What happened was: owner ruling in chat → code → ADR at
review. The gap is one milestone wide and it is recorded rather than smoothed over, because the
next time the finding will look identical and may not be authorised.

**The rule this makes explicit for anyone working here:** when the owner authorises something that
a signed plan excludes, the authorization goes into an ADR **before** the code, in his own words,
translated and marked. A chat message is a decision; only a record is evidence.

## D-132 — A surface may not change by more than a quarter in either direction unwatched

**Status:** accepted · **Date:** 2026-08-22 · **Decided by:** the lead agent under the owner's
signed M10 plan · **Implements:** REQ-GRD-001, closes **W-049** · **Extends:** D-128, which guarded
only the way down.

**Decision.** An unattended refresh REFUSES a candidate when, compared with what is being served:

1. more than **a quarter** of a surface's models are names this artifact has never seen, or
2. a surface's **median published price** moves by more than **a quarter**, in either direction.

Together with D-128 the rule a reader can hold in one sentence is: **a surface may not change by
more than a quarter, in either direction, without somebody looking.**

**What ordinary movement actually is, measured.** This is the sentence D-128 was missing and had to
be corrected for, so it comes first here. Between two consecutive builds against live sources on
2026-08-22: **0% previously-unseen names on all nine surfaces, and 0.0% median price movement on all
nine.** Rosters are stable and individual prices move without shifting a median. A quarter is
therefore not a tight limit being defended — it is a wide one that ordinary movement does not come
near, which is the right shape when the failure to fear is the product freezing while every check
reports healthy.

**Why names and not counts.** A count cannot see a roster that was REPLACED rather than resized —
twelve models swapped for twelve different ones is the same number and a different product. Names
also carry the signal that separates the two cases this rule exists to tell apart: a real board adds
models one or two at a time, and an injected set arrives together.

**Why the median and not a price.** One provider cutting a price is news, and this product exists to
report news. A whole surface's median moving is a FEED, and a feed is what a bug or an attacker
controls. The axis fires in BOTH directions: cheaper is the attack, because a cheaper artifact is a
more attractive one, and dearer is a fault.

**Three things this deliberately does NOT refuse.** A surface returning from blind — when arena came
back, `assistant` went from nothing to 65 models and every name was new; refusing that would have
frozen the product on the day it got better, every twelve hours. A surface simply growing within the
limit. And scores rising, which is the same reasoning D-128 used for scores falling: **a measurement
moving is news, not damage.**

**It refuses; it never judges.** Under the owner's ruling of 2026-08-22 the refresh may prepare,
compare and refuse, and may not acquire new judgement. This rule reports what looks wrong and the
cycle stops — it never decides something is acceptable on balance and publishes anyway.

**Amended by D-173 (2026-10-04)**: the roster's growth limit compares model ids, not display names (clause 2).

## D-133 — In a single-agent lane, K.7 means a separate SESSION, and the review is a FILE

**Status:** accepted · **Date:** 2026-08-22 · **Decided by:** the owner, in session on 2026-08-22,
choosing "amend the rule to match reality — a separate review session" from three options put to him
after W-055 was escalated. Recorded because the independent seat's N4 found this ADR was the only
one since D-125 with no attribution clause, on the one change AGENTS.md §3 classes as
Escalate-NOW. · **Supersedes nothing; amends the application of K.7.**

**Context.** K.7 says the reviewer never authored the code. In this project's local lane there has
only ever been one agent, so the rule described a situation that did not exist, and the gap was
filled the only way it could be: the author reviewed their own work and declared it. That happened
four times, each recorded, each closed green (W-055). `C2b` — the telemetry whose entire purpose is
that a third bypass sends the CONTROL for review — fired at M8, named M9, and M9 closed without
consuming it.

Then the gate written to enforce this ADR failed, on its first run, the one wave record in the
project's history that claimed K.7 WAS satisfied: `m8-wave-5-close.md` cited two review records by
path, and neither has ever existed. The three seats reported back in conversation and nobody wrote
the reports down (W-056).

**Decision.** For the LOCAL single-agent lane:

1. **The reviewing seat is a separate session.** It receives the diff and reads its policy from the
   protected base ref (V4C-06) — never the authoring session's context, because context is what
   makes a reviewer agree with the author.
2. **The review is a file**, `docs/reviews/*.md`, with `seat: independent` or `seat: author` in its
   frontmatter. A review that exists only as a report in a conversation is not evidence.
3. **A self-review cannot close a wave green.** `seat: author` forces the review row to WAIVED,
   which Block D already forces to name a ledger row, which puts the bypass in front of the owner.

**What this decision explicitly does NOT claim.** The gate cannot prove a review ran in a separate
session, and this ADR does not pretend otherwise. It makes a self-review *unable to pass silently*,
and it makes a cited-but-absent review *impossible*, in every era. The honesty of `independent`
rests on process. That is acceptable here for a specific reason: **the failure this rule exists to
stop was never a lie.** Every K.7 bypass was declared in the open, in the record, and closed green
anyway — the problem was never concealment, it was that nothing blocked.

**Consequences.** M11-W4's Stage 4.0 is the first review in this project run by a seat that did not
write the code and that leaves a file. The two rules that must not drift back together: reviewing
one's own code is allowed and it is not GREEN; and a review nobody can read is not a review.

## D-134 — A sibling resource is not a payload revision: `/v1/budgets`

**Status:** accepted · **Date:** 2026-08-22 · **Decided by:** the owner, in session on 2026-08-22,
choosing "a new `/v1/budgets` endpoint" over a third payload revision and over accepting W-044
permanently.

**Context.** `/v1/recommendations` answers a `budget=low` query with `eligible_count: 25` beside a
`ranking` array of 58 rows whose most expensive model is $36.09/1M. The array is unfiltered **by
design** — D-125 spent D-124's one revision window adding it precisely so a client could show every
ranked model. What was missing was the cap those 25 were counted against. It is $2.00/1M blended,
it lives in `recommend.BUDGETS`, and it was published nowhere: no endpoint, no field, no OpenAPI
document (`docs_url` and friends are off by security decision). This app reconciles the two numbers
on screen. **Any other consumer could not, because the input was not in the API.**

**Decision.** Publish the caps as a fourth route, `/v1/budgets`, returning each budget id with its
blended cap (`null` for `unlimited` — the absence of a cap, not a large one) plus the blend weights
that produce the `blended_per_m` each ranking row already carries.

**Why this is not a contract move D-115 forbids.** D-115 froze the `/v1` **payload**, and D-124
granted one revision to it which D-125 spent. A new resource changes no existing response: every
field of every current answer is byte-identical after this change. The frozen thing is what a
consumer already parses, and nothing a consumer already parses moved.

**The reading this ADR explicitly rejects.** "Any addition to `/v1` is a revision." Under that
reading the API could never gain a resource without an owner-level window, which would make the
freeze a ban on the surface rather than a stability promise about the payload — and would have left
W-044 with only two options, both worse: a third revision, or telling every non-first-party
consumer to hardcode a constant out of the source.

**What makes it honest rather than convenient.** The endpoint is checked against the engine, not
against itself: `tests/unit/test_budgets_endpoint.py` filters the served `ranking` by the served
cap and asserts the result equals the served `eligible_count`, across three surfaces and two
budgets on real data. A cap that did not reproduce the count would be a THIRD account of one query,
published somewhere new — worse than the two it was written to reconcile.

**Consequences.** `DECLARED_ROUTES` is four. The route-drift test's expectation is written out
independently of the module, so adding a route stays a two-file change that cannot self-approve.
The caps are policy constants, so the endpoint answers while the artifact is missing or being
republished — which, since M9, happens every twelve hours.

## D-135 — A structural absence is stated ONCE, not repeated per surface

**Status:** accepted · **Date:** 2026-08-25 · **Decided by:** the owner, choosing "say the
structural one once, do not repeat it" from three options after the council measured the disclosure
load. · **Amends the application of D-121; does not supersede it.**

**Context.** D-121 says a source may be optional but a blind surface may never be silent, and eleven
milestones have applied it by attaching a notice wherever a limitation touches an answer. The
council measured what that produced: **eight disclosure blocks per screen, 155–185 words of caveat
against 40–60 words of answer**, rendered as up to five identical orange warning triangles with no
severity order, carrying about four distinct facts.

Six of the nine surfaces carry a permanent *"evidence may be out of date"* notice. **Five of those
carry it because the source publishes no dates at all** — so the notice can never clear, on any
data, ever. It is a structural property of the source wearing the costume of a transient warning,
and it drowns the one notice that is transient and real: SWE-bench, 179 days.

**Decision.** A limitation that is a PROPERTY OF A SOURCE is stated once, per source, in calm
language. A limitation that is a STATE OF THE DATA — something that became true and can become
false again — keeps its warning treatment and its prominence.

**What this decision is NOT.** It is not a reduction in what the product discloses. Every fact
survives; the repetition does not. The test of any change under this ADR is: *can a reader still
learn every limitation that applies to the answer they are looking at?* If the answer is no, the
change is wrong and D-121 governs.

**Why this is the owner's ruling and not an implementation detail.** This project's identity is
that it never goes silent about what it cannot see. Reducing the volume of disclosure is exactly
the kind of change that is defensible in each instance and corrosive in aggregate, so it is
recorded as a ruling with its measurement attached rather than made quietly in a design pass.

**Consequences.** Six permanent staleness notices become one statement per source. The transient
one becomes visible for the first time. `docs/prd.md` REQ-APP rows that specify per-surface notices
are amended at the wave that implements this, not at closure.


## D-119 — `equivalent_plans` carries LABELLED groups, not a flat list of names

**Status:** accepted · **Ratified 2026-08-25, describing a decision in force since M6.**
**Decided by:** the M6 wave that implemented REQ-REC-014.

**This ADR is late by six milestones and that is the reason it is worth reading.** `docs/plans/m6-plan.md`
proposed it, `docs/closure-report-m6.md` states *"D-119 written at closure rather than mid-wave"*,
and it was never written. The code shipped, the tests pin it, three records cite it — and the
decision itself existed nowhere. Written now with today's date rather than backdated: a false date
would commit, inside the repair, the same defect the repair exists to fix.

**Context.** `equivalent_plans` was a flat tuple of plan names (W-002, raised at M4). With two or
more equivalence groups, a machine consumer could not tell which PICK each plan was equivalent to —
the labels had been flattened away, so "these three plans are equivalent" lost the answer to
"equivalent to what?".

**Decision.** `equivalent_plans` is a tuple of `EquivalenceGroup`, each carrying the label of the
pick it belongs to (`src/app/workflows/subscribe.py:147`). Not every label collapse is equivalence:
all labels may land on one plan, and the tuple stays empty when no second plan is equivalent to
anything.

**Consequences.** A consumer can group plans by the pick they match. The tuple is empty on the
shipped artifact today, measured — which is a fact about the data, not about the contract, and is
exactly why the shape matters before it is populated.

## D-120 — CLI exit codes are a frozen contract, and `3` is NOT uniform across it

**Status:** accepted · **Ratified 2026-08-25, describing a convention in force since M6.**
**Decided by:** the M6 wave that established it, with the divergence recorded here for the first
time.

**Cited in 26 files — including `src/app/workflows/build.py:25` as "`schema.py`'s frozen D-120
contract", and in `tests/unit/test_roster_window.py:416` as "a K.8 frozen contract, so the SET is
pinned" — and never written.** The M10 and M11 plans both list it among the frozen surfaces this
project promises not to move. **The most-deferred-to contract in the repository had no record.**

**Decision, as it actually shipped.** An operator learns one convention rather than one per tool:

| Code | Meaning | Where |
|---|---|---|
| `0` | did what was asked | everywhere |
| `1` | a RESULT, not a failure — "no model fits this budget", "nothing changed" | `recommend.py`, `coverage.py`, `refresh.py` |
| `2` | the command failed; the target is not usable | everywhere |
| `3` | **two different things — see below** | `build.py`, `schema.py`, `refresh.py` |

**The divergence, stated rather than tidied away.** In `build.py:549` and `schema.py:493`, `3` means
*built but NOT servable*, with `required_operator_actions` naming what is missing — a degraded
success. In `refresh.py:77`, `3` is `EXIT_REFUSED` — the refresh declined to publish, which is a
deliberate refusal and not a degraded anything.

Both are defensible in isolation and the pair is not a convention. It is recorded here as a KNOWN
divergence rather than resolved, for one reason: `contract-tests.yml` already tolerates `build.py`'s
`3` explicitly, and `runner` already reads `refresh.py`'s codes, so changing either number now would
break a consumer to tidy a document. **The document is what was wrong.** Resolving it needs a
migration and belongs in a plan, not in the ADR that finally writes the contract down.

**Consequences.** The SET is frozen: no CLI in this repository may introduce a fourth meaning, and
no existing code may change meaning without an ADR superseding this one. The divergence at `3` is
now a thing this project knows about instead of a thing it has been asserting is uniform.

## D-136 — `/v1` publishes the FACTS behind each sentence; the client writes the sentence

**Status:** accepted · **Date:** 2026-08-25 · **Decided by:** the owner, choosing "the engine
returns structured facts and the app composes the sentence" over `?lang=tr` and over an
interface-only translation. · **Moves the `/v1` answer payload, deliberately and additively.**

**Context.** Asked for Turkish, the obvious reading was a string file in the app. The measurement
said otherwise: **every sentence on screen is generated by the engine, in English** — `pick.why`,
`trade_off`, `ordering_note`, `stale_notice`, `evidence_dating_note`, `effort_mix_notice`,
`close_call`, `unavailable_reason`, and the surface titles. Eleven milestones of localisation debt
with nothing to reveal it, because there was no second language.

**Decision.** Each sentence the engine composes gains a machine-readable companion: the REASON it
was chosen and the values it quotes. `why` keeps its English text and gains `why_fact`:

    "why": "Highest SWE-bench Verified score among eligible models (83.5 % resolved).",
    "why_fact": {"reason": "highest_score", "benchmark": "SWE-bench Verified",
                 "score": 83.5, "unit": "% resolved"}

The client composes the sentence it shows, in either language, from the fact. The English prose
stays and is **derived from the same values**, so there is one source of truth and no consumer
breaks.

**Why additive rather than a replacement.** Removing the prose would break every existing consumer
to serve a client that could equally read the fact — and D-115's freeze exists precisely so a
consumer is not broken for the server's convenience. The prose is now DERIVED, not authored: if the
fact and the sentence ever disagree, the fact is right and the sentence is a defect.

**The rejected alternative, and why.** `?lang=tr` is smaller and writes every future sentence twice,
paying the whole cost again on a third language. It also puts the product's voice in the engine,
where D-104 says no judgement lives — a translation is a judgement about wording, and the engine
that must not say a model is good should not be choosing how to say anything.

**Scope, stated so the gap is not mistaken for completeness.** This ADR covers `why` and
`trade_off` — the two sentences under every pick, and the ones a reader meets first. The notices
(`stale_notice`, `effort_mix_notice`, `evidence_dating_note`, `close_call`, `unavailable_reason`)
keep English prose and are NOT localised by this decision. They are disclosures, they are longer,
and doing them badly is worse than doing them later. **Recorded as an explicit remainder rather
than left to be discovered by a Turkish reader.**

**Consequences.** `PUBLIC_ANSWER_FIELDS` and the `Pick` allowlist grow by two. D-115 is amended in
the same way D-125 amended it: the payload moves once, additively, under a recorded ruling. Any
future sentence added to a pick must arrive with its fact, and a test enforces it.



**AMENDED 2026-08-25 (M12-W5, on the Stage 4.0 seat's MAJOR-2). The prose did NOT stay, and this
ADR said it did.** The sentence above — *"The English prose stays and is derived from the same
values, so there is one source of truth and no consumer breaks"* — is true of the MECHANISM and
false of the OUTCOME, and the second half is the half a consumer feels.

The seat measured it by extracting `d13c810` into a scratch tree, pointing both trees at the same
copy of `advisor.db`, and calling every endpoint: the SHAPE moved exactly once and additively, as
recorded (`why_fact` and `trade_off_fact` added to a pick; every other level byte-identical; all
status codes identical). But **116 existing-field VALUES differ**, and while the title and
`ordering_note` changes are recorded product decisions (W-080), the 27 `trade_off` changes were
recorded nowhere. Re-measured here against today's real `advisor.db` across every category at three
budgets: **15 of the 24 `best_value` trade-off sentences now use the multiple form** (`but 3x
cheaper.`) where the pre-M12 `best_value` sentence was hardcoded to a percentage.

The cause is exactly the derivation this ADR ordered: the old `best_value` prose was a separate,
hardcoded string, and routing it through the one `trade_off_sentence` re-decides
percentage-vs-multiple from the ratio. That is the RIGHT outcome — it is what having one source of
truth means, and the old string was the second source — but it is a prose change on 27 sites and it
belongs in the record, not in the diff.

**The precedent this fixes, which is why the paragraph is load-bearing.** The next reader will use
this ADR to decide what "additive" permits. Additive is a claim about the SHAPE of a payload and
says nothing about its VALUES. A consumer keying on `"% cheaper"` in a `best_value` trade-off is
broken by this milestone, and D-115 exists so that a consumer is not broken for the server's
convenience. Unifying two sources of truth is worth breaking that consumer; **not saying so is
not.** A record that describes the mechanism and not the outcome leaves the next person to
rediscover the outcome from a user complaint.

**Amended by D-176 (2026-10-04)**: the recorded English remainder ends; the app composes the notices from served facts too, and `close_call_fact`, `unavailable_reason_code` and `source_health`'s `reason` are added.

## D-137 — A review has a DATE, and a review dated before the code did not read the code

**Status:** accepted · **Date:** 2026-08-25 · **Decided by:** the lead coding agent at M12-W5, on
the Stage 4.0 seat's BLOCKING-3, under the standing instruction to finish the milestone. Recorded
because it amends the application of a control (V3C-78) that C2b had just sent for review, and
because it is the second time a review rule has been found to be missing an axis rather than
misapplied. · **Supersedes nothing; amends the application of V3C-78 and K.7.**

**The finding.** All four M12 waves closed the K.7 row GREEN citing council reviews dated
2026-08-24. Every M12 code commit is dated 2026-08-25. The rows stated the timing themselves — *"the
review preceded the code"* — written as a defence, and it is the proof: those seats reviewed M11's
product and named findings that M12 then implemented. **Nobody independently read M12's code until
this Stage 4.0 pass, which found two BLOCKING defects in it** (an `Int` conversion that traps on
non-finite input, and an L1 scope hole where an unbalanced fence exempted 26 lines from the
English-only rule). Both were in code that four green K.7 rows said had been reviewed.

**Why the rule did not catch it.** V3C-78 tiers review DEPTH by risk — one combined reviewer for a
LOW/MED wave, more seats for HIGH. D-133 settled review IDENTITY — a separate session, and the
review is a file. Between them they answer *how much* and *by whom*, and neither answers **when**.
A review is the only artifact in this process whose value depends entirely on its position in time,
and it was the one property nothing asserted. The gate inherited the blind spot exactly: it asked
whether a cited review exists and declares `seat: independent`, and had no notion of whether that
seat could have SEEN the work.

**The decision.** A review discharges K.7 for a body of work only if it is dated on or after the
record that cites it. An earlier review may still be CITED — it is often precisely what shaped the
wave, as M11's council shaped all of M12 — but it cannot close the row. The wave either cites a
review of ITS OWN code, or it WAIVES, and the waiver names a ledger row, which is what puts the
bypass in front of the owner (V4C-13).

**Shipped with its gate (V4C-49).** `scripts/wave_check.py::review_seat_problems` now reads the
`date:` of every cited review and refuses to let a stale one satisfy the seat requirement. Measured
across every wave record in the repository, it fires on exactly five: M12's four, and
`m7-wave-1-close.md`, which predates the seat rule entirely.

**The general form, which is the part worth keeping.** *Dates are a coarse instrument, and they are
the one the records already carry.* This is the fourth instance this milestone of the council's
through-line — a thing asserted somewhere and exercised nowhere, each half locally correct. The
council reviewed. The waves cited. Both were true, and no code was read.

---

## D-138 — `/v1/categories` publishes the margin and the second board's age

**Status:** accepted · **Date:** 2026-09-15 · **Decided by:** the owner, in session on 2026-09-15,
choosing "add to `/v1/categories`" over a fifth route (`/v1/margins`) and over leaving the contract
untouched and deferring the tie bands to M14; and, the same day, choosing rank RANGES over the
council's greedy bands (M13 plan §7 ruling 4, D1) after the W2 review. · **Amends the M13 plan §3
field freeze, for `/v1/categories` only; supersedes the plan's §7 ruling 4.**

**Context.** M13-W2 owns REQ-UNC-001 (no ordered rank inside the engine's own margin) and
REQ-UNC-002 (a coverage count, with the age of the second board). The engine decides both with
numbers it never published: `CategorySpec.close_call`, the margin `recommend()` compares the
runner-up against, and `recommend.secondary_age_days`, the age that decides whether a second score
counts. The M13 plan froze every `/v1` field set (§3) and named exactly this situation an escalation.
Measured on the shipping artifact: `expert` printed `#2 of 50` for a model 0.3 points behind the
leader, while 25 of its 50 models sit inside the 5-point margin on raw scores.

**Decision.** Each `/v1/categories` entry gains `close_call_margin` (the surface's margin, on its
native scale), `secondary_benchmark`, and `secondary_age_days` (the engine's own age against the
artifact's anchor; `null` when the board is undated OR the artifact cannot be read — a client may
claim only that the age is unavailable). The client shows every model's position as the RANGE of
places that margin allows (the `expert` leader reads `#1–27 of 50`: 25 on raw scores, plus the
rounding step conceded below), and states the benchmark count with that age.

**Why ranges, and why not the bands this ADR first shipped with.** The council's D1 ruling grouped
the ranking into greedy bands anchored at the top. The W2 Code-Reviewer measured it on the shipping
artifact: 47 adjacent pairs inside the margin (45 on raw scores) were printed in different bands —
`=2` beside `=5`,
0.6 points apart — which is the ordering REQ-UNC-001 forbids. No single rank number can avoid that,
because "within the margin" is not transitive. A range can: `best` counts the models clearly ahead,
`worst` the models clearly behind, and two models inside the margin of each other always overlap.
`ios/EngineTests/UncertaintyTests.swift` asserts the overlap as a property over every shipping
margin. The owner chose ranges over "keep D1 and narrow the criterion to the leader's band" and
over "rank only the leader's band".

**The rounding direction.** Served scores carry one decimal (D-109) and the engine decides on raw
ones, so a served gap is within 0.1 of the raw gap. The client treats two models as separable only
beyond `margin + 0.1`, which makes it impossible for rounding to order a pair the engine calls
tied. The cost, accepted: a pair whose raw gap is just outside the margin can be shown as
overlapping. Overstating the uncertainty by one rounding step is the error the criterion allows;
overstating the order is the one it exists to prevent.

**REQ-APP-005 is crossed, by name.** A range compares two served scores against the engine's
threshold, which is arithmetic on a served number. It prints no new number. The client-contract
tripwire used to match only the spelling `.score -` and could not see this crossing; it now also
matches arithmetic on a local `score`, and `SCORE_ARITHMETIC_PERMITTED` names `Uncertainty.swift`
with this ADR, so a second crossing fails until someone writes the ADR that permits it.
REQ-APP-005's prd row records the amendment.

**Why this is not the payload move D-115 forbids.** The argument D-134 made: the frozen thing is
what a consumer already parses, and the `/v1/recommendations` FIELD SETS do not move —
`tests/unit/test_uncertainty_contract.py::test_the_recommendations_route_did_not_gain_a_field`
compares every answer against the frozen key set. **It is not byte-identical, and the first draft
of this ADR said it was:** REQ-UNC-003 changes the VALUE of `evidence_dating_note` so that it names
its benchmark. The three new fields are additive on a discovery resource, and all three are
optional on the client so an older engine still decodes.

**What makes it honest rather than convenient.** The margin is checked against the engine, not
against itself: a test steers the margin just above and just below the fixture's real frontier gap
and asserts the served value reproduces the engine's `close_call` decision in both directions. The
age is the engine's own function, called by the route, not a copy of its query.

**The cost, stated.** `/v1/categories` now opens the artifact once per request, for two surfaces'
ages. It still answers with no artifact at all (the ages arrive as `null`), because the app builds
its navigation from this route and a discovery call that can blank the product is worse than a
missing fact.

**Revisit when:** the engine should compute the ranges itself, on raw scores, which would remove
the rounding concession above. That moves the answer payload and is therefore a real revision.

**Amended by D-181 (2026-10-06)**: the arithmetic on the margin and the scores this ADR publishes is checked on the compiled module, not by spelling; `Uncertainty.swift` stays the one file allowed it (added at the M19 closure, the repo review's M10).

**Amended by D-160 (2026-09-23)**: see D-160 (its arithmetic permission); the pointer was added at M21-W4 (the review's second round, M5, #200).

---

## D-139 — A second benchmark older than 90 days, or undated, does not upgrade a coverage claim

**Status:** accepted · **Date:** 2026-09-15 (ruled 2026-09-06; implemented in `3440abe`) ·
**Decided by:** the three-seat blind council the owner delegated his decisions to (M13 plan §7,
ruling 1, "A3"). **Written late, and recorded as late:** plan §5 says each answer becomes an ADR at
the wave that consumes it. W1 consumed this one, in `3440abe`, and no ADR was written until W4
noticed the gap. Plan §7 row 1 says W2; the commit says W1.

**Context.** `confidence_of` returned "High" whenever a second benchmark had scored the model. On a
coding surface the only such benchmark was Aider polyglot: last run 2025-10-03, 328 days before the
artifact's anchor, and covering 15 of 74 models. Measured across nine surfaces and three budgets,
exactly one pick of eighteen read High, and it was the coding budget pick. The product was most
confident about its cheapest fallback, because a defunct board happened to have run the older model.

**Decision.** A second board counts only if its newest run is at most `STALE_NOTICE_DAYS` (90) days
old against the artifact's own anchor. An undated board does not count: being unable to check is not
the same as having checked. The threshold is REUSED from REQ-REC-006, so the module holds one
definition of stale.

**Consequence, stated.** On today's artifact every pick reads one benchmark. The field is still
named `confidence` in `/v1`, frozen by D-115. Since D-138 the client renders the count and the
second board's age, and never the word.

**Revisit when:** a payload revision renames the field (second-opinion Q10), or a current second
benchmark enters a surface.

---

## D-140 — A score says what it is out of: `/ 100`, a named scale, or a rank alone

**Status:** accepted · **Date:** 2026-09-15 · **Decided by:** the council (M13 plan §7, ruling 3,
"C1"), under the plan the owner signed; consumed at M13-W4. · **Amends REQ-CMP-001** for ECI only.

**Context.** The owner asked for one "Score" on every card (owner, translated from Turkish). Taken
literally, that prints `Score 161.7` beside `Score 83.5`: two numbers on unrelated scales in the same
shape. That is the comparison D-105 forbids the engine from making. The five-seat council that
preceded the plan refused a bare "Score" 4–1, and every one of its seats endorsed the intent: stop
printing numbers a reader cannot place (`docs/handovers/handover_m13-start.md`). The three-seat §7
council then ruled the form, C1.

**Decision.**
- A bounded percentage metric reads `Score 83.5 / 100`.
- Elo reads `Score 1504.2 Elo`: unbounded, with the name of its scale and no invented ceiling. C1
  wrote `Score 1504 Elo`; the decimal is D-109's rounding of the served number, kept because
  REQ-CMP-001 keeps a served number exact.
- ECI prints NO score number. Its scale publishes neither a ceiling nor a unit a reader can hold, so
  only its rank range and the one-line scale explanation are shown.
- A metric this build does not know keeps the engine's own label.

The logic is `ios/ModelRanking/Engine/Scores.swift`, and the payload does not move.

**The cost, stated.** REQ-CMP-001 (M12) said the exact number is never replaced, only given a
companion. For ECI it is now replaced by its rank, on the card and in the ranking rows. The number
is still in the payload, and M14's detail screen is where it can return with its explanation.

**Revisit when:** ECI publishes a ceiling or a readable unit, or the detail screen ships.

**Amended by D-143 (2026-09-18)**: see D-143; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-141 — A HIGH wave owes its pulled-forward security pass, and its author cannot waive it

**Status:** **accepted by the owner 2026-09-22** (in session, at M15-W4, choosing "Yes, make it
mandatory" after five bypasses, W-106) · **Date:** 2026-09-15 · **Proposed by:** the lead agent at
M13 closure, as the control review C2b asked for (W-088, W-089, W-090). **Ratifying it is the
owner's**, because it changes what a wave-close row may say. First discharged by M15-W3, whose pass
is `docs/reviews/m15-closure-security-review.md`.

**Context.** Two texts define when a HIGH wave gets a security read, and they disagree. V3C-78 in
`AGENTS.md` §4 makes the pulled-forward security pass part of the HIGH tier: Code-Reviewer, Tester,
and security on the slice. The Security-Reviewer profile says a HIGH wave MAY pull one forward, and
names auth, PII, payment, crypto and migration. M13 tagged three waves HIGH, and each waived the
pass under the profile's narrower reading. The waivers were honest and each named a local ledger
row. None reached `docs/warnings.ledger.md`, so C2b could not count them. The Stage 4.0 seat then
found the cost: W1's `/health` memo reported an artifact the process could not read as `servable`
(M13 security review MAJOR-1). This is the control's seventh acceptance.

**Decision.**
- A wave tagged HIGH gets its pulled-forward security pass, whatever surface its author believes it
  touches. The tag is the plan's decision, and the author is the one person who cannot judge what
  the wave's own slice exposes.
- If the pass cannot run, row 4 reads WAIVED and names a row in `docs/warnings.ledger.md`, not only
  a local one, so the waiver is counted where C2b reads.
- A plan that does not want the pass for a wave tags that wave MED, and says why, in the plan the
  owner signs.

**Consequence.** One more independent seat per HIGH wave: for M13, three reads of a few hundred
lines each, against a MAJOR that escaped to closure. The profile's list stays as the trigger for
pulling a pass into a MED wave.

**Revisit when:** a HIGH wave's pass finds nothing for three consecutive milestones. That would say
the plans tag too widely, not that the pass is wasted.

---

## D-142 — The product answers the question a person actually asks, and coverage is how

**Status:** accepted · **Date:** 2026-09-18 · **Decided by:** **the owner, in session**, after
reading the council's finding and the M13 handover §5–6 and overruling them where they conflict.
His words, translated from Turkish: *"I don't care what the council said. We are going to do this,
we will find a way, if necessary we will pull every benchmark in the world and produce meaningful
results for what the end user asks."* · **Supersedes** the scope half of the M13 council's B-ballot
reading. · **Does not touch** D-104, D-105 or D-126.

**Context.** The product ranks models on nine measured surfaces. A person opened it on 2026-09-18
and typed `Image enchantment`, meaning *which model best polishes a profile photo*. The routing
worked perfectly: the on-device model understood the question, found nothing in the catalogue that
measures it, and said so. **The failure was not comprehension. It was that there was nothing to
answer with** — and the app's honest refusal is, from the reader's side, still a refusal.

Three prior findings bear on this and all three stand as measurements:

- **The catalogue gap here is a COVERAGE gap, not a measurement gap** (handover §5, Finding 1).
  Image editing is publicly benchmarked with Elo: LMArena Single-Image Edit (`cc-by-4.0`, clean),
  ImgEdit-Bench, GEditBench v2. Artificial Analysis's arena grants no redistribution right, which
  under this project's free-and-legal rule is operationally a prohibition (Finding 5).
- **A single general-capability axis is real in our data.** 73 models × 12 columns, 50.2% filled;
  on the largest complete block PC1 = 0.806, and 0 of 2000 column permutations came near it.
- **And it does not predict a held-out board well enough to print.** Leave-one-out: ARC-AGI 0.813,
  TerminalBench 0.560, WebDev 0.398, SWE-bench Verified 0.334, **DeepSWE −0.104 — worse than
  printing the mean.** The council killed the derived layer 5–0 on exactly this.

**Decision.**

1. **The product's purpose is restated.** It is not a ranking that a reader must already know how to
   query. It is a thing that answers the question a person asks in their own words. Listing is the
   means, not the end. Every milestone from M14 is measured against that.
2. **Coverage is the instrument, and its ceiling is the licence, not the effort.** The project will
   ingest as many benchmarks as it can legally serve, beginning with the surfaces real questions
   land on. "How hard is it to ingest" is not a reason to decline a surface; "we may not legally
   republish it" is the only reason that counts.
3. **The demand signal is captured instead of discarded.** Every decline sentinel is a person asking
   for a surface the catalogue does not have. It is recorded on the device, it leaves the device
   never (D-126 is untouched), and it becomes the ranked list of what to ingest next. The product
   learns its own gaps from the people using it.
4. **Research into answering a genuinely unmeasured capability is REOPENED**, against the council's
   5–0. The owner's ruling is that the question is worth work even after a negative result.
5. **What may not ship is unchanged, and the owner is not asked to move it.** A number nobody can
   falsify does not go on a card. The LOO figures above are the standing bar: a derived estimate
   ships when it beats printing the mean on a held-out board, and not before. Research is
   authorized; publication is earned.

**The cost, stated.** Clause 4 spends effort on a direction this project has already measured a
negative result in, and the negative result was not marginal — one of five boards came out worse
than the mean in the easy case. If clause 5 holds, the likely outcome of clause 4 is another
negative result and the work is spent on knowing that more firmly. The owner has read this and
ruled anyway, which is his to do; it is recorded here so that outcome is not a surprise later.

**The lead agent's clarification, recorded separately because it is not the owner's ruling.** Most
of what clause 1 asks for is not in conflict with the council at all. The council endorsed coverage;
what it refused was inventing a surface from the latent axis. Pulling every benchmark in the world
*is* the coverage path, and it is the fastest route to the owner's own example — image editing is
already measured by somebody with a clean licence. The genuinely contested slice is narrow: what the
product does when **no benchmark anywhere** measures the question. Clause 4 owns that slice and
clause 5 fences it.

**Revisit when:** a derived estimate clears the held-out bar in clause 5, or three milestones of
coverage work show the decline sentinel still firing on questions that no public benchmark measures.
The second outcome would say the gap is real and structural rather than a backlog.

---

## D-143 — One score, out of 100, and the unit stops being the reader's problem

**Status:** accepted; **"pinned in `CategorySpec`" amended by D-162** (the Elo anchor is the
surface's derived floor) · **Date:** 2026-09-18 · **Decided by:** **the owner, in session**, answering
the M14 plan §5 question about the ranking rows and ruling further than it asked. · **Amends D-140
and REQ-CMP-004.** · **Does not amend D-105.**

**Context.** M13-W4 put `Score 83.5 / 100` and `Score 1504.2 Elo` on the card, and gave ECI no number
at all, because its scale publishes no ceiling a reader can hold (D-140). That decision was built to
stop the product printing two numbers on unrelated scales in the same shape. The owner's ruling
accepts that the reader should not be handed the scale at all.

His words, translated from Turkish: *"the aim here is that the end user should not have to know how
the ranking and the scoring are done, or what the unit is. Let it show on all of them, but let us
convert it — a simple conversion to how much it is out of 100 — and show that. 'Resolved' and the
other measurement units: if somebody knows that much already, let them go and read the thousands of
benchmarks, they will understand it from there. Ours has to be simpler. So we reduce it to a single
scoring."*

**Decision.**

1. **Every ranking row carries a score**, not only the cards.
2. **Every score is displayed on one 0–100 scale**, and the name of the underlying metric
   (`% resolved`, `Elo`, `ECI`) is not put in front of the reader on the card or in the rows.
3. **The conversion is PER SURFACE.** It is a presentation of one board against itself. It is not,
   and may not become, a number comparable across surfaces.
4. **The conversion must be strictly monotonic within a surface.** It changes what a reader sees and
   never what the engine ordered. A conversion that reorders anybody is a defect, not a rounding.
5. **The tie margin converts with the score.** D-138's rank ranges are computed from the engine's own
   margin; if the score is rescaled and the margin is not, ties silently break or silently widen.
   Both are the same bug in opposite directions.

**What this ruling does NOT do, stated because the sentence "a single scoring" can be read as it.**
It does not create one number for a model across surfaces. D-105 stands: scores are never averaged
across boards. The M13 council measured why — PC2 is Arena, human preference is a separate axis, and
any single score folding it in destroys the one thing this product measures most credibly. **Ten
surface-local scores out of 100 is this decision. One overall score out of 100 is not, and the data
refuses it** (D-142 clause 5).

**The open problem this decision creates, and W4 owns it: what is 100?**

- **A bounded percentage metric** is already out of 100. Identity, no work.
- **Elo has no ceiling.** The honest conversion is the expected score against a **pinned reference
  rating** — the logistic Elo expectation, which is by construction a number between 0 and 100 and
  means something a reader can state: how often this model is preferred over the reference. The
  anchor is pinned in `CategorySpec` and versioned.
- **A ceiling taken from the current board's maximum is forbidden.** It makes a model's score move
  when a different model is added, with no change to any measurement of it. This project has shipped
  a number that moved for the wrong reason before; it is not shipping another.
- **ECI is unresolved.** It publishes neither a ceiling nor a readable unit. W4 either finds a
  defensible anchor for it or that surface keeps rank-only under D-140. **This ADR does not decide
  it**, and W4 may not invent one to be consistent.

**Where the code goes.** The conversion is arithmetic on a served score, and D-138 makes
`Uncertainty.swift` the one file allowed to do that, named by the gate. The conversion goes there, or
D-138 is amended in the same wave and the gate updated with it. It does not quietly appear in a third
file.

**The cost, stated.** A reader loses the ability to tell a measured percentage from a preference
score, and two surfaces' "83" will look like the same kind of fact when they are not. That is exactly
the confusion D-140 was written to prevent, and four of five council seats refused a bare "Score" on
that reasoning. The owner has ruled that the unit was noise to the reader this product is built for —
the reading that began with the 60-year-old CFO at M12-W2 — and that simplicity is worth the loss.
Recorded so the trade is visible rather than forgotten.

**Revisit when:** a reader compares two surfaces' scores out loud and gets a wrong answer from it, or
ECI's anchor cannot be defended.

**Amended by D-146 (2026-09-20)**: see D-146; the pointer was added at M21-W4 (the review's M6, #200).

**Amended by D-162 (2026-09-24)**: see D-162; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-144 — The optional-source exception belongs to the upstream, not to one board of it

**Status:** **accepted as amended by the owner 2026-09-20** · **Date:** 2026-09-18 · **Proposed by:** the lead agent at M14-W2,
because the change is to a rule the owner made. **Ratifying, amending or refusing it is his.** ·
**Extends D-121.**

**Context.** D-121 is the owner's ruling from M7-W1: `arena` may be an OPTIONAL source, so an
upstream outage cannot make the whole artifact unbuildable, and it is safe to allow because the
serving surface discloses a missing source rather than answering with an empty list. The ruling
names one source, and `tests/unit/test_sources.py::test_arena_is_the_only_optional_source` pins
that — deliberately, because an exception nobody pins becomes the default.

M14-W2 adds two more boards. They are not another vendor: they are other configs of the same
dataset, fetched from the same endpoint, under the same CC-BY-4.0 grant. **The outage D-121 exists
for takes all three at once.**

**The forced choice, stated plainly.** If the new boards are REQUIRED, one LMArena incident blocks
an artifact that today survives that same incident — the system becomes more fragile than the state
the owner's ruling was written to protect, as a side effect of adding coverage. If they are
OPTIONAL, the exception now covers three sources instead of one and the pin has to say so.

**Decision (proposed).** The exception attaches to the UPSTREAM. Every board of
`lmarena-ai/leaderboard-dataset` is optional, on D-121's own reasoning and its own condition: each
board is the sole evidence for its surface, and a surface with no evidence must SAY so rather than
answer with an empty list. A source from any other upstream stays required unless the owner rules
otherwise, one upstream at a time.

**What is NOT proposed.** This does not make optionality a default, and it does not extend to a
second vendor. If a future board comes from somewhere else, that is a new ruling.

**Consequence if refused.** `arena_document` and `arena_factuality` become `required=True`, the
pinning test returns to `{"arena"}`, and an LMArena outage fails the build. That is a coherent
position — it says a thin artifact is worse than no artifact — and it is the owner's to take.

**Revisit when:** a second upstream asks for the same exception, or an LMArena outage actually
costs a build.

**RULED by the owner, 2026-09-20, and the ruling is broader than the proposal.** Translated from
Turkish: *"if its data does not arrive, its last data stays valid. If the data is about a month old,
the list drops. If the data updates within that month, nothing happens and it joins the
calculations."* So the rule is not "optional or required" but **carry forward, with an age limit**:

- A source that fails a cycle keeps serving its **last good data**; the other sources still refresh.
- A source whose last good data is **older than ~30 days** takes its list down, and the list says so.
- A fresh fetch inside that window simply replaces the carried data.

**What the code does today is different, and the difference is the work.** A failed optional source
today leaves its surface empty in the candidate; D-128 then refuses the WHOLE candidate as worse, so
the old artifact keeps serving — which carries Arena forward, but also blocks every OTHER source's
fresh data (measured 2026-09-20: an Arena timeout refused a cycle that had fresh LiteLLM, OpenRouter,
SWE-bench and both new boards). The owner's rule carries forward per source, not per artifact. This
is scheduled as an M14 wave; D-144's status is superseded by this ruling.

---

## D-145 — A new surface's floor follows the rule the product ships, until one rule is chosen for all

**Status:** accepted · **Date:** 2026-09-20 · **Decided by:** the owner, in session, answering "A"
to the question put in plain words: *should the two new surfaces' quality floor be the top third of
the whole board, as the nine shipped surfaces actually are, or of the models the engine can sell, as
the header of `categories.py` says they are?* · **Disposes W-094 for M14.** · **Does not decide
W-094's underlying question.**

**Context.** W-094 measured that the nine shipped `min_quality` values are the top third of the
WHOLE board, while the comment above them says they are sized on the ranked population. The two new
surfaces had to pick one. On `document` the two rules admit the same 10 models; on `factuality` the
board rule admits 32 of 59 and the ranked rule 20.

**Decision.** New surfaces use the rule the product ships: the top third of the whole board,
counted over distinct models (each model's best rating). `document` 1467.5, `factuality` 1450.6.
The product keeps one rule across all eleven surfaces.

**What stays open.** Which rule is RIGHT is still W-094's question, and it is one decision for
all eleven surfaces at once, not a private choice for two. Until it is made, the header comment of
`categories.py` states a rule the numbers do not follow; that contradiction is now recorded here and
in W-094 rather than hidden.

**Revisit when:** W-094's question is decided for the whole product.

---

## D-146 — The out-of-100 anchor is its own pinned field, and `/v1/categories` publishes it

**Status:** **accepted by the owner 2026-09-20** (in session: "1. evet" to the field, "2. A" to
keeping the anchors and their cost as written); **clause 2 superseded by D-162** (2026-09-24, #15:
the anchor is the surface's floor) · **Date:** 2026-09-20 · **Proposed by:** the lead
agent, because the M14-W3/W4 review (`docs/reviews/m14-wave-3-4-review.md` B-1) found that W4 widened
`/v1` against the owner's ruling "No K.8 change in M14" (`docs/plans/m14-plan.md` §0 ruling 2).
**Amends D-143 and that ruling, for `/v1/categories` only.**

**Context.** D-143 says an Elo score is converted against a reference "pinned in `CategorySpec`". The
phone computes the conversion (D-138: `Uncertainty.swift`), so the phone needs that reference. W4 sent
it as a new optional field on each `/v1/categories` entry, `score_anchor`. That is a contract change,
and the owner had ruled there would be none in M14. The review is right that the field is sound and
that the record is missing.

**Decision.**

1. `/v1/categories` gains one optional field per entry, `score_anchor`: a number on Elo surfaces,
   `null` everywhere else. Additive; an older app ignores it and keeps showing the engine's own
   scale. No existing field moves. `/v1/answers` is untouched.
2. **The anchor is its own field in `CategorySpec`**, not the surface's `min_quality` (review M-3).
   The floor is re-measured at every recalibration; if it were also the anchor, every card's number
   would move with no new measurement of any model. The four values are pinned at 2026-09-20 to the
   floors of that day (`assistant` 1400.0, `web-dev` 1478.9, `document` 1467.5, `factuality`
   1450.6) and move only by a reviewed edit to `PINNED_SCORE_ANCHORS` in
   `tests/unit/test_uncertainty_contract.py`.
3. **Ties stay on the engine's own scale** (amends D-143 clause 5 as written). `rankRanges` keeps
   the native margin: the conversion is monotonic, so which models are tied is identical, and a
   margin converted at one point of a curved scale would be wrong at every other point. What converts
   is the SENTENCE: the tie note and the why/trade-off lines restate their distances on the /100
   scale, measured below the engine's leader, in points (`anchoredFact`, `distanceOutOf100`).
4. An anchor more than 2000 Elo from a score is refused on the phone (review S-4); the card keeps the
   engine's scale rather than reading every model as 0.

**The cost, stated, with the live numbers of 2026-09-20.** An Elo leader reads 57–79 out of 100
(`document` 57.0, `factuality` 57.2, `assistant` 65.0, `web-dev` 79.3); a percentage leader reads
72.8–100. The same model reads 54.6 on `assistant` and 94.4 on `mathematics`. Even anchoring at each
board's LAST ranked model would put the `document` leader at 65.7: these boards are narrow (113 Elo
from first to last on `document`), and no pinned Elo anchor spreads them like a percentage. A reader
who compares two surfaces will misread them. D-143 already names that cost; this ADR records its size.
**The owner chose to accept it (option A)** over relabelling Elo cards as a preference rate (option
B): the line under each card already says what 50 means.

**Revisit when:** the owner asks for Elo surfaces to look different from percentage surfaces, or a
recalibration makes a pinned anchor sit outside its board.


## D-147 — The wording tier routes on example questions, not on one sentence per surface

**Status:** **accepted by the owner 2026-09-22** (in session, after the measurement below: "right,
it was broken, I tested it too — OK, start from there" *(owner, translated from Turkish)*) ·
**Date:** 2026-09-22 · **Proposed by:** the lead agent, discharging W-115's owed probe run.
**Amends the M10-W1 router design** (`docs/reviews/m10-router-calibration.md`) for the similarity
tier only.

**Context.** The similarity tier compared a question with one descriptive sentence per surface.
M15-W3 added three surfaces, and the re-run probe (`docs/reviews/m15-router-recalibration.md`) fell
from 18 of 18 to 11 of 18 on the pre-M15 questions. The two search sentences became hubs, and four
rewordings only moved the hub. The tier was already weak on unseen wording before M15 (5 of 17).

**Decision.**

1. The similarity tier compares a question with **example questions** (`CategoryHints.examples`),
   six per surface. A surface scores as the mean of its two closest examples. The space is centred
   on the mean over all examples.
2. The decline groups (`CategoryHints.unmeasuredHints`) take the same form and the same scoring, so
   a decline and a surface are still read with one ruler (M13-W3 BLOCKING-1 unchanged).
3. `CategoryHints.byID` stays, for the on-device model tier, which reads descriptions.
4. A new surface needs both a description and at least two examples.
   `test_router_hints.py::test_every_described_surface_has_example_questions_for_the_wording_tier`
   is the gate.
5. A change to any example or decline group owes a run of `scripts/router_probe/` on both question
   sets, and the held-out set is never tuned against.
   **Amended 2026-09-22:** one decline example had been copied from the held-out set, and was
   replaced (scores unchanged; `docs/reviews/m15-router-recalibration.md` §6). The next held-out
   set is written by someone other than the author of the examples.

**The cost.** About 100 embeddings per question instead of 17, not yet timed on a phone. The examples
are a second hand-maintained table keyed to engine ids, gated as the first one is.

**Revisit when:** the held-out score drops below the probe's by more than it does now (18 of 22
against 21 of 21), a phone timing shows the tier is slow, or the on-device model tier covers enough
of the device base that this tier matters less.

## D-148 — One floor rule for every surface: the top third of the whole board

**Status:** **accepted by the owner 2026-09-22** (in session, at M15-W4, answering W-094) ·
**AMENDED the same day** by the lead agent after the W1 review (`docs/reviews/m15-wave-1-review.md`
M-1) showed the first text named the wrong population; **clause 1's population ruled by the owner
the same day: board ROWS** · **Date:** 2026-09-22 · **Proposed by:** the lead agent, from M15-W1's measurement.

**Context.** `categories.py` said every floor was sized on the RANKED population (reconciled and
priced). D-145 floored the M14 surfaces on the WHOLE board instead, and W-094 asked which rule the
product actually follows. M15-W1 computed both rules on all eleven shipped surfaces
(`docs/research/m15-board-survey-2026-09-21.md`): nine sit closer to the board rule, so the comment
had been describing the rule the product did not ship since M8.

**Decision.**

1. A surface's `min_quality` is the top third of the WHOLE board's ROWS, one per raw name as the
   board parser emits them (not the ranked population, and not distinct canonical models), for
   every surface, current and new. **Ruled by the owner 2026-09-22** ("every row in the list",
   translated from Turkish), choosing the count the M8 floors already follow. **This supersedes
   D-145's count:** `document`, `factuality`, `vision`, `search` and `search_factuality` were floored
   on distinct models and are re-derived under this rule in M16, with `agentic-coding`, which fits
   neither count.
2. The window and the tie margin keep M8's sizing by candidate count on the ranked population: they
   are about the models a reader can buy, and nothing measured them as wrong.
3. The header comment in `categories.py` states the rule and names the floors that do not yet
   follow it.

**The cost, stated (as measured by the W1 review, which recomputed every floor).** Under the ROWS
count, the M8 floors already hold: `abstract`, `computer-use`, `mathematics` and `web-dev` exactly,
`everyday` and `expert` within 0.3, `coding` within 0.4; only `agentic-coding` (50.0) fits no rule.
Under the DISTINCT-models count, seven floors move (`abstract` +6.7, `everyday` −5.3,
`computer-use` +3.9, `mathematics` +2.0, `coding` +1.6, `web-dev` +1.1, `expert` −0.3), some by
more than the surface's own tie margin. Either way the product has two counts today, and the
first text of this ADR hid that by calling the M8 floors D-145's. Re-deriving anything changes
what a surface recommends, so it is a calibration wave with its own review, owned by M16 (W-094).

**Revisit when:** a board's population is too thin for a third to mean anything (the two outliers
are the two thinnest boards), or M16's re-derivation shows the rule refusing a model a reader would
reasonably want.

*Applied 2026-09-23 (M16-W3).* Every surface's floor is re-derived under clause 1 from the served
artifact (`docs/research/m16-w3-floor-table-2026-09-23.md`, `scripts/survey_boards.py --floors`).
Nine floors move; one pick changes (`agentic-coding`'s Budget Pick at `medium` and `unlimited`), and
the owner ruled that surface under the same rule, so no surface is an exception.


*Amendment, 2026-09-23 (owner, M17 plan §0.2; closes W-127).* Clause 2 names a second sizing rule
it had always had in the tree: **on an Elo board that publishes confidence intervals, the tie margin
and window measure what the board cannot tell apart** -- the live 95%-interval overlap for
`assistant` (M3), and the median gap of pairs whose published intervals overlap, window four times
it, for `document`, `factuality`, `vision`, `search` and `search_factuality` (`scripts/calibrate_board.py`).
The candidate-count sizing stays for the boards without published intervals. No number changes.

**Amended by D-159 (2026-09-23)**: clause 1 stays the rule; each floor's value is computed by the build from its board instead of kept by hand in `categories.py` (added at M21-W4, #200).

---

## D-149 — One application: the engine refreshes itself, and the app can ask it to

**Status:** **accepted by the owner 2026-09-22** (in session, at M15-W4) · **Date:** 2026-09-22 ·
**Proposed by:** the lead agent, answering the M13 note the M15 plan carried as "the app / harness
split" (§1, scoped in W4, not built).

**Context.** Asked what the M13 note meant, the owner first chose "data collection versus the
application", and the lead agent recorded that as a separation to be proposed in W4. The owner then
said what they actually want (translated from Turkish): "a single application that is also the
updater". Today the product is three pieces that run independently: the iOS app, which only reads;
the engine (`src/app/adapter/main.py`, started by `ios/app.sh up`); and the refresh
(`src/app/workflows/refresh.py`), run every 12 hours by a separate launchd job
(`deploy/com.hcs.modelranking.refresh.plist`, `StartInterval` 43200). The app cannot see or start a
refresh, and the refresh does not depend on the engine running.

**Decision.** The note is answered by merging, not splitting.

1. The engine owns the refresh schedule: while it runs, it starts a refresh cycle on the same 12-hour
   interval, so one process is started instead of two, and the launchd job is retired once this
   ships.
2. The engine calls `refresh.py`'s existing entry point and nothing else. The refresh keeps every
   property it has today (the lock that stops two cycles overlapping, the build's own safe publish,
   the refusal to publish a candidate that is not better), so there is still one definition of
   "safe to serve".
3. The app gains an "update now" action and shows when the data was last refreshed. Starting a
   refresh is a new request to the engine, and any new `/v1` route or field needs its own ADR before
   it ships (M15 plan §3); that ADR is part of the build wave.
4. Collection stays on the Mac. The collectors are Python and cannot run on the phone, so "one
   application" means one engine that answers and refreshes, and one app that shows and can ask for
   a refresh.

**The cost.** A refresh now shares a process with the server answering the app, so a slow or
failing cycle must not block or crash it; the build wave has to show that, not assume it. A refresh
button is also a way to make the engine do expensive upstream work on demand, so it needs a
rate limit and a place in the security review.

**Owning milestone: M16**, a build wave of its own. Nothing is built in M15; this ADR replaces the
"separation" proposal W4 was going to write.

**Revisit when:** the engine moves off the owner's Mac (the `fly.toml` deployment), where a
scheduler inside a server that can be scaled to zero or to several copies behaves differently.

**Amended by D-151 (2026-09-22)**: see D-151; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-150 — Two controls reviewed at their third acceptance: the Swift floor, and a fact `/v1` does not carry

**Status:** clause 1 **accepted by the owner 2026-09-22** (in session, at M15-W4, choosing "derive
it") and **AMENDED the same day** -- the mechanism it was accepted on cannot do what it claimed, see
the amendment under clause 1; clause 2 **accepted by the owner 2026-09-22** at the M15 sign-off · **Date:**
2026-09-22 · **Proposed by:** the lead agent, because `check_records` C2b stopped the M15 closure:
V3C-02 and K.8 each reached their third acceptance (W-043, W-048, W-111; W-009, W-020, W-112).

**Clause 1 — V3C-02: the Swift test floor is derived, not typed (W-111).**
*Context.* `SWIFT_TEST_FLOOR` is an integer in the `Makefile` that someone raises by hand. It has
been wrong three times (W-091, W-111 and the M14 closure's count), and each time the gap was a
number of tests that could be deleted with `make check` green, which is V3C-02's hole: a criterion
whose only citing test disappears silently. The two earlier acceptances (W-043, W-048) were
criteria that had no test at all; this one is a test that exists and is not protected.
*Decision.* The floor is computed at check time from the `func test` declarations under
`ios/EngineTests`, and `swift test` must run at least that many. A deleted test lowers both numbers
together only if its declaration is deleted too, which is a visible diff, not a silent loss.
*Owning milestone:* M16-W1. **Built 2026-09-22:** `ios/EngineTests/test-manifest.txt` lists every
test (262 at the M16-W1 close; first written here as 258, which the wave's review measured wrong); `make swift-test` diffs it against `swift test --list-tests` and takes the floor from its line
count, and `tests/unit/test_swift_test_manifest.py` compares it with the declarations in the source
for lanes with no Swift toolchain. Verified red four ways: a test deleted from the code, a line
deleted from the manifest, a renamed test, and the count falling short.

*Amendment, 2026-09-22 (M15-W4 independent review, MAJOR-2).* **The decision above is wrong, and the
lead agent wrote it and put it to the owner in those words.** A floor derived from the declarations
drops together with the declarations: deleting a whole test removes one of each, and `make check`
stays green. It only catches a test that is declared but no longer runs. Put to the owner again,
correctly: **the check reads a committed list of test names, and fails when a listed test did not
run**, so a deletion needs a visible edit to the list, which a reviewer sees in the diff. Ruled by
the owner 2026-09-22 (in session). The paragraph above stands as the record of what was first
accepted and why it was withdrawn.

**Clause 2 — K.8: the control held; it keeps its shape (W-112).**
*Context.* In all three acceptances the rule did its job: nothing was added to `/v1` without an ADR.
W-112 is the plan promising a fact on the detail screen that `/v1` does not publish; W2 dropped it
and recorded the drop instead of adding the field quietly. The owner ruled the field IN, to be
published under its own ADR in M16.
*Decision (accepted by the owner 2026-09-22).* K.8 stays as it is. What repeats is not a bypass of the contract but a plan
line written before anyone checked what `/v1` carries, so the plan template's shared-contracts
section should list, for every screen a wave builds, which `/v1` field each fact comes from. That
check belongs in the plan the owner signs, not in a wave.
*Carried out 2026-09-22 (M16-W1):* the clause is written into `AGENTS.md` §4 beside K.8 itself,
because this repository has no plan template — a rule in a template nobody instantiates is the
wallpaper V4C-49 warns about. W-112's `C2b-reviewed` marker now names an accepted decision, which is
what the M15-W4 re-review's MINOR-3 asked for.

**Revisit when:** the name list misses a deletion (clause 1), or a fourth K.8 acceptance is
about a field that WAS added without an ADR (clause 2).

---

## D-151 — The refresh runs once a night, quietly, and the app never asks for one

**Status:** **accepted by the owner 2026-09-22** (in session, at M16-W1) · **Date:** 2026-09-22 ·
**Amends D-149** clauses 1 and 3, which are superseded by this ADR. Clauses 2 and 4 stand.

**Context.** D-149 gave the engine the refresh and gave the app an "update now" action with a
"last refreshed" time, on the 12-hour interval the launchd job used. Asked how often a reader may
press that button, the owner answered the question underneath it (translated from Turkish): *"the
lists do not update that fast. Once at midnight is enough — this is not the stock market."* And
then: *"no need [for the button]. The app updates when it is installed on the phone; apart from
that it refreshes once somewhere between 23:00 and 01:00, in the background, without telling the
reader and without making them wait for anything. What more should it do with the lists?"*

**The measurement behind it.** The boards this product reads publish on the order of days:
`document` moved by one model and `search` by one between two survey runs a day apart
(`docs/research/m15-board-survey-2026-09-21.md`). Twice a day was never sized on how fast the data
changes.

**Decision.**

1. **Once a day, in a window, not on the hour.** The engine starts one refresh cycle per day at a
   time it picks inside 23:00–01:00 local. The window is spread deliberately: a fixed midnight is
   the hour every scheduled job on the machine wakes up, and the upstreams see the same minute
   from everyone who copies this.
2. **A stale artifact catches up at startup.** If the engine starts and the artifact's last
   successful refresh is more than a day old, it refreshes then — this is the "it updates when the
   app is installed" case, since the engine is what the app talks to. One catch-up, not a retry
   loop.
3. **No "update now", and no refresh control in the app.** Nothing in the reader's path waits for
   a refresh, and no screen shows refresh state. The app keeps reading whatever the artifact holds
   (D-128 still refuses to publish a surface the engine cannot stand behind).
4. **`/v1` gains nothing for this.** With no button there is no request to make, so the refresh
   ADR D-149 clause 3 asked for is not needed. `last_refreshed` is not published either; if a
   reader-facing freshness line is ever wanted, that is its own ADR.

**The cost.** A failure at 23:xx is invisible until someone looks: with no button and no screen,
the only signals are the refresh log and `/health`. The build wave keeps both honest, and a
refresh cycle still may not block or crash the engine answering the app (D-149's stated risk).
Data can also be up to a day old rather than half a day; on boards that move on the order of days
that is a difference nobody can see.

**Revisit when:** a board starts publishing intraday, or the owner wants to see freshness in the
app after all.

---

## D-152 — `/v1/categories` publishes each surface's floor, and the detail screen shows it

**Status:** **accepted by the owner 2026-09-22** (in session, at the M15 closure: "send it, show
it") · **Date:** 2026-09-22 · **Closes W-112** · **Precedent:** D-146, which added
`score_anchor` the same way.

**Context.** The M15 plan said the detail screen holds "the surface's floor" — the number below
which this product does not recommend a model. It does not, because `/v1/categories` does not
publish `min_quality` at all, and plan §3 refuses a quiet addition: a fact `/v1` does not carry is
an ADR. W2 dropped the line and recorded the drop (W-112).

**Decision.**

1. `/v1/categories` gains one field per surface, `min_quality`, on the surface's own scale, beside
   `close_call_margin` and `score_anchor`. A field is added; nothing changes shape (K.8).
2. **It is its own field and never derived from `score_anchor`, which today equals it on every
   Elo surface.** The two move for different reasons: the anchor is pinned by an owner ruling
   (D-146 clause 2), the floor is a calibration. A test moves one and not the other, the shape
   D-146's own regression uses.
3. The detail screen renders it as the line "we would not recommend below this", in both
   languages, as a fact the engine sent (`Detail.swift` composes, the view renders — D-138).
4. It is NOT a filter and changes no ranking: `/v1/recommendations` already applies the floor.
   Publishing it tells a reader what the engine did, it does not ask the client to do it.

**The cost.** The floor becomes a number readers can quote, so M16-W3's re-derivation under D-148
will move a number that is now on screen. That is the right order: publish the fact, then change it
under a ruling with a before/after table, rather than changing it while it is invisible.

**Revisit when:** a surface's floor stops being a single number (a per-effort floor, say), at which
point the field's shape is a new ADR rather than a new value.

---

## D-153 — The search surfaces say what their price does not include

**Status:** **accepted by the owner 2026-09-22** (in session, at the M15 closure, choosing "state
it" over withholding the picks) · **Date:** 2026-09-22 · **Closes W-119.**

**Context.** `search` and `search_factuality` rank models on the blended per-token price like every
other surface. What a search-capable model actually costs also includes a per-search fee, which
this catalogue does not carry: `registry.py` reconciles `gpt-5-search-api` and
`o4-mini-deep-research` to their base families, so they are priced at the base model's tokens. The
image boards were refused for exactly this kind of gap (per-image pricing, M14-W1), and the M15-W1
survey named it — then W3 shipped the surfaces without a ruling and without saying so. The
independent seat found it (M15-W3 review MAJOR-2).

**Decision.**

1. The two search surfaces keep their price-based picks. A per-token comparison is still the
   comparison a reader makes between these models, and withholding Budget Pick and Best Value
   would leave the surface less useful than the honest alternative.
2. **Each of them publishes what the price leaves out**, as a code on `/v1/categories`
   (`price_excludes: "search_call"`, absent on every other surface), never as a sentence from the
   server: the app owns its two languages (D-129), so the engine sends the fact and the client
   words it.
3. The app shows that line wherever it shows a price for those surfaces — the card's price line
   and the detail screen — not only in one place a reader may never open.
4. If a per-search price ever becomes available for the models on these boards, this field goes
   away with the gap it describes, under its own ADR.

**The cost.** A third price-shaped fact on screen, and a reader may still assume the listed price is
the whole cost. The alternative was to publish no picks at all on two surfaces the measurement
supports, which trades an honest partial answer for none.

**Revisit when:** a board arrives whose models carry two priced units (per-token and per-call), and
the engine has to rank on both rather than disclose one.

---

## D-154 — How the engine runs its own refresh: a child process, off by default, never in production

**Status:** **proposed** (M16-W2, lead agent; the owner reviews it at the milestone) · **Date:**
2026-09-23 · **Implements** D-149 clauses 2 and 4 and D-151; **keeps** D-116 clause 2.

**Status (2026-10-04, #33):** accepted -- the owner signed M16, the milestone this ADR named for his review, by merging its closure PR #9 on 2026-09-23 (`829e02d`); `docs/closure-report-m16.md` put D-154 before him in §0 item 1 and §1 and made that merge the sign-off. He ruled D-170 on 2026-09-25, which amends clause 2. The wave itself had no PR: `5fc3f02` was pushed to `main` under D-117, before the project's first PR.

**Context.** D-151 says what the engine does -- one refresh a night inside 23:00-01:00, one catch-up
at startup on a stale artifact, nothing in the app -- and D-149 names the risk: a refresh now shares
a process with the server answering the app. Three choices were left to the build, and each one
decides whether that risk is contained or merely hoped about.

**Decision.**

1. **The refresh runs as a CHILD PROCESS** (`python -m app.workflows.refresh`, the existing entry
   point), started and awaited by an asyncio task in the engine's lifespan
   (`src/app/adapter/nightly.py`). Not a thread: a thread cannot be killed, shares the interpreter's
   memory and holds a pool slot. The child is killed past 30 minutes (a real cycle takes 6-9
   seconds) and on engine shutdown. The serving process never imports the refresh, the build or the
   ingest code, so REQ-REF-007's structural half holds from both sides (a test reads the imports).
2. **Off unless `MODEL_RANKING_REFRESH=nightly`**, which `ios/app.sh` sets on the owner's Mac.
   **`validate_startup_config` refuses it outside the relaxed environments**, so a production engine
   with the switch on does not boot: D-116 clause 2 keeps ingestion off a serving host, and
   D-149's "revisit when the engine moves off the Mac" becomes a startup error rather than a note.
3. **`/health` gains four string fields** -- `refresh` (`off` / `scheduled` / `running`),
   `refresh_next`, `refresh_last` (the refresh's own recorded outcome) and `refresh_last_at` --
   additive, as that route's contract allows. `/v1` gains nothing (D-151 clause 4).
4. **The launchd job is retired by the owner** with `scripts/retire_refresh.sh`, which refuses to
   run until the engine reports its own refresh, so there is never a night with no refresher. Until
   then the two share `refresh.py`'s `flock` and cannot overlap; the second exits `busy`.

**The cost.** A timeout kill leaves the killed cycle's uniquely-named candidate file behind (W-124);
the live artifact is untouched and the next cycle runs normally. A Mac asleep through the whole
window skips that night; the next start or the next night catches it up.

**Revisit when:** the engine is deployed anywhere but the owner's Mac -- clause 2 then refuses to
boot it with the switch on, which is the point at which ingestion needs a home of its own.

*Amendment, 2026-09-23 (M16-W2 security pass, `docs/reviews/m16-wave-2-security.md` MAJOR-1).*
**Clause 1's last sentence is wrong as first written.** The serving process never imports the
refresh, the build or the source fetchers -- now measured transitively, in a fresh interpreter --
but it DOES load the source parsers (`app.workflows.ingest`, `app.clients.*`) and `httpx`, and did
before this wave, through `subscribe -> plans -> ingest` and `rank -> clients.epoch`. No fetch runs
in the server; the code that could fetch is present in it. Untangling the chain is W-125. The same
pass tightened four things now part of this decision: the child inherits an ALLOWLISTED environment
(no tokens from the owner's shell), its output is kept as a 64 KiB tail rather than buffered whole,
the switch is checked again when the schedule starts, and `-P` keeps the working directory off the
child's module path. `scripts/retire_refresh.sh` checks that the process listening on `:8080` runs
`app.adapter.main:app` before asking it -- a command-line check, which a process named to imitate it
would pass; the owner runs it on his own machine.

*Amendment, 2026-09-23 (M16-W2 code review, `docs/reviews/m16-wave-2-review.md`).* **"The Cost" said
a Mac asleep through the window skips that night; the code ran about a minute after waking.** Both
are now one rule, stated here: a run that comes due after its window has closed happens only if no
good cycle is on record within a day (D-151 clause 2's catch-up, applied on waking), and is skipped
otherwise. And "once a night" now holds across restarts too: a nightly run is skipped when a good
cycle is on record within 4 hours, so a startup catch-up at 23:11 is not followed by a second
cycle at 00:05 (12 hours at first, which the re-review showed skipped a whole night after a daytime
catch-up). A cycle that leaves no record of its own -- killed at the timeout, unable to start,
or crashed before `refresh.py` could write one -- is remembered by the engine and reported on
`/health` as `killed`, `not started` or `crashed`, instead of the previous cycle's outcome.

*Amended 2026-09-29 (M17 closure, milestone review M6).* Clause 2's switch is set by the engine
service's wrapper (`scripts/engine_service.sh`, D-170), not by `ios/app.sh`.

**Amended by D-173 (2026-10-04)**: clause 4's `scripts/retire_refresh.sh` is removed with the retired refresher (clause 7), and the child inherits the serving-bound variables (clause 4).

**Amended by D-170 (2026-09-29)**: clause 2 -- the engine runs as a launchd service, from a deployed release of `main` (added at M21-W4, #200).

**Amended by D-217 (2026-10-21, proposed)**: the revisit has come -- the hosted engine's refresh runs on a GitHub Actions runner, a third place that is neither the Mac nor a serving host; the refresh switch stays refused outside the relaxed environments (#387).

---

**AMENDED 2026-10-04 (M18-W6, #90; W-126, W-130; decided by the agent on the owner's standing
instruction of 2026-09-29).** Clause 1's kill is now the last of three limits:
- the cycle's downloads share a budget of 20 minutes; past it, the sources left carry their last good
  data (D-156);
- the cycle ends at 27 minutes. The kernel ends it (SIGALRM, default action), so no call that holds
  the interpreter can delay it; the engine reports "timed out";
- the engine kills it at 30 minutes, as before.

The engine starts the cycle in a session of its own and kills the whole group, whether or not the
cycle itself has exited, so a grandchild such as the parquet reader (D-165) cannot hold the output
pipe. A session of its own is outside launchd's cleanup of a dead engine's group. So the engine
names itself to the cycle (`MODEL_RANKING_ENGINE_PID`), and a cycle whose engine is gone ends
itself within seconds, the same way as at its limit (the W6 review's M1). "A real cycle takes 6-9
seconds" was true when written; with M17's boards a slow night is bounded by the budget, not by the
kill.


## D-155 — The project runs on DevFlow v6.0

**Status:** **accepted by the owner 2026-09-23** (in session, choosing each option below) · **Date:**
2026-09-23 · **Supersedes:** the git clause of the A0.5 operating mode as this project practised it
(agent commits pushed to `main` on the owner's word), by adopting D-999 below.

**Context.** The owner's own methodology moved from General Pipeline v5.0 to
[DevFlow v6.0](https://github.com/SADCAIVibe/DevFlow/tree/v6.0) (translated from Turkish: *"a
flow I developed; we will use it from now on"*). This project installed GP v5.0 at D-113 and had
since changed the control surface itself -- the review-seat gate, the inline-span language rule,
the C2b trigger, the per-module coverage floor, `swift-test`, `client-decls`. A copy-over would
have deleted those; keeping v5.0 would leave the project on a method its owner no longer uses.

**Decision.**

1. **The install is upgraded by a three-way merge**, base = GP v5.0 (the tag this project
   installed), theirs = DevFlow v6.0, ours = this tree. Files the project never changed take
   DevFlow's version; files DevFlow never changed keep the project's; files both changed are
   merged by hand, and the project's own controls survive every conflict.
2. **Git (D-999):** the agent works on a branch, pushes that branch and opens a DRAFT pull request;
   the owner marks it ready and merges. No AI attribution in commits, PR bodies or issues; agent
   identity plus the `GP-Agent`/`GP-Task` trailers stay (V4C-64). Staging is `git add -u`.
3. **`.github/workflows/**`** is the owner's surface under DevFlow. The adoption PR carries the
   workflow changes in ONE separately marked commit, a one-time exception the owner chose, so the
   owner reviews them as workflow changes.
4. **Where this project deliberately differs from DevFlow v6.0**, each with its reason, so the
   next harvest can hand them back rather than rediscover them:
   - `scripts/wave_check.py` keeps `review_seat_problems` (REQ-REV-001, W-056) -- DevFlow has no
     check that a review is a file by an independent seat -- and requires the three v5.1 footprint
     fields only of records declaring a version after v5.0 (GPF-001: 41 records predate them).
   - `scripts/check_records.py` keeps the project's L1 (balanced fences, double-backtick spans, a
     length bound on exempted spans), the C2b trigger, and `seat:`; adds `retrospective` to the
     record types -- nine retrospectives were "invalid" once selection moved to frontmatter.
   - `scripts/bootstrap-check.sh` takes DevFlow's position-aware scan (GPF-003) and also strips
     inline code spans (W-015), which GPF-003 does not.
   - `scripts/coverage_floor.py` is DevFlow's skip budget; the project's per-module floor (W-041)
     moves to `scripts/module_coverage_floor.py` and `make coverage-floor` runs it.
   - `src/__init__.py` from the package is NOT installed: in this src-layout tree it turns `src`
     into a package and mypy then reports 113 `import-untyped` errors on `app.*`.
   - `.governed-records-exempt` names three M7 reviews whose `status: proposed` predates the
     status flow (GPF-001), which the old glob kept out of scope.

**The cost.** The owner reviews a large one-time diff, and `main` must be protected in GitHub for
D-999 to be more than an honour system -- that setting is the owner's (`docs/branch-protection.md`).
Four DevFlow defects found while merging go back to DevFlow rather than being patched quietly here
(the adoption PR lists them).

**Revisit when:** DevFlow ships a version that absorbs the differences in clause 4.


*Amendment, 2026-09-23 (independent review `docs/reviews/devflow-v6-adoption-review.md`, PASS WITH
FINDINGS 0/5/7/4, and the first CI runs on PR #1).* Corrections to the text above, and what changed:

- "Four DevFlow defects" is wrong: the field-findings record lists every defect found, and the count
  grew with each review and CI run. Read the record, not a number here. Clause 4's "113
  `import-untyped` errors" is 105 `import-untyped` and 8 `no-any-return`.
- **Instruction surfaces are graded again (review MAJOR-1).** DevFlow's `lib_record.is_record` made
  every file with `record_type:` frontmatter a record, so templates and the current plan were
  skipped by the git-authority and documented-command checks. Templates and the CURRENT milestone
  plan are now instruction surfaces; plans of closed milestones are records with or without
  frontmatter. The skill check skips records the same way, and the two retired-skill rows are gone.
- **Allowlist rows are exact (MAJOR-2).** `src/*`, `tests/*`, `test_*.py`, `docs/plans/*`,
  `docs/research/*`, `workflows/*` and `scratchpad/*` matched every path below them (`*` crosses
  `/`); each is replaced by the exact paths the records cite.
- **The `GP-Agent:` trailer is checked again (MAJOR-3)**: DevFlow v6.0 removed the check as "AI
  attribution"; this project keeps the trailer (clause 2), so `test-git-authority` requires it in
  `issue-agent.yml` and `test-commit-identity` requires it on every agent commit on the branch.
  The local lane's identity (`noreply@anthropic.com`) is now recognised as an agent identity.
- **`bootstrap-check.sh` (MAJOR-4)** sets its placeholder counter before the ADR scan (it aborted
  under `set -u`) and strips inline code there too, as clause 4 claimed.
- **CI** installs PyYAML for the workflow check, audits declared dependencies, calls `make falsify`,
  and the skip budget is 62, the count CI measured. `dep-audit` and `install-and-governance` had
  been red on `main` since the v5.0 install; all six jobs are green on PR #1.
- `.gp/installed` is gitignored: `make install` rewrites it on every target (MINOR-3).
- `scripts/refresh_job.sh` changed only its shebang to `#!/usr/bin/env bash` (the shell-dialect
  check); launchd runs it through `/bin/bash` explicitly, so behaviour is unchanged (NIT-4).

**Open, and the owner's:**
1. **Clause 3 said ONE workflow commit; PR #1 carries two more** (9c9845c: PyYAML, `pip-audit --strict .`,
   `make falsify`), made because the first CI run showed three steps that could not pass. They
   stand only if the owner accepts them; otherwise they come out before the merge (MAJOR-5).
2. **The owner identity is vacuous here** (MINOR-4): `git config user.email` in this clone is the
   agent's, so `test-commit-identity` compares the agent with itself. It needs the owner's own
   commit email, passed as `--owner-email`, which only the owner can supply.
3. **The pre-tool hook blocks pushes to `main` but not `gh pr merge`, `gh pr ready`,
   `--no-verify` or `git push origin refs/heads/main`** (MINOR-5). Until the owner rules on a
   hook change, branch protection on `main` is the only enforcement of those four.


*Owner rulings on the three open items, 2026-09-23 (in session, translated from Turkish: "commit
what DevFlow says, create the PRs, I will merge. You can take my identity from git. If you are
leaving it to branch protection anyway, is there a need to ask?"):*
1. The two further workflow commits on PR #1 are accepted with it; the owner reviews and merges.
2. The owner identity is the address GitHub wrote on the owner's merge of PR #1, committed in `.owner-identity`
   with the D-999 anchor (`5fc3f02`, the last direct push). `test-commit-identity` reads it, fails
   an agent commit on the branch without the `GP-Agent:` trailer, and fails the local agent identity
   on `main`'s first-parent chain after the anchor (a rebase-merge or a push that skipped a PR).
   Its self-test covers both.
3. No hook change: `gh pr merge`, `gh pr ready`, `--no-verify` and `refs/heads/main` pushes are
   left to branch protection on `main`, which the owner sets.

**Amended by D-161 (2026-09-23)**: see D-161; the pointer was added at M21-W4 (the review's M6, #200).

---

## D-156 — Every source carries its last good data for 30 days, judged from when it last arrived

**Status:** **accepted by the owner 2026-09-23** (in session, M16-W3 plan, both options below) ·
**Date:** 2026-09-23 · **Implements** D-144 as the owner ruled it on 2026-09-20; closes W-116.

**Context.** The owner's ruling on D-144 (translated from Turkish): *"if its data does not arrive,
its last data stays valid. If the data is about a month old, the list drops. If the data updates
within that month, nothing happens and it joins the calculations."* The build did the opposite per
source: a failed optional source was emptied, a failed required one failed the whole build, and
D-128 then refused the candidate, throwing away every OTHER source's fresh data (measured
2026-09-20).

**Decision.**

1. **Every source carries forward**, the four required ones (`swebench`, `aider`, `litellm`,
   `openrouter`) included, and the Epoch bundle and boards (ruled 2026-09-23). A source that fails
   a cycle serves its last good `scores` and `pricing` rows from the live artifact.
2. **The limit is 30 days, measured from when the source last ARRIVED** in a cycle whose content is
   what the live artifact serves (published or unchanged), kept per source by the refresh. Not
   from `observed_at`: an unchanged cycle publishes nothing, so a row's stamp can be far older than
   the fetch that confirmed it. With no record for a source, the rows' own newest `observed_at`
   stands in, which can only overstate the age.
3. **Past 30 days the source is not carried**: an optional source's surfaces drop and say so, and a
   required source fails the build as before. The refresh accepts a surface blinded by an EXPIRED
   carry -- D-128 would otherwise refuse the candidate and freeze every other source -- and still
   refuses every other blinding.
4. **Disclosure is the engine's** (ruled 2026-09-23): the refresh record (`carried`, `expired`,
   `sources_last_ok`) and `/health` (`refresh_carried`, `refresh_expired`, additive to D-154's four)
   name each carried or expired source and its age. `/v1` and the app do not change (D-151 keeps operations out of the
   app; the board's own run date, already shown, is what a reader judges by).

**The cost.** A price or a score can serve up to 30 days after its source stopped answering, beside
fresher data from other sources; `/health` is where that shows. A surface can disappear at day 31
until its source returns.

**Revisit when:** a source's outages start lasting weeks, or the owner wants the carry visible in the
app after all.

*Amendment, 2026-09-23 (M16-W3 independent review, `docs/reviews/m16-wave-3-review.md`, BLOCKING).*
How clauses 2-4 are carried out, corrected after the review measured the first version:
- **One source of truth.** The build writes which sources arrived, were carried or expired, and the
  stamp each age is measured from (`--report-out`), on success and on failure; the refresh reads it
  and no longer re-infers it from row stamps (review MINOR-1, MINOR-2). A stamp from the future is
  not an age; the rows' own stamp stands in.
- **The exemption follows the benchmark, not `primary_source`** (review MAJOR-1): an expired source
  excuses every surface whose primary board its rows fed in the live artifact. `epoch_swe_bench_verified`
  feeds `coding` without being its primary source, and its expiry used to refuse every cycle.
- **The record describes what is served** (review MAJOR-2): `carried` and `expired` hold stamps, and
  `/health` computes the age when asked. A cycle that is not served leaves the carried set as it was;
  an expired source stays listed until it arrives in a served cycle, and a required source's expiry
  is recorded even though it fails the build.

*Second amendment, 2026-09-23 (M16-W3 re-review, `docs/reviews/m16-wave-3-rereview.md`).* It
supersedes the first amendment's exemption bullet.
- **An expiry excuses the loss its own rows account for, never a whole surface** (re-review
  MAJOR-1). Excusing each surface an expired source fed also lifted D-128 from the fresh primary
  source beside it, and it broke clause 3's "still refuses every other blinding". So on an expiry
  night the candidate is judged against the live artifact with the expired sources' `scores` and
  `pricing` rows removed and `px_median` re-derived (`refresh._served_without`), and every guard
  runs against that baseline: the model count, the budget axis and the median price. The median
  price is new: on the whole-surface rule, an expired cheap model moved a median and was refused.
  **Except the new-names guard** (third review `docs/reviews/m16-wave-3-rereview-2.md`, MINOR-1):
  removing rows never adds a name, so it is judged against the live artifact. Otherwise a surface
  the expiry blinds would pass for "a surface returning" and admit a roster never served. Where the
  baseline surface is blind, its median falls back to the served one.
- **A future stamp.** An arrival from the future falls back to the rows' own stamp. If the rows are
  ahead of now too, the clock stepped back, and the source carries at age 0 rather than expiring
  (re-review MINOR-1) -- if they are less than 30 days ahead. Further ahead they expire (third
  review MINOR-2). `/health` prints `?d`, never a negative age.
- **What `expired` means** (re-review NIT-2): the sources whose last good data is past 30 days. A
  cycle that is not served can leave such rows live, for example a required source that fails the
  build; `expired` lists them all the same, because their age, not their presence, is the fact.

**Amended (2026-10-04, M18-W5, #92 N2)**: carried rows meet the store's rules. A carried date is stored as a calendar date, and a source whose live rows hold a score that is not finite is not carried: it fails as an unreachable source would.

**Amended by D-179 (2026-10-06)**: the baseline also unlinks each derived model the expired rows leave without a price or a score, as a build does (D-157), and the board guards read the baseline's rows (a board the expiry empties keeps its live rows, for the third review's MINOR-1). Before, an expired price feed's derived models stayed linked in the baseline, and the accessibility guard refused the night.

---

## D-999 — the agent opens drafts; a human merges

**Status:** accepted -- adopted verbatim from DevFlow v6.0 by D-155 (2026-09-23).

**Decision.** The agent works on its own branch, commits there normally, pushes that branch and
opens a DRAFT pull request. It never pushes the protected branch, never marks a PR ready, never
merges, never force-pushes, never uses `--no-verify`, and never writes AI attribution anywhere.
A human marks ready and merges. Branch protection is what makes this real rather than an honour
system.

**Rationale.** Withholding `push` protected one property: no commit may be mistaken for the
owner's. That property is now carried by the branch, the draft state, the absence of AI
attribution and `conformance/test-commit-identity.py`. A review that happens in pull requests
needs the branch pushed.

**Revisit when:** a forge-less workflow needs supporting, or branch protection is not available.

---

## D-157 — A model on the boards reaches the lists without a code edit: the list wins, the data derives the rest

**Status:** proposed (M16-W4 plan; the principle ruled by the owner 2026-09-23, the mechanism to be
ratified with the wave) · **Date:** 2026-09-23 · **Supersedes** REQ-CAN-001's clause "unmatched
names are dropped with a count reported, never guessed".

**Status (2026-10-04, #33):** accepted -- the owner ruled the principle on 2026-09-23 (quoted under Context) and clauses 2 and 4 the same day (W4 plan decisions 1 and 2), and merged the wave that built it: PR #6 on 2026-09-23 (`5f6ab30`, the derived registry), its fix round PR #8 the same day (`eee2faf`, the first amendment), and the M16 closure PR #9 (`829e02d`, the second amendment). He ruled D-166 on 2026-09-25 as an amendment of it.

**Context.** The registry is a hand-kept rule table. On 2026-09-23, 1,450 of 2,834 score rows in a
fresh build matched no rule, GPT-6 Astra among them, with scores on six boards and prices on
LiteLLM. Every new model family waits for a code edit, so the lists fall behind the boards they
are built from. The owner (translated from Turkish): *"'Never guess' was something like v1; we are
maybe at v3 by now, and the app's main purpose has changed a little. If it is on a list, the list
wins; but when we cannot give anything, I cannot call it guessing any more -- we will present the
list we derived from the data as a result of measurements, our own list."*

**Decision.**
1. **The curated rules win.** A name a curated rule matches keeps that rule's model.
2. **A name no rule matches is normalised by a fixed grammar** (provider prefixes, dates and effort
   suffixes removed; every variant token kept), and registered as a DERIVED model when that id has
   both a price and a score. (Threshold ruled 2026-09-23, W4 plan decision 1.) The grammar is deterministic and tested; it is not fuzzy matching.
3. **A variant never merges into its parent by construction**: the derived id keeps every token
   the name carries after its version.
4. **Disclosure is the engine's** (ruled 2026-09-23, W4 plan decision 2): `/health` and the build report
   name derived models and the top unmatched names.

**The cost.** A derived model's display name is the grammar's, not a curator's, until a rule is
written. Two spellings the grammar does not unify stay two models until a curated rule joins them.

**Revisit when:** a derived registration is found merging two different models, or splitting one.

*Amendment, 2026-09-23 (M16-W4 review, `docs/reviews/m16-wave-4-review.md`, BLOCKING-1).* The
revisit trigger fired before merge: the first grammar removed any `-vN`, everything after `:` or `@`,
and any vendor head, and so merged products (deepseek-coder-v2 priced as `deepseek-coder`; three
Mistral 7B versions as one). Clause 2's decoration is now a CLOSED list -- the route; `:batch`,
`:free`, `:nitro`, `:floor`, `:exacto`; `@default`, `@latest`; a region head; a vendor head only before
its own family word; Bedrock's `-v1:0` only after such a head; Epoch's underscore effort;
separator spelling -- and every other token stays, so clause 3 holds by construction again. A fine-tune
(`ft:`) is never derived. **The residual, stated:** names two sources spell identically are one model
to the grammar, even where a vendor reused the name for two releases (`claude-3.5-sonnet`,
`mistral-7b-instruct`) or keeps a moving alias (`deepseek-chat`, `o1-mini`; about thirteen registered
ids, `docs/reviews/m16-wave-4-rereview.md` MINOR-1); only a curated rule splits those. Clause 2's
"dates ... removed" was never true of the code and is withdrawn: no date is removed.

*Second amendment, 2026-09-23 (M16 Stage 4.0 security review, MAJOR-1).* A derived model's DISPLAY
name is a spelling of the model and nothing else: the name's last route segment, at most 64
characters of a closed alphabet, reading as the same model through the grammar; otherwise the id.
Taken verbatim, a score's name had served "Visit evil.example ... /zeta 9" as a model name with no
length bound.

**Amended by D-189 (2026-10-09)**: clause 2 -- a curated rule refuses a fine-tune's name (`ft:`) for its reason, as the derive path does (#165).

**Amended by D-166 (2026-09-25)**: a moving, undated API alias never creates a derived model (added at M21-W4, #200).

---

## D-158 — The nightly refresh fetches the Epoch bundle itself

**Status:** accepted -- the owner ruled the direction and its clock on 2026-09-23 (M16-W4 plan,
decision 3) · **Date:** 2026-09-23 · **Amends** REQ-ING-010's owner-fetched acquisition.

**Context.** The Epoch bundle was downloaded by hand because the sandbox the project started in got
HTTP 403 from epoch.ai. The engine now runs on the owner's machine, which fetches it fine, and a
directory nobody refreshes meant nine of nineteen sources carried every night until they expired
(D-156). A fresh bundle measured on 2026-09-23 grows five boards by 18 to 50 percent.

**Decision.**
1. **The refresh fetches, the build never does.** `refresh --fetch-epoch` downloads
   `https://epoch.ai/data/benchmark_data.zip` into scratch beside the artifact, unpacks it, hands it
   to the build as `--epoch-dir`, and removes it after the cycle. The nightly schedule passes the
   flag; an owner-supplied `MODEL_RANKING_EPOCH_DIR` wins over it. Programmatic callers and tests
   are off the network unless they pass a fetcher.
2. **The archive is untrusted input.** A member that names a path outside the directory, is a
   symbolic link, resolves outside through an existing link, or expands past the limit (counted
   while writing) refuses the whole bundle; so do too many members and a body that is not a zip.
3. **A failed or refused fetch is a failed source**: the boards carry under D-156, the reason goes
   to the cycle's log, and nothing else in the cycle changes.
4. **The acquisition clock is the refresh record** (owner, decision 3): each Epoch board's arrival is
   in `sources_last_ok`, like every other source. `data/epoch-source.yaml` keeps the URL. Its
   `last_verified` stays until the CI step that reads it is removed; that step is a workflow change,
   proposed to the owner in the M16-W4 pull request.

**The cost.** The refresh now depends on epoch.ai answering; when it does not, the boards carry for
up to 30 days, which is the D-156 behaviour this replaces for the owner-fetched case too.

**Revisit when:** Epoch publishes a versioned API, or the bundle outgrows its 64 MB limit.

---

## D-159 — Every floor is derived from its board in every build

**Status:** accepted -- ruled by the owner 2026-09-23 (M17 plan §0.1, chosen over re-deriving at each
deliberate publish) · **Date:** 2026-09-23 · **Amends** D-148's application: clause 1 stays the rule;
its VALUE is computed by the build instead of kept by hand in `categories.py`. Closes W-128 when built.

**Context.** D-148 clause 1 makes a floor the top third of the board's rows. The rule is relative to
the board, so a floor measured on one day's boards goes stale as the boards grow: the fresh Epoch
bundle moved six floors (`abstract` 72.8 → 84.7). Kept by hand, every refresh widens the gap between
the rule and the number (W-128).

**Decision.**
1. The build computes each surface's floor from the board it ranks, under D-148 clause 1, and the
   artifact carries it. `/v1/categories` publishes that floor (D-152); the engine recommends from it.
2. `categories.py` keeps the RULE's parameters, not a number. The measurement script
   (`scripts/survey_boards.py --floors`) and the build call one function, so they cannot disagree.
3. D-128's guards and D-132 still judge every candidate: a floor that empties a budget, or moves a
   surface's roster past the limits, is refused like any other change.

**The cost, accepted by the owner.** A Budget Pick can change overnight because a board grew, with
nobody reading a before/after table first. That was the check M16 plan §0.3 kept; the owner chose
current floors over it.

**Revisit when:** a floor move changes a pick in a way a reader reports as wrong.

*Clarification, 2026-09-23 (M17-W1).* Clause 1's "the artifact carries it" is met by the artifact's
own rows: the floor is derived WHERE IT IS READ, from the served artifact, by one function
(`src/app/workflows/floors.py`), rather than computed at build time into a table. It is the same
number from the same rows; nothing stored can disagree with the rows beside it, and an artifact
built before M17 serves a correct floor. A surface whose own board is empty has no floor, and its
Budget Pick says so.

*Correction, 2026-09-23 (M17-W1 review, `docs/reviews/m17-wave-1-review.md`).*
- **Clause 3 described a guard that does not exist and should not be built.** The floor is not a
  filter: the budget caps decide which models a reader can be offered, and the floor only decides
  which of them the Budget Pick names. A guard refusing "a floor that empties a budget" would refuse
  every night a board grows past a budget's best model, and so freeze the refresh (D-128's own
  failure mode) against the owner's ruling that floors follow their boards.
- **What does exist:** a moved floor is a SERVED change. The refresh's fingerprint hashes every
  surface's floor, so a board that grows only by models nobody prices, which moves the floor and no
  ranked row, is published rather than reported as "nothing a user would notice"
  (`tests/unit/test_floor_served.py`).
- A surface whose own board is empty answers with its own reason, `no_floor_measured`, which the app
  words in both languages.

*Owner ruling, 2026-09-23 (re-review `docs/reviews/m17-wave-1-rereview.md`, OWNER-R1).*
- **The correction above withdraws only clause 3's first half**, "a floor that empties a budget".
  Its second half, "moves a surface's roster past the limits", is D-128 and D-132, which run on every
  candidate unchanged.
- **The gap the withdrawal left, put to the owner:** the floor is derived from every row of a board,
  and D-132's new-names limit reads only ranked models. On a copy of the owner's artifact, 60 rows
  nobody prices moved `coding`'s floor from 65.4 to 71.3, and neither guard objected. Asked (in
  Turkish, translated) "should we prevent this?", the owner ruled **"yes, add a simple guard"**.
- **The guard:** D-132's limit applies to each surface's own board, by raw name. A candidate whose
  board would be more than a quarter names the served artifact has never seen is refused, like any
  D-132 refusal, and a legitimate jump is published by hand. A board that was empty and answers
  again is a source returning, and passes, as a surface returning does
  (`refresh.upward_anomalies`; `tests/unit/test_floor_served.py`).
- **And its mirror (re-review 2, MAJOR-1):** a board that would lose a quarter or more of its names
  is refused as D-128 refuses a surface that loses a quarter of its models. Without it, a board could
  lose half its rows and move the floor as far as the flood did, and the rows' return would then be
  refused every night as "new".
- **What the guard is not (re-review 2, MINOR-1 and MINOR-3):** it limits ONE NIGHT's change to a
  board, not the floor. 57 unpriced rows (a quarter less a few) still move `coding`'s floor from 65.4
  to 74.4, and a second night can move it again. It also refuses some legitimate nights, each
  published by hand like any D-132 refusal: measured on the owner's artifact, an Epoch bundle
  returning after about two weeks away (28-32% new names), and an upstream that respells its names
  (ECI's `_` to `-`: 284 of 521). Single ordinary days measured 14-17% at most.

**Amended by D-179 (2026-10-06)**: the guard compares a board's rows by the model each links to, and by
raw name only where a row links to none, so an upstream that re-spells its names and keeps every model
(ECI's `_` to `-` above) is no longer refused (#100).

---

## D-160 — A combined list is built on the phone, and nothing about the question leaves it

**Status:** accepted -- ruled by the owner 2026-09-23 (M17 plan §0.3 "show it plain", §0.4 "nothing
leaves the phone", each chosen over the recommendation) · **Date:** 2026-09-23 · **Extends** D-104's
privacy boundary to the on-device model; **amends** D-138's arithmetic permission.

**Context.** M17 answers a question with a list no leaderboard publishes, by combining boards
(the owner: "that is the app's biggest feature"). The on-device model (Apple Intelligence) reads the
typed question into a structured intent. The plan recommended sending the intent's CODES to the
engine; the owner ruled that nothing leaves the phone.

**Decision.**
1. **Nothing derived from the question leaves the device**, not the text and not an intent. The
   engine publishes each board's standings on an additive `/v1` route (board identity, date, each
   model's position and price), fetched like any other data, and the question never shapes the request.
2. **The phone builds the combined list**, in the Engine layer, by POSITION on each chosen board,
   never by averaging raw scores (D-105). One named file does it, and the client-contract gate
   permits it by this ADR beside `Uncertainty.swift` (D-138).
3. **The list is shown plain.** The boards it came from and their dates are on the detail screen,
   not on the list itself.
4. **The on-device model only maps a question to an intent** (D-104: no model generates, adjusts or
   explains a score, price or availability). When it is unavailable, the router (D-147) stands in.

**The cost.** The app does more work and carries more data. A reader looking only at the list does not
see that it is the product's own combination; the detail screen says so.

**Revisit when:** a reader takes a combined list for a published leaderboard, or the standings payload
outgrows what a phone should download nightly.

*Amended 2026-09-29 (M17 closure, milestone review M3).* **Clause 1, as the code does it, is D-168
note 9:** the surface a question routes to is sent as `task` of `/v1/recommendations`, as since
D-126, the same request a reader's own tap on that surface makes. The question's text, its
refinements and the reader's removals never leave the device.

**Amended by D-181 (2026-10-06)**: clause 2 (the combination does arithmetic on positions only, in `Combine.swift`) is checked on the compiled module, through the names D-181 lists; gap G-2 holds the rest (added at the M19 closure, the repo review's M10).

**Amended by D-168 (2026-09-28)**: the "intent" wording -- the question selects its boards as a surface plus declared refinements (added at M21-W4, #200).

## D-161 — The project runs on DevFlow v6.4, and session commits carry the owner's identity

**Status:** accepted -- the owner asked for the upgrade (2026-09-23, translated from Turkish: *"I
moved DevFlow to v6.4, update DevFlow here again"*) and ruled the identity clause in session
("my identity", chosen over DevFlow's per-developer default) · **Date:** 2026-09-23 · **Amends:**
D-155 clauses 1, 2 and 4.

**Context.** DevFlow moved from v6.0 to v6.4: no retrospectives, handovers or `note.txt` in the
package; `METHODOLOGY.md`, the pre-commit configuration and the `governance-contract` workflow gone;
`.githooks/pre-push`, `docs/control-events.csv`, `.devflow-stack`, `CLAUDE.md` as `@AGENTS.md`, UTF-8
named on every text read and write, and a commit-identity check that refuses an AI tool's address.
Until now this project's agent commits were authored by the tool's own address with `GP-Agent` and
`GP-Task` trailers (D-155 clause 2), which that check refuses.

**Decision.**

1. **The upgrade is `UPGRADING.md`'s method:** `git diff v6.0 v6.4 | git apply -3` on a branch,
   excluding `.github/workflows/*` (the owner's part), `src/*` and `tests/unit/test_health.py`
   (DevFlow's template edits there are docstrings; `src/` is the product), and the deletions of
   `note.txt` and `docs/handovers/*` (this project's own history, which the diff cannot delete
   cleanly). Seed documents keep the project's content; `docs/decisions.md` and
   `docs/watchlist.md` declare `process_version: v6.4`, from which `make install` derives the
   installed version.
2. **Commit identity (replaces D-155 clause 2's identity half):** a session commit carries the
   owner's git identity, and an agent's commit adds the `GP-Agent:` and `GP-Task:` trailers, so an
   agent commit is still told apart from the owner's own by its trailers. The CI issue agent
   commits as `gp-agent` and owes the trailer too (`conformance/test-git-authority.py`). The rest of
   D-155 clause 2 stands: drafts only, the owner merges, no AI attribution.
3. **Where the project still differs from DevFlow v6.4** (continuing D-155 clause 4), each with its
   reason:
   - `scripts/check_records.py` and `schemas/record.schema.json` stay the project's: they pass this
     project's records and v6.4's own self-test fixtures, while v6.4's validator reports 121
     findings on records written under earlier versions.
   - `scripts/check_fast.py` stays the project's (a Python chain that keeps `coverage-floor` after
     `test`, and the Swift suite run as `swift-test-parallel`); it gains `--plan`, which v6.4's
     `conformance/test-check-fast.py` reads.
   - **`closes` is not a prerequisite of `check:`.** `scripts/closure_check.py` ignores
     `process_version` and fails all fifteen closure reports written before DevFlow; the wave
     closes it also grades are already graded by `wave-check-all`. A closure report is checked at
     its own closure with `make closure-check`, as before.
   - P-005's risk tiers (one combined reviewer on a LOW/MED wave) and a security seat at every
     milestone close stay, beside v6.4's Code-Reviewer-then-Tester and its single Stage 5.1 review.
   - `scripts/bootstrap-check.sh` is v6.4's, plus W-015's strip of inline code spans, which v6.4's
     position-aware scan still lacks.
   - `make lint` covers `scripts/`, so two DevFlow scripts carry small lint fixes
     (`slopsquat_check.py`, `create_labels.py`), and the 82 text reads and writes that v6.4's
     `conformance/test-text-encoding.py` found in `src/`, `scripts/` and `tests/` now name UTF-8.
4. **The owner's part:** the workflow change (`governance-contract.yml` removed; `ci.yml` and
   `issue-agent.yml` as v6.4 ships them, keeping the trailer rule of clause 2) is proposed in the
   upgrade PR, not made; branch protection stops requiring `governance-contract` when it is
   applied; `make hooks` turns on the pre-push gate once the owner decides about the untracked files
   in the working tree that `make secrets` would read.

**The cost.** One more large diff to review, and a tree that differs from DevFlow in the places
clause 3 lists. The defects found on the way go back to DevFlow in
`docs/research/devflow-v6.4-field-findings-2026-09-23.md`.

**Revisit when:** DevFlow grades closure reports by their declared version, or absorbs a clause-3
difference.

*Amendment, 2026-09-23 (DevFlow v6.6, the same upgrade PR; the independent review
`docs/reviews/devflow-v6.4-upgrade-review.md`, PASS WITH FINDINGS 0/4/5/8).* The branch takes
DevFlow v6.6 as well (`git diff v6.4 v6.6 | git apply -3`, workflows excluded), and the text above
changes as follows:

- **Review depth: fully DevFlow (owner ruling, 2026-09-23,** asked in Turkish, answered "Tamamen 6.4",
  translated "fully 6.4"). Every wave gets Code-Reviewer, then Tester, as two separate subagents, at
  every risk tier; the security review runs once, at Stage 5.1. **P-005's risk tiers and the
  per-milestone security seat are retired**, and clause 3's bullet keeping them no longer holds.
  From v6.5 each verdict declares `**Independent:** yes`; this project keeps its own K.7 check too,
  that the review is a file declaring `seat: independent`.
- **check-fast is DevFlow's** (`scripts/check_fast.py` byte-identical to v6.6). The project's own
  legs are in `stack.mk`: `CHECK_FAST_OWN_LEGS = client-decls swift-test` and
  `CHECK_FAST_FORMS = swift-test=swift-test-parallel`. W-041's per-module coverage floor moved into
  the `test` recipe, after pytest: as a separate `check:` prerequisite it would run in v6.6's
  records leg, beside the tests, and read the previous run's `coverage.json`.
- **`scripts/check_records.py` stays the project's.** It passes this project's records and v6.6's
  self-test fixtures; v6.6's reports 121 findings on `main` (120 R2 on records written under
  earlier versions, 1 C2b) and 124 on this branch. v6.5's unclosed-fence `L1`, v6.6's C2b wording
  and v6.6's issue-owned ACCEPTED ledger rows are therefore not checked here: in this project an
  ACCEPTED row names a milestone.
- **Clause 3 was wrong about two controls, and they are restored** (review MAJOR-2 and MAJOR-3):
  - `scripts/wave_check.py` refuses a close that is undated, or dated after 2026-09-23, and
    declares a version older than v6.6; every close is then graded by the version it declares, so
    a later DevFlow field does not turn it red (the v6.6 upgrade review's MAJOR-1 and MAJOR-2 on the
    first version of this fix, which regraded later closes by every future rule and missed an
    undated one). A close dated 2026-09-23 itself can still declare an older version: that day
    holds this project's real v6.0 closes;
  - `conformance/test-commit-identity.py` fails a machine-identity commit on the branch with no
    `GP-Agent:` trailer. On session commits under the owner's identity the trailer is a convention
    nothing can check, because nothing tells them from the owner's own. `.owner-identity`, which no
    check read after v6.4, is deleted. The check's self-test runs inside `make test`
    (`tests/unit/test_wave_check_versions.py`), so a DevFlow re-take that drops it goes red.
  - Clause 2's "the CI issue agent commits as `gp-agent`" is true once the owner applies the
    proposed workflow change; until then `issue-agent.yml` sets `gp-issue-agent`.
- **`scripts/wave_check_all.py` derives its scope** (review MAJOR-1): every close declaring v5.0 or
  later is graded, so a close stamped v6.6 by today's template is in scope.
- **`.path-refs-allow`** drops v6.4's `docs/plans/*` and `docs/reviews/*` wildcards again, for one
  exact row, `docs/reviews/release-security.md` (review MINOR-1).
- **Two things v6.4 changed that clause 3 did not say** (review MINOR-5, MAJOR-4): the post-edit
  hook runs `make check-fast`, not `make gate`, so secrets, deps and slopsquat run at `/pre-merge`,
  the pre-push hook and CI, not after every edit; and `make bootstrap-check` fails C11 (nothing gates
  a push) until `main` is protected and the brief says so (issue #13) or `make hooks` is on.
- **Numbers corrected** (review NITs): five DevFlow scripts differ from DevFlow, not two, four by
  lint fixes and `slopsquat_check.py` also by a docstring (`ci_liveness.py` is a sixth, from v6.5,
  lint only); `closes` would also fail the 20 pre-migration wave records.
- **The owner's part grows by one line:** v6.5's duplicate-key check fails
  `.github/workflows/issue-agent.yml`, which sets `pull-requests: write` twice (lines 31 and 33).
  GitHub rejects the file, so the issue agent has never started. The proposed workflow diff fixes
  it; until the owner applies it, `conformance` (and so `make check` and `make gate`) is red on it.

**Amended by D-172 (2026-09-29)**: the per-milestone security seat is back, once at each milestone's closure, and never per wave.

**Amended by D-199 (2026-10-15)**: the project runs on DevFlow v7.1; `make closes` stays out of `make check`, and the commit identity rule is unchanged.

## D-162 — The out-of-100 anchor is the surface's floor, and moves with it

**Status:** accepted -- **ruled by the owner 2026-09-23** (asked in Turkish whether the reference
should stay pinned or move with the floor, the owner chose, translated, "move the reference with the
floor"); built in #15 · **Date:** 2026-09-24 · **Supersedes:** D-146 clause 2 · **Amends:** D-143
("pinned in `CategorySpec`") and REQ-SCR-003.

**Context.** D-146 clause 2 kept each Elo surface's out-of-100 anchor as its own pinned number, apart
from the floor, so a recalibration could not move every card. D-159 then made the floor derived from
the served board every build. The two drifted apart, and the app's sentence "50 is at the bar we
recommend from" stopped being true: `assistant`'s floor read about 51, not 50 (M17-W1 review
MINOR-5, W-133).

**Decision.**
1. On every Elo surface `/v1/categories` serves `score_anchor` = `min_quality`, the floor D-159 derives
   from the served board. `CategorySpec.score_anchor` and the pinned table are removed.
2. Where there is no floor (no artifact, or an empty board) there is no anchor: `score_anchor` is
   `null`, and the app keeps the engine's own scale (D-146 clause 1). Off Elo nothing changes:
   percentages are already out of 100, and ECI stays rank-only (D-143).
3. D-146 clauses 1, 3 and 4 stand: the field is optional and additive, ties stay on the engine's
   scale, and an anchor more than 2000 Elo from a score is refused on the phone.
4. The app's sentences are unchanged: they already say "50 is at the bar", which is now true.
5. An artifact that cannot be read, or is caught mid-republish, serves no floor and so no anchor for
   that request: a card may show the engine's own scale for one load rather than a number out of 100
   against a guess. `/v1/categories` and `/v1/recommendations` read the artifact separately, so
   across a publish that moves a floor, one load can pair the new anchor with the old answer (the
   floor restated as, say, 50.3 instead of 50). Both are accepted: the next load is consistent.

**The cost, accepted by the owner.** A model's number out of 100 can now move without a new
measurement of that model: when its board grows and the floor moves, every card on that surface moves
with it. D-143 forbade exactly that for an anchor taken from the board's MAXIMUM; the floor is the top
third of the board's rows (D-148), which moves far less, and D-159's guards limit how fast a board
may change in one night. Measured on the owner's artifact the day it was built, the leaders move by
at most 0.9 points: `assistant` 65.0 -> 64.1, `vision` 61.0 -> 60.3, `document` 57.0 -> 56.5,
`factuality` 57.2 -> 57.0, `search_factuality` 56.3 -> 56.5, `web-dev` and `search` unchanged.

**Revisit when:** a reader reports a card's number moving with nothing new measured, or a board's
floor moves by more than a few points in one publish.

## D-163 — A criterion about the served data is tested against the served data, not a fixture

**Status:** accepted -- **ruled by the owner 2026-09-24** (asked in Turkish whether the check should
stay on the owner's machine or get a small pinned artifact in CI, the owner chose the first) ·
**Date:** 2026-09-24 · **Reviews control V3C-02 at its third acceptance** (`check_records` C2b; W-043,
W-048, W-132), from issue #14.
(D-162, the out-of-100 anchor, is decided in issue #15 and lands with its own pull request; the
two were written the same day on separate branches.)

**Context.** V3C-02 says a criterion whose only citing test cannot run in CI is half a gate. Three
rows have now accepted it. The third, W-132, is CAT-10 (`tests/unit/test_categories.py`: every
surface's value window stays below its floor). Since D-159 the floor is derived from the served
board, so the rule is about the served data itself. CI has no served artifact: a fixture would test
the fixture, and a pinned copy in the repository would test last month's boards.

**Decision.**
1. **A criterion that is a property of the served data is tested against the served data.** Its test
   is marked `artifact` (skipped by name where the artifact is absent, W-108), and it runs in the
   owner's `make test` (`MODEL_RANKING_REQUIRE_ARTIFACT=1`) and before every publish the owner makes.
   CI is not where such a rule is proven, and no pinned artifact is added for it.
2. **The rule's LOGIC still gets a fixture test where it has logic of its own** (a function that
   computes the floor, the window, the comparison). Only the data half stays artifact-only.
3. V3C-02 stands for everything else: a criterion about code, a contract or a process is not excused
   by this ADR.

**The cost.** A served board that breaks CAT-10 is caught on the owner's machine, not on a pull
request, and only when the owner runs the tests or publishes. The refresh's own guards (D-128, D-132,
D-159) are what run every night.

**Revisit when:** the engine runs somewhere other than the owner's machine, where a nightly check
against the served artifact could run.

## D-164 — A board is published content, and the refresh guards it as a board

**Status:** accepted -- **ruled by the owner 2026-09-24** (M17-W2 plan, decision 5, put to the owner in
Turkish in session and in PR #23; the owner answered, translated, "okay, continue") · **Date:**
2026-09-24 · **Extends** REQ-REF-002's "changed", D-128 and D-132 from surfaces to boards · from #22.

**Context.** M17-W2 stores Arena's category slices as boards that no surface ranks on; W4 serves them
(D-160). The refresh decides "changed" on what the artifact would serve, and `serving_summary`
fingerprinted surfaces only. A candidate that adds or moves boards therefore read as "nothing a user
would notice changed" and was discarded, while the refresh record listed the source as served. The
D-128/D-132 guards iterate surfaces too, so a board no surface names was unguarded.

**Decision.**
1. **Each declared board's standings are part of the fingerprint**: every row's name, the model it
   reconciled to (what W4 serves as the model's identity), and its score, rounded as the output
   boundary rounds it (D-109). A candidate that changes only a board publishes; one that only
   re-stamps its rows does not.
2. **The board guards apply to each board**: refused when a quarter or more of its raw names are lost
   (D-128), or more than a quarter are new (D-132), exactly as for a surface's own board (D-159).
3. **A board seen for the first time is returning, not new** (the existing empty-set rule), so the
   night that first carries the boards is not refused.
4. A board that fails to fetch carries on its own clock (D-156), as every source does.

**The cost.** A glitch on one thin board can now hold back a night's publish that would otherwise have
gone out. That is the guard doing its job: a board that loses a quarter of its names in one night is
bad data until someone looks.

**Revisit when:** boards held back a publish on more than one night in a month, or W4 serves boards on
a route whose own checks make this one redundant.

**Amended by D-179 (2026-10-06)**: clause 2's limits compare a board's rows by the model each links to,
and by raw name only where a row links to none; a re-spelling is recorded with the night (#100).

## D-165 — A downloaded file a native library parses is read in a process of its own, under a memory ceiling

**Status:** accepted -- **ruled by the owner 2026-09-24** (asked in Turkish whether to read the Arena
slice file in a separate process with a memory ceiling or to accept the risk and record it; the
owner chose the first) · **Date:** 2026-09-24 · from #22, M17-W2's re-reviews
(`docs/reviews/m17-wave-2-rereview.md` BLOCKING-R1, `m17-wave-2-security-rereview.md` S-R1).

**Context.** pyarrow decodes a whole column chunk before any check written in Python can run, and a
parquet file's sizes are its writer's claims. Two independent re-reviews made a 57 KB file take more
than 1 GB in the refresh process, growing linearly up to the download cap; two rounds of in-process
checks (the footer, then a counted decode budget) did not bound it.

**Decision.**
1. **The file is parsed by `app.clients.parquet_reader` in a child process**, which watches its own
   peak resident size from a thread and leaves with `EXIT_OVER_CEILING` past `MAX_READER_RSS`
   (512 MiB; the live `text` file reads at about 60 MB). The parent also stops it after
   `READER_TIMEOUT_S`.
2. **Every way the reader fails is a `SourceError`** for that config's slices: the ceiling, the time
   limit, a crash (a native one included), or an answer outside its protocol. The build carries
   the slices (D-156) and never fails the cycle over one file.
3. The in-process checks stay as cheap first refusals of a changed file (types, footer, rows as
   read, value length, decode budget); the ceiling is the bound.
4. **What the reader says is bounded before the parent holds it** (the second security re-look,
   S-R2-1): the answer is JSON lines read against `MAX_ANSWER_BYTES` (8 MiB; the live `text`
   answer is 1.6 MB), stderr goes to a file and only its tail is quoted, and every quoted reason is
   at most 200 printable characters. A slice's rows must also sit between its floor and its
   ceiling (four times its measured count), one rule the build, the smoke probe and the contract
   test share. The reader
   sees an allowlisted environment, starts with `-P`, reads its peak from `/proc` on Linux, and
   stops itself at its own time limit if its parent is gone.

**The cost.** One more process start per config per night (about 0.3 s), and a limit tuned to a
machine: a legitimate file that grows past it fails until the limit is raised.

**Revisit when:** a live file approaches the ceiling, or another source starts parsing a downloaded
file with a native library (it should go through the same reader shape).

## D-166 — A moving, undated API alias never creates a derived model

**Status:** accepted -- **ruled by the owner 2026-09-25** (asked in Turkish whether to stop derivation
for moving aliases or map each to a dated release by hand, the owner chose the first) · **Date:**
2026-09-25 · **Amends** D-157 (the derived registry) · from #37, the residual the M16-W4 re-review
named (`docs/reviews/m16-wave-4-rereview.md` MINOR-1).

**Context.** D-157 registers a model derived from the data when no curated rule names it but a price
and a score agree on a name. For an undated API alias whose meaning moves (`deepseek-chat`, `o1`,
`gpt4o-mini`, `claude-3.5-sonnet`, ...), those two do not describe one model: the score was measured
on whatever release the alias meant on its run date, and the price is what it means today. The
re-review counted thirteen such ids registered on 2026-09-23.

**Decision.**
1. **A declared list of moving aliases** (`registry.MOVING_ALIASES`, each with its reason) is never
   the basis of a derived id: `derive_identity` returns None for it, so its rows stay unmatched and
   are named in the unmatched report (`/health`'s `refresh_unmatched`), not served.
2. **The list only stops derivation.** A curated rule that names such an alias still takes it (the
   list wins, D-157); a vendor's dated name (`deepseek-v3.2`, `o1-2024-12-17`) is unaffected.
3. The list grows by review: an alias a vendor has repointed is added with its reason.

**The cost.** Models reachable only through a moving alias leave the lists until a dated name or a
curated rule brings them back, and a surface that ranked one of them loses it.

**Revisit when:** a source starts dating its aliases, or the list grows past what a review can keep.

**Correction to clause 1 (M17-W3 wave review M6, 2026-09-25).** A listed alias's rows stay unmatched
and are counted among the reconcile's dropped names. `/health`'s `refresh_unmatched` lists only the
twenty names with the most rows, so an alias appears there only when it ranks among them: on the
candidate measured before merge, `deepseek-chat` did and the other eleven did not. Clause 1's "named
in the unmatched report" is true of the drop count, not of that list.

**Clause 3 applied (#40, 2026-09-25).** The list gains two spellings of listed aliases, `command-r+`
and `claude-instant-v1`. It also gains one rule instead of entries: an undated name ending in `-latest`
derives no model, whichever family it names. A date after it (`chatgpt-4o-latest-20250326`) names one
release and still derives. A curated rule still takes a `-latest` name it matches (clause 2). The
`@latest` route decoration is unchanged: it stays decoration, as the M16-W4 grammar ruled.

**Amended by D-173 (2026-10-04)**: clause 8 -- a `-latest` token followed by a word names no release; followed by a date or a version (`v2`) it does (#48).

**Amended by D-189 (2026-10-09)**: a retired id its maker reroutes to a newer model is listed as a moving alias, with its retirement and where it now routes (#164).

## D-167 — The phone holds every board's standings as positions, and combines only what every chosen board ranks

**Status:** accepted -- **ruled by the owner 2026-09-25** (asked in Turkish, with explanations: the
owner chose one payload of every board fetched once a day; combining only the models present on
every chosen board; and W4 as infrastructure with no screen) · **Date:** 2026-09-25 · **Implements**
D-160 clauses 1-2 · from #50.

**Context.** D-160 moves the combined list onto the phone and forbids anything derived from the
question to leave it. A phone that fetched only the boards a question needs would reveal the
question through which boards it asked for. And the phone needs a rule for a model that one chosen
board does not rank: the agent boards rank 30 models, Arena text ranks 190.

**Decision.**
1. **One route, every board, no parameters.** `GET /v1/boards` publishes every board with at least
   one rankable model. For each board: its identity, metric, date and attribution, and its rankable
   models in order with their positions. For each model: its name, vendor, blended price and, where
   known, its accessibility. A query string changes nothing. The phone fetches it whatever the
   question is, keeps it, and fetches again when it is a day old.
2. **Positions, never scores.** No score is on this route. A board's position for a model comes from
   that model's best row on the board. Tied models share a position, so a tie's order carries no
   meaning.
3. **Only what every chosen board ranks.** The combination keeps the models present on every chosen
   board. It re-ranks them on each board among themselves by position, and orders them by the mean
   of those ranks. Ties are broken by model id, never by a display name. Nothing is guessed for a
   missing model. The list is at most as long as the smallest chosen board.
4. **Two named permissions, each for one file.**
   - `StandingsStore.swift` may touch the file system, to keep the payload the engine sent; the
     client-declaration gate names it beside `FrontDoor.swift`.
   - `Combine.swift` may do arithmetic on positions; the arithmetic gate names it beside
     `Uncertainty.swift` (D-138), as D-160 clause 2 provides.

   No other file gains either.

**The cost.** The phone downloads every board every day, about 250 KB (about 60 KB compressed),
measured on the served artifact on 2026-09-25. A list that includes a small board is short. The
phone cannot show how far apart two models are on a board, only their order.

**Revisit when:** the payload outgrows a daily download (D-160's trigger), or the owner wants the
distance between models shown, which would need scores and a new ADR under D-105.

**Amended by the M17-W4 review round (2026-09-25), before merge.**
- **Clause 2 follows D-112, as every surface does.** A board a surface ranks at one effort
  (`ranking_effort`: today DeepSWE at `high`) stands at that effort. Any other board stands on each
  model's best evidence. Every standing carries the effort its evidence was run at, and every board
  carries its `ranking_effort`, so the phone can disclose an unequal comparison as the surfaces do.
  Taking the best row at any effort, as first written, departed from D-112 without the owner's
  ruling (code review B1).
- **The phone keeps what it decoded, not the engine's bytes verbatim.** The standings are encoded
  again, so no field this app does not decode is ever stored (security S2). The store refuses any
  address that is not a file on the device (security S1).
- **The cost, as measured:** about 350 KB raw and 32 KB compressed on 2026-09-25, not the 250 KB
  and 60 KB first estimated (`docs/research/m17-w4-standings-payload-2026-09-25.md`).
- **Measured again after that round (2026-09-25):** the effort on every standing brings the payload
  to about 500 KB raw and 36 KB compressed. Since the second review (R5), the effort policy follows
  the benchmark: every board of a benchmark a surface ranks at one effort stands at it, and two
  surfaces asking two efforts of one benchmark are refused.
- **Clause 3 and the arithmetic permission of clause 4 leave M17-W4 (owner ruling, 2026-09-26).**
  The combination (`Combine.swift`) met the three-attempts stop: three Tester verdicts were BLOCKING
  on the proof of its ordering rule, though the code agreed with an independent implementation on
  every board set tried. It is filed as #61, with its code in the branch history, and returns with a
  property test. Clauses 1, 2 and the file-system half of clause 4 ship in M17-W4. The rule in
  clause 3 stands as ruled.

**Amended by D-173 (2026-10-04)**: `/v1/boards` is built once per artifact and compressed on request (clause 5), and boards no question selects stay published (clause 6).

**Amended by D-181 (2026-10-06)**: clause 4's two named permissions, each for one file, are checked on the compiled module: a served number is any numeric value a decoded type stores, found by the compiler, never listed by hand, and it is followed through the names D-181 lists; gap G-2 holds the rest (added at the M19 closure, the repo review's M10).

**Amended by D-188 (2026-10-08, proposed)**: clause 3 -- a surface's family is combined by mean percentile position, a model kept when half its boards rank it, not only the models every board ranks (D-188 clauses 2 and 3); the D-167 path stays for an engine that names no family.

## D-168 — The question selects its boards as a surface plus declared refinements

**Status:** accepted -- **ruled by the owner 2026-09-28** (asked in Turkish, with explanations, four
questions: board selection, #54, #53 and the screen) · **Date:** 2026-09-28 · **Amends** D-160's
"intent" wording; **applies** D-167 · from #64.

**Context.** D-160 has the on-device model read the question into an intent that selects the boards
the phone combines (D-167). The milestone plan first described a free intent schema: task, domain,
language, input size and constraints. Each value selects boards, and under D-167 clause 3 every
added board can only shorten the list; #54 measured 3 models for three boards. The phone already
routes a question to one of 14 surfaces, under a schema that makes any other answer inexpressible
(D-126, D-147).

**Decision.**
1. **Surface plus refinement.** The question selects a surface as today; its primary board is the
   first board. A refinement adds one Arena slice: the language the task concerns, a domain, or a
   kind of conversation, or for the vision surface a kind of image task. At most two refinements are
   added, in a declared order (language, then domain, then kind).
2. **Declared, not generated.** Every refinement and the surfaces it may refine are a table in the
   Engine layer, each entry with its reason. The on-device model's schema gains one enumerated field
   per refinement kind, each `anyOf` the declared values plus `none`, restricted to those the chosen
   surface allows. `ModelOutputBoundary` drops any value outside the table, as it drops a surface
   outside `/v1/categories`.
3. **The task's language, not the question's.** A language refinement is the language the task is
   about. A question written in Turkish about Python adds no language board.
4. **Without the on-device model,** the similarity and manual tiers select the surface alone: one
   board, today's cards.
5. **Two boards of one benchmark each count** when both are chosen (#53, owner ruling). They are
   two independent measurements, and the detail screen names both.
6. **D-167 clause 3 stays exactly** (#54, owner ruling): only the models every chosen board ranks,
   no threshold. The detail screen states how many models the chosen boards share.
7. **The screen.** More than one board: the main answer is the combined list, a plain order with each
   model's price. One board: today's cards. The combined list's detail screen names each board with
   its date and attribution, the shared count, and that the list is the product's own combination,
   not a published leaderboard (D-160 clause 3). A shown refinement can be removed with one tap, on
   the device.

**The cost.** A question outside the 14 surfaces is not rescued by refinements; it is still
declined or routed to chat as unmeasured. The table is hand-kept, so a slice the engine stops
serving must fail a test rather than vanish.

**Revisit when:** readers ask for combinations the table cannot express, or the router probe shows
refinements chosen wrongly more often than the surface itself.

**A refinement is a language or a domain (owner ruling 2026-09-28, on the probe).** Measured with the
on-device model on a held-out set of 40 questions written independently:
- The task's language was right on 38 of 40 questions; the domain on 36 to 37.
- A "kind" of conversation or image task was right on only 21 to 23. The model added "creative
  writing" to most message-writing requests and "writing about an image" to most image questions.
- Leaving kinds out, all refinements were right on 34 to 35 of 40 questions, and 15 to 16 of the 17
  questions needing none stayed clean.

Clause 1's third kind is withdrawn; English is not a task language either, since the model read it
from the question's own language (`docs/research/m17-w5-refinement-probe-2026-09-28.md`).

**Notes from the wave's code review (2026-09-28).** `docs/reviews/m17-wave-5-review.md`, with three
owner rulings of the same day, asked in Turkish.
1. **`/v1/categories` gains `primary_board`** (review B3). It is additive on a discovery resource,
   as D-138's three fields were: the surface's `primary_source`, a `/v1/boards` id. The benchmark's
   name cannot serve, because two boards publish SWE-bench Verified (#53).
2. **A coding request takes no refinement** (review B2, owner ruling). Ruling A (D-115) answers it on
   two surfaces and presents neither as the winner, and a combined list would replace both.
   `software` refines the chat surfaces and `web-dev` only; a test derives the rule from the route's
   `CODING_INTENT`.
3. **Tied models share a place** (review M1, owner ruling). The order still breaks an equal sum by
   id (D-167 clause 3); the place on screen does not: 1, 1, 3. `Combine.swift` computes it.
4. **The combined list discloses the effort mix and what each date means** (review B1). D-112's
   effort notice names the efforts the listed models stand at on each board that ranks at no one
   effort. A board's date is labelled as its newest evaluation, or as the day the engine read a board
   that publishes none. The cards' staleness warning (D-135) is not carried to it yet. That is latent,
   since every board a refinement can join is recent, and is filed as #72.
5. **Medical and legal questions are answered** (owner ruling). The on-device model's instructions
   no longer list them among what is declined, since the table's `medicine` and `legal` domains
   measure them. The app interprets published measurements and gives no medical or legal advice.
   Re-measured, the change is within the model's run-to-run spread.
6. **Clause 2, corrected** (review M3). The schema offers every declared value of a kind on every
   surface. The restriction to what the chosen surface allows is applied after generation, by
   `ModelOutputBoundary`. A test pins the schema's closed sets.
7. **The figures in the note above, corrected** (review M2). They came from runs whose schema still
   had the kind field. As shipped, on the 40 held-out questions:
   - the language was right on 37, the domain on 34 to 35, and both on 31 to 32;
   - 4 to 6 refinements were added where none was expected;
   - 16 to 18 of the 21 questions needing none stayed clean;
   - the task language was right on 15 of the 17 Turkish questions.

   "As shipped" means languages and domains only, the reworded instructions, and no refinement on
   coding.
8. **A question that is not a model search** is to get a guiding note instead of a ranking (owner
   ruling). Filed as #66, for after this wave.
9. **What leaves the device, stated as the code does it** (security pass S3; owner ruling
   2026-09-28: correct the record, change no code). D-160 clause 1 reads "nothing derived from the
   question leaves the device". Since D-126 the surface the question routes to is sent as `task` of
   `/v1/recommendations`: the same request a reader's own tap on that surface makes. The question's
   text, its refinements and the reader's removals never leave the device.

**Amended by D-188 (2026-10-08, proposed)**: clause 4 -- where the on-device model did not read the question, the answer plan reads its refinements from the words (D-188 clause 6); the routing outcome still carries none. Clause 6 (#54, no threshold) -- a family list keeps a model ranked by half its boards (D-188 clause 2). Clause 7 -- the combined list is the default answer, a family of one board the cards (D-188 clause 5). Clause 1 -- a refinement takes the place of its vote's board and never joins beside it, so of a language and a domain the language stands (D-188 clause 6).

## D-169 — A question that is not a model search gets a guiding note, not a ranking

**Status:** accepted -- **ruled by the owner 2026-09-28** (asked in Turkish, with explanations, seven
questions) · **Date:** 2026-09-28 · **Amends** REQ-ASK-003 and REQ-GAP-001 for this class of input,
and D-126's closed set and `RoutingOutcome` · from #66.

**Context.** The on-device model now reads every question behind the text box (D-126, D-168). Some
input is not a search for a model at all:
- an attempt to instruct the model;
- a knowledge question;
- chit-chat or nonsense;
- a request that the app do the task itself.

Today such input is routed to a surface, often `assistant`, and the reader gets a ranking that
answers a question nobody asked. REQ-ASK-003 answers an UNMEASURED need with the chat ranking and a
sentence saying what it cannot tell. That rule is right for a real need this product does not
measure, such as editing a photo; it is not right for input that states no need. The schema already
makes free text inexpressible (D-126), so this ADR is about what the screen shows, not about text the
model could emit.

**Decision.**
1. **Four classes get the note:** attempts to instruct the model, knowledge questions, chit-chat or
   nonsense, and requests that the app do the task itself. A task described as a need, even one with
   its content pasted in, is still a model search.
2. **A second closed value.** The surface field's closed set gains
   `ModelOutputBoundary.notASearchSentinel` beside the decline sentinel. Only `ModelOutputBoundary`
   maps it, to an outcome with `notASearch == true`:
   - `categoryID` is the unmeasured fallback;
   - `unmeasured` is true;
   - it carries no refinement and no alternative.
3. **Only the on-device model decides.** Without Apple Intelligence the wording tier behaves as
   before: its similarity scores for nonsense and for correct routes overlap
   (`docs/reviews/m16-router-floor-measurement.md`), so no threshold separates them.
4. **The screen shows the note and "Change" only.** There is no ranking, and the previous question's
   ranking goes too. The note is example-based guidance in the app's register: "this does not look
   like a model search; say what you will use the model for", with one example. No request is
   sent.
5. **Not recorded** in the on-device register of asked-but-unmeasured questions (REQ-GAP-001). These
   inputs are not unmet model needs, and an injection attempt's text is not kept.
6. **Accepted when measured.** On the on-device model, twice, on a set written independently of the
   instructions (D-147 clause 5):
   - at most 2 genuine model searches per run get the note;
   - at least 80 % of not-a-search inputs get it.

   Three failed attempts stop the work, and it goes back to the owner.

**The alternative not taken.** A separate "request kind" field beside the surface. It lets the model
answer a surface and "not a search" at once, a contradiction something would have to resolve. One
exclusive value in one field cannot contradict itself, as the decline sentinel already showed.

**The cost.** On a device without Apple Intelligence, off-topic input still gets a ranking with its
notice. A genuine search the model misreads gets no ranking at all; "Change" is always on screen to
correct it.

**Revisit when:** a probe shows false positives above the bound, or devices without Apple
Intelligence become the common case.

**AMENDED 2026-10-04 (M18-W3, decided by the agent on the owner's standing instruction of 2026-09-29,
within the milestone plan's §2 W3).** Measured in M17, the on-device model alone could not hold the
line (five variants; `docs/research/issue-66-not-a-model-search-probe-2026-09-28.md` on the issue-66
branch). M18 holds it as follows; the measure is `docs/research/m18-w3-question-reading-probe-2026-10-04.md`.
- **Clause 2 becomes a separate field.** It is a closed yes/no field, generated after the surface (the
  issue branch's variant 3; generated first, it moved questions about documents to other surfaces).
  "The alternative not taken" no longer holds: the contradiction it warned of is resolved in code, by
  the decision below.
- **Clause 3 is amended.** Signals decided in code apply on every tier, the model or not:
  - *no word* (keyboard runs, repeated letters, long runs with no vowel; an acronym is a word);
  - *small talk*: greetings, thanks and the like, and nothing else;
  - *pasted content*: three lines, a code block, or a verb of acting before a colon;
  - *an instruction to the app*: phrases specific enough that a search about instructions or roles
    does not use them.

  Each list is matched on whole words, under both the default and the Turkish case folding. A
  Turkish verb counts only in the forms a request takes, and an English order only where it opens
  its sentence: "which model won't ignore my instructions" orders nothing (the third code review,
  M17).
- **Clause 4 gains a third outcome.** The decision is:
  - *no word* or *small talk* → the note, alone: nothing in them can be routed;
  - pasted content or an instruction to the app, together with the model's "not a search" → the note;
  - any one of those three alone → a one-tap question back, "Did you mean to find a model for this?",
    which sends nothing until the reader taps "find a model" (the ranking, as routed) or "no" (the
    note). While it waits, no surface is shown.
- **#113, in the same place.** A request to make or change an image that a tier routed to `vision`,
  which measures reading an image, is routed as unmeasured instead. A question routed to any other
  surface is left alone: a question about code or a website that mentions an image is not overridden
  (the wave's second code review, B4).
- **Clause 6, restated for the question back.** On a held-out set, twice: at most 2 genuine searches
  get the note unasked, at most 4 are asked, and at least 80 % of the not-a-search inputs get the note
  or the question. Clause 6's "three failed attempts stop the work, and it goes back to the owner"
  stands: where a bar is missed, the wave's pull request asks the owner one plain question, whether to
  ship what holds.
- **The first held-out measure was spoiled** (the wave's code review, B2): the author had read part of
  the not-a-search held-out set, and its phrases reached the signals. That set and the first image set
  are tuning sets now, and fresh sets written by a new independent seat are the measure.
- **Measured** (`docs/research/m18-w3-question-reading-probe-2026-10-04.md` §5, at `da48707`, twice):
  - #66: no genuine search given the note, and one and two of 40 asked: the false-positive bound
    holds. 21 and 20 of 40 not-a-search inputs caught, against 32: the catch bar is missed; knowledge
    questions are the gap (1 of 10).
  - #113 misses both bars. Requests to make an image: 10 and 10 of 15 told "not measured" (from 0),
    against 11. Requests to read one reaching `vision`: 8 and 8 of 10, as at the baseline, against 9;
    3 and 2 of them only after the question back.
  - The question back costs genuine searches: 5 and 10 times in 145 across the three held-out sets,
    every time on the model's "something else" alone, most of them questions about reading an image.
  - The code that ships, after the second and third code reviews narrowed the rules, run on the spent
    sets, informational only (§6): 7 of 15 requests to make an image told "not measured", and 3 ranked
    on `web-dev` as if measured; #66 unchanged (21 and 20 caught, 1 and 2 genuine searches asked);
    coding 33 and 32 of 40. The question back reached genuine searches 8 and 10 times in 145.

**Amended by D-184 (2026-10-07)**: a question of fact is a doubt in code beside pasted content and an order to the app; the #113 image rule stays on `vision`, reading more Turkish forms (its reach beyond `vision` came out of M19-W4, #191).

**Amended by D-187 (2026-10-08)**: an understood question is answered from the closest board, never "not measured"; the note and the question back stay for input that is not a search.

**Amended by D-203 (2026-10-16)**: clause 3 -- the wording tier also holds small talk, text with no meaning and a dictated answer, measured on a fresh held-out set (#66).

**Amended by D-213 (2026-10-19)**: the closed verdict field's two values become `model search` and five named non-search kinds, each read as the model's "not a search"; the reading rules stand.

## D-170 — The engine runs as a launchd service, from a deployed release of `main`

**Status:** accepted -- **ruled by the owner on the review of #32** (2026-09-25), recorded as an ADR
at the M17 closure (milestone review M6) · **Date:** 2026-09-29 · **Amends** D-154 clause 2 · from #32.

*Numbering.* D-169 is held by #66 on the unmerged branch `enhancement/issue-66-not-a-model-search`
(a question that is not a model search; moved to M18 by the owner), so this decision takes D-170.

**Context.** The engine refreshes itself nightly (D-151, D-154), which needs it running. It was
started by hand with `ios/app.sh`, and the M16 refresher ran whatever branch was checked out on the
Desktop (M16 closure, retired under #16).

**Decision.**
1. **A launchd job keeps the engine up** (`com.ilgar.modelranking.engine`, `KeepAlive`), bound to
   127.0.0.1:8080, with `APP_ENV=test` and the strict startup preflight.
2. **It runs a DEPLOYED copy of `origin/main`,** never the development checkout:
   `~/Library/Application Support/model-ranking/engine/releases/<sha>`, exported with `git archive`,
   with its own venv, and `current` pointing at the live one. The served artifact and its refresh
   record live in `engine/data/` and survive every redeploy. Nothing launchd touches is under
   `~/Desktop`.
3. **The owner deploys.** `scripts/install_engine_service.sh` deploys and restarts, and is rerun after
   each merge; `scripts/remove_engine_service.sh` takes the service off. It changes the owner's
   machine, so it is his to run (AGENTS.md §5), or the agent's on his standing instruction
   (2026-09-29: "proceed with what you recommend").

**The cost.** A merge is not live until the installer runs again, so a merged change can wait for it.
The installer installs from PyPI without a lock (#35).

**Revisit when:** the engine is deployed anywhere but the owner's Mac (D-154's revisit), or the
installer's safety properties need more than the substring tests the M17 closure security seat found
(MINOR-4).

**Amended by D-171 (2026-09-29)**: clause 1's bind is loopback by default and the home network by opt-in, with every Host checked. **Amended by D-177 (2026-10-04)**: a release's venv takes `requirements/ingest.lock` and `requirements/build.lock`, hash-checked, so the cost's "without a lock (#35)" no longer holds.


## D-171 — The engine can serve the owner's phone on his home network, by opt-in, checking every Host

**Status:** accepted -- the owner asked on 2026-09-29 to see the app ("I want to see it, it's been two
weeks", translated from Turkish) and to proceed on the agent's recommendations; M18-W1 · **Date:**
2026-09-29 · **Amends** D-170 · from #87, #86.

**Context.** The engine service (D-170) binds 127.0.0.1, so only the Mac and its simulator reach it.
The owner's phone is on the same home network. A hosted engine needs the data licences ruled (#88) and
the Stage 5.1 review first.

**Decision.**
1. **The engine checks the Host.** With `MODEL_RANKING_ALLOWED_HOSTS` set (a comma list), a request
   whose Host, port stripped, is not on it gets 400. The service always sets it, loopback included, so
   a page the owner's browser loads cannot rebind a name to the engine (closure security seat INFO
   I-4). Unset, as in tests and by-hand development, every Host is served.
2. **Loopback by default, fail closed.** `MODEL_RANKING_BIND` feeds uvicorn's one `--host`, and defaults
   to 127.0.0.1. A bind that is not loopback with no allowed Hosts refuses to start.
3. **The home network by opt-in only.** `scripts/install_engine_service.sh --lan` binds 0.0.0.0 and
   allows `127.0.0.1`, `localhost`, the Mac's `<LocalHostName>.local` and its LAN address. Without
   `--lan` nothing changes but the Host check.
4. **The app's engine address is per build** (`ENGINE_URL` → the Info plist's `EngineURL`), with
   loopback the fallback. The app declares local networking. The requests are the same parameterless
   ones (D-126; D-160 as amended by D-168 note 9).

**The cost.** On the home network, anyone who can reach the Mac can read what the engine serves:
public benchmark data, read-only GETs, no account. A device on that network can also send an allowed
Host by hand. The Host check stops a browser page, not a person on the network. The Mac's firewall and
the opt-in are the controls.

**Revisit when:** the app leaves the home network (a hosted engine, Stage 5), or the engine serves
anything that is not public.

**Notes from the wave's code review (2026-09-29).** `docs/reviews/m18-wave-1-review.md` found the
decision describing a smaller exposure than the code made; these notes correct it.
1. **Clause 2 is held where the bind is known (B1).** The variable was checked, not the bind, so
   `make run` and a hand-typed `uvicorn --host 0.0.0.0` served every Host on every interface. Now,
   with no list, the engine refuses any request that arrived on a network address rather than
   loopback, whatever started it; and `make run` binds 127.0.0.1. The startup refusal stays for the
   service.
2. **Every network, not only the home one (M1).** `--lan` binds every interface, on every network
   the MacBook joins, and the Mac announces its `.local` name on each, until the installer runs with
   `--no-lan`. A reinstall keeps the mode it finds and says so (M2), so a routine redeploy after a
   merge does not close it by accident, nor open it.
3. **The Mac's firewall is off** (measured 2026-09-29), so it is not a control today; the opt-in is.
   The owner's page says how to close the engine or turn the firewall on.
4. **The phone's requests cross Wi-Fi in cleartext.** `/v1/recommendations` carries `task` (the
   surface the question routed to, D-168 note 9) and `budget`; clause 4's "parameterless" was wrong.
   Anyone who can see the network's traffic can read them. The question's text still never leaves
   the phone.
5. **The engine address is baked into the build,** an exception to AGENTS.md §5 ("runtime config
   never build-baked"): a phone app has no process environment. `ios/app.sh` pins its own simulator
   build to loopback, and the client's "not answering" message names the address it tried (M4).
6. **The `.local` name can change** (R1): macOS renames a Mac on a Bonjour conflict. The page says to
   check the name if the phone stops reaching the engine.

REQ-DEV-001 (`docs/prd.md`) states the criterion this ADR serves.

**Notes from the wave's second code review (2026-10-01).** They supersede the cost's last sentence
and note 3's pointer to the firewall.
7. **The firewall is not a control for this.** The macOS application firewall allows or blocks an
   application, not a device or a network: allowing Python lets every device on every network in, and
   blocking it shuts the phone out too. While `--lan` is on, the one control is `--no-lan`.
8. **The address is on the screen** (note 5 said so before it was true). Under a failure to reach the
   engine (unreachable, timed out, or no connection, which is how a refused local-network permission
   can read), the failure view shows the address the app asked (`EngineError.addressNote`).
9. **What forwards to loopback is not loopback** (R3). The no-list rule reads the socket's local
   address, so a reverse proxy, `ssh -L` or a tunnel in front of an engine with no list exposes it with
   every Host served. A hosted engine sets its list whatever its bind (#94).

**Note from the wave's third code review (2026-10-01).** It completes note 6.
10. **A renamed Mac needs the installer again**, not only a new address in the app: the engine's list
    holds the name it was installed with, and refuses the new one (`unknown_host`, whose address the
    failure screen now shows).


## D-172 — The security review runs once per milestone, at its closure; a wave closes on its Code-Reviewer and Tester

**Status:** accepted -- the owner's ruling of 2026-09-29: "a security review at the end of the
milestone is enough now; at a wave's close, testing is enough" (owner, translated from Turkish) ·
**Date:** 2026-09-29 ·
**Amends** D-161 (its v6.6 note on review depth) and `docs/plans/m18-plan.md` · from #84.

**Context.** Three texts disagreed on when a wave gets a security pass (#84): `AGENTS.md` §4 said
both "never per wave" and "a HIGH wave also gets a security pass on its slice", and D-161's note
retired the per-milestone seat that M17 then ran anyway. M17's two HIGH-wave passes found MINORs
only, after the wave's Code-Reviewer and Tester had run; the milestone's closure seat found the
cross-wave findings (MINOR-1 to MINOR-5).

**Decision.**
1. **No security pass per wave**, at any risk tier. `/close-wave` step 5 and checklist row 4 are
   N/A in this project, citing this ADR. The risk tier still sets the Tester's fault injection.
2. **A wave closes on its Code-Reviewer, then its Tester**, two separate independent subagents, as
   D-161 has it.
3. **One security seat per milestone, at its closure**: a fresh-eyes subagent from
   `.claude/agents/Security-Reviewer.md` on the milestone's whole diff, before the closure pull
   request opens. Each finding is fixed there, red first, or filed.
4. **The Stage 5.1 release review is unchanged**: once, before anything deploys beyond the owner's
   Mac.

**The cost.** A security defect in a wave's slice can sit on `main` until the milestone closes. It
reaches only the owner's Mac meanwhile, since nothing deploys elsewhere (D-170), with one exception:
M18-W1's `--lan`, which the owner turns on. W1 had no pass on its slice; its Code-Reviewer read the
network surface (B1, M1) and the closure seat reads it again.

**Revisit when:** a wave's defect that a slice pass would have caught reaches the owner, or anything
deploys beyond the owner's Mac.

**Amended by D-199 (2026-10-15)**: in heavy mode the Tester runs once per milestone, on the plan's last wave, not per wave; the security seat stays at each milestone's closure, and also runs where `make review-need` flags a change.

## D-173 — The engine's backlog decisions: stable ties, guards by id, an accessibility loss guard, bounds at refresh, a compressed boards route

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M18-W4 · **Date:**
2026-10-04 · **Amends** D-128, D-132, D-154, D-166 and D-167 as below · from #44, #48, #39, #42, #57, #55, #77, #76.

**Context.** M17's seats filed these as needing a decision. Each has a small, reversible answer, and the
owner asked the agent to take its recommendation rather than ask.

**Decision.**
1. **Ties are ordered by model id** (#44). A ranking's tie-break was the display name, a served
   spelling, so a re-spelled name moved a model inside a tie. The value and cheapest picks broke a
   price tie the same way; they now take the first row in the ranking's order (score, then id). The
   served order of tied rows changes when the engine runs this code. The refresh fingerprints the live
   artifact and the candidate with the same code, so no night publishes for this change alone.
2. **The night-to-night roster guards compare model ids** (#39; D-128, D-132). A display change is
   recorded in the refresh record as information. It is never read as one model lost and another
   gained. An attacker-controlled display name therefore moves no guard, which it could not do before
   either without also changing the id. This covers each surface's ranked roster. The board guards
   (D-159, D-164) still compare a board's raw names, the rows as they arrive, before any model id: an
   upstream re-spelling of a board's names still reads as names lost and gained there (#100).
3. **Accessibility has a loss guard** (#42). A night on which the number of models with an
   accessibility value falls by a quarter or more against the served artifact is refused, and the
   refusal's reason names both counts. The quarter is D-128's own.
4. **The refresh checks the serving bounds on the candidate** (#57). The startup check's bounds
   (`_egress_problems`) run on the candidate before it is published. A candidate past one is refused,
   and the live artifact keeps serving.
5. **`/v1/boards` is built once per artifact and compressed** (#55).
   - It is memoised on the artifact's identity.
   - Every route's response of 1 KB or more is gzip-compressed for a client that accepts it, with
     every security header kept. The data is public.
   - No ETag for now.
6. **Boards no question can select stay published** (#77; D-167). The phone picks boards by id from
   its own table, so a new refinement needs no engine release. With (5), the daily payload costs
   about a tenth of what it did. A board stops being published when its source does, not when no
   question selects it.
7. **The retired refresher's installer is removed** (#76). The engine service runs the nightly refresh
   (D-170, D-154). A second launchd refresher running a development checkout is no longer
   installable. D-154 clause 4's `scripts/retire_refresh.sh` goes with it: no such job is installed on
   the owner's Mac (measured 2026-10-04).
8. **A `-latest` token names no one release unless a date or a version follows it** (#48; amends D-166
   clause 3). `grok-4.20-beta-latest-reasoning` derives nothing, as `...-latest` alone did not;
   `chatgpt-4o-latest-20250326` and `gpt-4o-latest-v2` derive. The version form is `v` and a digit,
   so a word that starts with `v` (`-latest-vibe`) still derives nothing.

**Mitigation if violated.**
- If tie order follows a spelling again, positions move on nights when nothing was measured.
- If the roster guards compare names again, a cosmetic re-spelling can refuse a night (the board
  guards still can, #100).
- Without the accessibility guard, a truncated file empties the phone's filter with no refusal.
- Without the bounds at refresh, a refresh can publish what a restart would refuse.

**Revisit when:**
- the phone shows ties as shared places on the cards (the alternative to (1)); or
- the payload matters again (an ETag); or
- a board is carried that no source still publishes.

**Amended by D-179 (2026-10-06)**: clause 2's board half -- the board guards compare model ids too, and
a re-spelled board row is recorded with the night's `renamed` (#100).


## D-174 — Review seats run one after another, each in its own worktree

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29; M18-W5
· **Date:** 2026-10-04 · from #52 · **Amends** nothing; the DevFlow skills it touches stay DevFlow's.

**Context.** At M17-W4 the Code-Reviewer and the Security-Reviewer ran at once in one worktree, and each
saw the other's in-place mutants (#52). At M18-W1 a seat's probe ran the engine installer for real and
replaced the owner's launchd service with a scratch copy.

**Decision.**
1. A wave's seats run one after another, never at once on one tree.
2. Each seat works in its own `git worktree`, detached at the commit under review, with its own venv
   and its own copy of the artifact.
3. A seat runs behind command stubs that refuse `launchctl`, `simctl` and `xcodebuild`, and is told
   in writing never to run the engine installer or remover by hand.

**Mitigation if violated.** A verdict skewed by a mutant it did not make, or a review probe that changes
the owner's machine.

**Revisit when:** DevFlow's `/close-wave` says this itself (the finding is handed back on #52).

**AMENDED 2026-10-04 (M18-W7, #120; decided by the agent on the owner's standing instruction of
2026-09-29).** Clause 2's "its own copy of the artifact" is a copy of the artifact the engine
service serves (the deployed release's `advisor.db`), made when the seat is set up. The M18-W3 third
review seat found why it must say so: with no copy the suite stops at W-108, and with the older copy
in the owner's checkout (2026-09-24, before the refinement boards) one test fails that the wave did
not cause. Clause 2's own venv is built by `make install`, from the locks (D-177).

**AMENDED 2026-10-05 (M18 closure, the repo review's M10; decided by the agent on the owner's
standing instruction of 2026-09-29).** Clause 3 refuses `simctl` and `xcodebuild` to every seat, and
D-175 clause 2 asks a wave that changes a screen to cite a `make ui-test` run, which needs both. So
a screen wave's Tester may run `make ui-test`, and through it the simulator and `xcodebuild`, against
the engine that target starts on 127.0.0.1:8090 from a copy of the served artifact. Nothing else
leaves the stubs: never the engine installer or remover, never `launchctl`. The owner lifted the
simulator restriction on 2026-10-04. M18-W2's Tester and M18-W3's first Tester ran `make ui-test`
before this was written; `docs/control-events.csv` records both.


## D-175 — The screen is tested by a committed UI target, run locally, with scripted routing

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29; M18-W2
· **Date:** 2026-10-04 · from #69, #63.

**Context.** No committed test drives the iOS screen (#69). M17-W5 found two defects only by driving
the simulator through a scratch XCUITest target: a chip that could not be restored, and a row that
took no tap. M17's UI review of `cce2ced` (#63) was made the same way and never committed. The owner
lifted the simulator restriction on 2026-10-04.

**Decision.**
1. **A UI test target, `ModelRankingUITests` (`ios/UITests/`),** drives the screen's paths in the
   simulator. Its bundle id lives in `ios/Config/UITests.xcconfig`; the project carries none.
2. **It runs locally, through `make ui-test`.**
   - It starts an engine on 127.0.0.1:8090, from a copy of the served artifact.
   - It builds the app for that address (`ENGINE_URL` on the command line), runs the target on the
     iPhone 17 Pro simulator, and stops the engine.
   - It is not part of `check-fast`, `gate` or CI, which have no simulator, no artifact, or both.
   - A wave that changes a screen cites a `make ui-test` run in its close record.
3. **Routing in a UI test is scripted.**
   - A Debug-only launch argument (`-UITestRouting`) replaces the on-device model tier with a fixed
     table: question text to the model's answer (surface, language, domain).
   - That answer goes through `ModelOutputBoundary` exactly as the model's does, so a UI test cannot
     reach a choice the boundary refuses.
   - Release builds compile no such hook, and a test holds that.
   - The real model's reading is measured by the router probe, not by UI tests.
4. **Screenshots are evidence, not baselines.** The target saves what it sees for the record (#63). It
   asserts on the accessibility tree, never on pixels.

**Mitigation if violated.**
- A screen change ships unseen: the M17-W5 defects found only by hand.
- Or a UI suite that fails on the model's mood, and is then ignored.

**Revisit when:** CI gains a macOS runner with a simulator, or a second screen needs the same harness.

**Clause 3, as built (M18-W2 P1).** The scripted router (`ScriptedModelRouter`) is in the Engine,
which is never compiled on `DEBUG` (`test_ios_platform_drift`), and reads nothing itself. The one
launch-argument read is `LaunchRouting.swift`, in Debug only; `make client-decls` refuses a Release
build that reads its launch arguments or its launch environment (review M5). One launch argument
does reach a Release build, by design: `-language`, through `@AppStorage("language")`, the one
`UserDefaults` value the text gate allows. It chooses the language and nothing else.

**Decisions on #63's findings (clause 4, M18-W2 P3).** Reproduced on 2026-10-04; the list is in
#63's thread.
- **1, one model as three cards:** one card per model, carrying every label it earned. The
  value-window reason is not said on a card that is the best; a floor warning is never merged away.
- **2, English in Turkish mode:** D-176.
- **3, no sign the question was understood:** gone before this wave (the echo line, M17-W5).
- **4, length and repeated titles:** the bar title and the first surface's heading are gone. The
  cards stay as tall as they are; merging (1) and the ten-row combined list (A) are the length work
  of this wave.
- **5, "SORUN":** "SORU".
- **6, formats:** the page count is grouped per language and dates are said in words. Scores and
  prices keep one decimal form in both languages, as `Scores.swift` and `Language.swift` record:
  one served number reads the same to two readers.
- **7, register:** "sen" throughout.
- **8, wording:** fixed as listed in the P3 commits; the price blend is stated (75/25), held equal
  to the engine's weights by a test.
- **9, rank ranges:** one sentence under the cards that show a range; tied places on the combined
  list say what a shared place means.
- **10, raw model names:** the engine's data, filed as #112.
- **11, the send button:** disabled reads as disabled in both appearances.
- **12, the largest text:** the headline shrinks to fit and stops growing at the first
  accessibility size, so the question field is on the first screen; "Change" goes under its line.
- **13, surface names:** each has a line saying what it is for in the chooser.
- **14, the gap register:** it says what it is for, and its button carries a visible label.
- **A, the combined list's length:** ten rows, and the rest on request.
- **#72's other half, a stale phone copy** (review M3): standings kept on the phone past their day,
  because a newer copy could not be fetched, are said on the combined list as loudly as a stale
  board.
- **B, a drawing request ranked as image reading:** question reading, filed as #113 for W3.

**Decision on #78 (clause 4, M18-W2 P6).** The served accessibility becomes a reader filter on the
combined list: "Only models with an API or open weights". It is served on `/v1/boards` only, so the
cards (from `/v1/recommendations`) carry no filter. A model with no published access, or a value this
build does not know, is not claimed. The filter hides rows and never re-ranks: every row keeps its
place among all the shared models, and the screen says how many it shows of how many. D-173 clause
3's loss guard keeps protecting the values the filter reads.

## D-176 — The notices are composed by the app from facts; the close call gains its fact

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29; M18-W2
· **Date:** 2026-10-04 · **Amends** D-136 (its recorded English remainder; the field added by #253) · from #63 (finding 2). **Moves the `/v1` answer payload, additively.**

**Context.** D-136 had the app compose the two sentences under a pick from `/v1`'s facts, and left the
notices in the engine's English as a recorded remainder. M18-W2 reproduced #63 on the Turkish screen:
the coding answer shows five English sentences (stale evidence, effort mix, close call, undated
evidence, the ordering note) and the "N models ranked on X" line, and the stale one names internal
source ids (`epoch_swe_bench_verified`, `swebench`).

**Decision.**
1. **The app composes every notice, in both languages, in `Notices.swift`.** It uses served facts
   only: `source_health`'s rows, the `evidence_dating` kind, the picks' efforts, the answer's ranking,
   and `close_call_fact` (clause 2). The engine still decides WHETHER a notice is said; the app
   decides how. D-135's classification and deduplication are unchanged.
2. **`close_call_fact` is added to each answer:** `{"model", "behind_by", "unit"}`, the values the
   `close_call` sentence quotes. It is present exactly when `close_call` is. The English sentence
   stays.
3. **The ordering note carries no values.** The app keeps a copy of the engine's English sentence, a
   test holds the copy equal to `ORDERING_NOTE`, and the Turkish is its translation.
4. **The fallback is D-136's.** A missing fact, an unknown kind, or a close-call model that the
   answer's own ranking does not list shows the engine's English. Nothing is dropped.
5. **Source ids are not said.** The stale notice says how old the evidence is and how many sources
   are old, not what the engine calls its feeds.
6. **On an anchored Elo surface, the close call's gap is said out of 100,** the rule
   `leaderSentence` follows (D-143, review M-2).
7. **An empty answer and an empty source list carry their reason as a code** (added after the
   wave's code review, M2). The engine has three reasons for an empty answer: nothing reached the
   ranking, nothing fit the budget, or the evidence could not be read. Composed without a code, the
   third was said as the first, a false cause in two languages. So each answer gains
   `unavailable_reason_code` (`no_evidence`, `over_budget`, `unreadable`), and `source_health` gains
   `reason` (`no_source`, `unreadable`, or null). Both are additive; the English sentences stay.

**The rejected alternative.** `?lang=tr` on the engine. D-136 refused it for the sentences under a
pick; the same reasons hold here.

**Mitigation if violated.** A Turkish reader meets English warnings: the loudest sentences on the
screen are the ones they cannot read.

**Revisit when:** a third language is added, or the engine adds a notice. A new notice needs its
fact, as clause 2 did.


## D-177 — Every install reads a hash-checked lock, and pyarrow is the refresh's extra

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29; M18-W6
· **Date:** 2026-10-04 · from #35, #26 · **Amends** D-116 (how the serving image is built) and
D-170 clause 1 (how a release's venv is built).

**Context.** `pyproject.toml` gave lower bounds only, so every fresh install took the newest versions
that day. A release venv built on 2026-09-25 differed from the tested one in 11 packages (#35; the
M17 closure seat's I-6). The serving image installed pyarrow (126 MB), which only the refresh needs
and the serving image never runs (#26; D-116, D-154).

**Decision.**
1. **Four locks under `requirements/`,** resolved by `make lock` (`scripts/lock_dependencies.py`,
   uv, universal, Python 3.11 up), each with every hash:
   - `serve.lock`: the serving image;
   - `ingest.lock`: the engine's release on the owner's Mac, which serves and refreshes;
   - `dev.lock`: a working tree and the suite;
   - `build.lock`: the build backend, which `[build-system]` now declares.
2. **Every install takes its lock and the build lock with `--require-hashes`,** then the project with
   `--no-deps --no-build-isolation`. That covers `make install`, the release's venv
   (`scripts/install_engine_service.sh`) and the `Dockerfile`. Nothing is resolved or fetched beyond
   the locks.
3. **pyarrow is the `ingest` extra.** It is also in `dev`, so the suite can read parquet. The
   serving lock carries none.
4. **A lock is current or the suite fails.** Each lock records the hash of the `pyproject.toml`
   tables it was resolved from, and `tests/unit/test_dependency_locks.py` compares them offline. The
   same file holds clause 2 for every way of spelling `pip install`.
5. **CI's install lines are the owner's** (`.github/workflows/**`). The change is proposed as a
   patch in the wave's pull request, and CI keeps resolving fresh until it is applied. The
   `Dockerfile` is a K.10 surface (`AGENTS.md` §6): its change is named in the pull request for the
   owner's review.

**The rejected alternative.** Pinning exact versions in `pyproject.toml`. It pins only the direct
dependencies, checks no hash, and makes every library upgrade an edit to the project file.

**Mitigation if violated.** A deploy runs versions no test has seen, or the serving image ships the
refresh's code.

**Revisit when:** a dependency must be upgraded for a security advisory (run `make lock`, then the
suite), or CI's Pythons cannot install a pinned version (the risk the W6 review's R1 names).

**Amended at the M18 closure (2026-10-05, the closure security seat's S5 and S1):** `make install` makes its venv without `--upgrade-deps`, so the first pip to run is the Python's own, and it installs the locked pip; `make deps` audits the four locks, not `.`. Clause 2's "nothing is fetched beyond the locks" does not yet hold for the serving image, whose Python base is taken by tag (#141, the owner's file under K.10).

**Amended at #125 (2026-10-05):** the `dev` extra takes `httpx2`, the client starlette's test client runs on; on httpx it warned that a later starlette may drop that path. A `make lock` to the newest versions on 2026-10-05 changed only `dev.lock` (httpx2, httpcore2, truststore, httpx2-jsfetch for WebAssembly only, and `filelock` 4.0.10 to 4.0.11), and the suite stayed green.


## D-178 — A bug whose fix the owner merged is closed, marked unverified

**Status:** accepted -- the owner's instruction of 2026-10-04: "mr merged there is 53 issue if their
pr's are merged please close them" (owner) · **Date:** 2026-10-05, recorded at the M18 closure
(the repo review's M16) · **Amends** `.agents/rules/issues.md`'s verification pipeline for this
project.

**Context.** `.agents/rules/issues.md` keeps a bug open after its fix merges, with `dev:done`, until a
verifier sets `qa:passed` on a deployed build. This project has one verifier, the owner, and its only
deploy is the owner's Mac. On 2026-10-04 the owner asked for every bug whose fix PR was merged to be
closed, and thirteen were (for example #67 and #86). The rule was then only in issue comments, and
`issues.md` still said the opposite.

**Decision.**
1. When a bug's fix PR is merged, the agent closes the bug with `dev:done` and one comment: the fix
   is merged in #N and has not been verified on a deployed build; reopen it if the problem is still
   seen.
2. Only a bug the merged PR fixes in full is closed. A bug a PR addresses in part, or one whose
   measured bar was missed, stays open with what is left.
3. The rest of the pipeline stands. A bug's PR still carries no closing keyword, so the merge does not
   close it by itself. `qa:passed`, `qa:failed` and `qa:blocked` stay the verifier's, and a failed
   verification reopens the bug with `qa:failed`.

**The rejected alternative.** Keeping each bug open for `qa:passed`. With one verifier and no
deployed build beyond the owner's Mac, the open list filled with fixed bugs, and the owner asked for
them to be closed.

**Mitigation if violated.** A closed bug is taken as verified. The comment says it is not, and
`dev:done` stays on it.

**Revisit when:** someone other than the owner verifies, or the engine is deployed beyond the owner's
Mac.

## D-179 — The board guards compare a row by the model it links to

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W1 · **Date:**
2026-10-06 · **Amends** D-156 clause 3 (named by #253), D-159, D-164 and D-173 clause 2 · from #100.

**Context.** D-173 clause 2 moved the roster guards to model ids (#39). The board guards (D-159 on a
surface's own board, D-164 on every declared board) still compared raw names. The M18-W4 reviewer
re-spelled 77 of the 173 names on `coding`'s board, keeping every model, and the night was refused.
D-159 had measured the same on a real upstream: ECI's `_` to `-`, 284 of 521 names. A refusal on a
re-spelling is published by hand, and a guard that is waved through on ordinary nights is waved
through on the night it matters.

**Decision.**
1. A board row the reconcile linked to a model is compared by that model. A row linked to none is
   compared by its raw name, as before. A row's harness and effort are not part of it: a relabel on
   rows the board already had is a provenance update, and publishes
   (`test_refresh.py::test_a_freshness_or_provenance_update_is_published`).
2. The comparison counts rows, not models: a model's second row on a board is a row of its own. The
   floor counts every row (D-159), so a board flooded with new spellings of models it already had
   still reads as new rows.
3. A re-spelling is recorded with the night's `renamed`, as `old -> new on <board>`, once for each
   pair of spellings, with the number of boards it was seen on. It is never a reason to refuse.
4. The limits stay: a quarter lost refuses (D-128), and more than a quarter new refuses (D-132).

**What an upstream's names can move now.**
- A name re-spelled to another name that reconciles to the same model moves no guard. What a reader
  is served does not change: `/v1/boards` carries model ids and positions, never raw names.
- A name re-spelled to one that reconciles to another model, or to none, still counts as a row lost
  and a row new.
- A row that keeps its name and moves to another model now counts, where before it moved no board
  guard: what the board serves changed. A registry change does this, so a large one is read with
  the owner on its first night.
- So does a row that keeps its name and gains or loses its link (the M19-W1 review's M1): a standing
  appears on the board or leaves it. D-157 links a derived model only while it has a price and a
  score, so a price feed that adds or drops a quarter of a board's linked models in one night is
  refused, and the refusal names the board and its counts. Before, no board guard saw it; the
  surface's roster guard (D-173 clause 2) sees the models it ranks.
- On the night a source expires (D-156 clause 3), the baseline unlinks each derived model the
  expired rows leave without a price or a score, as a build without the source does, and the board
  guards read the baseline's rows. A row the expiry unlinked is then neither lost nor new, and the
  accessibility guard no longer reads its value as lost (the M19-W1 Tester's M5 and K1). Measured on
  the served artifact: a `litellm` or an `openrouter` expiry publishes; a `litellm` expiry was
  refused before, on a board and on accessibility.

**Measured.** The first night with M19-W1's code, simulated on a copy of the served artifact
(release-3f2e91d) on 2026-10-06, publishes. The board nearest a limit is `epoch_frontiermath`: 16% of
its rows (18 of 114) changed model, against the limit of 25%. That night carries a day of upstream
change and M18's and this wave's registry changes at once (#129's joins, GPT-5's dated rows among
them), with every link gained or lost in between. How often links move on ordinary nights is not yet
measured; a refusal for it names the board and its counts.

**The rejected alternative.** Comparing a row by its model, harness and effort. A harness relabel on
rows a board already had, which the refresh must publish, then read as every row lost and new.

**Mitigation if violated.**
- If board rows are compared by name again, a cosmetic re-spelling refuses a night.
- If they are compared by distinct model, a flood of spellings of one model moves the floor with no
  guard.

**Revisit when:** `/v1/boards` serves a row's raw name or harness, or a board's floor stops counting
every row.

## D-180 — The phone's privacy sinks hold by what the compiler resolves, not by how the source spells it

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W2 · **Date:**
2026-10-06 · **Amends** D-126's enforcement (`scripts/client_decl_gate.py`, "What this gate does NOT
do") · from #85, gap G-1.

**Context.** D-160 clause 1 and D-168 clause 9 promise that nothing derived from the question reaches
the daily `/v1/boards` request or the standings file. The M17 closure's security seat broke both
with every gate passing (`docs/reviews/m17-closure-security-review.md`, MINOR-3):
- **P2:** a `nonisolated(unsafe) static var` on `EngineClient`, set by the screen from the question's
  refinements and read by `boards()` into a query item;
- **P3:** the screen built `Standings(apiVersion: typed, ...)`, wrapped it as `FetchedStandings` and
  saved it through `StandingsStore`, into the device's caches.

The declaration gate scopes by file, and the text gate by spelling, so a relay through shared state,
or a constructor called from the wrong file, passes both.

**Decision.**
1. The two privacy sinks are named: `EngineClient.swift`, which sends every request, and
   `StandingsStore.swift`, which writes the standings file.
2. The declaration gate reads the compiled module, in all four build configurations, and refuses:
   - mutable stored state declared in a sink file outside a function body: a `static`, global or
     member `var`;
   - a sink file reading mutable stored state declared in any other file, whatever reaches it (a
     global, a static, or a class instance's `var` through a `let`);
   - `FetchedStandings(payload:)` built anywhere but the two sink files: only the engine's answer and
     the store's own file become standings;
   - `EngineClient(baseURL:session:)` or `EngineClient.engineURL(from:)` used anywhere but
     `EngineClient.swift`: the app builds `EngineClient()`, so no other file chooses where a request
     goes (the W2 review's B2);
   - anything a sink holds at a type's or the file's scope, a `let` included, of a type outside a short
     list of values and the `URLSession` its own initialiser builds: a `let` holding an
     `NSMutableString` is as shared as a `var` (the W2 review's M1);
   - a sink calling a function, an initialiser or a computed property another file declares, unless it
     is listed with its reason (today `UIText.engineAddress` and `FetchedStandings.init`): a body
     another file owns can read the screen's state (M1). A listed call the sink no longer makes fails
     the gate, so the list cannot go stale;
   - `StandingsStore(url:)` or `StandingsStore.save(_:at:)` used anywhere but `StandingsStore.swift`:
     the app reaches the store through `onDevice.currentKept` only (the second W2 review's U10, P3w);
   - a kept type (`FetchedStandings`, `EngineClient`, `StandingsStore`) extended outside the file that
     declares it, or conforming to a protocol the app declares: a protocol requirement its
     initialiser satisfies is another name for that initialiser (P3w, U8, U11);
   - memory touched unsafely anywhere in the client (`Unsafe*`, `withUnsafe*`, `unsafeBitCast`),
     which can rewrite a sink's own values (U9); the client uses none;
   - shared mutable state (a global, `static` or class `var`, or a closure kept in a global or a
     `static`) read by the code a sink runs outside its file: the functions, initialisers and computed
     properties it calls, followed through the client, every member a protocol requirement may
     dispatch to, and every custom coding witness, which a decoder runs by no name (S5, S5b).
3. So a sink sends or keeps only what its parameters, its own configuration and the engine's answer
   give it, by every route clause 2 names, and `boards()` takes no parameter (INV-66).
4. Lanes without Xcode hold the same by text, as the M17 seat proposed: no stored `static var`, with a
   value or without, a tuple's included, no stored `var` at file scope however indented, and no
   `nonisolated(unsafe)` in the two files; `boards()` calls exactly `fetch("v1/boards", query: [])`;
   `Standings(` is built nowhere in the client; `FetchedStandings(` appears only in the two files. A
   compilation directive inside a comment or a string is text, not a branch.

**Measured.** A throwaway spike (`spike-m19-g1`, 2026-10-06, never pushed) ran the three rules over
the compiled client in two configurations: the shipping client gave no finding; P2 was refused by
the first rule, a variant relaying through a global `var` in `ContentView.swift` by the second, and
P3 by the third. The current gate passed all three mutants in all four configurations. The W2
review's relays were each refused on the shipping client in all four configurations after the fix:
U5 and U3b (a client built on a URL made from typed text, in `Detail.swift` and in `FrontDoor.swift`),
S3 (an `NSMutableString` held as a `static let` on the client, set by the screen) and S2b (a function
in `Detail.swift` that the request calls). So were the second review's P3w (P3 through a protocol
requirement), U8 and U11 (a client built through one, on an address made from the question or out of
`Any`), U9 (the client's address rewritten through unsafe memory), U10 (a store on a path made from
the question), and S5 and S5b (the screen's global read by the standings' initialiser and by a
decoding witness), each planted alone.

**The rejected alternative.** A type that cannot carry the question: a constructor only the network
answer or the store's file can call. Swift's access control is per file, and `FetchedStandings` has
two legitimate producers in two files and twelve test call sites. Admitting exactly those needs a
token per file and a test-only way to make one, which any client file could then call. It also does
nothing for P2, whose relay is shared state, not a type.

**What it does not do.** It does not prove that nothing derived from the question reaches a sink
by any route the compiler accepts: that is a property of how values flow, and a check over the
declarations the compiler resolved holds only the routes it names (clause 2). Two reviews each found
routes past the rules of the day; each is named and refused now. It does not follow a stored
property's default value, a global or `static` `let`'s initialiser, a closure kept in a value, or
state Foundation holds (`Thread.threadDictionary`, the second review's M1): gap G-1, #172. A sink
file's own code is trusted: an edit inside `EngineClient.swift` that sends a new parameter is a
reviewed change to a security glob, and its tests pin what each request carries (INV-64, INV-65).
The date the standings store writes comes from its caller, a channel no rule here sees (#170).

**Mitigation if violated.** A relay through shared state, or standings built from typed text, again
carries the question off the device or into its caches with every gate passing.

**Revisit when:** a third sink appears (a new route or a new store), or Swift can admit exactly two
files to a declaration.

**Note (M21-W3, #172, #85, #170, #174, #188; the wave's review, rounds 1 to 4):** the sink rules
gained shapes in the gate's fixture (`scripts/client_decl_fixtures/`), which defines what they refuse.
The compiled gate refuses the shapes its fixture holds, each as written there; the same form written
another way (bound to a name first, split over lines, behind a widened type) is not held, and any
other form is not held: see INV-66 in `docs/security-invariants.md` (G-1, #242), and G-12 (#241) for
what reaches a value by name. The standings store dates what it keeps by its own clock (#170). The
request rule is INV-64's (G-11, #244).

**Note (M21-W4, #248):** "What it does not do" above says the routes two reviews found are "each
named and refused now". That is more than the gate holds: each is refused in the shapes the fixture
holds, as written there, and any other form is not held: see INV-66 in `docs/security-invariants.md`
(G-1, #242). The cited tests are renamed to what they hold (D-192 clause 6).

## D-181 — The phone's arithmetic and ordering rules are checked on what the compiler resolves

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W2 · **Date:**
2026-10-06 · **Amends** the enforcement of D-104, D-138, D-160 clause 2 and D-167 clause 4 · from
#60, gap G-2.

**Context.** The text tripwires for REQ-APP-005 (no arithmetic on a number the engine sent) and
Ruling A (the client orders nothing itself) match the words around an operator and the name of a
sort's receiver. `let place = standing.position; place + 1` passed the first (the M17-W4 review's
R4), and a second `common.sorted()` in `Combine.swift` passed the second (its Tester's M7).

**Decision.**
1. A served number is any numeric value stored by a type whose own declaration conforms to
   `Decodable` or `Codable`, found on the compiled module, never listed by hand; a type the engine
   never sends (the phone's own gap register) is named, with its reason, and a static is never
   decoded. A conformance declared in an extension is not seen (#173). The fields a ruling speaks of
   have a kind (score, position, price, the tie margin, the Elo anchor); any other is a served number
   no ruling names.
2. The declaration gate (D-180's home) follows each served number, to a fixed point, on the compiled
   module in all four configurations: through a binding, an assignment (`=` and `+=`), a function's
   or a computed property's result, a function's, a method's or an initialiser's parameter (and a
   memberwise initialiser's stored property), a function used as a value, every name a loop, a
   condition (`if let`, `guard let`) or a `switch` case binds, a place handed `inout` (a mutating
   method's receiver), a closure handed each element, and a protocol requirement, from every member of
   its name. A value carries a served number only if its compiled type can hold one, and each carrier
   is keyed where the compiler declares it, never by a bare name; but a name a loop, a condition or a
   closure binds is keyed by the line its statement or value starts, so one written on a later line
   is not followed, and a tuple assignment marks its first name only. Not followed: `self` in a member
   of a numeric type, an enum case's payload, a subscript's parameter, `Any` and text (#171, #173).
3. An infix arithmetic operator (`+`, `-`, `*`, `/`, `%`, each with its `=` and `&` forms) of the
   standard library or Foundation, on any type but text and the collections (`Int32` and `Decimal`
   included), or one of
   the numeric methods `advanced`, `distance`, `adding…`, `subtracting…`, `multiplied…`,
   `divided…`, `remainder…`, `squareRoot`, `negate` and `addProduct`, on a served number, is refused
   outside the place a ruling names. Prefix `-`, shifts and bit operators, an operator passed as a
   function (`reduce(0, +)`), free functions (`pow`) and other numeric methods
   (`truncatingRemainder`, `quotientAndRemainder`) are not seen (#173). The places: scores and the
   tie margin in `Uncertainty.swift` (D-138), the anchor in its three conversions out of 100 (D-143),
   positions in `Combine.swift` (D-167), and prices only in `priceInPages` in `Router.swift` and
   `Language.swift`, which turn the price per million tokens into a price per page, in English and
   in Turkish (REQ-CMP-002, the unit a reader outside the industry uses, beside the exact figure).
4. A sort, reversal, shuffle or `max(by:)`/`min(by:)`, the standard library's or Foundation's
   (`sorted(using:)`, `NSArray.sortedArray`), is keyed on the receiver the compiler resolved, and
   counted: each permitted one may occur as often as its table says, once today.
5. A permission the shipping client no longer uses fails the gate, so a ruling cannot outlive its
   code and a change in the compiler's printed layout cannot silence a rule unnoticed.
6. The text tripwires stay, for the lanes without Xcode.

**Found on the way.** The price-in-pages conversion was arithmetic on a served price that no table
named: its parameter is called `blendedPerM`, without the `.` the text tripwire looks for. REQ-CMP-002
requires it, so it is permitted by name here rather than removed.

**Measured.** The shipping client passes in all four configurations. Three mutants planted in it
were each refused: a served score doubled through a local on the screen, a served price divided
through a local in `Detail.swift`, and a second `common.sorted()` in `Combine.swift`. After the W2
review's B1, its sixteen mutants (A0 to A14 and O1) and eight more shapes found while fixing it (`if
let`, `guard let`, a `switch` case, a memberwise initialiser, a function as a value, `append`, a
protocol requirement, `-=`) were each refused on the shipping client in all four configurations,
with no refusal outside them.

**The rejected alternative.** Exact-expression permissions, as `EGRESS_EXACT` does for egress: each
permitted line spelled out. It holds what is written, but an alias on a line nobody listed is still
invisible to it, which is the hole.

**What it does not do.** It does not hold that no arithmetic happens on a served number however the
value is named: it holds the operators, methods and names clauses 1 to 3 list, and two reviews each
found more past the lists of the day (the second review's B3, #173). A number passed through `Any`
or through text is not followed, and the served facts (`whyFact`, `tradeOffFact`) reach the phone
through `Any`, so arithmetic on a fact's number is held by review (gap G-2, #171). It refuses more
than it should in two ways: a protocol requirement carries what any member of its name carries, and
an operand counts as served when a served field appears anywhere inside it, a closure's body
included, so `answers.filter { $0.eligibleCount > 0 }.count + 1` is refused (the second review's M5,
#173); and a list of served numbers is a carrier, so `let scores = picks.map(\.score)` then
`scores.count + 1` is refused as arithmetic on a score (the third review's M2, #173). Formatter rounding is not arithmetic here (REQ-APP-005 stays partial for it).

**Revisit when:** a file needs arithmetic on a served number a ruling does not yet name, or #171 or
#173 is taken.

**Note (M21-W3, #171, #173, #169; the wave's review, rounds 1 to 4):** both are taken: the arithmetic
rule gained shapes in the gate's fixture (`scripts/client_decl_fixtures/Arithmetic.swift`), which
defines what it refuses. The compiled gate refuses the shapes its fixture holds, each as written
there; the same form written another way (bound to a name first, split over lines, behind a widened
type) is not held, and any other form is not held: see INV-76 in `docs/security-invariants.md` (G-2,
#242). A served fact is a kind of its own that only the three D-143 places may restate. A named
closure or loop parameter is still matched by name up to five lines below its binding, so the gate
can refuse an unrelated binding of the same name, more than it should (round 2's M1; none on the
shipping client). The text tripwire derives the served fields the compiled gate does, held equal on
the fixture (#169).

**Note (M21-W4, #248):** "What it does not do" above says the rule "holds the operators, methods and
names clauses 1 to 3 list". It holds them in the shapes the fixture holds, as written there; the same
operator written another way is not held: see INV-76 in `docs/security-invariants.md` (G-2, #242).
The two text pins it cites are renamed to what they hold (D-192 clause 6).

## D-182 — Each pick carries its model's id on `/v1`, and the app keys its cards on it

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W2, written
before the wave serves the field · **Date:** 2026-10-06 · **Amends** the `/v1/recommendations` pick
contract (`PUBLIC_PICK_FIELDS`), additively · from #138.

**Context.** The engine and the app decide "the same model" by two rules. Since #102 (M18-W7) the
engine decides that a cheaper pick is the leader by its ranking row, because a display name is not
unique (`models.display`). The app merges picks into one card when their display name, vendor, score
and price are all equal (#63 finding 1, `AnswerPlan.swift`), because a pick carries no id. #129 was
the case where the rule could fail: one release under two ids, with the same name and vendor.

**Decision.**
1. Each pick on `/v1/recommendations` gains `model_id`: the canonical id of the model it ranks, the
   registry's own (curated or derived). The field is additive; every existing field keeps its name,
   type and meaning.
2. The app makes one card of the picks that share a `model_id`. A pick with none, from an engine
   older than this decision, falls back to the four-value rule.
3. The id is identity, not a name: it is never shown.

**Why it is safe to publish.** An id is derived from the public names the sources publish, by the
registry's closed grammar, and is already a key of `/v1/boards`' `models` (D-167). It says nothing
about the reader: no request carries the question (D-160 clause 1).

**The rejected alternative.** Keep the four-value rule. Two models that share a display name, a
vendor, a score and a price would still show as one card, and one model under two ids as two.

**Mitigation if violated.** The app shows one card for two models, or two for one, and the engine and
the app disagree about which pick is the leader.

**Revisit when:** the app needs the id for more than grouping, or `/v1` gains a second id field.

## D-183 — The gates see before the push: CI's skips counted, the run offline, the plan read

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W3, the owner
reviews the wave (AGENTS.md §3) · **Date:** 2026-10-06 · from #137, #140, #122, #149, #117, #108;
written at the W3 review's M10.

**Context.** Four checks found their problems after a push or never: CI's skip budget, raised three
times in M18 and once in M19-W2 only after CI failed; the wave gates, which read headings and one path
while the plan says more; a child process a test starts, which no in-process guard sees; and a
held-out set, which only measures while nothing was tuned on it (D-147 clause 5), with no check of
the signal words.

**Decision.**
1. **Every skip names its need.** A test skips only through `@pytest.mark.needs("<what>")`;
   `tests/skips.py` names each need once, with whether this machine has it and whether CI's test job
   does, and why. `make test` counts, from those markers, how many tests CI will skip
   (`coverage_floor.py --derive`) and fails unless it is the budget in `docs/skip-budget.txt`, more or
   fewer. A skip spelled any other way is refused in the source (#137).
2. **The wave gates read the plan.** A wave an amendment or a table names must have its own heading,
   so its close can be required; a close whose footprint touches one of its plan's security globs
   (the `Security globs` bullet, brace forms and folders read) must be HIGH, and a plan with no list
   fails closed (#140).
3. **The test run is offline at the operating system's level** (#122, option B). On macOS `make test`
   runs pytest inside `scripts/offline.sb`: every outbound connection but loopback is refused before
   a packet leaves, children included whatever their language, and so are the system resolver's
   socket and its mach service, and LaunchServices (read from the profile, not measured by a lookup).
   The run `make test` marks must be offline on a Mac whatever the environment names the system.
   The run says it must be offline, and stops before any test if a child could still name an outside
   peer. The probe sends nothing (a UDP `connect()`). CI's half is a patch for the owner's workflow
   file, posted on #122.
4. **A deadline test is held against a plain timer started beside it**, not the clock: a process that
   is not scheduled makes every timer late alike, and a race that waited for the work would not
   (#149).
5. **A signal word only a live held-out set holds is flagged by the entry**: every list of strings in
   `Reading.swift`, matched at a word's start with any ending, against the live held-out sets and every
   other probe set. Each flagged entry is named in the test with where it came from; a new one fails
   until a reviewer has asked, and a stale name fails too (#117).
6. **A bare `URLSessionConfiguration()` is refused in the source**, in its two spellings, since the
   Swift tripwire does not see it and it trapped a test process (#108, its cause read, not measured).

**The rejected alternatives.**
- **The checks in CI only.** They would keep finding problems after the push, which is the fault this
  decision exists to fix.
- **#122's option A**, a `sitecustomize` carrying the guard into Python children: it misses a scrubbed
  environment, a non-Python child and the nightly's refresh. **Option C**, holding it by review: a
  gate that names a stance proves nothing about what a child does.
- **#117 matching English whole and Turkish with suffixes.** Replayed on M18-W3's tree it missed two
  of the review's phrases, Turkish words with no Turkish letter; a word's language cannot be read from
  its letters (the W3 review's M8). The W3 Tester's fixture now holds M18-W3's own eleven, from its 27.

**What it does not do.** CI's test job is not offline until the owner applies the patch (gap G-5);
the record of what CI has (`NEEDS[...].in_ci`) is kept by hand beside the workflow; the HIGH rule
reads the footprint a close records, not the commit range's diff; the held-out check reads the
signal lists, not the wording tier's hint sentences; the Swift tests' own children are not under the
offline profile; #108's guard reads two spellings, not a typealias or a subclass. Each is filed.

**Revisit when:** the owner applies #122's CI patch (`NEEDS["offline"].in_ci` becomes `True`, and the
budget falls by one), or a check here fires on correct input.

**Amended by D-192 (2026-10-10)**: the close checks also read the commit range's history, the process log and the ledger for skips and the hooks (D-192 clauses 2 and 3).

## D-184 — Reading a question, the second round: a question of fact is a doubt, and the image rule stays on vision

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish); M19-W4, the owner
reviews the wave (AGENTS.md §3) · **Date:** 2026-10-07 · from #66, #113, #177 · **Amends** D-169
(as amended at M18-W3), clauses 3 and 4.

**Context.** M18-W3 left two gaps (`docs/research/m18-w3-question-reading-probe-2026-10-04.md`): the
on-device model calls a question of everyday fact "a model search" (1 of 10 caught), and a request to
make an image routed anywhere but `vision`, or worded as the rule did not read it, is ranked as if
measured (#113). M19-W4 measured three variants per problem on the tuning sets and the built one on
fresh held-out sets, twice per tier (`docs/research/m19-w4-question-reading-probe.md`).

**Decision.**
1. **A question of fact is a doubt in code** (`InputSignals.asksAFact`): at most ten words, opening as
   a question of fact ("who", "when", "where", "what is", "what was", "what year", "how many", "how
   much", "how tall", "how long", "how far", "how old", "how big", "how high"; and the Turkish words
   for where (as "the place of"), who, how many, when and which year), and naming, in any case folding,
   none of the models, AIs, AI tools, askers or their wishes, recommendations, tasks, current things
   or images of the asker's that its lists hold. A search those lists do not name ("who is the leader
   in reasoning") still reads as one, and is asked about rather than given the note (the second code
   review's M1). It joins pasted content and an order to the app in
   D-169's table: with the model's "something else" it is the note; alone the reader is asked. It runs
   on every tier, so without the model a question of fact is asked about.
2. **The signals read input as people typed it in the tuning sets:** small talk at length and Turkish
   without its letters; a task ordered by "make" or by a Turkish verb typed without its letters; an
   order to copy the hidden rules out, or a role handed over ("pretend ur a", "from now on answer").
   Every word the signals added before the measure is in a tuning row at a word's start, as #117's
   check reads; the code review found two that no tuning row holds whole, as the app matches them
   (`nerede`, `öner`): the first left the signal, the second is read by its stem (record §6).
3. **The image rule stays on `vision`** (M18-W3), and reads "photo" and "change" typed without their
   Turkish letters, takes an image before `galerisi`, `yükleme`, `sayfası` or `bölümü` as a modifier,
   and compares English words as English under the Turkish folding. The Turkish "make" (`yap`) the
   wave added came out: it is the verb of most Turkish task phrases ("do the question in the photo"),
   and read requests to read an image as making one (the fourth code review's B1); it stays a verb of
   a task with its content (`bu cümleyi daha resmi yap: …`, "make this sentence more formal: …", clause 2). At the baseline 6 and 7 of 20
   requests to make an image went to
   `web-dev`, where the rule does not reach. The wave reached beyond `vision` three times (every
   surface but code; a site vocabulary as a guard; a new image or the asker's own), and each reach
   told ordinary questions about an image on a website, in a store, an app or a document "not
   measured" (the three code reviews: MAJOR, BLOCKING, BLOCKING). By the rule that a third BLOCKING
   verdict on one finding takes the slice out, the reach came out (#191).
4. **The model's instructions do not change.** Telling it what a question of fact is moved its
   verdict on 1 of 22 such questions and cost surface accuracy (variant a); a closed field asking it
   whether the text makes a picture said yes to reading one (variant b). Neither was built.

**Measured** (§4 of the record), at `de8c3f8`, twice per tier: no genuine search given the note, 2 and
1 of 40 asked; knowledge questions 6 and 6 of 20 caught (baseline 1, 3; bar 14); not-a-search inputs 25
and 27 of 50 (baseline 18, 21; D-169's bar 40); requests to make an image told "not measured" 8 and 8
of 20 with the model (baseline 2, 1; bar 14), 18 and 18 without it (baseline 14; bar 18). Every guard
holds. D-169 clause 6's catch bar and #66's and #113's model-tier bars are missed: by clause 6 the
work stops after three variants per problem, and the pull request asks the owner whether to ship what
holds. After the code reviews (record §6), on the spent sets: knowledge 5 and 5 of 20, not a search 24
and 26 of 50, genuine searches asked 1 and 0; with the image rule back on `vision` only and without
`yap`, requests to make an image told "not measured" 2 and 1 of 20 with the model and 14 of 20 without
it, the baseline: what ships does not move #113, which meets neither of its bars.

**#177.** The three M18 held-out sets, spent at M18-W3, are retired to tuning
(`RETIRED_HELD_OUT`), rather than an origin shown for each of the four signal words added after them.

**The cost.** A few more genuine searches are asked about (on the tuning set, one more in 186; on the
held-out set, 2 and 1 of 40 at `de8c3f8`, and 1 and 0 of 40 as the code ships, from 0). The fact signal reads about a third of a stranger's questions of
fact: its forms are the tuning sets' (§4 lists the misses).

**Revisit when:** a stranger's first use (#91's protocol) gives a set to measure on, or a stronger
on-device model reads a question of fact as something else.

**Amended by D-187 (2026-10-08)**: clause 3's image rule is retired: a request to make or change an image is answered from `vision`.

**Note from D-191 (2026-10-09)**: #194's change to clause 1 (the question of fact's model names from the registry) was tried at M21-W2 and taken out after three verdicts; clause 1 stands as written, with its eleven brands.

## D-185 — The first release: a public artifact inside the hosted image, and the app ready for TestFlight

**Status:** accepted -- decided by the agent on the owner's standing instruction of 2026-09-29
("proceed with what you recommend, don't ask", owner, translated from Turkish), after the owner called
the release on 2026-10-07 ("we need to deploy the engine to a real supabase or something and we need
to go for testflight"); M19-W5, the owner reviews the wave (AGENTS.md §3) and may overrule any clause
before the deploy · **Date:** 2026-10-07 · from #94, #88, #141, #145, #147, #142 · **Amends** D-116
(how the hosted artifact ships) · **Records** the owner's #88 ruling as the agent's recommendation,
pending the owner.

**Context.** D-116 chose Fly.io and an artifact shipped to the host; D-123 moved go-live to the iOS
app, and stopped at Fly's payment step. The owner named Supabase "or something": Supabase hosts
Postgres, auth, storage and Deno edge functions, and the engine is one long-running Python process
reading one SQLite file (D-116 weighed Supabase and set it aside for that reason). The licence review
of 2026-10-07 (#88) found sources whose terms do not clearly permit a public app, and App Review asks
an app showing a third party's content to be permitted to (guideline 5.2.2), TestFlight's external
testing included.

**Decision.**
1. **The host stays Fly.io (D-116).** `fly.toml` deploys the image's `hosted` stage, one machine always
   up, and names `model-ranking.fly.dev` as the one Host the engine answers to; its health check sends
   that Host (#94).
2. **The artifact ships inside the hosted image, built on the owner's Mac.** A volume starts empty,
   so a first deploy could not boot; an image that carries its artifact is one immutable pair of code
   and data, and a rollback restores both. Ingestion stays on the Mac (D-116 clause 2). The image tells
   its startup check where it binds, so with no Host list it refuses to boot (#94).
3. **The hosted engine serves a public artifact**, derived offline from the Mac's (`app.workflows.public`),
   with seven sources left out, each for its reason in `LEFT_OUT`:

   | source | feeds | why it is left out |
   |---|---|---|
   | `swebench` | `coding` (half its rows; Epoch's SWE-bench Verified stays) | CC BY-NC 4.0 |
   | `epoch_arc_agi` | `abstract`, its only source | ARC Prize: personal or internal use; no database without permission. **Replaced by `arc_agi_2`, ARC Prize's MIT public-evaluation runs (D-194)** |
   | `epoch_deepswe_external` | `agentic-coding`, its only source | no licence published. **Replaced by `datacurve_deepswe`: Datacurve's own leaderboard (public numbers, attributed, D-215; D-216)** |
   | `epoch_terminalbench` | `computer-use`, its only source | no licence stated. **Replaced by `terminalbench_4`, TB 4.0's Apache-2.0 leaderboard repository (D-194)** |
   | `epoch_webdev` | `web-dev`, its only source | arena.ai's terms: personal or internal business use |
   | `epoch_mmlu` | `everyday`'s secondary score, display only | no licence found |
   | `openrouter` | the second price of 168 models | its terms forbid use of its data unless authorised. **Replaced by `models_dev`, MIT (D-194)** |

   The public artifact also drops LiteLLM's own copies of OpenRouter's prices (`openrouter/` aliases)
   and the vendor subscription plans, which `/v1` never serves; its pricing credit names only the
   sources it serves. Measured on the artifact of 2026-10-07: 296 models priced, against 303 (seven
   had only an OpenRouter price); `assistant`, `everyday`, `expert`, `factuality` and `mathematics` each
   rank 2 to 4 fewer models. `abstract`, `agentic-coding`, `computer-use` and `web-dev` answer that
   they have no evidence on the hosted engine (D-121's path). The owner's Mac keeps every source under W-129's ruling. A source comes
   back with its publisher's written permission, or a licensed replacement (LMArena's CC-BY `webdev`
   board for `web-dev`, #185).
4. **The app is ready for TestFlight:** an app icon (a placeholder), a privacy manifest (UserDefaults,
   reason CA92.1; no tracking; nothing collected, D-126), the encryption answer in its Info plist, and a
   Release `ENGINE_URL` of `https://model-ranking.fly.dev`. `docs/release-testflight.md` holds the
   owner's steps.
5. **Nothing is deployed or uploaded by the agent.** The account, card, signing and App Store Connect
   steps are the owner's, after the Stage 5.1 security review (BLOCKING before any deploy).

**The alternatives not taken.** Supabase: a rewrite of the engine as edge functions over Postgres, for
no gain the product needs. A volume with the artifact uploaded by hand: a first deploy that cannot
boot, and code and data that roll back apart. Every source in public: App Review may ask for permission
nobody holds.

**The cost.** Four surfaces dark on the hosted engine until a publisher says yes; `coding` ranks 32
models where the Mac's ranks 54. A deploy per refresh the owner wants public.

**Revisit when:** a publisher grants permission, a licensed replacement is built, or the app moves to
a paid launch (then SWE-bench must go whatever else changes, and the table goes to a lawyer).

**Amended by D-186 (2026-10-08)**: clause 3's table is not applied while the app is on TestFlight: the hosted engine serves every source; the table returns before production.

**Amended by D-190 (2026-10-09)**: `web-dev` ranks on LMArena's own WebDev board (CC-BY-4.0), so the public artifact keeps the surface while `epoch_webdev` stays in clause 3's table (#185).

**Amended by D-193 (2026-10-12)**: the owner ruled on clause 3's table source by source; no source is left out, and every served publisher is credited on the app's Credits screen (#260).

**Amended by D-194 (2026-10-13)**: clause 3's table -- `epoch_arc_agi`, `epoch_terminalbench` and `openrouter` are replaced by their publishers' licensed data and no longer built; `epoch_deepswe_external` waits for the owner's Hugging Face token (#265). The table notes each replacement.

**Amended by D-215 (2026-10-21)**: clause 3's licence stance -- the owner's rule for a free, non-commercial app; `epoch_webdev` and LiteLLM's `openrouter/` copies are removed as a duplicate and stale data, SWE-bench stays with an email owed before any payment (#376).

**Amended by D-216 (2026-10-21)**: clause 3's table -- `epoch_deepswe_external` is replaced by `datacurve_deepswe` (Datacurve's own leaderboard) and no longer built (#265).

**Amended by D-219 (2026-10-22, proposed)**: clause 3's licence record -- #379's ten boards, read under D-215: OSWorld-Verified, METR's time horizons, LiveBench and SimpleBench served; Humanity's Last Exam, DeepResearch Bench, SciCode, Vending-Bench 2, Video-MME and GDPval skipped, each for its reason (#379).

**Amended by D-217 (2026-10-21, proposed)**: clause 2 -- the hosted image's artifact is built by a scheduled GitHub Actions job each night as well as on the Mac; clause 5 -- that job, the owner's workflow, deploys it, never the agent (#387).

## D-186 — On TestFlight the hosted engine serves every source; the licences are settled before production

**Status:** accepted -- decided by the owner on 2026-10-08, from the TestFlight build ("remove D-185;
we talk about the licences when we go to production; let's see the app on TestFlight, I want all the
models", owner, translated from Turkish) · **Date:** 2026-10-08 · **Amends** D-185 clause 3 · from
the owner's first TestFlight session.

**Context.** D-185 clause 3, taken by the agent on the standing instruction, left seven sources out of
the hosted engine's artifact for their licences. On the first TestFlight build `agentic-coding`,
`web-dev`, `computer-use` and `abstract` answered "Nothing to recommend here" and `coding` ranked 32
models where the Mac's ranks 54. The owner had not ruled on the licences and read the result as a
filter gone wrong.

**Decision.**
1. `public.LEFT_OUT` is empty: the hosted engine serves every score, price and accessibility row the
   Mac's engine serves, LiteLLM's copies of OpenRouter's prices included. The vendor plans, which `/v1`
   never serves, still stay out.
2. The derivation's machinery stays, held by its tests on planted sources, so the day a source must
   go it is one line in `LEFT_OUT`.
3. D-185's table is the starting point when the app goes beyond internal testers: before external
   TestFlight testers or the App Store, the owner rules on each source (a permission, a licensed
   replacement such as #185's, or leaving it out).

**The cost.** The hosted engine serves data whose terms do not clearly permit a public app (D-185's
table), to the owner's internal testers. **Revisit when:** external testers or an App Store
submission are planned.

**Amended by D-193 (2026-10-12)**: clause 3's ruling is made; `LEFT_OUT` stays empty beyond TestFlight's internal testers, with the permissions the owner is getting.

## D-187 — An understood question is answered from the closest board, never "not measured"

**Status:** accepted -- decided by the owner on 2026-10-08, from the TestFlight build ("there is no
'we don't measure' any more: we measure, we produce something. If we don't understand the question,
that is different, but if we do, for image polishing for example, we show the models that scored
well on images", owner, translated from Turkish) · **Date:** 2026-10-08 · **Amends** D-169 and
D-184 clause 3, and REQ-RTR-005, REQ-ASK-003 and REQ-IMG-003 · from the owner's first TestFlight
session.

**Context.** With no on-device model on the owner's phone, the wording tier answered most questions
"not measured": its decline groups caught "which model writes code best", it refused every Turkish
question, and it needed an English embedding the device may not have. On the tuning and retired sets
it routed 22 and 26 of 80 coding questions right and declined 41 of each.

**Decision.**
1. **Words that name a surface decide first** (`CategoryHints.surfaceWords`), in English and in
   Turkish (typed with or without its letters), in an order where the more specific surface wins: an
   agent that codes, then code, then operating a computer or a site for the reader, then a site to
   build, and a cited search before a search. Only words with one reading are read; a word with a
   second one is read inside a phrase or not at all (the two hotfix reviews). They need neither the
   on-device model nor the embedding. The screen says the question was matched on wording. A question
   about AI models in general names no surface: the embedding reads it, and `everyday` answers it
   only where the embedding cannot.
2. **The decline groups decline nothing.** A question closest to making or changing an image goes to
   `vision`, the board of the models that read images best; one closest to sound, video or speed goes
   to the closest surface.
3. **#113's rule is retired.** A request to make an image on `vision` is answered from `vision`.
4. **The model's "none of these"** on a question it read as a search goes to the wording tier.
5. **What stays "not understood":** a question that names no surface and scores below the floor, and
   input that is not a search (D-169's note and question back).

**The cost.** A reader asking for something no board ranks (image making, speed) gets the closest
board's ranking, with its board named, not a statement that nothing ranks it. **Revisit when:** the
combination of boards for a task none ranks is built (the owner's next step: the on-device model
composing a list from the boards).

**Amended by D-191 (2026-10-09)**: clause 1 -- a comparison of any ranked families' names is answered from `everyday` (#206); the Turkish signals before the embedding (#218) and the Turkish general ask (#222) were tried and taken out after three verdicts.

**Amended by D-188 (2026-10-08, proposed)**: clause 1 -- a short question made only of model names, their tier names and Turkish particles ("claude mu chatgpt mi") is a general question before the embedding is tried, since the embedding reads it as English (#206, M20-W3; `CategoryHints.comparesModelsOnly`).

**Amended by D-196 (2026-10-14)**: clause 1 -- a confidently Turkish question that names no surface is read by the embedding against Turkish examples instead of declining (#222).

## D-188 — Our own list for every question: a family of boards per task, combined by position

**Status:** proposed -- the agent's proposal for the owner's goal of 2026-10-08 ("our biggest
strength": the app composes its own list per question from many boards, owner, translated from
Turkish); approved, amended or refused by the owner with the M20 plan (`docs/plans/m20-plan.md`) ·
**Date:** 2026-10-08 · **Would amend** D-167 clause 3, D-168 clauses 4, 6 and 7 (clause 6 is the owner's
#54 ruling, "no threshold": a family list keeps a model at half its boards) and D-187 clause 1 (#206) ·
from #209, #210, #211, #212.

**Context.** The default answer ranks one board per surface. The phone's combined list keeps only the
models every chosen board ranks (D-167 clause 3) and is built only when the on-device model picks a
refinement. The engine serves 63 boards; coding alone has eight related ones.

**Decision (proposed).**
1. **A family per surface.** The engine declares, for every surface, every board that measures that
   task, the primary first, and publishes it on `/v1/categories`; each board's evidence date is
   already on `/v1/boards`. The phone never keeps its own copy. A family holds at most one board of
   each source (Arena's slices are facets of one vote); two publishers of one benchmark are two boards
   (D-168 clause 5). Every other board stands outside every family with its reason: a language or a
   domain the question adds as a refinement, or a facet no surface measures. Each search surface keeps
   its one board: Arena's search and search-factuality boards rank the same models from one vote (the
   W1 Tester's M1). The families (`app.workflows.families`, held equal to this table by a test):

   | surface | family, the primary first |
   |---|---|
   | `coding` | `swebench`, `epoch_swe_bench_verified`, `aider`, `arena_text_coding` |
   | `agentic-coding` | `datacurve_deepswe`, `terminalbench_4`, `arena_agent` |
   | `assistant` | `arena` |
   | `everyday` | `epoch_eci`, `arena`, `epoch_mmlu`, `livebench`, `simplebench` |
   | `expert` | `epoch_gpqa`, `arena_text_expert`, `epoch_mmlu` |
   | `mathematics` | `epoch_aime`, `epoch_frontiermath`, `epoch_frontiermath_t4`, `arena_text_math` |
   | `computer-use` | `terminalbench_4`, `osworld_verified`, `arena_agent` |
   | `abstract` | `arc_agi_2`, `epoch_chess`, `epoch_mystery` |
   | `web-dev` | `arena_webdev`, `arena_text_coding` |
   | `document` | `arena_document`, `arena_text_longer_query` |
   | `factuality` | `arena_factuality`, `epoch_simpleqa` |
   | `vision` | `arena_vision` |
   | `search` | `arena_search` |
   | `search_factuality` | `arena_search_factuality` |
   | `text_to_image` | `arena_text_to_image` |
   | `image_edit` | `arena_image_edit` |
   | `text_to_video` | `arena_text_to_video` |
   | `image_to_video` | `arena_image_to_video` |
   | `video_edit` | `arena_video_edit` |
   | `long-tasks` | `metr_time_horizons` |

2. **Coverage.** A model enters the combined list when at least half of the family's boards rank it,
   rounded up, and at least one. With two boards, either is enough; "and at least two" was dropped after
   the W1 review measured it: on the served boards it turned a two-board family into the intersection
   this decision replaces (`computer-use`: 3 models where its primary board ranks 43). Measured on
   2026-10-08 (the served `/v1/boards`, the W1 families): `coding` 58 models (its primary 40),
   `agentic-coding` 18 (18), `everyday` 130 (155), `expert` 124 (154), `mathematics` 125 (144),
   `computer-use` 85 (43), `abstract` 80 (77), `web-dev` 215 (94), `document` 197 (34), `factuality` 134
   (116); `assistant`, `vision`, `search` and `search_factuality` are one board each (the search figures
   first measured, 28 (28, 27), were for a family that held both search boards, before the W1 Tester's M1).
3. **Place.** A model's place is the mean of its percentile positions, (position - 1) over (the
   board's size - 1), across the boards that rank it, positions only and never a score (D-105). Ties
   share a place and are broken by model id. A board that ranks no model, or that the standings lack
   (an outage, a source left out), is left out of the family's count.
4. **Staleness.** Every board counts the same. A board whose newest evaluation is more than 90 whole
   days old, or that publishes no date, is named under the list in one small line, never as a warning
   over it. A half weight was the first proposal; the W2 review measured it on the served boards:
   every board but Arena's is older than 90 days or undated, so Arena alone would have decided
   `coding`, `agentic-coding`, `everyday`, `computer-use` and `web-dev`, the one-source dominance
   clause 1 forbids. A shared position counts as that position (the competition ranking a board
   publishes).
5. **The default.** The combined list is the default answer on every surface: to every question asked,
   and on every surface the reader chooses (from "Change" or an alternative, read from no words). The
   launch screen, which answers no one yet, shows the primary boards' picks. The primary board's own
   answer (the picks and their price notes) is one tap away. Ruling A holds: coding shows two
   families, both or neither, neither leading. The list says which boards built it, each with its
   date, and how many of them a model needs (the W4 review's B1). A family of one board (`vision`,
   `search`, `search_factuality`, and `assistant` with no refinement) is that board's own answer, the
   cards (the M20 repo review's M6).
6. **Refinements from the words (amends D-168 clause 4; the W3 review's B1).** Where the on-device
   model did not read the question (it is off, or another tier answered), the words choose the
   refinements it would have: `Refinements.read`, in English and Turkish, from words with one reading
   only, and at most one of each kind, as the model's schema has one field per kind (the first each
   the question names). An English language name counts only as the task's language ("in French",
   "learn Spanish", "Korean translation"), since it is also a nationality ("German cars", "in Chinese
   stocks"); a domain word with a second meaning is not read (law, health, a novel approach). The
   answer plan is the one reader, a gate holds it, and `familyBoards` keeps only what the surface
   allows, languages first. The routing outcome still carries refinements only from
   `ModelOutputBoundary`. Where the model read the question, its choice stands, none included.
   **One vote, one board (the M20 repo review's M1, the agent's ruling under the owner's standing
   instruction of 2026-09-29).** Every refinement is a slice of Arena's text vote, so it takes the
   place of the family's board of that vote, which `/v1/categories` names as `refined_board`; it never
   joins beside it, where one vote would count twice for the coverage and for the mean (clause 1). Of
   a language and a domain, the language stands. `assistant` in Spanish is the Spanish board's list.
   A gate holds every family, with every refinement it allows, to one board a vote.

**The alternative.** Keep "every board ranks it" over the two or three boards most models share. It is
simpler, but a new model ranked by two boards out of eight would never appear.

**Revisit when:** the owner's judgement of a sample of answers (#226) prefers the primary board's own
answer to the family list on more questions than ours (`docs/judgement-sheet.md`; `revisit` in
`scripts/judgement_sheet.py`, M21-W2). The labelled set of #195 cannot show it: it is labelled for the surface, not
for the best model (M20-W5, `docs/research/m20-w5-family-probe.md` §4; the M20 repo review's M5).

**Amended by D-190 (2026-10-09)**: clause 1's table -- `web-dev`'s family is `arena_webdev`, `arena_text_coding`; Epoch's copy of the same board stands outside (#185).

**Amended by D-194 (2026-10-13)**: clause 1's table -- `computer-use` and `abstract` rank on licensed boards (`terminalbench_4`, `arc_agi_2`), and `terminalbench_4` takes Epoch's TB 2.0 copy's place in `agentic-coding`'s family (#265).

**Amended by D-216 (2026-10-21)**: clause 1's table -- `agentic-coding`'s family is `datacurve_deepswe`, `terminalbench_4`, `arena_agent`: Datacurve's own DeepSWE board in place of Epoch's copy (#265).

**Amended by D-219 (2026-10-22, proposed)**: clause 1's table -- `computer-use` adds `osworld_verified`, `everyday` adds `simplebench` and `livebench`, and `long-tasks` is METR's time-horizon board alone (#379).

## D-189 — What a model is: a release its maker names, and an id that keeps its meaning

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take
the recommended option; the owner may overrule) · **Date:** 2026-10-09 · **Amends** D-166, D-157
clause 2 · from #163, #164, #165.

**Context.** Three defects of one kind put one model's score or price on another (M19-W1's findings):
- DeepSeek V3's rule gathered V3-0324's rows, which boards spell `(0324)` or `(Mar 2025)`, so V3 was
  ranked on V3-0324's scores; R1's rule did the same with R1-0528, and Arena ranks both beside R1.
- xAI retired `grok-code-fast-1` and `grok-4-1-fast-reasoning` on 2026-05-15 and now routes them to
  newer models, so their prices are the new models' while their scores are the old ones'.
- A fine-tune's price alias (`ft:gpt-4o-...`) reached its base model's price median through a
  curated rule, at about twice the base price.

**Decision.**
1. **A model is a release its maker names.** Dated snapshots its maker serves under one model name
   (GPT-4o's, the Gemini 2.5 Pro previews) are that model, as D-182's one-release rule has it. A
   release the maker publishes under a name of its own (DeepSeek-V3-0324, DeepSeek-R1-0528) is its
   own model, whichever way a board spells its date; a curated rule for it precedes its
   predecessor's, which excludes it.
2. **An id that changes meaning moves.** A retired id its maker reroutes to another model is a
   moving alias (D-166): it derives no model, and its rows are dropped and counted. Each is listed
   with its retirement and where it routes. Its historical scores are lost, because a price row
   carries no date to keep only the prices from before the retirement.
3. **A fine-tune is its owner's model.** `canonicalize` refuses a name whose last route segment
   starts with `ft:`, for its reason (`fine-tune`), as D-157 already refuses it on the derive path;
   it is counted with the modality guard's refusals, never as drift.

**Applied (corrected after the M21-W1 review's B1 to B3).**
- **DeepSeek** V3-0324 and R1-0528, in every spelling a board uses (`(0324)`, `(Mar 2025)`, `(0528)`,
  Epoch's `(May 2025)`). A distill or a small size after the release (`DeepSeek-R1-0528-Qwen3-8B`) is
  another model, named by its own rule.
- **Mistral Large**, which Arena ranked five times as one model: Large 1.0 (24.02), 2 (24.07), 2.1
  (24.11), 3 (25.12) and 4, as Mistral's model page names them (docs.mistral.ai/getting-started/models,
  read 2026-10-09). The undated `mistral-large` moves (D-166).
- **Claude Sonnet 4.6**, which four boards ranked as Sonnet 4.
- **GLM-4.6V**, the vision model, apart from GLM-4.6, and GLM-4.6V-Flash apart from both, in every
  spelling (Epoch's `glm-4.6v_32K` included).
- **R1's namesakes**: R1-Zero, R1-Lite-Preview and the R1T Chimeras are not R1, and Volcengine's
  `deepseek-r1-250528` is R1-0528. A one-digit minor version after Mistral Large 3 or 4, as after
  Sonnet 4, is another release.

**What stays gathered, and why.** GPT-4o's dated snapshots and the Gemini 2.5 Pro and 2.5 Flash previews
are snapshots of one model name their makers serve, so they stay one model; a board that ranks two of them
is read at the model's best row (D-182). The first version of this paragraph said no board ranked a
gathered family twice. That was false: Arena ranks GPT-4o's snapshots apart. **The query that finds the
cases**, kept in `docs/research/m21-w1-first-nights-after-m19-w1.md`, lists each curated model a board
ranks under two release names; the candidates it found that are not split here (a size or a name the
maker publishes apart, whose maker's page this wave did not read) are #232's.

**Consequence.** Model ids move on the first night after the release (`deepseek-r1-0528` is new; V3's
rows split): D-179's board guards count those links as changed rows, as they did for #129's joins.

**Revisit when:** a maker names a release apart that a board spells with a date this rule does not
read, or a rerouted id's historical scores are needed (then pricing rows need a date).

**Amended by D-195 (2026-10-13)**: clause 1 -- seven more releases their makers publish apart are split (#232, #234), three cases stay gathered, and GPT-5.6's Pro is a mode, not a release (#266).

## D-190 — `web-dev` ranks on LMArena's own WebDev board

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 · **Date:**
2026-10-09 · **Amends** D-185 (what the public artifact can serve), D-188 clause 1 (the families table) ·
from #185.

**Context.** `web-dev`'s only board was Epoch's copy of the WebDev Arena leaderboard. Epoch cites arena.ai,
whose site terms D-185 read as personal or internal business use, so its licence table keeps the copy off a
public artifact, and the surface would go dark on the hosted engine once the table applies (D-186 empties it
on TestFlight). LMArena publishes the same board in `lmarena-ai/leaderboard-dataset` (the `webdev` config)
under the CC-BY-4.0 grant the engine's other Arena boards use.

**Decision.**
1. `arena_webdev` is declared as an Arena board (`ARENA_BOARDS["webdev"]`, optional as every Arena board is,
   D-121) and is `web-dev`'s primary board, credited as the dataset is.
2. Its thresholds are measured on the board, not carried over: `scripts/calibrate_board.py --config webdev`
   on 2026-10-08 (`docs/research/m21-w1-webdev-calibration.json`): 140 rows, 91 ranked, a close call of 9.3
   Elo and a window of 37.3 Elo (D-148's rules).
3. `web-dev`'s family is `arena_webdev` and `arena_text_coding`. Epoch's copy is one vote with LMArena's
   board, so it stands outside (D-188 clause 1), and stays in D-185's table.

**Consequence.** The first refresh after the release adds the board. Until then the surface has no
evidence on an artifact built by an older release, so the hosted engine is deployed after the owner's Mac
has refreshed once (the deploy's stamp names the release that built the data, #198).

## D-191 — A comparison of model names is general; the wave's three reading rules were taken out after three verdicts

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take
the recommended option, M21's plan approved with M20's), after two review rounds and a Tester
(`docs/reviews/m21-wave-2-review-round-1.md`, `docs/reviews/m21-wave-2-review.md`,
`docs/reviews/m21-wave-2-tester.md`) · **Date:** 2026-10-09 · **Amends** D-187 clause 1 · from #206; #194,
#218 and #222 stay open (M21-W2).

**Context.** On M20-W5's held-out set, 8 of 71 searches fell to "not measured" on a device without
Apple Intelligence, all of them Turkish (#222). A short Turkish question is not confidently Turkish to
the language recogniser, so the English embedding guesses a surface (#218). The fact doubt leaves a
search alone only when it names one of eleven brands, so a search naming another ranked model is asked
about (#194).

**Decision.**
1. **What ships: a comparison of model names is general (#206).** A question made only of ranked
   families' names, their tiers and Turkish particles (`nemotron mu glm mi`) is answered from `everyday`
   by the wording tier itself (`CategoryHints.comparesModelsOnly`).
   - The names are every family the registry names (`registry.family_words`, written to
     `ModelFamilies.swift` and held equal byte for byte), not twelve brands.
   - It is narrow by its shape: every word must be a name, a tier, a particle or one letter, so
     `kimi mi geldi` ("did some come?") is none.
   - The words the router reads hold letters only, so `o3 mü o4 mü` is not read here; it reaches the
     embedding, which is #218's.
2. **Taken out after three verdicts, as M19's image rule was.** Each review found the same class
   again. Each rule is back to its state at `972b55e`, and its issue stays open with the measured state.
   - **#194, a ranked model's name in the fact doubt.**
     - Round 1: a version rule. Its versions spelled with a letter missed Kimi K2, and the words with a
       second meaning (nvidia, o3, glm) were read as models.
     - Round 2: versions only, with no word about cost or making. It read "who makes llama" as a question
       of fact, and missed "llama3" and the Turkish forms.
     - The Tester: an everyday word as a served version ("step 3", "command a").
   - **#218, the Turkish signals before the embedding.**
     - Round 1: a German `ü` and an English "MI" were read as Turkish.
     - Round 2: a capitalised "Kim" or "NE" was read as Turkish, and a particle typed twice counted once.
     - The Tester: one Turkish-only letter sent an English search to "not measured" (an email to
       `Çağla`, a trip from `İzmir`), and an English "mu" typed twice was read as Turkish.
   - **#222, the Turkish general ask.** Taken out at round 2: its task words have a second reading
     (summer, a printer, a student, boots, a model aircraft).

**Measured** (`docs/research/m21-w2-reading-probe.md` §8; the wording tier, counts only):
- At the head, every one of the 78 held-out rows reads as at `972b55e`: 44 right, 8 of 71 searches not
  measured (all Turkish), none given the note. The kept comparison rule moves none of them.
- The model tier was measured only before the reviews (§2).

**Revisit when:** a fresh held-out set (#237) is written, which is where a fourth attempt at #194, #218
or #222 starts, with only words that have one reading; or the owner rules on the four core brands'
second readings (#238).

**Amended by D-196 (2026-10-14)**: the fourth attempt on the fresh set (#237) reads Turkish through the embedding with no word list (#222); #194 is closed on its sign and #238 ruled; #218 stays open.

## D-192 — The close checks read the history, and the records may not say more than a gate holds

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29; the
hook changes it names are the owner's to approve · **Date:** 2026-10-10 · **Amends** D-183 (what a wave
sees before it pushes) · from #200, #201, #202, #203, #183, #182, #179, #181, #248, #249, #122, #189.

**Context.** The M19 and M20 reviews found the same gaps at each closure: an ADR's Amends with no pointer
under the ADR it amends (#200), an ADR first written beside the code it governs (#201), a skipped gate
named only in a close's prose (#202), no process-log entry for a wave (#203), and a HIGH rule that reads
the footprint an author typed instead of the commit range (#183). M21-W3's six review rounds found records
and test names that state a gate's property flatly (#248).

**Decision.**
1. `make check-records` refuses an ADR whose Amends field names a D-ID that carries no `**Amended by` line
   naming it back (#200). The field is read in each spelling the log uses: `**Amends** D-n`,
   `**Amends:** D-n`, a bold run opening `**Amends D-n ...**`, and `**Would amend**`, in any case (the M21-W4
   review's M6, and its second round's M5).
2. `make wave-check` reads the close's commit range from git, for closes dated from 2026-10-10, and for a
   close dated earlier but committed from then (a gate does not invalidate records written before it,
   GPF-001; the review's M3). The range is read as `git diff A...B` reads it, from the merge base of its
   ends, whatever its dots (M4); it ends at HEAD, pinned to the last commit that changes the close (HEAD itself
   while the close has edits not yet committed), and an end the author names is refused (round 2's M4, round 3's M1); it must start at the wave's base or before it (the commit that added the
   previous wave's close, or the milestone's base on main) and hold a commit (M3); a start the history no
   longer holds is read from the merge base the footer records (``merge base `sha` ``), else from the
   wave's base (M4). Then:
   - every path the range changed, both sides of a rename, is held to the plan's security globs (#183);
   - an ADR the range adds first appears in a commit that changes no `src/`, `ios/`, `scripts/`, `.claude/` or
     `.githooks/` file (a hook is code here: round 3's M3),
     after no code commit of the range that cites it, and after no code commit at all unless the plan
     named it before; its heading is read as `## D-n`, `## D-n:` or `## D-n —`, and an ADR the range adds
     with no commit found adding its heading is a problem (#201, M5, round 2's M5);
   - `docs/process-log.md` has a heading naming the wave (`M21-W4`, or a span `M21-W1 to W4`), dated
     inside the range (#203, M5).
   A close is merged when the commit that added it is on main, whatever a later branch edits in it (the
   M21-W4 Tester's M1); a merged close is not
   read again: the rules ran on its branch before the merge. Where there is no history to read (not a git
   checkout, or a shallow clone as CI's test job checks out), or a close is merged, the rules say SKIPPED,
   and `wave-check-all` prints that line on a pass too (M8).
3. `make wave-check` reads row 9's `gates SKIPPED:` list (the label in any case, split on commas outside
   parentheses), every checklist row whose status says SKIPPED or WAIVED, and the field
   `Session started in the repository: yes|no` that the template's row 8 asks for, read from row 8's
   evidence cell only; rows marked N/A count with the skipped and waived ones, each ledgered by the control
   its check cell names (round 3's M2), and the label is read in
   its other spellings (`gates SKIPPED :`, `**SKIPPED**:`, `SKIPPED —`). Each skip, and a `no`, needs a row
   in `docs/control-events.csv` for the wave or its milestone (#202, M7, round 2's M6). Prose about the
   session is not read; from 2026-10-11 a close carries the field.
4. Tests that need git say so with `needs("git")` (#249). CI's test job's facts are read from its workflow
   by a test (#182); the workflow itself is the owner's.
5. The Swift legs run inside the offline profile on macOS (#179), and the model tier's deadline tests run
   once more on a one-thread cooperative pool (#181). Each `swift test` runs under `scripts/watchdog.py`:
   past `SWIFT_TEST_LIMIT` seconds, or on Ctrl-C, it lists the command's descendants, sends SIGINT to each
   of their process groups, then SIGKILL, so a hang fails the leg and leaves no test process behind (the
   review's R1, round 2's M7).
6. A test a gated row cites carries no universal word in its name (`no`, `never`, `any`, `every`,
   `whatever`, `however`, `nothing`) unless a hand-kept list says why the word is no claim; a block of a
   live record, or a docstring of a gate or pin file, that matches a hand-kept list of property phrases
   names the rows that hold it in part. Neither reads `only`, a phrase not on the list, an ADR body or a
   comment. A row's sentences beside its fixed ones are not checked: on the 15 gated rows, the three
   such sentences a universal-word rule would flag were all false alarms (#248).

**Consequence.** CI's shallow checkout cannot run the history rules; the owner's `make check` and the
pre-push gate do. The patch giving CI's test job its history (`fetch-depth: 0`) is posted on #122 for the
owner. The Bash guard's changes (#189) are in their own commits marked OWNER APPROVAL; what its second
reading does not hold is listed by class in its docstring and in G-7. A PreToolUse command hook that times
out does not block (Claude Code's hook docs), so the Bash hook carries `timeout: 30` and
`onFailure: "block"`, and the guard keeps its own bound (5 s, 32 KB).

## D-193 — The owner's ruling on D-185's table: every source served, each publisher credited on a Credits screen

**Status:** accepted -- decided by the owner on 2026-10-12 ("MMLU is settled (HELM Apache plus the arXiv
reports, credited). SWE-bench's CC BY-NC is confirmed; it stays in the free version, credited.
Terminal-Bench: the CSV is TB 2.0, and only 4.0 is Apache in the repo; look at moving to 4.0. ARC-AGI,
DeepSWE, OpenRouter: left out until permission comes. Add each source's licence and link to the Credits
screen"; then "I will get every permission somehow; do not hide any data", and `epoch_webdev` "stays",
owner, translated from Turkish) · **Date:** 2026-10-12 · **Amends** D-185 clause 3 and D-186 clause 3 ·
from #88, #124, #260.

**Context.** D-186 served every source to TestFlight's internal testers and left D-185's table for the
owner to rule on before external testers or the App Store. The licence review
(`docs/research/data-licences-2026-10-04.md`) asked six questions; its sixth was where attribution must
appear. The app showed a board's attribution string only on the combined-list detail screen.

**Decision.**
1. **No source is left out.** `public.LEFT_OUT` stays empty. The owner's second message replaced the first's
   left-out list: ARC-AGI (`epoch_arc_agi`), DeepSWE (`epoch_deepswe_external`) and OpenRouter (`openrouter`)
   are served while the owner gets each publisher's permission.
2. **Per source:**
   - `epoch_mmlu`: settled. Credited to Stanford CRFM's HELM (Apache-2.0) and the model makers' technical
     reports on arXiv, as compiled by Epoch AI.
   - `swebench`: CC BY-NC 4.0, confirmed. It stays while the app is free, credited with its licence.
   - `epoch_terminalbench`: Epoch's copy is Terminal-Bench 2.0. The move to 4.0, whose leaderboard is in an
     Apache-2.0 repository, is studied in `docs/research/terminalbench-4-feasibility-2026-10-12.md`; the
     move itself is the owner's next ruling.
   - `epoch_webdev`: stays.
3. **Attribution is a Credits screen** (the review's question 6). The engine declares one credit per
   publisher (`board_tables.CREDITS`: who, what, the data's link, the licence or terms, and its link) and
   derives a payload's credits from the attributions it owes (`rank.CREDITS_BY_ATTRIBUTION`). A citation
   with no credit is refused. `/v1/boards` carries them as `credits`, an additive key. The app shows them
   from a button at the end of its answers, with the notices CC BY asks for: how the app changes the data
   (each board ranked again among the models it can price, boards combined into its own lists), and that
   the data comes without warranty.
4. **The links are selectable text, not tappable.** D-126's compiled gate (`scripts/client_decl_gate.py`)
   refuses `Link`, `openURL` and a `URL` made from a string in the client. A tappable link would change
   that invariant, which is a ruling of its own.

**The alternatives not taken.** Leaving the three sources out (the owner's first message): it darkens
`abstract` and `agentic-coding` on the hosted engine, which the owner's second message refused. A credits
list typed into the app: a second list beside the engine's attributions, which would drift (AGENTS.md
section 3.5).

**The cost.** The hosted engine serves ARC-AGI, DeepSWE and OpenRouter data before their publishers have
given permission; the screen names their terms. App Review may ask for that permission before external
testers or the App Store (guideline 5.2.2). A paid app ends SWE-bench's place (CC BY-NC).

**Revisit when:** a publisher answers, the app becomes paid, or the owner rules on Terminal-Bench 4.0.

**Amended by D-194 (2026-10-13)**: clauses 1 and 2 -- ARC-AGI, Terminal-Bench and OpenRouter move to their publishers' licensed data instead of waiting for permission; DeepSWE moves when the owner's Hugging Face token is in place (#265).

**Amended by D-197 (2026-10-14)**: each Apache-2.0 or MIT credit carries its copyright notice, and the sheet carries those licences' full texts (#261).

## D-194 — The unlicensed boards and OpenRouter's prices move to their publishers' licensed data

**Status:** accepted -- decided by the owner on 2026-10-13. They first wrote "Terminal-Bench to the TB 4.0
repository rows (Apache); ARC-AGI, DeepSWE, OpenRouter left out, no search for alternatives; do not touch
web-dev (D-190); update D-185's table". Asked how that sat with their ruling of 2026-10-12 ("do not hide
any data"), they chose "move them to the licensed alternatives", and "yes, do it" for the Terminal-Bench
move and the table (owner, translated from Turkish). Revised before merge on 2026-10-13, after each source
was measured: TB 2.0's raw submissions are not read, DeepSWE waits for the owner's token, and ARC-AGI-2 is
derived once at a pinned revision · **Date:** 2026-10-13 · **Amends** D-185 clause 3, D-188 clause 1 (the
families table) and D-193 clauses 1 and 2 · from #265.

**Context.** D-193 served ARC-AGI (`epoch_arc_agi`, ARC Prize's terms bar commercial use), DeepSWE
(`epoch_deepswe_external`, no licence published), Terminal-Bench (`epoch_terminalbench`, Epoch's copy of
TB 2.0, no licence stated) and OpenRouter's prices (`openrouter`, its terms bar use of its data) while the
owner asked each publisher. Each publisher, or the benchmark's maintainer, puts out the same kind of data
under a licence:

| replaced | by | licence | what it holds |
|---|---|---|---|
| `epoch_terminalbench` | `terminalbench_4`: `harbor-framework/terminal-bench`, `leaderboard/submissions/*.json` | Apache-2.0 | TB 4.0's official leaderboard, 21 submissions, live |
| `epoch_arc_agi` | `arc_agi_2`: `arcprize/arc_agi_v2_public_eval` on Hugging Face | MIT | ARC Prize's own runs on the 120 **public** evaluation tasks, each attempt with its answer, most marked `correct` and some settings left unmarked; unchanged since 2026-06-04 |
| `openrouter` | `models_dev`: `models.dev/api.json` (`sst/models.dev`) | MIT | about 8,500 models' prices per million tokens, under each maker and every reseller |
| `epoch_deepswe_external` | (waits) `datacurve/deep-swe-leaderboard` on Hugging Face | CC BY 4.0 | Datacurve's runs, one job of 2026-06-06; gated, approved automatically, read with a Hugging Face token |

Two licensed copies were measured and not taken. TB 2.0's raw submissions
(`harborframework/terminal-bench-2-leaderboard`, Apache-2.0) keep submissions the official board took down
for cheating and trials it rescored to zero (tbench.ai's leaderboard integrity update), so a board rebuilt
from them would serve scores its maintainers withdrew. ARC-AGI-1's public-evaluation runs
(`arcprize/arc_agi_v1_public_eval`, MIT) would cost 15,000 more file reads for a test the 2026 models
have saturated.

**Decision.**
1. **Three sources are replaced now; DeepSWE when the owner's token is in place.** `openrouter`,
   `epoch_terminalbench` and `epoch_arc_agi` are no longer built. `epoch_deepswe_external` stays served
   under D-193, credited, until the owner has accepted Datacurve's dataset terms and given the engine a
   Hugging Face token; the format of a gated dataset cannot be read before then, and `agentic-coding`
   ranks only at `high` effort, which a parser written blind could leave empty. `public.LEFT_OUT` stays
   empty: nothing unlicensed is built that a derivation would have to remove.
2. **Surfaces and families** (D-188 clause 1, amended):
   - `computer-use` ranks on `terminalbench_4`; its family is `terminalbench_4`, `arena_agent`.
   - `abstract` ranks on `arc_agi_2`; its family is `arc_agi_2`, `epoch_chess`, `epoch_mystery`. These are
     public-evaluation scores, higher than arcprize.org's semi-private ones; the benchmark says so in its
     name, "ARC-AGI-2 (public eval)".
   - `agentic-coding`'s family is `epoch_deepswe_external`, `terminalbench_4`, `arena_agent`.
   - `models_dev` is the second price source. Only each model maker's own entry is read: never a
     reseller's, never models.dev's copy of OpenRouter's catalogue, and never another maker's model that
     a maker's catalogue resells (`registry.named_vendors`). Upstage, StepFun and Arcee join the
     registry's vendor routes.
3. **ARC-AGI-2 is derived once and committed.** Scoring every setting reads about 4,300 files, and Hugging
   Face answered 429 past its anonymous rate within a minute, so a nightly read would fail. The dataset
   has not changed since 2026-06-04. `scripts/derive_arc_public_eval.py` scores it at a pinned revision,
   as ARC Prize's own `results.json` does (a pair is solved by either attempt; a task scores its share of
   pairs; a setting scores the sum over the 120 tasks, a missing task as 0, and one that ran fewer than
   114 is left out), into `data/arc-agi-2-public-eval.json`, which the build reads. The contract test
   fails when the dataset moves past that revision. ARC Prize's `correct` mark is kept where it made
   one; an attempt it left unmarked (whole settings, such as GPT-5 Pro and Claude Sonnet 4.5) is scored
   by comparing its answer with the solution of its own pair index in `arcprize/ARC-AGI-2` (Apache-2.0,
   pinned commit `f3283f72`). The comparison agrees with all 16,681 of ARC Prize's marks. ARC Prize last
   changed those solutions on 2025-05-15 (the first test pair of five tasks removed), so a setting with an
   unmarked attempt run before then is left out: GPT-4.1's three. 58 settings are kept. Each setting is
   dated by its latest attempt.
4. **Each moved surface is calibrated on its board** by `scripts/calibrate_surface.py`, on the ranked
   population (D-148 clause 2, M8's two rules): `close_call` is twice the board's own standard error (TB
   4.0 publishes one; ARC-AGI-2's is binomial over its 120 tasks, taken over the models above the floor), and
   `value_window` ends at the middle of the first gap wider than `close_call` that leaves at least three
   candidates, so the window never splits two models the board cannot tell apart. The records are
   `docs/research/d194-computer-use-calibration.json` and `docs/research/d194-abstract-calibration.json`.
5. **Credits:** ARC Prize Foundation (MIT), Terminal-Bench (Apache-2.0) and models.dev (MIT) are credited
   for their own data, with their links (D-193 clause 3).
6. **The move is two-way safe for one release.** The sources D-194 stops building stay attributed and
   credited as D-193 credited them (`board_tables.RETIRED_EXTERNAL_ATTRIBUTION`, the retired credits), so
   an engine of this release boots on an artifact an older release built, and its startup refresh
   (#258) replaces that artifact. The other way does not hold: an older release refuses an artifact this
   one built, so a rollback past this release rebuilds the artifact with the older release's code.
7. **The calls are new external APIs from production code** (`permission-matrix.md` §3, ASK). This ruling
   is the owner's answer; each goes through `app.clients`, with the bounded fetch and a host list.

**The alternatives not taken.** Leaving the three out (the owner's first wording of 2026-10-13): it
darkens `abstract` and `agentic-coding`, which their ruling of 2026-10-12 refused. Waiting for permission
(D-193): the licensed data is already published. Reading ARC-AGI-2 nightly: past the rate limit.

**The cost.** Measured against main's build of the same hour:
- Prices (the branch's last build against `main`'s served artifact of 2026-10-13): 316 models priced,
  against 311. `gpt-3.5-turbo-0613`, `gpt-5.1-codex-max`, `minimax-m1` and `o1-pro` (2025-03-19) lost their
  only price (no maker lists them). 146 models have a second price, against 172. 43 models' blended
  price medians moved more than 20 %, 37 of them up, for two reasons. OpenRouter's half-price `:batch` rows had been linked to
  the base models (65 aliases, 62 models), and leave with it. And an open-weight model's second price is
  now its maker's list price, not the cheapest host's (Qwen's most).
- Budget edges crossed (blended $/1M; `low` is $2, `medium` $8): Claude Opus 5.5 leaves `medium` ($7.40
  to $8.40); GLM-5.1, GLM-5.2, GLM-5.3 and Qwen2.5 VL 72B leave `low`; Mistral Medium (2505) enters it.
- `computer-use` ranks 21 models, all priced, against 42 on TB 2.0.
- `abstract` ranks 24 models, against Epoch's copy's 79.
- DeepSWE's licence stays unsettled until the owner's token is in place.

**Revisit when:** the owner's Hugging Face token is in place (DeepSWE moves), ARC Prize publishes new runs
(re-derive), a publisher changes its licence, or ARC Prize publishes its leaderboard's scores under a
licence.

**Amended by D-216 (2026-10-21)**: clauses 1 and 2 -- DeepSWE moves to Datacurve's own leaderboard, which needs no token (`datacurve_deepswe`), which takes `epoch_deepswe_external`'s place in `agentic-coding`'s family (#265).

## D-195 — D-189 applied to #232's candidates; GPT-5.6's Pro is a mode, not a release

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take
the recommended option; the owner may overrule) · **Date:** 2026-10-13 · **Amends** D-189 clause 1 ·
from #232, #234, #266, #269.

**Context.** D-189 left #232's candidates unsplit because their makers' pages had not been read. #266
asked for GPT-5.6 Sol, Luna and Terra's rules to refuse their Pro variants. #234 found Fireworks' `p`
spellings (`deepseek-v3p1`, `kimi-k2p5`) falling into the major release. The makers' pages were read on
2026-10-13.

**Decision.**
1. **Split, each with its own maker card or announcement:** Kimi K2 Thinking
   (huggingface.co/moonshotai/Kimi-K2-Thinking, its own API id), Kimi K2.7 Code ("a coding-focused
   agentic model built upon Kimi K2.6", its own id), Qwen3-Coder 30B-A3B (its own card and price; the
   bare Qwen3-Coder stays the 480B-A35B flagship its boards rank), Qwen3-Coder-Next (another
   architecture), and DeepSeek V3.1-Terminus, V3.2-Exp and V3.2-Speciale (each announced apart,
   api-docs.deepseek.com/news).
2. **Gathered, as snapshots or modes of one model:** Kimi K2-Instruct-0905 and K2's dated previews
   ("the latest version of Kimi K2"), grok-4-fast's reasoning and non-reasoning modes ("a unified
   architecture"), and Qwen3-Max-Thinking and qwen3.7-max-preview (snapshots in Alibaba's model list).
3. **GPT-5.6's Pro is a mode.** OpenAI's GPT-5.6 guide enables it with `reasoning.mode: "pro"`, says it
   "works with any GPT-5.6 model", and bills it at "the selected model's standard token rates". Unlike
   GPT-5 Pro and GPT-5.4 Pro it has no model id or price of its own, so a Pro run is the model it runs
   and #266's fix is not taken. Its rows hold no effort level the schema holds and stay `unspecified`,
   as #267's ruling keeps ARC-AGI-2's thinking budgets: so GPT-5.6 Sol can stand on a board at its
   Pro-mode row (Epoch's Chess, 64.0 against its max run's 55.0).
4. **A provider's spelling of a point release is that release** (Fireworks' `p`), and **a speed tier's
   price is not its model's.** Moonshot's `-highspeed` and `-turbo`, Fireworks' `-fast` routers, MiniMax's
   `-highspeed` and `-lightning`, and DeepInfra's `-Turbo` serve the model's weights faster at about twice the price. In the
   Kimi and MiniMax families, whose tiers were read, such a price alias is refused for its reason
   (`registry.price_refusal`, counted as `speed-tier`); a score under its name is the model's, as Arena's
   only spelling of Kimi K2 Thinking (`kimi-k2-thinking-turbo`) is. A `fast` or `turbo` in a model's own
   name (Grok 4 Fast) or in a family not read here is untouched.
5. **A model trained apart for one use is its own model** (#269): GPT-5.5-Cyber and GPT-5.6-Cyber, in
   every GPT-5.4 to GPT-5.6 rule's spelling, ("built on
   GPT-5.6 Sol, it is trained to improve capabilities on several specialized cybersecurity tasks", served to
   vetted defenders only) are not GPT-5.5 or GPT-5.6.

**Consequence.** Model ids move on the first night after the release, as D-189's did. Measured on the
artifact of 2026-10-13, every link made again (the backlog-data review's rounds 2 and 3):
- 135 score rows and 45 price aliases leave Kimi K2, Qwen3-Coder and DeepSeek V3, V3.1 and V3.2 for six
  ids new to the artifact (Kimi K2 Thinking, Qwen3-Coder 30B-A3B and Next, DeepSeek V3.1-Terminus, V3.2-Exp
  and V3.2-Speciale) and for Kimi K2.7 Code, which was already served; 3 score rows and 6 aliases reach the
  point release they name; 55 score rows and an alias of K2's dated previews link to K2.
- 13 speed-tier aliases are refused as prices (MiniMax M2.5's `-lightning` among them, which no median
  counted before), and 3 Cyber aliases leave GPT-5.5's and GPT-5.6's medians.
- Every price median that moves: DeepSeek V3 0.56/1.25 to 0.89/1.0, V3.1 0.55/1.65 to 0.58/1.69, V3.2
  0.5/1.5 to 0.53/1.59; Qwen3-Coder 0.712/3.157 to 0.975/4.65 (the 480B-A35B alone); GPT-5.6 4.2/21.0 to
  4.1/20.5; Kimi K2 0.6/2.5 to 0.6/2.4; MiniMax M2.7 0.375/1.5 to 0.299/1.196, M2.5 0.385/1.54 to
  0.305/1.22 and M2.1 0.3/1.32 to 0.315/1.26. Kimi K2.7 Code stays 0.95/4.0.
- Both refresh gates pass from that artifact to the relinked one; the night's largest board change is 6
  of 232 rows.

**Revisit when:** a maker publishes a Pro or speed tier with an id and price of its own, another family's
speed tier is read (GLM's `-Fast`, DeepSeek's `-Turbo`), or a board ranks a gathered snapshot apart in a way
D-182 does not settle.

## D-196 — A Turkish question is read against Turkish examples; #194 and #238 are ruled, not given a fourth rule

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take
the recommended option) and the owner's word of 2026-10-13 to finish the open backlog
(`docs/research/reading-wave-m22-probe.md`) · **Date:** 2026-10-14 · **Amends** D-187 clause 1 and
D-191's "Revisit when" · from #222, #237, #194, #238; #218 and #66 stay open.

**Context.** D-191 sent a fourth attempt at #194, #218 and #222 to a fresh held-out set (#237). An
independent seat wrote it: 147 questions, 89 searches and 58 that are not a search. On it, before this
wave, the wording tier left 8 of 89 searches "not measured". It declines every question the recogniser
is sure is not English, and answers one only from a word that names a surface. Apple's contextual
embedding for Latin script is one multilingual model, the same for English and Turkish, and on the
device.

**Decision.**
1. **A confidently Turkish question that had no answer is read against Turkish examples (#222).**
   - `CategoryHints.examplesTurkish` holds six per surface and `unmeasuredHintsTurkish` the three
     groups, written for this wave, each also read in plain letters. The scoring, the floor and the
     image rule are the English path's.
   - It uses no word list, so D-191's class (a word with a second reading) does not arise.
   - A word that names a surface still decides first (D-187 clause 1), and a question about models in
     general (`generalSurface`) keeps `everyday` (the review's M1). So no question answered before the
     wave changes its surface; one that names its surface now also offers the two closest others, as an
     English one does. Where `everyday` is not served, the embedding answers.
   - A question with a letter Azerbaijani or Turkmen writes and Turkish never does (the schwa, a with
     diaeresis, n with caron, y with acute and z with caron) is not Turkish (the review's M2): the recogniser reads those two languages as Turkish. The
     question is composed first, so a decomposed letter counts; any other letter (a Greek one, an
     accented Latin one) and any mark keep it Turkish (rounds 2 and 3). An emoji is still embedded with
     the question and can move its surface. Azerbaijani or Turkmen written without such a letter is
     still read as Turkish. Every other language the recogniser is sure of still declines.
   - The English path is unchanged, except that every example's vector is now computed once per
     language and kept (the review's K2).
2. **#194 is closed without a fourth rule.** Its sign was "more than 4 of 40 genuine searches asked".
   On the fresh set the model tier asked 1 and 3 of 89 searches, and the wording tier none. Three
   verdicts found a second reading in every list of model names tried (D-191 clause 2).
3. **#238: claude, gemini, mistral and grok stay read as models wherever they stand.** In an app whose
   every question is about models, "how much does claude cost" is the common reading. A question of
   fact about Monet or the zodiac given a ranking is the cost, and is accepted. `AMBIGUOUS_FAMILY_WORDS`,
   which the issue names, went out with D-191's rules: nothing reads these four as ambiguous today.
4. **The held-out leak gate reads escapes.** A Turkish line in an ASCII-only test is written with
   `\u{...}` in Swift or `\uXXXX`/`\xXX` in Python. The gate compared the raw text, so an escaped
   held-out question passed it. It now decodes them first (Swift's one to eight digits, Python's `\U`
   and `\N{}` too) and compares each side in plain letters as well (the review's N4), which also finds
   a letter composed or decomposed; planted tests hold the escapes, the plain letters and the dotless i
   (the Tester's M9). A question split across two string literals is still not found.
5. **#237's set is live and `wording_heldout_m20_questions.json` is retired** (`RETIRED_HELD_OUT`).

**Measured** (the wording tier, two runs each, counts only):
- **Held-out set, after the review's fixes:** 88 right of 147 before, 91 after. Searches right went
  from 59 to 62 of 89, and searches not measured from 8 to 0. Lines that are not a search caught stay
  at 29 of 58. Against the first head, before M1's rule (65), 4 searches are lost and 1 gained: three
  of the 4 are answered `everyday` again, as before the wave, and the fourth, "not measured" before
  the wave, now reads another surface.
- **Question by question:** 3 rows gained and none lost.
- **The wave's own 61 Turkish searches:** 31 right before and 44 after; typed in plain letters, 29 and
  39.
- **The cost:** 10 Turkish lines that are not a search, which the reading does not catch, fell to "not
  measured" before. They get a ranking now. The reading catches less in Turkish than in English (the
  review's N5); catching them is #66's.
- **A floor does not separate them:** on the wave's own sentences, Turkish searches scored 0.18 to 0.51
  and Turkish lines that are not a search 0.24 to 0.56, as in English at M16-W1. That run was measured
  once and not kept; no committed run carries a score (the Tester's M9).

**Revisit when:**
- #218's short Turkish questions are read by a means with no second reading, measured on a set fresher
  than `reading_heldout_m22`, which this wave and its reviews have run at least eight times on the wording tier;
- #66's bars are met;
- or the owner asks for another language to be read.

## D-197 — The app carries the Apache-2.0 and MIT texts, and each publisher's notice

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take the
recommended option) · **Date:** 2026-10-14 · **Amends** D-193 (the Credits screen) · from #261.

**Context.** The Credits screen (#260, D-193) names each publisher's licence and links to it. Apache-2.0
section 4(a) asks a redistributor to give recipients a copy of the licence, and 4(c) to keep the copyright
notices; MIT asks that the copyright and permission notice be included. That covers Aider, Terminal-Bench,
HELM and the ARC-AGI-2 tasks and solutions the app scores the runs against (Apache-2.0, D-194 clause 3),
and LiteLLM, models.dev and the ARC Prize evaluation runs (MIT). Whether serving
positions and medians derived from their files is a redistribution was left open
(`docs/research/data-licences-2026-10-04.md`, rows 9 and 10). #261 offered an owner's ruling that it is
not, or carrying the texts.

**Decision.**
1. **The texts are carried, rather than ruled away.** It costs one sheet section, and holds under either
   reading of "redistribution".
2. **The engine sends each credit's notice** (`Credit.notice`): the copyright line the publisher's LICENSE
   file states, read on 2026-10-14. A publisher whose file states none is named in `PUBLISHES_NO_NOTICE`
   with why (Aider's and Terminal-Bench's appendix templates are unfilled; the ARC Prize runs' dataset holds
   no LICENSE file). The ARC-AGI-2 solutions are credited on their own (`arc_prize_solutions`), with the
   line their repository's LICENSE states at the pinned commit (the backlog-gates review round 1's N2). No publisher
   here has a NOTICE file. An older engine sends none, and the phone reads it.
3. **The app carries the full text of each licence** (`LicenceText`) and shows it once, under "Licence
   texts", for each licence the served credits name. A test holds each text against the published one, by
   hash, word for word, read as the build compiles it and once (the backlog-gates review round 1's N1).
4. **The Apache text's two addresses are text on the screen, never opened** (D-126): the egress pin
   permits each exactly once, in `Models.swift`.

**Revisit when:** a publisher adds a NOTICE file or a copyright line, a new Apache-2.0 or MIT source is
credited, or the owner rules that derived positions are not a redistribution.

## D-198 — The gates read what the backlog waves left them blind to: escapes, docs, raw pins, a rebound read and the decision's order

**Status:** accepted -- the agent's ruling under the owner's standing instruction of 2026-09-29 (take the
recommended option) · **Date:** 2026-10-14 · from #271, #272, #274, #275, #276.

**Context.** The reading wave and the gates wave (#277) filed five gaps in the gates themselves, each found
by a review or a Tester and each a place where a check passes because it does not look:
- L1 reads raw characters, so Turkish written with `\u` escapes passes it (#271);
- the held-out leak check reads no record in `docs/` (#272);
- the order "decision before code" (D-192 clause 2) is read only for a milestone wave's close (#274);
- pin files other than two read the app's Swift raw (#275);
- a URL rebound between a store's `isFileURL` guard and its one read passes every gate (#276).

**Decision.**
1. **L1 decodes escapes before it reads** (#271): a JSON string's `\uXXXX` in a `.json` file, and Swift's
   `\u{...}` in a `.swift` file. An escaped Turkish line then needs the same reasoned `.language-allow`
   entry a raw one does. The probe sets and tests that hold Turkish by design get entries that say so.
2. **The leak check reads `docs/**/*.md` too** (#272). A match in a record first committed before the set
   was is not a leak, since the record cannot have read the set; it is the set's overlap with published
   text, and the test holds those overlaps by file and count, so the next set's seat sees them. A match in
   any later record fails, as in the code. The check still reports by file and length only. A record is
   read with its whitespace collapsed and a backtick read as a quote, since Markdown wraps lines and quotes
   in backticks (the first review's M3).
3. **A backlog wave's decision comes before its code** (#274). When a branch's range from its merge base
   with `origin/main` adds no milestone close, each ADR it adds must first appear in a commit that changes
   no code, test or build file (`BACKLOG_CODE`), and after no code commit of the range that cites it; a finding names
   the range it read. Where `origin/main` is not in the history (a shallow clone), the check says it
   skipped. CI's test job checks out one commit, so in CI it says so on every PR until the owner's
   workflow sets `fetch-depth: 0` (#278); it holds on the owner's Mac, where `check-fast` runs it.
4. **Every pin file reads the app's Swift as the build compiles it** (#275): through `_code`, which drops
   comments of both kinds and a literally false branch, or `_swift` where a pin cuts a line at its `//`
   and says so (`# keeps //:`), or with a `# raw:` reason on the line. The guard sees a read that names the iOS folder or a constant
   bound to it; a read through a function's parameter it cannot see (the first review's N1). One guard reads every pin file under `tests/unit/`, and its line
   check is a helper tested on planted lines.
5. **A store's guard and its read are one expression** (#276). The egress pin permits
   `guard url.isFileURL,` and the `Data(contentsOf: url)` after it only as one exact expression in each
   store, so a clause between them fails it. A Swift test loads the on-device store under the offline
   tripwire. G-13 says what stays #242's: the compiled gate does not record which call made a URL.

**Revisit when:** #242 moves the compiled rules to allowlists, #243 runs the compiled gate in CI, or a
review finds a check here passing on something it does not read.

## D-199 — The project runs on DevFlow v7.1, in heavy mode, with both deploy commands gated

**Status:** accepted -- the owner asked for the upgrade (2026-10-14, translated from Turkish: *"we have
reached DevFlow 7.1, we will upgrade our flow for it"*) and chose in session (2026-10-15): merge the Bash
guard, heavy mode, gate both deploy commands · **Date:** 2026-10-15 · **Amends:** D-161, D-172.

**Context.** DevFlow moved from v6.6 to v7.1 through v6.7 and v7.0:
- a SessionStart marker and `make session-check`;
- two working modes, with the reviews computed by `make review-need`, and the Tester once per milestone in heavy mode;
- a deploy gate and `make deploy-check`;
- the Bash guard as a pinned file;
- a ledger whose row kinds come from a legend;
- the brief's version checked (`V1`) and the process log's session numbers (`S1`).

The project had grown its own copy of several of these: a pinned guard file (M21), project kinds in the
control-events ledger (`ruling`, `within-scope`), and inline code spans read as notation (W-015).
`git diff v6.6 v7.1` was applied three-way, with `.github/workflows/` left out.

**Decision.**
1. **Heavy mode** (`Working mode: heavy` in the brief). A wave gets the Code-Reviewer. The Tester runs once per
   milestone, on the plan's last wave (`docs/reviews/m{N}-tester.md`), not per wave as D-172 said; waves
   closed before this keep their per-wave Testers. `Paths that make a change HIGH:` is `none`, so the
   security seat stays at each milestone's closure and on the release (D-172), except where
   `make review-need` flags a sensitive name or a new parser.
2. **The deploy gate guards `fly deploy` and `scripts/deploy_hosted_engine.sh`.** Each is refused until
   `docs/reviews/release-security.md` and the milestone Tester's verdict name a reviewed head with no code
   changed after it. This is stricter than D-185 in one place: the script's `--dry-run` is refused too while
   the verdicts are stale. QA verification is off; no runtime config file sits outside git.
3. **One guard, merged.** v7.1's `.claude/hooks/bash_guard.py` is the base. The project's M21 rules it lacked
   are carried in it, held by `tests/unit/test_bash_guard_bounds.py`:
   - D-185's refusal of `fly`/`flyctl` other than read-only subcommands, and of the deploy script without
     `--dry-run`;
   - the refusal of writes into any work tree's `.claude/` and `.githooks/`, now run by the Write/Edit hook
     too (`--write`);
   - `-t` read only for cp, mv, ln and install;
   - `python -I -S` for every hook.

   Taken from v7.1 by design: `rm -rf` passes only on scratch (the temp directory, a `mktemp` result,
   `.claude/worktrees/<name>`), resolved from every directory the command can run in. The deadline is 10 s.
   `make guard-pin` writes the pin into both hooks. G-7 and INV-82 say so.
4. **The ledger takes v7.1's kinds.** Rows of kind `ruling` and `within-scope`, and waves written `m<N>` or
   `m<N>-closure`, were rewritten in place, each marked `[rewritten at the DevFlow v7.1 upgrade, D-199: ...]`:
   - an owner's ruling became a `review` row citing R-1, or this decision for `repository-hooks`, whose fix
     is v7.1's session marker;
   - a `within-scope` row became a `review` row citing R-1;
   - a milestone-wide wave became the milestone's last wave.

   A wave close's skip may be ledgered under any wave of its milestone, since v7.1 has no milestone-only
   wave shape (`scripts/wave_check.py::skip_ledger_problems`).
5. **What stays the project's own:**
   - `make closes` stays out of `make check` (D-161). M1-M15's closure reports, the early wave closes, and
     the release of 2026-10-07, which had per-wave Testers and no milestone Tester, fail today's rules;
     `wave-check-all` grades the closes.
   - W-015 stays: inline code spans are notation to `make bootstrap-check`. `conformance/test-placeholder-allow.py`
     writes its notation outside backticks.
   - `conformance/test-process-version.py` grades, in an installation, only the files the manifest ships.
     The project's records keep the version they were written under.
   - The optional §2a of `AGENTS.md` (two agent tools) is left out, since only one tool works here.
6. **The upgrade session cannot pass `make session-check`**, since the hook did not exist when it began, and
   records no skip for it. The owner commits and pushes the upgrade from a terminal, and the first session
   started in the repository after the merge passes it. The `ci.yml` half of v6.7 (a `python` container,
   the gitleaks binary, `DEVFLOW_RUNNER`) is the owner's, with #278.

**Revisit when:** DevFlow ships the next version, the owner changes the working mode, or a release needs
the milestone Tester that `make deploy-check` now asks for.

**Amended by D-200 (2026-10-15)**: clause 4 -- a `review` row citing a decision resets the three-row count, by the owner's choice; a skip row covers its own wave only, and a row for another wave of the milestone counts only when the upgrade moved it there from a milestone-only id.

**Amended by D-201 (2026-10-16)**: clause 1 -- the project runs in light mode.

**Amended by D-205 (2026-10-17)**: the project runs on DevFlow v7.1.2, in light mode; the guard is v7.1.2's file with the project's rules ported onto it.

## D-200 — The three-row count takes v7.1's reset, and one wave's skip row covers that wave only

**Status:** accepted -- the owner's choices of 2026-10-15, in session, on the v7.1 upgrade review
(`docs/reviews/devflow-v7.1-upgrade-review.md`), translated from Turkish: BLOCKING-1 *"accept the v7.1
meaning"*, MAJOR-1 *"exact matching for new closes"* · **Date:** 2026-10-15 · **Amends:** D-199.

**Context.** The upgrade's Code-Reviewer found that the ledger merge (D-199 clause 4) changed two rules
the project had held since the M21 fixes review:
- On `main`, only the owner's `ruling` reset a control's three-row count, and an in-scope event reset
  nothing. In v7.1 a `review` row whose reason cites a `D-`, `P-` or `R-<n>` resets it
  (`scripts/wave_check.py`, `ledger_findings`). The rows rewritten from `within-scope`, and the `review`
  row a docs-only commit now needs, are such rows. Nothing checks that the cited decision exists.
- A skip row for any wave of a milestone covered every other wave of it, so three skipped waves needed
  one row and the three-row rule could not fire.

**Decision.**
1. **The reset is v7.1's.** A `review` row citing a decision resets its control's count, as v7.1 ships it;
   the owner's ruling of 2026-10-10 that only the owner's ruling resets a count is replaced. The rewritten
   rows stay as they are. The cost is accepted: one `review` row citing any id clears a struck control, and
   only a reader of `docs/control-events.csv` sees it.
2. **One wave's skip row covers that wave only.** A row for another wave of the same milestone counts only
   when it carries the upgrade's marker for a milestone-only id (``[rewritten at the DevFlow v7.1 upgrade,
   D-199: wave was `m<N>` ``), which is what such a row covered on `main`. Held by
   `tests/unit/test_wave_check_m21_rules.py::test_a_row_for_another_wave_of_the_milestone_does_not_count`.

**Rationale.** Keeping v7.1's reset unforked lets the next upgrade apply the ledger rules without a
merge; the per-wave widening was the project's own reading, and it cost the three-row rule its signal.

**Mitigation if violated.** A control bypassed again and again is never put under review: the ledger
would show a run of bypasses, each followed by a `review` row that addresses something else.

**Revisit when:** a struck control is cleared by a `review` row whose cited decision does not exist or
does not address it, or DevFlow answers the field finding that a resetting `review` row should cite a
decision that exists.

## D-201 — The project runs in light mode

**Status:** proposed
**Owner ruling:** 2026-10-16, in chat, for run product-night
**Date:** 2026-10-16 · **Amends:** D-199 (clause 1).

**Decision:** `Working mode: light` in `docs/project-brief.md`. Work goes issue by issue (`/fix-issue`, `/work-enhancement`), each a red test, the change, `make gate` and one draft PR. No Code-Reviewer runs per change. The Security-Reviewer runs when `make review-need` says so and before every deploy. The milestone Tester runs once before a release, on everything merged since its last verdict (`docs/reviews/release-tester.md`).

**Rationale:** The owner asked (translated from Turkish) for the run to put "less process, more product" first: ranking the right models for the right question, in an app the owner can test on the phone. Heavy mode's per-wave review rounds took two days on one upgrade.

**Mitigation if violated:** A change lands with no independent code review. The red-to-green test per change, `make gate`, the security seat where the signals point, and the Tester before release are what hold it.

**Revisit when:** a light-mode change reaches the owner broken in a way a code review would have caught, or the owner turns heavy mode back on.

**Status:** accepted -- 2026-10-17, the owner merged the plan PR #290 (run product-night)

## D-202 — The product run: the right models for the right question, on the owner's iPhone

**Status:** proposed
**Owner ruling:** 2026-10-16, in chat, for run product-night
**Date:** 2026-10-16

**Decision:** The owner's answers (translated from Turkish):
1. **Scope:** ranking correctness, non-English questions (#218, #273), input that is not a model search (#66), and an app that works on the phone. All four are in the run.
2. **What "right" means:** each question in a golden set expects a surface and a top 3, both derived from the measurements on the published boards. The agent drafts 30 to 50 questions, and the owner corrects them in the morning. A question whose answer is not settled is marked `disputed`, and the tests put no hard expectation on it.
3. **Test path:** the owner installs from Xcode on their own iPhone.

Defaults the agent took, because the owner was asleep (run rule: an unanswered question takes its default, written down):
4. A build running on a physical device with no local engine override talks to the hosted engine, not to loopback, which a phone can never reach.
5. When the engine cannot be reached, the app shows the last answer it received for that question's surface, kept in Caches and dated, instead of the failure sentence. Nothing is bundled as fixture data, as REQ-APP-001 requires.
6. A new reading rule (#218, #273, #66) is measured on a fresh held-out set written by an independent seat, as D-191 and D-196 require. A rule that does not beat the shipped one on that set is not shipped; the measurement is recorded instead.
7. Nothing deploys and nothing is uploaded to TestFlight in the run.

**Rationale:** The owner wants to pick up the app in the morning and judge its rankings on the phone. The golden set makes "right" checkable at all; until now nothing tested a real question against a top N.

**Mitigation if violated:** If the golden expectations are wrong, the tests hold the wrong answer in place. The owner's morning review of the set, and the `disputed` mark, are the guard against that.

**Revisit when:** the owner corrects the golden set, or a fresh held-out measurement shows a shipped rule is worse than the one before it.

**Amended by D-204 (2026-10-17)**: clause 6 -- the owner ships #273, #218 and #301 although each scored the same as the shipped rule on the fresh set.

**Status:** accepted -- 2026-10-17, the owner merged the plan PR #290 (run product-night)

**Amended by D-206 (2026-10-17)**: clause 6 -- a reading rule ships when it turns no fresh held-out row from right to wrong and fixes the golden question it was written for.

## D-203 — The wording tier holds small talk, text with no meaning and a dictated answer (#66)

**Status:** proposed -- the agent's, in run product-night under D-202 clause 6, for the owner's review
**Date:** 2026-10-16 · **Amends:** D-169 (clause 3).

**Decision:** On a device without Apple Intelligence, the wording tier holds three more kinds of input as not a search, so the screen shows the owner's guiding note (D-169 clause 4) or asks back, instead of a ranking:
1. small talk: greetings and how-are-you lines, in English and Turkish;
2. text with no meaning: placeholder Latin, or one word repeated three or more times;
3. a dictated answer: "write nothing else" and its Turkish form count as an order to the app.

The on-device model's schema, `RoutingOutcome` and every gate are unchanged.

**Rationale:** On the fresh held-out set `reading_heldout_m23` (168 rows, written by an independent seat the implementer never saw; `docs/research/reading-wave-m23-probe.md`), the rule catches 11 of 72 non-searches against the shipped 10. It keeps 65 of 96 searches right, and holds or asks no real search. No language group loses a search. It meets D-202 clause 6's bar. On the tuning sets it catches 36 of 50 against 29.

**Mitigation if violated:** A real model search phrased like small talk gets the note instead of a ranking. "Change" on the screen still lets the reader pick a surface. The fresh set had no such case.

**Revisit when:** a genuine search is reported held, or the next fresh set shows the gain does not carry. The margin was one row, in English only. 61 of 72 non-searches are still ranked on the wording tier, so D-169 clause 6's 80 % bar stays the on-device model's.

**Status:** accepted -- 2026-10-17, approved by the owner (D-204 clause 3) and merged in #291

## D-204 — The owner's answers to run product-night's stops and open questions

**Status:** proposed
**Owner ruling:** 2026-10-17, in chat, for run product-night
**Date:** 2026-10-17 · **Amends:** D-202 (clause 6, for #273, #218 and #301 only).

**Decision:** The owner's answers (translated from Turkish):
1. **#298 (#273) and #299 (#218) ship.** On the fresh held-out set they scored the same as the shipped rule, which D-202 clause 6 alone would hold back. The owner ships them anyway: neither loses a search, and #273 turns 5 confident readings in other languages into "not measured".
2. **#303 (#301) ships.** `quantum` and `kuantum` are expert words. The rule moves 1 of 1247 probe questions from wrong to right and loses none, and every earlier independent held-out set labels quantum questions `expert`.
3. **D-203 is approved** as written. It is accepted when this ADR is.
4. **Light mode decides this stack's reviews** (D-201). #288, #66 and #289 merge with the security verdicts they have and no Code-Reviewer. #290 is merged before #291 (the integration delta review's M1).
5. **The golden snapshot stays in the repository** with its CC-BY-NC-4.0 SWE-bench data. It is a test-target fixture only, it carries its attribution, and the engine already serves the same data on `/v1`.
6. **The guard fixes wait for DevFlow 7.1.2.** #282–#287 and v7.1.1's remaining guard fixes are taken after that upgrade, as one small PR that the owner applies.

The three PRs are stacked on the integration PR (#291), so the owner merges #281, #290 and #291 only.

**Rationale:** The owner wants the app in hand. A rule that loses nothing on the fresh set and is right on the older sets is worth more shipped than parked.

**Mitigation if violated:** If a shipped rule turns out worse, the next fresh held-out set shows it, and D-202's "Revisit when" reopens it.

**Revisit when:** the next fresh held-out set is written, or DevFlow 7.1.2 lands.

**Status:** accepted -- 2026-10-17, the owner's ruling, merged in #291

## D-205 — The project runs on DevFlow v7.1.2, in light mode

**Status:** proposed -- the owner asked for the upgrade on 2026-10-17 (translated from Turkish: *"take 7.1.2 from DevFlow and finish the upgrade; we will go on in light mode"*)
**Date:** 2026-10-17 · **Amends:** D-199.

**Context.** DevFlow moved from v7.1 to v7.1.2 through v7.1.1. Both are patches: no record changes shape and no stage changes. Most of the difference is the Bash guard. v7.1.1 follows `cd`, refuses more ways of skipping a hook, and treats `$TMPDIR` as scratch only when it is set. v7.1.2 refuses `rm -r` and `mv` of a work tree or of `.git`, git aliases to writing commands, code-running config keys, and a deploy declared in another repository. The deploy gate goes to `JUDGE_PROTOCOL = 2`. Two of v7.1.1's conformance fixes were already taken in #281 (`ab8686f`). Nothing in `.github/workflows/` changed.

**Decision.**
1. **Light mode stays** (D-201). v7.1.2 moves heavy mode's security review to the milestone's end; light mode is unchanged apart from the guard.
2. **`git diff v7.1 v7.1.2` is applied three-way.** `.github/workflows/` is left out, since it did not change. `.claude/` and `.githooks/` are left out of the agent's apply, because they are the owner's to write (AGENTS.md §5). The agent prepares that half as one patch, and the owner applies it, re-pins the guard (`make guard-pin`) and commits.
3. **The guard is v7.1.2's file, with the project's rules ported onto it**: the M21 bounds that D-199 clause 3 carried, and the two owner patches of #281 (`b4dc1f3`, `b39bbe8`). `tests/unit/test_bash_guard_bounds.py` holds them. Each of #282–#287 is closed where v7.1.2 or the port covers it, with the test that shows it, and kept open where it does not.

**Rationale:** The owner wants the guard fixes taken from DevFlow rather than written by hand (D-204 clause 6), and v7.1.2 is the version that carries them.

**Mitigation if violated:** If a project rule is lost in the port, a command the project refused passes again. The bounds test and `conformance/test-bash-guard.py` both run against the new file before the owner pins it.

**Revisit when:** the next DevFlow release, or a guard finding that v7.1.2 does not cover.

**Amended by D-207 (2026-10-17)**: the project runs on DevFlow v7.2, the stable release, in light mode.

## D-206 — Run golden-night: what it does, and when a reading rule ships

**Status:** proposed
**Owner ruling:** 2026-10-17, in chat, for run golden-night
**Date:** 2026-10-17 · **Amends:** D-202 (clause 6).

**Decision:** The owner's answers (translated from Turkish):
1. **Reading rules (#293, #295, #292).** Before any rule is written, an independent seat writes one fresh held-out set, m24. The designs are the agent's defaults:
   - #293: more example sentences first.
   - #295: the general "yapay zeka" rule gives way when another surface's example scores confidently.
   - #292: an agent with its own coding verb reads as agentic coding.
2. **When a reading rule ships (amends D-202 clause 6).** A rule goes into the integration PR when two things hold: it turns no row of the fresh held-out set from right to wrong, and it fixes the golden question it was written for. Beating the shipped rule on the fresh set is not required. This is D-204's ruling, made general.
3. **#294 is `disputed`.** "is it true that we only use 10 percent of our brain" fits `factuality` and `expert` alike. The golden set marks it disputed with that reason, and #294 closes.
4. **#297 is approved, gate change included.** `scripts/client_decl_gate.py` limits `StandingsStore.keep` to the load path, and INV-73 is reworded for the hosted engine. It gets a security review.
5. **#304: the gate is fixed.** L1 in `scripts/check_records.py` skips what git ignores and does not track, and the `ios/.build/` entry leaves `.language-allow`.
6. **#255: an advisory make target.** It lists every issue a range's commit messages would close. It is not a leg of `make check`. Wiring it into `/pre-merge` is a skill patch for the owner.
7. **#279: the additive form.** An `XCTestObservation` is registered beside the `tearDown` check, and no invariant test changes.
8. **#265 is skipped tonight.** The licensed dataset needs the owner's Hugging Face token.
9. **Owner-only files, prepared as one patch.** The agent prepares the changes to `.claude/`, `.githooks/` and `.github/workflows/` as one owner patch, and the owner applies it in the morning with one line. It covers #252, #254, #278 with #122, #283, #284, #305, and the guard holes #285–#287 that D-204 clause 6 sends after the v7.1.2 upgrade. A guard change in it passes a security review before it is handed over.
10. **The run ends with the release reviews.** The milestone Tester (`docs/reviews/release-tester.md`) and the release security review (`docs/reviews/release-security.md`) run on the integration head, so `make deploy-check` can be green. Nothing deploys.

**Rationale:** The owner wants the misses the golden set found fixed, and the process items cleared in one morning merge, with nothing that only the owner can do left half-done.

**Mitigation if violated:** A rule that holds the fresh set level but is wrong on questions nobody wrote yet ships. The next fresh set and the golden set are where that shows.

**Revisit when:** a shipped rule loses a row on a later fresh set, or the owner corrects the golden set.

## D-207 — The project runs on DevFlow v7.2, the stable release, in light mode

**Status:** proposed -- the owner asked for it on 2026-10-17 (translated from Turkish: *"upgrade to the DevFlow 7.2 stable version first, then we look at the work"*)
**Date:** 2026-10-17 · **Amends:** D-205.

**Context.** v7.2 is a whole-process audit. No record changes shape. It changes these:
- the post-edit hook runs in the edited file's work tree, and only the records leg after a document edit;
- the gate stamp (`make gate-ok`);
- a PowerShell guard;
- in light mode, a change goes to the Security-Reviewer only when it touches the brief's declared HIGH paths;
- the ledger's legend moves into `docs/warnings.ledger.md`;
- the brief gains `Rollback command:`;
- `ci.yml` drops `make falsify`, and `issue-agent.yml` runs only when started by hand;
- an ADR is accepted when the PR carrying it merges.

**Decision.**
1. **Light mode stays** (D-201). The project's `Paths that make a change HIGH:` is `none`, so under v7.2 a light change goes to no per-change security review. Its signals are read at the release review, which this project runs before every deploy (the deploy gate).
2. **`git diff v7.1.2 v7.2` is applied three-way on top of run golden-night's integration branch.** The owner's files (`.claude/`, `.githooks/`, `.github/workflows/`) are left out. Run golden-night's owner bundle (D-206 clause 9) is folded into one owner patch with v7.2's changes to those files, so the owner applies one line, not two. The bundle's agent half is on this branch as `9575aef`.
3. **The project's own rules are kept where v7.2 meets them.**
   - **`deps`** still audits every lock under `requirements/` (D-177), and is not cached: v7.2's `net_cache.py` hashes no lock file.
   - **The deploy gate** reads the brief's policy at the protected base (#283), and a milestone security verdict stands for the release only when neither the base's nor the tree's brief says light.
   - **`make closes`** stays out of `make check` (D-161, D-199).
   - **`.path-refs-allow`** keeps its exact rows (D-155); it does not take back v7.2's `docs/plans/*` and `docs/reviews/*` wildcards.
   - **The closure checklist** keeps PASS or MINOR.
   - **The wave checklist's row 8** keeps `Session started in the repository:` (#202).
   - **`docs/security-invariants.md`** is the project's register, and v7.2's empty template is not taken.
   - **D-178** moves with the QA section into `.agents/rules/issues-qa.md`.
4. **`schemas/record.schema.json` and `scripts/gen_schema.py` stay.** v7.2 removed them, but the project changed both, and `scripts/check_records.py` reads the schema. **`docs/feature-catalog.md` stays too**: v7.2 removes it, and `tests/unit/test_security_invariants.py` reads it among the live records; a change to that test is the owner's (AGENTS.md, Escalate NOW).
5. **The brief's `Rollback command:` is `none`.** The owner rolls a failed deploy back by hand.
6. **ADRs.** Every ADR on `main` that still says `proposed` now reads as accepted, by v7.2's rule. Each one listed in the upgrade PR is in force, so none is superseded.

**Rationale:** The owner asked for the stable release. v7.2 also removes the night run's main friction: the post-edit hook ran every agent's edit in the project tree.

**Mitigation if violated:** If a project rule was lost in the merge, a gate gets looser. The upgrade's security review compares the result with v7.1.2's port.

**Revisit when:** the next DevFlow release.

## D-209 — Run bug-night: what it does, and the owner's answers

**Status:** proposed
**Owner ruling:** 2026-10-17, in chat, for run bug-night
**Date:** 2026-10-17 · **Amends:** none.

#295's ruling is its own ADR, on #333, which this run stacks first.

**Context.** The owner opened a light run for the night (translated from Turkish: *"triage what is untriaged, take in as much as one night can run, bugs first, plan it all up front, ask me the questions, then go on without stopping until morning"*). The answers below were given through the chat's choice picker.

**Decision.**
1. **The queue, in order:** #333 (#295) and #329 (#326) are stacked first. Then the bugs by severity: #331; the guard bugs #256, #287 and #305; then #332, #325, #330 and #328. Then the enhancements: the guard's #317, #318 and #320 with the workflow's #81; then #314, #322, #319 and #309.
2. **One owner bundle.** The changes to `.claude/`, `.githooks/` and `.github/workflows/` (#256, #287, #305, #317, #318, #320, #81) are prepared as one owner patch, as D-206 clause 9 did. Its guard changes **pass a security review before handover** (the owner's answer: yes).
3. **#332: `.mcp.json` stays removed.** Every GitHub step runs through `gh`, and an MCP tool has no guard hook here. The staged restore in the upgrade worktree was dropped.
4. **#331:** the agent runs `make install` once in the main clone, and checks the main clone for any other state left from before v7.2 (the owner's answer: *"if anything is left over from before, update it, of course"*, translated).
5. **#325, #319 and #322:** approved as gate changes. #325 grades no gitignored document; #319 derives `POLICY_SCRIPTS` instead of keeping it by hand; #322 closes the kept-answer rule's gaps.
6. **#314:** the app refuses an answers file over 8 MiB before reading it; the client gate's sink allowance changes with it.
7. **#323 is declined:** `answers.json` keeps the platform's default protection. The issue closes with this ruling.
8. **#309:** the network observer covers the whole test invocation, set-up and tear-down included, in one place.
9. **#115 and #243 close.** #115: a device build talks to the hosted engine, so the local-network prompt shows only with an override. #243: a macOS CI runner costs about ten times a Linux one, and the pre-push gate runs the compiled client gate on the owner's Mac.
10. **Not tonight:** #242 (several slices and an ADR first), #265 (needs the owner's Hugging Face token), #190 (a GitHub ruleset, the owner's setting).

**Rationale:** Bugs first, as the owner asked. Every reserved decision was answered before the run, so nothing waits on the owner overnight except the owner-only files.

**Mitigation if violated:** A guard change handed over without its review could open a hole that nothing reports; the bundle is not handed over until the review passes.

**Revisit when:** the owner's morning review.

## D-208 — #295: a verb clause right before "yapay zeka" names the question's task

**Status:** proposed
**Owner ruling:** 2026-10-17, in chat (option (a) of run golden-night's stop row for #295).
**Date:** 2026-10-17 · **Amends:** none.

**Context.** #222's general-words rule keeps a confident Turkish question that says "yapay zeka" on `everyday` before its examples are compared, so a question that names its task in words no rule lists (the golden question `tarayıcımda benim yerime alışveriş yapacak bir yapay zeka var mı`, *(translated: is there an AI that will shop for me in my browser)*, expected `computer-use`) gets the general list. Four attempts in run golden-night could not fix it without sending general questions off `everyday` (D-206).

**Decision.**
1. **A grammar rule:** in a Turkish question, a verb clause that ends right before "yapay zeka" (a participle such as `yapacak`, `yazan`, `kullanan`) names a task, and the general-words rule does not hold the question on `everyday`; the question is then read by its examples as any other.
2. **Measured as D-202 clause 6 as amended by D-206:** on a fresh held-out set written by an independent seat, it ships when it turns no row from right to wrong and fixes the golden question.

**Rationale:** The owner chose the rule that reads the question's own grammar over shipping attempt 3 (about one general question in six leaving `everyday`) or leaving it to the on-device model, which older phones do not have.

**Mitigation if violated:** A general question with a descriptive clause (`en çok kullanılan yapay zeka`, *(translated: the most used AI)*) would leave `everyday`; the fresh set's general rows catch it.

**Revisit when:** the fresh measurement fails the bar, or the on-device model tier is on every supported phone.

---

## D-210 — The Golden Rules: the product's backbone, as the owner set them

**Status:** proposed
**Owner ruling:** 2026-10-19, in chat ("these are the backbone of this project ... write them down somewhere very important, in golden letters, under the name Golden Rules; stop working on empty tasks, these are our goals" *(translated)*)

**Context.** After run bug-night the owner was shown where the product stands against its goals. Their reply set the goals as the project's backbone: what the owner expects from the app is that it can use every source's data, understand what the user wants through Apple Intelligence (or another LLM when it is not there), and show the most correct list, building one itself with an LLM when needed *(translated)*.

**Decision.** The Golden Rules. They outrank every other priority. `AGENTS.md` carries them at the top, so every session reads them.

1. **Every source's data, used lawfully.** Each board and price source is either under an open licence or used with its publisher's written permission. Before v1, no source stays unlicensed.
2. **Understand the question with an AI model, always.** Apple Intelligence reads every question whenever the device has it. Where it does not, another LLM reads it. Matching words alone is a fallback for when no model answers. It is never the plan.
3. **The most correct list for every question.** The answer is the list from our boards that fits the question. When no board ranks what was asked, the app composes the list itself with an LLM, from the boards' data, and shows it.
4. **No empty work.** Every task serves rules 1-3 or the v1 order below. Anything else waits, and the agent says so instead of doing it.

**The v1 order** (the owner's): (1) every open issue closed, no code work left; (2) permission from every source; (3) Apple Intelligence used fully and (4) the question understood fully, worked together; (5) routing to the right lists; (6) composing a list no board ranks, last.

**The owner's answers (2026-10-19, in chat, before this ADR merged):**
- **Rule 2 and D-160.** "I said 'if needed': Apple Intelligence must be used in every case" *(translated)*. Apple Intelligence reads every question on every device that has it, and the work goes there first. Another LLM is only the fallback for a device without it. Where that fallback runs (on the phone, which keeps D-160 clause 1, or hosted, which would supersede it) is decided by its own ADR when it is built.
- **Rule 3 and D-104.** Agreed: "it will produce or interpret from our lists, of course it will not make something up on its own" *(translated)*. The LLM chooses and combines boards and facets. Every model, position and number it shows comes from a board. D-104 stands.

**Rationale.** The owner's own statement of what the product is for. The roadmap had drifted to guard and process work while understanding stood at 83/173 on the fresh set (D-206) and accuracy on the Apple Intelligence tier had never been measured.

**Mitigation if violated:** A plan, wave or issue that serves none of rules 1-3 or the v1 order is challenged at triage. An app that answers from word matching while the device has Apple Intelligence is a defect against rule 2.

**Revisit when:** v1 ships, or the owner changes the goals.

**Amended by D-215 (2026-10-21)**: rule 1 is widened to attributed public numbers whose terms do not forbid non-commercial use (#376).

---

## D-211 — The task itself and a question of fact get the note, on the golden set too

**Status:** proposed
**Owner ruling:** 2026-10-19, in chat, on #351

**Context.** #351 measured Apple Intelligence for the first time (`make model-tier`). The two sets it scores by disagreed on one class of input. The m24 set, written by an independent seat, labels the task itself ("write me a haiku", "solve 2x+5=11") and a question of fact ("the population of Ankara") `NOT_A_SEARCH`, as D-169 clause 1 does. The golden set (D-202 clause 2) labelled the same kinds of rows as searches of their surface ("summarise my lease for me", "how many people are in this group picture"). The model's instructions (`ModelRouter`) follow neither: they call "explain quantum entanglement" a model search. Asked which way, with examples, the owner chose the note for both classes.

**Decision.**
1. **D-169 clause 1 stands, as written.** The task itself, addressed to the app, and a question of fact or knowledge get the guiding note, not a ranking. So do instructions to the app, small talk and nonsense. A person describing what they need a model for is a search, even when the task's content is pasted in.
2. **The golden set says so.** A row of either class carries `not_a_search`, naming its class ("the task itself" or "a question of fact"). Its `expected_surface` stays, as the surface the wording tier gives it: without the model the wording tier does not decide this (D-169 clause 3), and `GoldenQuestionTests` keeps checking it there. `make model-tier` scores such a row as `NOT_A_SEARCH`.
3. **The model's instructions follow clause 1.** Each change is measured twice on m24 and the golden set (#351 phase 2), and judged on m25 against #351's bar.

**Rationale.** The owner's ruling, the same as D-169's. A ranking answers a person choosing a model. The person who asks the app to do a task, or asks it a fact, is not choosing one, and the note tells them what the app is for.

**Mitigation if violated:** If a genuine search gets the note, the reader has to tap "Change" (D-169 clause 4 cost). D-169 clause 6's bar (at most 2 genuine searches per run) and #351's bar (85% of searches) catch it on m25.

**Revisit when:** readers on TestFlight type tasks and leave on the note, or the owner asks for lists on tasks.

---

## D-212 — Run night-351's rulings: #348's smoke, #353's example pool, m25, and one integration PR

**Status:** proposed
**Owner ruling:** 2026-10-19, in chat, for run night-351

**Context.** The owner opened run night-351 to carry #351 (Apple Intelligence reads every question) on through the night, with #348 and the issues filed for #351's rest: #353 (retrieved examples), #354 (prewarm) and #355 (m25). The run's decisions message asked four questions, and the owner took the recommended answer to each. Earlier the same day the owner ruled on m25's size and bar after reading the three research reports.

**Decision.**
1. **#348.** When the real-data recommend smoke finds no eligible model, it says which source came back short, so an upstream blip and a defect can be told apart. The engine's answer is not re-checked against the snapshot.
2. **#353's example pool.** The older probe sets are relabelled to D-169 and D-211 (the task itself and a question of fact are not searches) by an independent seat that reads no routing code, and the run's author checks where the two disagree. m24, the golden set and m25 never enter the pool.
3. **m25 (#355).** An independent seat writes it tonight, about 300 searches and about 200 non-searches, without seeing the model tier's instructions, hints or tuning sets. It stays out of the repository, sealed by its sha256, and judges once, on macOS 27, recording the OS build and the model variant. #351's bar is met on the observed rates; the Wilson interval is reported beside them.
4. **One integration PR.** The run's work, #352 included, stacks on `integration/run-night-351`, merged with a merge commit.

**Rationale.** The owner's answers. A blip should not read as a defect (1). Examples labelled to an old line teach the model that line (2). 173 rows tell apart only about 8 points, and the non-search side needs 170-350 rows to show 80% at all (3).

**Mitigation if violated:** A pool row from m24, golden or m25, or a near-duplicate of one, inflates every score it touches: the pool is checked against them before any run. An m25 read or tuned on before it judges is no longer held out, and a new set is written.

**Revisit when:** m25 has judged, or the owner changes the bar.

---

## D-213 — The model names the kind of a non-search, in its verdict field

**Status:** proposed
**Owner ruling:** 2026-10-19, in chat, on #351 ("yes, add the kinds", with INV-69's tests changed and an ADR before the code *(translated)*)
**Amends** D-169 as amended at M18-W3 (clause 2: the closed yes/no field) and INV-69's closed set.

**Context.** The owner's three research reports agreed that a small model under-chooses a catch-all answer such as "something else", and that named, positively described non-search kinds catch more. On 2026-09-28 (#66, variant 4) five named kinds had caught 25 of 39 non-searches but cut 45 of 89 searches, under the line D-211 has since moved. Measured again on 2026-10-19 with greedy decoding (#351 phase 2), three layouts against the committed state, on m24 and the golden set, question by question:
- the verdict field kept last, its two values replaced by "model search" and five kinds: m24 133 → 139 of 173; not a search caught 43 → 51 of 61 (8 fixed, 0 broken, exact McNemar p = 0.008; the task itself 9 → 13 of 13); searches 90 → 88 of 112 (2 fixed, 4 broken, p = 0.69, surface moves); the golden set 37 → 39 of 49;
- the kinds beside the surfaces in the surface field, the verdict kept: m24 +1, golden -4;
- the kinds in the surface field alone, no verdict field: m24 -22, golden -17.

**Decision.**
1. **The verdict field names the kind.** It stays a closed field generated last (D-169 as amended, the M18-W3 order). Its values are `model search` and five kinds, each with its meaning in the model's instructions: `task itself`, `fact question`, `app question`, `small talk`, `instruction attempt`. The first words differ, so no value is a prefix of another.
2. **Only `ModelOutputBoundary` maps them.** Each kind is the model's "not a search", with D-169's reading rules unchanged: alone it is a doubt, with a doubt in code it is the note. `model search`, no value, or a value outside the set reads as a search, as before. A kind never becomes an engine id or a surface.
3. **INV-69 holds the wider set.** Its tests assert the six values exactly, and that the schema offers nothing else.

**Rationale.** The gap to the owner's bar was non-searches, and this closes it on m24 (84% against 80%) with no non-search broken. The search loss is within the run's guardrail (at most 2) and not significant; m25 judges both.

**Mitigation if violated:** A sixth value, or a free one, would let the model say something the boundary does not map: the schema test fails. If m25 shows searches lost to the kinds, the kinds' meanings are narrowed, or this ADR is superseded.

**Revisit when:** m25 judges (#355), or a new on-device model (OS 27) is measured.

---

## D-214 — Run night-1021's rulings: #242's allowlists never loosen, and m25 judges last and closes on its bar

**Status:** proposed
**Owner ruling:** 2026-10-21, in chat, for run night-1021

**Context.** On 2026-10-20 the owner re-assessed the open queue against the Golden Rules (D-210) after the macOS 27 upgrade: four issues closed, #242 kept at the end of the queue, #265 waits on a new Hugging Face token, and the eight guard issues wait on the owner's bundle. #361 merged in #366. The owner then opened a night run over what the agent can work, with m25 (#355) last. The run's decisions message asked two questions, and the owner took the recommended answer to each.

**Decision.**
1. **#242 runs tonight, under one rule: no loosening.** The compiled client gate's deny-lists (sinks, served numbers, the request surface, the by-name set, the stores' URLs: #242's triage, five slices) become allowlists. Every input the gate refuses today is still refused (a test holds the fixture's refusals before against after), and every twin #242 names is refused. An allowlist entry for the app's own code names its reason. The Security-Reviewer reviews the change, whatever `make review-need` says. A slice not finished by morning stays a stop for the owner, never a weaker rule.
2. **m25 judges last, once,** on the run's final integration head: the model tier, greedy, recording the OS build and `SystemLanguageModel.default.variant`. #351's bar (D-212 clause 3): at least 80% of searches and 80% of non-searches read right, on the observed rates, with the Wilson interval beside them. Met → #351 and #355 close with the result. Not met → the result is recorded, both stay open, and nothing is tuned on m25's rows.

**Rationale.** The owner's answers. A gate that guards D-160 must not be weakened to be rewritten (1). m25 is held out once, so it judges the build that ships, and what it shows is final for this round (2).

**Mitigation if violated:** An allowlist that refuses less than the deny-list did would open a hole the reviews already closed: the before/after test fails. Tuning on m25 would spend the held-out set: a new one is written.

**Revisit when:** m25 has judged, or the next review plants a twin that the allowlists pass.

---

## D-215 — The owner's licence rule: attributed public numbers, for a free and non-commercial app

**Status:** proposed
**Owner ruling:** 2026-10-21, in issue #376 (the six-item licence list raised the same day *(translated)*)
**Amends** D-101, D-185 and D-210 · from #376.

**Context.** D-101 made provenance mandatory and admitted only documented, licensed endpoints. D-185 clause 3 kept a table of sources whose terms did not clearly permit a public app, and the Golden Rules (D-210, rule 1) ask that every source be "under an open licence or used with its publisher's written permission". On 2026-10-21 six sources were still open against that rule: DeepSWE, Epoch's WebDev copy, MMLU/HELM, SWE-bench (CC BY-NC), LiteLLM's copies of OpenRouter's prices, and the vendor subscription plans. The owner ruled on all six in #376's body.

**Decision.**
1. **The rule.** The app is free and non-commercial. A public leaderboard's numbers may be served when its publisher is named with a link on the Credits screen (D-185, D-193) and the publisher's terms do not forbid non-commercial use. A code licence on a publisher's repository (MIT, Apache-2.0) is not the licence of its leaderboard's numbers. A board whose publisher states no data licence is served under this rule, with its attribution.
2. **Golden Rule 1 is widened** (D-210): "open licence or the publisher's written permission" now also admits attributed public numbers whose terms do not forbid non-commercial use. `AGENTS.md` carries the widened text.
3. **Item by item:**
   - **DeepSWE** (`datacurve/deep-swe-leaderboard`, CC BY 4.0, gated): unchanged, stays on #265 until the owner's Hugging Face token is in place.
   - **`epoch_webdev`** (Epoch's copy of LMArena's WebDev board): removed as a duplicate of `arena_webdev`, which `web-dev` reads since D-190 (#185). It is no longer declared or built, so `/v1/boards` stops publishing it: a public-contract change this ADR covers. Its attribution and its `arena_site` credit stay as a retired source's, as `epoch_arc_agi`'s do (D-194), so an engine still boots on an artifact an older release built.
   - **MMLU/HELM** (`epoch_mmlu`): kept, served with its attribution. Its publisher names no data licence and no contact; no email is sent.
   - **SWE-bench** (CC BY-NC 4.0): kept. Non-commercial use is what its licence allows while the app is free. **Before the app ever takes payment, an email to SWE-bench's maintainers is owed**; that condition lives here, not in code.
   - **LiteLLM's `openrouter/` price copies**: removed as stale. Prices come from models.dev since D-194 (#268). The LiteLLM ingest drops them, and the public artifact drops any an older built artifact still holds. The `openrouter` retired attribution and credit stay, for that older artifact.
   - **Subscription plans**: out of scope for this ruling; the Perplexity plan rows stay owed before any public release.
4. **Nothing else leaves the catalogue.** The owner wants the board list as rich as possible: only duplicates and stale copies go.

**Rationale.** The owner's ruling. The app charges nothing and names every publisher with a link, which is what a public leaderboard's terms ask where they ask anything. Treating a repository's code licence as the licence of its numbers would claim a grant nobody made; treating silence as a ban would empty boards the owner wants served.

**Mitigation if violated:** A board served without its credit, or one whose terms forbid non-commercial use, breaks rule 1 as widened here: `credits_for` refuses a served citation with no credit, and a publisher whose terms forbid it is taken out by its own ADR. The app taking payment before SWE-bench's maintainers are written to breaks clause 3; D-185's revisit trigger (a paid launch) holds as well.

**Revisit when:** the app takes payment (SWE-bench's email, and every board's terms read again for commercial use), a publisher's terms change, or a served publisher objects.

**Amended by D-216 (2026-10-21)**: clause 3's DeepSWE item is carried out -- `agentic-coding` ranks on Datacurve's own leaderboard (`datacurve_deepswe`), public numbers attributed under this rule, and Epoch's copy is retired (#265).

---

## D-216 — `agentic-coding` ranks on Datacurve's own DeepSWE leaderboard

**Status:** proposed. Revised twice before merge on 2026-10-21, on the owner's rulings below: the first text read only the Hugging Face dataset, whose one job is of 2026-06-06; the second read the site's leaderboard with that dataset as a fallback.
**Owner ruling:** 2026-10-21, on #265: the owner accepted the dataset's terms, put a read token on the Mac, and told us to work the move now (the re-triage of 2026-10-21 pinned its scope). Shown that the dataset is four months behind Epoch's copy, the owner chose Datacurve's own data and added "but let's keep ourselves up to date; there is a ready list, why aren't we updating?" Then, of the fallback: "The engine already updates every day. Let it update daily; if the site goes down, the previous day's data is used. We set that up long ago." *(both translated)*
**Amends** D-194 clauses 1 and 2 (DeepSWE waited for the token; `agentic-coding`'s family), D-188 clause 1's families table, and D-185 clause 3's table. Carries out D-215 clause 3's DeepSWE item, which stayed on #265 until the token was in place.

**Context.** D-194 moved three unlicensed boards to their publishers' licensed data and kept Epoch's copy of DeepSWE
(`epoch_deepswe_external`, no licence published) until the owner's Hugging Face token was in place, because Datacurve's
dataset (`datacurve/deep-swe-leaderboard`, CC BY 4.0) is gated. Read on 2026-10-21, Datacurve publishes DeepSWE three ways:
- **The site's leaderboard** (`https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`, the JSON the site
  itself loads): DeepSWE v1.1, compiled 2026-09-22, newest job 2026-09-01, 70 configurations over 28 models, each with
  its harness, its stated `reasoning_effort` (one row states none), Pass@1 and a 95% run-to-run interval. It is the list
  Epoch's copy was taken from. The site says "© 2026 Datacurve", publishes no licence and no terms page (404), and its
  robots file allows every agent but the AI-training crawlers. No token is needed.
- **The Hugging Face dataset**: CC BY 4.0, gated. One branch, last changed 2026-06-09, one job directory
  (`20260606-deep-swe-leaderboard-all-4x`, DeepSWE v1.0), 27 runs over 19 models. Its result file names an effort only
  for a model run at several; its config file states one for four of the runs the keys leave without one.
- **The GitHub repository** (`datacurve-ai/deep-swe`, Apache-2.0): the 113 tasks, no scores.

**Decision.**
1. **`agentic-coding` ranks on `datacurve_deepswe`,** a declared remote source in `app.clients.datacurve` that reads the
   site's leaderboard, and nothing else. Benchmark `DeepSWE`, metric `% resolved`, harness as each row names it
   (`mini-swe-agent` in all of them). `epoch_deepswe_external` is no longer built; its family entry becomes
   `datacurve_deepswe`, `terminalbench_4`, `arena_agent`.
2. **The leaderboard is used under D-215:** public numbers, attributed to Datacurve with a link on the Credits screen,
   from a publisher whose terms do not forbid it.
3. **Effort, under D-194 clause 1's rule (the surface ranks at `high`).** A row keeps the effort the leaderboard states,
   so no `xhigh`, `max` or `medium` run is ranked as a `high` one. A row that states none ran at its model's default
   setting and stands at `high`, the level the leaderboard itself gives Gemini 3.1 Pro's default run. A row whose effort
   is outside the schema is skipped and counted.
4. **Dates.** A leaderboard row is undated: the list gathers jobs of several dates and names none per row, and the
   newest job's date would make older rows look fresh.
5. **No token.** The leaderboard is public. The dataset, which needs the owner's Hugging Face token, is not read, so the
   engine holds no token and no test needs one.
6. **A failed night is carried.** The source is optional (D-121), and the nightly refresh's carry-forward (D-156) keeps
   the previous night's rows when the site fails, as it does for every source; past the carry window, or on a first
   build with nothing to carry, the build exits 3 and `agentic-coding` says it has no evidence. It never serves an empty
   board, and it never fails another source's night.
7. **Calibration** follows D-194 clause 4 on the ranked population, with Datacurve's own standard error: its published
   95% run-to-run interval per row, halved by 1.96, median over the rows. The record is a JSON file under
   `docs/research/`; the note is under `docs/reviews/`.
8. **Credits:** Datacurve, for its leaderboard (public numbers, attributed; no licence published), with its link.
   Epoch's copy stays attributed and credited as D-193 credited it, as a retired source (D-194 clause 6), so an artifact
   an older release built still boots.
9. **The call is a new external API from production code** (`permission-matrix.md` §3, ASK). The owner's ruling on #265
   is the answer; the fetch goes through `app.clients` with the bounded fetch, limited to the site's host.

**Rationale.** Golden Rule 1 (D-210, as D-215 widened it) and the owner's rulings: Datacurve's own data, kept up to
date by the daily refresh, with the previous night's rows on a night the site does not answer.

**The alternatives not taken.** The dataset alone (this ADR's first text): four months behind the site, 19 models
against 28, and a secret on the Mac. The dataset as a fallback (its second text): on a night the site failed it would
have replaced the previous night's v1.1 rows with the June job of v1.0, older data than carry-forward keeps, for a
token the engine would otherwise not need. Epoch's copy: the same numbers, compiled by someone else, with no licence.

**As built (2026-10-21).** The leaderboard's 70 rows (28 models) all link a catalogue model and carry a price, with
no alias added; 19 models rank at `high`. Calibrated on it (`docs/reviews/issue-265-agentic-coding-calibration.md`):
floor 67.0 with five models above it, `close_call` 2.6 (twice the median published run-to-run error, 1.313),
`value_window` 3.0. Rounding the window to the half point had put it at 2.5, below its close call;
`scripts/calibrate_surface.py` now takes the half point above in that case.

**The cost.** The leaderboard publishes no licence: if Datacurve objects to this use, the licensed alternative is its
CC BY 4.0 dataset, which needs the owner's token and is months behind. The evidence is undated, as Epoch's copy was.

**Mitigation if violated:** A stated effort ranked as `high` would put an `xhigh` run in a `high` comparison: the
parser's tests hold each row's effort. A site that answers with something other than the board, or redirects off its
host, is a failed night, carried like any other: the client's tests hold both.

**Revisit when:** Datacurve publishes a licence or terms for its leaderboard, moves it to a new version (`v1.2`), or
objects to this use; or the default runs need a label of their own.

## D-217 — The hosted engine is refreshed and deployed each night by a GitHub Actions workflow, not from the Mac

**Status:** proposed. Revised once before merge on 2026-10-21, on the Security-Reviewer's round 1 (`docs/reviews/fix-issue-387-security.md`): the token became an environment's secret only `main` reaches (B1), starting the workflow by hand became a deploy command (M1), and clauses 2, 3 and the revisit say what the review found (M3, M4, R2, R4).
**Owner ruling:** 2026-10-21, in chat, on #387: "The engine has to be deployed somewhere; it cannot keep running on my Mac" *(translated)*. Asked three questions, the owner chose a scheduled GitHub Actions job, the previous night's artifact kept as an Actions artifact, and the deploy gate run every night with a stale gate skipping the deploy.
**Amends** D-116 clause 2, D-185 clauses 2 and 5, and answers D-154's revisit.

**Context.** `model-ranking.fly.dev` serves TestFlight from the artifact baked into its image (D-185 clause 2). The
refresh runs only in the Mac's launchd service (D-154, D-170), and Fly changes only when the owner runs
`scripts/deploy_hosted_engine.sh`, so the app's data goes stale when the Mac is off or nobody deploys. D-116 clause 2
keeps ingestion off the serving host so the network-fetching code, and the untrusted-producer boundary W-005 guards,
stay off the public surface. No source's permission is tied to the Mac, and the refresh reads no token (D-215, D-216).
The refresh's carry-forward (D-156) reads the live artifact and its `.refresh.json` record, which today exist only on
the Mac.

**Decision.**
1. **A scheduled workflow, `nightly-hosted.yml`, refreshes and deploys the hosted engine** once a night (and on
   `workflow_dispatch`). Ingestion runs on a GitHub-hosted runner: neither the serving host nor the Mac. The serving
   image is unchanged: it still carries no client, refresh or ingest dependency.
2. **Two jobs, and only the second holds a secret.** `refresh` holds none: its checkout keeps no credential, the
   `GITHUB_TOKEN` it reads the previous state with reaches only that step, and it is read-only (`contents: read`,
   `actions: read`). It fetches the sources, parses them, and builds the artifact. `deploy` holds the owner's
   deploy-scoped `FLY_API_TOKEN`; it never fetches a source, it receives `refresh`'s artifact, derives the public copy
   (`app.workflows.public`) and deploys. The code that parses fetched data never runs beside the token; the deploy
   still opens the refresh's SQLite output and record beside it (queued, #389). The token is the secret of the
   `fly-production` environment, which the owner limits to `main`, never a repository secret, and both jobs run only
   on `main`: a run dispatched on another branch reaches no token.
3. **The previous night's artifact and its record are an Actions artifact,** `hosted-state`, uploaded by `refresh`
   after a night that published or kept its data (exit 0 or 1), and downloaded by the next night as the live artifact
   carry-forward reads. Retention is 90 days, three times D-156's 30-day carry window. It is read only from this
   workflow file's own runs, started by the schedule or by hand in this repository, whose commit is on `main`: a pull
   request's run, a fork's included, can upload an artifact of the same name. The repository is public, so any
   signed-in GitHub user can download the state: it is the full artifact, which is safe only while the public copy
   leaves nothing out (`LEFT_OUT` empty, D-186, D-193), and a test fails the day a source goes into it. A failed night (2, 3 or 4)
   uploads nothing, so the last good state stands. With no state (the first night, or 90 days without a good night),
   the night is a first publish: a required source that fails it fails the night, and nothing deploys.
4. **The deploy gate runs every night, first.** `deploy` runs `scripts/deploy_gate.py --check`; while the release
   security review or the Tester has not seen every code change on `main`, the night deploys nothing and the job
   fails, naming the stale verdict, so the owner hears of it. The workflow and its script are code, so their own
   merge makes the gate stale until `/going-live`'s delta review: nothing deploys before that review.
5. **A night deploys only what is new.** The build stamp (`release-<sha>-data-<digest>-from-<sha>`) is compared with
   `/health`'s; when Fly already serves it, nothing is deployed. Data another release built is refused as the deploy
   script refuses it today; the workflow never sets `DEPLOY_ACCEPT_DATA_FROM`.
6. **`scripts/nightly_hosted.sh` and `gh workflow run nightly-hosted.yml` are deploy commands** in the brief, beside
   `fly deploy` and the deploy script, so the Bash guard judges an agent that runs them as it judges them. The
   `dispatches` API and other spellings of a dispatch are not judged yet (#390).
7. **The workflow is the owner's to apply** (`.github/workflows/**`): the agent commits the proposal at
   `scripts/ci/nightly-hosted.yml`, a test holds its shape and, once the owner copies it, that the installed workflow is
   the proposal. The owner creates the token (`fly tokens create deploy`) and the repository secret.
8. **The Mac keeps its own nightly refresh** for the engine it serves; it no longer feeds the hosted engine, and the
   owner's manual deploy stays available.

**Rationale.** The owner's ruling, and Golden Rule 3: the list is only as correct as the data is fresh. A runner keeps
ingestion off the public surface, which is D-116 clause 2's reason, and the two-job split keeps the one secret away
from the parsers. The Actions artifact needs no new store or secret. The gate every night keeps D-199's rule that
unreviewed code never ships.

**Mitigation if violated:** a token beside the parsers is one parser bug from a hostile deploy; a night deploying
without the gate ships unreviewed code; an upload after a failed night replaces the last good state with a broken one,
and carry-forward then loses every source.

**The alternatives not taken.** A second, private Fly machine that ingests and hands the artifact over: storage the
two machines share, or a deploy from inside Fly. A refresh inside the serving machine: it reverses D-116 clause 2.
A GitHub release asset for the state: as public as the Actions artifact, and permanent, for a file only the next
night needs, where the artifact expires. A data-only deploy
without the gate: unreviewed code would ship with it.

**The cost.** A red scheduled run every night between a code merge and its delta review. GitHub may delay a scheduled
run, and shared runner addresses may meet anonymous rate limits (Hugging Face, GitHub's API) or a 403 (epoch.ai,
D-158); each is a failed source, carried. A night whose data is unchanged after a reviewed code merge keeps the older
release's name on its data and is refused until a night changes it.

**Revisit when:** the runner's nights fail more often than the Mac's, a source's terms forbid automated fetching
from a data centre, Fly's deploy token scope changes, a source goes into `LEFT_OUT` (the public state would then
publish it), the repository goes private (the deploy's anonymous `git fetch` then needs a credential), or the app
moves to a public release (then the state's retention and the deploy cadence are read again).

**Amended before merge (2026-10-21, #389, run queue-1021)**: clause 2's queued item is done -- the `refresh` job, which holds no secret, also derives the public copy and its stamp (`scripts/nightly_hosted.sh prepare`, `hosted-public`); the `deploy` job installs no package and opens no database: `scripts/deploy_hosted_engine.sh --ship` reads the copy only for its digest, checks it against the stamp (this commit, the stamp writer's word that this release built the data, the copy's digest), and ships it. The stamp proves the copy and the stamp agree, not where they came from: the night trusts the refresh job that wrote both, as it did before. Steps of one job share a disk, so the split is by job, not by step.

## D-218 — Run queue-1021's rulings: the media surfaces on quality, new surfaces for new boards, #371's rule, and the first release's name

**Status:** proposed
**Owner ruling:** 2026-10-21, in chat, for run queue-1021

**Context.** The owner opened a run over the whole open queue before the first release (`docs/plans/run-queue-1021.md`). The release and the deploys follow the merge, under `/going-live`. #387's ruling is D-217, on #388's branch, which this run stacks. The run's decisions message asked four questions, and listed four defaults that the owner did not change. The licence rule needs no new question: D-215 is applied board by board.

**Decision.**
1. **#378: LMArena's five image and video boards open as surfaces ranked on quality only.** The boards are `image_edit`, `text_to_image`, `image_to_video`, `text_to_video` and `video_edit` (the owner's ruling of 2026-10-21 on #378, option 1). Each has no price column, no value window and no `budget` filter, and the app's detail screen says the price is not measured. A request to make an image or a video routes to its surface instead of declining, which reverses the decline hint of #113 and #192. A price in each surface's own unit is its own issue. The four `*_style_control` configs are skipped as duplicates.
2. **#379: METR's time-horizon board opens a new surface, long tasks,** with its own Turkish title, router hint, probes and D-148 calibration. It is not a second board in `agentic-coding`.
3. **#379: a board that fits no surface opens one,** with a Turkish title, a router hint, at least one probe and a D-148 calibration. This holds only when D-215 admits the board and it ranks at least 15 models (D-145). Video-MME, GDPval and Vending-Bench 2 are the likely cases. A board D-215 does not clearly admit is skipped, with the reason recorded. So is one behind a sign-in, a token or a click-through (the nightly refresh holds no secret), one that lives only in a paper's tables, and one that ranks fewer than 15 models.
4. **#371 (b): a comparison with a served number is refused inside a closure that counts or searches,** that is the closures given to `filter`, `first`, `firstIndex`, `lastIndex`, `last`, `count(where:)`, `contains(where:)`, `allSatisfy`, `drop(while:)`, `prefix(while:)` and `reduce`, since their result can be a new number. A comparison in `if`, `guard`, `switch`, a sort, or `min`/`max(by:)` stays admitted. Clause (a) refuses a served number passed into a generic parameter constrained to a numeric protocol. Nothing pinned before is lost (D-214 clause 1).
5. **The first release is `v1.0.0-beta.1`:** the app on TestFlight's internal testing. The public release takes `v1.0.0`.
6. **The defaults the owner left standing:**
   - #389 splits the deploy in two. A step with no token derives the public copy and reads the record. The token's step ships only the derived file, after checking its digest.
   - #390's guard half and #392's `ci.yml` change are owner bundles. The agent writes each patch and its tests, the Security-Reviewer reviews it, and the owner applies it after the run.
   - A new TestFlight build follows the release, because the app changes (#378, #371).
   - A question the run meets that is reversible and outside a ⛔ zone takes its most conservative answer in `docs/plans/assumptions-queue-1021.md`.

**Rationale.** The owner's answers. The more boards and surfaces, the more questions get a correct list (Golden Rule 3), within D-215's lawful-use rule (Golden Rule 1). Clause 4 refuses the shapes that rebuild a number, and keeps the comparisons a screen needs.

**Mitigation if violated:**
- A media surface given a per-token price would rank on a number that does not measure it.
- A new surface without probes routes nobody to it.
- A looser #371 rule lets the app show a number no board published (D-104).

**Revisit when:**
- a per-unit price source for images or video is settled (clause 1);
- a new surface's board drops below 15 models (clauses 2 and 3);
- the public release is cut (clause 5).

---

## D-219 — #379's new boards, read under D-215: four served, six skipped, each for its reason

**Status:** proposed
**Amends** D-185 clause 3's table (the licence record) and D-188 clause 1's families table · from #379.

**Context.** #379 asked for ten more boards, each licence-checked and then served or skipped with its reason:
OSWorld-Verified, METR's time horizons, Humanity's Last Exam and DeepResearch Bench first, then SciCode, LiveBench,
SimpleBench, Vending-Bench 2, Video-MME and GDPval. The licence rule is D-215's, applied board by board, and needs no
new owner ruling. This ADR carries out the run's ruling for #379: D-218 clause 2 opens a `long-tasks` surface for METR, and clause 3 opens a surface for a board that
fits none, when D-215 admits it and it ranks at least 15 models. A board D-215 does not clearly admit is skipped, and
so is one behind a sign-in, a token or a click-through, one that lives only in a paper's tables, and one that ranks
fewer than 15 models. A board under half linked to the catalogue is not served until its aliases are fixed.

**Decision.**
1. **The licence record, read on 2026-10-22,** board by board. "Linked" counts the board's names that reconcile to a
   catalogue model against a copy of the Mac's artifact (`registry.reconcile`), before any alias was added.

   | board | publisher | licence or terms | link | read | verdict |
   |---|---|---|---|---|---|
   | OSWorld-Verified | XLANG Lab (the OSWorld team) | the site is "licensed under a Creative Commons Attribution-ShareAlike 4.0 International License"; the results workbook is served from the site, which moved from `os-world.github.io` (now a plain-HTTP redirect) to its own host | https://osworld-v1.xlang.ai/ | 2026-10-22 | **served**, `osworld_verified`: 20 general models at 100 steps, 15 linked |
   | OSWorld 2.0 | XLANG Lab | the repository is Apache-2.0; `official-results.json` is public | https://osworld-v2.xlang.ai/ | 2026-10-22 | **skipped**: 11 models on its 55 rows, fewer than 15; OSWorld-Verified stands in for the benchmark until it ranks 15 |
   | METR time horizons (TH 1.1) | METR | no licence and no terms published (`metr.org/terms` answers 404); the page offers its raw data for download; robots allow it; the analysis repository names no licence | https://metr.org/time-horizons/ | 2026-10-22 | **served**, `metr_time_horizons`: 26 models, 20 linked |
   | Humanity's Last Exam | Center for AI Safety and Scale AI | lastexam.ai's own table ranks 10 models; Scale's terms (2021-08-25) limit use of its site "for your own internal purposes"; CAIS's terms (2023-03-13) admit not-for-profit reuse, but its dashboard publishes the scores only inside its compiled app code, at an address that changes with each deploy; the questions' dataset is gated | https://lastexam.ai/ | 2026-10-22 | **skipped**: the publisher's own table ranks fewer than 15 models, Scale's terms do not clearly admit the use, and CAIS publishes no file the nightly refresh can read |
   | DeepResearch Bench | its authors (USTC), on the `muset-ai/DeepResearch-Bench-Leaderboard` Space | the Space is tagged Apache-2.0 (its code); `data/leaderboard.csv` is public | https://huggingface.co/spaces/muset-ai/DeepResearch-Bench-Leaderboard | 2026-10-22 | **skipped**: 8 of 45 entries link, under half; the entries are research products, not catalogue models, so no alias can fix it |
   | SciCode | the SciCode team | the repository is Apache-2.0 (its code); the leaderboard is a table on its page only | https://scicode-bench.github.io/leaderboard/ | 2026-10-22 | **skipped**: 10 of 20 rows link, 8 distinct models, fewer than 15 ranked; its newest model is o3-mini (January 2025) |
   | LiveBench 2.0 | LiveBench (Abacus.AI and its co-authors) | no data licence published; the code is Apache-2.0; robots allow every agent | https://livebench.ai/ | 2026-10-22 | **served**, `livebench`: 49 models, 43 linked |
   | SimpleBench | the SimpleBench Team (AI Explained) | no licence on the site; the repository is MIT (its code and public questions) | https://simple-bench.com/ | 2026-10-22 | **served**, `simplebench`: 106 models, 91 linked |
   | Vending-Bench 2 | Andon Labs | "© 2026 Andon Labs Inc. All rights reserved", no terms beyond a privacy policy | https://andonlabs.com/evals/vending-bench-2 | 2026-10-22 | **skipped**: the page ranks 10 models; the other 61 sit only inside the site's compiled code, at addresses that change with each build |
   | Video-MME | the Video-MME team | "Video-MME is only used for academic research. Commercial use in any form is prohibited." | https://github.com/MME-Benchmarks/Video-MME | 2026-10-22 | **skipped**: D-215 does not clearly admit a use outside academic research |
   | GDPval | OpenAI | "The OpenAI-hosted GDPval leaderboard is no longer active"; its numbers stand in its paper and announcement; the third-party copy it points to (Artificial Analysis) needs an API key | https://evals.openai.com/gdpval/leaderboard | 2026-10-22 | **skipped**: no live board, only a paper's numbers, and the copy needs a secret |

2. **How each served board is read.** Each is a declared remote source (`app.workflows.sources`), read from its
   publisher's own host with no token, optional (D-121), with a floor of half the board as recorded, so a cut file
   fails the night and the refresh carries the previous one (D-156).
   - `osworld_verified`: the results workbook the page loads (`static/data/osworld_verified_results.xlsx` on
     `osworld-v1.xlang.ai`, the one host the client asks), read
     with the standard library. The rows the page's default "Foundation E2E GUI" tab shows that a catalogue can
     sell: approach type `General model`, no extra accessibility tree, no coding action. At 100 steps, the budget
     most rows report: a run at 15 or 50 steps is another measurement. A model's score is the mean of its runs, as
     the page shows it, dated by its latest run. Specialized GUI models and agentic frameworks are not read: a
     framework names a harness over a model, and the specialized models are not catalogue models (with them, 15 of
     32 link, under half).
   - `livebench`: release 2026-10-14 (LiveBench 2.0), `table.csv` with `categories.json`. The site computes its
     overall score in the browser and stores none: "mean of category averages". The source computes it the same
     way, rounded to two places as the site rounds, so the board's own rule, not a weighting of ours, ranks it. A row
     missing a category is skipped and counted. Rows are dated by the release. The release is pinned, as Datacurve's
     `v1.1` is: a new release is a code edit.
   - `simplebench`: the leaderboard file the page loads (`static/js/leaderboard-data.js`), one row per ranked model
     at its AVG@5 score, dated by the date the row was added; the human baselines are not models and are skipped.
   - `metr_time_horizons`: Time Horizon 1.1 (`assets/benchmark_results_1_1.yaml`), each model's 50% time horizon in
     minutes. Undated: its `release_date` is a model's release, never an evaluation date (D-139).
3. **Placement (D-188 clause 1's families).** OSWorld-Verified stands in `computer-use` after `terminalbench_4`;
   SimpleBench and LiveBench in `everyday` after `epoch_mmlu`. Each primary stays, so no surface's thresholds move.
   METR opens `long-tasks` (D-218 clause 2), its only board, titled "Long tasks" (`Uzun görevler` in Turkish), with a router
   hint, examples in English and Turkish and probes, and its thresholds calibrated by D-194 clause 4's rule
   (`scripts/calibrate_surface.py`) with METR's own published 95% intervals as the error. `score_anchor` stays
   unset: the engine pins it on an Elo surface only (D-162). No board opens a surface under clause 3: each served
   board fits one.
4. **Credits:** each served publisher, with its link and its terms as read above.

**Rationale.** Golden Rules 1 and 3: every board the owner's rule admits, from its publisher's own data, read each
night with no secret; every board it does not, named with its reason.

**The alternatives not taken.** Epoch's copies of OSWorld, SimpleBench and METR: a copy keeps its publisher's terms,
and the publisher's own file is fresher. Scraping CAIS's or Andon Labs' compiled app code: an address that changes
with each deploy is a broken night waiting. Computing LiveBench's overall with weights of our own: a number the board
never published.

**Mitigation if violated:** a served board with no credit is refused by `credits_for`. A publisher that objects or
changes its terms is taken out by its own ADR. A board that falls under half linked shows in the unlinked count of the
night's report.

**Revisit when:** a skipped board's terms or data change (HLE's publishers post a file, Vending-Bench 2 publishes its
whole board, GDPval's leaderboard returns, OSWorld 2.0 ranks 15 models); LiveBench publishes a new release; METR publishes a new time-horizon
version; the app takes payment (D-215's revisit).
