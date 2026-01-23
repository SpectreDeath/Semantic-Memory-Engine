import os
import sys
import logging
import random

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_rolling_delta():
    print("🚀 Starting Rolling Delta Verification...")
    
    # 1. Instantiate via Factory
    try:
        rolling = ToolFactory.create_rolling_delta()
        print("✅ RollingDelta instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 2. Test Window Generator
    # Create a mock text with 100 simple words
    simple_text = "word " * 100
    print("\n🪟 Testing Window Generation (Size=20, Step=10)...")
    
    windows = list(rolling.generate_windows(simple_text, window_size=20, step=10))
    print(f"Generated {len(windows)} windows.")
    
    # Expected: 0-20, 10-30, 20-40, 30-50, 40-60, 50-70, 60-80, 70-90, 80-100 (9 windows)
    assert len(windows) > 0, "Should generate windows for valid text"
    print(f"First window start: {windows[0][0]}, text len: {len(windows[0][1].split())}")
    
    assert len(windows[0][1].split()) == 20, "Window should contain exactly 20 words"
    
    # 3. Test Rolling Analysis
    print("\n📉 Testing Rolling Analysis...")
    target_text = "alpha beta gamma " * 200 # 600 words
    
    # Candidate profiles (Author A matches target, Author B is different)
    candidates = {
        "Author_A": "alpha beta gamma " * 100,
        "Author_B": "delta epsilon zeta " * 100
    }
    
    # Window 100, Step 50
    results = rolling.analyze_rolling_delta(target_text, candidates, window_size=100, step=50)
    
    # Verify structure
    assert "series" in results
    assert "volatility" in results
    assert "Author_A" in results["series"]
    assert "Author_B" in results["series"]
    
    dist_a = results["series"]["Author_A"]
    dist_b = results["series"]["Author_B"]
    
    print(f"\nSeries Lengths: A={len(dist_a)}, B={len(dist_b)}")
    print(f"First 3 distances for A: {dist_a[:3]}")
    print(f"First 3 distances for B: {dist_b[:3]}")
    
    # Logic check: A should be closer (lower distance) than B
    avg_a = sum(dist_a) / len(dist_a)
    avg_b = sum(dist_b) / len(dist_b)
    print(f"Avg Distance A: {avg_a:.4f} (Matches)")
    print(f"Avg Distance B: {avg_b:.4f} (Different)")
    
    assert avg_a < avg_b, "Author A (matching) should have lower distance than Author B"
    
    print(f"\nVolatility: {results['volatility']}")
    assert results['volatility']['Author_A'] >= 0, "Volatility should be non-negative"
    
    print("\n✅ Verification COMPLETE: Rolling Delta is operational.")

if __name__ == "__main__":
    test_rolling_delta()
