import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="SME Command Center",
    page_icon="🕵️",
    layout="wide",
)

# Custom CSS for Dark Mode/Premium Look
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Helper: Load Data
def load_json(filepath):
    if not Path(filepath).exists():
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
        return []

# Sidebar: Controls
st.sidebar.title("🕵️ SME Ops")
st.sidebar.info("NVIDIA 1660 Ti Optimized")

if st.sidebar.button("🚀 Trigger Intel Run"):
    with st.spinner("Executing Forensic Pipeline..."):
        try:
            # Run the prefect pipeline
            result = subprocess.run(["python", "src/pipeline.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.sidebar.success("Pipeline Completed!")
                st.balloons()
            else:
                st.sidebar.error("Pipeline Failed")
                st.sidebar.code(result.stderr)
        except Exception as e:
            st.sidebar.error(f"Execution Error: {e}")

# Main Dash
st.title("SME Command Center")
st.write("Real-time Forensic Intelligence & Pivot Control")

# 1. Summary Metrics
osint_data = load_json("data/raw/osint_results.json")
news_data = load_json("data/raw/forensic_news.json")
research_data = load_json("data/raw/research_papers.json")

m1, m2, m3 = st.columns(3)
m1.metric("Actor Footprints", len(osint_data))
m2.metric("News Articles", len(news_data))
m3.metric("Research Papers", len(research_data))

# 2. Actor Heatmap (Frequency Analysis)
st.subheader("📊 Actor Footprint Analysis")
if osint_data:
    # Process for Heatmap
    platforms_found = []
    for scan in osint_data:
        username = scan.get('username', 'Unknown')
        for plat in scan.get('platforms', []):
            if plat.get('status') == 'found':
                platforms_found.append({
                    "Username": username,
                    "Platform": plat.get('name')
                })
    
    if platforms_found:
        df = pd.DataFrame(platforms_found)
        fig = px.density_heatmap(
            df, 
            x="Platform", 
            y="Username", 
            title="Entity Detection Heatmap",
            color_continuous_scale="Viridis",
            labels={'Username': 'Potential Actor', 'Platform': 'Platform Found'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No platform matches found yet.")
else:
    st.info("Run the pipeline to gather OSINT data.")

# 3. Intel Browser (Pivoted View)
st.subheader("🔍 Intelligence Browser")
tab1, tab2 = st.tabs(["Academic TLDRs", "Forensic News"])

with tab1:
    if research_data:
        for paper in sorted(research_data, key=lambda x: x.get('ingested_at', ''), reverse=True):
            with st.expander(f"📄 {paper.get('title')[:80]}..."):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.write(f"**Year:** {paper.get('year')}")
                    st.write(f"**Abstract:** {paper.get('abstract') or 'N/A'}")
                    st.write(f"**TLDR:** {paper.get('tldr') or 'No summary available.'}")
                with col_b:
                    st.write("**Authors (Targets):**")
                    for author in paper.get('authors', []):
                        st.code(author)
                    st.link_button("View Paper", paper.get('url', '#'))
    else:
        st.write("No research data found.")

with tab2:
    if news_data:
        for news in sorted(news_data, key=lambda x: x.get('published_iso', ''), reverse=True):
            with st.expander(f"📰 {news.get('title')}"):
                st.write(f"**Feed:** {news.get('source_feed')}")
                st.write(f"**Published:** {news.get('published')}")
                st.write(news.get('summary', 'No summary provided.'))
                st.link_button("Read Full Article", news.get('link', '#'))
    else:
        st.write("No news data found.")

# Footer
st.markdown("---")
st.caption(f"SME Engine v1.5.0 | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
