"""
DEPRECATED: Secure Extension Loader
===================================

⚠️  THIS MODULE IS DEPRECATED AND WILL BE REMOVED IN v4.0.0 ⚠️

All functionality has been merged into the unified ExtensionManager at:
    gateway.extension_manager.ExtensionManager

The ExtensionManager now includes all security features:
- Manifest schema validation
- Import restriction enforcement (ImportBlocker)
- Path traversal prevention
- Resource quota enforcement
- Content hash verification
- Circuit breaker for failing extensions
- BasePlugin contract validation

Migration:
    OLD: from gateway.secure_extension_loader import SecureExtensionLoader
    NEW: from gateway.extension_manager import ExtensionManager

This file is kept for backward compatibility only. It will proxy calls
to the unified ExtensionManager.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, Optional

from gateway.extension_manager import (
    ExtensionManager,
    SecurityError,
    ImportBlocker,
    MANIFEST_SCHEMA,
    FORBIDDEN_IMPORTS,
    FORBIDDEN_BUILTINS,
)

logger = logging.getLogger("lawnmower.secure_loader")

warnings.warn(
    "gateway.secure_extension_loader is deprecated. "
    "Use gateway.extension_manager.ExtensionManager instead. "
    "This module will be removed in v4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)


class SecureExtensionLoader(ExtensionManager):
    """
    DEPRECATED: Backward-compatible wrapper around ExtensionManager.

    Use ExtensionManager directly instead. This class will be removed in v4.0.0.
    """

    def __init__(
        self,
        extensions_dir: str | None = None,
        strict_mode: bool = True,
    ):
        super().__init__(
            nexus_api=None,
            extensions_dir=extensions_dir,
            strict_mode=strict_mode,
        )


def create_secure_loader(
    extensions_dir: str | None = None,
    strict_mode: bool = True,
) -> SecureExtensionLoader:
    """DEPRECATED: Factory function for creating SecureExtensionLoader."""
    return SecureExtensionLoader(
        extensions_dir=extensions_dir,
        strict_mode=strict_mode,
    )