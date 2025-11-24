from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization
from backend.schemas import (
    OrgProfileUpdate,
    RiskAssessmentResponse,
    PlaybookGenerateRequest,
    PlaybookResponse,
)
from backend.auth import get_current_org
from backend.services.risk_analysis import (
    generate_risk_assessment,
    generate_preventive_playbook,
)
from backend.services.query_budget import check_and_decrement_budget
from backend.services.audit import log_action
import json

router = APIRouter(prefix="/risk-assessment", tags=["risk-assessment"])


@router.post("/profile", status_code=200)
async def update_org_profile(
    profile: OrgProfileUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """
    Update organization profile for risk assessment.
    """
    if profile.org_size is not None:
        org.org_size = profile.org_size
    if profile.primary_systems is not None:
        org.primary_systems = profile.primary_systems
    if profile.ai_systems_in_use is not None:
        org.ai_systems_in_use = profile.ai_systems_in_use
    if profile.mfa_enabled is not None:
        org.mfa_enabled = profile.mfa_enabled
    if profile.siem_platform is not None:
        org.siem_platform = profile.siem_platform
    if profile.security_training_frequency is not None:
        org.security_training_frequency = profile.security_training_frequency
    if profile.phishing_simulations is not None:
        org.phishing_simulations = profile.phishing_simulations
    if profile.incident_response_plan is not None:
        org.incident_response_plan = profile.incident_response_plan

    from datetime import datetime

    org.profile_completed_at = datetime.utcnow()

    db.commit()

    return {
        "status": "success",
        "message": "Organization profile updated",
        "org_id": org.id,
    }


@router.get("/", response_model=RiskAssessmentResponse)
async def get_risk_assessment(
    force_refresh: bool = False,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """
    Get risk assessment for organization.
    If force_refresh=true, regenerates assessment (costs 1 query).
    """
    # Check profile completion
    if not org.profile_completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization profile must be completed first. Please update your profile.",
        )

    # Check query budget if forcing refresh
    if force_refresh:
        check_and_decrement_budget(db, org)

    # Generate assessment
    assessment = generate_risk_assessment(db, org, force_refresh=force_refresh)

    # Log action
    log_action(
        db,
        org_id=org.id,
        action="get_risk_assessment",
        details={"force_refresh": force_refresh},
        result_count=assessment["relevant_incidents_count"],
    )

    return RiskAssessmentResponse(
        assessed_at=assessment["assessed_at"],
        org_id=assessment["org_id"],
        relevant_incidents_count=assessment["relevant_incidents_count"],
        high_risk=[
            {
                "threat_id": t["threat_id"],
                "threat_name": t["threat_name"],
                "attack_vector": t["attack_vector"],
                "evidence": t["evidence"],
                "exposure": t["exposure"],
                "likelihood": t["likelihood"],
                "likelihood_percentage": t["likelihood_percentage"],
                "estimated_impact": t["estimated_impact"],
                "reasoning": t["reasoning"],
                "risk_score": t["risk_score"],
            }
            for t in assessment.get("high_risk", [])
        ],
        medium_risk=[
            {
                "threat_id": t["threat_id"],
                "threat_name": t["threat_name"],
                "attack_vector": t["attack_vector"],
                "evidence": t["evidence"],
                "exposure": t["exposure"],
                "likelihood": t["likelihood"],
                "likelihood_percentage": t["likelihood_percentage"],
                "estimated_impact": t["estimated_impact"],
                "reasoning": t["reasoning"],
                "risk_score": t["risk_score"],
            }
            for t in assessment.get("medium_risk", [])
        ],
        low_risk=[
            {
                "threat_id": t["threat_id"],
                "threat_name": t["threat_name"],
                "attack_vector": t["attack_vector"],
                "evidence": t["evidence"],
                "exposure": t["exposure"],
                "likelihood": t["likelihood"],
                "likelihood_percentage": t["likelihood_percentage"],
                "estimated_impact": t["estimated_impact"],
                "reasoning": t["reasoning"],
                "risk_score": t["risk_score"],
            }
            for t in assessment.get("low_risk", [])
        ],
    )


@router.post("/playbook", response_model=PlaybookResponse)
async def generate_playbook(
    request: PlaybookGenerateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """
    Generate preventive playbook for a specific threat.
    Playbook viewing is free; regeneration costs 1 query.
    """
    # Check profile completion
    if not org.profile_completed_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization profile must be completed first.",
        )

    # Generate or retrieve assessment
    assessment = generate_risk_assessment(db, org, force_refresh=False)

    # Find the threat card
    threat_card = None
    for section in [assessment.get("high_risk", []), assessment.get("medium_risk", []), assessment.get("low_risk", [])]:
        for threat in section:
            if threat.get("threat_id") == request.threat_id:
                threat_card = threat
                break
        if threat_card:
            break

    if not threat_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found in assessment",
        )

    # Generate playbook
    playbook_text = generate_preventive_playbook(db, org, threat_card)

    # Log action
    log_action(
        db,
        org_id=org.id,
        action="generate_playbook",
        details={"threat_id": request.threat_id, "attack_vector": request.attack_vector},
    )

    return PlaybookResponse(
        playbook_type="preventive",
        threat_name=threat_card.get("threat_name", "Unknown"),
        full_text=playbook_text,
    )
