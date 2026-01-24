import streamlit as st
import psutil
import pynvml
import sqlite3
import pandas as pd
import chromadb
from pathlib import Path
import time
from datetime import datetime
import os
import plotly.express as px

# Internal Imports
from src.core.config import Config

# ============================================================================
# CONFIGURATION & STYLE
# ============================================================================

st.set_page_config(
    page_title="The Beacon - Semantic Intelligence",
    page_icon="🗼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional "Dark Mode" Theme via CSS
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4150;
    }
    .stDataFrame {
        border: 1px solid #3e4150;
        border-radius: 5px;
    }
    .gap-alert {
        padding: 10px;
        border-left: 5px solid #ff4b4b;
        background-color: #262730;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DATABASE CONNECTIONS (Cached)
# ============================================================================

@st.cache_resource
def get_db_connections():
    config = Config()
    base_dir = Path(config.get('storage.base_dir', './data'))
    
    lab_db_path = base_dir / "storage" / "laboratory.db"
    scribe_db_path = base_dir / "storage" / "scribe_profiles.sqlite"
    chroma_path = base_dir / "chroma_db"
    
    # Initialize connections
    # Note: Using check_same_thread=False for Streamlit's multi-threaded environment
    lab_conn = None
    if lab_db_path.exists():
        lab_conn = sqlite3.connect(str(lab_db_path), check_same_thread=False)
    
    scribe_conn = None
    if scribe_db_path.exists():
        scribe_conn = sqlite3.connect(str(scribe_db_path), check_same_thread=False)
    
    chroma_client = None
    if chroma_path.exists():
        try:
            chroma_client = chromadb.PersistentClient(path=str(chroma_path))
        except Exception as e:
            st.error(f"ChromaDB Error: {e}")
        
    return {
        "lab": lab_conn,
        "scribe": scribe_conn,
        "chroma": chroma_client
    }

# ============================================================================
# SYSTEM HEALTH (Hardware Monitoring)
# ============================================================================

def get_system_stats():
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=None)
    
    # RAM usage
    ram = psutil.virtual_memory()
    ram_used_gb = ram.used / (1024**3)
    ram_total_gb = ram.total / (1024**3)
    
    # VRAM usage (6GB 1660 Ti context)
    gpu_info = {"temp": "N/A", "vram_used": 0, "vram_total": 0, "available": False}
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_info["temp"] = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_info["vram_used"] = mem.used / (1024**2)
        gpu_info["vram_total"] = mem.total / (1024**2)
        gpu_info["available"] = True
        pynvml.nvmlShutdown()
    except:
        gpu_info["available"] = False
        
    return {
        "cpu": cpu_percent,
        "ram_used": ram_used_gb,
        "ram_total": ram_total_gb,
        "ram_percent": ram.percent,
        "gpu": gpu_info
    }

# ============================================================================
# DATA RETRIEVAL
# ============================================================================

def get_memory_stats(conns):
    stats = {"facts": 0, "vectors": 0, "logical_links": 0, "validated_perc": 0}
    
    if conns["lab"]:
        try:
            cursor = conns["lab"].cursor()
            # Count atomic facts
            cursor.execute("SELECT COUNT(*) FROM atomic_facts")
            stats["facts"] = cursor.fetchone()[0]
            
            # Count logical links
            cursor.execute("SELECT COUNT(*) FROM logical_links")
            stats["logical_links"] = cursor.fetchone()[0]
            
            # Simulated validation percentage (In production, this would query a 'validated' flag or specific ConceptNet results)
            if stats["facts"] > 0:
                stats["validated_perc"] = 85.0 # Mocked for dashboard demonstration
        except:
            pass
        
    # Total vectors in ChromaDB
    if conns["chroma"]:
        try:
            collections = conns["chroma"].list_collections()
            for col_name in collections:
                c = conns["chroma"].get_collection(col_name)
                stats["vectors"] += c.count()
        except:
            pass
            
    return stats

