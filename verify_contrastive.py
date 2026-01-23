import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_contrastive_analyzer():
    print("🚀 Starting Contrastive Analyzer Verification...")
    
    # 1. Instantiate via Factory
    try:
        analyzer = ToolFactory.create_contrastive_analyzer()
        print("✅ ContrastiveAnalyzer instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 2. Test Zeta Score Calculation
    print("\n⚔️ Testing Zeta Score Logic...")
    
    # Mock text samples
    texts_a = [
        "I absolutely love the wonderful amazing fantastic great",
        "The wonderful experience was absolutely fantastic",
        "I love the amazing wonderful time"
    ]
    
    texts_b = [
        "The terrible horrible awful bad experience",
        "It was a terrible and horrible situation",
        "The awful bad terrible outcome"
    ]
    
    zeta_scores = analyzer._calculate_zeta_scores(texts_a, texts_b, min_freq=1)
    print(f"Zeta scores calculated: {len(zeta_scores)} words")
    
    # Check that positive-sentiment words have positive zeta (preferred by A)
    assert zeta_scores.get("wonderful", 0) > 0, "Word 'wonderful' should be A-preferred"
    assert zeta_scores.get("terrible", 0) < 0, "Word 'terrible' should be B-preferred"
    
    print("✅ Zeta calculation verified.")
    
    # 3. Test get_contrastive_lexicon output format
    print("\n📊 Testing Output Formatting...")
    
    # Note: This will use the dummy _get_author_texts which returns placeholder data
    # In production, it would fetch real samples
    result = analyzer.get_contrastive_lexicon("author_alpha", "author_beta", top_n=5)
    
    print(f"Result keys: {result.keys()}")
    assert "preferred_a" in result
    assert "preferred_b" in result
    assert "author_a" in result
    assert "author_b" in result
    
    print(f"Author A markers: {result['preferred_a']}")
    print(f"Author B markers: {result['preferred_b']}")
    
    print("\n✅ Verification COMPLETE: Contrastive Analyzer operational.")

if __name__ == "__main__":
    test_contrastive_analyzer()
