from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.facts import MedicalFact
from app.schemas.verification import VerificationResult
from app.schemas.navigation import VerifiedNextStep

class DocumentBase(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    document_type: str
    page_count: int = 1
    ocr_quality: float = 0.95
    created_at: datetime
    updated_at: datetime

class DocumentDetail(DocumentBase):
    raw_text: Optional[str] = None
    extracted_facts: List[MedicalFact] = []
    confirmed_facts: List[MedicalFact] = []
    selected_language: str = "en"
    explanation_text: Optional[str] = None
    explanation_pending_verification: bool = False
    verification_result: Optional[VerificationResult] = None
    next_step: Optional[VerifiedNextStep] = None
    file_url: Optional[str] = None

class FactConfirmationRequest(BaseModel):
    confirmed_facts: List[MedicalFact]

class ExplanationRequest(BaseModel):
    language: str = "en"  # "en", "kn", "hi", "ta"
    corrupt_for_testing: Optional[str] = None  # None, "number", "drug", "dosage", "negation", "flag"

class ExplanationResponse(BaseModel):
    document_id: str
    language: str
    explanation_text: str
    summary_bullet_points: List[str]
    term_definitions: Dict[str, str] = {}
    is_safe: bool = True

class DocumentComparisonItem(BaseModel):
    document_id: str
    document_name: str
    date: Optional[str] = None
    facts: List[MedicalFact] = []

class ConflictItem(BaseModel):
    field_name: str
    category: str
    doc_a_value: str
    doc_b_value: str
    doc_a_name: str
    doc_b_name: str
    conflict_type: str
    warning_message: str

class DocumentComparisonResult(BaseModel):
    has_conflicts: bool
    conflicts: List[ConflictItem] = []
    timeline: List[Dict[str, Any]] = []
    summary: str
