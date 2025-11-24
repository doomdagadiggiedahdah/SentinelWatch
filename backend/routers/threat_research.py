from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import Organization
from backend.schemas import ThreatResearchRequest, ThreatResearchResponse
from backend.auth import get_current_org
from backend.services.threat_research import generate_threat_research_report
from backend.services.query_budget import check_and_decrement_budget
from backend.services.audit import log_action

router = APIRouter(prefix="/threat-research", tags=["threat-research"])


@router.post("/scan", response_model=ThreatResearchResponse)
async def scan_for_vulnerabilities(
    request: ThreatResearchRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
):
    """
    Scan organization for emerging threat vulnerabilities.
    - Searches recent security research
    - Analyzes vulnerability relevance to org
    - Generates defense recommendations
    - Costs 2 queries
    """
    # Validate request
    if not request.org_description or len(request.org_description) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization description must be at least 50 characters",
        )

    # Check query budget (scanning costs 2 queries)
    check_and_decrement_budget(db, org)
    check_and_decrement_budget(db, org)

    try:
        # Generate threat research report
        report = generate_threat_research_report(db, org, request.org_description)

        # Log action
        log_action(
            db,
            org_id=org.id,
            action="threat_research_scan",
            details={"description_length": len(request.org_description)},
            result_count=report["executive_summary"]["total_vulnerabilities"],
        )

        # Build response
        vulnerabilities = []
        for vuln in report.get("vulnerabilities", []):
            vulnerabilities.append(
                {
                    "name": vuln.get("name", "Unknown"),
                    "risk_level": vuln.get("risk_level", "MEDIUM"),
                    "why_vulnerable": vuln.get("why_vulnerable", []),
                    "likelihood_percentage": vuln.get("likelihood_percentage", 50),
                    "estimated_impact_min": vuln.get("estimated_impact_min", 20000),
                    "estimated_impact_max": vuln.get("estimated_impact_max", 50000),
                    "defense_plan": vuln.get("defense_plan", ""),
                }
            )

        return ThreatResearchResponse(
            report_id=report["report_id"],
            generated_at=report["generated_at"],
            org_description=report["org_description"],
            extracted_profile=report["extracted_profile"],
            vulnerabilities=vulnerabilities,
            executive_summary=report["executive_summary"],
            search_queries=report["search_queries"],
            sources_analyzed=report["sources_analyzed"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate threat research report: {str(e)}",
        )
