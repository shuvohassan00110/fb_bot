import requests

class ApiClient:
    def __init__(self, api_all_endpoint: str, timeout: int):
        self.api = api_all_endpoint
        self.timeout = timeout

    def fetch(self, fb_url: str):
        r = requests.get(self.api, params={"url": fb_url}, timeout=self.timeout)
        try:
            return r.json()
        except Exception:
            return None
