from backend.services.normalization import normalize_name
def score_lead(business, product_service, requested_category, radius_km, evidence_count):
    parts=[]
    distance=business.get("distance_km")
    geo=25 if distance is not None and distance<=radius_km else 10
    parts.append(f"Geographic match: {geo}/25")
    # OSM stores raw tag values ("college", "school") while users pick a label ("Education").
    # The connector records which category filter produced a result in "matched_category".
    requested=(requested_category or "").strip().lower()
    actual=(business.get("category") or "").lower()
    matched=(business.get("matched_category") or "").strip().lower()
    cat=25 if requested and (requested in actual or requested==matched) else (15 if not requested else 5)
    parts.append(f"Category fit: {cat}/25")
    # Keyword overlap is a transparent heuristic, not proof of customer intent.
    words={w.lower() for w in (product_service or "").split() if len(w)>3}
    hay=(business.get("name","")+" "+business.get("category","")+" "+business.get("location","")).lower()
    match=len(words & set(hay.split()))
    product=min(25, 5+match*10)
    parts.append(f"Product/service text match (heuristic): {product}/25")
    evidence=min(25, evidence_count*12.5)
    parts.append(f"Evidence coverage: {evidence}/25")
    total=round(geo+cat+product+evidence,1)
    return total, "; ".join(parts)+". Product/service fit is a preliminary text-based inference, not confirmed buying intent."
