from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.database import Base, engine
from backend import models  # register ORM models before create_all
from backend.routes.health import router as health_router
from backend.routes.search import router as search_router
from backend.routes.leads import router as leads_router
from backend.routes.export import router as export_router
from backend.routes.import_data import router as import_router
BASE=Path(__file__).resolve().parent.parent
(BASE/"data").mkdir(exist_ok=True)
Base.metadata.create_all(bind=engine)
app=FastAPI(title="Evidence-Based Business Lead Discovery",version="2.0.0",description="Location-aware business discovery with source evidence and transparent lead scoring")
app.include_router(health_router); app.include_router(search_router); app.include_router(leads_router); app.include_router(export_router); app.include_router(import_router)
# Mount frontend last so it cannot shadow API endpoints.
app.mount("/",StaticFiles(directory=str(BASE/"frontend"),html=True),name="frontend")
