---
name: log-decision
description: Use the moment a non-trivial choice is made under uncertainty — a trade-off, a library, a boundary, an exception to a rule, a deliberate deferral. Appends a decision record: what, why, and when to revisit. Append-only; a reversal supersedes, it never edits. Decisions are the expensive part and code is the cheap part.
---

1. Read `docs/decisions.md`. **Project ADRs start at D-100**: the next ID is the highest D-number
   at or above D-100, plus one — or D-100 itself if there is none. D-001..D-099 are the reserved
   universal band and are never the base for a project number.
   While D-100 is still the `<First project decision>` placeholder, the first decision fills it.
2. IDs are immutable (seed B.5): a superseded ID is still used. Never reuse one. Never edit old entries (B.2 — supersede, don't edit).
3. Ask the user for the decision content if not provided. The minimum required:
   - Topic (one sentence)
   - Decision (what we're choosing)
   - Rationale (why this option won)
4. Construct the ADR-lite entry:
   ```
   ## D-NNN — <Topic>

   **Status:** proposed
   **Decision:** <what we chose>
   **Rationale:** <why>
   **Mitigation if violated:** <what would go wrong>
   **Revisit when:** <trigger to reopen>
   ```
5. Append to the end of `docs/decisions.md`, after the last project ADR (do NOT insert in the middle; chronological append-only).
6. If this decision supersedes an earlier one (e.g., D-013 → D-NNN):
   - DO NOT edit D-013's body.
   - DO append a "Status: superseded by D-NNN" line to D-013, but only as a NEW line (not in-place edit).
7. Confirm to the user: "ADR D-NNN appended (status proposed). User approval moves it to status accepted."
