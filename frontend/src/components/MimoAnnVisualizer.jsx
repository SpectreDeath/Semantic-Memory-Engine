import React, { useState } from 'react';

export default function MimoAnnVisualizer({ mimoData, annData, onTriggerBackprop }) {
  const [d1Triplets, setD1Triplets] = useState(mimoData?.d1_context_max_triplets || 10);
  const [d2Timeout, setD2Timeout] = useState(mimoData?.d2_tool_timeout || 30);
  const [d3Temp, setD3Temp] = useState(mimoData?.d3_decoding_temperature || 0.2);
  const [d4Mode, setD4Mode] = useState(mimoData?.d4_routing_mode || 'auto');
  const [d5Persistence, setD5Persistence] = useState(mimoData?.d5_persistence_enabled ?? true);
  const [d6Schema, setD6Schema] = useState(mimoData?.d6_enforce_json_schema ?? true);

  const [backpropStatus, setBackpropStatus] = useState(null);

  const handleRunBackprop = async () => {
    setBackpropStatus('Running ∇text Backpropagation...');
    try {
      const res = await fetch('/api/v1/ann/backprop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layer_index: 1, target_objective: 'graph_synthesis' }),
      });
      const data = await res.json();
      setBackpropStatus(`Backprop Complete! Loss: ${data.global_gradient?.loss_score || 0.0}`);
      if (onTriggerBackprop) onTriggerBackprop(data);
    } catch (err) {
      setBackpropStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: '20px', background: 'rgba(15, 23, 42, 0.8)', borderRadius: '12px', color: '#e2e8f0', fontFamily: 'sans-serif' }}>
      <h3 style={{ color: '#38bdf8', marginTop: 0 }}>🎛️ MIMO 6D Control Surface & ANN Visualizer</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        {/* D1 Context Assembly */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>D1: Context Max Triplets</label>
          <input type="range" min="1" max="50" value={d1Triplets} onChange={(e) => setD1Triplets(Number(e.target.value))} style={{ width: '100%' }} />
          <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{d1Triplets} triplets</span>
        </div>

        {/* D2 Tool Interaction */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>D2: Tool Timeout (sec)</label>
          <input type="range" min="5" max="120" value={d2Timeout} onChange={(e) => setD2Timeout(Number(e.target.value))} style={{ width: '100%' }} />
          <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{d2Timeout}s</span>
        </div>

        {/* D3 Generation Controls */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>D3: Temperature</label>
          <input type="range" min="0" max="1" step="0.05" value={d3Temp} onChange={(e) => setD3Temp(Number(e.target.value))} style={{ width: '100%' }} />
          <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{d3Temp}</span>
        </div>

        {/* D4 Workflow Topology */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8' }}>D4: Routing Policy</label>
          <select value={d4Mode} onChange={(e) => setD4Mode(e.target.value)} style={{ width: '100%', background: '#0f172a', color: '#fff', padding: '4px', borderRadius: '4px' }}>
            <option value="auto">Auto Balance</option>
            <option value="local_only">Local SME Only</option>
            <option value="em_cubed_workflow">em-cubed DAG</option>
          </select>
        </div>

        {/* D5 Memory Management */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>D5: Persistence</span>
          <input type="checkbox" checked={d5Persistence} onChange={(e) => setD5Persistence(e.target.checked)} />
        </div>

        {/* D6 Output Processing */}
        <div style={{ background: '#1e293b', padding: '12px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>D6: JSON Schema</span>
          <input type="checkbox" checked={d6Schema} onChange={(e) => setD6Schema(e.target.checked)} />
        </div>
      </div>

      {/* ANN Self-Evolving Training Loop Section */}
      <div style={{ borderTop: '1px solid #334155', paddingTop: '16px' }}>
        <h4 style={{ color: '#4ade80', margin: '0 0 12px 0' }}>🧬 Agentic Neural Network (ANN) Candidate Pools</h4>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '13px', color: '#cbd5e1' }}>Candidate Blocks (Layer 1): </span>
            <strong style={{ color: '#38bdf8' }}>{annData?.candidate_blocks_layer_1 || 0}</strong>
          </div>
          <button
            onClick={handleRunBackprop}
            style={{
              background: '#0284c7',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            ⚡ Trigger Textual Backprop (∇text)
          </button>
        </div>
        {backpropStatus && (
          <p style={{ marginTop: '8px', fontSize: '12px', color: '#a7f3d0' }}>{backpropStatus}</p>
        )}
      </div>
    </div>
  );
}
