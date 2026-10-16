#!/usr/bin/env python3
"""The Bash guard: every Bash tool call, read as the shell splits it, judged one simple command at a time.

`.claude/settings.json` runs this as the PreToolUse hook for `Bash`, and with `--write` as the PreToolUse
hook for `Write`, `Edit` and `MultiEdit`, each after checking its sha256 against the pin written there
(`make guard-pin` rewrites both pins; INSTALL.md, "Changing the Bash guard"). The hook's JSON arrives on
stdin; exit 2 refuses the call with one `BLOCKED:` line on stderr, exit 0 allows it.

Until this file existed the guard was a set of regular expressions over the raw text. Measured in two
field projects over two weeks: every refusal it made on a deploy command was wrong (a commit message, an
issue comment, a heredoc, a self-test that mentioned the command), the commit message `... on main (#90)`
matched the push-main rule, a heredoc holding `git checkout -- .` matched the destructive rule, sixteen
refusals were `rm -rf` of the agent's own scratch directory, and the two evasions the field saw
(`a=xcodebuild; $a ...`, a reviewer switching to the Write tool) were both provoked by a wrong refusal.
A lexer reads the command the way the shell will: quoted text is data, a here-document's body is data,
and a rule looks only at the words in command position.

What it refuses, each in one simple command:
- refused: `git push` that forces (`-f`, `--force`, `--force-with-lease`, `--force-if-includes`, a `+ref`),
  mirrors, pushes every branch (`--all`, `--branches`), names `main`, `master` or `trunk` as the
  destination (`main`, `HEAD:main`, `heads/main`, `refs/heads/main`), or runs behind `xargs`;
- `git reset --hard`; `git clean -f`; `git checkout --`, `.`, `-f`, or a tree-ish followed by paths;
  `git switch -f` or `--discard-changes`; `git stash clear`; `git restore` without `--staged` or with
  `--worktree`. A git long option counts in any unique prefix, as git reads it;
- a skipped hook, refused: `--no-verify` (or a prefix of it git reads as it), `git commit -n`, and a `core.hooksPath`
  set on the command line (`-c`, `--config-env`); `git update-ref` naming `main`, `master` or `trunk`;
- a shell write to a secrets file by name (`.env`, `.env.<x>` but `.env.example`, `.env.sample` and
  `.env.template`, `<x>.env`, `.envrc`): a redirection, `tee`, or the destination of `cp`, `mv`, `install`
  or `ln` (with `-t`, every source's name too);
- `rm` both recursive and forced, and `find ... -delete`, unless every target is scratch: a `mktemp` result
  assigned earlier in the same command (`d=$(mktemp -d) && rm -rf "$d"`, or a path below it with no `..`), a
  worktree under `.claude/worktrees/`, or a path below `$TMPDIR` or the system temp directory (the session
  scratchpad lives there) that is no temp directory, lies in no git work tree, and holds or sits above none
  (the v7.1 upgrade security review's MAJOR-1: this project's work trees and review seats live under the temp
  directory). Each variable is replaced by what this text assigned it -- `$TMPDIR` unassigned by the guard's
  own -- and the path resolved where it lands, `..` and links followed; a variable it cannot know is no
  scratch (B1: `$TMPDIR/../..`, `"$TMPDIR/$unset"` and `TMPDIR=/x; rm -rf $TMPDIR` passed). A relative target
  is resolved from every directory the command may run in (WHERE, below) and must be scratch from each. A
  throwaway worktree is dropped with `git worktree remove [--force] <path>`, which is not refused;
- refused: `gh pr merge` and `gh pr ready` with flags anywhere (`gh -R a/b pr merge`, `gh pr -R a/b merge`),
  `gh api` on `/pulls/<n>/merge`, and `gh api` on `/protection` or `/rulesets` with a mutating method
  or a field (`-X PUT`, `--method delete`, `-f`, `-F`, `--input`, `--raw-field`);
- a declared deploy command (`Deploy commands:` in `docs/project-brief.md`) while `scripts/deploy_gate.py`
  refuses it: the governing tree is the git work tree of the directory the call runs in when it carries a
  brief, else the project root; the gate that judges it is always the project root's own --
  `$CLAUDE_PROJECT_DIR`, else the checkout this file lives in -- never the governing tree's (the v7.1
  upgrade security review's MAJOR-2: a cloned repository's script ran on the next `ls`); a project root
  with no `scripts/deploy_gate.py` refuses every call while a brief governs, never skips. The gate matches
  the declared words at command position, case-insensitively, by the program's basename: `FLY DEPLOY`,
  `fly  deploy`, `'fly' deplo'y'`, `/usr/local/bin/fly deploy`, `sudo fly deploy`, `bash -c 'fly deploy'`
  and `a=fly; $a deploy` are all the deploy; `echo 'fly deploy'` and `git commit -m 'fly deploy notes'`
  are not;
- a program word written as a pattern (`gi*`, `{git,ls}`), which could name anything;
- what an alias this text defines runs (`git config alias.x 'reset --hard'`, `git -c alias.x='!rm -rf /'`),
  judged as the git subcommand or the shell text it names, and the remote words of `ssh <host> <words>`,
  judged as a command from the home directory (the v7.1 upgrade security review's M1).

This project's own rules (model_ranking, carried over from its M21 guard in the DevFlow v7.1 upgrade):
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY, and `fly` behind `xargs` (D-185),
  whatever the deploy gate says: the hosted engine is deployed and destroyed by the owner only;
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run` (D-185);
- a write into the `.claude/` or `.githooks/` of any git work tree, the owner's hooks and settings (the M21
  closure security seat's S3): a redirection there; `rm`, `mv`, `tee`, `touch`, `chmod` and their kind on a
  path there; `cp`, `ln`, `install`, `rsync`, `ditto` or `dd` with a destination there (the last word, or
  `-t`/`--target-directory` for `cp`, `mv`, `ln` and `install`, or `of=` for `dd`); `sed -i` or `perl -i` on
  one; and `git rm`, `git mv`, `git checkout` or `git restore` naming one. Reading them is not refused. The
  one exception is v7.1's scratch rule: `rm` of a directory under `.claude/worktrees/<name>` (a worktree's
  own `.claude/` and `.githooks/` stay refused, below).
  A directory that holds them is refused too (#282): `rm -r`, and `mv` (`git rm`, `git mv`) of a source, whose
  path is a work tree's root with a `.claude/` or `.githooks/` or a directory above one (`rm -r .` at a root,
  `rm -r ..` from `ios/`, `mv ../<repo> x`); the directories below it are walked, links not followed, within
  WALK_S seconds and MAX_WALK directories, and one too large or unreadable to walk is refused.
  In a cluster of short options, `t` is `-t` only before any letter that takes a value (VALUED: `install
  -ostaff` names an owner); a `t` after one is doubt, and then every operand is judged a destination, as
  for `install -d` (the fixes review's round 3, M2).
  Which paths, exactly (`protected`; round 2's B1, as round 3's M1 left it): the path, `~` and variables
  expanded, is resolved from the directory the command runs in, links followed on its longest existing
  part. The work tree it lies in is the nearest directory above it that holds a `.git` entry, a file or a
  directory: this clone, a linked worktree, any other clone, or a worktree Claude Code made inside a
  repository's `.claude/worktrees/`. The path is refused when the directory directly below that work tree's
  root is named `.claude` or `.githooks`, in any case. Claude Code's own `~/.claude` is not refused, as no
  `.git` sits above it.
  Given `--write`, the guard judges the Write or Edit call's `file_path` instead: a secrets file by name
  (the shell rule's names), or a path `protected` refuses.
- The directories a command runs in (WHERE; `_linear`): when the text is only simple commands joined by
  `;`, `&&`, `||`, newlines and pipes, with no `cd` in a pipe or a substitution and each `cd`, `pushd` or
  `chdir` to a plain directory (no variable, substitution, glob, `-` or `~user`, and no `CDPATH` set), each
  command is judged from the directories it can run in: a `cd` that succeeds moves there, one that fails
  stays, and `&&` and `||` follow the status. Otherwise (a subshell, a group, a loop, `&`, `eval`, `source`,
  `popd`, a `cd` this cannot read) every directory a `cd` reached is kept, each `cd` taken from each of them
  (`_follow`), and a path is refused if it is protected from any of them. Past MAX_DIRS directories, the
  command is not read.

Where it looks: each command after `;`, `&&`, `||`, `|`, `|&`, `&`, a newline, `(`, `)`, `{` or `}`;
inside `$( )`, backticks, `<( )`, `${ }`, `$(( ))` and an unquoted here-document's body; past
assignments, shell keywords and the wrappers in WRAPPERS (after one, every later word is tried as the
program); inside `bash`, `sh`, `zsh`, `dash`, `ksh`, `csh`, `tcsh` or `fish` given `-c`, a script name, a
here-document or a here-string; and inside `eval`, `source`, `.`, `env -S` and `find -exec`. Text in
single quotes and a quoted here-document's body are data; a `#` that starts a word starts a comment. A
program named through a variable assigned a literal earlier in the same text (`a=git; $a push`) is read
as that program.

It refuses what it cannot read rather than reading it as data: an unclosed quote or substitution; a word
with `(` written against it; a `${(flags)...}`; a shell or `source` reading its commands from a pipe, a
file or stdin; a `-c` with no string; an input over MAX_INPUT characters; a payload that is not JSON; and
any call it has not finished judging within DEADLINE_S seconds (a timer thread writes the line and exits
2, where SIGALRM does not exist too; the M21 closure security seat's S2). A long call into C that holds the
interpreter runs to its end first; the hook's own `timeout` and `"onFailure": "block"` bound that case,
from Claude Code 2.1.295.

Not held, by class -- said here so nobody believes otherwise:
- a program named when the command runs: a variable set outside this text, an alias, a function, `hash`,
  a `PATH` holding a script of a guarded name; `xargs <deploy command>` whose subcommand comes on stdin;
- code another program runs: a script's contents (`bash x.sh`), `python -c`, `perl -e`, `node -e`,
  `awk`'s `system()`, `make` recipes, git hooks, git aliases set before this text, `ssh -o ProxyCommand=`;
  and git run by the project's deploy gate in a governing tree that is another repository, which reads that
  repository's own config (a `core.fsmonitor`, a filter) when a command matches a deploy its brief declares;
- a `mktemp` that fails: its variable is then empty, and `rm -rf "$d/sub"` removes `/sub`; and a `$TMPDIR`
  the shell holds other than the guard's own process does;
- a wrapper not in WRAPPERS, whose program is then read as an argument;
- a push to a destination git chooses itself: a bare `git push`, `git push origin HEAD` or `@`, an
  upstream, `push.default` or `remote.pushDefault` (from a checkout on main, each pushes main; branch
  protection on the remote is the control there, the M21 closure security seat's S4);
- a write into `.claude/` or `.githooks/` by a program this does not list (`python -c`, `git apply`, `tar`,
  an editor), through a path built when the command runs (`$(...)`, a glob), a hard link made before, or a
  directory reached by a `cd` this does not follow (one to a built path, through `CDPATH`, `cd -`, or
  repeated by a loop more than once);
- what the shell expands when the command runs, beyond the program word: `IFS`, history, globs and
  braces in arguments; syntax beyond POSIX-like shell.
Stdlib only, Python 3.11 or later.
"""

