# M<N> plan — <goal in one line>

<!-- Copy to `docs/plans/m<N>-plan.md` at `/plan-milestone` step 2 (heavy mode). Two lines are read by
     scripts and keep their wording: `waves:` (how many waves the plan has -- `make wave-check`
     derives "the plan's last wave" from it, so the milestone Tester and Security-Reviewer cannot be
     skipped by a wave that says it is not the last) and `security-globs:` (read by
     `make review-need` beside the brief's `Paths that make a change HIGH:`). The acceptance criteria
     are frozen when the owner merges this plan; a later change is an appended amendment row, never a
     silent edit. -->

waves: <n>
security-globs: <none | comma-separated globs>

## Goal

<what this milestone delivers, and for whom>

## Acceptance criteria

| REQ-ID | Criterion (end to end: who does what through which entry point, and what they see) |
|---|---|
| <REQ-..> | <criterion> |

## Risk tier

<LOW | MEDIUM | HIGH>, and why. MEDIUM/HIGH: one alternative approach and its trade-offs.

## Spike check

<none | the part that needs a throwaway `spike-*` branch, and the question it answers>

## Wave 1

- REQ-IDs: <...>
- Risk tier: <LOW | MEDIUM | HIGH>
- Tasks (each ≤5 minutes of subagent scope): <...>
- Container issue: #<n>; children: #<n>, #<n>

## K.8 contracts

<shared types, factories, env var names the waves rely on, each with its pasted `grep -n` output>

## Token budget

<the owner's figure, or `n/a`>

## Issue inventory

| Issue | Wave | Note |
|---|---|---|
| #<n> | 1 | <joined / left out, and why> |

## Closure tasks

<what the milestone close owes beyond the reviews: a roadmap snapshot, a migration note, ...>

## Amendments

| Date | What changed | Why |
|---|---|---|
