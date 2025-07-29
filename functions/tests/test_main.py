import pytest
import asyncio
from unittest.mock import patch, MagicMock

from main import generate_application

@pytest.fixture
def mock_firestore_client():
    with patch('main.firestore_client', new_callable=MagicMock) as mock_client:
        mock_client.get_user_profile.return_value = {
            "fullName": "Test User",
            "email": "test@example.com",
            "workExperience": [],
            "education": [],
            "skills": ["Python", "Genkit"]
        }
        yield mock_client

@pytest.fixture
def mock_job_scraper():
    with patch('main.job_scraper', new_callable=MagicMock) as mock_scraper:
        mock_scraper.scrape_job_ad.return_value = {
            "company_name": "TestCorp",
            "job_title": "AI Engineer",
            "job_description": "Develop amazing AI things.",
            "selection_criteria": "Must know Python."
        }
        yield mock_scraper

@pytest.fixture
def mock_dossier_generator():
    with patch('main.dossier_generator', new_callable=MagicMock) as mock_generator:
        mock_generator.generate_dossier.return_value = {
            "organizational_overview": "A great company.",
            "communication_style": "Professional",
            "strategic_priorities": "Growth",
            "key_pain_points": "None"
        }
        yield mock_generator

@pytest.fixture
def mock_ats_analyzer():
    with patch('main.ats_analyzer', new_callable=MagicMock) as mock_analyzer:
        mock_analyzer.analyze.return_value = {
            "keywordMatchPercent": 80.0,
            "matchedKeywords": ["Python"],
            "missingKeywords": [],
            "suggestions": "Looks good."
        }
        yield mock_analyzer

@pytest.fixture
def mock_genkit_generate():
    with patch('main.generate', new_callable=MagicMock) as mock_generate:
        mock_generate.return_value = MagicMock(text='{"document_type": "resume", "markdown_content": "Test resume content"}')
        yield mock_generate


@pytest.mark.asyncio
async def test_generate_application_flow(
    mock_firestore_client,
    mock_job_scraper,
    mock_dossier_generator,
    mock_ats_analyzer,
    mock_genkit_generate
):
    """
    Test the main e2e flow of the `generate_application` function.
    """
    request_data = {
        "job_ad_url": "https://example.com/job/123",
        "theme_id": "theme1",
        "tone_of_voice": "professional"
    }

    result = await generate_application(request_data)

    assert "generatedMarkdown" in result
    assert "atsAnalysis" in result
    assert result["generatedMarkdown"] == "Test resume content"
    assert result["atsAnalysis"]["keywordMatchPercent"] == 80.0

    mock_firestore_client.get_user_profile.assert_called_once()
    mock_job_scraper.scrape_job_ad.assert_called_once_with("https://example.com/job/123")
    mock_dossier_generator.generate_dossier.assert_called_once()
    mock_genkit_generate.assert_called_once()
    mock_ats_analyzer.analyze.assert_called_once()
