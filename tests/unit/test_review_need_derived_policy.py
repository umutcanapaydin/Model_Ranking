"""#319 (D-209 clause 5): review-need derives the policy scripts instead of keeping three by hand.

A change that touched only `scripts/wave_check.py` (it reads a plan's `security-globs:`), the Bash guard (it runs
the deploy gate), the Makefile's `review-need` recipe, or a plan's `security-globs:` line routed to `none` in light
mode. A script that names a policy reader or field is a policy script, read at both ends of the range; in the
Makefile and the plans only a changed line that names one is a policy edit, so an unrelated Makefile change is not.
"""

from __future__ import annotations

from pathlib import Path

from .test_review_need_base_policy import Repo, _brief


def _light(tmp_path: Path, name: str, files: dict[str, str]) -> Repo:
    repo = Repo(tmp_path / name, _brief("light"))
    for rel, text in files.items():
        repo.write(rel, text)
    repo.commit("base files")
    return repo


def test_a_script_that_reads_the_policy_is_a_policy_script(tmp_path: Path) -> None:
    for rel, text in (("scripts/wave_check.py", "GLOBS = 'security-globs:'\nx = 1\n"),
                      (".claude/hooks/bash_guard.py", "GATE = 'scripts/deploy_gate.py'\nx = 1\n")):
        repo = _light(tmp_path, Path(rel).stem, {rel: text})
        repo.write(rel, text.replace("x = 1", "x = 2"))
        repo.commit("chore: an unrelated line of a policy reader")
        _, last, out = repo.need()
        assert last == "review-need: security" and f"policy edit: {rel}" in out, (rel, out)


def test_a_makefile_line_that_names_a_policy_reader_is_a_policy_edit_and_another_is_not(tmp_path: Path) -> None:
    make = "review-need:\n\t@python3 scripts/review_need.py\n\nlint:\n\t@ruff check .\n"
    repo = _light(tmp_path, "make-recipe", {"Makefile": make})
    repo.write("Makefile", make.replace("scripts/review_need.py", "scripts/review_need.py --quiet"))
    repo.commit("chore: the recipe")
    _, last, out = repo.need()
    assert last == "review-need: security" and "policy edit: Makefile" in out, out
    repo = _light(tmp_path, "make-other", {"Makefile": make})
    repo.write("Makefile", make.replace("ruff check .", "ruff check src"))
    repo.commit("chore: lint")
    _, last, out = repo.need()
    assert "policy edit: Makefile" not in out, out


def test_a_plans_security_globs_line_is_a_policy_edit(tmp_path: Path) -> None:
    plan = "# M9\n\nsecurity-globs: src/auth/**\n\nOther text.\n"
    repo = _light(tmp_path, "plan", {"docs/plans/m9-plan.md": plan})
    repo.write("docs/plans/m9-plan.md", plan.replace("src/auth/**", "none"))
    repo.commit("docs: the plan")
    _, last, out = repo.need()
    assert last == "review-need: security" and "policy edit: docs/plans/m9-plan.md" in out, out
