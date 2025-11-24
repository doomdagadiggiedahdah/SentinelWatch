import uuid
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.db.models import Organization, ThreatResearchReport
from backend.services.llm_analysis import get_claude_client

logger = logging.getLogger(__name__)


def hash_org_description(description: str) -> str:
    """Generate SHA-256 hash of org description for caching."""
    return hashlib.sha256(description.encode()).hexdigest()


def get_cached_report(
    db: Session,
    org_id: str,
    description_hash: str,
) -> Optional[ThreatResearchReport]:
    """Get cached threat research report if still valid."""
    report = (
        db.query(ThreatResearchReport)
        .filter(
            ThreatResearchReport.org_id == org_id,
            ThreatResearchReport.org_description_hash == description_hash,
        )
        .first()
    )

    if report and report.cached_until and report.cached_until > datetime.utcnow():
        return report

    return None


def search_security_research(search_queries: List[str]) -> List[Dict[str, Any]]:
    """
    Search for recent security research using web search.
    Returns list of search results with title, url, snippet.
    """
    try:
        # Import web_search from tools available in context
        # This is a simplified version - in production, would call external search API
        # For hackathon, we'll return structured placeholder results
        results = []

        # Simulated search results (in production, call actual search API)
        sample_sources = [
            {
                "title": "Universal Adversarial Attacks on Aligned Language Models",
                "url": "https://arxiv.org/abs/2311.18662",
                "snippet": "We present a technique for generating adversarial suffixes that bypass safety guardrails in aligned language models...",
                "source": "arXiv",
            },
            {
                "title": "New Deepfake Audio Detection Evasion Methods Discovered",
                "url": "https://securityblog.example.com/deepfake-detection",
                "snippet": "Researchers found that deepfake audio can evade detection systems by adding subtle background noise patterns...",
                "source": "Security Research Blog",
            },
            {
                "title": "LLM-Powered Phishing Campaigns Target Enterprise Email",
                "url": "https://threatintel.example.com/llm-phishing",
                "snippet": "AI language models are being used to generate highly personalized phishing emails at scale...",
                "source": "Threat Intelligence",
            },
            {
                "title": "Prompt Injection Attacks in Production LLM Systems",
                "url": "https://owasp.org/www-community/attacks/prompt_injection",
                "snippet": "Attackers can manipulate LLM systems to disclose sensitive information or generate malicious content...",
                "source": "OWASP",
            },
            {
                "title": "AI-Assisted Code Generation Security Risks",
                "url": "https://codeql.example.com/ai-risks",
                "snippet": "GitHub Copilot and similar tools can introduce security vulnerabilities if not properly validated...",
                "source": "Code Security",
            },
        ]

        # Return sample results (in real implementation, filter by search_queries)
        return sample_sources[:10]

    except Exception as e:
        logger.error(f"Security research search failed: {e}")
        return []


