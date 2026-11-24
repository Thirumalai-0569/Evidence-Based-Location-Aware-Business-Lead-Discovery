import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'business_leads.db').as_posix()}")
NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org/search")
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
USER_AGENT = os.getenv("APP_USER_AGENT", "BusinessLeadDiscovery/2.0 (contact: replace-with-your-email@example.com)")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "25"))
# Overpass is a shared public service. Keep requests sequential, cache results,
# and use a separately operated fallback only when the primary is unavailable.
OVERPASS_URLS = [
    item.strip() for item in os.getenv(
        "OVERPASS_URLS",
        "https://overpass-api.de/api/interpreter,https://overpass.private.coffee/api/interpreter"
    ).split(",") if item.strip()
]
OVERPASS_CONNECT_TIMEOUT = float(os.getenv("OVERPASS_CONNECT_TIMEOUT", "10"))
OVERPASS_READ_TIMEOUT = float(os.getenv("OVERPASS_READ_TIMEOUT", "60"))
OVERPASS_QUERY_TIMEOUT = int(os.getenv("OVERPASS_QUERY_TIMEOUT", "45"))
OVERPASS_CACHE_TTL_SECONDS = int(os.getenv("OVERPASS_CACHE_TTL_SECONDS", "300"))
