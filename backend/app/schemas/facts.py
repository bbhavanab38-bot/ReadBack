from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
from enum import Enum

class FactCategory(str, Enum):
    LABORATORY = "laboratory"
    MEDICATION = "medication"
    INSTRUCTION = "instruction"
    GENERAL = "general"

class FlagType(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    ABNORMAL = "ABNORMAL"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NONE = "NONE"

class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    page: int = 1

class MedicalFact(BaseModel):
    field_id: str
    category: FactCategory
    name: str
    value: Optional[Union[float, int, str]] = None
    value_type: str = "numeric"  # numeric, string, boolean
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[FlagType] = None
    
    # Medication specifics
    strength: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration: Optional[str] = None
    
    # Instruction specifics
    action: Optional[str] = None
    negation: bool = False  # False = normal affirmative, True = negated ("do not", "never")
    condition: Optional[str] = None
    timing: Optional[str] = None
    instruction_text: Optional[str] = None
    
    # Provenance and Confidence
    source_text: str
    page: int = 1
    bbox: Optional[BoundingBox] = None
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    user_confirmed: bool = False
    edited: bool = False

class StructuredExtractionResult(BaseModel):
    document_type: str = "lab_report"
    patient_identifier_redacted: bool = True
    facts: List[MedicalFact] = []
    unparsed_sections: List[str] = []
    overall_confidence: float = 1.0
