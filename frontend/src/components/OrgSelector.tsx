import React from 'react';
import { useOrg } from '../context/OrgContext';
import { DEMO_ORGS } from '../types/api';

export const OrgSelector: React.FC = () => {
  const { currentOrg, setCurrentOrg } = useOrg();

  return (
    <div style={{ marginBottom: '1rem' }}>
      <label htmlFor="org-select" style={{ marginRight: '0.5rem' }}>
        <strong>Simulating Org:</strong>
      </label>
      <select
        id="org-select"
        value={currentOrg.id}
        onChange={(e) => {
          const org = DEMO_ORGS.find((o) => o.id === e.target.value);
          if (org) setCurrentOrg(org);
        }}
        style={{
          padding: '0.5rem',
          fontSize: '1rem',
          borderRadius: '4px',
          border: '1px solid #ccc',
        }}
      >
        {DEMO_ORGS.map((org) => (
          <option key={org.id} value={org.id}>
            {org.name}
          </option>
        ))}
      </select>
    </div>
  );
};
