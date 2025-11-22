from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization
from backend.auth import get_current_org, get_current_org_id
from backend.schemas import (
    CampaignSummary, CampaignDetail, AmIAloneResponse, 
    CampaignFilters, AttackVectorEnum, SectorEnum, RegionEnum
)
from backend.services.campaigns import list_campaigns, get_campaign_detail, get_am_i_alone
from backend.services.query_budget import check_and_decrement_budget
from backend.services.audit import log_action
from typing import List, Optional
from datetime import datetime

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
