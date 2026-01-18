import sqlite3
import time

class LogDB:
    def __init__(self, path="logs.sqlite"):
        self.path = path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                ts INTEGER,
                level TEXT,
                message TEXT
            )""")
            c.commit()

    def add(self, level: str, msg: str):
        with self._conn() as c:
            c.execute("INSERT INTO logs VALUES (?,?,?)", (int(time.time()), level, msg))
            c.execute("""
              DELETE FROM logs
              WHERE rowid NOT IN (SELECT rowid FROM logs ORDER BY ts DESC LIMIT 50)
            """)
            c.commit()

    def last(self, n=50):
        with self._conn() as c:
            return c.execute(
                "SELECT ts,level,message FROM logs ORDER BY ts DESC LIMIT ?", (n,)
            ).fetchall()
