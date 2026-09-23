# model_ranking — LLM Benchmark & Recommendation Engine (DevFlow v6.4)

> model_ranking: aggregates free-and-legal LLM benchmark + pricing data and produces budget-aware, per-use-case model recommendations, served to its own iOS app. Process: [DevFlow v6.4](https://github.com/SADCAIVibe/DevFlow/tree/v6.4) since 2026-09-23 (D-155, D-161); General Pipeline v4.3.1 -> v5.0 before that. `make gate` is everything the pipeline claims to enforce; `make check` is its day-to-day subset.
>
> **★ Fresh agent or new team member?** This is a RUNNING project, so the first question DevFlow asks — new or resuming? — is already answered: resuming. Run `/start-session`, which reads `docs/process-log.md` and the latest plan and establishes what green looks like before anything changes. Then `AGENTS.md` (the rules). `pipeline-schema.html` is the same workflow as a picture.
>
> **★ Git, in one line (D-999, D-155):** the agent works on a branch and opens a DRAFT pull request; the owner marks it ready and merges. Nothing is pushed to `main` by an agent.

---

## Quick start

```bash
make install     # venv + deps
make hooks       # once per clone: make gate before every push
make check-fast  # the same legs as make check, side by side -- what the post-edit hook runs
make check       # the offline half of the gate, in order: the merge gate
make run         # local dev server
make standup     # LLM-free project-state dump (per seed C.7)
make help        # every target, with what it does
```

`make check` must be **green on day 1**. If it isn't, fix that before writing any feature code (seed C.1).

## How to read this repo as a new agent (or new human)

`AGENTS.md` is the canonical rulebook: house rules, the stage model, the default-deny surfaces, and
the routing index to everything else. `CLAUDE.md` is one line, `@AGENTS.md`, which Claude Code
reads as an import on every OS, so both names load the same rules. **This README does not restate
its rules**: a second copy of a rule is a copy that goes stale.

The rest is read on demand, when a rule or a stage points at it:

- the skills in `.claude/skills/` — each stage's steps, from `/setup-project` to `/cycle-close`
- [`permission-matrix.md`](permission-matrix.md) — what you may and may not do, plus the BLOCKING
  taxonomy
- `docs/decisions.md` — what is settled (D-001..D-007 universal, project ADRs from D-100)
- `docs/closure-checklist.md` — milestone close and release
- `docs/security-baseline.md` — the release security review
- `.agents/rules/practices.md` — the engineering rules
- `UPGRADING.md` — moving this project to a newer DevFlow

## Repo layout

```
.
├── pipeline-schema.html        # visual schema (open in browser)
├── AGENTS.md                   # house rules (≤150 lines, D-003)
├── CLAUDE.md                   # one line: @AGENTS.md
├── Makefile                    # canonical commands
├── .devflow-stack              # the product's stack: python
├── pyproject.toml              # stack lock
├── permission-matrix.md        # default-deny + BLOCKING taxonomy
├── .claude/                    # harness config, hooks, skills, subagents (.claude/agents/)
├── .agents/rules/              # canonical rulebook (practices, seeds, git authority, review seats)
├── .githooks/pre-push          # make gate before every push (make hooks)
├── .github/CODEOWNERS          # DevOps build/deploy boundary (K.10)
├── .github/workflows/          # CI + issue-agent (hardened)
├── docs/                       # PRD, decisions, plans, reviews, closure reports
├── src/app/                    # adapter + clients (Protocol pattern, K.1) + workflows
├── ios/                        # the iOS app and its Engine layer
├── tests/                      # unit + integration
└── scripts/                    # gates, standup.sh, bootstrap-check.sh (Stage-0 gate)
```

## License

Proprietary — ILGAR / Umut Can Apaydın. All rights reserved.

## Data attribution

Epoch AI benchmark data is used under CC BY 4.0. Required citation: Epoch AI, ‘AI Benchmarking Hub’. Published online at epoch.ai. Retrieved from ‘https://epoch.ai/benchmarks’ [online resource].
This citation also travels in every ranking export and recommendation payload source list
(REQ-LIC-001).
