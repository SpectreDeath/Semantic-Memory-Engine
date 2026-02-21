"""
Error Handling Utilities for SME Extensions

Provides standardized error handling patterns, logging, and error responses
across all SME extensions for consistency and maintainability.
"""

import logging
import json
import traceback
from typing import Any, Dict, Optional, Callable, Union
from datetime import datetime


class SMEError(Exception):
    """Base exception class for SME extension errors."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", 
                 original_exception: Optional[Exception] = None):
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)


class ErrorContext:
    """Context information for error handling."""
    
    def __init__(self, plugin_id: str, operation: str, 
                 user_data: Optional[Dict[str, Any]] = None):
        self.plugin_id = plugin_id
        self.operation = operation
        self.user_data = user_data or {}
        self.timestamp = datetime.now().isoformat()


class ErrorHandler:
    """Standardized error handler for SME extensions."""
    
    def __init__(self, plugin_id: str):
        self.plugin_id = plugin_id
        self.logger = logging.getLogger(f"SME.{plugin_id}")
    
    def handle_extension_error(self, error: Exception, operation: str, 
                              user_data: Optional[Dict[str, Any]] = None,
                              log_level: str = "ERROR") -> Dict[str, Any]:
        """
        Handle extension errors with standardized logging and response format.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            user_data: Additional context data to include in logs
            log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        
        Returns:
            Standardized error response dictionary
        """
        context = ErrorContext(self.plugin_id, operation, user_data)
        
        # Determine error type and code
        error_code = self._get_error_code(error)
        error_message = str(error)
        
        # Log the error with appropriate level
        log_method = getattr(self.logger, log_level.lower())
        log_method(
            f"[{self.plugin_id}] {operation} failed: {error_message} "
            f"(Error Code: {error_code})"
        )
        
        # Log full traceback for debugging
        if log_level.upper() in ['ERROR', 'CRITICAL']:
            self.logger.error(
                f"[{self.plugin_id}] Full traceback for {operation}:",
                exc_info=True
            )
        
        # Return standardized error response
        return {
            "status": "error",
            "error_code": error_code,
            "message": error_message,
            "operation": operation,
            "plugin_id": self.plugin_id,
            "timestamp": context.timestamp,
            "context": context.user_data
        }
    
    def handle_tool_error(self, error: Exception, tool_name: str,
                         user_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle tool execution errors and return JSON response.
        
        Args:
            error: The exception that occurred
            tool_name: Name of the tool that failed
            user_data: Additional context data
        
        Returns:
            JSON string error response
        """
        error_response = self.handle_extension_error(
            error, f"Tool execution: {tool_name}", user_data, "ERROR"
        )
        return json.dumps(error_response, indent=2)
    
    def safe_execute(self, func: Callable, operation: str, 
                    *args, **kwargs) -> Any:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            operation: Description of the operation
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Function result or error response
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return self.handle_extension_error(e, operation)
    
    def safe_async_execute(self, coro, operation: str, 
                          *args, **kwargs) -> Any:
        """
        Safely execute an async function with error handling.
        
        Args:
            coro: Coroutine function to execute
            operation: Description of the operation
            *args, **kwargs: Arguments to pass to the coroutine
        
        Returns:
            Coroutine result or error response
        """
        try:
            # This would be called within an async context
            # The actual await would happen in the calling code
            return coro(*args, **kwargs)
        except Exception as e:
            return self.handle_extension_error(e, operation)
    
    def _get_error_code(self, error: Exception) -> str:
        """Determine appropriate error code based on exception type."""
        error_type = type(error).__name__
        
        error_codes = {
            # Database errors
            "OperationalError": "DB_OPERATIONAL_ERROR",
            "IntegrityError": "DB_INTEGRITY_ERROR", 
            "DatabaseError": "DB_ERROR",
            
            # Network errors
            "ConnectionError": "NETWORK_CONNECTION_ERROR",
            "TimeoutError": "NETWORK_TIMEOUT_ERROR",
            "RequestException": "NETWORK_REQUEST_ERROR",
            
            # File system errors
            "FileNotFoundError": "FILE_NOT_FOUND",
            "PermissionError": "FILE_PERMISSION_ERROR",
            "IsADirectoryError": "FILE_IS_DIRECTORY",
            
            # Configuration errors
            "KeyError": "CONFIGURATION_ERROR",
            "ValueError": "INVALID_VALUE",
            "TypeError": "TYPE_ERROR",
            
            # Plugin-specific errors
            "SMEError": error.error_code if hasattr(error, 'error_code') else "PLUGIN_ERROR",
        }
        
        return error_codes.get(error_type, "UNKNOWN_ERROR")


