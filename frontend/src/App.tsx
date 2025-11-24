import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OrgProvider } from './context/OrgContext';
import { SubmitIncident } from './pages/SubmitIncident';
import { CampaignList } from './pages/CampaignList';
import { CampaignDetail } from './pages/CampaignDetail';
import { AmIAlone } from './pages/AmIAlone';
import { Analytics } from './pages/Analytics';
import { RiskAssessment } from './pages/RiskAssessment';
import { ThreatResearch } from './pages/ThreatResearch';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <OrgProvider>
        <BrowserRouter>
          <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
            <nav style={navStyle}>
              <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '2rem', alignItems: 'center' }}>
                <h2 style={{ margin: 0, color: '#0066cc' }}>SentinelNet</h2>
                <Link to="/" style={linkStyle}>Home</Link>
                <Link to="/submit" style={linkStyle}>Submit Incident</Link>
                <Link to="/campaigns" style={linkStyle}>Campaigns</Link>
                <Link to="/risk-assessment" style={linkStyle}>Risk Assessment</Link>
                <Link to="/threat-research" style={linkStyle}>Threat Research</Link>
                <Link to="/analytics" style={linkStyle}>Analytics</Link>
              </div>
            </nav>

            <main style={{ padding: '2rem' }}>
              <Routes>
                <Route path="/" element={<Navigate to="/campaigns" replace />} />
                <Route path="/submit" element={<SubmitIncident />} />
                <Route path="/campaigns" element={<CampaignList />} />
                <Route path="/campaigns/:id" element={<CampaignDetail />} />
                <Route path="/risk-assessment" element={<RiskAssessment />} />
                <Route path="/threat-research" element={<ThreatResearch />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/alone/:id" element={<AmIAlone />} />
              </Routes>
            </main>

            <footer style={footerStyle}>
              <p>SentinelNet – Privacy-Preserving Threat Intelligence Sharing</p>
              <p style={{ fontSize: '0.9rem', color: '#666' }}>
                Demo application for AI-enabled threat campaign detection
              </p>
            </footer>
          </div>
        </BrowserRouter>
      </OrgProvider>
    </QueryClientProvider>
  );
}

const navStyle: React.CSSProperties = {
  backgroundColor: '#ffffff',
  padding: '1rem 2rem',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  marginBottom: '0',
};

const linkStyle: React.CSSProperties = {
  color: '#333',
  textDecoration: 'none',
  fontWeight: 500,
};

const footerStyle: React.CSSProperties = {
  backgroundColor: '#ffffff',
  padding: '2rem',
  textAlign: 'center',
  marginTop: '4rem',
  borderTop: '1px solid #ddd',
};

export default App;
