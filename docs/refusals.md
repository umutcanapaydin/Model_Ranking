# Refusals — decisions NOT to build

> **Purpose:** a refusal is a decision, and a decision that is not written down gets re-litigated
> every time the proposal comes back. Each row names what was refused, why, who ruled, and the
> trigger that re-opens it. **A refusal is not "not yet" — it is "no, until the trigger fires."**
> Do not re-open a row from prose: bring the trigger's evidence.

## When a row belongs here

- **A gate you will not wire.** `make smoke-deps`, `make cold-start` and `make journey` fail loudly
  until wired; refusing one is a legal answer, recorded here with the reason.
- **A repository you will not govern.** `docs/project-brief.md` §2.1 lists every repository that
  ships something a customer can reach; one that does not run DevFlow names its row id here, and
  `make bootstrap-check` refuses a `no` without one.
- **A control you retire.** When `make wave-check` reports the same control skipped or bypassed three
  times (`docs/control-events.csv`), fix it, re-scope it, or refuse it here. A retired control also
  gets a row in `docs/watchlist.md`, so it can come back on evidence.
- **A tool, service or practice you decided against**, so the next proposal starts from the reason.

## Format

`R-<n>`, monotonic, never reused. A refusal is reversed by a new row that names the old one, never by
editing it.

| id | Refused | Why (the failure mode or cost that decided it) | Ruled by (name, date) | Re-open trigger |
|---|---|---|---|---|
| — | — | — | — | *No refusal recorded yet. Delete this line when the first real row lands.* |
