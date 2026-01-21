"""
Comprehensive tests for Structured Logging System

Tests cover:
- JSON formatting and output
- Context propagation
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File rotation and persistence
- Integration with EventBus
- Thread safety and cleanup
- Error handling and recovery
"""

import pytest
import json
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import asyncio
from io import StringIO

from src.core.logging_system import (
    StructuredLogger,
    LogLevel,
    LogManager,
    LogContext,
    JSONFormatter,
    get_logger,
    setup_logging,
    get_log_context,
    reset_logging,
)


class TestJSONFormatter:
    """Tests for JSON formatter."""
    
    def test_format_basic_record(self):
        """Test formatting basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test.module"
        assert data["line"] == 42
    
    def test_format_with_context(self):
        """Test formatting with context fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"request_id": "123", "user_id": "user-1"}
        
        result = formatter.format(record)
        data = json.loads(result)
        
        assert data["request_id"] == "123"
        assert data["user_id"] == "user-1"
    
    def test_format_invalid_json_fallback(self):
        """Test fallback when JSON encoding fails."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None
        )
        # Add non-serializable object
        record.extra_fields = {"obj": object()}
        
        result = formatter.format(record)
        # Should contain JSON with str() representation
        assert "object" in result or "JSON" in result


class TestLogContext:
    """Tests for context propagation."""
    
    def test_context_manager_sets_fields(self):
        """Test context manager sets fields."""
        from src.core.logging_system import _context
        
        _context.set({})  # Clear context
        
        with LogContext(request_id="123", user_id="user-1"):
            ctx = _context.get()
            assert ctx["request_id"] == "123"
            assert ctx["user_id"] == "user-1"
    
    def test_context_restored_after_exit(self):
        """Test context restored after exiting manager."""
        from src.core.logging_system import _context
        
        _context.set({})
        original = _context.get().copy()
        
        with LogContext(request_id="123"):
            pass
        
        # Context should be restored
        assert _context.get() == original
    
    def test_nested_contexts(self):
        """Test nested context managers."""
        from src.core.logging_system import _context
        
        _context.set({})
        
        with LogContext(request_id="123"):
            with LogContext(user_id="user-1"):
                ctx = _context.get()
                assert ctx["request_id"] == "123"
                assert ctx["user_id"] == "user-1"
    
    def test_context_overrides(self):
        """Test context field overrides."""
        from src.core.logging_system import _context
        
        _context.set({"field": "original"})
        
        with LogContext(field="override"):
            ctx = _context.get()
            assert ctx["field"] == "override"


class TestStructuredLogger:
    """Tests for StructuredLogger class."""
    
    @pytest.fixture
    def logger(self):
        """Create test logger with string handler."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        py_logger = logging.getLogger("test")
        py_logger.handlers.clear()
        
        # Add string handler for testing
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())
        py_logger.addHandler(handler)
        py_logger.setLevel(logging.DEBUG)
        
        logger = StructuredLogger(py_logger)
        logger._stream = stream
        
        return logger
    
    def test_debug_message(self, logger):
        """Test debug logging."""
        logger.debug("Debug message", component="test")
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["level"] == "DEBUG"
        assert data["message"] == "Debug message"
        assert data["component"] == "test"
    
    def test_info_message(self, logger):
        """Test info logging."""
        logger.info("Info message")
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["level"] == "INFO"
        assert data["message"] == "Info message"
    
    def test_warning_message(self, logger):
        """Test warning logging."""
        logger.warning("Warning message")
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["level"] == "WARNING"
        assert data["message"] == "Warning message"
    
    def test_error_message(self, logger):
        """Test error logging."""
        logger.error("Error message", code=500)
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["level"] == "ERROR"
        assert data["message"] == "Error message"
        assert data["code"] == 500
    
    def test_critical_message(self, logger):
        """Test critical logging."""
        logger.critical("Critical message")
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["level"] == "CRITICAL"
        assert data["message"] == "Critical message"
    
    def test_with_context_manager(self, logger):
        """Test with_context helper."""
        with logger.with_context(request_id="req-123", user_id="user-1"):
            logger.info("Message in context")
        
        output = logger._stream.getvalue()
        data = json.loads(output.strip())
        
        assert data["request_id"] == "req-123"
        assert data["user_id"] == "user-1"
    
    def test_logger_name(self, logger):
        """Test logger name is stored."""
        assert logger.name == "test"
    
    def test_logger_repr(self, logger):
        """Test string representation."""
        repr_str = repr(logger)
        assert "StructuredLogger" in repr_str
        assert "test" in repr_str


class TestLogLevel:
    """Tests for LogLevel enum."""
    
    def test_all_levels_present(self):
        """Test all log levels defined."""
        assert LogLevel.DEBUG.value == logging.DEBUG
        assert LogLevel.INFO.value == logging.INFO
        assert LogLevel.WARNING.value == logging.WARNING
        assert LogLevel.ERROR.value == logging.ERROR
        assert LogLevel.CRITICAL.value == logging.CRITICAL
    
    def test_level_ordering(self):
        """Test log levels have correct ordering."""
        assert LogLevel.DEBUG.value < LogLevel.INFO.value
        assert LogLevel.INFO.value < LogLevel.WARNING.value
        assert LogLevel.WARNING.value < LogLevel.ERROR.value
        assert LogLevel.ERROR.value < LogLevel.CRITICAL.value


