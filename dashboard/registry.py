"""SQLite run registry (D6) — unified history of agent runs across voice, background, and
dashboard-spawned work. Small, stdlib-only, WAL-mode so multiple writers don't lock.

Writers: the dashboard process manager (direct), agents/background/runner.sh (via
registry_append.py), and the voice daemon. All are no-ops-safe: if the db can't be opened the
callers simply skip — a missing registry never breaks a run.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "brain-dashboard" / "runs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          TEXT PRIMARY KEY,
    persona     TEXT NOT NULL,
    task        TEXT NOT NULL,
    source      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',
    started_at  REAL NOT NULL,
    ended_at    REAL,
    cost_usd    REAL,
    input_tok   INTEGER,
    output_tok  INTEGER,
    report_path TEXT,
    pid         INTEGER
);
CREATE TABLE IF NOT EXISTS events (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    ts     REAL NOT NULL,
    kind   TEXT NOT NULL,
    data   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_run ON events(run_id, ts);
"""


def new_id() -> str:
    return secrets.token_urlsafe(16)


def open_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def insert_run(conn, id: str, persona: str, task: str, source: str, pid: int | None = None) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO runs(id,persona,task,source,status,started_at,pid) "
        "VALUES(?,?,?,?,'running',?,?)",
        (id, persona, task, source, time.time(), pid),
    )
    conn.commit()


def finish_run(conn, id: str, status: str, cost_usd=None, input_tok=None,
               output_tok=None, report_path=None) -> None:
    conn.execute(
        "UPDATE runs SET status=?, ended_at=?, cost_usd=?, input_tok=?, output_tok=?, "
        "report_path=? WHERE id=?",
        (status, time.time(), cost_usd, input_tok, output_tok, report_path, id),
    )
    conn.commit()


def append_event(conn, run_id: str, kind: str, data: dict) -> None:
    conn.execute(
        "INSERT INTO events(run_id,ts,kind,data) VALUES(?,?,?,?)",
        (run_id, time.time(), kind, json.dumps(data)),
    )
    conn.commit()


def recent_runs(conn, limit: int = 30) -> list[dict]:
    cur = conn.execute(
        "SELECT id,persona,task,source,status,started_at,ended_at,cost_usd,"
        "input_tok,output_tok,report_path,pid FROM runs ORDER BY started_at DESC LIMIT ?",
        (limit,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def totals(conn) -> dict:
    cur = conn.execute("SELECT COUNT(*), COALESCE(SUM(cost_usd),0) FROM runs")
    n, cost = cur.fetchone()
    return {"runs": n, "cost_usd": round(cost or 0.0, 4)}
