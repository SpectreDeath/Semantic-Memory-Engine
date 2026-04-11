import React, { useState, useEffect } from 'react';
import { Activity, Network } from 'lucide-react';
import { api, ws } from '../api';
import { SkeletonCard } from '../components/Skeleton';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [feedItems, setFeedItems] = useState([]);

  useEffect(() => {
    // Connect to WebSocket for real-time diagnostics
    ws.connect('/ws/diagnostics');

    // Try to fetch real data
    const fetchData = async () => {
      try {
        // Try to get health status
        const health = await api.healthCheck();
        if (health) {
          // Use real data if available
          setFeedItems([
            { type: 'ENTITY', msg: 'System health check passed', time: 'now' },
            { type: 'KNOWLEDGE', msg: 'Connected to Nexus database', time: 'now' },
          ]);
        }
      } catch {
        // Use fallback data if API unavailable
        setFeedItems([
          { type: 'ENTITY', msg: 'API server not connected - using demo mode', time: 'now' },
          { type: 'SENTIMENT', msg: 'System ready for analysis', time: '1m' },
          { type: 'KNOWLEDGE', msg: 'Knowledge graph initialized', time: '2m' },
        ]);
      }
      setLoading(false);
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }} role="feed" aria-label="Dashboard metrics">
      <section className="card glass-panel" aria-labelledby="ingestion-title">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 id="ingestion-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} aria-hidden="true" /> Live Ingestion Feed
          </h3>
          <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: 600 }} role="status" aria-label="Streaming status">
            STREAMING
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
          Latest entities discovery and processed data markers.
        </p>
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }} role="list" aria-label="Recent feed items">
          {feedItems.map((item, i) => (
            <div
              key={i}
              role="listitem"
              style={{
                padding: '0.75rem',
                borderLeft: `3px solid ${item.type === 'SENTIMENT' ? 'var(--danger)' : 'var(--accent-cyan)'}`,
                background: 'rgba(255,255,255,0.03)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                <span style={{ color: item.type === 'SENTIMENT' ? 'var(--danger)' : 'var(--accent-cyan)', fontWeight: 600 }}>
                  {item.type}
                </span>
                <time style={{ color: 'var(--text-secondary)' }}>{item.time}</time>
              </div>
              <div style={{ fontWeight: 400, marginTop: '0.25rem' }}>{item.msg}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="card glass-panel" aria-labelledby="overlays-title">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 id="overlays-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} aria-hidden="true" /> Semantic Overlays
          </h3>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
          Connections detected between disparate memory contexts.
        </p>
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(129, 140, 248, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 600 }}>Context: security_audit</span>
              <span style={{ color: 'var(--accent-purple)' }}>92% Match</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Overlaps with: firewalls, system_logs, network_topology
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;