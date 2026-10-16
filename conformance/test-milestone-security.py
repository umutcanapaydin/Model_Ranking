#!/usr/bin/env python3
"""Heavy mode runs the Security-Reviewer once per milestone: `wave_check` and `closure_check` require its verdict.

WHY (the owner's ruling of 2026-10-16, v7.1.2). Heavy mode ran security per wave, on the signals
`make review-need` computes; the owner moved it to the milestone's end, beside the milestone Tester:
one Security-Reviewer on the plan's last wave, over the whole milestone, verdict
`docs/reviews/m<N>-security.md`. A rule in prose is a rule nobody runs, so the gates ask for the file.

Both polarities, both modes, both versions: a heavy last-wave close declaring v7.1.2 with no security
verdict is refused and one with it is not refused for it; the same close in light mode, or declaring
v7.1.1, is not asked for it (light keeps security per change; an older close is graded by the rules it
was written under). `closure_check` the same, on the shipped closure fixture re-declared as v7.1.2.

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
WANT = "no milestone Security-Reviewer verdict"


def brief(mode: str) -> str:
    return f"---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n- **Working mode:** `{mode}`\n"


def verdict(path: pathlib.Path, text: str = "PASS") -> None:
    path.write_text(f"# Security Review -- m901\n\n**Independent:** yes\n\n## Verdict\n{text}\n", encoding="utf-8")


def wave(tmp: str, mode: str, version: str) -> pathlib.Path:
    root = pathlib.Path(tmp)
    (root / "docs" / "plans").mkdir(parents=True)
    (root / "docs" / "reviews").mkdir()
    (root / "docs" / "project-brief.md").write_text(brief(mode), encoding="utf-8")
    text = WAVE_FIXTURE.read_text(encoding="utf-8").replace("Last wave of the plan: no", "Last wave of the plan: yes")
    text = re.sub(r"^process_version: .*$", f"process_version: {version}", text, count=1, flags=re.M)
    (root / "docs" / "plans" / "m901-wave-2-close.md").write_text(text, encoding="utf-8")
    shutil.copy(REVIEW_FIXTURE, root / "docs" / "reviews" / "m901-wave-2-review.md")
    shutil.copy(ROOT / "conformance" / "reviews" / "m901-wave-2-tester.md", root / "docs" / "reviews" / "m901-tester.md")
    return root


def run_wave(root: pathlib.Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(WAVE), "docs/plans/m901-wave-2-close.md"], cwd=root,
                       capture_output=True, text=True, env=scrubbed_env())
    return r.returncode, r.stdout + r.stderr


def closure(tmp: str, mode: str, version: str) -> pathlib.Path:
    root = pathlib.Path(tmp)
    (root / "docs" / "reviews").mkdir(parents=True)
    (root / "docs" / "project-brief.md").write_text(brief(mode), encoding="utf-8")
    text = re.sub(r"^process_version: .*$", f"process_version: {version}", REPORT.read_text(encoding="utf-8"),
                  count=1, flags=re.M)
    (root / "docs" / "closure-report-m909.md").write_text(text, encoding="utf-8")
    for path, _ in re.findall(r"`([\w./-]+\.\w+):(\d+)`", text):
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n" * 200, encoding="utf-8")
    env = scrubbed_env()
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
        subprocess.run(["git", "-c", "user.name=f", "-c", "user.email=f@x", *args], cwd=root, check=True,
                       capture_output=True, env=env)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, env=env).stdout.strip()
    tester = TESTER.read_text(encoding="utf-8")
    if "**Reviewed head:**" not in tester:
        tester = tester.replace("**Independent:** yes\n", f"**Independent:** yes\n**Reviewed head:** {head}\n", 1)
    else:
        tester = re.sub(r"^\*\*Reviewed head:\*\*.*$", f"**Reviewed head:** {head}", tester, flags=re.M)
    (root / "docs" / "reviews" / ("m909-tester.md" if mode != "light" else "release-tester.md")).write_text(
        tester, encoding="utf-8")
    return root


def run_closure(root: pathlib.Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(CLOSURE), "docs/closure-report-m909.md"], cwd=root,
                       capture_output=True, text=True, env=scrubbed_env())
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    if (no_git := missing_tool("git", "build the throwaway repositories the closure check reads")):
        print(f"test-milestone-security NOT-EVALUABLE: {no_git}")
        return 2
    bad: list[str] = []
    count = 0

    def case(name: str, got: tuple[int, str], present: bool, rc: int | None = None) -> None:
        nonlocal count
        count += 1
        code, out = got
        if (WANT in out) != present or (rc is not None and code != rc):
            bad.append(f"  {name}: exit {code}; `{WANT}` {'missing' if present else 'present'}\n"
                       + "\n".join(f"    {ln}" for ln in out.splitlines()[-12:]))

    with tempfile.TemporaryDirectory() as tmp:
        root = wave(tmp, "heavy", "v7.1.2")
        case("wave_check, heavy, last wave, v7.1.2, no security verdict: refused", run_wave(root), True, 1)
        verdict(root / "docs" / "reviews" / "m901-security.md")
        case("wave_check, heavy, last wave, v7.1.2, the milestone security verdict beside it: not asked again",
             run_wave(root), False)
        verdict(root / "docs" / "reviews" / "m901-security.md", "BLOCKING")
        got = run_wave(root)
        count += 1
        if "`m901-security.md` is BLOCKING" not in got[1] or got[0] != 1:
            bad.append("  wave_check, heavy, a BLOCKING milestone security verdict: not refused\n" + got[1][-600:])
    with tempfile.TemporaryDirectory() as tmp:
        case("wave_check, light, last wave, v7.1.2: security stays per change, not asked here",
             run_wave(wave(tmp, "light", "v7.1.2")), False)
    with tempfile.TemporaryDirectory() as tmp:
        case("wave_check, heavy, last wave, a v7.1.1 close: graded by its own rules, not asked",
             run_wave(wave(tmp, "heavy", "v7.1.1")), False)

    with tempfile.TemporaryDirectory() as tmp:
        root = closure(tmp, "heavy", "v7.1.2")
        case("closure_check, heavy, v7.1.2, no security verdict: refused", run_closure(root), True, 1)
        verdict(root / "docs" / "reviews" / "m909-security.md")
        case("closure_check, heavy, v7.1.2, with the verdict: PASS", run_closure(root), False, 0)
    with tempfile.TemporaryDirectory() as tmp:
        case("closure_check, light, v7.1.2: not asked", run_closure(closure(tmp, "light", "v7.1.2")), False)
    with tempfile.TemporaryDirectory() as tmp:
        case("closure_check, heavy, a v7.1 report: not asked", run_closure(closure(tmp, "heavy", "v7.1")), False, 0)

    if bad:
        print("test-milestone-security FAIL (scripts/wave_check.py and closure_check.py in throwaway trees):")
        print("\n".join(bad))
        return 1
    print(f"test-milestone-security PASS: {count} cases -- heavy mode's milestone Security-Reviewer verdict required "
          "on the last wave and at the closure from v7.1.2, not in light mode, not for an older record")
    return 0


if __name__ == "__main__":
    sys.exit(main())
