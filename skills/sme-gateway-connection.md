---
Domain: SME_INTEGRATION
Version: 1.0.0
Complexity: Intermediate
Type: Tool
Category: Integration
name: sme-gateway-connection
Source: Semantic Memory Engine (SME)
Source_File: gateway/mcp_server.py
---

## Purpose

Establishes and manages connection to the SME (Semantic Memory Engine) MCP Gateway for accessing forensic AI capabilities. This skill enables AI agents to connect to the Lawnmower Man gateway and execute MCP tools.

## Description

The SME Gateway provides a Model Context Protocol (MCP) server that exposes forensic capabilities including trust scoring, adversarial pattern detection, stylometric analysis, and web ingestion. This skill handles connection lifecycle, authentication, and tool invocation through the MCP protocol.

## Workflow

1. **Connection Setup**: Initialize MCP client with gateway URL and credentials
2. **Handshake**: Perform capability negotiation with the gateway
3. **Tool Discovery**: Enumerate available MCP tools and their schemas
4. **Tool Invocation**: Execute specific forensic tools via JSON-RPC
5. **Result Processing**: Parse and validate tool responses
6. **Connection Management**: Handle reconnection and session persistence

## Examples

### Example 1: Connect to Local SME Gateway
**Input**: Request to connect to SME gateway at localhost:8000
**Output**: Active MCP connection with discovered tools
**Use Case**: Connecting to local SME instance for testing

### Example 2: Connect to Remote SME Gateway
**Input**: Request to connect to SME gateway with API key
**Output**: Authenticated connection to remote SME instance
**Use Case**: Connecting to production SME deployment

### Example 3: List Available Tools
**Input**: Request to enumerate MCP tools
**Output**: List of available forensic tools with schemas
**Use Case**: Discovering tool capabilities before execution

## Implementation Notes

- **Protocol**: MCP (Model Context Protocol) over stdio or HTTP
- **Authentication**: API key or TPM-signed requests
- **Python Dependencies**: `mcp` client SDK, `pydantic`
- **Gateway Location**: `D:/SME/gateway/mcp_server.py`
- **Port**: 8000 (default)

## Capabilities Exposed

- `trust_score_analysis` - Calculate epistemic trust scores
- `adversarial_pattern_detect` - Detect AI-smoothed text
- `stylometric_analyze` - Analyze writing style signatures
- `harvester_ingest` - Ingest web content
- `forensic_store` - Store evidentiary data
- `logic_verify` - Verify logical consistency

## See Also

- [SME Documentation](D:/SME/README.md)
- [SME v3.0.0 Operator Manual](D:/SME/SME%20v3.0.0%20Operator%20Manual.md)
- [MCP Protocol Specification](https://modelcontextprotocol.io)