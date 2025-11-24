from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.db.models import AttackVectorEnum, ImpactLevelEnum, SectorEnum, RegionEnum


# IOC model
class IOC(BaseModel):
    type: str
    value: str


# Request models
class IncidentCreate(BaseModel):
    local_ref: str
    time_start: datetime
    time_end: Optional[datetime] = None
    attack_vector: AttackVectorEnum
    ai_components: List[str] = Field(default_factory=list)
    techniques: List[str] = Field(default_factory=list)
    iocs: List[IOC] = Field(default_factory=list)
    impact_level: ImpactLevelEnum
    summary: str


class IncidentUpdate(BaseModel):
    local_ref: Optional[str] = None
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    attack_vector: Optional[AttackVectorEnum] = None
    ai_components: Optional[List[str]] = None
    techniques: Optional[List[str]] = None
    iocs: Optional[List[IOC]] = None
    impact_level: Optional[ImpactLevelEnum] = None
    summary: Optional[str] = None


# Response models
class IncidentResponse(BaseModel):
    id: int
    org_id: str
    local_ref: str
    time_start: datetime
    time_end: Optional[datetime]
    attack_vector: AttackVectorEnum
    ai_components: List[str]
    techniques: List[str]
    iocs: List[Dict[str, str]]
    impact_level: ImpactLevelEnum
    summary: str
    campaign_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class IncidentCreateResponse(BaseModel):
    incident_id: int
    campaign_id: Optional[int]


class CampaignSummary(BaseModel):
    id: int
    primary_attack_vector: AttackVectorEnum
    ai_components: List[str]
    num_orgs: int
    num_incidents: int
    first_seen: datetime
    last_seen: datetime
    sectors: List[str]  # May be empty for privacy (k-anonymity)
    regions: List[str]  # May be empty for privacy (k-anonymity)
    canonical_summary: Optional[str]

    class Config:
        from_attributes = True


class CampaignDetail(BaseModel):
    id: int
    primary_attack_vector: AttackVectorEnum
    ai_components: List[str]
    num_orgs: int
    num_incidents: int
    first_seen: datetime
    last_seen: datetime
    sectors: List[str]
    regions: List[str]
    canonical_summary: Optional[str]
    sample_iocs: List[IOC] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AmIAloneResponse(BaseModel):
    in_campaign: bool
    campaign: Optional[CampaignSummary] = None


class HealthResponse(BaseModel):
    status: str


# Filter models
class CampaignFilters(BaseModel):
    sector: Optional[SectorEnum] = None
    region: Optional[RegionEnum] = None
    attack_vector: Optional[AttackVectorEnum] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None


# Org profile schemas
class OrgProfileUpdate(BaseModel):
    org_size: Optional[str] = None
    primary_systems: Optional[List[str]] = None
    ai_systems_in_use: Optional[List[str]] = None
    mfa_enabled: Optional[str] = None
    siem_platform: Optional[str] = None
    security_training_frequency: Optional[str] = None
    phishing_simulations: Optional[str] = None
    incident_response_plan: Optional[str] = None


# Risk assessment schemas
class ThreatCard(BaseModel):
    threat_id: str
    threat_name: str
    attack_vector: str
    evidence: Dict[str, Any]
    exposure: Dict[str, Any]
    likelihood: str
    likelihood_percentage: float
    estimated_impact: Dict[str, float]
    reasoning: str
    risk_score: float


class RiskAssessmentResponse(BaseModel):
    assessed_at: str
    org_id: str
    relevant_incidents_count: int
    high_risk: List[ThreatCard]
    medium_risk: List[ThreatCard]
    low_risk: List[ThreatCard]


class PlaybookGenerateRequest(BaseModel):
    threat_id: str
    attack_vector: str


class PlaybookResponse(BaseModel):
    playbook_type: str
    threat_name: str
    full_text: str


# Threat research schemas
class ThreatResearchRequest(BaseModel):
    org_description: str = Field(..., min_length=50, max_length=2000)


class VulnerabilityResponse(BaseModel):
    name: str
    risk_level: str
    why_vulnerable: List[str]
    likelihood_percentage: float
    estimated_impact_min: float
    estimated_impact_max: float
    defense_plan: str


class ThreatResearchResponse(BaseModel):
    report_id: str
    generated_at: str
    org_description: str
    extracted_profile: Dict[str, Any]
    vulnerabilities: List[VulnerabilityResponse]
    executive_summary: Dict[str, int]
    search_queries: List[str]
    sources_analyzed: int
