#!/usr/bin/env python3
"""Every control the documentation claims is enforced must be reachable from `make gate`.

WHY. `METHODOLOGY.md` listed four controls on the commit hook: make check, gitleaks, pip-audit,
slopsquat. The hook ran `make check`. `make check` was `lint typecheck test`. It also listed a
PreToolUse block on destructive git commands, which had never existed in `.claude/settings.json`.
**Four of six advertised controls were absent, on the page a reviewer reads to learn what is enforced.**
Nobody noticed for several versions because prose and configuration are never compared by anything.

This compares them. Exit 0 clean, 1 findings.

v5.2, condition 17-1 -- A RULE MAY NOT OUTLIVE ITS GATE (the reverse direction of V4C-49, adopted
7/7 at Increment 17 with no new register id: V5C-110 already forbids the hand-kept list this file
was carrying).

**The `CLAIMED` dict is retired here.** It was eight hand-written entries sitting beside the
controls they described -- the exact shape V5C-110 names -- and it had already failed once by its
own admission: `check-records` and `check-records-selftest` were absent from it, so neutering them
in the Makefile went undetected. `bootstrap-check` was absent too, which is why `docs/security-
baseline.md` could call it a **GATE** in bold for five versions while nothing called it. Three
council seats found that independently.

What replaces it is derived: **a document that asserts its own enforcement declares
an `enforced-by:` line naming a path in backticks (optionally `@` a location), and this test resolves it
against what actually runs.** No list to update; the claim and its check live in the same sentence.

FAILS CLOSED (Security + Quality seats): finding zero declarations is a FAILURE, not a pass. A
parser that silently matches nothing is the defect this rule exists to name, one level up.

Field evidence, three non-GP projects: a rulebook asserting five rules as enforced while the same
commit deleted three of their gates; a data-erasure register claiming "read by <gate> on every push"
that, run by hand, failed on eight columns, three of them genuinely holding a person; and a restart
commit claiming to restore `mypy` in a tree where `grep mypy` returns nothing.
"""
import sys, re, json, pathlib, subprocess, shutil

# Where a project may assert enforcement. Documents, not code -- code is checked by being run.
CLAIM_ROOTS = ("docs", ".agents", "AGENTS.md", "README.md", "permission-matrix.md")
# `enforced-by: `path`` with an optional `@ `location``
CLAIM_RE = re.compile(r"enforced-by:\s*`([^`]+)`(?:\s*@\s*`([^`]+)`)?")


