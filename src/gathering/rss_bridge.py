#!/usr/bin/env python3
"""
RSS Bridge - SME Gathering Component
Monitors forensic and security RSS feeds using feedparser.
"""

import os
import json
import argparse
import feedparser
import time
from datetime import datetime, timedelta
from pathlib import Path

# Default feeds for forensic news
DEFAULT_FEEDS = [
    "https://www.ojp.gov/rss/all.xml", # NIJ / Forensic Science
    "https://krebsonsecurity.com/feed/",
    "https://www.darkreading.com/rss.xml", # Security / Forensic context
    "https://feeds.feedburner.com/ForensicFocus" # Forensic Focus
]

def save_to_json(entries, filename="forensic_news.json"):
    """Append new entries to a JSON file in data/raw/."""
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
            
    # Add new entries
    # Simple deduplication by link
    existing_links = {entry.get('link') for entry in existing_data}
    unique_new_entries = [e for e in entries if e.get('link') not in existing_links]
    
    all_data = existing_data + unique_new_entries
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    return file_path

def parse_feed(url, hours_limit=24):
    """Parse a single RSS feed and return entries from the last X hours."""
    print(f"📡 Polling: {url}")
    feed = feedparser.parse(url)
    
    now = datetime.now()
    time_limit = now - timedelta(hours=hours_limit)
    
    processed_entries = []
    for entry in feed.entries:
        # Get published date
        published_time = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            
        # Filter by time
        if published_time and published_time < time_limit:
            continue
            
        processed_entries.append({
            "title": entry.get("title", "No Title"),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "published_iso": published_time.isoformat() if published_time else None,
            "summary": entry.get("summary", ""),
            "source_feed": url,
            "ingested_at": now.isoformat()
        })
    
    return processed_entries

def main():
    parser = argparse.ArgumentParser(description="Monitor forensic RSS feeds.")
    parser.add_argument("--feeds", nargs="+", help="Custom RSS feed URLs")
    parser.add_argument("--hours", type=int, default=24, help="Limit to entries from the last X hours (default: 24)")
    args = parser.parse_args()
    
    feeds_to_poll = args.feeds if args.feeds else DEFAULT_FEEDS
    
    all_entries = []
    for feed_url in feeds_to_poll:
        try:
            entries = parse_feed(feed_url, hours_limit=args.hours)
            all_entries.extend(entries)
        except Exception as e:
            print(f"❌ Error polling {feed_url}: {e}")
            
    if all_entries:
        path = save_to_json(all_entries)
        print(f"✅ Successfully ingested {len(all_entries)} new entries (last {args.hours}h) to {path}")
    else:
        print(f"⚠️ No new entries found from the last {args.hours} hours.")

if __name__ == "__main__":
    main()
