#!/usr/bin/env python3
"""The range gate — condition C-2 of the checkpoint lane, and P-4 from the field.

THE RULE IN ONE SENTENCE: no commit may be mistaken for the owner's (V4C-64).

Concretely, on the milestone's commit range:
  - every commit on main's FIRST-PARENT chain carries the owner's identity and NO GP-Agent trailer
  - every other commit (work-branch checkpoints) carries the machine identity AND the trailer
  - the two cross-cases both refuse: owner-identity+trailer (an agent wearing the owner's name --
    the exact field precedent: twelve commits, one leaked identity) and machine-identity-without-
    trailer (an unattributable agent commit)

WHY EXECUTED, NOT GREPPED. The previous git-authority check scanned PROSE. This one runs `git log`,
because the thing being protected is the history itself. It ships to projects and runs there; in a
tree with no `.git` it says CANNOT RUN and exits 2 -- never 0 (a silent pass on an uncheckable tree
is the disease).

TB-098/TB-099 (Increment 18, instrument repair — GPF-002, this FILE). Two defects, both shipped
to projects, both of the shape this increment exists to remove: the control's declared subject and
its actual subject differed.

  TB-098  The docstring says "main's FIRST-PARENT chain"; the code derived that chain from `HEAD`.
          On a work branch — the state the checkpoint lane MANDATES — HEAD's first-parent chain IS
          the agent's checkpoints, so the gate reported FAIL on perfectly correct behaviour. Fixing
          it by defaulting the RANGE to main would have been wrong in the other direction: the
          population would then exclude the work-branch checkpoints and the rule's second half
          (machine identity + trailer) would grade nothing. So: the POPULATION is `--range`
          (default HEAD, everything we are asked about) and the OWNER'S CHAIN is `--base`
          (default main, the protected ref). Both are printed, because a control that does not say
          what it graded is how 18-B shipped twice.

  TB-099  It detected the repository as `cwd/.git`. GP's own packages are subdirectories, so inside
          them the gate said CANNOT RUN and GP has never once attested its own history. Now asks
          git. A tree with no repository at all is still NOT-EVALUABLE — that part was right.

A21 REVIEW, DISCHARGED (v6.0; friction-ledger §5 — the same control waived three times is a review
of the CONTROL). THIS RELAXES A CONTROL, so it says what it gave up and what now catches it.

What was wrong: the AI-attribution half graded HEAD's last 200 commits, so `dcb467d` — attributed,
merged into `main`, unfixable without rewriting a protected branch — failed on every push, for
everyone, for as long as 200 commits take to age out. On a repository that moves 200 commits in
months, that is a permanent red light, and a permanent red light is read as scenery. It became
unignorable the day the harness was installed at this root (A22): the post-edit hook refuses an
edit whenever the gate is red, so one unfixable finding began blocking every edit in the repository
that authors the rule. Four `--no-verify` pushes were the measurement.

So the two halves now grade two POPULATIONS, because they were never asking the same question:

  * the IDENTITY half — machine identity on the protected branch's first-parent chain, a third
    identity anywhere — keeps the FULL range. It is the field precedent (twelve commits, one
    leaked identity) and it has never once produced a finding nobody could act on.
  * the AI-ATTRIBUTION half grades only what the work under review ADDS: `base..HEAD`. Forward-only
    was always this rule's intent — `AI_EPOCH` is a date straining to express it — and a branch
    diff expresses it structurally instead of by calendar.

WHAT THIS GAVE UP, AND WHAT CATCHES IT NOW. AI attribution committed directly onto the protected
branch is outside the attribution half's population and is not graded there. Two things cover that
lane: the identity half still fires on an agent commit reaching the first-parent chain, and the
check that matters runs on the BRANCH, before the merge — where `base..HEAD` is exactly the set of
commits the merge would add. A gate grading a merge after the fact never stopped anything; the one
before it does. What is NOT covered: the owner, on the protected branch, committing AI attribution
by hand. That is a human bypassing their own rule with no agent involved, and it was the one shape
this control was never the answer to.

Usage: test-commit-identity.py [--range A..B] [--base REF] [--owner-email EMAIL]
  Defaults: range = last 200 commits of HEAD; base = main (else master, else HEAD);
            owner email = git config user.email.
Exit: 0 clean · 1 violations · 2 cannot run.
"""
import subprocess, sys, pathlib, tempfile

