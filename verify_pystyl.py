import os
import sys
import logging

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_pystyl():
    print("🚀 Starting PyStylWrapper Verification...")
    
    # 1. Instantiate via Factory
    try:
        wrapper = ToolFactory.create_pystyl_wrapper()
        print("✅ PyStylWrapper instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 2. Test Mendenhall's Breadth
    text_sample = "The quick brown fox jumps over the lazy dog."
    dist = wrapper.get_word_length_distribution(text_sample)
    print(f"\n📏 Mendenhall Distribution (Sample: '{text_sample[:15]}...'):")
    print(dist)
    
    # 'fox' (3), 'the' (3), 'dog' (3) -> Length 3 should be frequent
    assert 3 in dist, "Length 3 should be present"
    assert dist[3] > 0, "Length 3 frequency should be > 0"
    print("✅ Mendenhall logic passed basic check.")

    # 3. Test Kilgariff's Chi-squared
    text_a = "This is a simple text. It has common words."
    text_b = "This is a simple text. It has common words." # Identical
    text_c = "Completely different content about astrophysics and quantum mechanics."
    
    dist_ab = wrapper.compare_texts(text_a, text_b)
    dist_ac = wrapper.compare_texts(text_a, text_c)
    
    print(f"\n📉 Chi-squared Distance:")
    print(f"  Identical texts: {dist_ab:.4f}")
    print(f"  Different texts: {dist_ac:.4f}")
    
    assert dist_ab == 0.0, "Identical texts should have 0 distance"
    assert dist_ac > dist_ab, "Different texts should have higher distance"
    print("✅ Chi-squared logic passed basic check.")
    
    print("\n✅ Verification COMPLETE: PyStyl native fallback is operational.")

if __name__ == "__main__":
    test_pystyl()
