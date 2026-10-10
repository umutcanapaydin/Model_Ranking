"""#189: the Bash guard's second reading, and the Write and Edit hook's refusal (`--write`).

The text guard in `.claude/settings.json` runs first, unchanged. This one reads the command with a lexer of
its own and judges each simple command it finds. It is a best effort against an agent's ordinary commands,
not a parser of bash or zsh, and it only adds blocks to the text guard's. Given `--write`, it judges the Write
or Edit call's `file_path` instead: a `.env` file (permission-matrix.md S6), or a path `protected` refuses.

What it blocks:
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY, and `fly` behind `xargs` (D-185);
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run` (D-185);
- blocked too: a `git push` that forces, mirrors, pushes every branch, names main, master or trunk as its
  destination (`main`, `heads/main`, `refs/heads/main`), or runs behind `xargs` (AGENTS.md S3);
- `git reset --hard`, `git clean -f`, `git checkout --`, `.`, `-f` or a tree-ish with paths, `git switch -f`
  or `--discard-changes`, `git stash clear`, `git restore` without `--staged` or with `--worktree`, and `rm`
  both recursive and forced (permission-matrix.md S5). A git long option counts in any unique prefix;
- a write into the `.claude/` or `.githooks/` of any git work tree, the owner's hooks and settings (the M21
  closure security seat's S3): a redirection there; `rm`, `mv`, `tee`, `touch`, `chmod` and their kind on a
  path there; `cp`, `ln`, `install`, `rsync`, `ditto` or `dd` with a destination there (the last word, or
  `-t`/`--target-directory` for `cp`, `mv`, `ln` and `install`, or `of=` for `dd`); `sed -i` or `perl -i` on
  one; and `git rm`, `git mv`, `git checkout` or `git restore` naming one. Reading them is not refused.
  Which paths, exactly (`protected`, the fixes review's round 2, B1): the path, `~` and variables expanded,
  is resolved from the directory the command runs in, links followed on its longest existing part; it is
  refused when a directory on it named `.claude` or `.githooks` (in any case) has a parent that holds a
  `.git` entry, a file or a directory. That parent is a work-tree root: this clone, each of its linked
  worktrees, and any other clone. Claude Code's own `~/.claude` is not refused, as no `.git` sits beside it.
  The directory a command runs in is the payload's `cwd` and each one a `cd`, `pushd` or `git -C` in the
  command changes into, taken in order from every directory reached before it; a path is refused if it is
  protected from any of them.

Where it looks: each command after `;`, `&&`, `||`, `|`, `|&`, `&`, a newline, `(`, `)`, `{` or `}`; inside
`$( )`, backticks (nested ones too), `<( )`, `${ }`, `$(( ))` and an unquoted here-document's body; past
assignments, shell keywords and the wrappers in WRAPPERS (after one, every later word is tried as the
program); inside `bash`, `sh`, `zsh`, `dash`, `ksh`, `csh`, `tcsh` or `fish` given `-c`, a script, a
here-document or a here-string; and inside `eval`, `source`, `.`, `env -S` and `find -exec`. Text in single
quotes and a quoted here-document's body are data; a `#` that starts a word starts a comment.

It blocks what it cannot read, rather than reading it as data: an unclosed quote or substitution; a word
with `(` written against it (zsh's glob qualifiers, `=( )`); a `${(flags)...}`; a brace expansion, or a
pattern that could name a guarded program, as a program word; a shell or `source` reading its commands from
a pipe, a file or stdin; a `-c` with no string; an input over MAX_INPUT characters; and any command it has
not read within DEADLINE_S seconds, a timer thread that writes the BLOCKED line and exits 2 wherever the
guard runs (the M21 closure security seat's S2). The thread runs only when Python lets it: a long call into C
that holds the interpreter (a regex over a long word) runs to its end first, so that case is bounded only by
the hook's own 30 s timeout and `onFailure: "block"`, from Claude Code 2.1.295 (the fixes review's M6).

Not held, by class (G-7):
- a program named when the command runs: through a variable, a substitution, an alias, a function, `hash`,
  or a `PATH` holding a script of a guarded name;
- code another program runs: a script's contents, `python -c`, `perl -e`, `node -e`, `awk`'s `system()`,
  `make` recipes, git hooks and aliases (`git -c alias.x=...`, `git config`), `ssh host cmd`;
- a wrapper not in WRAPPERS, whose program is then read as an argument;
- a push to a destination git chooses itself: a bare `git push`, `git push origin HEAD` or `@`, an upstream,
  `push.default` or `remote.pushDefault` (from a checkout on main, each pushes main; GitHub's branch protection
  is the control of record there, the M21 closure security seat's S4);
- a write into `.claude/` or `.githooks/` by a program this does not list (`python -c`, `git apply`, `tar`, an
  editor), through a path built when the command runs (`$(...)`, a variable set earlier in it, a glob), a
  hard link made before, or a directory reached by a `cd` this does not follow (one to a built path, through
  `CDPATH`, `cd -`, or repeated by a loop more than once);
- what the shell expands when the command runs, beyond the program word: `IFS`, history, globs and braces in
  arguments;
- syntax this lexer does not model: it reads POSIX-like shell, and zsh's grammar beyond the forms above is
  not held.
Exit 2 blocks, with one line on stderr; exit 0 allows. The payload is the hook's JSON on stdin.
"""