def create_error_response(message: str, error_code: str = "UNKNOWN_ERROR", 
                         plugin_id: str = "UNKNOWN", operation: str = "UNKNOWN") -> str:
    """
    Create a standardized JSON error response.
    
    Args:
        message: Error message
        error_code: Error code identifier
        plugin_id: Plugin identifier
        operation: Operation that failed
    
    Returns:
        JSON string error response
    """
    error_response = {
        "status": "error",
        "error_code": error_code,
        "message": message,
        "operation": operation,
        "plugin_id": plugin_id,
        "timestamp": datetime.now().isoformat()
    }
    return json.dumps(error_response, indent=2)


def log_operation_start(logger: logging.Logger, plugin_id: str, operation: str,
                       user_data: Optional[Dict[str, Any]] = None):
    """Log the start of an operation."""
    context = ""
    if user_data:
        context = f" | Context: {user_data}"
    
    logger.info(f"[{plugin_id}] Starting {operation}{context}")


def log_operation_success(logger: logging.Logger, plugin_id: str, operation: str,
                         result_summary: Optional[str] = None):
    """Log successful completion of an operation."""
    summary = f" | Result: {result_summary}" if result_summary else ""
    logger.info(f"[{plugin_id}] {operation} completed successfully{summary}")


def log_operation_warning(logger: logging.Logger, plugin_id: str, operation: str,
                         warning: str):
    """Log a warning during operation."""
    logger.warning(f"[{plugin_id}] {operation} warning: {warning}")


# Context manager for operations with automatic error handling
class OperationContext:
    """Context manager for operations with automatic error handling."""
    
    def __init__(self, logger: logging.Logger, plugin_id: str, operation: str,
                 user_data: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.plugin_id = plugin_id
        self.operation = operation
        self.user_data = user_data
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        log_operation_start(self.logger, self.plugin_id, self.operation, self.user_data)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred
            error_handler = ErrorHandler(self.plugin_id)
            error_handler.handle_extension_error(exc_val, self.operation, self.user_data)
            return False  # Don't suppress the exception
        
        # Operation completed successfully
        duration = (datetime.now() - self.start_time).total_seconds()
        log_operation_success(
            self.logger, self.plugin_id, self.operation, 
            f"Duration: {duration:.2f}s"
        )
        return True


# Decorator for automatic error handling
def handle_errors(plugin_id: str, operation_name: Optional[str] = None):
    """
    Decorator to automatically handle errors in functions.
    
    Args:
        plugin_id: Plugin identifier for logging
        operation_name: Optional operation name (defaults to function name)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            error_handler = ErrorHandler(plugin_id)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return error_handler.handle_extension_error(e, op_name)
        return wrapper
    return decorator


# Async decorator for automatic error handling
def handle_async_errors(plugin_id: str, operation_name: Optional[str] = None):
    """
    Decorator to automatically handle errors in async functions.
    
    Args:
        plugin_id: Plugin identifier for logging
        operation_name: Optional operation name (defaults to function name)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            error_handler = ErrorHandler(plugin_id)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return error_handler.handle_extension_error(e, op_name)
        return wrapper
    return decorator