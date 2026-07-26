#!/usr/bin/env python3
"""Stdlib CLI shim so bash (agents/background/runner.sh) can write to the run registry.

Reuses dashboard/registry.py. No-op-safe: any error exits 0 so a registry hiccup never fails
the background job.

  registry_append.py start  --id ID --persona P --task T --source background
  registry_append.py finish --id ID --status done|error [--report_path PATH]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import registry
except Exception:
    sys.exit(0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["start", "finish"])
    ap.add_argument("--id", required=True)
    ap.add_argument("--persona", default="operator")
    ap.add_argument("--task", default="")
    ap.add_argument("--source", default="background")
    ap.add_argument("--status", default="done")
    ap.add_argument("--report_path", default=None)
    a = ap.parse_args()
    try:
        conn = registry.open_db()
        if a.mode == "start":
            registry.insert_run(conn, a.id, a.persona, a.task, a.source)
        else:
            registry.finish_run(conn, a.id, a.status, report_path=a.report_path)
        conn.close()
    except Exception:
        pass  # never break the caller
    return 0


if __name__ == "__main__":
    sys.exit(main())
