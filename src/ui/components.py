import streamlit as st
import pandas as pd
import json
from pathlib import Path

def render_metric_cards(osint_len, news_len, research_len):
    """Render high-level metrics."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Actor Footprints", osint_len)
    c2.metric("News Articles", news_len)
    c3.metric("Research Papers", research_len)

def render_identity_matrix(osint_data):
    """Render a color-coded matrix of Usernames vs Platforms."""
    if not osint_data:
        st.info("No OSINT data available for mapping.")
        return

    # Prepare matrix data
    data_map = []
    platforms = set()
    
    for scan in osint_data:
        user = scan.get("username", "Unknown")
        user_row = {"Username": user}
        for p in scan.get("platforms", []):
            name = p.get("name")
            status = p.get("status")
            platforms.add(name)
            
            # Map status to icons/colors
            if status == "found":
                user_row[name] = "🟢 FOUND"
            elif status == "not_found":
                user_row[name] = "🔴 MISSING"
            else:
                user_row[name] = "🟡 UNCERTAIN"
        data_map.append(user_row)
        
    df = pd.DataFrame(data_map).fillna("⚪ UNKNOWN")
    
    # Custom styling
    st.markdown("### 🧬 Identity Correlation Matrix")
    st.table(df) # st.table handles the density better for fixed matrices

from streamlit_agraph import agraph, Node, Edge, Config

def render_tactical_graph(osint_data):
    """Render a tactical relationship graph using streamlit-agraph."""
    st.markdown("### 🕸️ Identity Relationship Graph")
    
    if not osint_data:
        st.info("No OSINT data for graph visualization.")
        return None

    nodes = []
    edges = []
    seen_nodes = set()
    
    for scan in osint_data:
        user = scan.get("username", "Unknown")
        if user not in seen_nodes:
            # actor node
            nodes.append(Node(id=user, 
                             label=user, 
                             size=30, 
                             color="#FF4B4B", 
                             shape="dot",
                             font={'color': 'white', 'size': 14}))
            seen_nodes.add(user)
            
        for p in scan.get("platforms", []):
            if p.get("status") == "found":
                plat_name = p.get("name")
                plat_id = f"plat_{plat_name}"
                if plat_id not in seen_nodes:
                    # platform node
                    nodes.append(Node(id=plat_id, 
                                     label=plat_name, 
                                     size=20, 
                                     color="#238636",
                                     shape="diamond",
                                     font={'color': '#888', 'size': 12}))
                    seen_nodes.add(plat_id)
                
                edges.append(Edge(source=user, 
                                  target=plat_id, 
                                  color="#555555",
                                  width=2))
    
    config = Config(
        width=900, 
        height=500, 
        directed=False, 
        nodeHighlightBehavior=True, 
        highlightColor="#FF4B4B",
        collapsible=False,
        staticGraph=False,
        hierarchical=False,
    )

    return agraph(nodes=nodes, edges=edges, config=config)

def render_log_streamer(log_area, process):
    """Stream subprocess logs to the UI."""
    full_log = ""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            full_log += output
            # Display last 15 lines
            lines = full_log.splitlines()[-15:]
            log_area.code("\n".join(lines), language="text")
    return process.returncode
