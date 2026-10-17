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
  destination (`main`, `HEAD:main`, `heads/main`, `refs/heads/main`), or runs behind `xargs`; git's
  words are read with this text's literal assignments in, so `m=main; git push origin --delete $m` is the
  push it spells (it walked through v7.1), and a deletion (`--delete`, `-d`, a `:ref`) naming a ref
  through an expansion still unresolved is refused: it may be the protected branch;
- `git reset --hard`; `git clean -f`; `git checkout --`, `.`, `-f`, or a tree-ish followed by paths;
  `git switch -f` or `--discard-changes`; `git stash clear`; `git restore` without `--staged` or with
  `--worktree`. A git long option counts in any unique prefix, as git reads it;
- a skipped hook, refused: `--no-verify` on any subcommand, in any prefix git may read as it from `--no-ve`
  (`--no-veri` walked through v7.1), `git commit -n`, and `core.hooksPath` redirected: `-c` and
  `--config-env` in either form (`--config-env core.hooksPath=V` walked through, and its separate value
  was once read as the subcommand), a `GIT_CONFIG_PARAMETERS` or `GIT_CONFIG_KEY_<n>` assignment naming it
  or holding an expansion (git reads both, as it reads `-c`), and `git config` setting it to anything but
  `.githooks`, unsetting it, or dropping the `core` section;
- a git alias, judged as the command it names (`!` and shell text, or git and its words): an alias set by
  `-c alias.x=...` with the words it is then called with, through a chain of aliases as git resolves it
  (`git -c alias.r=reset r --hard` is `git reset --hard`); a persistent one (`git config [set] alias.x ...`) only to a read-only git command, since its
  later calls cannot be paired with it (`git config alias.r reset && git r --hard`); one set through
  `--config-env` or `GIT_CONFIG_*` is refused, its value unread. A config key whose value git runs
  (`core.pager`, `core.fsmonitor`, `core.sshCommand`, `diff.external`, filters, ...) is judged as shell
  text where it is set, and `include.path` is refused: it reads a file this does not open. So are the
  environment variables that stand for them (`GIT_SSH_COMMAND`, `GIT_PAGER`, `GIT_EDITOR`,
  `GIT_EXTERNAL_DIFF`, `PAGER`, `EDITOR`, ...), wherever they are assigned -- one whose value is an
  expansion, appended to (`+=`), written through a subscript (`GIT_PAGER[1,-1]=`), assigned by an expansion
  (`${GIT_PAGER:=...}`), bound by `read`, `printf -v` or zsh's `print -v`, or the target of a `declare -n`
  reference, is refused unread; so is any assignment or binding whose name is braces or an expansion
  (`export {GIT_PA,}GER=`, `printf -v "$n"`). `$HOME` in such a value is the home directory only while
  nothing in the text sets `HOME`. A shell (`!`) alias set beside other `-c` aliases is refused: git hands
  them to the commands it runs;
- `ssh [options] host [options] <words>`: the words are judged as the command line the remote shell runs,
  with no scratch and no place this can name there, and so is `-o RemoteCommand`; `-o ProxyCommand`,
  `LocalCommand` and `KnownHostsCommand` run here and are judged here. OpenSSH reads options after the host
  as well, until `--` or the command's first word (`ssh host -o ProxyCommand=...` runs locally);
- `rm -r`, `mv`, `find -delete`, and `git rm -r` or `git mv` whose operand is this repository, the work
  tree of a directory the command runs in, the home directory, a directory holding one of them, or its
  `.git` or anything inside it -- compared by device and inode, so `../PKG` on a case-insensitive disk is
  the repository (`mv . ../gone` and `git rm -r .` walked through v7.1.1). `git rm` options end at `--`,
  and `:/` and `:(top)` are the top of the work tree; `git rm -r --cached` is not refused. `$PWD` is
  each directory the command runs in, and `$(pwd)` is each of them and also unknown (the command may
  redefine `pwd`), so it is refused as the repository and never scratch;
- `rm` recursive, forced or not -- Claude Code runs Bash with no terminal, so `rm -r` never prompts and
  removes what `rm -rf` removes -- unless every target is scratch: under `$TMPDIR` or the system temp
  directory (the session scratchpad lives there), a `mktemp` result assigned earlier in the same command
  (`d=$(mktemp -d) && rm -rf "$d"`), or a worktree under `.claude/worktrees/`. A relative target is
  resolved from every directory the command may run in (WHERE, below) and must be scratch from each; from
  one this cannot name it is not scratch. `cd <repo> && rm -rf docs` called from a temp directory or a
  worktree once resolved `docs` from the call's directory and passed. `$TMPDIR` counts only when this
  process has it set: its value is substituted, `..` resolved, and the target must lie strictly below it
  -- an unset one once let `rm -rf "$TMPDIR"/x` through, which the shell runs as `rm -rf /x`, and
  `$TMPDIR/..` and `$TMPDIR` itself passed too. Below a `mktemp` result, a `..` leaves it. A `mktemp`
  result is the whole value of a lone `mktemp` (`d=$(mktemp -d; echo /x)` printed a second path), a path
  inside it starts with `/` (`"${d}x"` is its sibling), and `${TMPDIR:-/}x` is not `$TMPDIR`. A target that
  is scratch by place and is or holds a git work tree is refused (a `.git` anywhere below, or more than
  MAX_WALK entries to look through; a pattern's matches are each walked): a v7.1 upgrade lived in a
  worktree under the temp directory, uncommitted. Inside a repository the command runs in -- a worktree the
  agent works in, a checkout under the temp directory -- only that repository's own `.claude/worktrees/<x>`
  is scratch; elsewhere a worktree under `.claude/worktrees/` stays scratch. In a text that makes a link
  (`ln`, `cp -s`) no recursive removal or `find -delete` passes: a link made there can point a scratch
  path anywhere;
- an assignment before a program (`HOME=$(mktemp -d) true`), or behind `env` and the other wrappers, sets
  nothing for later words or commands, and `env -u NAME`, `env -i`, `exec -c`, `sudo` and `doas` leave
  `$TMPDIR` and this text's names unknown for what they run, so from there on the name is unknown (`... && rm -rf "$HOME"`
  removed the real home past v7.1.1). An assignment that may not happen or does not last -- after `&&` or
  `||`, in a branch, a loop, a subshell, a substitution or a pipe -- leaves the name unknown when it had a
  value before; `read`, `mapfile`, `getopts`, `unset`, `printf -v`, `for`, `select`, zsh's `print -v` and
  module binders, `${NAME:=...}`, and `declare -n` (for the reference and its target) make the names they
  bind unknown;
- `source`, `.` or a shell running a `<( )` or zsh `=( )` file, whose commands this cannot read;
- refused: `gh pr merge` and `gh pr ready` with flags anywhere (`gh -R a/b pr merge`, `gh pr -R a/b merge`),
  `gh api` on `/pulls/<n>/merge`, and `gh api` on `/protection` or `/rulesets` with a mutating method
  or a field (`-X PUT`, `--method delete`, `-f`, `-F`, `--input`, `--raw-field`);
