import * as vscode from 'vscode';
import { EventEmitter, FileChangeEvent, FileStat, FileType, Uri } from 'vscode';
import { SMEBridgeClient } from '../bridge/SMEBridgeClient';

export class SMEFileSystemProvider implements vscode.FileSystemProvider {
    private _onDidChangeFile = new EventEmitter<FileChangeEvent[]>();
    readonly onDidChangeFile = this._onDidChangeFile.event;

    constructor(private bridge: SMEBridgeClient) {}

    watch(_uri: Uri, _options: { recursive: boolean; excludes: string[] }): vscode.Disposable {
        return new vscode.Disposable(() => {});
    }

    async stat(uri: Uri): Promise<FileStat> {
        // Derived stat logic: folders are root or cluster-level (depth < 2 in path parts)
        const parts = uri.path.split('/').filter(p => p.length > 0);
        const isDirectory = parts.length < 2;
        
        return {
            type: isDirectory ? FileType.Directory : FileType.File,
            ctime: Date.now(),
            mtime: Date.now(),
            size: isDirectory ? 0 : 1024 // Default size for virtual files
        };
    }

    async readDirectory(uri: Uri): Promise<[string, FileType][]> {
        try {
            const results = await this.bridge.sendRequest('read_directory', { path: uri.path });
            return results.map(([name, type]: [string, number]) => [name, type as FileType]);
        } catch (e) {
            console.error(`Error reading directory ${uri.path}:`, e);
            return [];
        }
    }

    createDirectory(_uri: Uri): void {
        throw vscode.FileSystemError.NoPermissions();
    }

    async readFile(uri: Uri): Promise<Uint8Array> {
        try {
            const result = await this.bridge.sendRequest('read_file', { path: uri.path });
            const content = result.content || JSON.stringify(result, null, 2);
            return Buffer.from(content);
        } catch (e) {
            console.error(`Error reading file ${uri.path}:`, e);
            throw vscode.FileSystemError.FileNotFound(uri);
        }
    }

    writeFile(_uri: Uri, _content: Uint8Array, _options: { create: boolean; overwrite: boolean }): void {
        throw vscode.FileSystemError.NoPermissions();
    }

    delete(_uri: Uri, _options: { recursive: boolean }): void {
        throw vscode.FileSystemError.NoPermissions();
    }

    rename(_oldUri: Uri, _newUri: Uri, _options: { overwrite: boolean }): void {
        throw vscode.FileSystemError.NoPermissions();
    }
}
