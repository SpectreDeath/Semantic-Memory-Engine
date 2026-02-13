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
import glob
import json
import os
import sqlite3
from pathlib import Path

import pandas as pd
from gephistreamer import graph, Streamer, GephiREST


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
    try:
        # Test if the endpoint is actually reachable first
        import requests
        requests.get(f"http://localhost:8080", timeout=2)
        
        # Create the streamer with GephiREST backend
        gephi = Streamer(GephiREST(hostname="localhost", port=8080, workspace=workspace))
        return gephi, True
    except Exception as e:
        # print(f"Gephi connection failed: {e} - using mock mode")
        return None, False


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
    
    gephi, connected = connect_to_gephi(workspace)
    
    # Get data
    persona_data = read_active_persona()
    files = get_file_metadata()
    outliers = get_outlier_data()
    
    print(f"Found {len(files)} files to process...")
    print(f"Current persona: {persona_data['persona']}")
    
    # Process nodes and edges
    nodes_added = 0
    edges_added = 0
    
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
            node.r = 1.0  # Red for outliers
            node.g = 0.0
            node.b = 0.0
        else:
            node.r = 0.0  # Green for normal files
            node.g = 1.0
            node.b = 0.0
        
        # Set size based on line count (min 10, max 100)
        size = max(10, min(100, file_info['lines'] // 10))
        node.size = size
        
        if connected:
            gephi.add_node(node)
        nodes_added += 1
    
    # Create edges between files in same directory
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
                        print(f"Reached maximum edge limit of {MAX_NODES}")
                        break
                    edge_id = f"{file_list[i]}-{file_list[j]}"
                    edge = graph.Edge(edge_id, file_list[i], file_list[j])
                    if connected:
                        gephi.add_edge(edge)
                    edges_added += 1
    
    print(f"Processed {nodes_added} nodes and {edges_added} edges")
    if connected:
        print("Project mode streaming complete!")
    else:
        print("Mock processing complete - Gephi not available")


def stream_trust_mode(workspace="workspace0"):
    """
    Trust Mode (Epistemic View): Stream trust scores to Gephi.
    Node size based on trust score, color based on trust level.
    """
    print("=== TRUST MODE: Streaming epistemic trust scores ===")
    
    gephi, connected = connect_to_gephi(workspace)
    
    try:
        # Read trust scores
        df = pd.read_csv('data/results/trust_scores_results.csv')
        print(f"Loaded {len(df)} trust scores from data/results/trust_scores_results.csv")
        
        nodes_added = 0
        
        for _, row in df.iterrows():
            if nodes_added >= MAX_NODES:
                print(f"Reached maximum node limit of {MAX_NODES}")
                break
                
            node_id = row['node_id']
            trust_score = float(row['trust_score'])
            
            # Create node
            node = graph.Node(
                node_id,
                label=f"{node_id} (Trust: {trust_score:.2f})",
                attributes={
                    'trust_score': trust_score,
                    'mode': 'trust',
                    'node_type': 'trust_node'
                }
            )
            
            # Set size based on trust score (20-70 units as specified)
            size = 20 + (trust_score * 50)  # Maps 0.0-1.0 to 20-70
            node.size = size
            
            # Set color based on trust level
            if trust_score < 0.5:
                # Red for low trust
                node.r = 1.0
                node.g = 0.0
                node.b = 0.0
            elif trust_score < 0.8:
                # Yellow for medium trust
                node.r = 1.0
                node.g = 1.0
                node.b = 0.0
            else:
                # Green for high trust
                node.r = 0.0
                node.g = 1.0
                node.b = 0.0
            
            if connected:
                gephi.add_node(node)
            nodes_added += 1
        
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
    Samples 1,000 nodes and edges with weight > 0.5.
    """
    print("=== KNOWLEDGE MODE: Streaming semantic memory graph ===")
    
    gephi, connected = connect_to_gephi(workspace)
    
    conn = None
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('data/knowledge_core.sqlite')
        cursor = conn.cursor()
        
        # Get concepts (limit to 1,000 nodes)
        cursor.execute("SELECT id, label FROM concepts LIMIT 1000")
        concepts = cursor.fetchall()
        print(f"Loaded {len(concepts)} concepts from knowledge_core.sqlite")
        
        nodes_added = 0
        edges_added = 0
        
        # Add concept nodes
        concept_ids = set()
        for concept_id, label in concepts:
            if nodes_added >= MAX_NODES:
                print(f"Reached maximum node limit of {MAX_NODES}")
                break
                
            node = graph.Node(
                f"concept_{concept_id}",
                label=label,
                attributes={
                    'concept_id': concept_id,
                    'mode': 'knowledge',
                    'node_type': 'concept'
                }
            )
            node.size = 30  # Standard size for concepts
            node.r = 0.5    # Blue color for knowledge nodes
            node.g = 0.5
            node.b = 1.0
            
            if connected:
                gephi.add_node(node)
            nodes_added += 1
            concept_ids.add(concept_id)
        
        # Get assertions (edges) with weight > 0.5
        cursor.execute("""
            SELECT source_concept_id, target_concept_id, weight, relationship_type 
            FROM assertions 
            WHERE weight > 0.5
        """)
        assertions = cursor.fetchall()
        print(f"Found {len(assertions)} assertions with weight > 0.5")
        
        # Add assertion edges
        for source_id, target_id, weight, rel_type in assertions:
            if edges_added >= MAX_NODES:
                print(f"Reached maximum edge limit of {MAX_NODES}")
                break
                
            if source_id in concept_ids and target_id in concept_ids:
                edge_id = f"assertion_{source_id}_{target_id}"
                edge = graph.Edge(
                    edge_id, 
                    f"concept_{source_id}", 
                    f"concept_{target_id}",
                    attributes={
                        'weight': weight,
                        'relationship_type': rel_type,
                        'mode': 'knowledge'
                    }
                )
                edge.weight = weight
                
                if connected:
                    gephi.add_edge(edge)
                edges_added += 1
        
        print(f"Processed {nodes_added} concept nodes and {edges_added} assertion edges")
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
    
    gephi, connected = connect_to_gephi(workspace)
    
    try:
        # Read synthetic audit data
        df = pd.read_csv('data/results/synthetic_audit_results.csv')
        print(f"Loaded {len(df)} synthetic audit records from data/results/synthetic_audit_results.csv")
        
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
            
            # Set size based on confidence score
            size = 20 + (confidence_score * 60)  # Maps 0.0-1.0 to 20-80
            node.size = size
            
            # Set color: Orange for patterns, Purple for vaulted
            if vaulted:
                # Purple for vaulted documents
                node.r = 0.5
                node.g = 0.0
                node.b = 0.5
            else:
                # Orange for pattern signatures
                node.r = 1.0
                node.g = 0.5
                node.b = 0.0
            
            if connected:
                gephi.add_node(node)
            nodes_added += 1
            created_nodes[signature_id] = True
        
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
                        edge_id = f"{signatures[i]}-{signatures[j]}"
                        edge = graph.Edge(
                            edge_id, 
                            signatures[i], 
                            signatures[j],
                            attributes={
                                'relationship': 'same_pattern_type',
                                'pattern_type': pattern_type,
                                'mode': 'synthetic'
                            }
                        )
                        
                        if connected:
                            gephi.add_edge(edge)
                        edges_added += 1
        
        print(f"Processed {nodes_added} synthetic nodes and {edges_added} edges")
        if connected:
            print("Synthetic mode streaming complete!")
        else:
            print("Mock processing complete - Gephi not available")
            
    except FileNotFoundError:
        print("Error: data/synthetic_audit.csv not found")
    except Exception as e:
        print(f"Error processing synthetic data: {e}")


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
        choices=['project', 'trust', 'knowledge', 'synthetic'],
        default='project',
        help='Forensic mode to run (default: project)'
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


if __name__ == "__main__":
    main()