- a declared deploy command (`Deploy commands:` in `docs/project-brief.md`) while the deploy gate refuses
  it: the repository is the git work tree of each directory the command may run in (WHERE) when it
  carries a brief, else `$CLAUDE_PROJECT_DIR`, and from a directory this cannot name, both the call's own
  and `$CLAUDE_PROJECT_DIR` (`cd ../other && fly deploy` was once judged by the call's repository). The
  gate run is always THIS repository's `scripts/deploy_gate.py` (OWN), with the judged tree as its
  directory: past v7.1.1 the guard ran the judged tree's own script, so a cloned repository's gate ran on
  the next `ls` in it and its exit 0 passed its deploys. A tree that is neither OWN nor a worktree of it
  is foreign: its brief is read to tell a deploy, and every deploy there is refused. With no gate script
  in OWN, a brief refuses every call, never skips; so does a gate without the line `JUDGE_PROTOCOL = 1`
  (or v7.1's `--judge` dispatch) -- one written before `--judge` reads the flag as the command, finds no
  deploy and exits 0 (a v7.0 gate under the v7.1 guard passed `fly deploy`) -- and, in a foreign tree, a
  gate below `JUDGE_PROTOCOL = 2`, which cannot be told the tree is foreign. A word list judged only in
  foreign trees is judged in OWN as well (`fly deploy --config ../proj/fly.toml` from another repository).
  The gate matches the declared words at command position, case-insensitively, by the program's
  basename: `FLY DEPLOY`, `fly  deploy`, `'fly' deplo'y'`, `/usr/local/bin/fly deploy`, `sudo fly deploy`,
  `bash -c 'fly deploy'` and `a=fly; $a deploy` are all the deploy; `echo 'fly deploy'`
  and `git commit -m 'fly deploy notes'` are not;
- a program word written as a pattern (`gi*`, `{git,ls}`), which could name anything.

This project's own rules (model_ranking: its M21 guard, carried over in the DevFlow v7.1 upgrade by D-199
clause 3 and the owner's patches of #281, and ported onto DevFlow v7.1.2's file by D-205 clause 3):
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY, and `fly` behind `xargs` (D-185),
  whatever the deploy gate says: the hosted engine is deployed and destroyed by the owner only;
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run` (D-185);
- a write into the `.claude/` or `.githooks/` of any git work tree, the owner's hooks and settings (the M21
  closure security seat's S3): a redirection there (`>`, `>>`, `>|`, `&>`, `<>`, `>& file`); `rm`, `mv`,
  `tee`, `touch`, `chmod` and their kind on a path there; `cp`, `ln`, `install`, `rsync`, `ditto` or `dd`
  with a destination there (the last word, or `-t`/`--target-directory` for `cp`, `mv`, `ln` and `install`,
  or `of=` for `dd`); `sed -i` or `perl -i` on one; `find ... -delete` starting there; and `git rm`, `git
  mv`, `git checkout` or `git restore` naming one. Reading them is not refused. The one exception is the
  scratch rule's: `rm` of a directory under `.claude/worktrees/<name>` (a worktree's own `.claude/` and
  `.githooks/` stay refused).
  A directory that holds them is refused too (#282): `rm -r` without `-f`, and `mv` (`git rm`, `git mv`)
  of a source, whose path is a work tree's root with a `.claude/` or `.githooks/` or a directory above one
  (`rm -r .` at a root, `rm -r ..` from `ios/`, `mv ../<repo> x`); the directories below it are walked, links
  not followed, within WALK_S seconds and MAX_WALK directories, and one too large or unreadable to walk is
  refused. (`rm -rf`, and since v7.1.2 `rm -r` too, meets the scratch rule above as well.)
  In a cluster of short options, `t` is `-t` only before any letter that takes a value (VALUED: `install
  -ostaff` names an owner); a `t` after one is doubt, and then every operand is judged a destination, as
  for `install -d` (the fixes review's round 3, M2).
  Which paths, exactly (`protected`; round 2's B1, as round 3's M1 left it): the path, `~` and variables
  expanded, is resolved from each directory the command may run in (WHERE), links followed on its longest
  existing part. The work tree it lies in is the nearest directory above it that holds a `.git` entry, a
  file or a directory: this clone, a linked worktree, any other clone, or a worktree Claude Code made inside
  a repository's `.claude/worktrees/`. The path is refused when the directory directly below that work
  tree's root is named `.claude` or `.githooks`, in any case. Claude Code's own `~/.claude` is not refused,
  as no `.git` sits above it. From a place WHERE cannot name, the path is resolved from every directory a
  `cd`, `chdir` or `pushd` anywhere in the call reaches, from every one reached before it, variables
  expanded as this process holds them (FOLLOWED); past MAX_FOLLOWED of them the call is not read.
  Given `--write`, the guard judges the Write or Edit call's `file_path` instead: a secrets file by name
  (the shell rule's names), or a path `protected` refuses.
- the scratch rule, stricter (the v7.1 upgrade security review's B1 and MAJOR-1): a path that lies inside
  any git work tree, or is or sits above the work tree of a directory this call knows (where it runs,
  `$CLAUDE_PROJECT_DIR`, this checkout), is no scratch, nor is a temp directory itself or one above one;
  `$TMPDIR` is not taken from this process's environment when the text names `TMPDIR` other than to expand
  it (`local TMPDIR`, `export TMPDIR`, `read TMP""DIR`) or runs `unset`, nor a `mktemp` result as a new
  directory when the text defines a function or an alias of that name; and a `cd` into `$TMPDIR` lands
  where it resolves, so what follows is judged there, not as a new directory.

Where it looks: each command after `;`, `&&`, `||`, `|`, `|&`, `&`, a newline, `(`, `)`, `{` or `}`;
inside `$( )`, backticks, `<( )`, `${ }`, `$(( ))` and an unquoted here-document's body; past
assignments, shell keywords and the wrappers in WRAPPERS (after one, every later word is tried as the
program); inside `bash`, `sh`, `zsh`, `dash`, `ksh`, `csh`, `tcsh` or `fish` given `-c`, a script name, a
here-document or a here-string; and inside `eval`, `source`, `.`, `env -S`, `find -exec`, a `trap`'s
command, a shell `alias`'s value and `mapfile -C`'s callback. Text in
single quotes and a quoted here-document's body are data; a `#` that starts a word starts a comment. A
program named through a variable assigned a literal earlier in the same text (`a=git; $a push`) is read
as that program.

WHERE each command runs (`_moved`): the call's `cwd`, then wherever a `cd`, `chdir`, `pushd` or `popd`
before it leads, in order through `;`, `&&`, `||`, newlines and brace groups -- a `cd` that fails stays
put, `&&` and `||` follow its status, and nothing runs on past an `exit`. A `cd` in a subshell, a
substitution, a pipe, behind `&`, in an `eval` or `bash -c` string, or anywhere in a text holding a
branch, a loop or a function may or may not have moved what follows, so both places are kept. A `cd` to
a path written literally, or through a literal or `mktemp` variable of this text, is followed; any other
leads to a directory this cannot name: a variable set elsewhere, a substitution, `-`, `~user`, `pushd
+1`, a `popd` past what this text pushed, a relative path while `CDPATH` is set or in a text holding a
loop or a function (which may run it twice), and a `cd` word where this does not place it (`repeat 3 cd
..`). Past MAX_PLACES places every place becomes one this cannot name.

It refuses what it cannot read rather than reading it as data: an unclosed quote or substitution; a word
with `(` written against it; a `${(flags)...}`; a shell or `source` reading its commands from a pipe, a
file or stdin; a `-c` with no string; an input over MAX_INPUT characters; a payload that is not JSON; and
any call it has not finished judging within DEADLINE_S seconds (a timer thread writes the line and exits
2). A long call into C that holds the interpreter runs to its end first; the hook's own `timeout` and
`"onFailure": "block"` bound that case, from Claude Code 2.1.295.

Not held, by class -- said here so nobody believes otherwise:
- a program named when the command runs: a variable or an alias set outside this text, a function, `hash`,
  a `PATH` holding a script of a guarded name; `xargs <deploy command>` whose subcommand comes on stdin;
- code another program runs: a script's contents (`bash x.sh`), `python -c`, `perl -e`, `node -e`,
  `awk`'s `system()`, `make` recipes, git hooks, an alias set before this call or in a config file this
  does not open, ssh options from `~/.ssh/config`, `scp`, `rsync -e`;
- a `core.hooksPath`, an alias or a pager read from a file this does not open: `GIT_CONFIG_GLOBAL`,
  `git config --edit`, a config file written by another program;
- a wrapper not in WRAPPERS, whose program is then read as an argument;
- a directory changed by what this does not read: a sourced script's `cd`, zsh's `AUTO_CD`, a `CDPATH`
  the shell's startup files set and this process does not see;
- a push to a destination git chooses itself: a bare `git push`, `git push origin HEAD` or `@`, an
  upstream, `push.default`, or a variable set elsewhere naming the ref of a push that does not delete
  (`git push origin "$branch"`; branch protection on the remote is the control there);
- what the shell expands when the command runs, beyond the program word and git's words: `IFS`, history,
  globs and braces in arguments, `${m:-main}`; syntax beyond POSIX-like shell;
- an `mv` or `git rm -r` of the repository through a variable set outside this text or a pattern
  (`mv "$REPO" /x`, `mv * ..`, `git rm -r ':/*'`); a link that existed before this call is followed where
  it resolves, but one another program makes in this call (`python -c`, `tar`, `unzip`, a clone that holds
  a link) is not seen;
- a command on another machine is judged by this machine's rules: `ssh host 'rm -rf /tmp/build'` is
  refused, though `/tmp` is scratch there;
- a write into `.claude/` or `.githooks/` by a program this does not list (`python -c`, `git apply`, `tar`,
  an editor), through a path built when the command runs (`$(...)`, a glob), a hard link made before, or a
  directory reached by a `cd` to a built path, through `CDPATH` or `cd -`.
Stdlib only, Python 3.11 or later.
"""

from __future__ import annotations

import codecs
import fnmatch
import glob
import json
import os
import re
import shlex
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
#: The directory the call runs in (the payload's `cwd`): where WHERE starts.
CWD: dict[str, str] = {"dir": ""}
#: The directories the command being judged may run in (WHERE; `_moved`): each a path, SCRATCH (a `mktemp`
#: result or `$TMPDIR`), or UNKNOWN (a `cd` this cannot read). Relative `rm` targets resolve from each, and
#: each one's repository judges a deploy.
HERE: dict[str, list] = {"dirs": []}
UNKNOWN = object()
#: Every directory a place of this call has named: from a place this cannot name, a deploy is judged in
#: each one's repository too.
REACHED: set[str] = set()
#: Set for the rest of the call once a text holds a loop or a function, which may run a `cd` twice, or
#: assigns `CDPATH`, which may send a relative `cd` elsewhere.
SEEN: dict[str, bool] = {"repeats": False, "cdpath": False, "links": False, "home": False, "home_used": False}
#: Set while the command being judged may not run, or runs apart from what follows (`&&`, `||`, a
#: branch, a loop, a subshell, a substitution, a pipe): an assignment there may or may not hold after it.
FLOW: dict[str, bool] = {"maybe": False}
#: More places than this (each `;`-joined `cd` may fail and stay), and they become one this cannot name.
MAX_PLACES = 64
#: `name -> literal value` for assignments seen in this text, or SCRATCH for a `mktemp` result.
SCOPE: dict[str, object] = {}
SCRATCH = object()
#: `name -> the name it refers to`, for each `declare -n` in this text: assigning one assigns the other.
NAMEREF: dict[str, str] = {}
#: Every word list in program position, with the directories it may run in, for the deploy gate.
CANDIDATES: list[tuple[list, list[str]]] = []
#: Above zero while the words judged run on another machine (`ssh host <words>`): no path there is
#: scratch, and none is this repository.
REMOTE: dict[str, int] = {"on": 0}
#: `directory -> its git work tree` (None outside one), asked once per call.
TOPS: dict[str, str | None] = {}
#: The repository this guard belongs to: the guard lives at `<it>/.claude/hooks/bash_guard.py`, which is
#: where the hook command found it. Only this repository's deploy gate is ever run.
OWN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
#: Past this many entries a scratch directory is not walked for a work tree, and is not scratch; past this many
#: directories, a target of `rm -r` or `mv` is not walked for the owner's directories (#282) and is refused.
MAX_WALK = 20000
#: How long, in all, one call may spend walking directories for the owner's directories (`_walk`).
WALK_S = 4.0
WALK: dict[str, float] = {"left": WALK_S}
#: Whether this call may take `$TMPDIR` as the guard's own environment holds it, and a `mktemp` result as a new
#: directory (the v7.1 upgrade security review's B1). Not `$TMPDIR` when the text names `TMPDIR` other than to
#: expand it (`export`, `local`, `read`, `for TMPDIR in`) or runs `unset`; not `mktemp` when it defines a function
#: or an alias of that name.
TRUST: dict[str, bool] = {"TMPDIR": True, "mktemp": True}
TMPDIR_NAMED = re.compile(r"(?<![\w$])(?<!\$\{)TMPDIR\b|(?:^|[\s;&|(){}!`])unset\b")
MKTEMP_DEFINED = re.compile(r"\bmktemp\s*\(\s*\)|\bfunction\s+mktemp\b|\balias\b[^;&|\n]*\bmktemp=")
#: Every directory a `cd`, `chdir` or `pushd` in this call reaches, from every one reached before it, variables
#: expanded as this process holds them (`_follow_all`): where a written path is resolved from a place WHERE
#: cannot name, for the owner's-directory rule. Past MAX_FOLLOWED, `over`, and such a call is not read.
FOLLOWED: dict[str, list] = {"dirs": [], "over": []}
MAX_FOLLOWED = 4096

#: Words that run the command after them; every later word is tried as that command.
WRAPPERS = {"env", "command", "builtin", "time", "exec", "nohup", "nice", "sudo", "doas", "xargs", "timeout",
            "gtimeout", "caffeinate", "coproc", "noglob", "nocorrect", "-", "repeat", "function", "stdbuf",
            "setsid", "watch", "unbuffer", "script", "chronic", "ionice", "taskpolicy"}
#: Shell words a command follows on its line: `then git push` runs `git push`.
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "fi", "done", "esac", "[", "[["}
#: Builtins whose assignment-shaped arguments set variables.
SETTERS = {"export", "declare", "local", "typeset", "readonly"}
#: The builtins that change the shell's directory; the words before one that still run it in this shell;
#: and the words that start a loop or a function, which may run a `cd` more than once.
DIR_CHANGES = {"cd", "chdir", "pushd", "popd"}
IN_SHELL = {"builtin", "command", "time", "noglob", "nocorrect"}
LOOPS = {"for", "while", "until", "select", "foreach", "repeat", "function"}
COMPOUND = LOOPS | {"if", "then", "else", "elif", "fi", "case", "esac", "do", "done"}
SHELLS ={"bash", "sh", "zsh", "dash", "ksh", "csh", "tcsh", "fish"}
#: A shell or `source` given one of these reads its commands from stdin.
STDIN_PATHS = {"-", "/dev/stdin", "/dev/fd/0", "/proc/self/fd/0"}
PROTECTED = {"main", "master", "trunk"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?=")
#: A variable name as an assignment or a binder writes it, a subscript and `+` allowed.
NAME_WORD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?$")
#: `${NAME=...}`, `${NAME:=...}` and zsh's `${NAME::=...}` assign NAME as they expand.
EXPANSION_ASSIGN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:::?=|=)")
#: The environment variables git reads configuration from, `-c` included (`git help config`, ENVIRONMENT).
GIT_CONFIG_ENV = re.compile(r"^GIT_CONFIG_(PARAMETERS|KEY_[0-9]+)$")
#: `$name` or `${name}`, nothing else: `${TMPDIR:-/}x` is an expansion this cannot read, not `$TMPDIR`.
VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")
MKTEMP = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*g?mktemp\b")
#: The programs this guard reads; a program word written as a pattern is refused outright.
#: This project's hosted-engine deploy script (D-185).
DEPLOY = "deploy_hosted_engine.sh"
GUARDED = {"git", "rm", "mv", "gh", "ssh", "eval", "source", ".", "find", "fly", "flyctl", DEPLOY, *SHELLS, *WRAPPERS,
           *SETTERS}
#: Programs that bind a variable from their input or their words: after them the name is unknown.
BINDERS = {"read", "mapfile", "readarray", "getopts", "unset", "printf", "for", "select", "foreach",
           # zsh's: `print -v NAME`, `strftime -s NAME`, the module builtins that fill a named variable
           "print", "strftime", "zparseopts", "vared", "getln", "sysread", "zstat", "zformat", "zregexparse",
           "pcre_match", "zstyle", "zselect", "zsystem", "ztcp", "zsocket"}
#: Persistent aliases may name only these: a later `git <alias> <args>` is a call whose arguments this
#: guard reads as an unknown subcommand's, so an alias to anything that writes is refused where it is set.
ALIAS_SAFE = {"status", "log", "diff", "show", "describe", "shortlog", "blame", "grep", "ls-files", "ls-tree",
              "rev-parse", "fetch", "cat-file", "show-ref", "range-diff", "whatchanged", "help", "version"}
#: Environment variables whose value a program runs as a command (git's and the shell's pagers, editors,
#: ssh): judged as shell text wherever they are assigned, as the config keys they stand for are.
CODE_ENV = {"GIT_SSH_COMMAND", "GIT_SSH", "GIT_PAGER", "GIT_EDITOR", "GIT_SEQUENCE_EDITOR", "GIT_EXTERNAL_DIFF",
            "GIT_ASKPASS", "GIT_PROXY_COMMAND", "SSH_ASKPASS", "PAGER", "EDITOR", "VISUAL", "MANPAGER"}
#: Config keys whose value git runs as a command, as an alias's `!` is run: judged as shell text where set.
CODE_KEY = re.compile(r"^(core\.(pager|editor|fsmonitor|sshcommand|askpass)|sequence\.editor|diff\.external|"
                      r"diff\..+\.(textconv|command)|merge\..+\.driver|filter\..+\.(clean|smudge|process)|"
                      r"credential(\..+)?\.helper|gpg(\..+)?\.program|pager\..+|uploadpack\.packobjectshook|"
                      r"include\.path|includeif\..+\.path)$", re.I)
#: `git config` options that take the next word as their value.
CONFIG_VALUED = {"--comment", "--type", "--default", "--file", "-f", "--blob", "--value"}
#: `ssh` options that take a value, as `ssh(1)` lists them; every other letter is a flag.
SSH_VALUED = set("BbcDEeFIiJLlmOoPpQRSWw")
#: `ssh -o` options whose value is a command run on this machine, and the one run on the remote.
SSH_LOCAL = {"proxycommand", "localcommand", "knownhostscommand"}
SSH_REMOTE = {"remotecommand"}
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
RESTORE = ("BLOCKED: `git restore` without --staged, or with --worktree, discards uncommitted work "
           "(permission-matrix.md S5). Revert in place, or use --staged to unstage only.")
HOLDS_OWNED = ("BLOCKED: `{path}` holds a git work tree's .claude/ or .githooks/, the owner's hooks and settings; "
               "removing or moving it removes them (#282, OWNER APPROVAL). To drop a throwaway worktree, use "
               "`git worktree remove <path>`.")
UNWALKED = ("BLOCKED: `{path}` is too large or unreadable to tell whether it holds a git work tree's .claude/ or "
            ".githooks/ (#282), so it is not removed or moved; name a smaller path.")
OWNERS = ("BLOCKED: .claude/ and .githooks/ hold the owner's hooks and settings; an agent does not write them "
          "(OWNER APPROVAL, the M21 closure security seat's S3). Propose the change instead.")
FLY = ("BLOCKED: `{shown}` may change the hosted engine, and only the owner runs that, in their own terminal "
       "(D-185, permission-matrix.md S3); an agent may run only the read-only subcommands.")
DEPLOY_SCRIPT = ("BLOCKED: the hosted engine is deployed by the owner, in their own terminal (D-185); an agent "
                 "may run the script with --dry-run only.")
PROTECTED_PUSH = ("BLOCKED: the agent never pushes the protected branch (AGENTS.md S3). Push YOUR branch and open a "
                  "draft PR; a human marks it ready and merges.")
NO_VERIFY = ("BLOCKED: `--no-verify` and a redirected `core.hooksPath` skip the gate a hook runs (AGENTS.md S3): "
             "a hook you skipped is a gate you removed. Fix what is red, or ask the owner.")
UNREAD_DELETE = ("BLOCKED: this push deletes `{ref}`, a name this guard cannot read, and it may be the protected "
                 "branch (AGENTS.md S3). Write the branch name, or assign it a literal earlier in the command.")
ENV_WRITE = "BLOCKED: writes to .env are denied per permission-matrix.md S6 (default-deny secrets)."
PROTECTED_REF = ("BLOCKED: the agent never moves or deletes the protected branch's ref (AGENTS.md S3): "
                 "the default branch is the human's.")
ENV_EXEMPT = {".env.example", ".env.sample", ".env.template"}
GH_MERGE = ("BLOCKED: a human marks a pull request ready and merges it, never the agent (AGENTS.md S3). "
            "Leave the draft for the owner.")
GH_PROTECTION = "BLOCKED: branch protection and rulesets are the owner settings (AGENTS.md S3). Propose the change and stop."
NOT_JSON = "BLOCKED: this guard cannot read the tool call -- the payload is not a JSON object."
GATE_MISSING = ("BLOCKED: deploy gate -- {root} declares deploy commands in docs/project-brief.md and {own} has no "
                "scripts/deploy_gate.py, so no command can be told from a deploy. Restore the script "
                "(INSTALL-MANIFEST.md); the guard never skips this check.")
GATE_OLD = ("BLOCKED: deploy gate -- {gate} predates this guard: it carries no `JUDGE_PROTOCOL = {need}` line, so it "
            "would {why}. Upgrade the deploy gate to the guard's version (UPGRADING.md); the guard never skips "
            "this check.")
ALIAS_UNREAD = ("BLOCKED: this git alias takes its value from the environment (`--config-env`, `GIT_CONFIG_*`), "
                "which this guard cannot read, and an alias can run any command. Write the git command itself.")
PROJECT_TREE = ("BLOCKED: `{target}` is this repository, its `.git`, the home directory, or a directory holding one "
                "(permission-matrix.md S5): removing or moving it loses every uncommitted change. Escalate to the "
                "owner instead.")
HOLDS_REPO = ("BLOCKED: `{target}` is scratch by place but holds a git work tree (or more files than this guard "
              "looks through), and a work tree can hold the only copy of uncommitted work: a v7.1 upgrade lived "
              "in one under the temp directory. A worktree goes with `git worktree remove`; a clone you made goes "
              "with `rm -rf` in the same command that cloned it; otherwise ask the owner.")
ALIAS_SHELL = ("BLOCKED: a shell (`!`) git alias set beside other `-c` aliases: git hands them to the commands it "
               "runs, so a `git` there can call any of them, which this guard cannot pair. Write the command itself.")
NAME_UNREAD = ("BLOCKED: this sets a variable through a name this guard cannot read (an expansion, braces, a "
               "reference without a literal target): it may be `GIT_PAGER`, `EDITOR`, `HOME` or `TMPDIR`. "
               "Write the name.")
HOME_REBOUND = ("BLOCKED: this sets `HOME` and names a pager or an editor through `$HOME`: the program is run "
                "with the `HOME` it is given, which this guard cannot read. Write the path literally.")
CODE_ENV_UNREAD = ("BLOCKED: `{name}` is a command a program runs, and its value here is an expansion this guard "
                   "cannot read. Write the command literally.")
INCLUDED = ("BLOCKED: `{key}` makes git read another config file, which this guard does not open -- it can set "
            "`core.hooksPath`, an alias or a pager there. Set the key you need directly.")
LINKED = ("BLOCKED: this command makes a link (`ln`, `cp -s`) and removes a tree recursively: a link made here can "
          "point a scratch path at any directory. Make the link and remove the tree in separate calls.")
ALIAS_PERSIST = ("BLOCKED: `git config` setting alias `{name}` to `{value}`: a later `git {name} <args>` runs it with "
                 "arguments this guard cannot pair with it. A persistent alias may name only a read-only git command "
                 "(status, log, diff, show, ...); write the command itself.")
#: A gate that answers `--judge`: the line `JUDGE_PROTOCOL = <n>`, n at least 1, or v7.1's dispatch, which
#: predates the line. A gate with neither was written before `--judge` and would answer it with exit 0.
JUDGE_LINE = re.compile(r'^JUDGE_PROTOCOL = ([0-9]+)[ \t]*$|^    if argv == \["--judge"\]:[ \t]*$', re.M)

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
    procsub: bool = False                           # a `<( )` or zsh `=( )` file is among its words
    writes: list[Word] = field(default_factory=list)   # the targets of its `>`, `>>`, `>|`, `&>`, `<>`, `>&`
    joined: str = ""                                # what joins it to the command before
    inner: int = 0                                  # inside a substitution or a here-document's expansion
    subshell: bool = False                          # inside `( )`: a `cd` there does not outlive it


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
                cmd = self._end(cmd, piped=op in ("|", "|&"), joined=op)
            elif c == "(":
                if cmd.words and last_end == self.i:
                    if s.startswith("()", self.i):  # `name()`: a function's name is no command
                        SEEN["repeats"] = True      # and its body's `cd` runs at every call
                        self.i += 2
                        cmd = Command()
                    elif cmd.words[-1].text.endswith("="):  # `x=(a b)`: each element read as a command
                        cmd.procsub = cmd.procsub or cmd.words[-1].text == "="   # zsh's `=( )` is a file
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
                    cmd = self._end(cmd)  # a brace group's edge
                    continue
                cmd.words.append(word)
                cmd.subshell = cmd.subshell or parens > 0
                if word.text == "in" and len(cmd.words) >= 3 and cmd.words[0].text == "case":
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
            cmd.procsub = cmd.procsub or op == "<("
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
    """Why the command must be refused, or None. Every simple command in it is judged in order, from each
    directory it may run in (WHERE). A place is (directory, the last command's status, the `pushd` stack)."""
    if len(text) > MAX_INPUT:
        raise Unreadable(f"the command is over {MAX_INPUT} characters")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lexer = Lexer(text, depth)
    lexer.parse()
    lexer._bodies()  # a here-document opened on the last line runs to the end
    commands = lexer.commands
    _follow_all(commands)
    compound = False   # a branch or a loop body may not run at all: no `cd` in this text is taken as made
    for c in commands:
        k = next((j for j, w in enumerate(c.words) if w.text not in KEYWORDS), len(c.words))
        lead = [w.text for w in c.words[:k + 1] if not w.quoted]
        SEEN["repeats"] = SEEN["repeats"] or bool(LOOPS & set(lead))
        compound = compound or bool(COMPOUND & set(lead))
        # A link made anywhere in this text can turn a scratch path into any directory (`ln -s ~/proj
        # /tmp/x && rm -rf /tmp/x/src` resolved /tmp/x before the link existed).
        names = [os.path.basename(w.text) for w in c.words if not w.quoted]
        if {"ln", "link"} & set(names) or ("cp" in names and any(
                w.text == "--symbolic-link" or re.match(r"^-[A-Za-z]*s", w.text) for w in c.words)):
            SEEN["links"] = True
    entry = list(HERE["dirs"])
    places: list[tuple] = [(d, True, ()) for d in entry]
    top = [k for k, c in enumerate(commands) if not c.inner]
    following = {k: commands[j] for k, j in zip(top, top[1:])}
    for k, cmd in enumerate(commands):
        runs = places
        if not cmd.inner and cmd.joined in ("&&", "||"):
            runs = [p for p in places if p[1] == (cmd.joined == "&&")] or places
        dirs = list(dict.fromkeys(p[0] for p in runs))
        HERE["dirs"] = dirs
        nxt = following.get(k)
        outer = FLOW["maybe"]
        FLOW["maybe"] = outer or bool(compound or SEEN["repeats"] or cmd.inner or cmd.subshell or cmd.piped
                                      or (not cmd.inner and cmd.joined in ("&&", "||"))
                                      or (nxt is not None and nxt.joined in ("&", "|", "|&")))
        try:
            why = judge_command(cmd, depth)
        finally:
            FLOW["maybe"] = outer
        if why:
            return why
        # A `cd` in an `eval` or `bash -c` string this command ran: the nested text added its places.
        nested = [d for d in HERE["dirs"] if d not in dirs]
        moved = _moved(cmd, runs) + [(d, s, ()) for d in nested for s in (True, False)]
        scoped = (compound or SEEN["repeats"] or cmd.inner or cmd.subshell or cmd.piped
                  or (nxt is not None and nxt.joined in ("&", "|", "|&")))
        places = list(dict.fromkeys(places + moved if scoped else moved + [p for p in places if p not in runs]))
        REACHED.update(p[0] for p in places if isinstance(p[0], str))
        if len(places) > MAX_PLACES:
            places = [(UNKNOWN, True, ()), (UNKNOWN, False, ())]
    HERE["dirs"] = list(dict.fromkeys(entry + [p[0] for p in places]))
    return None


# --- where a command runs -----------------------------------------------------------------------------

def _change(cmd: Command) -> tuple[str, list[Word], bool] | object | None:
    """(the builtin, its operands, negated by `!`) for a `cd`, `chdir`, `pushd` or `popd` this shell runs;
    UNKNOWN for a `cd` word where this cannot place it (`repeat 3 cd ..`, `echo cd`); None for any other."""
    words = cmd.words
    i, negated = 0, False
    while i < len(words) and (ASSIGNMENT.match(words[i].text) or words[i].text in KEYWORDS):
        negated = negated or words[i].text == "!"
        i += 1
    while i < len(words) and words[i].text in IN_SHELL:
        if words[i].text == "command" and i + 1 < len(words) and words[i + 1].text.startswith("-"):
            break
        i += 1
        while words[i - 1].text == "time" and i < len(words) and words[i].text.startswith("-"):
            i += 1
    if i < len(words) and words[i].text in DIR_CHANGES:
        name, operands = words[i].text, words[i + 1:]
        if name in ("cd", "chdir"):  # `-L`, `-P`, `-e`, `-@`, then `--`
            while operands and operands[0].text.startswith("-") and operands[0].text != "-":
                done, operands = operands[0].text == "--", operands[1:]
                if done:
                    break
        return name, operands, negated
    if any(not w.quoted and w.text in DIR_CHANGES for w in words[i:]):
        return UNKNOWN
    return None


def _inward(rest: str) -> bool:
    """Whether a path below a scratch directory stays below it: no `..`, no expansion, no pattern."""
    return "$" not in rest and not any(ch in rest for ch in "*?[{") and ".." not in rest.replace("\\", "/").split("/")


def _below(rest: str) -> bool:
    """Whether what follows a scratch directory's variable names it or a path inside it: nothing, or `/` and
    a path that stays below. `"${d}x"` is a sibling of the directory, not inside it."""
    return rest == "" or (rest.startswith("/") and "$" not in rest
                          and ".." not in rest.replace("\\", "/").split("/"))


def _name(m: re.Match) -> str:
    return m.group(1) or m.group(2)


def _enter(base: object, word: Word) -> list:
    """Where a `cd` to `word` from `base` lands: as the shell reads `..` and as the disk does; SCRATCH for a
    `mktemp` result or `$TMPDIR` and a path inside it; UNKNOWN for what this cannot name."""
    text = word.text
    if text.startswith(("-", "+")):
        return [UNKNOWN]   # `cd -`, `pushd +1`, `pushd -n dir`
    m = VARIABLE.match(text)
    if m and _variable(_name(m)) is SCRATCH:
        rest = text[m.end():]
        return [SCRATCH] if _below(rest) and _inward(rest) else [UNKNOWN]
    if m and _name(m) == "TMPDIR" and "TMPDIR" not in SCOPE:
        # model_ranking: `$TMPDIR` as this process has it, the path below it resolved -- the temp directory may
        # hold work trees (MAJOR-1), so what runs there is judged there, not as a new directory's.
        value, rest = _variable("TMPDIR"), text[m.end():]
        if not isinstance(value, str) or not (_below(rest) and _inward(rest)):
            return [UNKNOWN]   # `$TMPDIR` unset here: the shell's may be empty too
        root, landed = os.path.realpath(value), os.path.realpath(value + rest)
        if root == os.path.sep or not (landed == root or landed.startswith(root.rstrip(os.sep) + os.sep)):
            return [UNKNOWN]
        return [landed]
    text = _expand(text)
    if "$" in text or word.glob or not text:
        return [UNKNOWN]
    if text == "~" or text.startswith("~/"):
        text = os.path.expanduser(text)
    elif text.startswith("~"):
        return [UNKNOWN]   # `~user`
    if not os.path.isabs(text):
        if SEEN["repeats"] or ((SEEN["cdpath"] or os.environ.get("CDPATH"))
                               and not text.startswith(("./", "../")) and text not in (".", "..")):
            return [UNKNOWN]
        if base is UNKNOWN:
            return [UNKNOWN]
        if base is SCRATCH:
            return [SCRATCH] if _inward(text) else [UNKNOWN]
        text = os.path.join(str(base), text)
    return list(dict.fromkeys([os.path.normpath(text), os.path.realpath(text)]))


def _moved(cmd: Command, runs: list[tuple]) -> list[tuple]:
    """The places after `cmd` ran from each of `runs`: a directory change lands where it names, or fails
    and stays; any other command stays, with either status."""
    change = _change(cmd)
    either = [(d, s, stack) for d, _, stack in runs for s in (True, False)]
    lead = next((w.text for w in cmd.words if w.text not in KEYWORDS and not ASSIGNMENT.match(w.text)), "")
    if lead == "exit" and change is None:
        return []   # `cd "$d" || exit 1`: nothing after it runs from where it ran
    if change is None:
        return either
    if change is UNKNOWN:
        return either + [(UNKNOWN, s, ()) for s in (True, False)]
    name, operands, negated = change
    out: list[tuple] = []
    for d, _, stack in runs:
        out.append((d, False, stack))
        if name == "popd" or (name == "pushd" and not operands):
            # Back to the top of the stack this text pushed (`pushd` alone swaps the two); past it, unknown.
            if operands or not stack:
                out.append((UNKNOWN, True, ()))
            else:
                out.append((stack[0], True, stack[1:] if name == "popd" else (d,) + stack[1:]))
            continue
        if len(operands) > 1:
            out.append((UNKNOWN, True, ()))   # zsh's `cd old new`
            continue
        pushed = (d,) + stack if name == "pushd" else stack
        for landed in _enter(d, operands[0] if operands else Word("~")):
            out.append((landed, True, pushed))
    return [(d, s, st) for d, _, st in out for s in (True, False)] if negated else out


def _assign(word: Word) -> None:
    """Record `name=value` for the rest of this text: a literal, a `mktemp` result, or unknown."""
    name, _, value = word.text.partition("=")
    if name.rstrip("+") == "CDPATH":
        SEEN["cdpath"] = True
    _bound(name.rstrip("+").split("[")[0])
    if name.endswith("+") or "[" in name:
        SCOPE[name.rstrip("+").split("[")[0]] = UNKNOWN
        return
    # Only the whole value, and only a lone `mktemp`: `$(mktemp -d; echo /x)` prints a second path, and
    # `$(mktemp -d)/../x` leaves the directory.
    if value == "$(...)" and len(word.subs) == 1 and _mktemp_only(word.subs[0]) and TRUST["mktemp"]:
        new: object = SCRATCH
    elif "$" not in value and not word.glob:
        new = value
    else:
        new = UNKNOWN   # assigned something this cannot read: it shadows the environment's value
    # An assignment that may not happen, or happens apart from what follows (`false && d=$(mktemp -d)`,
    # `(d=...)`), leaves the name what it was -- this text's value or the environment's -- or the new one.
    if FLOW["maybe"] and (name in SCOPE or name in os.environ) and SCOPE.get(name, None) is not new \
            and SCOPE.get(name) != new:
        new = UNKNOWN
    SCOPE[name] = new


def _binds(words: list[Word], start: int) -> None:
    """`read`, `mapfile`, `getopts`, `unset`, `printf -v`, `for`/`select` and `declare -n` set a name from
    input or by reference: from here on it is unknown (`read -r d <<< "$HOME"; rm -rf "$d"`)."""
    program = os.path.basename(words[start].text)
    rest = words[start + 1:]
    names: list[str] = []
    if program == "printf":
        names = [rest[k + 1].text for k, w in enumerate(rest[:-1]) if w.text == "-v"]
        names += [w.text[2:] for w in rest if w.text.startswith("-v") and len(w.text) > 2]   # `-vNAME`
    elif program in ("for", "select", "foreach"):
        names = [w.text for w in rest[:1]]
    elif program in BINDERS:
        names = [w.text for w in rest if not w.text.startswith("-")]
        # zsh's `print -vNAME`, `strftime -sNAME`, `zstat -ANAME`: the name written against its option.
        names += [w.text[2:] for w in rest if re.match(r"^-[vsAaFH][A-Za-z_]", w.text)]
        if program in ("mapfile", "readarray"):
            # `mapfile -C 'cmd'` runs its callback as shell text.
            for k, w in enumerate(rest):
                code = (rest[k + 1].text if w.text == "-C" and k + 1 < len(rest) else
                        w.text[2:] if w.text.startswith("-C") and len(w.text) > 2 else None)
                if code is not None and (why := judge_text(code, 1)):
                    raise Unreadable(why)
    elif program in SETTERS and any(re.match(r"^-[A-Za-z]*n", w.text) for w in rest):
        for w in rest:
            if w.text.startswith("-"):
                continue
            name, eq, target = w.text.partition("=")
            # `declare -n r=GIT_PAGER; r='rm -rf ~'` assigns GIT_PAGER through r, and `declare -n r` takes its
            # target from the next `r=...`: the target must be a literal name, and no command a program runs.
            if not eq or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", target) or CODE_ENV & {name, target}:
                raise Unreadable(NAME_UNREAD)
            NAMEREF[name] = target
            names += [name, target]
    for n in names:
        if "$" in n or "`" in n:   # `printf -v "$n"`, `read "$n"`: a name this cannot read
            raise Unreadable(NAME_UNREAD)
        n = n.split("[")[0]
        if n in CODE_ENV:
            raise Unreadable(CODE_ENV_UNREAD.format(name=n))
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", n):
            _bound(n)
            SCOPE[n] = UNKNOWN


def _mktemp_only(text: str) -> bool:
    """A substitution that runs `mktemp` and nothing else: no second command, no redirection, no expansion."""
    return bool(MKTEMP.match(text)) and not any(ch in text for ch in ";&|`$<>()\n")


def _shadow(word: Word) -> None:
    """A prefix assignment (`NAME=value cmd`) sets nothing for the shell: the command's own words and every
    later command expand NAME as before. What that is, this cannot say, so NAME is unknown from here on
    (`HOME=$(mktemp -d) true && rm -rf "$HOME"` removed the real home past v7.1.1)."""
    name = word.text.partition("=")[0].rstrip("+").split("[")[0]
    if name == "CDPATH":
        SEEN["cdpath"] = True
    _bound(name)
    SCOPE[name] = UNKNOWN


def _bound(name: str) -> None:
    """`name` takes a value here: a `declare -n` reference passes it to its target, and `HOME` set after a
    pager or an editor was read through `$HOME` changes what that runs (`export GIT_EDITOR='$HOME/ed'; HOME='rm
    -rf ~ ' git commit`)."""
    target = NAMEREF.get(name)
    if target:
        SCOPE[target] = UNKNOWN
    if "HOME" in (name, target):
        if SEEN["home_used"]:
            raise Unreadable(HOME_REBOUND)
        SEEN["home"] = True


def _variable(name: str) -> object:
    """What `$name` stands for here: the literal or SCRATCH this text assigned it, UNKNOWN for any other
    assignment, `$TMPDIR` as this process's environment has it (None when unset or empty); else None."""
    if name in SCOPE:
        return SCOPE[name]
    return (os.environ.get("TMPDIR") or None) if name == "TMPDIR" and TRUST["TMPDIR"] else None


def _expand(text: str) -> str:
    """A word with each `$name` or `${name}` replaced by the literal assigned to it earlier in this text.
    A variable this text did not assign a literal to stays as written."""
    def one(m: re.Match) -> str:
        value = SCOPE.get(_name(m))
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
    # `: ${GIT_PAGER:='rm -rf ~'}` and `: ${d::=/}` assign as they expand.
    for w in words:
        for name in EXPANSION_ASSIGN.findall(w.text):
            if name in CODE_ENV:
                return CODE_ENV_UNREAD.format(name=name)
            _bound(name)
            SCOPE[name] = UNKNOWN
    start = 0
    while start < len(words) and (ASSIGNMENT.match(words[start].text) or words[start].text in KEYWORDS):
        start += 1
    assigned = [w for w in words[:start] if ASSIGNMENT.match(w.text)]
    for w in assigned:
        if (why := _config_env(w)):
            return why
    # Alone, assignments set shell variables; before a program, only that program's environment.
    for w in assigned:
        (_assign if start >= len(words) else _shadow)(w)
    if start >= len(words):
        return None
    _binds(words, start)
    first = _program(words[start])
    if first in SETTERS:
        for w in words[start + 1:]:
            # `export {GIT_PA,}GER='...'` (the shell expands the braces into assignments) and
            # `export "$n"='...'` assign a name this cannot read.
            if "=" in w.text and not w.text.startswith("-") and not NAME_WORD.match(w.text.partition("=")[0]):
                return NAME_UNREAD
            if ASSIGNMENT.match(w.text):
                if (why := _config_env(w)):
                    return why
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
        # `env -i`, `exec -c`, `sudo` and `doas` start the program with an environment of their own, and `env -u
        # NAME` without NAME: `env -u TMPDIR sh -c 'rm -rf "$TMPDIR"/x'` runs `rm -rf /x`.
        if program in ("sudo", "doas") or (program == "exec" and any(
                re.match(r"^-[A-Za-z]*c", w.text) for w in words[k + 1:k + 4])) or (program == "env" and any(
                w.text == "-" or (w.text.startswith("--") and len(w.text) >= 3
                                  and "--ignore-environment".startswith(w.text.split("=")[0]))
                or re.match(r"^-[^-]*i", w.text) for w in _env_options(words[k + 1:]))):
            for name in list(SCOPE) + ["TMPDIR"]:
                SCOPE[name] = UNKNOWN
        if program == "env":
            for j, w in enumerate(words[k + 1:], k + 1):
                t = w.text
                gone = (words[j + 1].text if t in ("-u", "--unset") and j + 1 < len(words) else
                        t[2:] if t.startswith("-u") and len(t) > 2 and not t.startswith("--") else
                        t.split("=", 1)[1] if t.startswith("--unset=") else None)
                if gone:
                    SCOPE[gone] = UNKNOWN
        if program == "env":
            j = k + 1
            while j < len(words) and (words[j].text.startswith("-") or ASSIGNMENT.match(words[j].text)):
                arg = words[j].text
                text = (words[j + 1].text if arg in ("-S", "--split-string") and j + 1 < len(words) else
                        arg.split("=", 1)[1] if arg.startswith("--split-string=") else
                        arg[2:] if arg.startswith("-S") and len(arg) > 2 else None)
                # `-S` carries env's own options as well as the program: judged as an `env` line.
                if text is not None and (why := judge_text("env " + text, depth + 1)):
                    return why
                j += 1
        if k > start and word.text.startswith("-") and word.text != "-":
            continue
        if ASSIGNMENT.match(word.text):
            if (why := _config_env(word)):  # `env GIT_CONFIG_KEY_0=core.hooksPath ... git commit`
                return why
            _shadow(word)   # `env TMPDIR=/Users sh -c 'rm -rf "$TMPDIR"/x'`: the child's value, not this text's
            continue
        if program in WRAPPERS and k != len(words) - 1:
            continue
        tried += 1
        if tried > 64:
            raise Unreadable("more than 64 words behind wrappers")
        if (why := judge_words(words[k:], cmd, depth, behind_xargs=xargs_at < k)):
            return why
    return None


def _env_options(words: list[Word]) -> list[Word]:
    """`env`'s own options and assignments, up to the program it runs."""
    out: list[Word] = []
    for w in words:
        if not (w.text.startswith("-") or ASSIGNMENT.match(w.text)):
            break
        out.append(w)
    return out


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
    CANDIDATES.append((list(HERE["dirs"]), [_expand(first.text[1:] if first.equals else first.text)] + args))
    if (why := _writes_protected(program, [_expand(a) for a in args])):
        return why
    if program == "eval":
        return judge_text(" ".join(args), depth + 1)
    # `trap 'cmd' EXIT` runs its text when the shell exits or takes the signal.
    if program == "trap" and args and args[0] not in ("-", "-l", "-p", "--") and not args[0].isdigit():
        return judge_text(args[0], depth + 1)
    # `alias ls='rm -rf ~'` and a later line's `ls`: an alias is the text it names.
    if program == "alias":
        for a in args:
            if "=" in a and not a.startswith("-") and (why := judge_text(a.partition("=")[2], depth + 1)):
                return why
    if cmd.procsub and (program in ("source", ".") or program in SHELLS):
        return (f"BLOCKED: `{program}` running a `<( )` or `=( )` file, whose commands this guard cannot read; "
                "run the commands themselves, or the script by its name.")
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
            if (hit := _project_tree(starts)):
                return PROJECT_TREE.format(target=hit)
            if not starts or REMOTE["on"] or not all(_scratch(w) for w in starts):
                return DESTRUCTIVE
            if SEEN["links"]:
                return LINKED
            if _not_scratch_here(starts, above=True):
                return DESTRUCTIVE
            if (held := _holding(starts)):
                return HOLDS_REPO.format(target=held)
            if _not_scratch_here(starts):
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
    if program == "mv" and (hit := _project_tree(_mv_sources(words[1:]))):
        return PROJECT_TREE.format(target=hit)
    if program == "git":  # its ref words with this text's literals in (`m=main; git push origin --delete $m`)
        return _judge_git([_expand(a) for a in args], behind_xargs, depth)
    if program == "rm":
        return _judge_rm(words[1:])
    if program == "gh":
        return _judge_gh(args)
    if program == "ssh":
        return _judge_ssh(args, depth)
    return None


def _mv_sources(words: list[Word]) -> list[Word]:
    """What `mv` moves: every operand but the last, or every operand when `-t` names the destination --
    `-t`, a cluster ending in it (`-vt`), or `--target-directory` in any prefix GNU reads (`--target`)."""
    operands: list[Word] = []
    target = False
    skip = False
    for k, w in enumerate(words):
        if skip:
            skip = False
            continue
        t = w.text
        if t == "--":
            operands += words[k + 1:]
            break
        if t.startswith("--") and len(t) > 2:
            name, eq, _ = t.partition("=")
            if len(name) >= 3 and "--target-directory".startswith(name):
                target, skip = True, not eq
            elif len(name) >= 4 and "--suffix".startswith(name):
                skip = not eq
            continue
        if t.startswith("-") and len(t) > 1:
            for j, ch in enumerate(t[1:], 1):
                if ch in "tS":
                    target = target or ch == "t"
                    skip = j == len(t) - 1
                    break
            continue
        operands.append(w)
    return operands if target else operands[:-1]


# --- this project's rule: the owner's directories, .claude/ and .githooks/ of any work tree ---------------
#
# The M21 closure security seat's S3, its fixes reviews' rounds 2 and 3, and #282 (model_ranking; D-199 clause
# 3, D-205 clause 3). The one exception is a worktree under `.claude/worktrees/<name>`, Claude Code's and the
# seats' throwaway checkouts. The way to drop one is `git worktree remove <path>` (`--force` with changes in it):
# git deletes the directory and prunes its record, and the guard does not refuse it.

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


def _follow_all(commands: list[Command]) -> None:
    """Each directory a `cd`, `chdir` or `pushd` in these commands names, from every directory reached before it
    (variables this text assigned a literal, then this process's environment, expanded), joins FOLLOWED. They are
    never dropped: a `cd` in a subshell or one that fails is taken as made, which can only refuse more."""
    dirs = FOLLOWED["dirs"]
    for cmd in commands:
        change = _change(cmd)
        if not isinstance(change, tuple) or FOLLOWED["over"]:
            continue
        name, operands, _ = change
        if name == "popd" or (name == "pushd" and not operands):
            continue
        target = _expand(operands[0].text) if operands else "~"
        if target.startswith(("-", "+")):
            continue   # `cd -`, `pushd +1`: no directory named
        for found in [_resolved(d, target) for d in list(dirs)]:
            if found not in dirs:
                dirs.append(found)
        if len(dirs) > MAX_FOLLOWED:
            FOLLOWED["over"] = [True]


def _bases() -> list[str]:
    """The directories a written path is resolved from: each place WHERE names, and for a place it cannot name
    (UNKNOWN, or SCRATCH) every directory FOLLOWED holds; on another machine, the home directory too."""
    out: list[str] = []
    for d in HERE["dirs"] or [CWD["dir"] or os.getcwd()]:
        if isinstance(d, str):
            out.append(d)
            continue
        if FOLLOWED["over"]:
            raise Unreadable(f"the command changes into more than {MAX_FOLLOWED} directories")
        out += FOLLOWED["dirs"]
    if REMOTE["on"]:
        out.append(os.path.expanduser("~"))
    return list(dict.fromkeys(out)) or [CWD["dir"] or os.getcwd()]


def _owners(path: str, bases: list[str] | None = None, worktrees: bool = False) -> bool:
    """Whether a path a command writes is protected from any directory the command may run in; with
    `worktrees`, a path under `.claude/worktrees/<name>` is not."""
    for base in (bases if bases is not None else _bases()) or [os.getcwd()]:
        parts = _owned(path, base)
        if parts is not None and not (worktrees and _in_worktrees(parts)):
            return True
    return False


def _resolved(base: str, path: str) -> str:
    return os.path.realpath(os.path.join(base, os.path.expandvars(os.path.expanduser(path))))


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
    if (why := _held(moved)):
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
    bases, i, joined = _bases(), 0, ""
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            bases = [_resolved(base, args[i + 1]) for base in bases]
            joined = os.path.join(joined, args[i + 1])
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") else 1
    sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
    named = [a for a in rest if not a.startswith("-")]
    if sub in ("rm", "mv", "checkout", "restore") and any(_owners(a, bases) for a in named):
        return OWNERS
    if (sub == "mv" or (sub == "rm" and "--cached" not in rest)):
        return _held(named[:-1] if sub == "mv" else named, bases, joined)
    return None


def _held(paths: list[str], bases: list[str] | None = None, git_base: str = "") -> str | None:
    """#282 (`_removes_owned`), worded as v7.1.2 words it where v7.1.2 refuses the same path: this repository,
    the work tree of a directory the command runs in, or a directory holding one is PROJECT_TREE's."""
    why = _removes_owned(paths, bases)
    if why and (hit := _project_tree([Word(p) for p in paths], git_base)):
        return PROJECT_TREE.format(target=hit)
    return why


def judge_write(path: str, base: str) -> str | None:
    """The Write and Edit hook (`--write`): a secrets file by name, or a path `protected` refuses."""
    if path and _env_file(path):
        return ENV_WRITE
    if path and protected(path, base):
        return OWNERS
    return None


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
    for d in [*(x for x in HERE["dirs"] if isinstance(x, str)), CWD["dir"], os.environ.get("CLAUDE_PROJECT_DIR", ""),
              OWN]:
        root = _root_of(os.path.realpath(d)) if d else None
        if root and root not in found:
            found.append(root)
    return found


def _in_or_above_a_root(resolved: str) -> bool:
    """The v7.1 upgrade security review's MAJOR-1: whether `resolved` lies inside a git work tree -- any, not
    only one this call runs in -- or is or sits above the work tree of a directory this call knows."""
    if _root_of(resolved, proper=True):
        return True
    cut = resolved.rstrip(os.sep) + os.sep
    return any(root == resolved or root.startswith(cut) for root in _known_roots())


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


def _removes_owned(paths: list[str], bases: list[str] | None = None) -> str | None:
    """#282: a path removed or moved that holds a git work tree's `.claude/` or `.githooks/` -- the work tree's
    root, or a directory above it -- from any directory the command may run in. A `.claude/worktrees/<name>`
    worktree is not refused for holding its own; one too large to walk is refused."""
    def owns(d: str, names: dict[str, os.DirEntry[str]]) -> bool:
        return any(name in names and names[name].is_dir(follow_symlinks=False) for name in OWNED)

    for path in paths:
        for base in (bases if bases is not None else _bases()) or [os.getcwd()]:
            target = _resolved(base, path)
            if _worktree_path(target):
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



# --- the scratch exemption for rm ---------------------------------------------------------------------

def _temp_bases() -> list[str]:
    """Where scratch lives: `$TMPDIR`, the interpreter's temp directory, and the usual system ones. Not all of
    `/var/folders` (model_ranking, the v7.1.2 upgrade security review's M4): beside each user's `T/` temp directory it
    holds macOS's per-user state and caches (`0/`, `C/`), which are no scratch. Its per-user temp directories,
    `/var/folders/<a>/<b>/T`, are: what `$TMPDIR` names on macOS, and the temp directory when it is unset."""
    raw = [os.environ.get("TMPDIR"), os.environ.get("TEMP"), os.environ.get("TMP"), tempfile.gettempdir(),
           "/tmp", "/var/tmp", "/private/tmp", "/private/var/tmp"]
    raw += sorted(glob.glob("/var/folders/*/*/T"))[:64]
    out: list[str] = []
    for d in raw:
        if d:
            real = os.path.realpath(d)
            if real != os.path.sep and real not in out:
                out.append(real)
    return out


def _resolve(word: Word) -> list:
    """Where an operand lands, from each directory the command may run in (WHERE): a real path, SCRATCH
    for a path inside a `mktemp` result or a scratch place, UNKNOWN for what this cannot name."""
    text = word.text
    # `$PWD` is each place the command runs in. `$(pwd)` may be one too, and may be anything else (model_ranking,
    # the v7.1.2 upgrade security review's B1 and B1-R): the command can redefine `pwd` in ways no pattern lists
    # (`p""wd() {...}`, `eval`, `enable -n pwd`, zsh's `functions[pwd]=`). So it lands on each place the command
    # runs in AND on UNKNOWN: a refusal of the repository still sees it (`mv $(pwd) ..`), and it is never scratch.
    pwd_sub = text.startswith("$(...)") and len(word.subs) == 1 and word.subs[0].strip() in ("pwd", "pwd -P", "pwd -L")
    if pwd_sub:
        text = "." + text[len("$(...)"):]
    m = VARIABLE.match(text)
    if m and _name(m) == "PWD" and "PWD" not in SCOPE:
        text, m = "." + text[m.end():], None
    if m:
        name, rest = _name(m), text[m.end():]
        value = _variable(name)
        if value is SCRATCH:  # the mktemp directory, or a path below it that `..` does not leave
            return [SCRATCH] if _below(rest) else [UNKNOWN]
        if name == "TMPDIR" and isinstance(value, str) and "TMPDIR" not in SCOPE:
            # `$TMPDIR` as this process has it, substituted: strictly below it, `..` resolved -- never the
            # temp root itself, and never what `$TMPDIR/..` reaches (an unset one made `"$TMPDIR"/x` `/x`).
            root = os.path.realpath(value)
            resolved = os.path.realpath(value + rest) if "$" not in rest else root
            inside = root != os.path.sep and resolved.startswith(root.rstrip(os.sep) + os.sep)
            return [resolved] if inside else [UNKNOWN]
        if not isinstance(value, str):
            return [UNKNOWN]
        text = value + rest
    if "$" in text or word.glob or not text:
        return [UNKNOWN]
    path = os.path.expanduser(text) if text == "~" or text.startswith("~/") else text
    if path.startswith("~"):
        return [UNKNOWN]  # `~user`: another account's tree
    if os.path.isabs(path):
        return [os.path.realpath(path)]
    out: list = []
    for base in HERE["dirs"] or [CWD["dir"] or os.getcwd()]:
        if base is SCRATCH:
            out.append(SCRATCH if _inward(path) else UNKNOWN)
        elif base is UNKNOWN:
            out.append(UNKNOWN)
        else:
            out.append(os.path.realpath(os.path.join(str(base), path)))
    return out + [UNKNOWN] if pwd_sub else out


def _scratch(word: Word) -> bool:
    """Whether an `rm` target is scratch: under a temp directory, a `mktemp` result of this text, or a
    worktree under `.claude/worktrees/`. A relative one must be scratch from every directory the command
    may run in (WHERE). Anything this cannot resolve is not scratch; nothing on another machine is."""
    if REMOTE["on"]:
        return False
    return all(p is SCRATCH or (isinstance(p, str) and _scratch_path(p)) for p in _resolve(word))


def _scratch_path(resolved: str) -> bool:
    """Whether a resolved path is scratch: inside a repository this command runs in (or this guard's), only
    a worktree under that repository's `.claude/worktrees/` is -- the agent working inside such a worktree,
    or in a checkout under the temp directory, is working in a repository, not in scratch; elsewhere a
    path under a temp directory or any `.claude/worktrees/<name>/`."""
    roots = [r for r in _repos() if resolved == r or resolved.startswith(r.rstrip(os.sep) + os.sep)]
    if roots:
        r = max(roots, key=len)
        return _worktree_path(resolved[len(r):])
    if _worktree_path(resolved):
        return True
    for base in _temp_bases():
        if resolved != base and resolved.startswith(base + os.sep):
            return True
    return False



def _not_scratch_here(words: list[Word], above: bool = False) -> str | None:
    """model_ranking (the v7.1 upgrade security review's B1 and MAJOR-1), beside v7.1.2's own scratch rule: the
    first target that, resolved, sits above a temp directory (`above`: asked before `_holding`, which would
    otherwise word it), or else is a temp directory itself, lies inside any git work tree -- not only one this
    call runs in -- or is or sits above the work tree of a directory this call knows (asked after `_holding`). A
    `mktemp` result, and a worktree under `.claude/worktrees/`, are scratch by design."""
    bases = _temp_bases()
    for w in words:
        for p in _resolve(w):
            if not isinstance(p, str) or _worktree_path(p):
                continue
            cut = p.rstrip(os.sep) + os.sep
            if any(base.startswith(cut) for base in bases) or (
                    not above and (any(base == p for base in bases) or _in_or_above_a_root(p))):
                return w.text
    return None


def _worktree_path(resolved: str) -> bool:
    parts = resolved.replace("\\", "/").split("/")
    for i, part in enumerate(parts):
        if part == ".claude" and i + 2 < len(parts) and parts[i + 1] == "worktrees" and parts[i + 2]:
            return True
    return False


def _holding(words: list[Word]) -> str | None:
    """The first target, scratch by place, that is or holds a git work tree (`.git`, a directory or a
    worktree's file) or more than MAX_WALK entries to look through; a worktree under `.claude/worktrees/`
    is scratch by design. A pattern is read as the existing paths it matches, each walked."""
    for w in words:
        for p in _resolve(w):
            if not isinstance(p, str) or _worktree_path(p):
                continue
            for top in (_matches(p) if w.glob and any(ch in p for ch in "*?[") else [p]):
                if os.path.lexists(os.path.join(top, ".git")) or (
                        os.path.isdir(top) and not os.path.islink(top) and _walk_finds_repo(top)):
                    return w.text
    return None



def _matches(pattern: str) -> list[str]:
    """The existing paths a pattern in its last part names; a pattern higher up names nothing readable here,
    so its directory is taken whole."""
    head, tail = os.path.split(pattern)
    if any(ch in head for ch in "*?["):
        return [head.split("*")[0].split("?")[0].split("[")[0].rstrip(os.sep) or os.sep]
    try:
        return [os.path.join(head, n) for n in os.listdir(head) if fnmatch.fnmatch(n, tail)]
    except OSError:
        return []


def _walk_finds_repo(top: str) -> bool:
    seen = 0
    for _, dirs, files in os.walk(top):
        seen += len(dirs) + len(files)
        if ".git" in dirs or ".git" in files or seen > MAX_WALK:
            return True
    return False


def _toplevel_cached(d: str) -> str | None:
    if d not in TOPS:
        top = _toplevel(d) if os.path.isdir(d) else None
        TOPS[d] = os.path.realpath(top) if top else None
    return TOPS[d]


def _repos() -> set[str]:
    """This guard's repository and the work tree of every directory the command may run in."""
    out = {os.path.realpath(OWN)}
    for d in list(HERE["dirs"]) + [CWD["dir"]]:
        if isinstance(d, str) and d:
            near = d
            while not os.path.isdir(near) and os.path.dirname(near) != near:
                near = os.path.dirname(near)
            if (top := _toplevel_cached(near)):
                out.add(top)
    return out


def _identity(path: str, follow: bool = True) -> tuple[int, int] | None:
    try:
        st = os.stat(path) if follow else os.lstat(path)
    except OSError:
        return None
    return st.st_dev, st.st_ino


def _protected() -> tuple[set, set]:
    """(the identities an operand may not be: each repository of `_repos()`, every directory holding one, and
    the home directory; the identities of their `.git`, inside which nothing may be moved or removed).
    Compared by device and inode, so `../PKG` on a case-insensitive disk is `../pkg`."""
    keep: set = set()
    gits: set = set()
    home = os.path.realpath(os.path.expanduser("~"))
    for r in _repos() | {home}:
        d = r
        while True:
            if (i := _identity(d)):
                keep.add(i)
            if os.path.dirname(d) == d:
                break
            d = os.path.dirname(d)
        if r != home and (g := _identity(os.path.join(r, ".git"), follow=False)):
            gits.add(g)
    return keep, gits



def _project_tree(words: list[Word], base: str = "") -> str | None:
    """The first operand that is a protected repository, the home directory, a directory holding one, or
    its `.git` or anything inside that -- `mv . ../gone`, `rm -r ../repo`, `git rm -r .` (#282 in the
    field), `mv .GIT /x` on a case-insensitive disk. An operand this cannot name is not held here; nothing
    on another machine is this repository."""
    if REMOTE["on"]:
        return None
    keep, gits = _protected()
    for w in words:
        word = Word(os.path.join(base, w.text) if base and not os.path.isabs(w.text) else w.text, w.glob,
                    subs=list(w.subs))
        for p in _resolve(word):
            if not isinstance(p, str):
                continue
            here = _identity(p, follow=False)
            if here is not None and (here in keep or _identity(p) in keep):
                return w.text
            d = p
            while True:
                if (i := _identity(d, follow=False)) is not None and i in gits:
                    return w.text
                if os.path.dirname(d) == d:
                    break
                d = os.path.dirname(d)
    return None



def _judge_rm(words: list[Word]) -> str | None:
    opts: list[str] = []
    targets: list[Word] = []
    for k, w in enumerate(words):
        if w.text == "--":
            targets += words[k + 1:]
            break
        if w.text.startswith("-") and len(w.text) > 1:
            opts.append(w.text)
        else:
            targets.append(w)
    letters = "".join(a[1:] for a in opts if not a.startswith("--"))
    longs = [a for a in opts if a.startswith("--")]
    # Recursive is enough: Claude Code runs Bash with no terminal, so `rm -r` never prompts and removes
    # what `rm -rf` removes, read-only files included (v7.1.2; `rm -r ~/Documents` passed before).
    recursive = "r" in letters or "R" in letters or any(_unique(a, "--recursive", GIT_LONG["rm"]) for a in longs)
    if not recursive:
        return None
    if (hit := _project_tree(targets)):
        return PROJECT_TREE.format(target=hit)
    if not targets or not all(_scratch(w) for w in targets):
        return DESTRUCTIVE
    if SEEN["links"]:
        return LINKED
    if _not_scratch_here(targets, above=True):
        return DESTRUCTIVE
    if (held := _holding(targets)):
        return HOLDS_REPO.format(target=held)
    if _not_scratch_here(targets):
        return DESTRUCTIVE
    return None


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


def _judge_ssh(args: list[str], depth: int) -> str | None:
    """`ssh [options] host [options] [words]`: the words are a command line the remote shell runs, judged as
    one with no scratch and no place this can name there; `-o ProxyCommand=`, `LocalCommand` and
    `KnownHostsCommand` run on this machine and are judged here, `RemoteCommand` there. OpenSSH reads
    options after the host too, until `--` or the first word of the command (`ssh host -o ProxyCommand=...`
    runs locally). `ssh host rm -rf /srv/data` passed v7.1.1 unread."""
    remote: list[str] = []
    host = None
    ended = False
    i = 0
    while i < len(args):
        a = args[i]
        if not ended and a == "--":
            ended = True
            i += 1
            continue
        if ended or not a.startswith("-") or a == "-":
            if host is None:
                host = a
                i += 1
                continue
            break
        for j in range(1, len(a)):
            if a[j] in SSH_VALUED:
                value = a[j + 1:]
                if not value:
                    i += 1
                    value = args[i] if i < len(args) else ""
                if a[j] == "o":
                    m = re.match(r"\s*([A-Za-z]+)\s*(?:=\s*|\s+)(.*)$", value, re.S)
                    key, text = (m.group(1).lower(), m.group(2)) if m else ("", "")
                    if key in SSH_LOCAL and text.lower() != "none" and (why := judge_text(text, depth + 1)):
                        return why
                    if key in SSH_REMOTE and text.lower() != "none":
                        remote.append(text)
                break
        i += 1
    words = args[i:]
    if words:
        remote.append(" ".join(words))
    for text in remote:
        if (why := _judge_remote(text, depth)):
            return why
    return None



def _judge_remote(text: str, depth: int) -> str | None:
    """A command line run on another machine: judged with every place unknown and nothing scratch, and with
    this text's own places and variables left as they were."""
    places, scope = list(HERE["dirs"]), dict(SCOPE)
    HERE["dirs"] = [UNKNOWN]
    REMOTE["on"] += 1
    try:
        return judge_text(text, depth + 1)
    finally:
        REMOTE["on"] -= 1
        HERE["dirs"] = places
        SCOPE.clear()
        SCOPE.update(scope)


def _skips_hooks(option: str) -> bool:
    """Whether a long option is `--no-verify` as git may read it, refused: the name, or a prefix of it
    from `--no-ve` (`--no-veri` is it; a shorter one is ambiguous with `--no-verbose`), with or without `=`."""
    name = option.split("=", 1)[0]
    return len(name) >= len("--no-ve") and "--no-verify".startswith(name)


def _config_split(rest: list[str]) -> tuple[list[str], list[str]]:
    """`git config <rest>` as (options, plain words), each option that takes a value with it: `--comment
    --unset alias.x v` is a comment `--unset`, not an unset."""
    options: list[str] = []
    plain: list[str] = []
    k = 0
    while k < len(rest):
        a = rest[k]
        if a.startswith("-") and len(a) > 1:
            options.append(a)
            if a in CONFIG_VALUED:
                k += 1
        else:
            plain.append(a)
        k += 1
    return options, plain


def _reads(options: list[str], plain: list[str]) -> bool:
    return plain[:1] in (["get"], ["list"]) or any(
        a.startswith(("--get", "--list")) or a == "-l" for a in options)


def _redirects_hooks(rest: list[str]) -> bool:
    """Whether `git config <rest>` writes `core.hooksPath` to anything but `.githooks`, unsets it, or drops the
    `core` section: each leaves the pre-push gate unrun. Reading it is not refused."""
    options, plain = _config_split(rest)
    if (plain[:1] in (["remove-section"], ["rename-section"]) or
            any(a.startswith(("--remove-section", "--rename-section")) for a in options)):
        return any(a.lower() == "core" for a in plain)
    if plain[:1] == ["set"]:
        plain = plain[1:]
    at = next((n for n, a in enumerate(plain) if a.lower() == "core.hookspath"), None)
    if at is None:
        return False
    if plain[:1] == ["unset"] or any(a.startswith("--unset") for a in options):
        return True
    value = plain[at + 1] if at + 1 < len(plain) else None
    return not _reads(options, plain) and value is not None and value != ".githooks"



def _config_env(word: Word) -> str | None:
    """Why an assignment that feeds git's config through the environment (`GIT_CONFIG_PARAMETERS`,
    `GIT_CONFIG_KEY_<n>`) is refused: it names `core.hooksPath` or an expansion this cannot read there, or
    it defines an alias, whose command this cannot pair with the value set beside it."""
    name, _, value = word.text.partition("=")
    base = name.rstrip("+").split("[")[0]
    if base in CODE_ENV:
        # `+=` appends to a value set elsewhere (`GIT_PAGER=rm; GIT_PAGER+=' -rf ~'`), and a subscript writes
        # part of one (`GIT_PAGER[0]=`, zsh's slice `GIT_PAGER[1,-1]=`): the whole is unread.
        if name.endswith("+") or "[" in name:
            return CODE_ENV_UNREAD.format(name=base)
        # `EDITOR="$HOME/bin/ed"` names a path, not an expansion this cannot read -- while nothing in this text
        # sets `HOME`.
        if "HOME" not in SCOPE and not SEEN["home"]:
            homed = re.sub(r"\$\{HOME\}|\$HOME(?![A-Za-z0-9_])", os.path.expanduser("~").replace("\\", "/"), value)
            SEEN["home_used"] = SEEN["home_used"] or homed != value
            value = homed
        value = _expand(value)
        if "$" in value or word.subs:
            return CODE_ENV_UNREAD.format(name=base)
        return judge_text(value, 1) if value.strip() else None
    if not GIT_CONFIG_ENV.match(name.rstrip("+")):
        return None
    value = _expand(value)
    if "hookspath" in value.lower() or "$" in value:
        return NO_VERIFY
    keys = re.findall(r"[A-Za-z][\w.-]*", value)
    return ALIAS_UNREAD if "alias." in value.lower() or any(CODE_KEY.match(k) for k in keys) else None


def _judge_alias(value: str, depth: int, args: list[str] | None = None) -> str | None:
    """An alias is the command it names, with the words it is called with: `!` and shell text (git runs it
    with the arguments appended), or a git subcommand and its words."""
    tail = " ".join(shlex.quote(a) for a in (args or []))
    text = value[1:] if value.startswith("!") else "git " + value
    return judge_text(f"{text} {tail}".strip(), depth + 1)


def _config_set(rest: list[str]) -> tuple[str, str] | None:
    """(key, value) that `git config <rest>` writes, or None when it reads, unsets or writes nothing."""
    options, plain = _config_split(rest)
    if _reads(options, plain) or plain[:1] in (["unset"], ["remove-section"], ["rename-section"]) or any(
            a.startswith(("--unset", "--remove-section", "--rename-section", "--edit")) for a in options):
        return None
    if plain[:1] == ["set"]:
        plain = plain[1:]
    return (plain[0], plain[1]) if len(plain) >= 2 else None



def _judge_git(args: list[str], behind_xargs: bool, depth: int = 0,  # noqa: C901 -- one branch per subcommand
               inherited: dict[str, str] | None = None) -> str | None:
    i = 0
    base = ""
    aliases: dict[str, str] = dict(inherited or {})
    while i < len(args) and args[i].startswith("-"):
        # `-c k=v`, `-ck=v`, `--config-env k=ENV`, `--config-env=k=ENV`: core.hooksPath, an alias, or a key
        # whose value git runs, for this command
        setting, from_env = None, args[i].startswith("--config-env")
        if args[i] in ("-c", "--config-env") and i + 1 < len(args):
            setting = args[i + 1]
        elif args[i].startswith("--config-env="):
            setting = args[i][len("--config-env="):]
        elif args[i].startswith("-c") and len(args[i]) > 2:
            setting = args[i][2:]
        if setting is not None:
            key, _, value = setting.partition("=")
            if "hookspath" in setting.lower():
                return NO_VERIFY
            if key.lower().startswith(("include.", "includeif.")):
                return INCLUDED.format(key=key)
            if key.lower().startswith("alias.") or CODE_KEY.match(key):
                if from_env:
                    return ALIAS_UNREAD
                if key.lower().startswith("alias."):
                    aliases[key[len("alias."):].lower()] = value
                if (why := _judge_alias(value if key.lower().startswith("alias.") else "!" + value, depth)):
                    return why
        if args[i] == "-C" and i + 1 < len(args):
            base = os.path.join(base, args[i + 1])
        i += 2 if args[i] in ("-C", "-c", "--config-env", "--git-dir", "--work-tree", "--namespace",
                              "--exec-path") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    # An alias set by `-c` for this command runs with the words it is called with: `git -c alias.r=reset
    # r --hard` is `git reset --hard`, and was read as an unknown subcommand.
    if sub.lower() in aliases:
        value = aliases[sub.lower()]
        if value.startswith("!"):
            # git hands its `-c` settings to the shell alias's children, so a `git` it runs sees the other
            # aliases too (`-c alias.r=reset -c alias.x='!git r' x --hard`): not read, refused.
            if len(aliases) > 1:
                return ALIAS_SHELL
            return _judge_alias(value, depth, rest)
        try:
            expanded = shlex.split(value)
        except ValueError:
            raise Unreadable(f"the alias `{sub}` cannot be split as git would") from None
        # An alias may name another (`-c alias.r=reset -c alias.h=r h --hard`): git resolves the chain, and
        # so does this, with the same map; a chain past twelve steps, or a loop, is refused.
        if depth >= 12:
            raise Unreadable(f"the alias `{sub}` resolves through more than twelve aliases")
        return _judge_git(expanded + rest, behind_xargs, depth + 1, aliases)
    ended = rest.index("--") if "--" in rest else len(rest)
    options = [a for a in rest[:ended] if a.startswith("-")]
    longs = [a for a in options if a.startswith("--")]
    letters = "".join(a[1:] for a in options if not a.startswith("--"))
    known = GIT_LONG.get(sub, [])
    # refused: a skipped hook -- `--no-verify` in any prefix git reads as it (`--no-veri`), on any subcommand
    if any(_skips_hooks(a) for a in longs) or (sub == "commit" and "n" in letters):
        return NO_VERIFY
    if sub == "config" and _redirects_hooks(rest):
        return NO_VERIFY
    if sub == "config" and (pair := _config_set(rest)) is not None:
        key, value = pair
        if key.lower().startswith("alias."):
            # A persistent alias is called later with words this cannot pair with it: only a read-only
            # target, its own words judged.
            words = value.split()
            if value.startswith("!") or not words or words[0].lower() not in ALIAS_SAFE:
                return ALIAS_PERSIST.format(name=key[len("alias."):], value=value)
            if (why := _judge_alias(value, depth)):
                return why
        elif key.lower().startswith(("include.", "includeif.")):
            return INCLUDED.format(key=key)
        elif CODE_KEY.match(key) and (why := _judge_alias("!" + value, depth)):
            return why   # `git config core.pager 'rm -rf ~'` runs on the next `git log`
    # `git rm -r .` and `git mv` of the work tree itself: every tracked file gone from it (#282 in the field).
    # Options end at `--`; `:/` and `:(top)` name the work tree's top.
    if sub in ("rm", "mv"):
        paths = [Word(a) for a in rest[:ended] if not a.startswith("-")] + [Word(a) for a in rest[ended + 1:]]
        top = [w.text for w in paths if re.match(r"^:(/|\(top[^)]*\))[./]*$", w.text)]
        cached = "--cached" in rest[:ended]
        recursive = sub == "mv" or "r" in letters or any(_unique(a, "--recursive", GIT_LONG["rm"]) for a in longs)
        moved = paths[:-1] if sub == "mv" else paths
        if recursive and not cached and top:
            return PROJECT_TREE.format(target=top[0])
        if recursive and not cached and (hit := _project_tree(moved, base)):
            return PROJECT_TREE.format(target=hit)
    if sub == "update-ref":
        refs = [a for a in rest if not a.startswith("-")]
        if any(r.removeprefix("refs/").removeprefix("heads/") in PROTECTED for r in refs):
            return PROTECTED_REF

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
        # A deletion whose ref this cannot read may be the protected branch's; the remote (first) is not a ref.
        deleting = "d" in letters or given("--delete") or any(ref.startswith(":") for ref in refs[1:])
        unread = next((ref for ref in refs[1:] if "$" in ref), None)
        if deleting and unread is not None:
            return UNREAD_DELETE.format(ref=unread)
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


def project_root(cwd: str) -> str | None:
    """The repository whose brief governs this call: the work tree of `cwd` when it carries
    `docs/project-brief.md`, else `$CLAUDE_PROJECT_DIR` when that does; None when neither has a brief, so
    nothing is declared."""
    for cand in (_toplevel(cwd), os.environ.get("CLAUDE_PROJECT_DIR", "")):
        if cand and os.path.isfile(os.path.join(cand, "docs", "project-brief.md")):
            return cand
    return None


def _governing(candidates: list[tuple[list, list[str]]], cwd: str) -> dict[str, list[list[str]]]:
    """Each governing repository with the word lists it judges: the one of every directory a list may run
    in (WHERE), from its nearest existing directory (`mkdir x && cd x` is the parent's); from a directory
    this cannot name (UNKNOWN, or SCRATCH, which may hold any clone), the call's own, `$CLAUDE_PROJECT_DIR`'s
    and every named directory's, each when it carries a brief."""
    roots: dict[str, str | None] = {}

    def root_of(d: str) -> str | None:
        while not os.path.isdir(d) and os.path.dirname(d) != d:
            d = os.path.dirname(d)
        if d not in roots:
            roots[d] = project_root(d)
        return roots[d]

    found: dict[object, list[str | None]] = {}
    out: dict[str, list[list[str]]] = {}
    for dirs, words in candidates:
        for d in dirs:
            if d not in found:
                if isinstance(d, str):
                    found[d] = [root_of(d)]
                else:
                    env = os.environ.get("CLAUDE_PROJECT_DIR", "")
                    found[d] = [root_of(cwd), root_of(env) if env else None] + [root_of(r) for r in sorted(REACHED)]
            for root in found[d]:
                if root is not None and words not in out.setdefault(root, []):
                    out[root].append(words)
        # A deploy of this project run from another repository (`fly deploy --config ../proj/fly.toml`)
        # is judged by this project's gate too, unless this project or a worktree of it already judges it.
        mine = os.path.realpath(OWN)
        if os.path.isfile(os.path.join(mine, "docs", "project-brief.md")) and not any(
                r is not None and _own(r) for d in dirs for r in found[d]):
            if words not in out.setdefault(mine, []):
                out[mine].append(words)
    return out


def judge_deploy(candidates: list[tuple[list, list[str]]], cwd: str) -> str | None:
    """Hand every program-position word list to THIS repository's `scripts/deploy_gate.py --judge`, once for
    each repository that governs a directory it may run in, run there; any refusal is this guard's. The gate
    is never another repository's: a cloned repository's script ran on the next `ls` in it past v7.1.1, and
    its exit 0 passed that repository's deploys. In a repository that is not this one or a worktree of it,
    the gate is asked only whether a word list is one of that brief's deploys, and every one is refused."""
    for root, commands in _governing(candidates, cwd).items():
        if (why := _judge_in(root, commands, cwd, foreign=not _own(root))):
            return why
    return None


def _common(root: str) -> str | None:
    """The git directory a work tree's history lives in: `.git` itself, or for a worktree (whose `.git` is a
    file, `gitdir: <common>/worktrees/<name>`) the one its `commondir` names. Read from disk, without git."""
    dot = os.path.join(root, ".git")
    if os.path.isdir(dot):
        return os.path.realpath(dot)
    try:
        with open(dot, encoding="utf-8") as f:
            line = f.read(4096).strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    gitdir = os.path.realpath(os.path.join(root, line[len("gitdir:"):].strip()))
    try:
        with open(os.path.join(gitdir, "commondir"), encoding="utf-8") as f:
            return os.path.realpath(os.path.join(gitdir, f.read(4096).strip()))
    except OSError:
        return gitdir


def _own(root: str) -> bool:
    """Whether a repository is this guard's own, or a worktree of it."""
    if os.path.realpath(root) == os.path.realpath(OWN):
        return True
    mine = _common(OWN)
    return mine is not None and _common(root) == mine


def _judge_in(root: str, candidates: list[list[str]], cwd: str, foreign: bool = False) -> str | None:
    """This repository's gate on the word lists that may run under `root`, run with `root` as its tree."""
    gate = os.path.join(OWN, "scripts", "deploy_gate.py")
    if not os.path.isfile(gate):
        return GATE_MISSING.format(root=root, own=OWN)
    try:
        with open(gate, "rb") as f:
            source = f.read(1 << 20).decode("utf-8", "replace")
    except OSError as error:
        return f"BLOCKED: deploy gate -- {gate} could not be read ({type(error).__name__}: {error})."
    protocol = JUDGE_LINE.search(source)
    level = 0 if protocol is None else int(protocol.group(1)) if protocol.group(1) is not None else 1
    if level < 1:
        return GATE_OLD.format(gate=gate, need=1, why="read `--judge` as a command and pass every deploy")
    if foreign and level < 2:
        return GATE_OLD.format(gate=gate, need=2, why=f"judge {root}, another repository, by its own verdicts")
    payload = json.dumps({"cwd": cwd, "commands": candidates, **({"foreign": True} if foreign else {})})
    try:
        r = subprocess.run([sys.executable, "-I", "-B", gate, "--judge"], input=payload.encode("utf-8"),
                           capture_output=True, cwd=root, timeout=20)
    except (OSError, subprocess.SubprocessError) as error:
        return f"BLOCKED: deploy gate -- scripts/deploy_gate.py could not run ({type(error).__name__}: {error})."
    if r.returncode == 0:
        return None
    message = r.stderr.decode("utf-8", "replace").strip()
    return message or f"BLOCKED: deploy gate -- scripts/deploy_gate.py exited {r.returncode} and gave no reason."


# --- the hook -----------------------------------------------------------------------------------------

def _expired() -> None:
    """The guard's own bound: a thread, so it holds where SIGALRM does not exist. It cannot stop a long call
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
    CWD["dir"] = cwd
    HERE["dirs"] = [cwd]
    REACHED.clear()
    SEEN.update(repeats=False, cdpath=False, links=False, home_used=False,
                # `HOME` written anywhere but as `$HOME`: an editor or pager path through `$HOME` is unread.
                home=bool(re.search(r"(?<![\w$])HOME\b", re.sub(r"\$\{?HOME\b", "", command))))
    NAMEREF.clear()
    FLOW["maybe"] = False
    SCOPE.clear()
    CANDIDATES.clear()
    TOPS.clear()
    REMOTE["on"] = 0
    FOLLOWED["dirs"] = list(dict.fromkeys([os.path.normpath(os.path.abspath(cwd)), os.path.realpath(cwd)]))
    FOLLOWED["over"] = []
    WALK["left"] = WALK_S
    TRUST["TMPDIR"] = not TMPDIR_NAMED.search(command)   # B1: `unset TMPDIR`, `local TMPDIR`, `read TMPDIR`
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
