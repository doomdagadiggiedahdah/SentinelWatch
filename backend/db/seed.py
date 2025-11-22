"""
Seed script to create demo organizations, incidents, and campaigns.
Run this after initializing the database.
"""
from backend.db.session import SessionLocal, init_db
from backend.db.models import (
    Organization, Campaign, Incident, SectorEnum, RegionEnum, 
    AttackVectorEnum, ImpactLevelEnum
)
from backend.auth import hash_api_key
from datetime import datetime, timedelta


# Demo API keys (in production, these would be securely generated)
DEMO_API_KEYS = {
    "org_alice": "alice_key_12345",
    "org_bob": "bob_key_67890",
    "org_charlie": "charlie_key_11111"
}

DEMO_ORGS = [
    {
        "id": "org_alice",
        "display_name": "Alice Hospital",
        "sector": SectorEnum.HEALTH,
        "region": RegionEnum.NA_EAST,
        "api_key": "alice_key_12345"
    },
    {
        "id": "org_bob",
        "display_name": "Bob Energy Corp",
        "sector": SectorEnum.ENERGY,
        "region": RegionEnum.NA_WEST,
        "api_key": "bob_key_67890"
    },
    {
        "id": "org_charlie",
        "display_name": "Charlie Water Utility",
        "sector": SectorEnum.WATER,
        "region": RegionEnum.NA_EAST,
        "api_key": "charlie_key_11111"
    }
]

# Demo campaigns
DEMO_CAMPAIGNS = [
    {
        "primary_attack_vector": AttackVectorEnum.AI_PHISHING,
        "ai_components": ["llm_content", "email_spoofing"],
        "sectors": ["health", "finance"],
        "regions": ["NA-East", "NA-West"],
        "first_seen": datetime.now() - timedelta(days=5),
        "last_seen": datetime.now() - timedelta(days=1),
        "num_orgs": 2,
        "num_incidents": 3,
        "canonical_summary": "AI-crafted phishing campaign using LLM-generated content targeting healthcare and finance sectors across North America."
    },
    {
        "primary_attack_vector": AttackVectorEnum.DEEPFAKE_VOICE,
        "ai_components": ["deepfake_audio"],
        "sectors": ["energy"],
        "regions": ["NA-West"],
        "first_seen": datetime.now() - timedelta(days=3),
        "last_seen": datetime.now(),
        "num_orgs": 1,
        "num_incidents": 2,
        "canonical_summary": "Deepfake voice BEC attempts targeting energy sector (details suppressed due to single org)."
    },
    {
        "primary_attack_vector": AttackVectorEnum.LLM_PROMPT_INJECTION,
        "ai_components": ["llm_inference"],
        "sectors": ["health", "water"],
        "regions": ["NA-East"],
        "first_seen": datetime.now() - timedelta(days=2),
        "last_seen": datetime.now(),
        "num_orgs": 2,
        "num_incidents": 4,
        "canonical_summary": "LLM prompt injection attacks observed across critical infrastructure sectors."
    }
]

