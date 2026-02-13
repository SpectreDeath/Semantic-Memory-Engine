#!/usr/bin/env python3
"""
Gephi Export Tool — MCP-compatible tool for AionUi chat invocation.

Provides three MCP tools:
  • gephi_export        — legacy file-based .gexf export (delegates to gephi_bridge.py)
  • stream_forensics    — bipartite live-stream to Gephi with VRAM-aware chunking
  • gephi_list_exports  — list previously exported .gexf files

Usage (standalone):
    python gephi_export_tool.py        # starts MCP stdio server

From AionUi chat:
    "Export the trust graph to Gephi"
    "/stream-forensics"
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # D:\SME
GEPHI_BRIDGE = PROJECT_ROOT / "src" / "utils" / "gephi_bridge.py"
EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
PYTHON_EXE = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

VALID_MODES = ("project", "trust", "knowledge", "synthetic")

# Bipartite Deep-Stream constants
CHUNK_SIZE = 5000           # max nodes per chunk before VRAM check
CAUTION_THRESHOLD_MB = 5800 # from constitution & spec 004
VRAM_RETRY_DELAY_S = 10
VRAM_MAX_RETRIES = 3

# Node colours (RGB 0.0–1.0)
TARGET_COLOR = (1.0, 0.2, 0.2)   # Red for primary threat actors
FOOTPRINT_COLOR = (0.3, 0.5, 1.0)  # Blue for secondary artifacts

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP("GephiExporter")


# ========================== VRAM GUARD ====================================

def _get_vram_usage_mb() -> int:
    """Return current VRAM usage in MB via pynvml, or -1 on failure."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        used = mem.used // (1024 * 1024)
        pynvml.nvmlShutdown()
        return used
    except Exception:
        return -1


def _vram_safe_to_continue() -> tuple[bool, int]:
    """
    Check whether VRAM usage is below the CAUTION threshold.
    Returns (is_safe, current_vram_mb).
    If pynvml is unavailable, assumes safe (returns True, -1).
    """
    vram = _get_vram_usage_mb()
    if vram < 0:
        return True, -1
    return vram < CAUTION_THRESHOLD_MB, vram


def _wait_for_vram_headroom() -> dict:
    """
    Block until VRAM drops below CAUTION or retries are exhausted.
    Returns a status dict for inclusion in tool output.
    """
    for attempt in range(1, VRAM_MAX_RETRIES + 1):
        safe, vram = _vram_safe_to_continue()
        if safe:
            return {"vram_ok": True, "vram_mb": vram, "waited_attempts": attempt - 1}
        time.sleep(VRAM_RETRY_DELAY_S)

    # Exhausted retries
    _, vram = _vram_safe_to_continue()
    return {"vram_ok": False, "vram_mb": vram, "waited_attempts": VRAM_MAX_RETRIES}


# ========================== BIPARTITE BUILDER =============================

