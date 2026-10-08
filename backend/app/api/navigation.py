from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import DocumentModel
from app.schemas.navigation import VerifiedNextStep, ProviderContactInput
from app.schemas.facts import MedicalFact
from app.services.navigation.care_navigator import CareNavigator
from app.utils.audit import record_audit_event

router = APIRouter(prefix="/documents", tags=["Navigation"])

@router.get("/{id}/next-step", response_model=VerifiedNextStep)
def get_verified_next_step(id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    confirmed_raw = doc.confirmed_facts or doc.extracted_facts or []
    facts = [MedicalFact(**f) for f in confirmed_raw]

    next_step = CareNavigator.extract_verified_next_step(
        document_text=doc.raw_text or "",
        confirmed_facts=facts
    )

    if doc.saved_provider:
        next_step.saved_provider = doc.saved_provider

    doc.next_step = next_step.dict()
    db.commit()

    return next_step

@router.post("/{id}/provider", response_model=VerifiedNextStep)
def save_provider_contact(
    id: str,
    provider: ProviderContactInput,
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    provider_dict = provider.dict()
    doc.saved_provider = provider_dict
    
    if doc.next_step:
        ns = dict(doc.next_step)
        ns["saved_provider"] = provider_dict
        doc.next_step = ns

    db.commit()

    record_audit_event(db, "PROVIDER_SAVED", id, {"provider_name": provider.provider_name})

    return doc.next_step
