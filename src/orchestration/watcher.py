import time
import os
import json
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from src.core.utils import get_path

# --- SETUP ---
WATCH_DIRECTORY = get_path('storage', 'base_dir') # Watching the base data dir or a specific subset
LOG_DIRECTORY = get_path('storage', 'log_dir')
DB_PATH = get_path('storage', 'db_path')
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Initialize the Brain
analyzer = SentimentIntensityAnalyzer()
custom_signals = {
    "vermin": -3.5, "parasite": -3.5, "infestation": -2.5, 
    "entities": -1.0, "toxic": -2.0, "units": -1.5
}
analyzer.lexicon.update(custom_signals)

class AnalyzeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            print(f"❄️ New file detected in basement: {os.path.basename(event.src_path)}")
            self.process_file(event.src_path)

    def process_file(self, file_path):
        time.sleep(1) 
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        scores = analyzer.polarity_scores(content)
        
        # 1. Archive to SQLite (The Centrifuge)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sentiment_logs (source_file, neg, neu, pos, compound)
                VALUES (?, ?, ?, ?, ?)
            ''', (os.path.basename(file_path), scores['neg'], scores['neu'], scores['pos'], scores['compound']))
            conn.commit()
            conn.close()
            print(f"💾 Archived to Centrifuge: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ Archive Error: {str(e)}")

        # 2. Build the JSON report
        report = {
            "timestamp": time.ctime(),
            "source_file": os.path.basename(file_path),
            "sentiment": scores,
            "risk_status": "HIGH ALERT" if scores['neg'] > 0.4 else "NORMAL"
        }

        # Save report to logs
        report_name = f"report_{os.path.basename(file_path)}.json"
        with open(os.path.join(LOG_DIRECTORY, report_name), 'w') as out:
            json.dump(report, out, indent=4)
        print(f"✅ Analysis complete. Report saved to /logs/{report_name}")

def load_brain():
    """Load professional signals from compiled JSON file."""
    compiled_signals_path = "D:/mcp_servers/storage/compiled_signals.json"
    try:
        if os.path.exists(compiled_signals_path):
            with open(compiled_signals_path, 'r') as f:
                professional_signals = json.load(f)
            analyzer.lexicon.update(professional_signals)
            print(f"✅ Brain Loaded: {len(professional_signals)} professional signals active.")
        else:
            print(f"⚠️  Brain file not found: {compiled_signals_path}")
    except Exception as e:
        print(f"⚠️  Error loading brain: {e}")

if __name__ == "__main__":
    # Load professional signals if available
    load_brain()
    
    # Install watchdog first: pip install watchdog
    event_handler = AnalyzeHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    
    print(f"🚀 Laboratory Monitoring Active: Watching {WATCH_DIRECTORY}...")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()