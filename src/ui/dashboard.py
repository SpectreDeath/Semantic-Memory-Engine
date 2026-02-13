import streamlit as st
import pandas as pd
import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
from src.ui.components import render_metric_cards, render_identity_matrix, render_log_streamer
from src.utils.entity_filter import is_valid_username

# Page Configuration
st.set_page_config(
    page_title="SME Glass Cockpit",
    page_icon="🧭",
    layout="wide",
)

from src.database.supabase_client import supabase

from src.utils.loaders import load_intel_data

@st.cache_data(ttl=120)
def load_supabase_data(table_name):
    """Load data from Supabase if available."""
    if not supabase:
        return None
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data
    except Exception as e:
        st.sidebar.warning(f"Supabase Load Failed ({table_name}): {e}")
        return None

import sys
from src.ui.report_gen import generate_session_report

# Sidebar: Control Panel
st.sidebar.title("🧭 System Controls")
st.sidebar.caption("SME Gathering Engine v1.7.0")

# Supabase Status
if supabase:
    st.sidebar.success("🔗 Supabase Connected")
else:
    st.sidebar.info("📂 Mode: Local JSON Only")

def run_script(command_list, label):
    st.sidebar.info(f"Initiating {label}...")
    log_area = st.empty()
    try:
        # Use sys.executable to ensure we use the same environment
        full_command = [sys.executable] + command_list
        proc = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.getcwd()
        )
        return_code = render_log_streamer(log_area, proc)
        if return_code == 0:
            st.sidebar.success(f"{label} Complete")
            st.balloons()
            st.cache_data.clear() # Force reload
        else:
            st.sidebar.error(f"{label} Failed")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Row 1: Reporting
st.sidebar.subheader("📄 Reporting")
c1, c2 = st.sidebar.columns(2)

with c1:
    if st.button("📦 Full Session PDF"):
        osint_temp = load_intel_data("data/raw/osint_results.json")
        news_temp = load_intel_data("data/raw/forensic_news.json")
        research_temp = load_intel_data("data/raw/research_papers.json")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_file = f"reports/forensic_report_{timestamp}.pdf"
        
        try:
            os.makedirs("reports", exist_ok=True)
            from src.ui.report_gen import generate_session_report
            generate_session_report(report_file, osint_temp, news_temp, research_temp)
            st.success(f"Generated: {os.path.basename(report_file)}")
            with open(report_file, "rb") as f:
                st.download_button("📥 Download", f, file_name=os.path.basename(report_file))
        except Exception as e:
            st.error(f"Error: {e}")

with c2:
    if st.button("🕵️ Case Report"):
        osint_temp = load_intel_data("data/raw/osint_results.json")
        news_temp = load_intel_data("data/raw/forensic_news.json")
        
        from src.ui.analytics import batch_analyze_news
        sentiment_df = batch_analyze_news(news_temp) if news_temp else None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_file = f"data/reports/target_case_{timestamp}.pdf"
        
        try:
            os.makedirs("data/reports", exist_ok=True)
            from src.ui.report_gen import generate_case_report
            generate_case_report(report_file, osint_temp, sentiment_df)
            st.success(f"Case Report Created: {os.path.basename(report_file)}")
            with open(report_file, "rb") as f:
                st.download_button("📥 Download Case", f, file_name=os.path.basename(report_file))
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Remote Control")

if st.sidebar.button("📡 Ingest Forensic News (RSS)"):
    run_script(["src/gathering/rss_bridge.py"], "RSS Ingestion")

if st.sidebar.button("🎓 Scrape Research (Scholar)"):
    run_script(["src/gathering/scholar_api.py"], "Scholar Scrape")

if st.sidebar.button("🚀 Run Full Operational Flow"):
    run_script(["src/pipeline.py"], "Full Intel Cascade")

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Target Management")
target_to_pivot = st.sidebar.text_input("Manual Pivot (Username)")
if st.sidebar.button("🕵️ Pivot & Scan"):
    if is_valid_username(target_to_pivot):
        run_script(["python", "src/gathering/osint_toolkit.py", "--username", target_to_pivot], f"Pivot Scan: {target_to_pivot}")
    else:
        st.sidebar.warning("Invalid username pattern.")

from src.ui.analytics import batch_analyze_news
from src.ui.dvc_utils import get_dvc_history, fetch_historical_json
import plotly.graph_objects as go

# Main Interface
st.title("🧭 SME Glass Cockpit")
st.caption("Local Forensic Visualization Layer | 1660 Ti Optimized")

# Data Refresh
# Prioritize Supabase, Fallback to JSON
db_osint = load_supabase_data("actors")
osint_data = db_osint if db_osint else load_intel_data("data/raw/osint_results.json")

db_news = load_supabase_data("news_articles")
news_data = db_news if db_news else load_intel_data("data/raw/forensic_news.json")

db_research = load_supabase_data("research_papers")
research_data = db_research if db_research else load_intel_data("data/raw/research_papers.json")

render_metric_cards(len(osint_data), len(news_data), len(research_data))

tab_matrix, tab_research, tab_tactical, tab_news, tab_sentiment, tab_history = st.tabs([
    "🧬 Identity Matrix", "🎓 Research Feed", "🕸️ Tactical View", "📰 News Flow", "🎭 Sentiment Radar", "🕰️ History Slider"
])

with tab_matrix:
    render_identity_matrix(osint_data)

