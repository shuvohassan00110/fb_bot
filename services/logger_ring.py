from collections import deque
from datetime import datetime

class RingLogger:
    def __init__(self, maxlen=50):
        self.buf = deque(maxlen=maxlen)

    def add(self, level: str, msg: str):
        ts = datetime.utcnow().isoformat() + "Z"
        self.buf.appendleft(f"{ts} [{level}] {msg}")

    def tail(self, n=50):
        return list(self.buf)[:n]
