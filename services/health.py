import requests, time
def check_api_health(url, timeout=10):
    try:
        s=time.time(); r=requests.get(url,timeout=timeout)
        return True, r.status_code, round(time.time()-s,2)
    except Exception as e:
        return False, str(e), None
