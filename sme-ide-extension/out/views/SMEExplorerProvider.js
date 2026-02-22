"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SMEExplorerProvider = void 0;
const vscode = require("vscode");
class SMEExplorerProvider {
    constructor(bridge) {
        this.bridge = bridge;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    async getChildren(element) {
        if (element) {
            return [];
        }
        else {
            try {
                const nodes = await this.bridge.sendRequest('get_memory_nodes');
                return nodes.map((n) => new MemoryNode(n.label || n.id, n.type || 'node', vscode.TreeItemCollapsibleState.None));
            }
            catch (e) {
                console.error('Error fetching memory nodes:', e);
                return [new MemoryNode('Error fetching nodes', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        }
    }
}
exports.SMEExplorerProvider = SMEExplorerProvider;
class MemoryNode extends vscode.TreeItem {
    constructor(label, nodeType, collapsibleState) {
        super(label, collapsibleState);
        this.label = label;
        this.nodeType = nodeType;
        this.collapsibleState = collapsibleState;
        this.tooltip = `${this.label} (${this.nodeType})`;
        this.description = this.nodeType;
        this.contextValue = 'memoryNode';
        // Use a themed icon
        this.iconPath = new vscode.ThemeIcon(this.getIcon());
    }
    getIcon() {
        switch (this.nodeType) {
            case 'context': return 'brain';
            case 'document': return 'file-text';
            case 'fingerprint': return 'fingerprint';
            default: return 'database';
        }
    }
}
//# sourceMappingURL=SMEExplorerProvider.js.map