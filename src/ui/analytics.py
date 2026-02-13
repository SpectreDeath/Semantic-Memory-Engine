from textblob import TextBlob
import pandas as pd

def analyze_sentiment(text):
    """Perform basic sentiment analysis using TextBlob."""
    if not text or not isinstance(text, str):
        return 0.0, 0.0
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def detect_sentiment_drift(current_scores, historical_avg):
    """Detect significant shifts in sentiment polarity."""
    if not historical_avg:
        return 0.0
    return abs(current_scores - historical_avg)

def batch_analyze_news(news_list):
    """Analyze sentiment for a list of news articles."""
    results = []
    for news in news_list:
        text = f"{news.get('title', '')} {news.get('summary', '')}"
        polarity, subjectivity = analyze_sentiment(text)
        results.append({
            "title": news.get("title"),
            "polarity": polarity,
            "subjectivity": subjectivity,
            "published": news.get("published")
        })
    return pd.DataFrame(results)
