import React, { useState } from 'react';
import { useCampaigns } from '../api/hooks';
import { CampaignTable } from '../components/CampaignTable';
import { OrgSelector } from '../components/OrgSelector';
import { AttackVectorEnum } from '../types/api';

export const CampaignList: React.FC = () => {
  const [attackVector, setAttackVector] = useState<AttackVectorEnum | ''>('');
  const { data: campaigns, isLoading, error } = useCampaigns(
    attackVector ? { attack_vector: attackVector as AttackVectorEnum } : undefined
  );

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Campaign Radar</h1>
      <OrgSelector />

      <div style={{ marginBottom: '1.5rem' }}>
        <h3>Filters</h3>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div>
            <label>
              <strong>Attack Vector:</strong>
            </label>
            <select
              value={attackVector}
              onChange={(e) => setAttackVector(e.target.value as AttackVectorEnum | '')}
              style={selectStyle}
            >
              <option value="">All</option>
              {Object.values(AttackVectorEnum).map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {isLoading && <p>Loading campaigns...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
      {campaigns && <CampaignTable campaigns={campaigns} />}
    </div>
  );
};

const selectStyle: React.CSSProperties = {
  padding: '0.5rem',
  fontSize: '1rem',
  borderRadius: '4px',
  border: '1px solid #ccc',
  marginLeft: '0.5rem',
};
