# SME Extension Error Handling Guide

This guide explains how to use the standardized error handling utilities provided by `src/utils/error_handling.py` to ensure consistent error handling across all SME extensions.

## Overview

The error handling utilities provide:

- **Standardized error responses** with consistent JSON format
- **Enhanced logging** with context and error codes
- **Error categorization** for different types of failures
- **Context managers** for automatic operation tracking
- **Decorators** for automatic error handling
- **Safe execution wrappers** for functions and coroutines

## Quick Start

### Basic Error Handling

```python
from src.utils.error_handling import ErrorHandler, create_error_response

class MyPlugin(BasePlugin):
    def __init__(self, manifest, nexus_api):
        super().__init__(manifest, nexus_api)
        self.error_handler = ErrorHandler(self.plugin_id)
    
    async def my_tool(self):
        try:
            # Your operation here
            result = await self._do_something()
            return result
        except Exception as e:
            # Handle error with context
            return self.error_handler.handle_tool_error(
                e, "my_tool", {"user_id": "123"}
            )
```

### Using Context Manager

```python
from src.utils.error_handling import OperationContext

async def my_operation(self, data):
    with OperationContext(self.logger, self.plugin_id, "my_operation", {"data_size": len(data)}):
        # Your operation here
        result = await self._process_data(data)
        return result
```

### Using Decorators

```python
from src.utils.error_handling import handle_async_errors

@handle_async_errors("MyPlugin", "my_tool")
async def my_tool(self, input_data):
    # Your operation here - errors are automatically handled
    return await self._process(input_data)
```

## Error Response Format

All error responses follow this standardized JSON format:

```json
{
    "status": "error",
    "error_code": "DB_OPERATIONAL_ERROR",
    "message": "Database connection failed",
    "operation": "Tool execution: my_tool",
    "plugin_id": "MyPlugin",
    "timestamp": "2026-02-20T12:30:45.123456",
    "context": {
        "user_id": "123",
        "data_size": 1024
    }
}
```

## Error Codes

The system automatically categorizes errors:

### Database Errors
- `DB_OPERATIONAL_ERROR` - Database connection issues
- `DB_INTEGRITY_ERROR` - Constraint violations
- `DB_ERROR` - General database errors

### Network Errors
- `NETWORK_CONNECTION_ERROR` - Connection failures
- `NETWORK_TIMEOUT_ERROR` - Request timeouts
- `NETWORK_REQUEST_ERROR` - HTTP request failures

### File System Errors
- `FILE_NOT_FOUND` - Missing files
- `FILE_PERMISSION_ERROR` - Access denied
- `FILE_IS_DIRECTORY` - Expected file, got directory

### Configuration Errors
- `CONFIGURATION_ERROR` - Missing or invalid config
- `INVALID_VALUE` - Invalid parameter values
- `TYPE_ERROR` - Type mismatches

### Plugin Errors
- `PLUGIN_ERROR` - Plugin-specific errors
- `UNKNOWN_ERROR` - Uncategorized errors

## Advanced Usage

### Custom Error Classes

```python
from src.utils.error_handling import SMEError

class MyPluginError(SMEError):
    def __init__(self, message, original_exception=None):
        super().__init__(message, "MY_PLUGIN_ERROR", original_exception)

# Usage
raise MyPluginError("Something went wrong", original_exception)
```

### Safe Execution

```python
# For regular functions
result = self.error_handler.safe_execute(
    self._my_function, "my_operation", arg1, arg2
)

# For async functions (use within async context)
coro = self.error_handler.safe_async_execute(
    self._my_async_function, "my_async_operation", arg1, arg2
)
result = await coro
```

### Operation Tracking

```python
from src.utils.error_handling import log_operation_start, log_operation_success, log_operation_warning

async def my_complex_operation(self):
    log_operation_start(self.logger, self.plugin_id, "complex_operation", {"step": "initialization"})
    
    # Step 1
    log_operation_success(self.logger, self.plugin_id, "step_1", "Database initialized")
    
    # Step 2
    log_operation_warning(self.logger, self.plugin_id, "step_2", "High memory usage detected")
    
    # Step 3
    log_operation_success(self.logger, self.plugin_id, "step_3", "Processing completed")
```

## Migration Guide

### Before (Inconsistent)

```python
async def old_tool(self):
    try:
        result = await self._do_work()
        return result
    except Exception as e:
        self.logger.error(f"Tool failed: {e}")
        return {"error": str(e)}
```

### After (Standardized)

```python
async def new_tool(self):
    try:
        result = await self._do_work()
        return result
    except Exception as e:
        return self.error_handler.handle_tool_error(e, "new_tool")
```

## Best Practices

1. **Always use error handlers** for tool methods that return JSON responses
2. **Provide context** when possible to help with debugging
3. **Use appropriate log levels** (ERROR for failures, WARNING for issues)
4. **Include operation names** for better traceability
5. **Use decorators** for simple operations to reduce boilerplate
6. **Use context managers** for complex operations with multiple steps

## Integration with Existing Extensions

The following extensions have been updated to use the new error handling:

- `ext_adversarial_tester` - Added ErrorHandler import
- `ext_atlas` - Can be updated to use standardized error responses
- `ext_logic_auditor` - Can be updated to use ErrorHandler
- `ext_tactical_forensics` - Can be updated to use standardized responses
- `ext_sample_echo` - Can be updated to use ErrorHandler
- `ext_immunizer` - Can be updated to use standardized responses
- `ext_archival_diff` - Can be updated to use ErrorHandler
- `ext_governor` - Can be updated to use standardized responses

## Future Enhancements

- **Metrics collection** for error rates and patterns
- **Error recovery strategies** for transient failures
- **Circuit breaker patterns** for external dependencies
- **Error correlation** across multiple operations