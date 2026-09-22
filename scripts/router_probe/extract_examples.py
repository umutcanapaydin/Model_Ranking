"""Read the wording tier's example questions out of Router.swift, for `probe.swift`.

The probe must measure the SHIPPING examples, so it never keeps a copy of them: this reads
`CategoryHints.examples` and `CategoryHints.unmeasuredHints` from the Swift source and writes the
JSON that `probe.swift` takes. See `docs/reviews/m15-router-recalibration.md`.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROUTER = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking/Engine/Router.swift"


def extract(source: str) -> dict[str, object]:
    """Both example tables, as `probe.swift` expects them."""
    start = source.index("static let examples:")
    block = source[start : source.index("\n    ]\n", start)]
    examples = {
        match.group(1): re.findall(r'"([^"]*)"', match.group(2))
        for match in re.finditer(r'^\s*"([a-z_-]+)":\s*\[(.*?)\]', block, re.MULTILINE | re.DOTALL)
    }
    start = source.index("static let unmeasuredHints:")
    block = source[source.index("= [", start) + 3 : start + source[start:].index("\n    ]\n")]
    declines = [re.findall(r'"([^"]*)"', group) for group in re.findall(r"\[([^\]]*)\]", block)]
    return {"examples": examples, "declines": declines}


if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1])
    out.write_text(json.dumps(extract(ROUTER.read_text(encoding="utf-8")), indent=1), encoding="utf-8")
    print(f"wrote {out}")
