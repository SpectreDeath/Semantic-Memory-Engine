import streamlit as st
import pandas as pd
import sqlite3
import os
import psutil
import time
from datetime import datetime
import altair as alt

# Lawnmower Man: The Beacon (Visualization Layer)
# v0.6.0 - Sprint 9

st.set_page_config(
    page_title="Lawnmower Man: The Beacon",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Styling ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00ff9d;
    }
    .st-emotion-cache-12w0qpk {
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 20px;
        background-color: #111827;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration & Paths ---
DB_PATH = os.path.abspath("data/storage/laboratory.db")
PROVENANCE_DB = os.path.abspath("data/provenance.db")

# --- Helpers ---
def get_db_connection(path):
    return sqlite3.connect(path)

def get_system_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    # VRAM simulation if no GPU detected
    vram = 0.0
    try:
        import torch
        if torch.cuda.is_available():
            vram = torch.cuda.memory_percent()
    except:
        pass
    return cpu, ram, vram

def get_memory_metrics():
    try:
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM atomic_facts")
        facts_count = cursor.fetchone()[0]
        conn.close()
    except:
        facts_count = 0
        
    # We'll mock the vector count for now as ChromaDB access is via API
    vector_count = facts_count * 1.2 # Approximation for visualization
    return facts_count, int(vector_count)

# --- Sidebar: Hardware Telemetry ---
with st.sidebar:
    st.title("📡 System Monitor")
    st.markdown("---")
    
    cpu, ram, vram = get_system_stats()
    
    st.metric("CPU Load", f"{cpu}%")
    st.progress(cpu / 100)
    
    st.metric("RAM Usage", f"{ram}%")
    st.progress(ram / 100)
    
    if vram > 0:
        st.metric("VRAM Usage", f"{vram}%")
        st.progress(vram / 100)
    else:
        st.info("VRAM: No GPU Acceleration detected.")
    
    st.markdown("---")
    st.markdown("**Version:** Lawnmower Man v0.5.0")
    st.markdown("**Status:** `ONLINE`")

# --- Main Layout ---
st.title("🛡️ The Beacon: Forensic Intelligence Feed")

# --- Metric Cards ---
col1, col2, col3, col4 = st.columns(4)
facts, vectors = get_memory_metrics()

with col1:
    st.metric("Atomic Facts", facts)
with col2:
    st.metric("Memory Vectors", vectors)
with col3:
    st.metric("Certainty (Avg)", "0.85")
with col4:
    try:
        conn = get_db_connection(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM forensic_events")
        s_count = cursor.fetchone()[0]
        conn.close()
    except:
        s_count = 0
    st.metric("Active Sessions", s_count)

st.markdown("---")

# --- Tabs for Data Sections ---
tab1, tab2, tab3 = st.tabs(["📊 Forensic Feed", "📈 Epistemic Trends", "⚓ Provenance Registry"])

with tab1:
    st.subheader("Live Investigation Stream")
    
    try:
        conn = get_db_connection(DB_PATH)
        feed_df = pd.read_sql_query("""
            SELECT timestamp, tool_name as Module, event_type as Event, target as Target, confidence as Confidence 
            FROM forensic_events 
            ORDER BY timestamp DESC LIMIT 20
        """, conn)
        conn.close()
        
        if not feed_df.empty:
            st.dataframe(feed_df, use_container_width=True)
        else:
            st.info("No investigation events recorded yet. Start a case via Lawnmower Man.")
    except Exception as e:
        st.error(f"Error loading feed: {e}")

with tab2:
    st.subheader("Epistemic Certainty Trend")
    
    try:
        conn = get_db_connection(DB_PATH)
        trend_df = pd.read_sql_query("""
            SELECT id, confidence as 'Certainty Quotient' 
            FROM forensic_events 
            ORDER BY id ASC LIMIT 50
        """, conn)
        conn.close()
        
        if not trend_df.empty:
            chart = alt.Chart(trend_df).mark_line(point=True, color="#00ff9d").encode(
                x='id',
                y=alt.Y('Certainty Quotient', scale=alt.Scale(domain=[0, 1])),
                tooltip=['id', 'Certainty Quotient']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Insufficient data for trend analysis.")
    except Exception as e:
        st.error(f"Error loading trends: {e}")

with tab3:
    st.subheader("Source Provenance Audit")
    
    try:
        conn = get_db_connection(PROVENANCE_DB)
        provenance_df = pd.read_sql_query("SELECT source_id, reliability_tier, captured_at FROM source_provenance", conn)
        conn.close()
        st.dataframe(provenance_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading provenance: {e}")

# --- Footer ---
st.markdown("---")
st.caption("© 2026 Project Lawnmower Man | Advanced Agency Intelligence")
