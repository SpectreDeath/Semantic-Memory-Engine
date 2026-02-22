"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SMEGraphWebview = void 0;
const vscode = require("vscode");
class SMEGraphWebview {
    constructor(context, bridge) {
        this.context = context;
        this.bridge = bridge;
    }
    async show() {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.One);
        }
        else {
            this.panel = vscode.window.createWebviewPanel(SMEGraphWebview.viewType, 'SME Relationship Graph', vscode.ViewColumn.One, {
                enableScripts: true,
                retainContextWhenHidden: true
            });
            this.panel.onDidDispose(() => {
                this.panel = undefined;
            });
            this.update();
        }
    }
    async update() {
        if (!this.panel)
            return;
        try {
            const graphData = await this.bridge.sendRequest('get_semantic_graph');
            this.panel.webview.html = this.getHtmlContent(graphData);
        }
        catch (e) {
            console.error('Failed to fetch graph data:', e);
            this.panel.webview.html = `<h1>Error loading graph</h1><p>${e}</p>`;
        }
    }
    getHtmlContent(data) {
        const jsonData = JSON.stringify(data);
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SME Relationship Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body { margin: 0; background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; overflow: hidden; }
        #graph { width: 100vw; height: 100vh; }
        .node { stroke: #fff; stroke-width: 1.5px; cursor: pointer; }
        .link { stroke: #444; stroke-opacity: 0.6; }
        .label { font-size: 10px; fill: #8b949e; pointer-events: none; }
        .tooltip { position: absolute; background: rgba(22, 27, 34, 0.9); border: 1px solid #30363d; padding: 10px; border-radius: 6px; pointer-events: none; opacity: 0; transition: opacity 0.2s; font-size: 12px; }
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="tooltip" class="tooltip"></div>
    <script>
        const data = ${jsonData};
        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {
                container.attr("transform", event.transform);
            }));

        const container = svg.append("g");

        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = container.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.sqrt(d.value));

        const color = d3.scaleOrdinal(d3.schemeCategory10);

        const node = container.append("g")
            .selectAll("circle")
            .data(data.nodes)
            .join("circle")
            .attr("class", "node")
            .attr("r", d => d.size || 5)
            .attr("fill", d => color(d.group))
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        const label = container.append("g")
            .selectAll("text")
            .data(data.nodes)
            .join("text")
            .attr("class", "label")
            .text(d => d.label);

        node.on("mouseover", (event, d) => {
            d3.select("#tooltip")
                .style("opacity", 1)
                .html(\`<strong>Node:</strong> \${d.label}<br><strong>ID:</strong> \${d.id}\`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", () => {
            d3.select("#tooltip").style("opacity", 0);
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            label
                .attr("x", d => d.x + 8)
                .attr("y", d => d.y + 4);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        window.addEventListener('resize', () => {
            svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
        });
    </script>
</body>
</html>`;
    }
}
exports.SMEGraphWebview = SMEGraphWebview;
SMEGraphWebview.viewType = 'smeGraphView';
//# sourceMappingURL=SMEGraphWebview.js.map