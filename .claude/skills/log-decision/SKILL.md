---
name: log-decision
description: Append a new ADR to docs/decisions.md in the standard format (D-NNN with Status/Decision/Rationale/Mitigation/Revisit-when). Use whenever a non-trivial design choice is made under uncertainty. Append-only — never edits.
---

1. Read `docs/decisions.md` to find the next available D-ID number.
2. IMPORTANT: IDs are immutable (seed B.5). If D-013 was previously used but the decision was superseded, the next new decision is D-NNN where N = last number + 1. Never reuse IDs. Never edit old entries (B.2 — supersede, don't edit).
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
5. Append to `docs/decisions.md` (do NOT insert in the middle; chronological append-only).
6. If this decision supersedes an earlier one (e.g., D-013 → D-NNN):
   - DO NOT edit D-013's body.
   - DO append a "Status: superseded by D-NNN" line to D-013, but only as a NEW line (not in-place edit).
7. Confirm to the user: "ADR D-NNN appended (status proposed). User approval moves it to status accepted."
