from pydantic import BaseModel
from typing import Optional, List

class VerifiedNextStep(BaseModel):
    has_next_step: bool
    service_name: Optional[str] = None
    timing: Optional[str] = None
    department_or_specialty: Optional[str] = None
    source_text: Optional[str] = None
    page: Optional[int] = None
    is_explicit: bool = False
    verification_status: str = "UNVERIFIED"  # "VERIFIED", "NO_EXPLICIT_INSTRUCTION", "UNSUPPORTED_REJECTED"
    rationale: str
    saved_provider: Optional[dict] = None

class ProviderContactInput(BaseModel):
    provider_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    clinic_or_hospital: Optional[str] = None
    notes: Optional[str] = None
