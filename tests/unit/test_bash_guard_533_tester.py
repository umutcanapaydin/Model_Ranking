"""The release delta Tester of `integration/fixes-1101` (2026-11-01): #533 (D-236) in any case.

`_lands` reads a refspec's or a ref's destination "in any case" (its docstring): on the owner's case-insensitive
disk `refs/remotes/ORIGIN/x` is the loose file `refs/remotes/origin/x`, a ref under origin's, which D-236 lets only
a plain fetch or pull of origin move. Fault F-G5 (the `casefold()` dropped from `_lands`) stayed green on every
guard test: the range's cases spell the remote's refs in lower case, and the upper-case ones (`git branch -D MAIN`,
`git remote add ORIGIN`) reach other rules. Each command below was allowed under F-G5 and is refused at `eaee56b`.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from .test_bash_guard_bounds import _bash, guard, repo, ungoverned  # noqa: F401 -- the fixtures


# covers D-236 clause 1, #533
@pytest.mark.parametrize("command", [
    "git update-ref refs/remotes/ORIGIN/feature HEAD",
    "git symbolic-ref refs/remotes/ORIGIN/x refs/heads/y",
    "git fetch evil +refs/heads/x:refs/remotes/Origin/feature",
    "git fetch evil +refs/heads/x:REFS/remotes/origin/feature",
    "git push . HEAD:refs/remotes/ORIGIN/feature",
])
def test_a_ref_under_origins_written_in_another_case_moves_only_by_a_fetch_of_origin(
        guard: ModuleType, repo: Path, command: str) -> None:  # noqa: F811
    why = _bash(guard, command, repo)
    assert why and "#533" in why, (command, why)


# covers D-236 clause 1, #533 -- the control: the same shapes on a ref of the agent's own stay allowed
@pytest.mark.parametrize("command", [
    "git update-ref refs/heads/fix/ORIGIN HEAD",
    "git push origin HEAD:fix/Origin-notes",
])
def test_the_same_shape_on_the_agents_own_ref_stays_allowed(guard: ModuleType, repo: Path,  # noqa: F811
                                                           command: str) -> None:
    assert _bash(guard, command, repo) is None, command
