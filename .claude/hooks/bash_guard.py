"""#189: the Bash guard's second reading -- the command split as the shell splits it.

The guard in `.claude/settings.json` matches the command's text, and runs first, unchanged. This reads
the command with a lexer of its own and judges each simple command it finds:
- after `;`, `&&`, `||`, `|`, `|&`, `&`, a newline, `(` or `)`, and inside `$( )`, backticks and `<( )`,
  outside single quotes (in double quotes too); text in single quotes, and a here-document's body, is data;
- with quotes removed and `$'..'` decoded; a `#` starts a comment only where a word would start, to the end
  of its line; a redirection (`>`, `>>`, `<`, `2>`, `&>`, `>&`, `<<<`, `<<`) and its target are skipped and
  the same command read on;
- past assignments and the shell keywords (`then`, `do`, `{`, `!` and the rest), and past a wrapper
  (WRAPPERS: `env`, `sudo`, `xargs`, `timeout`, `nice`, zsh's `noglob`, `nocorrect`, `-`, `repeat N` and
  others): after a wrapper every later word is tried as the program, so an option's value is never taken
  for it; `env -S`'s string is read as a command;
- inside `bash`, `sh`, `zsh`, `dash` or `ksh` given `-c` (every word after it), a script file (its name
  and arguments), or a here-document or here-string (its body); a shell that reads its commands from a
  pipe or a file is blocked, since its commands cannot be read here; `eval`, `source`, `.` and
  `find -exec` likewise.

What it blocks, in those spellings:
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY, and any `fly` behind `xargs`, whose
  arguments come from stdin (D-185);
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run` (D-185);
- blocked too: a `git push` that forces (`--force` or a unique prefix of it, a short-option cluster holding
  `f`, a `+` refspec), mirrors (`--mirror` or a unique prefix), pushes every branch (`--all`, `--branches`
  or a prefix), names main, master or trunk as its destination, or runs behind `xargs` (AGENTS.md S3);
- `git reset --hard` (or a prefix), `git clean` with `-f`, `git checkout --` or `.`, `git restore` without
  `--staged` or with `--worktree` (or a prefix of either), and `rm` both recursive and forced
  (permission-matrix.md S5);
- a program word with an unquoted glob character (`fl[y]`, `*`, `?`, `{`), which names a program this
  cannot know; a leading `=` (zsh's path expansion) is read as the name after it.

Not held, and how the owner may close each (G-7):
- a program named through a variable, a command substitution or an alias (`$CMD deploy`, `$(echo fly)`),
  or through a function or an alias defined in an earlier call;
- a script's own contents (`bash deploy.sh` reads the name, not the file), and an interpreter given code
  (`python -c`, `perl -e`, `node -e`);
- a push set through `git -c` or `git config` (`remote.origin.push`, `push.default`), an alias such as
  `git config alias.p 'push --force'`, and a git hook;
- a wrapper this does not list (WRAPPERS), whose program is then read as an argument;
- what the shell expands at run time: brace and tilde expansion beyond the program word, `IFS`, history.
It only adds blocks to the text guard's. A command it cannot read (an unclosed quote or substitution) is
blocked. Exit 2 blocks, with one line on stderr; exit 0 allows. The payload is the hook's JSON on stdin.
"""

from __future__ import annotations

