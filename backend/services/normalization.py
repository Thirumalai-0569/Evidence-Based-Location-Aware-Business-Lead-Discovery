import re
from urllib.parse import urlparse
def normalize_name(name): return re.sub(r"[^a-z0-9]", "", (name or "").lower())
def normalize_domain(url):
    if not url: return ""
    candidate=url.strip()
    if not candidate.startswith(("http://","https://")): candidate="https://"+candidate
    host=urlparse(candidate).netloc.lower().removeprefix("www.")
    return host.split(":")[0]
