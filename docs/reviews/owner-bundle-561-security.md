---
record_type: review
id: owner-bundle-561-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — owner bundle for #561

**Reviewer:** Security-Reviewer subagent (an owner bundle owes a review before it is applied, `scripts/owner_bundle.py`)
**Independent:** yes. This seat did not write the patch or any of its tests. It read the patch, worked in its own exports of `fe2542b` (`git archive`, base and patched, no git work tree), and judged every command with both guards side by side.
**Date:** 2026-11-02
**Reviewed patch:** 4a1a5ac20332fecb15adf0a7bd4004bbcbbe53ca611ea7191b5fb1f5d96154f0
**Round 1 patch:** 67ba24e01d574e2b87f4139c0523855e4b458f3682c3138264a4b3a4f52794de (BLOCKING; see the round 1 findings below)
**Reviewed head:** fe2542b8b92645e434128463ab5ac5de0a8e707c
**Risk tier:** HIGH. The patch changes the Bash guard, which is the fail-closed control behind every agent-side refusal in `permission-matrix.md` §5: no push to the protected branch, no destructive git, no write into the owner's directories. It also changes the guard's pin in `.claude/settings.json` and `.codex/hooks.json`.

## Verdict
MINOR

Round 2 is MINOR; its section is at the end of this file. The findings below are round 1's, made on patch `67ba24e0…`.

## Findings

### BLOCKING

