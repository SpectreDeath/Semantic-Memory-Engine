import React, { useState } from "react";
import {
  LayoutDashboard,
  BrainCircuit,
  FileText,
  FlaskConical,
  Settings,
  Activity,
  Cpu,
  Network,
  Globe,
  Unplug,
  Database,
} from "lucide-react";
import KnowledgeBrain from "./components/KnowledgeBrain";
import "./index.css";

const ToolLab = () => {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalysis = async (type) => {
    setAnalyzing(true);
    try {
      const endpoint =
        type === "graph"
          ? "/api/v1/analysis/graph"
          : type === "report"
            ? "/api/v1/analysis/report"
            : "/api/v1/search";

      const response = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, context_id: "tool_lab" }),
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error("Analysis failed:", err);
      setResult({
        error:
          "Connection to API failed. Ensure 'python -m src dashboard' is running.",
      });
    }
    setAnalyzing(false);
  };

  return (
    <section className="card glass-panel">
      <h3>Interactive Tool Lab</h3>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
        Test laboratory tools directly against raw text input.
      </p>

      <div style={{ marginTop: "1.5rem" }}>
        <textarea
          className="glass-panel"
          placeholder="Insert raw text for analysis..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{
            width: "100%",
            height: "150px",
            background: "rgba(0,0,0,0.2)",
            padding: "1rem",
            border: "1px solid var(--glass-border)",
            borderRadius: "8px",
            color: "white",
            outline: "none",
            fontFamily: "inherit",
          }}
        />
        <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
          <button
            disabled={analyzing || !text}
            onClick={() => handleAnalysis("graph")}
            className="glass-panel"
            style={{
              padding: "0.75rem 1.5rem",
              background: "var(--accent-cyan)",
              color: "var(--bg-dark)",
              fontWeight: "600",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              opacity: analyzing || !text ? 0.5 : 1,
            }}
          >
            {analyzing ? "Processing..." : "Generate Graph"}
          </button>
          <button
            disabled={analyzing || !text}
            onClick={() => handleAnalysis("report")}
            className="glass-panel"
            style={{
              padding: "0.75rem 1.5rem",
              color: "white",
              borderRadius: "8px",
              cursor: "pointer",
              opacity: analyzing || !text ? 0.5 : 1,
            }}
          >
            Intelligence Briefing
          </button>
        </div>

        {result && (
          <div
            style={{
              marginTop: "2rem",
              padding: "1.5rem",
              border: "1px solid var(--glass-border)",
              borderRadius: "8px",
              background: "rgba(255,255,255,0.02)",
            }}
          >
            <h4 style={{ marginBottom: "1rem", color: "var(--accent-cyan)" }}>
              Analysis Results
            </h4>
            <pre
              style={{
                fontSize: "0.8rem",
                overflowX: "auto",
                color: "var(--text-secondary)",
              }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </section>
  );
};

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [metrics, setMetrics] = useState({ cpu: 0, memory: 0, latency: "0ms" });

  // Real-time diagnostics connection
  React.useEffect(() => {
    let socket;
    try {
      socket = new WebSocket("ws://127.0.0.1:8000/ws/diagnostics");

      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "diagnostics") {
          setMetrics(payload.data);
        }
      };
    } catch (e) {
      console.warn("WebSocket connection failed");
    }

    return () => socket && socket.close();
  }, []);

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel">
        <div style={{ marginBottom: "2rem" }}>
          <h2
            style={{
              color: "var(--accent-cyan)",
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <BrainCircuit size={28} /> SimpleMem
          </h2>
          <p
            style={{
              fontSize: "0.8rem",
              color: "var(--text-secondary)",
              paddingLeft: "40px",
            }}
          >
            Laboratory v2.0
          </p>
        </div>

        <nav>
          <div
            className={`sidebar-item ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <LayoutDashboard size={20} /> Dashboard
          </div>
          <div
            className={`sidebar-item ${activeTab === "brain" ? "active" : ""}`}
            onClick={() => setActiveTab("brain")}
          >
            <Network size={20} /> The Brain
          </div>
          <div
            className={`sidebar-item ${activeTab === "reports" ? "active" : ""}`}
            onClick={() => setActiveTab("reports")}
          >
            <FileText size={20} /> Intelligences
          </div>
          <div
            className={`sidebar-item ${activeTab === "lab" ? "active" : ""}`}
            onClick={() => setActiveTab("lab")}
          >
            <FlaskConical size={20} /> Tool Lab
          </div>
          <div
            className={`sidebar-item ${activeTab === "harvester" ? "active" : ""}`}
            onClick={() => setActiveTab("harvester")}
          >
            <Globe size={20} /> Harvester
          </div>
          <div
            className={`sidebar-item ${activeTab === "connections" ? "active" : ""}`}
            onClick={() => setActiveTab("connections")}
          >
            <Unplug size={20} /> Connections
          </div>
        </nav>

        <div
          style={{
            marginTop: "auto",
            paddingTop: "1rem",
            borderTop: "1px solid var(--glass-border)",
          }}
        >
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <div className="status-indicator"></div> System Online
          </div>
          <div className="sidebar-item" style={{ marginTop: "0.5rem" }}>
            <Settings size={18} /> Settings
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header
          style={{
            marginBottom: "2rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h1 style={{ fontSize: "1.8rem" }}>
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </h1>
            <p style={{ color: "var(--text-secondary)" }}>
              Monitoring laboratory operations in real-time.
            </p>
          </div>
          <div
            className="glass-panel"
            style={{ padding: "0.75rem 1rem", display: "flex", gap: "1.5rem" }}
          >
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "0.7rem",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <Cpu size={12} /> CPU
              </div>
              <div style={{ fontWeight: "600", color: "var(--accent-cyan)" }}>
                {metrics.cpu}%
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "0.7rem",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <Activity size={12} /> LATENCY
              </div>
              <div style={{ fontWeight: "600", color: "var(--accent-purple)" }}>
                {metrics.latency}
              </div>
            </div>
          </div>
        </header>

        {activeTab === "dashboard" && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: "1.5rem",
            }}
          >
            <section className="card glass-panel">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <h3
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <Activity size={18} /> Live Ingestion Feed
                </h3>
                <span
                  style={{
                    fontSize: "0.7rem",
                    color: "var(--success)",
                    fontWeight: "600",
                  }}
                >
                  STREAMING
                </span>
              </div>
              <p
                style={{
                  color: "var(--text-secondary)",
                  fontSize: "0.9rem",
                  marginTop: "0.5rem",
                }}
              >
                Latest entities discovery and processed data markers.
              </p>
              <div
                style={{
                  marginTop: "1.5rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                {[
                  {
                    type: "ENTITY",
                    msg: "Albert Einstein discovery in /papers",
                    time: "2m",
                  },
                  {
                    type: "SENTIMENT",
                    msg: "Negative spike detected in #security-feed",
                    time: "5m",
                  },
                  {
                    type: "KNOWLEDGE",
                    msg: "New relationship: Relativity → Physics",
                    time: "12m",
                  },
                ].map((item, i) => (
                  <div
                    key={i}
                    style={{
                      padding: "0.75rem",
                      borderLeft: `3px solid ${item.type === "SENTIMENT" ? "var(--danger)" : "var(--accent-cyan)"}`,
                      background: "rgba(255,255,255,0.03)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: "0.8rem",
                      }}
                    >
                      <span
                        style={{
                          color:
                            item.type === "SENTIMENT"
                              ? "var(--danger)"
                              : "var(--accent-cyan)",
                          fontWeight: "600",
                        }}
                      >
                        {item.type}
                      </span>
                      <span style={{ color: "var(--text-secondary)" }}>
                        {item.time} ago
                      </span>
                    </div>
                    <div style={{ fontWeight: "400", marginTop: "0.25rem" }}>
                      {item.msg}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="card glass-panel">
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <h3
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <Network size={18} /> Semantic Overlaps
                </h3>
              </div>
              <p
                style={{
                  color: "var(--text-secondary)",
                  fontSize: "0.9rem",
                  marginTop: "0.5rem",
                }}
              >
                Connections detected between disparate memory contexts.
              </p>
              <div
                style={{
                  marginTop: "1.5rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.75rem",
                }}
              >
                <div
                  className="glass-panel"
                  style={{
                    padding: "1rem",
                    background: "rgba(129, 140, 248, 0.05)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <span style={{ fontWeight: "600" }}>
                      Context: security_audit
                    </span>
                    <span style={{ color: "var(--accent-purple)" }}>
                      92% Match
                    </span>
                  </div>
                  <p
                    style={{
                      fontSize: "0.8rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    Overlaps with: firewalls, system_logs, network_topology
                  </p>
                </div>
              </div>
            </section>
          </div>
        )}

        {activeTab === "brain" && (
          <section
            className="card glass-panel"
            style={{ padding: "0", overflow: "hidden" }}
          >
            <div
              style={{
                padding: "1.5rem",
                borderBottom: "1px solid var(--glass-border)",
              }}
            >
              <h3>Silicon Brain Explorer</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Neural network of extracted concepts and relationships.
              </p>
            </div>
            <KnowledgeBrain />
          </section>
        )}

        {activeTab === "reports" && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 300px",
              gap: "1.5rem",
            }}
          >
            <section className="card glass-panel">
              <div
                style={{ display: "flex", alignItems: "center", gap: "12px" }}
              >
                <FileText size={24} color="var(--accent-cyan)" />
                <div>
                  <h3>Executive Summary: Project Alpha</h3>
                  <span
                    style={{
                      fontSize: "0.7rem",
                      color: "var(--text-secondary)",
                    }}
                  >
                    Generated: Jan 20, 2026
                  </span>
                </div>
              </div>
              <div style={{ marginTop: "1.5rem", lineHeight: "1.8" }}>
                <p>
                  Overall sentiment is <strong>highly positive (0.82)</strong>.
                  Key themes revolve around <strong>innovation</strong> and{" "}
                  <strong>efficiency</strong>. The knowledge graph indicates a
                  strong central connection between 'Machine Learning' and
                  'Infrastructure'...
                </p>
              </div>
              <div
                style={{ marginTop: "2rem", display: "flex", gap: "0.5rem" }}
              >
                {["NLP", "Optimization", "Security"].map((tag) => (
                  <span
                    key={tag}
                    style={{
                      background: "var(--glass-border)",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontSize: "0.7rem",
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </section>

            <aside className="glass-panel" style={{ padding: "1rem" }}>
              <h4 style={{ marginBottom: "1rem" }}>Archives</h4>
              <div
                className="sidebar-item active"
                style={{ fontSize: "0.8rem" }}
              >
                Summary: Jan 20
              </div>
              <div className="sidebar-item" style={{ fontSize: "0.8rem" }}>
                Briefing: Jan 18
              </div>
              <div className="sidebar-item" style={{ fontSize: "0.8rem" }}>
                Discovery: Jan 15
              </div>
            </aside>
          </div>
        )}

        {activeTab === "lab" && <ToolLab />}
        {activeTab === "harvester" && <HarvesterPanel />}
        {activeTab === "connections" && <ConnectionsManager />}
      </main>
    </div>
  )
}

const ConnectionsManager = () => {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [provider, setProvider] = useState('langflow')

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/connections/status')
      const data = await response.json()
      setStatus(data)
    } catch (err) {
      console.error("Failed to fetch status:", err)
    }
    setLoading(false)
  }

  const updateProvider = async (newProvider) => {
    try {
      await fetch('http://127.0.0.1:8000/api/v1/connections/ai-provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_type: newProvider })
      })
      setProvider(newProvider)
      fetchStatus()
    } catch (err) {
      console.error("Failed to update provider:", err)
    }
  }

  React.useEffect(() => {
    fetchStatus()
  }, [])

  return (
    <section className="card glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3>Control Room: Service Connections</h3>
        <button onClick={fetchStatus} disabled={loading} className="glass-panel" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem', cursor: 'pointer' }}>
          {loading ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Database size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: '600' }}>Relational Nexus</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: status?.database === 'online' ? 'var(--success)' : 'var(--danger)' }}>
             Status: {status?.database || 'Unknown'}
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Activity size={18} color="var(--accent-purple)" />
            <span style={{ fontWeight: '600' }}>AI Sidecar</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: status?.sidecar?.status === 'online' ? 'var(--success)' : 'var(--danger)' }}>
             Status: {status?.sidecar?.status || 'Offline'}
          </p>
          {status?.sidecar && <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Provider: {status.sidecar.provider}</p>}
        </div>

        <div className="glass-panel" style={{ padding: '1rem', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <BrainCircuit size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: '600' }}>AI Provider Strategy</span>
          </div>
          <select 
            value={provider} 
            onChange={(e) => updateProvider(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '4px' }}
          >
            <option value="langflow">Langflow (Hybrid-Cloud)</option>
            <option value="mock">Local Mock (Offline/Fast)</option>
            <option value="ollama">Ollama (Fully Local)</option>
          </select>
        </div>
      </div>
    </section>
  )
}

const HarvesterPanel = () => {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [options, setOptions] = useState({ js_render: false, deep_crawl: false })

  const handleIngest = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/ingestion/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, ...options })
      })
      const data = await response.json()
      setResult(data)
    } catch (err) {
      console.error("Ingestion failed:", err)
      setResult({ error: "Failed to connect to Harvester engine." })
    }
    setLoading(false)
  }

  return (
    <section className="card glass-panel">
      <h3>The Harvester: Digital Ingestion</h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Scrape web content and convert to semantic atomic facts.</p>
      
      <div style={{ marginTop: '1.5rem' }}>
        <input 
          type="text"
          className="glass-panel"
          placeholder="Enter target URL (e.g., https://en.wikipedia.org/wiki/Sovereignty)..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ width: '100%', padding: '1rem', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: '8px', color: 'white', outline: 'none' }}
        />
        
        <div style={{ display: 'flex', gap: '2rem', marginTop: '1rem', fontSize: '0.85rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input type="checkbox" checked={options.js_render} onChange={e => setOptions({...options, js_render: e.target.checked})} />
            JavaScript Rendering
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input type="checkbox" checked={options.deep_crawl} onChange={e => setOptions({...options, deep_crawl: e.target.checked})} />
            Recursive Deep Crawl
          </label>
        </div>

        <button 
          disabled={loading || !url}
          onClick={handleIngest}
          className="glass-panel" 
          style={{ marginTop: '1.5rem', padding: '0.75rem 2rem', background: 'var(--accent-purple)', color: 'white', fontWeight: '600', border: 'none', borderRadius: '8px', cursor: 'pointer', opacity: (loading || !url) ? 0.5 : 1 }}
        >
          {loading ? 'Ingesting...' : 'Start Ingestion'}
        </button>

        {result && (
          <div style={{ marginTop: '2rem', padding: '1.5rem', border: '1px solid var(--glass-border)', borderRadius: '8px', background: 'rgba(255,255,255,0.02)' }}>
             <h4 style={{ marginBottom: '1rem', color: 'var(--accent-purple)' }}>Capture Report</h4>
             {result.error ? (
               <p style={{ color: 'var(--danger)' }}>{result.error}</p>
             ) : (
               <div style={{ fontSize: '0.8rem' }}>
                  <p><strong>URL:</strong> {result.url}</p>
                  <p><strong>Word Count:</strong> {result.metadata?.word_count || 0}</p>
                  <p><strong>Quality Score:</strong> {result.quality_score}/100</p>
                  <div style={{ marginTop: '1rem', maxHeight: '200px', overflowY: 'auto', padding: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>{result.markdown?.substring(0, 1000)}...</pre>
                  </div>
               </div>
             )}
          </div>
        )}
      </div>
    </section>
  )
}

export default App;
