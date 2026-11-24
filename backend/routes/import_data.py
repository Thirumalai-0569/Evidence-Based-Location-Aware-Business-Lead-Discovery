from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.connectors.csv_connector import load_approved_csv_bytes
from backend.services.business_service import save_records
router=APIRouter(prefix="/api/import",tags=["import"])
@router.post("/approved-csv")
async def import_csv(file:UploadFile=File(...),db:Session=Depends(get_db)):
    if not (file.filename or "").lower().endswith(".csv"): raise HTTPException(400,"Upload a CSV file")
    content=await file.read()
    if len(content)>5_000_000: raise HTTPException(413,"CSV must be 5 MB or smaller")
    # Parse the uploaded bytes directly (no temp file) so this also works on Windows.
    try: records=load_approved_csv_bytes(content)
    except ValueError as e: raise HTTPException(400,str(e))
    saved=save_records(db,records)
    return {"imported":len(saved),"message":"Imported from user-provided dataset. Confirm you have permission to use this dataset."}
