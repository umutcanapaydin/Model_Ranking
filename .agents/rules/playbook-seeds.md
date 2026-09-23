# Playbook seeds — index

> A **seed** is a lesson that generalizes beyond the project that learned it. The rules in
> `AGENTS.md`, `.agents/rules/practices.md`, the skills, the agent profiles and the checklists cite
> seeds by ID (`seed C.6`, `K.8`); this file says what each ID means and what goes wrong without it.
> Read it when a rule cites a seed — not at session start.
>
> **Format.** One row per seed: ID · principle · risk if ignored. IDs are immutable (B.5): a seed
> that stops earning its place loses its row, and its number is never reused. The highest number
> used so far in each theme: A.4, B.6, C.12, D.4, E.6, F.10, G.12, H.10, I.1, J.4, K.11, L.9 — a new
> seed takes the next one. A project adds a seed only once the owner approves it at milestone
> Capture (`docs/closure-checklist.md` §B.2), and records where it learned it in `docs/EXPERIENCE.md`.

## A — Requirements before code

| ID | Principle | Risk if ignored |
|---|---|---|
| A.1 | Number every requirement (REQ-IDs per area) before writing code; tests and PRs cite the IDs from then on. | No audit trail from spec to test; "we covered that, right?" debates. |
| A.2 | Treat two sources of truth (PRD and architecture brief, two PRDs) as adversarial: build a conflict table on first read (`docs/architecture.md` §5). | Code silently follows one document's assumption; the customer meant the other. |
| A.3 | Structure the requirements first, then read again in a separate pass for Open Questions (`docs/prd.md` §9). | Open questions hide inside dense requirement tables. |
| A.4 | When several customer artifacts arrive together, catalogue every cross-document conflict with its severity and resolve each with the owner before editing anything. | The newest document silently wins; conflicting decisions surface at acceptance. |

## B — Decisions

| ID | Principle | Risk if ignored |
|---|---|---|
| B.1 | Lock a question that cannot be resolved upstream as an ADR — status, rationale, mitigation, revisit-when — before it ossifies in code (`/log-decision`). | Agents invent contradictory assumptions; nobody can audit why the code looks as it does. |
| B.2 | Supersede, never edit: mark the old ADR `superseded by D-NNN` and write a new one. | The reason for the change is lost and the discarded reasoning comes back. |
| B.3 | Decisions are the expensive part, code the cheap part: at small scale, regenerate code from fresh decisions instead of patching old code toward them (`docs/codex-audit.md`). | Sunk-cost patching toward the stack you wish you had started with. |
| B.4 | Snapshot a customer-facing artifact before each review iteration (`<name>_pre-<event>-<YYYY-MM-DD>.<ext>`). | "What changed since the customer last saw it?" needs git archaeology. |
| B.5 | IDs are immutable: a deleted or hidden item leaves a gap, and nothing is renumbered. | Every citation of the ID drifts silently to the wrong item. |
| B.6 | Keep ADR ranges apart: process ADRs `P-00x`, project ADRs from `D-100`, `D-001..D-099` reserved; an inherited project keeps its own IDs and writes down the mapping at Stage 0. | ID collisions and ambiguous citations. |

## C — Repository and toolchain

| ID | Principle | Risk if ignored |
|---|---|---|
| C.1 | Day-1 green: the first commit carries a runnable app, a passing test and a green `make check`, even if the app only serves `/health`. | Weeks of "almost ready" code before basic import errors surface. |
| C.2 | Build scripts pin a minimum interpreter version with a clear error, never a single point version. | Every new machine and CI runner hits the same wall. |
| C.4 | Record each stack choice in both `pyproject.toml` and `AGENTS.md` (e.g. `pydantic>=2` in the dependencies, and the same major version named in the house rules). | Half a decision: agents guess the other half — the wrong major version, or a library named in the docs but missing from the dependencies. |
| C.5 | `AGENTS.md` is navigation, not an encyclopedia: mandatory rules plus one-line pointers, within the hard cap it states. | Context is burned on long house rules, nobody re-reads the bottom half, and "important" stops meaning anything. |
| C.6 | A new `import X` and its `X>=N` entry in `pyproject.toml` land in the same edit. | Works for the author, breaks for every other machine and for CI. |
| C.7 | Deterministic project-state questions are LLM-free scripts behind `make` targets (`scripts/standup.sh`, `make standup`). | Every "where are we?" costs tokens and can return a made-up summary. |
| C.8 | An unused `# type: ignore` is a signal: delete it in the commit whose type check surfaced it (`warn_unused_ignores = true`). | Stale suppressions accumulate and hide real type errors. |
| C.9 | No agent-driven revert or destructive git (`reset --hard`, force-push, `checkout --`, `rm -rf`): the PreToolUse hook blocks them and `permission-matrix.md` §5 denies them. | Catastrophic loss of data or history. |
| C.10 | When the sandbox runtime lags the target, still lint in the sandbox, and shim the few version-only-missing names (e.g. in `sitecustomize.py`) so the full gate runs there; a test that depends on the target's real behaviour stays explicitly skipped and runs on the target. | A partial signal ships, or every check needs a round trip to the real machine. |
| C.11 | Stage-0 discipline is an executable gate (`make bootstrap-check`), not a checklist a person ticks. | Every bootstrap silently ships partial discipline. |
| C.12 | In a mounted sandbox git cannot remove its own lock files: finish commits and pushes from a real terminal and clear stale `.git/*.lock` files there. | "Another git process is running" failures in the middle of the work. |

