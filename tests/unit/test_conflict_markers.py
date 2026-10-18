"""#341: no tracked file carries a merge-conflict marker.

Run bug-night's merge of #333 left `<<<<<<<`, `=======` and `>>>>>>>` lines in `docs/decisions.md`; the commit
gate's `make check-fast` passed, and the records check read both sides as whole ADRs. A marker is a line that
starts a conflict side (`<<<<<<< ` or `>>>>>>> `) or is exactly the separator, outside a fenced code block in
Markdown. A Markdown heading's `===` underline and a fenced example are not markers.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
OPEN, SEP, CLOSE = "<" * 7 + " HEAD", "=" * 7, ">" * 7 + " branch"


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("conflict_markers", ROOT / "scripts" / "conflict_markers.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    return root


def test_a_conflicted_file_is_found_at_its_line(tmp_path: Path) -> None:
    text = f"# D\n\n{OPEN}\nours\n{SEP}\ntheirs\n{CLOSE}\n"
    found = _module().findings(_repo(tmp_path, {"docs/decisions.md": text, "a.py": f"x = 1\n{SEP}\n"}))
    assert ("docs/decisions.md", 3) in found and ("docs/decisions.md", 5) in found and ("docs/decisions.md", 7) in found
    assert ("a.py", 2) in found


def test_a_heading_underline_and_a_fenced_example_are_not_markers(tmp_path: Path) -> None:
    text = f"Title\n=====\n\n```text\n{OPEN}\n{SEP}\n{CLOSE}\n```\n\nA line that mentions {OPEN} inside.\n"
    assert _module().findings(_repo(tmp_path, {"docs/x.md": text})) == []


def test_no_tracked_file_in_this_repository_carries_a_marker() -> None:
    found = _module().findings(ROOT)
    assert found == [], found
