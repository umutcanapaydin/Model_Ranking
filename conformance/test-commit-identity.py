#!/usr/bin/env python3
"""The range gate: no commit may be mistaken for a human's, and none carries AI attribution.

THE RULE, as the code grades it:
  * The protected branch's first-parent chain (`--base`, default main) is the humans' history. A
    commit on it under the machine identity (`gp-agent@users.noreply.github.com`) means agent work
    reached the protected branch without a pull request a human merged.
  * The work under review -- `base..HEAD`, exactly what a merge would add -- carries no AI
    attribution (`Co-Authored-By:` a model, "Generated with", badges, or an AI tool's own address
    as author or committer) and no identity nobody knows. Known identities are DERIVED from git:
    every author already on the base, plus the developer running the gate -- never an AI tool's
    address, even one the base history carries. The machine identity is allowed on a branch:
    automated commits, the CI issue agent's included, carry it. There is no hand-kept team list.

WHY EXECUTED, NOT GREPPED. The thing being protected is the history itself, so this runs `git log`.
In a tree with no repository it says CANNOT RUN and exits 2 -- never 0: a silent pass on an
uncheckable tree is not a pass.

TWO POPULATIONS, on purpose. The first-parent check reads the commits in `--range` (default: the
last 200 of HEAD) that sit on the base's first-parent chain. Attribution and identity read only
`base..HEAD`. A finding already merged into the protected branch cannot be fixed without rewriting
it, and a permanent red light is read as scenery; the check that matters runs on the branch, before
the merge, where `base..HEAD` is exactly the set the merge would add.

WHAT THIS GIVES UP, stated: AI attribution a human commits directly onto the protected branch is
outside `base..HEAD` and is not graded -- a person bypassing their own rule, with no agent involved.
A teammate whose very first commit arrives on someone else's branch is flagged until one of their
commits has merged.

Usage: test-commit-identity.py [--range A..B] [--base REF] [--owner-email EMAIL] [--self-test]
  Defaults: range = last 200 commits of HEAD; base = main (else master, else HEAD);
            owner email = git config user.email.
Exit: 0 clean - 1 violations - 2 cannot run.
"""
import subprocess, sys, pathlib, tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env                    # noqa: E402

# Forward-only: commits authored before the no-attribution rule existed (2026-09-22) are exempt.
# Grading history by a rule it never had produces findings nobody can act on. The exemption is
# COUNTED AND PRINTED, because an exemption nobody can see is indistinguishable from a pass.
AI_EPOCH = "2026-09-22"
AI_MARKERS = ("Co-Authored-By: Claude", "Co-authored-by: Claude", "Generated with [Claude",
              "\U0001F916 Generated", "Co-Authored-By: GPT", "Co-Authored-By: Cursor")
MACHINE = "gp-agent@users.noreply.github.com"
# An AI tool's own address as a commit's author or committer is AI attribution carried in the
# identity rather than the message: agent commits authored as the model's no-reply address reached
# a project's history with no trailer at all. Named here because the address IS the rule; add the
# one any other tool that commits in your project uses.
AI_EMAILS = ("noreply@anthropic.com",)


def sh(args, cwd=None):
    r = subprocess.run(args, capture_output=True, encoding="utf-8", errors="replace", cwd=cwd)
    return r.returncode, r.stdout.strip()


def _git(repo, *args, env_email=None, env_name=None, committer=None):
    cmd = ["git"]
    if env_email:
        cmd += ["-c", f"user.email={env_email}", "-c", f"user.name={env_name or 'x'}"]
    extra = {"GIT_COMMITTER_EMAIL": committer, "GIT_COMMITTER_NAME": "c"} if committer else None
    return subprocess.run(cmd + list(args), cwd=repo, capture_output=True, encoding="utf-8",
                          errors="replace", env=scrubbed_env(extra))  # a temp repo: never the graded one


