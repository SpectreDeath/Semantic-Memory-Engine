import os
import sys
import sqlite3
import json
from unittest.mock import MagicMock, patch

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_aifdb_mapping():
    print("🚀 Starting AIFdbConnector Verification...")
    
    # Initialize DB (creates tables)
    from src.core.centrifuge import init_db
    init_db()
    
    connector = ToolFactory.create_aifdb_connector()
    
    # Mock AIF JSON data
    mock_aif = {
        "nodes": [
            {"nodeID": "1", "text": "Birds can fly.", "type": "I"},
            {"nodeID": "2", "text": "Tweety is a bird.", "type": "I"},
            {"nodeID": "3", "text": "Tweety can fly.", "type": "I"},
            {"nodeID": "4", "text": "Inference Scheme", "type": "RA", "text": "Modus Ponens"},
            {"nodeID": "5", "text": "Conflict Scheme", "type": "CA", "text": "But..."}
        ],
        "edges": [
            {"edgeID": "e1", "fromID": "1", "toID": "4"},
            {"edgeID": "e2", "fromID": "2", "toID": "4"},
            {"edgeID": "e3", "fromID": "4", "toID": "3"},
            {"edgeID": "e4", "fromID": "3", "toID": "5"}
        ]
    }
    
    print("\n📊 Testing AIF Mapping logic...")
    summary = connector.map_to_sme(mock_aif)
    print(f"Mapping Summary: {summary}")
    
    # Verify DB content
    conn = sqlite3.connect(connector.db_path)
    cursor = conn.cursor()
    
    # Check atomic_facts
    cursor.execute("SELECT COUNT(*) FROM atomic_facts")
    fact_count = cursor.fetchone()[0]
    print(f"Atomic Facts in DB: {fact_count}")
    
    # Check logical_links
    cursor.execute("SELECT COUNT(*) FROM logical_links")
    link_count = cursor.fetchone()[0]
    print(f"Logical Links in DB: {link_count}")
    
    # Check signal enrichment
    importer = ToolFactory.create_lexicon_importer()
    lex_summary = importer.get_category_summary()
    print(f"Lexicon Summary: {lex_summary}")
    
    if fact_count >= 3 and link_count >= 1:
        print("\n✅ Verification SUCCESS: Argumentation data properly mapped.")
    else:
        print("\n❌ Verification FAILED: Data mismatch.")
        sys.exit(1)
        
    conn.close()

if __name__ == "__main__":
    test_aifdb_mapping()
