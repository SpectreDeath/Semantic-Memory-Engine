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

// Activate extension
function activate(context) {
    console.log('SME Forensic Toolkit activated');
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sme.analyze', analyzeFile),
        vscode.commands.registerCommand('sme.query', queryKnowledgeBase),
        vscode.commands.registerCommand('sme.status', showStatus),
        vscode.commands.registerCommand('sme.startServer', startServer),
        vscode.commands.registerCommand('sme.stopServer', stopServer)
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
