import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Add path for imports
sys.path.append("D:/mcp_servers")

DB_PATH = "D:/mcp_servers/storage/laboratory.db"

def setup_test_data():
    print("--- Setting up test data ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clean old test data if needed, or just add new
    # Insert a few mock records over the last 3 days
    base_time = datetime.now()
    test_data = [
        (base_time - timedelta(days=2), "test1.md", 0.1, 0.8, 0.1, 0.2),
        (base_time - timedelta(days=1), "test2.md", 0.5, 0.4, 0.1, -0.6),
        (base_time, "test3.md", 0.05, 0.75, 0.2, 0.5)
    ]
    
    for ts, fname, neg, neu, pos, compound in test_data:
        cursor.execute('''
            INSERT INTO sentiment_logs (timestamp, source_file, neg, neu, pos, compound)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ts.strftime('%Y-%m-%d %H:%M:%S'), fname, neg, neu, pos, compound))
    
    conn.commit()
    conn.close()
    print("✅ Test data inserted.")

def test_visualization():
    print("\n--- Testing Bio-Feedback Logic ---")
    from bio_feedback import plot_sentiment_history
    result = plot_sentiment_history(days=7)
    if "successfully" in result:
        print(f"✅ Visualization PASS: {result}")
    else:
        print(f"❌ Visualization FAIL: {result}")

if __name__ == "__main__":
    setup_test_data()
    test_visualization()
