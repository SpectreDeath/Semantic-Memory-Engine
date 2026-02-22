# SME IDE Extension

This is the VS Code wrapper for the Semantic Memory Engine (SME). It transforms VS Code into a standalone forensic IDE where the SME engine acts as the 'brain'.

## Features

- **SME Explorer**: Browse semantic memory nodes and relationships in a custom Sidebar.
- **SME Dark Theme**: A high-performance dark theme optimized for forensic analysis.
- **JSON-RPC Bridge**: Live communication with the Python-based SME Core.

## Getting Started

1. Install dependencies:

   ```bash
   cd sme-ide-extension
   npm install
   ```

2. Compile the extension:

   ```bash
   npm run compile
   ```

3. Run the Python Bridge (Manual Start for Dev):

   ```bash
   python ../src/ai/bridge_rpc.py
   ```

4. Sideload in VS Code:
   - Open the `sme-ide-extension` folder in VS Code.
   - Press `F5` to start a new Extension Development Host window.

## Architecture

- `src/extension.ts`: Entry point.
- `src/views/SMEExplorerProvider.ts`: Sidebar implementation.
- `src/ai/bridge_rpc.py`: (Outside folder) The Python backend bridge.
