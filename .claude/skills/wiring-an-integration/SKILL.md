---
name: wiring-an-integration
description: Use when connecting this codebase to anything it does not own — an external API, a model provider, a gateway, a queue, a database, a cache, a webhook, an auth provider, a payment processor, another team's service. Also when writing or changing a mock, stub, fake client or test double for such a thing, and when a dependency "is configured" and you are about to call it done.
---

Four rules. All four come from integrations that passed every local check and failed the moment
they met the real thing.

## 1 · One canonical mock per integration, built BEFORE the integration code

Not one per test. One per integration, in a shared place, Protocol-typed. Bespoke per-test stubs
are how two tests end up disagreeing about what the upstream does, and neither is right.

## 2 · A contract test against the REAL API

The mock proves your code is internally consistent. Only a contract test proves the mock is
still true. Run it on a schedule or at closure, never only at authoring time — the upstream
changes without telling you.

Measured in four projects: code that passed green mocks and failed live. One of them, the wrapped
engine rejected passwords over twenty characters and the mock did not.

## 3 · Present in a catalog is not serving requests

A dependency listed in a provider registry, a config UI, or a values file — with credentials
accepted — does **not** mean it answers. Before calling an integration done, invoke it once for
real and inspect the RESULT, not the configuration screen.

The field case: a model was "listed but Invalid", and an AppCode set under `configMap.data` that
the pod saw as `{}`. Configured ≠ working, in both directions.

## 4 · Read the config back from inside the process

Between "I set it in the values file" and "the process sees it" sits an injection layer that can
drop a key in silence. Read each critical value back from inside the running process — a safe
echo of SET/EMPTY and length, never the value itself.

## Before you finish

- Does the upstream's error shape reach your caller intact, or does a 200 with `{"success": false}`
  get forwarded as success?
- If it fails, does it fail in the direction the control class demands — auth and safety CLOSED,
  fairness and rate limits OPEN?
- Is there exactly one place that knows this integration's endpoints, or two that must agree?
