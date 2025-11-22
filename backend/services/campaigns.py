from sqlalchemy.orm import Session
from backend.db.models import Campaign, Incident
from backend.schemas import CampaignSummary, CampaignDetail, CampaignFilters, IOC
from typing import List, Optional
from fastapi import HTTPException, status


def apply_privacy_rules(campaign: Campaign) -> dict:
    """
    Apply k-anonymity privacy rules to a campaign.
    If num_orgs < 2, suppress sectors and regions.
    """
    campaign_dict = {
        "id": campaign.id,
        "primary_attack_vector": campaign.primary_attack_vector,
        "ai_components": campaign.ai_components,
        "num_orgs": campaign.num_orgs,
        "num_incidents": campaign.num_incidents,
        "first_seen": campaign.first_seen,
        "last_seen": campaign.last_seen,
        "canonical_summary": campaign.canonical_summary,
    }
    
    # Apply k-anonymity: suppress sectors/regions if num_orgs < 2
    if campaign.num_orgs < 2:
        campaign_dict["sectors"] = []
        campaign_dict["regions"] = []
    else:
        campaign_dict["sectors"] = campaign.sectors
        campaign_dict["regions"] = campaign.regions
    
    return campaign_dict


def list_campaigns(
    db: Session,
    filters: Optional[CampaignFilters] = None
) -> List[CampaignSummary]:
    """
    List campaigns with optional filters.
    Applies privacy rules before returning.
    """
    query = db.query(Campaign)
    
    if filters:
        if filters.attack_vector:
            query = query.filter(Campaign.primary_attack_vector == filters.attack_vector)
        
        if filters.since:
            query = query.filter(Campaign.last_seen >= filters.since)
        
        if filters.until:
            query = query.filter(Campaign.first_seen <= filters.until)
        
        # Sector and region filters need special handling due to JSON arrays
        # For MVP, we'll skip these or do simple contains checks
        # In production, use proper JSON querying
    
    campaigns = query.all()
    
    # Apply privacy rules
    result = []
    for campaign in campaigns:
        campaign_dict = apply_privacy_rules(campaign)
        result.append(CampaignSummary(**campaign_dict))
    
    return result


def get_campaign_detail(db: Session, campaign_id: int) -> CampaignDetail:
    """
    Get detailed information about a campaign.
    Applies privacy rules before returning.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Apply privacy rules
    campaign_dict = apply_privacy_rules(campaign)
    
    # Get sample IOCs (first 3 from any incident in the campaign)
    incidents = db.query(Incident).filter(Incident.campaign_id == campaign_id).limit(3).all()
    sample_iocs = []
    for incident in incidents:
        for ioc in incident.iocs[:1]:  # 1 per incident
            if ioc not in sample_iocs:
                sample_iocs.append(IOC(**ioc))
            if len(sample_iocs) >= 3:
                break
        if len(sample_iocs) >= 3:
            break
    
    campaign_dict["sample_iocs"] = sample_iocs
    
    return CampaignDetail(**campaign_dict)


def get_am_i_alone(db: Session, incident_id: int, org_id: str) -> dict:
    """
    Check if an incident is part of a campaign (i.e., "Am I alone?").
    Returns campaign info if part of a campaign, otherwise returns not alone.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found"
        )
    
    # Verify incident belongs to requesting org
    if incident.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this incident"
        )
    
    # Check if incident has a campaign
    if not incident.campaign_id:
        return {"in_campaign": False, "campaign": None}
    
    # Get campaign and apply privacy rules
    campaign = db.query(Campaign).filter(Campaign.id == incident.campaign_id).first()
    if not campaign:
        return {"in_campaign": False, "campaign": None}
    
    campaign_dict = apply_privacy_rules(campaign)
    
    return {
        "in_campaign": True,
        "campaign": CampaignSummary(**campaign_dict)
    }