from __future__ import annotations

import codecs
import fnmatch
import json
import os
import re
import sys
import threading
from dataclasses import dataclass, field

#: The longest command this reads; a longer one is blocked (the session's longest was under 20 000).
MAX_INPUT = 32768
#: How long the guard may read; past it, it blocks.
DEADLINE_S = 5.0
#: The owner's hooks and settings: the directories of these names at a work tree's root (the M21 closure
#: security seat's S3; `protected`).
OWNED = (".claude", ".githooks")
#: The directories the command may run in: the payload's `cwd`, then each a `cd` in it reaches (`_follow`).
WHERE: dict[str, list[str]] = {"dirs": []}
#: More directories than this, and the command is not read.
MAX_DIRS = 64
#: Programs that change each path they are given, and those that change only their destination.
CHANGES_EVERY = {"rm", "mv", "tee", "touch", "chmod", "chown", "chgrp", "truncate", "unlink", "rmdir", "shred", "mkdir"}
CHANGES_LAST = {"cp", "ln", "install", "rsync", "dd", "ditto"}
#: The programs whose `-t DIR` (`--target-directory`) is the destination; for any other, `-t` is not one.
TARGET_OPTION = {"cp", "mv", "ln", "install"}
#: `fly` subcommands an agent may run: each reads, none changes the hosted engine.
READ_ONLY_FLY = {("version",), ("help",), ("status",), ("logs",), ("auth", "whoami"), ("apps", "list"),
                 ("releases",), ("machine", "list"), ("machine", "status"), ("machines", "list"),
                 ("scale", "show"), ("secrets", "list"), ("config", "show"), ("ips", "list"),
                 ("checks", "list"), ("volumes", "list")}
#: Words that run the command after them; every later word is tried as that command.
WRAPPERS = {"env", "command", "builtin", "time", "exec", "nohup", "nice", "sudo", "doas", "xargs", "timeout",
            "gtimeout", "caffeinate", "coproc", "noglob", "nocorrect", "-", "repeat", "function", "stdbuf",
            "setsid", "watch", "unbuffer", "script", "chronic", "ionice", "taskpolicy"}
