import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import httpx
import psycopg2

logger = logging.getLogger("lawnmower.health_check")

REQUIRED_ENV_VARS = [
    "SME_GATEWAY_SECRET",
    "SME_ADMIN_PASSWORD",
    "SME_HSM_SECRET",
    "SME_SIDECAR_URL",
]

_DEFAULT_DATA_DIR = str(Path(__file__).resolve().parent.parent / "data")

POSTGRES_CONFIG = {
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "database": os.environ.get("POSTGRES_DB", "sme_nexus"),
}

SIDECAR_URL = os.environ.get("SME_SIDECAR_URL", "http://127.0.0.1:8089")


def _check_postgresql() -> dict[str, str]:
    try:
        conn = psycopg2.connect(
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"],
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database=POSTGRES_CONFIG["database"],
            connect_timeout=5,
        )
        conn.close()
        logger.info("PostgreSQL health check passed")
        return {"status": "pass", "message": "PostgreSQL connection successful"}
    except psycopg2.OperationalError as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        return {"status": "fail", "message": f"PostgreSQL connection failed: {e}"}
    except Exception as e:
        logger.warning(f"PostgreSQL health check error: {e}")
        return {"status": "fail", "message": f"PostgreSQL error: {e}"}


def _check_sqlite() -> dict[str, str]:
    try:
        base_dir = os.environ.get("SME_DATA_DIR") or _DEFAULT_DATA_DIR
        primary_path = os.path.normpath(os.path.join(base_dir, "forensic_nexus.db"))

        if not os.path.exists(primary_path):
            logger.warning(f"SQLite database not found at {primary_path}")
            return {"status": "fail", "message": f"Database file not found: {primary_path}"}

        conn = sqlite3.connect(primary_path, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()

        logger.info("SQLite health check passed")
        return {"status": "pass", "message": f"SQLite database accessible at {primary_path}"}
    except sqlite3.OperationalError as e:
        logger.warning(f"SQLite health check failed: {e}")
        return {"status": "fail", "message": f"SQLite error: {e}"}
    except Exception as e:
        logger.warning(f"SQLite health check error: {e}")
        return {"status": "fail", "message": f"SQLite error: {e}"}


def _check_sidecar() -> dict[str, str]:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{SIDECAR_URL}/health")
            if response.status_code == 200:
                logger.info("Sidecar health check passed")
                return {"status": "pass", "message": f"Sidecar service available at {SIDECAR_URL}"}
            else:
                logger.warning(f"Sidecar health check returned status {response.status_code}")
                return {
                    "status": "fail",
                    "message": f"Sidecar returned status {response.status_code}",
                }
    except httpx.ConnectError as e:
        logger.warning(f"Sidecar health check failed: {e}")
        return {"status": "fail", "message": f"Cannot connect to sidecar at {SIDECAR_URL}: {e}"}
    except httpx.TimeoutException as e:
        logger.warning(f"Sidecar health check timed out: {e}")
        return {"status": "fail", "message": f"Sidecar request timed out: {e}"}
    except Exception as e:
        logger.warning(f"Sidecar health check error: {e}")
        return {"status": "fail", "message": f"Sidecar error: {e}"}


def _check_environment() -> dict[str, str]:
    try:
        missing = []
        for var in REQUIRED_ENV_VARS:
            value = os.environ.get(var)
            if not value or value.startswith("CHANGE_ME"):
                missing.append(var)

        if missing:
            logger.warning(f"Missing or incomplete environment variables: {missing}")
            return {
                "status": "fail",
                "message": f"Missing/incomplete env vars: {', '.join(missing)}",
            }

        logger.info("Environment variables health check passed")
        return {"status": "pass", "message": "All required environment variables present"}
    except Exception as e:
        logger.warning(f"Environment check error: {e}")
        return {"status": "fail", "message": f"Environment check error: {e}"}


def _check_disk_space() -> dict[str, str]:
    try:
        base_dir = os.environ.get("SME_DATA_DIR") or _DEFAULT_DATA_DIR
        abs_path = os.path.abspath(base_dir)

        if not os.path.exists(abs_path):
            logger.warning(f"Data directory does not exist: {abs_path}")
            return {"status": "fail", "message": f"Data directory not found: {abs_path}"}

        import shutil

        stat = shutil.disk_usage(abs_path)
        free_gb = stat.free / (1024**3)

        if free_gb < 1.0:
            logger.warning(f"Low disk space: {free_gb:.2f}GB free")
            return {"status": "fail", "message": f"Low disk space: {free_gb:.2f}GB free"}

        logger.info(f"Disk space check passed: {free_gb:.2f}GB available")
        return {"status": "pass", "message": f"Disk space OK ({free_gb:.2f}GB free)"}
    except Exception as e:
        logger.warning(f"Disk space check error: {e}")
        return {"status": "fail", "message": f"Disk space check error: {e}"}


def _check_extensions() -> dict[str, str]:
    try:
        from gateway.extension_manager import ExtensionManager
        from gateway.nexus_db import get_nexus

        nexus = get_nexus()
        manager = ExtensionManager(nexus_api=nexus)
        status = manager.get_status()

        if not status:
            logger.warning("No extensions loaded")
            return {"status": "fail", "message": "No extensions loaded"}

        logger.info(f"Extensions health check passed: {len(status)} loaded")
        return {"status": "pass", "message": f"{len(status)} extensions loaded"}
    except ImportError as e:
        logger.warning(f"Extension manager not available: {e}")
        return {"status": "fail", "message": f"Extension manager unavailable: {e}"}
    except TypeError as e:
        logger.warning(f"Extension manager instantiation issue: {e}")
        return {"status": "fail", "message": f"Extension manager unavailable: {e}"}
    except Exception as e:
        logger.warning(f"Extensions check error: {e}")
        return {"status": "fail", "message": f"Extensions check error: {e}"}


def deep_health_check() -> dict[str, Any]:
    checks = {
        "postgresql": _check_postgresql(),
        "sqlite": _check_sqlite(),
        "sidecar": _check_sidecar(),
        "environment": _check_environment(),
        "disk_space": _check_disk_space(),
        "extensions": _check_extensions(),
    }

    passed = sum(1 for c in checks.values() if c["status"] == "pass")
    total = len(checks)

    if passed == total:
        status = "healthy"
    elif passed == 0:
        status = "unhealthy"
    else:
        status = "degraded"

    logger.info(f"Deep health check: {status} ({passed}/{total} checks passed)")

    return {
        "status": status,
        "checks": checks,
        "timestamp": time.time(),
    }
