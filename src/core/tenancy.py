"""
Multi-tenancy - Data isolation for SimpleMem.

Provides:
- TenantContext for tracking current tenant
- Utilities for tenant-specific storage identifiers
- Middleware for tenant identification
"""

from contextvars import ContextVar
from typing import Optional, Any, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Context variable to store the current tenant_id
_tenant_context: ContextVar[str] = ContextVar("tenant_id", default="default")

class TenantContext:
    """Context manager and utilities for multi-tenancy."""
    
    @staticmethod
    def set_tenant(tenant_id: str):
        """Set the current tenant_id for the context."""
        return _tenant_context.set(tenant_id)

    @staticmethod
    def get_tenant() -> str:
        """Get the current tenant_id from the context."""
        return _tenant_context.get()

    @staticmethod
    def reset(token):
        """Reset the tenant context using the token returned by set_tenant."""
        _tenant_context.reset(token)

def with_tenant(tenant_id: str):
    """Decorator to run a function within a specific tenant context."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = TenantContext.set_tenant(tenant_id)
            try:
                return func(*args, **kwargs)
            finally:
                TenantContext.reset(token)
        return wrapper
    return decorator

def get_tenant_collection_name(base_name: str) -> str:
    """Get a tenant-specific collection name for vector DB."""
    tenant = TenantContext.get_tenant()
    if tenant == "default":
        return base_name
    return f"{base_name}_{tenant}"

def get_tenant_db_path(base_path: str) -> str:
    """Get a tenant-specific database path for SQLite."""
    tenant = TenantContext.get_tenant()
    if tenant == "default":
        return base_path
    
    # Insert tenant into file name before .db
    if base_path.endswith('.db'):
        return base_path.replace('.db', f'_{tenant}.db')
    return f"{base_path}_{tenant}"
