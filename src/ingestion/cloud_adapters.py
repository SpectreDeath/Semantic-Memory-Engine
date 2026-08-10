"""Multi-Cloud Storage Document Ingestion Adapters for SME Forensic Gateway.

Provides standardized connectors for S3, Dropbox, and OneDrive file sources,
converting cloud documents into normalized SME AtomicFact payloads.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class CloudDocument:
    """Normalized cloud storage document payload."""

    doc_id: str
    filename: str
    source_provider: str  # "s3", "dropbox", "onedrive"
    content_type: str
    content: str
    metadata: Dict[str, Any]


class S3StorageAdapter:
    """Mock connector for AWS S3 bucket file ingestion."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region

    def list_and_ingest(self, prefix: str = "") -> List[CloudDocument]:
        """List and convert S3 objects into SME CloudDocument objects."""
        logger.info("Ingesting S3 bucket s3://%s/%s", self.bucket_name, prefix)
        return [
            CloudDocument(
                doc_id=f"s3-{self.bucket_name}-doc-1",
                filename="s3_evidence_log.txt",
                source_provider="s3",
                content_type="text/plain",
                content="Forensic audit trail document retrieved from S3 storage bucket.",
                metadata={"bucket": self.bucket_name, "region": self.region, "prefix": prefix},
            )
        ]


class DropboxStorageAdapter:
    """Mock connector for Dropbox file ingestion."""

    def __init__(self, access_token: str | None = None):
        self.access_token = access_token

    def ingest_folder(self, folder_path: str = "/forensics") -> List[CloudDocument]:
        """Ingest documents from specified Dropbox folder."""
        logger.info("Ingesting Dropbox folder %s", folder_path)
        return [
            CloudDocument(
                doc_id="dropbox-doc-101",
                filename="dropbox_report.pdf",
                source_provider="dropbox",
                content_type="application/pdf",
                content="Extracted intelligence briefing from Dropbox team folder.",
                metadata={"folder_path": folder_path},
            )
        ]


class OneDriveStorageAdapter:
    """Mock connector for Microsoft OneDrive / SharePoint file ingestion."""

    def __init__(self, tenant_id: str | None = None):
        self.tenant_id = tenant_id

    def ingest_drive(self, drive_id: str = "main") -> List[CloudDocument]:
        """Ingest documents from Microsoft OneDrive."""
        logger.info("Ingesting OneDrive drive %s", drive_id)
        return [
            CloudDocument(
                doc_id="onedrive-doc-202",
                filename="onedrive_financials.xlsx",
                source_provider="onedrive",
                content_type="text/csv",
                content="Financial ledger export retrieved from OneDrive business drive.",
                metadata={"drive_id": drive_id, "tenant_id": self.tenant_id},
            )
        ]
