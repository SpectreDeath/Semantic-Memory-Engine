#!/usr/bin/env python3
"""
Gephi Streaming Bridge

Streams project metadata and outlier results to Gephi for visualization.
Requires Gephi with Graph Streaming plugin running on http://localhost:8080/workspace0
"""

import json
import os
import glob
from pathlib import Path
import pandas as pd
from gephistreamer import graph
from gephistreamer import GephiREST


def read_active_persona():
    """Read current persona from active_persona.json."""
    try:
        with open('active_persona.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"persona": "Unknown", "specialty": "Unknown", "timestamp": ""}


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
        df = pd.read_csv('audit_results.csv')
        for _, row in df.iterrows():
            filename = row.get('filename', row.get('file', 'unknown'))
            outliers[filename] = row.get('is_outlier', False)
    except FileNotFoundError:
        pass
    return outliers


def stream_to_gephi():
    """
    Stream project metadata to Gephi.
    Creates nodes for files and edges between related files.
    """
    # Connect to Gephi (mock for testing)
    try:
        gephi = GephiREST("http://localhost:8080", workspace="workspace0")
        connected = True
    except:
        print("Gephi connection failed - using mock mode")
        connected = False
    
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
        node_id = file_info['path']
        node = graph.Node(
            node_id,
            label=file_info['name'],
            attributes={
                'persona': persona_data['persona'],
                'specialty': persona_data['specialty'],
                'extension': file_info['ext'],
                'lines': file_info['lines'],
                'directory': file_info['dir']
            }
        )
        
        # Set visual properties
        if file_info['name'] in outliers and outliers[file_info['name']]:
            node.r = 1.0  # Red
            node.g = 0.0
            node.b = 0.0
        else:
            node.r = 0.0  # Green
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
                    edge_id = f"{file_list[i]}-{file_list[j]}"
                    edge = graph.Edge(edge_id, file_list[i], file_list[j])
                    if connected:
                        gephi.add_edge(edge)
                    edges_added += 1
    
    print(f"Processed {nodes_added} nodes and {edges_added} edges")
    if connected:
        print("Streaming complete!")
    else:
        print("Mock processing complete - Gephi not available")


if __name__ == "__main__":
    stream_to_gephi()