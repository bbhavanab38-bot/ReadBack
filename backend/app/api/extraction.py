from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.models import DocumentModel
from app.schemas.document import FactConfirmationRequest, DocumentDetail
from app.schemas.facts import StructuredExtractionResult, MedicalFact
from app.services.extraction.parser import DocumentFactParser
from app.utils.audit import record_audit_event

router = APIRouter(prefix="/documents", tags=["Extraction"])

@router.post("/{id}/extract", response_model=StructuredExtractionResult)
def extract_document_facts(id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    text = doc.raw_text or ""
    res = DocumentFactParser.parse_document_text(text, document_type=doc.document_type)
    
    doc.extracted_facts = [f.dict() for f in res.facts]
    if not doc.confirmed_facts:
        doc.confirmed_facts = doc.extracted_facts
    db.commit()
    
    record_audit_event(db, "EXTRACTION_COMPLETED", id, {"fact_count": len(res.facts)})
    return res

@router.post("/{id}/confirm", response_model=DocumentDetail)
def confirm_document_facts(
    id: str,
    payload: FactConfirmationRequest,
    db: Session = Depends(get_db)
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    confirmed_list = []
    for f in payload.confirmed_facts:
        f_dict = f.dict()
        f_dict["user_confirmed"] = True
        f_dict["confidence"] = max(f.confidence, 0.98)
        confirmed_list.append(f_dict)
    doc.confirmed_facts = confirmed_list
    doc.explanation_text = None
    doc.independent_facts = []
    doc.verification_result = None
    db.commit()
    db.refresh(doc)

    record_audit_event(db, "FIELDS_CONFIRMED", id, {
        "confirmed_fields_count": len(confirmed_list)
    })
    return doc
