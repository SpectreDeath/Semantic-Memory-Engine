import os
import sys
import logging

# Mock missing scipy for the purpose of this test
import sys
from unittest.mock import MagicMock
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()
sys.modules["scipy.spatial.distance"] = MagicMock()

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_stylo_integration():
    print("🚀 Starting Stylo-Integration Verification...")
    
    # 1. Test Factory access
    print("\n📦 Testing ToolFactory registration...")
    try:
        wrapper = ToolFactory.create_stylo_wrapper()
        print("✅ StyloWrapper instance created.")
    except Exception as e:
        print(f"❌ Failed to create StyloWrapper: {e}")
        sys.exit(1)

    # 2. Test Environment Check (Graceful Failure)
    print("\n🧪 Testing Environment Check...")
    status = wrapper.get_status()
    print(f"Status: {status}")
    
    # We expect ready: False because R/rpy2 are missing on this environment
    if not status["ready"]:
        print("✅ Correctly identified missing R/rpy2 environment.")
    else:
        print("⚠️ Environment reported as ready unexpectedly.")

    # 3. Test ScribeEngine Integration
    print("\n🖋️ Testing ScribeEngine integration...")
    scribe = ToolFactory.create_scribe()
    attribution = scribe.get_stylo_attribution("Test text", corpus_path="data/test_corpus")
    
    print(f"Attribution response: {attribution}")
    
    if attribution["status"] == "unavailable":
        print("✅ ScribeEngine correctly reported 'unavailable' with instructions.")
        if "instructions" in attribution:
            print("📜 Instructions present:")
            for step in attribution["instructions"]:
                print(f"  {step}")
    else:
        print(f"❌ Unexpected attribution status: {attribution['status']}")
        sys.exit(1)

    print("\n✅ Verification COMPLETE: Stylo integration is robust against missing dependencies.")

if __name__ == "__main__":
    test_stylo_integration()
