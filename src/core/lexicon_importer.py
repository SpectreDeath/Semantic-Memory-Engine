import os
import json
import re

# Paths aligned with your MCP Jail and Laboratory setup
LEXICON_BASE = "D:/mcp_servers/lexicons"
OUTPUT_PATH = "D:/mcp_servers/storage/compiled_signals.json"

def ingest_professional_lexicons():
    compiled_data = {}
    print(f"🚀 Laboratory Ingestion Started...")

    # 1. CUSTOM WMODEL PARSER (for Moral Foundations Dictionary.wmodel)
    # This specifically targets the file found in your MFD2 folder
    mfd_path = os.path.join(LEXICON_BASE, "MFD2/Moral Foundations Dictionary.wmodel")
    
    if os.path.exists(mfd_path):
        print(f"🔍 Found WMODEL file: {os.path.basename(mfd_path)}")
        try:
            with open(mfd_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Regex logic: Finds words in ALL CAPS followed by (1)
                # Example: VERMIN (1), INFESTATION (1)
                matches = re.findall(r'([A-Z0-9\']+)\s+\(1\)', content)
                
                for word in matches:
                    # Normalize to lowercase for the analysis engine
                    # Assigning a weight of -2.0 (High Risk Signal)
                    compiled_data[word.lower()] = -2.0
            
            print(f"✅ Extracted {len(matches)} moral signals from WMODEL.")
        except Exception as e:
            print(f"❌ Error parsing WMODEL: {e}")
    else:
        print(f"⚠️ MFD2 file not found at: {mfd_path}")

    # 2. ENHANCED MORALITY LEXICON (Fallback for CSV/TXT)
    eml_folder = os.path.join(LEXICON_BASE, "Enhanced_Morality_Lexicon_V1.1")
    if os.path.exists(eml_folder):
        # Basic check for any text-based file in the EML folder
        for file in os.listdir(eml_folder):
            if file.endswith(('.csv', '.txt')):
                print(f"🔍 Found EML file: {file}")
                with open(os.path.join(eml_folder, file), 'r', errors='ignore') as f:
                    for line in f:
                        # Simple split to grab words from the first column
                        parts = line.strip().split(',')
                        if parts:
                            word = parts[0].strip().lower()
                            if word and word not in compiled_data:
                                compiled_data[word] = -1.5

    # 3. SAVE TO SECURED STORAGE
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(compiled_data, f, indent=4)
    
    return len(compiled_data)

if __name__ == "__main__":
    total_signals = ingest_professional_lexicons()
    if total_signals > 0:
        print(f"\n✨ SUCCESS: {total_signals} professional signals ingested.")
        print(f"📂 Storage Location: {OUTPUT_PATH}")
    else:
        print("\n❌ FAILED: No signals found. Check your folder paths.")
        