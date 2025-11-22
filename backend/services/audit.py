from sqlalchemy.orm import Session
from backend.db.models import AuditLog
from datetime import datetime
from typing import Optional, Dict, Any


def log_action(
    db: Session,
    org_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    result_count: Optional[int] = None
):
    """Log an action to the audit log"""
    audit_log = AuditLog(
        org_id=org_id,
        action=action,
        details=details,
        result_count=result_count,
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()
