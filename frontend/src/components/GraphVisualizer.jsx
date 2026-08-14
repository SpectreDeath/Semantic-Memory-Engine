import React, { useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Share2, RefreshCw, Eye } from 'lucide-react';

const INITIAL_DATA = {
  nodes: [
    { id: 'FastMCP Gateway', group: 1, val: 20 },
    { id: 'ForensicNexus (SQLite WAL)', group: 2, val: 15 },
    { id: 'PostgresNexus Pool', group: 2, val: 15 },
    { id: 'Merkle Audit Engine', group: 3, val: 18 },
    { id: 'ED25519 Signature Core', group: 3, val: 12 },
    { id: 'Social Intelligence Crawler', group: 4, val: 14 },
    { id: 'Bluesky Feed Harvester', group: 4, val: 10 },
    { id: 'Telegram OSINT Stream', group: 4, val: 10 },
    { id: 'Cloud Fetcher (Drive/S3)', group: 5, val: 12 },
    { id: 'Kuzu Embedded Graph Engine', group: 5, val: 14 }
  ],
  links: [
    { source: 'FastMCP Gateway', target: 'ForensicNexus (SQLite WAL)' },
    { source: 'FastMCP Gateway', target: 'PostgresNexus Pool' },
    { source: 'FastMCP Gateway', target: 'Merkle Audit Engine' },
    { source: 'Merkle Audit Engine', target: 'ED25519 Signature Core' },
    { source: 'FastMCP Gateway', target: 'Social Intelligence Crawler' },
    { source: 'Social Intelligence Crawler', target: 'Bluesky Feed Harvester' },
    { source: 'Social Intelligence Crawler', target: 'Telegram OSINT Stream' },
    { source: 'FastMCP Gateway', target: 'Cloud Fetcher (Drive/S3)' },
    { source: 'FastMCP Gateway', target: 'Kuzu Embedded Graph Engine' },
    { source: 'Social Intelligence Crawler', target: 'Kuzu Embedded Graph Engine' }
  ]
};

export default function GraphVisualizer() {
  const [graphData, setGraphData] = useState(INITIAL_DATA);
  const [selectedNode, setSelectedNode] = useState(null);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const handleReset = () => {
    setSelectedNode(null);
    setGraphData({ ...INITIAL_DATA });
  };

  return (
    <div className="glass-panel p-6 rounded-xl relative overflow-hidden bg-slate-900/60 border border-slate-800 text-white shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/30 rounded-lg border border-indigo-500/40 text-indigo-400">
            <Share2 size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-slate-100">Interactive Knowledge Graph</h3>
            <p className="text-xs text-slate-400">Dynamic 2D force-directed topology of forensic entities & Merkle nodes</p>
          </div>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition border border-slate-700"
        >
          <RefreshCw size={14} />
          <span>Reset Layout</span>
        </button>
      </div>

      <div className="h-[380px] w-full rounded-lg border border-slate-800 bg-slate-950/80 relative overflow-hidden">
        <ForceGraph2D
          graphData={graphData}
          nodeAutoColorBy="group"
          nodeRelSize={6}
          linkWidth={1.5}
          linkColor={() => '#334155'}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.id;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Inter, sans-serif`;

            ctx.fillStyle = node.id === selectedNode?.id ? '#6366f1' : '#1e293b';
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.val / 2.5, 0, 2 * Math.PI, false);
            ctx.fill();
            ctx.strokeStyle = node.id === selectedNode?.id ? '#818cf8' : '#475569';
            ctx.lineWidth = 1.5 / globalScale;
            ctx.stroke();

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#f8fafc';
            ctx.fillText(label, node.x, node.y + (node.val / 2.5) + fontSize);
          }}
          onNodeClick={handleNodeClick}
        />
      </div>

      {selectedNode && (
        <div className="mt-4 p-4 rounded-lg bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Eye className="text-indigo-400" size={18} />
            <div>
              <span className="text-xs text-indigo-300 uppercase tracking-wider font-semibold">Active Node</span>
              <h4 className="text-sm font-bold text-white">{selectedNode.id}</h4>
            </div>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-indigo-900/60 border border-indigo-400/30 text-indigo-200">
            Cluster {selectedNode.group}
          </span>
        </div>
      )}
    </div>
  );
}
