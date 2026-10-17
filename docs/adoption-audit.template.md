# Adoption audit — what an existing codebase holds before DevFlow changes it

<!-- Copy to `docs/adoption-audit.md` at `/setup-project` question 1c (an adopted codebase); a
     brand-new project never needs it. -->

> Seed D.1: separate design IP from code IP. An adopted codebase is audited before any issue is filed against it: what exists, what its tests prove, which design decisions it embodies, and what stays — `INSTALL.md` keeps your code where it is; this file records what it is. Written by `/setup-project` (question 1c).

---

## 1. Source code IP received

| Source | Format | Received from | Date |
|---|---|---|---|
| `<repo / zip / handoff>` | `<lang / framework>` | `<who>` | YYYY-MM-DD |

## 2. Design IP to ADOPT

What from the source informs OUR design (no code reuse — just intent):

- `<decision or pattern>` — `<why it transfers>`

## 3. Code IP to DISCARD

- `<module / approach>` — `<why discard — e.g., wrong stack, sunk-cost trap (B.3)>`

## 4. Tests as specifications

Useful behaviors captured from source tests (not the test code itself):
- `<test name / scenario>` → REQ-XX-NNN (target REQ-ID)

## 5. Path A vs Path B reversal log

Record any "considered patching forward but reversed to regenerate" decisions here (B.2 + B.3).
