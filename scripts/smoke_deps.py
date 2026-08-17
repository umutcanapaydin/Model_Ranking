#!/usr/bin/env python3
"""Stage 4.3 / seed L.8 — invoke every external dependency THROUGH ITS OWN CLIENT.

**Why this is Python and not curl, and it is the whole point.** The first version of this gate was a
shell script with the endpoints typed into it. One of them said `main/` where the client says
`master/`, so the gate reported a 404 for a dependency that was working perfectly — it had probed a
URL nothing in this project calls. The docstring of that script said, in as many words, *"a smoke
test against a URL nobody calls proves the network works and nothing else"*, and then did exactly
that. Fourth instance in this milestone of the same lesson: **derive it, do not type it.**

So every probe here imports the real client, calls the real `fetch_raw()`, and hands the result to
the real parser. "Configured is not working" is checked by parsing, not by a status code: a 200
carrying HTML, an empty list, or a renamed field all fail here, and all of them pass a curl.

Exit 0 every dependency usable · 1 at least one is not.

NOT run in CI: `epoch.ai`, `huggingface.co` and `openrouter.ai` are proxy-403 from the agent
sandbox, and `contract-tests.yml` covers the halves that can run there. This is the owner's
deploy-gate command, run where all of them are reachable at once.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.workflows.sources import RemoteSource


def _probe(name: str, run: Callable[[], str]) -> bool:
    """Run one dependency end to end and report what its RESULT actually was."""
    try:
        detail = run()
    except Exception as exc:
        print(f"  FAIL  {name:<28} {type(exc).__name__}: {str(exc)[:90]}")
        if "-v" in sys.argv:
            traceback.print_exc()
        return False
    print(f"  ok    {name:<28} {detail}")
    return True


def _probe_for(source: RemoteSource) -> Callable[[], str]:
    """Build one probe from the registry entry rather than from a second hand-written list.

    **M7-W1 changed this and the reason is the whole point of the module.** These probes used to be
    a tuple of five functions typed out here, while `build.py` needed its own list of the same five
    dependencies. Two enumerations of one set, in two files, free to diverge — which is precisely
    the defect this file's own docstring was written about after the shell version probed a URL
    nothing in the project called. Both consumers now read `app.workflows.sources.REMOTE_SOURCES`,
    so a source cannot be added to the build and forgotten in the gate.

    The floor comes from the registry too: `minimum_rows` is what separates "the feed answered"
    from "the feed answered usefully", and a 200 carrying an empty list fails both here and in the
    build for the same declared reason.
    """

    def probe() -> str:
        rows, skipped = source.parse(source.client().fetch_raw())
        if len(rows) < source.minimum_rows:
            msg = (
                f"only {len(rows)} rows parsed, below the declared floor of "
                f"{source.minimum_rows} — the feed shape has changed"
            )
            raise ValueError(msg)
        return f"{len(rows)} rows, {skipped} skipped"

    return probe


# W-007 is why the arena probe matters beyond reachability: a 500 on the filter endpoint used to
# drop the client into full pagination and rate-limit itself. An unusable filter endpoint is a
# FAILED dependency even though the data exists behind the slower route.
#
# **Measured at the M6 deploy gate, and deliberately NOT retried:** 4 of 5 attempts returned 389
# rows in 5-10 s; one exceeded the client's 30 s read. That is this dependency's real behaviour,
# and a gate that retries until green reports a reliability the deploy will not have. If a probe is
# red, run it again and record BOTH results — the flake rate is the finding, not the failure.
#
# **Standing finding, W-024 (2026-08-17):** arena has been returning an upstream HTTP 500 across
# repeated runs, which is an outage rather than a flake.


def main() -> int:
    from app.workflows.sources import LOCAL_BUNDLES, REMOTE_SOURCES

    print("[smoke-deps] L.8 — every dependency invoked through its own client, RESULT parsed")
    results = [_probe(source.name, _probe_for(source)) for source in REMOTE_SOURCES]

    # Local bundles are deliberately NOT fetched, and the list of them is read from the registry
    # rather than typed here — a bundle added there is reported here without editing this file.
    for bundle in LOCAL_BUNDLES:
        print(f"  n/a   {bundle.name:<28} {bundle.reason}")

    print()
    if not all(results):
        failed = sum(1 for ok in results if not ok)
        print(f"[smoke-deps] FAIL — {failed} dependency/dependencies unusable. Stage 4.3 does not pass.")
        return 1
    print("[smoke-deps] PASS — every dependency answered and its own parser accepted the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
