import { useEffect, useCallback } from 'react';

/**
 * Keyboard Shortcuts Hook
 * Registers global keyboard shortcuts for power users
 */
const useKeyboardShortcuts = (shortcuts = {}, enabled = true) => {
  const handleKeyDown = useCallback((event) => {
    if (!enabled) return;

    const { key, metaKey, ctrlKey, shiftKey, altKey } = event;
    const modKey = metaKey || ctrlKey;

    // Check each shortcut
    Object.entries(shortcuts).forEach(([shortcut, handler]) => {
      let isMatch = false;

      // Parse shortcut string (e.g., "mod+k", "shift+?")
      const parts = shortcut.toLowerCase().split('+');
      
      const shortcutMod = parts.includes('mod') || parts.includes('ctrl');
      const shortcutShift = parts.includes('shift');
      const shortcutAlt = parts.includes('alt');
      const shortcutKey = parts.find(p => 
        !['mod', 'ctrl', 'shift', 'alt'].includes(p)
      );

      // Check modifier keys
      const modMatch = shortcutMod ? modKey : !modKey;
      const shiftMatch = shortcutShift ? shiftKey : !shiftKey;
      const altMatch = shortcutAlt ? altKey : !altKey;

      // Check main key
      if (shortcutKey) {
        if (shortcutKey === '?' && key === '?') {
          isMatch = modKey && shiftKey;
        } else if (shortcutKey === 'space' && key === ' ') {
          isMatch = true;
        } else if (shortcutKey === 'escape' && key === 'Escape') {
          isMatch = true;
        } else if (shortcutKey === key.toLowerCase()) {
          isMatch = true;
        }
      }

      if (isMatch && modMatch && shiftMatch && altMatch) {
        event.preventDefault();
        handler(event);
      }
    });
  }, [shortcuts, enabled]);

  useEffect(() => {
    if (enabled) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, enabled]);
};

// Default shortcuts configuration
export const DEFAULT_SHORTCUTS = {
  'mod+k': 'openSearch',      // Cmd+K - Open global search
  'mod+/': 'focusSearch',     // Cmd+/ - Focus search
  'mod+1': 'goToTab1',       // Cmd+1 - Dashboard
  'mod+2': 'goToTab2',       // Cmd+2 - Brain
  'mod+3': 'goToTab3',       // Cmd+3 - Intelligences
  'mod+4': 'goToTab4',       // Cmd+4 - Tool Lab
  'mod+5': 'goToTab5',       // Cmd+5 - Harvester
  'mod+6': 'goToTab6',       // Cmd+6 - Connections
  'mod+b': 'toggleSidebar',   // Cmd+B - Toggle sidebar
  'mod+j': 'nextTab',         // Cmd+J - Next tab
  'mod+g': 'prevTab',         // Cmd+G - Previous tab
  '?': 'showHelp',           // ? - Show shortcuts help
  'escape': 'closeModal',     // Escape - Close modal
};

// Tab mapping
export const TAB_SHORTCUTS = {
  1: 'dashboard',
  2: 'brain',
  3: 'reports',
  4: 'lab',
  5: 'harvester',
  6: 'connections',
};

export default useKeyboardShortcuts;
