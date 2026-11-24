from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
class Business(Base):
    __tablename__ = "businesses"
    id=Column(Integer, primary_key=True, index=True)
    name=Column(String(300), nullable=False, index=True)
    normalized_name=Column(String(300), index=True)
    category=Column(String(150), default="Unknown")
    location=Column(String(500), default="")
    latitude=Column(Float)
    longitude=Column(Float)
    website=Column(String(1000), default="")
    website_domain=Column(String(300), index=True)
    distance_km=Column(Float)
    relevance_score=Column(Float, default=0)
    relevance_explanation=Column(Text, default="")
    verification_status=Column(String(40), default="unverified", index=True)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())
    evidences=relationship("Evidence", back_populates="business", cascade="all, delete-orphan")
    __table_args__=(UniqueConstraint("name", "latitude", "longitude", name="uq_business_name_coordinates"),)
class Evidence(Base):
    __tablename__="evidence"
    id=Column(Integer, primary_key=True)
    business_id=Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    source=Column(String(100), nullable=False)
    source_record_id=Column(String(300), default="")
    source_url=Column(String(1200), default="")
    evidence_type=Column(String(100), default="discovery")
    snippet=Column(Text, default="")
    retrieved_at=Column(DateTime(timezone=True), server_default=func.now())
    business=relationship("Business", back_populates="evidences")
class SearchHistory(Base):
    __tablename__="search_history"
    id=Column(Integer, primary_key=True)
    location=Column(String(300), nullable=False)
    product_service=Column(String(300), default="")
    category=Column(String(150), default="")
    keywords=Column(String(500), default="")
    radius_km=Column(Float, default=5)
    results_count=Column(Integer, default=0)
    created_at=Column(DateTime(timezone=True), server_default=func.now())
class AuditEvent(Base):
    __tablename__="audit_events"
    id=Column(Integer, primary_key=True)
    business_id=Column(Integer, ForeignKey("businesses.id"), nullable=True)
    event_type=Column(String(100), nullable=False)
    details=Column(Text, default="")
    created_at=Column(DateTime(timezone=True), server_default=func.now())