from __future__ import annotations

import codecs
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

#: The longest command this reads; a longer one is refused.
MAX_INPUT = 32768
#: How long the guard may take; past it, it refuses.
DEADLINE_S = 10.0
#: The directories the command may run in: the payload's `cwd`, then each a `cd` in it reaches (`_follow`,
#: `_linear`). Relative `rm` targets and written paths resolve from them.
WHERE: dict[str, list[str]] = {"dirs": []}
#: More directories than this, and the command is not read.
MAX_DIRS = 64
#: `name -> literal value` for assignments seen in this text, SCRATCH for a `mktemp` result, or UNKNOWN for any
#: other value (an assignment this text made, so the variable no longer holds what the environment gave it).
SCOPE: dict[str, object] = {}
SCRATCH = object()
UNKNOWN = object()
#: Whether this call may take `$TMPDIR` as the guard's own environment holds it, and a `mktemp` result as a new
#: directory (the v7.1 upgrade security review's B1). Not `$TMPDIR` when the text names `TMPDIR` other than to
#: expand it (`export`, `read`, `for TMPDIR in`) or runs `unset`; not `mktemp` when it defines a function or an
#: alias of that name.
TRUST: dict[str, bool] = {"TMPDIR": True, "mktemp": True}
TMPDIR_NAMED = re.compile(r"(?<![\w$])(?<!\$\{)TMPDIR\b|(?:^|[\s;&|(){}!`])unset\b")
MKTEMP_DEFINED = re.compile(r"\bmktemp\s*\(\s*\)|\bfunction\s+mktemp\b|\balias\b[^;&|\n]*\bmktemp=")
#: A variable as `_scratch` reads one: `$name` or `${name}` exactly; any other `${...}` form is not read.
REFERENCE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
#: How long, in all, one call may spend walking directories to find the work trees a target holds
#: (`_walk`), and how many directories; past either, the target is taken to hold one.
WALK_S = 4.0
MAX_WALK = 400_000
WALK: dict[str, float] = {"left": WALK_S}
#: The checkout this file lives in (`.claude/hooks/bash_guard.py` below its root): the project root when
#: `$CLAUDE_PROJECT_DIR` is not set, so the deploy gate is always the project's own (MAJOR-2).
GUARD_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#: Every word list in program position, for the deploy gate: `[program, arg, ...]`.
CANDIDATES: list[list[str]] = []

#: Words that run the command after them; every later word is tried as that command.
WRAPPERS = {"env", "command", "builtin", "time", "exec", "nohup", "nice", "sudo", "doas", "xargs", "timeout",
            "gtimeout", "caffeinate", "coproc", "noglob", "nocorrect", "-", "repeat", "function", "stdbuf",
            "setsid", "watch", "unbuffer", "script", "chronic", "ionice", "taskpolicy"}
