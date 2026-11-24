import requests
import pytest
from backend.connectors import overpass_connector as oc

class FakeResponse:
    status_code = 200
    def raise_for_status(self):
        return None
    def json(self):
        return {"elements": [{"type": "node", "id": 1, "lat": 12.9165, "lon": 79.1325,
                              "tags": {"name": "Test Engineering College", "amenity": "college"}}]}

def test_fallback_after_primary_timeout(monkeypatch):
    calls = []
    monkeypatch.setattr(oc, "OVERPASS_URLS", ["https://primary.test/interpreter", "https://fallback.test/interpreter"])
    monkeypatch.setattr(oc, "_request_lock", __import__("threading").Lock())
    monkeypatch.setattr(oc, "_last_request_at", 0.0)
    def fake_post(url, **kwargs):
        calls.append(url)
        if "primary" in url:
            raise requests.Timeout("simulated timeout")
        return FakeResponse()
    monkeypatch.setattr(oc.requests, "post", fake_post)
    monkeypatch.setattr(oc, "_cache", {})
    result = oc.search_businesses(12.9165, 79.1325, 5, "education")
    assert calls == ["https://primary.test/interpreter", "https://fallback.test/interpreter"]
    assert result[0]["name"] == "Test Engineering College"

def test_successful_result_is_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(oc, "OVERPASS_URLS", ["https://primary.test/interpreter"])
    monkeypatch.setattr(oc, "_request_lock", __import__("threading").Lock())
    monkeypatch.setattr(oc, "_last_request_at", 0.0)
    monkeypatch.setattr(oc, "_cache", {})
    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse()
    monkeypatch.setattr(oc.requests, "post", fake_post)
    first = oc.search_businesses(12.9165, 79.1325, 5, "education")
    second = oc.search_businesses(12.9165, 79.1325, 5, "education")
    assert first == second
    assert len(calls) == 1

def test_clear_error_when_all_endpoints_timeout(monkeypatch):
    monkeypatch.setattr(oc, "OVERPASS_URLS", ["https://primary.test/interpreter"])
    monkeypatch.setattr(oc, "_request_lock", __import__("threading").Lock())
    monkeypatch.setattr(oc, "_last_request_at", 0.0)
    monkeypatch.setattr(oc, "_cache", {})
    monkeypatch.setattr(oc.requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.Timeout("slow")))
    with pytest.raises(oc.OverpassUnavailableError, match="temporarily unavailable"):
        oc.search_businesses(12.9165, 79.1325, 5, "education")

def test_results_record_the_category_filter_that_produced_them(monkeypatch):
    monkeypatch.setattr(oc, "OVERPASS_URLS", ["https://primary.test/interpreter"])
    monkeypatch.setattr(oc, "_request_lock", __import__("threading").Lock())
    monkeypatch.setattr(oc, "_last_request_at", 0.0)
    monkeypatch.setattr(oc, "_cache", {})
    monkeypatch.setattr(oc.requests, "post", lambda *a, **k: FakeResponse())
    assert oc.search_businesses(12.9165, 79.1325, 5, "Education")[0]["matched_category"] == "Education"
    monkeypatch.setattr(oc, "_cache", {})
    # No category (or an unknown one) must not claim a category match.
    assert oc.search_businesses(12.9165, 79.1325, 5, None)[0]["matched_category"] == ""
