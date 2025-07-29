"""
ATS Optimization & Scoring Module
Evaluates a document against a job description using Gemini.
"""

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

class ATSAnalyzer:
    """
    Performs ATS (Applicant Tracking System) analysis on a document.
    """

    def __init__(self):
        """Initialize the ATSAnalyzer."""
        try:
            stopwords.words('english')
        except LookupError:
            nltk.download('stopwords')
            nltk.download('punkt')

    def analyze(self, document_text: str, job_description: str) -> dict:
        """
        Performs a compatibility check, scoring, and provides feedback.

        Args:
            document_text: The text of the generated document.
            job_description: The text of the job description.

        Returns:
            A dictionary with the ATS analysis.
        """
        job_keywords = self._extract_keywords(job_description)
        doc_keywords = self._extract_keywords(document_text)

        if not job_keywords:
            return {
                "keywordMatchPercent": 0,
                "matchedKeywords": [],
                "missingKeywords": [],
                "suggestions": "Could not extract keywords from job description."
            }

        matched_keywords = list(job_keywords.intersection(doc_keywords))
        missing_keywords = list(job_keywords - doc_keywords)

        match_percent = (len(matched_keywords) / len(job_keywords)) * 100 if job_keywords else 0

        suggestions = self._generate_suggestions(missing_keywords)

        return {
            "keywordMatchPercent": round(match_percent, 1),
            "matchedKeywords": matched_keywords[:20],
            "missingKeywords": missing_keywords[:20],
            "suggestions": suggestions
        }

    def _extract_keywords(self, text: str) -> set:
        """Extracts keywords from a given text."""
        stop_words = set(stopwords.words('english'))
        text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = word_tokenize(text)
        return {word for word in tokens if word not in stop_words and len(word) > 2}

    def _generate_suggestions(self, missing_keywords: list) -> str:
        """Generates actionable feedback for improvement."""
        if not missing_keywords:
            return "Excellent keyword coverage!"

        return f"Consider incorporating these missing keywords: {', '.join(missing_keywords[:10])}"
