import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import DocumentModel
from app.schemas.document import DocumentBase, DocumentDetail, DocumentComparisonResult, ConflictItem
from app.schemas.facts import MedicalFact, FactCategory
from app.schemas.fidelity import FidelitySimulationRequest, FidelitySimulationResponse
from app.schemas.verification import VerificationStatus
from app.services.ocr.ocr_service import OCRUnavailableError, extract_document_text
from app.services.fidelity_lab import FidelitySimulationError, simulate_ai_error
from app.services.safety.guardrails import SafetyGuardrails
from app.services.extraction.parser import DocumentFactParser
from app.services.navigation.care_navigator import CareNavigator
from app.utils.audit import record_audit_event
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])

DEMO_DOCUMENTS = {
    "lab_report": {
        "filename": "DEMO_CBC_Blood_Report.txt",
        "doc_type": "lab_report",
        "content": (
            "METROPOLITAN DIAGNOSTIC LABS\n"
            "PATIENT REPORT - COMPLETE BLOOD COUNT (CBC)\n"
            "Date: 12-Oct-2026\n"
            "Specimen: Whole Blood EDTA\n\n"
            "TEST NAME                RESULT    UNIT       REFERENCE RANGE   FLAG\n"
            "--------------------------------------------------------------------\n"
            "Hemoglobin               10.2      g/dL       12.0 - 16.0       LOW\n"
            "WBC Count                7800      cells/µL   4000 - 11000      NORMAL\n"
            "Platelet Count           210000    cells/µL   150000 - 450000   NORMAL\n"
            "RBC Count                4.1       mil/µL     3.8 - 5.2         NORMAL\n\n"
            "INSTRUCTIONS:\n"
            "Do not take on an empty stomach.\n\n"
            "RECOMMENDATIONS / NEXT STEPS:\n"
            "Follow-up consultation after 2 weeks."
        )
    },
    "prescription": {
        "filename": "DEMO_Outpatient_Prescription.txt",
        "doc_type": "prescription",
        "content": (
            "CITY HEALTH CARE CLINIC\n"
            "OUTPATIENT PRESCRIPTION\n"
            "Date: 10-Oct-2026\n\n"
            "MEDICATION ORDERS:\n"
            "1. Tab. Metformin 500 mg - twice daily for 30 days\n"
            "2. Tab. Atorvastatin 20 mg - once daily at bedtime for 30 days\n\n"
            "DIRECTIONS / SPECIAL INSTRUCTIONS:\n"
            "Do NOT take on an empty stomach.\n\n"
            "NEXT VISIT:\n"
            "Review after 1 month with treating physician."
        )
    },
    "corrupted_test": {
        "filename": "DEMO_Edge_Case_Discrepancy.txt",
        "doc_type": "lab_report",
        "content": (
            "METROPOLITAN DIAGNOSTIC LABS\n"
            "PATIENT REPORT - COMPLETE BLOOD COUNT (CBC)\n"
            "Date: 14-Oct-2026\n\n"
            "TEST NAME                RESULT    UNIT       REFERENCE RANGE   FLAG\n"
            "--------------------------------------------------------------------\n"
            "Hemoglobin               10.2      g/dL       12.0 - 16.0       LOW\n"
            "WBC Count                7800      cells/µL   4000 - 11000      NORMAL\n\n"
            "INSTRUCTIONS:\n"
            "Do not take on an empty stomach."
        )
    }
}

FIDELITY_LAB_FIXTURES = {
    "fidelity_lab_cbc": ("synthetic_reports", "SYN_LAB_025.txt"),
    "fidelity_lab_prescription": ("prescriptions", "SYN_RX_001.txt"),
}

@router.get("", response_model=List[DocumentBase])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.desc()).all()
    return docs

