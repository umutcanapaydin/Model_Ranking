# Installing DevFlow

One package for every OS. Only the way you get the tools differs: **Windows** below, or **macOS /
Linux** after it. Then the **common steps**, the same everywhere — in Git Bash on Windows, in a
terminal elsewhere. Every developer who clones a DevFlow project needs the tools; the common steps
run once per project, except the ones marked *every clone*.

| Tool | Why DevFlow needs it |
|---|---|
| git and bash | every script and the pre-push gate are bash; on Windows that is Git Bash |
| Python ≥3.11 | DevFlow's own tooling — the records validator, the conformance suite, the guards that read each tool call — is Python on every stack, whatever the product is written in |
| GNU make | every command is a make target, and the post-edit hook runs `make check-fast` |
| gh, the GitHub CLI | `make labels` and the draft pull requests the skills open. Without it, the common steps say what to do instead |
| gitleaks | `make secrets`, a leg of `make gate`, which runs before every push |

## Windows

Windows 10 or 11, working in **Git Bash**: every command in this file after the installs runs there,
never in PowerShell or cmd, because the Makefile's recipes are POSIX shell. Claude Code on Windows
runs its Bash tool and its hooks through Git Bash as well.

Install from PowerShell or Windows Terminal (winget ships with Windows 11 and current Windows 10),
then open a **new** Git Bash window so it reads the new PATH:

```powershell
winget install -e --id Git.Git
winget install -e --id Python.Python.3.12 --scope user
winget install -e --id ezwinports.make
winget install -e --id GitHub.cli
winget install -e --id Gitleaks.Gitleaks
```

The Python package is the python.org installer, and winget runs it with "add to PATH" on.

**Then turn off the Microsoft Store aliases for Python.** Windows puts a `python.exe` and a
`python3.exe` on PATH that open the Store instead of running anything. Settings → Apps → Advanced
app settings → App execution aliases: switch off both **App Installer** entries, `python.exe` and
`python3.exe`. The python.org installer provides `python` and `py` but no `python3`, so afterwards
`python3` is simply not found. That is correct: the Makefile and the guards fall back to `python`.
If no interpreter works at all, every guarded tool call is refused with
`BLOCKED: this guard cannot read the tool call -- no working python3 or python on PATH (see INSTALL.md).`

Verify, in the new Git Bash:

| Command | Expect |
|---|---|
| `git --version` | `git version 2.x.windows.N` |
| `command -v python` | a path under `AppData/Local/Programs/Python/` — **not** `WindowsApps` |
| `python -c 'import json, sys; print(sys.version)'` | `3.12.x` — this is the check the guards run |
| `command -v python3` | nothing, or a real interpreter — never a `WindowsApps` path |
| `make --version` | `GNU Make 4.4.1` |
| `gh --version`, then `gh auth login` | `gh version 2.x`, logged in to the host your repository is on |
| `gitleaks version` | `8.x` |

What you do **not** have to do on Windows:

- **Symlinks.** `CLAUDE.md` is a one-line file, `@AGENTS.md`, so it loads the house rules whatever
  `core.symlinks` says.
- **Line endings.** `.gitattributes` checks out `*.sh`, `.githooks/*`, the `Makefile`, `*.mk` and
  `.devflow-stack` with LF on every OS, whatever `core.autocrlf` says.
- **The console code page.** The Makefile exports `PYTHONUTF8=1` and `.claude/settings.json` sets it
  for the hooks, so a cp1254 or cp1252 console no longer garbles a file or crashes a script. To run
  a script by hand outside `make`, add it to your shell once: `echo 'export PYTHONUTF8=1' >> ~/.bashrc`.
- **The venv layout.** A Windows venv keeps its interpreter in `.venv/Scripts/`; the Makefile looks
  there.

Prefer WSL2? Follow the Linux steps inside the distribution and keep the clone on its filesystem.

## macOS / Linux

