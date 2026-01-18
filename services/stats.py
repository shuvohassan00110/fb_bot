import sqlite3
import time

class StatsDB:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL
            )""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                key TEXT PRIMARY KEY,
                val INTEGER NOT NULL
            )""")
            for k in ["requests", "cache_hits", "zips_generated", "albums_sent", "profile_sent", "cover_sent", "inline_queries"]:
                conn.execute("INSERT OR IGNORE INTO counters (key,val) VALUES (?,0)", (k,))
            conn.commit()

    def touch_user(self, user_id: int):
        now = int(time.time())
        with self._conn() as conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
            if row:
                conn.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now, user_id))
            else:
                conn.execute("INSERT INTO users (user_id, first_seen, last_seen) VALUES (?,?,?)", (user_id, now, now))
            conn.commit()

    def inc(self, key: str, n: int = 1):
        with self._conn() as conn:
            conn.execute("UPDATE counters SET val = val + ? WHERE key=?", (n, key))
            conn.commit()

    def get_summary(self):
        with self._conn() as conn:
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            counters = dict(conn.execute("SELECT key,val FROM counters").fetchall())
        return users, counters
