import json
from pathlib import Path

def load_intel_data(file_path):
    """
    Load JSON intelligence data from a file.
    Shared between pipeline and dashboard.
    """
    path = Path(file_path)
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []
