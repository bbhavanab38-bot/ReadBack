from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import DocumentModel
from app.schemas.document import ExplanationRequest, ExplanationResponse
from app.schemas.facts import MedicalFact
from app.services.extraction.explainer import ExplanationEngine
from app.services.safety.guardrails import SafetyGuardrails
from app.utils.audit import record_audit_event

router = APIRouter(prefix="/documents", tags=["Explanation"])

@router.post("/{id}/explain", response_model=ExplanationResponse)
def explain_document(
    id: str,
    payload: ExplanationRequest,
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    facts_data = doc.confirmed_facts or doc.extracted_facts or []
    if not facts_data:
        raise HTTPException(status_code=400, detail="No extracted or confirmed facts found for document.")

    facts = [MedicalFact(**f) for f in facts_data]

    # Safety validation
    is_safe, safety_msg = SafetyGuardrails.validate_safety(doc.raw_text or "")
    if not is_safe:
        raise HTTPException(status_code=400, detail=safety_msg)

    # Generate patient-friendly explanation in selected language
    explanation_response = ExplanationEngine.generate_explanation(
        document_id=id,
        facts=facts,
        language=payload.language,
        corrupt_mode=payload.corrupt_for_testing
    )

    doc.explanation_text = explanation_response.explanation_text
    doc.selected_language = payload.language
    doc.independent_facts = []
    doc.verification_result = None
    db.commit()

    record_audit_event(db, "EXPLANATION_GENERATED", id, {
        "language": payload.language,
        "corrupt_for_testing": payload.corrupt_for_testing
    })

    return explanation_response.model_copy(update={"explanation_text": ""})
