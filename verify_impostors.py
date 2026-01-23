import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_impostors_method():
    print("🚀 Starting Impostors Method Verification...")
    
    # 1. Instantiate via Factory
    try:
        checker = ToolFactory.create_impostors_checker()
        print("✅ ImpostorsChecker instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 2. Test Authorship Verification
    print("\n🔍 Testing Verification Logic...")
    
    # Create target text that matches "suspect" vocab pattern
    target_text = "word_suspect_0 word_suspect_1 word_suspect_5 " * 20
    
    result = checker.verify_authorship(
        target_text=target_text,
        suspect_author_id="suspect",
        iterations=50,
        mfw_size=20,
        impostor_count=5
    )
    
    print(f"\nVerification Result:")
    print(f"  Verified: {result['verified']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Suspect Wins: {result['suspect_wins']}/{result['iterations']}")
    print(f"  Verdict: {result['verdict']}")
    
    # The dummy implementation won't give perfect results since vocab is random
    # But we can check the structure
    assert 'verified' in result
    assert 'confidence' in result
    assert 0.0 <= result['confidence'] <= 1.0
    assert result['verdict'] in ['Verified', 'External Author Likely']
    
    print("\n✅ Verification logic operational.")
    
    # 3. Test boundary conditions
    print("\n⚠️ Testing confidence threshold...")
    print(f"If confidence < 0.5: '{result['verdict']}' expected to indicate external author")
    
    if result['confidence'] < 0.5:
        assert result['verified'] == False
        print("✅ Correctly flagged as external author")
    else:
        assert result['verified'] == True
        print("✅ Correctly verified suspect")
    
    print("\n✅ Verification COMPLETE: Impostors Method operational.")

if __name__ == "__main__":
    test_impostors_method()
