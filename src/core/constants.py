"""
SME Constants - Central Configuration
======================================
All hardcoded values, magic numbers, ports, timeouts, and limits
are centralized here for easy maintenance and configuration.
"""

from __future__ import annotations

# =============================================================================
# Network & Server Configuration
# =============================================================================
DEFAULT_OPERATOR_HOST: str = "0.0.0.0"
DEFAULT_OPERATOR_PORT: int = 8000
DEFAULT_FRONTEND_PORT: int = 5173
DEFAULT_POSTGRES_PORT: int = 5432

# WebSocket
WS_DIAGNOSTICS_PATH: str = "/ws/diagnostics"
WS_RECONNECT_INTERVAL: float = 5.0  # seconds

# =============================================================================
# Timeouts (seconds)
# =============================================================================
DEFAULT_REQUEST_TIMEOUT: float = 30.0
DEFAULT_CRAWL_TIMEOUT: float = 120.0
DEFAULT_HEALTH_CHECK_TIMEOUT: float = 10.0
DEFAULT_WEBSOCKET_TIMEOUT: float = 60.0
EXTENSION_LOAD_TIMEOUT: float = 15.0
DATABASE_QUERY_TIMEOUT: float = 30.0

# Rate Limiting
RATE_LIMIT_WINDOW: int = 60  # seconds
RATE_LIMIT_MAX_REQUESTS: int = 100

# =============================================================================
# Memory & Resource Limits
# =============================================================================
# Hardware constraints (1660 Ti 6GB VRAM)
MAX_VRAM_GB: float = 6.0
MAX_RAM_GB: float = 16.0
BATCH_SIZE_SMALL: int = 32
BATCH_SIZE_MEDIUM: int = 64
BATCH_SIZE_LARGE: int = 128

# Database
MAX_QUERY_RESULTS: int = 1000
MAX_CONTENT_LENGTH: int = 5000  # characters for vaulting
MIN_CONTENT_LENGTH: int = 50  # minimum for analysis

# Cache
DEFAULT_CACHE_SIZE: int = 1000
DEFAULT_CACHE_TTL: int = 600  # seconds (10 minutes)

# =============================================================================
# Analysis Thresholds
# =============================================================================
# Entropy thresholds
ENTROPY_SYNTHETIC_THRESHOLD: float = 4.0
ENTROPY_HUMAN_THRESHOLD: float = 5.0

# Burstiness thresholds
BURSTINESS_SYNTHETIC_THRESHOLD: float = 2.0
BURSTINESS_HUMAN_THRESHOLD: float = 5.0

# Trust Score thresholds
TRUST_SCORE_LOW: int = 50
TRUST_SCORE_HIGH: int = 80

# Cross-Modal Auditor
CLIP_SYNC_THRESHOLD: float = 65.0

# =============================================================================
# Extension System
# =============================================================================
EXTENSIONS_DIR_ENV: str = "SME_EXTENSIONS_DIR"
CIRCUIT_BREAKER_THRESHOLD: int = 3  # failures before disabling
MODULE_NAME_PREFIX: str = "sme_ext_"

# =============================================================================
# File Patterns
# =============================================================================
SUPPORTED_TEXT_EXTENSIONS: tuple[str, ...] = (".txt", ".md", ".log", ".json")
SUPPORTED_IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
SUPPORTED_CODE_EXTENSIONS: tuple[str, ...] = (".py", ".js", ".ts", ".java", ".go", ".rs")

# =============================================================================
# API Versioning
# =============================================================================
API_VERSION: str = "v1"
API_PREFIX: str = f"/api/{API_VERSION}"

# =============================================================================
# Logging
# =============================================================================
LOG_FORMAT: str = (
    '{"time": "%(asctime)s", "level": "%(levelname)s", '
    '"module": "%(name)s", "message": "%(message)s"}'
)
LOG_DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
DEFAULT_LOG_LEVEL: str = "INFO"

# =============================================================================
# Version
# =============================================================================
SME_VERSION: str = "3.0.1"
SME_NAME: str = "Lawnmower Man: Forensic MCP Gateway"
