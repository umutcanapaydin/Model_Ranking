# Warning ledger (V4C-77)

> **Copy of `warnings.ledger.template.md`, instantiated so a fresh install starts with a report rather
> than a silence.** Read the template for why `C2b` stops at three.

**The rule in one line: a warning may not survive the close it was raised in.** It is FIXED, ACCEPTED
with a reason AND an owning milestone, or ESCALATED. `check_records.py` rules `C2a`/`C2b`/`C2c` enforce it.

| id | rule that warned | first seen | path | status | reason + owning milestone |
|---|---|---|---|---|---|
| W-001 | gitleaks `generic-api-key` | 2026-08-15 (M3-W0) | docs/reviews/m2-security-review.md:8 | ESCALATED | False positive: the match is the prose "APIs, D-101-compliant" (an ADR label, zero entropy), present since the M2 commit. Escalated to the owner same-day per AGENTS.md §3 (agents never waive scanner findings). Proposed remedy for the owner's M3 closure session: a scoped `.gitleaks.toml` allowlist for the `D-\d+` ADR-label pattern — owner decision, owning milestone M3. |
