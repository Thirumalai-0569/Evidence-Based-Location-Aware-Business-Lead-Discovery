from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from backend.database import get_db
from backend.schemas import SearchRequest
from backend.services.geocoding import geocode_location
from backend.connectors.overpass_connector import search_businesses
from backend.services.business_service import save_records, serialize_business
from backend.models.business import SearchHistory
router=APIRouter(prefix="/api/search",tags=["search"])
@router.post("/businesses")
def search(req:SearchRequest, db:Session=Depends(get_db)):
    try:
        place=geocode_location(req.location)
        records=search_businesses(place["latitude"],place["longitude"],req.radius_km,req.category)
        # Product/service and keywords are used in scoring/filter explanation, not represented as verified intent.
        saved=save_records(db,records,center=place,radius_km=req.radius_km,product_service=" ".join([req.product_service]+req.keywords),requested_category=req.category)
        history=SearchHistory(location=req.location,product_service=req.product_service,category=req.category or "",keywords=", ".join(req.keywords),radius_km=req.radius_km,results_count=len(saved)); db.add(history); db.commit()
        return {"status":"success","search_location":place["display_name"],"total":len(saved),"results":[serialize_business(x) for x in saved]}
    except ValueError as e: raise HTTPException(status_code=400,detail=str(e))
    except requests.RequestException as e: raise HTTPException(status_code=502,detail=f"External source request failed: {e}")
