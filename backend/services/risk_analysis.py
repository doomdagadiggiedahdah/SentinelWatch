import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.db.models import Organization, Incident, Campaign, RiskAssessment
from backend.services.llm_analysis import get_claude_client

logger = logging.getLogger(__name__)

# Risk scoring weights
THREAT_SCORING_WEIGHTS = {
    "incident_frequency": 0.3,
    "likelihood_percentage": 0.4,
    "estimated_impact": 0.3,
}

# Risk classification thresholds
HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40


def calculate_similarity_score(
    org_sector: str,
    org_region: str,
    org_size: Optional[str],
    org_systems: List[str],
    incident: Incident,
    incident_org_sector: Optional[str],
    incident_org_region: Optional[str],
) -> int:
    """
    Calculate similarity score between org profile and incident.
    Returns score 0-100.
    """
    score = 0

    # Sector match: +40 points
    if org_sector and incident_org_sector and org_sector.lower() == incident_org_sector.lower():
        score += 40
    elif org_sector and incident_org_sector:
        # Adjacent sectors (health/pharma, etc.) get partial credit
        adjacent_pairs = [("health", "pharma"), ("energy", "utilities")]
        if any(
            (org_sector.lower() in pair and incident_org_sector.lower() in pair)
            for pair in adjacent_pairs
        ):
            score += 20

    # Region match: +20 points
    if org_region and incident_org_region and org_region.lower() == incident_org_region.lower():
        score += 20

    # System match: +30 points (check if incident targeted systems in org's stack)
    if org_systems and incident.ai_components:
        org_systems_lower = [s.lower() for s in org_systems]
        incident_components_lower = [c.lower() for c in incident.ai_components]
        if any(sys in str(incident_components_lower) for sys in org_systems_lower):
            score += 30

    return min(score, 100)


def get_relevant_incidents(
    db: Session,
    org: Organization,
    days_back: int = 90,
    min_similarity: int = 50,
) -> List[Incident]:
    """
    Get incidents relevant to org based on similarity scoring.
    Returns incidents with score >= min_similarity from last N days.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

    # Query incidents from last N days
    incidents = (
        db.query(Incident)
        .filter(Incident.created_at >= cutoff_date)
        .all()
    )

    # Score and filter incidents
    scored_incidents = []
    for incident in incidents:
        # Skip incidents from same org
        if incident.org_id == org.id:
            continue

        # Get incident org info
        incident_org = db.query(Organization).filter(
            Organization.id == incident.org_id
        ).first()
        if not incident_org:
            continue

        # Calculate similarity
        score = calculate_similarity_score(
            org_sector=org.sector.value if org.sector else "",
            org_region=org.region.value if org.region else "",
            org_size=org.org_size,
            org_systems=org.primary_systems or [],
            incident=incident,
            incident_org_sector=incident_org.sector.value if incident_org.sector else "",
            incident_org_region=incident_org.region.value if incident_org.region else "",
        )

        if score >= min_similarity:
            scored_incidents.append((incident, score))

    # Sort by score descending
    scored_incidents.sort(key=lambda x: x[1], reverse=True)

    # Return incidents (drop score tuple)
    return [inc for inc, _ in scored_incidents]


def cluster_by_attack_vector(incidents: List[Incident]) -> Dict[str, List[Incident]]:
    """Group incidents by attack_vector."""
    clusters = {}
    for incident in incidents:
        vector = incident.attack_vector.value
        if vector not in clusters:
            clusters[vector] = []
        clusters[vector].append(incident)
    return clusters


def assess_org_exposure(
    db: Session,
    org: Organization,
    attack_vector: str,
    incident_cluster: List[Incident],
) -> Dict[str, Any]:
    """
    Use Claude to assess org's specific exposure to a threat cluster.
    Returns exposure assessment with likelihood and impact estimates.
    """
    client = get_claude_client()
    if not client:
        logger.warning("Claude not available for exposure assessment")
        return {
            "likelihood_percentage": 50,
            "exposure_level": "MEDIUM",
            "factors": ["Unable to compute detailed exposure (Claude API unavailable)"],
            "estimated_impact_min": 20000,
            "estimated_impact_max": 50000,
            "reasoning": "Baseline assessment due to API unavailability",
        }

    # Build cluster summary
    num_incidents = len(incident_cluster)
    affected_orgs = len(set(inc.org_id for inc in incident_cluster))
    avg_impact = 45000  # Default estimate

    # Collect patterns
    ai_components_set = set()
    sectors_set = set()
    regions_set = set()
    for incident in incident_cluster[:5]:  # Sample first 5
        ai_components_set.update(incident.ai_components)
        org = db.query(Organization).filter(Organization.id == incident.org_id).first()
        if org:
            sectors_set.add(org.sector.value if org.sector else "")
            regions_set.add(org.region.value if org.region else "")

    # Build org profile summary (no org identity)
    org_profile_summary = f"""
