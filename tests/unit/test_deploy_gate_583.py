"""#583 (D-245): what the #551 security review found D-242's reader missing, closed by refusing rather than reading.

- Clause 1: a dispatched deploy workflow that runs `make` refuses, whatever its Makefile says -- the Makefile reader
  missed conditionals, implicit rules, `$(shell ...)`, environment overrides, `MAKEFLAGS` (M1-M5), refused this
  repository's own targets anyway (R1), and expanded exponentially (R2).
- Clause 2: a program read from standard input by a path, `sudo -s`/`-i`, `busybox <shell>` (M6).
- Clause 3: an interpreter's code option after a valued option it does not know (M6).
- Clause 4: a runner's option value holding an expansion; a runner started as a Python module (M7).
- Clause 5: the runners outside D-242's list (R3).
# covers #583, D-245
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_522 import STEP
from .test_deploy_gate_549 import _deploy
from .test_deploy_gate_551 import _planted

NAMED = {"Makefile": ".PHONY: ship\nship:\n\tbash scripts/ship_it.sh\n"}

REFUSED: dict[str, tuple[str, dict[str, str]]] = {
    "make-named-recipe": ("      - run: make ship\n", NAMED),
    "gmake-named-recipe": ("      - run: gmake ship\n", NAMED),
    "make-version": ("      - run: make --version\n", {}),
    "make-wrapped": ("      - run: env -i make ship\n", NAMED),
    "stdin-path": ("      - run: curl -s \"$URL\" | bash /dev/stdin\n", {}),
    "stdin-fd": ("      - run: bash /dev/fd/0\n", {}),
    "stdin-proc": ("      - run: sh /proc/self/fd/0\n", {}),
    "sudo-shell": ("      - run: sudo -s\n", {}),
    "sudo-login": ("      - run: sudo -i\n", {}),
    "busybox-shell": ("      - run: busybox sh\n", {}),
    "python-code-after-valued": ("      - run: python --check-hash-based-pycs always -c 'print(1)'\n", {}),
    "node-code-after-valued": ("      - run: node --input-type module -e 'x'\n", {}),
    "php-code-after-valued": ("      - run: php -d x=1 -r 'x'\n", {}),
    "npx-package-variable": ("      - run: npx -p \"$PKG\" cowsay hi\n", {}),
    "uvx-from-variable": ("      - run: uvx --from \"$X\" ship\n", {}),
    "python-m-uv": ("      - run: python -m uv run scripts/ship_it.py\n", {}),
    "pipx-run": ("      - run: pipx run ship\n", {}),
    "npm-exec": ("      - run: npm exec ship\n", {}),
    "pnpm-dlx": ("      - run: pnpm dlx ship\n", {}),
    "yarn-dlx": ("      - run: yarn dlx ship\n", {}),
    "bunx": ("      - run: bunx ship\n", {}),
    "hatch-run": ("      - run: hatch run ship\n", {}),
    "pdm-run": ("      - run: pdm run ship\n", {}),
    "tox": ("      - run: tox\n", {}),
    "nox": ("      - run: nox\n", {}),
}


@pytest.mark.parametrize(("step", "files"), list(REFUSED.values()), ids=list(REFUSED))
def test_583_each_unread_start_refuses_the_deploy(tmp_path: Path, step: str, files: dict[str, str]) -> None:
    code, out = _deploy(_planted(tmp_path, STEP.format(step), files))
    assert code == 2 and "release.yml" in out, out


QUIET = {
    "named-script": "      - run: bash scripts/ship_it.sh\n",
    "uv-run-named": "      - run: uv run scripts/ship_it.py\n",
    "npm-ci": "      - run: npm ci\n",
    "python-module-pip": "      - run: python -m pip install x\n",
}


@pytest.mark.parametrize("step", list(QUIET.values()), ids=list(QUIET))
def test_583_the_control_what_names_its_file_still_passes(tmp_path: Path, step: str) -> None:
    code, out = _deploy(_planted(tmp_path, STEP.format(step), {}))
    assert code == 0, out
