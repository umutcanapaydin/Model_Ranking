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

**Status:** proposed (M5-W4 implementation; owner ratification requested at the M5 gate)

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

*Append new ADRs in sequence via `/log-decision` skill. IDs are immutable; deletion leaves a gap (seed B.5).*