# The no-AI-attribution rule arrives with v6.0. FORWARD-ONLY, for the reason C1c had to learn
# twice: grading history by an instrument history never had produces findings nobody can act on,
# and a report full of them teaches its reader to skip it. 24 commits in this repository predate
# the rule and carry the trailer; they are exempt and the exemption is COUNTED AND PRINTED,
# because an exemption nobody can see is indistinguishable from a pass.
AI_EPOCH = "2026-09-22"
AI_MARKERS = ("Co-Authored-By: Claude", "Co-authored-by: Claude", "Generated with [Claude",
              "\U0001F916 Generated", "Co-Authored-By: GPT", "Co-Authored-By: Cursor")
MACHINE = "gp-agent@users.noreply.github.com"
#: model_ranking (D-155 clause 2, independent review MAJOR-3). The identities an AGENT commits under in
#: this project: DevFlow's CI machine account and the local lane's Claude Code identity. The owner
#: ruled that agent commits keep the `GP-Agent:` / `GP-Task:` trailers (V4C-64) while carrying no AI
#: attribution, so a branch commit under one of these identities without the trailer is a finding.
AGENT_EMAILS = {MACHINE, "noreply@anthropic.com"}


def sh(args, cwd=None):
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip()



def _git(repo, *args, env_email=None, env_name=None):
    cmd = ["git"]
    if env_email:
        cmd += ["-c", f"user.email={env_email}", "-c", f"user.name={env_name or 'x'}"]
    return subprocess.run(cmd + list(args), cwd=repo, capture_output=True, text=True)


def self_test() -> int:
    """Both polarities, because TB-098 was a control that fired on CORRECT behaviour.

    The falsification registry proves a control FIRES. Nothing proved this one does not OVER-fire,
    and that is exactly how it shipped grading the checkpoint lane's mandated output as a violation.
    Case (a) is that regression; (b) and (c) keep the firing half honest.
    """
    me = str(pathlib.Path(__file__).resolve())
    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, build, want in (
            ("a: correct shape (owner on the protected branch, agent on its own branch)", "ok", 0),
            ("b: agent commit ON the protected branch's first-parent chain", "ff", 1),
            # model_ranking (D-155 clause 2): the owner kept the trailer, so this case INVERTS here.
            ("c: an agent branch commit with NO GP-Agent trailer (D-155 keeps it)", "notrailer", 1),
            ("d: a commit carrying AI attribution, on the branch under review", "ai", 1),
            # A21, and it is the RELAXATION, so it is proven rather than asserted: the same
            # attributed commit, already merged onto the protected branch, must stay quiet. Written
            # with the OWNER's identity on purpose -- with the machine's, the identity half would
            # fire and the case would pass for a reason that has nothing to do with what it tests.
            ("e: AI attribution already on the protected branch -- carried, not re-graded", "aimain", 0),
            ("f: the local agent identity on main after the D-999 anchor (a push that skipped a PR)", "anchor", 1),
        ):
            repo = pathlib.Path(tmp) / build
            repo.mkdir()
            _git(repo, "init", "-q", "-b", "main")
            (repo / "f").write_text("a")
            _git(repo, "add", "f")
            _git(repo, "commit", "-qm", "owner work", env_email="owner@x", env_name="O")
            if build == "ff":
                (repo / "f").write_text("b")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "agent", "-m", "GP-Agent: checkpoint-lane",
                     env_email=MACHINE, env_name="gp-agent")
            elif build == "anchor":
                _, first = sh(["git", "rev-parse", "HEAD"], cwd=repo)
                (repo / ".owner-identity").write_text(f"owner_email: owner@x\nd999_anchor: {first}\n")
                (repo / "f").write_text("b")
                _git(repo, "add", "f", ".owner-identity")
                _git(repo, "commit", "-qm", "agent", "-m", "GP-Agent: local-lane",
                     env_email="noreply@anthropic.com", env_name="Claude")
            elif build == "aimain":
                (repo / "f").write_text("b")
                _git(repo, "add", "f")
                _git(repo, "commit", "-qm", "owner work", "-m",
                     "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
                     env_email="owner@x", env_name="O")
            else:
                _git(repo, "switch", "-q", "-c", "work/1")
                (repo / "f").write_text("b")
                _git(repo, "add", "f")
                msg = ["-qm", "agent"]
                if build != "notrailer":
                    msg += ["-m", "GP-Agent: issue-agent"]
                if build == "ai":
                    msg += ["-m", "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"]
                _git(repo, "commit", *msg, env_email=MACHINE, env_name="gp-agent")
            r = subprocess.run([sys.executable, me, "--owner-email", "owner@x"],
                               cwd=repo, capture_output=True, text=True)
            cases.append((name, want, r.returncode, r.stdout.strip().splitlines()[-1:]))

    bad = [c for c in cases if c[1] != c[2]]
    for name, want, got, tail in cases:
        print(f"  [{'ok  ' if want == got else 'FAIL'}] want exit {want}, got {got} -- {name}")
        if want != got and tail:
            print(f"         {tail[0]}")
    print(f"test-commit-identity --self-test {'FAIL' if bad else 'PASS'}: "
          f"{len(cases)} case(s), {len(bad)} wrong")
    return 1 if bad else 0