#: Shell words a command follows on its line: `then git push` runs `git push`.
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "fi", "done", "esac", "[", "[["}
#: Builtins whose assignment-shaped arguments set variables.
SETTERS = {"export", "declare", "local", "typeset", "readonly"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "csh", "tcsh", "fish"}
#: A shell or `source` given one of these reads its commands from stdin.
STDIN_PATHS = {"-", "/dev/stdin", "/dev/fd/0", "/proc/self/fd/0"}
PROTECTED = {"main", "master", "trunk"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?=")
VARIABLE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
MKTEMP = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*g?mktemp\b")
#: This project's hosted-engine deploy script (D-185).
DEPLOY = "deploy_hosted_engine.sh"
#: The programs this guard reads; a program word written as a pattern is refused outright.
GUARDED = {"git", "rm", "gh", "eval", "source", ".", "find", "fly", "flyctl", DEPLOY, *SHELLS, *WRAPPERS, *SETTERS}
#: `gh` flags that take a value, so the value is not read as a subcommand word.
GH_VALUED = {"-R", "--repo", "--hostname", "-X", "--method", "-f", "--field", "-F", "--raw-field",
             "--input", "-H", "--header", "-q", "--jq", "-t", "--template", "-p", "--preview", "-b",
             "--body", "-B", "--body-file", "--title", "-m", "--subject", "-a", "--assignee", "-l",
             "--label", "-r", "--reviewer", "-A", "--author", "--match", "-c", "--comment", "--cache",
             "-e", "--editor", "-s", "--search", "-S", "--state", "-L", "--limit", "-M", "--milestone"}
GH_MUTATING = {"PUT", "PATCH", "POST", "DELETE"}

#: The owner's hooks and settings: the directories of these names at a work tree's root (the M21 closure
#: security seat's S3; `protected`).
OWNED = (".claude", ".githooks")
#: The commands that change the shell's directory, and the words that make a list one `_linear` cannot follow:
#: shell grammar, and builtins that run text or change the directory in ways this does not read.
DIR_CHANGES = {"cd", "pushd", "chdir"}
SHELL_GRAMMAR = {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "case", "esac", "select",
                 "function", "coproc", "!", "repeat", "foreach", "end"}
UNFOLLOWED = {"eval", "source", "popd"}
#: Programs that change each path they are given, and those that change only their destination.
CHANGES_EVERY = {"rm", "mv", "tee", "touch", "chmod", "chown", "chgrp", "truncate", "unlink", "rmdir", "shred", "mkdir"}
CHANGES_LAST = {"cp", "ln", "install", "rsync", "dd", "ditto"}
#: The programs whose `-t DIR` (`--target-directory`) is the destination; for any other, `-t` is not one.
TARGET_OPTION = {"cp", "mv", "ln", "install"}
#: Their short options that take a value (GNU's and BSD's): in a cluster, every letter after one is its value.
VALUED = {"install": set("BDfghlmMNoST"), "cp": {"S"}, "mv": {"S"}, "ln": {"S"}}
#: `fly` subcommands an agent may run: each reads, none changes the hosted engine (D-185).
READ_ONLY_FLY = {("version",), ("help",), ("status",), ("logs",), ("auth", "whoami"), ("apps", "list"),
                 ("releases",), ("machine", "list"), ("machine", "status"), ("machines", "list"),
                 ("scale", "show"), ("secrets", "list"), ("config", "show"), ("ips", "list"),
                 ("checks", "list"), ("volumes", "list")}

DESTRUCTIVE = "BLOCKED: destructive command (C.9, permission-matrix.md S5). Escalate to the owner instead."
HOLDS_OWNED = ("BLOCKED: `{path}` holds a git work tree's .claude/ or .githooks/, the owner's hooks and settings; "
               "removing or moving it removes them (#282, OWNER APPROVAL). To drop a throwaway worktree, use "
               "`git worktree remove <path>`.")
UNWALKED = ("BLOCKED: `{path}` is too large or unreadable to tell whether it holds a git work tree's .claude/ or "
            ".githooks/ (#282), so it is not removed or moved; name a smaller path.")
RESTORE = ("BLOCKED: `git restore` without --staged, or with --worktree, discards uncommitted work "
           "(permission-matrix.md S5). Revert in place, or use --staged to unstage only.")
PROTECTED_PUSH = ("BLOCKED: the agent never pushes the protected branch (AGENTS.md S3). Push YOUR branch and open a "
                  "draft PR; a human marks it ready and merges.")
NO_VERIFY = ("BLOCKED: `--no-verify` and a redirected `core.hooksPath` skip the gate a hook runs (AGENTS.md S3): "
             "a hook you skipped is a gate you removed. Fix what is red, or ask the owner.")
ENV_WRITE = "BLOCKED: writes to .env are denied per permission-matrix.md S6 (default-deny secrets)."
PROTECTED_REF = ("BLOCKED: the agent never moves or deletes the protected branch's ref (AGENTS.md S3): "
                 "the default branch is the human's.")
ENV_EXEMPT = {".env.example", ".env.sample", ".env.template"}
GH_MERGE = ("BLOCKED: a human marks a pull request ready and merges it, never the agent (AGENTS.md S3). "
            "Leave the draft for the owner.")
GH_PROTECTION = "BLOCKED: branch protection and rulesets are the owner settings (AGENTS.md S3). Propose the change and stop."
NOT_JSON = "BLOCKED: this guard cannot read the tool call -- the payload is not a JSON object."
GATE_MISSING = ("BLOCKED: deploy gate -- {tree} declares deploy commands in docs/project-brief.md and the project "
                "root {root} has no scripts/deploy_gate.py, so no command can be told from a deploy. Restore the "
                "script (INSTALL-MANIFEST.md); the guard never skips this check, nor runs another tree's gate.")
OWNERS = ("BLOCKED: .claude/ and .githooks/ hold the owner's hooks and settings; an agent does not write them "
          "(OWNER APPROVAL, the M21 closure security seat's S3). Propose the change instead.")
FLY = ("BLOCKED: `{shown}` may change the hosted engine, and only the owner runs that, in their own terminal "
       "(D-185, permission-matrix.md S3); an agent may run only the read-only subcommands.")
DEPLOY_SCRIPT = ("BLOCKED: the hosted engine is deployed by the owner, in their own terminal (D-185); an agent "
                 "may run the script with --dry-run only.")

#: Each git subcommand's long options, so a unique prefix is read as the option git reads it as.
GIT_LONG = {
    "push": ["--all", "--branches", "--mirror", "--tags", "--follow-tags", "--force", "--force-with-lease",
             "--force-if-includes", "--atomic", "--delete", "--dry-run", "--porcelain", "--prune", "--progress",
             "--push-option", "--quiet", "--verbose", "--set-upstream", "--thin", "--no-thin", "--receive-pack",
             "--exec", "--repo", "--recurse-submodules", "--signed", "--no-signed", "--verify", "--no-verify",
             "--ipv4", "--ipv6", "--no-force-with-lease", "--no-atomic"],
    "reset": ["--hard", "--soft", "--mixed", "--merge", "--keep", "--quiet", "--no-quiet", "--refresh",
              "--no-refresh", "--recurse-submodules", "--patch", "--intent-to-add", "--pathspec-from-file",
              "--pathspec-file-nul"],
    "restore": ["--worktree", "--staged", "--source", "--patch", "--quiet", "--progress", "--ours", "--theirs",
                "--merge", "--conflict", "--ignore-unmerged", "--ignore-skip-worktree-bits", "--recurse-submodules",
                "--overlay", "--no-overlay", "--pathspec-from-file", "--pathspec-file-nul"],
    "clean": ["--force", "--dry-run", "--quiet", "--exclude", "--interactive"],
    "checkout": ["--force", "--ours", "--theirs", "--track", "--no-track", "--guess", "--no-guess", "--orphan",
                 "--merge", "--conflict", "--patch", "--detach", "--quiet", "--progress", "--no-progress",
                 "--ignore-skip-worktree-bits", "--ignore-other-worktrees", "--overwrite-ignore",
                 "--no-overwrite-ignore", "--recurse-submodules", "--overlay", "--no-overlay",
                 "--pathspec-from-file", "--pathspec-file-nul"],
    "switch": ["--create", "--force-create", "--detach", "--guess", "--no-guess", "--force", "--discard-changes",
               "--merge", "--conflict", "--quiet", "--progress", "--no-progress", "--track", "--no-track",
               "--orphan", "--ignore-other-worktrees", "--recurse-submodules"],
    "rm": ["--recursive", "--force", "--interactive", "--one-file-system", "--no-preserve-root", "--preserve-root",
           "--dir", "--verbose"],
}


class Unreadable(Exception):
    """A command this cannot read; it is refused, never allowed."""


@dataclass
class Word:
    text: str
    glob: bool = False      # an unquoted * ? [ or { in it
    equals: bool = False    # it starts with an unquoted = (zsh's path expansion)
    quoted: bool = False    # some part of it was quoted
    subs: list[str] = field(default_factory=list)   # the text of each `$( )` or backtick in it


@dataclass
class Command:
    words: list[Word] = field(default_factory=list)
    fed: list[str] = field(default_factory=list)   # here-document bodies and here-strings it reads
    piped: bool = False                             # its stdin is a pipe
    from_file: bool = False                         # its stdin is a file
    writes: list[Word] = field(default_factory=list)   # the targets of its `>`, `>>`, `>|`, `&>`, `<>`, `>&`
    joined: str = ""                                # what joins it to the command before
    inner: int = 0                                  # inside a substitution or a here-document's expansion


class _Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.subs: list[str] = []
        self.glob = self.equals = self.quoted = False

    def add(self, text: str, quoted: bool) -> None:
        if quoted:
            self.quoted = True
        else:
            if not self.parts and text.startswith("="):
                self.equals = True
            self.glob = self.glob or any(ch in text for ch in "*?[{")
        self.parts.append(text)

    def word(self) -> Word:
        return Word("".join(self.parts), self.glob, self.equals, self.quoted, list(self.subs))


class Lexer:
    """One pass over the text: simple commands, substitutions inside them, here-documents after them."""

    def __init__(self, text: str, depth: int = 0, start: int = 0) -> None:
        if depth > 12:
            raise Unreadable("substitutions nested too deep")
        self.s, self.i, self.depth = text, start, depth
        self.commands: list[Command] = []
        self.pending: list[tuple[str, bool, bool, Command]] = []  # delimiter, tabs stripped, quoted, owner
        self.patterns = 0  # `case ... in` seen: a `)` may end a pattern inside `$( )`
        self.linear = True  # only `;`, `&&`, `||`, newlines and pipes join its commands (`_linear`)

    # --- the command level ---------------------------------------------------------------------------
    def parse(self, closing: str | None = None) -> None:  # noqa: C901 -- one branch per shell token
        cmd = Command()
        parens = 0
        last_end = -1
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t":
                self.i += 1
            elif s.startswith("\\\n", self.i):
                self.i += 2
            elif c == "#":
                end = s.find("\n", self.i)
                self.i = end if end >= 0 else len(s)
            elif c == "\n":
                self.i += 1
                cmd = self._end(cmd, joined=";")
                self._bodies()
            elif c in "<>" or s.startswith("&>", self.i):
                if cmd.words and last_end == self.i and cmd.words[-1].text.isdigit():
                    cmd.words.pop()  # an fd number written against its redirection
                self._redirect(cmd)
            elif c in ";&|":
                op = next(o for o in ("&&", "||", ";;&", ";;", ";&", "|&", "|", "&", ";") if s.startswith(o, self.i))
                self.i += len(op)
                self.linear = self.linear and op in ("&&", "||", ";", "|", "|&")
                cmd = self._end(cmd, piped=op in ("|", "|&"), joined=op)
            elif c == "(":
                self.linear = False
                if cmd.words and last_end == self.i:
                    if s.startswith("()", self.i):  # `name()`: a function's name is no command
                        self.i += 2
                        cmd = Command()
                    elif cmd.words[-1].text.endswith("="):  # `x=(a b)`: each element read as a command
                        self.i += 1
                        self._substitution(")")
                    else:
                        raise Unreadable("a word with `(` written against it (a zsh glob qualifier or `=( )`)")
                elif s.startswith("((", self.i) and not cmd.words and (end := self._arith_end(self.i + 2)):
                    self._expansions(s[self.i + 2:end - 2])  # `(( ... ))` is arithmetic
                    self.i = end
                else:
                    self.i += 1
                    parens += 1
                    cmd = self._end(cmd)
            elif c == ")":
                self.i += 1
                self.linear = False
                if closing == ")" and parens == 0 and not self.patterns:
                    self._end(cmd)
                    return
                if parens == 0:
                    cmd = Command()  # `pattern)` in a `case`: the words before it name no command
                    continue
                parens -= 1
                cmd = self._end(cmd)
            else:
                word = self._word()
                last_end = self.i
                if word.text in ("{", "}") and not word.quoted:
                    self.linear = False
                    cmd = self._end(cmd)  # a brace group's edge, and zsh's `if x {` and `} always {`
                    continue
                cmd.words.append(word)
                if word.text == "in" and len(cmd.words) >= 3 and cmd.words[0].text == "case":
                    self.linear = False
                    self.patterns += 1
                    cmd = self._end(cmd)
                elif word.text == "esac" and len(cmd.words) == 1:
                    self.patterns = max(0, self.patterns - 1)
        self._end(cmd)
        if closing:
            raise Unreadable("an unclosed $( substitution")

    def _end(self, cmd: Command, piped: bool = False, joined: str = ";") -> Command:
        if cmd.words or cmd.fed:
            self.commands.append(cmd)
        elif cmd.joined in ("&&", "||", "|", "|&"):  # `a &&` and a newline: what follows is joined by `&&`
            piped, joined = cmd.piped, cmd.joined
        return Command(piped=piped, joined=joined)

    def _nested(self, commands: list[Command]) -> None:
        """A substitution's or an expansion's commands, judged with the rest, marked as inside one."""
        for nested in commands:
            nested.inner += 1
        self.commands.extend(commands)

    def _bodies(self) -> None:
        """At a newline: each here-document opened on the line just ended takes the lines up to its delimiter
        (to the end, if none). The body is data; an unquoted delimiter's body has its substitutions judged."""
        for delimiter, tabs, quoted, owner in self.pending:
            lines: list[str] = []
            while self.i < len(self.s):
                end = self.s.find("\n", self.i)
                line = self.s[self.i:end] if end >= 0 else self.s[self.i:]
                self.i = end + 1 if end >= 0 else len(self.s)
                line = line.lstrip("\t") if tabs else line
                if line == delimiter:
                    break
                lines.append(line)
            body = "\n".join(lines)
            if not quoted:
                self._expansions(body)
            owner.fed.append(body)
        self.pending = []

    def _redirect(self, cmd: Command) -> None:
        s = self.s
        op = next(o for o in ("&>>", "&>", "<<<", "<<-", "<<", "<>", "<&", "<(", ">(", ">>", ">|", ">&", "<", ">")
                  if s.startswith(o, self.i))
        self.i += len(op)
        if op in ("<(", ">("):
            self._substitution(")")
            return
        while self.i < len(s) and s[self.i] in " \t":
            self.i += 1
        if self.i >= len(s) or s[self.i] in "\n;&|()<>":
            if op in ("<<", "<<-", "<<<"):
                raise Unreadable(f"`{op}` with nothing after it")
            return
        target = self._word()
        if op in ("<<", "<<-"):
            self.pending.append((target.text, op == "<<-", target.quoted, cmd))
        elif op == "<<<":
            cmd.fed.append(target.text)
        elif op in ("<", "<&"):
            cmd.from_file = True
        elif op == "<>":  # opened for reading and writing
            cmd.from_file = True
            cmd.writes.append(target)
        elif op == ">&":  # `>&2`, `>&-` move a descriptor; `>& file` writes the file (bash, zsh)
            if not target.text.isdigit() and target.text != "-":
                cmd.writes.append(target)
        elif op in (">", ">>", ">|", "&>", "&>>"):
            cmd.writes.append(target)

    # --- the word level ------------------------------------------------------------------------------
    def _word(self) -> Word:
        b = _Builder()
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\n;&|()<>":
                break
            if c == "\\":
                if s.startswith("\\\n", self.i):
                    self.i += 2
                    continue
                b.add(s[self.i + 1:self.i + 2], True)
                self.i += 2
            elif c == "'":
                end = s.find("'", self.i + 1)
                if end < 0:
                    raise Unreadable("an unclosed single quote")
                b.add(s[self.i + 1:end], True)
                self.i = end + 1
            elif c == '"':
                self._double(b)
            elif c == "$":
                self._dollar(b, in_double=False)
            elif c == "`":
                self._backtick(b)
            else:
                b.add(c, False)
                self.i += 1
        return b.word()

    def _double(self, b: _Builder) -> None:
        s = self.s
        self.i += 1
        while self.i < len(s):
            c = s[self.i]
            if c == '"':
                self.i += 1
                b.add("", True)
                return
            if c == "\\" and s[self.i + 1:self.i + 2] in ('$', '`', '"', "\\", "\n"):
                if s[self.i + 1] != "\n":
                    b.add(s[self.i + 1], True)
                self.i += 2
            elif c == "$":
                self._dollar(b, in_double=True)
            elif c == "`":
                self._backtick(b)
            else:
                b.add(c, True)
                self.i += 1
        raise Unreadable("an unclosed double quote")

    def _expansions(self, text: str) -> None:
        """The substitutions in text the shell expands as it would inside double quotes: an unquoted
        here-document's body, arithmetic, a `${ }`'s inner text. Each one's commands are judged."""
        sub = Lexer(text, self.depth + 1)
        b = _Builder()
        while sub.i < len(text):
            c = text[sub.i]
            if c == "\\":
                sub.i += 2
            elif c == "$":
                sub._dollar(b, in_double=True)
            elif c == "`":
                sub._backtick(b)
            else:
                sub.i += 1
        self._nested(sub.commands)

    def _dollar(self, b: _Builder, in_double: bool) -> None:
        s = self.s
        if not in_double and s.startswith("$'", self.i):
            end = self.i + 2
            while end < len(s) and s[end] != "'":
                end += 2 if s[end] == "\\" else 1
            if end >= len(s):
                raise Unreadable("an unclosed $'...' quote")
            raw = s[self.i + 2:end].encode("latin-1", "backslashreplace")
            b.add(codecs.decode(raw, "unicode_escape"), True)
            self.i = end + 1
        elif s.startswith("$((", self.i) and (end := self._arith_end(self.i + 3)):
            self._expansions(s[self.i + 3:end - 2])
            b.add("$((...))", True)
            self.i = end
        elif s.startswith("$(", self.i):  # `$((cmd) )` too: a substitution holding a subshell
            self.i += 2
            start = self.i
            self._substitution(")")
            b.subs.append(s[start:self.i - 1])
            b.add("$(...)", True)
        elif s.startswith("${", self.i):
            end = self._brace_end(self.i + 2)
            inner = s[self.i + 2:end]
            if inner.startswith("("):
                raise Unreadable("a `${(flags)...}`, which zsh may evaluate")
            self._expansions(inner)
            b.add("${" + inner + "}", True)
            self.i = end + 1
        else:
            name = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*|[0-9@*#?$!-])", s[self.i:])
            b.add(name.group(0) if name else "$", True)
            self.i += name.end() if name else 1

    def _arith_end(self, start: int) -> int | None:
        """The index past `))` closing an arithmetic `$((` or `((` opened before `start`; None when its two
        closing parentheses are apart (`$((cmd) )` is a substitution) or never come."""
        depth, one_at, j = 2, -1, start
        while j < len(self.s):
            ch = self.s[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 1:
                    one_at = j
                elif depth == 0:
                    return j + 1 if one_at == j - 1 else None
            j += 1
        return None

    def _brace_end(self, start: int) -> int:
        """The index of the `}` that ends a `${` as bash ends it: the first unquoted, unescaped one outside a
        nested `${ }` or parentheses."""
        s, j, depth, parens = self.s, start, 1, 0
        while j < len(s):
            ch = s[j]
            if ch == "\\":
                j += 2
                continue
            if ch == "'":
                end = s.find("'", j + 1)
                if end < 0:
                    raise Unreadable("an unclosed single quote in ${")
                j = end + 1
                continue
            if ch == '"':
                j += 1
                while j < len(s) and s[j] != '"':
                    j += 2 if s[j] == "\\" else 1
                j += 1
                continue
            if s.startswith("${", j):
                depth += 1
                j += 2
                continue
            if ch == "(":
                parens += 1
            elif ch == ")":
                parens = max(0, parens - 1)
            elif ch == "}" and parens == 0:
                depth -= 1
                if depth == 0:
                    return j
            j += 1
        raise Unreadable("an unclosed ${")

    def _backtick(self, b: _Builder) -> None:
        """A backtick substitution: its text with one level of `\\``, `\\$` and `\\\\` removed is a command line,
        nested backticks included."""
        s, j = self.s, self.i + 1
        while j < len(s) and s[j] != "`":
            j += 2 if s[j] == "\\" else 1
        if j >= len(s):
            raise Unreadable("an unclosed backtick")
        inner = re.sub(r"\\([`$\\\"])", r"\1", s[self.i + 1:j])
        sub = Lexer(inner, self.depth + 1)
        sub.parse()
        sub._bodies()
        self._nested(sub.commands)
        b.subs.append(inner)
        b.add("$(...)", True)
        self.i = j + 1

    def _substitution(self, closing: str) -> None:
        """A `$( )` substitution, read in a quoting context of its own; its commands are judged too."""
        sub = Lexer(self.s, self.depth + 1, self.i)
        sub.parse(closing)
        self._nested(sub.commands)
        self.pending.extend(sub.pending)
        self.i = sub.i


# --- judging ------------------------------------------------------------------------------------------

def judge_text(text: str, depth: int = 0) -> str | None:
    """Why the command must be refused, or None. Every simple command in it is judged in order, each from
    the directories it may run in (`_linear`, else `_follow`)."""
    if len(text) > MAX_INPUT:
        raise Unreadable(f"the command is over {MAX_INPUT} characters")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lexer = Lexer(text, depth)
    lexer.parse()
    lexer._bodies()  # a here-document opened on the last line runs to the end
    plan = _linear(lexer)
    if plan is None:
        _follow(lexer.commands)
        for cmd in lexer.commands:
            if (why := judge_command(cmd, depth)):
                return why
        return None
    judged, reached = plan
    for cmd, dirs in judged:
        WHERE["dirs"] = dirs
        if (why := judge_command(cmd, depth)):
            return why
    WHERE["dirs"] = reached  # what a text read after this one (an `eval`'s caller) is judged from
    return None


def _assign(word: Word) -> None:
    """Record `name=value` for the rest of this text: a literal, a `mktemp` result, or unknown. A `mktemp`
    result is the whole value and nothing else, one substitution running `mktemp` alone: `d=$(mktemp -d)/..`,
    `d=$(mktemp -d; echo /x)` and `d=$(mktemp -d)$x` are unknown (the v7.1 upgrade security review's B1)."""
    name, _, value = word.text.partition("=")
    if name.endswith("+") or "[" in name:
        SCOPE[name.rstrip("+").split("[", 1)[0]] = UNKNOWN
        return
    if (value == "$(...)" and len(word.subs) == 1 and MKTEMP.match(word.subs[0])
            and not re.search(r"[;&|\n`<>()]|\$\(", word.subs[0])):
        SCOPE[name] = SCRATCH
    elif "$" not in value and not word.glob:
        SCOPE[name] = value
    else:
        SCOPE[name] = UNKNOWN


def _expand(text: str) -> str:
    """A word with each `$name` or `${name}` replaced by the literal assigned to it earlier in this text.
    A variable this text did not assign a literal to stays as written."""
    def one(m: re.Match) -> str:
        value = SCOPE.get(m.group(1))
        return value if isinstance(value, str) else m.group(0)
    return VARIABLE.sub(one, text)


def _env_file(text: str) -> bool:
    """A secrets file by name: `.env`, `.env.<anything>` but the documented examples, `<x>.env`, or `.envrc`
    -- the Write/Edit guard's rule, so a shell cannot write what the editor may not."""
    name = text.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if name in ENV_EXEMPT:
        return False
    return name in (".env", ".envrc") or name.startswith(".env.") or name.endswith(".env")


def judge_command(cmd: Command, depth: int) -> str | None:
    """Past assignments and keywords; after a wrapper, every later word is tried as the program, in one pass."""
    words = cmd.words
    if any(TMPDIR_NAMED.search(w.text) for w in words):
        TRUST["TMPDIR"] = False   # `read TMP""DIR`: the name, quoted apart, as the shell will see it
    written = [_expand(w.text) for w in cmd.writes]
    # The Write/Edit guard refuses a `.env` file and the owner's directories; a shell redirection is the same write.
    if any(_env_file(t) for t in written):
        return ENV_WRITE
    if any(_owners(t) for t in written):
        return OWNERS
    start, prefix = 0, []
    while start < len(words) and (ASSIGNMENT.match(words[start].text) or words[start].text in KEYWORDS):
        if ASSIGNMENT.match(words[start].text):
            prefix.append(words[start])
        start += 1
    if start >= len(words):
        for w in prefix:
            _assign(w)
        return None
    # `NAME=value cmd` puts NAME in that one program's environment: the shell expands the command's own words
    # before it applies it, and no later command sees it. What NAME holds from here is not known, so a target
    # built from it is no scratch (the v7.1 upgrade security rereview's B1-R).
    for w in prefix:
        SCOPE[w.text.partition("=")[0].rstrip("+").split("[", 1)[0]] = UNKNOWN
    first = _program(words[start])
    if first in SETTERS:
        for w in words[start + 1:]:
            if ASSIGNMENT.match(w.text):
                _assign(w)
        return None
    if first not in WRAPPERS:
        return judge_words(words[start:], cmd, depth)
    xargs_at, tried = len(words), 0
    for k in range(start, len(words)):
        word = words[k]
        program = _program(word)
        if program == "xargs":
            xargs_at = min(xargs_at, k)
        if program == "env":
            j = k + 1
            while j < len(words) and (words[j].text.startswith("-") or ASSIGNMENT.match(words[j].text)):
                arg = words[j].text
                text = (words[j + 1].text if arg in ("-S", "--split-string") and j + 1 < len(words) else
                        arg.split("=", 1)[1] if arg.startswith("--split-string=") else
                        arg[2:] if arg.startswith("-S") and len(arg) > 2 else None)
                if text is not None and (why := judge_text(text, depth + 1)):
                    return why
                j += 1
        if k > start and word.text.startswith("-") and word.text != "-":
            continue
        if ASSIGNMENT.match(word.text):
            continue
        if program in WRAPPERS and k != len(words) - 1:
            continue
        tried += 1
        if tried > 64:
            raise Unreadable("more than 64 words behind wrappers")
        if (why := judge_words(words[k:], cmd, depth, behind_xargs=xargs_at < k)):
            return why
    return None


def _program(word: Word) -> str:
    return os.path.basename(_expand(word.text[1:] if word.equals else word.text))


def _unique(option: str, wanted: str, known: list[str]) -> bool:
    """Whether git reads `option` as `wanted`: the whole name, or a prefix no other option of its shares."""
    name = option.split("=", 1)[0]
    if not name.startswith("--") or len(name) < 3 or not wanted.startswith(name):
        return False
    return name == wanted or not any(other.startswith(name) for other in known if other != wanted)


def _stdin(cmd: Command, depth: int, who: str) -> str | None:
    """A shell or `source` reading its commands from stdin: its here-documents and here-strings are read;
    a pipe or a file is not, so it is refused."""
    if cmd.fed and not cmd.piped and not cmd.from_file:
        for text in cmd.fed:
            if (why := judge_text(text, depth + 1)):
                return why
        return None
    return (f"BLOCKED: {who} reading its commands from a pipe, a file or stdin, which this guard cannot read; "
            "run the commands themselves, or the script by its name.")


def judge_words(words: list[Word], cmd: Command, depth: int, behind_xargs: bool = False) -> str | None:  # noqa: C901
    first = words[0]
    if first.glob:
        return (f"BLOCKED: `{first.text}` names its program by a pattern, which this guard cannot read; "
                "write the program's name.")
    program = _program(first)
    args = [w.text for w in words[1:]]
    CANDIDATES.append([_expand(first.text[1:] if first.equals else first.text)] + args)
    if (why := _writes_protected(program, [_expand(a) for a in args])):
        return why
    if program == "eval":
        return judge_text(" ".join(args), depth + 1)
    if program in SHELLS:
        return _judge_shell(program, args, cmd, depth)
    if program in ("source", ".") and args:
        return _stdin(cmd, depth, f"`{program}`") if args[0] in STDIN_PATHS else judge_words(words[1:], cmd, depth)
    if program == "find":
        if "-delete" in args:
            # The starting points are the words before the first expression token; `-delete` under
            # anything but scratch removes files this guard would refuse `rm -rf` on.
            starts: list[Word] = []
            for w in words[1:]:
                if w.text.startswith("-") or w.text in ("(", ")", "!"):
                    break
                starts.append(w)
            if any(_owners(_expand(w.text), worktrees=True) for w in starts):
                return OWNERS
            if not starts or not all(_scratch(w) for w in starts):
                return DESTRUCTIVE
        for i, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                rest = words[i + 2:]
                end = next((j for j, w in enumerate(rest) if w.text in (";", "+")), len(rest))
                if rest[:end] and (why := judge_words(rest[:end], cmd, depth)):
                    return why
        return None
    if program in ("tee", "cp", "mv", "install", "ln"):
        targets = [a for a in args if not a.startswith("-")]
        option, doubt = _target_option(program, args) if program in TARGET_OPTION else ([], False)
        # With `-t DIR` every source lands under its own name, so each source's name is a destination too.
        checked = targets if program == "tee" or option or doubt else targets[-1:]
        if any(_env_file(_expand(a)) for a in checked + option):
            return ENV_WRITE
    if program in ("fly", "flyctl"):
        sub = tuple(a for a in args if not a.startswith("-"))
        if behind_xargs or (sub and not any(sub[:len(allowed)] == allowed for allowed in READ_ONLY_FLY)):
            return FLY.format(shown=f"{program} {' '.join(sub[:2]) if sub else '(its arguments from stdin)'}")
        return None
    if program == DEPLOY and (args != ["--dry-run"] or behind_xargs):
        return DEPLOY_SCRIPT
    if program == "git":
        return _judge_git(args, behind_xargs, depth)
    if program == "rm":
        return _judge_rm(words[1:])
    if program == "gh":
        return _judge_gh(args)
    if program == "ssh":
        return _judge_ssh(args, depth)
    return None


# --- the owner's directories: .claude/ and .githooks/ of any work tree --------------------------------

def _owned(path: str, base: str) -> list[str] | None:
    """The parts of `path`, resolved from `base`, below its work tree's root when the first of them is an
    owned directory; None when the path is not protected."""
    target = os.path.realpath(os.path.join(base or os.getcwd(), os.path.expandvars(os.path.expanduser(path))))
    below, root = target, os.path.dirname(target)
    while not os.path.lexists(os.path.join(root, ".git")):
        if os.path.dirname(root) == root:
            return None
        below, root = root, os.path.dirname(root)
    if os.path.basename(below).casefold() not in OWNED:
        return None
    return os.path.relpath(target, root).split(os.sep)


def protected(path: str, base: str) -> bool:
    """Whether writing `path`, from the directory `base`, writes the hooks or settings of a git work tree: the
    path (`~` and variables expanded, resolved from `base`, links followed on its longest existing part) lies
    in the work tree whose root is the nearest directory above it holding a `.git` entry, and the directory
    directly below that root is named `.claude` or `.githooks`, in any case. The Bash guard and the Write and
    Edit hook both ask this (round 2's B1; round 3's M1: a worktree inside `.claude/worktrees/` is its own)."""
    return _owned(path, base) is not None


def _in_worktrees(parts: list[str]) -> bool:
    """`.claude/worktrees/<name>` or below it: v7.1's scratch, which `rm` may remove."""
    return (len(parts) >= 3 and parts[0].casefold() == ".claude" and parts[1] == "worktrees"
            and parts[2] not in ("", ".", ".."))


def _owners(path: str, bases: list[str] | None = None, worktrees: bool = False) -> bool:
    """Whether a path a command writes is protected from any directory the command may run in; with
    `worktrees`, a path under `.claude/worktrees/<name>` is not."""
    for base in (bases if bases is not None else WHERE["dirs"]) or [os.getcwd()]:
        parts = _owned(path, base)
        if parts is not None and not (worktrees and _in_worktrees(parts)):
            return True
    return False


def _resolved(base: str, path: str) -> str:
    return os.path.realpath(os.path.join(base, os.path.expandvars(os.path.expanduser(path))))


def _in_shell(words: list[str], keywords: bool = False) -> int:
    """Where the program is, past assignments and the words that run it in the shell itself (`builtin`,
    `command` with no option, `time` and its `-p`, zsh's `noglob` and `nocorrect`), and shell keywords if asked."""
    i = 0
    while i < len(words):
        word = words[i]
        if ASSIGNMENT.match(word) or word in ("builtin", "noglob", "nocorrect") or (keywords and word in KEYWORDS):
            i += 1
        elif word == "command" and i + 1 < len(words) and not words[i + 1].startswith("-"):
            i += 1
        elif word == "time":
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 1
        else:
            break
    return i


def _changes_into(cmd: Command) -> str | None:
    """The directory a `cd`, `pushd` or `chdir` names (`~` for none), or None for any other command and for the
    forms that name no directory (`cd -`, `pushd +1`)."""
    words = [w.text for w in cmd.words]
    i = _in_shell(words, keywords=True)
    if i >= len(words) or words[i] not in DIR_CHANGES:
        return None
    rest = words[i + 1:]
    while rest and rest[0].startswith("-") and rest[0] != "-":
        done, rest = rest[0] == "--", rest[1:]
        if done:
            break
    if not rest:
        return "~" if words[i] != "pushd" else None
    return None if rest[0] == "-" or rest[0].startswith("+") else rest[0]


def _plain(cmd: Command) -> tuple[bool, str | None]:
    """(whether `_linear` can follow it, the directory it changes into): a command of shell grammar, one that
    runs text in the shell or pops its directory stack, or a `cd` to a directory this cannot name exactly, is
    not followed (round 3's M1)."""
    words = [w.text for w in cmd.words]
    i = _in_shell(words)
    if i >= len(words):
        return True, None
    if words[0] in SHELL_GRAMMAR or words[i] in SHELL_GRAMMAR or words[i] == "." or UNFOLLOWED & set(words):
        return False, None
    if words[i] not in DIR_CHANGES:
        return not DIR_CHANGES & set(words), None   # `time cd x`, `echo cd`: a `cd` this does not place
    operands = cmd.words[i + 1:]
    while operands and operands[0].text.startswith("-") and operands[0].text != "-":
        done, operands = operands[0].text == "--", operands[1:]
        if done:
            break
    if not operands:
        return words[i] != "pushd", "~" if words[i] != "pushd" else None
    target = operands[0]
    text = target.text
    named = (len(operands) == 1 and text and not target.glob and not any(ch in text for ch in "$`")
             and not text.startswith(("-", "+")) and (not text.startswith("~") or text == "~" or text.startswith("~/"))
             and not (os.environ.get("CDPATH") and not text.startswith(("/", "./", "../", "~"))
                      and text not in (".", "..")))
    return (True, text) if named else (False, None)


def _entered(base: str, target: str) -> list[str]:
    """Where a `cd` to `target` from `base` lands: as the shell reads `..` (logically) and as the disk does."""
    joined = os.path.join(base, os.path.expanduser(target))
    return list(dict.fromkeys([os.path.normpath(joined), os.path.realpath(joined)]))


def _linear(lexer: Lexer) -> tuple[list[tuple[Command, list[str]]], list[str]] | None:
    """For a text of simple commands joined only by `;`, `&&`, `||`, newlines and pipes, each command with the
    directories it can run in, and every directory reached; None for any other text (round 3's M1).

    The state is a set of (directory, the last command's status). A command joined by `&&` runs where the
    status is success, by `||` where it is failure, by `;` everywhere. A `cd` that succeeds lands where it
    names; one that fails stays, with the status failure. Any other command may end either way. A pipe's
    commands run where its first does. A substitution's commands are judged from every directory reached."""
    readings = {id(cmd): _plain(cmd) for cmd in lexer.commands}
    if not lexer.linear or not all(ok for ok, _ in readings.values()) or any(
            cmd.inner and readings[id(cmd)][1] is not None for cmd in lexer.commands):
        return None
    states = [(d, True) for d in WHERE["dirs"]]
    reached = list(WHERE["dirs"])
    judged: list[tuple[Command, list[str]]] = []
    top = [cmd for cmd in lexer.commands if not cmd.inner]
    i = 0
    while i < len(top):
        group = [top[i]]
        i += 1
        while i < len(top) and top[i].joined in ("|", "|&"):
            group.append(top[i])
            i += 1
        targets = [readings[id(cmd)][1] for cmd in group]
        if len(group) > 1 and any(t is not None for t in targets):
            return None   # a `cd` in a pipe runs in a subshell in bash and in the shell in zsh
        joined = group[0].joined
        runs = [st for st in states if joined in ("", ";") or st[1] == (joined == "&&")]
        dirs = list(dict.fromkeys(d for d, _ in (runs or states)))
        judged += [(cmd, dirs) for cmd in group]
        landed: list[tuple[str, bool]] = []
        for d, _ in runs:
            target = targets[0]
            landed += ([(n, True) for n in _entered(d, target)] + [(d, False)] if target is not None
                       else [(d, True), (d, False)])
        states = list(dict.fromkeys(landed + [st for st in states if st not in runs]))
        reached = list(dict.fromkeys(reached + [d for d, _ in states]))
        if len(reached) > MAX_DIRS:
            raise Unreadable(f"the command changes into more than {MAX_DIRS} directories")
    # In the lexer's order, so an assignment is known where its variable is used; a substitution's commands
    # are judged from every directory reached.
    where = {id(cmd): dirs for cmd, dirs in judged}
    return [(cmd, where.get(id(cmd), reached)) for cmd in lexer.commands], reached


def _follow(commands: list[Command]) -> None:
    """For a text `_linear` cannot follow: each directory a `cd` in these commands changes into, from every
    directory reached before it, joins the ones a written path is judged from. They are never dropped: a `cd`
    in a subshell or one that fails is taken as made, which can only refuse more."""
    dirs = WHERE["dirs"]
    for cmd in commands:
        target = _changes_into(cmd)
        if target is None:
            continue
        for found in [_resolved(d, target) for d in dirs]:
            if found not in dirs:
                dirs.append(found)
        if len(dirs) > MAX_DIRS:
            raise Unreadable(f"the command changes into more than {MAX_DIRS} directories")


def _target_option(program: str, args: list[str]) -> tuple[list[str], bool]:
    """(the `-t` values, doubt): `-t DIR`, `-tDIR`, a cluster whose `t` comes before any letter that takes a
    value (VALUED), `--target-directory DIR` or `=DIR`, or a unique prefix of it. A `t` after such a letter
    may be the value's or the option: that is doubt, and every operand is then judged (round 3's M2)."""
    found: list[str] = []
    doubt = False
    for i, arg in enumerate(args):
        following = args[i + 1] if i + 1 < len(args) else ""
        name = arg.split("=", 1)[0]
        if arg == "--":
            break
        if arg.startswith("--"):
            if len(name) >= 3 and "--target-directory".startswith(name):
                found.append(arg.split("=", 1)[1] if "=" in arg else following)
        elif arg.startswith("-") and len(arg) > 1:
            for j in range(1, len(arg)):
                if arg[j] == "t":
                    found.append(arg[j + 1:] or following)
                    break
                if arg[j] in VALUED.get(program, set()):
                    doubt = doubt or "t" in arg[j + 1:]
                    break
    return [f for f in found if f], doubt


def _install_dirs(args: list[str]) -> bool:
    """`install -d` (`--directory`, a unique prefix of it, or a `d` in a cluster before any valued letter):
    every operand is a directory it makes."""
    for arg in args:
        name = arg.split("=", 1)[0]
        if arg.startswith("--") and len(name) >= 4 and "--directory".startswith(name):
            return True
        if arg.startswith("-") and not arg.startswith("--"):
            for letter in arg[1:]:
                if letter == "d":
                    return True
                if letter in VALUED["install"]:
                    break
    return False


def _writes_protected(program: str, args: list[str]) -> str | None:
    """A write into a work tree's `.claude/` or `.githooks/` by a program this lists (S3; round 2, B1 and M6).
    `rm` may remove a directory under `.claude/worktrees/<name>`, v7.1's scratch."""
    paths = [a for a in args if not a.startswith("-")]
    option, doubt = _target_option(program, args) if program in TARGET_OPTION else ([], False)
    if program == "dd":
        written = [a[3:] for a in args if a.startswith("of=")]
    elif program in CHANGES_EVERY or doubt or (program == "install" and _install_dirs(args)):
        written = paths + option
    elif program in CHANGES_LAST:
        written = option or paths[-1:]   # with `-t`, the last word is a source
    else:
        written = []
    if any(_owners(a, worktrees=program == "rm") for a in written):
        return OWNERS
    # #282: what holds a work tree's `.claude/` or `.githooks/` -- its root, or a directory above it -- is
    # refused to `rm -r` and as the source of `mv`. `rm -rf` meets the stricter scratch rule (`_judge_rm`).
    recursive, forced = _rm_flags(args) if program == "rm" else (False, False)
    if recursive and not forced:
        moved = paths
    elif program == "mv":   # with `-t DIR`, every operand but DIR is a source
        moved = [a for a in paths if a not in option] if option or doubt else paths[:-1]
    else:
        moved = []
    if (why := _removes_owned(moved)):
        return why
    in_place = (program == "sed" and any(a.startswith("-i") or a == "--in-place" or a.startswith("--in-place=")
                                         for a in args)) or (
        program == "perl" and any(a.startswith("-") and not a.startswith("--") and "i" in a[1:] for a in args))
    if in_place and any(_owners(a) for a in paths):
        return OWNERS
    return _git_writes(args) if program == "git" else None


def _git_writes(args: list[str]) -> str | None:
    """`git rm`, `git mv`, `git checkout` or `git restore` naming a protected path, from each `-C` directory;
    and `git rm` (but `--cached`) or `git mv` naming what holds one (#282)."""
    bases, i = list(WHERE["dirs"]) or [os.getcwd()], 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            bases = [_resolved(base, args[i + 1]) for base in bases]
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") else 1
    sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
    named = [a for a in rest if not a.startswith("-")]
    if sub in ("rm", "mv", "checkout", "restore") and any(_owners(a, bases) for a in named):
        return OWNERS
    if (sub == "mv" or (sub == "rm" and "--cached" not in rest)):
        return _removes_owned(named[:-1] if sub == "mv" else named, bases)
    return None


def judge_write(path: str, base: str) -> str | None:
    """The Write and Edit hook (`--write`): a secrets file by name, or a path `protected` refuses."""
    if path and _env_file(path):
        return ENV_WRITE
    if path and protected(path, base):
        return OWNERS
    return None


# --- the scratch exemption for rm, and what a removal or a move may not take with it ----------------------
#
# The v7.1 upgrade security review's B1: a target that merely started with `$TMPDIR` or a `mktemp` variable was
# scratch, so `rm -rf $TMPDIR/../../Users/x` and `rm -rf "$TMPDIR/$unset"` passed. Every variable is now
# substituted and the path resolved where it lands. Its MAJOR-1 (round 1's M2): this project's work trees and
# review seats live under the temp directory, so "under a temp directory" let `rm -rf .` remove one; a path in,
# of or above a git work tree is no scratch. And #282: the owner's-directory rule asked only whether a path lay
# inside `.claude/` or `.githooks/`, never whether it held them, so `rm -r .` and `mv ../<repo> x` passed.
#
# The one exception is a worktree under `.claude/worktrees/<name>`, Claude Code's and the seats' throwaway
# checkouts. The way to drop one is `git worktree remove <path>` (`--force` with changes in it): git deletes the
# directory and prunes its record, and the guard does not refuse it. `rm -rf` of it passes too, leaving git a
# stale record that `git worktree prune` clears.

def _temp_bases() -> list[str]:
    """Where scratch lives: `$TMPDIR`, the interpreter's temp directory, and the usual system ones."""
    raw = [os.environ.get("TMPDIR"), os.environ.get("TEMP"), os.environ.get("TMP"), tempfile.gettempdir(),
           "/tmp", "/var/tmp", "/private/tmp", "/private/var/tmp", "/var/folders", "/private/var/folders"]
    out: list[str] = []
    for d in raw:
        if d:
            real = os.path.realpath(d)
            if real != os.path.sep and real not in out:
                out.append(real)
    return out


def _in_worktree_dir(resolved: str) -> bool:
    """At or below `<anything>/.claude/worktrees/<name>`: v7.1's scratch, MAJOR-1's one exception."""
    parts = resolved.replace("\\", "/").split("/")
    return any(part == ".claude" and i + 2 < len(parts) and parts[i + 1] == "worktrees" and parts[i + 2]
               for i, part in enumerate(parts))


def _root_of(path: str, proper: bool = False) -> str | None:
    """The nearest directory at (unless `proper`) or above `path` that holds a `.git` entry, or None."""
    d = os.path.dirname(path) if proper else path
    while True:
        if os.path.lexists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _known_roots() -> list[str]:
    """The work trees this call is known to touch without walking: those of each directory it runs in, of
    `$CLAUDE_PROJECT_DIR` and of this file's checkout."""
    found: list[str] = []
    for d in [*WHERE["dirs"], os.environ.get("CLAUDE_PROJECT_DIR", ""), GUARD_ROOT]:
        root = _root_of(os.path.realpath(d)) if d else None
        if root and root not in found:
            found.append(root)
    return found


def _listing(d: str) -> dict[str, os.DirEntry[str]]:
    """A directory's entries by their case-folded names."""
    with os.scandir(d) as entries:
        return {e.name.casefold(): e for e in entries}


class _Unwalked(Exception):
    """A directory too large, or unreadable, to say what it holds; the caller takes the answer that refuses."""


def _walk(top: str, wanted: Callable[[str, dict[str, os.DirEntry[str]]], bool]) -> bool:
    """Whether a directory at or below `top` (links not followed, no `.git` entered) holds a `.git` entry and
    satisfies `wanted(directory, names)`. Past the call's WALK budget or MAX_WALK directories, or on a
    directory it cannot read, it raises `_Unwalked`."""
    if not os.path.isdir(top) or os.path.islink(top):
        return False
    started, stack, seen = time.monotonic(), [top], 0
    try:
        while stack:
            seen += 1
            if seen > MAX_WALK or time.monotonic() - started > WALK["left"]:
                raise _Unwalked(top)
            d = stack.pop()
            try:
                names = _listing(d)
            except OSError:
                raise _Unwalked(top) from None
            if ".git" in names and wanted(d, names):
                return True
            stack += [e.path for n, e in names.items() if n != ".git" and e.is_dir(follow_symlinks=False)]
        return False
    finally:
        WALK["left"] -= time.monotonic() - started


def _near_a_work_tree(resolved: str) -> bool:
    """MAJOR-1: whether `resolved` lies in a git work tree, is one, or is above one (or cannot be told)."""
    if _root_of(resolved, proper=True):
        return True
    if any(root == resolved or root.startswith(resolved.rstrip(os.sep) + os.sep) for root in _known_roots()):
        return True
    try:
        return _walk(resolved, lambda d, names: True)
    except _Unwalked:
        return True


def _scratch_path(resolved: str) -> bool:
    """A resolved `rm -rf` target is scratch when it is a `.claude/worktrees/<name>` worktree or below one, or
    lies below a temp directory, is no temp directory and above none, and is in, of and above no git work
    tree (MAJOR-1)."""
    if _in_worktree_dir(resolved):
        return True
    bases, cut = _temp_bases(), resolved.rstrip(os.sep) + os.sep
    # A temp directory itself, or one above it (`$TMPDIR`, `/var/folders/qf`), holds every scratch tree: B1.
    if not any(resolved.startswith(base + os.sep) for base in bases) or any(
            base == resolved or base.startswith(cut) for base in bases):
        return False
    return not _near_a_work_tree(resolved)


def _value(m: re.Match[str]) -> str:
    """A variable's value as `_scratch` substitutes it; LookupError when this cannot know it."""
    name = m.group(1) or m.group(2)
    value = SCOPE.get(name)
    if isinstance(value, str):
        return value
    if name == "TMPDIR" and name not in SCOPE and TRUST["TMPDIR"] and os.environ.get("TMPDIR"):
        return os.environ["TMPDIR"]   # the hook's own; Claude Code hands the same environment to the shell
    raise LookupError(name)


def _scratch(word: Word) -> bool:
    """Whether an `rm -rf` or `find -delete` target is scratch, from every directory the command may run in.
    A `mktemp` variable of this text is, alone or with a path below it that holds no `..` and nothing to
    expand: the directory is new. Any other target has each `$name` and `${name}` replaced by the literal this
    text assigned it (`$TMPDIR` unassigned: the guard's own), is resolved where it lands, `..` and links
    followed, and must be `_scratch_path`. A variable this cannot know -- unset, assigned a value it cannot
    read, `${x:-y}` -- makes the target no scratch (B1)."""
    text = word.text
    if word.glob or not text:
        return False
    m = REFERENCE.match(text)
    if m and SCOPE.get(m.group(1) or m.group(2)) is SCRATCH and TRUST["mktemp"]:
        rest = text[m.end():]
        return (not rest or rest.startswith("/")) and not any(c in rest for c in "$`") and ".." not in rest.split("/")
    try:
        text = REFERENCE.sub(_value, text)
    except LookupError:
        return False
    if not text or any(c in text for c in "$`"):
        return False
    path = os.path.expanduser(text) if text == "~" or text.startswith("~/") else text
    if path.startswith("~"):
        return False  # `~user`: another account's tree
    bases = WHERE["dirs"] or [os.getcwd()]
    return all(_scratch_path(os.path.realpath(os.path.join(base, path))) for base in bases)


def _removes_owned(paths: list[str], bases: list[str] | None = None) -> str | None:
    """#282: a path removed or moved that holds a git work tree's `.claude/` or `.githooks/` -- the work tree's
    root, or a directory above it -- from any directory the command may run in. A `.claude/worktrees/<name>`
    worktree is not refused for holding its own; one too large to walk is refused."""
    def owns(d: str, names: dict[str, os.DirEntry[str]]) -> bool:
        return any(name in names and names[name].is_dir(follow_symlinks=False) for name in OWNED)

    for path in paths:
        for base in (bases if bases is not None else WHERE["dirs"]) or [os.getcwd()]:
            target = _resolved(base, path)
            if _in_worktree_dir(target):
                continue
            cut = target.rstrip(os.sep) + os.sep
            known = [root for root in _known_roots() if root == target or root.startswith(cut)]
            try:
                if any(owns(root, _listing(root)) for root in known) or _walk(target, owns):
                    return HOLDS_OWNED.format(path=path)
            except (_Unwalked, OSError):
                return UNWALKED.format(path=path)
    return None


def _rm_flags(args: list[str]) -> tuple[bool, bool]:
    """(recursive, forced) for `rm`'s arguments: `-r`, `-R`, `--recursive` (a unique prefix); `-f`, `--force`."""
    opts: list[str] = []
    for a in args:
        if a == "--":
            break
        if a.startswith("-") and len(a) > 1:
            opts.append(a)
    letters = "".join(a[1:] for a in opts if not a.startswith("--"))
    longs = [a for a in opts if a.startswith("--")]
    recursive = "r" in letters or "R" in letters or any(_unique(a, "--recursive", GIT_LONG["rm"]) for a in longs)
    forced = "f" in letters or any(_unique(a, "--force", GIT_LONG["rm"]) for a in longs)
    return recursive, forced


def _judge_rm(words: list[Word]) -> str | None:
    targets: list[Word] = []
    for k, w in enumerate(words):
        if w.text == "--":
            targets += words[k + 1:]
            break
        if not (w.text.startswith("-") and len(w.text) > 1):
            targets.append(w)
    recursive, forced = _rm_flags([w.text for w in words])
    if not (recursive and forced):
        return None
    if targets and all(_scratch(w) for w in targets):
        return None
    return DESTRUCTIVE


# --- gh -----------------------------------------------------------------------------------------------

def _judge_gh(args: list[str]) -> str | None:
    """Refused: `gh pr merge` and `gh pr ready` wherever their flags sit; `gh api` on a pull request's `/merge`,
    and on `/protection` or `/rulesets` with a mutating method or a field."""
    words: list[str] = []
    method = ""
    fields = False
    i = 0
    while i < len(args):
        a = args[i]
        name, eq, value = a.partition("=")
        if a.startswith("-") and len(a) > 1:
            if name in ("-X", "--method"):
                method = (value if eq else (args[i + 1] if i + 1 < len(args) else "")).upper()
            if name in ("-f", "--field", "-F", "--raw-field", "--input"):
                fields = True
            if not eq and name in GH_VALUED:
                i += 2
                continue
            i += 1
            continue
        words.append(a)
        i += 1
    if words[:2] in (["pr", "merge"], ["pr", "ready"]):
        return GH_MERGE
    if words[:1] == ["api"]:
        endpoints = words[1:]
        if any(re.search(r"/pulls/[^/\s]+/merge(?:$|[/?])", e) for e in endpoints):
            return GH_MERGE
        mutating = method in GH_MUTATING or fields
        if mutating and any(re.search(r"/protection(?:$|[/?])|/rulesets(?:$|[/?])", e) for e in endpoints):
            return GH_PROTECTION
    return None


# --- ssh ----------------------------------------------------------------------------------------------

#: `ssh`'s short options that take a value (OpenSSH): in a cluster, the rest of the word, or the next word, is it.
SSH_VALUED = set("BbcDEeFIiJLlmOoPpQRSWw")


def _judge_ssh(args: list[str], depth: int) -> str | None:
    """The v7.1 upgrade security review's M1: `ssh <host> <words>` runs the words, joined by spaces, in the
    remote shell, so they are judged as a command -- from the home directory, as the remote shell starts there,
    so a relative `rm -rf` target is never taken for a local temp directory's."""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            i += 1
            break
        if not arg.startswith("-") or len(arg) == 1:
            break
        valued = next((j for j in range(1, len(arg)) if arg[j] in SSH_VALUED), None)
        i += 2 if valued == len(arg) - 1 else 1
    remote = args[i + 1:]
    if not remote:
        return None
    where = WHERE["dirs"]
    WHERE["dirs"] = [os.path.expanduser("~")]
    try:
        return judge_text(" ".join(remote), depth + 1)
    finally:
        WHERE["dirs"] = where


# --- shells and git -----------------------------------------------------------------------------------

def _judge_shell(shell: str, args: list[str], cmd: Command, depth: int) -> str | None:
    """A shell runs `-c`'s string, a script file, or what it reads on stdin."""
    if any(a in ("--version", "--help") for a in args):
        return None
    j, given_c, reads_stdin = 0, False, False
    while j < len(args):
        arg = args[j]
        if arg == "--":
            j += 1
            break
        if arg in ("-o", "+o", "-O", "+O", "--rcfile", "--init-file"):
            j += 2
            continue
        if shell == "fish" and arg in ("-C", "--init-command"):
            if j + 1 < len(args) and (why := judge_text(args[j + 1], depth + 1)):
                return why
            j += 2
            continue
        if arg.startswith(("-", "+")) and len(arg) > 1:
            if not arg.startswith("--"):
                given_c = given_c or "c" in arg[1:]
                reads_stdin = reads_stdin or "s" in arg[1:]
            elif arg == "--command":
                given_c = True
            j += 1
            continue
        break
    rest = args[j:]
    if given_c:
        if not rest:
            return f"BLOCKED: `{shell} -c` with no command string takes it from elsewhere, which this guard cannot read."
        for text in rest:  # the string, then $0 and its arguments: each read as a command
            if (why := judge_text(text, depth + 1)):
                return why
        return None
    if rest and not reads_stdin and rest[0] not in STDIN_PATHS:
        return judge_words([Word(a) for a in rest], cmd, depth)
    return _stdin(cmd, depth, f"a shell (`{shell}`)")


def _skips_hooks(option: str) -> bool:
    """Refused: `--no-verify`, or a prefix of it long enough that git reads no other option (`--no-veri`)."""
    name = option.split("=", 1)[0]
    return len(name) >= 8 and "--no-verify".startswith(name)  # refused by the caller


def _judge_alias(key: str, value: str, depth: int) -> str | None:
    """The v7.1 upgrade security review's M1: an alias this text defines (`git config alias.<x> <value>`,
    `git -c alias.<x>=<value>`) is judged as what it runs -- a value starting `!` as shell text, any other as
    the git subcommand it names -- since a later `git <x>` in this text, or in another, runs it."""
    if not key.lower().startswith("alias."):
        return None
    return judge_text(value[1:] if value.startswith("!") else f"git {value}", depth + 1)


def _judge_git(args: list[str], behind_xargs: bool,  # noqa: C901 -- one branch per subcommand
               depth: int = 0) -> str | None:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] in ("-c", "--config-env") and i + 1 < len(args) and "hookspath" in args[i + 1].lower():
            return NO_VERIFY
        if args[i].startswith(("-c", "--config-env")) and "hookspath" in args[i].lower():
            return NO_VERIFY
        setting = (args[i + 1] if args[i] in ("-c", "--config-env") and i + 1 < len(args) else
                   args[i].split("=", 1)[1] if args[i].startswith("--config-env=") else "")
        key, _, value = setting.partition("=")
        if key.lower().startswith("alias.") and args[i].startswith("--config-env"):
            return (f"BLOCKED: `{args[i]}` takes the alias `{key}` from the environment, which this guard cannot "
                    "read; set it with `-c` instead (the v7.1 upgrade security review's M1).")
        if (why := _judge_alias(key, value, depth)):
            return why
        i += 2 if args[i] in ("-C", "-c", "--config-env", "--git-dir", "--work-tree", "--namespace",
                              "--exec-path") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    options = [a for a in rest if a.startswith("-")]
    longs = [a for a in options if a.startswith("--")]
    letters = "".join(a[1:] for a in options if not a.startswith("--"))
    known = GIT_LONG.get(sub, [])
    if any(_skips_hooks(a) for a in longs) or (sub == "commit" and "n" in letters):  # refused: a skipped hook
        return NO_VERIFY
    if sub == "update-ref":
        refs = [a for a in rest if not a.startswith("-")]
        if any(r.removeprefix("refs/").removeprefix("heads/") in PROTECTED for r in refs):
            return PROTECTED_REF
    if sub == "config":   # `git config [set] [--global] alias.<x> <value>`: every word after an alias key
        named = [a for a in rest if not a.startswith("-")]
        for k in range(len(named) - 1):
            if (why := _judge_alias(named[k], named[k + 1], depth)):
                return why

    def given(*wanted: str) -> bool:
        return any(_unique(a, w, known) for a in longs for w in wanted)

    if sub == "push":
        refs = [a for a in rest if not a.startswith("-")]
        forced = "f" in letters or given("--force", "--force-with-lease", "--force-if-includes")
        if forced or given("--mirror") or any(ref.startswith("+") for ref in refs):
            return DESTRUCTIVE
        targets = {ref.split(":")[-1].removeprefix("refs/").removeprefix("heads/") for ref in refs}
        if behind_xargs or given("--all", "--branches") or PROTECTED & targets:
            return PROTECTED_PUSH
    elif sub == "reset" and given("--hard"):
        return DESTRUCTIVE
    elif sub == "clean" and ("f" in letters or given("--force")):
        return DESTRUCTIVE
    elif sub == "checkout":
        if "--" in rest or "." in rest or "f" in letters or given("--force"):
            return DESTRUCTIVE
        creates = "b" in letters or "B" in letters or given("--orphan")
        valued = {"-b", "-B", "--orphan", "--conflict", "--pathspec-from-file"}
        plain = [a for n, a in enumerate(rest) if not a.startswith("-") and (n == 0 or rest[n - 1] not in valued)]
        if not creates and len(plain) >= 2:  # a tree-ish, then paths: their changes are discarded
            return DESTRUCTIVE
    elif sub == "switch" and ("f" in letters or given("--force", "--discard-changes")):
        return DESTRUCTIVE
    elif sub == "stash" and rest[:1] == ["clear"]:
        return DESTRUCTIVE
    elif sub == "restore":
        staged = "S" in letters or given("--staged")
        worktree = "W" in letters or given("--worktree")
        if not staged or worktree:
            return RESTORE
    return None


# --- the deploy gate ----------------------------------------------------------------------------------

def _toplevel(cwd: str) -> str | None:
    """The git work tree `cwd` lies in, or None."""
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True,
                           timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    top = r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else ""
    return top or None


def project_home() -> str:
    """The project root, whose `scripts/deploy_gate.py` is the only gate this guard runs: `$CLAUDE_PROJECT_DIR`,
    or the checkout this file lives in (the v7.1 upgrade security review's MAJOR-2)."""
    return os.environ.get("CLAUDE_PROJECT_DIR", "") or GUARD_ROOT


def project_root(cwd: str) -> str | None:
    """The tree whose brief and verdicts govern this call: the work tree of `cwd` when it carries
    `docs/project-brief.md`, else the project root when that does; None when neither has a brief, so nothing
    is declared. The tree is only read, by the project's own gate (`judge_deploy`)."""
    for cand in (_toplevel(cwd), project_home()):
        if cand and os.path.isfile(os.path.join(cand, "docs", "project-brief.md")):
            return cand
    return None


def judge_deploy(candidates: list[list[str]], cwd: str) -> str | None:
    """Hand every program-position word list to the project root's own `scripts/deploy_gate.py --judge`, run
    in the governing tree; its refusal is this guard's. No script of the tree the call runs in is run: a
    cloned repository's `scripts/deploy_gate.py` once ran on the next `ls` (MAJOR-2). A project root without
    its gate refuses every call while a brief governs, never skips, and never takes another tree's gate."""
    if not candidates:
        return None
    root = project_root(cwd)
    if root is None:
        return None
    home = project_home()
    gate = os.path.join(home, "scripts", "deploy_gate.py")
    if not os.path.isfile(gate):
        return GATE_MISSING.format(tree=root, root=home)
    payload = json.dumps({"cwd": cwd, "commands": candidates}).encode("utf-8")
    try:
        r = subprocess.run([sys.executable, "-I", "-B", gate, "--judge"], input=payload, capture_output=True,
                           cwd=root, timeout=20)
    except (OSError, subprocess.SubprocessError) as error:
        return f"BLOCKED: deploy gate -- scripts/deploy_gate.py could not run ({type(error).__name__}: {error})."
    if r.returncode == 0:
        return None
    message = r.stderr.decode("utf-8", "replace").strip()
    return message or f"BLOCKED: deploy gate -- scripts/deploy_gate.py exited {r.returncode} and gave no reason."


# --- the hook -----------------------------------------------------------------------------------------

def _expired() -> None:
    """The guard's own bound (S2): a thread, so it holds where SIGALRM does not exist. It cannot stop a long call
    into C that holds the interpreter; the hook's timeout bounds that."""
    sys.stderr.buffer.write(f"BLOCKED: the command was not judged within {DEADLINE_S:g} s.\n".encode())
    sys.stderr.flush()
    os._exit(2)


def _call(payload: object) -> tuple[dict, str]:
    """The tool call's input and the directory it runs in: the payload's `cwd`, which Claude Code sends."""
    if not isinstance(payload, dict):
        raise Unreadable(NOT_JSON)
    call = payload.get("tool_input")
    call = call if isinstance(call, dict) else {}
    cwd = str(payload.get("cwd") or "") or os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()
    return call, cwd


def judge_call(payload: object) -> str | None:
    """The Bash hook's payload, judged: the command's rules, then the deploy gate over its program words."""
    call, cwd = _call(payload)
    command = call.get("command", "")
    command = command if isinstance(command, str) else str(command)
    if not command.strip():
        return None
    WHERE["dirs"] = list(dict.fromkeys([os.path.normpath(os.path.abspath(cwd)), os.path.realpath(cwd)]))
    SCOPE.clear()
    CANDIDATES.clear()
    WALK["left"] = WALK_S
    TRUST["TMPDIR"] = not TMPDIR_NAMED.search(command)   # B1: `unset TMPDIR`, `for TMPDIR in`, `read TMPDIR`
    TRUST["mktemp"] = not MKTEMP_DEFINED.search(command)
    return judge_text(command) or judge_deploy(list(CANDIDATES), cwd)


def judge_file(payload: object) -> str | None:
    """The Write and Edit hook's payload (`--write`), judged by `judge_write`."""
    call, cwd = _call(payload)
    path = call.get("file_path") or call.get("notebook_path") or ""
    path = path if isinstance(path, str) else str(path)
    return judge_write(path, cwd) if path else None


def main(argv: list[str] | None = None) -> int:
    write = (sys.argv[1:] if argv is None else argv) == ["--write"]
    timer = threading.Timer(DEADLINE_S, _expired)
    timer.daemon = True
    timer.start()
    try:  # bytes, so a console's encoding (cp1254) cannot change what is read
        raw = sys.stdin.buffer.read()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise Unreadable(NOT_JSON) from None
        why = judge_file(payload) if write else judge_call(payload)
        timer.cancel()
    except Unreadable as error:
        text = str(error)
        why = text if text.startswith("BLOCKED:") else f"BLOCKED: this guard cannot read the command ({text})."
    except BaseException as error:  # any doubt refuses: a guard that cannot read the call never allows it
        what = "tool call" if write else "command"
        why = f"BLOCKED: this guard cannot read the {what} ({type(error).__name__}: {error})."
    if why:
        sys.stderr.buffer.write(why.encode("utf-8", "replace") + b"\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
