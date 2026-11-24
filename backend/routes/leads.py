from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.business import Business, SearchHistory
from backend.services.business_service import serialize_business
router=APIRouter(tags=["leads"])
@router.get("/api/leads")
def list_leads(db:Session=Depends(get_db), status:str|None=None):
    q=db.query(Business)
    if status: q=q.filter(Business.verification_status==status)
    return {"total":q.count(),"results":[serialize_business(x) for x in q.order_by(Business.id.desc()).limit(500).all()]}
@router.get("/api/leads/{lead_id}")
def lead_detail(lead_id:int,db:Session=Depends(get_db)):
    b=db.query(Business).filter_by(id=lead_id).first()
    if not b: raise HTTPException(status_code=404,detail="Lead not found")
    return serialize_business(b)
@router.get("/api/history")
def history(db:Session=Depends(get_db)):
    rows=db.query(SearchHistory).order_by(SearchHistory.id.desc()).limit(100).all()
    return [{"id":x.id,"location":x.location,"product_service":x.product_service,"category":x.category,"radius_km":x.radius_km,"results_count":x.results_count,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]
