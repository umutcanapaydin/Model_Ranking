"""#283: `scripts/review_need.py` reads the brief's policy fields at the range's base, not from the change.

AGENTS.md section 5 (base-pinned policy): a rule a gate consumes is read from the protected base, never from the
change under evaluation. The script read `Working mode:` and `Paths that make a change HIGH:` from the tree under
evaluation, so a change could lower the reviews it owes itself: setting `light` dropped the Code-Reviewer (the
v7.1 upgrade security review's M2), and since v7.1.2 deleting a `Working mode: light` line routed a change to
`none` (the v7.1.2 upgrade security review's M2). Now the brief is read at the merge-base of the range, a range
that edits a policy field or a policy script routes to `security` (light) or `code-reviewer+security` (heavy),
and a base git cannot read is CANNOT RUN (exit 2), never the defaults.

Each case is a throwaway repository: the base commit holds a brief, the range under evaluation holds the change.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "review_need.py"
BIG = "".join(f"v{i} = {i}\n" for i in range(200))


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _brief(mode: str | None = "heavy", high: str = "none", deploy: str = "none", extra: str = "") -> str:
    lines = ["---", "record_type: brief", "id: project-brief", "status: draft", "---"]
    if mode is not None:
        lines.append(f"- **Working mode:** `{mode}`")
    lines += [f"- **Paths that make a change HIGH:** `{high}`", f"- **Deploy commands:** `{deploy}`"]
    return "\n".join(lines) + "\n" + extra


class Repo:
    def __init__(self, root: Path, brief: str) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q", "-b", "main")
        self.write("docs/project-brief.md", brief)
        self.write("src/seed.py", "seed = 1\n")
        self.commit("base")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false",
                               *args], cwd=self.root, capture_output=True, text=True, check=True, env=_env(),
                              timeout=60).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def need(self, *args: str) -> tuple[int, str, str]:
        done = subprocess.run([sys.executable, str(SCRIPT), *(args or ("--range", "HEAD~1..HEAD"))], cwd=self.root,
                              capture_output=True, text=True, check=False, env=_env(), timeout=60)
        out = done.stdout + done.stderr
        return done.returncode, (out.strip().splitlines() or [""])[-1], out


def test_setting_light_inside_the_range_keeps_the_code_reviewer_and_security(tmp_path: Path) -> None:
    """The issue's `Done when`: a heavy project, a range that sets `Working mode: light` beside 200 product
    lines. Read from the change, it was light mode's `none`; read at the base it is heavy, and a policy edit."""
    repo = Repo(tmp_path, _brief("heavy"))
    repo.write("docs/project-brief.md", _brief("light"))
    repo.write("src/a.py", BIG)
    repo.commit("feat: a, and light mode")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: code-reviewer+security"), out
    assert "working mode: heavy" in out and "the range's merge-base" in out
    assert "policy edit: the brief's `Working mode:` (heavy -> light)" in out


def test_deleting_the_light_line_does_not_route_a_change_to_none(tmp_path: Path) -> None:
    """The v7.1.2 upgrade security review's M2, as measured: light, the mode line deleted, a HIGH-path edit."""
    repo = Repo(tmp_path, _brief("light", high="src/**"))
    repo.write("docs/project-brief.md", _brief(None, high="src/**"))
    repo.write("src/auth.py", "x = 1\n")
    repo.commit("fix: auth, and no mode line")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: security"), out
    assert "working mode: light" in out and "(light -> unset)" in out