def extract_profile_and_vulnerabilities(
    org_description: str,
    search_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Use Claude to extract org profile and identify vulnerabilities from search results.
    """
    client = get_claude_client()
    if not client:
        logger.warning("Claude not available for profile extraction")
        return {
            "extracted_profile": {
                "sector": "unknown",
                "size": "unknown",
                "systems": [],
                "security_posture": org_description[:100],
            },
            "vulnerabilities": [],
        }

    # Format search results for prompt
    results_text = "\n".join(
        [
            f"- {r.get('title', '')}: {r.get('snippet', '')[:200]}"
            for r in search_results[:10]
        ]
    )

    prompt = f"""You are a cybersecurity threat analyst.

TASK 1: Extract organization profile from description
TASK 2: Analyze recent research and identify relevant AI-enabled vulnerabilities

ORGANIZATION DESCRIPTION:
\"{org_description}\"

RECENT SECURITY RESEARCH (last 30 days):
{results_text}

FIRST: Extract structured profile:
{{
  "sector": "healthcare|finance|utilities|energy|manufacturing|government|education|other",
  "size": "estimated employee count or range",
  "systems": ["list of technologies mentioned"],
  "ai_systems": ["any AI tools mentioned"],
  "security_measures": ["MFA, training, etc."],
  "security_gaps": ["missing controls mentioned or implied"]
}}

SECOND: From the research, identify 2-4 AI-enabled vulnerabilities relevant to this organization.

For each vulnerability return:
{{
  "name": "concise name",
  "description": "2-3 sentence description",
  "attack_vector": "category from research",
  "prerequisites": ["what's needed to exploit"],
  "potential_impact": ["possible consequences"],
  "source_title": "which research paper/article",
  "source_url": "URL if available"
}}

Return JSON with keys: extracted_profile, vulnerabilities (array)

Only include vulnerabilities the organization is likely vulnerable to based on their profile."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
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
        logger.error(f"Claude profile extraction failed: {e}")
        return {
            "extracted_profile": {
                "sector": "unknown",
                "size": "unknown",
                "systems": [],
                "security_posture": org_description[:100],
            },
            "vulnerabilities": [],
        }


def map_vulnerabilities_to_org(
    org_description: str,
    extracted_profile: Dict[str, Any],
    vulnerabilities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Map vulnerabilities to organization and assess exposure.
    """
    client = get_claude_client()
    if not client:
        return []

    vulns_text = json.dumps(vulnerabilities, indent=2)

    prompt = f"""You are assessing which vulnerabilities are relevant to a specific organization.

ORGANIZATION PROFILE:
{json.dumps(extracted_profile, indent=2)}

Original description: \"{org_description}\"

IDENTIFIED VULNERABILITIES:
{vulns_text}

TASK: For EACH vulnerability, assess if organization is vulnerable. Return JSON array:

[
  {{
    "name": "vulnerability name",
    "is_vulnerable": true/false,
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "why_vulnerable": [
      "specific reason 1 from org profile",
      "specific reason 2",
      "specific reason 3"
    ],
    "likelihood_percentage": 0-100,
    "estimated_impact_min": dollars,
    "estimated_impact_max": dollars,
    "impact_description": "specific consequences for this org"
  }}
]

Only include vulnerabilities where is_vulnerable = true.
Be specific: reference what the user actually wrote."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""

        # Strip markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Claude vulnerability mapping failed: {e}")
        return []


def generate_defense_plan(
    vulnerability: Dict[str, Any],
    extracted_profile: Dict[str, Any],
) -> str:
    """
    Generate defense recommendations for a specific vulnerability.
    """
    client = get_claude_client()
    if not client:
        return "Error: Claude API not available"

    profile_str = json.dumps(extracted_profile, indent=2)

    prompt = f"""You are a security architect creating a defense plan.

ORGANIZATION:
{profile_str}

VULNERABILITY:
{json.dumps(vulnerability, indent=2)}

TASK: Generate detailed, actionable defense plan with these sections:

## IMMEDIATE ACTIONS (This Week)
3-5 specific actions the org can take in next 7 days.
- Be specific: exact configurations, commands, settings
- Estimate time/cost for each
- Prioritize by impact

## 30-DAY HARDENING
3-5 medium-term improvements.
- Tools to deploy (specific products)
- Processes to implement
- Include costs

## DETECTION RULES
2-3 specific SIEM/EDR rules or queries (Splunk SPL preferred)
- Include comments explaining what each detects

## ESTIMATED COSTS
- Implementation cost (developer hours × $160/hr)
- Monthly ongoing costs
- Breach prevention value
- ROI calculation

Be realistic about small/medium org resources.
Reference specific tools by name.
All costs in USD."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""
        return response_text.strip() if response_text else "Failed to generate defense plan"
    except Exception as e:
        logger.error(f"Failed to generate defense plan: {e}")
        return f"Error generating defense plan: {str(e)}"


def generate_threat_research_report(
    db: Session,
    org: Organization,
    org_description: str,
) -> Dict[str, Any]:
    """
    Generate threat research report for organization.
    Returns cached report if valid, otherwise generates new one.
    """
    # Check cache
    description_hash = hash_org_description(org_description)
    cached = get_cached_report(db, org.id, description_hash)
    if cached:
        try:
            return {
                "report_id": cached.id,
                "generated_at": cached.generated_at.isoformat(),
                "org_description": cached.org_description,
                "extracted_profile": json.loads(cached.extracted_profile or "{}"),
                "vulnerabilities": json.loads(cached.vulnerabilities or "[]"),
                "executive_summary": json.loads(cached.executive_summary or "{}"),
                "search_queries": json.loads(cached.search_queries or "[]"),
                "sources_analyzed": cached.sources_analyzed,
            }
        except Exception as e:
            logger.error(f"Failed to load cached report: {e}")

    # Search for recent research
    search_queries = [
        "AI security vulnerabilities 2025",
        "LLM jailbreak attack techniques",
        "deepfake detection bypass methods",
        "AI-powered cyber attacks research",
    ]
    search_results = search_security_research(search_queries)

    # Extract profile and identify vulnerabilities
    profile_and_vulns = extract_profile_and_vulnerabilities(
        org_description, search_results
    )

    extracted_profile = profile_and_vulns.get("extracted_profile", {})
    vulnerabilities = profile_and_vulns.get("vulnerabilities", [])

    # Map vulnerabilities to org
    if vulnerabilities:
        mapped_vulns = map_vulnerabilities_to_org(
            org_description, extracted_profile, vulnerabilities
        )
    else:
        mapped_vulns = []

    # Generate defense plans for each vulnerability
    for vuln in mapped_vulns:
        if not vuln.get("defense_plan"):
            vuln["defense_plan"] = generate_defense_plan(vuln, extracted_profile)

    # Build executive summary
    executive_summary = {
        "total_vulnerabilities": len(mapped_vulns),
        "critical_count": len([v for v in mapped_vulns if v.get("risk_level") == "CRITICAL"]),
        "high_count": len([v for v in mapped_vulns if v.get("risk_level") == "HIGH"]),
        "medium_count": len([v for v in mapped_vulns if v.get("risk_level") == "MEDIUM"]),
    }

    # Build report
    report = {
        "report_id": f"report_{uuid.uuid4().hex[:8]}",
        "generated_at": datetime.utcnow().isoformat(),
        "org_description": org_description,
        "extracted_profile": extracted_profile,
        "vulnerabilities": mapped_vulns,
        "executive_summary": executive_summary,
        "search_queries": search_queries,
        "sources_analyzed": len(search_results),
    }

    # Cache report
    cached_until = datetime.utcnow() + timedelta(days=7)
    threat_report = ThreatResearchReport(
        id=report["report_id"],
        org_id=org.id,
        org_description=org_description,
        org_description_hash=description_hash,
        extracted_profile=json.dumps(extracted_profile),
        generated_at=datetime.utcnow(),
        search_queries=json.dumps(search_queries),
        sources_analyzed=len(search_results),
        vulnerabilities=json.dumps(mapped_vulns),
        executive_summary=json.dumps(executive_summary),
        cached_until=cached_until,
    )
    db.add(threat_report)
    db.commit()

    return report
