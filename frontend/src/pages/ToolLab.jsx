import React, { useState } from 'react';

const ToolLab = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalysis = async (type) => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const endpoint =
        type === 'graph'
          ? '/api/v1/analysis/graph'
          : type === 'report'
            ? '/api/v1/analysis/report'
            : '/api/v1/search';

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, context_id: 'tool_lab' }),
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Connection to API failed. Ensure the API server is running.');
      setResult({
        error: 'API server unavailable. Run `python -m src.api.main` to start the server.',
      });
    }
    setAnalyzing(false);
  };

  return (
    <section className="card glass-panel">
      <h3>Interactive Tool Lab</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        Test laboratory tools directly against raw text input.
      </p>

      <div style={{ marginTop: '1.5rem' }}>
        <textarea
          className="glass-panel"
          placeholder="Insert raw text for analysis..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{
            width: '100%',
            height: '150px',
            background: 'rgba(0,0,0,0.2)',
            padding: '1rem',
            border: '1px solid var(--glass-border)',
            borderRadius: '8px',
            color: 'white',
            outline: 'none',
            fontFamily: 'inherit',
            resize: 'vertical',
          }}
        />
        
        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', flexWrap: 'wrap' }}>
          <button
            disabled={analyzing || !text}
            onClick={() => handleAnalysis('graph')}
            className="glass-panel"
            style={{
              padding: '0.75rem 1.5rem',
              background: analyzing ? 'var(--glass-border)' : 'var(--accent-cyan)',
              color: analyzing ? 'var(--text-secondary)' : 'var(--bg-dark)',
              fontWeight: '600',
              border: 'none',
              borderRadius: '8px',
              cursor: analyzing || !text ? 'not-allowed' : 'pointer',
              opacity: analyzing || !text ? 0.5 : 1,
            }}
          >
            {analyzing ? 'Processing...' : 'Generate Graph'}
          </button>
          <button
            disabled={analyzing || !text}
            onClick={() => handleAnalysis('report')}
            className="glass-panel"
            style={{
              padding: '0.75rem 1.5rem',
              color: 'white',
              borderRadius: '8px',
              cursor: analyzing || !text ? 'not-allowed' : 'pointer',
              opacity: analyzing || !text ? 0.5 : 1,
              border: '1px solid var(--glass-border)',
              background: 'transparent',
            }}
          >
            Intelligence Briefing
          </button>
        </div>

        {result && (
          <div
            style={{
              marginTop: '2rem',
              padding: '1.5rem',
              border: '1px solid var(--glass-border)',
              borderRadius: '8px',
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <h4 style={{ marginBottom: '1rem', color: 'var(--accent-cyan)' }}>
              Analysis Results
            </h4>
            <pre
              style={{
                fontSize: '0.8rem',
                overflowX: 'auto',
                color: 'var(--text-secondary)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </section>
  );
};

export default ToolLab;