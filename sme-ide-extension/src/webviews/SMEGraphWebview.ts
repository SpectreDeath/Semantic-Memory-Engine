import * as vscode from "vscode";
import { SMEBridgeClient } from "../bridge/SMEBridgeClient";

export class SMEGraphWebview {
  public static readonly viewType = "smeGraphView";
  private panel: vscode.WebviewPanel | undefined;

  constructor(
    private context: vscode.ExtensionContext,
    private bridge: SMEBridgeClient,
  ) {}

  public async show() {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.One);
    } else {
      this.panel = vscode.window.createWebviewPanel(
        SMEGraphWebview.viewType,
        "SME Relationship Graph",
        vscode.ViewColumn.One,
        {
          enableScripts: true,
          retainContextWhenHidden: true,
        },
      );

      this.panel.onDidDispose(() => {
        this.panel = undefined;
      });

      this.update();
    }
  }

  private async update() {
    if (!this.panel) return;

    try {
      const graphData = await this.bridge.sendRequest("get_semantic_graph");
      this.panel.webview.html = this.getHtmlContent(graphData);
    } catch (e) {
      console.error("Failed to fetch graph data:", e);
      this.panel.webview.html = `<h1>Error loading graph</h1><p>${e}</p>`;
    }
  }

  private getHtmlContent(data: any): string {
    const jsonData = JSON.stringify(data);
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SME React Force Graph</title>
    
    <!-- React 19 (rc) -->
    <script crossorigin src="https://unpkg.com/react@19.0.0-rc.1/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@19.0.0-rc.1/umd/react-dom.production.min.js"></script>
    
    <!-- Babel for JSX -->
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    
    <!-- React Force Graph 2D -->
    <script src="https://unpkg.com/react-force-graph-2d"></script>
    
    <style>
        body { margin: 0; background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; overflow: hidden; }
        #root { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect, useRef, useMemo, useCallback } = React;
        const ForceGraph2D = reactForceGraph2d.ForceGraph2D;

        const initialData = ${jsonData};

        function App() {
            const [graphData, setGraphData] = useState(initialData);
            const fgRef = useRef();

            // Handle window resize dynamically
            const [dimensions, setDimensions] = useState({
                width: window.innerWidth,
                height: window.innerHeight
            });

            useEffect(() => {
                const handleResize = () => {
                    setDimensions({
                        width: window.innerWidth,
                        height: window.innerHeight
                    });
                };
                window.addEventListener('resize', handleResize);
                return () => window.removeEventListener('resize', handleResize);
            }, []);

            const handleNodeClick = useCallback(node => {
                // Aim at node from outside it
                const distance = 40;
                const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z || 0);

                fgRef.current.centerAt(node.x, node.y, 1000);
                fgRef.current.zoom(8, 2000);
            }, [fgRef]);

            return (
                <ForceGraph2D
                    ref={fgRef}
                    width={dimensions.width}
                    height={dimensions.height}
                    graphData={graphData}
                    nodeLabel="label"
                    nodeColor={node => {
                        // Color styling based on group or trust score
                        const colors = ['#3fb950', '#d29922', '#f85149', '#58a6ff', '#bc8cff'];
                        return colors[node.group % colors.length] || '#8b949e';
                    }}
                    nodeRelSize={6}
                    linkColor={() => 'rgba(255,255,255,0.2)'}
                    linkWidth={link => Math.sqrt(link.value || 1)}
                    onNodeClick={handleNodeClick}
                    backgroundColor="#0d1117"
                />
            );
        }

        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<App />);
    </script>
</body>
</html>`;
  }
}