@router.post("/upload", response_model=DocumentDetail)
async def upload_document(
    file: Optional[UploadFile] = File(None),
    demo_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    doc_id = str(uuid.uuid4())

    if file:
        demo_type = None
    elif not demo_type:
        raise HTTPException(status_code=422, detail="A document file or explicit demo selection is required.")

    page_count = 1
    if demo_type in FIDELITY_LAB_FIXTURES:
        fixture_directory, fixture_name = FIDELITY_LAB_FIXTURES[demo_type]
        fixture_path = Path(__file__).resolve().parents[2] / "data" / fixture_directory / fixture_name
        if not fixture_path.is_file():
            raise HTTPException(status_code=503, detail="The selected synthetic Fidelity Lab document is unavailable.")
        filename = fixture_path.name
        with fixture_path.open("r", encoding="utf-8") as fixture:
            raw_text = fixture.read()
        file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
        with open(file_path, "w", encoding="utf-8") as uploaded_fixture:
            uploaded_fixture.write(raw_text)
        file_type = "text/plain"
        file_size = len(raw_text)
        doc_type = "lab_report"
        ocr_quality = 0.98
    elif demo_type and demo_type in DEMO_DOCUMENTS:
        demo = DEMO_DOCUMENTS[demo_type]
        filename = demo["filename"]
        raw_text = demo["content"]
        file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        file_type = "text/plain"
        file_size = len(raw_text)
        doc_type = demo["doc_type"]
        ocr_quality = 0.98
    elif file:
        filename = file.filename or "uploaded-document"
        extension = os.path.splitext(filename)[1].lower()
        if extension not in {".pdf", ".png", ".jpg", ".jpeg", ".txt"}:
            raise HTTPException(status_code=415, detail="Supported document formats are PDF, PNG, JPG, JPEG, and TXT.")
        file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(file_path)
        file_type = file.content_type or "application/octet-stream"

        try:
            ocr_res = extract_document_text(file_path, settings.OCR_PROVIDER)
        except OCRUnavailableError as error:
            try:
                os.remove(file_path)
            except OSError:
                pass
            if extension == ".pdf":
                detail = "Text extraction failed because this PDF contains scanned pages and no OCR engine is available."
            else:
                detail = "OCR failed to process this image because no OCR engine is available."
            raise HTTPException(status_code=503, detail=detail) from error
        except Exception as error:
            try:
                os.remove(file_path)
            except OSError:
                pass
            if extension == ".pdf":
                detail = "PDF extraction failed because the file is corrupt or unreadable."
            else:
                detail = "OCR failed to process this image. Check that the file is a valid PNG, JPG, or JPEG image."
            raise HTTPException(status_code=422, detail=detail) from error

        raw_text = ocr_res.raw_text
        ocr_quality = ocr_res.confidence
        page_count = ocr_res.page_count
        if not raw_text.strip():
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise HTTPException(
                status_code=422,
                detail="This document contains no readable text.",
            )
        
        # Guess document type. Lab markers are checked first: lab report PDFs
        # can mention "prescription" in disclaimers, which must not override
        # their actual laboratory content.
        low_t = raw_text.lower()
        lab_markers = ["laboratory report", "complete blood count", "lipid profile", "reference range", "test name"]
        rx_markers = ["prescription", "tab.", "rx"]
        if any(marker in low_t for marker in lab_markers):
            doc_type = "lab_report"
        elif any(marker in low_t for marker in rx_markers):
            doc_type = "prescription"
        else:
            doc_type = "lab_report"
    else:
        raise HTTPException(status_code=422, detail="A valid document file or explicit demo selection is required.")

    # Safety: sanitize prompt injections and redact PII
    sanitized_text = SafetyGuardrails.sanitize_untrusted_text(raw_text)
    sanitized_text = SafetyGuardrails.redact_pii(sanitized_text)

    # Initial structured fact parsing
    extracted_res = DocumentFactParser.parse_document_text(
        sanitized_text,
        document_type=doc_type,
        ocr_boxes=ocr_res.bounding_boxes if file else None,
    )
    fact_dicts = [f.dict() for f in extracted_res.facts]

    # Pre-extract verified next step
    next_step_res = CareNavigator.extract_verified_next_step(sanitized_text, extracted_res.facts)

    # Save document in SQLite
    doc_model = DocumentModel(
        id=doc_id,
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        document_type=doc_type,
        page_count=page_count,
        ocr_quality=ocr_quality,
        raw_text=sanitized_text,
        extracted_facts=fact_dicts,
        confirmed_facts=fact_dicts,  # initially defaults to extracted facts
        next_step=next_step_res.dict()
    )
    db.add(doc_model)
    db.commit()
    db.refresh(doc_model)

    # Audit events
    record_audit_event(db, "DOCUMENT_UPLOADED", doc_id, {"filename": filename, "file_size": file_size})
    record_audit_event(db, "OCR_COMPLETED", doc_id, {"ocr_quality": ocr_quality})
    record_audit_event(db, "EXTRACTION_COMPLETED", doc_id, {"facts_count": len(fact_dicts)})

    return doc_model

@router.get("/{id}", response_model=DocumentDetail)
def get_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document_data = {column.name: getattr(doc, column.name) for column in DocumentModel.__table__.columns}
    verification = doc.verification_result or {}
    safe_to_display = verification.get("explanation_safe_to_display", False)
    document_data["explanation_text"] = doc.explanation_text if safe_to_display else None
    document_data["explanation_pending_verification"] = bool(doc.explanation_text and not verification)
    return document_data


@router.post("/{id}/simulate-ai-error", response_model=FidelitySimulationResponse)
def simulate_document_ai_error(
    id: str,
    payload: FidelitySimulationRequest,
    db: Session = Depends(get_db),
):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not doc.explanation_text or not doc.verification_result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Generate and verify an explanation before running a simulation.")
    if (
        doc.verification_result.get("overall_status") != VerificationStatus.VERIFIED.value
        or not doc.verification_result.get("explanation_safe_to_display")
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Simulation requires a currently VERIFIED explanation.")

    facts_data = doc.confirmed_facts or doc.extracted_facts or []
    if not facts_data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No confirmed facts are available for simulation.")

    facts = [MedicalFact(**fact) for fact in facts_data]
    try:
        return simulate_ai_error(doc.id, doc.explanation_text, facts, payload.failure_type)
    except FidelitySimulationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

@router.delete("/{id}")
def delete_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Privacy delete
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass
    
    db.delete(doc)
    db.commit()
    record_audit_event(db, "DOCUMENT_DELETED", id, {"privacy_mode": True})
    return {"status": "success", "message": "Document and associated health data permanently deleted."}

@router.post("/compare", response_model=DocumentComparisonResult)
def compare_documents(
    doc_ids: List[str],
    db: Session = Depends(get_db)
):
    """
    Multi-document comparison and conflict detection (Section 27).
    Detects dosage or test discrepancies across documents without declaring which is correct.
    """
    if len(doc_ids) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 document IDs to compare.")

    docs = db.query(DocumentModel).filter(DocumentModel.id.in_(doc_ids)).all()
    if len(docs) < 2:
        raise HTTPException(status_code=404, detail="Could not find specified documents to compare.")

    conflicts: List[ConflictItem] = []
    
    # Map facts by name across documents
    fact_map = {}
    for d in docs:
        facts = [MedicalFact(**f) for f in (d.confirmed_facts or d.extracted_facts or [])]
        for f in facts:
            norm_name = f.name.lower().strip()
            if norm_name not in fact_map:
                fact_map[norm_name] = []
            fact_map[norm_name].append({"doc": d, "fact": f})

    for name, occurrences in fact_map.items():
        if len(occurrences) >= 2:
            first = occurrences[0]
            for other in occurrences[1:]:
                # Check for medication dosage conflicts
                if first["fact"].category == FactCategory.MEDICATION and other["fact"].category == FactCategory.MEDICATION:
                    d1 = first["fact"].dosage or first["fact"].strength
                    d2 = other["fact"].dosage or other["fact"].strength
                    if d1 and d2 and d1.lower() != d2.lower():
                        conflicts.append(ConflictItem(
                            field_name=first["fact"].name,
                            category="medication",
                            doc_a_value=d1,
                            doc_b_value=d2,
                            doc_a_name=first["doc"].filename,
                            doc_b_name=other["doc"].filename,
                            conflict_type="DOSAGE_CONFLICT",
                            warning_message=f"Two documents contain different dosage information for {first['fact'].name}: {d1} vs {d2}. ReadBack cannot determine which is correct. Please verify with your healthcare professional."
                        ))

    return DocumentComparisonResult(
        has_conflicts=len(conflicts) > 0,
        conflicts=conflicts,
        summary=f"Compared {len(docs)} documents. Detected {len(conflicts)} potential cross-document discrepancies."
    )

@router.get("/timeline")
def get_timeline(db: Session = Depends(get_db)):
    """
    Extracts laboratory facts across documents over time (Section 28).
    Strictly displays data without interpreting trends.
    """
    docs = db.query(DocumentModel).order_by(DocumentModel.created_at.asc()).all()
    timeline_records = []
    
    for d in docs:
        facts = [MedicalFact(**f) for f in (d.confirmed_facts or d.extracted_facts or [])]
        lab_facts = [f for f in facts if f.category == FactCategory.LABORATORY and f.value is not None]
        if lab_facts:
            timeline_records.append({
                "document_id": d.id,
                "filename": d.filename,
                "date": d.created_at.strftime("%b %d, %Y"),
                "values": {f.name: f.value for f in lab_facts}
            })

    return timeline_records
