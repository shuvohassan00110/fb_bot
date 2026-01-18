import sqlite3, time
class LogDB:
    def __init__(self,path):
        self.path=path
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS logs (ts INTEGER, level TEXT, msg TEXT)"); c.commit()
    def add(self,l,m):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO logs VALUES (?,?,?)",(int(time.time()),l,m))
            c.execute("DELETE FROM logs WHERE rowid NOT IN (SELECT rowid FROM logs ORDER BY ts DESC LIMIT 50)")
            c.commit()
    def last(self,n=50):
        with sqlite3.connect(self.path) as c:
            return c.execute("SELECT ts,level,msg FROM logs ORDER BY ts DESC LIMIT ?",(n,)).fetchall()
