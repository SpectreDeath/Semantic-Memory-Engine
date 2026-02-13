import subprocess
import os
import json
from pathlib import Path

def get_dvc_history(file_path):
    """Fetch Git log for the .dvc file to identify available versions."""
    dvc_file = f"{file_path}.dvc"
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", dvc_file],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        history = []
        for line in result.stdout.splitlines():
            commit_hash, commit_msg = line.split(" ", 1)
            history.append({"hash": commit_hash, "msg": commit_msg})
        return history
    except Exception as e:
        print(f"Error fetching DVC history: {e}")
        return []

def fetch_historical_json(file_path, commit_hash):
    """Use 'dvc get' to retrieve a historical version of a JSON file."""
    temp_dir = Path("tmp/dvc_history")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    file_name = Path(file_path).name
    temp_file = temp_dir / f"{commit_hash}_{file_name}"
    
    try:
        # Command: dvc get . data/raw/osint_results.json --rev <hash> -o <out>
        subprocess.run(
            ["dvc", "get", ".", file_path, "--rev", commit_hash, "-o", str(temp_file)],
            check=True, cwd=os.getcwd()
        )
        
        with open(temp_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error fetching historical JSON ({commit_hash}): {e}")
        return None
