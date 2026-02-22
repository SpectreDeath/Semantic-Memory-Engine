"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SMESearchView = void 0;
class SMESearchView {
    constructor(bridge) {
        this.bridge = bridge;
    }
    resolveWebviewView(webviewView, context, _token) {
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
    _getHtmlForWebview(webview) {
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
exports.SMESearchView = SMESearchView;
SMESearchView.viewType = 'smeSearchView';
//# sourceMappingURL=SMESearchView.js.map