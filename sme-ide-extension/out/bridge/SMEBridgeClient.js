"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SMEBridgeClient = void 0;
const cp = require("child_process");
class SMEBridgeClient {
    constructor(pythonPath, scriptPath) {
        this.pythonPath = pythonPath;
        this.scriptPath = scriptPath;
        this.process = null;
        this.requestId = 0;
        this.callbacks = new Map();
    }
    start() {
        console.log(`Starting SME Bridge: ${this.pythonPath} ${this.scriptPath}`);
        this.process = cp.spawn(this.pythonPath, [this.scriptPath]);
        this.process.stdout?.on('data', (data) => {
            const lines = data.toString().split('\n');
            for (const line of lines) {
                if (!line.trim())
                    continue;
                try {
                    const response = JSON.parse(line);
                    if (response.id !== undefined) {
                        const callback = this.callbacks.get(response.id);
                        if (callback) {
                            callback(response);
                            this.callbacks.delete(response.id);
                        }
                    }
                }
                catch (e) {
                    console.error('Failed to parse bridge response:', e);
                }
            }
        });
        this.process.stderr?.on('data', (data) => {
            console.error(`Bridge Stream Error: ${data.toString()}`);
        });
        this.process.on('close', (code) => {
            console.log(`Bridge process exited with code ${code}`);
        });
    }
    async sendRequest(method, params = {}) {
        return new Promise((resolve, reject) => {
            if (!this.process) {
                return reject(new Error('Bridge process not started'));
            }
            const id = ++this.requestId;
            const request = {
                jsonrpc: "2.0",
                method,
                params,
                id
            };
            this.callbacks.set(id, (response) => {
                if (response.error) {
                    reject(new Error(response.error.message));
                }
                else {
                    resolve(response.result);
                }
            });
            this.process.stdin?.write(JSON.stringify(request) + '\n');
        });
    }
    stop() {
        this.process?.kill();
        this.process = null;
    }
}
exports.SMEBridgeClient = SMEBridgeClient;
//# sourceMappingURL=SMEBridgeClient.js.map