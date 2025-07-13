"""CalendarAgent with intent classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@dataclass
class IntentExample:
    text: str
    intent: str


class IntentClassifier:
    """Simple TF-IDF + logistic regression classifier."""

    def __init__(self) -> None:
        examples: List[IntentExample] = [
            IntentExample("book a meeting", "create_event"),
            IntentExample("schedule an appointment", "create_event"),
            IntentExample("set up a call tomorrow", "create_event"),
            IntentExample("am i free at 2pm", "check_availability"),
            IntentExample("do i have anything on friday", "check_availability"),
            IntentExample("what's my schedule like", "check_availability"),
        ]
        texts = [e.text for e in examples]
        labels = [e.intent for e in examples]
        self.vectorizer = TfidfVectorizer()
        X = self.vectorizer.fit_transform(texts)
        self.model = LogisticRegression()
        self.model.fit(X, labels)

    def classify(self, text: str) -> str:
        X = self.vectorizer.transform([text])
        return self.model.predict(X)[0]


class CalendarAgent:
    """Agent that detects calendar-related intents."""

    def __init__(self) -> None:
        self.classifier = IntentClassifier()

    def detect_intent(self, text: str) -> str:
        return self.classifier.classify(text)
