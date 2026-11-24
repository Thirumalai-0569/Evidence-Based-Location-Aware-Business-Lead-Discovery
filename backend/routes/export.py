from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import StringIO
import csv
from backend.database import get_db
from backend.models.business import Business
router=APIRouter(tags=["export"])
def safe_cell(value):
    s="" if value is None else str(value)
    if isinstance(value, str) and s.startswith(("=","+","-","@")): return "'"+s
    return s
@router.get("/api/export/csv")
def export_csv(ids:str|None=Query(default=None),db:Session=Depends(get_db)):
    q=db.query(Business)
    if ids:
        try: id_list=[int(x) for x in ids.split(",") if x.strip()]
        except ValueError: id_list=[]
        q=q.filter(Business.id.in_(id_list))
    rows=q.all(); output=StringIO(); writer=csv.writer(output)
    writer.writerow(["id","name","category","location","latitude","longitude","website","distance_km","relevance_score","relevance_explanation","verification_status"])
    for b in rows: writer.writerow([safe_cell(x) for x in [b.id,b.name,b.category,b.location,b.latitude,b.longitude,b.website,b.distance_km,b.relevance_score,b.relevance_explanation,b.verification_status]])
    output.seek(0)
    return StreamingResponse(iter(["\ufeff"+output.getvalue()]),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=business_leads.csv"})
