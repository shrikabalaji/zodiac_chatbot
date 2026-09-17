from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def now() -> str:
    return datetime.now(UTC).isoformat()


class Store:
    """One local SQLite store; every user-owned row is scoped to a team."""

    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "agentforge.sqlite3"
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, team TEXT NOT NULL, created TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY, team TEXT NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS blueprints (
                    team TEXT NOT NULL, domain TEXT NOT NULL, instructions TEXT NOT NULL, PRIMARY KEY(team, domain));
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, team TEXT NOT NULL, domain TEXT NOT NULL,
                    role TEXT NOT NULL, content TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS run_team ON runs(team, created);
                CREATE INDEX IF NOT EXISTS events_run ON events(run_id, id);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def put_run(self, run: dict):
        with self.connection() as db:
            db.execute(
                "INSERT INTO runs VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (run["id"], run["team"], run["created"], json.dumps(run)),
            )

    def get_run(self, run_id: str, team: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT data FROM runs WHERE id=? AND team=?", (run_id, team)
            ).fetchone()
        return json.loads(row["data"]) if row else None

    def runs(self, team: str, limit: int = 30) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT data FROM runs WHERE team=? ORDER BY created DESC LIMIT ?", (team, limit)
            ).fetchall()
        return [json.loads(row["data"]) for row in rows]

    def recover(self):
        with self.connection() as db:
            for row in db.execute("SELECT data FROM runs").fetchall():
                run = json.loads(row["data"])
                if run["status"] in {"queued", "running"}:
                    run.update(
                        status="interrupted",
                        error="Server restarted before this run completed. Run it again.",
                    )
                    db.execute("UPDATE runs SET data=? WHERE id=?", (json.dumps(run), run["id"]))

    def event(self, run_id: str, kind: str, **payload):
        event = {"kind": kind, "time": now(), **payload}
        with self.connection() as db:
            db.execute("INSERT INTO events(run_id,data) VALUES(?,?)", (run_id, json.dumps(event)))

    def events(self, run_id: str, after: int = 0) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,data FROM events WHERE run_id=? AND id>? ORDER BY id", (run_id, after)
            ).fetchall()
        return [{"id": row["id"], **json.loads(row["data"])} for row in rows]

    def notes(self, team: str) -> list[dict]:
        with self.connection() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT id,title,text,created FROM notes WHERE team=? ORDER BY created DESC",
                    (team,),
                )
            ]

    def add_note(self, team: str, title: str, text: str) -> dict:
        note = {"id": uuid4().hex, "title": title, "text": text, "created": now()}
        with self.connection() as db:
            db.execute(
                "INSERT INTO notes VALUES(?,?,?,?,?)",
                (note["id"], team, title, text, note["created"]),
            )
        return note

    def delete_note(self, team: str, note_id: str):
        with self.connection() as db:
            db.execute("DELETE FROM notes WHERE team=? AND id=?", (team, note_id))

    def search(self, team: str, query: str) -> list[dict]:
        terms = set(re.findall(r"\w{3,}", query.lower()))
        ranked = []
        for note in self.notes(team):
            score = len(
                terms & set(re.findall(r"\w{3,}", (note["title"] + " " + note["text"]).lower()))
            )
            if score:
                # Return matching lines, with a bounded context window, rather than the whole vault.
                lines = note["text"].splitlines()
                hit = next(
                    (
                        i
                        for i, line in enumerate(lines)
                        if terms & set(re.findall(r"\w{3,}", line.lower()))
                    ),
                    0,
                )
                ranked.append(
                    (
                        score,
                        {
                            "source": note["title"],
                            "note_id": note["id"],
                            "excerpt": "\n".join(lines[max(0, hit - 1) : hit + 6])[:1800],
                        },
                    )
                )
        return [item for _, item in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:4]]

    def blueprint(self, team: str, domain: str) -> str:
        with self.connection() as db:
            row = db.execute(
                "SELECT instructions FROM blueprints WHERE team=? AND domain=?", (team, domain)
            ).fetchone()
        return row["instructions"] if row else ""

    def set_blueprint(self, team: str, domain: str, instructions: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO blueprints VALUES(?,?,?) ON CONFLICT(team,domain) DO UPDATE SET instructions=excluded.instructions",
                (team, domain, instructions),
            )

    def messages(self, team: str, domain: str, limit: int = 10) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT role,content FROM messages WHERE team=? AND domain=? ORDER BY id DESC LIMIT ?",
                (team, domain, limit),
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def add_message(self, team: str, domain: str, role: str, content: str):
        with self.connection() as db:
            db.execute(
                "INSERT INTO messages(team,domain,role,content) VALUES(?,?,?,?)",
                (team, domain, role, content),
            )