def test_a_policy_edit_alone_needs_security_in_light_mode(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light", high="src/**"))
    repo.write("docs/project-brief.md", _brief("light", high="none"))
    repo.commit("docs: no HIGH paths")
    code, last, out = repo.need()
    assert (code, last) == (0, "review-need: security"), out
    assert "`Paths that make a change HIGH:` (src/** -> none)" in out


def test_emptying_the_high_globs_inside_the_range_does_not_hide_a_high_path(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light", high="src/**"))
    repo.write("docs/project-brief.md", _brief("light", high="none"))
    repo.write("src/core.py", "x = 1\n")
    repo.commit("feat: core, and no HIGH paths")
    _, last, out = repo.need()
    assert last == "review-need: security" and "declared HIGH paths: src/core.py" in out, out


def test_a_deploy_command_edit_is_a_policy_edit(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("heavy", deploy="fly deploy"))
    repo.write("docs/project-brief.md", _brief("heavy", deploy="none"))
    repo.commit("docs: no deploys")
    _, last, out = repo.need()
    assert last == "review-need: code-reviewer+security", out
    assert "`Deploy commands:` (fly deploy -> none)" in out


def test_each_policy_script_is_a_policy_edit_in_either_mode(tmp_path: Path) -> None:
    for mode, want in (("light", "review-need: security"), ("heavy", "review-need: code-reviewer+security")):
        for script in ("scripts/review_need.py", "scripts/deploy_gate.py", "scripts/brief_fields.py"):
            repo = Repo(tmp_path / f"{mode}-{Path(script).stem}", _brief(mode))
            repo.write(script, "x = 1\n")
            repo.commit("chore: the script")
            _, last, out = repo.need()
            assert last == want, (mode, script, out)
            assert f"policy edit: {script}" in out, out


def test_a_brief_edit_that_leaves_the_policy_fields_is_not_a_policy_edit(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light"))
    repo.write("docs/project-brief.md", _brief("light", extra="- **Customer:** someone else\n"))
    repo.write("src/a.py", "a = 1\n")
    repo.commit("docs: the customer")
    _, last, out = repo.need()
    assert last == "review-need: none" and "policy edit" not in out, out


def test_an_uncommitted_brief_is_not_read(tmp_path: Path) -> None:
    """The working tree is not the base either: a heavy project stays heavy while the tree says light."""
    repo = Repo(tmp_path, _brief("heavy"))
    repo.write("src/a.py", BIG)
    repo.commit("feat: a")
    repo.write("docs/project-brief.md", _brief("light"))
    _, last, out = repo.need()
    assert last == "review-need: code-reviewer" and "working mode: heavy" in out, out


def test_the_base_is_the_merge_base_of_the_two_ends(tmp_path: Path) -> None:
    """`A...B` and a branch beside a later `main`: the brief is read where the branch left `main`."""
    repo = Repo(tmp_path, _brief("heavy"))
    repo.git("checkout", "-q", "-b", "side")
    repo.write("src/a.py", BIG)
    repo.commit("feat: a")
    repo.git("checkout", "-q", "main")
    repo.write("docs/project-brief.md", _brief("light"))
    repo.commit("docs: light")
    _, last, out = repo.need("--range", "main...side")
    assert last == "review-need: code-reviewer" and "working mode: heavy" in out, out


def test_explicit_at_still_reads_the_brief_there(tmp_path: Path) -> None:
    """`--at` stays (how `make wave-check` grades a close by the rules of its own time)."""
    repo = Repo(tmp_path, _brief("light"))
    at = repo.git("rev-parse", "HEAD")
    repo.write("docs/project-brief.md", _brief("heavy"))
    repo.commit("docs: heavy")
    repo.write("src/a.py", BIG)
    repo.commit("feat: a")
    _, last, out = repo.need()
    assert last == "review-need: code-reviewer", out          # the base, heavy
    _, last, out = repo.need("--range", "HEAD~1..HEAD", "--at", at)
    assert last == "review-need: none" and f"brief read at {at} (--at)" in out, out   # light, as of --at


def test_a_base_that_cannot_be_read_is_cannot_run(tmp_path: Path) -> None:
    repo = Repo(tmp_path, _brief("light"))
    repo.write("src/a.py", "a = 1\n")
    head = repo.commit("feat: a")
    for args in (("--range", f"{'0' * 40}..{head}"), ("--range", head), ("--range", "HEAD~1..HEAD", "--at", "f" * 40)):
        code, last, out = repo.need(*args)
        assert code == 2 and "CANNOT RUN" in last and "review-need:" not in out.replace("review-need CANNOT", ""), out
