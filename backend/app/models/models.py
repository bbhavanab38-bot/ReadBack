from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from datetime import datetime
import uuid
from app.models.database import Base

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_type = Column(String, default="application/pdf")
    file_size = Column(Integer, default=0)
    file_path = Column(String, nullable=True)
    document_type = Column(String, default="lab_report")
    page_count = Column(Integer, default=1)
    ocr_quality = Column(Float, default=0.95)
    raw_text = Column(Text, nullable=True)
    
    # Structured representations stored as JSON
    extracted_facts = Column(JSON, default=list)
    confirmed_facts = Column(JSON, default=list)
    
    # Explanation and verification
    selected_language = Column(String, default="en")
    explanation_text = Column(Text, nullable=True)
    independent_facts = Column(JSON, default=list)
    verification_result = Column(JSON, nullable=True)
    
    # Verified Next Step
    next_step = Column(JSON, nullable=True)
    saved_provider = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=True, index=True)
    event_type = Column(String, nullable=False)  # DOCUMENT_UPLOADED, OCR_COMPLETED, etc.
    event_details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationResultModel(Base):
    __tablename__ = "evaluation_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String, default="Full Benchmark Run")
    timestamp = Column(DateTime, default=datetime.utcnow)
    dataset_size = Column(Integer, default=0)
    baseline_metrics = Column(JSON, default=dict)
    readback_metrics = Column(JSON, default=dict)
    language_breakdown = Column(JSON, default=list)
    category_breakdown = Column(JSON, default=dict)
    recent_failures = Column(JSON, default=list)