# Demo incidents
DEMO_INCIDENTS = [
    # Campaign 1 - AI Phishing (org_alice)
    {
        "org_id": "org_alice",
        "local_ref": "INC-2025-001",
        "time_start": datetime.now() - timedelta(days=5),
        "time_end": datetime.now() - timedelta(days=5, hours=-2),
        "attack_vector": AttackVectorEnum.AI_PHISHING,
        "ai_components": ["llm_content", "email_spoofing"],
        "techniques": ["T1566"],
        "iocs": [
            {"type": "domain", "value": "secure-login-okta.example.com"},
            {"type": "email", "value": "noreply@secure-hospital-alerts.com"}
        ],
        "impact_level": ImpactLevelEnum.MEDIUM,
        "summary": "Staff received highly polished fake Okta emails with unusual domain. 50 users clicked links.",
        "campaign_id": 1
    },
    # Campaign 1 - AI Phishing (org_bob)
    {
        "org_id": "org_bob",
        "local_ref": "ENC-2025-042",
        "time_start": datetime.now() - timedelta(days=3),
        "time_end": datetime.now() - timedelta(days=3, hours=-1),
        "attack_vector": AttackVectorEnum.AI_PHISHING,
        "ai_components": ["llm_content", "email_spoofing"],
        "techniques": ["T1566"],
        "iocs": [
            {"type": "domain", "value": "secure-login-okta.example.com"},
            {"type": "email", "value": "alerts@energy-systems.net"}
        ],
        "impact_level": ImpactLevelEnum.HIGH,
        "summary": "SCADA operators targeted with AI-generated phishing mimicking system alerts.",
        "campaign_id": 1
    },
    # Campaign 1 - AI Phishing (org_charlie)
    {
        "org_id": "org_charlie",
        "local_ref": "WU-2025-789",
        "time_start": datetime.now() - timedelta(days=1),
        "time_end": datetime.now() - timedelta(days=1, hours=-3),
        "attack_vector": AttackVectorEnum.AI_PHISHING,
        "ai_components": ["llm_content"],
        "techniques": ["T1566"],
        "iocs": [
            {"type": "domain", "value": "okta-verification-secure.example.com"}
        ],
        "impact_level": ImpactLevelEnum.MEDIUM,
        "summary": "Phishing campaign targeting water utility admins with credential harvesting.",
        "campaign_id": 1
    },
    # Campaign 2 - Deepfake Voice (org_bob)
    {
        "org_id": "org_bob",
        "local_ref": "ENC-2025-043",
        "time_start": datetime.now() - timedelta(days=3),
        "time_end": datetime.now() - timedelta(days=3, hours=-1),
        "attack_vector": AttackVectorEnum.DEEPFAKE_VOICE,
        "ai_components": ["deepfake_audio"],
        "techniques": ["T1598"],
        "iocs": [
            {"type": "phone", "value": "+1-555-0101"},
            {"type": "caller_id", "value": "CFO Office"}
        ],
        "impact_level": ImpactLevelEnum.HIGH,
        "summary": "CEO deepfake voice call requesting wire transfer of $500k. Finance team requested verification.",
        "campaign_id": 2
    },
    # Campaign 2 - Deepfake Voice (org_bob) #2
    {
        "org_id": "org_bob",
        "local_ref": "ENC-2025-044",
        "time_start": datetime.now(),
        "time_end": None,
        "attack_vector": AttackVectorEnum.DEEPFAKE_VOICE,
        "ai_components": ["deepfake_audio"],
        "techniques": ["T1598"],
        "iocs": [
            {"type": "phone", "value": "+1-555-0102"}
        ],
        "impact_level": ImpactLevelEnum.HIGH,
        "summary": "Follow-up deepfake call targeting accounts payable department.",
        "campaign_id": 2
    },
    # Campaign 3 - LLM Prompt Injection (org_alice)
    {
        "org_id": "org_alice",
        "local_ref": "INC-2025-002",
        "time_start": datetime.now() - timedelta(days=2),
        "time_end": datetime.now() - timedelta(days=2, hours=-4),
        "attack_vector": AttackVectorEnum.LLM_PROMPT_INJECTION,
        "ai_components": ["llm_inference"],
        "techniques": ["T1190"],
        "iocs": [
            {"type": "url", "value": "hospital-chatbot.internal?prompt=ignore_rules"}
        ],
        "impact_level": ImpactLevelEnum.MEDIUM,
        "summary": "Attackers exploited hospital chatbot to extract patient information via prompt injection.",
        "campaign_id": 3
    },
    # Campaign 3 - LLM Prompt Injection (org_charlie)
    {
        "org_id": "org_charlie",
        "local_ref": "WU-2025-790",
        "time_start": datetime.now() - timedelta(days=2, hours=-6),
        "time_end": datetime.now() - timedelta(days=2, hours=-2),
        "attack_vector": AttackVectorEnum.LLM_PROMPT_INJECTION,
        "ai_components": ["llm_inference"],
        "techniques": ["T1190"],
        "iocs": [
            {"type": "url", "value": "water-control-assistant.local?jailbreak"}
        ],
        "impact_level": ImpactLevelEnum.HIGH,
        "summary": "SCADA AI assistant compromised to return false sensor readings.",
        "campaign_id": 3
    },
    # Campaign 3 - LLM Prompt Injection (org_alice) #2
    {
        "org_id": "org_alice",
        "local_ref": "INC-2025-003",
        "time_start": datetime.now(),
        "time_end": None,
        "attack_vector": AttackVectorEnum.LLM_PROMPT_INJECTION,
        "ai_components": ["llm_inference"],
        "techniques": ["T1190"],
        "iocs": [
            {"type": "url", "value": "hospital-chatbot.internal?admin_bypass"}
        ],
        "impact_level": ImpactLevelEnum.MEDIUM,
        "summary": "New attempt to override hospital chatbot safety guidelines.",
        "campaign_id": 3
    },
    # Campaign 3 - LLM Prompt Injection (org_charlie) #2
    {
        "org_id": "org_charlie",
        "local_ref": "WU-2025-791",
        "time_start": datetime.now() - timedelta(hours=2),
        "time_end": None,
        "attack_vector": AttackVectorEnum.LLM_PROMPT_INJECTION,
        "ai_components": ["llm_inference"],
        "techniques": ["T1190"],
        "iocs": [
            {"type": "url", "value": "water-ai-monitoring.local?inject_command"}
        ],
        "impact_level": ImpactLevelEnum.HIGH,
        "summary": "Ongoing attacks against water utility AI monitoring systems.",
        "campaign_id": 3
    }
]


