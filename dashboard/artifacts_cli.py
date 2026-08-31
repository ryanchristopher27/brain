"""Thin CLI over artifacts.py — collect each project's markdown artifacts into brain.

  python -m dashboard.artifacts_cli sync   [--all | --project NAME]
  python -m dashboard.artifacts_cli mark   --project NAME --file PATH [--note "…"]
  python -m dashboard.artifacts_cli ls

`sync --all` refreshes every registered project (backfill). With no flag it syncs all too.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard import artifacts, data  # noqa: E402


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
    return 0


if __name__ == "__main__":
    sys.exit(main())
