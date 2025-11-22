import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAmIAlone } from '../api/hooks';
import { OrgSelector } from '../components/OrgSelector';

export const AmIAlone: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const incidentId = id ? parseInt(id, 10) : undefined;
  const { data, isLoading, error } = useAmIAlone(incidentId);

  if (isLoading) return <p>Checking campaign membership...</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error.message}</p>;
  if (!data) return <p>No data available</p>;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1>Am I Alone?</h1>
      <OrgSelector />

      <div style={{ marginTop: '2rem', padding: '2rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
        <h2>Incident #{incidentId}</h2>
        
        {!data.in_campaign ? (
          <div style={{ padding: '1.5rem', backgroundColor: '#d4edda', borderRadius: '4px', marginTop: '1rem' }}>
            <h3 style={{ color: '#155724' }}>No Matching Campaign Found</h3>
            <p>
              You might be the first to see this pattern. No other organizations have reported
              similar incidents yet.
            </p>
          </div>
        ) : (
          <div>
            <div style={{ padding: '1.5rem', backgroundColor: '#cce5ff', borderRadius: '4px', marginTop: '1rem' }}>
              <h3 style={{ color: '#004085' }}>Part of a Wider Campaign</h3>
              <p>
                This incident is part of Campaign #{data.campaign!.id}. You are not alone – multiple
                organizations are seeing this pattern.
              </p>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <h3>Campaign Information</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Attack Vector:</td>
                    <td>{data.campaign!.primary_attack_vector}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>AI Components:</td>
                    <td>{data.campaign!.ai_components.join(', ') || 'None'}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Organizations Affected:</td>
                    <td>{data.campaign!.num_orgs}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Total Incidents:</td>
                    <td>{data.campaign!.num_incidents}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>First Seen:</td>
                    <td>{new Date(data.campaign!.first_seen).toLocaleString()}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Last Seen:</td>
                    <td>{new Date(data.campaign!.last_seen).toLocaleString()}</td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Sectors:</td>
                    <td>
                      {data.campaign!.sectors.length > 0
                        ? data.campaign!.sectors.join(', ')
                        : <em>Details suppressed (k-anonymity)</em>
                      }
                    </td>
                  </tr>
                  <tr style={rowStyle}>
                    <td style={labelStyle}>Regions:</td>
                    <td>
                      {data.campaign!.regions.length > 0
                        ? data.campaign!.regions.join(', ')
                        : <em>Details suppressed (k-anonymity)</em>
                      }
                    </td>
                  </tr>
                </tbody>
              </table>

              <div style={{ marginTop: '1.5rem' }}>
                <Link
                  to={`/campaigns/${data.campaign!.id}`}
                  style={{
                    display: 'inline-block',
                    padding: '0.75rem 1.5rem',
                    backgroundColor: '#0066cc',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '4px',
                  }}
                >
                  View Full Campaign Details
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={{ marginTop: '2rem', textAlign: 'center' }}>
        <Link to="/submit" style={{ color: '#0066cc', marginRight: '1rem' }}>
          Submit Another Incident
        </Link>
        <Link to="/campaigns" style={{ color: '#0066cc' }}>
          View All Campaigns
        </Link>
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
