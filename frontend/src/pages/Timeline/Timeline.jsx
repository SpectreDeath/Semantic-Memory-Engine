import React, { useState, useEffect } from 'react';
import { Clock, Filter, Download, RefreshCw } from 'lucide-react';
import { api } from '../../api';

const Timeline = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [dateRange, setDateRange] = useState('24h');

  const eventTypes = [
    { id: 'all', label: 'All Events' },
    { id: 'ingestion', label: 'Ingestion' },
    { id: 'analysis', label: 'Analysis' },
    { id: 'threat', label: 'Threats' },
    { id: 'system', label: 'System' },
    { id: 'webhook', label: 'Webhooks' },
  ];

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await api.getTimeline({ filter, dateRange });
      setEvents(response.events || []);
    } catch {
      // Demo data
      setEvents([
        { id: 1, type: 'ingestion', message: 'URL ingested: example.com', timestamp: new Date().toISOString(), severity: 'info' },
        { id: 2, type: 'analysis', message: 'Analysis complete: 42 facts extracted', timestamp: new Date(Date.now() - 60000).toISOString(), severity: 'success' },
        { id: 3, type: 'threat', message: 'Suspicious pattern detected in source A', timestamp: new Date(Date.now() - 120000).toISOString(), severity: 'warning' },
        { id: 4, type: 'system', message: 'Database connection pool refreshed', timestamp: new Date(Date.now() - 180000).toISOString(), severity: 'info' },
        { id: 5, type: 'webhook', message: 'Webhook triggered: analysis_complete', timestamp: new Date(Date.now() - 240000).toISOString(), severity: 'info' },
        { id: 6, type: 'ingestion', message: 'Cloud storage sync completed', timestamp: new Date(Date.now() - 300000).toISOString(), severity: 'success' },
        { id: 7, type: 'analysis', message: 'Semantic embedding updated', timestamp: new Date(Date.now() - 360000).toISOString(), severity: 'info' },
      ]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchEvents(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [filter, dateRange]); // eslint-disable-line react-hooks/exhaustive-deps

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      case 'success': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getTypeIcon = (type) => {
    const icons = { ingestion: '📥', analysis: '🔍', threat: '⚠️', system: '⚙️', webhook: '🔗' };
    return icons[type] || '📌';
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={24} />
            Timeline
          </h1>
          <p style={{ color: '#9ca3af', marginTop: '0.25rem' }}>Event history and forensic timeline</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={fetchEvents} style={iconButtonStyle}>
            <RefreshCw size={18} />
          </button>
          <button style={iconButtonStyle}>
            <Download size={18} />
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '0.25rem', background: '#1f2937', padding: '0.25rem', borderRadius: '0.5rem' }}>
          {eventTypes.map(type => (
            <button
              key={type.id}
              onClick={() => setFilter(type.id)}
              style={{
                ...tabStyle,
                background: filter === type.id ? '#374151' : 'transparent',
                color: filter === type.id ? '#fff' : '#9ca3af',
              }}
            >
              {type.label}
            </button>
          ))}
        </div>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          style={{ padding: '0.5rem', borderRadius: '0.5rem', background: '#1f2937', color: '#fff', border: '1px solid #374151' }}
        >
          <option value="1h">Last hour</option>
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>Loading events...</div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>No events found</div>
        ) : (
          events.map(event => (
            <div key={event.id} style={eventCardStyle}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ fontSize: '1.25rem' }}>{getTypeIcon(event.type)}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500' }}>{event.message}</div>
                  <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>{formatTime(event.timestamp)}</div>
                </div>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getSeverityColor(event.severity) }} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const iconButtonStyle = {
  padding: '0.5rem',
  borderRadius: '0.5rem',
  background: '#1f2937',
  color: '#fff',
  border: '1px solid #374151',
  cursor: 'pointer',
};

const tabStyle = {
  padding: '0.5rem 1rem',
  borderRadius: '0.375rem',
  border: 'none',
  cursor: 'pointer',
  fontSize: '0.875rem',
  transition: 'all 0.2s',
};

const eventCardStyle = {
  padding: '1rem',
  background: '#1f2937',
  borderRadius: '0.75rem',
  border: '1px solid #374151',
};

export default Timeline;