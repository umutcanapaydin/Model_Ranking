---
name: log-decision
description: Use the moment a non-trivial choice is made under uncertainty — a trade-off, a library, a boundary, an exception to a rule, a deliberate deferral, or retiring a control. Appends an ADR; a reversal supersedes, never edits.
---

1. `make next-adr` prints the next ID — never read `docs/decisions.md` for it. **Project ADRs start
   at D-100** (D-001..D-099 is the universal band); while D-100 is still the `<First project
   decision>` placeholder, the first decision fills it. Read only the ADRs this one touches.
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
   An answer the owner gave to a run's decisions message (`/plan-run` §2) adds one line after
   **Status:** — `**Owner ruling:** <date>, in chat, for run <name>` — and its id goes on the run
   file's `Rulings:` line (`make run-check` refuses an id this file does not hold).
5. Append to the end of `docs/decisions.md`, after the last project ADR (do NOT insert in the middle; chronological append-only).
6. If this decision supersedes an earlier one (e.g., D-013 → D-NNN):
   - DO NOT edit D-013's body.
   - DO append a "Status: superseded by D-NNN" line to D-013, but only as a NEW line (not in-place edit).
7. An ADR that retires a control or relaxes one also appends its row to `docs/watchlist.md`: what it
   caught, why it goes, the count that brings it back.
8. Confirm to the user: "ADR D-NNN appended (status proposed). Your merge of the PR that carries it
   accepts it." No status line is edited for that: an ADR on the default branch is accepted (`make
   standup` lists only the proposed ADRs not merged yet).
