from enum import Enum
from typing import List

from pydantic import BaseModel

from app.schemas.facts import MedicalFact
from app.schemas.verification import VerificationResult


class FidelityFailureType(str, Enum):
    NUMERIC_VALUE_CHANGED = "numeric_value_changed"
    UNIT_CHANGED = "unit_changed"
    DRUG_NAME_CHANGED = "drug_name_changed"
    DOSAGE_CHANGED = "dosage_changed"
    FREQUENCY_CHANGED = "frequency_changed"
    NEGATION_FLIPPED = "negation_flipped"
    ABNORMAL_FLAG_CHANGED = "abnormal_flag_changed"
    IMPORTANT_FACT_OMITTED = "important_fact_omitted"


class FidelitySimulationRequest(BaseModel):
    failure_type: FidelityFailureType


class FidelitySimulationResponse(BaseModel):
    document_id: str
    demo_label: str = "DEMO: INTENTIONALLY CORRUPTED AI OUTPUT"
    failure_type: FidelityFailureType
    original_explanation: str
    simulated_explanation: str
    original_facts: List[MedicalFact]
    reextracted_facts: List[MedicalFact]
    verification_result: VerificationResult