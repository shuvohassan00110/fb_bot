import json
import sqlite3
import time
import os

class SqliteCache:
    def __init__(self, db_path: str, ttl_seconds: int):
        self.db_path = db_path
        self.ttl = ttl_seconds

        # 🔑 Ensure directory exists (THIS IS THE FIX)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._init_db()

    def _conn(self):
        return sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    ts INTEGER NOT NULL
                )
            """)
            conn.commit()

    def get(self, key):
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value, ts FROM cache WHERE key = ?",
                (key,)
            ).fetchone()

            if not row:
                return None

            value, ts = row
            if now - ts > self.ttl:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None

            return json.loads(value)

    def set(self, key, value):
        now = int(time.time())
        payload = json.dumps(value, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, ts) VALUES (?, ?, ?)",
                (key, payload, now)
            )
            conn.commit()
