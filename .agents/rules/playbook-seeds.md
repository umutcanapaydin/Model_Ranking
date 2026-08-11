# Playbook Seeds

> Append-only collection of **generalizable principles** discovered while building this project. Each seed is a candidate paragraph in a future "vibe coding playbook" doc and/or a rule in a reusable `AGENTS.template.md`.
>
> Format per seed:
> - **Principle** (one sentence, stand-alone)
> - **Origin** (the moment in *this* project where we learned it — link to `process-log.md` entry)
> - **Reusable artifact** (what concrete file/snippet/process embodies it)
> - **Risk if ignored** (what goes wrong in projects that skip it)
> - **Tradeoff / cost of adoption** (added 2026-05-27 — what it costs to adopt this pattern: cognitive overhead, tooling, learning curve, ongoing maintenance. Required for seeds added from M6 onwards; older seeds are grandfathered per B.2 supersede-don't-edit. Going-forward only.)
>
> Discipline: at slice-end, ask "did anything we did today apply beyond this client?" — if yes, drop a seed here.

---

## Theme A — Pre-code documentation

### A.1 — Number every requirement before writing a single line of code.
- **Principle:** restructure the customer's PRD into REQ-IDs (REQ-CC-001, REQ-S-001, …). Tests and PRs cite these IDs forever.
- **Origin:** S1.
- **Reusable artifact:** `docs/prd.md` numbered-table format; per-area prefixes.
- **Risk if ignored:** "we covered that, right?" debates with no audit trail; tests drift from spec.

### A.2 — Treat two source-of-truth docs as adversarial until proven otherwise.
- **Principle:** on first read of a PRD + an architecture brief (or two PRDs, or PRD + slide deck), build a conflict table. Don't trust either doc.
- **Origin:** S2 — Huawei vs DU Cloud, ModelArts vs local H100 were both authoritative-feeling.
- **Reusable artifact:** `docs/architecture.md` §5 PRD↔Arch conflict table format.
- **Risk if ignored:** silently coding against the assumption of one doc; weeks later, the customer says "no, we meant the other thing."

### A.3 — Extract Open Questions in a separate pass from the structuring pass.
- **Principle:** first restructure, *then* re-read for OQs. Don't mix.
- **Origin:** S1 — we did them mixed and it was slower.
- **Reusable artifact:** `docs/prd.md` §9 OQ section pattern.
- **Risk if ignored:** OQs hide inside dense REQ tables and aren't visible to the agent or the customer.

### A.4 — Catalog conflicts across multiple customer artifacts before saying "yes" to next-step work.
- **Principle:** when the customer drops 3+ new artifacts in one batch (updated feature list + Error Handling Guide + requirement.md + verbal expert input), do a dedicated conflict-cataloging pass before any edit. List every cross-document conflict with severity. Resolve per-conflict with the user before building.
- **Origin:** S18-bis (2026-05-21) — three docs arrived together; without the explicit pass we would have shipped SMS without taskId, 5-attempt callback retry (vs Guide's 3), and err_code 1005 (vs Guide's 413).
- **Reusable artifact:** the numbered-decision-points format — `Karar N — <topic>: <context>. (Önerim: ...)` per conflict.
- **Risk if ignored:** agent silently picks the most recent doc as authoritative; conflicting decisions slip in and only surface at customer acceptance.

---

## Theme B — Decisions discipline

### B.1 — Capture every assumption as an ADR before it ossifies in code.
- **Principle:** when an open question can't be resolved upstream, lock it as a `proposed` decision with status, rationale, mitigation, and "revisit when". Then code can move.
- **Origin:** S3.
- **Reusable artifact:** `docs/decisions.md` ADR-lite format with status legend.
- **Risk if ignored:** agents three weeks later invent contradictory assumptions; impossible to audit why the code looks the way it does.

### B.2 — Supersede, never edit.
- **Principle:** when a decision is overturned, mark old as `superseded by D-NNN`. Never edit in place.
- **Origin:** S5 (Path A → Path B reversal recorded explicitly as D-027 superseding earlier framing).
- **Reusable artifact:** the status legend + the "Revisit triggers" section at the bottom of `decisions.md`.
- **Risk if ignored:** lose the audit trail of *why* we changed our mind. Future agents repeat the discarded reasoning.

### B.3 — Decisions are the expensive part; code is the cheap part.
- **Principle:** at the ~hundreds-of-LOC scale, regenerating code with fresh decisions is faster than patching old code toward new decisions.
- **Origin:** S5.
- **Reusable artifact:** `docs/codex-audit.md` — explicit separation of "design IP to adopt" vs "code IP to discard".
- **Risk if ignored:** sunk-cost trap; keep patching toward a target stack you wish you'd started with.

### B.4 — Snapshot any customer-facing artifact before every review iteration.
- **Principle:** before editing any customer-facing artifact (xlsx, md, yaml, OpenAPI), copy it to `<name>_pre-<event>-<YYYY-MM-DD>.<ext>`. The current file moves forward; the snapshot freezes the version the customer / team last reviewed.
- **Origin:** S18 (2026-05-19) + S18-bis (2026-05-21) — both turns produced `_pre-<event>-<date>` snapshots; cross-version diff was trivial; the team always had a clean "as last shown to customer" reference.
- **Reusable artifact:** the filename convention; complements B.2 (supersede-don't-edit) at the artifact level instead of the decision level.
- **Risk if ignored:** rollback path becomes git-only; "what changed since last review?" needs archaeology; trust in iteration history erodes.

### B.5 — Preserve stable IDs even when rows are removed or hidden.
- **Principle:** feature / decision / requirement IDs are cited across many documents (process-log, FAQ, ADRs, prior chat handoffs, customer correspondence). When an item is deleted or moved to internal-only, leave its ID slot empty; never renumber.
- **Origin:** S18 — C2.02 deleted, P.06 / O.05 / CR.05 moved to internal-only; renumbering would have invalidated every back-reference across the repo and prior chat handoffs.
- **Reusable artifact:** AGENTS.md rule "IDs are immutable; deletion leaves a gap, moves preserve the ID".
- **Risk if ignored:** every doc that cites an ID drifts silently; future agents trust the cite, fetch the wrong row, ship the wrong behaviour.

---

## Theme C — Repo bootstrap

### C.1 — Day-1 green baseline.
- **Principle:** the *very first commit* must include a runnable app + a passing test + `make check` green. Even if the app only serves `/health`.
- **Origin:** S6/S7.
- **Reusable artifact:** `src/ef_ai/adapter/main.py` minimal app + `tests/unit/test_health.py`.
- **Risk if ignored:** projects accumulate "almost ready" code for weeks before discovering basic import errors.

### C.2 — Pin a minimum, not a fixed version.
- **Principle:** never hard-code `python3.11` (or any single point version) in build scripts. Always auto-detect with a `>=N` floor and a clear error on failure.
- **Origin:** S6 — `make install` blew up on Python 3.14 because of `python3.11` literal.
- **Reusable artifact:** `Makefile` auto-detect loop + `_check_python` guard.
- **Risk if ignored:** onboarding friction; every new developer or CI runner hits the same wall.

### C.3 — Every command in `Makefile` is the canonical way.
- **Principle:** `make test`, `make lint`, `make typecheck`, `make check`, `make run`. Agents and humans both invoke through `make`. No ad-hoc shell pipelines in PRs or chat.
- **Origin:** S6.
- **Reusable artifact:** the `Makefile` itself.
- **Risk if ignored:** the agent invents its own pytest invocation that misses coverage flags; tests pass locally but CI shape is different.

### C.4 — Stack choices encoded in `pyproject.toml` and `AGENTS.md` simultaneously.
- **Principle:** if the project uses pydantic v2, both `pyproject.toml` lists it as dependency *and* `AGENTS.md` says "all schemas are pydantic v2". One without the other is half a decision.
- **Origin:** S6 (D-019 + pyproject.toml lockstep).
- **Reusable artifact:** the dual presence pattern.
- **Risk if ignored:** agents see `pydantic` in deps and assume v1; or see "use pydantic" in docs and don't add it to deps.

### C.5 — `AGENTS.md` is navigation, not encyclopedia. Cap around 150 lines; the rest lives in `docs/`.
- **Principle:** the entry point file an agent reads first MUST stay short. Long instruction files have three failure modes simultaneously: (a) they consume too much context, (b) when too many rules are marked important none of them effectively are, (c) they go stale faster than they get reviewed. Keep `AGENTS.md` to mandatory rules + one-line pointers; move detail to `docs/<topic>.md` files referenced from those pointers.
- **Origin:** OpenAI "Harness Engineering" article (Feb 2026) + our own AGENTS.md drift in S19 (added §3.4.2 with 8 rules, AGENTS.md grew to 230+ lines). S20 cleanup extracted §3.4.2 detail into `docs/discipline-customer-iteration.md`.
- **Reusable artifact:** the "navigation + per-topic doc" split. AGENTS.md cites; the topic doc owns the body.
- **Risk if ignored:** every new agent burns context reading 300-line house rules; the rules drift because nobody re-reads the bottom half; "important" loses its meaning when applied to everything.

### C.6 — Test imports map 1:1 to `pyproject.toml` entries; never add an `import X` without the matching dep entry in the same edit.
- **Principle:** the moment you write `from foo import Bar` in a test file, you also add `foo>=N` to `[project.optional-dependencies].dev` in `pyproject.toml`. Same commit, same change. Not "later". Not "after I verify it works locally". The dep entry IS part of the import.
- **Origin:** S20 — `asgi-lifespan` was installed in sandbox venv and used by `test_sms_workflow.py`; missing from `pyproject.toml`. Mac `make check` failed on `ModuleNotFoundError`; round-trip cost ~5 min and a separate edit.
- **Reusable artifact:** AGENTS.md §3.3 rule "every test import must have a matching pyproject entry in the same edit"; could also be enforced by a custom lint rule scanning imports vs. pyproject (see F.3).
- **Risk if ignored:** "works on my machine" — tests pass for the author who installed the dep manually, break for everyone else (other agents, CI, Mac vs sandbox).

### C.7 — Deterministic project-state ops as bash scripts; LLM-free, fast, cheap.
- **Principle:** operations like "show me the latest process-log entry", "what ADRs are still `proposed`?", "which external dependencies are blocking M-next?" do not need an LLM call. Write them as bash scripts that scan the repo files and emit a structured text report. Invoke through `Makefile` so agents and humans use the same canonical interface.
- **Origin:** CCPM uses 14 bash scripts (`status.sh`, `standup.sh`, `epic-list.sh`, `search.sh`, ...). OpenAI Harness mentions "deterministic ops" as a velocity multiplier. Our `make standup` in S20 closure is the first instance.
- **Reusable artifact:** the `scripts/standup.sh` + `make standup` target pair. New tracking ops added the same way: one bash file per concern, one `make` target per file.
- **Risk if ignored:** every "where are we?" question turns into an LLM token spend + a chat round-trip + a possibly hallucinated summary. Slow, expensive, sometimes wrong.

### D.4 — Garbage-collect "AI slop" continuously, not in big bangs.
- **Principle:** agents replicate the patterns they observe in the repo. If the repo has 3 different ways of doing the same thing, agents will create a fourth. Continuous small cleanup beats periodic large refactors. Encode the "golden version" of each pattern in `playbook-seeds.md` and `docs/`, then either (a) run periodic scan-for-deviation tasks, or (b) include a "drift check" in every milestone closure.
- **Origin:** OpenAI Harness Engineering — "many small cleanup PRs can be reviewed quickly and automerged"; we hit our own version in S19 (pre-M5 cleanup pass found 6 stale docs after only two customer-review iterations).
- **Reusable artifact:** wave-based cleanup pass (Wave 1 must / Wave 2 should / Wave 3 housekeeping / Wave 4 capture); a recurring agent that scans for deviations and opens targeted PRs (deferred to Phase-2).
- **Risk if ignored:** drift compounds like high-interest debt; six months in, the repo has three coexisting "patterns" for the same problem, the next agent guesses wrong, and untangling costs more than a rewrite.

### F.3 — Custom lint rules carry remediation guidance, not just a complaint.
- **Principle:** when you encode a project-specific rule (`extra='forbid'` required on wire-facing models, `taskId` required on SMS, etc.) into a custom linter, the failure message MUST tell the next agent how to fix it. Lint failures become first-class agent context. Without the fix, the agent has to guess; with the fix, the next iteration is direct.
- **Origin:** OpenAI Harness Engineering — "custom lint messages can include remediation instructions, meaning lint failures become part of the agent's context and guide the agent toward the correct fix." We don't have custom rules yet, but every new rule we write must follow this discipline from day one.
- **Reusable artifact:** rule-message template: `"<short failure>. Fix: <action> like <example>. See: <playbook-seed or docs link>."`
- **Risk if ignored:** lint failures repeat across PRs because agents don't know the canonical fix; the rule "works" but doesn't accelerate convergence.

### H.8 — `Any` at LLM / JSON boundaries must be pinned to `object` before return.
- **Principle:** `orjson.loads`, `json.loads`, and most LLM-output parsers return `Any` per their type stubs. Mypy strict's `no-any-return` rule fires the moment such a value crosses a function boundary. The fix is one line: assign to a locally-typed variable (`parsed: object = orjson.loads(text)`) and return the variable. Same pattern at every LLM-to-schema or untrusted-JSON-to-schema boundary in the codebase.
- **Origin:** S20 — `_parse_json` in `src/ef_ai/workflows/sms_format.py`. Will reappear in M6 (Insight coercer) and M7 (Statement coercer) for the same reason.
- **Reusable artifact:** the local-type-pin pattern. Could be promoted to a custom lint rule (F.3) once we have one or two more instances.
- **Risk if ignored:** every LLM-output boundary surfaces the same mypy strict error; agents waste cycles rediscovering the fix; or worse, they paper over with `# type: ignore` (anti-pattern per H.7).

### G.11 — Customer-source-doc → mirrored on three audience surfaces, single canonical source.
- **Principle:** when a customer hands over a canonical document (Error Handling Guide, requirement.md, security spec), mirror it on three surfaces with cross-references back to the original: (1) a sheet inside the customer-facing workbook (e.g. `Error Code Guide` sheet in `feature-list.xlsx`), (2) an appendix in the prose customer doc (e.g. `feature-catalog.md` Appendix B), (3) typed code constants (e.g. `EHG_*` in `schemas/common.py`). All three reference the canonical source by version and date.
- **Origin:** S18-bis — Error Handling Guide v1.0 ingestion. We landed all three surfaces on 2026-05-21 / 2026-05-25.
- **Reusable artifact:** the "canonical doc + 3 mirrored surfaces" template; cross-reference convention `(per <source name> v<version>, <YYYY-MM-DD>)`.
- **Risk if ignored:** surfaces drift apart; "what does the customer think err_code 422 means?" requires triangulating three places that no longer agree; customer trust erodes.

---

## Theme D — Working with prior AI output

### D.1 — Separate design IP from code IP.
- **Principle:** when reading another agent's output, two passes. First: what *decisions* did it make? (extract → adopt or reject.) Second: how much code is worth keeping? (almost always less than you'd think at <500 LOC.)
- **Origin:** S4.
- **Reusable artifact:** `docs/codex-audit.md` format — sections "Side-by-side decision comparison" vs "Code: strengths" vs "Gaps to fix".
- **Risk if ignored:** carry over working-but-misaligned code because "it tests green", patch around its assumptions forever.

### D.2 — Tests can be specifications even when the code they test is discarded.
- **Principle:** a passing test from a discarded codebase still tells you what the prior agent *believed* the behavior should be. Read tests as design docs.
- **Origin:** S5.
- **Reusable artifact:** the practice of reading `test_*.py` before deleting the SUT.
- **Risk if ignored:** lose the behavioral intent that was encoded in the tests.

### D.3 — Cross-language artifacts are operability debt.
- **Principle:** if the prior agent's docs are in a language the team can't operate in (e.g. Chinese AGENTS.md for a UAE team), this alone is enough to discard the doc — but not the decisions inside it.
- **Origin:** S4.
- **Reusable artifact:** AGENTS.md rule "no documentation in any language other than English".
- **Risk if ignored:** future agents can't follow the house rules; humans can't review them.

---

## Theme E — Verification

### E.1 — Run the tests; don't trust the markdown that says "tests pass".
- **Principle:** before adopting another agent's repo, run `make check` (or equivalent) yourself. Markdown can lie; the test runner can't.
- **Origin:** S4 — we couldn't run Codex's tests because of sandbox PyPI block, and explicitly flagged the gap to the user.
- **Reusable artifact:** a `git clone && make check` rule before any reuse.
- **Risk if ignored:** "Phase 2 completed" in someone's plan doesn't mean their phase 2 actually compiles on your machine.

### E.2 — Tests cite REQ-IDs and D-IDs in comments.
- **Principle:** every test has at least one comment naming the REQ or decision it covers, e.g. `# covers REQ-S-016, D-026`.
- **Origin:** S6 (AGENTS.md §3.3).
- **Reusable artifact:** AGENTS.md rule + the practice itself.
- **Risk if ignored:** future agents can't tell which tests are load-bearing vs incidental, and refactor away coverage of critical rules.

### E.3 — Defensive LLM output coercion: strip, unwrap, sentinel-check *before* schema validation.
- **Principle:** never feed raw LLM output into a pydantic model. Always pre-process in three explicit steps before validating: (1) strip markdown fences (` ```json `), (2) unwrap single-key envelopes (`{"data": {...}}` -> `{...}`), (3) check for a known "unrecognizable content" sentinel phrase. Each step maps to a distinct error class (markdown drift, envelope drift, refusal) and produces a specific `err_code` (602 vs 603) instead of one opaque "schema validation failed".
- **Origin:** S20 (M5) — `coerce_sms_output` in `src/ef_ai/workflows/sms_format.py`. Without the markdown strip the model's occasional fenced output would have triggered err_code 603; without the sentinel check a polite "this isn't a bank SMS" reply would have been miscategorised as schema mismatch.
- **Reusable artifact:** the `_strip_markdown_fence` + `_unwrap_single_envelope` + `_looks_unrecognizable` triad. Encapsulate as a tiny preprocessing pipeline in front of every LLM-to-schema boundary.
- **Risk if ignored:** every transient model formatting drift becomes a customer-visible "schema mismatch" error. The customer sees the same err_code for "model wrapped its answer in markdown" and "model returned outright garbage", losing actionable signal.

---

## Theme F — Operations and security baseline

### F.1 — Security gaps must be named, not refactored quietly.
- **Principle:** if you find a security issue in prior code (e.g. AppCode → scenario binding gap), record it as an explicit "gap to fix" item in the audit doc + a new decision. Don't just fix it silently in the rewrite.
- **Origin:** S4 (D-026 came from explicit gap recording).
- **Reusable artifact:** `docs/codex-audit.md` §4 "Gaps to fix" pattern.
- **Risk if ignored:** the rewrite contains the fix but no one knows there was ever a bug; same class of bug recurs next time.

### F.2 — Legal/compliance gates belong in decisions, not just deploy docs.
- **Principle:** anything PDPL/GDPR/HIPAA-flavoured must surface as a `proposed` decision with explicit risk-if-false. Decision becomes deploy-time legal gate.
- **Origin:** S2 (D-004 — "assume model endpoint is in PDPL-compliant jurisdiction").
- **Reusable artifact:** D-004's structure.
- **Risk if ignored:** "we'll handle compliance at deploy" — and then deploy day arrives, no one mapped the actual data path.

---

## Theme H — Schema design

### H.1 — Mirror the customer wire format in schema field names, then ignore lint warnings via config, not noqa.
- **Principle:** if the customer's contract has `taskId` (camelCase) and `err_code` (snake_case) mixed, pydantic field names should match exactly. Suppress lint rules via `per-file-ignores`, not per-line `# noqa`.
- **Origin:** S9.
- **Reusable artifact:** the `[tool.ruff.lint.per-file-ignores]` pattern in `pyproject.toml`.
- **Risk if ignored:** either noqa noise on every wire-facing model, or a layer of alias mapping that doubles the cognitive load of every serialization call.

### H.2 — Lock wire-format conventions as ADRs before bulk-writing schemas.
- **Principle:** decisions like "JSON keys are snake_case" or "amounts are strings, not numbers" must exist as a written ADR (`decisions.md` D-XXX) *before* writing 20+ classes that depend on them. Otherwise the convention is implicit, and the next slice silently breaks it.
- **Origin:** S9 — D-028 was added retroactively after writing the insight tree.
- **Reusable artifact:** discipline rule for any project with multi-file schema scope.
- **Risk if ignored:** mid-project the convention shifts, and all dependent code has to migrate.

### H.7 — Trust strict mypy's narrowing; don't preemptively `# type: ignore`.
- **Principle:** with `warn_unused_ignores = true` (strict-mode default), each unnecessary `# type: ignore` is an error, not a no-op. Modern mypy narrows types through `in <Literal set>` membership, `isinstance` checks, and exhaustive enums. Write the natural code, run mypy, add ignores only after a real error — and pin each to the exact rule code so churn is detectable.
- **Origin:** S10-bis — three `# type: ignore` comments preemptively scattered through `settings.py` all turned out to be unnecessary; mypy strict surfaced them on the first run.
- **Reusable artifact:** AGENTS.md §5 rule "no `# type: ignore` without an explicit mypy error message to justify it".
- **Risk if ignored:** code rot — agents add ignores defensively, the codebase ends up sprinkled with stale suppressions that hide real type errors when libraries upgrade.

### H.6 — Configure `src = ["src"]` for any project using src-layout.
- **Principle:** if the repo uses `src/<package>/` layout, every code-quality tool that does first-party/third-party classification must be told. For ruff, set `[tool.ruff] src = ["src"]` and `[tool.ruff.lint.isort] known-first-party = ["<package>"]`. Same for mypy, pyright, isort, etc.
- **Origin:** S9 — without `src = ["src"]`, ruff classified `ef_ai` as third-party and refused to accept any import order in tests. Two iterations of trial-and-error confirmed the symptom was grouping, not ordering.
- **Reusable artifact:** the `src = ["src"]` + `known-first-party` pair in `pyproject.toml`.
- **Risk if ignored:** lint failures that look like ordering bugs but are actually classification bugs; agents waste cycles swapping import order in circles.

### H.5 — When the linter offers an auto-fix, use it; don't guess the canonical form.
- **Principle:** for rules like import ordering (ruff `I001`), formatting (`black`), or simple fixups (`ruff --fix`), the tool itself is the source of truth. An agent that tries to manually replicate the expected order will iterate 2-3 wrong times before matching the tool. Pipe through `make format` (which wraps both) instead.
- **Origin:** S9 — after the first lint failure, I manually swapped import order to what I thought ruff wanted. The second `make check` still failed because ruff's default isort ordering wasn't what I guessed.
- **Reusable artifact:** the `make format` target combining `black` + `ruff --fix`; AGENTS.md rule "always run `make format` before `make check` after editing imports".
- **Risk if ignored:** wasted iterations on every lint failure; agent confidence erodes; CI shows the same class of failure over and over.

### H.4 — Ban ambiguous Unicode (en-dash, multiplication sign, ellipsis, NBSP, etc.) in code.
- **Principle:** AI agents writing prose default to typographic Unicode: `–` (en-dash), `—` (em-dash), `×` (mult), `…` (ellipsis), `→` (arrow), `≤`/`≥`, non-breaking spaces. Several of these are visually confusable with ASCII (`-`, `x`, `...`) and trigger `RUF001/RUF002`. Em-dash and arrow happen to slip through ruff's default confusables list, but the rule of thumb is: **use plain ASCII for code, docstrings, and field descriptions in ANY symbolic context.** Reserve typographic Unicode for end-user-facing markdown (READMEs, prose docs) only.
- **Origin:** three separate lint failures across S9, S10, S13 — first `–`, then `×`, then `…` in different files. Em-dash itself didn't trigger but matches the pattern.
- **Reusable artifact:** AGENTS.md §5 rule "use plain ASCII in code and docstrings"; `pyproject.toml` ruff config with `RUF` rules enabled.
- **Risk if ignored:** recurring lint failures across every PR an agent opens, plus subtle text bugs that break `grep`, `diff`, search-and-replace.

### H.3 — `extra="forbid"` on every public boundary model.
- **Principle:** every pydantic model that crosses the wire (request, response, callback) sets `model_config = ConfigDict(extra="forbid")`. Unknown fields fail validation.
- **Origin:** S9.
- **Reusable artifact:** the `_Forbid` base class pattern in `insight.py`.
- **Risk if ignored:** agents silently add fields; customer integration breaks long after the offending PR shipped.

---

## Theme J — Test infrastructure and DI

### J.1 — Factory-style app builders for test isolation.
- **Principle:** the `create_app(**overrides)` factory pattern lets tests construct a fresh app instance per test with injected fakes — no monkey-patching, no shared global state, no fixture file teardown gymnastics. Each test owns its dependencies; cross-test bleed is structurally impossible.
- **Origin:** M3 — `tests/contracts/test_adapter_routes.py` uses a `_build()` helper that returns `(TestClient, dify_mock, status_store)` per test. 15 end-to-end tests, zero shared state.
- **Reusable artifact:** `create_app(*, settings=None, authenticator=None, task_status_store=None, dify_client=None)` signature with keyword-only optional overrides; `_build()` helper at top of test module.
- **Risk if ignored:** monkey-patched dependencies leak across tests; failures depend on test ordering; CI flakes that don't reproduce locally.

### J.2 — Frozen dataclasses for boundary results.
- **Principle:** when a function returns a structured outcome (auth check, dispatch record, task record), use a `@dataclass(frozen=True)` (or pydantic with `frozen=True`). Tests assert with simple equality (`assert record == DispatchRecord(...)`); immutability blocks accidental mutation in handlers.
- **Origin:** M3 — `AuthResult`, `DispatchRecord` immutable; `TaskRecord` mutable but only via `dataclasses.replace` in the store. Tests stay declarative.
- **Reusable artifact:** the dataclass-as-result pattern visible in `validation/auth.py` and `clients/dify.py`.
- **Risk if ignored:** mutable result objects encourage handlers to "patch in place"; tests grow brittle assertions about call sequences instead of clean equalities.

### J.3 — Coverage gaps are design tells, not metric targets.
- **Principle:** when a module sits at 36% coverage while everything else is 100%, that's a signal — usually that a production-critical code path (JSON env parsing, error fall-through) lacks a test. Don't add coverage to "hit a number"; add coverage where the gap reveals untested behavior. Likewise, 100% coverage doesn't mean correctness — it means you've executed every line at least once.
- **Origin:** S10-bis — `settings.py` was at 36% because tests only exercised the default-factory path; JSON parsing branch was production-critical and untested. Adding 9 test cases pushed coverage to ~98% AND uncovered no real bugs, but the *act of looking* validated the code.
- **Reusable artifact:** `pytest --cov=...` output as a design review tool, not a CI gate threshold.
- **Risk if ignored:** either gaming coverage with trivial tests, or chasing 100% as theatre.

### J.4 — Integration tests drive in-process FastAPI mocks via `httpx.ASGITransport` + `LifespanManager`.
- **Principle:** when a workflow needs to be tested end-to-end across multiple HTTP boundaries (here: workflow code -> customer callback), spin up the mock callback FastAPI app **in the same process** and mount it as an `httpx.ASGITransport`. Wrap it in `asgi_lifespan.LifespanManager` so startup / shutdown events run. No port binding, no socket leakage, no flakiness from "address already in use", and async paths are exercised exactly as production runs them. Tests complete in milliseconds because there is literally no network involved.
- **Origin:** S20 (M5) — `tests/integration/test_sms_workflow.py` runs the M4 mock callback in-process for 8 end-to-end scenarios (5 happy-path fixtures + FAIL_ONCE + ALWAYS_FAIL + unrecognisable-content terminal-skip). Total runtime under 200 ms for all 8.
- **Reusable artifact:** the `_mock_callback_client` async context manager pattern — a single helper that yields `(httpx.AsyncClient, recorder)` per test. Combine with `FakeSleeper` (no real time waits) to drive retry loops in microseconds.
- **Risk if ignored:** integration tests either (a) use real HTTP, accumulating port assignments and CI flakiness, or (b) get skipped locally and pushed to a slower CI lane where developers stop running them. Either way, the team loses fast feedback on the most expensive-to-debug class of bugs (cross-boundary contract drift).

---

## Theme K — Service architecture

### K.1 — Customer-facing adapter is separate from workflow orchestrator.
- **Principle:** never put the customer's stable API contract inside the workflow engine that you'll change weekly. Put a thin Python (or Go, or whatever) adapter in front. Adapter owns: URL shapes, auth, request validation, idempotency, sync ack, async dispatch. Workflow owns: AI/business logic, model calls, callback assembly, retry. Changing one doesn't break the other.
- **Origin:** D-021, surfaced from Codex audit (S4). Our original implicit plan was "Dify Code nodes do everything"; Codex's explicit split was the better idea.
- **Reusable artifact:** the `src/ef_ai/adapter/` (Python FastAPI) + `dify_dsl/` (workflow definitions) split visible in this repo. Replace `dify_dsl/` with any orchestrator (Temporal, n8n, Step Functions) and the principle holds.
- **Risk if ignored:** every workflow tweak risks the customer-facing contract; every contract clarification forces a workflow change; customer integration tests become flaky.

### K.2 — One typed Settings object for env config; never sprinkle `os.getenv`.
- **Principle:** every env var the app cares about lands in a single `Settings` class (pydantic-settings, environ-config, etc.). Modules consume `settings.foo`, never `os.getenv("FOO")`. The Settings class becomes the discoverable contract — `.env.example` writes itself from it.
- **Origin:** M3 — `adapter/settings.py` consolidated `APP_CODES_JSON`, `TASK_STATUS_TTL_DAYS`, `CALLBACK_HMAC_ENABLED` and validated at parse-time, catching bad values at startup instead of mid-request.
- **Reusable artifact:** the pydantic-settings pattern in `adapter/settings.py` (typed fields + `@field_validator` for env-aware parsing).
- **Risk if ignored:** drift between `.env.example` and reality; "works on my machine" because someone set an env var no one else knew about; production crashes from missing config that should have been validated at startup.

### K.4 — Subagent dispatch via concurrent Agent calls delivers context isolation + parallelism even when OS-level worktrees are unavailable.
- **Principle:** When N ≥ 3 tasks of a milestone are mostly independent, dispatch fresh general-purpose subagents in waves of up to 3 (single message with multiple Agent tool calls = concurrent execution). Each subagent receives full inline task context; none inherits prior session history. The controller orchestrates waves, runs verification, and performs two-stage review per task. This produces parallelism + context isolation without requiring `git worktree` support.
- **Origin:** S22 — M6 Insight workflow: 6 tasks dispatched as Wave 1 (3 concurrent: callback shim / coercer + fallback / prompt) + Wave 2 (2 concurrent + 1 sequential: route+DSL / fixtures / integration test). Wall-clock ~10 min; 198 tests green on first Mac verify. Sandbox FUSE blocks `git worktree add` — proved subagent dispatch still works when the tree is shared and task scopes are non-overlapping.
- **Reusable artifact:** the Wave-1/Wave-2 dispatch envelope from `docs/m6-plan.md` §"Subagent dispatch plan"; per-subagent prompt template with status semantics (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED). D-038 codifies adoption.
- **Risk if ignored:** parallel work serializes; controller's main context fills with implementation details; quality drift across tasks because no fresh-context discipline.
- **Tradeoff / cost of adoption:** tokens-per-turn grows substantially (each subagent gets a few KB of inline context); requires careful prompt design so the subagent does not lack reference files; controller review burden scales linearly with task count (2 reviews × N tasks); subagents can "lie about DONE" — every task closure requires controller's own `make check` verify, not just the subagent's report. Not worth it for milestones with <3 independent tasks; serial execution wins on those.

### K.5 — Internal consistency guards between data dictionaries and their consumers.
- **Principle:** When a data module (constants, templates, mappings) is consumed by both production code and test fixtures, add a test that walks the data module and asserts every entry is reachable from at least one consumer. Drift between dictionary and consumer becomes a test failure, not a silent runtime surprise.
- **Origin:** S22 — Subagent B (M6 Task 2) added an unsolicited 12th test `test_complete_tree_covers_all_fallback_paths` that walks all 26 `FALLBACK_TEMPLATES` entries and asserts they correspond to actual leaf paths in `InsightTree`. Without this guard, adding or removing an insight leaf would leave the fallback dict silently stale.
- **Reusable artifact:** the "data module + walker test" pattern: one test per data module that enumerates the module and asserts coverage against the consumer's expected structure.
- **Risk if ignored:** silent drift; the dictionary grows stale relative to the consumer; a year later nobody knows which entries are reachable, and removing schema fields silently orphans data.
- **Tradeoff / cost of adoption:** the walker test needs intentional update when schema changes (false-positive failures on schema migrations until the walker is updated). For very large data modules (>1k entries), the walker can slow the test suite — acceptable tradeoff but worth measuring. Skip this pattern when the data module is so small (≤5 entries) that drift is implausible.

### K.6 — Subagent prompts should specify the bar but leave room for discretionary contributions.
- **Principle:** When dispatching a subagent, specify the goal + acceptance criteria + cited REQ-IDs, but explicitly allow the subagent to add bonus tests, drift guards, helpers, or refactorings within ≤5 min of additional scope. Their "I noticed X" in the status report is signal: a thoughtful addition reveals where the original brief was incomplete.
- **Origin:** S22 — Three of the six M6 subagents made unsolicited improvements that made the final codebase materially better. Subagent B added a drift-guard test (now K.5). Subagent E built a `_fallback_leaf(path)` helper that imports the truth source instead of copying strings (eliminates a maintenance burden the brief did not flag). Subagent F added a substring guard alongside strict equality in the fallback-delivery test (defence-in-depth against silent template rewording). None were in the brief; all three improved the codebase.
- **Reusable artifact:** subagent prompt format includes one sentence: "If you spot anything else worth doing for ≤5 min of additional scope, do it and mention it in your status report; we'll judge whether to keep it." Controller reviews the discretionary contribution in the same two-stage review pass as the main task.
- **Risk if ignored:** subagents follow briefs mechanically; opportunities to harden against drift, add observability, or simplify are missed; the controller's spec becomes the only source of test coverage, even when the subagent could have surfaced a better one organically.
- **Tradeoff / cost of adoption:** not every discretionary contribution is good — some are over-engineering or off-topic. Reviewer must judge each on the merits; "no, don't keep that" is a valid outcome. Adds slight scope-creep risk per task (mitigated by the ≤5 min ceiling). Doesn't help with junior models that lack the judgement to know which bonuses are valuable.

### K.7 — Code-quality review delegated to a fresh subagent catches integration drift the controller misses.
- **Principle:** Two-stage review (spec compliance + code quality) is strictly stronger when Stage 2 is dispatched to a fresh subagent rather than performed by the controller. The controller, having drafted task briefs and read every subagent's status report, has anchoring bias: it sees what it expected to see. A fresh reviewer reads only the diff + seeds + plan, and notices what the controller skimmed past.
- **Origin:** S23 — M7 Wave 2 Stage-2 subagent caught a MAJOR runtime ImportError: `statement.yaml` Code node imported `compensation_queue_from_env` and `enqueue_sync` from `obs_compensation.py` — neither symbol existed (Subagent F wrote against an API Subagent E didn't ship). Controller-side review of the same diff in M6 had passed equivalent inter-task contract checks visually without catching this class of failure. Wave 1 Stage-2 also caught a docstring-vs-implementation drift in `statement_format.py` pipeline ordering — minor, but representative.
- **Reusable artifact:** Stage-2 subagent prompt: read-only, no editing/running tests, output `APPROVED / MINOR_CONCERNS / MAJOR_CONCERNS` with FILE:LINE citations. ~10-15 min per Wave. See M7 plan §"Two-stage review (literal pattern, M7-specific)".
- **Risk if ignored:** controller-only review misses cross-subagent contract drift; "I dispatched both, so I'd notice if they didn't fit" turns out false at the API-name level.
- **Tradeoff / cost of adoption:** tokens — each Stage-2 review burns ~20-40k tokens depending on diff size. Latency — adds 5-15 min per Wave. Wrong-positive risk: Stage-2 may complain about cosmetic issues the controller would have shipped. Not worth it for ≤2-task Waves where the controller can spot drift in a single read.

### K.8 — Cross-subagent contract surfaces (factory names, sync/async semantics, env var names, AND implementing modules) drift silently when each subagent ships in isolation.
- **Principle:** When two subagents in the same Wave touch a shared contract — one defines a public symbol (`compensation_queue_from_env`), the other imports it — they may disagree about name, signature, or sync/async semantics. The Wave-2 dispatch envelope must either (a) freeze the contract in the plan doc before dispatch, or (b) include a controller "merge check" between the diffs before Stage-1 review. A fresh Stage-2 review (K.7) reliably catches the residue, but the cheaper guardrail is making the contract explicit upfront. **Contract surfaces must enumerate the IMPLEMENTING module, not just the URL/symbol** — listing `POST /mock/calls` is not enough; the plan must also say "implemented by `src/ef_ai/mock_callback/main.py:create_app`" so the subagent shipping the URL reference knows whose responsibility it is to ship the route.
- **Origin:** S23 — Wave 2 of M7: Subagent E (compensation worker) and Subagent F (Dify DSL) disagreed on `compensation_queue_from_env` / `enqueue_sync` — Stage-2 caught the runtime ImportError. S24 — Wave 1 of M8: Subagent C documented `/mock/calls` and `/mock/calls/{call_id}` in OpenAPI + Postman without anyone shipping the routes in `mock_callback/main.py`. Subagent D (Wave 2) self-spotted the gap and filled it (K.6 dividend), but only by luck — K.8 §3 listed the URLs without naming the implementing module. Amendment: contract surfaces must enumerate where each surface is implemented.
- **Reusable artifact:** In plans with ≥2 subagents that touch a shared module, add a "Shared contract" subsection listing every public symbol both sides will import AND the implementing file path. Lock it before dispatch.
- **Risk if ignored:** runtime ImportError in production OR latent gap (route documented but not implemented) that surfaces only when a downstream consumer hits the missing endpoint. Worse: the latent gap may pass Stage-2 review (the reviewer doesn't grep for implementations of every URL).
- **Tradeoff / cost of adoption:** plan-doc length grows by ~5-10 lines per Wave. Locks subagent flexibility on symbol naming (could be too rigid for refactor-heavy Waves). Mitigation: contract surface lists names + signatures + implementing module, not implementations — the subagent shipping the impl is still free to design the body.

### K.9 — Subagent self-spotting cross-Wave gaps is the K.6 dividend at peak value.
- **Principle:** K.6 (subagent discretion within scope) produces its highest-impact outcomes when a subagent in Wave N spots and fills a gap left by a subagent in Wave N-1. The downstream subagent has fresh eyes on the joined surface area and can see what the upstream subagent's status report missed. This is qualitatively different from in-Wave bonus tests — those harden a single task; cross-Wave gap-fills repair the integration boundary.
- **Origin:** S24 — M8 Wave 2 Subagent D was wiring `app.mount("/mock", ...)` in lifespan, and noticed the Postman collection (Wave 1 Subagent C) referenced `GET /mock/calls` and `GET /mock/calls/{call_id}`. Subagent D checked `mock_callback/main.py` and found those routes missing. Filled the gap unsolicited (K.6 discretion), respected existing route patterns, returned `dict[str, object]` matching the recorder shape. Stage-2 reviewer marked it KEEP and noted "this is exactly the kind of cross-Wave gap-fill K.7 review is designed to catch — but here Subagent D self-spotted it, which is the K.6 dividend."
- **Reusable artifact:** subagent prompt template should explicitly invite this pattern: "If you notice that an earlier Wave referenced a symbol/route/file you can see is missing, fill the gap and report it as K.6 bonus." Higher-resolution invitation than the generic "spot adjacent improvements within ≤5 min".
- **Risk if ignored:** cross-Wave gaps survive into Stage-2 review (which catches them but later than the source) or further into runtime (which catches them only when a downstream consumer hits the missing surface).
- **Tradeoff / cost of adoption:** rewards Subagent N for fixing Subagent (N-1)'s oversight — could create blame-shifting if not framed as collaborative. Reviewer must judge whether the gap-fill is in-scope or scope-creep. Doesn't replace K.8 (still better to lock contracts upfront), but supplements it.

### H.10 — `asyncio.create_task` needs `Coroutine`, not `Awaitable`; type your hook accordingly.
- **Principle:** When defining a callable type alias for an async hook that will be passed to `asyncio.create_task(...)`, use `Callable[[...], Coroutine[Any, Any, T]]`, not `Callable[[...], Awaitable[T]]`. mypy strict mode rejects the `Awaitable` form because `create_task` requires the strict `Coroutine` subset, not the looser `Awaitable` interface. `async def` functions return `Coroutine` automatically, so the change is invisible to implementers — they just `async def hook(...) -> T` and it satisfies the alias.
- **Origin:** S24 — M8 dify.py:85 mypy strict error: `Argument 1 to "create_task" has incompatible type "Awaitable[None]"; expected "Generator[Any, None, Never] | Coroutine[Any, Any, Never]"`. Subagent A had typed the hook as `Callable[[DispatchRecord], Awaitable[None]]` (technically permissive, but `create_task` is stricter). Fix: change to `Callable[[DispatchRecord], Coroutine[Any, Any, None]]`. Same root cause as H.8 — the boundary type must match the consumer's contract, not the upstream abstract concept.
- **Reusable artifact:** project convention — async hook type aliases use `Coroutine[Any, Any, T]` whenever the hook is consumed by `asyncio.create_task` or `asyncio.ensure_future`. `Awaitable[T]` is fine for hooks consumed by `await` alone, but write `Coroutine` by default so future code is free to call `create_task` without retyping.
- **Risk if ignored:** mypy strict fails on Mac (sandbox may pass if mypy isn't fully strict there); fix requires `cast(...)` or refactor; reviewers waste cycles debating Awaitable-vs-Coroutine.
- **Tradeoff / cost of adoption:** none — `Coroutine` is strictly stronger than `Awaitable` for `async def`-produced callables. No flexibility lost. Only cognitive shift: developers used to typing hooks as `Awaitable` learn the asyncio-specific stricter type.

### C.8 — Unused `# type: ignore` directives are a signal, not noise — remove them, don't normalize them.
- **Principle:** When mypy reports `Unused "type: ignore" comment [unused-ignore]`, the developer's first instinct is often to add `--ignore-unused-ignores` or downgrade the rule. Don't. The directive was a workaround for a problem that no longer exists (config change, library type-stub update, refactor); leaving it means future grep-ers think the bug is still there. Remove every `unused-ignore` finding immediately, in the same commit as the mypy run that surfaced it.
- **Origin:** S24 — M8 cleanup: `fake_dify_orchestrator.py` had three `# type: ignore[import-not-found]` directives on `from tests.gold.*` imports. The original author believed mypy couldn't resolve them from `src/` scope. mypy strict on the project's actual config DID resolve them (tests/ is sys.path-visible), so the ignores were dead. Mac mypy flagged with `unused-ignore`; sandbox mypy hadn't surfaced this because sandbox couldn't run mypy at all (Python version mismatch). Removed all three; no replacement needed.
- **Reusable artifact:** every milestone closure has an `unused-ignore` sweep step — `mypy --strict src 2>&1 | grep unused-ignore` then delete each line.
- **Risk if ignored:** type-ignore litter grows; new contributors copy them as "the way things are done here"; real type errors hide behind noise.
- **Tradeoff / cost of adoption:** minor — each `unused-ignore` is a one-line delete. No downside. The only edge case is platform-conditional ignores (e.g. `# type: ignore[attr-defined]  # only on Windows`) — these are rare and should be wrapped in `if sys.platform == ...` blocks anyway, not raw comments.

---

### G.12 — Per-milestone retrospective with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts.
- **Principle:** At every milestone closure, write a retrospective doc that scores each new discipline added in the last cycle. Each item gets one of four verdicts: PULLED WEIGHT (used, paid off, evidence shown), PARTIAL (used but didn't deliver full claim), THEORETICAL (added but not exercised), TOO EARLY (insufficient N to judge). The doc is not "what we built" — it is "what each new process actually delivered to the codebase". Prevents discipline cargo-culting: every added rule must justify itself across milestones.
- **Origin:** S22 — `docs/m6-retrospective.md` was the first instance; S23 — `docs/m7-retrospective.md` is the second. Two data points proved the format catches things `process-log.md` does not: process-log captures "we did X", retrospective captures "X actually did Y for us".
- **Reusable artifact:** the m6/m7-retrospective.md template — verdict line per discipline, 1-paragraph evidence per verdict, "Implications for M{N+1}" section that becomes the next plan's checklist.
- **Risk if ignored:** disciplines accumulate without measurement; "we follow K.5 because we always have"; team can't tell which rules pay off vs which are dead weight.
- **Tradeoff / cost of adoption:** ~30 min per closure cycle; requires honest self-grading (some PARTIAL / THEORETICAL grades sting); risk of retroactive rationalisation if scored carelessly. Skip if a milestone added zero new disciplines.

### H.9 — Async function `timeout` parameter names trip ruff ASYNC109; use `deadline_seconds` instead.
- **Principle:** ruff's ASYNC109 flags `async def foo(timeout: float = 1.0)` because the caller's natural reaction is to write `await foo(timeout=5)` instead of `async with asyncio.timeout(5): await foo()`. The fix is parameter rename, not lint suppression. `deadline_seconds`, `max_wait_seconds`, or `budget_seconds` all read naturally and don't collide.
- **Origin:** S23 — M7 ruff cleanup: `_wait_until(predicate, *, timeout: float = 1.0)` and `_drain_queue(..., timeout: float = 1.0)` both tripped ASYNC109. Rename to `deadline_seconds` was a 1-line fix; suppression via `# noqa: ASYNC109` would have been the lazy path.
- **Reusable artifact:** project convention — when writing an async helper that polls a predicate within a budget, name the budget parameter `deadline_seconds` (not `timeout`).
- **Risk if ignored:** `# noqa: ASYNC109` accumulates; reviewers can't tell which suppressions are intentional contract decisions vs lazy bypass.
- **Tradeoff / cost of adoption:** minor cognitive shift — `timeout` is the C-stdlib word for this concept. Mitigation: docstring explicitly calls out the rename rationale.

### C.7 — Sandbox-as-canary: run ruff in the dev sandbox even when pytest cannot.
- **Principle:** When the local sandbox Python version mismatches the project's required version (e.g. Python 3.10 sandbox vs 3.11 project), `make check` won't run end-to-end. But ruff is version-agnostic at the AST level — it will still flag style/lint drift before the Mac round-trip. Wire a sandbox-friendly `make lint-only` (or accept ruff as a single command) so the controller catches 90% of cleanup work pre-push.
- **Origin:** S23 — M7 cleanup: 14 ruff errors caught on Mac after first push attempt. Subsequently ran `~/.local/bin/ruff check src tests` in the sandbox (Python 3.10 incompatible with 3.11 project) and found the same 14 issues without needing Mac round-trip. 6 of 14 were auto-fixable in-place; the rest fixed via Edit. Saved ~3 Mac round-trips.
- **Reusable artifact:** `make lint-only` target that runs `ruff check src tests` and nothing else; cheap to add. Reference in AGENTS.md §3.x as the pre-push canary.
- **Risk if ignored:** cleanup loops via Mac become long-tail; each ruff round trip is 30-60s + context switch; teams either push dirty (CI ruff fails) or stop using ruff aggressively.
- **Tradeoff / cost of adoption:** ruff may flag a small number of false positives that only matter on the target Python version — extremely rare. The 99% case is "if it lints clean in sandbox, it lints clean on Mac".

### F.4 — `_repo_root()` walker as the portability anchor; never use `Path("./x")` for runtime defaults.
- **Principle:** Any module that needs a default filesystem path (mock OBS folder, gold fixture root, sample corpus directory) must resolve it via a `_repo_root()` helper that walks up from `__file__` until it finds `pyproject.toml`. `Path("./x")` is cwd-dependent — works in dev because everyone runs `make` from the repo root, breaks the moment someone runs `python -c "from foo import bar"` from `/tmp`. The walker is 6 lines, cacheable, cwd-agnostic.
- **Origin:** S23 — M7 Task 1 implemented `_repo_root()` for `FilesystemOBSClient` defaults (portability principle from the M7 plan). Closure smoke `cd /tmp && python -c "from ef_ai.clients.obs import obs_client_from_env; print(...)"` proved cwd-independence.
- **Reusable artifact:** the `_repo_root()` snippet — `@cache; walks up from Path(__file__).resolve().parent while sentinel file (pyproject.toml) not present`. Drop-in for any module needing a repo-relative default. Pair with a unit test `test_repo_root_helper_finds_pyproject` that asserts the helper finds the project root.
- **Risk if ignored:** "works on my machine"; new contributors hit `FileNotFoundError` on first clone; CI flakes when `cwd` shifts between steps.
- **Tradeoff / cost of adoption:** trivial — 6 lines per project. The walker has a corner case (no `pyproject.toml` found → `RuntimeError`); tests must cover the case for completeness. Adds one cached lookup at first use; near-zero runtime cost.

---

## Theme I — Status snapshots

### I.1 — Roadmap files are snapshots, not state.
- **Principle:** progress trackers like `docs/roadmap.md` should be treated like decisions in `docs/decisions.md` — supersede, don't edit. When status changes meaningfully, write a new dated file and update the README link, leaving the old roadmap as a historical artifact. This preserves the "where we were at moment X" view for retrospectives and the manager demo.
- **Origin:** S10 (M3 kickoff) — user explicitly asked to keep the initial roadmap historical rather than overwriting it as we ship milestones.
- **Reusable artifact:** AGENTS.md §3.4.1 rule; README link convention pointing to the *current* snapshot.
- **Risk if ignored:** lose the trail of "we used to think we were 20% done, now we know it was actually 30%"; training deck and manager demo lose their before/after texture.

---

## Theme G — Multi-deliverable projects

### G.1 — If the final output needs a "how we got here" narrative, open the capture file before the work starts.
- **Principle:** any project that will end with a presentation / demo / retrospective needs a build diary, not a post-hoc reconstruction. Diaries lose ~70% of nuance when rebuilt from chat or commit history alone.
- **Origin:** S8 — user asked "are you tracking the journey of the *generalization* too?", surfacing a deliverable I had been treating as a final artifact only.
- **Reusable artifact:** `docs/process-log.md` Phase-N placeholder section pattern; `docs/deliverables-plan.md` listing audience + raw-material dependency per deliverable.
- **Risk if ignored:** the manager demo becomes a polished lie about a linear path that wasn't linear; the audience can tell.

### G.4 — Internal docs and customer-facing docs are different artifacts; keep them separate.
- **Principle:** an engineer-facing PRD (REQ-IDs, decision references, internal terminology) and a customer-facing feature catalog (business value, SLAs, acceptance criteria, scope boundaries) are two different documents serving two different audiences. Never reuse one as the other. The act of translating between them surfaces silent assumptions the original carried.
- **Origin:** S14 — drafting `docs/feature-catalog.md` from `docs/prd.md` revealed that D-025 (idempotency policy) had never been raised as a customer question, only as an internal assumption.
- **Reusable artifact:** the dual-doc pattern — internal `docs/prd.md` for engineering; customer-facing `docs/feature-catalog.md` for stakeholder review. Cross-link them from README under separate sections.
- **Risk if ignored:** customer sees internal jargon and loses confidence; or engineering reads customer marketing and ships under-specified.

### G.3 — A two-tier closure checklist replaces "did you remember to update X?".
- **Principle:** every slice and every milestone closes by walking an explicit checklist (per-slice for tactical, per-milestone for strategic audit). The agent ticks it in the final reply. The user never has to ask "did you update process-log / decisions / AGENTS / roadmap / playbook?". Skipped items are explicit `[ ]` with reasons; missed items are surfaced and amended in the next slice via a log entry, never via a silent edit.
- **Origin:** S12 — by M3 the cadence of "what should I have updated?" started costing energy. The user proposed a checklist so the agent self-audits at close instead of relying on prompts.
- **Reusable artifact:** `docs/closure-checklist.md` §A (per-slice), §B (per-milestone), §C (per-phase). Referenced from AGENTS.md §7 DoD.
- **Risk if ignored:** capture discipline collapses gradually — first one slice forgets to update `playbook-seeds.md`, then three, then the manager-demo retrospective has to be rebuilt from chat history.

### G.2 — Distinguish "deliverable" from "artifact" from "raw material."
- **Principle:** a deliverable (e.g. a manager demo) is composed of artifacts (e.g. a slide deck, a live coding session), which are composed of raw material (e.g. a build log, a decisions file, a screenshot). Plan capture at the raw-material level, not the deliverable level.
- **Origin:** S8.
- **Reusable artifact:** `docs/deliverables-plan.md` "Raw material it needs" sections.
- **Risk if ignored:** project ends with deliverables specified but materials missing; everyone scrambles.

### G.5 — Single-file dual-audience via an explicit Customer-Visible column.
- **Principle:** when one workbook serves both customer review and internal handoff, add a `Customer-Visible: Yes / No` column instead of maintaining two parallel files. Tint internal-only rows for visual reinforcement (pale yellow works).
- **Origin:** S18 — the annotated workbook gained a Customer-Visible column for P.06 / O.05 / CR.05; avoided two parallel xlsx files drifting apart.
- **Reusable artifact:** the column convention + the row tint.
- **Risk if ignored:** two parallel files drift; agents update one and forget the other; the "should the customer see this?" call gets made inconsistently per row.

### G.6 — Soft-framing for cross-team dependencies that have not landed yet.
- **Principle:** when an upstream doc is still pending (Error Handling Guide, requirement.md, security review), rows that depend on it use a placeholder phrase like `"per <doc name> (delivered separately)"`. Greppable later, vague enough to stay valid in the interim. When the doc lands, sweep and replace.
- **Origin:** S18 — five feature-list rows said "unified error envelope per Error Handling Guide" before the Guide existed. S18-bis swept those after the Guide arrived. Zero silent drift.
- **Reusable artifact:** the placeholder-phrase convention, paired with a `when_<doc>_has_come.txt` playbook describing the exact sweep recipe for the next agent.
- **Risk if ignored:** rows either hardcode guesses (wrong values when the real doc lands) or stay blank (customer notices the gap).

### G.7 — Hand-off files written FOR future agents are first-class deliverables.
- **Principle:** when a session might be picked up by a future agent (account switch, mid-flight work, team handoff), write `handover.txt`, `note.txt`, and `when_<X>_has_come.txt`-style files that an LLM can read top-to-bottom and proceed without further onboarding. Plain ASCII, English, self-contained.
- **Origin:** S0 (the handover.txt received at session start) and S18 (the note.txt + when_error_handling_guide_has_come.txt produced for the team).
- **Reusable artifact:** the three-file pattern — general project state / this-turn's changes / event-triggered playbook.
- **Risk if ignored:** every new agent session burns 30-60 minutes on context recovery; user re-onboards the agent manually every time.

### G.8 — Numbered question list with recommendations, not open-ended Q&A.
- **Principle:** when the agent needs N decisions from the user, present them as a numbered list (1..N), each with options + a recommendation. User responds per-number in batch.
- **Origin:** S18-bis — 13 decisions resolved across two user replies; total turnaround under 30 minutes vs probable hour+ of unstructured Q&A.
- **Reusable artifact:** the `Karar N — <topic>: <context>. (Önerim: ...)` (or `Decision N — <topic>: <context>. Recommended: ...`) format.
- **Risk if ignored:** either over-asking (agent paralyzes), under-asking (silent guesses), or unstructured Q&A (user cannot answer in batch).

### G.9 — PM-friendly risk register: cap at 7 items, two lines each, zero engineer vocabulary.
- **Principle:** a risk register a non-engineer PM scans in 2 minutes needs a strict format: ranked, bold title <= 6 words, one business-language sentence describing the risk, one sentence on the next step. No DSL / namespace / container-cluster vocabulary. Cap at 5-7 items.
- **Origin:** S18-bis — iterated from 10 detailed risks to "first 7, PM language, shorter" in three rounds before the format clicked.
- **Reusable artifact:** the format itself + AGENTS.md rule "translate to business-language when audience is non-engineer".
- **Risk if ignored:** PMs glaze over; risks do not get owned; every review starts the risk discussion from scratch.

### G.10 — Share a literal sentinel string between the system prompt and the output coercer.
- **Principle:** when a workflow needs to distinguish "model refused / gave up" from "model returned malformed output", commit a specific sentinel phrase that the prompt instructs the model to emit on refusal, AND match the exact phrase in the coercer. The two artifacts (`prompts/<x>_system.md` and `src/ef_ai/workflows/<x>_format.py`) are coupled by that string. Document the coupling in both files so the next agent can't drift one without the other.
- **Origin:** S20 (M5) — the prompt instructs the model to reply `"Unrecognizable content: not a bank transaction SMS."` on non-bank input; the coercer's `_UNRECOGNIZABLE_MARKERS` set contains the same lowercase substring. Matching produces err_code 602 instead of err_code 603, surfacing the right business meaning to the customer.
- **Reusable artifact:** the constant-set + the matching prompt line; cross-references at the top of both files pointing at each other.
- **Risk if ignored:** prompt and coercer drift; "model refused" silently degrades to "model produced garbage"; customer integration logic that treats 602 differently from 603 (e.g. retry vs surface to end-user) breaks invisibly.

---

## Future seeds — to be added as we go

- [ ] How to slice work for vibe coding (schemas → routes → integrations → workflows → infra)
- [ ] When to introduce sub-agents vs solo-agent
- [ ] Gold dataset strategy for AI-output validation
- [ ] When to break decisions.md into per-file ADRs (size threshold)
- [ ] Prompt versioning practice (`prompts/` folder convention)
- [ ] Dify workflow DSL diffing and review hygiene


---

## ★ v1.1 ADDENDUM (2026-06-01 — promoted to v2.0 baseline 2026-06-02)

5 ACTIVE + 3 CANDIDATE seeds added at pipeline v1.1 baseline, carried into v2.0 unchanged.

### F.6 — Secret scanning is non-optional (ACTIVE; v2.0 names gitleaks specifically)
- **Principle:** every commit runs a secret scanner (gitleaks). Pre-commit hook + CI gate. v2.0 also fires via .claude/settings.json PreToolUse hook before writes to .env/*.env*.
- **Origin:** RedHunt Labs Project Resonance Wave 15 — 25,000 unique secrets exposed across vibe-coded sites.
- **Reusable artifact:** Stage 2 internal commit-gate (HOOK), `.gitleaks.toml`, Makefile `make secrets` target, CI gate.
- **Risk if ignored:** secrets leak into git history; rotation cost is high.
- **Tradeoff:** ~5 minute setup, ~2 second per commit overhead. Effectively free.

### F.7 — Dependency vulnerability scan at every closure (ACTIVE)
- **Principle:** run `pip-audit` at Stage 4.1 Quality Gate + per-PR CI. Block on KNOWN CVEs.
- **Origin:** industry consensus + Veracode 45% finding extends to dep CVEs.
- **Reusable artifact:** Stage 4.1 Quality Gate checklist; `pyproject.toml` dev dep `pip-audit>=2.7`; Makefile `make deps` target.
- **Risk if ignored:** known CVEs ship; supply-chain risk accumulates.
- **Tradeoff:** ~10 seconds per closure; near-zero false positive rate.

### F.8 — Hallucinated-dep / slopsquat check (ACTIVE)
- **Principle:** every new `import X` triggers verification: does X exist on PyPI? Last release < 12 months? Maintainer trustworthy?
- **Origin:** Virginia Tech / UTSA / Oklahoma slopsquatting study (576k samples, 20% hallucination rate, 58% recurrence). MITRE ATT&CK T1195.001.
- **Reusable artifact:** Stage 2 internal commit-gate; mechanical check (`pip index versions X` + age check).
- **Risk if ignored:** agent installs non-existent or malicious package.
- **Tradeoff:** ~5 seconds per new dep; small.

### F.9 — Done Evidence template (ACTIVE)
- **Principle:** every task ends with structured Done Evidence: files changed, tests run + outcomes, assumptions, new ADRs, risks queued. PASS verdicts cite `file:line` evidence per acceptance criterion. v2.0 makes this a permission-matrix §11 BLOCKING criterion if absent.
- **Origin:** Phase-1 AGENTS.md sec.3.6 prose form worked but was rebuilt every closure. Replit fabricated-completeness incident shows cost of "trust me" prose.
- **Reusable artifact:** Stage 4.3 closure manifest; AGENTS.template.md §7.
- **Risk if ignored:** reviewers can't audit; fabricated completeness ships.
- **Tradeoff:** ~5 minutes per closure; reusable structure.

### C.9 — No LLM-driven revert; permission matrix governs (ACTIVE)
- **Principle:** agents shall not run `git reset --hard`, `git push --force`, `git checkout --` outside controlled recovery, or any destructive op without explicit user approval. Encoded in `permission-matrix.md` §5. v2.0 candidate for PreToolUse hook promotion.
- **Origin:** Replit DB-deletion incident (July 2025) — agent bypassed "code freeze" and destroyed prod DB.
- **Reusable artifact:** `permission-matrix.md` §5 Destructive operations; `permission-matrix.md` §11 Catastrophe-class.
- **Risk if ignored:** catastrophic data / history loss.
- **Tradeoff:** zero ongoing cost.

---

### F.5 — Veracode-style SAST scan (CANDIDATE)
- **Principle:** when project touches auth / PII / payment surface, run SAST scan (Veracode, Semgrep, CodeQL) at Stage 4.1 Quality Gate. v2.0 graduation criterion: first auth/PII milestone + G.12 PULLED-WEIGHT verdict.
- **Origin:** Veracode 2025 — 45% of AI-generated code carries OWASP Top 10 flaws.
- **Reusable artifact:** Stage 4.1 conditional gate (risk-tier HIGH only); permission-matrix §11 already triggers human review.
- **Risk if ignored:** known classes of vulnerability ship.
- **Tradeoff:** license cost ($) + integration days + false-positive triage. Risk-tiered.

### E.4 — TDD-with-AI for new modules (CANDIDATE)
- **Principle:** when subagent implements a NEW module, write tests first (citing REQ-IDs); subagent then implements until green. Only when K.8 contract is pre-locked. v2.0 already operationalizes this via `/fix-issue-prepare` + `/fix-issue-implement` skill split.
- **Origin:** Willison / Osmani / Blomfield consensus; opposes "AI writes test+impl in same turn" coverage theater.
- **Reusable artifact:** `.claude/skills/fix-issue-prepare/` skill.
- **Risk if ignored:** AI writes both test and implementation in same turn → coverage theater.
- **Tradeoff:** ~15 minutes extra per new module; high if contract is wrong.

### L' — Specialised subagent profiles beyond Code-Reviewer + Security-Reviewer (CANDIDATE)
- **Principle:** when a milestone's domain demands a specific lens (Architect for cross-service, Migration-Specialist for schema), add a third profile under `subagent-profiles/`. v2.0: Code + Security are MANDATORY (D-005); third profile graduates only after ≥2 milestones of PULLED-WEIGHT.
- **Origin:** BMAD-METHOD pattern (43k+ stars suggests 12-21 profiles); we reject that ceiling.
- **Reusable artifact:** `subagent-profiles/README.md` graduation rule.
- **Risk if ignored:** unique domain lens missed.
- **Tradeoff:** ~1 hour per profile + ongoing maintenance.

---

## ★ M12 ADDENDUM (2026-06-10 — production-hardening milestone: async-callback adapter made correct under multi-node + rolling deploys)

> Seeds harvested while adding Redis idempotency, durable delivery, drain, and backpressure to an async-callback adapter. Origin trail: EF-AI `docs/process-log.md` S32–S33 + `docs/m12-retrospective.md`. Theme L (distributed correctness) is this milestone's main generalizable contribution; E.5 + C.10 extend existing themes.

## Theme L — Distributed correctness, durability & multi-node safety

> (Theme letter "L"; distinct from the single CANDIDATE seed "L'" above.)

### L.1 — Commit the durable record BEFORE you return the ack.
- **Principle:** if you synchronously acknowledge a request (`accepted: true`) and then hand the real work to a background task/queue, the durable write MUST happen *before* the ack returns — never in a fire-and-forget `create_task`/goroutine scheduled after it. Any crash in the ack→enqueue window loses work the caller was told you accepted. "Enqueue, then ack" is correct; "ack, then enqueue" is a slower way to lose the message.
- **Origin:** EF-AI M12 (S32) — the K.7 Code-Reviewer's first BLOCKING on the project: the "durable" dispatch path enqueued inside an `asyncio.create_task` scheduled *after* the sync ack, so the durability was illusory. Fixed with a synchronous `on_dispatch_sync` hook that does the Redis `LPUSH` inline before the route returns.
- **Reusable artifact:** a synchronous enqueue hook on the request path (the durable write is a single cheap op — `LPUSH`/`INSERT` — so it belongs inline); the background worker does the slow work (AI call, callback), never the durability commit.
- **Risk if ignored:** at-least-once silently degrades to at-most-once; every unit test still passes (they don't kill the process in the window); loss only shows as missing callbacks under production pod churn.
- **Tradeoff / cost of adoption:** one extra synchronous I/O (a single queue write — negligible) on the hot accept path. The async-accept it resists is a false economy. Essentially none.

### L.2 — Release what you reserved when you reject.
- **Principle:** when the accept path reserves state early (an idempotency slot, a lock, a sequence number) and a *later* step then fails or sheds load, roll back the reservation before returning the error — otherwise the caller's retry sees half-reserved state (e.g. "duplicate") and is permanently stuck. Reserve → on-failure-release is the invariant.
- **Origin:** EF-AI M12 (S33) — adding backpressure: the route claims the idempotency slot (`create_if_absent`) *before* dispatch, so a naive "queue full → 503" stranded the taskId as a permanent duplicate. Fix: on `DispatchQueueFull`, `delete(task_id)` to release the slot, then 503 — so the retry is a fresh accept.
- **Reusable artifact:** a `delete`/release method on the reservation store, called only in the rejection path; a route test asserting "reject → retry is accepted as NEW, not duplicate."
- **Risk if ignored:** load-shedding / transient failures convert into permanent stuck tasks; the caller retries forever and always gets "duplicate."
- **Tradeoff / cost of adoption:** the reservation store grows a `delete`; a narrow window remains (a duplicate arriving between reserve and release sees "duplicate" momentarily) — acceptable for load-shedding, but document it.

### L.3 — Promise at-least-once with a stable idempotency key, never exactly-once.
- **Principle:** exactly-once delivery across a network boundary isn't achievable without the receiver's cooperation. Declare **at-least-once** and make every delivery carry a stable idempotency key (the customer's `taskId`) and a byte-identical signed body, so a duplicate is safe to apply twice. Put the duplicate-safe contract in the customer-facing API doc — deduping on the key is the receiver's job.
- **Origin:** EF-AI M12 (ADR D-043) — a pod that dies after delivering a callback but before acking it re-drives the job → a second, byte-equal, HMAC-signed callback for the same taskId. Documented as the contract rather than engineered away.
- **Reusable artifact:** an ADR stating delivery semantics = at-least-once + duplicate-safe; the same stable key threaded through queue job → callback body → signature.
- **Risk if ignored:** you either over-engineer toward an impossible exactly-once, or ship at-least-once *without telling the customer*, and their non-idempotent handler double-applies.
- **Tradeoff / cost of adoption:** pushes a dedup requirement onto the integrator (must be stated explicitly and early); in exchange the producer stays simple and crash-safe.

### L.4 — Cross-node "who's first?" must be one atomic op, never check-then-act.
- **Principle:** electing a single winner across replicas (idempotency, leader, dedup) uses a single atomic primitive — `SET key val NX EX ttl`, `INSERT ... ON CONFLICT`, a conditional write — never `GET`-then-`SET`. The read-then-write form has a window where two replicas both believe they won and both proceed (double-dispatch).
- **Origin:** EF-AI M12 (B6 / D-044) — `RedisTaskStatusStore.create_if_absent` uses `SET … NX EX`; an 8-thread shared-server test asserts exactly one creator. A get-then-set version was explicitly rejected as a BLOCKING-class defect.
- **Reusable artifact:** atomic create-if-absent behind a `create_if_absent → (record, created: bool)` interface; a concurrency test racing N callers at one shared backend asserting `sum(created) == 1` (use an in-memory fake like fakeredis `FakeServer`).
- **Risk if ignored:** rare, load-dependent double-processing that passes every single-threaded test and only manifests under concurrent same-key traffic at >1 replica.
- **Tradeoff / cost of adoption:** ties you to a backend offering the atomic primitive (essentially all do); the concurrency test needs a shared fake to be meaningful.

### L.5 — A durable queue without a depth cap is an outage waiting for a slow consumer; shed load, don't grow.
- **Principle:** an unbounded durable queue will OOM its store when the consumer wedges (downstream dependency down). Put a configurable depth cap on the producer; past it, reject the accept with a transient 503 (load-shed) rather than grow without bound. A soft `LLEN ≥ cap` check before the write only ever *rejects* — never drops an accepted item — so the worst case is the cap is exceeded slightly under concurrency, never a lost item.
- **Origin:** EF-AI M12 (S33, plan Wave 1.3) — `DISPATCH_QUEUE_MAX_DEPTH` + `DispatchQueueFull` → 503; off by default (0 = unbounded), ops sets it before scaling out.
- **Reusable artifact:** an env-configured cap read by the queue factory; `enqueue` raises a typed `QueueFull` past the cap; the route maps it to 503 + a rate-limit error code; pairs with L.2 (release the reservation on the 503).
- **Risk if ignored:** a wedged worker becomes a store OOM that takes down the whole service (and every tenant sharing that store), instead of a localised, recoverable load-shed.
- **Tradeoff / cost of adoption:** one extra round-trip (`LLEN`) on the accept path when enabled; picking the cap is an ops tuning task. Off-by-default keeps single-node deploys unchanged.

### L.6 — The process can't know its own replica count; make scale-out preconditions a boot guard.
- **Principle:** a pod can't detect at runtime how many replicas of itself are running, so it can't self-protect against "I'm multi-replica but configured for single-node" (e.g. in-memory idempotency across 3 pods). Make the operator *declare* scale-out via an explicit env flag (`REQUIRE_REDIS=true`) and **refuse to boot** if the declared mode's preconditions are absent. Pair with a fail-fast config doctor that validates ALL required env at once at startup and prints one readable block — instead of the platform surfacing one missing var per crash-redeploy cycle.
- **Origin:** EF-AI M11→M12 — M11 prod bring-up was death-by-a-thousand-crashes (one empty/invalid env per boot). M12 added `config_doctor.py`: validates everything at once, gated by `APP_ENV`, carrying the `REQUIRE_REDIS && !REDIS_URL ⇒ refuse boot` guard.
- **Reusable artifact:** a `check_required_env(env) -> list[problem]` pure function + a `run_or_raise` that prints all problems and exits; an explicit scale-out flag that gates the dangerous default; the doctor gated to prod/staging only.
- **Risk if ignored:** a careless `replicaCount: 3` on a single-node-shaped config silently double-processes; and every environment swap repeats the one-crash-at-a-time bring-up loop.
- **Tradeoff / cost of adoption:** the doctor must be gated (run only in prod/staging) so dev/test/CI on defaults aren't blocked; the scale-out flag is one more thing ops must set — mitigated because forgetting it fails *safe* (refuses to boot).

### E.5 — Acceptance-criterion tests ship in the same wave as the feature; verify they exist on subagent death.
- **Principle:** the test that proves a *hard* acceptance criterion (concurrency safety, survives-restart, the exact thing the milestone promises) is written in the same wave as the code it proves — never deferred to closure. When a subagent dies mid-task, the controller verifies the *acceptance-criterion tests exist*, not just that the code compiles — death-tolerance for code is not death-tolerance for proof.
- **Origin:** EF-AI M12 (S32) — a Wave-1 subagent died after landing the atomic-`SET NX` store but *before* writing the B1/B6 concurrency + restart tests. The code looked done; the proof was missing; K.7 caught it one stage later as BLOCKING. Cheaper at the dispatch boundary.
- **Reusable artifact:** a controller post-death checklist item — "for each acceptance criterion in the plan, grep for its citing test"; the plan's acceptance criteria each name the test that will prove them.
- **Risk if ignored:** an untested core ships behind green-but-incomplete suites; the gap surfaces in review (good) or production (bad) instead of at the wave boundary (cheapest).
- **Tradeoff / cost of adoption:** a few minutes of grep per wave / per subagent death; occasionally flags a criterion whose test is legitimately deferred (then record the deferral explicitly).

### C.10 — When the sandbox runtime lags the target, shim the version-only-missing names and run the FULL gate.
- **Principle:** if the dev/CI sandbox is a lower language runtime than production (and can't fetch the target interpreter), don't settle for a partial test signal. Inject the small set of version-only-missing names (e.g. Python 3.11's `datetime.UTC`, `enum.StrEnum`) via a startup shim (`sitecustomize.py`) so the *entire* suite runs in-sandbox. Extends C.7 (sandbox-as-canary) from "lint only" to "full gate."
- **Origin:** EF-AI M12 (S33) — target is 3.11+ (`datetime.UTC`), sandbox is 3.10 and `uv` couldn't fetch 3.12 (allowlisted network). A `sitecustomize.py` shimming `datetime.UTC` + a faithful `StrEnum` let the full suite run (446 passed / 1 skipped) and caught residual lint nits before the Mac round-trip.
- **Reusable artifact:** a `PYTHONPATH`-injected `sitecustomize.py` that backfills only the missing stdlib names; the one test that genuinely depends on runtime-version *behaviour* stays explicitly `skip`-marked and runs on the real target.
- **Risk if ignored:** you ship on a partial-module signal + repeated target-machine round-trips, or trust a lint-only sandbox and let test regressions through.
- **Tradeoff / cost of adoption:** the shim is a faithful-enough *approximation* — version-specific *behaviour* (not just name presence) still needs a real-target run; keep that one test skipped-in-sandbox and assert it on the target so the gap is explicit, not hidden.

## ★ S34 follow-on (2026-06-11 — first prod deploy of the M12 image)

> Harvested while diagnosing "is the M12 patch even live?" The running pod was still M11: a feature merge had clobbered DevOps's `Dockerfile`, so CI never rebuilt — and a pod *restart* re-ran the same old image (restart ≠ re-pull). Two seeds: one graduates the long-standing S28 candidate, one is new.

### L.7 — Version-stamp the health/readiness probe so "which code is live?" is one curl. (graduates the S28 candidate)
- **Principle:** bake the build identity (image tag / git SHA) into the running app via an env var the CI/build sets (`APP_BUILD`), and surface it in the `/health` (or `/version`) body alongside an app `version`. A green probe proves the process is *up*, never *which code* it is; the stamp closes that gap. Keep the probe's status field unchanged (additive fields only) so the liveness contract is untouched.
- **Origin:** EF-AI — first raised as a candidate at M10/S28 ("a green liveness probe says the server is up, not that it's running the code you think"; stale `make mock-qwen` process scored 7/11). Graduated at S34 when a prod pod ran M11 code behind a green `/health` and it took three exec-and-grep checks (`/ready` 404, missing modules, ImportError) to prove it. Fix: `APP_BUILD` env → `/health` returns `{status, version, build}`.
- **Reusable artifact:** an `APP_BUILD = os.environ.get("APP_BUILD", "unknown")` module constant surfaced in the probe body; CI bakes the tag (`ENV APP_BUILD=<tag>` in the Dockerfile, or the deploy env). A drift check becomes `curl /health | jq .build` vs the tag you expected to deploy.
- **Risk if ignored:** deploy-roll failures (old image still running) are invisible behind a green probe; you debug "why didn't my change take effect?" by exec'ing into pods and grepping for symbols — exactly the S34 hour.
- **Tradeoff / cost of adoption:** one env var the build must set (defaults to "unknown" if unset, so dev/test are unaffected); the probe body grows two fields — verify no consumer asserts the body by exact equality (one test needed updating here).

### K.10 — DevOps-customized files in a shared repo are a contract surface; mark the boundary or a feature merge will clobber them.
- **Principle:** when the app team and DevOps share one repo, the files DevOps customizes for the prod build/deploy (the `Dockerfile`, `/deploy/**`, CI/CD pipeline config) are a cross-*team* contract surface — the same hazard as K.8's cross-*subagent* contracts, one org level up. A feature branch that carries its own copy of these files will silently overwrite DevOps's customizations on merge, and the next CI build ships the wrong thing. Mark the boundary with `CODEOWNERS` (so changes require DevOps review) and a header/README note; never let an app-feature merge edit them blind.
- **Origin:** EF-AI S34 — an M12 feature merge overwrote DevOps's `Dockerfile` customizations on `master`; CI built from the clobbered file (or didn't rebuild the expected image), so the deployed pod stayed on M11 code. Cost: a deploy that looked done but wasn't, plus a DevOps round-trip to restore their changes.
- **Reusable artifact:** a root `CODEOWNERS` listing `/Dockerfile`, `/deploy/`, CI config under the DevOps handle; an `⚠️ Ownership` callout at the top of the deploy README; an AGENTS.md "do not overwrite DevOps-owned build/deploy files" rule.
- **Risk if ignored:** silent prod-build regressions on every merge that touches shared infra files; "I merged my feature and prod broke / didn't update" with no obvious cause; inter-team trust erosion.
- **Tradeoff / cost of adoption:** `CODEOWNERS` enforcement depends on the platform (GitHub enforces on PRs; some internal Git servers don't — then it's a documented convention, not a gate); requires knowing the real DevOps handles; adds a review hop on legitimate infra changes (the point).

## ★ v2.2 RATIFIED — two-project bootstrap + prod bring-up feedback (2026-06-19)

> Ratified for v2.2 by a 7-role blind council (Senior SW, Senior Data, PM, QM, Security, DevOps, Cloud Architect) + the product owner. Sources: HCS-MaaS bootstrap (FB-1..FB-5) and EF-AI S35 prod bring-up (L.8, L.9, K.11, E.6). Through-line: **documented discipline is not self-enforcing -> make it an executable gate, at Stage 0 and at go-live.** Append-only; supersede, don't edit.

### C.11 — Stage-0 discipline must be an executable gate, not a checklist. (ACTIVE; FB-1)
- **Principle:** a written Stage-0 checklist silently degrades -- an init pass can fill some items and skip others (L.7 `/health`, universal ADRs, a filled architecture.md, a stray `<PLACEHOLDER>`) and nobody notices until a re-audit. Ship an executable gate (`scripts/bootstrap-check.sh` + `make bootstrap-check`) that FAILS Stage-0 closure on: stray `<PLACEHOLDER>` in must-fill files, a non-L.7 `/health`, still-template prd/decisions/architecture, missing universal ADRs, or a wrapped OSS engine without a license review. A milestone literally cannot close partially done.
- **Origin:** HCS MaaS S1/S2 -- the v2.1 starter even shipped a v2.0 `{status:ok}` health test contradicting the design doc's L.7 day-1 claim; the gap was in the starter, not just the init agent.
- **Reusable artifact:** `scripts/bootstrap-check.sh` + `make bootstrap-check`, wired into the Stage-0 closure checklist; each gate criterion has a citing test (QM: a gate without a citing test is itself undocumented discipline).
- **Risk if ignored:** every greenfield bootstrap silently ships partial discipline; design doc and starter drift.
- **Tradeoff / cost of adoption:** ~1-2h once; turns "remember to" into "can't close without." The unfilled starter intentionally fails the gate (it is a template).

### B.6 — Reserve non-colliding ADR-ID ranges (process vs project). (ACTIVE; FB-2)
- **Principle:** the pipeline pre-seeds universal/process ADRs; an inherited project can already number its own domain ADRs in the same band (D-006+ cited across its PRD + feature list), colliding. Going forward: **process/universal ADRs use `P-00x`; projects start at `D-100`** (D-001..D-099 reserved). At bootstrap, run the reconciliation recipe: keep the project's existing D-ids, renumber/representing the pipeline's process ADRs as `P-00x`, and write the mapping down before the first commit.
- **Origin:** HCS MaaS S1 (universal D-006/D-007 collided with the project's own D-006+; reconciled by moving process ADRs out of the project D-band).
- **Reusable artifact:** the `P-00x` process namespace + "projects start at D-100" rule in `docs/decisions.md`; a Stage-0 reconciliation recipe; `bootstrap-check` C5 warns on project ADRs in the reserved band.
- **Risk if ignored:** ID collisions + ambiguous citations whenever a project arrives with its own ADR history.
- **Tradeoff / cost of adoption:** one-time numbering convention; existing universal D-001..D-005 are grandfathered (supersede-don't-edit, B.2).

### F.10 — License & commercial-use review of any wrapped/forked OSS engine is a Stage-0 gate. (ACTIVE; FB-4)
- **Principle:** when a project wraps or forks an OSS engine, its license can change the entire delivery model. AGPL/GPL/SSPL on a network service forces **"wrap, don't fork"** (run an unmodified copy as a separate service behind your own proprietary control plane) + a legal sign-off -- decide this at Stage 0, not after weeks of build. Add "license & commercial-use review of any wrapped/forked OSS engine" to the Stage-0 gates and the project-brief; treat an unreviewed AGPL/GPL/SSPL wrap as BLOCKING (permission-matrix catastrophe-class).
- **Origin:** HCS MaaS -- the wrapped NewAPI gateway is AGPL-3.0 (network copyleft + Section 7 attribution); surfaced only via deep code analysis (`docs/research/newapi-legal-note.md`).
- **Reusable artifact:** a Stage-0 gate line + a `project-brief.template.md` field; an optional `docs/license-review.md` the `bootstrap-check` C6 looks for; the three-scenario table (fork=AGPL trap / wrap-unmodified=safe / headless-wrap=cleanest).
- **Risk if ignored:** weeks of build on a dependency whose license forbids the intended proprietary productization.
- **Tradeoff / cost of adoption:** ~1 checklist line + a short legal review; saves a strategic mistake.

### L.8 — Configured != working: invoke every external dependency once before declaring it ready. (ACTIVE; go-live readiness)
- **Principle:** a dependency in a provider catalog / config UI, with credentials accepted, does NOT mean it serves requests. Before calling an integration "ready," **invoke it once for real** (a Test Run / smoke call) and inspect the *result*, not the config screen. Catalog presence + valid auth can sit on a backend that returns "not found / not deployed."
- **Origin:** EF-AI S35 -- Dify's Huawei MaaS provider listed DeepSeek/Qwen with a valid token, but every call returned `ModelArts.81009 "Invalid model"` (nothing deployed); only a Test Run exposed it.
- **Reusable artifact:** a `make smoke-deps` target + a Stage 4.3 "go-live readiness" step -- one real invocation per external dependency (model, queue, store, callback) with the response inspected; never tick "ready" off the config screen.
- **Risk if ignored:** you wire everything around a dead dependency, declare go-live, and discover at the first real request that the core service was never available.
- **Tradeoff / cost of adoption:** one real call per dependency (a little quota); a single smoke call is enough.

### L.9 — Verify config reaches the *process*, not just the values file. (ACTIVE; go-live readiness)
- **Principle:** between "I set it in the values/manifest" and "the process sees it" sits a templating/injection layer (Helm chart, operator, secret mount) that can silently drop a key. Always **read the value back from inside the running process** (its env / a debug echo that prints SET/EMPTY + lengths, never secret values) after a config change; treat the values file as a *request*, not proof.
- **Origin:** EF-AI S35 (and again from M11) -- the `llm-base` chart injects `secrets.environment` but NOT `configMap.data`; an AppCode set under `configMap.data` was `{}` in the pod. Caught only by reading the env from inside the pod.
- **Reusable artifact:** an in-process config echo run after every config change; know which section of your deploy template is actually injected; pairs with L.6 config-doctor and Stage 4.3.
- **Risk if ignored:** hours lost on "but I set it" -- config present in source-of-truth, absent in the running process; auth/keys silently empty.
- **Tradeoff / cost of adoption:** a 30-second read-back per change; requires a safe echo that never prints secret values.

### E.6 — Verify the pipe up to a blocked dependency via the downstream's own run-log attribution. (ACTIVE)
- **Principle:** when one dependency is blocked, you can still prove everything else works: send a real request, confirm it traverses every stage up to the blocked one, and use the **downstream system's own run log** to confirm your call arrived authenticated/attributed. "Run created, attributed to my service, failed only at node X" proves auth + connectivity + routing and isolates the blocker.
- **Origin:** EF-AI S35 -- with the model down, a `/v2` call returned `200 accepted` and Dify's run log showed the run attributed to `ef-ai-adapter`, failing only at the model node; that one line proved the whole pipe except the model.
- **Reusable artifact:** an integration smoke asserting (a) the entry ack and (b) a downstream run-log entry attributed to the caller, even when the end result is an expected failure at the blocked node; pairs with E.5.
- **Risk if ignored:** a blocked dependency masks whether the rest of the integration is even wired.
- **Tradeoff / cost of adoption:** needs read access to the downstream's run history; the attribution signal must be distinguishable (named service account/key).

### K.11 — An agent can drive a prod UI (browser) to configure/verify a dependency. (CANDIDATE, N=1; guardrails ACTIVE)
- **Principle:** when there is no API/CLI for a step (a console-only workflow tool), an agent can drive the UI via browser automation to configure and *verify* it (select a model, publish, run a Test Run, read a run log). **The capability stays CANDIDATE (N=1) pending a 2nd independent payoff -- but the GUARDRAILS are ACTIVE now** (the agent already does this, so the rails are needed regardless): the agent NEVER enters real credentials; state-changing clicks (publish, settings) are per-action, visible, and human-confirmable; screenshots may contain the user's secrets so they are not transcribed; corporate web filters may block fresh navigations (work within the open tab). Default-deny otherwise (permission-matrix).
- **Origin:** EF-AI S35 -- configured 3 Dify workflows (model repoint + publish) + ran a live Test Run + read the run log entirely through the browser; the user did the credential/cluster steps.
- **Reusable artifact:** a "UI-ops" pattern with a clear split of agent-doable (UI clicks, reads) vs user-only (credentials, cluster apply); guardrails written into `permission-matrix.md`.
- **Risk if ignored:** either the step stalls waiting for an API that doesn't exist, or the agent oversteps into entering secrets / irreversible clicks without confirmation.
- **Tradeoff / cost of adoption:** browser automation is slower + more brittle than an API; only worth it when there is genuinely no programmatic path. Graduate the capability (not just the guardrails) after a 2nd payoff -- the same bar council planning cleared.

### C.12 — In a Cowork mounted sandbox, finish git host-side. (ACTIVE; FB-3)
- **Principle:** in a Cowork mounted sandbox, git cannot remove its own lock files (`.git/index.lock`, `HEAD.lock`) -- EPERM -- so the first commit succeeds but leaves stale locks that block the next; commits/pushes must be finished from the user's real terminal.
- **Origin:** HCS MaaS S2.
- **Reusable artifact:** START_HERE's "Cowork-blocked files" note extended with a git-in-mount caveat + lock-cleanup recipe (`rm -f .git/*.lock`); prefer `git init`/commit host-side.
- **Risk if ignored:** confusing "another git process is running" failures mid-bootstrap.
- **Tradeoff / cost of adoption:** none (documentation).

### FB-5 RATIFIED — council planning graduates to a standing optional Stage-1 variant.
- **What changed:** v2.1 §15.8 listed council planning as PULLED-WEIGHT but N=1, deferring promotion until a 2nd independent payoff. EF-AI ran two more blind parallel councils (planning + auth/D-029), and this very v2.2 cut was decided by a 7-role blind council -- the 2nd (and 3rd) payoff. Graduated to a **standing OPTIONAL Stage-1 variant** (kept optional for anti-bloat).
- **Reusable artifact (the blind-parallel-subagent ballot recipe):** dispatch N role sub-agents concurrently in one message (true blind parallelism -- none sees the others); give each the SAME briefing packet + a role lens; collect a fixed ballot (verdict + per-item ADOPT/DEFER/REJECT + placement + top concern + confidence); a non-voting chair (represents the user) tallies and surfaces only the genuine splits for the user's decision. Convergent independent answers are a strong signal; splits are where the real decision is.

## ★ v3 RATIFIED — cross-project harvest (2026-06-26)

> Ratified for v3 by a 13-seat blind council (6 core + skeptic voting all 68 candidates; 7 domain seats voting their clusters) + the product owner, splits S1-S4 settled by the owner. Sources: 7 projects -- Reimbursement-App (reimbursement, Node/Vue), Poyraz-Dekorasyon (Poyraz site, React), aop-portal (Next.js AI-ops), BotIm-AOP (multi-tenant AI CS), aop_growth (aop_growth), HSC-MaaS (NewAPI Go gateway), one-api (LLM gateway, Go). Budget §5.5: ~15 adopts, ≤3 BLOCKING gates (2 spent, 1 reserve). Through-line: **the largest new gap is agent-native/LLM-ops + gateway, but most of that evidence is one ecosystem, so it is chartered as candidate, not adopted wholesale.** Append-only; supersede, don't edit. Full register: `General_Pipeline/v3-candidate-register.md`; ratification: `General_Pipeline/v3-ratification.md`.

### V3C-11 — Web/API security baseline: no plaintext creds / no default-admin password. (GATE; ACTIVE)
- **Principle:** hash credentials from day one (even in prototypes); ship no hardcoded default-admin password and no plaintext credential in source; secrets come from env/secrets-manager, never inline literals. Catastrophic + grep-checkable, so it is a `make bootstrap-check` gate criterion.
- **Origin:** Reimbursement-App F1 (plaintext passwords, catastrophic) + one-api F12 (hardcoded default admin password, catastrophic) -- two independent projects re-derived GP's inherited security gate the hard way.
- **Reusable artifact:** `scripts/bootstrap-check.sh` C7 (default-admin / plaintext heuristic over source); `docs/security-baseline.md` item 1; closure Security review confirms hashing.
- **Risk if ignored:** total-blast-radius credential breach shipped on day one.
- **Tradeoff / cost of adoption:** the grep heuristic can false-positive on test fixtures (review the hit); the deeper baseline (authz/CORS/encrypt) is reviewed at closure, not grep-gated.

### V3C-02 — No "done" without a citing test per acceptance criterion; red-test the symptom first. (GATE; ACTIVE)
- **Principle:** every acceptance criterion has a test that cites it; when fixing a reported symptom, reproduce it with a FAILING test before diagnosing, then make it green (red->green); a new capability ships with its test in the same wave. Mostly formalizes GP's existing REQ-coverage Quality Gate.
- **Origin:** Reimbursement-App F11, aop F2/F9, zek F14 (independently-testable milestones), HSC-MaaS F1 (test-plan doc) -- convergent across ecosystems + validates GP's E.4/E.2.
- **Reusable artifact:** the V3C-02 line in the Quality Gate (`docs/closure-checklist.md` §B.1) + AGENTS.md §3.3 + the per-wave `subagent-profiles/Tester.md`.
- **Risk if ignored:** coverage theater (AI writes test + impl in one turn) and fixes that re-break because nothing pinned the symptom.
- **Tradeoff / cost of adoption:** a little more test authoring up front; the payoff is a citing test per criterion as a permanent audit trail.

### V3C-68 — Restructure the review loop: per-wave Code-Reviewer + Tester + per-agent dev-test loop; Security review -> milestone closure (BLOCKING before deploy). (TEMPLATE-CHANGE; ACTIVE)
- **Principle:** during the wave each implementing agent runs a tight dev-test loop (implement->test->self-review->fix) owning its slice; at wave exit a Code-Reviewer + a Tester (fresh-eyes, never own code) flush all fixes; Security review runs once at milestone closure over the whole surface and is BLOCKING before the deploy/go-live step. Safe because nothing ships mid-milestone (waves don't deploy). Always-on catastrophe-class guardrails (no committed secrets, no destructive ops) still apply every wave.
- **Origin:** owner proposal 2026-06-26 + convergent test evidence (V3C-02; zek F14; one-api F9 race). Replaces the v2.2 per-wave Duo (Code + Security) with per-wave (Code + Tester) + dev-test loop; Security joins Quality at Stage 4.
- **Reusable artifact:** revised Stage 2/3/4 in `pipeline-design.md`; `subagent-profiles/Tester.md`; the closure Security step (`docs/closure-checklist.md` §B.2a); the HIGH-risk security trigger in `permission-matrix.md`.
- **Risk if ignored:** self-review without fresh eyes misses integration drift (GP's measured win is K.7); or security feedback arrives only after deploy.
- **Tradeoff / cost of adoption:** an early-wave security-shaped flaw may cost more rework (accepted: no prod exposure, since deploy is at closure and security is BLOCKING before it -- the cost is rework, not a leak). The dev-test loop must ADD to, never replace, the wave-exit fresh-eyes pass.

### V3C-44 — One canonical mock per integration, built before integration code, + a contract test. (TEMPLATE; ACTIVE)
- **Principle:** for each external integration build one canonical mock/fake-client before the integration code (extends K.1's Protocol-typed fake); consolidate any parallel mocks into it; keep a contract test that runs against the real API so the mock can't silently drift.
- **Origin:** BotIm-AOP F6+F8 (mock divergence), HSC-MaaS F6, one-api -- 3 gateways; validates GP's K.1 / J.4.
- **Reusable artifact:** the canonical-mock convention in `pipeline-design.md` §7 (testing) + the closure check in `docs/closure-checklist.md` §A; tests drive the canonical fake, never bespoke per-test stubs.
- **Risk if ignored:** parallel mocks drift apart and the suite passes against a fiction the real API never honored.
- **Tradeoff / cost of adoption:** one contract test per integration (a little quota / a live dependency to hit); buys protection against silent contract drift.

### V3C-12 — Server-side authz on every mutating route; client checks are UI sugar. (GUARDRAIL; ACTIVE)
- **Principle:** every mutating route enforces authn/authz server-side; assume the client is hostile and replays the raw request. Client-side guards (hidden buttons, route guards) protect nothing.
- **Origin:** Reimbursement-App F2 (catastrophic, client-only auth).
- **Reusable artifact:** `docs/security-baseline.md` item 2; closure Security review enumerates mutating routes + names each server-side guard; `permission-matrix.md` §7.
- **Risk if ignored:** any user mints privileged requests by calling the API directly.
- **Tradeoff / cost of adoption:** not cheaply grep-checkable per route (hence guardrail, not gate) -- it is a review obligation.

### V3C-13 — CORS allowlist in prod; never allow-all + credentials. (GUARDRAIL; ACTIVE)
- **Principle:** restrict CORS to an explicit origin allowlist in prod; never ship wildcard origin together with `Access-Control-Allow-Credentials: true` (leaks authenticated responses to any origin).
- **Origin:** Reimbursement-App F6 + one-api F13 (two ecosystems).
- **Reusable artifact:** `docs/security-baseline.md` item 3; `.agents/rules/practices.md` v3 guardrails.
- **Risk if ignored:** cross-origin theft of authenticated responses.
- **Tradeoff / cost of adoption:** maintain the allowlist per environment.

### V3C-51 — Validate security-critical config at startup; fail the prod process. (GUARDRAIL; ACTIVE)
- **Principle:** validate security-critical config at startup (auth secrets, CORS, keys, enforce-prod flags) and fail the process in prod mode on a missing/invalid value; never silently default to insecure (auth-off, empty key, 0). Extends bootstrap-check + Theme L L.6.
- **Origin:** BotIm-AOP F9 (startup config validation) + one-api F15 (fail loud on parse error, never default to zero).
- **Reusable artifact:** a startup validator gated to prod/staging; pairs with the L.6 config-doctor; `docs/security-baseline.md` item 4.
- **Risk if ignored:** a service boots "successfully" with auth off or an empty key.
- **Tradeoff / cost of adoption:** must be gated so dev/CI on defaults aren't blocked.

### V3C-56 — Encrypt credentials/PII at rest with a rotation-friendly multi-key chain. (GUARDRAIL; ACTIVE)
- **Principle:** encrypt stored credentials/PII at rest; use a multi-key chain where decrypt tries all keys and encrypt uses the first (current) key, so rotation is a config change, not a migration.
- **Origin:** BotIm-AOP F7 + one-api F11 (plaintext upstream creds = total-blast-radius breach; 2 ecosystems).
- **Reusable artifact:** `docs/security-baseline.md` item 5; keys themselves are not committed (gitleaks + permission-matrix §6).
- **Risk if ignored:** a store compromise leaks every credential/PII record in plaintext.
- **Tradeoff / cost of adoption:** key-management plumbing; the multi-key chain is what makes rotation cheap.

### V3C-33 + V3C-45 — Control class decides fail direction: auth/safety fail CLOSED, fairness fails OPEN. (GUARDRAIL, paired; ACTIVE)
- **Principle:** know your control class. Auth/safety guardrails fail CLOSED on error/timeout (deny) and must have a tested disable switch + correct domain scope; availability/fairness controls (rate-limit) fail OPEN (serve rather than block legitimate traffic). Encode the two together so neither is misapplied.
- **Origin:** BotIm-AOP F2 + zek F10 (fail-closed safety) + HSC-MaaS F3 (fail-open rate-limit) -- the one genuinely cross-ecosystem agent-native pair.
- **Reusable artifact:** the paired rule in `.agents/rules/practices.md` + `permission-matrix.md` §5; part of the closure Security review.
- **Risk if ignored:** a safety control that fails open ships an unguarded path; a rate-limiter that fails closed takes down legitimate traffic on its own failure.
- **Tradeoff / cost of adoption:** requires classifying each control up front and testing the disable switch.

### V3C-08 + V3C-36 — Agent least-privilege tool allowlist + human-confirm on all writes (CI and runtime). (GUARDRAIL; ACTIVE)
- **Principle:** give each agent only the tools its task needs; the LLM proposes and deterministic code acts; human-confirm on ALL writes -- in CI the agent opens drafts and a human merges (never edits its own workflow, fires only on an explicit human label, "ACT don't narrate" with a named served model + allowlisted tools); at runtime mutating tool-calls are per-action confirmed, never batched/unattended.
- **Origin:** aop F5/F6 + GP's own issue-agent.yml + zek F5 (per-agent tool allowlist + human-confirm) + BotIm-AOP F2 -- multi-project + GP.
- **Reusable artifact:** the allowlist + human-confirm rule in `permission-matrix.md` §5/§8 + `.agents/rules/practices.md`; extends V3C-08 (Layer-2 issue agent).
- **Risk if ignored:** an over-privileged agent self-merges, edits its own CI, or makes unconfirmed destructive writes.
- **Tradeoff / cost of adoption:** a human stays in the write path (the point); slightly slower unattended throughput.

### V3C-06 + V3C-53 — No destructive ops; destructive defaults OFF. (GUARDRAIL; ACTIVE)
- **Principle:** never full-revert to an old commit to fix one thing -- revert surgically and verify `main` actually contains the merged commits; any reseed/reset-on-boot defaults OFF or is loud + explicit. Catastrophe-class, always-on.
- **Origin:** Poyraz-Dekorasyon F3, aop F7 (surgical revert) + zek F13 (destructive default-on reseed).
- **Reusable artifact:** `permission-matrix.md` §5 (reseed default-off row + v3 safety guardrails); the catastrophe-class list.
- **Risk if ignored:** a one-line fix nukes unrelated work; a boot reseed wipes data by default.
- **Tradeoff / cost of adoption:** none meaningful -- it constrains only destructive shortcuts.

### V3C-03 / V3C-05 / V3C-10 / V3C-65 — Build guardrails. (GUARDRAILS; ACTIVE)
- **Principle:** V3C-03 read per-environment config at runtime, never bake it at build time (generalizes L.9 to build-time bake, e.g. Next.js); V3C-05 every dependency used is saved to the manifest in the same edit (extends C.6 to JS/npm); V3C-10 pin the runtime/toolchain version in CI (`.nvmrc`/`engines`) and test the build on the target; V3C-65 run the race detector (`-race`) on concurrent packages as a recommended CI step (a `// BUG:` touching shared state blocks release).
- **Origin:** aop F3 (build-bake), Poyraz-Dekorasyon F2 (Vercel build break), Poyraz-Dekorasyon F5 (toolchain pin), one-api F9 (data race).
- **Reusable artifact:** the build-guardrails block in `.agents/rules/practices.md`; CI notes in the Makefile / `.github/workflows/`.
- **Risk if ignored:** "works locally, breaks in CI/prod" from baked config, unsaved deps, or a toolchain mismatch; latent data races.
- **Tradeoff / cost of adoption:** V3C-65 is recommended-not-gate (evidence is Go-only); the rest are near-free hygiene.

### V3C-50 / V3C-52 / V3C-01 / V3C-27 — Confirm / fold (doc). (ACTIVE doc updates)
- **Principle:** V3C-50 write design notes + a gap-analysis (what exists vs what to build) before the first line of code -- keep it light (ceremony risk); V3C-52 commit per-repo rules to `.agents/rules/` + treat AGENTS.md §8 as a PROCESS routing index with lazy doc-loading (token economy) -- independently re-derives GP's own design; V3C-01 confirms L.7 (version-stamped /health); V3C-27 commit `.gitignore` first.
- **Origin:** HSC-MaaS F1 + aop F1 (design+gap-analysis); BotIm-AOP F3/F4 (.agents/rules + routing index); Reimbursement-App F5 + both GP-v2.2 runs (V3C-01); Poyraz-Dekorasyon F1 (V3C-27).
- **Reusable artifact:** Stage-1 gap-analysis line + START_HERE routing-index note (`pipeline-design.md`, `START_HERE.md`); these validate existing GP design (raise confidence, no new mechanism).
- **Risk if ignored:** code before a clear build/reuse picture; AGENTS.md bloats; untracked files leak into the first commit.
- **Tradeoff / cost of adoption:** keep V3C-50 to a few lines so it doesn't become a heavyweight design phase for small milestones.

### ★ CANDIDATE sub-block — Agent-Native / LLM-Ops theme (NOT active; promote on a 2nd independent ecosystem)

> Chartered as a v3 **container**, not adopted. The evidence is mostly ONE ecosystem -- Botim AOP/aop_growth/aop-portal (BotIm-AOP, aop_growth, aop-portal) + the one-api ≈ NewAPI gateway family (one-api, HSC-MaaS). Per the council's weighting rule, down-weight intra-ecosystem agreement; promote a seed only when it also appears OUTSIDE one ecosystem or re-derives GP's own design. The four that already cleared that bar (V3C-33/45, V3C-08/36, V3C-44, V3C-56) are ACTIVE above; the rest wait here. Full text per candidate in `General_Pipeline/v3-candidate-register.md`. Append-only; do NOT promote without a 2nd independent ecosystem + council/owner sign-off.

- **V3C-32 (CANDIDATE)** — LLM providers in a DB registry (runtime-swappable, probe-verified), not hardcoded env keys. *Sources: BotIm-AOP F1, one-api F5.*
- **V3C-34 (CANDIDATE)** — every LLM step has a deterministic fallback, tagged with `source` (llm vs fallback). *zek F3.*
- **V3C-35 (CANDIDATE)** — force a machine-readable LLM output contract (fenced JSON schema) + a neutral default on parse failure; never parse prose. *zek F4.*
- **V3C-37 (CANDIDATE)** — dual-grounding: LLM for qualitative judgment, deterministic queries for every checkable number. *zek F2.*
- **V3C-38 (CANDIDATE)** — number provenance: label real/simulated/estimate, log score↔outcome from day 1, no silent imputation. *zek F8/F15.*
- **V3C-39 (CANDIDATE)** — instrument every LLM call with tracing (prompt/tokens/latency/tools) from the first call. *BotIm-AOP F10.*
- **V3C-40 (CANDIDATE)** — add new capability as a dedicated single-purpose agent, not a new router skill on a proven agent. *zek F17.*
- **V3C-41 (CANDIDATE)** — separate ephemeral AI/session state from durable business/workflow state with a one-way escalation link. *BotIm-AOP F14.*
- **V3C-42 (CANDIDATE)** — rule-based retrieval over vectors on small corpora; split into two corpora when the join key is broken. *zek F6/F7.*
- **V3C-43 (CANDIDATE)** — MCP tool servers on stateless HTTP (curl-testable) + a lazy process-lifetime connection pool, never closed per request. *BotIm-AOP F5, zek F11.*
- **V3C-46 (CANDIDATE)** — streaming token rate-limiting: pre-reserve `max_tokens` upfront, post-adjust by actual after the stream (one-api: same for two-phase billing). *HSC-MaaS F2, one-api F2.*
- **V3C-47 (CANDIDATE)** — structured 429 + `Retry-After`; pick sliding-window (RPM) vs fixed-window (TPM) by precision need. *HSC-MaaS F9/F11.*
- **V3C-48 (CANDIDATE)** — multi-DB ORM abstraction encoded as written rules before the first cross-DB bug (driver from DSN at runtime). *HSC-MaaS F5, one-api F4.*
- **V3C-58 (CANDIDATE)** — split the read-only data plane from the write/action plane; integrate as complementary tools. *zek F1.*
- **V3C-59 (CANDIDATE)** — prove "no side-effects" safety constraints by tracing the code path + a negative grep, never by assumption (extends E.5/E.6). *zek F9.*
- **V3C-61 (CANDIDATE)** — circuit-breaker: auto-disable a failing upstream on a rolling success-rate, tri-state status (enabled / manually-disabled / auto-disabled) so automation never overrides an operator. *one-api F6.*
- **V3C-62 (CANDIDATE)** — classify upstream failures by stable signals (HTTP status, structured type/code), never by matching error-message substrings. *one-api F8.*
- **V3C-66 (CANDIDATE)** — one minimal lifecycle interface per external backend (adaptor pattern) → adding a provider is a localized copy-one-file task (extends K.1 / V3C-32). *one-api F1.*


---

## ★ v3.1 RATIFIED (2026-07-03) — hcs_maas_vib field harvest + owner directives (11-seat blind council · `General_Pipeline/v3.1-ratification.md`)

> First field run of GP v3 itself (hcs_maas_vib, M0–M4, 171 tests). All six v3-adopt validations CONFIRMED, five sharpened, none contradicted. **0 new gates** (reserve preserved). New meta-rule (council-design §5.6): validates-GP evidence from projects run ON GP cannot alone escalate anything past template weight.

- **V3C-69 (ACTIVE, guardrail+template)** — discipline is executable, never documentary: Stage-0 / wave close / milestone close each run an executable check or a committed checklist file (`docs/wave-checklist.template.md`); every ✅ cites a fresh, wave-scoped evidence referent; skipped/waived checks are ledgered, never silent. *hcs F1 (N=3) + owner OD-2.*
- **V3C-70 (ACTIVE, guardrail)** — day-0 license/commercial-use review of any wrapped/forked OSS engine (AGPL/GPL/SSPL ⇒ wrap-not-fork + sign-off) BEFORE architecture depends on it. *hcs F2 (catastrophic, averted).*
- **V3C-71 (ACTIVE, template)** — consumption posture named explicitly: wrap | fork | port + change triggers; the wrapper never touches the wrapped system's datastore. *hcs F3.*
- **V3C-72 (ACTIVE, template)** — Tester fault-injection: break → confirm RED → revert in place, verify byte-identical (md5); a fault that STAYS GREEN is the finding → mandatory new test. Scoped to load-bearing/HIGH-risk slices. *hcs F5 (N≥4).*
- **V3C-73 (ACTIVE, guardrail)** — "built ≠ wired": acceptance criteria phrased end-to-end on the live path; the citing test enters through the live entrypoint; review asks "is this control reachable from the request path?" *hcs F6.*
- **V3C-74 (ACTIVE, guardrail)** — every security invariant has its NEGATIVE test (fails when the invariant is removed), listed per milestone with citations; checked at the BLOCKING security close. *hcs F7.*
- **V3C-75 (ACTIVE, doc)** — idempotency test = same key, DIFFERENT payload, assert first-write-wins. *hcs F8.*
- **V3C-77 (ACTIVE, guardrail — domain-scoped: projects handling money)** — money is integer minor units + currency end-to-end; the Money type rejects float; round half-up exactly once at the boundary. *hcs F12.*
- **V3C-78 (ACTIVE, template — amends V3C-68 via P-005)** — risk-tiered review depth: LOW/MED wave → ONE combined reviewer; HIGH (auth/payment/crypto/migration/distributed-correctness; auto-escalated on authz/secrets/crypto/input-parsing/egress diffs) → Code + Tester + pulled-forward security-on-slice. Escaped-blocker tripwire reverts to full review. *hcs F14 (measured ~11→~5 reviewer runs).*
- **V3C-79 (ACTIVE, template)** — every retrospective answers the previous retro's carried question and poses one; a rule proposed twice but never built is BUILT or DROPPED (verdict buckets + retired count already active via G.12/D.4). *hcs F18.*
- **V3C-81 (ACTIVE, guardrail+template)** — living EXPERIENCE.md (`docs/EXPERIENCE.template.md`): appended at every milestone closure; the quarterly handover BLOCKS without a dated entry for the latest closed milestone; no secrets/PII; findings cite evidence. *Owner OD-1.*
- **Sharpened (existing seeds, same IDs):** V3C-44 + one live contract test vs a pinned real instance (self-skip is LOUD, counted at closure) + pre-freeze spike *(F4)* · V3C-33/45 + TESTED disable switch + fail-direction table at security close *(F10)* · V3C-53 + deny-service enforcement OFF-in-code/ON-in-prod-profile + boot preflight *(F13)* · V3C-68 + wave-close gates on plan-tagged passes *(F15)* · V3C-10/C.6 + hermetic gate recipe *(F16)* · V3C-06 + revert in place, NEVER checkout/restore on uncommitted work *(F17)*.
- **DEFERRED:** V3C-76 (redaction assert-absence-in-sink — promote fast on a 2nd ecosystem) · V3C-80 generator (principle "customer progress view ≠ internal truth tracker" rides as doc). **Agent-Native theme unchanged** — hcs_maas_vib is gateway-family (wraps One API), NOT the awaited 2nd independent ecosystem.


---

## ★ v3.2 RATIFIED (2026-07-03) — external research harvest + owner autonomy directive (2-phase council: 6 core → 3 domain, chair decided under owner delegation · `General_Pipeline/v3.2-ratification.md`)

> Source: the 9-doc Agentic-Engineering research curriculum (`research/agentic-engineering-curriculum/`) — the first fully EXTERNAL evidence class — + owner directive OD-3 (PRD → sign → autonomous run → owner reviews results + git). **0 new gates.** Central rule, converged on blind by 9/9 seats: **anything feeding trust/promotion/gates is computed from git/CI/hooks against protected refs; agent-asserted content is context, never a gate input.**

- **V3C-82 (NORTH-STAR CANDIDATE — NOT ACTIVE; owner decision 2026-07-03: "we are not ready — I review every wave and milestone, run the tests/checks, and make the commits"; A0 is the only operating mode, activation only by future owner-initiated ADR)** — autonomy designed as a LADDER (A0/A1/A2, `docs/autonomy-protocol.md`): promotion = 2 consecutive mechanically-clean milestones; demotion automatic, non-waivable, asymmetric; ⛔ zones glob-detected + human line-by-line at every level; per-plan scope grants replace per-write confirms; assumption ledger replaces mid-loop questions (⛔/criteria-meaning = HALT); blocked = halt-and-notify, never improvise; backpressure pauses the loop when closure packs sit unreviewed. *OD-3 + trust-ladder/harness-loop literature.*
- **V3C-83 (ACTIVE, template)** — every closure generates the OWNER REVIEW PACK — an AID to the owner's wave/milestone review, never a replacement for it — (`docs/closure-report.template.md`), derived from raw referents, 2-page cap, prose architecture-delta BLOCKING ("can't explain it → doesn't ship"); replaces the separate §B walkthrough output + note.txt milestone summary; absorbs the agent-authorship commit trailer (V3C-89). *OD-3 + comprehension-debt literature.*
- **V3C-84 (ACTIVE, template)** — trust telemetry per task type at every closure: post-closure fix rate (path overlap vs protected closure tag), churn, reverts, findings (security ×2) — script-computed into cost-log. Purpose TODAY: honest quality signal for the owner + the multi-version track record the north star would someday need. *Progressive-trust demotion rule; Apiiro 10× trigger.*
- **V3C-85 (ACTIVE, doc+profile)** — context economy: one task/session; fresh subagents per wave; exploration via the read-only **Explorer** profile (≤2k-token summary; NEW `subagent-profiles/Explorer.md`); compaction anchored to wave close, preserving open findings verbatim + re-injecting security invariants; token budget as a live circuit breaker; continuity is FILES, not sessions. *Anthropic context evals (−84% tokens; +90.2% isolation — construct caveat recorded).*
- **V3C-86 (ACTIVE, template — one home per check)** — AI-generation review smells: duplication-vs-reuse, drive-by edits, swallowed exceptions (Code-Reviewer); mirror-implementation + weakened/deleted-to-green tests (Tester, BLOCKING at HIGH); ~≤400-line wave diff WARN (wave checklist). *GitClear 8×, CodeRabbit 1.7×, DORA −7.2%.*
- **V3C-87 (ACTIVE, doc + mechanical backstop)** — declared L0 spike lane: `spike-*` exempt from gates EXCEPT secrets scanning; NEVER merged (branch-guard + closure check + delete-at-close); productionize = rebuild. *Mode-drift incidents (Replit, Tea).*
- **V3C-88 (ACTIVE, doc — scoped MED/HIGH)** — plans name ONE alternative + trade-offs; rejection anchored to concrete absence (mechanically checkable at A2). LOW-tier exempt.
- **External corroboration recorded (B1–B7):** V3C-69 executable-discipline (first independent confirm), the security gates (Veracode 45%, no scale improvement), slopsquat defense (USENIX 19.7%), AGENTS.md diet, fresh-eyes isolation (with the Skeptic's construct caveat on +90.2%), red-test-first, ⛔ zones.
- **Standing obligation:** the v3.2 retro MUST report the retired count of v3.1's own additions — zero retirements = the accretion-cap promise was decoration; treat the next autonomy escalation accordingly.


---

## ★ v3.3 RATIFIED (2026-07-05) — OD-4: A0.5 milestone-cadence owner review (7-seat council, chair-delegated · `General_Pipeline/v3.3-ratification.md`)

- **V3C-90 (ACTIVE — PROVISIONAL, guardrail+template)** — operating mode **A0.5**: waves close agent-side; the owner's deep review, personal test runs, and commits happen at every milestone boundary (capped ~4–6 waves / ~2k net lines; 60–90 min session; per-wave table + "decisions on your behalf" in the closure report). Owner checkpoint commits per wave (`wip: NOT reviewed`; agents never run git). Escalate-NOW list halts mid-wave; assumption ledger active; reviewer countersigns checklist rows; semantic-security items added to the agent pass. **Bright line: agent commit on main = A1 = explicit owner ADR.** **Tripwire:** escaped blocker an owner wave-pass would plausibly have caught → auto-fallback to wave cadence. *OD-4 + hcs field evidence (single project — hence provisional); Skeptic dissent recorded.*
- **Increment-6 harvest note:** final hcs_maas_vib EXPERIENCE = md5-identical to the interim → obligation CLOSED, zero new findings; the md5 duplicate check is PULLED-WEIGHT (two catches).
- **Retired by this cut (net ceremony down):** the owner-reviews-every-wave rule; the owner per-wave test-run expectation; the per-wave owner sign-off sense.


---

## ★ v3.4 RATIFIED (2026-07-17) — OD-6: Stage 5 Maintenance Loop (5-seat council · `General_Pipeline/v3.4-ratification.md`)

- **V3C-98 (ACTIVE, template+guardrail)** — post-deploy fix discipline: fix waves = normal waves
  (red-test intake; the failing test IS the frozen spec; only turn red tests green) → **fixpack**
  deploy gate (caps ≤5/~400 lines, HIGH ships solo; security floor incl. full invariant suite;
  full regression on the final bundle; migration + rollback plan) → **owner out-of-sandbox
  verification, BLOCKING** (reproduce pre-fix → gone post-fix → local tests → sign) → deploy with
  fix probe + watch window. Emergency path: compressed scope, never-skipped floor, 48h retro-close
  debt, >1/month alarm. *OD-6 + HCS post-prod (verbal, ~5 fixes; written harvest owed).*
- **Capture made MECHANICAL:** fixpack lesson lines (symptom → root cause → gate-attribution →
  lesson) append to EXPERIENCE.md as a **deploy condition**. 3 same-gate misses in 2 packs →
  mandatory gate-change proposal ("no gate" counts double). N=3 fixes on one surface → surface
  locks; refactor via a normal milestone.
- **RETIRED by this cut:** the standalone, memory-based EXPERIENCE harvest session (3 md5-identical
  uploads proved it decorative). Capture now happens at artifact-time: fixpack rows + closure
  reports. **Debt line:** the v3.1 retirement count is STILL owed to the first v3.3+ project retro.


---

## ★ v3.5 RATIFIED (2026-07-27) — Increment 9: the first post-prod dataset (5-seat council · `General_Pipeline/v3.5-ratification.md`)

> Source: 7 defects AFTER green gates on a customer-operated air-gapped cluster — ZERO caught by
> automated gates, 100% boundary defects. Doctrine line: **gates were excellent at correctness of
> what we imagined and blind to the shape of the world we deployed into.** v3.5 points the
> machinery outward. 0 new gates; net new package files: 0. Skeptic's dissent recorded: two cuts
> in one week is not precedent.

- **V3C-99 (ACTIVE, guardrail)** — `make check-templates` (SHIPPED templates instantiate the
  parser) + `make cold-start` (zero persisted state → serve-ready/honest not-ready); CI at
  merge+release; no default creds in the boot path. *FIX-01/02: two total outages.*
- **V3C-100 (ACTIVE, template)** — human-path: a non-author, shipped docs only, completes the
  primary journey (credentials instance mandated). *FIX-04.*
- **V3C-101 (ACTIVE, guardrail)** — producer enumeration on hardened invariants: checklist row +
  required verdict section + citing test per producer; security signs auth-class. *FIX-03.*
- **V3C-102 (ACTIVE narrow, doc)** — never parse a bounded prefix; diagnostics print revision
  stamps. Broad tooling-rigor doctrine deferred. *FIX-06.*
- **V3C-103 (ACTIVE, guardrail)** — ready≠alive (stack-conditional) + diagnosable fail-closed with
  the disclosure channel in the criterion (logs + authed diag only). *FIX-02/05.*
- **V3C-104 (SPLIT)** — boundary-grep line ("touches build/CI/k8s: NO", machine-verified) ACTIVE;
  full patch-package format CANDIDATE (one partner). *§4 of the harvest.*
- **V3C-105 (ACTIVE, edit)** — cadence binds to ARTIFACTS: every outward deliverable = a wave
  close. *FIX-07.*
- **V3C-106 (ACTIVE, template — default-expected, not mandatory)** — black-box journey tester
  (`make journey URL=…`, stdlib, shipped in-package, authored during build; QM bar: cold entry ·
  credential lifecycle · paying-customer round trip asserting CONTENT · one cross-wave sequence;
  custody: minted short-TTL tokens, never stored secrets); runs at 4.3 + every fixpack; skips
  recorded. *Found FIX-03.*
- **V3C-107 (ACTIVE, doc)** — every boot prerequisite: in the image OR a named-owned provisioning
  row — no third category. *FIX-02's ownership gap.*
