from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization
from backend.auth import get_current_org, get_current_org_id
from backend.schemas import IncidentCreate, IncidentCreateResponse, IncidentResponse
from backend.services.incidents import create_or_update_incident, get_incident
from backend.services.audit import log_action

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