import codecs
import json
import os
import re
import sys
from dataclasses import dataclass, field

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
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "fi", "done", "esac", "[", "[["}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
PROTECTED = {"main", "master", "trunk"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?\+?=")
DEPLOY = "deploy_hosted_engine.sh"
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


@dataclass
class Command:
    words: list[Word] = field(default_factory=list)
    fed: list[str] = field(default_factory=list)   # here-document bodies and here-strings it reads
    piped: bool = False                             # its stdin is a pipe
    from_file: bool = False                         # its stdin is a file


class _Builder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.glob = self.equals = False

    def add(self, text: str, quoted: bool) -> None:
        if not quoted:
            if not self.parts and text.startswith("="):
                self.equals = True
            self.glob = self.glob or any(ch in text for ch in "*?[{")
        self.parts.append(text)


class Lexer:
    """One pass over the text: simple commands, substitutions inside them, here-documents after them."""

    def __init__(self, text: str, depth: int = 0, start: int = 0) -> None:
        if depth > 12:
            raise Unreadable("substitutions nested too deep")
        self.s, self.i, self.depth = text, start, depth
        self.commands: list[Command] = []
        self.pending: list[tuple[str, bool, Command]] = []
        self.patterns = 0  # `case ... in` seen: a `)` may end a pattern inside `$( )`

    # --- the command level ---------------------------------------------------------------------------
    def parse(self, closing: str | None = None) -> None:
        cmd = Command()
        parens = 0
        last_end = -1
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if closing == "`" and c == "`":
                self.i += 1
                self._end(cmd)
                return
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
                if s.startswith("((", self.i) and not cmd.words:
                    self._arithmetic(self.i + 2)  # `(( x <<= 1 ))` is arithmetic, not a here-document
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
                cmd.words.append(self._word(closing))
                last_end = self.i
                if cmd.words[-1].text == "in" and len(cmd.words) >= 3 and cmd.words[0].text == "case":
                    self.patterns += 1
                    cmd = self._end(cmd)
                elif cmd.words[-1].text == "esac" and len(cmd.words) == 1:
                    self.patterns = max(0, self.patterns - 1)
        self._end(cmd)
        if closing:
            raise Unreadable(f"an unclosed {'$(' if closing == ')' else 'backtick'} substitution")

    def _end(self, cmd: Command, piped: bool = False) -> Command:
        if cmd.words or cmd.fed:
            self.commands.append(cmd)
        return Command(piped=piped)

    def _bodies(self) -> None:
        """At a newline: each here-document opened on the line just ended takes the lines up to its delimiter.
        A body with no delimiter runs to the end, as the shell reads it."""
        for delimiter, tabs, owner in self.pending:
            lines: list[str] = []
            while self.i < len(self.s):
                end = self.s.find("\n", self.i)
                line = self.s[self.i:end] if end >= 0 else self.s[self.i:]
                self.i = end + 1 if end >= 0 else len(self.s)
                if (line.lstrip("\t") if tabs else line) == delimiter:
                    break
                lines.append(line)
            owner.fed.append("\n".join(lines))
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
        target = self._word(None)
        if op in ("<<", "<<-"):
            self.pending.append((target.text, op == "<<-", cmd))
        elif op == "<<<":
            cmd.fed.append(target.text)
        elif op in ("<", "<>", "<&"):
            cmd.from_file = True

    # --- the word level ------------------------------------------------------------------------------
    def _word(self, closing: str | None) -> Word:
        b = _Builder()
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\n;&|()<>" or (closing == "`" and c == "`"):
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
                self.i += 1
                self._substitution("`")
                b.add("$(...)", True)
            else:
                b.add(c, False)
                self.i += 1
        return Word("".join(b.parts), b.glob, b.equals)

    def _double(self, b: _Builder) -> None:
        s = self.s
        self.i += 1
        while self.i < len(s):
            c = s[self.i]
            if c == '"':
                self.i += 1
                return
            if c == "\\" and s[self.i + 1:self.i + 2] in ('$', '`', '"', "\\", "\n"):
                if s[self.i + 1] != "\n":
                    b.add(s[self.i + 1], True)
                self.i += 2
            elif c == "$":
                self._dollar(b, in_double=True)
            elif c == "`":
                self.i += 1
                self._substitution("`")
                b.add("$(...)", True)
            else:
                b.add(c, True)
                self.i += 1
        raise Unreadable("an unclosed double quote")

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
        elif s.startswith("$((", self.i):
            self._arithmetic(self.i + 3)
            b.add("$((...))", True)
        elif s.startswith("$(", self.i):
            self.i += 2
            self._substitution(")")
            b.add("$(...)", True)
        elif s.startswith("${", self.i):
            depth, j = 0, self.i + 1
            while j < len(s):
                depth += {"{": 1, "}": -1}.get(s[j], 0)
                if depth == 0:
                    break
                j += 1
            if j >= len(s):
                raise Unreadable("an unclosed ${")
            inner = s[self.i + 2:j]
            if "$(" in inner or "`" in inner:  # `${x:-$(cmd)}` runs cmd
                sub = Lexer(inner, self.depth + 1)
                sub.parse()
                self.commands.extend(sub.commands)
            b.add("$" + s[self.i + 1:j + 1], True)
            self.i = j + 1
        else:
            name = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*|[0-9@*#?$!-])", s[self.i:])
            if name:
                b.add(name.group(0), True)
                self.i += name.end()
            else:
                b.add("$", True)
                self.i += 1

    def _arithmetic(self, start: int) -> None:
        """Past `$(( ... ))` or `(( ... ))`: arithmetic runs no command (a `<<` there is a shift)."""
        depth, j = 2, start
        while j < len(self.s) and depth:
            depth += {"(": 1, ")": -1}.get(self.s[j], 0)
            j += 1
        if depth:
            raise Unreadable("an unclosed $((")
        self.i = j

    def _substitution(self, closing: str) -> None:
        """A command substitution, read in a quoting context of its own; its commands are judged too."""
        sub = Lexer(self.s, self.depth + 1, self.i)
        sub.parse(closing)
        self.commands.extend(sub.commands)
        self.pending.extend(sub.pending)
        self.i = sub.i


# --- judging ------------------------------------------------------------------------------------------

def judge_text(text: str, depth: int = 0) -> str | None:
    """Why the command must be blocked, or None."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lexer = Lexer(text, depth)
    lexer.parse()
    lexer._bodies()  # a here-document opened on the last line runs to the end
    for cmd in lexer.commands:
        if (why := judge_command(cmd, depth)):
            return why
    return None


def judge_command(cmd: Command, depth: int) -> str | None:
    words = cmd.words
    start = 0
    while start < len(words) and (ASSIGNMENT.match(words[start].text) or words[start].text in KEYWORDS):
        start += 1
    if start >= len(words):
        return None
    candidates = [start]
    xargs_at = len(words)
    if _program(words[start]) in WRAPPERS:
        candidates = list(range(start, len(words)))
    for k in candidates:
        program = _program(words[k])
        if program == "xargs":
            xargs_at = min(xargs_at, k)
        if program == "env":
            for j in range(k + 1, len(words)):
                arg = words[j].text
                if arg in ("-S", "--split-string") and j + 1 < len(words):
                    if (why := judge_text(words[j + 1].text, depth + 1)):
                        return why
                elif arg.startswith(("-S", "--split-string=")) and len(arg) > 2:
                    if (why := judge_text(arg.split("=", 1)[-1] if arg.startswith("--") else arg[2:], depth + 1)):
                        return why
        if (program in WRAPPERS and k != len(words) - 1) or (k > start and words[k].text.startswith("-")
                                                             and words[k].text != "-"):
            continue
        if (why := judge_words(words[k:], cmd, depth, behind_xargs=xargs_at < k)):
            return why
    return None


#: The programs this guard reads; a program word written as a pattern that matches one is blocked.
GUARDED = {"fly", "flyctl", DEPLOY, "git", "rm", "eval", "source", ".", "find", *SHELLS, *WRAPPERS}


def _could_name_guarded(pattern: str) -> bool:
    """Whether a glob (`fl[y]`, `*`, `{fly,x}`) in a program word could expand to a guarded program."""
    import fnmatch

    names = [pattern]
    while any("{" in n and "," in n for n in names):
        expanded = []
        for name in names:
            brace = re.search(r"\{([^{}]*,[^{}]*)\}", name)
            expanded += ([name[:brace.start()] + part + name[brace.end():] for part in brace.group(1).split(",")]
                         if brace else [name])
        if expanded == names:
            break
        names = expanded
    return any(fnmatch.fnmatchcase(guarded, os.path.basename(name)) for name in names for guarded in GUARDED)


def _program(word: Word) -> str:
    return os.path.basename(word.text[1:] if word.equals else word.text)


def _unique(option: str, wanted: str, known: list[str]) -> bool:
    """Whether git reads `option` as `wanted`: the whole name, or a prefix no other option of its shares."""
    name = option.split("=", 1)[0]
    if not name.startswith("--") or len(name) < 3 or not wanted.startswith(name):
        return False
    return name == wanted or not any(other.startswith(name) for other in known if other != wanted)


def judge_words(words: list[Word], cmd: Command, depth: int, behind_xargs: bool = False) -> str | None:
    first = words[0]
    if first.glob and first.text not in KEYWORDS and _could_name_guarded(first.text):
        return (f"BLOCKED: `{first.text}` names its program by a pattern that could be a guarded program, "
                "which this guard cannot read (#189); write the program's name.")
    program = _program(first)
    args = [w.text for w in words[1:]]
    if program == "eval":
        return judge_text(" ".join(args), depth + 1)
    if program in SHELLS:
        return _judge_shell(args, cmd, depth)
    if program in ("source", ".") and args:
        return judge_words(words[1:], cmd, depth)
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


def _judge_shell(args: list[str], cmd: Command, depth: int) -> str | None:
    """A shell runs `-c`'s string, a script file, or what it reads on stdin."""
    if any(a in ("--version", "--help") for a in args):
        return None
    j, given_c, reads_stdin = 0, False, False
    while j < len(args):
        arg = args[j]
        if arg == "--":
            j += 1
            break
        if arg in ("-o", "+o", "-O", "+O"):
            j += 2
            continue
        if arg.startswith(("-", "+")) and len(arg) > 1:
            if not arg.startswith("--"):
                given_c = given_c or "c" in arg[1:]
                reads_stdin = reads_stdin or "s" in arg[1:]
            j += 1
            continue
        break
    rest = args[j:]
    if given_c:
        for text in rest:  # the string, then $0 and its arguments: each read as a command
            if (why := judge_text(text, depth + 1)):
                return why
        return None
    if rest and not reads_stdin:
        return judge_words([Word(a) for a in rest], cmd, depth)
    if cmd.fed and not cmd.piped and not cmd.from_file:
        for text in cmd.fed:
            if (why := judge_text(text, depth + 1)):
                return why
        return None
    return ("BLOCKED: a shell reading its commands from a pipe or a file, which this guard cannot read (#189); "
            "run the commands themselves, or the script by its name.")


def _judge_git(args: list[str], behind_xargs: bool) -> str | None:
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
        targets = {ref.split(":")[-1].removeprefix("refs/heads/") for ref in refs}
        if behind_xargs or given("--all", "--branches") or PROTECTED & targets:
            return PROTECTED_PUSH
    elif sub == "reset" and given("--hard"):
        return DESTRUCTIVE
    elif sub == "clean" and ("f" in letters or given("--force")):
        return DESTRUCTIVE
    elif sub == "checkout" and ("--" in rest or "." in rest):
        return DESTRUCTIVE
    elif sub == "restore":
        staged = "S" in letters or given("--staged")
        worktree = "W" in letters or given("--worktree")
        if not staged or worktree:
            return ("BLOCKED: `git restore` without --staged, or with --worktree, discards uncommitted work "
                    "(permission-matrix.md S5). Revert in place, or use --staged to unstage only.")
    return None


def main() -> int:
    try:  # bytes, so a console's encoding (cp1254) cannot change what is read
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        command = str(payload.get("tool_input", {}).get("command", "")) if isinstance(payload, dict) else ""
        why = judge_text(command) if command.strip() else None
    except Exception as error:  # any doubt blocks: a guard that cannot read the call never allows it
        why = f"BLOCKED: this guard cannot read the command ({type(error).__name__}: {error}) (#189)."
    if why:
        sys.stderr.buffer.write(why.encode("utf-8") + b"\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
