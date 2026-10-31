"""Harness store (H1) — roster, sessions, conversation log and usage for long-lived agents.

SQLite in WAL mode next to the run registry. Live state only: agent *definitions* that should
travel between machines arrive with the agent library (H6) as files in git.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / ".claude" / "brain-dashboard" / "harness.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    name        TEXT PRIMARY KEY,
    persona     TEXT NOT NULL,
    project     TEXT NOT NULL,
    brief       TEXT NOT NULL DEFAULT '',
    scope       TEXT NOT NULL,             -- JSON list of absolute dirs
    model       TEXT NOT NULL,             -- JSON model settings (see runtime.default_model)
    session_id  TEXT,
    paused      INTEGER NOT NULL DEFAULT 0,
    usage_usd   REAL NOT NULL DEFAULT 0,
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    agent   TEXT NOT NULL,
    ts      REAL NOT NULL,
    role    TEXT NOT NULL,                 -- user | assistant | tool | system
    sender  TEXT NOT NULL,                 -- 'you', another agent's name, or the agent itself
    text    TEXT NOT NULL,
    model   TEXT,
    cost    REAL
);
CREATE INDEX IF NOT EXISTS messages_agent ON messages(agent, id);
"""

_JSON = ("scope", "model")


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def _row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in _JSON:
        d[k] = json.loads(d[k])
    d["paused"] = bool(d["paused"])
    return d


def create_agent(conn, name: str, persona: str, project: str, brief: str, scope: list[str], model: dict) -> dict:
    now = time.time()
    conn.execute("INSERT INTO agents(name,persona,project,brief,scope,model,created_at,updated_at) "
                 "VALUES(?,?,?,?,?,?,?,?)",
                 (name, persona, project, brief, json.dumps(scope), json.dumps(model), now, now))
    conn.commit()
    return get_agent(conn, name)


def get_agent(conn, name: str) -> dict | None:
    return _row(conn.execute("SELECT * FROM agents WHERE name=?", (name,)).fetchone())


def list_agents(conn) -> list[dict]:
    return [_row(r) for r in conn.execute("SELECT * FROM agents ORDER BY created_at")]


def update_agent(conn, name: str, **fields) -> dict | None:
    if not fields:
        return get_agent(conn, name)
    vals = {k: json.dumps(v) if k in _JSON else (int(v) if k == "paused" else v) for k, v in fields.items()}
    sets = ", ".join(f"{k}=?" for k in vals)
    conn.execute(f"UPDATE agents SET {sets}, updated_at=? WHERE name=?", (*vals.values(), time.time(), name))
    conn.commit()
    return get_agent(conn, name)


def add_usage(conn, name: str, cost: float) -> None:
    conn.execute("UPDATE agents SET usage_usd = usage_usd + ? WHERE name=?", (cost, name))
    conn.commit()


def delete_agent(conn, name: str) -> None:
    conn.execute("DELETE FROM agents WHERE name=?", (name,))
    conn.execute("DELETE FROM messages WHERE agent=?", (name,))
    conn.commit()


def log_message(conn, agent: str, role: str, sender: str, text: str, model: str | None = None,
                cost: float | None = None) -> dict:
    ts = time.time()
    cur = conn.execute("INSERT INTO messages(agent,ts,role,sender,text,model,cost) VALUES(?,?,?,?,?,?,?)",
                       (agent, ts, role, sender, text, model, cost))
    conn.commit()
    return {"id": cur.lastrowid, "agent": agent, "ts": ts, "role": role, "sender": sender, "text": text,
            "model": model, "cost": cost}


def messages(conn, agent: str, limit: int = 200) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages WHERE agent=? ORDER BY id DESC LIMIT ?", (agent, limit))
    return [dict(r) for r in rows][::-1]
