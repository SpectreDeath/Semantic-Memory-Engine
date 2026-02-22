import * as vscode from 'vscode';
import { SMEBridgeClient } from '../bridge/SMEBridgeClient';

export class SMESearchView implements vscode.WebviewViewProvider {
    public static readonly viewType = 'smeSearchView';
    private _view?: vscode.WebviewView;

    constructor(private bridge: SMEBridgeClient) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'search':
                    const results = await this.bridge.sendRequest('search_memory', { query: data.value });
                    webviewView.webview.postMessage({ type: 'results', value: results });
                    break;
            }
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        body { padding: 10px; color: var(--vscode-foreground); font-family: var(--vscode-font-family); }
        input { width: 100%; box-sizing: border-box; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); padding: 5px; margin-bottom: 10px; }
        .result { padding: 5px; border-bottom: 1px solid var(--vscode-widget-shadow); cursor: pointer; }
        .result:hover { background: var(--vscode-list-hoverBackground); }
    </style>
</head>
<body>
    <input type="text" id="searchInput" placeholder="Search Semantic Memory..." />
    <div id="results"></div>
    <script>
        const vscode = acquireVsCodeApi();
        const input = document.getElementById('searchInput');
        const resultsDiv = document.getElementById('results');

        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                vscode.postMessage({ type: 'search', value: input.value });
            }
        });

        window.addEventListener('message', event => {
            const message = event.data;
            if (message.type === 'results') {
                resultsDiv.innerHTML = message.value.map(r => \`<div class="result">\${r.text}</div>\`).join('');
            }
        });
    </script>
</body>
</html>`;
    }
}
