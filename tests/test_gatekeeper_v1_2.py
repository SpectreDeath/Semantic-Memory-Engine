
import unittest
import sys
import os

# Add src/gateway to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gateway.gatekeeper_logic import calculate_trust_score, calculate_vault_proximity, calculate_entropy, calculate_burstiness

class TestGatekeeper(unittest.TestCase):
    def test_vault_proximity(self):
        # Text identical to vault sample
        vault_text = "ultimately, the decision rests with the stakeholders."
        proximity = calculate_vault_proximity(vault_text)
        print(f"Vault Proximity for exact match: {proximity}")
        self.assertGreater(proximity, 0.8, "Proximity should be high for vault text")

        # Text different from vault
        clean_text = "The quick brown fox jumps over the lazy dog."
        proximity_clean = calculate_vault_proximity(clean_text)
        print(f"Vault Proximity for clean text: {proximity_clean}")
        self.assertLess(proximity_clean, 0.5, "Proximity be low for clean text")

    def test_trust_score_pollutant(self):
        # Simulate a pollutant
        # Low entropy (repetitive), Low burstiness (uniform), High proximity
        entropy = 3.0 # Low -> Deficit = 1.5 -> Pen = 37.5
        burstiness = 2.0 # Low -> Deficit = 4 -> Pen = 32
        proximity = 0.9 # High -> Pen = 54
        # Total Pen = 37.5 + 32 + 54 = 123.5 -> NTS = 0
        
        score = calculate_trust_score(entropy, burstiness, proximity)
        print(f"Pollutant Score: {score}")
        self.assertLess(score['nts'], 40)
        self.assertEqual(score['label'], "Synthetic Hazard")

    def test_trust_score_human(self):
        # Simulate human
        # High entropy, High burstiness, Low proximity
        entropy = 5.0 # High -> Deficit 0
        burstiness = 7.0 # High -> Deficit 0
        proximity = 0.0 # Low -> Pen 0
        
        score = calculate_trust_score(entropy, burstiness, proximity)
        print(f"Human Score: {score}")
        self.assertGreater(score['nts'], 80)
        self.assertEqual(score['label'], "Grounded Human Content")

if __name__ == '__main__':
    unittest.main()
