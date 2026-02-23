# =============================================================================
# OSINT Tasks
# =============================================================================
# Run OSINT footprinting and stream results to Gephi
# =============================================================================

from prefect import task, get_run_logger


@task(name="Run OSINT Toolkit")
def run_osint_scan(username):
    """Run OSINT footprinting for a specific target."""
    logger = get_run_logger()
    logger.info(f"🕵️ Scanning footprint for: {username}")
    
    from src.gathering.osint_toolkit import footprint_username, save_to_json
    results = footprint_username(username)
    save_to_json(results)
    return results


@task(name="Stream to Gephi Bipartite")
def stream_bipartite(osint_results_list):
    """Stream OSINT results to Gephi as a bipartite graph."""
    logger = get_run_logger()
    logger.info("📊 Streaming bipartite footprint to Gephi...")
    
    from src.utils.gephi_bridge import connect_to_gephi, graph
    
    gephi, connected = connect_to_gephi()
    if not connected:
        logger.warning("Gephi not available. Skipping stream.")
        return
        
    for res in osint_results_list:
        user_node = graph.Node(res["username"], Type="Actor", Color="Orange")
        gephi.add_node(user_node)
        
        for platform in res.get("platforms", []):
            if platform["status"] == "found":
                plat_node = graph.Node(platform["name"], Type="Platform", Color="Blue")
                gephi.add_node(plat_node)
                gephi.add_edge(graph.Edge(user_node, plat_node, Type="Found_On"))
    
    logger.info("Gephi bipartite streaming complete.")
