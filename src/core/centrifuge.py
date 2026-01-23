from mcp.server.fastmcp import FastMCP
import sqlite3
import os
from datetime import datetime

from src.core.utils import get_path
from src.core.tenancy import get_tenant_db_path

mcp = FastMCP("Centrifuge")

# Database path
def get_current_db_path():
    base_path = get_path('storage', 'db_path')
    return get_tenant_db_path(base_path)

def init_db():
    """Initializes the database schema."""
    db_path = get_current_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_file TEXT,
            neg REAL,
            neu REAL,
            pos REAL,
            compound REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atomic_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE,
            content TEXT NOT NULL,
            source_type TEXT DEFAULT 'AIFdb',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logical_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_node_id TEXT,
            target_node_id TEXT,
            link_type TEXT, -- RA (Inference), CA (Conflict)
            scheme TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_node_id) REFERENCES atomic_facts(node_id),
            FOREIGN KEY(target_node_id) REFERENCES atomic_facts(node_id)
        )
    ''')
    conn.commit()
    conn.close()

@mcp.tool()
def archive_sentiment(source_file: str, neg: float, neu: float, pos: float, compound: float) -> str:
    """Stores sentiment results in the Centrifuge archive."""
    try:
        db_path = get_current_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sentiment_logs (source_file, neg, neu, pos, compound)
            VALUES (?, ?, ?, ?, ?)
        ''', (source_file, neg, neu, pos, compound))
        conn.commit()
        conn.close()
        return f"Archived: {source_file} (Compound: {compound})"
    except Exception as e:
        return f"Archive Error: {str(e)}"

@mcp.tool()
def get_sentiment_trends(days: int = 7) -> str:
    """Retrieves recent sentiment trends from the archive."""
    try:
        db_path = get_current_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, compound FROM sentiment_logs 
            WHERE timestamp >= datetime('now', ?)
            ORDER BY timestamp ASC
        ''', (f'-{days} days',))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return f"No trends found for the last {days} days."
            
        trend_summary = [f"{row[0]}: {row[1]}" for row in results]
        return "\n".join(trend_summary)
    except Exception as e:
        return f"Query Error: {str(e)}"

if __name__ == "__main__":
    init_db()
    mcp.run()
