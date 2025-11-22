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
