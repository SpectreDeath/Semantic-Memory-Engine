#!/usr/bin/env python3
"""
Scholar API - SME Gathering Component
Uses Semantic Scholar SDK to fetch academic papers on forensic topics.
Captures TLDR field and deduplicates by S2ID.
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import os
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path

# Core forensic queries
CORE_QUERIES = [
    "Forensic Linguistics",
    "CBRN detection",
    "Digital Forensics"
]

def save_to_json(papers, filename="research_papers.json"):
    """Save paper metadata to a JSON file in data/raw/."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = raw_dir / filename
    
    existing_data = []
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
            
    # Deduplication based on paperId (S2ID)
    existing_ids = {p.get('paperId') for p in existing_data if p.get('paperId')}
    new_papers = [p for p in papers if p.get('paperId') not in existing_ids]
    
    all_data = existing_data + new_papers
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    return file_path, len(new_papers)

def fetch_papers_for_query(query, limit=10):
    """Fetch papers for a specific query using direct API calls for stability."""
    print(f"🎓 Searching Semantic Scholar for: {query}")
    
    # Fields: paperId (S2ID), title, abstract, authors, year, url, citationCount, tldr
    fields = "paperId,title,abstract,authors,year,url,citationCount,tldr"
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={limit}&fields={fields}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        papers_data = []
        for paper in data.get('data', []):
            papers_data.append({
                "paperId": paper.get('paperId'),
                "title": paper.get('title'),
                "abstract": paper.get('abstract'),
                "tldr": paper.get('tldr', {}).get('text') if paper.get('tldr') else None,
                "authors": [a.get('name') for a in paper.get('authors', [])] if paper.get('authors') else [],
                "year": paper.get('year'),
                "url": paper.get('url'),
                "citationCount": paper.get('citationCount'),
                "query": query,
                "ingested_at": datetime.now().isoformat()
            })
        return papers_data
    except Exception as e:
        print(f"❌ Error fetching '{query}': {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Fetch academic papers from Semantic Scholar.")
    parser.add_argument("--queries", nargs="+", default=CORE_QUERIES, help="Search queries")
    parser.add_argument("--limit", type=int, default=10, help="Number of papers per query")
    args = parser.parse_args()

    all_new_papers = []
    
    for query in args.queries:
        papers = fetch_papers_for_query(query, limit=args.limit)
        all_new_papers.extend(papers)
            
    if all_new_papers:
        path, count = save_to_json(all_new_papers)
        print(f"✅ Successfully ingested {count} new papers to {path}")
        print(f"   (Skipped {len(all_new_papers) - count} duplicates)")
    else:
        print("⚠️ No new papers found for the specified queries.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
