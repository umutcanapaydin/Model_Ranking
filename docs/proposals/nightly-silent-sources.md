# Proposal: the nightly opens one issue for the sources silent for 7 or more nights

The workflow half of #552 (D-243 clause 3). The refresh half is in this repository: each cycle writes
`silent` into its record (`advisor.db.refresh.json`), the sources whose last arrival (D-156) is 7 or more
days before the cycle, with that arrival (`app.workflows.refresh.silent_sources`), and
`scripts/silent_sources.py` turns it into a list or into the issue. The agent may not write
`.github/workflows/**` (AGENTS.md section 3), so this change is the owner's to apply.

## What the change does

- **The refresh job** gains `outputs.silent` and one step, its last, `The sources silent for 7 or more
  nights (D-243)`: `python3 scripts/silent_sources.py --issue "$RUNNER_TEMP/state/advisor.db.refresh.json"`
  prints the issue as one line of JSON (`{"title": ..., "body": ...}`), or nothing when no source is silent;
  the step prints the names to the log and passes the JSON on as the job's output.
  - It runs with `if: ${{ !cancelled() }}`, so on a failed or refused night too: a night that serves
    nothing new is when a silence grows.
  - It never fails the job: an unreadable record is a `::warning::` line, and the step is `continue-on-error`
    (#580 M1: under `bash -e` a failure in its `then` branch would fail the job and skip the deploy).
  - The job's permissions stay `contents: read, actions: read`, as `tests/unit/test_nightly_hosted.py` holds
    them (D-217 clause 2).
- **A new job, `notice`**, runs after the refresh, only on main, only when the output is not empty, and is the
  only job that holds `issues: write`. It finds the open issue the workflow opened before, by its title and
  its author (`--author app/github-actions`, so an issue anyone else opens with that title is never written
  to), and comments on it; with none open it opens one. A silence that lasts is one issue, not one a night
  (D-243 clause 2). Every `gh` call names the repository (`-R "$GITHUB_REPOSITORY"`, or the API path).
  - Its title, and every other field, is fixed in the workflow (`title='Sources silent for 7 or more nights'`,
    `scripts/silent_sources.py`'s `TITLE`); only the body comes from the refresh, taken out of the
    script's JSON with `jq -r '.body'` and posted with `gh issue create`/`gh issue comment --body-file`
    (#580 R2: code run in `refresh` could otherwise choose the title, labels or assignees). `jq` is not
    an interpreter the deploy gate refuses (D-242 clause 4, D-245 clause 3).
  - The body carries the marker line `<!-- silent-sources -->`, which GitHub does not render.
- D-156's 30-day carry and the serving path are untouched (D-243 clause 4).

## Checked before proposing

- Rebuilt for #580 (the security review of the first bundle, `docs/reviews/owner-bundle-552-security.md`): M1,
  M3 (the header names the three jobs) and R2 are in the patch; M2's claims are held by
  `tests/unit/test_nightly_notice_580.py`, which applies this patch to a scratch copy until the owner applies it.
- The deploy gate's readers (D-239, D-242, D-245) find no start of a file without its name in the patched
  workflow (58 run commands).

- `tests/unit/test_nightly_hosted.py` passes, 44 tests, against both copies with the change.
- D-239's reader (`scripts/deploy_gate.py` `unnamed_starts`, on this tree and on #553's branch) finds no
  start of a file without its name in the changed workflow.

## The patch

`make owner-bundle` built it: two files, `.github/workflows/nightly-hosted.yml` and its proposal copy
`scripts/ci/nightly-hosted.yml`, changed identically (the test holds them equal). It owes the
Security-Reviewer's reading: the apply refuses it until a `docs/reviews/*-security.md` verdict names
`**Reviewed patch:** 9d89f61fc7184fb7aeda42f763c96b612c9abdc07cbf09933b547a32f4a7fb8d`.

```diff
diff --git a/.github/workflows/nightly-hosted.yml b/.github/workflows/nightly-hosted.yml
index 1e67c9d..c7191b4 100644
--- a/.github/workflows/nightly-hosted.yml
+++ b/.github/workflows/nightly-hosted.yml
@@ -4,7 +4,7 @@
 # (AGENTS.md section 3): `cp scripts/ci/nightly-hosted.yml .github/workflows/`. tests/unit/test_nightly_hosted.py
 # holds this file's shape, and holds the installed copy equal to it once it exists.
 #
-# Two jobs, and only the second holds a secret (D-217 clause 2):
+# Three jobs; only `deploy` holds a secret (D-217 clause 2), and only `notice` may write issues (D-243):
 #   refresh  fetches and parses every source, builds the artifact, and keeps it as `hosted-state` for the
 #            next night's carry-forward (D-156); then derives the public copy and its stamp, `hosted-public`.
 #            No secret; the checkout keeps no credential; the token that reads the previous state reaches
@@ -15,7 +15,10 @@
 #            It runs in the `fly-production` environment, which only `main` may deploy from, and the token
 #            is that environment's secret, never the repository's: a run dispatched on another branch
 #            cannot reach it (the #387 security review's B1).
-# Both jobs run only on main.
+#   notice   opens one issue for the sources silent for 7 or more nights, or comments on the open one
+#            (D-243 clause 2). It holds `issues: write` and nothing else, checks nothing out and uses no
+#            action; its title is fixed here, and only the body comes from the refresh (#580 R2).
+# Every job runs only on main.
 # A failed night uploads and deploys nothing: Fly keeps serving the last good image, the last good state stands.
 name: nightly-hosted
 
@@ -41,6 +44,7 @@ jobs:
       actions: read
     outputs:
       outcome: ${{ steps.night.outputs.outcome }}
+      silent: ${{ steps.silent.outputs.notice }}
     steps:
       - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262  # v4.4.0
         with:
@@ -104,6 +108,49 @@ jobs:
             build/hosted/build.txt
           retention-days: 1
           if-no-files-found: error
+      - name: The sources silent for 7 or more nights (D-243)
+        # Last, and on a failed or refused night too: a night that serves nothing new is when a source's
+        # silence grows. It never fails the job, so it never holds the deploy back.
+        id: silent
+        if: ${{ !cancelled() }}
+        continue-on-error: true  # #580 M1: under bash -e a failure here would skip the deploy
+        run: |
+          record="$RUNNER_TEMP/state/advisor.db.refresh.json"
+          if python3 scripts/silent_sources.py --issue "$record" > "$RUNNER_TEMP/silent.json"; then
+            python3 scripts/silent_sources.py "$record"
+            echo "notice=$(cat "$RUNNER_TEMP/silent.json")" >> "$GITHUB_OUTPUT"
+          else
+            echo "::warning::the silent sources could not be read from the refresh record (D-243)"
+          fi
+
+  notice:
+    # D-243 clause 2: one issue for the silent sources, opened once and commented on each night after, so a
+    # silence that lasts is one issue. Its own job: the refresh job's token never holds `issues: write`.
+    needs: refresh
+    if: >-
+      !cancelled() && github.ref == 'refs/heads/main' && needs.refresh.outputs.silent != ''
+    runs-on: ubuntu-latest
+    timeout-minutes: 5
+    permissions:
+      issues: write
+    steps:
+      - name: Open the silent-sources issue, or comment on the open one
+        env:
+          GH_TOKEN: ${{ github.token }}
+          NOTICE: ${{ needs.refresh.outputs.silent }}
+        run: |
+          # #580 R2: the title and every other field are fixed here; only the body comes from the refresh
+          printf '%s\n' "$NOTICE" | jq -r '.body' > "$RUNNER_TEMP/notice.md"
+          title='Sources silent for 7 or more nights'
+          open=$(gh issue list -R "$GITHUB_REPOSITORY" --state open --author app/github-actions \
+            --search "\"$title\" in:title" --json number --jq '.[0].number // empty')
+          if [ -n "$open" ]; then
+            gh issue comment "$open" -R "$GITHUB_REPOSITORY" --body-file "$RUNNER_TEMP/notice.md"
+            echo "commented on issue #$open"
+          else
+            gh issue create -R "$GITHUB_REPOSITORY" --title "$title" --body-file "$RUNNER_TEMP/notice.md"
+            echo "opened the silent-sources issue"
+          fi
 
   deploy:
     needs: refresh
diff --git a/scripts/ci/nightly-hosted.yml b/scripts/ci/nightly-hosted.yml
index 1e67c9d..c7191b4 100644
--- a/scripts/ci/nightly-hosted.yml
+++ b/scripts/ci/nightly-hosted.yml
@@ -4,7 +4,7 @@
 # (AGENTS.md section 3): `cp scripts/ci/nightly-hosted.yml .github/workflows/`. tests/unit/test_nightly_hosted.py
 # holds this file's shape, and holds the installed copy equal to it once it exists.
 #
-# Two jobs, and only the second holds a secret (D-217 clause 2):
+# Three jobs; only `deploy` holds a secret (D-217 clause 2), and only `notice` may write issues (D-243):
 #   refresh  fetches and parses every source, builds the artifact, and keeps it as `hosted-state` for the
 #            next night's carry-forward (D-156); then derives the public copy and its stamp, `hosted-public`.
 #            No secret; the checkout keeps no credential; the token that reads the previous state reaches
@@ -15,7 +15,10 @@
 #            It runs in the `fly-production` environment, which only `main` may deploy from, and the token
 #            is that environment's secret, never the repository's: a run dispatched on another branch
 #            cannot reach it (the #387 security review's B1).
-# Both jobs run only on main.
+#   notice   opens one issue for the sources silent for 7 or more nights, or comments on the open one
+#            (D-243 clause 2). It holds `issues: write` and nothing else, checks nothing out and uses no
+#            action; its title is fixed here, and only the body comes from the refresh (#580 R2).
+# Every job runs only on main.
 # A failed night uploads and deploys nothing: Fly keeps serving the last good image, the last good state stands.
 name: nightly-hosted
 
@@ -41,6 +44,7 @@ jobs:
       actions: read
     outputs:
       outcome: ${{ steps.night.outputs.outcome }}
+      silent: ${{ steps.silent.outputs.notice }}
     steps:
       - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262  # v4.4.0
         with:
@@ -104,6 +108,49 @@ jobs:
             build/hosted/build.txt
           retention-days: 1
           if-no-files-found: error
+      - name: The sources silent for 7 or more nights (D-243)
+        # Last, and on a failed or refused night too: a night that serves nothing new is when a source's
+        # silence grows. It never fails the job, so it never holds the deploy back.
+        id: silent
+        if: ${{ !cancelled() }}
+        continue-on-error: true  # #580 M1: under bash -e a failure here would skip the deploy
+        run: |
+          record="$RUNNER_TEMP/state/advisor.db.refresh.json"
+          if python3 scripts/silent_sources.py --issue "$record" > "$RUNNER_TEMP/silent.json"; then
+            python3 scripts/silent_sources.py "$record"
+            echo "notice=$(cat "$RUNNER_TEMP/silent.json")" >> "$GITHUB_OUTPUT"
+          else
+            echo "::warning::the silent sources could not be read from the refresh record (D-243)"
+          fi
+
+  notice:
+    # D-243 clause 2: one issue for the silent sources, opened once and commented on each night after, so a
+    # silence that lasts is one issue. Its own job: the refresh job's token never holds `issues: write`.
+    needs: refresh
+    if: >-
+      !cancelled() && github.ref == 'refs/heads/main' && needs.refresh.outputs.silent != ''
+    runs-on: ubuntu-latest
+    timeout-minutes: 5
+    permissions:
+      issues: write
+    steps:
+      - name: Open the silent-sources issue, or comment on the open one
+        env:
+          GH_TOKEN: ${{ github.token }}
+          NOTICE: ${{ needs.refresh.outputs.silent }}
+        run: |
+          # #580 R2: the title and every other field are fixed here; only the body comes from the refresh
+          printf '%s\n' "$NOTICE" | jq -r '.body' > "$RUNNER_TEMP/notice.md"
+          title='Sources silent for 7 or more nights'
+          open=$(gh issue list -R "$GITHUB_REPOSITORY" --state open --author app/github-actions \
+            --search "\"$title\" in:title" --json number --jq '.[0].number // empty')
+          if [ -n "$open" ]; then
+            gh issue comment "$open" -R "$GITHUB_REPOSITORY" --body-file "$RUNNER_TEMP/notice.md"
+            echo "commented on issue #$open"
+          else
+            gh issue create -R "$GITHUB_REPOSITORY" --title "$title" --body-file "$RUNNER_TEMP/notice.md"
+            echo "opened the silent-sources issue"
+          fi
 
   deploy:
     needs: refresh
```

## The owner's one command

Once this proposal is on main and the review names the patch, from the main work tree:

```sh
cd ~/Desktop/ILGAR/model_ranking && git switch main && git pull && git switch -c owner/nightly-silent-sources && mkdir -p build/owner-bundle && awk '/^```diff$/{f=1;next} /^```$/{f=0} f' docs/proposals/nightly-silent-sources.md > build/owner-bundle/9d89f61fc718.patch && python3 scripts/owner_bundle.py apply build/owner-bundle/9d89f61fc718.patch 9d89f61fc7184fb7aeda42f763c96b612c9abdc07cbf09933b547a32f4a7fb8d && git commit -m "ci: the nightly names the sources silent for 7 or more nights in one issue (D-243)" && git push -u origin owner/nightly-silent-sources && gh pr create --draft --fill
```

The command takes the patch out of this file, checks its sha256 (`9d89f61fc71813c3...`), applies and
stages it, commits it on its own branch and opens the draft; a human merges it.
