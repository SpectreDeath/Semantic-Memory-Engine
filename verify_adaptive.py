import os
import sys
import logging
import time

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_adaptive_learning():
    print("🚀 Starting Adaptive Learner Verification...")
    
    # 1. Instantiate
    try:
        learner = ToolFactory.create_adaptive_learner()
        print("✅ AdaptiveLearner instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    author_id = "test_author_v1"
    
    # 2. Save Historical Snapshots
    print("\n📸 Testing Snapshot Logic...")
    
    # Snapshot 1 (Oldest) - Focused on 'emotion'
    data_t0 = {"signal_anger": 0.8, "signal_joy": 0.1, "signal_trust": 0.5}
    learner.save_profile_snapshot(author_id, data_t0)
    time.sleep(1) # Ensure timestamp diff
    
    # Snapshot 2 (Middle) - Shift towards 'trust'
    data_t1 = {"signal_anger": 0.4, "signal_joy": 0.2, "signal_trust": 0.7}
    learner.save_profile_snapshot(author_id, data_t1)
    time.sleep(1)
    
    # Snapshot 3 (Newest) - Heavy 'trust' focus
    data_t2 = {"signal_anger": 0.2, "signal_joy": 0.3, "signal_trust": 0.9}
    learner.save_profile_snapshot(author_id, data_t2)
    
    print("✅ Snapshots saved.")
    
    # 3. Test Weighted Profile (Exponential Decay)
    print("\n⚖️ Testing Weighted Profile (Decay=0.5)...")
    # T2 is freshest (w=1), T1 (w=0.5), T0 (w=0.25) ... normalized
    # Weights sum = 1 + 0.5 + 0.25 = 1.75
    # Normalized weights: T2=0.57, T1=0.28, T0=0.14 approx
    
    profile = learner.calculate_weighted_profile(author_id, decay_factor=0.5)
    print(f"Weighted Profile: {profile}")
    
    # Expect 'trust' to be high because recent snapshots favor it
    # Trust ~ (0.9*1 + 0.7*0.5 + 0.5*0.25) / 1.75 = (0.9 + 0.35 + 0.125) / 1.75 = 1.375 / 1.75 = 0.785
    # Anger ~ (0.2*1 + 0.4*0.5 + 0.8*0.25) / 1.75 = (0.2 + 0.2 + 0.2) / 1.75 = 0.6 / 1.75 = 0.34
    
    exp_trust = 0.78
    assert abs(profile['signal_trust'] - exp_trust) < 0.05, f"Trust score {profile['signal_trust']:.2f} should be close to recent value {exp_trust}"
    print(f"✅ Weighting logic verified. Trust score: {profile['signal_trust']:.3f}")
    
    # 4. Test Drift Detection
    print("\n⚠️ Testing Drift Detection...")
    
    # Case A: Consistent Data (Similar to weighted profile)
    consistent_data = {"signal_anger": 0.25, "signal_joy": 0.3, "signal_trust": 0.85}
    drift_a = learner.detect_style_drift(consistent_data, author_id, threshold=0.1)
    print(f"Case A (Consistent): Drift={drift_a['drift_detected']}, Dist={drift_a['distance']:.4f}")
    assert not drift_a['drift_detected'], "Should NOT detect drift for consistent data"
    
    # Case B: Outlier Data (Very different style)
    outlier_data = {"signal_anger": 0.9, "signal_joy": 0.0, "signal_trust": 0.1} # High Anger, Low Trust
    drift_b = learner.detect_style_drift(outlier_data, author_id, threshold=0.1)
    print(f"Case B (Outlier): Drift={drift_b['drift_detected']}, Dist={drift_b['distance']:.4f}")
    assert drift_b['drift_detected'], "Should detect drift for outlier data"
    
    print("\n✅ Verification COMPLETE: Adaptive Learning System operational.")

if __name__ == "__main__":
    test_adaptive_learning()
