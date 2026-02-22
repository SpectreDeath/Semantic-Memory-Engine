"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ForensicController = void 0;
const vscode = require("vscode");
class ForensicController {
    constructor(bridge) {
        this.bridge = bridge;
        this.decorationTypes = new Map();
        this.activeDecorations = new Map();
        this.initDecorations();
    }
    initDecorations() {
        // Ghost Gutter: High Burstiness (Purple/Magenta)
        this.decorationTypes.set('high_burstiness', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 255, 0.1)',
            gutterIconPath: vscode.Uri.parse('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><circle cx="8" cy="8" r="4" fill="%23ff00ff" /></svg>'),
            gutterIconSize: 'contain',
            overviewRulerColor: 'magenta',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
        }));
        // Styling Outlier (Orange)
        this.decorationTypes.set('styling_outlier', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 165, 0, 0.1)',
            gutterIconPath: vscode.Uri.parse('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect x="4" y="4" width="8" height="8" fill="%23ffa500" /></svg>'),
            gutterIconSize: 'contain',
            overviewRulerColor: 'orange',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
        }));
        // Low Entropy (Red)
        this.decorationTypes.set('high_entropy', vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 0, 0.1)',
            border: '1px solid rgba(255, 0, 0, 0.3)',
            overviewRulerColor: 'red',
            overviewRulerLane: vscode.OverviewRulerLane.Right,
        }));
    }
    async analyzeEditor(editor) {
        const doc = editor.document;
        console.log(`Analyzing document: ${doc.uri.fsPath}`);
        try {
            const results = await this.bridge.sendRequest('analyze_document', { path: doc.uri.fsPath });
            this.applyMarkers(editor, results.markers);
        }
        catch (e) {
            console.error('Forensic analysis failed:', e);
        }
    }
    applyMarkers(editor, markers) {
        // Clear previous decorations
        this.decorationTypes.forEach(dt => editor.setDecorations(dt, []));
        const markerGroups = new Map();
        for (const marker of markers) {
            const range = new vscode.Range(marker.line - 1, 0, marker.line - 1, editor.document.lineAt(marker.line - 1).text.length);
            const decoration = {
                range,
                hoverMessage: `**SME Forensic Alert**\n\n- Type: ${marker.type}\n- Score: ${marker.score}\n- Insight: ${marker.message}`
            };
            if (!markerGroups.has(marker.type)) {
                markerGroups.set(marker.type, []);
            }
            markerGroups.get(marker.type).push(decoration);
        }
        markerGroups.forEach((decorations, type) => {
            const dt = this.decorationTypes.get(type);
            if (dt) {
                editor.setDecorations(dt, decorations);
            }
        });
    }
    dispose() {
        this.decorationTypes.forEach(dt => dt.dispose());
    }
}
exports.ForensicController = ForensicController;
//# sourceMappingURL=ForensicController.js.map