#: Shell words a command follows on its line: `then fly deploy` runs `fly deploy`.
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "fi", "done", "esac", "[", "[["}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "csh", "tcsh", "fish"}
#: A shell or `source` given one of these reads its commands from stdin.
STDIN_PATHS = {"-", "/dev/stdin", "/dev/fd/0", "/proc/self/fd/0"}
PROTECTED = {"main", "master", "trunk"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?=")
DEPLOY = "deploy_hosted_engine.sh"
#: The programs this guard reads; a program word written as a pattern that could match one is blocked.
GUARDED = {"fly", "flyctl", DEPLOY, "git", "rm", "eval", "source", ".", "find", *SHELLS, *WRAPPERS}
DESTRUCTIVE = "BLOCKED: destructive command (C.9, permission-matrix.md S5). Escalate to the owner instead."
PROTECTED_PUSH = ("BLOCKED: the agent never pushes the protected branch (AGENTS.md S3). Push YOUR branch and open a "
                  "draft PR; a human marks it ready and merges.")
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
    """A command this cannot read; it is blocked, never allowed."""


@dataclass
class Word:
    text: str
    glob: bool = False      # an unquoted * ? [ or { in it
    equals: bool = False    # it starts with an unquoted = (zsh's path expansion)
    quoted: bool = False    # some part of it was quoted


@dataclass
class Command:
    words: list[Word] = field(default_factory=list)
    fed: list[str] = field(default_factory=list)   # here-document bodies and here-strings it reads
    piped: bool = False                             # its stdin is a pipe
    from_file: bool = False                         # its stdin is a file
    writes: list[str] = field(default_factory=list)  # the paths its redirections write


class _Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []
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
        return Word("".join(self.parts), self.glob, self.equals, self.quoted)


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
                cmd = self._end(cmd)
                self._bodies()
            elif c in "<>" or s.startswith("&>", self.i):
                if cmd.words and last_end == self.i and cmd.words[-1].text.isdigit():
                    cmd.words.pop()  # an fd number written against its redirection
                self._redirect(cmd)
            elif c in ";&|":
                op = next(o for o in ("&&", "||", ";;&", ";;", ";&", "|&", "|", "&", ";") if s.startswith(o, self.i))
                self.i += len(op)
                cmd = self._end(cmd, piped=op in ("|", "|&"))
            elif c == "(":
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
                    cmd = self._end(cmd)  # a brace group's edge, and zsh's `if x {` and `} always {`
                    continue
                cmd.words.append(word)
                if word.text == "in" and len(cmd.words) >= 3 and cmd.words[0].text == "case":
                    self.patterns += 1
                    cmd = self._end(cmd)
                elif word.text == "esac" and len(cmd.words) == 1:
                    self.patterns = max(0, self.patterns - 1)
        self._end(cmd)
        if closing:
            raise Unreadable("an unclosed $( substitution")

    def _end(self, cmd: Command, piped: bool = False) -> Command:
        if cmd.words or cmd.fed:
            self.commands.append(cmd)
        return Command(piped=piped)

    def _bodies(self) -> None:
        """At a newline: each here-document opened on the line just ended takes the lines up to its delimiter
        (to the end, if none). An unquoted delimiter's body is expanded as the shell expands it."""
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
        elif op in ("<", "<>", "<&"):
            cmd.from_file = True
        if op in ("&>>", "&>", ">>", ">|", ">", "<>"):
            cmd.writes.append(target.text)

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
        self.commands.extend(sub.commands)

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
            self._substitution(")")
            b.add("$(...)", True)
        elif s.startswith("${", self.i):
            end = self._brace_end(self.i + 2)
            inner = s[self.i + 2:end]
            if inner.startswith("("):
                raise Unreadable("a `${(flags)...}`, which zsh may evaluate")
            self._expansions(inner)
            b.add("${...}", True)
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
        self.commands.extend(sub.commands)
        b.add("$(...)", True)
        self.i = j + 1

    def _substitution(self, closing: str) -> None:
        """A `$( )` substitution, read in a quoting context of its own; its commands are judged too."""
        sub = Lexer(self.s, self.depth + 1, self.i)
        sub.parse(closing)
        self.commands.extend(sub.commands)
        self.pending.extend(sub.pending)
        self.i = sub.i


# --- judging ------------------------------------------------------------------------------------------

def judge_text(text: str, depth: int = 0) -> str | None:
    """Why the command must be blocked, or None."""
    if len(text) > MAX_INPUT:
        raise Unreadable(f"the command is over {MAX_INPUT} characters")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lexer = Lexer(text, depth)
    lexer.parse()
    lexer._bodies()  # a here-document opened on the last line runs to the end
    _follow(lexer.commands)
    for cmd in lexer.commands:
        if (why := judge_command(cmd, depth)):
            return why
    return None


def judge_command(cmd: Command, depth: int) -> str | None:
    """Past assignments and keywords; after a wrapper, every later word is tried as the program, in one pass."""
    if any(_owners(path) for path in cmd.writes):
        return OWNERS
    words = cmd.words
    start = 0
    while start < len(words) and (ASSIGNMENT.match(words[start].text) or words[start].text in KEYWORDS):
        start += 1
    if start >= len(words):
        return None
    if _program(words[start]) not in WRAPPERS:
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
        if program in WRAPPERS and k != len(words) - 1:
            continue
        if program in GUARDED or word.glob or word.equals:
            tried += 1
            if tried > 64:
                raise Unreadable("more than 64 guarded programs behind wrappers")
            if (why := judge_words(words[k:], cmd, depth, behind_xargs=xargs_at < k)):
                return why
    return None


def _program(word: Word) -> str:
    return os.path.basename(word.text[1:] if word.equals else word.text)


def _could_name_guarded(pattern: str) -> bool:
    """Whether a pattern in a program word could be a guarded program. A brace expansion is not enumerated:
    it is taken as one that could."""
    if re.search(r"\{[^{}]*(,|\.\.)[^{}]*\}", pattern):
        return True
    return any(fnmatch.fnmatchcase(guarded, os.path.basename(pattern)) for guarded in GUARDED)


def _unique(option: str, wanted: str, known: list[str]) -> bool:
    """Whether git reads `option` as `wanted`: the whole name, or a prefix no other option of its shares."""
    name = option.split("=", 1)[0]
    if not name.startswith("--") or len(name) < 3 or not wanted.startswith(name):
        return False
    return name == wanted or not any(other.startswith(name) for other in known if other != wanted)


def _stdin(cmd: Command, depth: int, who: str) -> str | None:
    """A shell or `source` reading its commands from stdin: its here-documents and here-strings are read;
    a pipe or a file is not, so it is blocked."""
    if cmd.fed and not cmd.piped and not cmd.from_file:
        for text in cmd.fed:
            if (why := judge_text(text, depth + 1)):
                return why
        return None
    return (f"BLOCKED: {who} reading its commands from a pipe, a file or stdin, which this guard cannot read "
            "(#189); run the commands themselves, or the script by its name.")


def judge_words(words: list[Word], cmd: Command, depth: int, behind_xargs: bool = False) -> str | None:
    first = words[0]
    if first.glob and _could_name_guarded(first.text):
        return (f"BLOCKED: `{first.text}` names its program by a pattern that could be a guarded program, "
                "which this guard cannot read (#189); write the program's name.")
    program = _program(first)
    args = [w.text for w in words[1:]]
    if (why := _writes_protected(program, args)):
        return why
    if program == "eval":
        return judge_text(" ".join(args), depth + 1)
    if program in SHELLS:
        return _judge_shell(program, args, cmd, depth)
    if program in ("source", ".") and args:
        return _stdin(cmd, depth, f"`{program}`") if args[0] in STDIN_PATHS else judge_words(words[1:], cmd, depth)
    if program == "find":
        for i, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                rest = words[i + 2:]
                end = next((j for j, w in enumerate(rest) if w.text in (";", "+")), len(rest))
                if rest[:end] and (why := judge_words(rest[:end], cmd, depth)):
                    return why
        return None
    if program in ("fly", "flyctl"):
        sub = tuple(a for a in args if not a.startswith("-"))
        if behind_xargs or (sub and not any(sub[:len(allowed)] == allowed for allowed in READ_ONLY_FLY)):
            shown = " ".join(sub[:2]) if sub else "(its arguments from stdin)"
            return (f"BLOCKED: `{program} {shown}` may change the hosted engine, and only the owner runs that, in "
                    "their own terminal (D-185); an agent may run only the read-only subcommands.")
        return None
    if program == DEPLOY and (args != ["--dry-run"] or behind_xargs):
        return ("BLOCKED: the hosted engine is deployed by the owner, in their own terminal (D-185); an agent "
                "may run the script with --dry-run only.")
    if program == "git":
        return _judge_git(args, behind_xargs)
    if program == "rm":
        letters = "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))
        longs = [a for a in args if a.startswith("--")]
        recursive = "r" in letters or "R" in letters or any(_unique(a, "--recursive", GIT_LONG["rm"]) for a in longs)
        forced = "f" in letters or any(_unique(a, "--force", GIT_LONG["rm"]) for a in longs)
        if recursive and forced:
            return DESTRUCTIVE
    return None


OWNERS = ("BLOCKED: .claude/ and .githooks/ hold the owner's hooks and settings; an agent does not write them "
          "(OWNER APPROVAL, the M21 closure security seat's S3). Propose the change instead.")
ENV_FILE = "BLOCKED: writes to .env are denied per permission-matrix.md S6 (default-deny secrets)."


def protected(path: str, base: str) -> bool:
    """Whether writing `path`, from the directory `base`, writes the hooks or settings of a git work tree: the
    path (`~` and variables expanded, resolved from `base`, links followed on its longest existing part) lies
    in a directory named `.claude` or `.githooks`, in any case, whose parent holds a `.git` entry. The Bash
    guard and the Write and Edit hook both ask this (the fixes review's round 2, B1)."""
    full = os.path.realpath(os.path.join(base or os.getcwd(), os.path.expandvars(os.path.expanduser(path))))
    while True:
        parent = os.path.dirname(full)
        if os.path.basename(full).casefold() in OWNED and os.path.lexists(os.path.join(parent, ".git")):
            return True
        if parent == full:
            return False
        full = parent


def _owners(path: str, bases: list[str] | None = None) -> bool:
    """Whether a path a command writes is protected from any directory the command may run in."""
    return any(protected(path, base) for base in (bases if bases is not None else WHERE["dirs"]))


def _resolved(base: str, path: str) -> str:
    return os.path.realpath(os.path.join(base, os.path.expandvars(os.path.expanduser(path))))


def _changes_into(cmd: Command) -> str | None:
    """The directory a `cd`, `pushd` or `chdir` names (`~` for none), or None for any other command and for the
    forms that name no directory (`cd -`, `pushd +1`)."""
    words = [w.text for w in cmd.words]
    i = 0
    while i < len(words) and (ASSIGNMENT.match(words[i]) or words[i] in KEYWORDS or words[i] in ("builtin", "command")):
        i += 1
    if i >= len(words) or words[i] not in ("cd", "pushd", "chdir"):
        return None
    rest = words[i + 1:]
    while rest and rest[0].startswith("-") and rest[0] != "-":
        done, rest = rest[0] == "--", rest[1:]
        if done:
            break
    if not rest:
        return "~" if words[i] != "pushd" else None
    return None if rest[0] == "-" or rest[0].startswith("+") else rest[0]


def _follow(commands: list[Command]) -> None:
    """Each directory a `cd` in these commands changes into, from every directory reached before it, joins the
    ones a written path is judged from. They are never dropped: a `cd` in a subshell or one that fails is
    taken as made, which can only refuse more."""
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


def _target_option(args: list[str]) -> list[str]:
    """`-t DIR`, `-tDIR` (or a cluster ending `t`), `--target-directory DIR`, `=DIR`, or a unique prefix of it."""
    found: list[str] = []
    for i, arg in enumerate(args):
        name = arg.split("=", 1)[0]
        if arg.startswith("--") and len(name) >= 3 and "--target-directory".startswith(name):
            value = arg.split("=", 1)[1] if "=" in arg else (args[i + 1] if i + 1 < len(args) else "")
            found.append(value)
        elif arg.startswith("-") and not arg.startswith("--") and "t" in arg[1:]:
            rest = arg[arg.index("t", 1) + 1:]
            found.append(rest or (args[i + 1] if i + 1 < len(args) else ""))
    return [f for f in found if f]


def _writes_protected(program: str, args: list[str]) -> str | None:
    """A write into a work tree's `.claude/` or `.githooks/` by a program this lists (S3; round 2, B1 and M6)."""
    paths = [a for a in args if not a.startswith("-")]
    option = _target_option(args) if program in TARGET_OPTION else []
    if program == "dd":
        written = [a[3:] for a in args if a.startswith("of=")]
    elif program == "install" and any(a in ("-d", "--directory") for a in args):
        written = paths
    elif program in CHANGES_EVERY:
        written = paths + option
    elif program in CHANGES_LAST:
        written = option or paths[-1:]   # with `-t`, the last word is a source
    else:
        written = []
    if any(_owners(a) for a in written):
        return OWNERS
    in_place = (program == "sed" and any(a.startswith("-i") or a == "--in-place" or a.startswith("--in-place=")
                                         for a in args)) or (
        program == "perl" and any(a.startswith("-") and not a.startswith("--") and "i" in a[1:] for a in args))
    if (in_place and any(_owners(a) for a in paths)) or (program == "git" and _git_writes(args)):
        return OWNERS
    return None


def _git_writes(args: list[str]) -> bool:
    """`git rm`, `git mv`, `git checkout` or `git restore` naming a protected path, from each `-C` directory."""
    bases, i = list(WHERE["dirs"]), 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            bases = [_resolved(base, args[i + 1]) for base in bases]
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") else 1
    sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
    return sub in ("rm", "mv", "checkout", "restore") and any(_owners(a, bases) for a in rest if not a.startswith("-"))


def judge_write(path: str, base: str) -> str | None:
    """The Write and Edit hook (`--write`): a `.env` file, or a path `protected` refuses."""
    if path.endswith(".env") or ".env." in path:
        return ENV_FILE
    if path and protected(path, base):
        return OWNERS
    return None


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


def _judge_git(args: list[str], behind_xargs: bool) -> str | None:  # noqa: C901 -- one branch per subcommand
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    options = [a for a in rest if a.startswith("-")]
    longs = [a for a in options if a.startswith("--")]
    letters = "".join(a[1:] for a in options if not a.startswith("--"))
    known = GIT_LONG.get(sub, [])

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
            return ("BLOCKED: `git restore` without --staged, or with --worktree, discards uncommitted work "
                    "(permission-matrix.md S5). Revert in place, or use --staged to unstage only.")
    return None


def _expired() -> None:
    """The guard's own bound (S2): a thread, so it holds where SIGALRM does not exist. It cannot stop a long call
    into C that holds the interpreter; the hook's timeout bounds that."""
    sys.stderr.buffer.write(f"BLOCKED: the command was not read within {DEADLINE_S:g} s (#189).\n".encode())
    sys.stderr.flush()
    os._exit(2)


def main(argv: list[str] | None = None) -> int:
    write = (sys.argv[1:] if argv is None else argv) == ["--write"]
    timer = threading.Timer(DEADLINE_S, _expired)
    timer.daemon = True
    timer.start()
    try:  # bytes, so a console's encoding (cp1254) cannot change what is read
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if write and not isinstance(payload, dict):
            raise ValueError("the payload is not a JSON object")
        call = payload.get("tool_input", {}) if isinstance(payload, dict) else {}
        # The directory the call runs in: the payload's `cwd`, which Claude Code always sends.
        base = (str(payload.get("cwd") or "") if isinstance(payload, dict) else "") or \
            os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()
        if write:
            why = judge_write(str(call.get("file_path", "") or ""), base)
        else:
            WHERE["dirs"] = [os.path.realpath(base)]
            command = str(call.get("command", ""))
            why = judge_text(command) if command.strip() else None
        timer.cancel()
    except BaseException as error:  # any doubt blocks: a guard that cannot read the call never allows it
        why = (f"BLOCKED: this guard cannot read the tool call ({type(error).__name__}: {error}) (#189)." if write else
               f"BLOCKED: this guard cannot read the command ({type(error).__name__}: {error}) (#189).")
    if why:
        sys.stderr.buffer.write(why.encode("utf-8", "replace") + b"\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
