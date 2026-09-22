# model_ranking — LLM Benchmark & Recommendation Engine (DevFlow v6.0)

> model_ranking: aggregates free-and-legal LLM benchmark + pricing data and produces budget-aware, per-use-case model recommendations, served to its own iOS app. Process: [DevFlow v6.0](https://github.com/SADCAIVibe/DevFlow/tree/v6.0) since 2026-09-23 (D-155); General Pipeline v4.3.1 -> v5.0 before that. `make gate` is everything the pipeline claims to enforce; `make check` is its day-to-day subset.
>
> **★ Fresh agent or new team member?** This is a RUNNING project, so the first question DevFlow asks — new or resuming? — is already answered: resuming. Run `/start-session`, which reads `note.txt`, the latest plan and the latest retrospective and establishes what green looks like before anything changes. Then `AGENTS.md` (the rules). `METHODOLOGY.md` is the reference, not a linear read; `pipeline-schema.html` is the same workflow as a picture.
>
> **★ Git, in one line (D-999, D-155):** the agent works on a branch and opens a DRAFT pull request; the owner marks it ready and merges. Nothing is pushed to `main` by an agent.

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

See `METHODOLOGY.md` for the full design and `pipeline-schema.html` (open in browser) for the visual schema.

For a plain-language overview to share with managers or non-technical stakeholders, see DevFlow's own [README](https://github.com/SADCAIVibe/DevFlow/tree/v6.0); the executive overview stayed with the methodology and is not shipped into a project.

## What's new vs v1.1

- **Hooks** — `.claude/settings.json` enforces 2 baseline rules deterministically.
- **Skills** — DevFlow's 14 skills under `.claude/skills/`: `/start-session` to resume, `/work-issue` and `/work-enhancement` for a change, `/pre-merge` and `/post-merge` around the owner's merge, `/cycle-close` at a milestone (retrospective and handover), plus `/triage-issue`, `/file-issue`, `/fix-issue`, `/log-decision`, `/repo-review`, `/going-live`, `/writing-a-control` and `/wiring-an-integration`.
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
4. `/start-session` — resumes from files (note.txt, the latest plan, the latest retrospective); it replaced the onboarding guide at DevFlow v6.0.
5. `docs/closure-checklist.md` — when you "ship," walk this.

## Repo layout

```
.
├── METHODOLOGY.md          # DevFlow's full design (a reference, not a linear read)
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

## Data attribution

Epoch AI benchmark data is used under CC BY 4.0. Required citation: Epoch AI, ‘AI Benchmarking Hub’. Published online at epoch.ai. Retrieved from ‘https://epoch.ai/benchmarks’ [online resource].
This citation also travels in every ranking export and recommendation payload source list
(REQ-LIC-001).