with tab_research:
    st.subheader("🎓 Academic Abstracts & Target Pivoting")
    if research_data:
        for paper in sorted(research_data, key=lambda x: x.get('ingested_at', ''), reverse=True)[:10]:
            with st.expander(f"📄 {paper.get('title')}"):
                st.write(f"**TLDR:** {paper.get('tldr') or 'Summarization pending...'}")
                st.write(f"**Abstract Snippet:** {paper.get('abstract')[:300] if paper.get('abstract') else 'N/A'}...")
                
                st.write("**Identified Authors:**")
                auth_cols = st.columns(len(paper.get('authors', [])) or 1)
                for idx, author in enumerate(paper.get('authors', [])):
                    clean_name = author.replace(" ", "")
                    if auth_cols[idx % len(auth_cols)].button(f"🔭 Pivot {clean_name}", key=f"pivot_{clean_name}_{paper.get('paperId')}"):
                        run_script(["python", "src/gathering/osint_toolkit.py", "--username", clean_name], f"Auto-Pivot: {clean_name}")
    else:
        st.info("No research papers detected.")

with tab_tactical:
    from src.ui.components import render_tactical_graph
    selected_node = render_tactical_graph(osint_data)
    
    if selected_node:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Deep Trace Pivot")
        st.sidebar.info(f"Selected: **{selected_node}**")
        
        # Only pivot on usernames (actors), not platform nodes
        if not selected_node.startswith("plat_"):
            if st.sidebar.button(f"🔍 Deep Trace {selected_node}"):
                # Log manual pivot
                pivot_log = Path("data/raw/pivot_log.json")
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "target": selected_node,
                    "action": "Deep Trace Pivot"
                }
                try:
                    logs = []
                    if pivot_log.exists():
                        with open(pivot_log, 'r') as f:
                            logs = json.load(f)
                    logs.append(log_entry)
                    with open(pivot_log, 'w') as f:
                        json.dump(logs, f, indent=4)
                except:
                    pass
                
                # Targeted Execution
                run_script(["python", "src/gathering/osint_toolkit.py", "--username", selected_node], f"Deep Trace: {selected_node}")
        else:
            clean_plat = selected_node.replace("plat_", "")
            st.sidebar.write(f"Platform: **{clean_plat}**")

with tab_news:
    st.subheader("📰 Recent Forensic Alerts (Sentiment-Coded)")
    if news_data:
        # Prepare color-coded news stream
        news_df = pd.DataFrame(news_data)
        
        # Ensure sentiment is available
        if "polarity" not in news_df.columns:
            from src.ui.analytics import batch_analyze_news
            news_df = batch_analyze_news(news_data)
            
        def color_sentiment(val):
            if val < -0.3: return 'background-color: rgba(255, 75, 75, 0.2)' # Hostile
            if val > 0.3: return 'background-color: rgba(35, 134, 54, 0.2)'  # Academic/Positive
            return ''

        styled_df = news_df[["title", "source_feed", "published", "polarity"]].style.applymap(
            color_sentiment, subset=['polarity']
        )
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No news updates found.")

with tab_sentiment:
    st.subheader("🎭 Forensic Sentiment Radar")
    if news_data:
        # Lazy Loading analysis
        if st.button("🔍 Analyze Forensic Vibe"):
            sentiment_df = batch_analyze_news(news_data)
            avg_polarity = sentiment_df["polarity"].mean()
            
            # Gauge Chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = avg_polarity,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Collective Hostility/Tone (-1 to 1)"},
                gauge = {
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': "#ff4b4b" if avg_polarity < 0 else "#238636"},
                    'steps': [
                        {'range': [-1, -0.2], 'color': "rgba(255, 75, 75, 0.3)"},
                        {'range': [-0.2, 0.2], 'color': "rgba(255, 255, 255, 0.1)"},
                        {'range': [0.2, 1], 'color': "rgba(35, 134, 54, 0.3)"}
                    ]
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            # Identify Toxicity
            toxic_news = sentiment_df[sentiment_df["polarity"] < -0.3]
            if not toxic_news.empty:
                st.warning(f"⚠️ Detected {len(toxic_news)} potentially hostile/urgent signals.")
                st.dataframe(toxic_news[["title", "polarity"]], hide_index=True)
            else:
                st.success("No outlier hostility detected in news cycle.")
    else:
        st.info("No news data to analyze.")

with tab_history:
    st.subheader("🕰️ DVC Time Machine: Historical Comparison")
    dvc_history = get_dvc_history("data/raw/osint_results.json")
    
    if dvc_history:
        ver_option = st.selectbox("Select Historical Snapshot (Rev)", 
                                 [f"{h['hash']} - {h['msg']}" for h in dvc_history])
        commit_hash = ver_option.split(" ")[0]
        
        if st.button("🕒 Compare with Current"):
            hist_data = fetch_historical_json("data/raw/osint_results.json", commit_hash)
            if hist_data:
                # Comparison Logic
                curr_users = {s['username'] for s in osint_data}
                hist_users = {s['username'] for s in hist_data}
                
                new_actors = curr_users - hist_users
                lost_actors = hist_users - curr_users
                
                col1, col2 = st.columns(2)
                col1.metric("Newly Detected Actors", len(new_actors))
                col2.metric("Sunsetted Profiles", len(lost_actors))
                
                if new_actors:
                    st.write("**New Actor Footprints:**")
                    st.write(", ".join(list(new_actors)[:10]))
                
                st.info(f"Historical Snapshot loaded: {commit_hash}. Delta analysis complete.")
            else:
                st.error("Failed to load historical version.")
    else:
        st.info("No DVC history found for the identity database.")

# Footer
st.markdown("---")
st.caption(f"Engine Heartbeat: {datetime.now().strftime('%H:%M:%S')} | DVC Tracked: data/raw/")

# Footer
st.markdown("---")
st.caption(f"SME Engine v1.5.1 | Session Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
