# Engineering Practices

Portable engineering rules. Apply across machines and developers in this project.

For per-developer machine specifics (shell, conda env, ports) see `.agents/rules/environment.md` (gitignored, your own).

For the full 64+8 seed compendium see `.agents/rules/playbook-seeds.md`. This file is the *frequently-used subset* of those seeds in narrative form.

---

## Plan before implementing

Output a short plan: goal, files touched, test approach, risks. Skip only for typo edits. See `docs/external-skills/writing-plans.md` for the format superpowers established.

For a full milestone, write a `docs/plans/m{N}-plan.md` per the Stage 1 template in [`pipeline-design.md`](https://github.com/SADCAIVibe/General_Pipeline/blob/v5.0/general_pipeline_v5.0/pipeline-design.md). Mandatory sections: Goal, REQ-ID acceptance, Risk tier, Wave decomp, K.8 contracts grep-verified, Token budget, Subagent profile source.

## Code quality (consolidated from playbook seeds H.1-H.10 + K.x)

- **Match existing codebase style.** Match what's there before introducing new abstractions.
- **`extra="forbid"` on every pydantic v2 boundary model** (seed H.3).
- **Type-hinted public surface** — strict mypy enforces this.
- **Trust mypy narrowing** — don't preemptively `# type: ignore` (seed H.7).
- **Unused `# type: ignore` is a signal** — remove, don't normalize (seed C.8).
- **`Any` at LLM / JSON boundaries** must be pinned to `object` before return (seed H.8).
- **Async at boundary** — sync internals are fine; async lives at adapter / external-call boundaries.
- **ASCII only** in code — ban en-dash, multiplication sign, ellipsis, NBSP (seed H.4).
- **Paths via `_repo_root()`** — never `Path("./x")` for runtime defaults (seed F.4).
- **Auto-fix lint** — use the linter's `--fix`; don't `# noqa` to silence (seed H.5).
- **`src = ["src"]`** in ruff config for src-layout discovery (seed H.6).

## Tests as truth signal (consolidated from seeds C.1, E.1-E.3, J.1-J.4)

- **Day-1 green baseline (seed C.1).** First commit includes runnable app + at least 1 passing test + `make check` green.
- **Run the tests; don't trust markdown that says "tests pass"** (seed E.1).
- **Tests cite REQ-IDs and D-IDs** in comments — e.g., `# covers REQ-CC-001, D-026` (seed E.2). PASS verdicts WITHOUT `file:line` evidence are BLOCKING per `permission-matrix.md` §11.
- **Every acceptance criterion has a citing test; red-test the reported symptom first (V3C-02, gate).** No "done" without a test that cites the criterion; when fixing a reported bug, reproduce it with a FAILING test before diagnosing, then make it green (red→green). Enforced at the Quality Gate and the per-wave Tester.
- **One canonical mock per integration + a contract test (V3C-44).** Build one canonical mock/fake-client per external integration before the integration code (extends K.1); consolidate parallel mocks into it; keep a contract test that runs against the real API so the mock can't drift. Tests drive the canonical fake (J.4), never bespoke per-test stubs.
- **Defensive LLM output coercion** — strip, unwrap, sentinel-check BEFORE schema validation (seed E.3).
- **Factory-style app builders for test isolation** (seed J.1).
- **Frozen dataclasses for boundary results** (seed J.2).
- **Coverage gaps are design tells** — not metric targets (seed J.3).
- **Integration tests via `httpx.ASGITransport` + `LifespanManager`** (seed J.4).
- **Test imports map 1:1 to `pyproject.toml` entries** — every new `import X` has matching `X>=N` in pyproject in the same commit (seed C.6).
- **TDD-with-AI for new modules behind a locked contract** (seed E.4, ACTIVE in v2.1) — when a wave builds a NEW module and its K.8 contract is already frozen, write the acceptance-criterion tests FIRST (citing REQ-IDs), then implement to green. Scope is narrow: only new-module + locked-contract, never a blanket mandate. Closes the coverage-theater failure (AI writes test + impl in one turn).
- **Acceptance-criterion tests ship in the same wave as the feature** (seed E.5) — never defer the test that proves a *hard* criterion (concurrency, survives-restart) to closure. On subagent death, verify the criterion's test EXISTS, not just that the code compiles.
- **Full gate in-sandbox via a runtime shim** (seed C.10) — when the sandbox runtime lags prod, inject the version-only-missing names (`datetime.UTC`, `StrEnum`) via `sitecustomize.py` and run the WHOLE suite; keep the one behaviour-version-dependent test `skip`-marked for the real target.

## Distributed correctness & durability (consolidated from seeds L.1-L.6) — for any multi-node / async-callback / queue-backed service

- **Commit the durable record BEFORE the ack** (L.1) — enqueue-then-ack, never ack-then-enqueue; the durability write is synchronous on the request path, the slow work is the worker's.
- **Release what you reserved when you reject** (L.2) — if the accept path claims an idempotency slot/lock before a step that can fail or load-shed, roll it back on rejection so the retry is a fresh accept, not a stuck duplicate.
- **At-least-once + a stable idempotency key; never promise exactly-once** (L.3) — duplicate = byte-equal signed body for the same key; the dedup-on-key contract goes in the customer API doc.
- **Cross-node election is one atomic op** (L.4) — `SET NX EX` / `INSERT ON CONFLICT`, never `GET`-then-`SET`; prove it with an N-thread shared-backend race asserting exactly one winner.
- **Bound the durable queue + load-shed** (L.5) — a configurable depth cap → 503 past it (pairs with L.2 rollback); a soft `LLEN` bound only ever rejects, never drops.
- **Scale-out preconditions are a boot guard** (L.6) — the pod can't know its replica count; require an explicit flag (`REQUIRE_REDIS`) + refuse to boot if its precondition is absent; pair with a fail-fast config-doctor that reports ALL bad env at once.
- **Version-stamp the health/readiness probe** (L.7) — `APP_BUILD` (image tag / git SHA) -> `/health` body `{status, version, build}`. A green probe proves *up*, never *which code*. Day-1 baseline; additive fields only (don't break the liveness contract).
- **Configured != working** (L.8, v2.2) — invoke every external dependency once for real (`make smoke-deps`: model / queue / store / callback) and inspect the RESULT before declaring "ready"; catalog presence + valid creds can sit on a backend that returns "not deployed."
- **Config reaches the *process*, not just the values file** (L.9, v2.2) — read each critical value back from inside the running process (safe echo: SET/EMPTY + length, never the value); injection layers (Helm/operator/secret mount) silently drop keys.

## Stage-0 is an executable gate, not a checklist (v2.2)

- **`make bootstrap-check` before Stage 0 closes** (C.11 / FB-1) — fails on stray `<PLACEHOLDER>`s, a non-L.7 `/health`, still-template prd/decisions/architecture, missing universal ADRs. Documented discipline silently degrades; a failing make-target does not.
- **ADR-ID convention** (B.6 / FB-2) — process/universal ADRs use `P-00x`; project ADRs start at `D-100` (D-001..D-099 reserved). Reconcile inherited projects at Stage 0 (P-001 recipe).
- **License & commercial-use review of any wrapped/forked OSS engine** (F.10 / FB-4) — AGPL/GPL/SSPL on a network service ⇒ "wrap, don't fork" + legal sign-off; an unreviewed copyleft fork is BLOCKING. Capture in `docs/license-review.md`.
- **Finish git host-side in a Cowork mounted sandbox** (C.12 / FB-3) — git can't remove its own `.git/*.lock` (EPERM); stale locks block the next commit. Prefer host-side `git`; clear locks with `rm -f .git/*.lock`.
- **Commit `.gitignore` first** (V3C-27) — before the first real commit, so venv/caches/`environment.md` are never tracked.

## v3 guardrails (cross-project harvest, 2026-06-26)

### Web/API security baseline (V3C-11/12/13/51/56 — see `docs/security-baseline.md`)
- **No plaintext creds / no default-admin password (V3C-11, gate).** Hash credentials from day one; secrets from env/secrets-manager, never inline literals. `make bootstrap-check` C7 fails on an obvious default-admin / plaintext-credential pattern.
- **Server-side authz on every mutating route (V3C-12).** Client-side checks are UI sugar; assume the client is hostile.
- **CORS allowlist, never allow-all + credentials (V3C-13).** No wildcard-origin + `Access-Control-Allow-Credentials: true` in prod.
- **Validate security-critical config at startup; fail the prod process (V3C-51).** Never silently default to an insecure value (auth-off, empty key, 0). Pairs with L.6 config-doctor.
- **Encrypt creds/PII at rest with a rotation-friendly key chain (V3C-56).** Decrypt tries all keys; encrypt uses the first (current). Rotation is a config change, not a migration.
- **Generic client errors; log detail server-side.** No stack/SQL/internal-path leaks; no user-enumeration oracles.

### Control-class fail direction (V3C-33 + V3C-45 — ONE paired rule)
- **Auth/safety controls fail CLOSED** on error/timeout (deny), with a **tested disable switch** + correct domain scope.
- **Fairness/rate-limit controls fail OPEN** (serve rather than block legitimate traffic on limiter failure).
- Encode the two together so neither is misapplied; misapplying either direction is BLOCKING.

### Agent least-privilege + human-confirm (V3C-08 + V3C-36)
- Per-agent **tool allowlist** (only the tools the task needs). **LLM proposes, deterministic code acts.** **Human-confirm on ALL writes** — CI: the agent opens drafts, a human merges, the agent never edits its own workflow, "ACT don't narrate" with a named served model + allowlisted tools; runtime: mutating tool-calls are per-action confirmed, never batched/unattended. Extends V3C-08 (Layer-2 issue agent) + the permission matrix.

### No destructive ops / destructive-defaults OFF (V3C-06 + V3C-53)
- Revert **surgically** — never full-revert to an old commit to fix one thing; verify `main` actually contains the merged commits. Any reseed/reset-on-boot **defaults OFF or is loud + explicit** (catastrophe-class).

### Build guardrails (V3C-03/05/10/65)
- **V3C-03 — runtime config, never build-baked.** Config that differs per environment is read at runtime, not baked at build time (generalizes L.9 beyond k8s values-files to build-time bake, e.g. Next.js).
- **V3C-05 — every dependency saved to the manifest.** Every `import`/use of a dep is in the manifest (pyproject / package.json) in the same edit, or CI breaks where local "worked" (extends C.6 to JS/npm).
- **V3C-10 — pin the toolchain version in CI.** `.nvmrc` / `engines` / language version pinned; test the build on the target version (extends C.2/C.7 to JS toolchains).
- **V3C-65 — race detector as a recommended CI step.** For concurrent packages, run the race detector (`-race` / equivalent) in CI; a `// BUG:` touching shared state blocks release. Recommended, not a universal gate (evidence is Go-only).

### Agent-Native / LLM-Ops (CANDIDATE container)
- The agent-native/LLM-ops + gateway cluster (provider registry, deterministic fallbacks, LLM output contracts, tracing, MCP pooling, circuit-breakers, streaming rate-limit accounting, ...) is **CANDIDATE, not active** — most evidence is one ecosystem (Botim AOP + one-api/NewAPI gateway family). Promote on a 2nd independent ecosystem. See [`pipeline-design.md`](https://github.com/SADCAIVibe/General_Pipeline/blob/v5.0/general_pipeline_v5.0/pipeline-design.md) §3.6 and the candidate block in `playbook-seeds.md`. Adopted now from this cluster: V3C-33/45 (fail direction), V3C-08/36 (least-privilege), V3C-44 (canonical mock), V3C-56 (encrypt at rest).

## v3.1 guardrails (first GP-v3 field run — hcs_maas_vib, 2026-07-03)

- **Hermetic gate (sharpens V3C-10/C.6):** trust a verdict only from a reproducible environment — clean venv built solely from the manifest, dev tools pinned (not `>=`-floored), stale bytecode cleared (`PYTHONDONTWRITEBYTECODE=1` or purge `__pycache__` pre-gate), ONE designated authoritative gate host. Add the import and its manifest entry in the SAME edit.
- **In-place revert (sharpens V3C-06):** `git checkout <file>` / `git restore` reverts to the last COMMIT — on uncommitted work it destroys everything since. Revert experimental edits in place (string-replace the exact change back), verify byte-identical (md5/`git diff`). Forbidden op for reviewer/tester agents mid-wave.
- **Wave close is checklist-gated (V3C-69):** fill + commit `docs/plans/m{N}-wave-{W}-close.md` from `docs/wave-checklist.template.md`; every ✅ cites a fresh wave-scoped referent; skipped/waived checks are ledgered. `make wave-check FILE=...` verifies mechanically.
- **Money (V3C-77 — only if the project handles money):** integer minor units + currency; float rejected at the type; one boundary rounding.

## v3.5 — outward-facing checks (Increment 9: the post-prod dataset, 2026-07-27)

- **Test the world's shape, not your imagination of it:** ~~`make check-templates`~~ (shipped  <!-- **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything. -->  <!-- REMOVED at the v5 control screen 2026-08-12 -- see `docs/watchlist.md`, returns after 2 recurrences. It needs a deployed URL and a live environment neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything. Left visible on purpose: a control that quietly vanishes is how a checklist becomes folklore. -->
  templates instantiate the parser) + ~~`make cold-start`~~ (zero persisted state → serve-ready or  <!-- **REMOVED at the v5 control screen (2026-08-12) — on `docs/watchlist.md`, returns at 2 recurrences.** It needs a deployed URL and a live environment that neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything. -->  <!-- REMOVED at the v5 control screen 2026-08-12 -- see `docs/watchlist.md`, returns after 2 recurrences. It needs a deployed URL and a live environment neither this package nor a fresh project has, so in five versions nobody could write down how to break it and it was never once shown to catch anything. Left visible on purpose: a control that quietly vanishes is how a checklist becomes folklore. -->
  honest not-ready) run in CI at merge + release. The tested artifact is the SHIPPED artifact.
- **Human-path criterion (general form):** a person who did NOT build it, using only shipped docs
  and artifacts, completes the surface's primary journey. Mandated instance: credentials.
- **Boundary-grep line (V3C-104):** every externally-delivered change declares "touches
  build/CI/k8s: NO|YES", verified by `git diff --name-only` against the boundary list; YES forces
  a pre-delivery conversation with the pipeline owner.
- **Never parse a bounded prefix** — size-bound the display, never the read feeding a parser;
  every re-runnable diagnostic prints its revision stamp (V3C-102 narrow).
- **Boot-prerequisite ownership (V3C-107):** in the image, or a named-owned provisioning row —
  no third category. Cold-start is the executable audit.
- **Cadence binds to artifacts (V3C-105):** every outward deliverable = a wave close.

## v3.4 — Stage 5 maintenance loop (OD-6, 2026-07-17)

- **Fix waves are waves** (existing machinery by reference). Intake = reproduced RED test (the
  frozen spec). Fix waves only turn red tests green — never new behavior. Red tests become
  PERMANENT suite members (bug-ID tagged).
- **Fixpack = the deploy gate** (`docs/fixpack.template.md`): caps ≤5 fixes/~400 net lines
  (HIGH/⛔ ships solo); full regression once on the final bundle; owner out-of-sandbox
  verification signed; fix probe + watch window at deploy; rollback plan per pack.
- **Capture is mechanical:** fixpack lesson lines append to EXPERIENCE.md as a deploy condition;
  the standalone memory-based harvest session is RETIRED. 3 same-gate misses in 2 packs →
  gate-change proposal. N=3 fixes on one surface → surface locks, refactor via a normal milestone.

## v3.3 — A0.5 milestone-cadence owner review (OD-4, 2026-07-05; PROVISIONAL, tripwire-protected)

- **Cadence:** waves close AGENT-side — fresh-eyes reviews per tier, `make` checks green pinned to the closing tree, committed evidence-cited checklist, HIGH-tier pulled-forward security pass. The OWNER engages at every MILESTONE: report + per-wave diffs + his own tests/smoke tests + the commits. Milestone cap ~4–6 waves / ~2k net lines — close early, never stretch.
- **Checkpoint commits:** the owner (never agents) makes a labeled `wip(m{N}-w{W}): checkpoint — NOT reviewed` commit per wave (batchable daily). Commit ≠ approval. Kills the F17 uncommitted-loss class; keeps per-wave diffs decomposable for the milestone review; fires commit hooks on wave content.
- **Escalate NOW (halt to owner, never wait for the boundary):** suspected secret · scanner-finding suppression (agents may NEVER waive gitleaks/SCA) · BLOCKING at HIGH incl. test-integrity · stay-green fault with no covering test · CI/hook/gate-definition changes · critical-CVE/slopsquat dep · security-invariant test modified/deleted · ⛔-zone or criteria-meaning questions · plan-invalidating scope change · evidence a prior wave's gate leaked. ⛔-glob touch mid-milestone → async ping (non-blocking).
- **Assumption ledger is ACTIVE at A0.5:** assume-and-log when reversible, wave-local, non-⛔; HALT above that. Rendered in the closure report §1b.
- **Semantic-security compensation:** the agent security pass explicitly checks weakened validation / broadened permissions / disabled checks (HIGH waves; lightweight on MED); diff-vs-plan flags sensitive files (auth/crypto/secrets/CI/deps manifests) touched outside the declared slice.
- **Tripwire (automatic, non-waivable):** an escaped blocker traceable to an unreviewed wave that an owner wave-pass would plausibly have caught → fallback to wave-cadence review (rest of milestone + one full milestone). A0.5 is PROVISIONAL until it survives two full milestones on the next project.

## v3.2 — autonomy, context economy, AI-aware review (external research + OD-3, 2026-07-03)

- **Owner-in-the-loop (binding, v3.2):** the owner reviews every wave and milestone, runs the tests/smoke tests/checks, and makes all git commits. The autonomy ladder (`docs/autonomy-protocol.md`) is a NORTH-STAR CANDIDATE only — its one active idea TODAY is the evidence rule: anything measured about the pipeline is computed from git/CI vs protected refs, never agent-asserted.
- **Trust telemetry (V3C-84):** per task-type at every closure — post-closure fix rate (path overlap vs closure tag), churn, reverts, findings (security double-weighted) — script-computed into cost-log. Purpose TODAY: give the owner an honest quality signal and build the multi-version track record the north star would someday require.
- **Context economy (V3C-85):** smallest set of high-signal tokens. One task/session; fresh subagents per wave; compaction anchored to wave close and MUST preserve open findings/red tests verbatim and re-inject security-baseline invariants; token budget is a live circuit breaker — a wave projected to exceed it pauses at the boundary with a variance note (numbers are revisable defaults; principles are the rule).
- **Plan interrogation (V3C-88, MED/HIGH tiers only):** the plan names ONE alternative + its trade-offs ("which would a senior object to, and why"); a plan missing the alternative section fails plan-completeness mechanically. LOW-tier plans exempt.
- **Provenance (V3C-89→83):** agent-authored commits carry the trailer `Co-Authored-By: <agent> (GP-v3.2)` — forensics + heightened-review routing.

## Deploy + go-live readiness (Stage 4.3 — for any milestone that deploys)

- **"Code green + image built" is NOT "the new code is live."** `curl <target>/health | jq .build` MUST equal the tag/SHA you intended to ship (L.7).
- **A pod restart != a rebuild != a re-pull.** Restarting re-runs the image the deployment already references; if `/health` shows the old build, fix the build pipeline — do not just restart.
- **Confirm DevOps-owned build files weren't clobbered** (K.10) — a merge that overwrites the `Dockerfile` makes CI ship the wrong image behind a green probe (S34).
- **Then go-live readiness:** L.8 smoke-deps (invoke each dependency once) + L.9 read config back from the process + E.6 prove the pipe via the downstream's run-log attribution (S35).
- **Agent-driven prod UI** (K.11, guardrails ACTIVE) — when there's no API, an agent may configure/verify via the browser but NEVER enters credentials; state-changing clicks are per-action + visible; screenshots may hold secrets, so don't transcribe them (permission-matrix §12).
- Grounding: 12-factor "build / release / run" — releases are immutable, uniquely-IDed, and the run stage only launches a *selected* release.

## Decisions discipline (consolidated from seeds B.1-B.5)

- **Capture every assumption as an ADR** (seed B.1) — use `/log-decision` skill.
- **Supersede, never edit** (seed B.2) — old ADR keeps body; mark `superseded by D-NNN`.
- **Decisions are expensive; code is cheap** (seed B.3) — at hundreds-of-LOC scale, regenerate code with new decisions instead of patching.
- **Snapshot customer-facing artifacts before every review** (seed B.4) — `<name>_pre-<event>-<YYYY-MM-DD>.<ext>`.
- **Preserve stable IDs** (seed B.5) — IDs are immutable; deletion leaves a gap; moves preserve the ID.

## Subagent dispatch (consolidated from K.1-K.9)

- **Cloud-agnostic SDK boundaries** — Protocol-typed `clients/` (K.1 / D-001).
- **Typed Settings object for env config** — never sprinkle `os.getenv` (K.2).
- **Subagent dispatch via parallel waves** for independent scope (K.4).
- **Drift-guard between data dictionaries and consumers** — factor coercer when 3+ subagents produce the same helper (K.5).
- **Subagent prompts specify bar + leave discretion** within ≤5 min scope (K.6).
- **Code-quality review delegated to fresh subagent** (Code-Reviewer profile per K.7). The reviewer MUST NOT be the one that authored any of the wave's code. In a single-agent lane the reviewing seat is a SEPARATE SESSION carrying the diff and the base-ref rules, not the authoring context, and **it writes a file** — `docs/reviews/*.md` with `seat: independent` in its frontmatter. A review returned as a conversational report leaves the wave record citing evidence that does not exist; that happened once, on the one row certifying K.7 itself (W-056).
- **Cross-subagent contracts grep-verified** in plan (K.8) — paste `grep -n <symbol>` output into the plan.
- **Subagent self-spotting cross-Wave gaps** — flag K.9 candidates; don't fix; queue to next-M.
- **DevOps-owned files in a shared repo are a cross-TEAM contract** (K.10) — never let an app-feature merge overwrite `Dockerfile` / `/deploy/**` / CI config; mark them in `CODEOWNERS` and require DevOps review.

## Doc / knowledge sync (G.4 + G.5 + G.11)

- **When a rule changes, update both the canonical file AND any cached pointer** (e.g., README + AGENTS.md + memory pointers in `~/.claude/projects/<slug>/memory/`).
- **Customer-source-doc → mirrored on three audience surfaces, single canonical source** (G.11).
- **Customer-facing artifacts get a `Customer-Visible: Yes/No` flag** (G.5) — single canonical source, dual audience.
- **Internal docs and customer-facing docs are different artifacts** — keep separate (G.4).

## Process capture (G.1-G.3 + G.7-G.10 + G.12)

- **Open the capture file BEFORE the work starts**, not after (G.1).
- **process-log per session** — 3-10 lines, ends with `Lesson: <one-liner>` tag.
- **Distinguish deliverable / artifact / raw material** (G.2).
- **Two-tier closure-checklist** (G.3) — per-slice + per-milestone.
- **Hand-off files written FOR future agents** are first-class deliverables (G.7).
- **Numbered question list with recommendations** (G.8), not open-ended Q&A.
- **PM-friendly risk register: cap at 7 items, two lines each, zero engineer vocab** (G.9).
- **Share literal sentinel string between system prompt and output coercer** (G.10).
- **Per-milestone retrospective with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts** (G.12) — run at M≥3 via `/retrospect` skill.

## Logging at boundaries

Log at the system's edges — API entry, DB write, external call, queue publish/consume. Structured logs (JSON via structlog), not bare `print` / `console.log`. Internal pure functions don't need logging.

The goal: when something breaks in production, boundary logs alone tell you which side failed.

## Roadmap discipline (I.1)

- Roadmap files are snapshots, not state. Create `docs/roadmap-{YYYY-MM-DD}-post-m{N}.md` rather than editing existing.
- README points to the latest snapshot.

## Garbage collection (D.4)

- Continuously prune "AI slop" — don't accumulate stale docs that contradict current decisions.
- At quarterly handover (every M%3==0), do a harness diet: retire any skill / hook / MCP not fired in 90 days.

## See also

- `playbook-seeds.md` — full seed compendium (themes A-L + v1.1/M12/S34 ADDENDA + ★ v2.2 RATIFIED: C.11 bootstrap-gate, B.6 ADR-ID ranges, F.10 OSS-license gate, L.8/L.9 go-live, E.6 pipe-attribution, K.11 agent-UI, C.12 git-in-mount + ★ v3 RATIFIED: V3C-11 security gate, V3C-02 tests gate, V3C-68 review-loop restructure, V3C-44 canonical-mock, V3C-12/13/51/56 security baseline, V3C-33/45 fail-direction, V3C-08/36 least-privilege, V3C-06/53 + build guardrails, + Agent-Native CANDIDATE sub-block)
- `docs/security-baseline.md` — web/API security baseline (V3C-11/12/13/51/56)
- [`pipeline-design.md`](https://github.com/SADCAIVibe/General_Pipeline/blob/v5.0/general_pipeline_v5.0/pipeline-design.md) §3.5 (Theme L) + Stage 4.3 (deploy verification) + §0 (v2.1 changelog)
- `docs/pm-status.template.md` — PM-readable status snapshot (pairs with G.9)
- `permission-matrix.md` — default-deny matrix + BLOCKING taxonomy
- `docs/decisions.md` — D-001..D-005 universal + your project D-006+
- `docs/discipline-*.md` (in `docs/external-skills/`) — referenced superpowers SKILL.md
