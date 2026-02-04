"""
Ghost Trap Extension - Persistence Monitor

Monitors Governor task execution for potential self-replication events.
Hooks into task execution to detect calls to os.system, shutil.copy, or pickle.dump
in hidden directories.
"""

import os
import sys
import logging
import functools
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
from contextlib import contextmanager

# Configure logging for the ghost trap
logger = logging.getLogger('ghost_trap.persistence_monitor')
logger.setLevel(logging.INFO)

# Create file handler for ghost trap events
ghost_trap_handler = logging.FileHandler('ghost_trap_events.log')
ghost_trap_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ghost_trap_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(ghost_trap_handler)


class GhostTrapMonitor:
    """Monitors for potential self-replication events in task execution."""
    
    def __init__(self):
        self._original_functions: Dict[str, Callable] = {}
        self._is_monitoring = False
        self._hidden_directories: Set[str] = self._get_hidden_directories()
        self._thread_local = threading.local()
        
    def _get_hidden_directories(self) -> Set[str]:
        """Get common hidden directories where self-replication might occur."""
        hidden_dirs = set()
        
        # Common hidden directories on different platforms
        if sys.platform == 'win32':
            appdata = os.getenv('APPDATA', '')
            local_appdata = os.getenv('LOCALAPPDATA', '')
            if appdata:
                hidden_dirs.add(appdata.lower())
            if local_appdata:
                hidden_dirs.add(local_appdata.lower())
        else:
            # Unix-like systems
            home = os.path.expanduser('~')
            hidden_dirs.update([
                os.path.join(home, '.cache').lower(),
                os.path.join(home, '.config').lower(),
                os.path.join(home, '.local').lower(),
                '/tmp',
                '/var/tmp'
            ])
        
        return hidden_dirs
    
    def _is_hidden_directory(self, path: str) -> bool:
        """Check if a path is in a hidden directory."""
        if not path:
            return False
            
        path_lower = os.path.normpath(path).lower()
        
        # Check if path contains any of our hidden directories
        for hidden_dir in self._hidden_directories:
            if hidden_dir in path_lower:
                return True
        
        # Also check for dot-prefixed directories
        path_parts = Path(path).parts
        for part in path_parts:
            if part.startswith('.') and len(part) > 1:  # Exclude '.' and '..'
                return True
                
        return False
    
    def _log_ghost_event(self, function_name: str, args: tuple, kwargs: dict, 
                        target_path: Optional[str] = None):
        """Log a potential self-replication event."""
        event_details = {
            'function': function_name,
            'args': str(args),
            'kwargs': str(kwargs),
            'target_path': target_path,
            'hidden_directory': self._is_hidden_directory(target_path) if target_path else False,
            'thread_id': threading.get_ident()
        }
        
        message = (
            f"POTENTIAL SELF-REPLICATION EVENT - "
            f"Function: {function_name}, "
            f"Target: {target_path}, "
            f"Hidden: {event_details['hidden_directory']}, "
            f"Thread: {event_details['thread_id']}"
        )
        
        logger.warning(message)
        print(f"⚠️  GHOST TRAP ALERT: {message}")
    
    def _wrap_os_system(self, original_func: Callable) -> Callable:
        """Wrap os.system to monitor for suspicious commands."""
        @functools.wraps(original_func)
        def wrapper(command: str, *args, **kwargs):
            if self._is_monitoring:
                # Check if command might create files in hidden directories
                if any(hidden_dir in command.lower() for hidden_dir in self._hidden_directories):
                    self._log_ghost_event('os.system', (command,) + args, kwargs, command)
            
            return original_func(command, *args, **kwargs)
        return wrapper
    
    def _wrap_shutil_copy(self, original_func: Callable) -> Callable:
        """Wrap shutil.copy to monitor file copying operations."""
        @functools.wraps(original_func)
        def wrapper(src: str, dst: str, *args, **kwargs):
            if self._is_monitoring:
                if self._is_hidden_directory(dst):
                    self._log_ghost_event('shutil.copy', (src, dst) + args, kwargs, dst)
            
            return original_func(src, dst, *args, **kwargs)
        return wrapper
    
    def _wrap_pickle_dump(self, original_func: Callable) -> Callable:
        """Wrap pickle.dump to monitor serialization operations."""
        @functools.wraps(original_func)
        def wrapper(obj: Any, file: Any, *args, **kwargs):
            if self._is_monitoring:
                # Try to get the file path
                target_path = None
                if hasattr(file, 'name'):
                    target_path = file.name
                elif isinstance(file, str):
                    target_path = file
                
                if target_path and self._is_hidden_directory(target_path):
                    self._log_ghost_event('pickle.dump', (obj, file) + args, kwargs, target_path)
            
            return original_func(obj, file, *args, **kwargs)
        return wrapper
    
    def _wrap_pickle_dumps(self, original_func: Callable) -> Callable:
        """Wrap pickle.dumps to monitor serialization operations."""
        @functools.wraps(original_func)
        def wrapper(obj: Any, *args, **kwargs):
            if self._is_monitoring:
                # Check if this might be part of a larger operation
                # We can't easily detect the target path for dumps, but we can log the call
                self._log_ghost_event('pickle.dumps', (obj,) + args, kwargs)
            
            return original_func(obj, *args, **kwargs)
        return wrapper
    
    def start_monitoring(self):
        """Start monitoring for self-replication events."""
        if self._is_monitoring:
            return
            
        self._is_monitoring = True
        
        # Store original functions
        if hasattr(os, 'system') and 'os.system' not in self._original_functions:
            self._original_functions['os.system'] = os.system
            os.system = self._wrap_os_system(os.system)
        
        if hasattr(sys.modules.get('shutil'), 'copy') and 'shutil.copy' not in self._original_functions:
            import shutil
            self._original_functions['shutil.copy'] = shutil.copy
            shutil.copy = self._wrap_shutil_copy(shutil.copy)
        
        if hasattr(sys.modules.get('pickle'), 'dump') and 'pickle.dump' not in self._original_functions:
            import pickle
            self._original_functions['pickle.dump'] = pickle.dump
            pickle.dump = self._wrap_pickle_dump(pickle.dump)
        
        if hasattr(sys.modules.get('pickle'), 'dumps') and 'pickle.dumps' not in self._original_functions:
            import pickle
            self._original_functions['pickle.dumps'] = pickle.dumps
            pickle.dumps = self._wrap_pickle_dumps(pickle.dumps)
        
        logger.info("Ghost Trap Persistence Monitor started")
        print("🛡️  Ghost Trap Persistence Monitor activated")
    
    def stop_monitoring(self):
        """Stop monitoring and restore original functions."""
        if not self._is_monitoring:
            return
            
        self._is_monitoring = False
        
        # Restore original functions
        for func_name, original_func in self._original_functions.items():
            if func_name == 'os.system':
                os.system = original_func
            elif func_name == 'shutil.copy':
                import shutil
                shutil.copy = original_func
            elif func_name == 'pickle.dump':
                import pickle
                pickle.dump = original_func
            elif func_name == 'pickle.dumps':
                import pickle
                pickle.dumps = original_func
        
        self._original_functions.clear()
        logger.info("Ghost Trap Persistence Monitor stopped")
        print("🛡️  Ghost Trap Persistence Monitor deactivated")
    
    @contextmanager
    def monitor_context(self):
        """Context manager for temporary monitoring."""
        self.start_monitoring()
        try:
            yield
        finally:
            self.stop_monitoring()


# Global monitor instance
ghost_monitor = GhostTrapMonitor()


def hook_governor_task_execution(task_func: Callable, *args, **kwargs):
    """
    Hook function to be called by Governor before task execution.
    
    This function wraps the task execution with ghost trap monitoring.
    """
    with ghost_monitor.monitor_context():
        return task_func(*args, **kwargs)


def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring status."""
    return {
        'is_monitoring': ghost_monitor._is_monitoring,
        'hidden_directories': list(ghost_monitor._hidden_directories),
        'wrapped_functions': list(ghost_monitor._original_functions.keys())
    }


# Export the hook function for the Governor to use
__all__ = ['hook_governor_task_execution', 'ghost_monitor', 'get_monitoring_status']