def seed_organizations():
    """Seed demo organizations into the database"""
    db = SessionLocal()
    
    try:
        # Check if orgs already exist
        existing = db.query(Organization).count()
        if existing > 0:
            print(f"Database already has {existing} organizations. Skipping org seed.")
            db.close()
            return
        
        # Create demo organizations
        for org_data in DEMO_ORGS:
            api_key = org_data.pop("api_key")
            org = Organization(
                **org_data,
                api_key_hash=hash_api_key(api_key),
                query_budget=100,
                budget_reset_at=datetime.utcnow() + timedelta(days=1)
            )
            db.add(org)
            print(f"Created org: {org.id} with API key: {api_key}")
        
        db.commit()
        print("\nOrganizations seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding organizations: {e}")
        db.rollback()
    finally:
        db.close()


def seed_campaigns():
    """Seed demo campaigns into the database"""
    db = SessionLocal()
    
    try:
        # Check if campaigns already exist
        existing = db.query(Campaign).count()
        if existing > 0:
            print(f"Database already has {existing} campaigns. Skipping campaign seed.")
            db.close()
            return
        
        # Create demo campaigns
        for campaign_data in DEMO_CAMPAIGNS:
            campaign = Campaign(**campaign_data)
            db.add(campaign)
            print(f"Created campaign: {campaign_data['primary_attack_vector'].value}")
        
        db.commit()
        print(f"\nCampaigns seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding campaigns: {e}")
        db.rollback()
    finally:
        db.close()


def seed_incidents():
    """Seed demo incidents into the database"""
    db = SessionLocal()
    
    try:
        # Check if incidents already exist
        existing = db.query(Incident).count()
        if existing > 0:
            print(f"Database already has {existing} incidents. Skipping incident seed.")
            db.close()
            return
        
        # Create demo incidents
        for incident_data in DEMO_INCIDENTS:
            incident = Incident(**incident_data)
            db.add(incident)
            print(f"Created incident: {incident_data['local_ref']} for {incident_data['org_id']}")
        
        db.commit()
        print(f"\nIncidents seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding incidents: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database first
    init_db()
    print("Database initialized")
    
    # Seed organizations, campaigns, and incidents
    seed_organizations()
    seed_campaigns()
    seed_incidents()
    
    print("\nDemo API Keys:")
    for org_id, api_key in DEMO_API_KEYS.items():
        print(f"  {org_id}: {api_key}")
