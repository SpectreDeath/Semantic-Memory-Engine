#!/usr/bin/env python3
"""
Multi-Mode Gephi Forensic Bridge

Streams project metadata and forensic data to Gephi for visualization.
Supports four distinct forensic modes: project, trust, knowledge, and synthetic.
Requires Gephi with Graph Streaming plugin running on http://localhost:8080/workspace0

Usage:
    python gephi_bridge.py --mode project
    python gephi_bridge.py --mode trust
    python gephi_bridge.py --mode knowledge
    python gephi_bridge.py --mode synthetic
    python gephi_bridge.py --mode trust --workspace workspace1
"""

import argparse
import asyncio
import glob
import json
import os
import requests
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# Optional: gephistreamer for Gephi visualization (not on PyPI)
try:
    from gephistreamer import graph, Streamer, GephiREST
    GEPHISTREAMER_AVAILABLE = True
except ImportError:
    GEPHISTREAMER_AVAILABLE = False
    graph = Streamer = GephiREST = None


# Hardware optimization: Maximum nodes limit for 1660 Ti
MAX_NODES = 2000


def read_active_persona():
    """Read current persona from active_persona.json."""
    try:
        with open('active_persona.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        try:
            with open('../active_persona.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"persona": "Unknown", "specialty": "Unknown", "timestamp": ""}


def connect_to_gephi(workspace="workspace0"):
    """Connect to Gephi with error handling."""
    if not GEPHISTREAMER_AVAILABLE:
        return None, False
    
    try:
        # Test if the endpoint is actually reachable first
        requests.get(f"http://localhost:8080", timeout=0.5)
        
        # Create the streamer with GephiREST backend
        adapter = GephiREST(hostname="localhost", port=8080, workspace=workspace)
        gephi = Streamer(adapter)
        return gephi, True
    except Exception as e:
        # print(f"Gephi connection failed: {e} - using mock mode")
        return None, False

class GephiBatcher:
    """
    Batches Gephi streaming operations to avoid memory spikes.
    Chunks nodes and edges into groups of 100.
    """
    def __init__(self, streamer, batch_size=100):
        self.streamer = streamer
        self.batch_size = batch_size
        self._node_queue = []
        self._edge_queue = []
        self.nodes_sent = 0
        self.edges_sent = 0

    def add_node(self, node):
        if not self.streamer:
            return
        self._node_queue.append(node)
        if len(self._node_queue) >= self.batch_size:
            self.flush_nodes()

    def add_edge(self, edge):
        if not self.streamer:
            return
        self._edge_queue.append(edge)
        if len(self._edge_queue) >= self.batch_size:
            self.flush_edges()

    def flush_nodes(self):
        if not self.streamer or not self._node_queue:
            return
        for node in self._node_queue:
            self.streamer.add_node(node)
        self.nodes_sent += len(self._node_queue)
        self._node_queue = []

    def flush_edges(self):
        if not self.streamer or not self._edge_queue:
            return
        for edge in self._edge_queue:
            self.streamer.add_edge(edge)
        self.edges_sent += len(self._edge_queue)
        self._edge_queue = []

    def flush(self):
        self.flush_nodes()
        self.flush_edges()


def get_file_metadata():
    """Extract metadata for all Python and key files in project."""
    files = []
    patterns = ['*.py', '*.md', '*.json', '*.csv', '*.txt']
    
    for pattern in patterns:
        for file_path in glob.glob(f'**/{pattern}', recursive=True):
            if os.path.getsize(file_path) > 0:  # Skip empty files
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                except:
                    lines = 0
                
                files.append({
                    'path': file_path,
                    'name': Path(file_path).name,
                    'ext': Path(file_path).suffix,
                    'lines': lines,
                    'dir': str(Path(file_path).parent)
                })
    
    return files


def get_outlier_data():
    """Read outlier data from audit_results.csv."""
    outliers = {}
    try:
        df = pd.read_csv('data/results/audit_results.csv')
        for _, row in df.iterrows():
            filename = row.get('filename', row.get('file', 'unknown'))
            outliers[filename] = row.get('is_outlier', False)
    except FileNotFoundError:
        pass
    return outliers


def stream_project_mode(workspace="workspace0"):
    """
    Project Mode: Stream project metadata to Gephi.
    Creates nodes for files and edges between related files.
    """
    print("=== PROJECT MODE: Streaming project metadata ===")
    
    gephi_streamer, connected = connect_to_gephi(workspace)
    batcher = GephiBatcher(gephi_streamer if connected else None)
    
    # Get data
    persona_data = read_active_persona()
    files = get_file_metadata()
    outliers = get_outlier_data()
    
    print(f"Found {len(files)} files to process...")
    print(f"Current persona: {persona_data['persona']}")
    
    # Process nodes
    nodes_added = 0
    for file_info in files:
        if nodes_added >= MAX_NODES:
            print(f"Reached maximum node limit of {MAX_NODES}")
            break
            
        node_id = file_info['path']
        node = graph.Node(
            node_id,
            label=file_info['name'],
            attributes={
                'persona': persona_data['persona'],
                'specialty': persona_data['specialty'],
                'extension': file_info['ext'],
                'lines': file_info['lines'],
                'directory': file_info['dir'],
                'mode': 'project'
            }
        )
        
        # Set visual properties
        if file_info['name'] in outliers and outliers[file_info['name']]:
            node.r, node.g, node.b = 1.0, 0.0, 0.0
        else:
            node.r, node.g, node.b = 0.0, 1.0, 0.0
        
        node.size = max(10, min(100, file_info['lines'] // 10))
        
        batcher.add_node(node)
        nodes_added += 1
        if nodes_added % 50 == 0:
            print(f"  Processed {nodes_added} nodes...")
    
    batcher.flush_nodes()
    
    # Create edges
    edges_added = 0
    dir_groups = {}
    for file_info in files:
        dir_path = file_info['dir']
        if dir_path not in dir_groups:
            dir_groups[dir_path] = []
        dir_groups[dir_path].append(file_info['path'])
    
    for dir_path, file_list in dir_groups.items():
        if len(file_list) > 1:
            for i in range(len(file_list)):
                for j in range(i + 1, len(file_list)):
                    if edges_added >= MAX_NODES:
                        break
                    edge_id = f"{file_list[i]}-{file_list[j]}"
                    edge = graph.Edge(edge_id, file_list[i], file_list[j])
                    batcher.add_edge(edge)
                    edges_added += 1
                    if edges_added % 100 == 0:
                        print(f"  Processed {edges_added} edges...")
    
    batcher.flush_edges()
    
    print(f"Total: {nodes_added} nodes, {edges_added} edges processed.")
    if connected:
        print("Project mode streaming complete!")


def stream_trust_mode(workspace="workspace0"):
    """
    Trust Mode (Epistemic View): Stream trust scores to Gephi.
    """
    print("=== TRUST MODE: Streaming epistemic trust scores ===")
    
    gephi_streamer, connected = connect_to_gephi(workspace)
    batcher = GephiBatcher(gephi_streamer if connected else None)
    
    try:
        df = pd.read_csv('data/results/trust_scores_results.csv')
        print(f"Loaded {len(df)} trust scores.")
        
        nodes_added = 0
        for _, row in df.iterrows():
            if nodes_added >= MAX_NODES:
                break
                
            node_id = row['node_id']
            trust_score = float(row['trust_score'])
            
            node = graph.Node(
                node_id,
                label=f"{node_id} (Trust: {trust_score:.2f})",
                attributes={'trust_score': trust_score, 'mode': 'trust'}
            )
            
            node.size = 20 + (trust_score * 50)
            
            if trust_score < 0.5:
                node.r, node.g, node.b = 1.0, 0.0, 0.0
            elif trust_score < 0.8:
                node.r, node.g, node.b = 1.0, 1.0, 0.0
            else:
                node.r, node.g, node.b = 0.0, 1.0, 0.0
            
            batcher.add_node(node)
            nodes_added += 1
        
        batcher.flush()
        print(f"Processed {nodes_added} trust nodes")
        if connected:
            print("Trust mode streaming complete!")
        else:
            print("Mock processing complete - Gephi not available")
            
    except FileNotFoundError:
        print("Error: data/trust_scores.csv not found")
    except Exception as e:
        print(f"Error processing trust data: {e}")


def stream_knowledge_mode(workspace="workspace0"):
    """
    Knowledge Mode (Semantic Memory): Stream knowledge graph from SQLite.
    """
    print("=== KNOWLEDGE MODE: Streaming semantic memory graph ===")
    
    gephi_streamer, connected = connect_to_gephi(workspace)
    batcher = GephiBatcher(gephi_streamer if connected else None)
    
    conn = None
    try:
        conn = sqlite3.connect('data/knowledge_core.sqlite')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, label FROM concepts LIMIT 1000")
        concepts = cursor.fetchall()
        print(f"Loaded {len(concepts)} concepts.")
        
        nodes_added = 0
        concept_ids = set()
        for concept_id, label in concepts:
            if nodes_added >= MAX_NODES:
                break
                
            node = graph.Node(
                f"concept_{concept_id}",
                label=label,
                attributes={'concept_id': concept_id, 'mode': 'knowledge'}
            )
            node.size = 30
            node.r, node.g, node.b = 0.5, 0.5, 1.0
            
            batcher.add_node(node)
            nodes_added += 1
            concept_ids.add(concept_id)
        
        batcher.flush_nodes()
        
        cursor.execute("SELECT source_concept_id, target_concept_id, weight, relationship_type FROM assertions WHERE weight > 0.5")
        assertions = cursor.fetchall()
        print(f"Loaded {len(assertions)} assertions.")
        
        edges_added = 0
        for source_id, target_id, weight, rel_type in assertions:
            if edges_added >= MAX_NODES:
                break
            if source_id in concept_ids and target_id in concept_ids:
                edge = graph.Edge(f"assertion_{source_id}_{target_id}", f"concept_{source_id}", f"concept_{target_id}",
                               attributes={'weight': weight, 'relationship_type': rel_type, 'mode': 'knowledge'})
                edge.weight = weight
                batcher.add_edge(edge)
                edges_added += 1
        
        batcher.flush_edges()
        print(f"Processed {nodes_added} nodes and {edges_added} edges")
        if connected:
            print("Knowledge mode streaming complete!")
        else:
            print("Mock processing complete - Gephi not available")
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error processing knowledge data: {e}")
    finally:
        if conn:
            conn.close()


def stream_synthetic_mode(workspace="workspace0"):
    """
    Synthetic Mode (Counter-Intel): Stream synthetic audit data.
    Orange nodes for pattern signatures, Purple nodes for vaulted documents.
    """
    print("=== SYNTHETIC MODE: Streaming counter-intelligence data ===")
    
    gephi_streamer, connected = connect_to_gephi(workspace)
    batcher = GephiBatcher(gephi_streamer if connected else None)
    
    try:
        # Read synthetic audit data
        df = pd.read_csv('data/results/synthetic_audit_results.csv')
        print(f"Loaded {len(df)} synthetic audit records.")
        
        nodes_added = 0
        edges_added = 0
        
        # Track created nodes for edge creation
        created_nodes = {}
        
        for _, row in df.iterrows():
            if nodes_added >= MAX_NODES:
                print(f"Reached maximum node limit of {MAX_NODES}")
                break
                
            signature_id = row['signature_id']
            pattern_type = row['pattern_type']
            confidence_score = float(row['confidence_score'])
            # Handle both string and boolean values for vaulted field
            vaulted_str = str(row['vaulted']).lower()
            vaulted = vaulted_str == 'true' or vaulted_str == '1'
            
            # Create node with appropriate color
            node = graph.Node(
                signature_id,
                label=f"{signature_id}\n{pattern_type}\nConf: {confidence_score:.2f}",
                attributes={
                    'pattern_type': pattern_type,
                    'confidence_score': confidence_score,
                    'vaulted': vaulted,
                    'mode': 'synthetic',
                    'node_type': 'signature'
                }
            )
            
            node.size = 20 + (confidence_score * 60)
            
            if vaulted:
                node.r, node.g, node.b = 0.5, 0.0, 0.5
            else:
                node.r, node.g, node.b = 1.0, 0.5, 0.0
            
            batcher.add_node(node)
            nodes_added += 1
            created_nodes[signature_id] = True
        
        batcher.flush_nodes()
        
        # Create edges between related patterns (same type)
        pattern_groups = {}
        for _, row in df.iterrows():
            pattern_type = row['pattern_type']
            signature_id = row['signature_id']
            
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(signature_id)
        
        for pattern_type, signatures in pattern_groups.items():
            if len(signatures) > 1:
                for i in range(len(signatures)):
                    for j in range(i + 1, len(signatures)):
                        if edges_added >= MAX_NODES:
                            print(f"Reached maximum edge limit of {MAX_NODES}")
                            break
                        if signatures[i] in created_nodes and signatures[j] in created_nodes:
                            edge = graph.Edge(f"{signatures[i]}-{signatures[j]}", signatures[i], signatures[j], attributes={'mode': 'synthetic'})
                            batcher.add_edge(edge)
                            edges_added += 1
        
        batcher.flush_edges()
        print(f"Processed {nodes_added} synthetic nodes and {edges_added} edges")
        if connected:
            print("Synthetic mode streaming complete!")
        else:
            print("Mock processing complete - Gephi not available")
            
    except FileNotFoundError:
        print("Error: data/synthetic_audit.csv not found")
    except Exception as e:
        print(f"Error processing synthetic data: {e}")


def stream_archival_data(url, snapshots, divergences, workspace="workspace0"):
    """
    Streams archival snapshot history and semantic drift to Gephi.
    """
    print(f"=== ARCHIVAL MODE: Streaming historical forensics for {url} ===")
    gephi_streamer, connected = connect_to_gephi(workspace)
    batcher = GephiBatcher(gephi_streamer if connected else None)

    nodes_added = 0
    
    # 1. Create central URL node
    url_node = graph.Node(url, label=url, size=50, r=0.0, g=0.5, b=1.0)
    batcher.add_node(url_node)
    nodes_added += 1

    # 2. Add snapshots as temporal nodes
    for snap in snapshots:
        ts = snap['timestamp']
        node = graph.Node(
            ts, 
            label=f"Snapshot: {snap['human_date']}",
            attributes={
                'timestamp': ts,
                'digest': snap['digest'],
                'mode': 'archival'
            }
        )
        node.size = 30
        
        # Color based on whether it's part of a divergence
        is_divergent = any(d['post_change']['timestamp'] == ts for d in divergences)
        if is_divergent:
            node.r, node.g, node.b = 1.0, 0.0, 0.0 # Red for divergent
        else:
            node.r, node.g, node.b = 0.0, 1.0, 0.0 # Green for stable
            
        batcher.add_node(node)
        nodes_added += 1
        
        # Link to main URL
        edge = graph.Edge(f"{url}-{ts}", url, ts, attributes={'mode': 'archival'})
        batcher.add_edge(edge)

    # 3. Add drift edges between divergent snapshots
    for d in divergences:
        e_id = f"drift-{d['pre_change']['timestamp']}-{d['post_change']['timestamp']}"
        drift_score = d.get('semantic_drift', 0.0)
        edge = graph.Edge(
            e_id, 
            d['pre_change']['timestamp'], 
            d['post_change']['timestamp'],
            label=f"Drift: {drift_score:.2%}",
            attributes={
                'semantic_drift': drift_score,
                'mode': 'archival',
                'relationship': 'temporal_divergence'
            }
        )
        batcher.add_edge(edge)

    batcher.flush()
    print(f"Processed {nodes_added} archival nodes and related edges")


def main():
    """Main entry point with argparse support."""
    parser = argparse.ArgumentParser(
        description="Multi-Mode Gephi Forensic Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gephi_bridge.py --mode project
  python gephi_bridge.py --mode trust
  python gephi_bridge.py --mode knowledge
  python gephi_bridge.py --mode synthetic
  python gephi_bridge.py --mode trust --workspace workspace1
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['project', 'trust', 'knowledge', 'synthetic', 'archival'],
        default='project',
        help='Forensic mode to run (default: project)'
    )
    
    parser.add_argument(
        '--url',
        help='Target URL for archival mode'
    )
    
    parser.add_argument(
        '--workspace',
        default='workspace0',
        help='Target Gephi workspace (default: workspace0)'
    )
    
    args = parser.parse_args()
    
    print(f"Starting Gephi Forensic Bridge")
    print(f"Mode: {args.mode}")
    print(f"Workspace: {args.workspace}")
    print(f"Max Nodes Limit: {MAX_NODES} (Hardware optimization for 1660 Ti)")
    print("-" * 50)
    
    # Route to appropriate mode handler
    if args.mode == 'project':
        stream_project_mode(args.workspace)
    elif args.mode == 'trust':
        stream_trust_mode(args.workspace)
    elif args.mode == 'knowledge':
        stream_knowledge_mode(args.workspace)
    elif args.mode == 'synthetic':
        stream_synthetic_mode(args.workspace)
    elif args.mode == 'archival':
        if not args.url:
            print("Error: --url is required for archival mode")
            sys.exit(1)
        # For CLI usage, we'd need to invoke WaybackScout here
        # But since we're mostly using this as a library, we'll keep it simple
        print("Archival mode via CLI: Please use the integration script or provide --url")
        from src.extensions.ext_archival_diff.scout import WaybackScout
        scout = WaybackScout()
        history = asyncio.run(scout.get_snapshot_history(args.url))
        divergences = scout.identify_divergent_points(history)
        stream_archival_data(args.url, history, divergences, args.workspace)


if __name__ == "__main__":
    main()
