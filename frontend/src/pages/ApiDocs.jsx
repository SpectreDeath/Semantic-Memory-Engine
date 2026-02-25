import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { BookOpen, Search, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { api } from '../api';
import ErrorBoundary from '../components/ErrorBoundary';
import { SkeletonCard, SkeletonList } from '../components/Skeleton';

/**
 * API Documentation Page
 * Displays all available MCP tools with descriptions and parameters
 */
const ApiDocs = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedTool, setExpandedTool] = useState(null);
  const [copiedTool, setCopiedTool] = useState(null);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    setLoading(true);
    try {
      const data = await api.listTools();
      setTools(data.registry || []);
      setError(null);
    } catch (err) {
      setError('Failed to load tools. Make sure the API server is running.');
      console.error('Error loading tools:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTools = tools.filter(tool =>
    tool.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleTool = (toolName) => {
    setExpandedTool(prev => prev === toolName ? null : toolName);
  };

  const copyToClipboard = async (text, toolName) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedTool(toolName);
      setTimeout(() => setCopiedTool(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      analysis: '#38bdf8',
      forensic: '#818cf8',
      memory: '#10b981',
      search: '#f59e0b',
      utility: '#ef4444',
    };
    return colors[category?.toLowerCase()] || '#94a3b8';
  };

  if (loading) {
    return (
      <div>
        <SkeletonCard />
        <SkeletonList items={5} itemHeight="80px" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error}</p>
        <button onClick={loadTools} className="glass-panel" style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <ErrorBoundary fallbackTitle="Error in API Docs" fallbackMessage="Something went wrong loading the API documentation.">
      <div>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <BookOpen size={28} color="var(--accent-cyan)" />
            API Documentation
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Available MCP tools and their parameters. Total: {tools.length} tools
          </p>
        </div>

        {/* Search */}
        <div className="glass-panel" style={{ padding: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Search size={20} color="var(--text-secondary)" />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: '1rem',
              }}
            />
          </div>
        </div>

        {/* Tools List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredTools.length === 0 ? (
            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No tools found matching "{searchQuery}"
            </div>
          ) : (
            filteredTools.map((tool, index) => (
              <div
                key={tool.name || index}
                className="glass-panel"
                style={{ overflow: 'hidden' }}
              >
                {/* Tool Header */}
                <div
                  onClick={() => toggleTool(tool.name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '1rem',
                    cursor: 'pointer',
                    transition: 'background 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    {expandedTool === tool.name ? (
                      <ChevronDown size={20} color="var(--text-secondary)" />
                    ) : (
                      <ChevronRight size={20} color="var(--text-secondary)" />
                    )}
                    <div>
                      <h3 style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {tool.name || 'Unnamed Tool'}
                      </h3>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                        {tool.description || 'No description available'}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {tool.category && (
                      <span
                        style={{
                          padding: '0.25rem 0.75rem',
                          borderRadius: '12px',
                          fontSize: '0.75rem',
                          background: `${getCategoryColor(tool.category)}20`,
                          color: getCategoryColor(tool.category),
                          border: `1px solid ${getCategoryColor(tool.category)}40`,
                        }}
                      >
                        {tool.category}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Tool Details */}
                {expandedTool === tool.name && (
                  <div
                    style={{
                      padding: '1rem',
                      paddingTop: 0,
                      borderTop: '1px solid var(--glass-border)',
                    }}
                  >
                    {/* Parameters */}
                    {tool.parameters && Object.keys(tool.parameters).length > 0 ? (
                      <div style={{ marginBottom: '1rem' }}>
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                          Parameters
                        </h4>
                        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '1rem' }}>
                          <code style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                            {JSON.stringify(tool.parameters, null, 2)}
                          </code>
                        </div>
                      </div>
                    ) : (
                      <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        No parameters required
                      </div>
                    )}

                    {/* Copy Example */}
                    <div>
                      <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                        Usage Example
                      </h4>
                      <div
                        style={{
                          position: 'relative',
                          background: 'rgba(0,0,0,0.3)',
                          borderRadius: '8px',
                          padding: '1rem',
                          fontFamily: 'monospace',
                          fontSize: '0.8rem',
                        }}
                      >
                        <code style={{ color: 'var(--text-secondary)' }}>
                          {`// MCP Tool Call\nawait mcp.call("${tool.name}", {\n  // parameters here\n});`}
                        </code>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copyToClipboard(tool.name, tool.name);
                          }}
                          style={{
                            position: 'absolute',
                            top: '0.5rem',
                            right: '0.5rem',
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            padding: '0.25rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                          title="Copy tool name"
                        >
                          {copiedTool === tool.name ? (
                            <Check size={16} color="var(--success)" />
                          ) : (
                            <Copy size={16} color="var(--text-secondary)" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default ApiDocs;
