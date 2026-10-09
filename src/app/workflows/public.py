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

#: Each source left out of the public artifact, with its reason. Empty since D-186: the owner ruled on
#: 2026-10-08 that the hosted engine serves every source while the app is on TestFlight, and that the
#: licences (D-185's table) are settled before it goes to production. The machinery stays, held by
#: its tests on planted sources, for that day.
LEFT_OUT: dict[str, str] = {}

#: The rows a source owns, each removed by one fixed statement; the sources go in as one JSON list.
_REMOVE = {
    "scores": "DELETE FROM scores WHERE source IN (SELECT value FROM json_each(?))",
    "pricing": "DELETE FROM pricing WHERE source IN (SELECT value FROM json_each(?))",
    # Each model's accessibility names its source as well (the W5 Tester's M3); a test holds that
    # every table with a `source` column is here.
    "access": "DELETE FROM access WHERE source IN (SELECT value FROM json_each(?))",
}
#: What else the public artifact does not carry: the vendor subscription plans, which `/v1` never
#: serves and one vendor's terms keep from public display (the M19-W5 review's M2).
_REMOVE_ALSO = {
    "plan_models": "DELETE FROM plan_models",
    "plans": "DELETE FROM plans",
}
#: The copies another source keeps of a left-out source's rows, removed only while it is left out:
#: what the removal is called, its statement, and the count the survivor check reads (#205).
_COPIES_OF = {
    "openrouter": ("openrouter_aliases", "DELETE FROM pricing WHERE source = 'litellm' AND alias LIKE 'openrouter/%'",
                   "SELECT count(*) FROM pricing WHERE source = 'litellm' AND alias LIKE 'openrouter/%'"),
}
_SURVIVORS = (
    "SELECT (SELECT count(*) FROM scores WHERE source IN (SELECT value FROM json_each(?)))"
    " + (SELECT count(*) FROM pricing WHERE source IN (SELECT value FROM json_each(?)))"
    " + (SELECT count(*) FROM access WHERE source IN (SELECT value FROM json_each(?)))"
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
                for left_out, (what, statement, _count) in _COPIES_OF.items():
                    removed[f"{what}_removed"] = conn.execute(statement).rowcount if left_out in LEFT_OUT else 0
                for what, statement in _REMOVE_ALSO.items():
                    removed[f"{what}_removed"] = conn.execute(statement).rowcount
            if build_price_medians(conn) <= 0:
                raise ValueError("no prices are left to rank by: the public artifact would answer nothing")
            left = conn.execute(_SURVIVORS, (sources, sources, sources)).fetchone()[0]
            # #205: a left-out source's copies under another source survive a missed delete too.
            left += sum(conn.execute(count).fetchone()[0] for source_name, (_what, _delete, count)
                        in _COPIES_OF.items() if source_name in LEFT_OUT)
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
