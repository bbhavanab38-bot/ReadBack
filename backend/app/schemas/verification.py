from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from app.schemas.facts import FactCategory

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"

class MismatchType(str, Enum):
    NUMERIC_MISMATCH = "NUMERIC_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    CRITICAL_DRUG_MISMATCH = "CRITICAL_DRUG_MISMATCH"
    CRITICAL_DOSAGE_MISMATCH = "CRITICAL_DOSAGE_MISMATCH"
    CRITICAL_FREQUENCY_MISMATCH = "CRITICAL_FREQUENCY_MISMATCH"
    CRITICAL_ROUTE_MISMATCH = "CRITICAL_ROUTE_MISMATCH"
    CRITICAL_DURATION_MISMATCH = "CRITICAL_DURATION_MISMATCH"
    CRITICAL_NEGATION_FLIP = "CRITICAL_NEGATION_FLIP"
    FLAG_MISMATCH = "FLAG_MISMATCH"
    FIELD_OMITTED = "FIELD_OMITTED"
    UNSUPPORTED_ADDITION = "UNSUPPORTED_ADDITION"

class FieldComparison(BaseModel):
    field_id: str
    field_name: str
    category: FactCategory
    original_display: str
    explanation_display: str
    status: str  # "PASS", "MISMATCH", "NEEDS_REVIEW", "MISSING"
    mismatch_type: Optional[MismatchType] = None
    is_critical: bool = False
    details: str
    source_text: Optional[str] = None
    explanation_source_text: Optional[str] = None

class VerificationResult(BaseModel):
    overall_status: VerificationStatus
    fidelity_score: float  # Percentage 0.0 - 100.0
    total_fields_checked: int
    passed_count: int
    review_count: int
    critical_mismatches_count: int
    field_comparisons: List[FieldComparison]
    blocked_reason: Optional[str] = None
    what_readback_could_not_verify: List[str] = []
    explanation_safe_to_display: bool = True
