---
record_type: review
id: fix-issue-505-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — fix-issue-505

**Reviewer:** Security-Reviewer subagent (light mode, run 1030; a deploy-gate control change that D-231 clause 2 pre-approves as tightening only)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-30
**Release range:** 0bc39ca..39f0829 (`5ce756f` red test, `39f0829` fix; cut from #501's head)
**Reviewed head:** 39f0829677bc6cf0d3bb7ce9cde8391a7a9b9580
**Risk tier:** HIGH (a deploy-gate policy change; a control change that must only tighten)

## Verdict
MINOR

The branch only tightens. All six ways from #505 are refused at 39f0829: an fsmonitor hook, a stat-clean index
entry, a filter in `.git/info/attributes`, `.git/info/exclude`, `core.excludesFile`, and a self-ignoring untracked
`.gitignore`. A forged index entry for a new file is also refused. I compared the old and the new listing on the real
tree against five heads, and they were identical. In the main tree, the only difference is the two files the owner's
local exclude list hides, which is what the owner-actions row says. Neither listing produced a false positive on a
normal tree: `.venv/`, `build/`, `*.db`, `.gp/`, the linked worktree's `.git` file and macOS case-folding all read
the same as before. The new comparison costs 0.13 to 0.48 s, against 0.14 to 0.20 s for the old one (1,370 files).

Two bypasses of the same class remain, and both behave the same at 0bc39ca, so they are not introduced here. The
first is an untracked nested checkout, made with a plain file write, which hides every file below it. Through
setuptools' package discovery and Python's `sitecustomize`, that becomes unreviewed code running in production after
a deploy the gate approved (M1). The second is `core.worktree`, which still redirects the comparison (M2). Both are
gate bypasses that stay green with no test: Escalate NOW (AGENTS.md section 3). I grade them MINOR, not BLOCKING,
because this change does not loosen either one and fixing #505's own list does not depend on them. That follows the
#493 precedent: pre-existing vectors were escalated and filed, and the fix still merged.

I worked in my own worktree `scratchpad/sec-505` at `39f0829` (detached), with its own venv (`make install`) and a
copy of `advisor.db` (D-174). For the old reading I swapped in 0bc39ca's `scripts/deploy_gate.py` by copy and
restored it by copy (`cmp` clean). The probes were throwaway pytest files that used the suite's fixtures, plus
scripts kept in `scratchpad/probes/`. In the main tree I ran only read-only git listings (`ls-files`, `cat-file`)
and wrote nothing.

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/deploy_gate.py:229 with :291-292 — an untracked nested checkout hides everything below it. For a
  directory that holds a `.git` entry, `ls-files --others` reports only `dir/`, and `changed_since` drops every entry
  that ends in `/`. A `.git` *file* (`gitdir: <repo>/.git`) is enough, so no `git init` is needed. The Write guard
  (`bash_guard.py --write`) returns 0 for `src/evil/.git`; only the Bash guard refuses the same write through a
  redirect. Probe at 39f0829: `src/sitecustomize/.git` plus `src/sitecustomize/__init__.py` gives `--check` exit 0
  and `--judge` for `fly deploy` exit 0. The same probe at 0bc39ca gives the same result. The chain to production:
  - `pyproject.toml` declares no package list, so setuptools' automatic src-layout discovery packs `sitecustomize`
    into the wheel (verified with `pip wheel`).
  - Dockerfile:15 copies `src`.
  - Python's `site` imports `sitecustomize` at every interpreter start, including uvicorn's in the image.

  D-231 clause 2 says the gate hashes "each tracked and untracked file", and the issue's Expected says "ignore rules
  the change can write". A `.git` file is one of those rules. Remedy: list a `dir/` entry from `--others` as a
  changed path unless a `.gitignore` committed at the head ignores it. That turns a nested checkout into a refusal.
  `.claude/worktrees/` then needs a committed ignore line. Alternatively, walk the tree directly, skipping only the
  root `.git` and committed-ignored directories. Add a test with a `.git` file. Escalate NOW.
- **M2** scripts/deploy_gate.py:972 and :291 — `core.worktree` redirects the comparison. The Bash guard allows
  `git config core.worktree <dir>` (rc 0). With it pointed at a clean linked worktree of the reviewed head:
  - `make deploy-check` (`--check`, whose root is `rev-parse --show-toplevel`, so the configured worktree) exits 0
    with a tracked edit and a new file in the real tree.
  - `--judge` (root is the cwd, :958) now catches the tracked edit, because `_differs` reads the real disk. That is
    an improvement on 0bc39ca, which passed both. But a change that only adds a file still exits 0, because
    `ls-files --others` lists the configured worktree.

  `make deploy-check` is the gate for a deploy the guard never sees, such as the owner's own `fly deploy` from a
  terminal (D-222). Remedy: run `_new_files`' git calls with `--work-tree=<root>`. In `--check`, refuse when
  `core.worktree` is set, or when the toplevel is not the directory that holds the `.git` git found. Escalate NOW,
  together with M1.
- **M3** docs/owner-actions.md:40 — the row's listing command
  (`git ls-files --others --exclude-standard --ignored -- .claude epb.html`) prints six files in the main tree, not
  the two the row means: `.claude/.DS_Store`, `.claude/RESUME.md`,
  `.claude/hooks/__pycache__/bash_guard.cpython-314.pyc`, `.claude/last-check.log`, `.claude/settings.local.json`
  and `epb.html`. Following "move each" would move the owner's local settings and the post-edit log out of the
  tree. The row's two-file claim is right: a read-only old/new comparison in the main tree against `421d7c8` differs
  in exactly `.claude/RESUME.md` and `epb.html`. Remedy: change the command to
  `git -C ~/Desktop/ILGAR/model_ranking ls-files --others --exclude-per-directory=.gitignore -- .claude epb.html`.
  I ran it read-only, and it prints exactly those two files.

### PASS
- The comparison no longer reads the index's stat data, fsmonitor, attribute filters, `info/exclude` or
  `core.excludesFile`. Each of these is held by a test: tests/unit/test_deploy_gate_505.py:25, :37, :51, :60, :68
  and :77. The reviewed head's tree comes from `brief_fields.verified_tree` (scripts/brief_fields.py:236-264), with
  the commit and every tree hashed. The ignore blobs come from `verified_blobs` (:267-285). `Unverified` subclasses
  `RuntimeError`, so `changed_since` returns None and refuses.
- **Ignore translation fidelity** (`_head_excludes`, scripts/deploy_gate.py:265-281). I ran a differential against
  `git ls-files --others --exclude-per-directory=.gitignore` with committed `.gitignore` files at three levels. The
  patterns covered anchoring, a middle slash, `**/x`, `x/**`, `a/**/b`, a trailing `/`, negation (including
  re-including a file under an ignored directory), escaped `#` and `!`, escaped and trailing spaces, character
  classes, `?`, and deeper-file precedence. Both sides agreed on all 22 files listed. The two differences are
  folder-name escaping (R3).
- Correctly refused, by probe: `src/` replaced by a symlink to an identical copy, a symlink retargeted, a tracked
  file deleted, `git mv src/app.py docs/app.md` (the deleted side is listed), and a forged `--cacheinfo` index entry.
- Mutants killed: b (executable bit), c (staged entries), d (nested scoping), g (`--exclude-standard` back).
- No new third-party import (`hashlib` and `tempfile` are stdlib). The exclude file is created 0600 in the per-user
  `TMPDIR` and unlinked in `finally`. The red test (`5ce756f`) was committed alone first. Both commits carry
  `GP-Agent: claude-code` / `GP-Task: issue-505` and no AI attribution. There is no edit under
  `.github/workflows/**`, `.claude/`, `.githooks/`, `pyproject.toml` or a lock.

## Gates passed
- [x] Secret scan green (`make secrets` at 39f0829, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief declares
  no HIGH paths)
- [x] SAST (`ruff check --select S` on scripts/deploy_gate.py and scripts/brief_fields.py: one pre-existing S101 at
  brief_fields.py:138, outside the range. `make conformance` at 39f0829: "conformance PASS: 33 test(s) derived from
  conformance/, 0 failing". Tests at 39f0829: `-k "deploy_gate or deploy or closure or brief"` 413 passed)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #505, a `core.fsmonitor` hook that reports nothing → scripts/deploy_gate.py:243-262 (bytes from disk);
  tests/unit/test_deploy_gate_505.py:25
- #505, a forged stat-clean index entry → scripts/deploy_gate.py:243-262; tests/unit/test_deploy_gate_505.py:37
- #505, a clean filter through `.git/info/attributes` → scripts/deploy_gate.py:256 (raw bytes hashed);
  tests/unit/test_deploy_gate_505.py:51
- #505, `.git/info/exclude` and `core.excludesFile` → scripts/deploy_gate.py:284-301 (`--exclude-from` only);
  tests/unit/test_deploy_gate_505.py:60, :68
- #505, an untracked self-ignoring `.gitignore` → scripts/deploy_gate.py:221-225 (the head's committed files only);
  tests/unit/test_deploy_gate_505.py:77
- D-231 clause 2, the head's committed `.gitignore` still counts, scoped to its folder →
  scripts/deploy_gate.py:265-281; tests/unit/test_deploy_gate_505.py:84, :110
- An index entry cannot take a file out of `--others` → scripts/deploy_gate.py:297-300;
  tests/unit/test_deploy_gate_505.py:101. A mode change → :127
- #505's Expected, "no ignore rules the change can write" → partly met: a written nested `.git` still hides files
  (M1)

## Risks queued
- **R1** tests/unit/test_deploy_gate_505.py — five mutants of the new hand-written comparison survive all 182
  deploy-gate tests. Three of them loosen the gate: (a) a symlink's target ignored, (k) a deleted tracked file not
  seen, and (e) negation dropped from the translated rules. The other two are (f) precedence reversed and (i) a
  submodule always "same". The real code gets (a) and (k) right by probe, but nothing holds them. The docstring's
  "a rename is both its sides (#506)" (scripts/deploy_gate.py:216-217) has no test in this stack. Remedy: one case
  each for a retargeted link, a deleted code file (and the code-to-record rename), a committed `!` re-include, and a
  deeper file overriding a shallower one.
- **R2** scripts/deploy_gate.py:243-262 — latent false positives. They fail closed, and this tree has no symlink,
  no submodule and no CRLF checkout (1,336 entries at 100644, 34 at 100755):
  - `str(path.readlink())` normalises `./app.py` to `app.py` and `../src/` to `../src`, so an unchanged link is
    listed (probe exit 1). Use `os.readlink`.
  - The executable test reads any `0o111` bit, where git reads `S_IXUSR`, so `chmod 654` is listed while
    `git diff` sees nothing.
  - On a `core.autocrlf=true` clone, a file with no eol attribute is listed.
  - `git -C <uninitialised submodule dir> rev-parse HEAD` answers with the parent's HEAD, so such a submodule
    always differs. A dirty submodule's working tree is no longer compared (only its HEAD is). That loosens the
    gate, but only in a repository that has gitlinks.
- **R3** scripts/deploy_gate.py:279 — the folder prefix is not escaped. A committed `we[ir]d/.gitignore` also
  ignores `weid/a.txt` and `werd/x/b.txt` (the gate hides them, git lists them). A folder named `#x` or `!x` turns
  its rules into a comment or a negation. No such folder exists at any head. Remedy: escape `\ * ? [ ! #` in `folder`.
- **R4** scripts/deploy_gate.py:307 (`_flagged`) and the other plain `git` calls — a configured `core.fsmonitor`
  hook still runs inside the gate. It ran 4 times during one `--check`. Its answer no longer changes the result, but
  a program the change configured runs inside the guard's deploy judgement. Remedy: use `_PLAIN_GIT` for every git
  call in the gate.
- **R5** `.gitignore` (committed) — `build/`, `env/`, `venv/`, `dist/` and `notes/` match at any depth. Under D-231
  they now decide what the gate counts, so a new file under `scripts/build/` or `src/app/build/` is not seen
  (probe exit 0 for `scripts/build/run.py`). This is by design. As hardening, the owner could anchor these patterns
  to the root (`/build/`).
