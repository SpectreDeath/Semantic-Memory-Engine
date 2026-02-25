import React, { useState, useEffect, useCallback } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  FileText,
  FlaskConical,
  Settings,
  Activity,
  Cpu,
  Network,
  Globe,
  Unplug,
  Database,
  Sun,
  Moon,
  Search,
  Command,
} from 'lucide-react';

import { api, ws } from './api';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import GlobalSearch from './components/GlobalSearch';
import ThemeToggle from './components/ThemeToggle';
import Breadcrumbs, { generateBreadcrumbs } from './components/Breadcrumbs';
import { SkeletonCard, SkeletonList } from './components/Skeleton';
import { DEFAULT_SHORTCUTS, TAB_SHORTCUTS } from './hooks/useKeyboardShortcuts';
import KnowledgeBrain from './components/KnowledgeBrain';
import ApiDocs from './pages/ApiDocs';
import './index.css';

// ============================================================================
// PAGE COMPONENTS
// ============================================================================

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [feedItems, setFeedItems] = useState([]);
  const [metrics, setMetrics] = useState({ cpu: 0, memory: 0, latency: '0ms' });

  useEffect(() => {
    // Connect to WebSocket for real-time diagnostics
    ws.connect('/ws/diagnostics');
    
    const unsubMessage = ws.on('diagnostics', (data) => {
      setMetrics(data);
    });

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
      } catch (e) {
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

    return () => {
      unsubMessage?.();
    };
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
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
      <section className="card glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} /> Live Ingestion Feed
          </h3>
          <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: 600 }}>
            STREAMING
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
          Latest entities discovery and processed data markers.
        </p>
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {feedItems.map((item, i) => (
            <div
              key={i}
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
                <span style={{ color: 'var(--text-secondary)' }}>{item.time}</span>
              </div>
              <div style={{ fontWeight: 400, marginTop: '0.25rem' }}>{item.msg}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="card glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} /> Semantic Overlays
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

const Brain = () => (
  <section className="card glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
    <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
      <h3>Silicon Brain Explorer</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        Neural network of extracted concepts and relationships.
      </p>
    </div>
    <KnowledgeBrain />
  </section>
);

const Intelligences = () => {
  const [reports] = useState([
    { title: 'Summary: Jan 20', date: '2026-01-20' },
    { title: 'Briefing: Jan 18', date: '2026-01-18' },
    { title: 'Discovery: Jan 15', date: '2026-01-15' },
  ]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem' }}>
      <section className="card glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FileText size={24} color="var(--accent-cyan)" />
          <div>
            <h3>Executive Summary: Project Alpha</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
              Generated: Jan 20, 2026
            </span>
          </div>
        </div>
        <div style={{ marginTop: '1.5rem', lineHeight: 1.8 }}>
          <p>
            Overall sentiment is <strong>highly positive (0.82)</strong>.
            Key themes revolve around <strong>innovation</strong> and <strong>efficiency</strong>.
            The knowledge graph indicates a strong central connection between 'Machine Learning' and 'Infrastructure'...
          </p>
        </div>
        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.5rem' }}>
          {['NLP', 'Optimization', 'Security'].map((tag) => (
            <span
              key={tag}
              style={{
                background: 'var(--glass-border)',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '0.7rem',
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      </section>

      <aside className="glass-panel" style={{ padding: '1rem' }}>
        <h4 style={{ marginBottom: '1rem' }}>Archives</h4>
        {reports.map((report, i) => (
          <div key={i} className="sidebar-item" style={{ fontSize: '0.8rem' }}>
            {report.title}
          </div>
        ))}
      </aside>
    </div>
  );
};

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
    fetchStatus();
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

// ============================================================================
// MAIN LAYOUT COMPONENT
// ============================================================================

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDark, toggleTheme } = useTheme();
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [metrics, setMetrics] = useState({ cpu: 0, memory: 0, latency: '0ms' });
  const [searchOpen, setSearchOpen] = useState(false);

  // Tab to route mapping
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { id: 'brain', label: 'The Brain', icon: Network, path: '/brain' },
    { id: 'reports', label: 'Intelligences', icon: FileText, path: '/reports' },
    { id: 'lab', label: 'Tool Lab', icon: FlaskConical, path: '/lab' },
    { id: 'harvester', label: 'Harvester', icon: Globe, path: '/harvester' },
    { id: 'connections', label: 'Connections', icon: Unplug, path: '/connections' },
    { id: 'api-docs', label: 'API Docs', icon: BookOpen, path: '/api-docs' },
  ];

  // Sync tab with URL
  useEffect(() => {
    const path = location.pathname;
    const tab = tabs.find(t => t.path === path);
    if (tab) setActiveTab(tab.id);
  }, [location.pathname]);

  // WebSocket connection
  useEffect(() => {
    ws.connect('/ws/diagnostics');
    const unsub = ws.on('diagnostics', (data) => setMetrics(data));
    return () => unsub?.();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Cmd+K - Open search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
      }
      // Number keys for tab navigation
      if ((e.metaKey || e.ctrlKey) && e.key >= '1' && e.key <= '7') {
        e.preventDefault();
        const idx = parseInt(e.key) - 1;
        if (tabs[idx]) {
          navigate(tabs[idx].path);
        }
      }
      // Escape - Close search
      if (e.key === 'Escape') {
        setSearchOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate, tabs]);

  const handleSearchNavigate = (result) => {
    if (result.type === 'route' && result.route) {
      const tab = tabs.find(t => t.id === result.route);
      if (tab) navigate(tab.path);
    }
  };

  const currentTab = tabs.find(t => t.id === activeTab);
  const breadcrumbs = generateBreadcrumbs(location.pathname);

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel">
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <BrainCircuit size={28} /> SimpleMem
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', paddingLeft: '40px' }}>
            Laboratory v2.0
          </p>
        </div>

        <nav>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <div
                key={tab.id}
                className={`sidebar-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => navigate(tab.path)}
              >
                <Icon size={20} /> {tab.label}
              </div>
            );
          })}
        </nav>

        <div
          style={{
            marginTop: 'auto',
            paddingTop: '1rem',
            borderTop: '1px solid var(--glass-border)',
          }}
        >
          {/* Search Button */}
          <div
            className="sidebar-item"
            onClick={() => setSearchOpen(true)}
            style={{ marginBottom: '0.5rem' }}
          >
            <Search size={18} /> 
            <span style={{ flex: 1 }}>Search</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>⌘K</span>
          </div>

          {/* Theme Toggle */}
          <div
            className="sidebar-item"
            onClick={toggleTheme}
            style={{ marginBottom: '0.5rem' }}
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
            {isDark ? 'Light Mode' : 'Dark Mode'}
          </div>

          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <div className="status-indicator"></div> System Online
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header
          style={{
            marginBottom: '2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <Breadcrumbs items={breadcrumbs} onNavigate={(item) => navigate(item.path)} />
            <h1 style={{ fontSize: '1.8rem' }}>
              {currentTab?.label || 'Dashboard'}
            </h1>
            <p style={{ color: 'var(--text-secondary)' }}>
              Monitoring laboratory operations in real-time.
            </p>
          </div>
          <div
            className="glass-panel"
            style={{ padding: '0.75rem 1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Cpu size={12} /> CPU
              </div>
              <div style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{metrics.cpu}%</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Activity size={12} /> LATENCY
              </div>
              <div style={{ fontWeight: 600, color: 'var(--accent-purple)' }}>{metrics.latency}</div>
            </div>
          </div>
        </header>

        {/* Page Content with Error Boundary */}
        <ErrorBoundary fallbackTitle="Page Error" fallbackMessage="This section encountered an error. Please try again.">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/brain" element={<Brain />} />
            <Route path="/reports" element={<Intelligences />} />
            <Route path="/lab" element={<ToolLab />} />
            <Route path="/harvester" element={<HarvesterPanel />} />
            <Route path="/connections" element={<ConnectionsManager />} />
            <Route path="/api-docs" element={<ApiDocs />} />
          </Routes>
        </ErrorBoundary>
      </main>

      {/* Global Search Modal */}
      <GlobalSearch 
        isOpen={searchOpen} 
        onClose={() => setSearchOpen(false)}
        onNavigate={handleSearchNavigate}
      />
    </div>
  );
};

// ============================================================================
// APP ENTRY POINT
// ============================================================================

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Layout />
      </Router>
    </ThemeProvider>
  );
}

export default App;
