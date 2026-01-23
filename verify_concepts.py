import os
import sys
import sqlite3
import json
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_concept_resolver():
    print("🚀 Starting ConceptResolver Verification...")
    
    resolver = ToolFactory.create_concept_resolver()
    
    # Mock ConceptNet API response
    mock_response = {
        "edges": [
            {
                "rel": {"@id": "/r/IsA"},
                "start": {"label": "canary"},
                "end": {"label": "bird"},
                "weight": 2.0
            },
            {
                "rel": {"@id": "/r/CapableOf"},
                "start": {"label": "bird"},
                "end": {"label": "fly"},
                "weight": 1.5
            },
            {
                "rel": {"@id": "/r/UsedFor"},
                "start": {"label": "oven"},
                "end": {"label": "baking"},
                "weight": 3.0
            }
        ]
    }

    with patch('requests.get') as mock_get:
        # Configure mock
        mock_resp_obj = MagicMock()
        mock_resp_obj.json.return_value = mock_response
        mock_resp_obj.status_code = 200
        mock_get.return_value = mock_resp_obj
        
        # 1. Test get_common_sense (First call - API hit)
        print("\n🌐 Testing get_common_sense (First call)...")
        data1 = resolver.get_common_sense("bird")
        print(f"Relations found: {len(data1)}")
        assert mock_get.called
        
        # 2. Test caching (Second call - No API hit)
        print("\n💾 Testing Caching (Second call)...")
        mock_get.reset_mock()
        data2 = resolver.get_common_sense("bird")
        print(f"Relations found in cache: {len(data2)}")
        assert not mock_get.called
        assert data1 == data2
        
        # 3. Test Semantic Expansion
        print("\n📈 Testing Semantic Expansion...")
        expanded = resolver.expand_concept("bird")
        print(f"Expanded concepts: {expanded}")
        assert "canary" in expanded
        assert "bird" in expanded
        
        # 4. Test Fact Verification
        print("\n🔍 Testing Fact Verification...")
        # Positive case
        v1 = resolver.verify_fact("canary", "IsA", "bird")
        print(f"Verify 'canary IsA bird': {v1['veracity']}")
        assert v1['veracity'] == "verified"
        
        # Negative/Unknown case
        v2 = resolver.verify_fact("canary", "IsA", "fish")
        print(f"Verify 'canary IsA fish': {v2['veracity']}")
        assert v2['veracity'] == "unverified"

    print("\n✅ Verification SUCCESS: ConceptResolver operational and cached.")

if __name__ == "__main__":
    test_concept_resolver()
