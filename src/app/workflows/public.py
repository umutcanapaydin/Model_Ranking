"""M19-W5 (#88): the public artifact the hosted engine serves. Not yet derived (red)."""

from __future__ import annotations

import shutil
from pathlib import Path

LEFT_OUT: dict[str, str] = {}


def derive(source: Path, target: Path) -> dict[str, int]:
    """Not yet derived (red): a plain copy."""
    shutil.copyfile(source, target)
    return {}
