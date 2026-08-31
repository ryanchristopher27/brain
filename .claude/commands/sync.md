# /sync

Refresh brain's artifact archive and push it to the remote. Use this to snapshot the current
state of all your projects' markdown artifacts up to GitHub.

## Do this

Run this single command (it targets the brain repo regardless of your current directory) and
report its output to the user verbatim:

```
/Users/rchristopher/Desktop/Code/brain/voice/.venv/bin/python -m dashboard.artifacts_cli push
```

Pass `--message "…"` to set the artifact commit message, `--dry-run` to preview without
changing anything, or `--no-pull` to push only.

## What it does, in order

1. **Refresh** `brain/artifacts/` from every tracked project — docs, task history, session
   summaries, marked deliverables. (Idempotent: unchanged artifacts produce no diff.)
2. **Commit** only `artifacts/` changes, if any (message `Sync artifacts <timestamp>` by default).
3. **Pull** `origin/main` with `--rebase --autostash` — brings in remote changes, keeps history
   linear, and protects any uncommitted code by stashing it around the rebase.
4. **Push** the current branch to `origin` — brain's remote is
   `github.com/ryanchristopher27/brain` on branch **`main`**.

## Notes

- Pull-then-push makes this a true two-way sync (useful across machines). `--no-pull` for push-only.
- Push sends **all** pending local commits to `origin/main`, not just the artifact commit —
  bringing the remote fully up to date.
- It never touches uncommitted **code** changes: only `artifacts/` is staged/committed; the pull's
  autostash preserves the rest.
- **Conflicts are never auto-resolved.** If the rebase hits a conflict, it aborts to leave the
  brain repo clean and reports that local and remote diverged — relay that so the user resolves
  manually, then re-runs `/sync`.
- Never `--force`. A rejected push (remote moved) is surfaced — re-run `/sync` to pull, or
  reconcile manually. Relay git's error rather than retrying blindly.