## D — Working with prior AI output

| ID | Principle | Risk if ignored |
|---|---|---|
| D.1 | Separate design IP from code IP: first extract and judge the decisions a prior agent made, then keep far less of its code than seems reasonable (`docs/codex-audit.md`). | Working-but-misaligned code is carried forward and patched around forever. |

## E — Verification

| ID | Principle | Risk if ignored |
|---|---|---|
| E.1 | Run the tests yourself; never trust a document or an agent that says they pass. | "Done" work that does not even run on your machine. |
| E.2 | Every test names the REQ-ID or D-ID it covers in a comment (`# covers REQ-XX-001`). | Load-bearing tests look incidental and get refactored away. |
| E.3 | Before validating LLM output against a schema, strip markdown fences, unwrap single-key envelopes and check for a refusal sentinel — each one a distinct error. | Every formatting drift of the model becomes one opaque "schema mismatch". |
| E.4 | For a new module behind a locked contract, write the acceptance tests first, then implement to green. | Test and implementation written in the same turn: coverage theatre. |
| E.5 | The test proving a hard acceptance criterion ships in the same wave as the code; after a subagent dies, grep that every criterion's citing test exists. | An untested core ships behind a green but incomplete suite. |
| E.6 | When one dependency is blocked, prove the rest of the pipe: send a real request and find it in the downstream's own run log, attributed to your service. | A blocked dependency hides whether anything else is wired at all. |

## F — Operations and security

| ID | Principle | Risk if ignored |
|---|---|---|
| F.4 | Resolve default paths from a `_repo_root()` helper that walks up to `pyproject.toml`, never from `Path("./x")`. | Failures that depend on the working directory, on a fresh clone or in a CI step. |
| F.5 | On a HIGH-risk surface (auth, PII, payment), run a SAST scan at the release security review when one is budgeted. | Known vulnerability classes ship. |
| F.6 | Every change is secret-scanned (gitleaks: `make secrets`, a leg of `make gate` and of CI). | Secrets reach git history, where rotation is the only fix. |
| F.7 | Declared dependencies are audited for known CVEs (`make deps`, a leg of `make gate` and of CI). | Known CVEs ship. |
| F.8 | Every declared dependency must exist on PyPI and not be brand new (`make slopsquat`). | An agent installs a hallucinated or malicious package. |
| F.10 | Review the license of any wrapped or forked OSS engine at Stage 0: AGPL/GPL/SSPL means wrap, don't fork, plus a legal sign-off (`docs/license-review.template.md`). | Weeks of build on a dependency whose license forbids the product. |

## G — Deliverables and communication

| ID | Principle | Risk if ignored |
|---|---|---|
| G.1 | If the work ends in a narrative (a demo, a presentation, a retrospective), keep the build diary from the first day (`docs/process-log.md`). | A story reconstructed afterwards loses most of what happened. |
| G.5 | One file for two audiences: a `Customer-Visible: Yes/No` column instead of parallel copies. | Two copies drift, and visibility is decided row by row, inconsistently. |
| G.9 | A risk register for a non-engineer: at most seven items, each a short title, one business-language sentence and one next step. | The reader stops reading and the risks go unowned. |

## H — Schemas and lint

