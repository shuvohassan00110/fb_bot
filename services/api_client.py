import requests

def fetch_all(api_endpoint: str, fb_url: str, timeout=45):
    r = requests.get(api_endpoint, params={"url": fb_url}, timeout=timeout)
    return r.json()
