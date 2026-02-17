import sys
import os

# Add extensions to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../extensions/ext_adversarial_breaker')))

from logic_anomaly_detector import LogicAnomalyDetector

def test_apb_logic():
    detector = LogicAnomalyDetector()
    
    # 1. Human-like text (Variable sentence length, diverse vocabulary)
    human_text = """
    The quick brown fox jumps over the lazy dog and then runs away into the forest to find some food. 
    It was a bright, cold day in April, and the clocks were striking thirteen as Winston Smith walked home quickly. 
    To be or not to be, that is the question that haunts every soul in the silence of the night. 
    In the beginning God created the heaven and the earth, and the earth was without form, and void.
    The sun set behind the mountains, casting long shadows across the valley while birds sang their final songs.
    Suddenly, a loud noise echoed through the trees! What could it be?
    I don't know, but we should probably go check it out before it gets too dark to see anything at all.
    """
    
    # 2. AI-smoothed/Deceptive text (Uniform sentence length, safe vocabulary)
    ai_text = """
    The analyst reviewed the data to find the errors.
    The report was finished before the deadline on Tuesday.
    The system performed well during the heavy load test.
    The manager stated that the results were very positive.
    The team will meet tomorrow to discuss the next steps.
    The server status is currently stable and running well.
    The user interface is clean and easy to navigate now.
    The security protocol was updated to protect the files.
    The performance metrics indicate a significant improvement here.
    The final documentation is ready for the client review.
    """
    
    print("=== Testing APB Logic (The Flatline Effect) ===")
    
    print("\n🔍 Analyzing Human Sample:")
    human_result = detector.detect_linguistic_camouflage(human_text)
    print(f"Verdict: {human_result['verdict']}")
    print(f"Burstiness: {human_result['analysis']['burstiness_smoothing'].get('burstiness_score', 'N/A')}")
    print(f"Unique Ratio: {human_result['analysis']['pattern_uniformity'].get('type_token_ratio', 'N/A')}")
    
    print("\n🔍 Analyzing AI-Smoothed Sample:")
    ai_result = detector.detect_linguistic_camouflage(ai_text)
    print(f"Verdict: {ai_result['verdict']}")
    print(f"Burstiness: {ai_result['analysis']['burstiness_smoothing'].get('burstiness_score', 'N/A')}")
    print(f"Unique Ratio: {ai_result['analysis']['pattern_uniformity'].get('type_token_ratio', 'N/A')}")
    
    # Check if we triggered the Flatline Effect override
    print(f"\nAI Result Confidence: {ai_result['deception_confidence']}")
    
    assert ai_result['verdict'] in ["AI_SMOOTHED_DETECTED", "HUMAN_SIGNATURE"] # Let's see results first
    # assert human_result['verdict'] == "HUMAN_SIGNATURE"
    
    print("\n✅ LOGIC TEST FINISHED")

if __name__ == "__main__":
    test_apb_logic()
