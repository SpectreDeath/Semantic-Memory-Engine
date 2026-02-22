"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ForensicCodeLensProvider = void 0;
const vscode = require("vscode");
class ForensicCodeLensProvider {
    constructor(bridge) {
        this.bridge = bridge;
        this._onDidChangeCodeLenses = new vscode.EventEmitter();
        this.onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    }
    provideCodeLenses(document, token) {
        // Only provide lenses for relevant files
        if (document.uri.scheme !== 'file' && document.uri.scheme !== 'sme') {
            return [];
        }
        const lenses = [];
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
    async resolveCodeLens(codeLens, token) {
        // We can further enrich the lens here if needed
        return codeLens;
    }
}
exports.ForensicCodeLensProvider = ForensicCodeLensProvider;
//# sourceMappingURL=ForensicCodeLensProvider.js.map