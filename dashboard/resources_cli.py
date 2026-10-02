"""CLI for the per-project resources file (dev dashboard). No server needed.

    python -m dashboard.resources_cli seed --path .            # propose entries, print JSON
    python -m dashboard.resources_cli seed --path . --out .brain/resources.json
    python -m dashboard.resources_cli validate --path .brain/resources.json

`seed` only scans and proposes — it never writes without `--out`, and even then the
output is meant to be reviewed/edited by a human before being trusted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import resources


def main() -> None:
    ap = argparse.ArgumentParser(prog="resources_cli")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_seed = sub.add_parser("seed", help="scan a project dir and propose resource entries")
    p_seed.add_argument("--path", default=".")
    p_seed.add_argument("--out", default=None, help="write proposal to this file instead of stdout")

    p_val = sub.add_parser("validate", help="validate a resources.json file against the schema")
    p_val.add_argument("--path", required=True)

    args = ap.parse_args()

    if args.cmd == "seed":
        root = Path(args.path).expanduser().resolve()
        proposal = resources.generate_seed(root)
        doc = {"project": root.name, "resources": proposal["resources"]}
        text = json.dumps(doc, indent=2) + "\n"
        if proposal["unmatched_env_vars"]:
            print(f"# unmatched env vars (not auto-attributed — add manually): "
                  f"{', '.join(proposal['unmatched_env_vars'])}", file=sys.stderr)
        if args.out:
            Path(args.out).write_text(text)
            print(f"wrote {args.out} — review before trusting it", file=sys.stderr)
        else:
            print(text)
    elif args.cmd == "validate":
        doc = json.loads(Path(args.path).read_text())
        problems = resources.validate(doc)
        if problems:
            for p in problems:
                print(f"- {p}")
            sys.exit(1)
        print("ok")


if __name__ == "__main__":
    main()
