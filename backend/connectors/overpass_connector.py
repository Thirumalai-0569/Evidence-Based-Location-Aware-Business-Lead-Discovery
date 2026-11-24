"""Polite Overpass client with caching, sequential fallback and clear errors."""
from __future__ import annotations

import logging
import threading
import time
from copy import deepcopy

import requests

from backend.config import (
    OVERPASS_URLS,
    OVERPASS_CONNECT_TIMEOUT,
    OVERPASS_READ_TIMEOUT,
    OVERPASS_QUERY_TIMEOUT,
    OVERPASS_CACHE_TTL_SECONDS,
    USER_AGENT,
)
from backend.utils.distance import haversine_km

logger = logging.getLogger(__name__)

CATEGORY_TAGS = {
    "education": '["amenity"~"college|university|school"]',
    "healthcare": '["amenity"~"hospital|clinic|doctors"]',
    "retail": '["shop"]',
    "food": '["amenity"~"restaurant|cafe|fast_food"]',
    "professional services": '["office"]',
    "automotive": '["shop"="car_repair"]',
    "hospitality": '["tourism"~"hotel|guest_house"]',
}

# One process-wide lock prevents multiple simultaneous requests from this app.
_request_lock = threading.Lock()
_cache_lock = threading.Lock()
_cache: dict[tuple, tuple[float, list[dict]]] = {}
_last_request_at = 0.0


class OverpassUnavailableError(requests.RequestException):
    """Raised when all configured Overpass endpoints fail temporarily."""


def _build_query(lat: float, lon: float, radius_m: int, tag: str) -> str:
    # The server-side timeout is distinct from the client's network timeout.
    return (
        f"[out:json][timeout:{OVERPASS_QUERY_TIMEOUT}];"
        f"(node(around:{radius_m},{lat},{lon}){tag};"
        f"way(around:{radius_m},{lat},{lon}){tag};"
        f"relation(around:{radius_m},{lat},{lon}){tag};);"
        "out center tags;"
    )


def _post_with_fallback(query: str) -> dict:
    global _last_request_at
    if not OVERPASS_URLS:
        raise OverpassUnavailableError("No Overpass endpoints are configured.")

    failures: list[str] = []
    # Do not send concurrent requests to public community infrastructure.
    with _request_lock:
        for endpoint in OVERPASS_URLS:
            wait = 1.0 - (time.monotonic() - _last_request_at)
            if wait > 0:
                time.sleep(wait)
            try:
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                    timeout=(OVERPASS_CONNECT_TIMEOUT, OVERPASS_READ_TIMEOUT),
                )
                _last_request_at = time.monotonic()
                if response.status_code in (429, 502, 503, 504):
                    failures.append(f"{endpoint}: HTTP {response.status_code}")
                    logger.warning("Overpass endpoint %s returned HTTP %s; trying configured fallback.", endpoint, response.status_code)
                    continue
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as exc:
                    failures.append(f"{endpoint}: invalid JSON response")
                    logger.warning("Overpass endpoint %s returned invalid JSON: %s", endpoint, exc)
                    continue
            except (requests.Timeout, requests.ConnectionError) as exc:
                _last_request_at = time.monotonic()
                failures.append(f"{endpoint}: {type(exc).__name__}")
                logger.warning("Overpass endpoint %s unavailable: %s", endpoint, exc)
                continue
            except requests.HTTPError as exc:
                # A 400 usually means a query/configuration problem, not an outage.
                raise OverpassUnavailableError(f"Overpass rejected the search query: {exc}") from exc
            except requests.RequestException as exc:
                failures.append(f"{endpoint}: {type(exc).__name__}")
                logger.warning("Overpass request failed for %s: %s", endpoint, exc)
                continue

    detail = "; ".join(failures) or "No endpoint returned a result"
    raise OverpassUnavailableError(
        "The OpenStreetMap search service is temporarily unavailable. "
        "Please try again in a minute or reduce the search radius. "
        f"Endpoint details: {detail}"
    )


def search_businesses(lat, lon, radius_km, category=None):
    if not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
        raise ValueError("Invalid latitude or longitude.")
    if not (0 < float(radius_km) <= 50):
        raise ValueError("Search radius must be greater than 0 and no more than 50 km.")

    radius_m = int(float(radius_km) * 1000)
    tag = CATEGORY_TAGS.get((category or "").lower(), '["name"]')
    # Only claim a category match when the query was actually filtered by that category.
    matched_category = (category or "").strip() if (category or "").lower() in CATEGORY_TAGS else ""
    cache_key = (round(float(lat), 5), round(float(lon), 5), radius_m, (category or "").lower())
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < OVERPASS_CACHE_TTL_SECONDS:
            return deepcopy(cached[1])
        if cached:
            _cache.pop(cache_key, None)

    payload = _post_with_fallback(_build_query(float(lat), float(lon), radius_m, tag))
    output = []
    seen = set()
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        element_lat = element.get("lat") or element.get("center", {}).get("lat")
        element_lon = element.get("lon") or element.get("center", {}).get("lon")
        if element_lat is None or element_lon is None:
            continue
        distance = haversine_km(float(lat), float(lon), float(element_lat), float(element_lon))
        if distance > float(radius_km):
            continue
        source_id = f"{element.get('type')}/{element.get('id')}"
        if source_id in seen:
            continue
        seen.add(source_id)
        output.append({
            "name": name,
            "category": tags.get("amenity") or tags.get("shop") or tags.get("office") or tags.get("tourism") or "Unknown",
            "location": ", ".join(x for x in [tags.get("addr:street"), tags.get("addr:city"), tags.get("addr:postcode")] if x),
            "latitude": float(element_lat),
            "longitude": float(element_lon),
            "website": tags.get("website", ""),
            "distance_km": round(distance, 2),
            "matched_category": matched_category,
            "source": "OpenStreetMap",
            "source_record_id": source_id,
            "source_url": f"https://www.openstreetmap.org/{source_id}",
            "snippet": "OpenStreetMap name and tagged attributes",
        })

    with _cache_lock:
        _cache[cache_key] = (time.monotonic(), deepcopy(output))
    return output
