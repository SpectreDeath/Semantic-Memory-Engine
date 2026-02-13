#!/usr/bin/env python3
"""
OSINT Toolkit - SME Gathering Component
High-concurrency identity footprinting tool with stealth and rate-limit handling.
"""

import os
import json
import argparse
import random
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from src.database.supabase_client import sync_osint_results_to_supabase
except Exception:
    sync_osint_results_to_supabase = lambda x: None

try:
    from fake_useragent import UserAgent
    ua = UserAgent()
except Exception:
    ua = None

import requests

# Core platforms for forensic actor footprinting
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "PyPI": "https://pypi.org/user/{}"
}

def get_random_user_agent():
    """Return a random user agent using fake-useragent."""
    try:
        return ua.random
    except Exception:
        # Fallback if library fails
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def check_platform(name, url_template, username, session):
    """Check a single platform for a username."""
    url = url_template.format(username)
    headers = {"User-Agent": get_random_user_agent()}
    
    try:
        # Use a reasonable timeout to prevent hanging the pool
        response = session.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            # Special logic for Reddit: sometimes they redirect/shadow-ban check
            if "reddit.com" in url and "unauthenticated" in response.url:
                return {"name": name, "url": url, "status": "uncertain", "reason": "Redirected to auth"}
            return {"name": name, "url": url, "status": "found"}
        
        elif response.status_code == 404:
            return {"name": name, "url": url, "status": "not_found"}
        
        elif response.status_code == 429:
            return {"name": name, "url": url, "status": "uncertain", "reason": "Rate Limited"}
        
        else:
            return {"name": name, "url": url, "status": "uncertain", "reason": f"HTTP {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"name": name, "url": url, "status": "uncertain", "reason": "Timeout"}
    except Exception as e:
        return {"name": name, "url": url, "status": "uncertain", "reason": str(e)}

def footprint_username(username):
    """Concurrently check a username across multiple platforms."""
    print(f"🕵️  Scanning OSINT footprint for actor: {username}")
    
    results = {
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "platforms": []
    }
    
    # Using a session for connection pooling
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_platform = {
                executor.submit(check_platform, name, template, username, session): name 
                for name, template in PLATFORMS.items()
            }
            
            for future in as_completed(future_to_platform):
                platform_res = future.result()
                results["platforms"].append(platform_res)
                status_icon = "✅" if platform_res["status"] == "found" else "❌" if platform_res["status"] == "not_found" else "⚠️"
                print(f"  {status_icon} {platform_res['name']}: {platform_res['status']} ({platform_res.get('reason', 'N/A')})")

    return results

def save_to_json(data, filename="osint_results.json"):
    """Save/Append OSINT results to data/raw/."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / filename
    
    existing_data = []
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass
            
    # Add new scan results
    existing_data.append(data)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    return file_path

def main():
    parser = argparse.ArgumentParser(description="Concurrent OSINT Toolkit for Forensic Ingestion.")
    parser.add_argument("--username", type=str, required=True, help="Username to track")
    args = parser.parse_args()
    
    scan_results = footprint_username(args.username)
    path = save_to_json(scan_results)
    
    # Sync to Supabase
    sync_osint_results_to_supabase(scan_results)
    
    found_count = len([p for p in scan_results["platforms"] if p["status"] == "found"])
    print(f"\n🎯 Scan complete for {args.username}. Found on {found_count} platforms. Ingested to {path}")

if __name__ == "__main__":
    main()
