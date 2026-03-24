#!/usr/bin/env python3
"""
PostgreSQL Backup Script for SME v3.0.0

Usage:
    python scripts/backup_postgres.py                    # Interactive mode
    python scripts/backup_postgres.py --schedule        # Add to crontab
    python scripts/backup_postgres.py --restore file   # Restore from backup

Crontab example (daily at 2am):
    0 2 * * * cd /app && python scripts/backup_postgres.py >> /var/log/sme_backup.log 2>&1
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "sme_user")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "sme_nexus")

BACKUP_DIR = os.environ.get("SME_BACKUP_DIR", "/app/data/backups")
RETENTION_DAYS = int(os.environ.get("SME_BACKUP_RETENTION_DAYS", "7"))


def get_backup_filename(prefix: str = "sme") -> str:
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{POSTGRES_DB}_{timestamp}.sql"


def create_backup() -> Path:
    """Create a PostgreSQL backup."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    backup_file = Path(BACKUP_DIR) / get_backup_filename()

    env = os.environ.copy()
    env["PGPASSWORD"] = POSTGRES_PASSWORD

    cmd = [
        "pg_dump",
        "-h",
        POSTGRES_HOST,
        "-p",
        POSTGRES_PORT,
        "-U",
        POSTGRES_USER,
        "-d",
        POSTGRES_DB,
        "-F",
        "p",  # Plain SQL format
        "-f",
        str(backup_file),
    ]

    logger.info(f"Creating backup: {backup_file}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Backup created successfully: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e.stderr}")
        raise


def cleanup_old_backups() -> int:
    """Remove backups older than RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    removed = 0

    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return 0

    for backup_file in backup_path.glob("*.sql"):
        mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
        if mtime < cutoff:
            logger.info(f"Removing old backup: {backup_file}")
            backup_file.unlink()
            removed += 1

    logger.info(f"Removed {removed} old backup(s)")
    return removed


def restore_backup(backup_file: Path) -> None:
    """Restore PostgreSQL from a backup file."""
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    env = os.environ.copy()
    env["PGPASSWORD"] = POSTGRES_PASSWORD

    cmd = [
        "psql",
        "-h",
        POSTGRES_HOST,
        "-p",
        POSTGRES_PORT,
        "-U",
        POSTGRES_USER,
        "-d",
        POSTGRES_DB,
        "-f",
        str(backup_file),
    ]

    logger.info(f"Restoring from backup: {backup_file}")

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Restore completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Restore failed: {e.stderr}")
        raise


def list_backups() -> list[dict]:
    """List available backups."""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return []

    backups = []
    for backup_file in sorted(backup_path.glob("*.sql"), reverse=True):
        stat = backup_file.stat()
        backups.append(
            {
                "file": backup_file.name,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
        )

    return backups


def generate_crontab() -> str:
    """Generate crontab entry for daily backups."""
    return """# SME PostgreSQL Backup - Add to crontab
# Daily at 2:00 AM
0 2 * * * cd /app && python scripts/backup_postgres.py >> /var/log/sme_backup.log 2>&1
"""


def main():
    parser = argparse.ArgumentParser(description="SME PostgreSQL Backup Tool")
    parser.add_argument("--schedule", action="store_true", help="Print crontab entry")
    parser.add_argument("--restore", metavar="FILE", help="Restore from backup")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old backups")

    args = parser.parse_args()

    if args.schedule:
        print(generate_crontab())
        return

    if args.list:
        backups = list_backups()
        if not backups:
            print("No backups found")
            return
        for b in backups:
            print(f"  {b['file']} - {b['size_mb']} MB - {b['created']}")
        return

    if args.restore:
        restore_backup(Path(args.restore))
        return

    if args.cleanup:
        cleanup_old_backups()
        return

    # Default: create backup
    create_backup()
    cleanup_old_backups()


if __name__ == "__main__":
    main()
