"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
const path = require("path");
const SMEExplorerProvider_1 = require("./views/SMEExplorerProvider");
const SMEFileSystemProvider_1 = require("./providers/SMEFileSystemProvider");
const SMEBridgeClient_1 = require("./bridge/SMEBridgeClient");
const ForensicController_1 = require("./forensics/ForensicController");
const ForensicCodeLensProvider_1 = require("./forensics/ForensicCodeLensProvider");
const SMEGraphWebview_1 = require("./webviews/SMEGraphWebview");
const SMESearchView_1 = require("./webviews/SMESearchView");
function activate(context) {
    console.log('SME IDE Engine is now active');
    // 0. Initialize Bridge Client
    const pythonPath = 'python'; // Should be configurable via settings
    const scriptPath = path.join(context.extensionPath, '..', 'src', 'ai', 'bridge_rpc.py');
    const bridge = new SMEBridgeClient_1.SMEBridgeClient(pythonPath, scriptPath);
    bridge.start();
    // 0.1 Initialize Forensic Components
    const forensicController = new ForensicController_1.ForensicController(bridge);
    const codeLensProvider = new ForensicCodeLensProvider_1.ForensicCodeLensProvider(bridge);
    const graphWebview = new SMEGraphWebview_1.SMEGraphWebview(context, bridge);
    const searchViewProvider = new SMESearchView_1.SMESearchView(bridge);
    context.subscriptions.push(forensicController);
    // 0.2 Register Search View
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(SMESearchView_1.SMESearchView.viewType, searchViewProvider));
    // 1. Register Explorer Sidebar
    const smeExplorerProvider = new SMEExplorerProvider_1.SMEExplorerProvider(bridge);
    vscode.window.registerTreeDataProvider('smeMemoryNodes', smeExplorerProvider);
    // 2. Register Virtual File System
    const smeFileSystemProvider = new SMEFileSystemProvider_1.SMEFileSystemProvider(bridge);
    context.subscriptions.push(vscode.workspace.registerFileSystemProvider('sme', smeFileSystemProvider, {
        isCaseSensitive: true,
        isReadonly: true
    }));
    // 3. Register Providers, Commands & Listeners
    context.subscriptions.push(vscode.languages.registerCodeLensProvider({ scheme: 'file' }, codeLensProvider), vscode.languages.registerCodeLensProvider({ scheme: 'sme' }, codeLensProvider));
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument((doc) => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document === doc) {
            forensicController.analyzeEditor(editor);
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('sme-ide.showGraph', () => {
        graphWebview.show();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('sme-ide.inspectEntity', (entity) => {
        vscode.window.showInformationMessage(`Inspecting forensic entity: ${entity}`);
        // Future: Open semantic graph or details view for this entity
    }));
    // Analyze active editor on start
    if (vscode.window.activeTextEditor) {
        forensicController.analyzeEditor(vscode.window.activeTextEditor);
    }
    context.subscriptions.push(vscode.commands.registerCommand('sme-ide.indexMemory', async () => {
        const folder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (folder) {
            vscode.window.showInformationMessage(`Indexing project memory at ${folder}...`);
            try {
                await bridge.sendRequest('index_project', { path: folder });
                vscode.window.showInformationMessage('Indexing complete.');
            }
            catch (e) {
                vscode.window.showErrorMessage(`Indexing failed: ${e}`);
            }
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('sme-ide.retrieveMemory', async () => {
        const query = await vscode.window.showInputBox({ prompt: 'Search Semantic Memory' });
        if (query) {
            try {
                const results = await bridge.sendRequest('search_memory', { query });
                vscode.window.showInformationMessage(`Found ${results.length} results for: ${query}`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`Search failed: ${e}`);
            }
        }
    }));
    context.subscriptions.push({
        dispose: () => bridge.stop()
    });
}
function deactivate() { }
//# sourceMappingURL=extension.js.map