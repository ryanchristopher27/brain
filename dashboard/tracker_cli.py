"""Thin CLI over tracker.py so workflow commands (and you) can create/maintain tasks without the
dashboard server running. Writes the git-versioned .brain/tasks/ files directly.

  python -m dashboard.tracker_cli list   [--project P]
  python -m dashboard.tracker_cli create --project P --title T [--type --brief --assignee --source --status]
  python -m dashboard.tracker_cli upsert --project P --source S --title T [--type --brief]
  python -m dashboard.tracker_cli status --project P --id ID --to STATUS [--note] [--actor user]
  python -m dashboard.tracker_cli comment --project P --id ID --detail "…"
  python -m dashboard.tracker_cli link   --project P --id ID --run RUN [--result "…"]

Project is resolved to a repo root from the known set (data._project_roots) or via --root PATH.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Runnable both as `python -m dashboard.tracker_cli` (from brain) and as a standalone script
# `python3 /abs/brain/dashboard/tracker_cli.py` from any project's cwd (workflow-command hooks).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard import data, tracker  # noqa: E402


def _root(args) -> Path:
    if args.root:
        return Path(args.root).expanduser()
    for name, root in data._project_roots():
        if name == args.project:
            return root
    sys.exit(f"unknown project: {args.project!r} (use --root, or one of "
             f"{[n for n, _ in data._project_roots()]})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tracker_cli")
    p.add_argument("--project"); p.add_argument("--root")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--type", default="task"); c.add_argument("--brief", default="")
    c.add_argument("--assignee", default=""); c.add_argument("--scoped-dir", default=".")
    c.add_argument("--source", default=""); c.add_argument("--status", default="backlog")

    u = sub.add_parser("upsert")
    u.add_argument("--source", required=True); u.add_argument("--title", required=True)
    u.add_argument("--type", default="task"); u.add_argument("--brief", default="")
    u.add_argument("--assignee", default="")

    s = sub.add_parser("status")
    s.add_argument("--id", required=True); s.add_argument("--to", required=True)
    s.add_argument("--note", default=""); s.add_argument("--actor", default="user")

    cm = sub.add_parser("comment")
    cm.add_argument("--id", required=True); cm.add_argument("--detail", required=True)

    ln = sub.add_parser("link")
    ln.add_argument("--id", required=True); ln.add_argument("--run", required=True)
    ln.add_argument("--result", default=None)

    args = p.parse_args(argv)
    root = _root(args)

    try:
        if args.cmd == "list":
            for t in tracker.list_tasks(root):
                print(f"  {t['status']:8} #{t['id']}  {t['title']}"
                      + (f"   [{t['source']}]" if t.get("source") else ""))
        elif args.cmd == "create":
            t = tracker.create_task(root, args.title, type=args.type, brief=args.brief,
                                    assignee=args.assignee, scoped_dir=args.scoped_dir,
                                    source=args.source)
            if args.status != "backlog":
                tracker.set_status(root, t["id"], args.status, actor="user")
            print(f"created #{t['id']}  {t['title']}")
        elif args.cmd == "upsert":
            t = tracker.upsert_task(root, args.source, args.title, type=args.type,
                                    brief=args.brief, assignee=args.assignee)
            print(f"{'created' if t.get('_created') else 'updated'} #{t['id']}  {t['title']}")
        elif args.cmd == "status":
            t = tracker.set_status(root, args.id, args.to, actor=args.actor, note=args.note)
            print(f"#{args.id} → {t['status']}")
        elif args.cmd == "comment":
            tracker.add_update(root, args.id, "comment", args.detail)
            print(f"#{args.id} commented")
        elif args.cmd == "link":
            tracker.link_run(root, args.id, args.run, result=args.result)
            print(f"#{args.id} linked {args.run}")
    except tracker.TrackerError as e:
        sys.exit(f"error: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
