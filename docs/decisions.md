---
record_type: register
id: model-ranking-decisions
status: ratified
date: 2026-08-11
---
# Decisions

> ADR-lite log. Pre-seeded with universal decisions (D-001..D-007) from EF-AI Phase-1 + v2.0 consortium.
>
> **ADR-ID convention (v2.2, seed B.6 / FB-2):** to avoid colliding with an inherited project's own ADR history, **process/universal ADRs use the `P-00x` namespace; project ADRs start at `D-100`** (the `D-001..D-099` band is reserved). The existing universal `D-001..D-007` are grandfathered (supersede-don't-edit, B.2) and are equivalently addressable as their `P-00x` mirror (see P-001). **Your project starts at D-100.** For an inherited project that already numbered low D-ids, run the Stage-0 reconciliation recipe in P-001.
>
> **Discipline:**
> - When an assumption ossifies under uncertainty, add a new ADR with status `proposed` via `/log-decision` skill (seed B.1).
> - To reverse: mark old as `superseded by D-NNN`. Never edit in place (seed B.2).
> - IDs are immutable; deletion leaves a gap (seed B.5).
>
> **Status legend:**
> `proposed` — captured, not yet ratified.
> `accepted` — locked. Changing requires `superseded by`.
> `superseded by D-NNN` — old; do not follow.

---

## D-001 — Cloud-agnostic SDK boundaries (UNIVERSAL)

**Status:** accepted

**Decision:** All external cloud / vendor SDK calls (object storage, model endpoints, telemetry, identity providers, payment, etc.) live behind a typed Protocol in `src/<pkg>/clients/`. Production implementations are isolated; a fake implementation lives alongside for tests.

**Rationale:** A future cloud / vendor pivot is a `clients/` swap, not a feature rewrite. Phase-1 lesson: this single discipline saved an entire milestone of rework when the cloud target shifted.

**Mitigation if violated:** Code calling vendor SDK directly from `workflows/` or `adapter/` is a contract violation; refactor before merge.

**Revisit when:** Customer mandates a specific SDK in a way that breaks the Protocol abstraction.

---

## D-002 — ADR-lite format (UNIVERSAL)

**Status:** accepted

**Decision:** All non-trivial design decisions go in this file using this format: ID, Status, Decision, Rationale, Mitigation, Revisit. One-paragraph per field. No full IETF-ADR ceremony. Use `/log-decision` skill for format enforcement.

**Rationale:** Phase-1 captured 40 ADRs cleanly with this format in <2 hours total; heavier ADR formats took ~15 min per decision and got skipped under pressure.

**Mitigation:** None — this is the format.

**Revisit when:** Project crosses ≥3 teams and needs richer audit format.

---

## D-003 — AGENTS.md diet (UNIVERSAL)

**Status:** accepted

**Decision:** `AGENTS.md` is **navigation, not encyclopedia**. Target ≤80 lines; hard cap 150 lines. Anything longer goes to `.agents/rules/practices.md` or related concern files.

**Rationale:** Phase-1 measurement: AGENTS.md trended 250 → 218 → 170 lines across M5-M9. Each diet pass increased agent task success. ETH Zurich AGENTbench (arxiv:2602.11988) corroborates: LLM-generated context files >200 lines LOWER task success by ~3% and raise cost 20%+. v2.0 lowers the target from v1.1's 170-line tolerance to 80.

**Mitigation:** At every milestone closure (§4.2 Capture), check `wc -l AGENTS.md`. If over cap, extract a section to `.agents/rules/`.

**Revisit when:** Multi-week milestones consistently need >150 lines of navigation.

---

## D-004 — Permission matrix default-deny (UNIVERSAL)

**Status:** accepted

**Decision:** `permission-matrix.md` defines what coding agents may and may not do. Default for any sensitive action is DENY; allowances require a new ADR. v2.0 extends this with §10 OS-aware patterns + §11 BLOCKING taxonomy.

**Rationale:** Replit DB deletion incident (July 2025) + Lovable RLS CVE-2025-48757 (May 2025) both stemmed from agents acting beyond authority. Standing matrix removes ambiguity.

**Mitigation:** `permission-matrix.md` is editable only via ADR. Commits violating without prior `accepted` ADR are reverted.

