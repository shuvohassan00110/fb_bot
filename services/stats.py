import sqlite3, time
class StatsDB:
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_seen INTEGER, last_seen INTEGER)")
            c.execute("CREATE TABLE IF NOT EXISTS counters (key TEXT PRIMARY KEY, val INTEGER)")
            for k in ["requests","cache_hits","zips_generated","albums_sent","profile_sent","cover_sent","inline_queries"]:
                c.execute("INSERT OR IGNORE INTO counters VALUES (?,0)", (k,))
            c.commit()

    def touch_user(self, uid):
        now=int(time.time())
        with sqlite3.connect(self.path) as c:
            r=c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,)).fetchone()
            if r: c.execute("UPDATE users SET last_seen=? WHERE user_id=?", (now,uid))
            else: c.execute("INSERT INTO users VALUES (?,?,?)",(uid,now,now))
            c.commit()

    def inc(self,k,n=1):
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE counters SET val=val+? WHERE key=?",(n,k)); c.commit()

    def summary(self):
        with sqlite3.connect(self.path) as c:
            users=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            cnt=dict(c.execute("SELECT key,val FROM counters").fetchall())
        return users,cnt
