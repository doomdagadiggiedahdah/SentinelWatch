import os
import json
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_claude_client():
    """Lazily import and create Anthropic client."""
    try:
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        return Anthropic(api_key=api_key)
    except ImportError:
        return None


class AnalysisResult:
    def __init__(self, success: bool, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        self.success = success
        self.data = data or {}
        self.error = error


def analyze_incident(summary: str, sector: str = "", region: str = "") -> AnalysisResult:
    """
    Use Claude to analyze an incident summary and extract structured classification.

    Returns: {
        attack_vector: str,
        ai_components: List[str],
        techniques: List[str],
        suggested_iocs: List[{type, value}],
        confidence: "high" | "medium" | "low",
        reasoning: str
    }
    """
    client = get_claude_client()
    if not client:
        logger.warning("Claude API not available, returning empty analysis")
        return AnalysisResult(success=False, error="Claude API not configured")

    prompt = f"""You are a cybersecurity incident classifier specializing in AI-enabled threats.

Incident report:
"{summary}"

Organization context:
- Sector: {sector if sector else "unknown"}
- Region: {region if region else "unknown"}

Analyze this incident and return a JSON object with:
{{
  "attack_vector": "one of: ai_phishing, deepfake_voice, deepfake_video, llm_prompt_injection, ai_malware_dev, ai_lateral_movement, other",
  "ai_components": ["list from: llm_content, deepfake_audio, deepfake_video, ai_code_assistant, llm_inference, other"],
  "techniques": ["MITRE ATT&CK technique IDs, e.g., T1566.002"],
  "suggested_iocs": [
    {{"type": "domain|ip|email|hash", "value": "extracted value"}}
  ],
  "confidence": "high|medium|low",
  "reasoning": "brief explanation of classification"
}}

Only return valid JSON. Do not include any text outside the JSON structure."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""
        logger.info(f"Claude response (raw): {response_text[:500]}...")  # Log first 500 chars
        
        # Strip markdown code blocks if present
        if response_text.startswith("```"):
            # Remove ```json or ``` at start and ``` at end
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first line
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove last line
            response_text = "\n".join(lines)
        
        result_data = json.loads(response_text)

        return AnalysisResult(success=True, data=result_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.error(f"Raw response was: {response_text}")
        return AnalysisResult(success=False, error=f"Failed to parse response: {str(e)}")
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return AnalysisResult(success=False, error=str(e))


def generate_campaign_summary(
    incident_summaries: List[str],
    attack_vector: str,
    ai_components: List[str],
    first_seen: datetime,
    last_seen: datetime,
    regions: List[str],
    sectors: List[str],
) -> str:
    """
    Generate a professional campaign summary from multiple incidents.
    Falls back to template if Claude fails.
    """
    client = get_claude_client()

    # Fallback template
    fallback_summary = (
        f"Campaign targeting {', '.join(sectors) if sectors else 'multiple sectors'} "
        f"using {', '.join(ai_components) if ai_components else 'AI components'}. "
        f"Attack vector: {attack_vector}. Active from {first_seen.date()} to {last_seen.date()}."
    )

    if not client:
        logger.warning("Claude API not available, using template summary")
        return fallback_summary

    # Format incident summaries
    incidents_text = "\n".join([f"- {s}" for s in incident_summaries[:5]])  # Limit to first 5

    prompt = f"""You are a threat intelligence analyst writing a campaign brief.

Incidents in this campaign (organization identities protected):

{incidents_text}

Campaign metadata:
- Attack vector: {attack_vector}
- AI components: {', '.join(ai_components) if ai_components else 'unknown'}
- Timeframe: {first_seen.date()} to {last_seen.date()}
- Geographic spread: {', '.join(regions) if regions else 'multiple regions'}
- Sectors affected: {', '.join(sectors) if sectors else 'multiple sectors'}

Write a concise campaign summary (2-3 sentences, max 150 words) that:
1. Describes the attack pattern and tactics
2. Highlights the AI-enabled aspects
3. Notes cross-sector or geographic coordination if applicable
4. Provides actionable intelligence for defenders
5. Does NOT identify specific victim organizations

Style: Professional threat intelligence brief. Be specific but protect victim privacy.

Return ONLY the summary text, no additional formatting."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""
        return response_text.strip() if response_text else fallback_summary
    except Exception as e:
        logger.error(f"Failed to generate campaign summary: {e}")
        return fallback_summary


def generate_playbook(
    campaign_summary: str,
    attack_vector: str,
    ai_components: List[str],
    num_orgs: int,
    num_incidents: int,
    first_seen: datetime,
    last_seen: datetime,
    org_sector: str,
    org_region: str,
    org_incidents: List[str],
) -> str:
    """
    Generate a customized defensive playbook for an organization.
    Returns markdown-formatted playbook or error message.
    """
    client = get_claude_client()
    if not client:
        logger.error("Claude API not available for playbook generation")
        return "Error: Claude API not configured. Playbook generation unavailable."

    org_incidents_text = "\n".join([f"- {s}" for s in org_incidents[:10]])  # Limit to first 10

    prompt = f"""You are an incident response expert creating an actionable defensive playbook.

CAMPAIGN INTELLIGENCE:
{campaign_summary}

Campaign Details:
- Attack Vector: {attack_vector}
- AI Components: {', '.join(ai_components)}
- Scale: {num_orgs} organizations, {num_incidents} incidents
- Timeline: {first_seen.date()} to {last_seen.date()}

OUR ORGANIZATION'S EXPOSURE:
{org_incidents_text if org_incidents_text else "No specific incidents yet, but organization is at risk"}

OUR ENVIRONMENT:
- Sector: {org_sector}
- Region: {org_region}

Generate a prioritized, sector-specific defensive playbook with these sections:

## Immediate Actions (Next 1 Hour)
[3-5 critical steps to contain threat right now]

## Short-Term Mitigations (Next 24 Hours)
[5-7 actions to reduce risk and prevent spread]

## Long-Term Prevention (Next 30 Days)
[4-6 strategic improvements to prevent recurrence]

## Detection Rules
[Specific SIEM/EDR queries or rules to implement - use actual syntax where possible]

## Indicators to Block
[Specific IoCs from this campaign to add to blocklists]

## AI-Specific Defenses
[How to detect and prevent the AI-enabled aspects of this attack]

Make all recommendations:
- Specific and actionable (not generic advice)
- Appropriate for {org_sector} sector's risk profile
- Prioritized by impact and ease of implementation
- Include both technical and procedural controls"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text if message.content else ""
        return response_text.strip() if response_text else "Failed to generate playbook"
    except Exception as e:
        logger.error(f"Failed to generate playbook: {e}")
        return f"Error generating playbook: {str(e)}"
