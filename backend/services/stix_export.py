import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
from backend.db.models import Campaign, Incident
from sqlalchemy.orm import Session


def generate_stix_bundle(campaign: Campaign, incidents: List[Incident]) -> Dict[str, Any]:
    """
    Generate a STIX 2.1 bundle for a campaign.
    Includes Campaign, Attack-Pattern, Indicator, and Relationship objects.
    """
    bundle_id = f"bundle--{uuid.uuid4()}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Campaign object
    campaign_id = f"campaign--{uuid.uuid4()}"
    campaign_obj = {
        "type": "campaign",
        "id": campaign_id,
        "created": campaign.first_seen.isoformat() + "Z",
        "modified": campaign.last_seen.isoformat() + "Z",
        "name": f"Campaign: {campaign.primary_attack_vector}",
        "description": campaign.canonical_summary or "",
        "campaign_type": "attack",
    }

    objects = [campaign_obj]

    # Attack-Pattern object (one per unique technique)
    all_techniques = set()
    for incident in incidents:
        all_techniques.update(incident.techniques or [])

    attack_pattern_ids = {}
    for technique in all_techniques:
        ap_id = f"attack-pattern--{uuid.uuid4()}"
        attack_pattern_ids[technique] = ap_id
        attack_pattern_obj = {
            "type": "attack-pattern",
            "id": ap_id,
            "created": timestamp,
            "modified": timestamp,
            "name": technique,
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "external_id": technique,
                }
            ],
        }
        objects.append(attack_pattern_obj)

        # Relationship from campaign to attack pattern
        rel_id = f"relationship--{uuid.uuid4()}"
        relationship_obj = {
            "type": "relationship",
            "id": rel_id,
            "created": timestamp,
            "modified": timestamp,
            "relationship_type": "uses",
            "source_ref": campaign_id,
            "target_ref": ap_id,
        }
        objects.append(relationship_obj)

    # Indicator objects (one per unique IOC)
    all_iocs = {}
    for incident in incidents:
        for ioc in incident.iocs or []:
            key = f"{ioc.get('type')}:{ioc.get('value')}"
            if key not in all_iocs:
                all_iocs[key] = ioc

    indicator_ids = {}
    for key, ioc in all_iocs.items():
        ind_id = f"indicator--{uuid.uuid4()}"
        indicator_ids[key] = ind_id

        # Map IOC type to STIX pattern
        ioc_type = ioc.get("type", "unknown").lower()
        ioc_value = ioc.get("value", "")

        if ioc_type == "domain":
            pattern = f"[domain-name:value = '{ioc_value}']"
        elif ioc_type == "ip":
            pattern = f"[ipv4-addr:value = '{ioc_value}']"
        elif ioc_type == "email":
            pattern = f"[email-addr:value = '{ioc_value}']"
        elif ioc_type == "hash":
            pattern = f"[file:hashes.MD5 = '{ioc_value}' OR file:hashes.SHA-256 = '{ioc_value}']"
        else:
            pattern = f"[x-custom:value = '{ioc_value}']"

        indicator_obj = {
            "type": "indicator",
            "id": ind_id,
            "created": campaign.first_seen.isoformat() + "Z",
            "modified": campaign.last_seen.isoformat() + "Z",
            "pattern": pattern,
            "pattern_type": "stix",
            "valid_from": campaign.first_seen.isoformat() + "Z",
            "labels": ["malicious-activity"],
        }
        objects.append(indicator_obj)

        # Relationship from campaign to indicator
        rel_id = f"relationship--{uuid.uuid4()}"
        relationship_obj = {
            "type": "relationship",
            "id": rel_id,
            "created": timestamp,
            "modified": timestamp,
            "relationship_type": "indicates",
            "source_ref": ind_id,
            "target_ref": campaign_id,
        }
        objects.append(relationship_obj)

    # Create bundle
    bundle = {
        "type": "bundle",
        "id": bundle_id,
        "objects": objects,
    }

    return bundle


def export_campaign_as_stix(db: Session, campaign_id: int) -> Dict[str, Any]:
    """
    Export a campaign as STIX 2.1 bundle.
    """
    # Fetch campaign and incidents
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        return {"success": False, "error": "Campaign not found"}

    incidents = db.query(Incident).filter(Incident.campaign_id == campaign_id).all()

    try:
        bundle = generate_stix_bundle(campaign, incidents)
        return {"success": True, "bundle": bundle}
    except Exception as e:
        return {"success": False, "error": str(e)}
