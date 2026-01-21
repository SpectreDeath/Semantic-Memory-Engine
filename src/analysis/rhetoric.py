from textblob import TextBlob
import json

# Your custom dictionary (Risk Signals)
custom_lexicon = {
    "dehumanizing": ["vermin", "parasite", "infestation", "toxic"],
    "distancing": ["collateral", "entities", "processing_units"]
}

def analyze_rhetoric(text):
    blob = TextBlob(text)
    results = {
        "polarity": blob.sentiment.polarity,      # -1 (neg) to 1 (pos)
        "subjectivity": blob.sentiment.subjectivity, # 0 (fact) to 1 (opinion)
        "custom_flags": []
    }
    
    # Check for your specific character tells
    words = [w.lower() for w in blob.words]
    for category, terms in custom_lexicon.items():
        found = [t for t in terms if t in words]
        if found:
            results["custom_flags"].append({category: found})
            
    return results

# Example crawl-ready text
sample_text = "The entities were cleared as part of the toxic infestation removal."
print(analyze_rhetoric(sample_text))
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import json

# Ensure you have the lexicon downloaded (only needed once)
nltk.download('vader_lexicon')

class RhetoricAnalyzer:
    def __init__(self):
        # Initialize the standard VADER engine
        self.vader = SentimentIntensityAnalyzer()
        
        # YOUR CUSTOM LEXICON (Add your dehumanizing terms here)
        self.custom_signals = {
            "dehumanizing": ["vermin", "parasite", "infestation", "toxic"],
            "distancing": ["entities", "units", "case-load"]
        }

    def analyze(self, text):
        # 1. Get standard sentiment scores from VADER
        vader_scores = self.vader.polarity_scores(text)
        
        # 2. Run your custom "Character Tell" check
        text_lower = text.lower()
        signal_counts = {}
        for category, terms in self.custom_signals.items():
            matches = [t for t in terms if t in text_lower]
            signal_counts[category] = len(matches)

        return {
            "sentiment": vader_scores,
            "risk_signals": signal_counts,
            "is_high_risk": vader_scores['neg'] > 0.5 or sum(signal_counts.values()) > 0
        }

# --- TEST IT ---
engine = RhetoricAnalyzer()
sample_text = "The entities represent a toxic infestation that must be cleared."
results = engine.analyze(sample_text)

print(json.dumps(results, indent=4))