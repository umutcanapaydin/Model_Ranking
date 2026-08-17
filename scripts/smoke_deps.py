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


def _probe(name: str, run: Callable[[], str]) -> bool:
    """Run one dependency end to end and report what its RESULT actually was."""
    try:
        detail = run()
    except Exception as exc:  # noqa: BLE001 - a smoke gate reports every failure shape
        print(f"  FAIL  {name:<28} {type(exc).__name__}: {str(exc)[:90]}")
        if "-v" in sys.argv:
            traceback.print_exc()
        return False
    print(f"  ok    {name:<28} {detail}")
    return True


def _litellm() -> str:
    from app.clients.litellm import LiteLLMClient, parse_pricing

    rows, skipped = parse_pricing(LiteLLMClient().fetch_raw())
    if len(rows) < 100:
        msg = f"only {len(rows)} priced rows parsed — the feed shape has changed"
        raise ValueError(msg)
    return f"{len(rows)} priced rows, {skipped} skipped"


def _swebench() -> str:
    from app.clients.swebench import SweBenchClient, parse_verified

    rows, skipped = parse_verified(SweBenchClient().fetch_raw())
    if not rows:
        msg = "the Verified leaderboard parsed to zero rows"
        raise ValueError(msg)
    return f"{len(rows)} Verified rows, {skipped} skipped"


def _aider() -> str:
    from app.clients.aider import AiderClient, parse_polyglot

    rows, skipped = parse_polyglot(AiderClient().fetch_raw())
    if not rows:
        msg = "the polyglot leaderboard parsed to zero rows"
        raise ValueError(msg)
    return f"{len(rows)} rows, {skipped} skipped"


def _openrouter() -> str:
    from app.clients.openrouter import OpenRouterClient, parse_models

    rows, skipped = parse_models(OpenRouterClient().fetch_raw())
    if len(rows) < 50:
        msg = f"only {len(rows)} models in the catalogue — the feed shape has changed"
        raise ValueError(msg)
    return f"{len(rows)} models, {skipped} skipped"


def _arena() -> str:
    from app.clients.arena import ArenaClient, parse_arena

    rows, skipped = parse_arena(ArenaClient().fetch_raw())
    if not rows:
        msg = "the Arena filter endpoint parsed to zero rows"
        raise ValueError(msg)
    # W-007 is the reason this probe matters beyond reachability: a 500 on the filter endpoint used
    # to drop the client into full pagination and rate-limit itself. An unusable filter endpoint is
    # a FAILED dependency even though the data exists behind the slower route.
    #
    # **Measured at the M6 deploy gate, and deliberately NOT retried here:** 4 of 5 attempts
    # returned 389 rows in 5-10 s; one exceeded the client's 30 s read. That is this dependency's
    # real behaviour, and a gate that retries until green reports a reliability the deploy will not
    # have. If this probe is red, run it again and record BOTH results — the flake rate is the
    # finding, not the failure.
    return f"{len(rows)} rows via the filter endpoint, {skipped} skipped"


PROBES: tuple[tuple[str, Callable[[], str]], ...] = (
    ("litellm pricing", _litellm),
    ("openrouter catalogue", _openrouter),
    ("swebench Verified", _swebench),
    ("aider polyglot", _aider),
    ("arena via HF filter", _arena),
)


def main() -> int:
    print("[smoke-deps] L.8 — every dependency invoked through its own client, RESULT parsed")
    results = [_probe(name, run) for name, run in PROBES]

    # Epoch is deliberately NOT fetched: D-101 and the M5 data-boundary invariant make it an
    # owner-fetched local bundle, and a runtime fetch would be the violation, not the check.
    print("  n/a   epoch bundle                 local artifact by design (D-101); not fetched")

    print()
    if not all(results):
        failed = sum(1 for ok in results if not ok)
        print(f"[smoke-deps] FAIL — {failed} dependency/dependencies unusable. Stage 4.3 does not pass.")
        return 1
    print("[smoke-deps] PASS — every dependency answered and its own parser accepted the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
