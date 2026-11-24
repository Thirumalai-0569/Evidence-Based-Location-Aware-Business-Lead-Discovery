
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.models.business import Business, Evidence
from backend.services.normalization import (
    normalize_name,
    normalize_domain,
)
from backend.services.scoring import score_lead
from backend.utils.distance import haversine_km


# --------------------------------------------------
# 1. Helper functions
# --------------------------------------------------

def to_float(value):
    """Convert coordinates or distance to float safely."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_source_count(db: Session, business_id: int) -> int:
    """Count distinct evidence sources for a business."""

    sources = (
        db.query(Evidence.source)
        .filter(Evidence.business_id == business_id)
        .distinct()
        .all()
    )

    return len({
        source[0]
        for source in sources
        if source[0]
    })


# --------------------------------------------------
# 2. Verification status
# --------------------------------------------------

def determine_verification_status(rec, source_count):
    """
    Determine business verification status.

    Verification information must come from actual
    comparisons against reliable evidence.

    Expected verification fields:
        name_match
        address_match
        website_match
        reliable_evidence
        independent_sources_confirmed
        identity_conflict
    """

    verification = rec.get("verification") or {}

    name_match = verification.get("name_match") is True
    address_match = verification.get("address_match") is True
    website_match = verification.get("website_match") is True

    reliable_evidence = (
        verification.get("reliable_evidence") is True
    )

    independent_sources = (
        verification.get("independent_sources_confirmed") is True
        and source_count >= 2
    )

    identity_conflict = (
        verification.get("identity_conflict") is True
    )

    # Conflicting identity evidence
    if identity_conflict:
        return "rejected"

    # No reliable supporting evidence
    if not reliable_evidence:
        return "unverified"

    # A website match is required only when
    # the business has a website.
    website_required = bool(
        (rec.get("website") or "").strip()
    )

    website_ok = (
        not website_required or website_match
    )

    # Full verification
    if (
        name_match
        and address_match
        and website_ok
        and independent_sources
    ):
        return "verified"

    # Some details have been confirmed
    if name_match or address_match or website_match:
        return "partially_verified"

    return "unverified"


# --------------------------------------------------
# 3. Avoid downgrading existing verification status
# --------------------------------------------------

def update_verification_status(current_status, new_status):
    """
    Preserve a stronger existing status when a new
    search provides no stronger verification evidence.

    Explicit identity conflicts are handled separately.
    """

    priority = {
        "unverified": 0,
        "partially_verified": 1,
        "verified": 2,
        "rejected": 3,
    }

    if new_status == "rejected":
        return "rejected"

    if current_status == "rejected":
        return "rejected"

    current_priority = priority.get(current_status, 0)
    new_priority = priority.get(new_status, 0)

    if new_priority > current_priority:
        return new_status

    return current_status or new_status


# --------------------------------------------------
# 4. Find an existing business
# --------------------------------------------------

def find_existing_business(
    db: Session,
    normalized_name,
    website_domain,
    latitude,
    longitude,
):
    """
    Find an existing business using:
    1. Matching website domain
    2. Matching normalized name and nearby coordinates

    Matching names alone are not sufficient to merge
    two businesses.
    """

    conditions = []

    if website_domain:
        conditions.append(
            Business.website_domain == website_domain
        )

    if normalized_name:
        conditions.append(
            Business.normalized_name == normalized_name
        )

    if not conditions:
        return None

    candidates = (
        db.query(Business)
        .filter(or_(*conditions))
        .all()
    )

    for business in candidates:

        same_domain = bool(
            website_domain
            and business.website_domain
            and website_domain == business.website_domain
        )

        same_name = bool(
            normalized_name
            and business.normalized_name
            and normalized_name == business.normalized_name
        )

        near = False

        if (
            same_name
            and latitude is not None
            and longitude is not None
            and business.latitude is not None
            and business.longitude is not None
        ):
            distance = haversine_km(
                latitude,
                longitude,
                float(business.latitude),
                float(business.longitude),
            )

            near = distance <= 0.5

        if same_domain or near:
            return business

    return None


# --------------------------------------------------
# 5. Save evidence
# --------------------------------------------------

def save_evidence(db: Session, business_id: int, rec):
    """Save source evidence without duplicating identified records."""

    source = (rec.get("source") or "Unknown").strip()

    source_record_id = str(
        rec.get("source_record_id") or ""
    ).strip()

    source_url = (rec.get("source_url") or "").strip()

    query = db.query(Evidence).filter(
        Evidence.business_id == business_id,
        Evidence.source == source,
    )

    if source_record_id:
        query = query.filter(
            Evidence.source_record_id == source_record_id
        )
    elif source_url:
        query = query.filter(
            Evidence.source_url == source_url
        )
    else:
        # No reliable identifier is available to deduplicate
        query = None

    existing_evidence = (
        query.first() if query is not None else None
    )

    if existing_evidence:
        return existing_evidence

    evidence = Evidence(
        business_id=business_id,
        source=source,
        source_record_id=source_record_id,
        source_url=source_url,
        snippet=rec.get("snippet") or "",
    )

    db.add(evidence)
    db.flush()

    return evidence


# --------------------------------------------------
# 6. Main function: Save business records
# --------------------------------------------------

def save_records(
    db: Session,
    records,
    center=None,
    radius_km=5,
    product_service="",
    requested_category=None,
):
    """
    Save business records, collect evidence,
    determine verification status and calculate
    lead relevance scores.

    center is retained for compatibility with
    existing callers.
    """

    saved = []
    saved_ids = set()

    try:

        for rec in records:

            # --------------------------------------
            # A. Validate business name
            # --------------------------------------

            name = (rec.get("name") or "").strip()

            if not name:
                continue

            normalized_name = normalize_name(name)

            website = (
                rec.get("website") or ""
            ).strip()

            website_domain = normalize_domain(website)

            latitude = to_float(rec.get("latitude"))
            longitude = to_float(rec.get("longitude"))

            # --------------------------------------
            # B. Find existing business
            # --------------------------------------

            business = find_existing_business(
                db=db,
                normalized_name=normalized_name,
                website_domain=website_domain,
                latitude=latitude,
                longitude=longitude,
            )

            # --------------------------------------
            # C. Create or update business
            # --------------------------------------

            if business is None:

                business = Business(
                    name=name,
                    normalized_name=normalized_name,
                    category=rec.get("category") or "Unknown",
                    location=rec.get("location") or "",
                    latitude=latitude,
                    longitude=longitude,
                    website=website,
                    website_domain=website_domain,
                    distance_km=to_float(
                        rec.get("distance_km")
                    ),
                    verification_status="unverified",
                )

                db.add(business)
                db.flush()

            else:

                # Fill missing fields without blindly
                # overwriting existing business details.

                if not business.website and website:
                    business.website = website
                    business.website_domain = website_domain

                if (
                    not business.location
                    and rec.get("location")
                ):
                    business.location = rec.get("location")

                if (
                    not business.category
                    or business.category == "Unknown"
                ):
                    business.category = (
                        rec.get("category") or "Unknown"
                    )

                if (
                    business.latitude is None
                    and latitude is not None
                ):
                    business.latitude = latitude

                if (
                    business.longitude is None
                    and longitude is not None
                ):
                    business.longitude = longitude

                # Distance is relative to the current search centre, so a
                # fresh value always replaces the one from an earlier search.
                # Records without a distance (e.g. CSV imports) keep theirs.
                new_distance = to_float(rec.get("distance_km"))

                if new_distance is not None:
                    business.distance_km = new_distance

            # --------------------------------------
            # D. Save source evidence
            # --------------------------------------

            save_evidence(
                db=db,
                business_id=business.id,
                rec=rec,
            )

            db.flush()

            # --------------------------------------
            # E. Determine verification status
            # --------------------------------------

            source_count = get_source_count(
                db=db,
                business_id=business.id,
            )

            new_status = determine_verification_status(
                rec=rec,
                source_count=source_count,
            )

            business.verification_status = (
                update_verification_status(
                    current_status=business.verification_status,
                    new_status=new_status,
                )
            )

            # --------------------------------------
            # F. Calculate lead relevance
            # --------------------------------------

            evidence_count = (
                db.query(Evidence)
                .filter(
                    Evidence.business_id == business.id
                )
                .count()
            )

            payload = {
                "name": business.name,
                "category": business.category,
                "location": business.location,
                "distance_km": business.distance_km,
                "matched_category": rec.get("matched_category"),
            }

            (
                business.relevance_score,
                business.relevance_explanation,
            ) = score_lead(
                payload,
                product_service,
                requested_category,
                radius_km,
                evidence_count,
            )

            # --------------------------------------
            # G. Add unique business to result
            # --------------------------------------

            if business.id not in saved_ids:
                saved.append(business)
                saved_ids.add(business.id)

        # ------------------------------------------
        # H. Commit database changes
        # ------------------------------------------

        db.commit()

        return saved

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# 7. Serialize business details
# --------------------------------------------------

def serialize_business(b):

    return {
        "id": b.id,
        "name": b.name,
        "category": b.category,
        "location": b.location,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "website": b.website,
        "distance_km": b.distance_km,
        "relevance_score": b.relevance_score,
        "relevance_explanation": b.relevance_explanation,
        "verification_status": b.verification_status,

        "evidence": [
            {
                "source": e.source,
                "source_record_id": e.source_record_id,
                "source_url": e.source_url,
                "snippet": e.snippet,
                "retrieved_at": (
                    e.retrieved_at.isoformat()
                    if e.retrieved_at
                    else None
                ),
            }
            for e in b.evidences
        ],
    }