| ID | Principle | Risk if ignored |
|---|---|---|
| H.1 | Schema field names mirror the customer's wire format exactly; silence the resulting naming lint in `per-file-ignores`, never per line. | Alias layers on every model, or `# noqa` noise that hides real findings. |
| H.5 | Fix lint with the tool (`make format`, the linter's own fix), never by hand-guessing its canonical form and never with `# noqa`. | Wasted iterations, and suppressions that hide real findings. |
| H.6 | In a src-layout project tell every tool so (`src = ["src"]`, `known-first-party`). | Classification failures that look like import-order bugs. |
| H.7 | Trust strict mypy's narrowing: add a `# type: ignore` only for a real error, pinned to its rule code. | Defensive ignores that hide real type errors after an upgrade. |

## I — Status snapshots

| ID | Principle | Risk if ignored |
|---|---|---|
| I.1 | A roadmap is a dated snapshot, never edited in place (`docs/roadmap-{YYYY-MM-DD}-post-m{N}.md`). | The record of where the project stood at each point is lost. |

## J — Test infrastructure

| ID | Principle | Risk if ignored |
|---|---|---|
| J.1 | Build the app through a factory (`create_app(**overrides)`) so each test injects its own fakes. | Shared state and failures that depend on test order. |
| J.2 | Return boundary results as frozen dataclasses; tests assert by equality. | Handlers mutate results in place and tests assert call sequences instead. |
| J.3 | Coverage gaps are design tells, not targets: add tests where a gap exposes untested behaviour. | Coverage gaming on one side, coverage theatre on the other. |
| J.4 | Drive integration tests against in-process mocks (`httpx.ASGITransport` with a lifespan manager): no ports, no network. | Flaky integration tests that people stop running. |

## K — Architecture and subagents

| ID | Principle | Risk if ignored |
|---|---|---|
| K.1 | A thin customer-facing adapter (contract, auth, validation, idempotency) sits in front of the workflow code, which it reaches through Protocol-typed clients. | Every workflow change puts the customer contract at risk. |
| K.2 | One typed Settings object holds all environment config and validates it at startup; no scattered `os.getenv`. | Undocumented env vars, and config errors found in the middle of a request. |
| K.4 | Independent tasks run as parallel waves of fresh subagents, each given its full context inline. | Serialized work, and a controller whose context fills with implementation detail. |
| K.5 | A data module that both code and tests consume gets a walker test proving every entry is reachable. | The dictionary silently goes stale against its consumers. |
| K.6 | A subagent brief states the bar and allows up to five minutes of discretionary scope, which the subagent reports. | Mechanical execution that misses what the brief forgot. |
| K.7 | Review is done by a fresh subagent that authored none of the code, never by the controller. | Anchoring: the author sees what it expected to see. |
| K.8 | Shared contracts — symbol names, signatures, sync or async, env names and the implementing module — are frozen in the plan, with pasted `grep -n` output, before dispatch. | Runtime import errors, and routes documented but never implemented. |
| K.9 | A later wave that spots a gap left by an earlier one fills it if it is in scope and reports it; anything out of scope is queued, not fixed. | Cross-wave gaps survive into review or production. |
| K.10 | DevOps-owned build and deploy files (`Dockerfile`, `/deploy/**`, CI config) are a cross-team contract: `CODEOWNERS` marks them, and a feature branch never overwrites them. | A merge silently ships the wrong image. |
| K.11 | An agent drives a production UI only under guardrails: it never enters real credentials, each state-changing click is visible and confirmed, and screenshots are not transcribed (`permission-matrix.md` §12). | An agent types secrets or makes an irreversible click. |

## L — Deployed correctness

| ID | Principle | Risk if ignored |
|---|---|---|
| L.6 | A process cannot know its replica count: scale-out is an explicit flag, the process refuses to boot without its preconditions, and all required config is validated at once at startup. | Silent double-processing, and one crash-and-redeploy per missing variable. |
| L.7 | Version-stamp the health probe: `/health` returns `{status, version, build}`, with `APP_BUILD` set by the build. | An old image runs unnoticed behind a green probe. |
| L.8 | Configured is not working: invoke every external dependency once for real, and read the result, before calling it ready (`make smoke-deps`). | Go-live on a dependency that never served a request. |
| L.9 | Read each critical config value back from inside the running process (set or empty, and its length — never the value). | A key dropped by the injection layer, discovered as "but I set it". |