- Sector: {org.sector.value if org.sector else "Unknown"}
- Region: {org.region.value if org.region else "Unknown"}
- Organization Size: {org.org_size or "Unknown"}
- Primary Systems: {', '.join(org.primary_systems or []) or "Not specified"}
- AI Systems in Use: {', '.join(org.ai_systems_in_use or []) or "None"}
- MFA Enabled: {org.mfa_enabled or "Not specified"}
- SIEM Platform: {org.siem_platform or "None"}
- Security Training: {org.security_training_frequency or "None"}
- Phishing Simulations: {org.phishing_simulations or "Never"}
- Incident Response Plan: {org.incident_response_plan or "None"}
"""

    prompt = f"""You are a cybersecurity risk analyst.

THREAT CLUSTER:
- Attack Vector: {attack_vector}
- Incidents in cluster: {num_incidents}
- Affected organizations: {affected_orgs}
- Affected sectors: {', '.join(sectors_set) or "multiple"}
- Affected regions: {', '.join(regions_set) or "multiple"}
- Common AI components: {', '.join(ai_components_set) or "various"}

ORGANIZATION PROFILE (no identifying information):
{org_profile_summary}

TASK:
Assess this organization's exposure to the threat cluster.

Return JSON object:
{{
  "likelihood_percentage": <0-100>,
  "exposure_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "factors": [
    "specific factor 1",
    "specific factor 2",
    "specific factor 3"
  ],
  "estimated_impact_min": <dollars>,
  "estimated_impact_max": <dollars>,
  "reasoning": "2-3 sentence explanation"
}}

Be specific: reference the org's actual systems and gaps from the profile, not generic statements.
Consider sector-specific risks and threat patterns."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""

        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)
        return result
    except Exception as e:
        logger.error(f"Claude exposure assessment failed: {e}")
        return {
            "likelihood_percentage": 50,
            "exposure_level": "MEDIUM",
            "factors": ["Unable to compute detailed exposure"],
            "estimated_impact_min": 20000,
            "estimated_impact_max": 50000,
            "reasoning": "Fallback assessment due to API error",
        }


def calculate_risk_score(
    incident_count: int,
    likelihood_percentage: float,
    estimated_impact_min: float,
    estimated_impact_max: float,
) -> float:
    """
    Calculate overall risk score (0-100).
    Uses weighted formula: incident_frequency * 0.3 + likelihood * 0.4 + impact * 0.3
    """
    # Normalize incident count to 0-100
    incident_score = min(incident_count * 10, 100)

    # Average estimated impact
    avg_impact = (estimated_impact_min + estimated_impact_max) / 2
    impact_score = min(avg_impact / 500, 100)  # Normalize: 50K = 100

    risk_score = (
        incident_score * THREAT_SCORING_WEIGHTS["incident_frequency"]
        + likelihood_percentage * THREAT_SCORING_WEIGHTS["likelihood_percentage"]
        + impact_score * THREAT_SCORING_WEIGHTS["estimated_impact"]
    )

    return risk_score


