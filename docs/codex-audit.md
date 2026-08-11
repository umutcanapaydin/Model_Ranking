# Codex Audit (only if pre-existing code IP)

> Seed D.1: separate design IP from code IP. If predecessor handed you a code base, don't patch forward — audit, extract design decisions, discard the rest, regenerate fresh.
>
> Skip this file if project is greenfield.

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
