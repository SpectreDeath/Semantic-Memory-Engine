import json
import os
from datetime import datetime

# Path Configuration (Absolute)
OSINT_PATH = "d:/SME/data/raw/osint_results.json"
NEWS_PATH = "d:/SME/data/raw/forensic_news.json"

def inject_threat():
    # 1. The Target Alias
    target_alias = "CBRN_Ghost_99"

    # 2. Mock OSINT Hit (Matching the Toolkit's Schema)
    mock_osint = [
        {
            "username": target_alias,
            "timestamp": datetime.now().isoformat(),
            "platforms": [
                {"name": "GitHub", "status": "found", "url": f"https://github.com/{target_alias}"},
                {"name": "Reddit", "status": "found", "url": f"https://reddit.com/u/{target_alias}"},
                {"name": "HackerNews", "status": "not_found"}
            ]
        }
    ]

    # 3. Mock News Article (CBRN Specific)
    mock_article = [
        {
            "title": "Novel Bypasses in CBRN Sensor Arrays",
            "author": target_alias,
            "summary": "This paper explores how to suppress alerts in industrial CBRN sensors using a specific frequency oscillation.",
            "source_feed": "Underground Forensic Journal",
            "link": f"https://darkweb.onion/research/{target_alias}",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sentiment_polarity": -0.85
        }
    ]

    # Inject into files
    for path, data in [(OSINT_PATH, mock_osint), (NEWS_PATH, mock_article)]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    
    print(f"✅ Threat Injected: '{target_alias}' is now a cross-referenced target in the SME ecosystem.")

if __name__ == "__main__":
    inject_threat()
