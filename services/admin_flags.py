import sqlite3

class AdminFlags:
    def __init__(self, db_path="admin_flags.sqlite"):
        self.db = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db)

    def _init(self):
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS flags (
                key TEXT PRIMARY KEY,
                val INTEGER NOT NULL
            )""")
            for k in ["force_join", "maintenance"]:
                c.execute("INSERT OR IGNORE INTO flags VALUES (?,1)", (k,))
            c.commit()

    def get(self, key: str) -> bool:
        with self._conn() as c:
            r = c.execute("SELECT val FROM flags WHERE key=?", (key,)).fetchone()
            return bool(r[0]) if r else False

    def set(self, key: str, val: bool):
        with self._conn() as c:
            c.execute("UPDATE flags SET val=? WHERE key=?", (1 if val else 0, key))
            c.commit()