def enforcement_claims(root: pathlib.Path) -> list[tuple[pathlib.Path, str, str | None]]:
    """Every `enforced-by:` declaration in the documentation tree. DERIVED, never enumerated."""
    out = []
    for base in CLAIM_ROOTS:
        target = root / base
        files = [target] if target.is_file() else (
            sorted(target.rglob("*.md")) if target.is_dir() else [])
        for f in files:
            for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
                m = CLAIM_RE.search(ln)
                if m:
                    out.append((f.relative_to(root), m.group(1).strip(), m.group(2)))
    return out


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
    def prereqs(target: str) -> set[str]:
        # A target line may carry a `## help` comment, which `split()` happily turned into
        # forty-odd "prerequisites" with names like `the` and `a`. Stop at the comment.
        return set(tg[target].splitlines()[0].split("#")[0].split()) if target in tg else set()

    gate_deps = prereqs("gate")
    # transitively expand one level (gate: check secrets ... ; check: lint typecheck ...)
    reachable = set(gate_deps)
    for d in list(gate_deps):
        reachable |= prereqs(d)

    # v5 (Software seat), widened at v5.2 (17-1). Token presence was defeated by keeping the token
    # and disabling the command: `-$(PY) -m ruff check src tests || true` still contains "ruff". The
    # seat unwired `make lint` and gutted `make secrets` to `echo skipping; exit 0`, and every board
    # stayed green. **A recipe that cannot fail is not a control, whatever words are in it.**
    # This used to run only over the eight targets the retired `CLAIMED` dict listed. It now runs
    # over EVERY target reachable from `make gate`, which is the set the claim actually covers --
    # retiring the list widened the check instead of narrowing it.
    for target in sorted(reachable):
        if target not in tg:
            bad.append(f"`{target}` is a prerequisite of `make gate` but has no target")
            continue
        for line in tg[target].splitlines():
            ln = line.strip()
            if not ln or ln.startswith("#"):
                continue
            if ln.startswith("-") or re.search(r"\|\|\s*true\b|;\s*exit\s+0\b|\|\|\s*exit\s+0\b", ln):
                bad.append(f"`{target}` swallows its own failure (`{ln[:46]}`) -- the token is there "
                           "and the control cannot fail")
        # v5.2 (17-1). The retired `CLAIMED` dict carried a per-target `must` token -- "this target
        # has to invoke `ruff`" -- which is how it caught a leg neutered to `@echo neutered`.
        # Deriving the suite dropped that, and `falsify.py` reported two controls NOT-BROKEN within
        # the hour. **Retiring a hand-kept list must not retire what the list was checking.** The
        # derived form of the same question: a leg whose whole recipe is echoes and no-ops runs
        # nothing, whatever it is named.
        real = [ln.strip().lstrip("@-") for ln in tg[target].splitlines()[1:]
                if ln.strip() and not ln.strip().startswith("#")]
        if real and all(re.match(r"(echo|true|:)\b", c) for c in real):
            bad.append(f"`{target}` is a gate leg whose recipe only echoes -- it runs nothing, and "
                       f"a target that cannot fail is not a control")
        # v5.3, TB-092 (Increment 18). Retiring the `CLAIMED` dict recovered the echo/no-op half of
        # what it checked and LOST the substitution half. Measured on three scratch trees: `lint`
        # neutered to `@echo neutered` FAILS in both versions; `lint` neutered to
        # `$(PY) -c "import sys; sys.exit(0)"` -- a real command that checks nothing -- FAILED under
        # the dict and PASSED under the derived replacement. It went unnoticed because every recipe
        # in `falsifications.py` neuters with `@echo`, so the repair was green against every probe
        # while the class stayed open. **Retiring a hand-kept list must not retire what the list was
        # checking** -- the same lesson as the no-op check above, one layer deeper.
        #
        # Derived, not hand-kept: the tool a leg must invoke is the token `leg_tokens()` already
        # extracts from the Makefile for caller-liveness. If a leg names a tool, it must still run
        # it.
        if target in reachable and tg[target].splitlines()[1:]:
            declared = set(re.findall(r"(?:scripts|conformance)/[\w.-]+\.py", tg[target]))
            declared |= set(re.findall(r"\b(gitleaks|pip_audit|pip-audit|ruff|mypy|pytest)\b",
                                       "\n".join(l for l in tg[target].splitlines()
                                                 if not l.strip().startswith("#"))))
            body_code = "\n".join(l for l in tg[target].splitlines()[1:]
                                   if l.strip() and not l.strip().startswith("#"))
            for tool in sorted(declared):
                if tool not in body_code:
                    bad.append(f"`{target}` names `{tool}` but its recipe does not invoke it")

    # ---- 17-1: a rule may not outlive its gate ------------------------------------------------
    claims = enforcement_claims(root)
    if not claims:
        bad.append("no `enforced-by:` declaration found anywhere in the documentation tree. This "
                   "check FAILS CLOSED: a parser that matches nothing is not evidence that nothing "
                   "is claimed, and GP asserts enforcement in at least one shipped document")
    dry_gate = ""
    if shutil.which("make"):
        dry_gate = subprocess.run(["make", "-n", "gate"], cwd=root,
                                  capture_output=True, text=True).stdout
    ci_text = "\n".join(f.read_text(encoding="utf-8", errors="replace")
                        for f in sorted((root / ".github" / "workflows").glob("*.yml"))) \
        if (root / ".github" / "workflows").is_dir() else ""
    hooks_text = (root / ".claude" / "settings.json").read_text(encoding="utf-8", errors="replace") \
        if (root / ".claude" / "settings.json").is_file() else ""

    for where, path_claim, at in claims:
        name = pathlib.PurePosixPath(path_claim).name
        if not (root / path_claim).is_file():
            bad.append(f"{where} declares `enforced-by: {path_claim}` and that file does not exist")
            continue
        if at:
            # An explicit home: the control runs from a named place rather than from `make gate`.
            # `bootstrap-check` is the shipped example -- it belongs at Stage 0 close, because it
            # fails on unfilled placeholders and would make every fresh export red on day one.
            home = root / at.split("#")[0].strip()
            if not home.is_file():
                bad.append(f"{where} declares `enforced-by: {path_claim} @ {at}` -- that home "
                           f"does not exist")
            elif not any(tok in home.read_text(encoding="utf-8", errors="replace")
                         for tok in (path_claim, name, pathlib.PurePosixPath(name).stem)):
                bad.append(f"{where} claims `{path_claim}` is enforced at `{at}`, and `{at}` never "
                           f"mentions it -- the claim names a home that does not hold it")
        elif not any(name in blob for blob in (dry_gate, ci_text, hooks_text)):
            bad.append(f"{where} claims `{path_claim}` enforces something, and nothing runs it: "
                       f"absent from `make -n gate`, from every workflow, and from the hooks. "
                       f"**A rule that outlives its gate is worse than one that never had a gate, "
                       f"because the sentence claiming enforcement is still there to be believed**")

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
    # v6.0. `git push origin main` was in MUST_ALLOW and is now in MUST_BLOCK, and that reversal is
    # the point of the change: three shipped files said the agent never pushes the protected branch
    # while the hook -- the only thing that can actually refuse -- permitted it, and THIS TEST
    # ASSERTED THE PERMISSION. A control asserting the opposite of the rule it serves is worse than
    # no control, because the board is green. Pushing the agent's OWN branch stays allowed: it is
    # how the draft PR gets opened, and a rule that blocked it would be unwirable within a day.
    MUST_BLOCK = ["git push origin main --force", "git push --force origin main", "git push -f o x",
                  "git push origin main", "git push origin master", "git push origin HEAD:main",
                  "git reset --hard HEAD~1", "rm -rf .", "rm -rf ~/work", "rm -fr /home/u",
                  "git clean -fd"]
    MUST_ALLOW = ["git push -u origin fix/issue-3", "git push origin enhancement/x", "git push",
                  "git status", "rm file.txt", "rm -r build",
                  "git reset HEAD~1", "npm run format"]
    bash_hook = next((h["hooks"][0]["command"] for h in
                      json.loads(st.read_text(encoding="utf-8"))["hooks"].get("PreToolUse", [])
                      if h.get("matcher") == "Bash"), None)
    if bash_hook is None:
        bad.append("no PreToolUse Bash hook at all, and METHODOLOGY.md claims one blocks "
                   "destructive commands")
    else:
        for cmd, want_block in [(c, True) for c in MUST_BLOCK] + [(c, False) for c in MUST_ALLOW]:
            payload = json.dumps({"tool_input": {"command": cmd}})
            r = subprocess.run(["bash", "-c", bash_hook], input=payload,
                               capture_output=True, text=True)
            blocked = r.returncode != 0
            if blocked != want_block:
                bad.append(f"PreToolUse {'failed to block' if want_block else 'wrongly blocked'} "
                           f"`{cmd}` -- permission-matrix.md S6 and METHODOLOGY.md both describe "
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
    print(f"test-hook-claims {'FAIL' if bad else 'PASS'}: {len(claims)} enforcement claim(s) "
          f"derived, {len(reachable)} gate leg(s), {len(bad)} unbacked")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