**Revisit when:** Permission categories themselves change.

---

## D-005 — Subagent-profiles mandatory: Code-Reviewer + Security-Reviewer (UNIVERSAL)

**Status:** accepted — **superseded in part by P-004 (v3, V3C-68):** the per-wave pair is now Code-Reviewer + Tester; Security-Reviewer moves to Stage-4 closure (BLOCKING before deploy). Decision body preserved below per B.2 (supersede, don't edit).

**Decision:** Every wave-end fires two subagent profiles in Stage 3: `subagent-profiles/Code-Reviewer.md` (3a) and `subagent-profiles/Security-Reviewer.md` (3b). These are MANDATORY. Other profiles (Architect, Docs, etc.) are project-specific and added per need. Profile content invoked via `/review` and `/security-review` skills.

**Rationale:** Phase-1 K.7 (fresh-eyes review) caught BLOCKING at every milestone. Industry research (Veracode 45%, Lovable RLS, Replit) shows parallel security pass needed.

**Mitigation:** Stage 0 ships baseline profile files. Stage 1 plan chooses source (A/B/C/D).

**Revisit when:** A third profile graduates to mandatory (≥2 milestones PULLED-WEIGHT).

---

## D-006 — BLOCKING / MINOR / Catastrophe taxonomy locked (UNIVERSAL, v2.0)

**Status:** accepted

**Decision:** Stage 3 Per-Wave Duo verdicts (3a + 3b) and Stage 4.1 Quality Gate verdicts MUST use these categories:

- **BLOCKING:** REQ unmet / test red / secret leak / contract-grep miss / coverage drop / PASS without `file:line` evidence / auth-PII-payment-migration without senior review / permission-matrix region touched without ADR / hook violation.
- **MINOR:** style / doc drift / cross-wave K.9 candidate / AGENTS.md approaching cap (not over).
- **Catastrophe-class (DENY always):** `git reset --hard` / `git push --force` / `rm -rf` / drop table / commit secret / log PII unredacted / self-merge agent's own PR / any `--force` on irreversible op without user confirmation.

Full taxonomy in `permission-matrix.md` §11.

**Rationale:** Quality consortium identified "undefined BLOCKING drifts per reviewer" as the highest-leverage quality bug in either of the merged models. Writing it down once eliminates per-reviewer reinterpretation.

**Mitigation:** PASS verdicts WITHOUT file:line evidence are automatically demoted to BLOCKING (no false-pass surface). All BLOCKING findings need an attached evidence path.

**Revisit when:** First Phase-2 milestone closes with a new BLOCKING class not covered.

---

## D-007 — Two baseline hooks ship day-1 (UNIVERSAL, v2.0)

**Status:** accepted

**Decision:** `.claude/settings.json` ships with exactly 2 PreToolUse/PostToolUse hooks at bootstrap:
1. PreToolUse — block writes to `.env` / `*.env*` (catastrophe-class catch).
2. PostToolUse — run `make check` after Write/Edit/MultiEdit (Stage 2 commit-gate enforcement).

Additional hooks earn their way in only after a rule in `.agents/rules/practices.md` or `permission-matrix.md` is violated 3+ times in measured sessions. Catastrophe-class items (§11 of permission-matrix) may ship as hooks day-1 without violation prerequisite.

**Rationale:** PM consortium lens — every hook is a maintenance liability. Shipping 2 catches the highest-leverage incidents (Lovable secret-commit class + lint-drift) while not pre-defining what doesn't break.

**Mitigation:** Promotion rule documented in `permission-matrix.md`. Quarterly handover harness diet retires hooks not fired in 90 days.

**Revisit when:** First Phase-2 milestone surfaces a recurrent rule violation that would benefit from a 3rd hook.

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

**Mitigation if violated:** any agent auto-approving or skipping an owner touchpoint "per the protocol" is an integrity violation → catastrophe-class (permission-matrix).

**Revisit when:** the owner initiates — expected only after many versions of clean telemetry track record.

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

**Status:** ratified — owner ruling, 2026-08-17: *"Let the payload be English, and the query values
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

*Append new ADRs in sequence via `/log-decision` skill. IDs are immutable; deletion leaves a gap (seed B.5).*
