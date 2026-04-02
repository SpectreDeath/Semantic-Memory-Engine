import React, { useState } from 'react';
import { FileText } from 'lucide-react';

const Intelligences = () => {
  const [reports] = useState([
    { title: 'Summary: Jan 20', date: '2026-01-20' },
    { title: 'Briefing: Jan 18', date: '2026-01-18' },
    { title: 'Discovery: Jan 15', date: '2026-01-15' },
  ]);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem' }}>
      <section className="card glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <FileText size={24} color="var(--accent-cyan)" />
          <div>
            <h3>Executive Summary: Project Alpha</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
              Generated: Jan 20, 2026
            </span>
          </div>
        </div>
        <div style={{ marginTop: '1.5rem', lineHeight: 1.8 }}>
          <p>
            Overall sentiment is <strong>highly positive (0.82)</strong>.
            Key themes revolve around <strong>innovation</strong> and <strong>efficiency</strong>.
            The knowledge graph indicates a strong central connection between 'Machine Learning' and 'Infrastructure'...
          </p>
        </div>
        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.5rem' }}>
          {['NLP', 'Optimization', 'Security'].map((tag) => (
            <span
              key={tag}
              style={{
                background: 'var(--glass-border)',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '0.7rem',
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      </section>

      <aside className="glass-panel" style={{ padding: '1rem' }}>
        <h4 style={{ marginBottom: '1rem' }}>Archives</h4>
        {reports.map((report, i) => (
          <div key={i} className="sidebar-item" style={{ fontSize: '0.8rem' }}>
            {report.title}
          </div>
        ))}
      </aside>
    </div>
  );
};

export default Intelligences;