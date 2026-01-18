import json, sqlite3, time

class SqliteCache:
    def __init__(self, db_path: str, ttl_seconds: int):
        self.db_path = db_path
        self.ttl = ttl_seconds
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, ts INTEGER)")
            c.commit()

    def get(self, key):
        now = int(time.time())
        with self._conn() as c:
            r = c.execute("SELECT value, ts FROM cache WHERE key=?", (key,)).fetchone()
            if not r: return None
            val, ts = r
            if now - ts > self.ttl:
                c.execute("DELETE FROM cache WHERE key=?", (key,))
                c.commit()
                return None
            return json.loads(val)

    def set(self, key, value):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (key, json.dumps(value), int(time.time())))
            c.commit()
