---
record_type: register
id: watchlist
status: ratified
process_version: v5.0
date: 2026-08-12
---
# Watch list — controls removed, and what brings each one back

**The owner's rule, translated:** *"if it happens again we bring it back in, based on how many times it
recurs. That way we learn which ones actually earn their place and which one we added because we hit it
once in a million and it's now just dead weight."*

**This is the first time this lineage has ever asked whether a control earns its place.** Every rule we
have was added after something went wrong, and not one was ever revisited. A list that only grows is
not a policy, it is a sediment.

## How a row returns

A removed control comes back when its `count` reaches its `returns at` — counted **in real projects,
not here.** It returns with field evidence and a falsification recipe, or it does not return.

If the count stays at zero, that is a result too, and a valuable one: it means we correctly identified
something we had over-fitted to a single incident.

| id | what it caught | why removed | count | returns at |
|---|---|---|---|---|
| `check-templates` | a shipped template that no longer parses | needs a built artifact; unfalsifiable here for 5 versions (TB-001) | 0 | 1 |
| `cold-start` | a repo that cannot be built from scratch | needs a clean machine; never demonstrated to catch anything | 0 | 1 |
| `journey` | a deployed artifact failing the real human path | needs a deployed URL; unfalsifiable here for 5 versions (TB-002) | 0 | 1 |

## What "count" means, precisely

One increment per **distinct project** where the failure this control would have caught actually
happened and was found by something else — a human, an incident, a customer. Two occurrences in the
same project count once. **The question is whether the failure mode is general, not whether one project
is unlucky.**

## The honest caveat

All three of these are *outward-facing* checks: they test the shipped thing against the real world
rather than the repo against itself, which is the direction this methodology is weakest in. Removing
them makes the remaining set more inward-looking, and that is a real cost, not a rounding error.
They were removed for being unprovable, not for being unimportant.
