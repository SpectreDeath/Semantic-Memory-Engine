
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ai.agent_logic import generate_forensic_summary


def test_omcs_integration():
    print("🚀 Testing OMCS/ConceptNet Integration...")

    # Payload mimicking a high-value threat detection
    intel_package = {
        "osint": [
            {"username": "CBRN_Ghost_99", "platform": "GitHub"}
        ],
        "news": []
    }

    print("\n--- Triggering Forensic Summary ---")
    summary = generate_forensic_summary(intel_package)

    print("\n[AGENT SUMMARY OUTPUT]")
    print(summary)

    # Validation
    if "Common-sense context" in summary and "CBRN" in summary:
        print("\n✅ SUCCESS: Summary contains common-sense expansion.")
    else:
        print("\n❌ FAILURE: Summary missing common-sense context.")

if __name__ == "__main__":
    test_omcs_integration()