def _build_bipartite_graph(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Build bipartite node/edge lists from threat_leads rows.

    Returns (nodes, edges) where each node/edge is a dict ready for
    gephistreamer or GEXF serialization.
    """
    nodes = []
    edges = []
    footprint_registry: dict[str, str] = {}  # value → footprint node_id

    def _get_footprint_id(value: str) -> str:
        if value not in footprint_registry:
            fid = f"fp_{len(footprint_registry)}"
            footprint_registry[value] = fid
            nodes.append({
                "id": fid,
                "label": value,
                "node_class": "footprint",
                "probability_score": 0.0,
                "source_origin": "derived",
                "r": FOOTPRINT_COLOR[0],
                "g": FOOTPRINT_COLOR[1],
                "b": FOOTPRINT_COLOR[2],
                "size": 20,
            })
        return footprint_registry[value]

    # Pass 1 — Target nodes
    for i, row in enumerate(rows):
        tid = f"target_{i}"
        target_node = {
            "id": tid,
            "label": row.get("name", row.get("actor", f"Actor_{i}")),
            "node_class": "target",
            "probability_score": float(row.get("confidence_score", 0)),
            "source_origin": row.get("source", row.get("incident_type", "unknown")),
            "confidence_score": float(row.get("confidence_score", 0)),
            "first_seen": str(row.get("first_seen", "")),
            "incident_type": str(row.get("incident_type", "")),
            "ai_verdict": str(row.get("ai_verdict", "")),
            "r": TARGET_COLOR[0],
            "g": TARGET_COLOR[1],
            "b": TARGET_COLOR[2],
            "size": max(20, min(80, int(float(row.get("confidence_score", 0)) * 80))),
        }
        nodes.append(target_node)

        # Pass 2 — Footprint extraction & edges (Target → Footprint)
        footprints_for_target = []

        # Aliases
        aliases = row.get("aliases", "")
        if isinstance(aliases, str) and aliases:
            for alias in aliases.split(","):
                alias = alias.strip()
                if alias:
                    fid = _get_footprint_id(alias)
                    footprints_for_target.append(fid)
                    edges.append({
                        "id": f"e_{tid}_{fid}",
                        "source": tid,
                        "target": fid,
                        "type": "owns_alias",
                    })

        # IP addresses
        ips = row.get("ip_addresses", row.get("ips", ""))
        if isinstance(ips, str) and ips:
            for ip in ips.split(","):
                ip = ip.strip()
                if ip:
                    fid = _get_footprint_id(ip)
                    footprints_for_target.append(fid)
                    edges.append({
                        "id": f"e_{tid}_{fid}",
                        "source": tid,
                        "target": fid,
                        "type": "uses_ip",
                    })

        # Fingerprints / tool artifacts
        fingerprints = row.get("fingerprints", row.get("metadata_fingerprints", ""))
        if isinstance(fingerprints, str) and fingerprints:
            for fp in fingerprints.split(","):
                fp = fp.strip()
                if fp:
                    fid = _get_footprint_id(fp)
                    footprints_for_target.append(fid)
                    edges.append({
                        "id": f"e_{tid}_{fid}",
                        "source": tid,
                        "target": fid,
                        "type": "leaves_fingerprint",
                    })

        # Store footprints list on Target node for co-occurrence computation
        target_node["_footprints"] = footprints_for_target  # transient, stripped before output

    # Pass 3 — Target ↔ Target co-occurrence edges
    target_nodes = [n for n in nodes if n["node_class"] == "target"]
    for i, t1 in enumerate(target_nodes):
        for j in range(i + 1, len(target_nodes)):
            t2 = target_nodes[j]
            shared = set(t1.get("_footprints", [])) & set(t2.get("_footprints", []))
            if shared:
                edges.append({
                    "id": f"cooccur_{t1['id']}_{t2['id']}",
                    "source": t1["id"],
                    "target": t2["id"],
                    "type": "co_occurrence",
                    "weight": len(shared),
                })

    # Strip transient key
    for n in nodes:
        n.pop("_footprints", None)

    return nodes, edges


# ========================== GEXF WRITER ===================================

def _write_gexf(nodes: list[dict], edges: list[dict], output_path: Path) -> str:
    """Write a bipartite graph to a .gexf file with streaming writes."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<gexf xmlns="http://gexf.net/1.3" version="1.3">\n')
        f.write('  <meta lastmodifieddate="{}">\n'.format(datetime.now().strftime("%Y-%m-%d")))
        f.write('    <creator>SME Gephi Exporter — Bipartite Deep-Stream</creator>\n')
        f.write('  </meta>\n')
        f.write('  <graph defaultedgetype="undirected" mode="static">\n')

        # Attribute declarations
        f.write('    <attributes class="node">\n')
        for i, attr in enumerate(["node_class", "probability_score", "source_origin",
                                   "confidence_score", "first_seen", "incident_type", "ai_verdict"]):
            atype = "float" if attr in ("probability_score", "confidence_score") else "string"
            f.write(f'      <attribute id="{i}" title="{attr}" type="{atype}"/>\n')
        f.write('    </attributes>\n')

        # Nodes
        f.write('    <nodes>\n')
        attr_keys = ["node_class", "probability_score", "source_origin",
                     "confidence_score", "first_seen", "incident_type", "ai_verdict"]
        for node in nodes:
            label = str(node.get("label", "")).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
            f.write(f'      <node id="{node["id"]}" label="{label}">\n')
            f.write('        <attvalues>\n')
            for i, key in enumerate(attr_keys):
                val = str(node.get(key, "")).replace("&", "&amp;").replace('"', "&quot;")
                f.write(f'          <attvalue for="{i}" value="{val}"/>\n')
            f.write('        </attvalues>\n')
            r, g, b = int(node.get("r", 0.5) * 255), int(node.get("g", 0.5) * 255), int(node.get("b", 0.5) * 255)
            f.write(f'        <viz:color r="{r}" g="{g}" b="{b}"/>\n')
            f.write(f'        <viz:size value="{node.get("size", 30)}"/>\n')
            f.write('      </node>\n')
        f.write('    </nodes>\n')

        # Edges
        f.write('    <edges>\n')
        for edge in edges:
            weight = f' weight="{edge["weight"]}"' if "weight" in edge else ""
            f.write(f'      <edge id="{edge["id"]}" source="{edge["source"]}" '
                    f'target="{edge["target"]}" label="{edge.get("type", "")}"{weight}/>\n')
        f.write('    </edges>\n')

        f.write('  </graph>\n')
        f.write('</gexf>\n')

    return str(output_path)


# ========================== GEPHI LIVE PUSH ===============================

def _stream_to_gephi(nodes: list[dict], edges: list[dict], workspace: str) -> dict:
    """
    Push bipartite graph to a running Gephi instance via gephistreamer.
    Implements chunked streaming with VRAM guard.
    """
    try:
        from gephistreamer import graph, Streamer, GephiREST
        import requests
        requests.get("http://localhost:8080", timeout=2)
    except Exception:
        return {"connected": False, "reason": "Gephi not reachable on localhost:8080"}

    gephi = Streamer(GephiREST(hostname="localhost", port=8080, workspace=workspace))

    nodes_sent = 0
    chunk_alerts = []

    for node in nodes:
        n = graph.Node(
            node["id"],
            label=node.get("label", ""),
            attributes={k: v for k, v in node.items()
                        if k not in ("id", "label", "r", "g", "b", "size")}
        )
        n.r = node.get("r", 0.5)
        n.g = node.get("g", 0.5)
        n.b = node.get("b", 0.5)
        n.size = node.get("size", 30)
        gephi.add_node(n)
        nodes_sent += 1

        # VRAM guard at chunk boundaries
        if nodes_sent % CHUNK_SIZE == 0 and nodes_sent > 0:
            guard = _wait_for_vram_headroom()
            chunk_alerts.append({"at_node": nodes_sent, **guard})
            if not guard["vram_ok"]:
                return {
                    "connected": True,
                    "nodes_sent": nodes_sent,
                    "aborted": True,
                    "reason": f"VRAM at {guard['vram_mb']}MB exceeds limit ({CAUTION_THRESHOLD_MB}MB) after {VRAM_MAX_RETRIES} retries",
                    "chunk_alerts": chunk_alerts,
                }

    # Edges
    for edge in edges:
        e = graph.Edge(
            edge["id"], edge["source"], edge["target"],
            attributes={"type": edge.get("type", ""), "weight": edge.get("weight", 1)}
        )
        if "weight" in edge:
            e.weight = edge["weight"]
        gephi.add_edge(e)

    return {
        "connected": True,
        "nodes_sent": nodes_sent,
        "edges_sent": len(edges),
        "aborted": False,
        "chunk_alerts": chunk_alerts,
    }


# ========================== MCP TOOLS =====================================

@mcp.tool()
def stream_forensics(
    mode: str = "trust",
    workspace: str = "workspace0",
    live: bool = True,
) -> str:
    """
    Bipartite Deep-Stream: build a bipartite graph from threat_leads and
    push it live to Gephi or save as .gexf.

    This is the tool bound to the /stream-forensics command in AionUi.

    Args:
        mode: Forensic mode — 'trust', 'project', 'knowledge', 'synthetic'.
        workspace: Target Gephi workspace.
        live: If True, push to running Gephi. If False, save .gexf file only.

    Returns:
        JSON status with node/edge counts, VRAM guard results, and file path.
    """
    # --- Fetch data (mock for now — replace with Supabase query via bridge) ---
    rows = _fetch_threat_leads()

    if not rows:
        return json.dumps({"status": "warning", "message": "No threat_leads data found."})

    # --- Build bipartite graph ---
    nodes, edges = _build_bipartite_graph(rows)

    result = {
        "status": "success",
        "mode": mode,
        "total_nodes": len(nodes),
        "target_nodes": sum(1 for n in nodes if n.get("node_class") == "target"),
        "footprint_nodes": sum(1 for n in nodes if n.get("node_class") == "footprint"),
        "total_edges": len(edges),
    }

    # --- Always save .gexf ---
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = EXPORT_DIR / f"bipartite_{mode}_{ts}.gexf"
    _write_gexf(nodes, edges, output_file)
    result["output_file"] = str(output_file)

    # --- Live push to Gephi ---
    if live:
        stream_result = _stream_to_gephi(nodes, edges, workspace)
        result["gephi_connected"] = stream_result.get("connected", False)
        result["gephi_stream"] = stream_result

        if not stream_result.get("connected"):
            result["note"] = (
                f"File saved to {output_file}. "
                "Gephi is not running — open Gephi and load the file manually."
            )
        elif stream_result.get("aborted"):
            result["note"] = (
                f"Streaming aborted at {stream_result['nodes_sent']} nodes due to VRAM pressure. "
                f"File saved to {output_file}."
            )
        else:
            result["note"] = "Bipartite graph streamed to Gephi and saved to file."
    else:
        result["note"] = f"File export only. Saved to {output_file}."

    return json.dumps(result, indent=2)


@mcp.tool()
def gephi_export(mode: str = "trust", workspace: str = "workspace0") -> str:
    """
    Export forensic data to a .gexf file for Gephi visualization.
    Delegates to the legacy Multi-Mode Gephi Bridge.

    Args:
        mode: One of 'project', 'trust', 'knowledge', 'synthetic'.
        workspace: Target Gephi workspace. Defaults to 'workspace0'.

    Returns:
        JSON string with export status and file path.
    """
    if mode not in VALID_MODES:
        return json.dumps({
            "status": "error",
            "message": f"Invalid mode '{mode}'. Choose from: {', '.join(VALID_MODES)}"
        })

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = EXPORT_DIR / f"{mode}_{ts}.gexf"

    cmd = [
        str(PYTHON_EXE),
        str(GEPHI_BRIDGE),
        "--mode", mode,
        "--workspace", workspace,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(PROJECT_ROOT),
            timeout=120,
        )

        gephi_available = "Mock processing" not in result.stdout

        return json.dumps({
            "status": "success",
            "mode": mode,
            "workspace": workspace,
            "output_file": str(output_file),
            "gephi_connected": gephi_available,
            "bridge_output": result.stdout.strip()[-500:],
            "note": (
                "Graph exported and streamed to Gephi."
                if gephi_available
                else "File saved. Gephi is not running — open Gephi and load the file manually."
            ),
        }, indent=2)

    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": "Gephi bridge timed out after 120 seconds."})
    except FileNotFoundError:
        return json.dumps({"status": "error", "message": f"Python not found at {PYTHON_EXE}."})
    except Exception as exc:
        return json.dumps({"status": "error", "message": f"Unexpected error: {exc}"})


@mcp.tool()
def gephi_list_exports() -> str:
    """
    List all previously exported .gexf files in data/exports/.

    Returns:
        JSON array of export files with name, size, and modification time.
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    exports = []
    for f in sorted(EXPORT_DIR.glob("*.gexf"), key=os.path.getmtime, reverse=True):
        stat = f.stat()
        exports.append({
            "file": f.name,
            "path": str(f),
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return json.dumps(exports, indent=2)


# ========================== DATA FETCH ====================================

def _fetch_threat_leads() -> list[dict]:
    """
    Fetch threat_leads from Supabase via the existing bridge/client.
    Falls back to local CSV or returns empty list if unavailable.
    """
    # Try Supabase client first
    try:
        # Import only within 3.14 context
        from src.database.supabase_client import get_threat_leads
        results = get_threat_leads()
        if results:
            return results
    except Exception as e:
        print(f"⚠️ Supabase fetch failed: {e}")

    # Fallback: try local CSV
    import csv
    csv_path = PROJECT_ROOT / "data" / "results" / "threat_leads.csv"
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    # Fallback: try trust_scores for demo
    csv_path = PROJECT_ROOT / "data" / "results" / "trust_scores_results.csv"
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            # Map CSV columns to expected schema
            return [
                {
                    "name": row.get("node_id", f"Actor_{i}"),
                    "confidence_score": row.get("trust_score", 0),
                    "incident_type": "trust_assessment",
                    "source": "trust_engine",
                    "ai_verdict": "assessed",
                    "first_seen": "",
                    "aliases": "",
                    "ip_addresses": "",
                    "fingerprints": "",
                }
                for i, row in enumerate(rows)
            ]

    return []


# ========================== ENTRY POINT ===================================

if __name__ == "__main__":
    mcp.run()
