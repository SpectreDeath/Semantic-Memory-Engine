import React, { useState } from 'react';

const HarvesterPanel = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [options, setOptions] = useState({ js_render: false, deep_crawl: false });
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);

  // URL validation
  const validateUrl = (value) => {
    try {
      new URL(value);
      setValidationError(null);
      return true;
    } catch {
      setValidationError('Please enter a valid URL (e.g., https://example.com)');
      return false;
    }
  };

  const handleUrlChange = (e) => {
    const value = e.target.value;
    setUrl(value);
    if (value) validateUrl(value);
    else setValidationError(null);
  };

  const handleIngest = async () => {
    if (!validateUrl(url)) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/api/v1/ingestion/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, ...options }),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error('Ingestion failed:', err);
      setError('Failed to connect to Harvester engine. Make sure the API server is running.');
    }
    setLoading(false);
  };

  return (
    <section className="card glass-panel">
      <h3>The Harvester: Digital Ingestion</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        Scrape web content and convert to semantic atomic facts.
      </p>
      
      <div style={{ marginTop: '1.5rem' }}>
        <input 
          type="text"
          className="glass-panel"
          placeholder="Enter target URL (e.g., https://en.wikipedia.org/wiki/Sovereignty)..."
          value={url}
          onChange={handleUrlChange}
          style={{ 
            width: '100%', 
            padding: '1rem', 
            background: 'rgba(0,0,0,0.2)', 
            border: validationError ? '1px solid var(--danger)' : '1px solid var(--glass-border)', 
            borderRadius: '8px', 
            color: 'white', 
            outline: 'none',
            marginBottom: '0.5rem',
          }}
        />
        
        {validationError && (
          <div style={{ color: 'var(--danger)', fontSize: '0.8rem', marginBottom: '1rem' }}>
            {validationError}
          </div>
        )}
        
        <div style={{ display: 'flex', gap: '2rem', marginTop: '1rem', fontSize: '0.85rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={options.js_render} 
              onChange={e => setOptions({...options, js_render: e.target.checked})} 
            />
            JavaScript Rendering
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={options.deep_crawl} 
              onChange={e => setOptions({...options, deep_crawl: e.target.checked})} 
            />
            Recursive Deep Crawl
          </label>
        </div>

        <button 
          disabled={loading || !url || !!validationError}
          onClick={handleIngest}
          className="glass-panel" 
          style={{ 
            marginTop: '1.5rem', 
            padding: '0.75rem 2rem', 
            background: loading ? 'var(--glass-border)' : 'var(--accent-purple)', 
            color: 'white', 
            fontWeight: '600', 
            border: 'none', 
            borderRadius: '8px', 
            cursor: loading || !url ? 'not-allowed' : 'pointer', 
            opacity: (loading || !url) ? 0.5 : 1 
          }}
        >
          {loading ? 'Ingesting...' : 'Start Ingestion'}
        </button>

        {error && (
          <div style={{ marginTop: '1rem', color: 'var(--danger)', fontSize: '0.9rem' }}>
            {error}
          </div>
        )}

        {result && (
          <div style={{ marginTop: '2rem', padding: '1.5rem', border: '1px solid var(--glass-border)', borderRadius: '8px', background: 'rgba(255,255,255,0.02)' }}>
             <h4 style={{ marginBottom: '1rem', color: 'var(--accent-purple)' }}>Capture Report</h4>
             {result.error ? (
               <p style={{ color: 'var(--danger)' }}>{result.error}</p>
             ) : (
               <div style={{ fontSize: '0.8rem' }}>
                  <p><strong>URL:</strong> {result.url}</p>
                  <p><strong>Word Count:</strong> {result.metadata?.word_count || 0}</p>
                  <p><strong>Quality Score:</strong> {result.quality_score}/100</p>
                  <div style={{ marginTop: '1rem', maxHeight: '200px', overflowY: 'auto', padding: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>{result.markdown?.substring(0, 1000)}...</pre>
                  </div>
               </div>
             )}
          </div>
        )}
      </div>
    </section>
  );
};

export default HarvesterPanel;