**macOS**, with [Homebrew](https://brew.sh):

```bash
xcode-select --install                   # git, make and bash (the Command Line Tools)
brew install python@3.12 gh gitleaks
```

The Command Line Tools' own `python3` is older than 3.11: the Makefile skips it and finds
`python3.12`, and the guards can still use it. Without the Command Line Tools, `/usr/bin/python3` is
a stub that only offers to install them, and the guards refuse every call until a real Python is on
PATH.

**Debian / Ubuntu** (Ubuntu 24.04 or later, Debian 13 or later):

```bash
sudo apt update
sudo apt install -y git make python3 python3-venv gh gitleaks
```

Older releases: Ubuntu 22.04 ships Python 3.10, so add `python3.11 python3.11-venv`; neither it nor
Debian 12 packages gitleaks — take the binary from its releases page,
<https://github.com/gitleaks/gitleaks/releases>.

Verify:

| Command | Expect |
|---|---|
| `git --version` | any recent git |
| `python3.12 --version` (or `python3.11`, `python3`) | 3.11 or later |
| `make --version` | GNU Make — the 3.81 macOS ships works |
| `gh --version`, then `gh auth login` | `gh version 2.x`, logged in |
| `gitleaks version` | `8.x` |

## Common steps — Stage 0

In Git Bash (Windows) or a terminal (macOS, Linux), at the repository root.

1. **Get the files.** An existing repository: follow
   [Installing into an existing repository](#installing-into-an-existing-repository) below, then
   come back to step 2. A brand-new project — `<tag>` is the DevFlow version you install:

   ```bash
   git init -b main my-project && cd my-project     # or clone your new, empty repository
   git remote add devflow https://github.com/SADCAIVibe/DevFlow.git
   git fetch devflow --tags
   git archive <tag> | tar -xf -
   ```

   The `devflow` remote stays: `UPGRADING.md` applies the next version from it.
2. **`/setup-project`**, in Claude Code. Nine questions, each with its reason and default. It writes
   `docs/project-brief.md`, the product's stack to `.devflow-stack` and, for a product in another
   language, the paths you name to `.language-allow`. It commits them on a branch and opens a draft
   pull request; without `gh`, it pushes the branch and hands you the compare URL to open the draft
   yourself. Merging it is you signing the choices.
3. Name the project in `pyproject.toml`.
4. `make install` — *every clone*: the venv, DevFlow's tooling and the project; it records the
   installed version in `.gp/installed`.
5. `make hooks` — *every clone*: `make gate` runs before every push. Where GitHub Actions do not
   run, this is the only gate between a change and the remote, and `make bootstrap-check` fails
   without it unless the brief records that both Actions and branch protection work here.
6. `make labels` — once per repository: every lifecycle skill keys on the labels in
   `.agents/rules/issues.md`, and a fresh repository has none of them. Without `gh` it prints the
   table of labels to create and exits 2: create them by hand on the repository's Labels page.
7. A stack other than `python`: bind its legs in `stack.mk`
   ([Binding another stack](#binding-another-stack), below).
8. Branch protection on the default branch (`docs/branch-protection.md`), if the brief says the
   repository can have it.
9. `make check-fast`, then `make check` — both green. `check-fast` runs the legs of `check` side by
   side and names every one that fails; `check` runs them in order and is the merge gate.
10. `make bootstrap-check` until it is green, then `/plan-milestone`.

## Installing into an existing repository

Your repository already has code and history, perhaps a README and a `CLAUDE.md` of its own. DevFlow's
files are added beside yours and **nothing of yours is overwritten**: every path both sides have is
listed first, and you decide it by the rule below. Work on a branch; the owner merges it.

```bash
git switch -c setup/devflow
git remote add devflow https://github.com/SADCAIVibe/DevFlow.git
git fetch devflow --tags
```

**Dry run — every DevFlow path you already have.** It writes nothing:

```bash
git ls-tree -r --name-only <tag> | while IFS= read -r f; do [ -e "$f" ] && echo "COLLIDES  $f"; done
```

Each line it prints needs the rule for that path, in the table below. Then copy **only the paths you
do not have**, and stage them by path:

```bash
new=$(git ls-tree -r --name-only <tag> | while IFS= read -r f; do [ -e "$f" ] || echo "$f"; done)
[ -n "$new" ] && git archive <tag> $new | tar -xf -
git add $new
```

For each colliding path, `git show <tag>:<path>` prints DevFlow's copy.

| Path | Rule |
|---|---|
| `README.md` | **Merge.** Your project's title and description stay on top; DevFlow's README follows, from "Your first question, before any code" down. `AGENTS.md` sends every new agent to the README first, so that part has to stay. |
| `.gitignore` | **Concatenate:** yours, then DevFlow's — `git show <tag>:.gitignore >> .gitignore`. A duplicate line is harmless. Commit it before anything else, or the venv and caches get tracked. |
| `src/` (and `tests/`) | **Keep yours where it is.** DevFlow's `src/app/` and its test files join beside your code — the copy above already added each one you did not have — and a file at the same path stays yours. Nothing moves. On the `python` stack, lint, typecheck and test grade all of `src/` and `tests/`, yours included; on another stack, `stack.mk` decides what is graded. |
| `CLAUDE.md` | **Move its content, then take DevFlow's.** What yours says goes into `AGENTS.md` §1–§2, the project-specific part (the 150-line cap applies); then `git show <tag>:CLAUDE.md > CLAUDE.md`. Its whole content is `@AGENTS.md`, and `conformance/test-claude-md.py` fails anything else. An `AGENTS.md` of your own: the same merge, into §1–§2. |
| `.install-lock` | **Take DevFlow's, unchanged — never regenerate it from your tree.** It records how many files each DevFlow directory shipped with; your own files only add to those counts, and `make install-check` fails only on fewer. A `.install-lock` already in your repository means DevFlow is installed here: this is an upgrade — stop, and follow `UPGRADING.md`. |
| `docs/decisions.md` | **DevFlow's universal decisions first, yours after them.** `make bootstrap-check` requires D-001..D-007; your own ADRs keep their ids, by the reconciliation recipe in its P-001. |
| `Makefile`, `pyproject.toml` | **Take DevFlow's, then carry yours over.** They are the gate and its tooling. Your make targets go into `stack.mk` (the Makefile includes it) or into the Makefile; a Python project's `[project]` table and dependencies go into DevFlow's `pyproject.toml`, keeping its `dev` extra and its `[tool.*]` sections. |
| `.github/workflows/` | **A human's part** — an agent never edits workflows. Keep yours; a human adds DevFlow's `ci.yml` beside them, under another name if yours is taken. |
| anything else | Keep yours, read DevFlow's, merge by hand. |

A file of yours at a path that `INSTALL-MANIFEST.md` lists as GP-INTERNAL fails `make install-check`
(M2): rename yours. Then commit on `setup/devflow` — the new files and each merged one, by path —
and continue at step 2 of the common steps. `/setup-project` derives *adopted* from the code already
in the tree, and `docs/codex-audit.md` records what exists before any wave changes it.

## Binding another stack

`.devflow-stack` names the product's stack in one line. It ships as `python`, and `/setup-project`
question 9 writes it. On `python`, `make lint`, `make typecheck`, `make test` and `make deps` run
ruff, mypy, pytest and pip-audit. On any other value, those four targets run the commands bound in
`stack.mk` — a file you write at the repository root, which DevFlow never ships and never overwrites:

| Variable | Runs as |
|---|---|
| `STACK_LINT` | `make lint` |
| `STACK_TYPECHECK` | `make typecheck` |
| `STACK_TEST` | `make test` |
| `STACK_DEPS` | `make deps`, after the pip-audit of DevFlow's own tooling |

A variable left unbound **fails** its target with a line starting `BIND ME:` that names the
variable, the stack and this file — a red leg, never a quiet pass. Everything else stays as it is:
DevFlow's own tooling is Python on every stack — `pyproject.toml`, the records validator, the
conformance suite, and the dependency checks of that tooling — so the Python prerequisite above
holds whatever the product is written in. Two things the binding does not reach:

- **CI.** The `test` job in `.github/workflows/ci.yml` runs ruff, mypy and pytest directly, so on
  another stack it grades DevFlow's Python scaffold only. Running the product's legs in CI — a macOS
  runner for an iOS app — is a workflow change, and a human's part.
- **The version-stamped health check (L.7).** `make bootstrap-check` checks `/health` on `python`
  only; on another stack it warns *bind L.7 for your stack*. The rule is the same everywhere: the
  running artefact reports the build it was made from — for an app, the build number it shows, set
  from the commit at build time. Record how you bind it with `/log-decision`, or refuse it in
  `docs/refusals.md` with the reason.

**Example — a Swift/iOS product.** `.devflow-stack` holds `swift`, and `stack.mk`:

```make
# stack.mk -- the legs of the swift stack. The Makefile includes this file (INSTALL.md).
SCHEME      ?= MyApp
DESTINATION ?= platform=iOS Simulator,name=iPhone 16

STACK_LINT      = swiftlint lint --strict
# make check-fast runs the legs side by side: two xcodebuilds sharing one DerivedData lock it,
# so each leg builds into its own directory under the ignored build/.
STACK_TYPECHECK = xcodebuild build -scheme $(SCHEME) -destination '$(DESTINATION)' -derivedDataPath build/dd-typecheck -quiet
STACK_TEST      = xcodebuild test -scheme $(SCHEME) -destination '$(DESTINATION)' -derivedDataPath build/dd-test -quiet
# No local advisory audit covers Swift packages the way pip-audit covers PyPI. Refused, with the
# reason, in docs/refusals.md R-1 (Dependabot alerts on the repository instead) -- the leg says so.
STACK_DEPS      = echo "deps: refused for swift -- docs/refusals.md R-1"
```

**On Windows, `xcodebuild` cannot run, and neither can an iOS `swift` build** — both need macOS. A
Windows developer on such a project gets a red gate for those legs: `make check-fast` after every
edit, `make check`, and `make gate` before every push. There are two ways out, and both are recorded:

- **A human pushes past it:** `git push --no-verify`, with a `bypass` row in
  `docs/control-events.csv` naming the leg and the reason. An agent never does this. The post-edit
  hook stays red on every edit, so this suits an occasional push, not someone who works on Windows
  every day; and three rows naming the same control put that control under review.
- **Bind the leg to skip on Windows only, with a recorded reason:** an ADR (`/log-decision`) naming
  the leg, the OS, and where the leg still runs before every merge — a macOS clone's pre-push, a
  macOS CI job — and a skip line that cites it, in place of the `STACK_TEST` line above:

  ```make
  ifeq ($(OS),Windows_NT)
  STACK_TEST = echo "SKIPPED test on Windows: xcodebuild needs macOS -- D-104"
  else
  STACK_TEST = xcodebuild test -scheme $(SCHEME) -destination '$(DESTINATION)' -derivedDataPath build/dd-test -quiet
  endif
  ```

  If nothing runs the leg before a merge, this is not a skip, it is a removed gate: do not bind it.
