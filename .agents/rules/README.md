# `.agents/rules/` — Canonical Rulebook

> Read every file in this directory at the start of every session. These are the rules.
>
> Pipeline v2.0 consortium decision: this directory replaces `docs/discipline-*.md` from v1.1. Same content, cleaner hierarchy.

---

## Files in this directory

| File | Status | Purpose |
|---|---|---|
| `practices.md` | committed | Portable engineering rules across machines / developers |
| `playbook-seeds.md` | committed | All 64 + 8 seeds across themes A-K |
| `environment.md` | **gitignored** | YOUR machine specifics (shell, language runtime, paths) — generate on first session |
| `README.md` (this file) | committed | This index |

---

## What goes where

- **Universal to the project** (any developer / machine) → `practices.md` or a new file like `architecture.md`, `data-model.md`, `deploy.md`, `security.md`.
- **Per-developer machine specifics** (your conda env, shell, ports, container names) → `environment.md` (NEVER commit; never share).
- **Generalizable principles** discovered while building → `playbook-seeds.md` (Principle / Origin / Reusable artifact / Risk if ignored / Tradeoff).

---

## First-session checklist

If you just cloned this repo:

1. Generate your own `environment.md` (gitignored). Template at `.agents/rules/environment.md.template` if present, otherwise create from scratch matching the practices.md style.
2. Read `practices.md` end-to-end.
3. Scan `playbook-seeds.md` — themes A through K. Don't memorize; know where things live.
4. Verify `make check` is GREEN.
5. Read `AGENTS.md` at repo root (≤80 lines, navigation only).

---

## Promotion rules

- A frequently-applied principle → propose a seed in `playbook-seeds.md` (status: candidate). User approval moves to active.
- A seed that has been ACTIVE for 3+ milestones AND keeps catching issues → consider promoting its mechanism to a hook (`.claude/settings.json` — see `permission-matrix.md` §11 hook-promotion rule).
- An active seed that hasn't fired in 90 days → propose retirement at the quarterly handover (PM lens: disciplines-retired count).
