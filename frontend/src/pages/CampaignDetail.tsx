import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCampaign } from '../api/hooks';
import { OrgSelector } from '../components/OrgSelector';

export const CampaignDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const campaignId = id ? parseInt(id, 10) : undefined;
  const { data: campaign, isLoading, error } = useCampaign(campaignId);

  if (isLoading) return <p>Loading campaign...</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error.message}</p>;
  if (!campaign) return <p>Campaign not found</p>;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <Link to="/campaigns" style={{ color: '#0066cc', marginBottom: '1rem', display: 'inline-block' }}>
        ← Back to Campaigns
      </Link>
      
      <h1>Campaign {campaign.id} – {campaign.primary_attack_vector}</h1>
      <OrgSelector />

      <div style={{ backgroundColor: '#f9f9f9', padding: '1.5rem', borderRadius: '8px', marginTop: '1rem' }}>
        <h3>Campaign Summary</h3>
        <p>{campaign.canonical_summary || 'No summary available.'}</p>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3>Statistics</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            <tr style={rowStyle}>
              <td style={labelStyle}>Organizations Affected:</td>
              <td>{campaign.num_orgs}</td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>Total Incidents:</td>
              <td>{campaign.num_incidents}</td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>First Seen:</td>
              <td>{new Date(campaign.first_seen).toLocaleString()}</td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>Last Seen:</td>
              <td>{new Date(campaign.last_seen).toLocaleString()}</td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>AI Components:</td>
              <td>{campaign.ai_components.join(', ') || 'None'}</td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>Sectors:</td>
              <td>
                {campaign.sectors.length > 0 ? (
                  campaign.sectors.join(', ')
                ) : (
                  <em>Details suppressed (k-anonymity, num_orgs &lt; 2)</em>
                )}
              </td>
            </tr>
            <tr style={rowStyle}>
              <td style={labelStyle}>Regions:</td>
              <td>
                {campaign.regions.length > 0 ? (
                  campaign.regions.join(', ')
                ) : (
                  <em>Details suppressed (k-anonymity, num_orgs &lt; 2)</em>
                )}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {campaign.sample_iocs && campaign.sample_iocs.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Sample IOCs</h3>
          <ul>
            {campaign.sample_iocs.map((ioc, i) => (
              <li key={i}>
                <strong>{ioc.type}:</strong> {ioc.value}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
        <strong>Privacy Notice:</strong> Incident-level details are not shown. This is an aggregate view only.
      </div>
    </div>
  );
};

const rowStyle: React.CSSProperties = {
  borderBottom: '1px solid #ddd',
};

const labelStyle: React.CSSProperties = {
  padding: '0.75rem',
  fontWeight: 'bold',
  width: '30%',
};