def classify_risk_level(risk_score: float) -> str:
    """Classify risk score into HIGH/MEDIUM/LOW."""
    if risk_score >= HIGH_RISK_THRESHOLD:
        return "HIGH"
    elif risk_score >= MEDIUM_RISK_THRESHOLD:
        return "MEDIUM"
    else:
        return "LOW"


def generate_risk_assessment(
    db: Session,
    org: Organization,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Generate or retrieve risk assessment for organization.
    Returns cached assessment if valid and not force_refresh.
    """
    # Check for cached valid assessment
    if not force_refresh:
        existing = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.org_id == org.id)
            .first()
        )
        if existing and existing.valid_until and existing.valid_until > datetime.utcnow():
            return json.loads(existing.high_risk_threats + existing.medium_risk_threats + existing.low_risk_threats)

    # Get relevant incidents
    relevant_incidents = get_relevant_incidents(db, org)
    relevant_count = len(relevant_incidents)

    if relevant_count == 0:
        # No relevant threats found
        assessment = {
            "assessed_at": datetime.utcnow().isoformat(),
            "org_id": org.id,
            "relevant_incidents_count": 0,
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
        }
    else:
        # Cluster by attack vector
        clusters = cluster_by_attack_vector(relevant_incidents)

        high_risk = []
        medium_risk = []
        low_risk = []

        # Assess each threat cluster
        for attack_vector, incident_cluster in clusters.items():
            # Get exposure assessment from Claude
            exposure = assess_org_exposure(
                db, org, attack_vector, incident_cluster
            )

            # Calculate risk score
            risk_score = calculate_risk_score(
                incident_count=len(incident_cluster),
                likelihood_percentage=exposure["likelihood_percentage"],
                estimated_impact_min=exposure["estimated_impact_min"],
                estimated_impact_max=exposure["estimated_impact_max"],
            )

            # Build threat card
            threat_card = {
                "threat_id": f"threat_{uuid.uuid4().hex[:8]}",
                "threat_name": f"{attack_vector.replace('_', ' ').title()} Threat",
                "attack_vector": attack_vector,
                "evidence": {
                    "incident_count": len(incident_cluster),
                    "timeframe_days": 90,
                    "affected_orgs_count": len(set(inc.org_id for inc in incident_cluster)),
                    "avg_loss": 45000,
                },
                "exposure": {
                    "level": exposure["exposure_level"],
                    "factors": exposure["factors"],
                },
                "likelihood": "HIGH" if exposure["likelihood_percentage"] > 70 else "MEDIUM" if exposure["likelihood_percentage"] > 40 else "LOW",
                "likelihood_percentage": exposure["likelihood_percentage"],
                "estimated_impact": {
                    "min": exposure["estimated_impact_min"],
                    "max": exposure["estimated_impact_max"],
                },
                "reasoning": exposure["reasoning"],
                "risk_score": risk_score,
            }

            # Classify by risk level
            risk_level = classify_risk_level(risk_score)
            if risk_level == "HIGH":
                high_risk.append(threat_card)
            elif risk_level == "MEDIUM":
                medium_risk.append(threat_card)
            else:
                low_risk.append(threat_card)

        # Sort by risk score descending
        for lst in [high_risk, medium_risk, low_risk]:
            lst.sort(key=lambda x: x["risk_score"], reverse=True)

        assessment = {
            "assessed_at": datetime.utcnow().isoformat(),
            "org_id": org.id,
            "relevant_incidents_count": relevant_count,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
        }

    # Cache assessment
    valid_until = datetime.utcnow() + timedelta(days=7)
    risk_assessment = RiskAssessment(
        id=f"risk_{org.id}_{datetime.utcnow().timestamp()}",
        org_id=org.id,
        assessed_at=datetime.utcnow(),
        relevant_incidents_count=relevant_count,
        high_risk_threats=json.dumps(assessment["high_risk"]),
        medium_risk_threats=json.dumps(assessment["medium_risk"]),
        low_risk_threats=json.dumps(assessment["low_risk"]),
        valid_until=valid_until,
    )
    db.add(risk_assessment)
    db.commit()

    return assessment


def generate_preventive_playbook(
    db: Session,
    org: Organization,
    threat_card: Dict[str, Any],
) -> str:
    """
    Generate preventive defense playbook for a specific threat.
    """
    client = get_claude_client()
    if not client:
        return "Error: Claude API not available for playbook generation"

    threat_name = threat_card.get("threat_name", "Unknown Threat")
    attack_vector = threat_card.get("attack_vector", "")
    exposure_factors = threat_card.get("exposure", {}).get("factors", [])
    likelihood = threat_card.get("likelihood_percentage", 50)
    impact_min = threat_card.get("estimated_impact", {}).get("min", 30000)
    impact_max = threat_card.get("estimated_impact", {}).get("max", 60000)

    # Build org profile summary (no org identity)
    org_profile = f"""
- Sector: {org.sector.value if org.sector else "Unknown"}
- Organization Size: {org.org_size or "Unknown"}
- Primary Systems: {', '.join(org.primary_systems or []) or "Not specified"}
- AI Systems: {', '.join(org.ai_systems_in_use or []) or "None"}
- MFA: {org.mfa_enabled or "Not specified"}
- SIEM: {org.siem_platform or "None"}
- Security Training: {org.security_training_frequency or "None"}
"""

    prompt = f"""You are a cybersecurity consultant creating a PREVENTIVE defense plan.

IMPORTANT: This organization has NOT been attacked yet. Your job is to help them PREVENT the attack from succeeding.

THREAT: {threat_name}
- Attack Vector: {attack_vector}
- Likelihood of Attack: {likelihood}%
- Estimated Impact if Breached: ${impact_min:,} - ${impact_max:,}

ORG'S VULNERABILITY FACTORS:
{chr(10).join(f"• {f}" for f in exposure_factors)}

ORGANIZATION PROFILE:
{org_profile}

Generate a prioritized preventive defense plan with these sections:

## IMMEDIATE ACTIONS (This Week)
3-5 specific, quick actions to reduce risk immediately.
- Include exact settings, configurations, or commands where possible
- Prioritize by impact/effort ratio
- Estimate time/cost for each

## 30-DAY HARDENING PLAN
5-7 actions to strengthen defenses over the next month.
- Focus on sustainable improvements: training, process changes, tool deployment
- Include resource requirements (time, budget, personnel)
- Provide implementation guidance

## DETECTION RULES
3-5 specific SIEM/EDR rules or queries to detect this attack pattern.
- Format for {org.siem_platform or 'Splunk'} SPL if possible
- Include explanatory comments
- Provide test/validation guidance

## KEY INDICATORS TO MONITOR
5-7 warning signs that attack is incoming or in progress.
- Behavioral indicators, not just technical IoCs
- Actionable: "If you see X, do Y immediately"

## COST-BENEFIT ANALYSIS
- Estimated implementation cost (itemized)
- Estimated breach cost ({impact_min:,} - {impact_max:,})
- ROI calculation
- Payback period

## AI-SPECIFIC DEFENSES
How to detect and prevent the AI-enabled aspects of this threat.
- Content filtering for LLM-generated text
- User education on AI-enhanced social engineering
- Technical controls specific to AI tools

Requirements:
- All recommendations PREVENTIVE (before attack), not reactive
- Tailor to {org.sector.value or 'their'} sector
- Assume realistic budget constraints (~$15K available)
- Be specific and actionable, not generic advice
- Reference the org's specific vulnerabilities listed above"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""
        return response_text.strip() if response_text else "Failed to generate playbook"
    except Exception as e:
        logger.error(f"Failed to generate preventive playbook: {e}")
        return f"Error generating playbook: {str(e)}"
