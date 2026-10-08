from sqlalchemy.orm import Session
from app.models.models import AuditEventModel
from typing import Dict, Any, Optional

def record_audit_event(db: Session, event_type: str, document_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    try:
        event = AuditEventModel(
            document_id=document_id,
            event_type=event_type,
            event_details=details or {}
        )
        db.add(event)
        db.commit()
    except Exception as e:
        print(f"Failed to record audit event {event_type}: {e}")
