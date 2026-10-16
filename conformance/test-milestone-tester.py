#!/usr/bin/env python3
"""The milestone Tester runs at every milestone close, in light mode too: `closure_check` and `wave_check` require its verdict.

WHY (DevFlow #16, D8, the owner's ruling of 2026-10-13). v7.0 defined light mode as "no Tester",
and in the field a light-mode release went to the store with no fault-injection review at all, while
the other light project ran zero Testers after its upgrade. The owner ruled that the Tester runs at
every milestone close in both modes, and that the GATE makes it happen rather than the prose.

Heavy: `docs/reviews/m<N>-tester.md`, the verdict the plan's last wave carried. Light: the close is
the one before a release, on everything merged since the Tester's last verdict, and the file is
`docs/reviews/release-tester.md` with a `**Reviewed head:**` line that must be current for the
working tree -- the deploy gate's rule for `release-security.md`. Each case builds a throwaway
repository holding the shipped v7.1 closure fixture, its own brief, and the files the fixture cites,
and runs the scripts there in both polarities and both modes; `wave_check` is run on the shipped
last-wave fixture with a light-mode brief and no Tester verdict, and must refuse. A light project
writes no closure report, so `closure_check.py --release-records` (a leg of `make closes`, both
modes) is what reaches it: once `docs/reviews/release-security.md` exists, the Tester's verdict for
that release must exist beside it; the deploy gate and `make deploy-check` ask the same at the deploy.

Exit: 0 every case behaves - 1 one does not - 2 git not installed.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLOSURE = ROOT / "scripts" / "closure_check.py"
WAVE = ROOT / "scripts" / "wave_check.py"
REPORT = ROOT / "conformance" / "closure" / "closure-report-m909.md"
TESTER = ROOT / "conformance" / "closure" / "reviews" / "m909-tester.md"
WAVE_FIXTURE = ROOT / "conformance" / "wave" / "m901-wave-2-close.md"
REVIEW_FIXTURE = ROOT / "conformance" / "reviews" / "m901-wave-2-review.md"


def brief(mode: str) -> str:
    return (f"---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n"
            f"- **Working mode:** `{mode}`\n")


class Tree:
    def __init__(self, tmp: str, mode: str):
        self.root = pathlib.Path(tmp)
        self.env = scrubbed_env()
        (self.root / "docs" / "reviews").mkdir(parents=True)
        (self.root / "docs" / "project-brief.md").write_text(brief(mode), encoding="utf-8")
        shutil.copy(REPORT, self.root / "docs" / "closure-report-m909.md")
        for path, _ in re.findall(r"`([\w./-]+\.\w+):(\d+)`", REPORT.read_text(encoding="utf-8")):
            p = self.root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x\n" * 200, encoding="utf-8")
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=self.root,
                              capture_output=True, text=True, check=True, env=self.env).stdout.strip()

    def tester(self, name: str, head: str | None = None) -> None:
        body = re.sub(r"^\*\*Reviewed head:\*\*.*\n", "", TESTER.read_text(encoding="utf-8"), flags=re.M)
        if head:
            body = body.replace("**Independent:** yes\n", f"**Independent:** yes\n**Reviewed head:** {head}\n", 1)
        (self.root / "docs" / "reviews" / name).write_text(body, encoding="utf-8")

    def release_records(self) -> tuple[int, str]:
        r = subprocess.run([sys.executable, str(CLOSURE), "--release-records"], cwd=self.root,
                           capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr

    def closure(self) -> tuple[int, str]:
        r = subprocess.run([sys.executable, str(CLOSURE), "docs/closure-report-m909.md"], cwd=self.root,
                           capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr


def main() -> int:
    no_git = missing_tool("git", "build the throwaway repositories the closure check reads")
    if no_git:
        print(f"test-milestone-tester NOT-EVALUABLE: {no_git}")
        return 2
    if not (REPORT.is_file() and TESTER.is_file()):
        print(f"test-milestone-tester FAIL: the v7.1 fixtures {REPORT.name} and reviews/{TESTER.name} are missing")
        return 1
    bad: list[str] = []

    def case(name: str, got: tuple[int, str], rc: int, *want: str) -> None:
        code, out = got
        if code != rc or any(w not in out for w in want):
            bad.append(f"  {name}: exit {code} (wanted {rc}); wanted {list(want)}\n"
                       + "\n".join(f"    {ln}" for ln in out.splitlines()))

    with tempfile.TemporaryDirectory() as tmp:
        t = Tree(tmp, "heavy")
        case("heavy, no Tester verdict: refused, and the expected file is named", t.closure(), 1,
             "no milestone Tester verdict (heavy mode", "`reviews/m909-tester.md`", "working mode: heavy")
        t.tester("m909-tester.md")
        case("heavy, the verdict with no reviewed head: refused (the deploy gate reads it in heavy mode too)",
             t.closure(), 1, "names no `**Reviewed head:**")
        t.tester("m909-tester.md", t.git("rev-parse", "HEAD"))
        case("heavy, the verdict beside the report, with its head: accepted", t.closure(), 0, "closure_check PASS")

    with tempfile.TemporaryDirectory() as tmp:
        t = Tree(tmp, "light")
        case("light, no verdict: refused -- light mode is not exempt", t.closure(), 1,
             "`reviews/release-tester.md`", "working mode: light", "in light mode too")
        t.tester("m909-tester.md")
        case("light, only the heavy-mode file: still refused", t.closure(), 1, "`reviews/release-tester.md`")
        t.tester("release-tester.md")
        case("light, release-tester.md with no reviewed head: refused", t.closure(), 1, "names no `**Reviewed head:**")
        head = t.git("rev-parse", "HEAD")
        t.tester("release-tester.md", head)
        case("light, a current reviewed head: accepted", t.closure(), 0, "closure_check PASS")
        (t.root / "src").mkdir()
        (t.root / "src" / "new.py").write_text("y = 1\n", encoding="utf-8")
        case("light, code added after the reviewed head (untracked): refused", t.closure(), 1,
             "changed since `release-tester.md`'s reviewed head", "src/new.py")
        (t.root / "docs" / "note.md").write_text("a record\n", encoding="utf-8")
        (t.root / "src" / "new.py").unlink()
        case("light, only a record added after the head: accepted (the deploy gate's rule)", t.closure(), 0,
             "closure_check PASS")

    # `make closes` in a tree with no closure report at all -- a light project, or a heavy one with
    # the Quality Gate off -- still asks: did the reviewed release have its Tester?
    with tempfile.TemporaryDirectory() as tmp:
        t = Tree(tmp, "light")
        (t.root / "docs" / "closure-report-m909.md").unlink()
        case("release-records, light, no release yet: nothing to grade", t.release_records(), 0, "no release to grade")
        (t.root / "docs" / "reviews" / "release-security.md").write_text("# s\n**Reviewed head:** abc\n", encoding="utf-8")
        case("release-records, light, a reviewed release and no Tester: refused", t.release_records(), 1,
             "release-security.md exists and the milestone Tester's release verdict (light mode")
        t.tester("release-tester.md")
        case("release-records, light, Tester with no reviewed head: refused", t.release_records(), 1,
             "names no `**Reviewed head:**")
        t.tester("release-tester.md", t.git("rev-parse", "HEAD"))
        case("release-records, light, Tester with a head: accepted", t.release_records(), 0, "release-records PASS")
    with tempfile.TemporaryDirectory() as tmp:
        t = Tree(tmp, "heavy")
        (t.root / "docs" / "closure-report-m909.md").unlink()
        (t.root / "docs" / "reviews" / "release-security.md").write_text("# s\n**Reviewed head:** abc\n", encoding="utf-8")
        case("release-records, heavy, a reviewed release and no m<N>-tester: refused", t.release_records(), 1,
             "a milestone Tester verdict (heavy mode: docs/reviews/m<N>-tester.md, written on a plan's last wave) is missing")
        t.tester("m909-tester.md", t.git("rev-parse", "HEAD"))
        case("release-records, heavy, m909-tester.md with its head: accepted", t.release_records(), 0, "release-records PASS")

    # wave_check on the plan's last wave, light mode, no Tester verdict: refused and the mode named.
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "docs" / "plans").mkdir(parents=True)
        (root / "docs" / "reviews").mkdir()
        (root / "docs" / "project-brief.md").write_text(brief("light"), encoding="utf-8")
        shutil.copy(WAVE_FIXTURE, root / "docs" / "plans" / "m901-wave-2-close.md")
        shutil.copy(REVIEW_FIXTURE, root / "docs" / "reviews" / "m901-wave-2-review.md")
        close = root / "docs" / "plans" / "m901-wave-2-close.md"
        close.write_text(close.read_text(encoding="utf-8").replace("Last wave of the plan: no", "Last wave of the plan: yes"),
                         encoding="utf-8")
        r = subprocess.run([sys.executable, str(WAVE), "docs/plans/m901-wave-2-close.md"], cwd=root,
                           capture_output=True, text=True, env=scrubbed_env())
        case("wave_check, last wave, light mode, no Tester: refused and the mode named",
             (r.returncode, r.stdout + r.stderr), 1, "no milestone Tester verdict", "working mode: light")

    if bad:
        print("test-milestone-tester FAIL (scripts/closure_check.py and wave_check.py in throwaway trees):")
        print("\n".join(bad))
        return 1
    print("test-milestone-tester PASS: 16 cases -- the milestone Tester's verdict required in heavy and light "
          "mode, light scoped by a current reviewed head; `make closes` asks a reviewed release for its Tester")
    return 0


if __name__ == "__main__":
    sys.exit(main())
