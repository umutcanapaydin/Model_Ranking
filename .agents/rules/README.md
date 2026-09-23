# `.agents/rules/` — Canonical Rulebook

> `practices.md` and `issues.md` are the rules: read them at the start of a session, with `AGENTS.md`.
> `playbook-seeds.md` is reference: open it when a rule cites a seed, not at session start.

---

## Files in this directory

| File | Status | Purpose |
|---|---|---|
| `practices.md` | committed | Portable engineering rules across machines / developers |
| `issues.md` | committed | Issues, labels and the verification pipeline — the skills implement it |
| `playbook-seeds.md` | committed | Index of the seeds (A.1, C.9, L.7 …) that rules cite |
| `environment.md.template` | committed | Template for your own `environment.md` |
| `environment.md` | **gitignored** | YOUR machine specifics (shell, language runtime, paths) — generate on first session |
| `README.md` (this file) | committed | This index |

---

## What goes where

- **Universal to the project** (any developer / machine) → `practices.md` or a new file like `architecture.md`, `data-model.md`, `deploy.md`, `security.md`.
- **Per-developer machine specifics** (your conda env, shell, ports, container names) → `environment.md` (NEVER commit; never share).
- **Generalizable principles** discovered while building → `playbook-seeds.md`: one row, ID · principle · risk if ignored (format in the file's header).

---

## First-session checklist

If you just cloned this repo:

1. Generate your own `environment.md` (gitignored) from `.agents/rules/environment.md.template`.
2. Read `AGENTS.md` at the repo root (hard cap 150 lines; the rules, and a routing index to everything else).
3. Read `practices.md` and `issues.md` end-to-end.
4. Skim `playbook-seeds.md` so you know where the seeds live. Don't memorize it.
5. Verify `make check` is GREEN.

---

## Promotion rules

- A frequently-applied principle → add its row to `playbook-seeds.md` once the owner approves it.
- A seed that has been ACTIVE for 3+ milestones AND keeps catching issues → consider promoting its mechanism to a hook (`.claude/settings.json` — see the hook-promotion rule under "How to add a hook" in `permission-matrix.md`).
- An active seed that hasn't fired in 90 days → propose retirement in the end-of-work diet (`/cycle-close`).
