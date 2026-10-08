from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import DocumentModel
from app.schemas.verification import VerificationResult
from app.schemas.facts import MedicalFact
from app.services.extraction.independent_extractor import IndependentExtractor
from app.services.verification.engine import VerificationEngine
from app.utils.audit import record_audit_event
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Verification"])

@router.post("/{id}/verify", response_model=VerificationResult)
def verify_document_explanation(
    id: str,
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not doc.explanation_text:
        raise HTTPException(status_code=400, detail="Cannot verify without generated explanation.")

    confirmed_raw = doc.confirmed_facts or doc.extracted_facts or []
    confirmed_facts = [MedicalFact(**f) for f in confirmed_raw]

    # Independent fact extraction directly from explanation text
    independent_facts = IndependentExtractor.extract_from_explanation(
        explanation_text=doc.explanation_text,
        expected_facts=confirmed_facts
    )
    doc.independent_facts = [f.dict() for f in independent_facts]

    # Field-level verification engine
    result = VerificationEngine.verify(
        confirmed_facts=confirmed_facts,
        explanation_facts=independent_facts,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD
    )

    doc.verification_result = result.dict()
    db.commit()

    record_audit_event(db, "VERIFICATION_COMPLETED", id, {
        "status": result.overall_status.value,
        "fidelity_score": result.fidelity_score,
        "critical_mismatches_count": result.critical_mismatches_count,
        "passed_count": result.passed_count
    })

    return result

@router.get("/{id}/verification", response_model=VerificationResult)
def get_document_verification(id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not doc.verification_result:
        raise HTTPException(status_code=404, detail="Verification has not yet been executed for this document.")

    return doc.verification_result
