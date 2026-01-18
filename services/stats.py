import threading
from dataclasses import dataclass, field
from typing import Dict, Set

@dataclass
class RuntimeState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    force_join: bool = True
    maintenance: bool = False
    last_url: Dict[int, str] = field(default_factory=dict)
    users_seen: Set[int] = field(default_factory=set)
    requests_count: int = 0

    def set_force_join(self, v: bool):
        with self.lock: self.force_join = v

    def set_maintenance(self, v: bool):
        with self.lock: self.maintenance = v

    def save_url(self, uid: int, url: str):
        with self.lock:
            self.last_url[uid] = url
            self.users_seen.add(uid)

    def get_url(self, uid: int):
        with self.lock:
            return self.last_url.get(uid)

    def bump(self):
        with self.lock:
            self.requests_count += 1
