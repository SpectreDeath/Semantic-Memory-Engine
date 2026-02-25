import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

/**
 * Theme Toggle Component
 * Switches between dark and light themes
 */
const ThemeToggle = ({ showLabel = false }) => {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="glass-panel"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.5rem 1rem',
        background: 'transparent',
        border: '1px solid var(--glass-border)',
        borderRadius: '8px',
        cursor: 'pointer',
        color: 'var(--text-primary)',
        transition: 'all 0.2s ease',
        fontSize: '0.9rem',
      }}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      {isDark ? (
        <>
          <Sun size={18} />
          {showLabel && <span>Light</span>}
        </>
      ) : (
        <>
          <Moon size={18} />
          {showLabel && <span>Dark</span>}
        </>
      )}
    </button>
  );
};

export default ThemeToggle;
