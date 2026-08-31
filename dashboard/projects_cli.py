"""Thin CLI over projects.py — register the projects brain tracks and set their status,
without the dashboard server running. Writes ~/.claude/brain/projects.json.

  python -m dashboard.projects_cli ls
  python -m dashboard.projects_cli add   --name N --path DIR [--status active]
  python -m dashboard.projects_cli status --name N --to shipped
  python -m dashboard.projects_cli remove --name N
  python -m dashboard.projects_cli vault [--path DIR]      # (re)generate the Obsidian projects vault

Status is one of: active · paused · blocked · shipped · archived.
`add` with --path "." registers the current working directory (handy from a new project).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard import projects  # noqa: E402


def _print_row(p: dict) -> None:
    flag = "" if p["exists"] else "  ⚠ missing"
    phase = f"  ·  phase:{p['phase']}" if p.get("phase") else ""
    tasks = f"  ·  {p['tasks_open']}/{p['tasks_total']} open" if "tasks_total" in p else ""
    print(f"  {p['status']:8} {p['name']:28} {p['root_path']}{phase}{tasks}{flag}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="projects_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ls")

    a = sub.add_parser("add")
    a.add_argument("--name", required=True)
    a.add_argument("--path", required=True)
    a.add_argument("--status", default=projects.DEFAULT_STATUS)

    s = sub.add_parser("status")
    s.add_argument("--name", required=True)
    s.add_argument("--to", required=True)

    r = sub.add_parser("remove")
    r.add_argument("--name", required=True)

    v = sub.add_parser("vault")
    v.add_argument("--path", default=None)

    sy = sub.add_parser("sync")   # used by the SessionStart hook
    sy.add_argument("--path", default=".")
    sy.add_argument("--no-vault", action="store_true")

    args = p.parse_args(argv)

    try:
        if args.cmd == "ls":
            rows = projects.enriched()
            if not rows:
                print("(no projects registered — `add` some, or auto-discovery is empty)")
            for row in rows:
                _print_row(row)
        elif args.cmd == "add":
            e = projects.add_project(args.name, args.path, args.status)
            print(f"registered {e['name']}  [{e['status']}]  → {e['root_path']}")
        elif args.cmd == "status":
            e = projects.set_status(args.name, args.to)
            print(f"{e['name']} → {e['status']}")
        elif args.cmd == "remove":
            projects.remove_project(args.name)
            print(f"removed {args.name}")
        elif args.cmd == "vault":
            from dashboard import projects_vault
            out = projects_vault.generate(args.path)
            print(f"vault written → {out}  ({len(projects.list_projects())} projects)")
        elif args.cmd == "sync":
            res = projects.sync_cwd(args.path, regenerate=not args.no_vault)
            parts = []
            if res["registered"]:
                parts.append(f"registered {res['registered']}")
            elif res["skipped"]:
                parts.append(res["skipped"])
            if res.get("artifacts"):
                parts.append(f"artifacts {res['artifacts']}")
            if res["vault"]:
                parts.append(f"vault {res['vault']}")
            print("project sync: " + " · ".join(parts))
    except projects.ProjectError as e:
        sys.exit(f"error: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
