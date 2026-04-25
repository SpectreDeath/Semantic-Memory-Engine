import React, { useState, useEffect } from 'react';
import { Search, Download, User, Activity } from 'lucide-react';
import { api } from '../../api';

const AuditLog = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');
  const [dateRange, setDateRange] = useState('24h');

  const levels = [
    { id: 'all', label: 'All Levels' },
    { id: 'info', label: 'Info', color: '#3b82f6' },
    { id: 'warning', label: 'Warning', color: '#f59e0b' },
    { id: 'error', label: 'Error', color: '#ef4444' },
    { id: 'critical', label: 'Critical', color: '#dc2626' },
  ];

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const response = await api.getAuditLogs({ search, level: levelFilter, dateRange });
      setLogs(response.logs || []);
    } catch {
      // Demo data
      setLogs([
        { id: 1, timestamp: '2026-04-18T08:00:00Z', level: 'info', action: 'user_login', user: 'admin', details: 'User logged in successfully' },
        { id: 2, timestamp: '2026-04-18T07:55:00Z', level: 'warning', action: 'api_key_expiring', user: 'system', details: 'API key "OpenAI Production" expires in 7 days' },
        { id: 3, timestamp: '2026-04-18T07:45:00Z', level: 'error', action: 'extension_load_failed', user: 'system', details: 'Failed to load ext_analysis_core: chromadb not found' },
        { id: 4, timestamp: '2026-04-18T07:30:00Z', level: 'info', action: 'data_ingested', user: 'harvester', details: 'Ingested 42 facts from https://example.com' },
        { id: 5, timestamp: '2026-04-18T07:15:00Z', level: 'info', action: 'webhook_triggered', user: 'system', details: 'Webhook "Slack Alert" triggered for event analysis_complete' },
        { id: 6, timestamp: '2026-04-18T06:00:00Z', level: 'critical', action: 'security_breach_attempt', user: 'unknown', details: 'Blocked suspicious login attempt from IP 192.168.1.100' },
        { id: 7, timestamp: '2026-04-18T05:30:00Z', level: 'info', action: 'job_scheduled', user: 'scheduler', details: 'Registered job "Daily cleanup" with schedule "0 2 * * *"' },
      ]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs(); // eslint-disable-line react-hooks/set-state-in-effect
  }, [search, levelFilter, dateRange]); // eslint-disable-line react-hooks/exhaustive-deps

  const getLevelColor = (level) => {
    const levelData = levels.find(l => l.id === level);
    return levelData?.color || '#6b7280';
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const exportLogs = () => {
    const csv = ['Timestamp,Level,Action,User,Details'];
    logs.forEach(log => {
      csv.push(`${log.timestamp},${log.level},${log.action},${log.user},"${log.details}"`);
    });
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const filteredLogs = logs.filter(log => {
    if (levelFilter !== 'all' && log.level !== levelFilter) return false;
    if (search && !log.details.toLowerCase().includes(search.toLowerCase()) && !log.action.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={24} />
            Audit Log
          </h1>
          <p style={{ color: '#9ca3af', marginTop: '0.25rem' }}>Searchable audit trail of all system actions</p>
        </div>
        <button onClick={exportLogs} style={primaryButtonStyle}>
          <Download size={18} />
          Export CSV
        </button>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
          <input
            placeholder="Search logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ ...inputStyle, paddingLeft: '2.5rem' }}
          />
        </div>
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          style={{ ...inputStyle, width: 'auto' }}
        >
          {levels.map(level => (
            <option key={level.id} value={level.id}>{level.label}</option>
          ))}
        </select>
        <select
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          style={{ ...inputStyle, width: 'auto' }}
        >
          <option value="1h">Last hour</option>
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>Loading logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>No logs found</div>
        ) : (
          filteredLogs.map(log => (
            <div key={log.id} style={logCardStyle}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getLevelColor(log.level) }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{formatTime(log.timestamp)}</span>
                    <span style={badgeStyle(log.level)}>{log.level}</span>
                    <span style={{ fontWeight: '500' }}>{log.action}</span>
                  </div>
                  <div style={{ marginTop: '0.25rem', color: '#d1d5db' }}>{log.details}</div>
                  <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <User size={12} /> {log.user}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const inputStyle = {
  padding: '0.75rem 1rem',
  borderRadius: '0.5rem',
  background: '#1f2937',
  color: '#fff',
  border: '1px solid #374151',
  fontSize: '0.875rem',
};

const primaryButtonStyle = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
  padding: '0.5rem 1rem',
  borderRadius: '0.5rem',
  background: '#3b82f6',
  color: '#fff',
  border: 'none',
  cursor: 'pointer',
};

const logCardStyle = {
  padding: '1rem',
  background: '#1f2937',
  borderRadius: '0.5rem',
  border: '1px solid #374151',
};

const badgeStyle = (level) => ({
  padding: '0.125rem 0.5rem',
  borderRadius: '0.25rem',
  fontSize: '0.625rem',
  fontWeight: '600',
  textTransform: 'uppercase',
  background: level === 'error' ? '#7f1d1d' : level === 'warning' ? '#78350f' : level === 'critical' ? '#991b1b' : '#1e3a5f',
  color: '#fff',
});

export default AuditLog;