#!/usr/bin/env python3
"""
Web Researcher - SME Gathering Component
Uses Firecrawl SDK to scrape forensic news for semantic memory ingestion.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from firecrawl import FirecrawlApp

def save_to_markdown(content, filename):
    """Save content to a markdown file in data/raw/."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = raw_dir / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

def main():
    parser = argparse.ArgumentParser(description="Gather forensic news using Firecrawl.")
    parser.add_argument("--query", type=str, default="latest digital forensic news", help="Search query for news")
    parser.add_argument("--url", type=str, help="Specific URL to scrape instead of searching")
    parser.add_argument("--limit", type=int, default=3, help="Number of search results to process (Free Tier friendly)")
    args = parser.parse_args()

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("❌ Error: FIRECRAWL_API_KEY environment variable not set.")
        print("Please set it with: $env:FIRECRAWL_API_KEY='your_key_here'")
        sys.exit(1)

    app = FirecrawlApp(api_key=api_key)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if args.url:
            print(f"🔍 Scraping URL: {args.url}")
            scrape_result = app.scrape_url(args.url, params={'formats': ['markdown']})
            markdown_content = scrape_result.get('markdown', 'No markdown content found.')
            
            filename = f"scrape_{timestamp}.md"
            path = save_to_markdown(markdown_content, filename)
            print(f"✅ Saved scrape to: {path}")
            
        else:
            print(f"🔎 Searching for: {args.query}")
            # Use search to find relevant news
            search_results = app.search(args.query, params={'limit': args.limit})
            
            combined_markdown = f"# Forensic News Research - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            combined_markdown += f"Query: {args.query}\n\n---\n\n"
            
            for i, result in enumerate(search_results.get('data', [])):
                url = result.get('url')
                title = result.get('title', 'Untitled')
                print(f"[{i+1}/{args.limit}] Processing: {title}")
                
                # Scrape each search result
                scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
                markdown = scrape_result.get('markdown', '')
                
                if markdown:
                    combined_markdown += f"## {title}\n"
                    combined_markdown += f"Source: {url}\n\n"
                    combined_markdown += markdown
                    combined_markdown += "\n\n---\n\n"
            
            filename = f"news_research_{timestamp}.md"
            path = save_to_markdown(combined_markdown, filename)
            print(f"✅ Saved combined news research to: {path}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
