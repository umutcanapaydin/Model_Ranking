"""#189: the Bash guard's second reading -- the command split as the shell splits it.

The guard in `.claude/settings.json` matches the command's text, and runs first, unchanged. This reads
the command with a shell tokenizer (`shlex`) and judges each simple command wherever it starts: after
`;`, `&&`, `||`, `|`, `&`, a newline, `(`, `$(`, a backtick or a shell keyword (`then`, `do`, `{`,
`!`); behind assignments and `env`, `command`, `time`, `exec`, `nohup`, `nice`, `sudo`, `xargs` or
`timeout`; inside `bash -c`, `sh -c`, `zsh -c`, `eval` or `find -exec`; and with its words unquoted
(`'HEAD:main'`, `\\+x`, `''+x`, `$'--mirror'`). A here-document's body is data and is not read.

What it blocks, in any of those spellings:
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY (D-185);
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run`, directly, through a shell or
  sourced (D-185);
- blocked too: `git push` that forces (`--force*`, a short-option cluster holding `f`, a `+` refspec), mirrors
  (`--mirror` or an abbreviation), pushes every branch (`--all`) or names main, master or trunk as
  its destination (AGENTS.md S3);
- `git reset --hard`, `git clean` with `-f`, `git checkout --` or `.`, `git restore` without
  `--staged` or with `--worktree`, and `rm` both recursive and forced (permission-matrix.md S5).

It only adds blocks to the text guard's. A command it cannot split (an unclosed quote) is blocked.
Exit 2 blocks, with one line on stderr; exit 0 allows. The payload is the hook's JSON on stdin.
"""

from __future__ import annotations

import codecs
import json
import os
import re
import shlex
import sys

#: `fly` subcommands an agent may run: each reads, none changes the hosted engine.
READ_ONLY_FLY = {("version",), ("help",), ("status",), ("logs",), ("auth", "whoami"), ("apps", "list"),
                 ("releases",), ("machine", "list"), ("machine", "status"), ("machines", "list"),
                 ("scale", "show"), ("secrets", "list"), ("config", "show"), ("ips", "list"),
                 ("checks", "list"), ("volumes", "list")}
