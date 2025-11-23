import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCampaign, useGeneratePlaybook, useExportSTIX } from '../api/hooks';
import { OrgSelector } from '../components/OrgSelector';

export const CampaignDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const campaignId = id ? parseInt(id, 10) : undefined;
  const { data: campaign, isLoading, error } = useCampaign(campaignId);
  const generatePlaybook = useGeneratePlaybook(campaignId);
  const exportSTIX = useExportSTIX(campaignId);
  const [showPlaybook, setShowPlaybook] = useState(false);
  const [playbookText, setPlaybookText] = useState('');
  const [showPlaybookError, setShowPlaybookError] = useState<string | null>(null);

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

      <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
        <button
          onClick={async () => {
            setShowPlaybookError(null);
            try {
              const result = await generatePlaybook.mutateAsync();
              if (result.success) {
                setPlaybookText(result.playbook || '');
                setShowPlaybook(true);
              } else {
                setShowPlaybookError(result.error || 'Failed to generate playbook');
              }
            } catch (e: any) {
              setShowPlaybookError(e?.message || 'Error generating playbook');
            }
          }}
          style={actionButtonStyle}
          disabled={generatePlaybook.isPending}
        >
          {generatePlaybook.isPending ? '⚡ Generating Playbook...' : '⚡ Generate Defensive Playbook'}
        </button>
        <button
          onClick={async () => {
            try {
              const result = await exportSTIX.mutateAsync();
              if (result.success && result.bundle) {
                const element = document.createElement('a');
                element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(result.bundle, null, 2)));
                element.setAttribute('download', `campaign-${campaignId}-stix.json`);
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
              }
            } catch (e: any) {
              alert(`Error exporting STIX: ${e?.message}`);
            }
          }}
          style={{ ...actionButtonStyle, backgroundColor: '#666' }}
          disabled={exportSTIX.isPending}
        >
          {exportSTIX.isPending ? '📦 Exporting...' : '📦 Export as STIX 2.1'}
        </button>
      </div>

      {showPlaybookError && (
        <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#ffcccc', borderRadius: '4px', color: 'darkred' }}>
          <strong>Error:</strong> {showPlaybookError}
        </div>
      )}

      {showPlaybook && playbookText && (
        <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#f0f8ff', borderRadius: '8px', border: '1px solid #0066cc' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Defensive Playbook</h3>
            <button
              onClick={() => setShowPlaybook(false)}
              style={{ padding: '0.25rem 0.75rem', backgroundColor: '#ddd', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Close
            </button>
          </div>
          <div
            style={{
              backgroundColor: 'white',
              padding: '1rem',
              borderRadius: '4px',
              maxHeight: '600px',
              overflowY: 'auto',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
            }}
          >
            {playbookText}
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => {
                const element = document.createElement('a');
                element.setAttribute('href', 'data:text/markdown;charset=utf-8,' + encodeURIComponent(playbookText));
                element.setAttribute('download', `playbook-${campaignId}.md`);
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
              }}
              style={{ ...actionButtonStyle, backgroundColor: '#28a745' }}
            >
              Download as Markdown
            </button>
            <button
              onClick={() => {
                const element = document.createElement('a');
                element.setAttribute('href', 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify({ playbook: playbookText }, null, 2)));
                element.setAttribute('download', `playbook-${campaignId}.json`);
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
              }}
              style={{ ...actionButtonStyle, backgroundColor: '#666' }}
            >
              Download as JSON
            </button>
          </div>
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

const actionButtonStyle: React.CSSProperties = {
  padding: '0.75rem 1rem',
  fontSize: '0.95rem',
  borderRadius: '4px',
  border: 'none',
  backgroundColor: '#0066cc',
  color: 'white',
  cursor: 'pointer',
  fontWeight: 'bold',
};
