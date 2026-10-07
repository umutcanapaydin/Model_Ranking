"""M19-W5 (#88): the public artifact the hosted engine serves.

The artifact built on the owner's Mac carries every source the engine reads, under W-129's ruling:
kept and recorded until a commercial launch. A hosted engine and a TestFlight build show that data
to people beyond the owner, and App Review asks that an app showing a third party's content be
permitted to (guideline 5.2.2). So the hosted engine serves a copy with each source whose terms do
not clearly permit a public app left out. The licence review of 2026-10-07 names them; the ADR this
wave adds holds the table.

The copy is derived, never rebuilt: the build fetches its sources from the network, and this runs
offline on the owner's Mac, from the artifact the engine already serves. A surface whose only
source is left out answers that it has no evidence, by the path an unavailable source already
takes (D-121).
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

from app.workflows.rank import build_price_medians
from app.workflows.schema import open_readonly

#: Each source left out of the public artifact, with the reason the licence review gave.
LEFT_OUT: dict[str, str] = {
    "swebench": "the SWE-bench leaderboard is CC BY-NC 4.0: not for a paid app, unclear for a free one",
    "epoch_arc_agi": "ARC Prize's terms grant personal or internal use only, and forbid a database of "
    "its data without written permission",
    "epoch_deepswe_external": "Datacurve publishes no licence for the DeepSWE board",
    "epoch_terminalbench": "the Terminal-Bench leaderboard states no licence",
    "epoch_webdev": "Epoch's copy cites arena.ai, whose terms permit personal or internal business use",
    "epoch_mmlu": "the MMLU scores (HELM Lite and model reports) carry no licence found",
    "openrouter": "OpenRouter's terms forbid use of its data except as it expressly authorises",
}

#: The rows a source owns, each removed by one fixed statement; the sources go in as one JSON list.
_REMOVE = {
    "scores": "DELETE FROM scores WHERE source IN (SELECT value FROM json_each(?))",
    "pricing": "DELETE FROM pricing WHERE source IN (SELECT value FROM json_each(?))",
}
#: What else the public artifact does not carry (the M19-W5 review): LiteLLM's own copies of
#: OpenRouter's prices, under `openrouter/` aliases (MJ1), and the vendor subscription plans, which
#: `/v1` never serves and one vendor's terms keep from public display (M2).
_REMOVE_ALSO = {
    "openrouter_aliases": "DELETE FROM pricing WHERE source = 'litellm' AND alias LIKE 'openrouter/%'",
    "plan_models": "DELETE FROM plan_models",
    "plans": "DELETE FROM plans",
}
_SURVIVORS = (
    "SELECT (SELECT count(*) FROM scores WHERE source IN (SELECT value FROM json_each(?)))"
    " + (SELECT count(*) FROM pricing WHERE source IN (SELECT value FROM json_each(?)))"
)


def derive(source: Path, target: Path) -> dict[str, int]:
    """Write `target`: a copy of `source` with every row of a `LEFT_OUT` source removed and the
    price medians rebuilt from the prices kept. `source` is never written. Returns the rows removed
    per table. The copy is made in a temporary file beside `target` and moved into place only once
    it is complete, so a failure leaves no half-derived artifact to deploy."""
    if source.resolve() == target.resolve():
        raise ValueError("the public artifact is derived beside the built one, never over it")
    handle, raw = tempfile.mkstemp(prefix=f"{target.name}.", suffix=".deriving", dir=target.parent)
    os.close(handle)
    workspace = Path(raw)
    try:
        conn = sqlite3.connect(workspace)
        try:
            built = open_readonly(source)
            try:
                built.backup(conn)
            finally:
                built.close()
            removed = {}
            sources = json.dumps(sorted(LEFT_OUT))
            with conn:
                for table, statement in _REMOVE.items():
                    removed[f"{table}_removed"] = conn.execute(statement, (sources,)).rowcount
                for what, statement in _REMOVE_ALSO.items():
                    removed[f"{what}_removed"] = conn.execute(statement).rowcount
            if build_price_medians(conn) <= 0:
                raise ValueError("no prices are left to rank by: the public artifact would answer nothing")
            left = conn.execute(_SURVIVORS, (sources, sources)).fetchone()[0]
            if left:
                raise ValueError(f"{left} rows of a left-out source survived the derivation")
            # Out of WAL, whatever the built artifact journals: a WAL file cannot be opened read-only in
            # a folder the engine cannot write, as `/srv` in the image is not (the review's R3). The
            # VACUUM drops the deleted rows' pages from the file (its M2).
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("VACUUM")
        finally:
            conn.close()
        # The image's engine runs as a non-root user and the file is copied in owned by root, so it
        # must be readable by all; a temporary file is created readable by its owner only.
        workspace.chmod(0o644)
        workspace.replace(target)
    except BaseException:
        workspace.unlink(missing_ok=True)
        raise
    return removed


def main(argv: list[str] | None = None) -> int:
    """`python -m app.workflows.public --from SERVED --to TARGET`: what the deploy script runs."""
    import argparse

    parser = argparse.ArgumentParser(prog="public", description="Derive the public artifact (#88).")
    parser.add_argument("--from", dest="source", required=True, help="the built artifact, only read")
    parser.add_argument("--to", dest="target", required=True, help="the public copy to write")
    args = parser.parse_args(argv)
    removed = derive(Path(args.source), Path(args.target))
    print(json.dumps({"public": args.target, **removed, "left_out": sorted(LEFT_OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
