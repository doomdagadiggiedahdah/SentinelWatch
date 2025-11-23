import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubmitIncident, useAnalyzeIncident } from '../api/hooks';
import { AttackVectorEnum, ImpactLevelEnum, IOC } from '../types/api';
import { OrgSelector } from '../components/OrgSelector';
import { useOrg } from '../context/OrgContext';

export const SubmitIncident: React.FC = () => {
  const navigate = useNavigate();
  const submitIncident = useSubmitIncident();
  const analyzeIncident = useAnalyzeIncident();
  useOrg(); // Ensures org context is available

  const [localRef, setLocalRef] = useState('');
  const [timeStart, setTimeStart] = useState('');
  const [timeEnd, setTimeEnd] = useState('');
  const [attackVector, setAttackVector] = useState<AttackVectorEnum>(AttackVectorEnum.AI_PHISHING);
  const [aiComponents, setAiComponents] = useState('llm_content');
  const [techniques, setTechniques] = useState('T1566');
  const [iocType, setIocType] = useState('domain');
  const [iocValue, setIocValue] = useState('');
  const [iocs, setIocs] = useState<IOC[]>([]);
  const [impactLevel, setImpactLevel] = useState<ImpactLevelEnum>(ImpactLevelEnum.MEDIUM);
  const [summary, setSummary] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const handleAddIoc = () => {
    if (iocType && iocValue) {
      setIocs([...iocs, { type: iocType, value: iocValue }]);
      setIocValue('');
    }
  };

  const handleRemoveIoc = (index: number) => {
    setIocs(iocs.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const result = await submitIncident.mutateAsync({
        local_ref: localRef,
        time_start: new Date(timeStart).toISOString(),
        time_end: timeEnd ? new Date(timeEnd).toISOString() : undefined,
        attack_vector: attackVector,
        ai_components: aiComponents.split(',').map(s => s.trim()).filter(Boolean),
        techniques: techniques.split(',').map(s => s.trim()).filter(Boolean),
        iocs,
        impact_level: impactLevel,
        summary,
      });

      alert(`Incident submitted successfully! ID: ${result.incident_id}, Campaign: ${result.campaign_id || 'None'}`);
      
      if (result.incident_id) {
        navigate(`/alone/${result.incident_id}`);
      }
    } catch (error) {
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1>Submit Incident</h1>
      <OrgSelector />
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <label><strong>Local Reference:</strong></label>
          <input
            type="text"
            value={localRef}
            onChange={(e) => setLocalRef(e.target.value)}
            required
            style={inputStyle}
            placeholder="e.g., ticket-123"
          />
        </div>

        <div>
          <label><strong>Time Start:</strong></label>
          <input
            type="datetime-local"
            value={timeStart}
            onChange={(e) => setTimeStart(e.target.value)}
            required
            style={inputStyle}
          />
        </div>

        <div>
          <label><strong>Time End (optional):</strong></label>
          <input
            type="datetime-local"
            value={timeEnd}
            onChange={(e) => setTimeEnd(e.target.value)}
            style={inputStyle}
          />
        </div>

        <div>
          <label><strong>Attack Vector:</strong></label>
          <select value={attackVector} onChange={(e) => setAttackVector(e.target.value as AttackVectorEnum)} style={inputStyle}>
            {Object.values(AttackVectorEnum).map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>

        <div>
          <label><strong>AI Components (comma-separated):</strong></label>
          <input
            type="text"
            value={aiComponents}
            onChange={(e) => setAiComponents(e.target.value)}
            style={inputStyle}
            placeholder="e.g., llm_content, deepfake_audio"
          />
        </div>

        <div>
          <label><strong>Techniques (comma-separated):</strong></label>
          <input
            type="text"
            value={techniques}
            onChange={(e) => setTechniques(e.target.value)}
            style={inputStyle}
            placeholder="e.g., T1566, T1078"
          />
        </div>

        <div>
          <label><strong>IOCs:</strong></label>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <select value={iocType} onChange={(e) => setIocType(e.target.value)} style={{ ...inputStyle, flex: 1 }}>
              <option value="domain">Domain</option>
              <option value="ip">IP Address</option>
              <option value="email">Email</option>
              <option value="hash">Hash</option>
            </select>
            <input
              type="text"
              value={iocValue}
              onChange={(e) => setIocValue(e.target.value)}
              placeholder="IOC value"
              style={{ ...inputStyle, flex: 2 }}
            />
            <button type="button" onClick={handleAddIoc} style={buttonStyle}>Add IOC</button>
          </div>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {iocs.map((ioc, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>
                {ioc.type}: {ioc.value}{' '}
                <button type="button" onClick={() => handleRemoveIoc(i)} style={{ ...buttonStyle, fontSize: '0.8rem' }}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <label><strong>Impact Level:</strong></label>
          <select value={impactLevel} onChange={(e) => setImpactLevel(e.target.value as ImpactLevelEnum)} style={inputStyle}>
            {Object.values(ImpactLevelEnum).map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>

        <div>
          <label><strong>Summary:</strong></label>
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            required
            rows={4}
            style={inputStyle}
            placeholder="Brief summary of the incident..."
          />
          <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button
              type="button"
              onClick={async () => {
                setAnalysisError(null);
                setAnalyzing(true);
                try {
                  const res = await analyzeIncident.mutateAsync({ summary });
                  if (res.success) {
                    if (res.attack_vector) setAttackVector(res.attack_vector as AttackVectorEnum);
                    if (res.ai_components) setAiComponents(res.ai_components.join(', '));
                    if (res.techniques) setTechniques(res.techniques.join(', '));
                    if (res.suggested_iocs) setIocs(res.suggested_iocs as IOC[]);
                  } else {
                    setAnalysisError(res.error || 'Analysis failed');
                  }
                } catch (e: any) {
                  setAnalysisError(e?.message || 'Analysis failed');
                } finally {
                  setAnalyzing(false);
                }
              }}
              style={{ ...buttonStyle, backgroundColor: '#444' }}
              disabled={analyzing}
            >
              {analyzing ? 'Analyzing…' : 'Analyze with AI'}
            </button>
            {analysisError && <span style={{ color: 'crimson' }}>{analysisError}</span>}
          </div>
        </div>

        <button type="submit" disabled={submitIncident.isPending} style={{ ...buttonStyle, padding: '0.75rem' }}>
          {submitIncident.isPending ? 'Submitting...' : 'Submit Incident'}
        </button>
      </form>
    </div>
  );
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.5rem',
  fontSize: '1rem',
  borderRadius: '4px',
  border: '1px solid #ccc',
};

const buttonStyle: React.CSSProperties = {
  padding: '0.5rem 1rem',
  fontSize: '1rem',
  borderRadius: '4px',
  border: 'none',
  backgroundColor: '#0066cc',
  color: 'white',
  cursor: 'pointer',
};
