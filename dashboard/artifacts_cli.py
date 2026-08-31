"""Thin CLI over artifacts.py — collect each project's markdown artifacts into brain.

  python -m dashboard.artifacts_cli sync   [--all | --project NAME]
  python -m dashboard.artifacts_cli mark   --project NAME --file PATH [--note "…"]
  python -m dashboard.artifacts_cli ls

`sync --all` refreshes every registered project (backfill). With no flag it syncs all too.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard import artifacts, data  # noqa: E402


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(data.BRAIN_DIR), *args],
                          capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="artifacts_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync")
    s.add_argument("--all", action="store_true")
    s.add_argument("--project", default=None)

    m = sub.add_parser("mark")
    m.add_argument("--project", required=True)
    m.add_argument("--file", required=True)
    m.add_argument("--note", default="")

    sub.add_parser("ls")

    pu = sub.add_parser("push")   # backs the /sync command (pull-then-push)
    pu.add_argument("--message", default=None)
    pu.add_argument("--dry-run", action="store_true")
    pu.add_argument("--no-pull", action="store_true", help="skip the pull step; push only")

    args = p.parse_args(argv)

    if args.cmd == "sync":
        if args.project and not args.all:
            root = next((r for n, r in data._project_roots() if n == args.project), None)
            if root is None:
                sys.exit(f"unknown project: {args.project!r}")
            r = artifacts.sync_project(args.project, root)
            artifacts.write_catalog()
            print(f"synced {r['project']}: {r['docs']} docs · {r['tasks']} tasks · "
                  f"{r['sessions']} sessions · {r['deliverables']} deliverables")
        else:
            for r in artifacts.sync_all():
                print(f"  {r['project']:28} {r['docs']} docs · {r['tasks']} tasks · "
                      f"{r['sessions']} sessions · {r['deliverables']} deliverables")
            print(f"catalog → {artifacts.ARTIFACTS_DIR / 'README.md'}")
    elif args.cmd == "mark":
        try:
            r = artifacts.mark(args.project, args.file, args.note)
        except FileNotFoundError as e:
            sys.exit(f"error: {e}")
        print(f"marked {r['file']} → {r['dest']}")
    elif args.cmd == "ls":
        for r in artifacts.sync_all():
            print(f"  {r['project']:28} {r['docs']} docs · {r['tasks']} tasks · "
                  f"{r['sessions']} sessions · {r['deliverables']} deliverables")
    elif args.cmd == "push":
        return _push(args)
    return 0


def _push(args) -> int:
    # 1. refresh the archive from every tracked project
    synced = artifacts.sync_all()
    print(f"refreshed {len(synced)} project(s)")

    if "origin" not in _git("remote").stdout.split():
        sys.exit("no 'origin' remote on the brain repo — add one before syncing")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()

    # 2. stage only artifacts/, check whether anything changed
    _git("add", "--", "artifacts")
    has_changes = _git("diff", "--cached", "--quiet", "--", "artifacts").returncode != 0

    if args.dry_run:
        _git("reset", "--quiet", "--", "artifacts")   # leave the tree as we found it
        _git("fetch", "--quiet", "origin", branch)    # refresh remote-tracking ref for counts
        behind = _git("rev-list", "--count", "HEAD..@{u}").stdout.strip() or "0"
        ahead = _git("rev-list", "--count", "@{u}..HEAD").stdout.strip() or "0"
        print("dry-run — would:")
        print("  commit artifacts/ changes" if has_changes else "  (artifacts/ unchanged — nothing to commit)")
        if not args.no_pull:
            print(f"  pull {behind} commit(s) from origin/{branch} (rebase, autostash)")
        print(f"  push {ahead} pending commit(s) → origin/{branch}")
        return 0

    # 3. commit artifacts if changed
    if has_changes:
        msg = args.message or f"Sync artifacts {artifacts._now()}"
        c = _git("commit", "-m", msg)
        if c.returncode != 0:
            sys.exit(f"commit failed:\n{c.stdout}{c.stderr}")
        print(f"committed: {msg}")
    else:
        print("artifacts/ unchanged — nothing new to commit")

    # 4. pull remote changes first (rebase keeps history linear; autostash protects any
    #    uncommitted code). On conflict, abort cleanly and hand it back — never auto-resolve.
    if not args.no_pull:
        pull = _git("pull", "--rebase", "--autostash", "origin", branch)
        if pull.returncode != 0:
            git_dir = data.BRAIN_DIR / ".git"
            if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
                _git("rebase", "--abort")
                sys.exit("pull hit conflicts — local and remote diverged. Aborted the rebase to "
                         "leave the brain repo clean; resolve manually, then re-run /sync.")
            sys.exit(f"pull failed:\n{(pull.stderr or pull.stdout).strip()}")
        tail = (pull.stdout + pull.stderr).strip().splitlines()
        print("pulled: " + (tail[-1] if tail else "already up to date"))

    # 5. push the branch to origin
    ahead = _git("rev-list", "--count", "@{u}..HEAD").stdout.strip() or "?"
    push = _git("push", "origin", "HEAD")
    if push.returncode != 0:
        sys.exit(f"push failed (remote may have moved — /sync again to pull, or reconcile):\n"
                 f"{(push.stderr or push.stdout).strip()}")
    print(f"pushed {ahead} commit(s) → origin/{branch} ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
