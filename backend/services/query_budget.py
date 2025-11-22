from sqlalchemy.orm import Session
from backend.db.models import Organization
from datetime import datetime, timedelta
from fastapi import HTTPException, status

DEFAULT_QUERY_BUDGET = 100


def check_and_decrement_budget(db: Session, org: Organization):
    """
    Check if org has query budget remaining and decrement it.
    Resets budget if reset time has passed.
    Raises HTTPException if budget is exhausted.
    """
    now = datetime.utcnow()
    
    # Check if budget reset time has passed
    if now >= org.budget_reset_at:
        # Reset budget
        org.query_budget = DEFAULT_QUERY_BUDGET
        org.budget_reset_at = now + timedelta(days=1)
        db.commit()
    
    # Check if budget is available
    if org.query_budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Query budget exhausted. Please wait for reset window."
        )
    
    # Decrement budget
    org.query_budget -= 1
    db.commit()
