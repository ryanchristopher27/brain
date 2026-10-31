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
    limits      TEXT NOT NULL DEFAULT '{}',   -- JSON, e.g. {"daily_usd": 2.0}
    always      TEXT NOT NULL DEFAULT '[]',   -- JSON list of exact commands approved "always" for this agent
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
    cost    REAL,
    thread  TEXT,                          -- conversation a message belongs to (starts at a user message)
    hop     INTEGER NOT NULL DEFAULT 0,    -- agent-to-agent hand-offs since the user's message
    route   TEXT                           -- why this model: 'pinned' or 'auto: <tier> (<why>)'
);
CREATE INDEX IF NOT EXISTS messages_agent ON messages(agent, id);
CREATE TABLE IF NOT EXISTS holds (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT NOT NULL,
    ts          REAL NOT NULL,
    tool        TEXT NOT NULL,
    input       TEXT NOT NULL,             -- JSON tool input
    kind        TEXT NOT NULL,             -- outside-scope write | command | destructive command | git push | tool
    reason      TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | denied | expired
    decided_at  REAL
);
"""

_JSON = ("scope", "model", "limits", "always")
# Columns added after a table first shipped: (table, column, definition).
_ADDED = [("agents", "limits", "TEXT NOT NULL DEFAULT '{}'"), ("agents", "always", "TEXT NOT NULL DEFAULT '[]'"), ("messages", "thread", "TEXT"),
          ("messages", "hop", "INTEGER NOT NULL DEFAULT 0"), ("messages", "route", "TEXT")]


def open_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    for table, col, ddl in _ADDED:
        if col not in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    conn.execute("CREATE INDEX IF NOT EXISTS messages_thread ON messages(thread)")
    # Holds can't outlive the process that awaited them: anything still pending was never answered.
    conn.execute("UPDATE holds SET status='expired', decided_at=? WHERE status='pending'", (time.time(),))
    conn.commit()
    return conn


def _row(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in _JSON:
        d[k] = json.loads(d[k])
    d["paused"] = bool(d["paused"])
    return d


def create_agent(conn, name: str, persona: str, project: str, brief: str, scope: list[str], model: dict,
                 limits: dict) -> dict:
    now = time.time()
    conn.execute("INSERT INTO agents(name,persona,project,brief,scope,model,limits,created_at,updated_at) "
                 "VALUES(?,?,?,?,?,?,?,?,?)",
                 (name, persona, project, brief, json.dumps(scope), json.dumps(model), json.dumps(limits), now, now))
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
                cost: float | None = None, thread: str | None = None, hop: int = 0,
                route: str | None = None) -> dict:
    ts = time.time()
    cur = conn.execute("INSERT INTO messages(agent,ts,role,sender,text,model,cost,thread,hop,route) "
                       "VALUES(?,?,?,?,?,?,?,?,?,?)", (agent, ts, role, sender, text, model, cost, thread, hop, route))
    conn.commit()
    return {"id": cur.lastrowid, "agent": agent, "ts": ts, "role": role, "sender": sender, "text": text,
            "model": model, "cost": cost, "thread": thread, "hop": hop, "route": route}


def messages(conn, agent: str, limit: int = 200) -> list[dict]:
    rows = conn.execute("SELECT * FROM messages WHERE agent=? ORDER BY id DESC LIMIT ?", (agent, limit))
    return [dict(r) for r in rows][::-1]


def usage_since(conn, agent: str, since: float) -> float:
    row = conn.execute("SELECT COALESCE(SUM(cost),0) FROM messages WHERE agent=? AND ts>=?", (agent, since)).fetchone()
    return float(row[0])


def thread_turns(conn, thread: str) -> int:
    """Agent turns taken in a thread, across every agent."""
    return conn.execute("SELECT COUNT(*) FROM messages WHERE thread=? AND role='assistant'", (thread,)).fetchone()[0]


def create_hold(conn, agent: str, tool: str, inp: dict, kind: str, reason: str) -> dict:
    cur = conn.execute("INSERT INTO holds(agent,ts,tool,input,kind,reason) VALUES(?,?,?,?,?,?)",
                       (agent, time.time(), tool, json.dumps(inp), kind, reason))
    conn.commit()
    return get_hold(conn, cur.lastrowid)


def get_hold(conn, hold_id: int) -> dict | None:
    r = conn.execute("SELECT * FROM holds WHERE id=?", (hold_id,)).fetchone()
    return {**dict(r), "input": json.loads(r["input"])} if r else None


def decide_hold(conn, hold_id: int, status: str) -> dict | None:
    conn.execute("UPDATE holds SET status=?, decided_at=? WHERE id=? AND status='pending'",
                 (status, time.time(), hold_id))
    conn.commit()
    return get_hold(conn, hold_id)


def holds(conn, status: str | None = "pending", limit: int = 100) -> list[dict]:
    q, args = "SELECT id FROM holds", []
    if status:
        q, args = q + " WHERE status=?", [status]
    rows = conn.execute(q + " ORDER BY id DESC LIMIT ?", (*args, limit)).fetchall()
    return [get_hold(conn, r[0]) for r in rows]
