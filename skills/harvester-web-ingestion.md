---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Data Ingestion
name: harvester-web-ingestion
Source: Semantic Memory Engine (SME)
Source_File: src/harvester/
---

## Purpose

Ingests web content from URLs and converts it into semantic atomic facts for AI agent consumption. The Harvester supports multiple file formats and cloud storage providers.

## Description

The Harvester is a web ingestion engine that transforms URLs into structured, queryable semantic data. It supports PDF, DOCX, HTML, and various cloud storage sources (Google Drive, Dropbox, OneDrive, S3). Extracted content is converted to markdown and atomic facts for downstream forensic analysis.

## Workflow

1. **URL Parsing**: Analyze URL and detect content provider type
2. **Content Fetching**: Retrieve content via HTTP or cloud API
3. **Format Detection**: Identify file type and select appropriate parser
4. **Content Extraction**: Extract text using MarkItDown or native parsers
5. **Semantic Processing**: Convert to markdown and atomic facts
6. **Entity Redaction**: Strip PII before storage (optional)
7. **Storage**: Persist to knowledge graph or database

## Examples

### Example 1: Simple Web Page Ingestion
**Input**: URL to a blog post
**Output**: Markdown content with extracted semantic entities
**Use Case**: Ingesting articles for analysis

### Example 2: PDF Document Processing
**Input**: URL to a PDF file
**Output**: Extracted text with metadata
**Use Case**: Processing research papers or reports

### Example 3: Cloud Storage Integration
**Input**: Shared link from Google Drive
**Output**: Downloaded and parsed content
**Use Case**: Processing collaborative documents

## Implementation Notes

- **Supported Formats**: PDF, DOCX, HTML, TXT, MD
- **Cloud Providers**: Google Drive, Dropbox, OneDrive, S3
- **Parser**: MarkItDown for multi-format support
- **Location**: `D:/SME/src/harvester/`

## See Also

- [SME Documentation - Harvester Panel](D:/SME/docs/CONTROL_ROOM_OPERATOR.md)
- [Crawling Capabilities Expansion](D:/SME/docs/CRAWLING_CAPABILITIES_EXPANSION.md)

---