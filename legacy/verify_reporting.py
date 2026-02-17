import sys
import os
import json
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(os.getcwd())

from src.ui.report_gen import generate_case_report

def verify_reporting():
    print("🚀 Starting Reporting Verification...")
    
    # Mock Data
    osint_data = [
        {
            "username": "test_actor",
            "platforms": [
                {"name": "GitHub", "status": "found", "url": "https://github.com/test_actor"},
                {"name": "Reddit", "status": "not_found"}
            ]
        }
    ]
    
    sentiment_data = pd.DataFrame([
        {"title": "Hostile activity detected in sector 7G", "polarity": -0.8},
        {"title": "New research shows alignment in identity matrix", "polarity": 0.5}
    ])
    
    output_path = "data/reports/verification_test.pdf"
    os.makedirs("data/reports", exist_ok=True)
    
    try:
        generate_case_report(output_path, osint_data, sentiment_data)
        if Path(output_path).exists():
            print(f"✅ Success: Case Report generated at {output_path}")
            print(f"File size: {os.path.getsize(output_path)} bytes")
        else:
            print("❌ Failure: Report file not found.")
    except Exception as e:
        print(f"❌ Error during generation: {e}")

if __name__ == "__main__":
    verify_reporting()
