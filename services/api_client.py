import requests
from typing import Dict, Any, Optional

class ApiClient:
    def __init__(self, api_all_endpoint: str, timeout: int):
        self.api = api_all_endpoint
        self.timeout = timeout

    def fetch(self, fb_url: str) -> Optional[Dict[str, Any]]:
        r = requests.get(self.api, params={"url": fb_url}, timeout=self.timeout)
        try:
            data = r.json()
        except Exception:
            return None
        return data
