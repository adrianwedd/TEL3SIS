"""Sentiment analysis utilities."""
from textblob import TextBlob


def analyze_sentiment(text: str) -> float:
    """Return polarity score for ``text`` using TextBlob."""
    return TextBlob(text).sentiment.polarity
