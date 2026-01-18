import time

class TTLCache:
    def __init__(self, ttl_sec: int):
        self.ttl = ttl_sec
        self.store = {}  # key -> (exp, value)

    def get(self, key):
        item = self.store.get(key)
        if not item:
            return None
        exp, val = item
        if time.time() > exp:
            self.store.pop(key, None)
            return None
        return val

    def set(self, key, val):
        self.store[key] = (time.time() + self.ttl, val)

    def purge(self):
        self.store.clear()

    def size(self):
        return len(self.store)
