---
name: retrospect
description: Walk the G.12 retrospective format at milestone closure (M≥3 only). Categorize every discipline that fired this cycle with PULLED-WEIGHT / PARTIAL / THEORETICAL / TOO-EARLY verdicts. Use ONLY at Stage 4.2 closure when M≥3.
---

1. Verify current milestone N satisfies N≥3. If not, stop — G.12 retrospectives need a minimum sample size to differentiate verdict columns.
2. Read these source files:
   - `docs/plans/m{N}-plan.md` (what disciplines were planned to fire)
   - `docs/reviews/m{N}-*.md` (what disciplines actually caught BLOCKING / MINOR)
   - `docs/process-log.md` S{N} entry
   - Prior `docs/retrospectives/m{N-1}-retrospective.md` (continuity)
3. For every discipline that fired this milestone, assign one of:
   - **PULLED-WEIGHT** — fired AND caught something that would have shipped broken otherwise. Provide a concrete example with `file:line`.
   - **PARTIAL** — fired but the catch was small / cosmetic / redundant with another discipline.
   - **THEORETICAL** — fired but caught nothing this milestone. Don't kill yet; sample size matters.
   - **TOO-EARLY** — discipline is new (first 1-2 milestones); insufficient signal.
4. Write `docs/retrospectives/m{N}-retrospective.md` with format:
   ```
   # M{N} Retrospective — G.12 (Sample N=<N - 2>)

   Date: YYYY-MM-DD
   Milestone: M{N}
   Disciplines evaluated: <count>

   ## PULLED-WEIGHT (the proven ones)
   - <Discipline> (e.g., K.7 fresh-eyes review)
     - Concrete catch: file:line — issue avoided
   ## PARTIAL
   - <Discipline> — explanation
   ## THEORETICAL
   - <Discipline> — explanation
   ## TOO-EARLY
   - <Discipline> — explanation

   ## Disciplines-retired count this milestone
   <number>: <list of disciplines marked for retirement per anti-bloat>

   ## Carried question (v3.1, V3C-79)
   Answered from M{N-1}: <the previous retro's carried question + this milestone's evidence-backed answer>
   Carried to M{N+1}: <exactly ONE open question this retro cannot yet answer>

   ## Implications for next milestone (M{N+1})
   - <action 1>
   - <action 2>
   ```
5. **v3.1 (V3C-79):** answer the carried question from the previous retro with evidence; pose exactly ONE for the next. A discipline proposed twice but never implemented must be BUILT next milestone or RETIRED now — never carried a third time.
6. Append to `docs/process-log.md` S{N} entry: `Lesson: <retrospective key takeaway>`.
7. The Stage 4 closure check fails if this file is missing for M≥3.
