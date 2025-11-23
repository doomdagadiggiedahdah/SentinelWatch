import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiClient } from './client';
import { useOrg } from '../context/OrgContext';
import {
  IncidentCreate,
  IncidentCreateResponse,
  CampaignSummary,
  CampaignDetail,
  AmIAloneResponse,
  AttackVectorEnum,
  SectorEnum,
  RegionEnum,
} from '../types/api';

export const useApiClient = () => {
  const { currentOrg } = useOrg();
  return new ApiClient(currentOrg.apiKey);
};

// Incidents
export const useSubmitIncident = () => {
  const client = useApiClient();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: IncidentCreate) => 
      client.post<IncidentCreateResponse>('/incidents', data),
    onSuccess: () => {
      // Invalidate campaigns list to reflect new incident
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
};

// Campaigns
interface CampaignFilters {
  sector?: SectorEnum;
  region?: RegionEnum;
  attack_vector?: AttackVectorEnum;
  since?: string;
  until?: string;
}

export const useCampaigns = (filters?: CampaignFilters) => {
  const client = useApiClient();
  
  const queryParams = new URLSearchParams();
  if (filters?.sector) queryParams.append('sector', filters.sector);
  if (filters?.region) queryParams.append('region', filters.region);
  if (filters?.attack_vector) queryParams.append('attack_vector', filters.attack_vector);
  if (filters?.since) queryParams.append('since', filters.since);
  if (filters?.until) queryParams.append('until', filters.until);
  
  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';

  return useQuery({
    queryKey: ['campaigns', filters],
    queryFn: () => client.get<CampaignSummary[]>(`/campaigns${queryString}`),
  });
};

export const useCampaign = (campaignId: number | undefined) => {
  const client = useApiClient();

  return useQuery({
    queryKey: ['campaign', campaignId],
    queryFn: () => client.get<CampaignDetail>(`/campaigns/${campaignId}`),
    enabled: !!campaignId,
  });
};

export const useAmIAlone = (incidentId: number | undefined) => {
  const client = useApiClient();

  return useQuery({
    queryKey: ['am-i-alone', incidentId],
    queryFn: () => client.get<AmIAloneResponse>(`/campaigns/am-i-alone/${incidentId}`),
    enabled: !!incidentId,
  });
};

// Incident analysis
export interface AnalyzeIncidentRequest {
  summary: string;
  sector?: string;
  region?: string;
}

export interface AnalyzeIncidentResponse {
  success: boolean;
  attack_vector?: string;
  ai_components?: string[];
  techniques?: string[];
  suggested_iocs?: Array<{ type: string; value: string }>;
  confidence?: string;
  reasoning?: string;
  error?: string;
}

export const useAnalyzeIncident = () => {
  const client = useApiClient();

  return useMutation({
    mutationFn: (data: AnalyzeIncidentRequest) =>
      client.post<AnalyzeIncidentResponse>('/incidents/analyze', data),
  });
};

// Playbook generation
export interface PlaybookResponse {
  success: boolean;
  playbook?: string;
  error?: string;
}

export const useGeneratePlaybook = (campaignId: number | undefined) => {
  const client = useApiClient();

  return useMutation({
    mutationFn: () =>
      client.post<PlaybookResponse>(`/campaigns/${campaignId}/playbook`, {}),
  });
};

// STIX export
export const useExportSTIX = (campaignId: number | undefined) => {
  const client = useApiClient();

  return useMutation({
    mutationFn: async () => {
      const response = await client.get<any>(`/campaigns/${campaignId}/export-stix`);
      return response;
    },
  });
};

// Analytics
export interface TrendDataPoint {
  time: string;
  llm_content: number;
  deepfake_audio: number;
  deepfake_video: number;
  ai_code_assistant: number;
  llm_inference: number;
  other: number;
}

export interface DistributionItem {
  attack_vector: string;
  count: number;
  avg_impact: string;
}

export interface HeatmapCell {
  sector: string;
  attack_vector: string;
  count: number;
}

export interface CoordinationOpportunity {
  campaign_id: number;
  campaign_name: string;
  priority: string;
  num_orgs: number;
  num_incidents: number;
  last_seen: string;
  attack_vector: string;
}

export const useTrends = (timeWindow: string = '90d') => {
  const client = useApiClient();
  return useQuery({
    queryKey: ['analytics-trends', timeWindow],
    queryFn: () => client.get<TrendDataPoint[]>(`/analytics/trends?time_window=${timeWindow}`),
  });
};

export const useDistribution = () => {
  const client = useApiClient();
  return useQuery({
    queryKey: ['analytics-distribution'],
    queryFn: () => client.get<DistributionItem[]>('/analytics/distribution'),
  });
};

export const useSectorHeatmap = () => {
  const client = useApiClient();
  return useQuery({
    queryKey: ['analytics-heatmap'],
    queryFn: () => client.get<HeatmapCell[]>('/analytics/sector-heatmap'),
  });
};

export const useCoordinationOpportunities = () => {
  const client = useApiClient();
  return useQuery({
    queryKey: ['analytics-opportunities'],
    queryFn: () => client.get<CoordinationOpportunity[]>('/analytics/opportunities'),
  });
};
