from backend.services.scoring import score_lead
def test_score_is_bounded_and_explained():
    score, explanation=score_lead({"name":"ABC College","category":"education","location":"Vellore","distance_km":2},"website development","education",15,2)
    assert 0 <= score <= 100
    assert "Geographic match" in explanation
    assert "not confirmed buying intent" in explanation

def test_matched_category_gives_full_category_fit_for_raw_osm_tags():
    # OSM stores raw tag values ("college"); the user picks a label ("Education").
    _, explanation = score_lead({"name": "ABC", "category": "college", "matched_category": "Education"}, "", "Education", 5, 1)
    assert "Category fit: 25/25" in explanation

def test_category_fit_without_match_is_low_and_without_request_is_neutral():
    assert "Category fit: 5/25" in score_lead({"name": "ABC", "category": "college"}, "", "Healthcare", 5, 1)[1]
    assert "Category fit: 15/25" in score_lead({"name": "ABC", "category": "college"}, "", None, 5, 1)[1]
