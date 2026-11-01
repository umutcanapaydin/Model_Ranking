# `.agents/rules/` — Canonical Rulebook

> `practices.md` and `issues.md` are the rules: read them at the start of a session, with `AGENTS.md`.
> `playbook-seeds.md` is reference: open it when a rule cites a seed, not at session start.

---

## Files in this directory

| File | Status | Purpose |
|---|---|---|
| `practices.md` | committed | Portable engineering rules across machines / developers |
| `issues.md` | committed | Issues, labels and the verification pipeline — the skills implement it |
| `issues-qa.md` | committed | The verification pipeline and the closing-keyword rule — read only when the brief says `QA verification: on` |
| `two-tools.md` | committed | Read only while a second agent tool (Codex, or another) works here: what changes for it |
| `ci-traps.md` | committed | Read only when the CI issue agent is on, or a draft shows no CI run: the two repository facts that stop it quietly |
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
2. Run `/start-session`. It is the read order and it runs the checks; `AGENTS.md` §3.1 is the
   order before any change. There is no second list here, because two lists drift.

---

## Promotion rules

- A frequently-applied principle → add its row to `playbook-seeds.md` once the owner approves it.
- A seed that has been ACTIVE for 3+ milestones AND keeps catching issues → consider promoting its mechanism to a hook (`.claude/settings.json` — see the hook-promotion rule under "How to add a hook" in `permission-matrix.md`).
- An active seed that hasn't fired in 90 days → propose retirement in the end-of-work diet (`/cycle-close`).
