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
