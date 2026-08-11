# model_ranking — LLM Benchmark & Recommendation Engine (Pipeline v4.2)

> model_ranking: aggregates free-and-legal LLM benchmark + pricing data and produces budget-aware, per-use-case model recommendations (engine behind a future iOS advisor app). Generated from the D-A vibe-engineering pipeline template v4.2. Run `make check` (day-1 green) and `make bootstrap-check` (the Stage-0 gate) until both pass. (v2→v4 changelog: `pipeline-design.md` §0.)
>
> **★ Fresh agent or new team member?** Read [`START_HERE.md`](START_HERE.md) first (5-minute orientation). Then `AGENTS.md`, then the rest.
>
> **★ Starting a brand-new project?** Fill out [`docs/project-brief.template.md`](docs/project-brief.template.md) (~5-10 minutes) and hand it to the agent alongside the PRD. The brief §10 is the contract for what the agent must deliver (plan + workload estimate) before any wave dispatches.

---

## Quick start

```bash
make install     # venv + deps
make check       # lint + typecheck + test (the gate)
make run         # local dev server
make standup     # LLM-free project-state dump (per seed C.7)
```

`make check` must be **green on day 1**. If it isn't, fix that before writing any feature code (seed C.1).

## What this is

A starter repo with two layers:

1. **Layer 1 — Starter Package (~60 files)** — opinionated scaffolding from EF-AI Phase-1 + Claude Code harness.
2. **Layer 2 — Workflow (5 stages)** — Bootstrap → Plan → Wave → Per-Wave Review (Code + Tester; v3 V3C-68) → Closure (Security review is BLOCKING before deploy). Quarterly handover every 3rd milestone.

See `pipeline-design.md` for the full design and `pipeline-schema.html` (open in browser) for the visual schema.

For a plain-language overview to share with managers or non-technical stakeholders, see `docs/executive-overview.pdf` (rendered from `docs/executive-overview.md`). Both are regenerated from one source via `docs/executive-overview.gen.py` — refresh them at each version cut.

## What's new vs v1.1

- **Hooks** — `.claude/settings.json` enforces 2 baseline rules deterministically.
- **Skills** — 10 starter skills under `.claude/skills/` including `/triage-issue`, `/fix-issue-{prepare,implement}`, `/file-issue`, `/quarterly-handover`, `/log-decision`, `/retrospect`.
- **`.agents/rules/`** — canonical rulebook directory; `environment.md` is per-developer gitignored.
- **MCP** — `.mcp.json` ships with GitHub/GitLab default; tokens in `.env`.
- **3-layer issue management** — pure CI / CI-triggered agent / scheduled + interactive.
- **AGENTS.md canonical**, CLAUDE.md symlink.
- **BLOCKING taxonomy locked** in `permission-matrix.md` §11.
- **Gitleaks** for secret scanning (replaces TruffleHog mention).

## How to read this repo as a new agent (or new human)

1. `AGENTS.md` — house rules (≤80 lines, navigation only).
2. `permission-matrix.md` — what you may + may not do (default-deny matrix + BLOCKING taxonomy).
3. `docs/decisions.md` — what is settled (D-001..D-005 universal + project D-006+).
4. `docs/onboarding.md` — Pazartesi-başla / Cuma-milestone-bitir rehberi (Monday-start, Friday-milestone-done guide).
5. `docs/closure-checklist.md` — when you "ship," walk this.

## Repo layout

```
.
├── pipeline-design.md      # full v3 design document (§0 changelog)
├── pipeline-schema.html     # visual schema (open in browser)
├── AGENTS.md                   # house rules (≤80 lines)
├── CLAUDE.md → AGENTS.md       # symlink so Claude Code finds it natively
├── Makefile                    # canonical commands
├── pyproject.toml              # stack lock
├── permission-matrix.md        # default-deny + BLOCKING taxonomy
├── note.txt                    # current-turn handoff (≤30 lines)
├── .claude/                    # harness config + 10 skills
├── .agents/rules/              # canonical rulebook (practices, seeds, environment)
├── .github/CODEOWNERS          # DevOps build/deploy boundary (K.10, v2.1)
├── .github/workflows/          # CI + issue-agent (hardened)
├── docs/                       # PRD, decisions, plans, reviews, retrospectives, handovers
├── docs/executive-overview.*   # manager-facing overview (.md + .pdf; regen via .gen.py)
├── subagent-profiles/          # Code-Reviewer + Security-Reviewer (MANDATORY)
├── src/<pkg>/                  # adapter + clients (Protocol pattern, K.1)
├── tests/                      # unit + integration
└── scripts/                    # standup.sh + bootstrap-check.sh (Stage-0 gate, FB-1)
```

## After clone — set up symlink

```bash
ln -s AGENTS.md CLAUDE.md
```

Both names point to the same file. Industry standard (AGENTS.md, in 60k+ public repos) + Claude Code's native loading (CLAUDE.md). Zero drift.

## License

Proprietary — ILGAR / Umut Can Apaydın. All rights reserved.
