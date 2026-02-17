import numpy as np
import pandas as pd
import sys
import os

# Ensure SME src is importable
SME_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SME_ROOT not in sys.path:
    sys.path.insert(0, SME_ROOT)

from src.sme.vendor.faststylometry import burrows_delta, Corpus
from src.sme.vendor.faststylometry.en import tokenise_remove_pronouns_en
from src.sme.vendor import forensic_metrics

def main():
    print("=== Forensic Metrics Side-by-Side Comparison ===")
    
    # 1. Setup Sample Corpus
    train_corpus = Corpus()
    train_corpus.add_book("Author_A", "Book_1", "The quick brown fox jumps over the lazy dog. Stylometry is the study of linguistic style.")
    train_corpus.add_book("Author_B", "Book_1", "Artificial intelligence and machine learning are transforming the world of digital forensics.")
    train_corpus.tokenise(tokenise_remove_pronouns_en)
    
    test_text = "The quick brown fox moves quickly. Stylometry helps in identifying authors of unknown texts."
    test_corpus = Corpus()
    test_corpus.add_book("Unknown", "Sample", test_text)
    test_corpus.tokenise(tokenise_remove_pronouns_en)
    
    # 2. Calculate Burrows' Delta
    print("\nCalculating Burrows' Delta...")
    delta_results = burrows_delta.calculate_burrows_delta(train_corpus, test_corpus, vocab_size=10)
    print("Burrows' Delta Matrix:")
    print(delta_results)
    
    # 3. Calculate New Metrics (Cosine Delta and KL Divergence)
    print("\nCalculating New Forensic Metrics...")
    
    # Mock some frequency vectors for comparison based on the text
    # In a real scenario, these would be the Z-scores or proportions
    v_test = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 1])
    v_a = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    v_b = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0])
    
    cd_a = forensic_metrics.calculate_cosine_delta(v_test, v_a)
    cd_b = forensic_metrics.calculate_cosine_delta(v_test, v_b)
    
    kl_a = forensic_metrics.calculate_symmetrized_kl_divergence(v_test, v_a)
    kl_b = forensic_metrics.calculate_symmetrized_kl_divergence(v_test, v_b)
    
    print(f"Author A - Cosine Delta: {cd_a:.4f}, KL Div: {kl_a:.6f}")
    print(f"Author B - Cosine Delta: {cd_b:.4f}, KL Div: {kl_b:.6f}")
    
    comparison_data = {
        "Author": ["Author_A", "Author_B"],
        "Burrows Delta": [delta_results.loc["Author_A", "Unknown - Sample"], delta_results.loc["Author_B", "Unknown - Sample"]],
        "Cosine Delta": [cd_a, cd_b],
        "KL Divergence": [kl_a, kl_b]
    }
    
    df_comp = pd.DataFrame(comparison_data)
    print("\nSide-by-Side Comparison Table:")
    print(df_comp)
    
    # Identification logic
    winner_cd = df_comp.loc[df_comp['Cosine Delta'].idxmin(), 'Author']
    print(f"\nAttribution result (Cosine Delta): {winner_cd}")

if __name__ == "__main__":
    main()
