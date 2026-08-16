#!/usr/bin/env python3
"""Every control the documentation claims is enforced must be reachable from `make gate`.

WHY. `pipeline-design.md` listed four controls on the commit hook: make check, gitleaks, pip-audit,
slopsquat. The hook ran `make check`. `make check` was `lint typecheck test`. It also listed a
PreToolUse block on destructive git commands, which had never existed in `.claude/settings.json`.
**Four of six advertised controls were absent, on the page a reviewer reads to learn what is enforced.**
Nobody noticed for several versions because prose and configuration are never compared by anything.

This compares them. Exit 0 clean, 1 findings.
"""
import sys, re, json, pathlib, subprocess, shutil

# control name -> (Makefile target that must exist, string that must appear in that target's recipe)
CLAIMED = {
    "lint":      ("lint",      "ruff"),
    "typecheck": ("typecheck", "mypy"),
    "test":      ("test",      "pytest"),
    "secrets":   ("secrets",   "gitleaks"),
    "deps":      ("deps",      "pip_audit"),
    "slopsquat": ("slopsquat", "slopsquat_check.py"),
    # v5: neutering these two in the Makefile went undetected, because CLAIMED never listed them --
    # the governance validator and its own not-a-no-op proof were the two controls the claims-checker
    # was not checking. Found by `falsify.py` the first time its recipes actually mutated anything.
    "check-records":          ("check-records", "check_records.py"),
    "check-records-selftest": ("check-records-selftest", "--self-test"),
}


