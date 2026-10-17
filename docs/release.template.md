# Release <version> — <YYYY-MM-DD>

<!-- Copy to `docs/releases/<version>.md` at the end of `/going-live`, on the `release/<version>` branch,
     beside the release verdicts. It is what a person -- the customer, a teammate, the owner a month
     later -- reads to learn what this build is. The owner tags the release and publishes it from this
     file (`docs/owner-actions.md` carries the command). Written for people: behaviour, not commits. -->

**Build:** `<the tag or git SHA that /health reports>` · **Target:** `<environment>`

## What changed

<!-- One bullet per behaviour a person can notice, with its issue. -->
- <what a user can now do, or no longer meets> (#<issue>)

## Database

<none | each migration, and how it runs -- automatically at boot, or by a named command>

## Dependencies

<none | each pin that changed, from -> to, and why>

## Verdicts

- Security: `docs/reviews/<release-security.md | m<N>-security.md>`, reviewed head `<sha>`
- Tester: `docs/reviews/<release-tester.md | m<N>-tester.md>`, reviewed head `<sha>`
- `make deploy-check`: <the two lines it printed>

## Rollback

`<the brief's Rollback command, or "none: <why>">` -- and what a rollback leaves behind (a migration
that does not reverse, a cache to clear).
