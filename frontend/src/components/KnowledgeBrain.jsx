import React, { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const KnowledgeBrain = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const containerRef = useRef();

  useEffect(() => {
    // Fetch initial graph data or provide dummy data for preview
    const fetchData = async () => {
        try {
            // In a real scenario, we'd fetch from http://localhost:8000/api/v1/analysis/graph
            // with a default query. For now, let's seed with some interesting dummy items.
            const dummyData = {
                nodes: [
                    { id: '1', name: 'Albert Einstein', val: 10, group: 'PERSON' },
                    { id: '2', name: 'Relativity', val: 8, group: 'CONCEPT' },
                    { id: '3', name: 'Princeton', val: 6, group: 'LOCATION' },
                    { id: '4', name: 'Physics', val: 12, group: 'FIELD' },
                    { id: '5', name: 'Quantum Mechanics', val: 7, group: 'CONCEPT' },
                ],
                links: [
                    { source: '1', target: '2', label: 'developed' },
                    { source: '1', target: '3', label: 'worked at' },
                    { source: '1', target: '4', label: 'practiced' },
                    { source: '2', target: '4', label: 'part of' },
                    { source: '5', target: '4', label: 'part of' },
                ]
            };
            setGraphData(dummyData);
            setLoading(false);
        } catch (err) {
            console.error("Failed to fetch graph:", err);
            setLoading(false);
        }
    };

    fetchData();
  }, []);

  return (
    <div style={{ width: '100%', height: '500px', position: 'relative' }} ref={containerRef}>
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
          <span>Loading Neural Network...</span>
        </div>
      ) : (
        <ForceGraph2D
          graphData={graphData}
          nodeLabel="name"
          nodeAutoColorBy="group"
          linkDirectionalArrowLength={3.5}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.25}
          width={containerRef.current?.clientWidth || 800}
          height={500}
          backgroundColor="rgba(0,0,0,0)"
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Inter`;
            const textWidth = ctx.measureText(label).width;
            const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

            ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
            ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);

            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = node.color;
            ctx.fillText(label, node.x, node.y);

            node.__bckgDimensions = bckgDimensions;
          }}
          nodePointerAreaPaint={(node, color, ctx) => {
            ctx.fillStyle = color;
            const bckgDimensions = node.__bckgDimensions;
            bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, ...bckgDimensions);
          }}
        />
      )}
    </div>
  );
};

export default KnowledgeBrain;
