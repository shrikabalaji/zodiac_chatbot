"""Team authentication and bounded request admission for a single server process."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from collections import OrderedDict


class BusyError(ValueError):
    pass


class RateLimiter:
    def __init__(self, limit=20, window=60, capacity=4096):
        self.limit, self.window, self.capacity = limit, window, capacity
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, key):
        with self.lock:
            now = time.monotonic()
            hits = [t for t in self.entries.pop(key, []) if now - t < self.window]
            allowed = len(hits) < self.limit
            if allowed:
                hits.append(now)
            self.entries[key] = hits
            while len(self.entries) > self.capacity:
                self.entries.popitem(last=False)
            return allowed


class TeamAuth:
    COOKIE = "agentforge_session"
    TTL = 12 * 60 * 60

    def __init__(self, store):
        self.store = store
        with store.connection() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS credentials(team TEXT PRIMARY KEY, salt TEXT NOT NULL, digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, team TEXT NOT NULL, expires REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS session_expiry ON sessions(expires);
            """)

    @staticmethod
    def digest(password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()

    def provision(self, team, password):
        salt = secrets.token_hex(16)
        with self.store.connection() as db:
            db.execute(
                "INSERT INTO credentials VALUES(?,?,?) ON CONFLICT(team) DO UPDATE SET salt=excluded.salt,digest=excluded.digest",
                (team, salt, self.digest(password, salt)),
            )
            db.execute("DELETE FROM sessions WHERE team=?", (team,))

    def login(self, team, password):
        with self.store.connection() as db:
            row = db.execute("SELECT * FROM credentials WHERE team=?", (team,)).fetchone()
        salt = row["salt"] if row else "00" * 16
        actual = self.digest(password, salt)
        if not row or not hmac.compare_digest(actual, row["digest"]):
            return None
        token = secrets.token_urlsafe(32)
        with self.store.connection() as db:
            db.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?)",
                (hashlib.sha256(token.encode()).hexdigest(), team, time.time() + self.TTL),
            )
        return token

    def team(self, token):
        if not token or len(token) > 256:
            return None
        with self.store.connection() as db:
            row = db.execute(
                "SELECT team FROM sessions WHERE digest=? AND expires>?",
                (hashlib.sha256(token.encode()).hexdigest(), time.time()),
            ).fetchone()
        return row["team"] if row else None

    def logout(self, token):
        with self.store.connection() as db:
            db.execute(
                "DELETE FROM sessions WHERE digest=?",
                (hashlib.sha256((token or "").encode()).hexdigest(),),
            )
