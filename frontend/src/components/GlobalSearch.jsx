import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, Command, FileText, Brain, Settings, Globe, Database } from 'lucide-react';
import { api } from '../api';

/**
 * Global Search Component (Cmd+K)
 * Provides quick access to search across tools, entities, and history
 */
const GlobalSearch = ({ isOpen, onClose, onNavigate }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState([]);
  const inputRef = useRef(null);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Reset state when closing
  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Search handler
  const handleSearch = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Search across multiple endpoints in parallel
      const [searchResult, toolsResult] = await Promise.allSettled([
        api.search(searchQuery, 5),
        api.listTools(),
      ]);

      const searchResults = searchResult.status === 'fulfilled' ? searchResult.value : { results: [] };
      const toolsResults = toolsResult.status === 'fulfilled' ? toolsResult.value : { registry: [] };

      // Build results array
      const formattedResults = [
        // Search results
        ...(searchResults.results || []).map((item, idx) => ({
          id: `search-${idx}`,
          type: 'search',
          title: item.title || item.concept || 'Result',
          subtitle: item.description || 'Search result',
          icon: Search,
        })),
        // Tool matches
        ...((toolsResults.registry || []).filter(tool => 
          tool.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
        ).slice(0, 5).map((tool, idx) => ({
          id: `tool-${idx}`,
          type: 'tool',
          title: tool.name,
          subtitle: tool.description,
          icon: Settings,
        }))),
      ];

      setResults(formattedResults);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, handleSearch]);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          handleSelectResult(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  };

  const handleSelectResult = (result) => {
    // Save to recent searches
    const newRecent = [
      { query, timestamp: Date.now() },
      ...recentSearches.filter(r => r.query !== query).slice(0, 4)
    ];
    setRecentSearches(newRecent);
    localStorage.setItem('recentSearches', JSON.stringify(newRecent));

    // Navigate based on result type
    if (onNavigate) {
      onNavigate(result);
    }
    
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0, 0, 0, 0.7)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '600px',
          maxHeight: '70vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '1rem 1.5rem',
            borderBottom: '1px solid var(--glass-border)',
          }}
        >
          <Search size={20} color="var(--text-secondary)" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search tools, entities, history..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{
              flex: 1,
              marginLeft: '1rem',
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '1rem',
            }}
          />
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              padding: '0.25rem 0.5rem',
              background: 'var(--glass-border)',
              borderRadius: '4px',
              fontSize: '0.75rem',
              color: 'var(--text-secondary)',
            }}
          >
            <Command size={12} />
            <span>K</span>
          </div>
          <button
            onClick={onClose}
            style={{
              marginLeft: '0.5rem',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '0.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={20} color="var(--text-secondary)" />
          </button>
        </div>

        {/* Results */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '0.5rem' }}>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              Searching...
            </div>
          ) : query && results.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No results found for "{query}"
            </div>
          ) : query ? (
            <div>
              {results.map((result, index) => {
                const Icon = result.icon || Search;
                return (
                  <div
                    key={result.id}
                    onClick={() => handleSelectResult(result)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      background: index === selectedIndex ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                      transition: 'background 0.1s',
                    }}
                  >
                    <Icon size={18} color={index === selectedIndex ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                        {result.title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {result.subtitle}
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        background: 'var(--glass-border)',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {result.type}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Recent searches */
            <div>
              <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                Recent Searches
              </div>
              {recentSearches.length === 0 ? (
                <div style={{ padding: '1rem', color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'center' }}>
                  No recent searches
                </div>
              ) : (
                recentSearches.map((item, index) => (
                  <div
                    key={index}
                    onClick={() => setQuery(item.query)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      padding: '0.75rem 1rem',
                      cursor: 'pointer',
                      borderRadius: '8px',
                    }}
                  >
                    <Search size={16} color="var(--text-secondary)" />
                    <span style={{ color: 'var(--text-primary)' }}>{item.query}</span>
                  </div>
                ))
              )}

              {/* Quick links */}
              <div style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginTop: '1rem' }}>
                Quick Access
              </div>
              {[
                { icon: Brain, label: 'The Brain', route: 'brain' },
                { icon: Globe, label: 'Harvester', route: 'harvester' },
                { icon: Database, label: 'Connections', route: 'connections' },
                { icon: FileText, label: 'Intelligences', route: 'reports' },
              ].map((item) => (
                <div
                  key={item.route}
                  onClick={() => {
                    if (onNavigate) onNavigate({ type: 'route', route: item.route });
                    onClose();
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '0.75rem 1rem',
                    cursor: 'pointer',
                    borderRadius: '8px',
                  }}
                >
                  <item.icon size={16} color="var(--text-secondary)" />
                  <span style={{ color: 'var(--text-primary)' }}>{item.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.75rem 1rem',
            borderTop: '1px solid var(--glass-border)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
          }}
        >
          <div style={{ display: 'flex', gap: '1rem' }}>
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>Esc Close</span>
          </div>
          <span>Press K to open</span>
        </div>
      </div>
    </div>
  );
};

export default GlobalSearch;
