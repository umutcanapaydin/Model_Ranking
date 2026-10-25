# Assumptions — run v020

Questions the run met that are reversible, local to one issue and outside a ⛔ zone, each with the most conservative answer it took. The owner reads them in the morning; each is undone by a commit.

| When | Issue | Question | Answer taken |
|---|---|---|---|
| 2026-10-24 | #396 | D-223 clause 8 refuses a served number cast back to a number from an existential (`h as? Int`). The shipping client reads the engine's facts, `[String: Any]`, by `as? Double` (`tradeOffSentence`, `anchoredFact`): refuse a cast out of `Any` too, or only out of `any` of a protocol? | Only out of `any` of a protocol, the shape the ruling names (`EXISTENTIAL` in `_cast_back`); a cast out of `Any` or `AnyObject` stays refused only when arithmetic follows (#171), and G-2 names it. Undone by widening `EXISTENTIAL`. |
| 2026-10-24 | #396 | The ruling and the integration review's R1 name `map { ... }.reduce(0, +)` and a closure handed to a parameter of the app's own: how far does each reach? | As far as #371's method list and no further: the closure of a `map` or `flatMap` whose result any method that counts or searches reads directly (`reduce`, `filter`, `count(where:)`, ...), and a parameter that reaches one by name, called inside the closure given to one, or through a parameter of another function of the app's own. A `map` read through a sort or `max()` first, and a predicate held in a member, stay not held, and G-2 names them. Undone by narrowing `MAPS_BEFORE` and `_handed_on`. |
