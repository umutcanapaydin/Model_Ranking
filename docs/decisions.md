---
record_type: register
id: model-ranking-decisions
status: ratified
process_version: v6.6
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
> `proposed` — captured, not yet ratified.
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

**Revisit when:** A release is harmed by late security feedback — then move a security pass earlier for that risk class.

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

---

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