#: Words that run the command after them (their own options skipped).
WRAPPERS = {"env", "command", "time", "exec", "nohup", "nice", "sudo", "xargs", "builtin", "timeout"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
#: Shell words a command may follow on its line: `then fly deploy` runs `fly deploy`.
KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{", "}", "fi", "done", "esac"}
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", ";;", "|&", ";&"}
PROTECTED = {"main", "master", "trunk"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
DEPLOY = "deploy_hosted_engine.sh"


class Unreadable(Exception):
    """A command this cannot split; it is blocked, never allowed."""


def _flattened(text: str) -> str:
    """The text with continued lines joined, here-document bodies dropped, `$'..'` decoded to a plain
    quoted word, and each newline outside quotes made a `;`."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\\\n", "")
    out: list[str] = []
    pending: list[tuple[str, bool]] = []  # here-documents opened on this line: (delimiter, tabs stripped)
    lines = text.split("\n")
    quote = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        i = 0
        while i < len(line):
            ch = line[i]
            if quote == "'":
                out.append(ch)
                quote = "" if ch == "'" else quote
            elif quote == '"':
                if ch == "\\" and i + 1 < len(line):
                    out.append(line[i:i + 2])
                    i += 1
                else:
                    out.append(ch)
                    quote = "" if ch == '"' else quote
            elif ch == "\\" and i + 1 < len(line):
                out.append(line[i:i + 2])
                i += 1
            elif ch == "$" and line[i + 1:i + 2] == "'":
                end = i + 2
                while end < len(line) and line[end] != "'":
                    end += 2 if line[end] == "\\" else 1
                if end >= len(line):
                    raise Unreadable("an unclosed $'...' quote")
                decoded = codecs.decode(line[i + 2:end].encode("latin-1", "backslashreplace"), "unicode_escape")
                out.append(shlex.quote(decoded))
                i = end
            elif ch in "'\"":
                out.append(ch)
                quote = ch
            elif line.startswith("<<", i) and not line.startswith("<<<", i):
                heredoc = re.match(r"<<(-?)\s*(['\"]?)([\w.@/-]+)\2", line[i:])
                if not heredoc:
                    raise Unreadable("a here-document with no delimiter")
                pending.append((heredoc.group(3), heredoc.group(1) == "-"))
                out.append(" ")
                i += heredoc.end() - 1
            else:
                out.append(ch)
            i += 1
        if quote:
            out.append("\n")  # a newline inside quotes is part of the word
            continue
        out.append(" ; ")
        for delimiter, tabs in pending:
            while index < len(lines) and (lines[index].lstrip("\t") if tabs else lines[index]) != delimiter:
                index += 1
            if index >= len(lines):
                raise Unreadable(f"a here-document that never ends ({delimiter})")
            index += 1
        pending = []
    if quote:
        raise Unreadable("an unclosed quote")
    return "".join(out)


def _substitutions(text: str) -> list[str]:
    """The text of each `$(...)` and backtick substitution, which the shell runs wherever it stands."""
    found = re.findall(r"`([^`]*)`", text)
    start = text.find("$(")
    while start >= 0:
        depth, end = 0, start + 1
        while end < len(text):
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            if depth == 0:
                break
            end += 1
        found.append(text[start + 2:end])
        start = text.find("$(", start + 2)
    return found


def judge_text(text: str, depth: int = 0) -> str | None:
    """Why the command must be blocked, or None."""
    if depth > 8:
        raise Unreadable("substitutions nested too deep")
    flat = _flattened(text)
    for inner in _substitutions(flat):
        if (why := judge_text(inner, depth + 1)):
            return why
    lexer = shlex.shlex(flat.replace("`", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError as error:
        raise Unreadable(str(error)) from error
    words: list[str] = []
    for token in [*tokens, ";"]:
        if token in SEPARATORS or set(token) <= set(";&|()<>"):
            if words and (why := judge(words, depth)):
                return why
            words = []
        else:
            words.append(token)
    return None


def _after_wrappers(words: list[str]) -> list[str]:
    i = 0
    while i < len(words):
        word = words[i]
        if ASSIGNMENT.match(word) or word == "$" or word in KEYWORDS:
            i += 1
        elif os.path.basename(word) in WRAPPERS:
            wrapper = os.path.basename(word)
            i += 1
            while i < len(words) and (words[i].startswith("-") or ASSIGNMENT.match(words[i])):
                takes = words[i] in ("-u", "-C", "-S", "-n", "-I", "-L", "-s", "-k", "-g")
                i += 2 if takes else 1
            if wrapper == "timeout" and i < len(words):
                i += 1  # the duration
        else:
            break
    return words[i:]


def judge(words: list[str], depth: int) -> str | None:
    words = _after_wrappers(words)
    if not words:
        return None
    program, args = os.path.basename(words[0]), words[1:]
    if program == "eval":
        return judge_text(" ".join(args), depth + 1)
    if program in SHELLS:
        for i, arg in enumerate(args):
            if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                return judge_text(args[i + 1], depth + 1) if i + 1 < len(args) else None
        script = [a for a in args if not a.startswith("-")]
        return judge(script, depth) if script else None
    if program in ("source", ".") and args:
        return judge(args, depth)
    if program == "find":
        for i, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                rest = args[i + 1:]
                end = next((j for j, a in enumerate(rest) if a in (";", "\\;", "+")), len(rest))
                if (why := judge(rest[:end], depth)):
                    return why
        return None
    if program in ("fly", "flyctl"):
        sub = tuple(a for a in args if not a.startswith("-"))
        if sub and not any(sub[:len(allowed)] == allowed for allowed in READ_ONLY_FLY):
            return (f"BLOCKED: `{program} {' '.join(sub[:2])}` changes the hosted engine, and only the owner runs "
                    "that, in their own terminal (D-185); an agent may run only the read-only subcommands.")
        return None
    if program == DEPLOY and args != ["--dry-run"]:
        return ("BLOCKED: the hosted engine is deployed by the owner, in their own terminal (D-185); an agent "
                "may run the script with --dry-run only.")
    if program == "git":
        return _judge_git(args)
    if program == "rm":
        letters = "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))
        recursive = "r" in letters or "R" in letters or "--recursive" in args
        if recursive and ("f" in letters or "--force" in args):
            return "BLOCKED: destructive command (C.9, permission-matrix.md S5). Escalate to the owner instead."
    return None


def _judge_git(args: list[str]) -> str | None:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    destructive = "BLOCKED: destructive command (C.9, permission-matrix.md S5). Escalate to the owner instead."
    if sub == "push":
        options = [a for a in rest if a.startswith("-")]
        refs = [a for a in rest if not a.startswith("-")]
        forced = any(a.startswith("--force") or (not a.startswith("--") and "f" in a[1:]) for a in options)
        mirrored = any(len(a.split("=")[0]) >= 4 and "--mirror".startswith(a.split("=")[0]) for a in options)
        if forced or mirrored or any(ref.startswith("+") for ref in refs):
            return destructive
        targets = [ref.split(":")[-1].removeprefix("refs/heads/") for ref in refs]
        if "--all" in options or PROTECTED & set(targets):
            return ("BLOCKED: the agent never pushes the protected branch (AGENTS.md S3). Push YOUR branch and "
                    "open a draft PR; a human marks it ready and merges.")
    if sub == "reset" and "--hard" in rest:
        return destructive
    if sub == "clean" and any(a == "--force" or (a.startswith("-") and not a.startswith("--") and "f" in a)
                              for a in rest):
        return destructive
    if sub == "checkout" and ("--" in rest or "." in rest):
        return destructive
    if sub == "restore" and ("--staged" not in rest and "-S" not in rest or "--worktree" in rest or "-W" in rest):
        return ("BLOCKED: `git restore` without --staged discards uncommitted work (permission-matrix.md S5). "
                "Revert in place, or use --staged to unstage only.")
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
