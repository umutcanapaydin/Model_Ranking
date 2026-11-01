"""The release delta Tester of `integration/fixes-1101` (2026-11-01): #525's "tolerating already booted".

#525: the harness boots the device before the uninstall, "tolerating 'already booted'". The range's tests start every
pass from a device xcodebuild shut down, so fault F-S3 (`simctl bootstatus -b` replaced by `simctl boot`, which fails
with 149 on a booted device) stayed green. A simulator the owner booted before the run stays booted after a pass
(xcodebuild shuts down only a device it booted), and the run must still remove the app and go on.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_ui_test_script import _harness, _run

#: xcodebuild passes and leaves the device as it found it: booted before the run, booted after.
XCODEBUILD_KEEPS_STATE = r"""#!/bin/sh
echo "xcodebuild $1 $*" >> "$UI_STUB_LOG"
exit 0
"""


# covers #525
@pytest.mark.needs("bash_curl")
def test_a_simulator_booted_before_the_run_is_tolerated_and_the_app_still_removed(tmp_path: Path) -> None:
    env, log = _harness(tmp_path)
    Path(env["UI_STUB_STATE"]).write_text("Booted\n", encoding="utf-8")
    stub = Path(env["PATH"].split(":")[0]) / "xcodebuild"
    stub.write_text(XCODEBUILD_KEEPS_STATE, encoding="utf-8")
    done = _run(tmp_path, env)
    calls = log.read_text(encoding="utf-8").splitlines()
    assert done.returncode == 0, done.stdout + done.stderr + "\n".join(calls)
    removed = [i for i, call in enumerate(calls) if call == "removed com.ilgar.modelranking"]
    offline = [i for i, call in enumerate(calls) if "-only-testing:ModelRankingUITests/FailureScreenTests" in call]
    assert removed and offline and removed[-1] < offline[0], calls
