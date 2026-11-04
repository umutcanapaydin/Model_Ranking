"""#572 (the #562 security review's R1): a dependency waiver written outside `.deps-accept` routed to no review.

In light mode, `--ignore-vuln` added to the Makefile's `deps:` recipe, or a change to `scripts/deps_accept.py` (the
reader that turns `.deps-accept` into those flags), named no word `review_need` treats as policy, so the change went to
no reviewer; D-244 makes a waiver a policy edit, a security review in either mode.
# covers #572, D-244
"""

from __future__ import annotations

from pathlib import Path

from .test_review_need_base_policy import Repo, _brief

DEPS = "deps:\n\t$(PY) -m pip_audit --strict --disable-pip $$acc $(addprefix -r ,$(LOCKS))\n"


def test_572_an_ignore_vuln_flag_in_the_deps_recipe_is_a_policy_edit(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light"))
    repo.write("Makefile", DEPS)
    repo.commit("the deps recipe")
    repo.write("Makefile", DEPS.replace("--strict", "--strict --ignore-vuln GHSA-xxxx-xxxx-xxxx"))
    repo.commit("waive an advisory in the recipe")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: security"), out


def test_572_a_change_to_the_waiver_reader_is_a_policy_edit(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light"))
    repo.write("scripts/deps_accept.py", "def flags():\n    return []\n")
    repo.commit("the waiver reader")
    repo.write("scripts/deps_accept.py", "def flags():\n    return ['--ignore-vuln', 'GHSA-xxxx-xxxx-xxxx']\n")
    repo.commit("the reader waives one itself")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: security"), out


def test_572_an_unrelated_makefile_line_stays_unrouted(tmp_path: Path) -> None:
    """The control: only a line naming the waiver is policy, not every Makefile change."""
    repo = Repo(tmp_path, _brief("light"))
    repo.write("Makefile", DEPS)
    repo.commit("the deps recipe")
    repo.write("Makefile", DEPS + "\nhello:\n\techo hi\n")
    repo.commit("an unrelated target")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: none"), out
