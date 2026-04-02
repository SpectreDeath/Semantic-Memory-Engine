import React from 'react';
import KnowledgeBrain from '../components/KnowledgeBrain';

const Brain = () => (
  <section className="card glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
    <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
      <h3>Silicon Brain Explorer</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
        Neural network of extracted concepts and relationships.
      </p>
    </div>
    <KnowledgeBrain />
  </section>
);

export default Brain;