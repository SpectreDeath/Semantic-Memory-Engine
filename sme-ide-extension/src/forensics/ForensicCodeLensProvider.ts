import * as vscode from 'vscode';
import { SMEBridgeClient } from '../bridge/SMEBridgeClient';

export class ForensicCodeLensProvider implements vscode.CodeLensProvider {
    private _onDidChangeCodeLenses: vscode.EventEmitter<void> = new vscode.EventEmitter<void>();
    public readonly onDidChangeCodeLenses: vscode.Event<void> = this._onDidChangeCodeLenses.event;

    constructor(private bridge: SMEBridgeClient) {}

    public provideCodeLenses(document: vscode.TextDocument, token: vscode.CancellationToken): vscode.CodeLens[] | Thenable<vscode.CodeLens[]> {
        // Only provide lenses for relevant files
        if (document.uri.scheme !== 'file' && document.uri.scheme !== 'sme') {
            return [];
        }

        const lenses: vscode.CodeLens[] = [];
        const text = document.getText();
        
        // Simulating entity extraction for CodeLens
        // In a real scenario, we'd use the bridge to get entities for the whole file
        const lines = text.split('\n');
        lines.forEach((line, index) => {
            if (line.includes('spectre') || line.includes('Ollama') || line.includes('SME')) {
                const range = new vscode.Range(index, 0, index, 0);
                lenses.push(new vscode.CodeLens(range, {
                    title: "🔍 Inspect Entity",
                    command: "sme-ide.inspectEntity",
                    arguments: [line.match(/spectre|Ollama|SME/)?.[0]]
                }));
            }
        });

        return lenses;
    }

    public async resolveCodeLens(codeLens: vscode.CodeLens, token: vscode.CancellationToken): Promise<vscode.CodeLens> {
        // We can further enrich the lens here if needed
        return codeLens;
    }
}
