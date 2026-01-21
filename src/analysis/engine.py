import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import json

# Initialize the analyzer
# Note: On a first run, you may need to run nltk.download('vader_lexicon')
analyzer = SentimentIntensityAnalyzer()

# 1. DEFINE YOUR CUSTOM DICTIONARY (Risk Signals)
# You can keep these in an external JSON/CSV as you scale
custom_lexicon = {
    "dehumanizing_metaphors": {
        "vermin": -3.0, "parasite": -3.5, "infestation": -2.5, "toxic": -2.0
    },
    "bureaucratic_distancing": {
        "entities": -1.0, "units": -0.5, "processing_units": -1.5, "collateral": -2.0
    }
}

# 2. UPDATE VADER WITH YOUR SIGNALS
# This forces the engine to recognize your specific 'Character Tells'
for category in custom_lexicon.values():
    analyzer.lexicon.update(category)

def analyze_rhetoric(text):
    """
    Analyzes text for sentiment and specific risk signals.
    """
    scores = analyzer.polarity_scores(text)
    
    # Check for specific "tells" from your research
    found_signals = {}
    text_lower = text.lower()
    for cat_name, terms in custom_lexicon.items():
        matches = [t for t in terms if t in text_lower]
        if matches:
            found_signals[cat_name] = matches

    return {
        "sentiment_summary": scores,
        "flagged_terms": found_signals,
        "risk_level": "HIGH" if scores['neg'] > 0.4 or found_signals else "LOW"
    }

# --- TEST CASE ---
sample = "The entities represent a toxic infestation that must be cleared."
print(json.dumps(analyze_rhetoric(sample), indent=4))