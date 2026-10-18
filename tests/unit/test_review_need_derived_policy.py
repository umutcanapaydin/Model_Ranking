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


# --- the #319 security review (docs/reviews/fix-issue-319-security.md): M1-M4 ---------------------------------

def _routes(repo: Repo, path: str) -> None:
    _, last, out = repo.need()
    assert last == "review-need: security" and f"policy edit: {path}" in out, (path, out)


def test_a_reader_is_read_at_both_ends_of_the_range(tmp_path: Path) -> None:
    """M2: a new script that names a policy reader (read at the end), and one whose last mention the change
    removes (read at the base)."""
    repo = _light(tmp_path, "added", {"src/a.py": "x = 1\n"})
    repo.write("scripts/new_gate.py", "GATE = 'scripts/deploy_gate.py'\n")
    repo.commit("feat: a new reader")
    _routes(repo, "scripts/new_gate.py")
    repo = _light(tmp_path, "removed", {"scripts/old_gate.py": "GATE = 'scripts/deploy_gate.py'\n"})
    repo.write("scripts/old_gate.py", "GATE = None\n")
    repo.commit("chore: the mention goes")
    _routes(repo, "scripts/old_gate.py")


def test_a_hook_a_field_label_a_removed_line_and_a_non_ascii_name_count(tmp_path: Path) -> None:
    """M2 and M3: `.githooks/`, a policy field's label, a Makefile line the change removes, and a reader whose
    path git would quote."""
    for name, rel, text, change in (
            ("hook", ".githooks/pre-push", "make review-need\nx=1\n", ("x=1", "x=2")),
            ("label", "scripts/reads_brief.py", "LABEL = 'Deploy commands'\nx = 1\n", ("x = 1", "x = 2")),
            ("accent", "scripts/café.py", "GATE = 'deploy_gate'\nx = 1\n", ("x = 1", "x = 2")),
            ("removed", "Makefile", "review-need:\n\t@python3 scripts/review_need.py\n\nlint:\n\t@true\n",
             ("review-need:\n\t@python3 scripts/review_need.py\n\n", ""))):
        repo = _light(tmp_path, name, {rel: text})
        repo.write(rel, text.replace(*change))
        repo.commit(f"chore: {name}")
        _routes(repo, rel)


def test_an_attribute_that_hides_the_diff_hides_no_policy_line(tmp_path: Path) -> None:
    """M1: a `.gitattributes` line `Makefile -diff` in the change made the recipe edit a binary diff."""
    make = "review-need:\n\t@python3 scripts/review_need.py\n"
    repo = _light(tmp_path, "attr", {"Makefile": make})
    repo.write(".gitattributes", "Makefile -diff\n")
    repo.write("Makefile", make.replace("review_need.py", "review_need.py --quiet"))
    repo.commit("chore: attributes")
    _routes(repo, "Makefile")


def test_a_reader_outside_scripts_counts(tmp_path: Path) -> None:
    """M4: the scanned places are the gate code's, so a conformance test of the policy counts too."""
    rel = "conformance/test-policy.py"
    repo = _light(tmp_path, "conf", {rel: "SCRIPT = 'scripts/review_need.py'\nx = 1\n"})
    repo.write(rel, "SCRIPT = 'scripts/review_need.py'\nx = 2\n")
    repo.commit("chore: the conformance test")
    _routes(repo, rel)


def test_a_commit_git_cannot_search_is_cannot_run(tmp_path: Path) -> None:
    """M2: a failed search fails closed."""
    import importlib.util
    import os

    import pytest

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("review_need_319", root / "scripts" / "review_need.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    repo = _light(tmp_path, "nosearch", {"src/a.py": "x = 1\n"})
    here = Path.cwd()
    os.chdir(repo.root)
    try:
        with pytest.raises(RuntimeError, match="cannot search"):
            module.policy_readers(("0" * 40,))
    finally:
        os.chdir(here)
