# /sync

Refresh brain's artifact archive and push it to the remote. Use this to snapshot the current
state of all your projects' markdown artifacts up to GitHub.

## Do this

Run this single command (it targets the brain repo regardless of your current directory) and
report its output to the user verbatim:

```
/Users/rchristopher/Desktop/Code/brain/voice/.venv/bin/python -m dashboard.artifacts_cli push
```

Pass `--message "…"` to set the artifact commit message, or `--dry-run` to preview without
committing or pushing.

## What it does, in order

1. **Refresh** `brain/artifacts/` from every tracked project — docs, task history, session
   summaries, marked deliverables. (Idempotent: unchanged artifacts produce no diff.)
2. **Commit** only `artifacts/` changes, if any (message `Sync artifacts <timestamp>` by default).
3. **Push** the current branch to `origin` — brain's remote is
   `github.com/ryanchristopher27/brain` on branch **`main`**.

## Notes

- This pushes **all** pending local commits on the branch to `origin/main`, not only the
  artifact commit — it brings the remote fully up to date.
- It never touches uncommitted **code** changes: only `artifacts/` is staged and committed.
- If `artifacts/` is unchanged, it skips the commit and still pushes any pending commits.
- On any git failure (no `origin`, no push access, rejected non-fast-forward) it stops and
  reports git's error — relay that to the user rather than retrying blindly.
- Do not add `--force` or otherwise override a rejected push; if the remote is ahead, tell the
  user so they can pull/reconcile first.
