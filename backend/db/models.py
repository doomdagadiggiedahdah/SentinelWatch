from sqlalchemy import (
    Column, String, Integer, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class SectorEnum(str, enum.Enum):
    HEALTH = "health"
    ENERGY = "energy"
    WATER = "water"
    GOV = "gov"
    FINANCE = "finance"
    OTHER = "other"


class RegionEnum(str, enum.Enum):
    NA_EAST = "NA-East"
    NA_WEST = "NA-West"
    EU = "EU"
    APAC = "APAC"


class AttackVectorEnum(str, enum.Enum):
    AI_PHISHING = "ai_phishing"
    DEEPFAKE_VOICE = "deepfake_voice"
    LLM_PROMPT_INJECTION = "llm_prompt_injection"
    AI_MALWARE_DEV = "ai_malware_dev"
    AI_LATERAL_MOVEMENT = "ai_lateral_movement"
    OTHER = "other"


class ImpactLevelEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True)  # e.g., "org_alice"
    display_name = Column(String, nullable=False)
    sector = Column(SQLEnum(SectorEnum), nullable=False)
    region = Column(SQLEnum(RegionEnum), nullable=False)
    api_key_hash = Column(String, nullable=False, unique=True)
    query_budget = Column(Integer, nullable=False, default=100)
    budget_reset_at = Column(DateTime, nullable=False)

    incidents = relationship("Incident", back_populates="organization")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_attack_vector = Column(SQLEnum(AttackVectorEnum), nullable=False)
    ai_components = Column(JSON, nullable=False, default=list)  # array of strings
    sectors = Column(JSON, nullable=False, default=list)  # array of strings
    regions = Column(JSON, nullable=False, default=list)  # array of strings
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    num_orgs = Column(Integer, nullable=False, default=0)
    num_incidents = Column(Integer, nullable=False, default=0)
    canonical_summary = Column(Text, nullable=True)

    incidents = relationship("Incident", back_populates="campaign")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    local_ref = Column(String, nullable=False)  # unique per org
    time_start = Column(DateTime, nullable=False)
    time_end = Column(DateTime, nullable=True)
    attack_vector = Column(SQLEnum(AttackVectorEnum), nullable=False)
    ai_components = Column(JSON, nullable=False, default=list)  # array of strings
    techniques = Column(JSON, nullable=False, default=list)  # array of strings
    iocs = Column(JSON, nullable=False, default=list)  # array of {type, value} objects
    impact_level = Column(SQLEnum(ImpactLevelEnum), nullable=False)
    summary = Column(Text, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="incidents")
    campaign = relationship("Campaign", back_populates="incidents")

    __table_args__ = (
        # Unique constraint on (org_id, local_ref)
        UniqueConstraint("org_id", "local_ref", name="uq_org_local_ref"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # submit_incident, list_campaigns, etc.
    details = Column(JSON, nullable=True)  # filters, IDs, etc.
    result_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
