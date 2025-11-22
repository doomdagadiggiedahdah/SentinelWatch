from sqlalchemy.orm import Session
from backend.db.models import Campaign, Incident, Organization
from datetime import datetime, timedelta
import hashlib
from typing import Optional, List


def compute_fingerprint(
    attack_vector: str,
    region: str,
    time_start: datetime,
    iocs: List[dict]
) -> str:
    """
    Compute a fingerprint for an incident for clustering.
    
    Fingerprint = hash(attack_vector + region + ISO_week + first_2_iocs)
    """
    # Get ISO week (e.g., "2025-W47")
    iso_week = f"{time_start.year}-W{time_start.isocalendar()[1]:02d}"
    
    # Extract first 2 IOC values (lowercased and sorted)
    ioc_values = [ioc.get("value", "").lower() for ioc in iocs[:2]]
    ioc_values.sort()
    iocs_joined = ",".join(ioc_values)
    
    # Create fingerprint string
    fingerprint_str = f"{attack_vector}|{region}|{iso_week}|{iocs_joined}"
    
    # Hash it
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()


def find_or_create_campaign(
    db: Session,
    incident: Incident,
    org: Organization
) -> Campaign:
    """
    Find an existing campaign for the incident or create a new one.
    
    Matching logic:
    - Same attack_vector
    - last_seen within ±7 days of incident.time_start
    - Matching fingerprint
    """
    fingerprint = compute_fingerprint(
        attack_vector=incident.attack_vector.value,
        region=org.region.value,
        time_start=incident.time_start,
        iocs=incident.iocs
    )
    
    # Find candidate campaigns
    time_window_start = incident.time_start - timedelta(days=7)
    time_window_end = incident.time_start + timedelta(days=7)
    
    candidates = db.query(Campaign).filter(
        Campaign.primary_attack_vector == incident.attack_vector,
        Campaign.last_seen >= time_window_start,
        Campaign.last_seen <= time_window_end
    ).all()
    
    # Check fingerprint match (simplified: just check if same attack vector for MVP)
    # In production, we'd store fingerprints or check against all incidents in campaign
    for campaign in candidates:
        # For MVP, we'll match on attack_vector and time window
        # More sophisticated fingerprint matching can be added
        return campaign
    
    # No match found, create new campaign
    campaign = Campaign(
        primary_attack_vector=incident.attack_vector,
        ai_components=incident.ai_components,
        sectors=[org.sector.value],
        regions=[org.region.value],
        first_seen=incident.time_start,
        last_seen=incident.time_start,
        num_orgs=1,
        num_incidents=1,
        canonical_summary=generate_canonical_summary(incident, org)
    )
    db.add(campaign)
    db.flush()  # Get the campaign ID
    
    return campaign


def update_campaign_aggregates(db: Session, campaign_id: int):
    """
    Recalculate campaign aggregates based on all incidents in the campaign.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return
    
    # Get all incidents in this campaign
    incidents = db.query(Incident).filter(Incident.campaign_id == campaign_id).all()
    
    if not incidents:
        return
    
    # Get all unique orgs
    org_ids = set()
    all_ai_components = set()
    all_sectors = set()
    all_regions = set()
    
    for incident in incidents:
        org_ids.add(incident.org_id)
        all_ai_components.update(incident.ai_components)
        
        # Get org's sector and region
        org = db.query(Organization).filter(Organization.id == incident.org_id).first()
        if org:
            all_sectors.add(org.sector.value)
            all_regions.add(org.region.value)
    
    # Update campaign
    campaign.num_orgs = len(org_ids)
    campaign.num_incidents = len(incidents)
    campaign.ai_components = list(all_ai_components)
    campaign.sectors = list(all_sectors)
    campaign.regions = list(all_regions)
    campaign.first_seen = min(inc.time_start for inc in incidents)
    campaign.last_seen = max(inc.time_start for inc in incidents)
    
    db.commit()


def generate_canonical_summary(incident: Incident, org: Organization) -> str:
    """
    Generate a canonical summary for a campaign.
    For MVP, use a simple template.
    """
    ai_comps = ", ".join(incident.ai_components) if incident.ai_components else "AI components"
    return (
        f"AI-{incident.attack_vector.value} campaign using {ai_comps} "
        f"observed in {org.sector.value} sector, {org.region.value} region."
    )
