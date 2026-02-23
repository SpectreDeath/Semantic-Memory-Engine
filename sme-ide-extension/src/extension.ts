import * as vscode from 'vscode';
import * as path from 'path';
import { SMEExplorerProvider } from './views/SMEExplorerProvider';
import { SMEFileSystemProvider } from './providers/SMEFileSystemProvider';
import { SMEBridgeClient } from './bridge/SMEBridgeClient';
import { ForensicController } from './forensics/ForensicController';
import { ForensicCodeLensProvider } from './forensics/ForensicCodeLensProvider';
import { SMEGraphWebview } from './webviews/SMEGraphWebview';
import { SMESearchView } from './webviews/SMESearchView';
// @ts-ignore
import { enableHotReload } from '@hediet/node-reload';

// 1. Evolutionary Hot-Reloading Support
if (process.env.NODE_ENV !== 'production') {
    enableHotReload({ entryModule: module });
}

export function activate(context: vscode.ExtensionContext) {
    console.log('SME IDE Engine is now active');

    // 0. Initialize Bridge Client
    const pythonPath = 'python'; // Should be configurable via settings
    const scriptPath = path.join(context.extensionPath, '..', 'src', 'ai', 'bridge_rpc.py');
    const bridge = new SMEBridgeClient(pythonPath, scriptPath);
    bridge.start();

    // 0.1 Initialize Forensic Components
    const forensicController = new ForensicController(bridge);
    const codeLensProvider = new ForensicCodeLensProvider(bridge);
    const graphWebview = new SMEGraphWebview(context, bridge);
    const searchViewProvider = new SMESearchView(bridge);
    context.subscriptions.push(forensicController);

    // 0.2 Register Search View
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(SMESearchView.viewType, searchViewProvider)
    );

    // 1. Register Explorer Sidebar
    const smeExplorerProvider = new SMEExplorerProvider(bridge);
    vscode.window.registerTreeDataProvider('smeMemoryNodes', smeExplorerProvider);

    // 2. Register Virtual File System
    const smeFileSystemProvider = new SMEFileSystemProvider(bridge);
    context.subscriptions.push(
        vscode.workspace.registerFileSystemProvider('sme', smeFileSystemProvider, { 
            isCaseSensitive: true,
            isReadonly: true 
        })
    );

    // 3. Register Providers, Commands & Listeners
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider({ scheme: 'file' }, codeLensProvider),
        vscode.languages.registerCodeLensProvider({ scheme: 'sme' }, codeLensProvider)
    );

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc: vscode.TextDocument) => {
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document === doc) {
                forensicController.analyzeEditor(editor);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sme-ide.showGraph', () => {
            graphWebview.show();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sme-ide.inspectEntity', async (entity: string) => {
            vscode.window.showInformationMessage(`Inspecting forensic entity: ${entity}`);
            
            // Evolutionary Loop: Log trace to Nexus
            try {
                await bridge.sendRequest('log_telemetry', { 
                    action: 'inspect_entity', 
                    target: entity,
                    context: 'graph_view'
                });
            } catch (e) {
                console.warn('Telemetry sync failed:', e);
            }
        })
    );

    // Analyze active editor on start
    if (vscode.window.activeTextEditor) {
        forensicController.analyzeEditor(vscode.window.activeTextEditor);
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('sme-ide.indexMemory', async () => {
            const folder = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
            if (folder) {
                vscode.window.showInformationMessage(`Indexing project memory at ${folder}...`);
                try {
                    await bridge.sendRequest('index_project', { path: folder });
                    vscode.window.showInformationMessage('Indexing complete.');
                } catch (e) {
                    vscode.window.showErrorMessage(`Indexing failed: ${e}`);
                }
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sme-ide.retrieveMemory', async () => {
            const query = await vscode.window.showInputBox({ prompt: 'Search Semantic Memory' });
            if (query) {
                try {
                    const results = await bridge.sendRequest('search_memory', { query });
                    vscode.window.showInformationMessage(`Found ${results.length} results for: ${query}`);
                    
                    // Evolutionary Loop: Log search trace to Nexus
                    await bridge.sendRequest('log_telemetry', { 
                        action: 'search_memory', 
                        query: query,
                        results_count: results.length
                    });
                } catch (e) {
                    vscode.window.showErrorMessage(`Search failed: ${e}`);
                }
            }
        })
    );

    context.subscriptions.push({
        dispose: () => bridge.stop()
    });
}

export function deactivate() {}
