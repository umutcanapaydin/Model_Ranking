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
GATE = ROOT / "scripts" / "deploy_gate.py"
REPORT = ROOT / "conformance" / "closure" / "closure-report-m909.md"
TESTER = ROOT / "conformance" / "closure" / "reviews" / "m909-tester.md"
WAVE_FIXTURE = ROOT / "conformance" / "wave" / "m901-wave-2-close.md"
REVIEW_FIXTURE = ROOT / "conformance" / "reviews" / "m901-wave-2-review.md"
WANT = "no milestone Security-Reviewer verdict"


def brief(mode: str) -> str:
    return f"---\nrecord_type: brief\nid: project-brief\nstatus: draft\n---\n- **Working mode:** `{mode}`\n"


def verdict(path: pathlib.Path, text: str = "PASS") -> None:
    path.write_text(f"# Security Review -- m901\n\n**Independent:** yes\n\n## Verdict\n{text}\n", encoding="utf-8")


def wave(tmp: str, mode: str, version: str, plan_waves: int | None = None, says_last: bool = True) -> pathlib.Path:
    root = pathlib.Path(tmp)
    (root / "docs" / "plans").mkdir(parents=True)
    (root / "docs" / "reviews").mkdir()
    (root / "docs" / "project-brief.md").write_text(brief(mode), encoding="utf-8")
    text = WAVE_FIXTURE.read_text(encoding="utf-8")
    if says_last:
        text = text.replace("Last wave of the plan: no", "Last wave of the plan: yes")
    if plan_waves is not None:
        (root / "docs" / "plans" / "m901-plan.md").write_text(f"# M901\n\nwaves: {plan_waves}\n", encoding="utf-8")
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
    # v7.2: the plan's `waves:` line decides which wave is the last (the owner's ruling of 2026-10-17).
    def plan_case(name: str, plan_waves: int, says_last: bool, want: str) -> None:
        nonlocal count
        count += 1
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_wave(wave(tmp, "heavy", "v7.2", plan_waves, says_last))
            if want not in out or code != 1:
                bad.append(f"  {name}: exit {code}, `{want}` missing\n" + out[-500:])
    plan_case("the plan says waves: 2 and wave 2 says it is not the last: refused", 2, False, "says `waves: 2`")
    plan_case("...and the milestone verdicts are then required anyway", 2, False, WANT)
    plan_case("the plan says waves: 3 and wave 2 calls itself the last: refused", 3, True, "is not the plan's last")
    plan_case("the plan says waves: 1 and this is wave 2: refused until the plan is amended", 1, True,
              "amend the plan")

    def plan_ok(name: str, root: pathlib.Path) -> None:
        nonlocal count
        count += 1
        code, out = run_wave(root)
        if any(w in out for w in ("says `waves:", "is not the plan's last", "amend the plan")):
            bad.append(f"  {name}: refused on the plan's waves\n" + out[-500:])
    with tempfile.TemporaryDirectory() as tmp:
        root = wave(tmp, "heavy", "v7.2", 2, True)
        (root / "docs" / "plans" / "m901-plan.md").write_text("# M901\n\nwaves: 1\n\n| amended |\n\nwaves: 2\n",
                                                              encoding="utf-8")
        plan_ok("an amended plan appends `waves: 2` under `waves: 1`: the last line is the plan's", root)
    with tempfile.TemporaryDirectory() as tmp:
        root = wave(tmp, "heavy", "v7.2", 2, True)
        env = scrubbed_env()
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "wave 2 closed"]):
            subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=root, check=True,
                           capture_output=True, env=env)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
                              env=env).stdout.strip()
        close = root / "docs" / "plans" / "m901-wave-2-close.md"
        close.write_text(close.read_text(encoding="utf-8").replace("a1b2c3d..f4e5d6c", f"a1b2c3d..{head}"),
                         encoding="utf-8")
        (root / "docs" / "plans" / "m901-plan.md").write_text("# M901\n\nwaves: 3\n", encoding="utf-8")
        plan_ok("the plan amended to waves: 3 after wave 2 closed as the last: graded by the plan at its head",
                root)
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

    # v7.2 (the owner's ruling of 2026-10-17): in heavy mode a current milestone security verdict stands
    # for the release's at the deploy gate; in light mode it does not, and a stale one never does.
    def deploy(mode: str, head_in_verdict: bool, change_after: bool, release: str = "",
               independent: bool = True, older: bool = False) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "docs" / "reviews").mkdir(parents=True)
            (root / "src").mkdir()
            (root / "docs" / "project-brief.md").write_text(brief(mode), encoding="utf-8")
            (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
            env = scrubbed_env()
            g = ["git", "-c", "user.name=f", "-c", "user.email=f@x"]
            subprocess.run([*g, "init", "-q"], cwd=root, check=True, capture_output=True, env=env)
            subprocess.run([*g, "add", "-A"], cwd=root, check=True, capture_output=True, env=env)
            subprocess.run([*g, "commit", "-q", "-m", "code"], cwd=root, check=True, capture_output=True, env=env)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
                                  env=env).stdout.strip()
            line = f"**Reviewed head:** {head}\n" if head_in_verdict else ""
            ind = "**Independent:** yes\n"
            for name in ("m910-security.md", "m910-tester.md", "release-tester.md"):
                (root / "docs" / "reviews" / name).write_text(
                    f"# Review\n\n{ind if independent or 'security' not in name else ''}{line}\n## Verdict\nPASS\n",
                    encoding="utf-8")
            if older:   # m9 sorts after m10 as text; by number the latest is m10, which is the stale one
                (root / "docs" / "reviews" / "m9-security.md").write_text(
                    f"# Review\n\n{ind}{line}\n## Verdict\nPASS\n", encoding="utf-8")
                (root / "docs" / "reviews" / "m910-security.md").write_text(
                    f"# Review\n\n{ind}**Reviewed head:** {'0' * 40}\n\n## Verdict\nPASS\n", encoding="utf-8")
            if release:
                (root / "docs" / "reviews" / "release-security.md").write_text(
                    f"# Review\n\n{ind}{line}\n## Verdict\n{release}\n", encoding="utf-8")
            if change_after:
                (root / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(GATE), "--check"], cwd=root, capture_output=True,
                               text=True, env=env)
            return r.returncode, r.stdout + r.stderr

    for name, args, ok in (
            ("deploy gate, heavy, a current m<N>-security.md and no release-security.md: PASS",
             ("heavy", True, False), True),
            ("deploy gate, heavy, the milestone verdict names no reviewed head: refused", ("heavy", False, False), False),
            ("deploy gate, heavy, code changed after the milestone verdict's head: refused", ("heavy", True, True), False),
            ("deploy gate, light, only a milestone security verdict: refused (light reads release-security.md)",
             ("light", True, False), False),
            ("deploy gate, heavy, a BLOCKING release verdict under a PASS milestone one: refused",
             ("heavy", True, False, "BLOCKING"), False),
            ("deploy gate, heavy, the milestone verdict does not declare Independent: refused",
             ("heavy", True, False, "", False), False),
            ("deploy gate, heavy, the latest milestone by number (m910, stale) decides, not m9: refused",
             ("heavy", True, False, "", True, True), False)):
        count += 1
        rc, out = deploy(*args)
        if (rc == 0) != ok:
            bad.append(f"  {name}: exit {rc}\n" + "\n".join(f"    {ln}" for ln in out.splitlines()[-6:]))

    if bad:
        print("test-milestone-security FAIL (scripts/wave_check.py and closure_check.py in throwaway trees):")
        print("\n".join(bad))
        return 1
    print(f"test-milestone-security PASS: {count} cases -- heavy mode's milestone Security-Reviewer verdict required "
          "on the last wave and at the closure from v7.1.2, not in light mode, not for an older record; in "
          "heavy mode a current one stands for the release's at the deploy gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
