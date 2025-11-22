// Enums matching backend
export enum SectorEnum {
  HEALTH = "health",
  ENERGY = "energy",
  WATER = "water",
  GOV = "gov",
  FINANCE = "finance",
  OTHER = "other",
}

export enum RegionEnum {
  NA_EAST = "NA-East",
  NA_WEST = "NA-West",
  EU = "EU",
  APAC = "APAC",
}

export enum AttackVectorEnum {
  AI_PHISHING = "ai_phishing",
  DEEPFAKE_VOICE = "deepfake_voice",
  LLM_PROMPT_INJECTION = "llm_prompt_injection",
  AI_MALWARE_DEV = "ai_malware_dev",
  AI_LATERAL_MOVEMENT = "ai_lateral_movement",
  OTHER = "other",
}

export enum ImpactLevelEnum {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
}

// Types
export interface IOC {
  type: string;
  value: string;
}

export interface IncidentCreate {
  local_ref: string;
  time_start: string; // ISO datetime string
  time_end?: string; // ISO datetime string
  attack_vector: AttackVectorEnum;
  ai_components: string[];
  techniques: string[];
  iocs: IOC[];
  impact_level: ImpactLevelEnum;
  summary: string;
}

export interface IncidentResponse {
  id: number;
  org_id: string;
  local_ref: string;
  time_start: string;
  time_end?: string;
  attack_vector: AttackVectorEnum;
  ai_components: string[];
  techniques: string[];
  iocs: Record<string, string>[];
  impact_level: ImpactLevelEnum;
  summary: string;
  campaign_id?: number;
  created_at: string;
}

export interface IncidentCreateResponse {
  incident_id: number;
  campaign_id?: number;
}

export interface CampaignSummary {
  id: number;
  primary_attack_vector: AttackVectorEnum;
  ai_components: string[];
  num_orgs: number;
  num_incidents: number;
  first_seen: string;
  last_seen: string;
  sectors: string[];
  regions: string[];
  canonical_summary?: string;
}

export interface CampaignDetail extends CampaignSummary {
  sample_iocs: IOC[];
}

export interface AmIAloneResponse {
  in_campaign: boolean;
  campaign?: CampaignSummary;
}

// Demo org configuration
export interface DemoOrg {
  id: string;
  name: string;
  apiKey: string;
}

export const DEMO_ORGS: DemoOrg[] = [
  { id: "org_alice", name: "Alice Hospital", apiKey: "alice_key_12345" },
  { id: "org_bob", name: "Bob Energy Corp", apiKey: "bob_key_67890" },
  { id: "org_charlie", name: "Charlie Water Utility", apiKey: "charlie_key_11111" },
];
