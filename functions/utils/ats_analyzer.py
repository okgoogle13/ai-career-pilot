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
        """
        Initializes the ATSAnalyzer and ensures required NLTK resources for stopword removal and tokenization are available.
        """
        try:
            stopwords.words('english')
        except LookupError:
            nltk.download('stopwords')
            nltk.download('punkt')

    def analyze(self, document_text: str, job_description: str) -> dict:
        """
        Analyze a document against a job description to assess keyword match and provide improvement suggestions.
        
        Parameters:
            document_text (str): The text content of the document to be evaluated.
            job_description (str): The text content of the job description for comparison.
        
        Returns:
            dict: A dictionary containing the percentage of job keywords matched, lists of matched and missing keywords (up to 20 each), and tailored suggestions for improvement.
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
        """
        Extract keywords from text by removing punctuation, lowercasing, tokenizing, and filtering out English stopwords and short words.
        
        Parameters:
            text (str): The input text from which to extract keywords.
        
        Returns:
            set: A set of keywords found in the text.
        """
        stop_words = set(stopwords.words('english'))
        text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = word_tokenize(text)
        return {word for word in tokens if word not in stop_words and len(word) > 2}

    def _generate_suggestions(self, missing_keywords: list) -> str:
        """
        Generate feedback based on missing keywords, suggesting which ones to incorporate for improved keyword coverage.
        
        Parameters:
            missing_keywords (list): List of keywords not found in the document.
        
        Returns:
            str: Suggestion message tailored to the presence or absence of missing keywords.
        """
        if not missing_keywords:
            return "Excellent keyword coverage!"

        return f"Consider incorporating these missing keywords: {', '.join(missing_keywords[:10])}"
