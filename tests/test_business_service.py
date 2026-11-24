import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.database import Base
from backend import models  # noqa: F401  (registers ORM models)
from backend.models.business import Evidence
from backend.services.business_service import save_records

@pytest.fixture()
def db():
    # Isolated in-memory database: never touches data/business_leads.db
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()

def osm(distance=2.0, name="Test Engineering College", lat=12.0, lon=79.0, rid="node/1", matched="Education"):
    return {"name": name, "category": "college", "location": "Main Rd", "latitude": lat, "longitude": lon,
            "website": "", "distance_km": distance, "matched_category": matched, "source": "OpenStreetMap",
            "source_record_id": rid, "source_url": f"https://www.openstreetmap.org/{rid}", "snippet": "OSM"}

def csv_rec(lat=12.0001, lon=79.0001, name="Test Engineering College"):
    return {"name": name, "category": "Education", "location": "", "latitude": lat, "longitude": lon,
            "website": "", "distance_km": None, "source": "Approved CSV Dataset", "source_record_id": "2",
            "source_url": "", "snippet": "csv"}

def test_category_fit_is_full_when_search_was_filtered_by_that_category(db):
    b = save_records(db, [osm()], radius_km=15, product_service="website", requested_category="Education")[0]
    assert "Category fit: 25/25" in b.relevance_explanation

def test_category_fit_is_low_when_result_did_not_match_requested_category(db):
    b = save_records(db, [osm(matched="")], radius_km=15, product_service="website", requested_category="Healthcare")[0]
    assert "Category fit: 5/25" in b.relevance_explanation

def test_distance_is_refreshed_by_a_later_search(db):
    save_records(db, [osm(distance=2.0)], radius_km=15)
    b = save_records(db, [osm(distance=9.5)], radius_km=15)[0]
    assert b.distance_km == 9.5

def test_csv_import_does_not_erase_existing_distance(db):
    save_records(db, [osm(distance=2.0)], radius_km=15)
    b = save_records(db, [csv_rec()])[0]
    assert b.distance_km == 2.0

def test_same_business_from_two_sources_is_merged_with_both_evidence_rows(db):
    save_records(db, [osm()], radius_km=15)
    b = save_records(db, [csv_rec()])[0]
    assert len(b.evidences) == 2
    assert {e.source for e in b.evidences} == {"OpenStreetMap", "Approved CSV Dataset"}
    # Source count alone never verifies a record (see determine_verification_status).
    assert b.verification_status == "unverified"

def test_repeating_a_search_does_not_duplicate_evidence(db):
    save_records(db, [osm()], radius_km=15)
    save_records(db, [osm()], radius_km=15)
    assert db.query(Evidence).count() == 1

def test_same_name_far_apart_is_not_merged(db):
    a = save_records(db, [osm(lat=12.0, lon=79.0, rid="node/1")], radius_km=15)[0]
    b = save_records(db, [osm(lat=13.5, lon=80.5, rid="node/2")], radius_km=15)[0]
    assert a.id != b.id
