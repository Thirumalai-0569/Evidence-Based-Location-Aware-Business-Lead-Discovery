from pydantic import BaseModel, Field
from typing import Optional, List
class SearchRequest(BaseModel):
    location: str = Field(min_length=2, max_length=300)
    product_service: str = Field(min_length=2, max_length=300)
    category: Optional[str] = None
    keywords: List[str] = []
    radius_km: float = Field(default=5, gt=0, le=50)
class CsvImportResult(BaseModel):
    imported: int
    message: str
