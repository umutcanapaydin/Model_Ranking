"""#505: the deploy gate compared the working tree with the reviewed head through git state the change can write.

`changed_since` asked `git diff` and `git ls-files --others --exclude-standard`. Each consults something the change
under evaluation can set in its own clone: an fsmonitor hook, the index's stat data, a clean filter in
`.git/info/attributes`, ignore rules in `.git/info/exclude` or `core.excludesFile`, and an untracked `.gitignore`
that ignores itself. Each hid a code change or a new code file, and the gate said no code changed since (the #493
security review's R1). D-231 clause 2: the gate hashes the content itself and compares it with the reviewed head's
tree; the only ignore rules that count are the `.gitignore` files committed at the reviewed head.
"""

from __future__ import annotations

import os
from pathlib import Path

from .test_deploy_gate_pin import Repo, _installed


def _seen(repo: Repo, rel: str) -> None:
    code, out = repo.check()
    assert code != 0, out
    assert rel in out, out


def test_an_fsmonitor_hook_that_reports_nothing_does_not_hide_an_edit(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    hook = repo.root / ".git" / "quiet-monitor"
    hook.write_text("#!/bin/sh\nprintf 'token\\0'\n", encoding="utf-8")
    hook.chmod(0o755)
    repo.git("config", "core.fsmonitor", str(hook))
    repo.git("config", "core.fsmonitorHookVersion", "2")
    repo.git("status", "--porcelain")
    repo.write("src/app.py", "x = 2  # a product change\n")
    _seen(repo, "src/app.py")


def test_a_same_size_edit_with_its_mtime_restored_is_seen(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    path = repo.root / "src" / "app.py"
    # An mtime well before the index is written, so git does not treat the entry as racy and look again.
    past = path.stat().st_mtime_ns - 100 * 10**9
    os.utime(path, ns=(past, past))
    repo.git("update-index", "--refresh")
    path.write_text("x = 9\n", encoding="utf-8")
    os.utime(path, ns=(past, past))
    repo.git("config", "core.checkStat", "minimal")
    repo.git("config", "core.trustctime", "false")
    _seen(repo, "src/app.py")


def test_a_clean_filter_in_info_attributes_does_not_hide_an_edit(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    (repo.root / ".git" / "info").mkdir(exist_ok=True)
    (repo.root / ".git" / "info" / "attributes").write_text("src/*.py filter=hide\n", encoding="utf-8")
    repo.git("config", "filter.hide.clean", "git show HEAD:%f")
    repo.write("src/app.py", "x = 2  # a product change\n")
    _seen(repo, "src/app.py")


def test_info_exclude_does_not_hide_a_new_code_file(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    (repo.root / ".git" / "info").mkdir(exist_ok=True)
    (repo.root / ".git" / "info" / "exclude").write_text("src/new.py\n", encoding="utf-8")
    repo.write("src/new.py", "x = 3\n")
    _seen(repo, "src/new.py")


def test_core_excludes_file_does_not_hide_a_new_code_file(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    excludes = repo.root / ".git" / "my-excludes"
    excludes.write_text("src/new.py\n", encoding="utf-8")
    repo.git("config", "core.excludesFile", str(excludes))
    repo.write("src/new.py", "x = 3\n")
    _seen(repo, "src/new.py")


def test_an_untracked_gitignore_that_ignores_itself_does_not_hide_a_new_code_file(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    repo.write("src/extra/.gitignore", "*\n")
    repo.write("src/extra/new.py", "x = 3\n")
    _seen(repo, "src/extra/new.py")


def test_a_gitignore_committed_at_the_reviewed_head_still_counts(tmp_path: Path) -> None:
    """The control: what the reviewed head's own `.gitignore` ignores is not a change."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write(".gitignore", "build/\n*.log\n")
    repo.commit("ignore build output")
    head = repo.git("rev-parse", "HEAD")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts at the ignore")
    repo.git("checkout", "-q", "-b", "after-ignore")
    repo.write("build/out.py", "x = 4\n")
    repo.write("src/run.log", "noise\n")
    code, out = repo.check()
    assert code == 0, out


def test_a_staged_new_file_is_seen_though_others_does_not_list_it(tmp_path: Path) -> None:
    """`--others` leaves out every path the index holds, so an index entry (a plain `git add`, or a forged one) took a
    new file out of it; each entry the reviewed head's tree does not hold counts on its own."""
    repo = _installed(tmp_path)
    repo.write("src/new.py", "x = 3\n")
    repo.git("add", "src/new.py")
    _seen(repo, "src/new.py")


def test_a_nested_gitignore_at_the_reviewed_head_ignores_only_below_itself(tmp_path: Path) -> None:
    """A committed `docs/.gitignore` scopes its patterns to `docs/`, as git does: it does not ignore `src/new.py`."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write("docs/.gitignore", "new.py\n")
    repo.commit("a docs-only ignore")
    head = repo.git("rev-parse", "HEAD")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts at the ignore")
    repo.git("checkout", "-q", "-b", "after-ignore")
    repo.write("docs/new.py", "x = 3\n")
    assert repo.check()[0] == 0, "the control: below docs/ it ignores"
    repo.write("src/new.py", "x = 3\n")
    _seen(repo, "src/new.py")


def test_a_mode_change_alone_is_seen(tmp_path: Path) -> None:
    """`git diff` listed a file whose executable bit changed; the content comparison reads the bit from disk too."""
    repo = _installed(tmp_path)
    (repo.root / "src" / "app.py").chmod(0o755)
    _seen(repo, "src/app.py")
