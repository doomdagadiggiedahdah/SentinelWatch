import React from 'react';
import { Link } from 'react-router-dom';
import { CampaignSummary } from '../types/api';

interface Props {
  campaigns: CampaignSummary[];
}

export const CampaignTable: React.FC<Props> = ({ campaigns }) => {
  if (campaigns.length === 0) {
    return <p>No campaigns found.</p>;
  }

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ backgroundColor: '#f0f0f0' }}>
          <th style={cellStyle}>Attack Vector</th>
          <th style={cellStyle}>AI Components</th>
          <th style={cellStyle}>Orgs</th>
          <th style={cellStyle}>Incidents</th>
          <th style={cellStyle}>First Seen</th>
          <th style={cellStyle}>Last Seen</th>
          <th style={cellStyle}>Sectors</th>
          <th style={cellStyle}>Regions</th>
          <th style={cellStyle}>Details</th>
        </tr>
      </thead>
      <tbody>
        {campaigns.map((campaign) => (
          <tr key={campaign.id} style={{ borderBottom: '1px solid #ddd' }}>
            <td style={cellStyle}>{campaign.primary_attack_vector}</td>
            <td style={cellStyle}>{campaign.ai_components.join(', ') || 'N/A'}</td>
            <td style={cellStyle}>{campaign.num_orgs}</td>
            <td style={cellStyle}>{campaign.num_incidents}</td>
            <td style={cellStyle}>{new Date(campaign.first_seen).toLocaleDateString()}</td>
            <td style={cellStyle}>{new Date(campaign.last_seen).toLocaleDateString()}</td>
            <td style={cellStyle}>
              {campaign.sectors.length > 0 ? campaign.sectors.join(', ') : <em>Suppressed</em>}
            </td>
            <td style={cellStyle}>
              {campaign.regions.length > 0 ? campaign.regions.join(', ') : <em>Suppressed</em>}
            </td>
            <td style={cellStyle}>
              <Link to={`/campaigns/${campaign.id}`} style={{ color: '#0066cc' }}>
                View
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const cellStyle: React.CSSProperties = {
  padding: '0.75rem',
  textAlign: 'left',
  border: '1px solid #ddd',
};