- **B1** `.claude/hooks/bash_guard.py:1729-1735` (patched): the new split makes the guard refuse less than it does at `fe2542b`. It reads past `-c` and `-C` values and refuses less on protected-branch pushes, destructive git, PR merges and owner-directory writes. This is an OWASP A04 (insecure design) flaw in a safety control.
  The loop takes `_expand(w.text)` for every `bare` word after the program and splits it with Python's `str.split()` wherever `\s` matches. The trouble is that `w.text` is the whole word. A blank can come from three places where the shell keeps the word whole:
  (a) A quoted part next to the expansion. In `$k"=a b"` the shell sees one word, `user.name=a b`. `bash -c 'k=user.name; printf "[%s]" git -c $k"=a b" push origin main'` prints `[git][-c][user.name=a b][push][origin][main]`.
  (b) A variable in a shell that does not split. The agent's Bash tool on this machine runs `/bin/zsh`, measured. zsh does not split an unquoted `$k`: with `k='user.name=a b'`, `zsh -c 'printf "[%s]" git -c $k push origin main'` prints the same six words.
  (c) Whitespace outside the default `IFS`: `\f`, `\v`, `U+00A0`, which `str.split()` splits on and bash does not.
  In each case the split word moves every later position. The tail of a `-c` or `-C` value is read as git's subcommand, so the real subcommand is never judged.
  Evidence: every command below was judged in-process by both guards; base refuses it and the patch allows it. Two of them, the zsh `push origin main` form and the quoted `reset --hard` form, were also run as Claude Code runs them, through each tree's pinned `Bash` hook command: base exits 2, patched exits 0.
  - `k=user.name; git -c $k"=a b" push origin main`, and the same with `reset --hard HEAD~1`, `push --force origin x`, `branch -D main`, `checkout -- .`, `update-ref -d refs/heads/main`, `worktree add -b main /tmp/w HEAD`
  - `k='user.name=a b'; git -c $k push origin main`, plus `reset --hard` and `clean -fdx` (zsh form)
  - `k=$'user.name=a\fb'; git -c $k push origin main`
  - `p='./a b'; git -C $p push origin main`
  - `r=o; gh -R $r"/a b" pr merge 5`
  - `d=.; cp x $d"/.claude/a b"` and `d=.; cp x $d"/.githooks/a b"` (both are owner-directory writes)
  - `k=user.name; git -c $k"=a b" tag main` (the patch's own new rule)

  Failure scenario: an agent, or a prompt-injected agent, runs `k=user.name; git -c $k"=a b" push origin main` or `... reset --hard`. The guard allows it, and the default branch moves or uncommitted work is lost. Today's guard refuses both.
  Remedy: make the split unable to lower a verdict. Judge the command once as written and once split, and refuse if either reading refuses, the way `_defaults` judges variants. Split only on `" \t\n"`. Add the commands above to `tests/unit/test_bash_guard_bounds.py`, plus a differential test that loads the base guard and asserts no command in the corpus goes from refused to allowed.

- **B2** `.claude/hooks/bash_guard.py:1729-1735` together with the `SETTERS` branch at `:1749`: in bash, `export`, `declare`, `readonly`, `local` and `typeset` keep an assignment argument whole. The patch splits it anyway, because every word at `k >= start` is split, including the words after `export`. The variable is then read as holding only the first piece. That is the M14 class this patch closes, reopened for another shape, and it loses a refusal the base guard had.
  Evidence: `bash -c 'v="/tmp/x/a /Users/z"; export d=$v; printf "[%s]" $d'` prints `[/tmp/x/a][/Users/z]`: `d` held the whole value, and only the use splits it. Base refuses, patched allows:
  - `bash -c 'v="/tmp/x/a $HOME"; export d=$v; rm -rf $d'`
  - the same with `declare d=$v` and with `readonly d=$v`

  Without `export`, the plain-assignment form is refused by both guards. `bash -c 'v="fix/a main"; export b=$v; git push origin --delete $b'` is allowed by both, so M14's push shape is still open behind `export`.
  Failure scenario: `bash -c 'v="/tmp/x/a $HOME"; export d=$v; rm -rf $d'` removes the home directory.
  Remedy: do not split an assignment-shaped word after a `SETTERS` program. B1's both-readings judgement also covers this. Add the four commands above as bounds tests.

### MINOR

- **M1** `.claude/hooks/bash_guard.py:3560-3564` and `:3627-3644`: the new shadow-tag rule (#554's R3) holds on every spelling this seat tried for `git tag`, `git update-ref` and `git push`. That covers `git tag -- main`, `MAIN`, `Main`, `ma''in`, `\main`, `ma\in`, `t=main; git tag $t`, `refs/tags/./main`, `./main`, `heads/main`, `refs/remotes/origin/HEAD`, `git -c user.name=x tag main`, `git -C sub tag main`, `-a/-s/-u/-F/-m/--message=/--file=/--cleanup=`, `git push origin main:refs/tags/x/main`, `HEAD:refs/tags//main`, `tag MAIN`, `tag -- main`, `+HEAD:refs/tags/main`, and `update-ref` under `refs/tags/` (already refused by the protected-ref rule). `git tag 'origin/main^{}'` is allowed, and git itself rejects that name.
  The rule does not reach three ways to make the same tag:
  - brace expansion: `git tag {main,HEAD}` becomes `git tag main HEAD`
  - a fetch whose destination is a pattern: `git fetch origin 'refs/heads/*:refs/tags/*'` makes `refs/tags/main` from origin's `main`
  - a plain file write: `echo <sha> > .git/refs/tags/main`

  Base allows all three as well, so none of them is a regression. The guard's docstring lists braces in arguments and `.git/refs/tags/` writes as limits; the fetch pattern is not listed, and it is the one an agent could hit by accident. Remedy: refuse a fetch or pull refspec whose destination may land under `refs/tags/` with a last part of `main`, `master` or `head`, the same way `_lands` handles `refs/replace/`. Or list it with the limits.

- **M2** `.claude/hooks/bash_guard.py:576`, `:630-632`: two messages are off.
  - A write into `.codex/` is refused with `OWNERS`, which still says ".claude/ and .githooks/ hold the owner's hooks". `rm -rf .codex` and `mv ... .codex` get that text.
  - `SHADOW_REF` says "deleting one is allowed", but `git push origin :refs/tags/main` is refused with that same message. Base refused it too, with the protected-ref message. Only a local `git tag -d` is allowed.

  Both are wording fixes and do not change any security outcome.

### PASS

- **The pin:** `shasum -a 256` of the patched `.claude/hooks/bash_guard.py` is `70aa67bb02f5182c1e1641e933f5aa41b3f245756a4630390cbded52b2fe1300`. That value appears in both pinned commands of `.claude/settings.json` (Write/Edit and Bash) and in `.codex/hooks.json`, and no other value is left there. The base guard's sha256 is `c085b476…a57a38af26`, matching the old pin. The patched tree's conformance run goes through its own pinned hook command, which shows the pin and the guard agree. `owner_bundle.py apply` re-pins as well.
- **The earlier attempts are gone:** across the whole file, the patched guard differs from `fe2542b`'s by 38 lines, all inside the five hunks of the patch. `_for_value` (`:1572`) and `_expand` (`:1630`) are byte-identical to base.
- **M15:** `.codex` is in `OWNED` (`:554`). `echo x > .codex/hooks.json`, `cp x .codex/hooks.json` and `rm -rf .codex` are refused, and so is the Write/Edit hook on `.codex/hooks.json`.
- **M14's stated shapes are refused:** `bash -c 'for d in "/tmp/x/a <home>"; do rm -rf $d; done'`, its `sh -c` form, `for b in "fix/a main"; do git push origin --delete $b; done`, `bash -c 'd="/tmp/x/a <home>"; rm -rf $d'` and `d="/tmp/x/a ~"; rm -rf $d`.
- **Correct readings that still hold:**
  - `"$d"` stays one word: `d="/tmp/x/a b"; rm -rf "$d"` is allowed.
  - `"$@"` is not split.
  - Assignments before the program are not split (`k >= start`).
  - `git commit -m $m` and `git add $f` with blanks stay allowed.
  - Scratch loops without blanks stay allowed.
- **Differential runs:**
  - Over all 938 judge calls in `tests/unit/test_bash_guard_bounds.py` (base and patched called with the same payload by a pytest plugin): 0 refused at base and allowed by the patch. 18 are refused only by the patch: the new cases, plus 3 artifacts of monkeypatched attributes the plugin did not copy to base.
  - `conformance/test-bash-guard.py`: 838 calls, 0 wrong verdicts on both base and patched exports, the same corpus.
  - `tests/unit/test_bash_guard_bounds.py`: 859 passed on base, 884 passed on the patched export.

  None of these corpora contains a word that mixes an expansion with a quoted blank, which is why B1 and B2 passed every gate.

## Gates passed
- [ ] Secret scan green (`make secrets` on the release commit): not run by this seat. The patch adds no literal credential; the 64-hex values are guard pins.
- [ ] `make deps` (pip-audit) green: not applicable, no dependency changes.
- [x] `make slopsquat` green: no new import (the guard is stdlib only).
- [ ] Default-deny preserved for new external surfaces: **no**. B1 and B2 lower refusals the base guard made.
- [ ] Permission-matrix not violated: **no**. §5's refusals (protected-branch push, destructive git, owner-directory writes) can be bypassed under the patched guard.
- [x] Prompt-injection hygiene: the guard reads command text as data only.
- [x] Auth/PII checks + human review trigger fired: no auth/PII/payment/migration path. The owner applies the bundle by hand.
- [x] SAST: no new subprocess, eval or file write in the patched lines.

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #561 M14 → `tests/unit/test_bash_guard_bounds.py` (patched) `test_a_word_holding_a_blank_is_not_one_argument`; refused by the patched guard, but see B1 and B2
- #561 M15 → `test_a_write_into_a_work_trees_codex_is_refused`, `test_the_write_and_edit_hook_refuses_codex`; `bash_guard.py:554`
- #554 R3 → `test_a_tag_named_like_the_default_branch_is_refused`, `test_other_tags_and_deleting_a_shadowing_one_are_allowed`; `bash_guard.py:3560`, `:3627`, `:3631`, `:3641`

## Risks queued
- **R1** A command that sets `IFS` changes what the shell splits, and the guard lists `IFS` as a limit. Under the patch, `IFS=; c="git push origin main"; bash -c $c` and `IFS=; d="/tmp/a b"; git -C $d push origin main` go from refused to allowed. B1's remedy (refuse if either reading refuses) closes this too.
- **R2** Every new bundle of the guard should carry the differential check this seat ran: base and patched guards over the bounds and conformance corpora, failing on any refused-to-allowed change. The 884 and 838 green results did not catch B1 or B2. A `conformance/` case that loads the protected base's guard would make "never refuses less" a gate rather than a reviewer's habit.
- **R3** Empty probe directories are left at `~/.srprobe561repo` (`.git`, `.claude/hooks`, `.githooks`, `.codex`, `sub`; no files). The guard rightly refuses to let this seat remove a tree holding `.claude/`. The owner removes it with `rm -r ~/.srprobe561repo`.

## Round 2

**Patch:** `4a1a5ac20332fecb15adf0a7bd4004bbcbbe53ca611ea7191b5fb1f5d96154f0`, still against `fe2542b8b92645e434128463ab5ac5de0a8e707c`. This seat built its own `git archive` export of `fe2542b`, applied the patch there, and compared it with round 1's base export.

**What changed:**
- `_judge_command_once` is the base's again: only the #68 program-position split remains.
- The split reading is now an extra judgement. In `judge_command`'s variant loop (patched `bash_guard.py:1700-1713`), `_split_variant` (`:1737-1756`) splits each `bare` word after the program on `[ \t\n]`. It returns None after `SETTERS | {alias, let}`. The split command is judged between `_snapshot()` and `_restore()` (`:1719-1735`), and then the command is judged as written, exactly as at base.
- The split can therefore only add a refusal. It cannot remove one, and the variable values it reads are dropped before the as-written judgement.

**The pin:** sha256 of the patched guard is `69b57281bd577a3e1271d0f82d89ccd95a897d4f4d331fed7f08fbe6617cd582`. It is the only 64-hex value in both pinned commands of `.claude/settings.json` and in `.codex/hooks.json`. This seat's export and the coordinator's `g561/new` have byte-identical `.claude/` trees.

### Dispositions

- **B1: fixed.** Every round 1 bypass is refused again, with base's reason:
  - `git -c $k"=a b" push origin main`, and the same with `reset --hard`, `push --force`, `branch -D main`, `checkout -- .`, `update-ref -d refs/heads/main`, `worktree add -b main` and `push origin HEAD:main`
  - the zsh forms `k='user.name=a b'; git -c $k push|reset --hard|branch -D|clean -fdx`
  - `\f`, `\v` and U+00A0 in the value
  - `git -C $p push origin main`
  - `gh -R $r"/a b" pr merge 5`
  - `cp x $d"/.claude/a b"`

  `git -c $k"=a b" tag main` is now refused by the new rule. Through each tree's pinned `Bash` hook command, the zsh `push origin main` form and the quoted `reset --hard` form exit 2 on both base and patched; in round 1 the patched tree exited 0.
- **B2: fixed.** `bash -c 'v="/tmp/x/a $HOME"; export|declare|readonly d=$v; rm -rf $d'` is refused, as at base. The split reading's state is restored before the as-written reading, so `d` keeps its whole value. Round 1's open M14 shape behind `export` is closed too: `v="fix/a main"; export b=$v; git push origin --delete $b` and the `bash -c` forms with `export` and with `local` are now refused, and base allowed them.
- **R1 (`IFS=`): fixed by the same construction.** `IFS=; d="/tmp/a b"; git -C $d push origin main` and `IFS=; c="git push origin main"; bash -c $c` are refused, as at base.
- **M2, second half: fixed.** `SHADOW_REF` now says "deleting one locally (`git tag -d`) is allowed" (`:631`).
- **M2, first half: accepted as is.** `OWNERS` still names only `.claude/` and `.githooks/`. The refusal itself covers `.codex/` (`OWNED` at `:555`), and 50 bounds tests pin the message text. This is wording only, with no change to any security outcome.
- **M1: still open, not a regression.** Base allows all three spellings and the patch still allows them: `git tag {main,HEAD}`, `git fetch origin 'refs/heads/*:refs/tags/*'`, and `echo <sha> > .git/refs/tags/main`. This stays MINOR and should be filed as an issue so the fetch-pattern case gets a rule or a named limit.
- **R2: met in substance.** The probes are now `test_the_split_reading_never_refuses_less`. A conformance check that loads the protected base's guard is still only a reviewer's habit, so R2 stays queued.
- **R3:** still open. `~/.srprobe561repo` remains, holding empty directories only.

### Round 2 evidence

- **Snapshot coverage:** every module-level dict, list or set the guard writes at run time was checked against `_STATE`. Outside it, `WALK["left"]` and `STATUS["left"]` are time budgets, and spending them fails closed: `_Unwalked` at `:2513`, `UNMEASURED_WORKTREE` when `_git_ask` returns None at `:2852-2853`. `RERUNS` is a cache keyed by its inputs, and `CALL` is set once per call. So the split reading can make the as-written judgement refuse more, never less.
- **This seat's round 1 corpora (`c1.txt` to `c7.txt`, 204 commands) plus 9 state-interplay probes:**
  - 0 commands refused at base and allowed by the patch
  - 63 + 3 commands refused only by the patch: the shadow-tag cases, `.codex` writes, M14 shapes, and the over-refusals below
  - Correct readings still allowed:
    - `"$d"` and `"$@"`, when they do not hold a refusable target
    - `for d in "/tmp/x/a /tmp/x/b"; do rm -rf $d; done`
    - `d="/tmp/x/a b"; rm -rf "$d"`
    - `git commit -m $m` and `git add $f` with blanks
    - `x="x main"; git tag $x`, which makes tag `x` at `main`
- **Bounds differential:** the base-vs-patched pytest plugin ran over all 945 judge calls of the patched `tests/unit/test_bash_guard_bounds.py`, with 891 tests passing. Results: 0 refused at base and allowed by the patch, 20 refused only by the patch. Three of those 20 are round 1's artifacts (monkeypatched attributes the plugin does not copy to base); the rest are the new cases.
- **Conformance:** `conformance/test-bash-guard.py` on the patched export: 838 calls, 0 wrong verdicts.

### MINOR (round 2)

- **M3** `bash_guard.py:1748-1754`: the split reading also refuses some commands whose quoted blank the shell keeps inside one word, because it splits the whole word text:
  - `d=/tmp/x; rm -rf $d"/a b"`, which removes a single scratch path
  - `b=fix/a; git push origin $b" main"`

  This fails closed. It is a false positive an agent avoids by quoting the whole word (`"$d/a b"`). It is noted as a known cost, not as a defect to fix before apply.

### Gates (round 2)
- [x] Default-deny preserved: the split reading only adds refusals, by construction and as measured.
- [x] Permission-matrix not violated: every §5 refusal of `fe2542b` holds under the patch.
- [x] `make slopsquat`: one new import, `copy`, from the standard library.
- [x] SAST: no new subprocess, eval or file write. `copy.deepcopy` runs only on the guard's own state.
- [ ] Secret scan: not run by this seat. The patch holds no credential; the 64-hex values are guard pins.
