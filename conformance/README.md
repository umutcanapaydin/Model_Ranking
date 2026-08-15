# Conformance fixtures (V4C-32)

`pass/` — the smallest records that MUST validate clean.
`fail/` — one fixture per blocking rule; each declares its expected diagnostic on an
`<!-- expect: RULE -->` line. `check_records.py --self-test` runs the whole corpus and FAILS if a
fail fixture does not produce its declared rule.

This is our own fault-injection doctrine (V3C-72: break it → confirm RED → revert) applied to the
validator itself. It exists because Increment 11 found that `make check-templates` — a ratified
gate — had never executed once: a control nobody exercises is a control nobody has.

Adding a blocking rule to `check_records.py` REQUIRES adding its fail fixture in the same change.

## Package-level and project-level rules are covered by PROBES, not by record fixtures (v4.3)

`P2`, `P3`, `D1`, `M3`, `C2a`, `C2b` and `C2c` cannot be expressed inside a single record, because they
are facts about a **package** or a **project tree**, not about one file's frontmatter. `--self-test`
builds a deliberately broken throwaway tree for each and asserts the rule fires.

**This distinction was learned the hard way, twice.** At v4.2 the Quality seat found `P2`/`P3` were
**structurally unreachable** from `--self-test` — the two rules the validator was most credited with
were never asserted, whatever the fixture count. At v4.3 the first attempt at covering `M3` and `C2a`
was a pair of marker files carrying `<!-- expect: M3 -->` and `<!-- expect: C2a -->` — **rules those
files could not possibly produce.** A fixture that declares an expectation it cannot meet is a false
claim in the test corpus, which is the exact class this whole conformance directory exists to catch.
Deleted; the probes are the coverage.

**The rule that follows:** a fail fixture may only declare a rule that a *single record* can trigger.
Everything else gets a probe, and the probe is asserted by name in the self-test output so it cannot
silently stop running.
