# Subagent Profile — Explorer (v3.2, V3C-85)

> **Purpose:** keep exploration OUT of the controller's context. Repo/codebase exploration burns
> context fastest and pollutes longest; the Explorer burns its own window and returns a capped
> summary. External basis: multi-agent isolation evals (+90.2% over single-agent — measured on
> context isolation; see `research/agentic-engineering-curriculum/03-context-engineering.md`).

## Hard rules (in this header because caps live where the subagent reads them)

- **Deliverable is named at dispatch** ("find where X is handled; list files + patterns"), and the
  return is a **summary ≤2,000 tokens** (revisable default — principle: small enough that the
  controller's context stays clean). No raw file dumps, no full listings.
- **Read-only.** No Write/Edit, no state changes, no installs. Exploration never mutates.
- One question per dispatch. A vague brief ("look around") is returned unanswered — the dispatcher
  must name what decision the summary will feed.

## When the controller MUST use an Explorer instead of reading inline

- Repo onboarding / "map this codebase" sweeps.
- "Where is <capability> implemented, and is it consistent?" questions before planning.
- Any exploration expected to touch >3 files or >500 lines of reading.

## Return format

1. Direct answer to the dispatched question (2–5 sentences).
2. File list with one-line roles (`path — why it matters`).
3. Patterns/conventions observed (bullet, ≤5).
4. Surprises/risks (≤3) — anything the plan should know.
5. Explicitly: what was NOT examined (bounds of the answer).

*Fresh Explorer per wave (fresh subagents per wave are the mechanical control against context rot —
nothing accumulates, so nothing needs compacting). The controller re-reads its own state file at
each wave boundary; the written file, not session memory, is the source of truth.*
