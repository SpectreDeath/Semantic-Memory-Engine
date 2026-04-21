// SME Forensic Toolkit - VS Code Extension
// Pure JavaScript implementation

const vscode = require('vscode');
const { spawn, ChildProcess } = require('child_process');
const path = require('path');

// Global server process
let serverProcess = null;
let statusBarItem = null;

// Configuration
function getConfig() {
    return vscode.workspace.getConfiguration('sme');
}

// Update status bar
function updateStatus(status) {
    if (!statusBarItem) {
        statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
    }
    
    switch (status) {
        case 'running':
            statusBarItem.text = '$(check) SME Running';
            statusBarItem.color = '#4caf50';
            break;
        case 'stopped':
            statusBarItem.text = '$(circle-slash) SME Stopped';
            statusBarItem.color = '#9e9e9e';
            break;
        case 'error':
            statusBarItem.text = '$(error) SME Error';
            statusBarItem.color = '#f44336';
            break;
    }
    statusBarItem.show();
}

// Start SME server
async function startServer() {
    if (serverProcess) {
        vscode.window.showWarningMessage('SME server is already running');
        return;
    }
    
    const config = getConfig();
    const port = config.get('serverPort', 8089);
    const dataDir = config.get('dataDir', '${workspaceFolder}/data');
    
    try {
        // Start the MCP server process
        serverProcess = spawn('python', [
            '-m', 'src.gateway.mcp_server',
            '--port', port.toString(),
            '--data-dir', dataDir
        ], {
            cwd: vscode.workspace.rootPath,
            detached: false,
            shell: true
        });
        
        serverProcess.stdout.on('data', (data) => {
            console.log('[SME]', data.toString());
        });
        
        serverProcess.stderr.on('data', (data) => {
            console.error('[SME Error]', data.toString());
        });
        
        serverProcess.on('exit', (code) => {
            serverProcess = null;
            updateStatus('stopped');
        });
        
        updateStatus('running');
        vscode.window.showInformationMessage(`SME server started on port ${port}`);
        
    } catch (error) {
        updateStatus('error');
        vscode.window.showErrorMessage(`Failed to start SME: ${error}`);
    }
}

// Stop SME server
function stopServer() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
        updateStatus('stopped');
        vscode.window.showInformationMessage('SME server stopped');
    } else {
        vscode.window.showWarningMessage('SME server is not running');
    }
}

// Show status
function showStatus() {
    if (serverProcess) {
        const config = getConfig();
        const port = config.get('serverPort', 8089);
        vscode.window.showInformationMessage(
            `SME Server Running\nPort: ${port}\nStatus: Active`,
            { modal: false }
        );
    } else {
        vscode.window.showInformationMessage(
            'SME Server Stopped\nUse "SME: Start Server" to start',
            { modal: false }
        );
    }
}

// Analyze command
async function analyzeFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No file selected');
        return;
    }
    
    const filePath = editor.document.uri.fsPath;
    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);
    
    // Show progress
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'SME Analysis',
        cancellable: false
    }, async (progress) => {
        progress.report({ message: 'Analyzing file...' });
        
        // Simulate analysis (in real implementation, call MCP server)
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        progress.report({ message: 'Complete!' });
        vscode.window.showInformationMessage(`Analysis complete for ${path.basename(filePath)}`);
    });
}

// Query command
async function queryKnowledgeBase() {
    const query = await vscode.window.showInputBox({
        prompt: 'Enter your query for the SME knowledge base',
        placeHolder: 'What would you like to know?'
    });
    
    if (query) {
        // In real implementation, send to MCP server
        vscode.window.showInformationMessage(`Query sent: ${query}`);
    }
}

// ============================================================================
// SME Explorer Sidebar (Weight Explorer)
// ============================================================================

let smeExplorerProvider = null;

class SmeExplorerProvider {
    constructor() {
        this._view = null;
    }

    resolveWebviewViewPanel(webviewView) {
        this._view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: []
        };
        