def self_test() -> int:
    """Both polarities: the control must fire on a violation AND stay quiet on correct work.

    A check that fires on correct behaviour gets switched off; a check that only ever fires is
    never shown to be quiet. (a), (d), (e) and (j) must stay quiet; the rest must fire, and a case
    that names a message must print it -- a refusal for another reason proves nothing about it.
    """
    me = str(pathlib.Path(__file__).resolve())
    ai = AI_EMAILS[0]
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, build, want, said in (
            ("a: correct shape (a human on the protected branch, the machine on its own branch)", "ok", 0, ""),
            ("b: machine commit ON the protected branch's first-parent chain", "ff", 1, ""),
            ("c: a commit carrying AI attribution, on the branch under review", "ai", 1, ""),
            # The relaxation, proven rather than asserted: the same attributed commit, already
            # merged onto the protected branch, stays quiet. Written with the human's identity on
            # purpose -- with the machine's, the first-parent check would fire and the case would
            # pass for a reason that has nothing to do with what it tests.
            ("d: AI attribution already on the protected branch -- carried, not re-graded", "aimain", 0, ""),
            # The team case: a teammate's commit reached main through a merged PR; graded from
            # another developer's clone it must stay quiet, or the pre-push hook refuses every
            # push that developer makes.
            ("e: a teammate's commit merged into main, graded from another developer's clone", "teammerge", 0, ""),
            ("f: an identity nobody knows, on the branch under review", "stranger", 1, ""),
            # The identity half of AI attribution: no trailer, the model's own address.
            ("g: an AI tool's address as the AUTHOR, on the branch under review", "aiauthor", 1,
             "an AI tool's address"),
            ("h: an AI tool's address as the COMMITTER only, on the branch under review",
             "aicommitter", 1, "the committer is"),
            # The base already carries the address (carried, quiet) -- and it still does not make
            # the address a known human: the branch commit fires, and only the owner is known.
            ("i: the same AI address in the base history is still not a known identity", "aiknown",
             1, "1 known human identity"),
            ("j: an AI address already on the protected branch -- carried, not re-graded", "aibase", 0,
             "already on `main`"),
        ):
            repo = pathlib.Path(tmp) / build
            repo.mkdir()
            _git(repo, "init", "-q", "-b", "main")
            (repo / "f").write_text("a", encoding="utf-8")
            _git(repo, "add", "f")
            _git(repo, "commit", "-qm", "owner work", env_email="owner@x", env_name="O")
            if build in ("aiknown", "aibase"):
                (repo / "f").write_text("m", encoding="utf-8")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "merged long ago", env_email=ai, env_name="Claude")
            if build in ("aiauthor", "aicommitter", "aiknown"):
                _git(repo, "switch", "-q", "-c", "work/1")
                (repo / "f").write_text("w", encoding="utf-8")
                _git(repo, "add", "f")
                if build == "aicommitter":
                    _git(repo, "commit", "-qm", "work", env_email="owner@x", env_name="O", committer=ai)
                else:
                    _git(repo, "commit", "-qm", "work", env_email=ai, env_name="Claude")
            elif build == "aibase":
                pass
            elif build == "ff":
                (repo / "f").write_text("b", encoding="utf-8")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "agent", env_email=MACHINE, env_name="gp-agent")
            elif build == "teammerge":
                _git(repo, "switch", "-q", "-c", "work/2")
                (repo / "f").write_text("t", encoding="utf-8")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "teammate work", env_email="mate@x", env_name="M")
                _git(repo, "switch", "-q", "main")
                _git(repo, "merge", "-q", "--no-ff", "-m", "Merge PR", "work/2",
                     env_email="owner@x", env_name="O")
            elif build == "stranger":
                _git(repo, "switch", "-q", "-c", "work/1")
                (repo / "f").write_text("s", encoding="utf-8")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "who is this", env_email="stranger@x", env_name="S")
            elif build == "aimain":
                (repo / "f").write_text("b", encoding="utf-8")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "owner work", "-m",
                     "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
                     env_email="owner@x", env_name="O")
            else:
                _git(repo, "switch", "-q", "-c", "work/1")
                (repo / "f").write_text("b", encoding="utf-8")
                _git(repo, "add", "f")
                msg = ["-qm", "agent"]
                if build == "ai":
                    msg += ["-m", "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"]
                _git(repo, "commit", *msg, env_email=MACHINE, env_name="gp-agent")
            r = subprocess.run([sys.executable, me, "--owner-email", "owner@x"], cwd=repo,
                               capture_output=True, encoding="utf-8", errors="replace",
                               env=scrubbed_env())
            ok = r.returncode == want and said in r.stdout
            cases.append((name, want, r.returncode, ok, said, r.stdout.strip().splitlines()[-1:]))

    bad = [c for c in cases if not c[3]]
    for name, want, got, ok, said, tail in cases:
        note = f" and `{said}` never printed" if want == got and not ok else ""
        print(f"  [{'ok  ' if ok else 'FAIL'}] want exit {want}, got {got}{note} -- {name}")
        if not ok and tail:
            print(f"         {tail[0]}")
    print(f"test-commit-identity --self-test {'FAIL' if bad else 'PASS'}: "
          f"{len(cases)} case(s), {len(bad)} wrong")
    return 1 if bad else 0


