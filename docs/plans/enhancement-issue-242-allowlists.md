# Enhancement — #242: the compiled client gate refuses what is not allowed

**Goal.** `scripts/client_decl_gate.py`'s rules on sinks and served numbers stop listing what is refused and start listing what is allowed, so a compiling twin of a refused spelling no longer passes (#242; every review since M19-W2 planted one).

**Owner ruling.** D-214 clause 1: no loosening. Everything the gate refuses today stays refused, and the Security-Reviewer reviews the change.

## Scope

In: `scripts/client_decl_gate.py`, `scripts/client_decl_fixtures/`, `tests/unit/test_client_decl_gate.py`, `tests/unit/data/g2_fixture_ast.txt`, and gaps G-1, G-2, G-11, G-12 and G-13 in `docs/security-invariants.md`.

Out: the text pins, the four build configurations, the self-test and its dump format; the app's own code, except where a phase finds that a real call needs an allowlist entry, which then names its reason.

## Open decisions

None left: D-214 answers the one question (the allowlist model, with no loosening).

## Phases

Each phase: a red commit that plants its twins as `shape:` lines in the fixture, then the allowlist, with `make check` green.

0. **The no-loosening pin.** A test records the fixture's refusals today and fails if a later phase refuses fewer of them.
1. **Sinks.** Per sink file, one allowlist of the declarations the sink and the code it runs may reference (backlog-gates round 2, K1), checked for staleness.
2. **Served numbers.** What a served number may meet: comparison, display, the named rulings, and counts carried through a binding. Twins: `abs`, `max`, `.magnitude`, `Double(...).rounded`, a subscript, `Array(repeating:count:)`.
3. **The request surface** (INV-64, G-11): every argument read, labelled or not, and initialisers too.
4. **The by-name set** (G-12): matched by argument label.
5. **The stores' URLs** (G-13): admitted only from `FileManager` makers.
6. **The register.** G-1, G-2, G-11, G-12 and G-13 move from "refuses these listed forms" to the allowlist each now enforces.