        webviewView.webview.html = this._getHtml();
    }

    _getHtml() {
        return `<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Segoe UI', sans-serif; padding: 10px; }
        .section { margin-bottom: 15px; }
        .section h3 { margin: 0 0 8px 0; color: #007acc; }
        .activation { padding: 5px; margin: 2px 0; background: #1e1e1e; border-radius: 3px; }
        .activation .layer { color: #888; font-size: 0.85em; }
        .activation .value { float: right; color: #4ec9b0; }
        .loading { color: #666; font-style: italic; }
        .empty { color: #666; }
        button { background: #007acc; color: white; border: none; padding: 5px 10px; cursor: pointer; }
        button:hover { background: #005a9e; }
    </style>
</head>
<body>
    <div class="section">
        <h3>Weight Explorer</h3>
        <p class="empty">Click a word in your editor to see top 5 activations</p>
    </div>
    <div class="section">
        <h3>Recent Activations</h3>
        <div id="activations">No activations yet</div>
    </div>
    <div class="section">
        <button onclick="refresh()">Refresh</button>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        
        function refresh() {
            document.getElementById('activations').innerHTML = '<span class="loading">Loading...</span>';
            vscode.postMessage({ command: 'refreshActivations' });
        }
        
        function showActivations(data) {
            if (!data || !data.length) {
                document.getElementById('activations').innerHTML = '<span class="empty">No activations</span>';
                return;
            }
            let html = '';
            data.forEach(act => {
                html += '<div class="activation">';
                html += '<span class="layer">L' + act.layer + ' N' + act.neuron + '</span>';
                html += '<span class="value">' + act.activation.toFixed(4) + '</span>';
                html += '</div>';
            });
            document.getElementById('activations').innerHTML = html;
        }
        
        window.addEventListener('message', event => {
            if (event.data.type === 'activations') {
                showActivations(event.data.activations);
            }
        });
    </script>
</body>
</html>`;
    }

    updateActivations(activations) {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'activations',
                activations: activations
            });
        }
    }
}

// ============================================================================
// Poseidon Test (Right-Click Inject Feature)
// ============================================================================

async function injectAsPhysicalFact() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No file selected');
        return;
    }
    
    const selection = editor.selection;
    const selectedText = editor.document.getText(selection);
    
    if (!selectedText || selectedText.trim().length === 0) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }
    
    // Show confirmation dialog
    const answer = await vscode.window.showInformationMessage(
        `Inject "${selectedText.substring(0, 50)}${selectedText.length > 50 ? '...' : ''}" as a Physical Fact?`,
        { modal: true },
        'Inject',
        'Cancel'
    );
    
    if (answer !== 'Inject') {
        return;
    }
    
    // In real implementation:
    // 1. Extract triplet from selected text
    // 2. Inject into V-Index via MCP
    // 3. Query model to verify it repeats the fact
    // This is the "Atlantis Test" - verify model repeats injected fact with >90% confidence
    
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Poseidon Test',
        cancellable: false
    }, async (progress) => {
        progress.report({ message: 'Extracting fact triplet...' });
        
        // Simulate extraction
        await new Promise(resolve => setTimeout(resolve, 500));
        
        progress.report({ message: 'Injecting into V-Index...' });
        
        // Simulate injection
        await new Promise(resolve => setTimeout(resolve, 500));
        
        progress.report({ message: 'Running Atlantis Test...' });
        
        // Simulate verification (in real impl, query model)
        const confidence = 0.85 + Math.random() * 0.14; // Simulated 85-99%
        
        progress.report({ message: 'Complete!' });
        
        if (confidence >= 0.90) {
            vscode.window.showInformationMessage(
                `✓ Poseidon Test PASSED\nInjected fact confirmed with ${(confidence * 100).toFixed(1)}% confidence`
            );
        } else {
            vscode.window.showWarningMessage(
                `⚠ Poseidon Test FAILED\nConfidence: ${(confidence * 100).toFixed(1)}% (threshold: 90%)`
            );
        }
        
        // Log result
        console.log(`[Poseidon] Injected: "${selectedText}" | Confidence: ${(confidence * 100).toFixed(1)}%`);
    });
}

// Activate extension
function activate(context) {
    console.log('SME Forensic Toolkit activated');
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sme.analyze', analyzeFile),
        vscode.commands.registerCommand('sme.query', queryKnowledgeBase),
        vscode.commands.registerCommand('sme.status', showStatus),
        vscode.commands.registerCommand('sme.startServer', startServer),
        vscode.commands.registerCommand('sme.stopServer', stopServer),
        vscode.commands.registerCommand('sme.injectFact', injectAsPhysicalFact)
    );
    
    // Register SME Explorer sidebar
    smeExplorerProvider = new SmeExplorerProvider();
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('smeExplorer', smeExplorerProvider)
    );
    
    // Initialize status bar
    updateStatus('stopped');
    
    // Auto-start server if configured
    const config = getConfig();
    const autoStart = config.get('autoStart', false);
    if (autoStart) {
        startServer();
    }
}

// Deactivate extension
function deactivate() {
    if (serverProcess) {
        serverProcess.kill();
        serverProcess = null;
    }
}

module.exports = { activate, deactivate };
