#!/usr/bin/env bash
# Resolve every `uses: owner/repo@ref` in .github/workflows/ to an immutable commit SHA.
#
# WHY. A tag is mutable by whoever owns the action's repository. `gitleaks/gitleaks-action@v2` is the
# secret scanner; `anthropics/claude-code-action@v1` sits beside `ANTHROPIC_API_KEY` and
# `contents: write`. V4C-44 has required pinning since v4.1 and nothing enforced it.
#
# TWO BUGS THIS FILE IS THE REPAIR OF, both in its own first version, both found by running it:
#
#   1. It used `git/ref/tags/$tag`, which 404s on `actions/checkout@v4` and `actions/setup-python@v5`
#      while working fine for other repositories. `repos/OWNER/REPO/commits/REF` resolves any ref --
#      lightweight tag, annotated tag, branch -- to a commit, and does not care which it is.
#
#   2. **It wrote whatever came back without checking it was a SHA.** `gh` prints the error body to
#      stdout on failure, so `{"message":"Not Found",...}` went straight into eight `uses:` lines in
#      two workflows. The script could not tell success from failure -- the defect class this entire
#      release exists to remove, produced by the tool written to close it.
#
# So: resolve, then VALIDATE, then write. A value that is not 40 hex characters is never written, the
# reference is left exactly as it was, and the script says which one it could not resolve.
#
# Usage:  bash scripts/pin-actions.sh          # rewrite in place
#         bash scripts/pin-actions.sh --dry    # show what it would do, change nothing
set -uo pipefail

DRY=${1:-}
command -v gh >/dev/null || { echo "needs the GitHub CLI: brew install gh"; exit 2; }
gh auth status >/dev/null 2>&1 || { echo "run: gh auth login"; exit 2; }

pinned=0; failed=0
for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
  [ -e "$wf" ] || continue
  while IFS= read -r ref; do
    repo=${ref%@*}
    tag=${ref#*@}
    # already a SHA? leave it alone.
    case "$tag" in ([0-9a-f]*) [ ${#tag} -eq 40 ] && continue ;; esac

    sha=$(gh api "repos/$repo/commits/$tag" --jq '.sha' 2>/dev/null)

    # THE GUARD. Anything that is not exactly 40 hex characters is not a SHA, and a non-SHA must
    # never reach a workflow file. Leaving the mutable tag is worse than pinning -- and writing an
    # error message where a SHA belongs is worse than both.
    if ! printf '%s' "$sha" | grep -qE '^[0-9a-f]{40}$'; then
      echo "  UNRESOLVED $ref -- left as-is (got: ${sha:0:60})"
      failed=$((failed+1)); continue
    fi

    echo "  $ref -> $sha"
    [ "$DRY" = "--dry" ] && continue

    REPO="$repo" TAG="$tag" SHA="$sha" WF="$wf" python3 - <<'PY'
import os, re, pathlib
repo, tag, sha, wf = os.environ["REPO"], os.environ["TAG"], os.environ["SHA"], os.environ["WF"]
p = pathlib.Path(wf); s = p.read_text(encoding="utf-8")
# Keep the tag in a trailing comment: a bare SHA is unreadable and the next person needs to know
# which release it was before they consider moving it.
s = re.sub(rf"uses:\s*{re.escape(repo)}@{re.escape(tag)}\b[^\n]*", f"uses: {repo}@{sha}  # {tag}", s)
p.write_text(s, encoding="utf-8")
PY
    pinned=$((pinned+1))
  done < <(grep -ohE "uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[A-Za-z0-9_.-]+" "$wf" | sed 's/uses: //' | sort -u)
done

echo "pin-actions: $pinned pinned, $failed unresolved"
if [ "$failed" -gt 0 ]; then
  echo "  The unresolved ones were NOT touched. Check the name and the tag by hand:"
  echo "    gh api repos/OWNER/REPO/commits/TAG --jq .sha"
  exit 1
fi
echo "Now run: python3 conformance/test-action-pins.py"
