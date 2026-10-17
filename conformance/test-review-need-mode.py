#!/usr/bin/env python3
"""`make review-need` reads the working mode, ignores test-only HIGH hits, and knows the Go decoders.

WHY (DevFlow #16, D3; two field projects, 24 contradictions). The script had no light/heavy input:
the "light runs no Code-Reviewer" rule lived only in the skills' prose, and the same project
followed the prose one day and the script the next. A range touching only tests under a HIGH glob
was routed to security for no product change. The Go body parser in the field was
`json.NewDecoder(r.Body).Decode(&v)`, and only `json.Unmarshal` was in the regex.

Each case is a throwaway git repository with its own brief: the script is run there and its last
line (`review-need: ...`) and its reasons are read. Both polarities per rule: light must not answer
`code-reviewer`, heavy must; a test-only HIGH hit must be `none`, the same path as product code must
be `security` (light mode; in heavy mode it is kept for the milestone's security review, v7.1.2); `NewDecoder`
must be `security`, and a stacked branch measured by its own base must
not report the lower branch's gate change.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "review_need.py"
BIG = "".join(f"v{i} = {i}\n" for i in range(200))


class Repo:
    def __init__(self, tmp: str):
        self.root = pathlib.Path(tmp)
        self.env = scrubbed_env()
        self.git("init", "-q")
        self.git("commit", "-q", "--allow-empty", "-m", "base")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=self.root,
                              capture_output=True, text=True, check=True, env=self.env).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def need(self, rng: str = "HEAD~1..HEAD", *extra: str) -> tuple[str, str]:
        r = subprocess.run([sys.executable, str(SCRIPT), "--range", rng, *extra], cwd=self.root, capture_output=True,
                           text=True, env=self.env)
        out = r.stdout + r.stderr
        last = out.strip().splitlines()[-1] if out.strip() else ""
        return last, out


def brief(mode: str, high: str = "none") -> str:
    return (f"---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n"
            f"- **Working mode:** `{mode}`\n- **Paths that make a change HIGH:** `{high}`\n")


def main() -> int:
    no_git = missing_tool("git", "build the throwaway repositories review_need.py measures")
    if no_git:
        print(f"test-review-need-mode NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []

    def case(name: str, got: tuple[str, str], want_last: str, *want_in: str) -> None:
        last, out = got
        if last != want_last or any(w not in out for w in want_in):
            bad.append(f"  {name}: got `{last}`, wanted `{want_last}`"
                       + (f" and the lines {list(want_in)}" if want_in else "") + "\n"
                       + "\n".join(f"    {ln}" for ln in out.splitlines()))

    with tempfile.TemporaryDirectory() as tmp:
        r = Repo(tmp)
        r.write("docs/project-brief.md", brief("light"))
        r.commit("brief")
        r.write("src/a.py", BIG)
        r.commit("big")
        case("light mode, 200 product lines: no Code-Reviewer, and it says why", r.need(), "review-need: none",
             "working mode: light", "no Code-Reviewer in light mode")
        r.write("docs/project-brief.md", brief("heavy"))
        r.commit("heavy")
        r.write("src/a.py", BIG + "w = 0\n")
        r.write("src/b.py", BIG)
        r.commit("big again")
        case("heavy mode, the same change: a Code-Reviewer", r.need(), "review-need: code-reviewer",
             "working mode: heavy")

    with tempfile.TemporaryDirectory() as tmp:
        r = Repo(tmp)
        r.write("docs/project-brief.md", brief("light", "src/**, tests/**"))
        r.commit("brief")
        r.write("tests/test_auth_flow.py", "def test_x():\n    assert 1\n")
        r.commit("test only")
        case("a test-only range under a HIGH glob with a sensitive name: none, and the hit is named test-only",
             r.need(), "review-need: none", "test-only files under declared HIGH paths")
        r.write("src/auth_flow.py", "x = 1\n")
        r.commit("product")
        case("the same path shape as product code: security", r.need(), "review-need: security",
             "declared HIGH paths: src/auth_flow.py")
        # v7.1.2: heavy mode runs security once per milestone (the owner's ruling of 2026-10-16), so the
        # same range in heavy mode is not routed there; the signal is printed for the milestone's review.
        r.write("docs/project-brief.md", brief("heavy", "src/**, tests/**"))
        r.commit("heavy")
        r.write("src/auth_flow.py", "x = 2\n")
        r.commit("product, heavy")
        case("heavy mode, a HIGH path: no per-wave security, the signal kept for the milestone", r.need(),
             "review-need: none", "declared HIGH paths: src/auth_flow.py", "security runs once per milestone")
        case("...and with --wave-security (a close written before v7.1.2): security, as it was",
             r.need("HEAD~1..HEAD", "--wave-security"), "review-need: security")

    with tempfile.TemporaryDirectory() as tmp:
        r = Repo(tmp)
        r.write("docs/project-brief.md", brief("light"))
        # #283: the brief is read at the range's base, and a range that writes it is a policy edit, so the
        # brief is committed before the range this case measures.
        r.commit("brief")
        r.write("src/h.go", "package h\n\nfunc load(r io.Reader, v any) error {\n"
                            "\tdec := json.NewDecoder(r)\n\treturn dec.Decode(v)\n}\n")
        r.commit("decoder")
        # v7.2 (the owner's ruling of 2026-10-17): light mode routes per change only declared HIGH paths;
        # a parser is still found, and named for the release review.
        case("light, a Go NewDecoder/Decode body parser and no HIGH path: found, kept for the release review",
             r.need(), "review-need: none", "new parser or fetch of untrusted input: .Decode(, json.NewDecoder(",
             "these signals are for the release review")
        r.write("docs/project-brief.md", brief("light", "src/**"))
        r.commit("declare src HIGH")
        r.write("src/h.go", "package h\n\nfunc load(r io.Reader, v any) error {\n\treturn json.NewDecoder(r).Decode(v)\n}\n")
        r.commit("decoder under a HIGH path")
        case("light, the same parser under a declared HIGH path: security", r.need(), "review-need: security",
             "declared HIGH paths: src/h.go")

    with tempfile.TemporaryDirectory() as tmp:
        r = Repo(tmp)
        r.write("scripts/gate.py", "x = 1\n")
        lower = r.commit("lower branch: gate code")
        r.write("src/a.py", "y = 2\n")
        r.commit("upper branch: one product line")
        case("a stacked branch measured from its own base reports no gate change",
             r.need(f"{lower}..HEAD"), "review-need: none")
        case("...and measured from the default base it does, which is why the range is documented",
             r.need("HEAD~2..HEAD"), "review-need: code-reviewer", "gate or control code changed: scripts/gate.py")
        # A failed merge-base upstream (no origin/HEAD) used to hand over `..HEAD`: an empty diff, `none`.
        case("a range with an empty side cannot run, never a vacuous none", r.need("..HEAD"),
             "review-need CANNOT RUN: `..HEAD` is not a range of two commits -- a review decision with no diff behind it decides nothing")
        case("a range naming no commit cannot run", r.need("nosuchref..HEAD"),
             "review-need CANNOT RUN: `nosuchref..HEAD` is not a range of two commits -- a review decision with no diff behind it decides nothing")

    if bad:
        print("test-review-need-mode FAIL (scripts/review_need.py in throwaway repositories):")
        print("\n".join(bad))
        return 1
    print("test-review-need-mode PASS: 11 cases of scripts/review_need.py -- mode, test-only paths, Go decoders, "
          "stacked range, heavy mode's security once per milestone")
    return 0


if __name__ == "__main__":
    sys.exit(main())
