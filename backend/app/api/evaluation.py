from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.models.database import get_db
from app.models.models import EvaluationResultModel, DocumentModel, AuditEventModel
from app.schemas.evaluation import EvaluationRunResponse
from app.services.evaluation.evaluator import EvaluationService

router = APIRouter(tags=["Evaluation"])

@router.post("/evaluation/run", response_model=EvaluationRunResponse)
def run_evaluation(db: Session = Depends(get_db)):
    result = EvaluationService.run_evaluation(db=db)
    return result

@router.get("/evaluation/results", response_model=EvaluationRunResponse)
def get_evaluation_results(db: Session = Depends(get_db)):
    # Check if a recent run exists in DB
    record = db.query(EvaluationResultModel).order_by(EvaluationResultModel.timestamp.desc()).first()
    if not record:
        # Run live evaluation on synthetic dataset
        return EvaluationService.run_evaluation(db=db)
    
    return EvaluationRunResponse(
        run_id=record.id,
        timestamp=record.timestamp,
        dataset_size=record.dataset_size,
        comparison=record.baseline_metrics and {
            "baseline_metrics": record.baseline_metrics,
            "readback_metrics": record.readback_metrics
        },
        language_breakdown=record.language_breakdown or [],
        category_breakdown=record.category_breakdown or {},
        recent_failures=record.recent_failures or []
    )

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    docs = db.query(DocumentModel).all()
    total_docs = len(docs)
    
    verified_count = 0
    blocked_count = 0
    review_count = 0
    fidelity_scores = []

    for d in docs:
        vr = d.verification_result
        if vr:
            status_val = vr.get("overall_status")
            if status_val == "VERIFIED":
                verified_count += 1
            elif status_val == "BLOCKED":
                blocked_count += 1
            else:
                review_count += 1
            
            score = vr.get("fidelity_score")
            if score is not None:
                fidelity_scores.append(score)

    avg_fidelity = round(sum(fidelity_scores) / len(fidelity_scores), 1) if fidelity_scores else 0.0

    recent_audit = db.query(AuditEventModel).order_by(AuditEventModel.created_at.desc()).limit(10).all()

    return {
        "documents_analyzed": total_docs,
        "verified_explanations": verified_count,
        "blocked_explanations": blocked_count,
        "needs_review": review_count,
        "average_document_fidelity": avg_fidelity,
        "recent_audit_events": [
            {
                "id": a.id,
                "document_id": a.document_id,
                "event_type": a.event_type,
                "timestamp": a.created_at.strftime("%H:%M:%S - %d %b"),
                "details": a.event_details
            }
            for a in recent_audit
        ]
    }
