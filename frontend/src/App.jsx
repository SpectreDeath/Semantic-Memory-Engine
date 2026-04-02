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
  Activity,
  Cpu,
  Network,
  Globe,
  Unplug,
  Sun,
  Moon,
  Search,
  BookOpen,
} from 'lucide-react';

import { ws } from './api';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import GlobalSearch from './components/GlobalSearch';
import Breadcrumbs, { generateBreadcrumbs } from './components/Breadcrumbs';
import Dashboard from './pages/Dashboard';
import Brain from './pages/Brain';
import Intelligences from './pages/Intelligences';
import ToolLab from './pages/ToolLab';
import HarvesterPanel from './pages/HarvesterPanel';
import ConnectionsManager from './pages/ConnectionsManager';
import ApiDocs from './pages/ApiDocs';
import './index.css';

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
            Forensic MCP Gateway v3.0.1
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
