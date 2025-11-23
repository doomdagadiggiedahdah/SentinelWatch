from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization
from backend.auth import get_current_org, get_current_org_id
from backend.schemas import IncidentCreate, IncidentCreateResponse, IncidentResponse
from backend.services.incidents import create_or_update_incident, get_incident
from backend.services.audit import log_action
from backend.services.llm_analysis import analyze_incident
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentCreateResponse)
async def create_incident(
    incident_data: IncidentCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Create or update an incident for the authenticated organization.
    Automatically assigns the incident to a campaign via clustering.
    """
    # Create or update incident
    incident = create_or_update_incident(db, incident_data, org)
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="submit_incident",
        details={"incident_id": incident.id, "local_ref": incident.local_ref}
    )
    
    return IncidentCreateResponse(
        incident_id=incident.id,
        campaign_id=incident.campaign_id
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident_by_id(
    incident_id: int,
    org_id: str = Depends(get_current_org_id),
    db: Session = Depends(get_db)
):
    """
    Get an incident by ID.
    Only returns incidents belonging to the authenticated organization.
    """
    incident = get_incident(db, incident_id, org_id)
    return incident


# Request/Response schemas for analyze endpoint
class AnalyzeIncidentRequest(BaseModel):
    summary: str
    sector: Optional[str] = None
    region: Optional[str] = None


class AnalyzeIncidentResponse(BaseModel):
    success: bool
    attack_vector: Optional[str] = None
    ai_components: Optional[List[str]] = None
    techniques: Optional[List[str]] = None
    suggested_iocs: Optional[List[Dict[str, str]]] = None
    confidence: Optional[str] = None
    reasoning: Optional[str] = None
    error: Optional[str] = None


@router.post("/analyze", response_model=AnalyzeIncidentResponse)
async def analyze_incident_summary(
    request: AnalyzeIncidentRequest,
    org: Organization = Depends(get_current_org),
):
    """
    Analyze an incident summary using AI to suggest classification.
    Returns suggested attack vector, AI components, techniques, and IoCs.
    Does not require database access.
    """
    result = analyze_incident(
        summary=request.summary,
        sector=request.sector or "",
        region=request.region or ""
    )

    if result.success:
        return AnalyzeIncidentResponse(
            success=True,
            attack_vector=result.data.get("attack_vector"),
            ai_components=result.data.get("ai_components"),
            techniques=result.data.get("techniques"),
            suggested_iocs=result.data.get("suggested_iocs"),
            confidence=result.data.get("confidence"),
            reasoning=result.data.get("reasoning"),
        )
    else:
        return AnalyzeIncidentResponse(
            success=False,
            error=result.error,
        )
