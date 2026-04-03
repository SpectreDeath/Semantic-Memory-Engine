import React, { useState, useEffect } from 'react';
import { Database, Activity, BrainCircuit } from 'lucide-react';

const ConnectionsManager = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState('langflow');

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/v1/connections/status`);
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
      setStatus({
        database: 'offline',
        sidecar: { status: 'offline', provider: 'unknown' }
      });
    }
    setLoading(false);
  };

  const updateProvider = async (newProvider) => {
    try {
      await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/v1/connections/ai-provider`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_type: newProvider })
      });
      setProvider(newProvider);
      fetchStatus();
    } catch (err) {
      console.error('Failed to update provider:', err);
    }
  };

  useEffect(() => {
    // Use requestAnimationFrame to avoid calling setState synchronously
    requestAnimationFrame(() => {
      fetchStatus();
    });
  }, []);

  return (
    <section className="card glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3>Control Room: Service Connections</h3>
        <button 
          onClick={fetchStatus} 
          disabled={loading} 
          className="glass-panel" 
          style={{ 
            padding: '0.5rem 1rem', 
            fontSize: '0.8rem', 
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1,
          }}
        >
          {loading ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Database size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: '600' }}>Relational Nexus</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: status?.database === 'online' ? 'var(--success)' : 'var(--danger)' }}>
             Status: {status?.database || 'Unknown'}
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Activity size={18} color="var(--accent-purple)" />
            <span style={{ fontWeight: '600' }}>AI Sidecar</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: status?.sidecar?.status === 'online' ? 'var(--success)' : 'var(--danger)' }}>
             Status: {status?.sidecar?.status || 'Offline'}
          </p>
          {status?.sidecar && <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Provider: {status.sidecar.provider}</p>}
        </div>

        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <BrainCircuit size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: '600' }}>AI Provider Strategy</span>
          </div>
          <select 
            value={provider} 
            onChange={(e) => updateProvider(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              background: 'rgba(0,0,0,0.3)', 
              color: 'white', 
              border: '1px solid var(--glass-border)', 
              borderRadius: '4px' 
            }}
          >
            <option value="langflow">Langflow (Hybrid-Cloud)</option>
            <option value="mock">Local Mock (Offline/Fast)</option>
            <option value="ollama">Ollama (Fully Local)</option>
          </select>
        </div>
      </div>
    </section>
  );
};

export default ConnectionsManager;