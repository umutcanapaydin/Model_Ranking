#!/usr/bin/env python3
"""The Bash guard: every Bash tool call, read as the shell splits it, judged one simple command at a time.

`.claude/settings.json` runs this as the PreToolUse hook for `Bash`, and with `--write` as the PreToolUse
hook for `Write`, `Edit` and `MultiEdit`, each after checking its sha256 against the pin written there
(`make guard-pin` rewrites them; INSTALL.md, "Changing the Bash guard"); `.codex/hooks.json` runs the same
command for Codex's `Bash`. The hook's JSON arrives on stdin; exit 2 refuses the call with one `BLOCKED:` line
on stderr, exit 0 allows it.

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
  mirrors, pushes every branch (`--all`, `--branches`), names a protected branch as the destination
  (`main`, `HEAD:main`, `heads/main`, `refs/heads/main`) -- `main`, `master`, `trunk`, and the default of the
  call's repository, its `origin/HEAD`, else `init.defaultBranch` (v7.3) -- or runs behind `xargs`; git's
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
  `.githooks`, unsetting it, or dropping the `core` section; and husky's off switch on a push (v7.3:
  `make hooks` may run the gate through husky): `HUSKY` set to `0` or to what this cannot read, or
  `HUSKY_SKIP_HOOKS` (husky 4) set to `1`, `true` or the unreadable -- as a prefix, through `env`, exported or
  assigned anywhere in the text that pushes;
- a git alias, judged as the command it names (`!` and shell text, or git and its words): an alias set by
  `-c alias.x=...` with the words it is then called with, through a chain of aliases as git resolves it
  (`git -c alias.r=reset r --hard` is `git reset --hard`); a persistent one (`git config [set] alias.x ...`) only to a read-only git command, since its
  later calls cannot be paired with it (`git config alias.r reset && git r --hard`); one set through
  `--config-env` or `GIT_CONFIG_*` is refused, its value unread. A config key whose value git runs
  (`core.pager`, `core.fsmonitor`, `core.sshCommand`, `diff.external`, filters, ...) is judged as shell
  text where it is set, a leading `!` taken off as git takes it (`credential.helper '!rm -rf ~'` walked through
  as a program named `!rm`, #305), and `include.path` is refused: it reads a file this does not open. So are the
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
- an assignment that may not happen or does not last, by where it stands (#287): in a subshell, a substitution, a
  pipeline stage, behind `&`, after `||`, after an `&&` a later command does not wait on, in a branch's or a loop's
  body (`if`/`for`/`while`/`until`/`select`/`case`/`foreach`/`repeat` to `fi`/`done`/`esac`/`end`), or anywhere
  after a function is defined (`f()`, `f ()`, `function f`, zsh's `functions[f]=`) -- and one a child process or a
  deferred text makes (`bash -c`, a `trap`, an `alias`, a git alias): the call is judged twice, once with every
  such assignment made and once with none (WORLD), and refused when either refuses. So the name, though it had no
  value before (`(X=$(mktemp -d)); rm -rf "$X"/Users/x` ran `rm -rf /Users/x`), is unset in the second and its
  target no scratch, and a literal it may take (`f() { :; }; d=.claude; echo x > "$d"/settings.json`) is read in
  the first, as every refusal reads one -- an unknown value never stands for a harmless one (the bundle security
  review's B1); one set in the line of the text holds after such a body as before;
- an assignment before a program (`HOME=$(mktemp -d) true`), or behind `env` and the other wrappers, sets
  nothing for later words or commands, and `env -u NAME`, `env -i`, `exec -c`, `sudo` and `doas` leave
  `$TMPDIR` and this text's names unknown for what they run, so from there on the name is unknown (`... && rm -rf "$HOME"`
  removed the real home past v7.1.1) -- in the second world; in the first it holds, as before a POSIX special
  builtin; `read`, `mapfile`, `getopts`, `unset`, `printf -v`, `for`, `select`, zsh's `print -v` and
  module binders, `${NAME:=...}`, and `declare -n` (for the reference and its target) make the names they
  bind unknown -- but a `for NAME in WORDS` over literal words, NAME unset before it, gives NAME each word in
  turn: the call is judged once per word, every combination up to MAX_PASSES (v7.3);
- a value this cannot read, where a refusal would read it (#344): a command substitution's output (but a lone
  `mktemp`'s), an array (`a=(.claude)`, `mapfile`), a positional parameter (`$1`, `$@`), a `${...}` that is not a
  plain `${name}` (`${d:-.claude}`), a pattern, or a name this text gave one of them -- as a write's target (a
  redirection, and the paths of the owner's-directory rule's programs, `sed -i`/`perl -i` files included), as a
  program word's last part (`p=$(echo fly); $p deploy`), and as any word of a git subcommand that writes (GIT_UNREAD_SUBS:
  `git push origin "$(...)"`, `git commit $o`), a message's value (`-m "$(cat msg)"`) and a `-C` of a reading one
  excepted. Such a value may be the owner's file, `--no-verify` or `main`, so it is refused, as it was once read as
  harmless (`d=$(echo .claude); echo x > "$d"/settings.json`). A value built from this text's literals and the
  environment (`d=$HOME/notes`) is read as the shell will, and a `${NAME:-literal}` (`-`, `:=`, `=` too) outside an
  assignment as each value it may take, NAME's and the literal's (`"${TMPDIR:-/tmp}/x"` passes,
  `"${X:-.claude}"/settings.json` does not; the bundle review's M5);
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
  and `git commit -m 'fly deploy notes'` are not. Where the brief declares a `gh workflow run` deploy, a
  `gh run rerun` is also handed over as `gh workflow run <its workflow>`, which one `gh api` call reads; one
  gh cannot place is refused (v7.3);
- a program word written as a pattern (`gi*`, `{git,ls}`), which could name anything;
- a command that names the gate stamp (`devflow-gate…`) or its script (`gate_stamp…`; lower-cased, quotes,
  backslashes and `$` removed first) anywhere but where it is only read: `make gate` writes it when it passes,
  and pre-push and `/pre-merge` trust it, so a stamp written by hand is a gate that never ran. Read means an
  operand of a program in STAMP_READERS or of `git log|show|diff|grep|status` (no `--output`), or text that
  writes nothing: a `git commit` or `git tag` message, `echo`, `printf` without `-v`, a here-document into
  another file (v7.3; v7.2 refused every mention). In a call that names either, a redirection, an operand
  behind `xargs` or a word this cannot read that may be the stamp is refused, and so is a code runner fed its
  code on stdin. So is a pattern that expands to the script, run by an interpreter (`$'...'` decoded first; the
  stamp is named by its commit, so a pattern cannot create HEAD's); and `make` with `-i`, `-o`, `-W`,
  `-t`, `-e`, `--eval` or their long forms in any abbreviation, or `MAKEFLAGS` or `MAKELEVEL` assigned,
  which run a target whose prerequisites failed or never ran, or pass a script off as make.

This project's own rules (model_ranking: its M21 guard, carried over in the DevFlow v7.1 upgrade by D-199
clause 3 and the owner's patches of #281, and ported onto DevFlow v7.1.2's file by D-205 clause 3):
- `fly` or `flyctl` but the read-only subcommands in READ_ONLY_FLY, and `fly` behind `xargs` (D-185),
  whatever the deploy gate says: the hosted engine is deployed and destroyed by the owner only;
- `deploy_hosted_engine.sh` run with anything but exactly `--dry-run` (D-185);
- git's own configuration and hooks (#285): `git config --edit`, `--ed...`, `-e` (alone or in a cluster) and
  `edit`; and a write, by the redirections and programs of the owner's-directory rule below, into a `.git`
  directory's `config`, `config.worktree` or `hooks/` (any case, as written and as resolved), the same files of
  the git directory of a work tree this call knows, `~/.gitconfig`, or `$XDG_CONFIG_HOME/git/config`
  (`~/.config/git/config`). `core.hooksPath` set by `git config` stays refused as above. Since #320 also its
  `info/` (`exclude` hides work from `git status`), `commondir` (a worktree's too), and the same files of a
  submodule's git directory, `modules/<name>/`; and a template directory, whose hooks and config `git init` and `git
  clone` copy in: `--template` (any prefix git reads), `init.templateDir` set by `git config` or `-c`, or named in
  `GIT_CONFIG_*`, and `GIT_TEMPLATE_DIR` assigned or bound anywhere;
- the default branch the deploy gate reads its base from (#318: `brief_fields.DEFAULT_BRANCHES`, origin/HEAD,
  origin/main, origin/master, main, master), and since #533 (D-236) every ref under `refs/remotes/origin/`: these
  move only by a plain `git fetch origin` or `git pull` of origin. Refused: `git branch` forcing, creating, moving
  onto or copying onto `main`, `master`, `trunk` or a remote's of those or its `HEAD` (`git branch -f main HEAD`);
  deleting or renaming one (`-d`, `-D`, `-m`, `-M`; with `-r`, any `origin/<x>`), and a lone `-m <new>`, which
  renames the current branch (deleted, then made again by `git worktree add -b main <dir> <old sha>`, the gate's
  base moved; #533); `git checkout -b/-B`, `git switch -c/-C`/`--create`/`--force-create` and `git worktree add
  -b/-B` making one, the value apart or attached (`-Bmain`), the long options in any prefix git reads, and `git
  worktree add <dir>` alone, which makes a branch named after the directory's last part; `git update-ref` naming
  one or a ref under `refs/remotes/origin/`, or reading its refs from `--stdin`; `git symbolic-ref` writing or
  deleting one; a `fetch` or `pull` refspec, or a `--refmap`, whose destination may land on one (`git fetch .
  HEAD:main`), a pattern read as every ref it may name (`refs/*:refs/*`, `*:*`); and each of these but a branch
  only made (`-b`, `-c`, plain `git branch`) naming its ref through an expansion this cannot read (`git branch -D
  "$b"`); `git remote` changing `origin` in any case or adding one named `origin/<x>` (`set-url`, `add`, `rename`,
  `remove`, `set-branches`), adding a `--mirror`, or changing any remote's `HEAD` but by `set-head --auto`; any
  remote's `url` or `fetch` (`remote.evil.fetch=+refs/heads/x:refs/remotes/origin/main`, #533), or
  `url.<base>.insteadOf` (which rewrites origin's URL), set by `git config`, `-c`, `--config-env` or
  `GIT_CONFIG_*`, and a `remote.` section renamed by `git config`; `git push` to one of this repository's (`git
  push . HEAD:refs/remotes/origin/main`); `git replace` but its listing, which moves every merge-base with one;
  and a write into `.git/refs/heads/<one>`, `.git/refs/remotes/`, `.git/refs/replace/`, `.git/packed-refs` or
  `.git/shallow`;
- a version tag or a replace ref (#410, D-223 clause 5), the owner's: `git tag` making, forcing or deleting a
  `v*` tag, or one named through an expansion this cannot read, but listing (`-l`, `-n`, `--contains` and the
  other filters) and `-v` -- an option's value is not read as one of them (#529, D-236: `git tag -m -l v1.0` makes
  `v1.0`); `git update-ref` naming a ref under `refs/tags/v` or `refs/replace/`; and a `fetch`, `pull` or `push`
  refspec whose destination may land under `refs/replace/` (`git push origin 'refs/replace/*'`, `git fetch origin
  'refs/*:refs/*'`, #529);
- a worktree with uncommitted work (#286): `rm -r`, `find -delete` and `git worktree remove` (forced or not) of a
  `.claude/worktrees/<name>`, a path inside one, or a path holding one in a nested `.claude/worktrees/`, and
  `git worktree remove` of any live worktree, named by its path or by the last part of it that git matches, while
  `git status --porcelain` there prints anything or cannot be measured within STATUS_S seconds in all. Live is a
  `.git` directory, or a `.git` file whose `gitdir:` names an existing directory; one whose `gitdir:` names
  nothing is no live worktree and is removed as before. Since #317, the same worktree's `.git` file is not removed,
  moved or rewritten by the programs of the owner's-directory rule, `sed -i` and `perl -i` included (`rm <wt>/.git` made it a plain directory for
  the next call), the worktree is not moved by `git worktree move` (to the temp directory, then removed), and an
  untracked `.gitignore` that ignores itself (`echo '*' > <wt>/notes/.gitignore`) counts as uncommitted work;
- a write into the `.claude/` or `.githooks/` of any git work tree, the owner's hooks and settings (the M21
  closure security seat's S3): a redirection there (`>`, `>>`, `>|`, `&>`, `<>`, `>& file`); `rm`, `mv`,
  `tee`, `touch`, `chmod` and their kind on a path there; `cp`, `ln`, `install`, `rsync`, `ditto` or `dd`
  with a destination there (the last word, or `-t`/`--target-directory` for `cp`, `mv`, `ln` and `install`,
  or `of=` for `dd`); `sed -i` or `perl -i` on one; `find ... -delete` starting there; and `git rm`, `git
  mv`, `git checkout` or `git restore` naming one. Reading them is not refused. The one exception is the
  scratch rule's: `rm` of a directory under `.claude/worktrees/<name>` (a worktree's own `.claude/` and
  `.githooks/` stay refused). `git init`, `git clone`, `git submodule add` and `git worktree add` (and
  `--separate-git-dir`) making their directory there are refused as a write is (#256), but `git worktree add`
  under `.claude/worktrees/<name>`; so is any git command given `--git-dir` or `--work-tree` there, or run with
  `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` or `GIT_INDEX_FILE` assigned there.
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
  existing part. A work tree it lies in is a directory above it that holds a `.git` entry, a file or a
  directory: this clone, a linked worktree, any other clone, or a worktree Claude Code made inside a
  repository's `.claude/worktrees/`. The path is refused when, for any of them, nearest first, the directory
  directly below that work tree's root is named `.claude` or `.githooks`, in any case -- every one, not only the
  nearest (#256: after `git init .claude`, `.claude` was the nearest work tree, and its files passed). The walk ends,
  allowed, at a path inside `<root>/.claude/worktrees/<name>` whose `<name>` holds a `.git`: that worktree was
  asked as its own work tree first. Claude Code's own `~/.claude` is not refused, as no `.git` sits above it. From a place WHERE cannot name, the path is resolved from every directory a
  `cd`, `chdir` or `pushd` anywhere in the call reaches, from every one reached before it, variables
  expanded as this process holds them (FOLLOWED); past MAX_FOLLOWED of them the call is not read.
  Given `--write`, the guard judges the Write or Edit call's `file_path` instead: a secrets file by name
  (the shell rule's names), the gate stamp by name (`devflow-gate…`, in any case: v7.2's editor-hook rule,
  held here because this project's editor hook is this guard), or a path `protected` refuses.
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
program); inside `bash`, `sh`, `zsh`, `dash`, `ksh`, `csh`, `tcsh` or `fish` given `-c` (fish's `-c` and `-C`
in every spelling its getopt reads: glued, `=`, a long prefix -- v7.3, #54), a script name, a
here-document or a here-string; and inside `eval`, `source`, `.`, `env -S`, `find -exec`, a `trap`'s
command, a shell `alias`'s value and `mapfile -C`'s callback. Text in
single quotes and a quoted here-document's body are data; a `#` that starts a word starts a comment. A
program named through a variable assigned a literal earlier in the same text (`a=git; $a push`) is read
as that program; unquoted, a value with blanks is split into words (`x='rm -rf ~'; $x`), and `eval`'s and
`-c`'s text is read with those literals in (v7.3, #68).

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
any call it has not finished judging within its time budget, DEADLINE_S seconds (a timer thread writes
BUDGET, which says to split the command, and exits 2). A long call into C that holds the interpreter runs to
its end first; the hook's own `timeout` and `"onFailure": "block"` bound that case, from Claude Code 2.1.295
(an older one ignores the key and loads the file: measured on 2.1.294). Codex documents no such key.

Not held, by class -- said here so nobody believes otherwise:
- a program named when the command runs: a variable or an alias set outside this text, a function, `hash`,
  a `PATH` holding a script of a guarded name; `xargs <deploy command>` whose subcommand comes on stdin;
- code another program runs: a script's contents (`bash x.sh`), `python -c`, `perl -e`, `node -e`,
  `awk`'s `system()`, `make` recipes, git hooks, an alias set before this call or in a config file this
  does not open, ssh options from `~/.ssh/config`, `scp`, `rsync -e`;
- a `core.hooksPath`, an alias or a pager read from a file this does not open: `GIT_CONFIG_GLOBAL`,
  `GIT_CONFIG_SYSTEM`, `XDG_CONFIG_HOME` or `HOME` set for a `git` command, `/etc/gitconfig`, a config file
  written by a program this does not list (`git apply`, `python -c`) or through a path built when the command
  runs (#285);
- a worktree's commits that no branch outside it holds, and its ignored files, which `git status --porcelain`
  does not list (#286);
- a wrapper not in WRAPPERS, whose program is then read as an argument;
- a directory changed by what this does not read: a sourced script's `cd`, zsh's `AUTO_CD`, a `CDPATH`
  the shell's startup files set and this process does not see;
- a push to a destination git chooses itself: a bare `git push`, `git push origin HEAD` or `@`, an
  upstream, `push.default`, or a variable set elsewhere naming the ref of a push that does not delete
  (`git push origin "$branch"`; branch protection on the remote is the control there); a default branch
  other than the call's repository's (a push after `cd` into another one), or set in a reftable `origin/HEAD`;
- a remote's tags: a `v*` tag pushed or fetched by name or in bulk (`git push origin v1`, `--tags`,
  `--follow-tags`, `git fetch --tags`), and a tag file written under `.git/refs/tags/` (#410 holds the local
  `git tag` and `update-ref` only);
- the owner's machine changed by a program this does not list: `launchctl` (`bootstrap`, `bootout`, `load`),
  a write under `~/Library/LaunchAgents`, a script that runs one, or a copy of a guarded script under
  another name (#471; the launchd deploy and its rules retired with #427, #461 and #470);
- a rerun gh misreports (`gh` is read from PATH), or a declared deploy with options a rerun does not carry;
- what the shell expands when the command runs, beyond the program word and git's words: `IFS`, history,
  globs and braces in arguments; syntax beyond POSIX-like shell; a name bound by `read`, `for`, `printf -v`,
  `getopts` or a wrapper's assignment, which is unknown to the scratch rule only (#344 left them read as unset);
- an `mv` or `git rm -r` of the repository through a variable set outside this text or a pattern
  (`mv "$REPO" /x`, `mv * ..`, `git rm -r ':/*'`); a link that existed before this call is followed where
  it resolves, but one another program makes in this call (`python -c`, `tar`, `unzip`, a clone that holds
  a link) is not seen;
- the gate stamp, like the pre-push hook it serves (which the editor tool can rewrite), against an agent
  set on evading it: its name built at run time, or written by code another program runs (a script's own
  code, a `make` recipe); a commit made while `make gate`
  runs (the stamp names the HEAD at its end); a work tree git is told not to see (`update-index
  --skip-worktree`, a `.git/info/exclude` a program this does not list writes), which pre-push graded no better
  before the stamp; CI still runs every gate leg;
- the deploy gate's base moved where this does not look (#318, #533): a commit, merge, reset or rebase made while
  the default branch is checked out, a ref written by a program this does not list, a remote other than `origin`
  renamed to it by a program this does not list, a fetch of origin itself from a URL a program this does not list
  rewrote, or a remote's settings in a config file this does not open; ignore rules from
  `core.excludesFile` that hide a worktree's work (#317); a clone moved by `mv` and then removed;
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
#: The guard's time budget for one call. A call is judged in milliseconds; past the budget it is refused with
#: BUDGET -- inside the hook's own `timeout`, so the refusal, not a timeout, is what the agent reads.
DEADLINE_S = 10.0
BUDGET = ("BLOCKED: this guard did not finish judging the command within its {s:g} s budget. Split it into smaller "
          "Bash calls; if one short command keeps hitting this, the machine or the deploy gate is slow -- tell the owner.")
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
SEEN: dict[str, bool] = {"repeats": False, "cdpath": False, "links": False, "home": False, "home_used": False,
                         "stamp": False}
#: A3: the `for NAME in WORDS` loops over literal words this text holds, in the order it meets them: how many words
#: each has, and the word each gives NAME in this pass. A text holding them is judged once per combination, up to
#: MAX_PASSES; past that once more with every such NAME unknown, as before v7.3.
FORS: dict[str, object] = {"sizes": [], "pick": (), "unknown": False}
MAX_PASSES = 64
#: Set while the command being judged may not run, or runs apart from what follows (`&&`, `||`, a
#: branch, a loop, a subshell, a substitution, a pipe): an assignment there may or may not hold after it.
#: `scoped` is the same question asked by where the command sits (#287): in a subshell, a substitution, a pipeline
#: stage, behind `&`, after `||`, after an `&&` some later command does not wait on, in a branch's or a loop's body
#: (by its keywords), or anywhere after a function is defined (whose body's end this does not mark).
FLOW: dict[str, bool] = {"maybe": False, "scoped": False}
#: #287, as the security review of run bug-night's bundle (B1) left it: the call is judged in two worlds, and refused
#: when either refuses. In the first (`skip` False) every assignment that may not happen or may not last -- one where
#: it stands (`scoped`), one before a program (`NAME=v cmd`), one made by a child process or a deferred text
#: (`_apart`) -- happens and holds; in the second none of them does, and each name keeps the value it had. Each world
#: is a run the shell may make, so a value that MAY be set is judged as each value it may take, and no refusal
#: reads a name as unknown -- and so as harmless -- because it may have two. `forked` says whether the second world
#: differs from the first.
WORLD: dict[str, bool] = {"skip": False, "forked": False}
#: Above zero while the text judged is run by `eval` or `source` in this shell, whose commands after it this text
#: does not hold: an assignment after `&&` there may not happen, and what follows the `eval` runs anyway (#287).
EVALED: dict[str, int] = {"on": 0}
#: The words that open and close a branch's or a loop's body, read at the head of each command (#287).
OPENS = {"if", "while", "until", "for", "select", "case", "foreach", "repeat"}
CLOSES = {"fi", "done", "esac", "end"}
#: More places than this (each `;`-joined `cd` may fail and stay), and they become one this cannot name.
MAX_PLACES = 64
#: `name -> literal value` for assignments seen in this text, or SCRATCH for a `mktemp` result.
SCOPE: dict[str, object] = {}
SCRATCH = object()
#: #344: a value this cannot read and that may be anything -- a command substitution's output, an array, a
#: positional parameter, a `${...}` form, a pattern -- so every refusal that reads a value takes it as possibly
#: protected: a write to it, a git word of it, a program named by it is refused (`_unread_word`). (UNKNOWN, which a
#: binder such as `read` or `for` leaves, is unknown only to the scratch rule: "Not held".)
UNREAD = object()
#: #344: what in a word is an expansion this cannot read: a positional parameter, a `${...}` that is not a plain
#: `${name}`, a command substitution (the lexer writes each as `$(...)`), a backtick.
UNREAD_FORM = re.compile(r"\$(?:[0-9@*]|\{(?![A-Za-z_][A-Za-z0-9_]*\})|\(\.\.\.\))|`")
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
#: GNU env's long options (prefixes resolve to them, #47) and those that take the next word as their value.
ENV_LONG = ("argv0", "block-signal", "chdir", "debug", "default-signal", "help", "ignore-environment",
            "ignore-signal", "list-signal-handling", "null", "split-string", "unset", "version")
ENV_VALUED = {"argv0", "chdir", "split-string", "unset"}
PROTECTED = {"main", "master", "trunk"}
#: A8: the default branch of the call's repository -- its `origin/HEAD`, else `init.defaultBranch` -- is protected
#: beside PROTECTED, never instead of it. One lookup per git directory for the life of this process.
DEFAULTS: dict[str, str | None] = {}
#: fish's options as its getopt reads them (`fish_parse_opt`): a long one in any unique prefix, True when it takes
#: a value; the short ones that take a value glued or as the next word. `-c` and `-C` carry shell text.
FISH_LONG = {"command": True, "init-command": True, "features": True, "debug": True, "debug-output": True,
             "debug-stack-frames": True, "profile": True, "profile-startup": True, "interactive": False,
             "login": False, "no-config": False, "no-execute": False, "print-rusage-self": False,
             "print-debug-categories": False, "private": False, "help": False, "version": False}
FISH_VALUED = set("cCdfDop")
#: A2: in a call that names the gate stamp, the only commands that may name it: programs that read their
#: operands, `git`'s reading subcommands (no `--output`), and text that writes nothing (`_stamp_ok`).
STAMP_READERS = {"grep", "egrep", "fgrep", "rg", "cat", "head", "tail", "ls", "wc", "stat", "test", "[", "[["}
GIT_READS = {"log", "show", "diff", "grep", "status"}
#: Programs that run code from their words or stdin: one fed code there, in a call naming the stamp, may write it.
CODE_RUNNERS = re.compile(r"^(python[0-9.]*|py|pypy[0-9.]*|perl[0-9.]*|ruby[0-9.]*|node|nodejs|deno|bun|php[0-9.]*|"
                          r"lua[0-9.]*|luajit|rscript|osascript|[gmn]?awk|tclsh[0-9.]*|pwsh|powershell)$", re.I)
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
#: How long, in all, one call may spend asking git about worktrees it would remove (#286): `git status
#: --porcelain` in each, `git worktree list` for `git worktree remove`. Past it, a live worktree is not removed.
STATUS_S = 5.0
STATUS: dict[str, float] = {"left": STATUS_S}
#: Past this many `.claude/worktrees/<name>` directories at or below one removed path, it is not removed (#286).
MAX_WORKTREES = 64
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
#: #320: what names a git template directory, whose hooks and config `git init` and `git clone` copy in.
TEMPLATE_ENV = "GIT_TEMPLATE_DIR"
#: #256: the environment variables that place git's directories, as `--git-dir` and `--work-tree` do.
GIT_PLACE_ENV = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_INDEX_FILE"}
TEMPLATE_KEY = "init.templatedir"
#: #318: the remote's settings that decide what `origin/main` and `origin/HEAD` hold after the next fetch, and
#: `url.<base>.insteadOf`, which rewrites origin's URL with `remote.origin.url` untouched. Since #533 (D-236) any
#: remote's: `git -c remote.evil.fetch=+refs/heads/stale:refs/remotes/origin/main fetch evil` moved `origin/main`.
REMOTE_KEY = re.compile(r"^(remote\..+\.(url|fetch)|url\..+\.insteadof)$", re.I)
#: The same keys inside a `GIT_CONFIG_*` value.
REMOTE_KEY_IN = re.compile(r"remote\..+\.(url|fetch)\b|url\..+\.insteadof", re.I)
#: `git branch`, `git fetch` and `git symbolic-ref` options that take the next word as their value.
BRANCH_VALUED = {"-u", "--set-upstream-to", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at",
                 "--format", "--sort"}
FETCH_VALUED = {"--depth", "--deepen", "--shallow-since", "--shallow-exclude", "--upload-pack", "-j", "--jobs",
                "--negotiation-tip", "-o", "--server-option", "--filter", "--refmap"}
#: `git init`, `git clone`, `git submodule add` and `git worktree add` options that take the next word as their value
#: (#256).
MADE_VALUED = {"--template", "--separate-git-dir", "--object-format", "--ref-format", "-b", "--initial-branch",
               "--branch", "-o", "--origin", "-u", "--upload-pack", "--reference", "--reference-if-able", "--depth",
               "--shallow-since", "--shallow-exclude", "-c", "--config", "--server-option", "-j", "--jobs", "--filter",
               "--bundle-uri", "-B", "--reason", "--name"}
#: #344: the git subcommands whose words, unread, may be `--no-verify`, `--force`, `--hard`, the protected branch or
#: an owner's path; and the options whose value is a message or a name, which may hold any text.
GIT_UNREAD_SUBS = {"push", "commit", "merge", "rebase", "cherry-pick", "revert", "pull", "am", "reset", "clean",
                   "checkout", "switch", "restore", "stash", "config", "branch", "update-ref", "symbolic-ref",
                   "worktree", "fetch", "remote", "replace", "init", "clone", "rm", "mv", "submodule"}
GIT_MESSAGE = {"-m", "--message", "-F", "--file", "--author", "--date", "--trailer", "-o", "--push-option",
               "--reason"}
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
CONFIG_EDIT = ("BLOCKED: `git config --edit` (`-e`, `edit`) opens a config file in an editor, where `core.hooksPath`, "
               "an alias or a pager can be set where this guard does not read it (#285). Set the key with "
               "`git config <key> <value>`, which this guard reads.")
GIT_FILE_WRITE = ("BLOCKED: `{path}` is git's own configuration, hooks or default-branch refs (`.git/config`, "
                  "`.git/hooks/`, `.git/info/`, `.git/modules/<name>/`, `.git/refs/heads/main`, `~/.gitconfig`): a "
                  "write there can set `core.hooksPath`, an alias or a pager, replace a hook, hide work from `git "
                  "status`, or move the deploy gate's base, where this guard does not read it (#285, #318, #320). Set "
                  "a key with `git config <key> <value>`; the hooks are the owner's (`make hooks`).")
UNREAD_WRITE = ("BLOCKED: `{path}` is built from a value this guard cannot read (a command substitution, an array, a "
                "positional parameter, a `${{...}}` form), so it may be the owner's `.claude/` or `.githooks/`, git's "
                "config or a secrets file (#344). Write the value out, or assign it from a literal first (or use `mktemp`).")
UNREAD_GIT = ("BLOCKED: `git {sub}` is given `{word}`, a value this guard cannot read (a command substitution, an array, "
              "a positional parameter, a `${{...}}` form), not read: it may be `--no-verify`, `--force`, `--hard`, the protected "
              "branch or the owner's files (#344). Write the value out, or assign it from a literal first; a message "
              "(`-m`, `-F`) may hold one.")
ENV_UNREAD = ("BLOCKED: `{word}` is an `env` option this guard cannot read (#400), so the command it may carry "
              "(`-S`) cannot be judged. Write env's options apart: `env -i -S '...'`, or the command itself.")
ENV_S_UNREAD = ("BLOCKED: `env -S` splits `{text}` by its own rules (`\\_`, a tab, a VT, an FF, a CR or a newline "
                "separate words; `${{NAME}}` expands), which this guard does not read (#400). Write the command out "
                "without `env -S`, or with plain spaces and no backslash or `$` in its string.")
UNREAD_PROGRAM = ("BLOCKED: `{word}` names its program through a value this guard cannot read (a command substitution, "
                  "an array, a positional parameter, a `${{...}}` form), which may be `fly` or a deploy (#344). Write "
                  "the value out, or assign it from a literal first.")
TEMPLATE = ("BLOCKED: a git template directory (`--template`, `init.templateDir`, `GIT_TEMPLATE_DIR`) copies its hooks "
            "and config into the repository `git init` or `git clone` makes or re-initialises, from a place this guard "
            "does not read (#320). Run the command without one.")
DIRTY_WORKTREE = ("BLOCKED: `{path}` removes the worktree `{root}`, which holds uncommitted work (`git status "
                  "--porcelain` lists it), and that work would be lost (#286). Commit it there, or ask the owner.")
UNMEASURED_WORKTREE = ("BLOCKED: `{path}` removes `{root}`, a live worktree whose `git status` this guard could not "
                       "measure ({why}), so it may hold uncommitted work (#286). Check it with `git -C <it> status` "
                       "and ask the owner.")
PROTECTED_PUSH = ("BLOCKED: the agent never pushes the protected branch (AGENTS.md S3). Push YOUR branch and open a "
                  "draft PR; a human marks it ready and merges.")
NO_VERIFY = ("BLOCKED: `--no-verify` and a redirected `core.hooksPath` skip the gate a hook runs (AGENTS.md S3): "
             "a hook you skipped is a gate you removed. Fix what is red, or ask the owner.")
HUSKY_OFF = ("BLOCKED: `HUSKY=0` (or husky 4's `HUSKY_SKIP_HOOKS`) on a push skips every hook husky runs, the "
             "pre-push gate among them; refused, as `--no-verify` is (AGENTS.md S3). Push without it: a hook you "
             "skipped is a gate you removed.")
UNREAD_DELETE = ("BLOCKED: this push deletes `{ref}`, a name this guard cannot read, and it may be the protected "
                 "branch (AGENTS.md S3). Write the branch name, or assign it a literal earlier in the command.")
ENV_WRITE = "BLOCKED: writes to .env are denied per permission-matrix.md S6 (default-deny secrets)."
#: v7.2's Write/Edit hook message, word for word: the stamp's name, in any case, is never an editor's to write.
STAMP_WRITE = ("BLOCKED: the gate stamp (devflow-gate-ok) is written only by make gate when it passes -- a stamp "
               "written by hand is a gate that never ran.")
PROTECTED_REF = ("BLOCKED: the agent never moves or deletes the protected branch's ref, nor `origin/HEAD`, a ref "
                 "under `origin/` or a remote's default branch, where the deploy gate reads its base (AGENTS.md S3, "
                 "#318, #533): only a plain `git fetch origin` or `git pull` of origin moves them, and the default "
                 "branch is the human's.")
OWNER_REF = ("BLOCKED: a `v*` tag names a release, and a `refs/replace/` ref moves every merge-base the deploy "
             "gate measures from; the owner makes, moves and deletes both, in their own terminal (#410, D-223 "
             "clause 5). Listing them (`git tag -l`, `git replace -l`) is allowed.")
ENV_EXEMPT = {".env.example", ".env.sample", ".env.template"}
GH_MERGE = ("BLOCKED: a human marks a pull request ready and merges it, never the agent (AGENTS.md S3). "
            "Leave the draft for the owner.")
GH_PROTECTION = "BLOCKED: branch protection and rulesets are the owner settings (AGENTS.md S3). Propose the change and stop."
NOT_JSON = "BLOCKED: this guard cannot read the tool call -- the payload is not a JSON object."
GATE_MISSING = ("BLOCKED: deploy gate -- {root} declares deploy commands in docs/project-brief.md and {own} has no "
                "scripts/deploy_gate.py, so no command can be told from a deploy. Restore the script "
                "(INSTALL-MANIFEST.md); the guard never skips this check.")
CONFLICT_MARKER = re.compile(r"^(<{7}|>{7})(?: |$)|^={7}$", re.M)
GATE_CONFLICT = ("BLOCKED: deploy gate -- scripts/{name} holds an unresolved merge conflict (line {line}), so no "
                 "command can be judged. Resolve it with the Edit tool -- no Bash call runs until it is resolved -- "
                 "and resolve this file before any other an upgrade conflicted.")
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
GATE_STAMP = ("BLOCKED: the gate stamp (`devflow-gate-ok`, `scripts/gate_stamp.py`) is written only by `make gate` "
              "when it passes -- pre-push and /pre-merge trust it, so a stamp written any other way is a gate that "
              "never ran. Run `make gate`; `make gate-ok` reads it.")
MAKE_FLAGS = ("BLOCKED: `make` with `-i`, `-o`, `-W` or `-t` (or `MAKEFLAGS` set) runs a target whose prerequisites "
              "failed or never ran -- `make gate` would pass, and stamp, a tree it did not grade. Run the target "
              "plainly.")
MAKE_LEVEL = ("BLOCKED: `MAKELEVEL` is set by make for its recipes: assigning it passes a script off as one, "
              "and the gate stamp is written only from inside a plain `make gate`.")
#: `make` options that let a target's recipe run, or count as done, while its prerequisites failed or never ran.
MAKE_UNSAFE_LONG = ("--ignore-errors", "--old-file", "--assume-old", "--what-if", "--new-file", "--assume-new",
                    "--touch", "--environment-overrides", "--eval")
#: Interpreters that would run the stamp's script.
INTERPRETERS = re.compile(r"^(python[0-9.]*|py|pypy[0-9.]*)$")



def _stamp_pattern(text: str, names: tuple[str, ...] = ("gate_stamp.py", "devflow-gate-ok")) -> bool:
    """A word -- a literal, or a pattern the shell expands (`gat*.py`, `.git/dev*`, `gate_s{t,}amp.py`) --
    whose last path component may name the gate stamp or its script."""
    last = re.sub(r"\{[^}]*\}", "*", text.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower())
    return any(fnmatch.fnmatchcase(name, last) for name in names) if last else False


def _stamp_named(text: str) -> bool:
    """Whether text names the gate stamp or its script as the call's flat reading does: lower-cased, with quotes,
    backslashes and `$` removed."""
    flat = re.sub(r"[\"'\\$]", "", text).lower()
    return "devflow-gate" in flat or "gate_stamp" in flat


def _stamp_target(word: "Word") -> bool:
    """A2: whether a file a command writes may be the gate stamp or its script -- its last path component names
    one (this text's literals in), or, in a call that names the stamp, holds an expansion this cannot read that
    may make it one (`"$a"`, `x-$n`; not `${slug}.md`, nor a `mktemp` result)."""
    last = _expand(word.text).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if _stamp_named(last):
        return True
    m = VARIABLE.fullmatch(last)
    if not SEEN["stamp"] or not ("$" in last or "{}" in last or not last) or (m and _variable(_name(m)) is SCRATCH):
        return False
    pattern = re.sub(r"\$\{[^}]*\}|\$\(\.\.\.\)|\$[A-Za-z_][A-Za-z0-9_]*|\$.?|\{\}", "*", last).lower() or "*"
    return any(fnmatch.fnmatchcase(n, pattern) for n in ("devflow-gate-ok-" + "0" * 40, "gate_stamp.py"))


def _stamp_ok(cmd: "Command") -> bool:
    """A2, in a call that names the gate stamp: whether this command only reads it. Every mention must be a read
    -- an operand, not an option, of a program in STAMP_READERS or of a `git` subcommand in GIT_READS without
    `--output` -- or text that writes nothing: `git commit` and `git tag`, `echo`, `printf` without `-v`, a
    here-document fed to one of them. Any other command that names it, or takes its operands from where this
    cannot read (`xargs`, an expansion, a code runner's stdin), may write it, as v7.2 read every one."""
    words = cmd.words
    named = [k for k, w in enumerate(words) if _stamp_named(_expand(w.text))]
    fed = any(_stamp_named(t) for t in cmd.fed)
    i, xargs = 0, False
    while i < len(words) and (ASSIGNMENT.match(words[i].text) or words[i].text in KEYWORDS - {"[", "[["}):
        i += 1
    while i < len(words) and _program(words[i]) in WRAPPERS:
        xargs = xargs or _program(words[i]) == "xargs"
        i += 1
        while i < len(words) and (words[i].text.startswith("-") or ASSIGNMENT.match(words[i].text)):
            i += 1
    if i >= len(words) or any(k < i for k in named):   # an assignment, or a wrapper's own word, names it
        return not (named or fed)
    program, rest = _program(words[i]), words[i + 1:]
    options = [w for w in rest if w.text.startswith("-")]
    if program == "git":
        k = 0
        while k < len(rest) and rest[k].text.startswith("-"):
            k += 2 if rest[k].text in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env") else 1
        sub = rest[k].text if k < len(rest) else ""
        reads = sub in ("commit", "tag") or (sub in GIT_READS and not any(
            w.text.startswith("--outp") or _stamp_named(_expand(w.text)) for w in options))
    else:
        reads = (program == "echo" or (program == "printf" and not any(w.text.startswith("-v") for w in options))
                 or (program in STAMP_READERS and not any(_stamp_named(_expand(w.text)) for w in options)))
    return reads or not (named or fed or xargs or any(_stamp_target(w) for w in words[i:])
                         or (CODE_RUNNERS.match(program) and (cmd.piped or cmd.from_file or cmd.fed)))


def _braces(text: str, limit: int = 64) -> list[str] | None:
    """Bash's brace expansion of `text`, enough to see every path a `{a,b}` group can name (a group may hold a
    `/`: `docs/{../scripts/g*.py,x}`, which v7.2 read as one name ending in `x}`). None past `limit` names in
    all: a word built to expand that far is refused, never walked (v7.2.1, review: 2^n work otherwise)."""
    out, todo = [], [text]
    while todo:
        if len(out) + len(todo) > limit:
            return None
        t = todo.pop()
        m = re.search(r"\{([^{}]*,[^{}]*)\}", t)
        if not m:
            out.append(t)
            continue
        todo += [t[:m.start()] + alt + t[m.end():] for alt in m.group(1).split(",")]
    return out


#: Commands that put a file somewhere, or move a directory or link, before a pattern later in the same call
#: is expanded: the directory checked now is not the one the shell expands then (v7.2.1, review).
PLACES_FILES = re.compile(r"\b(cp|mv|ln|rmdir|mkdir|install|rsync|ditto|tar|unzip|cpio|pax|patch)\b"
                          r"|\bgit\s+(mv|checkout|restore|switch|worktree|stash|apply|am|cherry-pick|merge|pull)\b")
CALL = {"text": ""}


def _names_stamp_script(word: "Word") -> bool:
    if "{" in word.text:
        alternatives = _braces(word.text)
        if alternatives is None:
            return True
        if len(alternatives) > 1 or alternatives[0] != word.text:
            return any(_names_stamp_script_one(Word(t, word.glob, word.equals, word.quoted, list(word.subs)))
                       for t in alternatives)
    return _names_stamp_script_one(word)


def _names_stamp_script_one(word: "Word") -> bool:
    """Whether an interpreter's argument may be, or expand to, the stamp's script. A literal name, a pattern
    with no directory, or one whose directory this cannot read -- a variable, a substitution, `~`, a brace,
    a pattern, a directory that does not exist yet (a link made in the same call) -- keeps v7.2's refusal.
    A pattern in a plain directory that exists and holds no `gate_stamp.py` cannot expand to it:
    `tests/unit/*.py` and `conformance/*.py` were refused as the stamp's script (Project-J, v7.2)."""
    text = word.text
    if not _stamp_pattern(text, ("gate_stamp.py",)):
        return False
    last = text.replace("\\", "/").rstrip("/").rsplit("/", 1)
    if len(last) == 1 or not any(c in last[1] for c in "*?[") or "{" in text or "}" in text or word.subs:
        return True
    directory = last[0]
    if SEEN.get("links") or PLACES_FILES.search(CALL["text"]):
        return True
    if not directory or not re.fullmatch(r"[A-Za-z0-9_./-]+", directory) or any(c in directory for c in "*?["):
        return True
    for base in HERE["dirs"] or [CWD["dir"] or os.getcwd()]:
        if not isinstance(base, str):
            return True
        real = os.path.realpath(os.path.join(base, directory))
        if not os.path.isdir(real) or os.path.exists(os.path.join(real, "gate_stamp.py")):
            return True
    return False
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
    "tag": ["--annotate", "--sign", "--no-sign", "--local-user", "--force", "--delete", "--verify", "--list",
            "--sort", "--color", "--no-color", "--ignore-case", "--omit-empty", "--column", "--no-column",
            "--contains", "--no-contains", "--merged", "--no-merged", "--points-at", "--message", "--file",
            "--trailer", "--edit", "--no-edit", "--cleanup", "--create-reflog", "--format"],
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
    bare: bool = False      # it holds an expansion outside double quotes, which the shell splits into words
    expands: bool = False   # it holds an expansion at all (a `$` in single quotes is a character, not one)


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
        self.glob = self.equals = self.quoted = self.bare = self.expands = False

    def add(self, text: str, quoted: bool) -> None:
        if quoted:
            self.quoted = True
        else:
            if not self.parts and text.startswith("="):
                self.equals = True
            self.glob = self.glob or any(ch in text for ch in "*?[{")
        self.parts.append(text)

    def word(self) -> Word:
        return Word("".join(self.parts), self.glob, self.equals, self.quoted, list(self.subs), self.bare,
                    self.expands)


class Lexer:
    """One pass over the text: simple commands, substitutions inside them, here-documents after them."""

    def __init__(self, text: str, depth: int = 0, start: int = 0) -> None:
        if depth > 12:
            raise Unreadable("substitutions nested too deep")
        self.s, self.i, self.depth = text, start, depth
        self.commands: list[Command] = []
        self.pending: list[tuple[str, bool, bool, Command]] = []  # delimiter, tabs stripped, quoted, owner
        self.patterns = 0  # `case ... in` seen: a `)` may end a pattern inside `$( )`
        self.defs: list[int] = []  # #287: where each `name()` stood, as the index of the command after it

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
                fn = re.match(r"\([ \t]*\)", s[self.i:])
                if cmd.words and (last_end == self.i or fn):
                    if fn:                          # `name()`, `name ()`: a function's name is no command
                        SEEN["repeats"] = True      # and its body's `cd` runs at every call
                        self.defs.append(len(self.commands))
                        self.i += fn.end()
                        cmd = Command()
                    elif cmd.words[-1].text.endswith("="):  # `x=(a b)`: each element read as a command
                        cmd.procsub = cmd.procsub or cmd.words[-1].text == "="   # zsh's `=( )` is a file
                        self.i += 1
                        start = self.i
                        self._substitution(")")
                        # #344: an array's value is read nowhere; the assignment is marked as a substitution's.
                        w = cmd.words[-1]
                        cmd.words[-1] = Word(w.text + "$(...)", w.glob, w.equals, True,
                                             [*w.subs, "(" + self.s[start:self.i - 1] + ")"])
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
        if cmd.words or cmd.fed or cmd.writes:   # `> file` alone writes it (zsh copies stdin there): v7.3 review, B1
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
        if op in (">", ">>", "&>", "&>>") and s[self.i:self.i + 1] in ("!", "|"):
            self.i += 1   # zsh's clobbering `>!`, `>>!`, `&>|`, `&>!`: still a write (v7.3 review, B2)
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
            return
        # every other `$` that reaches here starts an expansion; a lone `$` (no name after it) is undone below
        expanded, b.expands = b.expands, True
        if s.startswith("$((", self.i) and (end := self._arith_end(self.i + 3)):
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
            b.bare = b.bare or not in_double
            self.i = end + 1
        else:
            name = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*|[0-9@*#?$!-])", s[self.i:])
            b.add(name.group(0) if name else "$", True)
            b.bare = b.bare or (not in_double and name is not None)
            b.expands = expanded or name is not None
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
        b.expands = True
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
    # #287: whether each command sits in a branch's or a loop's body, or after a function is defined.
    inside: list[bool] = []
    body, defined = 0, min(lexer.defs, default=len(commands))
    for n, c in enumerate(commands):
        k = next((j for j, w in enumerate(c.words) if w.text not in KEYWORDS), len(c.words))
        lead = [w.text for w in c.words[:k + 1] if not w.quoted]
        body += sum(w in OPENS for w in lead)
        defined = min(defined, n) if "function" in lead or any(
            w.text.startswith(("functions[", "aliases[")) for w in c.words[:k + 1]) else defined
        inside.append(body > 0 or n >= defined)
        body = max(0, body - sum(w in CLOSES for w in lead))
        if any(w.text.startswith("functions[") for w in c.words[:k + 1]):
            SEEN["repeats"] = True   # zsh's `functions[cd]=...` defines `cd`, as `cd() {...}` does
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
        outer, outer_scoped = FLOW["maybe"], FLOW["scoped"]
        FLOW["maybe"] = outer or bool(compound or SEEN["repeats"] or cmd.inner or cmd.subshell or cmd.piped
                                      or (not cmd.inner and cmd.joined in ("&&", "||"))
                                      or (nxt is not None and nxt.joined in ("&", "|", "|&")))
        # `a && X=...; rm "$X"/y` runs `rm` when `a` fails; `a && X=... && rm "$X"` does not.
        unwaited = cmd.joined == "&&" and (EVALED["on"] > 0 or any(commands[j].joined not in ("&&", "|", "|&")
                                                                   for j in top if j > k))
        FLOW["scoped"] = outer_scoped or bool(inside[k] or cmd.inner or cmd.subshell or cmd.piped
                                              or (not cmd.inner and (cmd.joined == "||" or unwaited))
                                              or (nxt is not None and nxt.joined in ("&", "|", "|&")))
        try:
            why = judge_command(cmd, depth)
        finally:
            FLOW["maybe"], FLOW["scoped"] = outer, outer_scoped
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


def _apart(text: str, depth: int) -> str | None:
    """#287: text run by another process (`bash -c`, a shell's here-document, a git alias, a pager, ssh's local
    commands) or at another time (a `trap`, an `alias`, `mapfile -C`'s callback), judged as a command. What it
    assigns holds inside it; after it, it holds in the first world (WORLD) and is undone in the second: the shell
    running this text never takes it, or takes it later."""
    before = dict(SCOPE)
    try:
        return judge_text(text, depth)
    finally:
        if SCOPE != before:
            WORLD["forked"] = True
            if WORLD["skip"]:
                SCOPE.clear()
                SCOPE.update(before)


def _evaled(text: str, depth: int) -> str | None:
    """Text `eval` or `source` runs in this shell: its assignments hold after it, as the rest of this text's do,
    but one after `&&` may not happen while what follows the `eval` runs anyway (`eval 'false && X=...'; rm "$X"/y`)."""
    EVALED["on"] += 1
    try:
        return judge_text(text, depth)
    finally:
        EVALED["on"] -= 1


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
    new = _value(word, value)
    # An assignment that may not happen, or happens apart from what follows (`false && d=$(mktemp -d)`, `(d=...)`),
    # leaves the name what it was -- this text's value, the environment's, or unset (`"$d"/Users/x` is `/Users/x`) --
    # or gives it the new one: each is judged, in its world (WORLD, #287). Made unknown instead, as once, a literal
    # `.claude` or `main` read as harmless to every refusal that reads a name's value (the review's B1).
    if FLOW["scoped"]:
        WORLD["forked"] = True
        if WORLD["skip"]:
            return
    SCOPE[name] = new


def _value(word: Word, value: str) -> object:
    """What an assignment's value is: SCRATCH for a lone `mktemp` (only the whole value: `$(mktemp -d; echo /x)`
    prints a second path, and `$(mktemp -d)/../x` leaves the directory), the literal, or UNKNOWN for what this cannot
    read, which shadows the environment's value."""
    if value == "$(...)" and len(word.subs) == 1 and _mktemp_only(word.subs[0]) and TRUST["mktemp"]:
        return SCRATCH
    # #344: a substitution's output, an array, a positional parameter, a `${...}` form or a pattern may be anything.
    if word.subs or word.glob or _unread_text(value):
        return UNREAD
    if "$" not in value or not word.expands:   # `x='rm -rf $HOME'` is literal: its `$` is a character (#68, v7.3)
        return value
    names = [_name(m) for m in VARIABLE.finditer(value)]
    if any(SCOPE.get(n) is UNREAD for n in names):
        return UNREAD
    if any(n in SCOPE and not isinstance(SCOPE[n], str) for n in names):
        return UNKNOWN
    # This text's literals put in; a name it never set is the environment's, read where the value is used
    # (`d=$HOME/notes`), and keeps the value no scratch.
    return _expand(value)


def _unread_text(text: str) -> bool:
    """#344: whether text holds an expansion this cannot read (UNREAD_FORM), or names a variable this text gave such
    a value."""
    return bool(UNREAD_FORM.search(text)) or any(SCOPE.get(_name(m)) is UNREAD for m in VARIABLE.finditer(text))


def _unread_word(word: Word) -> bool:
    """#344: whether a word may be anything: it holds a substitution other than a lone `mktemp`, or an expansion
    `_unread_text` cannot read."""
    if any(not (_mktemp_only(sub) and TRUST["mktemp"]) for sub in word.subs):
        return True
    return _unread_text(word.text.replace("$(...)", ""))


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
        if program == "for" and (value := _for_value(rest)) is not None:
            _bound(names[0])
            SCOPE[names[0]] = value
            return
    elif program in BINDERS:
        names = [w.text for w in rest if not w.text.startswith("-")]
        # zsh's `print -vNAME`, `strftime -sNAME`, `zstat -ANAME`: the name written against its option.
        names += [w.text[2:] for w in rest if re.match(r"^-[vsAaFH][A-Za-z_]", w.text)]
        if program in ("mapfile", "readarray"):
            # `mapfile -C 'cmd'` runs its callback as shell text.
            for k, w in enumerate(rest):
                code = (rest[k + 1].text if w.text == "-C" and k + 1 < len(rest) else
                        w.text[2:] if w.text.startswith("-C") and len(w.text) > 2 else None)
                if code is not None and (why := _apart(code, 1)):
                    raise Unreadable(why)
    elif program in SETTERS and any(re.match(r"^-[A-Za-z]*n", w.text) for w in rest):
        for w in rest:
            if w.text.startswith("-"):
                continue
            name, eq, target = w.text.partition("=")
            # `declare -n r=GIT_PAGER; r='rm -rf ~'` assigns GIT_PAGER through r, and `declare -n r` takes its
            # target from the next `r=...`: the target must be a literal name, and no command a program runs.
            if (not eq or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", target) or CODE_ENV & {name, target}
                    or TEMPLATE_ENV in (name, target)):
                raise Unreadable(NAME_UNREAD)
            NAMEREF[name] = target
            names += [name, target]
    for n in names:
        if "$" in n or "`" in n:   # `printf -v "$n"`, `read "$n"`: a name this cannot read
            raise Unreadable(NAME_UNREAD)
        n = n.split("[")[0]
        if n in CODE_ENV:
            raise Unreadable(CODE_ENV_UNREAD.format(name=n))
        if n == TEMPLATE_ENV:
            raise Unreadable(TEMPLATE)
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", n):
            _bound(n)
            if FLOW["scoped"]:
                WORLD["forked"] = True
                if WORLD["skip"]:
                    continue
            SCOPE[n] = UNREAD if program in ("mapfile", "readarray") else UNKNOWN   # #344: an array


def _for_value(rest: list[Word]) -> str | None:
    """A3: `for NAME in WORDS` over literal words gives NAME each word in turn, judged one pass per word
    (FORS); this pass's word. None -- NAME unknown, as for any binder -- when a word is an expansion or a
    pattern, or NAME had a value before the loop (here, in the environment, or through a reference), since a
    loop that may not run leaves that one."""
    if len(rest) < 3 or rest[1].text != "in" or rest[1].quoted or FORS["unknown"]:
        return None
    name, words = rest[0].text, rest[2:]
    if (not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) or name in CODE_ENV or name in SCOPE or name in NAMEREF
            or name in os.environ or any(w.glob or w.equals or w.subs or w.expands for w in words)):
        return None
    sizes, pick = FORS["sizes"], FORS["pick"]
    k = len(sizes)
    sizes.append(len(words))
    return words[pick[k] if k < len(pick) else 0].text


def _mktemp_only(text: str) -> bool:
    """A substitution that runs `mktemp` and nothing else: no second command, no redirection, no expansion."""
    return bool(MKTEMP.match(text)) and not any(ch in text for ch in ";&|`$<>()\n")


def _shadow(word: Word) -> None:
    """A prefix assignment (`NAME=value cmd`) sets nothing for the shell -- the command's own words and every later
    command expand NAME as before (`HOME=$(mktemp -d) true && rm -rf "$HOME"` removed the real home past v7.1.1) --
    but before a special builtin (`NAME=v :` in a POSIX shell) it holds. So in the first world (WORLD) it holds,
    and in the second NAME is unknown from here on, as it always was: what this text or the environment held before
    may not be what the command's shell holds (`PWD`, `HOME`), and an unknown value is never scratch (#287)."""
    name, _, value = word.text.partition("=")
    base = name.rstrip("+").split("[")[0]
    if base == "CDPATH":
        SEEN["cdpath"] = True
    _bound(base)
    WORLD["forked"] = True
    SCOPE[base] = UNKNOWN if WORLD["skip"] or name != base else _value(word, value)


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


#: M5 of the bundle review: `${NAME:-literal}`, `${NAME-literal}`, `${NAME:=literal}`, `${NAME=literal}` with a plain
#: literal default -- each may be NAME's value or the default, and the command is judged with each (`_defaults`).
DEFAULT_FORM = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):?[-=]([^}$`'\"\\*?\[{]*)\}")
#: Past this many variants of one command, its defaults are left unread (#344), and so refused where read.
MAX_VARIANTS = 16


def _defaults(cmd: Command) -> list[Command] | None:
    """M5: the command once per value its `${NAME:-literal}` forms may take -- `${NAME}` (its value as this text or
    the environment holds it) or the literal -- in its words and redirection targets, never in an assignment (whose
    value stays unread). None when it holds none, or more than MAX_VARIANTS variants."""
    def variants(w: Word) -> list[Word]:
        out = [""]
        k = 0
        for m in DEFAULT_FORM.finditer(w.text):
            out = [o + w.text[k:m.start()] + choice for o in out for choice in ("${" + m.group(1) + "}", m.group(2))]
            k = m.end()
            if len(out) > MAX_VARIANTS:
                raise OverflowError
        return [Word(o + w.text[k:], w.glob, w.equals, w.quoted, list(w.subs)) for o in out]
    if not any(DEFAULT_FORM.search(w.text) for w in cmd.words + cmd.writes):
        return None
    try:
        words = [[w] if ASSIGNMENT.match(w.text) else variants(w) for w in cmd.words]
        writes = [variants(w) for w in cmd.writes]
    except OverflowError:
        return None
    combos: list[tuple[list[Word], list[Word]]] = [([], [])]
    for options in words:
        combos = [(ws + [o], wr) for ws, wr in combos for o in options]
    for options in writes:
        combos = [(ws, wr + [o]) for ws, wr in combos for o in options]
    if len(combos) > MAX_VARIANTS:
        return None
    return [Command(ws, cmd.fed, cmd.piped, cmd.from_file, cmd.procsub, wr, cmd.joined, cmd.inner, cmd.subshell)
            for ws, wr in combos]


def judge_command(cmd: Command, depth: int) -> str | None:
    """M5: a command with `${NAME:-literal}` defaults is judged once per value they may take, refused if any is."""
    if any(_stamp_target(w) for w in cmd.writes):
        return GATE_STAMP
    # `: ${GIT_PAGER:='rm -rf ~'}` and `: ${d::=/}` assign as they expand (read before a variant writes the form out).
    for w in cmd.words + cmd.writes:
        for name in EXPANSION_ASSIGN.findall(w.text):
            if name in CODE_ENV:
                return CODE_ENV_UNREAD.format(name=name)
            if name == TEMPLATE_ENV:
                return TEMPLATE
            _bound(name)
            SCOPE[name] = UNKNOWN
    for variant in _defaults(cmd) or [cmd]:
        if (why := _judge_command_once(variant, depth)):
            return why
    return None


def _judge_command_once(cmd: Command, depth: int) -> str | None:
    """Past assignments and keywords; after a wrapper, every later word is tried as the program, in one pass."""
    words = cmd.words
    if any(TMPDIR_NAMED.search(w.text) for w in words):
        TRUST["TMPDIR"] = False   # `read TMP""DIR`: the name, quoted apart, as the shell will see it
    written = [_expand(w.text) for w in cmd.writes]
    if (hit := next((w.text for w in cmd.writes if _unread_word(w)), None)) is not None:
        return UNREAD_WRITE.format(path=hit)   # #344: `echo x > "$(echo .claude)"/settings.json`
    # The Write/Edit guard refuses a `.env` file and the owner's directories; a shell redirection is the same write.
    if any(_env_file(t) for t in written):
        return ENV_WRITE
    if any(_owners(t) for t in written):
        return OWNERS
    if (hit := next((t for t in written if _git_file(t, itself=True)), None)) is not None:
        return GIT_FILE_WRITE.format(path=hit)   # #285: `echo ... >> .git/config`
    if (why := _unlinks_worktree(written)):
        return why   # #317: `echo x > <wt>/.git`
    start = 0
    while start < len(words) and (ASSIGNMENT.match(words[start].text) or words[start].text in KEYWORDS):
        start += 1
    # #68: an unquoted `$x` in program position is split into words, as the shell splits its value
    # (`x='rm -rf ~'; $x` is `rm -rf ~`; v7.2 read one program named `rm -rf ~`).
    if start < len(words) and words[start].bare and re.search(r"\s", value := _expand(words[start].text)):
        words = cmd.words = (words[:start] + [Word(t, glob=any(c in t for c in "*?[")) for t in value.split()]
                             + words[start + 1:])
    if SEEN["stamp"] and not _stamp_ok(cmd):
        return GATE_STAMP
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
            # This shell expands `"$x"` before the child starts: judge the rest with its literals in, too (#68, run v73 R1).
            if any(w.expands for w in words[k + 1:]) and (why := judge_command(Command(words=[word] + [
                    Word(_expand(w.text)) if w.expands else w for w in words[k + 1:]]), depth + 1)):
                return why
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
                if arg == "--":
                    break
                # #400: `-S` read anywhere in a cluster (`-iS 'fly deploy'`, `-vS'...'`), after a valued option
                # and its value (`-u X -S ...`), and as an abbreviated long option (`--sp`); a cluster or a long
                # option this cannot read is refused, never passed whole.
                read = _env_option(arg, words[j + 1].text if j + 1 < len(words) else None)
                if read is None:
                    return ENV_UNREAD.format(word=arg)
                text, used = read
                # #68 (v7.3): this shell expands `"$x"` before env runs: the string is read with this text's
                # literals in, then refused as below if a `$` is left.
                if text is not None and any(w.expands for w in words[j:j + used]):
                    text = _expand(text)
                # The bundle review's rounds 2 and 3 (B1, B2): env splits the `-S` string by its own rules, not the
                # shell's -- `\_` separates words, `${NAME}` expands, and a raw tab, VT, FF, CR or LF is a space --
                # so a string holding a backslash, a `$`, or any character that is not printable but the plain space
                # is refused rather than read with the shell's (`env -S 'fly\_deploy'`, `env -S $'fly\vdeploy'`).
                if text is not None and _env_s_unread(text):
                    return ENV_S_UNREAD.format(text=text.encode("unicode_escape").decode("ascii"))
                # `-S` carries env's own options as well as the program: judged as an `env` line.
                if text is not None and (why := judge_text("env " + text, depth + 1)):
                    return why
                j += used
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


#: #400: `env`'s short options, GNU's and BSD's: the flags, and those that take a value (the rest of the word, or
#: the next one). `-S` is the one whose value is a command line.
ENV_FLAGS = frozenset("i0v")
ENV_VALUED = frozenset("uCSPaL")
#: `env`'s long options, each with whether it takes a value; GNU takes any unambiguous prefix (`--sp`).
ENV_LONG = {"--unset": True, "--chdir": True, "--split-string": True, "--argv0": True,
            "--ignore-environment": False, "--null": False, "--debug": False, "--help": False, "--version": False,
            "--list-signal-handling": False, "--default-signal": False, "--ignore-signal": False,
            "--block-signal": False}


def _env_option(arg: str, following: str | None) -> tuple[str | None, int] | None:
    """One word of `env`'s options: (the command line `-S` carries in it, or None; the words it uses), or None
    when this cannot read it (#400: `env -iS 'fly deploy'` passed whole)."""
    if ASSIGNMENT.match(arg) or arg == "-":
        return None, 1
    if arg.startswith("--"):
        name, eq, value = arg.partition("=")
        found = [long for long in ENV_LONG if long == name] or [long for long in ENV_LONG if long.startswith(name)]
        if len(name) < 3 or len(found) != 1:
            return None
        if not ENV_LONG[found[0]] or eq:
            return (value if eq and found[0] == "--split-string" else None), 1
        return (following if found[0] == "--split-string" else None), 2
    for i, letter in enumerate(arg[1:], 1):
        if letter in ENV_FLAGS:
            continue
        if letter not in ENV_VALUED:
            return None
        rest = arg[i + 1:]
        value, used = (rest, 1) if rest else (following, 2)
        return (value if letter == "S" else None), used
    return None, 1


def _env_s_unread(text: str) -> bool:
    """Whether env could split an `-S` string otherwise than the shell reads it: a backslash, a `$`, or any
    character that is not printable but the plain space (#400; the bundle review's B1 and B2)."""
    return any(c in "\\$" or (not c.isprintable() and c != " ") for c in text)


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
        for text in cmd.fed:   # a shell reads them in a process of its own; `source`, in this one
            if (why := (_apart(text, depth + 1) if who.startswith("a shell") else _evaled(text, depth + 1))):
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
    # #344: a program named through a value this cannot read (`p=$(echo fly); $p deploy`); a path to it whose last
    # part is written (`"$(git rev-parse --show-toplevel)"/scripts/x.sh`) names it.
    last = first.text.rsplit("/", 1)[-1]
    if _unread_word(Word(last, subs=first.subs if "$(...)" in last else [])):
        return UNREAD_PROGRAM.format(word=first.text)
    # A pattern the shell expands to the stamp's script, run by an interpreter. (The stamp itself is named
    # by its commit, so a pattern can only rewrite an old one: no check is owed for it here.)
    if INTERPRETERS.match(program) and any(_names_stamp_script(w) for w in words[1:]):
        return GATE_STAMP
    # The stamp's script run as the program (the rest of A2 is `_stamp_ok`, per command).
    if _stamp_pattern(_expand(first.text), ("gate_stamp.py",)):
        return GATE_STAMP
    if program in ("make", "gmake") and any(
            (a.startswith("--") and len(a.split("=", 1)[0]) >= 3
             and any(u.startswith(a.split("=", 1)[0]) for u in MAKE_UNSAFE_LONG))
            or re.match(r"^-[a-zA-Z]*[iotWe]", a)
            for a in (w.text for w in words[1:]) if a.startswith("-") and a != "--"):
        return MAKE_FLAGS
    args = [w.text for w in words[1:]]
    CANDIDATES.append((list(HERE["dirs"]), [_expand(first.text[1:] if first.equals else first.text)] + args))
    unread = [_unread_word(w) for w in words[1:]]   # #344
    if (why := _writes_protected(program, [_expand(a) for a in args],
                                 {_expand(a) for a, u in zip(args, unread) if u})):
        return why
    if program == "eval":
        return _evaled(" ".join(_expand(a) for a in args), depth + 1)   # #68 (v7.3)
    # `trap 'cmd' EXIT` runs its text when the shell exits or takes the signal.
    if program == "trap" and args and args[0] not in ("-", "-l", "-p", "--") and not args[0].isdigit():
        return _apart(args[0], depth + 1)
    # `alias ls='rm -rf ~'` and a later line's `ls`: an alias is the text it names.
    if program == "alias":
        for a in args:
            if "=" in a and not a.startswith("-") and (why := _apart(a.partition("=")[2], depth + 1)):
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
            if (why := _removes_dirty_worktree(starts)):
                return why
        for i, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                rest = words[i + 2:]
                end = next((j for j, w in enumerate(rest) if w.text in (";", "+")), len(rest))
                if not rest[:end]:
                    continue
                # The bundle review's round 3, M10: a wrapper behind `-exec` (`find . -exec env fly deploy \;`) is
                # walked as at a command position, so `env`, `sudo` and the rest are unwrapped there too.
                # `{}` stays a pattern there, as any pattern after a wrapper is (`sudo chmod 644 *.txt`): it is a
                # path this cannot name, so `find ~ -exec env rm -rf {} \;` is refused like `rm -rf {}` there.
                inner = Command(rest[:end], cmd.fed, cmd.piped, cmd.from_file, cmd.procsub, [], cmd.joined,
                                cmd.inner, cmd.subshell)
                if (why := (judge_command(inner, depth + 1) if _program(rest[0]) in WRAPPERS
                            else judge_words(rest[:end], cmd, depth))):
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
    # The owner's disk is case-insensitive (APFS): `scripts/DEPLOY_HOSTED_ENGINE.sh` runs the same script (the run
    # golden-night owner-bundle security review's M1), so the deploy scripts are named casefolded.
    named = program.casefold()
    if named == DEPLOY and (args != ["--dry-run"] or behind_xargs):
        return DEPLOY_SCRIPT
    if program == "mv" and (hit := _project_tree(_mv_sources(words[1:]))):
        return PROJECT_TREE.format(target=hit)
    if program == "git":  # its ref words with this text's literals in (`m=main; git push origin --delete $m`)
        return _judge_git([_expand(a) for a in args], behind_xargs, depth,
                          unread_at={k for k, u in enumerate(unread) if u})
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
# seats' throwaway checkouts. The way to drop one is `git worktree remove <path>`: git deletes the directory and
# prunes its record. Since #286 that, `rm -r` and `find -delete` of one are refused while it holds uncommitted work.

def _owned(path: str, base: str) -> list[str] | None:
    """The parts of `path`, resolved from `base`, below the root of a work tree it lies in when the first of them is
    an owned directory; None when the path is not protected. Every work tree above the path is asked, nearest
    first, not only the nearest (#256): a `.git` planted inside `.claude/` (`git init .claude`) made `.claude` a
    work tree of its own, and the owner's files in it writable. The one work tree that ends the walk is a worktree
    at `<root>/.claude/worktrees/<name>`, Claude Code's own, already asked as its own work tree below."""
    target = os.path.realpath(os.path.join(base or os.getcwd(), os.path.expandvars(os.path.expanduser(path))))
    below, root = target, os.path.dirname(target)
    while True:
        while not os.path.lexists(os.path.join(root, ".git")):
            if os.path.dirname(root) == root:
                return None
            below, root = root, os.path.dirname(root)
        parts = os.path.relpath(target, root).split(os.sep)
        if os.path.basename(below).casefold() in OWNED:
            if len(parts) > 3 and _in_worktrees(parts) and os.path.lexists(os.path.join(root, *parts[:3], ".git")):
                return None
            return parts
        if os.path.dirname(root) == root:
            return None
        below, root = root, os.path.dirname(root)


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


def _writes_protected(program: str, args: list[str], unread: set[str] | None = None) -> str | None:
    """A write into a work tree's `.claude/` or `.githooks/` by a program this lists (S3; round 2, B1 and M6).
    `rm` may remove a directory under `.claude/worktrees/<name>`, v7.1's scratch. The same writes into git's own
    configuration or hooks (`_git_file`, #285) are refused, with no exception."""
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
    unread = unread or set()
    # #344: a path written through a value this cannot read may be any of the paths below. (`rm -r` meets the scratch
    # rule, which takes such a path as no scratch.)
    if program == "rm" and _rm_flags(args)[0]:
        unread = set()
    if (hit := next((a for a in written if a in unread or "of=" + a in unread), None)
            or next((o for o in option if any(u.endswith(o) for u in unread)), None)) is not None:
        return UNREAD_WRITE.format(path=hit)
    if any(_owners(a, worktrees=program == "rm") for a in written):
        return OWNERS
    # #285; a destination may be the git directory itself (`cp -r hooks .git/`), a removed path may not.
    dests = written if program not in CHANGES_EVERY else (option or paths[-1:]) if program == "mv" else []
    if (hit := next((a for a in written if _git_file(a, itself=a in dests)), None)) is not None:
        return GIT_FILE_WRITE.format(path=hit)
    if (why := _unlinks_worktree(written)):
        return why   # #317: `rm <wt>/.git`, `mv <wt>/.git x`, `cp /dev/null <wt>/.git`
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
    files = [a for a in paths if a][1:]   # the first plain word is the script (`-e`'s value, or its own)
    if in_place and (hit := next((a for a in files if a in unread), None)) is not None:
        return UNREAD_WRITE.format(path=hit)
    if in_place and any(_owners(a) for a in paths):
        return OWNERS
    if in_place and (hit := next((a for a in paths if _git_file(a)), None)) is not None:
        return GIT_FILE_WRITE.format(path=hit)   # #285: `sed -i ... .git/config`
    if in_place and (why := _unlinks_worktree(paths)):
        return why   # #317 (the review's M3): `sed -i '' d <dirty wt>/.git`
    return _git_writes(args, unread) if program == "git" else None


def _git_writes(args: list[str], unread: set[str] | None = None) -> str | None:
    """`git rm`, `git mv`, `git checkout` or `git restore` naming a protected path, from each `-C` directory;
    and `git rm` (but `--cached`) or `git mv` naming what holds one (#282)."""
    bases, i, joined = _bases(), 0, ""
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            bases = [_resolved(base, args[i + 1]) for base in bases]
            joined = os.path.join(joined, args[i + 1])
        # #256 (the review's M2): `git --git-dir=.claude/.git init` plants a git directory there; any git command
        # pointed at a git directory or a work tree in the owner's directories writes into them.
        name, eq, value = args[i].partition("=")
        place = value if eq else args[i + 1] if i + 1 < len(args) else ""
        if name in ("--git-dir", "--work-tree") and place and _owners(place, bases):
            return OWNERS
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path") else 1
    sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
    named = [a for a in rest if not a.startswith("-")]
    if sub in ("rm", "mv", "checkout", "restore") and any(_owners(a, bases) for a in named):
        return OWNERS
    # #256: `git init .claude`, `git clone <url> .claude/x` and `git worktree add .githooks/w` plant a `.git` in the
    # owner's directories; a worktree under `.claude/worktrees/<name>` is Claude Code's own.
    if any(_owners(a, bases, worktrees=sub == "worktree") for a in _git_made(sub, rest)):
        return OWNERS
    if (sub == "mv" or (sub == "rm" and "--cached" not in rest)):
        return _held(named[:-1] if sub == "mv" else named, bases, joined)
    return None


def _git_made(sub: str, rest: list[str]) -> list[str]:
    """The directories `git init`, `git clone`, `git submodule add` or `git worktree add` makes a repository or a git
    directory in (#256):
    init's directory (`.` when none), clone's (the second operand, or the last part of the URL), a worktree's path,
    and `--separate-git-dir`'s; none for any other subcommand."""
    if sub in ("worktree", "submodule"):
        if [a for a in rest if not a.startswith("-")][:1] != ["add"]:
            return []
        rest = rest[rest.index("add") + 1:]
        sub = "clone" if sub == "submodule" else sub   # `git submodule add <url> [<path>]` clones as `git clone` does
    elif sub not in ("init", "clone"):
        return []
    plain: list[str] = []
    made: list[str] = []
    k = 0
    while k < len(rest):
        a = rest[k]
        name, eq, value = a.partition("=")
        if a == "--":
            plain += rest[k + 1:]
            break
        if a.startswith("-") and len(a) > 1:
            if name == "--separate-git-dir":
                made.append(value if eq else rest[k + 1] if k + 1 < len(rest) else "")
            k += 2 if not eq and name in MADE_VALUED else 1
            continue
        plain.append(a)
        k += 1
    if sub == "init":
        made.append(plain[0] if plain else ".")
    elif sub == "clone" and plain:
        made.append(plain[1] if len(plain) > 1 else
                    re.sub(r"(/?\.git)?/*$", "", plain[0]).replace(":", "/").rsplit("/", 1)[-1] or ".")
    elif sub == "worktree" and plain:
        made.append(plain[0])
    return [m for m in made if m]


def _held(paths: list[str], bases: list[str] | None = None, git_base: str = "") -> str | None:
    """#282 (`_removes_owned`), worded as v7.1.2 words it where v7.1.2 refuses the same path: this repository,
    the work tree of a directory the command runs in, or a directory holding one is PROJECT_TREE's."""
    why = _removes_owned(paths, bases)
    if why and (hit := _project_tree([Word(p) for p in paths], git_base)):
        return PROJECT_TREE.format(target=hit)
    return why


# --- #285: git's own configuration and hooks, written by a shell ---------------------------------------------
#
# `git config <key> <value>` is read by `_judge_git` (core.hooksPath, aliases, keys whose value git runs). A file
# written straight into git's configuration or hooks is not: `echo '[core] hooksPath = /dev/null' >> .git/config`
# switches off the commit-msg and pre-push gates for every later command, and a script in `.git/hooks/` runs on
# the next commit. The programs and redirections are the owner's-directory rule's (`_writes_protected`).

def _git_rest(rest: list[str], itself: bool = False) -> bool:
    """Whether the parts below a git directory name its `config`, `config.worktree`, `hooks/` (or below), a linked
    worktree's `worktrees/<name>/config.worktree`, or, with `itself` (a destination: `cp -r hooks .git/` writes
    into it), the directory itself; any case, as a case-insensitive disk reads it. Since #320 also `info/` (or
    below: `exclude` hides work from `git status`), `commondir` (a worktree's too: it points the config elsewhere),
    and the same files of a submodule's git directory, `modules/<name>/` (names may hold `/`); since #318 the
    default branch's refs, where the deploy gate reads its base: `refs/heads/<protected>`, `refs/remotes/` (or below),
    `packed-refs`, and what moves a merge-base without a ref: `refs/replace/` (or below) and `shallow`."""
    rest = [p.casefold() for p in rest if p not in ("", ".")]
    if ((itself and (not rest or rest in (["refs"], ["refs", "heads"]))) or rest[:1] in (["hooks"], ["info"])
            or rest in (["config"], ["config.worktree"], ["commondir"], ["packed-refs"], ["shallow"])
            or rest[:2] in (["refs", "remotes"], ["refs", "replace"]) or (len(rest) == 3 and rest[:2] == ["refs", "heads"]
                                                   and rest[2] in PROTECTED)
            or (len(rest) == 3 and rest[0] == "worktrees" and rest[2] in ("config", "config.worktree", "commondir"))):
        return True
    return rest[:1] == ["modules"] and any(_git_rest(rest[k:]) for k in range(2, len(rest)))


def _git_dirs() -> list[str]:
    """The git directories of the work trees this call knows (`_known_roots`): each one's common directory and a
    linked worktree's own (its `gitdir:`), so one not named `.git` (`--separate-git-dir`) is held too."""
    out: list[str] = []
    for root in _known_roots():
        found = [_common(root)]
        dot = os.path.join(root, ".git")
        if os.path.isfile(dot):
            try:
                with open(dot, encoding="utf-8") as f:
                    line = f.read(4096).strip()
            except (OSError, UnicodeDecodeError):
                line = ""
            if line.startswith("gitdir:"):
                found.append(os.path.realpath(os.path.join(root, line[len("gitdir:"):].strip())))
        out += [d for d in found if d and d not in out]
    return out


def _git_file(path: str, bases: list[str] | None = None, itself: bool = False) -> bool:
    """#285: whether writing `path`, from any directory the command may run in, writes git's configuration or
    hooks: a `.git` directory's `config`, `config.worktree` or `hooks/`, and with `itself` the directory itself
    (`_git_rest`), the path as written and as resolved; the same of the git directory of each work tree this call
    knows (`_git_dirs`); or the global config, `~/.gitconfig` and `$XDG_CONFIG_HOME/git/config`. A removal of
    `.git` itself is not asked here: the rules for the repository and its `.git` answer it (PROJECT_TREE)."""
    home = os.path.expanduser("~")
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    named = [os.path.join(home, ".gitconfig"), os.path.join(xdg, "git", "config"),
             os.path.join(home, ".config", "git", "config")]
    named_folded = {p.casefold() for p in named + [os.path.realpath(p) for p in named]}
    dirs = _git_dirs()
    for base in (bases if bases is not None else _bases()) or [os.getcwd()]:
        written = os.path.join(base, os.path.expandvars(os.path.expanduser(path)))
        for target in dict.fromkeys([os.path.normpath(written), os.path.realpath(written)]):
            parts = target.split(os.sep)
            if target.casefold() in named_folded or any(
                    p.casefold() == ".git" and _git_rest(parts[i + 1:], itself) for i, p in enumerate(parts)):
                return True
            for d in dirs:
                cut = d.rstrip(os.sep) + os.sep
                if (itself and target.casefold() == d.rstrip(os.sep).casefold()) or (
                        target.casefold().startswith(cut.casefold()) and _git_rest(target[len(cut):].split(os.sep))):
                    return True
    return False


def judge_write(path: str, base: str) -> str | None:
    """The Write and Edit hook (`--write`): a secrets file by name, the gate stamp by name, or a path
    `protected` refuses."""
    if path and _env_file(path):
        return ENV_WRITE
    if path and path.replace("\\", "/").rsplit("/", 1)[-1].lower().startswith("devflow-gate"):
        return STAMP_WRITE
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
    return _removes_dirty_worktree(targets)


# --- #286: a worktree with uncommitted work is not removed --------------------------------------------------
#
# A `.claude/worktrees/<name>` worktree is scratch (v7.1, D-199 clause 3), and every review seat and implementer
# works in one (D-174). `rm -r`, `find -delete` and `git worktree remove --force` deleted one with uncommitted work
# in it. A worktree is LIVE when its `.git` is a directory, or a file whose `gitdir:` names a directory that
# exists; one whose `gitdir:` names nothing has no git record left and is not live. A live one is removed only
# when `git status --porcelain` there, bounded by STATUS, prints nothing; unmeasured, it is not removed.

def _git_env(ceiling: str | None = None) -> dict[str, str]:
    """The environment of the guard's own `git`: none of the call's `GIT_*` (a `GIT_DIR` points git at another
    repository), no optional lock taken, no prompt; with `ceiling`, git looks for no repository above it."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    if ceiling:
        env["GIT_CEILING_DIRECTORIES"] = ceiling
    return env


def _git_ask(args: list[str], ceiling: str | None = None, feed: bytes | None = None) -> tuple[str | None, str]:
    """(git's stdout, or None and why) for one `git` call within what is left of STATUS, `feed` on its stdin.
    `core.fsmonitor` is off: a worktree's config may name one, and this runs before the agent's command does."""
    left = STATUS["left"]
    if left <= 0:
        return None, f"the guard's {STATUS_S:g} s for git were spent"
    started = time.monotonic()
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", *args], capture_output=True, input=feed or b"",
                           env=_git_env(ceiling), timeout=left)
    except subprocess.TimeoutExpired:
        return None, f"git did not answer within {left:.1f} s"
    except (OSError, subprocess.SubprocessError) as error:
        return None, f"git could not run: {type(error).__name__}"
    finally:
        STATUS["left"] -= time.monotonic() - started
    if r.returncode != 0:
        return None, f"git exited {r.returncode}"
    return r.stdout.decode("utf-8", "replace"), ""


def _live(root: str) -> bool | None:
    """Whether `root` is a live work tree: True for a `.git` directory, or a `.git` file whose `gitdir:` names an
    existing directory; False with no `.git`, or a `gitdir:` naming nothing; None when the `.git` cannot be read."""
    dot = os.path.join(root, ".git")
    if not os.path.lexists(dot):
        return False
    if os.path.isdir(dot):
        return True
    try:
        with open(dot, encoding="utf-8") as f:
            line = f.read(4096).strip()
    except (OSError, UnicodeDecodeError):
        return None
    if not line.startswith("gitdir:"):
        return None
    return os.path.isdir(os.path.join(root, line[len("gitdir:"):].strip()))


def _worktree_roots(resolved: str) -> list[str]:
    """Each `.claude/worktrees/<name>` directory that `resolved` is or lies in, and each one below it, through
    nested `.claude/worktrees/`, links not followed. Past MAX_WORKTREES, or on one unreadable, `_Unwalked`."""
    parts = resolved.split(os.sep)
    out = [os.sep.join(parts[:i + 3]) for i, p in enumerate(parts)
           if p.casefold() == ".claude" and i + 2 < len(parts) and parts[i + 1].casefold() == "worktrees"
           and parts[i + 2] not in ("", ".", "..")]
    stack = [resolved]
    while stack:
        holder = os.path.join(stack.pop(), ".claude", "worktrees")
        if os.path.islink(holder) or not os.path.isdir(holder):
            continue
        try:
            with os.scandir(holder) as entries:
                found = [e.path for e in entries if e.is_dir(follow_symlinks=False)]
        except OSError:
            raise _Unwalked(holder) from None
        out += found
        stack += found
        if len(out) > MAX_WORKTREES:
            raise _Unwalked(resolved)
    return list(dict.fromkeys(out))


def _unclean(shown: str, roots: list[str]) -> str | None:
    """Why removing `shown` is refused: one of `roots` is a live worktree with uncommitted work, or one whose
    status cannot be measured; None when each is clean or not live."""
    for root in roots:
        live = _live(root)
        if live is False:
            continue
        if live is None:
            return UNMEASURED_WORKTREE.format(path=shown, root=root, why="its `.git` cannot be read")
        # `--untracked-files=all` over the repository's `status.showUntrackedFiles=no`, which an agent may set (the
        # owner-bundle security review's M2): a worktree holding only new files is not clean.
        out, why = _git_ask(["-C", root, "status", "--porcelain", "--untracked-files=all"], ceiling=os.path.dirname(root))
        if out is None:
            return UNMEASURED_WORKTREE.format(path=shown, root=root, why=why)
        if out.strip():
            return DIRTY_WORKTREE.format(path=shown, root=root)
        # #317: an untracked `.gitignore` that ignores itself (`echo '*' > notes/.gitignore`) hides its directory's
        # work, and itself, from the status above. One ignored by a rule of another file (a tool's own
        # `.pytest_cache/.gitignore` in a directory the committed `.gitignore` ignores) hides nothing new.
        found, why = _git_ask(["-C", root, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--",
                               ":(glob)**/.gitignore"], ceiling=os.path.dirname(root))
        if found is None:
            return UNMEASURED_WORKTREE.format(path=shown, root=root, why=why)
        # A nested repository is listed as `<dir>/` whatever the pathspec says; only the ignore files are asked.
        files = [f for f in found.split("\0") if f.rsplit("/", 1)[-1] == ".gitignore"]
        if files:
            out, why = _git_ask(["-C", root, "check-ignore", "-v", "-z", "--stdin"], ceiling=os.path.dirname(root),
                                feed="".join(f + "\0" for f in files).encode("utf-8", "surrogateescape"))
            if out is None:
                return UNMEASURED_WORKTREE.format(path=shown, root=root, why=why)
            fields = out.split("\0")
            if any(fields[k] == fields[k + 3] for k in range(0, len(fields) - 3, 4)):
                return DIRTY_WORKTREE.format(path=shown, root=root)
    return None


def _unlinks_worktree(paths: list[str]) -> str | None:
    """#317: a write to, or the removal of, the `.git` file of a live worktree with uncommitted work (`rm <wt>/.git`,
    `echo x > <wt>/.git`) leaves a plain directory that the removal rules then take: refused as its removal is. A
    `.git` directory is a repository's own, which the rules for the repository and its `.git` answer."""
    for a in paths:
        for base in _bases():
            target = os.path.normpath(os.path.join(base, os.path.expandvars(os.path.expanduser(a))))
            if os.path.basename(target).casefold() != ".git" or not os.path.isfile(target):
                continue
            if (hit := _project_tree([Word(target)])):   # this repository's own `.git`: the rule for it, in its words
                return PROJECT_TREE.format(target=hit)
            if (why := _unclean(a, [os.path.dirname(target)])):
                return why
    return None


def _removes_dirty_worktree(words: list[Word]) -> str | None:
    """#286 for `rm -r` and `find -delete`: a target at, in or above a `.claude/worktrees/<name>` that `_unclean`
    refuses, from each directory the command may run in."""
    for w in words:
        for p in _resolve(w):
            if not isinstance(p, str):
                continue
            try:
                roots = _worktree_roots(p)
            except _Unwalked:
                return UNMEASURED_WORKTREE.format(path=w.text, root=p, why=f"more than {MAX_WORKTREES} worktrees, "
                                                  "or an unreadable one, below it")
            if (why := _unclean(w.text, roots)):
                return why
    return None


def _judge_worktree_remove(targets: list[str], git_base: str, behind_xargs: bool) -> str | None:
    """#286 for `git worktree remove [--force] <worktree>`, forced or not (unforced, git refuses a dirty one
    itself). Git names the worktree by its path or by a unique last part of it (`seat` for
    `.claude/worktrees/seat`), so the target is the path from each directory the command runs in (`-C` joined)
    and each worktree `git worktree list` gives whose path ends in it; each, and each worktree below it, must be
    clean or not live. A path this cannot read, or one git cannot list that names no directory, is refused."""
    if behind_xargs:
        return UNMEASURED_WORKTREE.format(path="git worktree remove", root="(a path from stdin)",
                                          why="`xargs` hands it the path")
    for t in targets:
        if "$" in t or "`" in t or any(ch in t for ch in "*?["):
            return UNMEASURED_WORKTREE.format(path=t, root=t, why="its path is an expansion or a pattern")
        roots: list[str] = []
        listed, named = True, False
        want = t.rstrip("/").casefold()
        for base in _bases():
            d = os.path.join(base, git_base) if git_base else base
            path = os.path.realpath(os.path.join(d, os.path.expanduser(t)))
            roots.append(path)
            named = named or os.path.isdir(path)
            out, _ = _git_ask(["-C", d, "worktree", "list", "--porcelain"])
            if out is None:
                listed = False
                continue
            for line in out.splitlines():
                w = line[len("worktree "):] if line.startswith("worktree ") else ""
                if w and want and (w.casefold() == want or w.casefold().endswith("/" + want)):
                    roots.append(os.path.realpath(w))
        if not listed and not named:
            return UNMEASURED_WORKTREE.format(path=t, root=t, why="git could not list the worktrees, and no "
                                              "directory has that path")
        every: list[str] = []
        for root in dict.fromkeys(roots):
            try:
                every += [root] + _worktree_roots(root)
            except _Unwalked:
                return UNMEASURED_WORKTREE.format(path=t, root=root, why=f"more than {MAX_WORKTREES} worktrees, "
                                                  "or an unreadable one, below it")
        if (why := _unclean(t, list(dict.fromkeys(every)))):
            return why
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
    """A shell runs `-c`'s string, a script file, or what it reads on stdin. fish reads its options its own way."""
    if shell == "fish":
        return _judge_fish(args, cmd, depth)
    # Only a shell asked for nothing BUT long options, `--help` or `--version` among them, prints and stops (the run
    # golden-night owner-bundle security review's P1, kept over v7.3's reading of a `--help` before any short
    # option; v7.3's `--rcfile FILE --help` is such a call): `bash -c 'rm -rf ~' --help` runs the string, with
    # `--help` as its $0, and `bash --help -c '...'` is judged as its string too. An option's value is not one.
    k, asked = 0, False
    while k < len(args) and args[k].startswith("--") and args[k] != "--":
        asked = asked or args[k] in ("--version", "--help")
        k += 2 if args[k] in ("--rcfile", "--init-file") else 1
    if asked and k == len(args):
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
        for text in rest:  # the string, then $0 and its arguments: each read as a command, literals in (#68)
            if (why := _apart(_expand(text), depth + 1)):
                return why
        return None
    if rest and not reads_stdin and rest[0] not in STDIN_PATHS:
        return judge_words([Word(a) for a in rest], cmd, depth)
    return _stdin(cmd, depth, f"a shell (`{shell}`)")


def _judge_fish(args: list[str], cmd: Command, depth: int) -> str | None:
    """fish runs the text of `-c` and `-C` in every spelling its getopt reads: the next word (`-C x`), glued
    (`-Cx`, `-iCx`), `--command=x`, and a long option in any unique prefix (`--init=x`) -- #54: only the first
    was read. Then a script, or stdin. `--help` runs beside `-c`, so it means nothing unless it is all there is
    (#47)."""
    if args and all(a in ("--version", "--help") for a in args):
        return None
    texts: list[str] = []
    given_c = False
    j = 0
    while j < len(args) and args[j].startswith("-") and len(args[j]) > 1:
        arg = args[j]
        if arg == "--":
            j += 1
            break
        value: str | None = None
        letter = ""
        if arg.startswith("--"):
            name, eq, value = arg[2:].partition("=")
            hits = [o for o in FISH_LONG if o.startswith(name)]
            full = name if name in FISH_LONG else hits[0] if len(hits) == 1 else ""
            letter = {"command": "c", "init-command": "C"}.get(full, "")
            if FISH_LONG.get(full) and not eq:
                j += 1
                value = args[j] if j < len(args) else None
        else:
            k = next((k for k in range(1, len(arg)) if arg[k] in FISH_VALUED), None)
            if k is not None:
                letter, value = arg[k], arg[k + 1:]
                if not value:
                    j += 1
                    value = args[j] if j < len(args) else None
        if letter in ("c", "C"):
            if value is None:
                return f"BLOCKED: `fish -{letter}` with no command string takes it from elsewhere, which this guard cannot read."
            texts.append(value)
            given_c = given_c or letter == "c"
        j += 1
    rest = args[j:]
    for text in texts + (rest if given_c else []):  # with `-c`, the words after are `$argv`: read as commands too
        if (why := _apart(_expand(text), depth + 1)):
            return why
    if given_c:
        return None
    if rest and rest[0] not in STDIN_PATHS:
        return judge_words([Word(a) for a in rest], cmd, depth)
    return _stdin(cmd, depth, "a shell (`fish`)")


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
                    if key in SSH_LOCAL and text.lower() != "none" and (why := _apart(text, depth + 1)):
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


def _default_branch(start: str) -> str | None:
    """A8: the default branch of the repository holding `start` -- what its `origin/HEAD` names, read from the git
    directory with no git call; else `init.defaultBranch`, one git call; None when neither says. Once per git
    directory for the life of this process (DEFAULTS)."""
    top = os.path.realpath(start or ".")
    while not os.path.lexists(os.path.join(top, ".git")) and os.path.dirname(top) != top:
        top = os.path.dirname(top)
    if not os.path.lexists(os.path.join(top, ".git")):
        top = os.path.realpath(start or ".")   # no repository: `init.defaultBranch` from the user's config
        while not os.path.isdir(top) and os.path.dirname(top) != top:
            top = os.path.dirname(top)
        common = None
    else:
        common = _common(top)
    key = common or top
    if key not in DEFAULTS:
        name = None
        if common:
            try:
                with open(os.path.join(common, "refs", "remotes", "origin", "HEAD"), encoding="utf-8") as f:
                    line = f.read(4096).strip()
                if line.startswith("ref: refs/remotes/origin/"):
                    name = line[len("ref: refs/remotes/origin/"):]
            except OSError:
                pass
        if name is None:
            try:
                r = subprocess.run(["git", "-C", top, "config", "--get", "init.defaultBranch"], capture_output=True,
                                   timeout=10)
                name = r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None
            except (OSError, subprocess.SubprocessError):
                name = None
        DEFAULTS[key] = name if name and re.fullmatch(r"[\w./-]+", name) else None
    return DEFAULTS[key]


def _protected_branches() -> set[str]:
    """The branches the agent never pushes, deletes or moves: main, master and trunk, and the default branch of
    the repository the call runs in (A8)."""
    name = _default_branch(CWD["dir"] or os.getcwd())
    return PROTECTED | ({name} if name else set())


def _skips_hooks(option: str) -> bool:
    """Whether a long option is `--no-verify` as git may read it, refused: the name, or a prefix of it
    from `--no-ve` (`--no-veri` is it; a shorter one is ambiguous with `--no-verbose`), with or without `=`."""
    name = option.split("=", 1)[0]
    return len(name) >= len("--no-ve") and "--no-verify".startswith(name)


def _husky_off() -> bool:
    """Whether this text turns husky's runner off for the push it holds: `HUSKY=0` (husky 5-9) or `HUSKY_SKIP_HOOKS`
    `1` or `true` (husky 4), or either set to a value this cannot read -- a prefix or `env` assignment leaves its
    name unread for the rest of the text, so `HUSKY=0 git push` and `env HUSKY=0 git push` are read here as well."""
    husky, skip = SCOPE.get("HUSKY", ""), SCOPE.get("HUSKY_SKIP_HOOKS", "")
    return (not isinstance(husky, str) or husky.strip() == "0"
            or not isinstance(skip, str) or skip.strip().lower() in ("1", "true"))


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



def _edits_config(rest: list[str]) -> bool:
    """#285: `git config --edit` in any prefix of it from `--e`, `-e` alone or in a cluster of short options, or
    the `edit` subcommand (the first plain word, unless an option reads: `--get-regexp edit` reads): git opens the
    file in an editor, and what is written there this guard never reads. Every word is looked at, an option's
    value too: an `-e` that is one is refused as well."""
    options, plain = _config_split(rest)
    if plain[:1] == ["edit"] and not _reads(options, plain[1:]):
        return True
    for a in rest:
        if a.startswith("--"):
            name = a.split("=", 1)[0]
            if len(name) >= 3 and "--edit".startswith(name):
                return True
        elif a.startswith("-") and len(a) > 1 and "e" in a[1:]:
            return True
    return False


def _config_env(word: Word) -> str | None:
    """Why an assignment that feeds git's config through the environment (`GIT_CONFIG_PARAMETERS`,
    `GIT_CONFIG_KEY_<n>`) is refused: it names `core.hooksPath` or an expansion this cannot read there, or
    it defines an alias, whose command this cannot pair with the value set beside it."""
    name, _, value = word.text.partition("=")
    base = name.rstrip("+").split("[")[0]
    if base == TEMPLATE_ENV:
        return TEMPLATE   # #320: wherever it is assigned, whatever its value
    if base in GIT_PLACE_ENV and value and "$" not in value and _owners(_expand(value)):
        return OWNERS   # #256 (the review's M2): `GIT_DIR=.claude/.git git init`
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
        return _apart(value, 1) if value.strip() else None
    if not GIT_CONFIG_ENV.match(name.rstrip("+")):
        return None
    value = _expand(value)
    if "hookspath" in value.lower() or "$" in value:
        return NO_VERIFY
    if TEMPLATE_KEY in value.lower():
        return TEMPLATE
    if REMOTE_KEY_IN.search(value):
        return PROTECTED_REF
    keys = re.findall(r"[A-Za-z][\w.-]*", value)
    return ALIAS_UNREAD if "alias." in value.lower() or any(CODE_KEY.match(k) for k in keys) else None


def _judge_alias(value: str, depth: int, args: list[str] | None = None) -> str | None:
    """An alias is the command it names, with the words it is called with: `!` and shell text (git runs it
    with the arguments appended), or a git subcommand and its words."""
    tail = " ".join(shlex.quote(a) for a in (args or []))
    text = value[1:] if value.startswith("!") else "git " + value
    return _apart(f"{text} {tail}".strip(), depth + 1)


def _judge_code(value: str, depth: int) -> str | None:
    """#305: a config value git runs as a command (CODE_KEY), judged as that command. A value that starts with `!`
    (`credential.helper '!rm -rf ~'`) is shell text after the `!`; any other names a program and its words. The
    `!` was once left on, and `!rm` read as a program of that name."""
    # v7.3 (#47): every leading `!` -- `!!rm -rf ~` is `rm -rf ~` to read, not the program `!rm`.
    return _apart(value.lstrip().lstrip("!"), depth + 1)


def _config_set(rest: list[str]) -> tuple[str, str] | None:
    """(key, value) that `git config <rest>` writes, or None when it reads, unsets or writes nothing."""
    options, plain = _config_split(rest)
    if _reads(options, plain) or plain[:1] in (["unset"], ["remove-section"], ["rename-section"]) or any(
            a.startswith(("--unset", "--remove-section", "--rename-section", "--edit")) for a in options):
        return None
    if plain[:1] == ["set"]:
        plain = plain[1:]
    return (plain[0], plain[1]) if len(plain) >= 2 else None



def _default_ref(name: str) -> bool:
    """#318: whether a ref names a branch the deploy gate reads its base from (`brief_fields.DEFAULT_BRANCHES`): a
    protected branch (`main`, `heads/main`, `refs/heads/main`), or a remote's (`origin/main`, `origin/HEAD`,
    `refs/remotes/origin/HEAD`); a pattern there (`refs/remotes/origin/*`) may be one. Any case: a loose ref is a
    file, and the owner's disk does not tell `MAIN` from `main`."""
    n = name.lstrip("+").casefold().removeprefix("refs/")
    if n.removeprefix("heads/") in PROTECTED:
        return True
    parts = n.removeprefix("remotes/").split("/")
    return len(parts) >= 2 and (parts[-1] in PROTECTED | {"head"} or (
        "*" in n and n.startswith(("heads/", "remotes/"))))


def _unread_or_default(name: str) -> bool:
    """A ref `_default_ref` names, or one built from an expansion this cannot read, which may be one."""
    return _default_ref(name) or "$" in name or "`" in name


#: #533 (D-236): the refs the deploy gate reads, as git stores them: the protected branches, and every ref under
#: `refs/remotes/origin/` (`_default_ref` adds a remote's `HEAD` and protected branches by their shape).
GATE_REFS = tuple(sorted(f"refs/heads/{b}" for b in PROTECTED))
GATE_UNDER = ("refs/remotes/origin/",)


def _lands(dst: str, exact: tuple[str, ...], under: tuple[str, ...]) -> bool:
    """#533, #529 (D-236): whether a refspec's destination may be one of `exact` or lie under one of `under`, in any
    case. A destination not under `refs/` is a branch (`main` is `refs/heads/main`), and one under `heads/`, `tags/`
    or `remotes/` is that under `refs/`, as git stores a fetched ref. A pattern is read as every name it may take:
    its `*` stands for anything, a `refs/...` too, so `refs/*` and `*` may be any ref (`git fetch origin
    'refs/*:refs/*'` wrote `refs/heads/main` and `refs/replace/` past #318 and #410)."""
    d = dst.lstrip("+").casefold()
    if not d:
        return False
    names = [d] if d.startswith("refs/") else ["refs/" + d] if d.startswith(("heads/", "tags/", "remotes/")) else [
        "refs/heads/" + d]
    if "*" in d and not d.startswith("refs/"):
        names += [d, "refs/" + d]
    for n in names:
        if "*" not in n:
            if n in exact or n.startswith(under):
                return True
            continue
        head = n.split("*", 1)[0]
        shape = re.compile(".*".join(re.escape(part) for part in n.split("*")), re.S)
        if any(shape.fullmatch(e) for e in exact) or any(head.startswith(u) or u.startswith(head) for u in under):
            return True
    return False


def _lands_on_gate(dst: str) -> bool:
    """#318, #533: a destination that is, or may be, a ref the deploy gate reads (an unread one may be any)."""
    return _unread_or_default(dst) or _lands(dst, GATE_REFS, GATE_UNDER)


def _refmaps(rest: list[str]) -> list[str]:
    """#533: the refspecs `git fetch --refmap` maps the command line's refs by, in any prefix git reads (`--refm`)."""
    out: list[str] = []
    for k, a in enumerate(rest):
        name, eq, value = a.partition("=")
        if len(name) >= 6 and "--refmap".startswith(name):
            out.append(value if eq else rest[k + 1] if k + 1 < len(rest) else "")
    return out


def _worktree_made(after: list[str]) -> str | None:
    """#533 (D-236): `git worktree add` making a branch the deploy gate reads: `-b`/`-B` (apart, against it, or
    ending a cluster: `-fB main`), or, with neither and no `--detach`, the branch git names after the path's last
    part when the path is the only operand (`git worktree add ../main`)."""
    plain: list[str] = []
    made, forced, detached = None, False, False
    k = 0
    while k < len(after):
        a = after[k]
        if a == "--":
            plain += after[k + 1:]
            break
        if a.startswith("--"):
            name, eq, _ = a.partition("=")
            detached = detached or (len(name) >= 4 and "--detach".startswith(name))
            k += 2 if not eq and len(name) >= 4 and "--reason".startswith(name) else 1
            continue
        if a.startswith("-") and len(a) > 1:
            at = next((j for j, ch in enumerate(a[1:], 1) if ch in "bB"), None)
            detached = detached or "d" in a[1:at]
            if at is not None:
                made, forced = a[at + 1:] or (after[k + 1] if k + 1 < len(after) else ""), a[at] == "B"
                k += 1 if a[at + 1:] else 2
                continue
            k += 1
            continue
        plain.append(a)
        k += 1
    if made is not None:
        return PROTECTED_REF if (_unread_or_default if forced else _default_ref)(made) else None
    if not detached and len(plain) == 1:
        return PROTECTED_REF if _default_ref(plain[0].rstrip("/").rsplit("/", 1)[-1]) else None
    return None


def _renames_remote(rest: list[str]) -> bool:
    """#533: `git config --rename-section` (or `rename-section`) of a `remote.` section: `remote.evil` renamed to
    `remote.origin` is origin with evil's URL and refspec."""
    options, plain = _config_split(rest)
    if plain[:1] == ["rename-section"] or any(a.startswith("--rename-section") for a in options):
        return any(p.casefold() == "remote" or p.casefold().startswith("remote.") for p in plain)
    return False


def _plain(rest: list[str], valued: set[str]) -> list[str]:
    """The words of `rest` that are no option and no option's value."""
    out: list[str] = []
    k = 0
    while k < len(rest):
        a = rest[k]
        if a == "--":
            return out + rest[k + 1:]
        if a.startswith("-") and len(a) > 1:
            k += 2 if a in valued else 1
            continue
        out.append(a)
        k += 1
    return out


def _moves_default(sub: str, rest: list[str], letters: str, given: Callable[..., bool]) -> str | None:
    """#318, #533 (D-236): a command that moves, deletes, creates or redirects a ref the deploy gate reads its base
    from: `git branch` (forced, moved, copied, deleted, or created), `git checkout -b/-B`, `git switch -c/-C` and `git
    worktree add -b/-B`, `git update-ref` (or its `--stdin`), `git symbolic-ref` writing or deleting one, a fetch or
    pull refspec or `--refmap` whose destination may land on one, and `git remote` changing `origin` (`set-url`,
    `add`, `rename`, `remove`, or `set-head` but `--auto`) or adding a mirror."""
    if sub == "branch":
        plain = _plain(rest, BRANCH_VALUED)
        if any(ch in letters for ch in "dDmM") or given("--delete", "--move"):
            # #533: deleted, the gate's branch was made again at a commit of the agent's choosing (`git branch -D
            # main`, then `git worktree add -b main <dir> <old sha>`), and renamed it is gone the same way; with `-r`
            # a name is a remote's (`origin/HEAD` is `refs/remotes/origin/HEAD`). A lone `-m <new>` renames the
            # current branch, which may be `main`.
            remote = "r" in letters or given("--remotes")
            if (any(ch in letters for ch in "mM") or given("--move")) and len(plain) < 2:
                return PROTECTED_REF
            return PROTECTED_REF if any(_unread_or_default(p) or (remote and _lands("remotes/" + p, (), GATE_UNDER))
                                        for p in plain) else None
        copying = any(ch in letters for ch in "cC") or given("--copy")
        listing = any(ch in letters for ch in "larv") or given("--list", "--all", "--remotes", "--show-current")
        forced = copying or "f" in letters or given("--force")
        # copied: the destination, the last name; forced or made: the first.
        named = plain[-1:] if copying else plain[:1] if not listing or forced else []
        # A name this cannot read is refused where the branch is moved or forced; a new one is only made.
        return PROTECTED_REF if any((_unread_or_default if forced else _default_ref)(p) for p in named) else None
    if sub in ("checkout", "switch"):
        # The branch a `-b`/`-B` (`-c`/`-C`) makes: its value written apart, against it (`-Bmain`), or at the end of a
        # cluster (`-qB main`); `--create`, `--force-create` and `--orphan` in any prefix git reads (`--force-cr`).
        letters_made = "bB" if sub == "checkout" else "cC"
        longs_made = ["--orphan"] if sub == "checkout" else ["--create", "--force-create", "--orphan"]
        for k, a in enumerate(rest):
            following = rest[k + 1] if k + 1 < len(rest) else ""
            if a == "--":
                break
            if a.startswith("--"):
                name, eq, value = a.partition("=")
                hit = [w for w in longs_made if name == w or (len(name) >= 4 and w.startswith(name) and name != "--force")]
                forced = any(w == "--force-create" for w in hit)
                named = value if eq else following
            elif a.startswith("-") and len(a) > 1:
                at = next((j for j, ch in enumerate(a[1:], 1) if ch in letters_made), None)
                if at is None:
                    continue
                hit, forced, named = [a[at]], a[at].isupper(), a[at + 1:] or following
            else:
                continue
            if hit and (_unread_or_default if forced else _default_ref)(named):
                return PROTECTED_REF
        return None
    if sub == "worktree" and [a for a in rest if not a.startswith("-")][:1] == ["add"]:
        return _worktree_made(rest[rest.index("add") + 1:])
    if sub == "update-ref":
        refs = _plain(rest, {"-m"})
        return PROTECTED_REF if "--stdin" in rest or any(_lands_on_gate(r) for r in refs) else None
    if sub == "symbolic-ref":
        refs = _plain(rest, {"-m"})
        writes = len(refs) >= 2 or "d" in letters or given("--delete")
        return PROTECTED_REF if writes and any(_lands_on_gate(r) for r in refs) else None
    if sub in ("fetch", "pull"):
        # #533: a plain fetch or pull of origin moves `origin/*` by origin's own refspec; any other destination that
        # may be one of the gate's refs is refused, a `--refmap`'s too.
        specs = _plain(rest, FETCH_VALUED)[1:] + _refmaps(rest)
        return PROTECTED_REF if any(":" in sp and _lands_on_gate(sp.rsplit(":", 1)[1]) for sp in specs) else None
    if sub == "replace" and not (any(ch in letters for ch in "l") or given("--list")):
        return PROTECTED_REF   # `git replace <main's commit> HEAD` moves every merge-base with main, its ref unmoved
    if sub == "remote":
        plain = _plain(rest, {"-t", "-m", "--track", "--master"})
        if plain[:1] == ["set-head"]:
            return None if "-a" in rest or "--auto" in rest else PROTECTED_REF
        # #533: `ORIGIN` is origin's loose refs on a case-insensitive disk, and `origin/x` fetches under
        # `refs/remotes/origin/`; a mirror (`--mirror=fetch`) fetches `+refs/*:refs/*`.
        named = [p.casefold() for p in plain[1:]]
        if plain[:1] in (["set-url"], ["add"], ["rename"], ["remove"], ["rm"], ["set-branches"]) and any(
                p == "origin" or p.startswith("origin/") for p in named):
            return PROTECTED_REF
        if plain[:1] == ["add"] and any(len(n) >= 4 and "--mirror".startswith(n)
                                        for n in (a.split("=", 1)[0] for a in rest if a.startswith("--"))):
            return PROTECTED_REF
    return None


def _owner_ref(name: str, under: tuple[str, ...] = ("tags/v", "replace/")) -> bool:
    """A ref under `refs/tags/v` or `refs/replace/` (#410), in any case git may store it in."""
    return name.lstrip("+").casefold().removeprefix("refs/").startswith(under)


#: `git tag` options that take a value (#529): a short letter's is the rest of its word or the next word (`-m-l`,
#: `-am <msg>`), a long one's follows `=` or is the next word, in any prefix git reads (`--mess <msg>`).
TAG_SHORT_VALUED = "mFu"
TAG_LONG_VALUED = ("--message", "--file", "--local-user", "--cleanup", "--trailer", "--contains", "--no-contains",
                   "--merged", "--no-merged", "--points-at", "--sort", "--format")


def _tag_words(rest: list[str]) -> tuple[str, list[str], list[str]]:
    """`git tag <rest>` as (the short letters given, the long option names given, the plain words). An option's
    value is none of them (#529, D-236): `git tag -m -l v1.0` makes `v1.0` with the message `-l`, and was read as a
    listing because `-l` was taken from every option word, the value too. `-n<num>` carries its number."""
    letters, longs, names = "", [], []
    k = 0
    while k < len(rest):
        a = rest[k]
        k += 1
        if a == "--":
            names += rest[k:]
            break
        if a.startswith("--"):
            name, eq, _ = a.partition("=")
            longs.append(name)
            if not eq and any(_unique(name, w, GIT_LONG["tag"]) for w in TAG_LONG_VALUED):
                k += 1
        elif a.startswith("-") and len(a) > 1:
            for j, ch in enumerate(a[1:], 1):
                letters += ch
                if ch in TAG_SHORT_VALUED:
                    k += 0 if a[j + 1:] else 1
                    break
                if ch == "n":
                    break
        else:
            names.append(a)
    return letters, longs, names


def _moves_owner_ref(sub: str, rest: list[str], letters: str, given: Callable[..., bool]) -> str | None:
    """#410 (D-223 clause 5): `git tag` making, forcing or deleting a `v*` tag, or one it cannot read, but listing
    and `-v`; `git update-ref` naming a ref under `refs/tags/v` or `refs/replace/`; and a fetch, pull or push
    refspec whose destination may land under `refs/replace/` (#529: `refs/*:refs/*`). The listing and verifying
    options are read from `_tag_words`, never from an option's value (#529); a value of an option it does not know
    is read as the tag's name, so the rule errs closed there."""
    if sub == "tag":
        letters, longs, names = _tag_words(rest)

        def said(*wanted: str) -> bool:
            return any(_unique(a, w, GIT_LONG["tag"]) for a in longs for w in wanted)

        deleting = "d" in letters or said("--delete")
        listing = not names or any(ch in letters for ch in "lnv") or said(
            "--list", "--verify", "--contains", "--no-contains", "--merged", "--no-merged", "--points-at")
        if not deleting and listing:
            return None
        named = names if deleting else names[:1]
        return OWNER_REF if any(n.casefold().startswith("v") or "$" in n or "`" in n for n in named) else None
    if sub == "update-ref":
        return OWNER_REF if any(_owner_ref(r) for r in _plain(rest, {"-m"})) else None
    if sub in ("fetch", "pull", "push"):
        # Every plain word, the remote's too: none is named under `refs/replace/`, and `--repo=<it>` leaves the
        # first word a refspec.
        specs = _plain(rest, FETCH_VALUED if sub != "push" else {"--receive-pack", "--exec", "--repo", "-o",
                                                                   "--push-option"})
        # #529: a pattern that may land there too (`refs/*:refs/*`); a fetch's spec with no `:` stores nothing.
        return OWNER_REF if any(_owner_ref(sp.rsplit(":", 1)[-1], ("replace/",)) or (
            (":" in sp or sub == "push") and _lands(sp.rsplit(":", 1)[-1], (), ("refs/replace/",))) for sp in specs) else None
    return None


def _unread_git(args: list[str], at: int, unread: set[int]) -> str | None:
    """#344: a git word this does not read (`_unread_word`) where it may be `--no-verify`, `--force`, `--hard`, the
    protected branch or an owner's path: the subcommand itself, a `-c` setting, or any word of a subcommand in
    GIT_UNREAD_SUBS (a global option, `-C` or `--git-dir`, there too) but a message's (`-m "$(cat msg)"`)."""
    if not unread:
        return None
    sub = args[at]
    if at in unread:
        return UNREAD_GIT.format(sub=sub, word=sub)
    for k in range(at):
        if k in unread and (args[k - 1:k] == ["-c"] or sub.lower() in GIT_UNREAD_SUBS):
            return UNREAD_GIT.format(sub=sub, word=args[k])
    if sub.lower() not in GIT_UNREAD_SUBS or (sub == "rm" and "--cached" in args[at:]):
        return None   # `git rm --cached` leaves the work tree as it is
    for k in range(at + 1, len(args)):
        before = args[k - 1]
        message = before in GIT_MESSAGE or bool(re.match(r"^-[A-Za-z]*[mF]$", before)) or (
            args[k].split("=", 1)[0] in GIT_MESSAGE and "=" in args[k])
        if k in unread and not message:
            return UNREAD_GIT.format(sub=sub, word=args[k])
    return None


def _judge_git(args: list[str], behind_xargs: bool, depth: int = 0,  # noqa: C901 -- one branch per subcommand
               inherited: dict[str, str] | None = None, unread_at: set[int] | None = None) -> str | None:
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
                if (why := (_judge_alias(value, depth) if key.lower().startswith("alias.") else
                            _judge_code(value, depth))):
                    return why
            if key.lower() == TEMPLATE_KEY:
                return TEMPLATE   # #320: `git -c init.templateDir=... init`
            if REMOTE_KEY.match(key):
                return PROTECTED_REF   # #318: `git -c remote.origin.fetch=... fetch`
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
        return _judge_git(expanded + rest, behind_xargs, depth + 1, aliases,
                          {len(expanded) + k - i - 1 for k in (unread_at or set()) if k > i})
    ended = rest.index("--") if "--" in rest else len(rest)
    options = [a for a in rest[:ended] if a.startswith("-")]
    longs = [a for a in options if a.startswith("--")]
    letters = "".join(a[1:] for a in options if not a.startswith("--"))
    known = GIT_LONG.get(sub, [])

    def given(*wanted: str) -> bool:
        return any(_unique(a, w, known) for a in longs for w in wanted)

    # refused: a skipped hook -- `--no-verify` in any prefix git reads as it (`--no-veri`), on any subcommand
    if any(_skips_hooks(a) for a in longs) or (sub == "commit" and "n" in letters):
        return NO_VERIFY
    if sub == "config" and _redirects_hooks(rest):
        return NO_VERIFY
    if sub == "config" and _edits_config(rest):
        return CONFIG_EDIT
    # #320: `git init --template=<dir>` and `git clone --tem=<dir>` (git reads a unique prefix) copy that directory's
    # hooks and config in.
    if sub in ("init", "clone") and any(len(a.split("=", 1)[0]) >= 3 and "--template".startswith(a.split("=", 1)[0])
                                        for a in longs):
        return TEMPLATE
    # #318: the refs the deploy gate reads its base from -- `main`, `origin/main`, `origin/HEAD` -- are not moved.
    if (why := _moves_default(sub, rest, letters, given)):
        return why
    # #410: a `v*` tag and a `refs/replace/` ref are the owner's.
    if (why := _moves_owner_ref(sub, rest, letters, given)):
        return why
    # #317: a worktree with uncommitted work is not moved out from under the rule below (`git worktree move <dirty>
    # /tmp/x && rm -rf /tmp/x`): it is judged as its removal is.
    if sub == "worktree" and [a for a in rest if not a.startswith("-")][:1] == ["move"]:
        after = [a for a in rest[rest.index("move") + 1:] if not a.startswith("-")]
        if (why := _judge_worktree_remove(after[:1], base, behind_xargs)):
            return why
    if sub == "worktree" and [a for a in rest if not a.startswith("-")][:1] == ["remove"]:
        after = rest[rest.index("remove") + 1:]
        cut = after.index("--") if "--" in after else len(after)
        removed = [a for a in after[:cut] if not a.startswith("-")] + after[cut + 1:]
        if (why := _judge_worktree_remove(removed, base, behind_xargs)):
            return why
    if sub == "config" and _renames_remote(rest):
        return PROTECTED_REF   # #533: `git config --rename-section remote.evil remote.origin`
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
        elif CODE_KEY.match(key) and (why := _judge_code(value, depth)):
            return why   # `git config core.pager 'rm -rf ~'` runs on the next `git log`
        elif key.lower() == TEMPLATE_KEY:
            return TEMPLATE   # #320
        elif REMOTE_KEY.match(key):
            return PROTECTED_REF   # #318: origin's URL or refspec decides what the next fetch puts in origin/main
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
        # #287's P5: `git rm -r "$(pwd)"` -- a path this cannot read may be the work tree (`pwd` can be redefined).
        if recursive and not cached and (hit := next((w.text for w in moved if "$" in w.text or "`" in w.text), None)):
            return PROJECT_TREE.format(target=hit)
        if recursive and not cached and (hit := _project_tree(moved, base)):
            return PROJECT_TREE.format(target=hit)
    # v7.3: the repository's default branch by any name (`develop` too), beside #533's `_moves_default`.
    if sub == "update-ref":
        refs = [a for a in rest if not a.startswith("-")]
        if refs and {r.removeprefix("refs/").removeprefix("heads/") for r in refs} & _protected_branches():
            return PROTECTED_REF
    if sub == "push":
        if _husky_off():
            return HUSKY_OFF
        refs = [a for a in rest if not a.startswith("-")]
        forced = "f" in letters or given("--force", "--force-with-lease", "--force-if-includes")
        if forced or given("--mirror") or any(ref.startswith("+") for ref in refs):
            return DESTRUCTIVE
        targets = {ref.split(":")[-1].removeprefix("refs/").removeprefix("heads/") for ref in refs}
        if behind_xargs or given("--all", "--branches") or (targets and _protected_branches() & targets):
            return PROTECTED_PUSH
        if any(":" in ref and (_default_ref(dst := ref.rsplit(":", 1)[1]) or _lands(dst, GATE_REFS, GATE_UNDER))
               for ref in refs[1:]):
            return PROTECTED_REF   # #318, #533: `git push . HEAD:refs/remotes/origin/main`, `git push . 'refs/*:refs/*'`
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
    # #344, after every rule that names what it found: a word this cannot read, where it may be any of them.
    return _unread_git(args, i, unread_at or set())


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
    # An upgrade's unresolved three-way merge left conflict markers in the gate, and every Bash call came back
    # as a raw IndentationError (Project-J, v7.2). Say what it is, and that the Edit tool still works.
    for name in ("deploy_gate.py", "brief_fields.py"):
        path = os.path.join(OWN, "scripts", name)
        try:
            with open(path, "rb") as f:
                text = source if name == "deploy_gate.py" else f.read(1 << 20).decode("utf-8", "replace")
        except OSError:
            continue
        marker = CONFLICT_MARKER.search(text)
        if marker:
            line = text.count("\n", 0, marker.start()) + 1
            return GATE_CONFLICT.format(name=name, line=line)
    protocol = JUDGE_LINE.search(source)
    level = 0 if protocol is None else int(protocol.group(1)) if protocol.group(1) is not None else 1
    if level < 1:
        return GATE_OLD.format(gate=gate, need=1, why="read `--judge` as a command and pass every deploy")
    if foreign and level < 2:
        return GATE_OLD.format(gate=gate, need=2, why=f"judge {root}, another repository, by its own verdicts")
    # A4: `gh run rerun` runs its run's workflow again, so where the brief declares a `gh workflow run` deploy it
    # is also handed over as `gh workflow run <file>` and `<name>`: a rerun of the CI tests is not a deploy, one
    # of the deploy workflow is (Project-J's own rule refused both). A run gh cannot place there is refused.
    reruns = [r for words in candidates if (r := _gh_rerun(words)) and (r[0] or r[1])]   # none: gh reruns nothing
    if reruns and _declares_workflow(root):
        candidates = list(candidates)
        for run, job, repo in reruns:
            names, why = _rerun_workflow(run, job, repo, root)
            if why:
                return RERUN_UNREAD.format(run=run or f"--job {job}", root=root, why=why)
            candidates += [["gh", "workflow", "run", n] for n in names if ["gh", "workflow", "run", n] not in candidates]
    payload = json.dumps({"cwd": cwd, "commands": candidates, **({"foreign": True} if foreign else {})})
    try:
        r = subprocess.run([sys.executable, "-I", "-B", gate, "--judge"], input=payload.encode("utf-8"),
                           capture_output=True, cwd=root, timeout=20)
    except (OSError, subprocess.SubprocessError) as error:
        return f"BLOCKED: deploy gate -- scripts/deploy_gate.py could not run ({type(error).__name__}: {error})."
    if r.returncode == 0:
        return None
    message = r.stderr.decode("utf-8", "replace").strip()
    if message and not message.startswith("BLOCKED:"):
        last = message.splitlines()[-1][:200]
        return (f"BLOCKED: deploy gate -- scripts/deploy_gate.py failed (exit {r.returncode}): {last}. "
                "Fix the script (the Edit tool still works); the guard never skips this check.")
    return message or f"BLOCKED: deploy gate -- scripts/deploy_gate.py exited {r.returncode} and gave no reason."


def _gh_rerun(words: list[str]) -> tuple[str | None, str | None, str | None] | None:
    """(the run, the `--job`, the `-R` repository) of a `gh ... run rerun` word list, flags anywhere; None for any
    other list."""
    if not words or os.path.basename(words[0]).lower() != "gh":
        return None
    plain: list[str] = []
    found: dict[str, str | None] = {"repo": None, "job": None}
    i = 1
    while i < len(words):
        name, eq, value = words[i].partition("=")
        if words[i].startswith("-") and len(words[i]) > 1:
            valued = name in GH_VALUED or name in ("-j", "--job")
            if valued and not eq:
                value = words[i + 1] if i + 1 < len(words) else ""
            if name in ("-R", "--repo", "-j", "--job"):
                found["repo" if name in ("-R", "--repo") else "job"] = value
            i += 2 if valued and not eq else 1
            continue
        plain.append(words[i])
        i += 1
    if plain[:2] != ["run", "rerun"]:
        return None
    return (plain[2] if len(plain) > 2 else None), found["job"], found["repo"]


def _declares_workflow(root: str) -> bool:
    """Whether the brief of `root` may declare a `gh workflow run` deploy: its text, quotes and backticks removed,
    has `gh` and then `workflow run` on one line. Only then is a rerun's workflow looked up."""
    try:
        with open(os.path.join(root, "docs", "project-brief.md"), "rb") as f:
            text = f.read(1 << 20).decode("utf-8", "replace")
    except OSError:
        return False
    return re.search(r"\bgh\b.*\bworkflow\s+run\b", re.sub(r"[`'\"]", "", text).lower()) is not None


#: A4: the workflows of the runs this call reruns, by (run, job, repository): looked up once.
RERUNS: dict[tuple, tuple[list[str], str | None]] = {}
RERUN_UNREAD = ("BLOCKED: deploy gate -- `gh run rerun {run}` runs that run's workflow again, {root}'s brief declares "
                "a `gh workflow run` deploy, and gh could not say which workflow the run is ({why}). Check "
                "`gh auth status` and the network, then try again.")


def _rerun_workflow(run: str | None, job: str | None, repo: str | None, root: str) -> tuple[list[str], str | None]:
    """(the workflow file name and the workflow name of the run a rerun names, or why gh could not say): one
    `gh api` call, two for a `--job`."""
    key = (run, job, repo)
    if key in RERUNS:
        return RERUNS[key]
    base = f"repos/{repo}" if repo and re.fullmatch(r"[\w.-]+/[\w.-]+", repo) else "repos/{owner}/{repo}"

    def api(path: str, jq: str) -> tuple[str, str | None]:
        try:
            r = subprocess.run(["gh", "api", f"{base}/{path}", "--jq", jq], capture_output=True, cwd=root, timeout=8)
        except (OSError, subprocess.SubprocessError) as error:
            return "", f"gh could not run: {type(error).__name__}"
        err = r.stderr.decode("utf-8", "replace").strip().splitlines()
        return r.stdout.decode("utf-8", "replace").strip(), None if r.returncode == 0 else (
            err[-1][:120] if err else f"gh exited {r.returncode}")

    why = None
    if job is not None:
        run, why = api(f"actions/jobs/{job}", ".run_id") if re.fullmatch(r"[0-9]+", job) else ("", f"job `{job}`")
    if why is None and not re.fullmatch(r"[0-9]+", run or ""):
        why = f"`{run}` is not a run number"
    out, why = (api(f"actions/runs/{run}", '.path + "\\t" + .name') if why is None else ("", why))
    path, _, name = out.partition("\t")
    names = [n for n in dict.fromkeys((os.path.basename(path.strip()), name.strip())) if n]
    RERUNS[key] = (names, why or (None if names else "gh named no workflow"))
    return RERUNS[key]


# --- the hook -----------------------------------------------------------------------------------------

def _expired() -> None:
    """The guard's time budget: a thread, so it holds where SIGALRM does not exist. It cannot stop a long call
    into C that holds the interpreter; the hook's timeout bounds that."""
    sys.stderr.buffer.write(BUDGET.format(s=DEADLINE_S).encode() + b"\n")
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
    # Lower-cased (a case-insensitive disk opens DEVFLOW-GATE-OK as the stamp), quotes, backslashes and `$`
    # removed (`devflow-gate-o'k'`, `$'\x6b'`); the prefix catches a brace expansion. A name built at run
    # time is in "Not held". In a call that names the stamp, each command must only read it (A2, `_stamp_ok`).
    def ansi_c(m: re.Match) -> str:     # `$'\055'` is `-` to the shell: decode before reading
        try:
            return codecs.decode(m.group(1), "unicode_escape")
        except (UnicodeDecodeError, ValueError):
            return m.group(1)
    flat = re.sub(r"[\"'\\$]", "", re.sub(r"\$'((?:[^'\\]|\\.)*)'", ansi_c, command)).lower()
    SEEN["stamp"] = "devflow-gate" in flat or "gate_stamp" in flat
    if re.search(r"\b(gnu)?makeflags\s*\+?=|\bmflags\s*\+?=", flat):
        return MAKE_FLAGS
    # And the builtins that assign without `=` (`read MAKELEVEL <<< 1`, `printf -v`, `declare`): v7.2.1, review.
    if re.search(r"\bmakelevel\s*\+?=", flat) or re.search(
            r"(^|[;&|\n(`{]|\bthen|\bdo|\belse)\s*(read|printf\s+-v|declare|typeset|local|mapfile|readarray)\b"
            r"[^;&|\n]*\bmakelevel\b", flat):
        return MAKE_LEVEL
    REACHED.clear()
    CANDIDATES.clear()
    TOPS.clear()
    WALK["left"] = WALK_S
    STATUS["left"] = STATUS_S
    # A3: one pass per word of each literal `for` loop, every combination; past MAX_PASSES, one pass with
    # those loops' variables unknown. Places reached and deploy candidates gather across the passes. A pass
    # branches on every loop it meets past its pick, so a loop met only under another's word -- held in a
    # loop variable and run by `eval` -- is walked too (v7.3 review, R1). The budgets above are the call's,
    # shared by every pass and world.
    todo, passes, why = [()], 0, None
    while todo and why is None:
        pick = todo.pop()
        passes += 1
        if passes > MAX_PASSES:
            why = _judge_pass(command, cwd, None)[1]
            break
        sizes, why = _judge_pass(command, cwd, pick)
        full = pick + (0,) * (len(sizes) - len(pick))
        todo += [full[:j] + (k,) for j in range(len(pick), len(sizes)) for k in range(1, sizes[j])]
    return why or judge_deploy(list(CANDIDATES), cwd)


def _judge_pass(command: str, cwd: str, pick: tuple | None) -> tuple[list[int], str | None]:
    """One reading of the call from its start, each literal `for` loop's variable at the word `pick` gives it
    (None: unknown): (how many words each loop had, why it is refused or None). #287: the first world, then the
    second when they differ (WORLD); a loop met in either world is branched on."""
    WORLD["forked"] = False
    sizes: list[int] = []
    for skip in (False, True):
        if skip and not WORLD["forked"]:
            break
        WORLD["skip"] = skip
        CWD["dir"] = cwd
        CALL["text"] = command
        HERE["dirs"] = [cwd]
        SEEN.update(repeats=False, cdpath=False, links=False, home_used=False,
                    # `HOME` written anywhere but as `$HOME`: an editor or pager path through `$HOME` is unread.
                    home=bool(re.search(r"(?<![\w$])HOME\b", re.sub(r"\$\{?HOME\b", "", command))))
        NAMEREF.clear()
        FLOW["maybe"] = FLOW["scoped"] = False
        EVALED["on"] = 0
        SCOPE.clear()
        REMOTE["on"] = 0
        FOLLOWED["dirs"] = list(dict.fromkeys([os.path.normpath(os.path.abspath(cwd)), os.path.realpath(cwd)]))
        FOLLOWED["over"] = []
        TRUST["TMPDIR"] = not TMPDIR_NAMED.search(command)   # B1: `unset TMPDIR`, `local TMPDIR`, `read TMPDIR`
        TRUST["mktemp"] = not MKTEMP_DEFINED.search(command)
        FORS.update(sizes=[], pick=pick or (), unknown=pick is None)
        why = judge_text(command)
        if len(FORS["sizes"]) > len(sizes):
            sizes = list(FORS["sizes"])
        if why:
            return sizes, why
    return sizes, None


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