def get_forensic_feed(conns, limit=10, search_query=""):
    if not conns["scribe"]:
        return pd.DataFrame()
        
    try:
        query = """
            SELECT created_at as Timestamp, candidate_author_id as "Author ID", 
                   confidence_level as Confidence, attribution_score as Score,
                   verified as Verified
            FROM attribution_history
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conns["scribe"], params=(limit,))
        
        if search_query:
            df = df[df['Author ID'].str.contains(search_query, case=False) | 
                    df['Confidence'].str.contains(search_query, case=False)]
            
        return df
    except Exception as e:
        return pd.DataFrame()

def get_knowledge_gaps(conns):
    # Simulated gap detection logic
    gaps = [
        {"concept": "Neural Topology", "reason": "Missing hypernyms for context mapping", "severity": "High"},
        {"concept": "Sub-symbolic Reasoning", "reason": "Sparse vector density in latest crawl", "severity": "Medium"},
    ]
    return gaps

# ============================================================================
# DASHBOARD LAYOUT
# ============================================================================

def main():
    conns = get_db_connections()
    stats = get_system_stats()
    
    # SIDEBAR - System Health
    st.sidebar.title("🏮 System Health")
    hw_container = st.sidebar.container()
    with hw_container:
        st.metric("CPU Usage", f"{stats['cpu']}%")
        st.progress(stats['cpu'] / 100)
        
        st.metric("RAM Usage", f"{stats['ram_used']:.2f} / {stats['ram_total']:.1f} GB")
        st.progress(stats['ram_percent'] / 100)
        
        if stats["gpu"]["available"]:
            st.metric("VRAM Usage (1660 Ti)", f"{stats['gpu']['vram_used']:.0f} / {stats['gpu']['vram_total']:.0f} MB")
            vram_p = stats['gpu']['vram_used'] / stats['gpu']['vram_total'] if stats['gpu']['vram_total'] > 0 else 0
            st.progress(min(1.0, vram_p))
            st.caption(f"GPU Temp: {stats['gpu']['temp']}°C")
        else:
            st.sidebar.warning("GPU / VRAM Monitor Offline")

    st.sidebar.divider()
    st.sidebar.info("The Beacon prototype is running on local hardware. Resource consumption is minimized for background AI tasks.")

    # MAIN CONTENT
    st.title("🗼 The Beacon / Semantic Dashboard")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Intelligence Overview", 
        "Forensic Deep-Dive", 
        "⚖️ Author Versus",
        "🛡️ Verification",
        "🕸️ Stylistic Map",
        "Hardware Diagnostics"
    ])
    
    # TAB 1: Intelligence Overview
    with tab1:
        col1, col2, col3 = st.columns(3)
        mem_stats = get_memory_stats(conns)
        
        with col1:
            st.metric("Total Atomic Facts", f"{mem_stats['facts']:,}", delta="Centrifuge DB")
        with col2:
            st.metric("Common Sense Validation", f"{mem_stats['validated_perc']:.1f}%", delta="ConceptNet Audit")
        with col3:
            st.metric("Logical Links", f"{mem_stats['logical_links']:,}", delta="AIFdb Mapping")
            
        st.divider()
        st.subheader("🚨 Reasoning Audit & Veracity Alerts")
        # Sample alerts for ConceptNet conflicts
        alerts = [
            {"subject": "Global Warming", "claim": "IsA hoax", "status": "Conflict", "evidence": "ConceptNet: Global Warming IsA climate_change (Weight 4.5)"},
            {"subject": "AI Consciousness", "claim": "IsA solved_problem", "status": "Unverified", "evidence": "No supporting IsA relations in ConceptNet baseline."}
        ]
        for alert in alerts:
            with st.expander(f"⚠️ {alert['status']}: {alert['subject']} - {alert['claim']}"):
                st.write(alert['evidence'])
                st.button(f"Mark as Potential Hallucination", key=f"hb_{alert['subject']}")
            
        st.subheader("⚠️ Knowledge Gap Alerts")
        gaps = get_knowledge_gaps(conns)
        if gaps:
            for gap in gaps:
                st.markdown(f"""
                <div class="gap-alert">
                    <strong>{gap['severity']} Priority Gap:</strong> {gap['concept']}<br>
                    <small>{gap['reason']}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No critical knowledge gaps detected.")

    # TAB 2: Forensic Deep-Dive
    with tab2:
        st.subheader("🖋️ Scribe Forensic Feed")
        search = st.text_input("Search Attribution History...", placeholder="Filter by Author or Confidence...")
        
        feed_df = get_forensic_feed(conns, limit=20, search_query=search)
        if not feed_df.empty:
            st.dataframe(feed_df, use_container_width=True)
        else:
            st.info("No forensic data available in scribe_profiles.sqlite.")

        # --- SIGNAL DISTRIBUTION CHART ---
        st.divider()
        st.subheader("📊 Rhetorical Profile Analysis")
        
        try:
            # Get list of authors
            scribe_conns = get_db_connections()
            if scribe_conns["scribe"]:
                cursor = scribe_conns["scribe"].cursor()
                cursor.execute("SELECT author_id, author_name FROM author_profiles")
                authors = cursor.fetchall()
                author_options = {f"{name} ({uid})": uid for uid, name in authors}
                
                if author_options:
                    selected_label = st.selectbox("Select Author to Profile", options=list(author_options.keys()))
                    selected_uid = author_options[selected_label]
                    
                    if selected_uid:
                        from src.core.factory import ToolFactory
                        importer = ToolFactory.create_lexicon_importer()
                        stats = importer.get_summary_by_author(selected_uid)
                        
                        if not stats.empty:
                            fig = px.bar(
                                stats, 
                                x='category', 
                                y='count', 
                                title=f"Rhetorical Profile: {selected_label}",
                                labels={'category': 'Signal Category', 'count': 'Relative Weight'},
                                color='count',
                                color_continuous_scale='Viridis',
                                template='plotly_dark'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No signal data available for this author yet. Try running a Lexicon Import.")
                else:
                    st.info("No author profiles found to analyze.")
                    
                # --- STYLOMETRIC COMPARISON ---
                st.divider()
                st.subheader("🔬 Stylometric Engine Cross-Check")
                
                compare_data = []
                for name, uid in author_options.items():
                    # Mocking Delta results for UI demonstration
                    # In production, this would call get_stylo_attribution(text, corpus)
                    compare_data.append({
                        "Author": name,
                        "Rhetorical Fingerprint (Python)": "88%",
                        "Delta Distance (R-Stylo)": "0.42",
                        "Consensus": "Strong Match"
                    })
                
                if compare_data:
                    st.table(pd.DataFrame(compare_data))
                    from src.core.factory import ToolFactory
                    stylo = ToolFactory.create_stylo_wrapper()
                    stylo_status = stylo.get_status()
                    if not stylo_status["ready"]:
                        st.info("💡 R-Stylo secondary engine is offline. Using rhetorical fallback.")

                # --- AUTHOR STYLISTIC EVOLUTION ---
                st.divider()
                st.subheader("📈 Author Stylistic Evolution")

                if selected_uid:
                    # 1. Initialize Adaptive Learner via Factory
                    from src.core.factory import ToolFactory
                    learner = ToolFactory.create_adaptive_learner()
                    
                    # 2. Get evolution data (historical snapshots)
                    evolution_df = learner.get_evolution_history(selected_uid)
                    
                    if not evolution_df.empty:
                        # Filter columns that exist (avoid KeyError)
                        potential_cols = ["signal_anger", "signal_trust", "signal_joy", "signal_sadness"]
                        plot_cols = [c for c in potential_cols if c in evolution_df.columns]
                        
                        if plot_cols:
                            st.caption("Tracking top emotional signals over time:")
                            st.line_chart(
                                evolution_df, 
                                x="timestamp", 
                                y=plot_cols,
                                use_container_width=True
                            )
                        else:
                            st.info("Snapshots exist but lack standard emotional signals for plotting.")
                        
                        # 3. Check for recent Drift Alerts
                        is_drifting, score = learner.analyze_recent_drift(selected_uid)
                        if is_drifting:
                            st.warning(f"⚠️ **Style Drift Detected:** Recent content deviates by {score:.2f} (Cosine Dist) from historical baseline.")
                    else:
                        st.info("Insufficient historical data to plot evolution. Keep harvesting content to build the profile.")
                
            else:
                st.warning("Forensic database not connected.")
        except Exception as e:
            st.error(f"Error rendering comparison: {e}")

    # TAB 3: Author Versus (Contrastive Analysis)
    with tab3:
        st.subheader("⚖️ Contrastive Analysis (Zeta-Scores)")
        st.caption("Identify distinctive lexical markers that separate two authors.")
        
        # Get author list
        try:
            scribe_conns = get_db_connections()
            if scribe_conns["scribe"]:
                cursor = scribe_conns["scribe"].cursor()
                cursor.execute("SELECT author_id, author_name FROM author_profiles")
                authors = cursor.fetchall()
                author_options = {f"{name} ({uid})": uid for uid, name in authors}
                
                if len(author_options) >= 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        auth_a_label = st.selectbox("Select Author A", options=list(author_options.keys()), key="versus_a")
                    with col2:
                        auth_b_label = st.selectbox("Select Author B", options=list(author_options.keys()), key="versus_b")
                    
                    if st.button("Run Contrastive Analysis"):
                        auth_a = author_options[auth_a_label]
                        auth_b = author_options[auth_b_label]
                        
                        from src.core.factory import ToolFactory
                        analyzer = ToolFactory.create_contrastive_analyzer()
                        results = analyzer.get_contrastive_lexicon(auth_a, auth_b, top_n=10)
                        
                        st.divider()
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.write(f"**{auth_a_label} Preferred Words**")
                            if results['preferred_a']['words']:
                                df_a = pd.DataFrame({
                                    'Word': results['preferred_a']['words'],
                                    'Zeta Score': results['preferred_a']['scores']
                                })
                                st.dataframe(df_a, use_container_width=True)
                            else:
                                st.info("Insufficient data for analysis")
                        
                        with col_b:
                            st.write(f"**{auth_b_label} Preferred Words**")
                            if results['preferred_b']['words']:
                                df_b = pd.DataFrame({
                                    'Word': results['preferred_b']['words'],
                                    'Zeta Score': results['preferred_b']['scores']
                                })
                                st.dataframe(df_b, use_container_width=True)
                            else:
                                st.info("Insufficient data for analysis")
                else:
                    st.warning("Need at least 2 author profiles for contrastive analysis.")
            else:
                st.warning("Forensic database not connected.")
        except Exception as e:
            st.error(f"Error in contrastive analysis: {e}")

    # TAB 4: Verification (Impostors Method)
    with tab4:
        st.subheader("🛡️ Authorship Verification (Impostors Method)")
        st.caption("Probabilistic verification using reference impostor pool.")
        
        target_text = st.text_area(
            "Target Text to Verify", 
            height=200,
            placeholder="Paste the document you want to verify..."
        )
        
        try:
            scribe_conns = get_db_connections()
            if scribe_conns["scribe"]:
                cursor = scribe_conns["scribe"].cursor()
                cursor.execute("SELECT author_id, author_name FROM author_profiles")
                authors = cursor.fetchall()
                author_options = {f"{name} ({uid})": uid for uid, name in authors}
                
                if author_options:
                    suspect_label = st.selectbox("Select Suspect Author", options=list(author_options.keys()))
                    suspect_uid = author_options[suspect_label]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        iterations = st.slider("Bootstrap Iterations", 50, 200, 100)
                    with col2:
                        impostor_count = st.slider("Impostor Pool Size", 5, 20, 10)
                    
                    if st.button("Run Probabilistic Audit"):
                        if target_text:
                            from src.core.factory import ToolFactory
                            checker = ToolFactory.create_impostors_checker()
                            report = checker.verify_authorship(
                                target_text, 
                                suspect_uid,
                                iterations=iterations,
                                impostor_count=impostor_count
                            )
                            
                            st.divider()
                            st.metric(
                                "Confidence Score", 
                                f"{report['confidence']*100:.2f}%",
                                delta=f"{report['suspect_wins']}/{report['iterations']} wins"
                            )
                            
                            if report['verified']:
                                st.success(f"✅ **{report['verdict']}**: Text matches {suspect_label}'s style")
                            else:
                                st.error(f"⚠️ **{report['verdict']}**: Text does NOT match {suspect_label}'s style")
                            
                            with st.expander("Technical Details"):
                                st.json(report)
                        else:
                            st.warning("Please provide text to verify.")
                else:
                    st.warning("No author profiles available for verification.")
            else:
                st.warning("Forensic database not connected.")
        except Exception as e:
            st.error(f"Error in verification: {e}")

    # TAB 5: Stylistic Map (Network Visualization)
    with tab5:
        st.subheader("🕸️ Global Stylistic Consensus Network")
        st.caption("Interactive graph showing similarity relationships between all authors.")
        
        col1, col2 = st.columns(2)
        with col1:
            threshold = st.slider("Similarity Threshold (Delta)", 0.5, 2.0, 1.2, 0.1)
        with col2:
            max_nodes = st.slider("Max Nodes", 10, 100, 50)
        
        if st.button("Generate Author Network"):
            try:
                from src.core.factory import ToolFactory
                import streamlit.components.v1 as components
                
                gen = ToolFactory.create_network_generator()
                html_path = gen.generate_network(threshold=threshold, max_nodes=max_nodes)
                
                if html_path and os.path.exists(html_path):
                    with open(html_path, 'r', encoding='utf-8') as f:
                        components.html(f.read(), height=600, scrolling=True)
                    st.success(f"✅ Network generated with threshold={threshold}")
                else:
                    st.error("Failed to generate network. Check database for author profiles.")
            except Exception as e:
                st.error(f"Error generating network: {e}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

    # TAB 6: Hardware Diagnostics
    with tab6:
        st.subheader("🛠️ Detailed Hardware Stats")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Machine Load Profile**")
            st.write(f"- Logical Processors: {psutil.cpu_count()}")
            st.write(f"- Physical Cores: {psutil.cpu_count(logical=False)}")
            st.write(f"- Disk I/O (Read): {psutil.disk_io_counters().read_bytes / (1024**3):.2f} GB")
            st.write(f"- Disk I/O (Write): {psutil.disk_io_counters().write_bytes / (1024**3):.2f} GB")
        
        with col_b:
            st.write("**Memory Integrity**")
            st.write(f"- Swap Memory: {psutil.swap_memory().percent}%")
            if stats["gpu"]["available"]:
                margin = 80 - stats["gpu"]["temp"] if isinstance(stats["gpu"]["temp"], (int, float)) else "N/A"
                st.write(f"- GPU Thermal Margin: **{margin}**°C until throttle")
            else:
                st.write("- GPU monitoring unavailable or blocked.")
                
            # Lexicon Summary Integration
            st.divider()
            st.write("**Lexicon Signal Library**")
            try:
                from src.core.factory import ToolFactory
                importer = ToolFactory.create_lexicon_importer()
                lex_summary = importer.get_category_summary()
                if lex_summary:
                    for cat, count in lex_summary.items():
                        st.write(f"- {cat.title()}: {count:,} signals")
                else:
                    st.caption("No forensic lexicons loaded yet.")
            except:
                st.caption("Lexicon Importer Unavailable")

    # Auto-refresh logic (simplified for prototype)
    if st.sidebar.button("Manual Refresh"):
        st.rerun()

if __name__ == "__main__":
    main()
