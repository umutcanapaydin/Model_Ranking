"""D-233 (#517's review M2), the release Tester, delta round 2026-10-31b: "A base with no pin, or a pin that does not
read, exempts nothing."

`devflow_pins` returns None unless EVERY protected base holds a pin that reads (`all(found)`). Weakened to `any`, the
base that has a pin was read alone and the exemption held: the fault stayed green on every deploy-gate test, since
each fixture pins at both bases or at neither. Here the merge-base holds the upgrade's pin and the default branch's
tip has lost it, or garbled it, after the branch was cut.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_pin import Repo, _installed


def _tip_pin(repo: Repo, text: str | None) -> None:
    """On main, after `after-upgrade` was cut: the pin removed (None) or rewritten as `text`."""
    repo.git("checkout", "-q", "main")
    pin = repo.root / "docs" / "devflow-pin.txt"
    if text is None:
        pin.unlink()
    else:
        pin.write_text(text, encoding="utf-8")
    repo.commit("the tip's pin changes")
    repo.git("checkout", "-q", "after-upgrade")


@pytest.mark.parametrize("tip", [None, "v9.10 not-a-commit\n", ""], ids=["no-pin", "a-pin-that-does-not-read", "empty"])
def test_a_tooling_file_is_not_exempt_when_the_tips_pin_does_not_read(tmp_path: Path, tip: str | None) -> None:
    """# covers D-233, #517: red with `all(found)` in `devflow_pins` weakened to `any(found)`."""
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2  # DevFlow's fix\n")
    code, out = repo.check()
    assert code == 0, f"the control: both bases pin the upgrade, so its file is DevFlow's\n{out}"
    _tip_pin(repo, tip)
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_tooling_file_is_not_exempt_when_the_merge_bases_pin_does_not_read(tmp_path: Path) -> None:
    """# covers D-233, #517: the other side -- a branch cut from a main commit whose pin is garbled, main's tip pinning
    the upgrade. The tip's pin alone exempts nothing either."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    (repo.root / "docs" / "devflow-pin.txt").write_text("v9.9 garbled\n", encoding="utf-8")
    repo.commit("a garbled pin")
    repo.git("checkout", "-q", "-b", "cut", "main")
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2  # DevFlow's fix\n")
    upgraded = repo.git("rev-parse", "main")
    repo.git("checkout", "-q", "cut")
    repo.git("checkout", "-q", upgraded, "--", "scripts/tool.py")
    repo.commit("the upgrade's bytes on the older history")
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out