def targets(mk: str) -> dict[str, str]:
    out, cur = {}, None
    for line in mk.splitlines():
        m = re.match(r"^([A-Za-z0-9_.-]+):(.*)$", line)
        if m:
            cur = m.group(1); out[cur] = m.group(2) + "\n"
        elif cur and (line.startswith("\t") or line.startswith("    ")):
            out[cur] += line + "\n"
        elif line.strip() == "":
            cur = None
    return out


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    mk = (root / "Makefile").read_text(encoding="utf-8")
    tg = targets(mk)
    bad = []

    if "gate" not in tg:
        print("  FAIL no `gate` target -- there is no single name meaning 'everything we claim'")
        return 1
    gate_deps = set(tg["gate"].splitlines()[0].split())

    # transitively expand one level (gate: check secrets ... ; check: lint typecheck ...)
    reachable = set(gate_deps)
    for d in list(gate_deps):
        if d in tg:
            reachable |= set(tg[d].splitlines()[0].split())

    for name, (target, must) in CLAIMED.items():
        if target not in tg:
            bad.append(f"`{name}` is claimed in the docs but there is no `{target}` target"); continue
        if target not in reachable:
            bad.append(f"`{target}` exists but is NOT reachable from `make gate` -- a target with no "
                       "caller is a control only someone who already knows the name can run")
        # v5 (Software seat). Token presence was defeated by keeping the token and disabling the
        # command: `-$(PY) -m ruff check src tests || true` still contains "ruff". The seat unwired
        # `make lint` and gutted `make secrets` to `echo skipping; exit 0`, and every board stayed
        # green. **A recipe that cannot fail is not a control, whatever words are in it.**
        body = tg[target]
        for line in body.splitlines():
            ln = line.strip()
            if not ln or ln.startswith("#"):
                continue
            if ln.startswith("-") or re.search(r"\|\|\s*true\b|;\s*exit\s+0\b|\|\|\s*exit\s+0\b", ln):
                bad.append(f"`{target}` swallows its own failure (`{ln[:46]}`) -- the token is there "
                           "and the control cannot fail")
        if must not in tg[target]:
            bad.append(f"`{target}` does not actually invoke `{must}` -- it runs "
                       f"`{tg[target].strip().splitlines()[-1][:50] if tg[target].strip() else '(nothing)'}`")

    # v4.3.2 (audit S10/B1). This function used to reason over Makefile TEXT. It reported
    # "0 unbacked" on a Makefile where `make gate` silently skipped the whole conformance suite,
    # because `conformance` is also a directory and was missing from `.PHONY`. **Reading a build file
    # is not the same as running it, and the difference is exactly where this defect lived.**
    # Ask make itself.
    if shutil.which("make"):
        dry = subprocess.run(["make", "-n", "gate"], cwd=root, capture_output=True, text=True).stdout
        for must, why in (("run-all.py", "the conformance suite"),
                          ("check_records.py", "the governance validator"),
                          ("slopsquat_check.py", "the slopsquat check")):
            if must not in dry:
                bad.append(f"`make -n gate` never expands `{must}` -- {why} does not execute through "
                           "the documented command, whatever the Makefile appears to say")
        phony = re.search(r"^\.PHONY:(.*(?:\\\n.*)*)$", mk, re.M)
        declared = set((phony.group(1) if phony else "").replace("\\", " ").split())
        for t in tg:
            if (root / t).exists() and t not in declared:
                bad.append(f"target `{t}` collides with a real path and is not in .PHONY -- make will "
                           "call it up to date and never run its recipe")

    # the destructive-command PreToolUse hook the design doc has promised since v2
    st = root / ".claude" / "settings.json"
    blob = json.dumps(json.loads(st.read_text(encoding="utf-8"))) if st.is_file() else ""
    # v5, THIRD generation of this mistake. It began as `"rm" in blob`, satisfied by the word
    # "pe-rm-ission". It became a narrower regex over the config TEXT -- and then a correctly widened
    # hook failed it, because the new pattern does not spell `-rf` literally. **Grepping a hook tells
    # you what it looks like; only running it tells you what it does.** So run it.
    MUST_BLOCK = ["git push origin main --force", "git push --force origin main", "git push -f o x",
                  "git reset --hard HEAD~1", "rm -rf .", "rm -rf ~/work", "rm -fr /home/u",
                  "git clean -fd"]
    MUST_ALLOW = ["git push origin main", "git status", "rm file.txt", "rm -r build",
                  "git reset HEAD~1", "npm run format"]
    bash_hook = next((h["hooks"][0]["command"] for h in
                      json.loads(st.read_text(encoding="utf-8"))["hooks"].get("PreToolUse", [])
                      if h.get("matcher") == "Bash"), None)
    if bash_hook is None:
        bad.append("no PreToolUse Bash hook at all, and pipeline-design.md claims one blocks "
                   "destructive commands")
    else:
        for cmd, want_block in [(c, True) for c in MUST_BLOCK] + [(c, False) for c in MUST_ALLOW]:
            payload = json.dumps({"tool_input": {"command": cmd}})
            r = subprocess.run(["bash", "-c", bash_hook], input=payload,
                               capture_output=True, text=True)
            blocked = r.returncode != 0
            if blocked != want_block:
                bad.append(f"PreToolUse {'failed to block' if want_block else 'wrongly blocked'} "
                           f"`{cmd}` -- permission-matrix.md S6 and pipeline-design.md both describe "
                           "this hook, and a claim nobody executes is a claim nobody has checked")

    env_hook = next((h["hooks"][0]["command"] for h in
                     json.loads(st.read_text(encoding="utf-8"))["hooks"].get("PreToolUse", [])
                     if h.get("matcher", "").startswith("Write")), None)
    if env_hook:
        for path, want_block in [(".env", True), ("cfg/.env.prod", True), ("prod.env", True),
                                 ("src/app.py", False), ("README.md", False)]:
            r = subprocess.run(["bash", "-c", env_hook],
                               input=json.dumps({"tool_input": {"file_path": path}}),
                               capture_output=True, text=True)
            if (r.returncode != 0) != want_block:
                bad.append(f"PreToolUse {'failed to block' if want_block else 'wrongly blocked'} "
                           f"a write to `{path}`")
    if "make gate" not in blob:
        bad.append("the PostToolUse hook does not call `make gate` -- the docs say the full gate fires "
                   "on every commit")

    for b in bad:
        print(f"  FAIL {b}")
    print(f"test-hook-claims {'FAIL' if bad else 'PASS'}: {len(CLAIMED)} claimed control(s), {len(bad)} unbacked")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
