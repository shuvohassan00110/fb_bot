import sqlite3
class AdminFlags:
    def __init__(self,path):
        self.path=path
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS flags (key TEXT PRIMARY KEY, val INTEGER)")
            for k in ("force_join","maintenance"):
                c.execute("INSERT OR IGNORE INTO flags VALUES (?,1)",(k,))
            c.commit()
    def get(self,k):
        with sqlite3.connect(self.path) as c:
            r=c.execute("SELECT val FROM flags WHERE key=?",(k,)).fetchone()
            return bool(r[0]) if r else False
    def set(self,k,v):
        with sqlite3.connect(self.path) as c:
            c.execute("UPDATE flags SET val=? WHERE key=?",(1 if v else 0,k)); c.commit()
