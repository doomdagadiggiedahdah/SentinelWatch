from sqlalchemy.orm import Session
from backend.db.models import Incident, Organization
from backend.schemas import IncidentCreate
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from backend.services.clustering import find_or_create_campaign, update_campaign_aggregates


def create_or_update_incident(
    db: Session,
    incident_data: IncidentCreate,
    org: Organization
) -> Incident:
    """
    Create a new incident or update existing one (based on org_id + local_ref).
    Assigns the incident to a campaign via clustering.
    """
    # Check if incident already exists
    existing = db.query(Incident).filter(
        Incident.org_id == org.id,
        Incident.local_ref == incident_data.local_ref
    ).first()
    
    if existing:
        # Update existing incident
        existing.time_start = incident_data.time_start
        existing.time_end = incident_data.time_end
        existing.attack_vector = incident_data.attack_vector
        existing.ai_components = incident_data.ai_components
        existing.techniques = incident_data.techniques
        existing.iocs = [ioc.dict() for ioc in incident_data.iocs]
        existing.impact_level = incident_data.impact_level
        existing.summary = incident_data.summary
        
        incident = existing
    else:
        # Create new incident
        incident = Incident(
            org_id=org.id,
            local_ref=incident_data.local_ref,
            time_start=incident_data.time_start,
            time_end=incident_data.time_end,
            attack_vector=incident_data.attack_vector,
            ai_components=incident_data.ai_components,
            techniques=incident_data.techniques,
            iocs=[ioc.dict() for ioc in incident_data.iocs],
            impact_level=incident_data.impact_level,
            summary=incident_data.summary,
            created_at=datetime.utcnow()
        )
        db.add(incident)
    
    db.flush()  # Ensure incident has an ID
    
    # Assign to campaign
    campaign = find_or_create_campaign(db, incident, org)
    incident.campaign_id = campaign.id
    
    db.commit()
    
    # Update campaign aggregates
    update_campaign_aggregates(db, campaign.id)
    
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: int, org_id: str) -> Incident:
    """
    Get an incident by ID, ensuring it belongs to the requesting org.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    if incident.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident"
        )
    
    return incident