def _declared_identity() -> dict:
    """`key: value` rows from the repository's committed `.owner-identity`, if it has one."""
    _, top = sh(["git", "rev-parse", "--show-toplevel"])
    f = pathlib.Path(top or ".") / ".owner-identity"
    rows: dict = {}
    if f.is_file():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and ":" in line:
                k, _, v = line.partition(":")
                rows[k.strip()] = v.strip()
    return rows


def main() -> int:
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()
    rng = argv[argv.index("--range") + 1] if "--range" in argv else "HEAD"
    # TB-099: ask git, do not look for a `.git` directory beside us. A package that sits inside a
    # repository is still inside it; the old test made GP exempt from its own identity rule.
    rc, _ = sh(["git", "rev-parse", "--git-dir"])
    if rc != 0:
        print("test-commit-identity CANNOT RUN: not inside a git repository. A history that cannot "
              "be read cannot be attested -- this is not a pass."); return 2
    rc, _ = sh(["git", "rev-parse", "HEAD"])
    if rc != 0:
        print("test-commit-identity CANNOT RUN: no commits yet."); return 2

    # model_ranking (D-155): the owner is DECLARED in a committed `.owner-identity`, because this
    # clone's git config is the agent's own identity. `--owner-email` still overrides.
    declared = _declared_identity()
    anchor = declared.get("d999_anchor", "")
    if "--owner-email" in argv:
        owner = argv[argv.index("--owner-email") + 1]
    elif declared.get("owner_email"):
        owner = declared["owner_email"]
    else:
        _, owner = sh(["git", "config", "user.email"])
    if not owner:
        print("test-commit-identity CANNOT RUN: no owner email (git config user.email empty and "
              "--owner-email not given). An identity rule with no identity to compare against "
              "checks nothing."); return 2

    # TB-098: the owner's history is the PROTECTED BASE's first-parent chain, never HEAD's. On a
    # work branch HEAD's chain is the agent's own checkpoints, and grading them as the owner's
    # history made the lane's correct output a violation.
    if "--base" in argv:
        base = argv[argv.index("--base") + 1]
    else:
        base = next((b for b in ("main", "master")
                     if sh(["git", "rev-parse", "--verify", "--quiet", b])[0] == 0), "HEAD")
    _, fp = sh(["git", "log", "--first-parent", "--format=%H", base, "-n", "200"])
    first_parent = set(fp.splitlines())
    if not first_parent:
        print(f"test-commit-identity CANNOT RUN: base ref `{base}` has no commits -- there is no "
              "owner history to compare against."); return 2

    # A21: the attribution half grades only what this work ADDS over the protected base. Derived
    # from git, never from a list of SHAs to forgive — an allowlist added to keep a report green is
    # what the ledger names as the wrong way to end this row. On the base itself the set is empty,
    # and that is PRINTED rather than passed quietly: an exemption nobody can see is
    # indistinguishable from a pass.
    after_anchor: set = set()
    if anchor:
        _, later = sh(["git", "rev-list", "--first-parent", f"{anchor}..{base}"])
        after_anchor = set(later.splitlines())
    _, added = sh(["git", "log", "--format=%H", f"{base}..HEAD"])
    ai_pop = set(added.splitlines())

    _, log = sh(["git", "log", "--format=%H%x00%ae%x00%aI%x00%B%x1e", rng, "-n", "200"])
    bad = []
    n = 0
    pre_epoch = 0
    carried = 0
    for entry in log.split("\x1e"):
        if not entry.strip():
            continue
        n += 1
        sha, email, adate, body = (entry.strip("\n").split("\x00") + ["", "", ""])[:4]
        # v6.0. The trailer half of this gate INVERTED. Under the checkpoint lane an agent commit
        # was REQUIRED to carry `GP-Agent:`, because withholding `push` was what kept agent work
        # separable and the trailer was what made it attributable. The lane is replaced: the agent
        # now works on a branch and opens a DRAFT pull request, so separability is structural, and
        # the methodology this merges with forbids AI attribution outright -- no `Co-Authored-By`,
        # no "Generated with", no badges, in commits, PR bodies, issues or comments.
        #
        # So a control that DEMANDED the trailer now demands the thing the rule forbids. Shipping
        # both would be a gate and a rule in the same tree saying opposite things, which is the
        # defect this package keeps measuring in other people's repositories.
        #
        # What survives unchanged is the property both versions protect: no commit may be mistaken
        # for the owner's, and the first-parent chain of the protected branch is the owner's.
        ai_attributed = any(m in body for m in AI_MARKERS)
        if ai_attributed and sha not in ai_pop:
            carried += 1
            ai_attributed = False
        if ai_attributed and adate[:10] < AI_EPOCH:
            pre_epoch += 1
            ai_attributed = False
        if sha in ai_pop and email in AGENT_EMAILS and "GP-Agent:" not in body:
            bad.append(f"{sha[:9]} is an agent commit (`{email}`) with no `GP-Agent:` trailer -- "
                       "D-155 clause 2 keeps the trailer on every agent commit (V4C-64)")
        if ai_attributed:
            bad.append(f"{sha[:9]} carries AI attribution -- no `Co-Authored-By` with a model, no "
                       "\"Generated with\", no badges, in commits or anywhere else")
        if sha in first_parent:
            if email in AGENT_EMAILS and sha in after_anchor:
                bad.append(f"{sha[:9]} agent identity `{email}` on the protected branch after "
                           "D-999 -- agent work reaches `main` only as a pull request the owner "
                           "merges; a rebase-merge or a direct push puts it here")
            elif email == MACHINE:
                bad.append(f"{sha[:9]} machine identity on the FIRST-PARENT chain -- agent work "
                           "reached the protected branch as the owner's history. It should have "
                           "arrived as a merged pull request the owner merged")
        else:
            if email not in AGENT_EMAILS and email != owner:
                bad.append(f"{sha[:9]} third identity `{email}` -- neither owner nor machine; "
                           "every commit must be one or the other")

    for b in bad:
        print(f"  FAIL {b}")
    exempt = (f", {pre_epoch} pre-{AI_EPOCH} AI-attributed commit(s) exempt" if pre_epoch else "")
    inherited = (f", {carried} AI-attributed commit(s) already on `{base}` and outside this "
                 f"branch's scope" if carried else "")
    scope = (f"attribution scope {base}..HEAD = {len(ai_pop)} commit(s)" if ai_pop else
             f"attribution scope {base}..HEAD is EMPTY — HEAD adds nothing over `{base}`, so the "
             f"attribution half graded nothing HERE; it grades on the branch, before the merge")
    print(f"test-commit-identity {'FAIL' if bad else 'PASS'}: {n} commit(s), {len(bad)} "
          f"violation(s) [identity population {rng}; {scope}; owner chain = first-parent of "
          f"{base}{exempt}{inherited}]")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
