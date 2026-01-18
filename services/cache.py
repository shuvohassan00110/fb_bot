import json
import sqlite3
import time
from typing import Optional, Dict, Any

class SqliteCache:
    def __init__(self, db_path: str, ttl_seconds: int):
        self.db_path = db_path
        self.ttl = ttl_seconds
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

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

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute("SELECT value, ts FROM cache WHERE key = ?", (key,)).fetchone()
            if not row:
                return None
            value, ts = row
            if now - ts > self.ttl:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None
            try:
                return json.loads(value)
            except Exception:
                return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        now = int(time.time())
        payload = json.dumps(value, ensure_ascii=False)
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, ts) VALUES (?, ?, ?)",
                (key, payload, now)
            )
            conn.commit()
