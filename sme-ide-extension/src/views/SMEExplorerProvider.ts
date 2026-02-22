import * as vscode from 'vscode';
import { SMEBridgeClient } from '../bridge/SMEBridgeClient';

export class SMEExplorerProvider implements vscode.TreeDataProvider<MemoryNode> {
    private _onDidChangeTreeData: vscode.EventEmitter<MemoryNode | undefined | void> = new vscode.EventEmitter<MemoryNode | undefined | void>();
    readonly onDidChangeTreeData: vscode.Event<MemoryNode | undefined | void> = this._onDidChangeTreeData.event;

    constructor(private bridge: SMEBridgeClient) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: MemoryNode): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: MemoryNode): Promise<MemoryNode[]> {
        if (element) {
            return [];
        } else {
            try {
                const nodes = await this.bridge.sendRequest('get_memory_nodes');
                return nodes.map((n: any) => new MemoryNode(
                    n.label || n.id, 
                    n.type || 'node', 
                    vscode.TreeItemCollapsibleState.None
                ));
            } catch (e) {
                console.error('Error fetching memory nodes:', e);
                return [new MemoryNode('Error fetching nodes', 'error', vscode.TreeItemCollapsibleState.None)];
            }
        }
    }
}

class MemoryNode extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        private readonly nodeType: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label} (${this.nodeType})`;
        this.description = this.nodeType;
        this.contextValue = 'memoryNode';
        
        // Use a themed icon
        this.iconPath = new vscode.ThemeIcon(this.getIcon());
    }

    private getIcon(): string {
        switch (this.nodeType) {
            case 'context': return 'brain';
            case 'document': return 'file-text';
            case 'fingerprint': return 'fingerprint';
            default: return 'database';
        }
    }
}
