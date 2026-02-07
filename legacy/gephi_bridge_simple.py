#!/usr/bin/env python3
"""
Gephi Streaming Bridge - Simplified Version

Demonstrates the core logic for streaming project metadata to Gephi.
This version shows the file processing and visualization logic.
"""

import json
import os
import glob
from pathlib import Path
import pandas as pd


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
    # Get data
    persona_data = read_active_persona()
    files = get_file_metadata()
    outliers = get_outlier_data()
    
    print(f"Processing {len(files)} files for Gephi visualization...")
    print(f"Current persona: {persona_data['persona']}")
    print(f"Specialty: {persona_data['specialty']}")
    
    # Process nodes
    nodes = []
    edges = []
    
    for file_info in files:
        # Determine visual properties
        is_outlier = file_info['name'] in outliers and outliers[file_info['name']]
        color = "red" if is_outlier else "green"
        size = max(10, min(100, file_info['lines'] // 10))
        
        node = {
            'id': file_info['path'],
            'label': file_info['name'],
            'color': color,
            'size': size,
            'persona': persona_data['persona'],
            'specialty': persona_data['specialty'],
            'extension': file_info['ext'],
            'lines': file_info['lines'],
            'directory': file_info['dir']
        }
        nodes.append(node)
    
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
                    edge = {
                        'id': f"{file_list[i]}-{file_list[j]}",
                        'source': file_list[i],
                        'target': file_list[j],
                        'type': 'directory_connection'
                    }
                    edges.append(edge)
    
    print(f"Created {len(nodes)} nodes and {len(edges)} edges")
    
    # Show sample nodes
    print("\nSample nodes:")
    for i, node in enumerate(nodes[:5]):
        print(f"  {node['label']}: {node['color']}, size={node['size']}, outlier={node['label'] in outliers}")
    
    # Show sample edges
    print(f"\nSample edges:")
    for i, edge in enumerate(edges[:3]):
        print(f"  {edge['source']} -> {edge['target']}")
    
    return nodes, edges


if __name__ == "__main__":
    nodes, edges = stream_to_gephi()
    print(f"\nGephi bridge ready - {len(nodes)} nodes, {len(edges)} edges prepared for streaming")