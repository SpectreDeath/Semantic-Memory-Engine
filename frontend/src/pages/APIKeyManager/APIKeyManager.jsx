import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { api } from '../../api';

const APIKeyManager = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newKey, setNewKey] = useState({ name: '', api_key: '', provider: 'openai', expiry_days: 90, notes: '' });

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const response = await api.listAPIKeys();
      setKeys(response.keys || []);
    } catch {
      setKeys([
        { id: 'key_demo_1', name: 'OpenAI Production', provider: 'openai', expiry: '2026-06-01', last_used: '2026-04-17', notes: 'Main production key' },
        { id: 'key_demo_2', name: 'Anthropic Dev', provider: 'anthropic', expiry: '2026-05-15', last_used: '2026-04-16', notes: 'Development testing' },
      ]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchKeys(); // eslint-disable-line react-hooks/set-state-in-effect
  }, []);

  const addKey = async () => {
    if (!newKey.name || !newKey.api_key) return;
    try {
      await api.addAPIKey(newKey);
      setNewKey({ name: '', api_key: '', provider: 'openai', expiry_days: 90, notes: '' });
      setShowAdd(false);
      fetchKeys();
    } catch {
      alert('Failed to add key');
    }
  };

  const deleteKey = async (keyId) => {
    if (!confirm('Delete this API key?')) return;
    try {
      await api.deleteAPIKey(keyId);
      fetchKeys();
    } catch {
      setKeys(keys.filter(k => k.id !== keyId));
    }
  };

  const getProviderColor = (provider) => {
    const colors = { openai: '#10a37f', anthropic: '#d97757', custom: '#6366f1', huggingface: '#ff9f1c' };
    return colors[provider] || '#6b7280';
  };

  const isExpiringSoon = (expiry) => {
    if (!expiry) return false;
    const days = (new Date(expiry) - new Date()) / (1000 * 60 * 60 * 24);
    return days < 7;
  };

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Key size={24} />
            API Keys
          </h1>
          <p style={{ color: '#9ca3af', marginTop: '0.25rem' }}>Manage external API credentials</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} style={primaryButtonStyle}>
          <Plus size={18} />
          Add Key
        </button>
      </div>

      {showAdd && (
        <div style={modalStyle}>
          <h3 style={{ marginBottom: '1rem' }}>Add New API Key</h3>
          <input
            placeholder="Key Name"
            value={newKey.name}
            onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
            style={inputStyle}
          />
          <input
            type="password"
            placeholder="API Key"
            value={newKey.api_key}
            onChange={(e) => setNewKey({ ...newKey, api_key: e.target.value })}
            style={inputStyle}
          />
          <select
            value={newKey.provider}
            onChange={(e) => setNewKey({ ...newKey, provider: e.target.value })}
            style={inputStyle}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="huggingface">Hugging Face</option>
            <option value="custom">Custom</option>
          </select>
          <input
            type="number"
            placeholder="Expiry (days)"
            value={newKey.expiry_days}
            onChange={(e) => setNewKey({ ...newKey, expiry_days: parseInt(e.target.value) })}
            style={inputStyle}
          />
          <input
            placeholder="Notes"
            value={newKey.notes}
            onChange={(e) => setNewKey({ ...newKey, notes: e.target.value })}
            style={inputStyle}
          />
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
            <button onClick={addKey} style={primaryButtonStyle}>Save</button>
            <button onClick={() => setShowAdd(false)} style={secondaryButtonStyle}>Cancel</button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>Loading...</div>
        ) : keys.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>No API keys configured</div>
        ) : (
          keys.map(key => (
            <div key={key.id} style={keyCardStyle}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '0.5rem', background: getProviderColor(key.provider), display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>
                  {key.provider.slice(0, 2).toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500' }}>{key.name}</div>
                  <div style={{ fontSize: '0.875rem', color: '#9ca3af' }}>{key.provider} • Last used: {key.last_used || 'never'}</div>
                </div>
                {key.expiry && isExpiringSoon(key.expiry) && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#f59e0b', fontSize: '0.875rem' }}>
                    <AlertTriangle size={16} />
                    Expiring
                  </div>
                )}
                <button onClick={() => deleteKey(key.id)} style={iconButtonStyle}>
                  <Trash2 size={18} />
                </button>
              </div>
              {key.notes && <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#9ca3af' }}>{key.notes}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
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

const secondaryButtonStyle = {
  ...primaryButtonStyle,
  background: '#374151',
};

const inputStyle = {
  width: '100%',
  padding: '0.75rem',
  marginBottom: '0.5rem',
  borderRadius: '0.5rem',
  background: '#1f2937',
  color: '#fff',
  border: '1px solid #374151',
};

const modalStyle = {
  padding: '1.5rem',
  background: '#111827',
  borderRadius: '0.75rem',
  marginBottom: '1.5rem',
  border: '1px solid #374151',
};

const keyCardStyle = {
  padding: '1rem',
  background: '#1f2937',
  borderRadius: '0.75rem',
  border: '1px solid #374151',
};

const iconButtonStyle = {
  padding: '0.5rem',
  borderRadius: '0.375rem',
  background: 'transparent',
  color: '#9ca3af',
  border: 'none',
  cursor: 'pointer',
};

export default APIKeyManager;