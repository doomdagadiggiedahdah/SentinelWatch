from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization, Incident, Campaign
from backend.auth import get_current_org
from backend.services.query_budget import check_and_decrement_budget
from backend.services.audit import log_action
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["analytics"])


class TrendDataPoint(BaseModel):
    time: str  # ISO date
    llm_content: int = 0
    deepfake_audio: int = 0
    deepfake_video: int = 0
    ai_code_assistant: int = 0
    llm_inference: int = 0
    other: int = 0


class DistributionItem(BaseModel):
    attack_vector: str
    count: int
    avg_impact: str


class HeatmapCell(BaseModel):
    sector: str
    attack_vector: str
    count: int


class CoordinationOpportunity(BaseModel):
    campaign_id: int
    campaign_name: str
    priority: str
    num_orgs: int
    num_incidents: int
    last_seen: str
    attack_vector: str


@router.get("/trends", response_model=List[TrendDataPoint])
async def get_trends(
    time_window: str = Query("90d"),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get AI component usage trends over time.
    Returns time series data grouped by AI component type.
    """
    check_and_decrement_budget(db, org)

    # Parse time window
    if time_window == "90d":
        start_date = datetime.utcnow() - timedelta(days=90)
    elif time_window == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    elif time_window == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
    else:
        start_date = datetime.utcnow() - timedelta(days=90)

    # Get incidents in time range
    incidents = db.query(Incident).filter(
        Incident.time_start >= start_date,
        Incident.time_start <= datetime.utcnow()
    ).all()

    # Aggregate by date and AI component
    trend_dict: Dict[str, Dict[str, int]] = {}

    for incident in incidents:
        # Round to day
        date_key = incident.time_start.date().isoformat()
        if date_key not in trend_dict:
            trend_dict[date_key] = {
                "llm_content": 0,
                "deepfake_audio": 0,
                "deepfake_video": 0,
                "ai_code_assistant": 0,
                "llm_inference": 0,
                "other": 0,
            }

        # Count components
        for comp in incident.ai_components or []:
            if comp in trend_dict[date_key]:
                trend_dict[date_key][comp] += 1
            else:
                trend_dict[date_key]["other"] += 1

    # Convert to list of TrendDataPoint, sorted by date
    result = []
    for date_str in sorted(trend_dict.keys()):
        data = trend_dict[date_str]
        result.append(
            TrendDataPoint(
                time=date_str,
                **data
            )
        )

    log_action(db, org.id, "view_trends", {"time_window": time_window}, len(result))
    return result


@router.get("/distribution", response_model=List[DistributionItem])
async def get_distribution(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get distribution of incidents by attack vector and impact level.
    """
    check_and_decrement_budget(db, org)

    # Get all campaigns with their incident counts and average impact
    campaigns = db.query(Campaign).all()

    result = []
    for campaign in campaigns:
        incidents = db.query(Incident).filter(
            Incident.campaign_id == campaign.id
        ).all()

        if not incidents:
            continue

        # Calculate average impact (converted to numeric)
        impact_scores = []
        for inc in incidents:
            if inc.impact_level.value == "high":
                impact_scores.append(3)
            elif inc.impact_level.value == "medium":
                impact_scores.append(2)
            else:
                impact_scores.append(1)

        avg_score = sum(impact_scores) / len(impact_scores) if impact_scores else 1
        if avg_score >= 2.5:
            avg_impact = "high"
        elif avg_score >= 1.5:
            avg_impact = "medium"
        else:
            avg_impact = "low"

        result.append(
            DistributionItem(
                attack_vector=campaign.primary_attack_vector.value,
                count=len(incidents),
                avg_impact=avg_impact
            )
        )

    log_action(db, org.id, "view_distribution", {}, len(result))
    return result


@router.get("/sector-heatmap", response_model=List[HeatmapCell])
async def get_sector_heatmap(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get cross-sector attack vector heatmap.
    Shows which sectors are targeted by which attack vectors.
    """
    check_and_decrement_budget(db, org)

    result = []

    # Get all campaigns
    campaigns = db.query(Campaign).all()

    for campaign in campaigns:
        # Get incidents and their org sectors
        incidents = db.query(Incident).filter(
            Incident.campaign_id == campaign.id
        ).all()

        # Group by sector
        sector_counts: Dict[str, int] = {}
        for incident in incidents:
            org_record = db.query(Organization).filter(
                Organization.id == incident.org_id
            ).first()
            if org_record:
                sector = org_record.sector.value
                sector_counts[sector] = sector_counts.get(sector, 0) + 1

        # Create heatmap cells
        for sector, count in sector_counts.items():
            result.append(
                HeatmapCell(
                    sector=sector,
                    attack_vector=campaign.primary_attack_vector.value,
                    count=count
                )
            )

    log_action(db, org.id, "view_heatmap", {}, len(result))
    return result


@router.get("/opportunities", response_model=List[CoordinationOpportunity])
async def get_coordination_opportunities(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get campaigns needing coordination (high priority).
    Prioritizes by recency, org count, and impact.
    """
    check_and_decrement_budget(db, org)

    opportunities = []

    # Get all campaigns, sorted by last_seen descending
    campaigns = db.query(Campaign).order_by(Campaign.last_seen.desc()).all()

    for campaign in campaigns:
        # Calculate priority
        days_old = (datetime.utcnow() - campaign.last_seen).days

        if campaign.num_orgs >= 5 and days_old <= 7:
            priority = "critical"
        elif campaign.num_orgs >= 3 and days_old <= 14:
            priority = "high"
        elif campaign.num_orgs >= 2 and days_old <= 30:
            priority = "medium"
        else:
            priority = "low"

        if priority in ["critical", "high", "medium"]:
            opportunities.append(
                CoordinationOpportunity(
                    campaign_id=campaign.id,
                    campaign_name=campaign.primary_attack_vector.value,
                    priority=priority,
                    num_orgs=campaign.num_orgs,
                    num_incidents=campaign.num_incidents,
                    last_seen=campaign.last_seen.isoformat(),
                    attack_vector=campaign.primary_attack_vector.value
                )
            )

    log_action(db, org.id, "view_opportunities", {}, len(opportunities))
    return opportunities
