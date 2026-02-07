#!/usr/bin/env python3
"""
Lightweight Context Sniffer - <80 lines

Identifies project context and updates active_persona.json
"""

import json, argparse, sys, os
from datetime import datetime
from pathlib import Path

def get_ext(file_path):
    return Path(file_path).suffix.lower()

def scan_keywords(file_path, lines=20):
    keywords = {
        'pyod':'Data Forensic Scientist','sklearn':'Data Forensic Scientist',
        'fastapi':'Backend Architect','flask':'Backend Architect','django':'Backend Architect',
        'pandas':'Data Engineering','numpy':'Data Engineering',
        'tensorflow':'ML Engineer','pytorch':'ML Engineer'
    }
    specialties = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= lines: break
                line_lower = line.lower()
                for kw, spec in keywords.items():
                    if kw in line_lower: specialties.add(spec)
    except Exception as e:
        print(f"Error: {e}"); sys.exit(1)
    return list(specialties)

def get_persona(ext, specs):
    if ext == '.md': return "Technical Writer", "Documentation"
    if ext in ['.csv','.json']: return "Data Auditor", "Data Analysis"
    if 'Data Forensic Scientist' in specs: return "Data Forensic Scientist", "Forensic"
    if 'Backend Architect' in specs: return "Backend Architect", "Backend"
    if 'Data Engineering' in specs: return "Data Engineer", "Data Processing"
    if 'ML Engineer' in specs: return "ML Engineer", "ML Engineering"
    return "General Developer", "General"

def update_json(persona, specialty):
    data = {"persona": persona, "specialty": specialty, "timestamp": datetime.now().isoformat()}
    with open('active_persona.json', 'w') as f: json.dump(data, f, indent=2)
    return data

def main():
    p = argparse.ArgumentParser(description='Context Sniffer')
    p.add_argument('file', help='File to analyze')
    p.add_argument('--lines', '-l', type=int, default=20, help='Lines to scan')
    args = p.parse_args()
    
    ext = get_ext(args.file)
    specs = scan_keywords(args.file, args.lines)
    persona, specialty = get_persona(ext, specs)
    
    result = update_json(persona, specialty)
    print(f"Persona: {persona} | Specialty: {specialty}")
    print(f"Updated: {result['timestamp']}")

if __name__ == "__main__":
    main()
