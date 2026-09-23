---
record_type: brief
id: project-brief-template
status: draft
process_version: v6.6
date: 2026-09-23
---
<!-- When you copy this template, KEEP this frontmatter and change `id` to match your
     filename. `check_records.py` reads it; a copy without it fails R1 on the first run. -->
# Project Brief — `<PROJECT_NAME>`

> **`/setup-project` fills this.** It reads what the repository already says, asks the nine questions
> in §2 in one message, and writes every answer into its field — an unanswered question takes its
> default, written down as the default. It commits the brief on a branch and opens a draft PR; **the
> owner merging that PR is the owner signing the choices.** A choice that changes later is updated
> the same way. This file is the one place the next agent reads them.

---

## 1. What the repository already says (read first, not asked)

- **Project name:** `<from pyproject.toml>`
- **Stack recorded so far:** `<from .devflow-stack>`
- **Customer / owner:** `<who is asking for this software>`
- **One-line description:** `<what this project does, in plain English>`
- **Repo host:** `<from git remote -v>`
- **Owner's commit identity:** `<from git config user.email>`
- **Already on a DevFlow version?** `<none | the version in .gp/installed, or the one an earlier install's docs/decisions.md declares>`
- **Code beyond the starter?** `<no | yes: what, and in which language>`

## 2. The setup answers (`/setup-project`, in its order)

1. **Where are we starting:** `<new | upgrade | adopted>` *(default derived from §1: a recorded
   install version means **upgrade**, follow `UPGRADING.md` and nothing else from this list until it
   is done; code beyond the starter means **adopted**, and `docs/codex-audit.md` records what exists
   before any wave changes it; otherwise **new**)*
2. **Milestone Quality Gate:** `<off (default) | on>` *(on: every milestone close also writes
   `docs/closure-report-m{N}.md` with the REQ-ID trace, coverage delta and token cost, `make closes`
   grades it, and the owner runs his own milestone test session; off: a milestone closes on its merged
   waves, and each wave's Tester already requires a citing test for every criterion it touched)*
3. **Retrospective when the work is done:** `<no (default) | yes>` *(one short file at the very end,
   `/cycle-close`, Stage 5.3 — never during the work)*
4. **HIGH-risk areas this project touches:** *(default: none, until the first one appears; a wave
   touching one is HIGH: it also gets a security pass, and the senior reviewer in 5 reviews it)*
   - [ ] Authentication / authorization
   - [ ] Payments / financial transactions
   - [ ] Personal data (real customer data, not synthetic fixtures)
   - [ ] Cryptography
   - [ ] Irreversible migrations (DROP TABLE class)
   - [ ] Regulated compliance (PDPL / GDPR / HIPAA / SOC2)
   - [ ] Production deploy automation
   - [ ] Wraps / forks an OSS engine *(not a question of its own: a ticked box makes
         `docs/license-review.md` required, and `make bootstrap-check` reads this line)*
5. **Senior human reviewer for those areas:** `<name + contact>` *(default: the owner)*
6. **Does the work end in a deploy, and where:** `<yes: target environment | no>` *(default: decided
   at the first release; it decides whether Stage 5 — security review, then `/going-live` — applies
   and what it checks against)*
7. **What this repository can enforce by itself:** *(default: assume neither until someone checks;
   replace each placeholder with the bare word `yes` or `no` — `make bootstrap-check` reads these two
   lines, and unless both say `yes`, a clone without `make hooks` fails Stage 0)*
   - GitHub Actions run here: `<yes | no>` *(a private repository on a free plan may have no minutes)*
   - The default branch can be protected: `<yes | no>` *(no: the gate on each developer's machine is
     the only enforcement)*
   - `make hooks` installed in every clone (the gate runs before every push): `<yes | no>`
8. **The CI issue agent:** `<no (default) | yes>` *(a labelled issue triggers a headless agent that
   comments or opens a draft PR; it needs Actions and an API key in the repository secrets)*
9. **The product:**
   - Stack: `<python (default) | the name bound in stack.mk>` *(written to `.devflow-stack`; any stack
     but `python` binds its four legs in `stack.mk` — `INSTALL.md`, "Binding another stack")*
   - Language of its user-facing copy: `<English (default) | the language>`
   - Paths that hold that copy: `<none | the paths>` *(the repository stays English; each path goes
     into `.language-allow` with its reason — design files, localisation strings)*

## 2.1 Repositories — every tree that ships something a customer can reach

**A product is not a repository.** A customer-facing product split across two trees, with DevFlow
installed in one, leaves the second ungoverned — not by anyone's decision, but because nothing asked.

List **every** repo that ships an artifact a customer can reach: backends, frontends, mobile
clients, admin consoles, scheduled jobs, infrastructure that serves traffic. A tree that only builds
internal tooling is out of scope; say so in a row rather than by leaving it out.

| Repo | What a customer reaches from it | DevFlow installed? | If NO: the owner ruling |
|---|---|---|---|
| `<org/repo>` | `<the API / the console / the mobile app>` | yes / no | `<the refusal, as "refusals.md R-n", or "—">` |
| `<org/repo-fe>` | `<...>` | yes / no | `<...>` |

**Each repo is either DevFlow-installed or named in `docs/refusals.md` with an owner ruling.**
`make bootstrap-check` asserts that this declaration exists and is filled — at least one real row, no
placeholders left, and every `no` carrying a ruling. It claims nothing about the contents of the
other trees, which it cannot see.

## 3. Other choices (defaults unless the owner changes them)

- **CODEOWNERS / DevOps boundary (K.10):** does app + DevOps share this repo? `<yes | no>` *(default:
  yes → fill `<DEVOPS_HANDLE>` in `.github/CODEOWNERS` and enable "Require review from Code Owners";
  no DevOps team → delete the build/deploy lines rather than leaving a placeholder owner)*
- **Version-stamped `/health` (L.7):** on by default *(set `APP_BUILD` in the Dockerfile / deploy env so
  the deployed build is verifiable via `curl /health | jq .build` at Stage 5.2; opt out only for a
  service that genuinely never deploys)*
- **Token budget cap per milestone:** `<e.g., $5 / 500k tokens / no cap>`
- **MCP servers beyond the GitHub default:** `<none (default) | list>` *(add only if the team uses the
  tool daily)*
- **AGENTS.md size cap:** 150 hard cap (the template ships at ≤120) *(change only by ADR)*
- **Subagent profiles beyond the shipped four:** `<none (default) | list>` *(a new profile is a
  candidate until it meets the graduation rule in `docs/subagents.md`)*

## 4. Notes / unusual context (free text)

`<anything that doesn't fit elsewhere — e.g., "the customer is on holiday until Nov 15", "the senior reviewer is on leave M3-M5">`

---

**Next:** the common steps in `INSTALL.md` — `make install`, `make hooks`, `make labels`, a
`stack.mk` for a stack other than `python`, then `make bootstrap-check` (walk
`docs/closure-checklist.md` §0) — then `/plan-milestone`. The owner approves each milestone plan by
merging its PR; no wave is dispatched before that.
