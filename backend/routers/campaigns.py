from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization, Campaign, Incident
from backend.auth import get_current_org, get_current_org_id
from backend.schemas import (
    CampaignSummary, CampaignDetail, AmIAloneResponse, 
    CampaignFilters, AttackVectorEnum, SectorEnum, RegionEnum
)
from backend.services.campaigns import list_campaigns, get_campaign_detail, get_am_i_alone
from backend.services.query_budget import check_and_decrement_budget
from backend.services.audit import log_action
from backend.services.llm_analysis import generate_playbook
from backend.services.stix_export import export_campaign_as_stix
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=List[CampaignSummary])
async def list_all_campaigns(
    sector: Optional[SectorEnum] = Query(None),
    region: Optional[RegionEnum] = Query(None),
    attack_vector: Optional[AttackVectorEnum] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    List all campaigns with optional filters.
    Applies k-anonymity privacy rules.
    Consumes query budget.
    """
    # Check and decrement query budget
    check_and_decrement_budget(db, org)
    
    # Build filters
    filters = CampaignFilters(
        sector=sector,
        region=region,
        attack_vector=attack_vector,
        since=since,
        until=until
    )
    
    # Get campaigns
    campaigns = list_campaigns(db, filters)
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="list_campaigns",
        details=filters.dict(exclude_none=True),
        result_count=len(campaigns)
    )
    
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific campaign.
    Applies k-anonymity privacy rules.
    Consumes query budget.
    """
    # Check and decrement query budget
    check_and_decrement_budget(db, org)
    
    # Get campaign detail
    campaign = get_campaign_detail(db, campaign_id)
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="get_campaign",
        details={"campaign_id": campaign_id},
        result_count=1
    )
    
    return campaign


@router.get("/am-i-alone/{incident_id}", response_model=AmIAloneResponse)
async def am_i_alone(
    incident_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Check if an incident is part of a wider campaign.
    Returns campaign info if the incident is part of a campaign.
    Consumes query budget.
    """
    # Check and decrement query budget
    check_and_decrement_budget(db, org)
    
    # Get am-i-alone response
    result = get_am_i_alone(db, incident_id, org.id)
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="am_i_alone",
        details={"incident_id": incident_id},
        result_count=1 if result["in_campaign"] else 0
    )
    
    return result


# Response schema for playbook
class PlaybookResponse(BaseModel):
    success: bool
    playbook: Optional[str] = None
    error: Optional[str] = None


@router.post("/{campaign_id}/playbook", response_model=PlaybookResponse)
async def generate_campaign_playbook(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Generate a customized defensive playbook for this campaign.
    Only org that has incidents in this campaign can generate it.
    Consumes query budget.
    """
    # Check and decrement query budget
    check_and_decrement_budget(db, org)
    
    # Fetch campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Check if org has incidents in this campaign
    org_incidents = db.query(Incident).filter(
        Incident.campaign_id == campaign_id,
        Incident.org_id == org.id
    ).all()
    
    if not org_incidents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization has no incidents in this campaign"
        )
    
    # Get all incidents for context
    all_incidents = db.query(Incident).filter(Incident.campaign_id == campaign_id).all()
    
    # Prepare incident summaries for org
    org_incident_summaries = [inc.summary for inc in org_incidents]
    
    # Generate playbook
    playbook = generate_playbook(
        campaign_summary=campaign.canonical_summary or "",
        attack_vector=campaign.primary_attack_vector.value,
        ai_components=campaign.ai_components,
        num_orgs=campaign.num_orgs,
        num_incidents=campaign.num_incidents,
        first_seen=campaign.first_seen,
        last_seen=campaign.last_seen,
        org_sector=org.sector.value,
        org_region=org.region.value,
        org_incidents=org_incident_summaries,
    )
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="generate_playbook",
        details={"campaign_id": campaign_id},
        result_count=1
    )
    
    return PlaybookResponse(success=True, playbook=playbook)


# Response schema for STIX export
class STIXExportResponse(BaseModel):
    success: bool
    bundle: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/{campaign_id}/export-stix", response_model=STIXExportResponse)
async def export_stix(
    campaign_id: int,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Export campaign as STIX 2.1 bundle.
    Consumes query budget.
    """
    # Check and decrement query budget
    check_and_decrement_budget(db, org)
    
    # Fetch campaign
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Export as STIX
    result = export_campaign_as_stix(db, campaign_id)
    
    # Log action
    log_action(
        db=db,
        org_id=org.id,
        action="export_stix",
        details={"campaign_id": campaign_id},
        result_count=1 if result.get("success") else 0
    )
    
    if result.get("success"):
        return STIXExportResponse(success=True, bundle=result.get("bundle"))
    else:
        return STIXExportResponse(success=False, error=result.get("error"))
