import time, requests
from backend.config import NOMINATIM_URL, USER_AGENT, REQUEST_TIMEOUT
_last_call=0.0
_cache={}
def geocode_location(location: str):
    global _last_call
    key=location.strip().lower()
    if key in _cache: return _cache[key]
    # Public Nominatim policy: max one request/second; use a descriptive contact User-Agent.
    wait=1.05-(time.monotonic()-_last_call)
    if wait>0: time.sleep(wait)
    r=requests.get(NOMINATIM_URL, params={"q":location,"format":"jsonv2","limit":1}, headers={"User-Agent":USER_AGENT}, timeout=REQUEST_TIMEOUT)
    _last_call=time.monotonic(); r.raise_for_status(); data=r.json()
    if not data: raise ValueError(f"Location not found: {location}")
    result={"latitude":float(data[0]["lat"]),"longitude":float(data[0]["lon"]),"display_name":data[0].get("display_name",location)}
    _cache[key]=result
    return result
