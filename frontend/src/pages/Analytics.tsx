import React, { useState } from 'react';
import { useTrends, useDistribution, useSectorHeatmap, useCoordinationOpportunities } from '../api/hooks';
import { OrgSelector } from '../components/OrgSelector';
import { Link } from 'react-router-dom';

export const Analytics: React.FC = () => {
  const [timeWindow, setTimeWindow] = useState('90d');
  
  const trendsQuery = useTrends(timeWindow);
  const distQuery = useDistribution();
  const heatmapQuery = useSectorHeatmap();
  const opportunitiesQuery = useCoordinationOpportunities();

  const isLoading = trendsQuery.isLoading || distQuery.isLoading || heatmapQuery.isLoading || opportunitiesQuery.isLoading;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1>📊 Threat Intelligence Analytics</h1>
      <OrgSelector />

      <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
        <label><strong>Time Window:</strong></label>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
          {['7d', '30d', '90d'].map((w) => (
            <button
              key={w}
              onClick={() => setTimeWindow(w)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: timeWindow === w ? '#0066cc' : '#ddd',
                color: timeWindow === w ? 'white' : 'black',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              {w}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p>Loading analytics...</p>}

      {/* Trends */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>AI Component Trends</h2>
        {trendsQuery.isLoading ? (
          <p>Loading trends...</p>
        ) : trendsQuery.data && trendsQuery.data.length > 0 ? (
          <div style={{ overflowX: 'auto', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
            <svg width="100%" height="300" viewBox="0 0 800 300" style={{ minWidth: '800px' }}>
              {/* Simple line chart */}
              <text x="10" y="20" fontSize="14" fontWeight="bold">
                Incident count by AI component
              </text>
              
              {/* Grid lines */}
              {[0, 1, 2, 3, 4].map((i) => (
                <line
                  key={`gridline-${i}`}
                  x1="50"
                  y1={50 + (i * 50)}
                  x2="780"
                  y2={50 + (i * 50)}
                  stroke="#eee"
                  strokeWidth="1"
                />
              ))}

              {/* Data points */}
              {trendsQuery.data.map((point, i) => {
                const x = 50 + (i * (700 / trendsQuery.data.length));
                const maxCount = Math.max(...trendsQuery.data.flatMap((p) => [p.llm_content, p.deepfake_audio, p.deepfake_video, p.ai_code_assistant, p.llm_inference])) || 1;
                
                return (
                  <g key={`point-${i}`}>
                    <circle
                      cx={x}
                      cy={250 - (point.llm_content / maxCount) * 200}
                      r="3"
                      fill="#ff6b6b"
                    />
                  </g>
                );
              })}

              {/* Axes */}
              <line x1="50" y1="50" x2="50" y2="250" stroke="black" strokeWidth="2" />
              <line x1="50" y1="250" x2="780" y2="250" stroke="black" strokeWidth="2" />
              <text x="20" y="150" fontSize="12">Count</text>
              <text x="400" y="280" fontSize="12" textAnchor="middle">Time</text>
            </svg>
          </div>
        ) : (
          <p style={{ color: '#999' }}>No trend data available</p>
        )}
      </div>

      {/* Distribution */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>Attack Vector Distribution</h2>
        {distQuery.isLoading ? (
          <p>Loading distribution...</p>
        ) : distQuery.data && distQuery.data.length > 0 ? (
          <div style={{ padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              {distQuery.data.map((item) => (
                <div
                  key={item.attack_vector}
                  style={{
                    padding: '1rem',
                    backgroundColor: 'white',
                    border: `3px solid ${item.avg_impact === 'high' ? '#ff6b6b' : item.avg_impact === 'medium' ? '#ffd93d' : '#6bcf7f'}`,
                    borderRadius: '8px',
                    textAlign: 'center',
                  }}
                >
                  <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{item.count}</div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>{item.attack_vector}</div>
                  <div style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>Impact: <strong>{item.avg_impact}</strong></div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p style={{ color: '#999' }}>No distribution data available</p>
        )}
      </div>

      {/* Sector Heatmap */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>Cross-Sector Heatmap</h2>
        {heatmapQuery.isLoading ? (
          <p>Loading heatmap...</p>
        ) : heatmapQuery.data && heatmapQuery.data.length > 0 ? (
          <div style={{ overflowX: 'auto', padding: '1rem', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
            <table style={{ borderCollapse: 'collapse', minWidth: '100%' }}>
              <thead>
                <tr>
                  <th style={{ border: '1px solid #ccc', padding: '0.5rem', textAlign: 'left' }}>Sector</th>
                  {Array.from(new Set(heatmapQuery.data.map((h) => h.attack_vector))).map((av) => (
                    <th key={av} style={{ border: '1px solid #ccc', padding: '0.5rem', textAlign: 'center' }}>
                      {av}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from(new Set(heatmapQuery.data.map((h) => h.sector))).map((sector) => (
                  <tr key={sector}>
                    <td style={{ border: '1px solid #ccc', padding: '0.5rem', fontWeight: 'bold' }}>{sector}</td>
                    {Array.from(new Set(heatmapQuery.data.map((h) => h.attack_vector))).map((av) => {
                      const cell = heatmapQuery.data.find((h) => h.sector === sector && h.attack_vector === av);
                      const intensity = cell ? Math.min(cell.count / 5, 1) : 0;
                      return (
                        <td
                          key={`${sector}-${av}`}
                          style={{
                            border: '1px solid #ccc',
                            padding: '0.5rem',
                            textAlign: 'center',
                            backgroundColor: `rgba(255, 107, 107, ${intensity})`,
                          }}
                        >
                          {cell ? cell.count : '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: '#999' }}>No heatmap data available</p>
        )}
      </div>

      {/* Coordination Opportunities */}
      <div style={{ marginBottom: '2rem' }}>
        <h2>Coordination Opportunities</h2>
        {opportunitiesQuery.isLoading ? (
          <p>Loading opportunities...</p>
        ) : opportunitiesQuery.data && opportunitiesQuery.data.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {opportunitiesQuery.data.map((opp) => (
              <div
                key={opp.campaign_id}
                style={{
                  padding: '1.5rem',
                  backgroundColor:
                    opp.priority === 'critical'
                      ? '#ffcccc'
                      : opp.priority === 'high'
                      ? '#ffe6cc'
                      : '#fff3cc',
                  border: `2px solid ${opp.priority === 'critical' ? '#ff0000' : opp.priority === 'high' ? '#ff9900' : '#ffcc00'}`,
                  borderRadius: '8px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                  <h3 style={{ margin: 0 }}>{opp.campaign_name}</h3>
                  <span
                    style={{
                      padding: '0.25rem 0.75rem',
                      backgroundColor: opp.priority === 'critical' ? '#ff0000' : opp.priority === 'high' ? '#ff9900' : '#ffcc00',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase',
                    }}
                  >
                    {opp.priority}
                  </span>
                </div>
                <div style={{ fontSize: '0.9rem', color: '#333', marginBottom: '0.5rem' }}>
                  <strong>{opp.num_orgs}</strong> organizations | <strong>{opp.num_incidents}</strong> incidents
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '1rem' }}>
                  Last seen: {new Date(opp.last_seen).toLocaleString()}
                </div>
                <Link
                  to={`/campaigns/${opp.campaign_id}`}
                  style={{
                    display: 'inline-block',
                    padding: '0.5rem 1rem',
                    backgroundColor: '#0066cc',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                  }}
                >
                  View Campaign
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#999' }}>No coordination opportunities at this time</p>
        )}
      </div>
    </div>
  );
};