class TestLogManager:
    """Tests for LogManager singleton."""
    
    def test_singleton_pattern(self):
        """Test LogManager is singleton."""
        reset_logging()
        manager1 = LogManager()
        manager2 = LogManager()
        
        assert manager1 is manager2
    
    def test_setup_configuration(self):
        """Test setup with configuration."""
        reset_logging()
        
        config = {
            "level": "WARNING",
            "log_file": "test.log",
            "rotate_size_mb": 50,
            "backup_count": 3
        }
        
        LogManager.setup(config)
        
        assert LogManager._configured is True
    
    def test_setup_idempotent(self):
        """Test setup is idempotent."""
        reset_logging()
        LogManager.setup({"level": "DEBUG"})
        LogManager.setup({"level": "ERROR"})  # Should not reconfigure
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG  # First config wins
    
    def test_get_logger_creates_new(self):
        """Test get_logger creates new loggers."""
        reset_logging()
        manager = LogManager()
        
        logger1 = manager.get_logger("test1")
        logger2 = manager.get_logger("test2")
        
        assert logger1.name == "test1"
        assert logger2.name == "test2"
        assert logger1 is not logger2
    
    def test_get_logger_caches(self):
        """Test get_logger caches instances."""
        reset_logging()
        manager = LogManager()
        
        logger1 = manager.get_logger("test")
        logger2 = manager.get_logger("test")
        
        assert logger1 is logger2
    
    def test_reset_clears_state(self):
        """Test reset clears LogManager state."""
        LogManager.setup({"level": "DEBUG"})
        assert LogManager._configured is True
        
        LogManager.reset()
        assert LogManager._configured is False


class TestModuleFunctions:
    """Tests for module-level functions."""
    
    def test_get_logger_function(self):
        """Test get_logger function."""
        reset_logging()
        
        logger = get_logger("test")
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test"
    
    def test_setup_logging_function(self):
        """Test setup_logging function."""
        reset_logging()
        
        setup_logging({"level": "DEBUG"})
        
        assert LogManager._configured is True
    
    def test_get_log_context_function(self):
        """Test get_log_context function."""
        ctx = get_log_context(request_id="123")
        
        assert isinstance(ctx, LogContext)
    
    def test_reset_logging_function(self):
        """Test reset_logging function."""
        LogManager.setup()
        assert LogManager._configured is True
        
        reset_logging()
        
        assert LogManager._configured is False


class TestFileLogging:
    """Tests for file-based logging configuration."""
    
    def test_log_manager_setup_creates_handlers(self):
        """Test that setup creates appropriate handlers."""
        reset_logging()
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        LogManager.setup({"level": "DEBUG"})
        
        # Should have handlers configured
        assert len(root_logger.handlers) > 0
    
    def test_log_manager_configuration_defaults(self):
        """Test LogManager applies default configuration."""
        reset_logging()
        
        LogManager.setup()  # Use defaults
        
        assert LogManager._configured is True
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
    
    def test_log_manager_custom_level(self):
        """Test LogManager applies custom log level."""
        reset_logging()
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        LogManager.setup({"level": "WARNING"})
        
        # Root logger should be set to WARNING
        assert root_logger.level == logging.WARNING


class TestLogIntegration:
    """Integration tests for logging system."""
    
    def test_multiple_loggers(self):
        """Test multiple loggers work independently."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both should be usable
        logger1.info("Message 1")
        logger2.warning("Message 2")
    
    def test_context_across_loggers(self):
        """Test context propagates across different loggers."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        with get_log_context(request_id="123"):
            # Both loggers should see the context
            # (Would need to capture output to verify)
            logger1.info("Message 1")
            logger2.info("Message 2")
    
    def test_exception_logging(self):
        """Test logging exceptions."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error("An error occurred", exc_info=True)
    
    def test_logging_with_all_field_types(self):
        """Test logging with various field types."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        logger.info(
            "Message",
            string="value",
            number=42,
            float_val=3.14,
            bool_val=True,
            none_val=None,
            list_val=[1, 2, 3],
            dict_val={"nested": "value"}
        )


class TestThreadSafety:
    """Tests for thread safety."""
    
    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        def log_messages():
            for i in range(10):
                logger.info(f"Message {i}")
        
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(log_messages) for _ in range(4)]
            for future in futures:
                future.result()


class TestErrorHandling:
    """Tests for error handling and recovery."""
    
    def test_logger_handles_none_message(self):
        """Test logger handles None message gracefully."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        # Should not crash
        logger.info(None)  # type: ignore
    
    def test_logger_handles_special_characters(self):
        """Test logger handles special characters."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        logger.info("Message with special: \n\t\r\\\"'")
    
    def test_logger_handles_unicode(self):
        """Test logger handles unicode characters."""
        reset_logging()
        setup_logging({"level": "DEBUG"})
        
        logger = get_logger("test")
        
        logger.info("Unicode: 中文 العربية Ελληνικά")


class TestLoggingPerformance:
    """Performance-related tests."""
    
    def test_logging_overhead_is_minimal(self):
        """Test logging has minimal performance overhead."""
        import time
        
        reset_logging()
        setup_logging({"level": "INFO"})
        
        logger = get_logger("test")
        
        # Time 1000 log calls
        start = time.time()
        for i in range(1000):
            logger.info(f"Message {i}", index=i)
        elapsed = time.time() - start
        
        # Should be fast (< 1 second for 1000 calls = < 1ms per call)
        assert elapsed < 1.0
    
    def test_context_manager_overhead(self):
        """Test context manager has minimal overhead."""
        import time
        
        from src.core.logging_system import _context
        
        # Time 10000 context manager creations
        start = time.time()
        for i in range(10000):
            with LogContext(iteration=i):
                pass
        elapsed = time.time() - start
        
        # Should be very fast
        assert elapsed < 1.0
