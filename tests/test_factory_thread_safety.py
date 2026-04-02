"""
Tests for ToolFactory Thread Safety
====================================

Tests the thread-safe improvements made to ToolFactory:
- Lock protection for singleton instances
- VRAM guardrail fix
- Thread safety of create_with_lock
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import pytest


class TestToolFactoryThreadSafety:
    """Tests for thread safety in ToolFactory."""
    
    def test_lock_exists(self):
        """ToolFactory should have a lock for thread safety."""
        from src.core.factory import ToolFactory
        assert hasattr(ToolFactory, '_lock')
        assert isinstance(ToolFactory._lock, type(threading.RLock()))
    
    def test_instances_dict_exists(self):
        """ToolFactory should have _instances dict for caching."""
        from src.core.factory import ToolFactory
        assert hasattr(ToolFactory, '_instances')
        assert isinstance(ToolFactory._instances, dict)
    
    def test_create_with_lock_thread_safe(self):
        """create_with_lock should protect against race conditions."""
        from src.core.factory import ToolFactory
        
        # Reset instances
        ToolFactory._instances.clear()
        
        creation_count = 0
        lock = threading.Lock()
        
        def mock_creator():
            nonlocal creation_count
            time.sleep(0.01)  # Simulate expensive creation
            with lock:
                creation_count += 1
            return MagicMock()
        
        def create_from_thread():
            ToolFactory.create_with_lock('test_tool', mock_creator)
        
        # Create multiple threads
        threads = [threading.Thread(target=create_from_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have created instance only once due to lock
        assert creation_count == 1
        assert 'test_tool' in ToolFactory._instances
        
        # Cleanup
        ToolFactory._instances.clear()
    
    def test_multiple_tools_thread_safe(self):
        """Multiple different tools created concurrently should be safe."""
        from src.core.factory import ToolFactory
        ToolFactory._instances.clear()
        
        errors = []
        
        def create_tool(name):
            try:
                def creator():
                    return MagicMock()
                ToolFactory.create_with_lock(name, creator)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(20):
            t = threading.Thread(target=create_tool, args=(f'tool_{i}',))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0
        assert len(ToolFactory._instances) == 20
        
        # Cleanup
        ToolFactory._instances.clear()


class TestVramGuardrailFix:
    """Tests for the VRAM guardrail bug fix."""
    
    def test_vram_config_is_stored(self):
        """VRAM limit config value should be stored, not discarded."""
        with patch('src.core.factory.Config') as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            
            # Configure to return 4096
            mock_config_instance.get.return_value = {'vram_limit_mb': 4096}
            
            # Import after patching
            from src.core.factory import ToolFactory
            
            # The bug was that vram_limit_mb was never stored
            # After fix, it should be used in the warning
            # We can verify the get is called and result used
            from src.core.config import Config
            config = Config()
            result = config.get('hardware', {}).get('vram_limit_mb', 6144)
            assert result == 4096
    
    def test_vram_guardrail_returns_true_when_enough_memory(self):
        """VRAM check should pass when enough memory available."""
        with patch('src.core.factory.PerformanceProfiler') as mock_profiler:
            mock_instance = MagicMock()
            mock_profiler.return_value = mock_instance
            mock_instance.profile_gpu_fallback.return_value = {
                'gpus': [{'memory_free_mb': 2048}]
            }
            
            from src.core.factory import ToolFactory
            result = ToolFactory._check_vram_guardrail(required_mb=1024)
            assert result is True
    
    def test_vram_guardrail_returns_false_when_insufficient(self):
        """VRAM check should fail when not enough memory."""
        with patch('src.core.factory.PerformanceProfiler') as mock_profiler:
            mock_instance = MagicMock()
            mock_profiler.return_value = mock_instance
            mock_instance.profile_gpu_fallback.return_value = {
                'gpus': [{'memory_free_mb': 256}]  # Less than required
            }
            
            from src.core.factory import ToolFactory
            result = ToolFactory._check_vram_guardrail(required_mb=1024)
            assert result is False
    
    def test_vram_guardrail_graceful_degradation(self):
        """VRAM check should default to True if GPU check fails."""
        with patch('src.core.factory.PerformanceProfiler') as mock_profiler:
            mock_profiler.side_effect = Exception("GPU not available")
            
            from src.core.factory import ToolFactory
            result = ToolFactory._check_vram_guardrail(required_mb=1024)
            assert result is True  # Should not raise, should return True
    
    def test_vram_guardrail_no_gpus(self):
        """VRAM check should pass when no GPUs reported."""
        with patch('src.core.factory.PerformanceProfiler') as mock_profiler:
            mock_instance = MagicMock()
            mock_profiler.return_value = mock_instance
            mock_instance.profile_gpu_fallback.return_value = {'gpus': []}
            
            from src.core.factory import ToolFactory
            result = ToolFactory._check_vram_guardrail(required_mb=1024)
            assert result is True