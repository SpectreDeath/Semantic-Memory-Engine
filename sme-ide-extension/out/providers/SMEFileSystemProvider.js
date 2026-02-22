"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SMEFileSystemProvider = void 0;
const vscode = require("vscode");
const vscode_1 = require("vscode");
class SMEFileSystemProvider {
    constructor(bridge) {
        this.bridge = bridge;
        this._onDidChangeFile = new vscode_1.EventEmitter();
        this.onDidChangeFile = this._onDidChangeFile.event;
    }
    watch(_uri, _options) {
        return new vscode.Disposable(() => { });
    }
    async stat(uri) {
        // Derived stat logic: folders are root or cluster-level (depth < 2 in path parts)
        const parts = uri.path.split('/').filter(p => p.length > 0);
        const isDirectory = parts.length < 2;
        return {
            type: isDirectory ? vscode_1.FileType.Directory : vscode_1.FileType.File,
            ctime: Date.now(),
            mtime: Date.now(),
            size: isDirectory ? 0 : 1024 // Default size for virtual files
        };
    }
    async readDirectory(uri) {
        try {
            const results = await this.bridge.sendRequest('read_directory', { path: uri.path });
            return results.map(([name, type]) => [name, type]);
        }
        catch (e) {
            console.error(`Error reading directory ${uri.path}:`, e);
            return [];
        }
    }
    createDirectory(_uri) {
        throw vscode.FileSystemError.NoPermissions();
    }
    async readFile(uri) {
        try {
            const result = await this.bridge.sendRequest('read_file', { path: uri.path });
            const content = result.content || JSON.stringify(result, null, 2);
            return Buffer.from(content);
        }
        catch (e) {
            console.error(`Error reading file ${uri.path}:`, e);
            throw vscode.FileSystemError.FileNotFound(uri);
        }
    }
    writeFile(_uri, _content, _options) {
        throw vscode.FileSystemError.NoPermissions();
    }
    delete(_uri, _options) {
        throw vscode.FileSystemError.NoPermissions();
    }
    rename(_oldUri, _newUri, _options) {
        throw vscode.FileSystemError.NoPermissions();
    }
}
exports.SMEFileSystemProvider = SMEFileSystemProvider;
//# sourceMappingURL=SMEFileSystemProvider.js.map