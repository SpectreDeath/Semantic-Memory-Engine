import os
import sys
import csv
import json
import sqlite3

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def create_sample_lexicons():
    """Create sample CSV and JSON lexicons for testing."""
    os.makedirs('data/lexicons', exist_ok=True)
    
    # Sample CSV: NRC Emotion-like
    csv_path = 'data/lexicons/sample_emotions.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Word', 'Emotion', 'Association'])
        writer.writerow(['abandoned', 'anger', '1'])
        writer.writerow(['abandoned', 'fear', '1'])
        writer.writerow(['abandoned', 'sadness', '1'])
        writer.writerow(['ability', 'positive', '1'])
        writer.writerow(['abundance', 'anticipation', '1'])
        writer.writerow(['abundance', 'joy', '1'])
        writer.writerow(['abundance', 'positive', '1'])
        writer.writerow(['abundance', 'trust', '1'])
        
    # Sample JSON: Propaganda markers
    json_path = 'data/lexicons/sample_propaganda.json'
    markers = [
        {"term": "radical", "category": "loaded_language", "intensity": 0.8},
        {"term": "unprecedented", "category": "hyperbole", "intensity": 0.6},
        {"term": "traitor", "category": "name_calling", "intensity": 0.95}
    ]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(markers, f)
        
    return csv_path, json_path

def test_importer():
    print("🚀 Starting LexiconImporter Verification...")
    
    csv_path, json_path = create_sample_lexicons()
    importer = ToolFactory.create_lexicon_importer()
    
    # 1. Test CSV Import (Emotion Mapping)
    print("\n📊 Testing CSV Import (Emotions)...")
    def emotion_mapper(row):
        # NRC format: word, emotion, association (0 or 1)
        if row['Association'] == '1':
            return [(row['Word'], f"signal_{row['Emotion']}", 1.0)]
        return []
    
    importer.clear_lexicon('emotion')
    res_csv = importer.import_lexicon(csv_path, 'emotion', emotion_mapper)
    print(f"Result: {res_csv}")
    
    # 2. Test JSON Import (Propaganda Mapping)
    print("\n📝 Testing JSON Import (Propaganda)...")
    def propaganda_mapper(row):
        return [(row['term'], f"signal_{row['category']}", row['intensity'])]
        
    importer.clear_lexicon('propaganda')
    res_json = importer.import_lexicon(json_path, 'propaganda', propaganda_mapper)
    print(f"Result: {res_json}")
    
    # 3. Test Summary for Beacon
    print("\n🗼 Testing Summary for Beacon...")
    summary = importer.get_category_summary()
    print(f"Summary: {summary}")
    
    # 4. Verify in DB
    print("\n🔍 Verifying Database Records...")
    conn = sqlite3.connect(importer.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM rhetorical_signals")
    count = cursor.fetchone()[0]
    print(f"Total records in DB: {count}")
    
    if count >= 11: # 8 from CSV + 3 from JSON
        print("\n✅ Verification SUCCESS: Records properly ingested.")
    else:
        print("\n❌ Verification FAILED: Record count mismatch.")
        sys.exit(1)
    
    conn.close()

if __name__ == "__main__":
    test_importer()
