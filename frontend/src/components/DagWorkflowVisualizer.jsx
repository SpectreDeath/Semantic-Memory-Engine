import React, { useState } from 'react';

export default function DagWorkflowVisualizer({ onExecuteWorkflow }) {
  const [selectedPreset, setSelectedPreset] = useState('bioinformatics');
  const [running, setRunning] = useState(false);
  const [workflowResult, setWorkflowResult] = useState(null);

  const presets = {
    bioinformatics: {
      workflow_id: 'sci_wf_bioinformatics',
      target_domain: 'bioinformatics',
      tasks: [
        { task_id: 'fetch_compound', skill_id: 'chembl_database', deps: [], status: 'COMPLETED', time_ms: 120 },
        { task_id: 'fetch_structure', skill_id: 'pdb_database', deps: ['fetch_compound'], status: 'COMPLETED', time_ms: 340 },
        { task_id: 'render_3d', skill_id: 'pymol', deps: ['fetch_structure'], status: 'COMPLETED', time_ms: 85 },
      ],
    },
    threat_intel: {
      workflow_id: 'sci_wf_threat_intel',
      target_domain: 'threat_intel',
      tasks: [
        { task_id: 'harvest_feed', skill_id: 'threat_harvester', deps: [], status: 'COMPLETED', time_ms: 45 },
        { task_id: 'inject_vindex', skill_id: 'vindex_overlay', deps: ['harvest_feed'], status: 'COMPLETED', time_ms: 60 },
        { task_id: 'audit_log', skill_id: 'audit_engine', deps: ['inject_vindex'], status: 'COMPLETED', time_ms: 30 },
      ],
    },
  };

  const handleRunPreset = async () => {
    setRunning(true);
    setWorkflowResult(null);

    try {
      const res = await fetch('/api/v1/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_name: 'route_scientific_workflow',
          payload: { prompt: 'Analyze target compound', target_domain: selectedPreset },
          mode: 'em_cubed_workflow',
        }),
      });
      const data = await res.json();
      setWorkflowResult(data);
    } catch (err) {
      setWorkflowResult({ status: 'error', error: err.message });
    } finally {
      setRunning(false);
    }
  };

  const activePreset = presets[selectedPreset];

  return (
    <div style={{ padding: '20px', background: 'rgba(15, 23, 42, 0.8)', borderRadius: '12px', color: '#e2e8f0', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ color: '#818cf8', margin: 0 }}>🕸️ Distributed em-cubed DAG Workflow Visualizer</h3>
        <div style={{ display: 'flex', gap: '12px' }}>
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            style={{ background: '#0f172a', color: '#fff', padding: '6px 12px', borderRadius: '6px', border: '1px solid #334155' }}
          >
            <option value="bioinformatics">Bioinformatics DAG Preset</option>
            <option value="threat_intel">Threat Intel IOC Harvester DAG</option>
          </select>
          <button
            onClick={handleRunPreset}
            disabled={running}
            style={{
              background: running ? '#64748b' : '#6366f1',
              color: '#fff',
              border: 'none',
              padding: '6px 16px',
              borderRadius: '6px',
              cursor: running ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
            }}
          >
            {running ? 'Executing DAG...' : '▶ Execute DAG Pipeline'}
          </button>
        </div>
      </div>

      {/* Interactive DAG Task Nodes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {activePreset.tasks.map((t, idx) => (
          <div
            key={t.task_id}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              borderLeft: '4px solid #4ade80',
              padding: '12px',
              borderRadius: '8px',
              position: 'relative',
            }}
          >
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>Step {idx + 1}</div>
            <div style={{ fontWeight: 'bold', color: '#f8fafc', margin: '4px 0' }}>{t.task_id}</div>
            <div style={{ fontSize: '12px', color: '#38bdf8' }}>Skill: {t.skill_id}</div>
            {t.deps.length > 0 && (
              <div style={{ fontSize: '11px', color: '#a7f3d0', marginTop: '6px' }}>
                Depends on: {t.deps.join(', ')}
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
              <span style={{ background: '#064e3b', color: '#34d399', fontSize: '10px', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                {t.status}
              </span>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>{t.time_ms} ms</span>
            </div>
          </div>
        ))}
      </div>

      {workflowResult && (
        <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #334155', fontSize: '12px' }}>
          <strong style={{ color: '#4ade80' }}>Execution Output:</strong>
          <pre style={{ margin: '8px 0 0 0', color: '#cbd5e1', overflowX: 'auto' }}>
            {JSON.stringify(workflowResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