def main() -> int:
    argv = sys.argv[1:]
    no_git = missing_tool("git", "read the history to attest")
    if no_git:
        print(f"test-commit-identity CANNOT RUN: {no_git}. A history that cannot be read cannot "
              "be attested -- this is not a pass."); return 2
    if "--self-test" in argv:
        return self_test()
    rng = argv[argv.index("--range") + 1] if "--range" in argv else "HEAD"
    # Ask git, do not look for a `.git` directory beside this file: a tree that sits inside a
    # repository (a package in a subdirectory) is still inside it.
    rc, _ = sh(["git", "rev-parse", "--git-dir"])
    if rc != 0:
        print("test-commit-identity CANNOT RUN: not inside a git repository. A history that cannot "
              "be read cannot be attested -- this is not a pass."); return 2
    rc, _ = sh(["git", "rev-parse", "HEAD"])
    if rc != 0:
        print("test-commit-identity CANNOT RUN: no commits yet."); return 2

    if "--owner-email" in argv:
        owner = argv[argv.index("--owner-email") + 1]
    else:
        _, owner = sh(["git", "config", "user.email"])
    if not owner:
        print("test-commit-identity CANNOT RUN: no owner email (git config user.email empty and "
              "--owner-email not given). An identity rule with no identity to compare against "
              "checks nothing."); return 2

    # The humans' history is the PROTECTED BASE's first-parent chain, never HEAD's: on a work
    # branch HEAD's chain is the branch's own commits, and grading them as the protected history
    # makes correct work a violation.
    if "--base" in argv:
        base = argv[argv.index("--base") + 1]
    else:
        base = next((b for b in ("main", "master")
                     if sh(["git", "rev-parse", "--verify", "--quiet", b])[0] == 0), "HEAD")
    _, fp = sh(["git", "log", "--first-parent", "--format=%H", base, "-n", "200"])
    first_parent = set(fp.splitlines())
    if not first_parent:
        print(f"test-commit-identity CANNOT RUN: base ref `{base}` has no commits -- there is no "
              "protected history to compare against."); return 2

    # What this work ADDS over the protected base. Derived from git, never from a list of SHAs to
    # forgive. On the base itself the set is empty, and that is PRINTED rather than passed quietly.
    _, added = sh(["git", "log", "--format=%H", f"{base}..HEAD"])
    ai_pop = set(added.splitlines())

    # Known humans: every author already on the protected branch, plus the person running the gate.
    # An AI tool's address is never one of them, whatever the base history carries.
    _, known_raw = sh(["git", "log", "--format=%ae", base])
    known = {e for e in set(known_raw.splitlines()) | {owner}
             if e and e != MACHINE and e.lower() not in AI_EMAILS}

    _, log = sh(["git", "log", "--format=%H%x00%ae%x00%ce%x00%aI%x00%B%x1e", rng, "-n", "200"])
    bad = []
    n = 0
    pre_epoch = 0
    carried = 0
    for entry in log.split("\x1e"):
        if not entry.strip():
            continue
        n += 1
        sha, email, cemail, adate, body = (entry.strip("\n").split("\x00") + ["", "", "", ""])[:5]
        ai_identity = [(role, e) for role, e in (("author", email), ("committer", cemail))
                       if e.lower() in AI_EMAILS]
        ai_attributed = bool(ai_identity) or any(m in body for m in AI_MARKERS)
        if ai_attributed and sha not in ai_pop:
            carried += 1
            ai_attributed = False
        if ai_attributed and adate[:10] < AI_EPOCH:
            pre_epoch += 1
            ai_attributed = False
        if ai_attributed and ai_identity:
            role, who = ai_identity[0]
            bad.append(f"{sha[:9]} carries AI attribution in its identity: the {role} is `{who}`, "
                       "an AI tool's address -- commit as the developer or as the machine account")
        elif ai_attributed:
            bad.append(f"{sha[:9]} carries AI attribution -- no `Co-Authored-By` with a model, no "
                       "\"Generated with\", no badges, in commits or anywhere else")
        if sha in first_parent:
            if email == MACHINE:
                bad.append(f"{sha[:9]} machine identity on the FIRST-PARENT chain -- agent work "
                           "reached the protected branch as a human's history. It should have "
                           "arrived as a pull request a human merged")
        elif sha in ai_pop and email != MACHINE and email not in known \
                and email.lower() not in AI_EMAILS:
            bad.append(f"{sha[:9]} unknown identity `{email}` on the work under review -- not the "
                       "machine account and not anyone with a commit on the protected branch; an "
                       "agent must commit as the developer or as the machine, never as a stranger")

    for b in bad:
        print(f"  FAIL {b}")
    exempt = (f", {pre_epoch} pre-{AI_EPOCH} AI-attributed commit(s) exempt" if pre_epoch else "")
    inherited = (f", {carried} AI-attributed commit(s) already on `{base}` and outside this "
                 f"branch's scope" if carried else "")
    scope = (f"attribution scope {base}..HEAD = {len(ai_pop)} commit(s)" if ai_pop else
             f"attribution scope {base}..HEAD is EMPTY -- HEAD adds nothing over `{base}`, so the "
             f"attribution half graded nothing HERE; it grades on the branch, before the merge")
    print(f"test-commit-identity {'FAIL' if bad else 'PASS'}: {n} commit(s), {len(bad)} "
          f"violation(s) [identity population {rng}; {scope}; owner chain = first-parent of "
          f"{base}; {len(known)} known human identit{'y' if len(known) == 1 else 'ies'} derived from "
          f"`{base}`{exempt}{inherited}]")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
