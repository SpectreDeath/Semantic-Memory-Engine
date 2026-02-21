# SME Forensic Toolkit - VS Code Extension

This extension integrates the Semantic Memory Engine (SME) into VS Code / Cline for AI-powered forensic analysis.

## Features

- **SME: Analyze** - Run forensic analysis on selected files or directories
- **SME: Query** - Query the knowledge base with natural language
- **SME: Status** - View server status and statistics
- **SME: Start/Stop Server** - Control the embedded MCP server

## Requirements

- Python 3.9+
- VS Code 1.75+
- Optional: Ollama for local AI inference

## Installation

### Option 1: Build .vsix Package

```bash
# Install vsce if needed
npm install -g vsce

cd extension
vsce package
code --install-extension sme-forensic-toolkit-*.vsix
```

### Option 2: Load Unpacked (Development)

```bash
code --extension-development extension/
```

## Configuration

After installation, configure the extension in VS Code settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `sme.serverPort` | 8089 | MCP server port |
| `sme.aiProvider` | ollama | AI provider |
| `sme.ollamaUrl` | http://localhost:11434 | Ollama server URL |
| `sme.dataDir` | ${workspaceFolder}/data | Data directory |

## Usage

1. **Start the server**: Press `Ctrl+Shift+P` → "SME: Start Server"
2. **Analyze a file**: Open a file, press `Ctrl+Shift+P` → "SME: Analyze"
3. **Query knowledge**: Press `Ctrl+Shift+P` → "SME: Query"

## Commands

| Command | Description |
|---------|-------------|
| `sme.analyze` | Analyze selected file/directory |
| `sme.query` | Query knowledge base |
| `sme.status` | Show server status |
| `sme.startServer` | Start MCP server |
| `sme.stopServer` | Stop MCP server |

## Docker Integration

The extension can connect to SME running in Docker:

```yaml
# docker-compose.yaml
services:
  sme-sidecar:
    ports:
      - "8089:8089"
```

Set `sme.serverPort` to match your Docker port.

## Architecture

```
+------------------------------------------+
|           VS Code / Cline               |
+------------------------------------------+
|  SME Extension                          |
|  +-- Command Palette Integration        |
|  +-- Status Bar                        |
|  +-- MCP Client                        |
+------------------------------------------+
|  SME MCP Server (Python)               |
|  +-- Forensic Analysis                 |
|  +-- Knowledge Query                   |
|  +-- AI Integration (Ollama/OpenAI)    |
+------------------------------------------+
```

## License

MIT
