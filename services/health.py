import requests
import time

def check_api_health(api_url: str, timeout=10):
    try:
        start = time.time()
        r = requests.get(api_url, timeout=timeout)
        latency = round(time.time() - start, 2)
        return True, r.status_code, latency
    except Exception as e:
        return False, str(e), None
