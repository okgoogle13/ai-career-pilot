"""
AI service for generating career documents.
"""

import json
from typing import Dict, Any, List, Optional

from genkit import ai, flow
from genkit.core import generate
from genkit.models.googleai import gemini_2_5_pro
from werkzeug.datastructures import FileStorage

from pathlib import Path
from firebase_admin import firestore
from ..utils.scraper import JobAdScraper
from ..utils.firebase_client import FirestoreClient
from .dossier_generator import DossierGenerator
from ..utils.ats_analyzer import ATSAnalyzer
from ..config import Config
from .resume_parser import process_resume

# Initialize configuration
config = Config()

# Initialize utilities
job_scraper = JobAdScraper()
dossier_generator = DossierGenerator()
ats_analyzer = ATSAnalyzer()

# Initialize Firestore client
db = firestore.client()
firestore_client = FirestoreClient(db)


@flow
async def generate_application(request: Dict[str, Any], resume_file: Optional[FileStorage] = None) -> Dict[str, Any]:
    """
    Primary Genkit flow for generating tailored career documents and ATS analysis.

    Args:
        request: {
            "job_ad_url": str,
            "theme_id": str,
            "tone_of_voice": str
        }
        resume_file: An optional FileStorage object for the user's resume.

    Returns:
        {
            "generatedMarkdown": str,
            "atsAnalysis": {
                "keywordMatchPercent": float,
                "matchedKeywords": List[str],
                "missingKeywords": List[str],
                "suggestions": str
            }
        }
    """

    try:
        # Step 1: Process resume if provided
        if resume_file:
            user_profile = await process_resume(resume_file)
        else:
            # Step 2: Retrieve user profile from Firestore if no resume is uploaded
            user_profile = await firestore_client.get_user_profile()

        # Step 3: Scrape job advertisement
        job_data = await job_scraper.scrape_job_ad(request["job_ad_url"])

        # Step 4: Generate company dossier
        company_name = job_data.get("company_name")
        if not company_name:
            raise ValueError("The job data does not contain a 'company_name'. Unable to generate dossier.")
        dossier = await dossier_generator.generate_dossier(company_name)

        # Step 5: Load knowledge base content
        kb_content = load_knowledge_base()

        # Step 6: Construct structured prompt for Gemini 2.5 Pro
        prompt = _construct_generation_prompt(
            job_data=job_data,
            user_profile=user_profile,
            kb_content=kb_content,
            dossier=dossier,
            theme_id=request["theme_id"],
            tone_of_voice=request["tone_of_voice"]
        )

        # Step 7: Generate content using Gemini 2.5 Pro
        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={
                "maxOutputTokens": 8192,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        # Step 8: Parse response and extract components
        generated_content = _parse_generation_response(response.text)

        # Step 9: Perform ATS analysis
        ats_analysis = ats_analyzer.analyze(
            document_text=generated_content["document_text"],
            job_description=job_data["job_description"] + " " + job_data.get("selection_criteria", "")
        )

        return {
            "generatedMarkdown": generated_content["markdown"],
            "atsAnalysis": ats_analysis
        }

    except Exception as e:
        print(f"Error in generate_application flow: {str(e)}")
        raise e

def _construct_generation_prompt(job_data: Dict, user_profile: Dict, kb_content: str,
                               dossier: Dict, theme_id: str, tone_of_voice: str) -> str:
    """Construct the structured prompt for Gemini 2.5 Pro."""

    prompt = f\"\"\"
You are an expert Australian community services career consultant with deep knowledge of the sector. Your task is to generate a tailored career document (resume, cover letter, or KSC response) and perform ATS analysis.

JOB ADVERTISEMENT DETAILS:
Company: {job_data.get('company_name', 'N/A')}
Position: {job_data.get('job_title', 'N/A')}
Description: {job_data.get('job_description', 'N/A')}
Key Responsibilities: {job_data.get('key_responsibilities', 'N/A')}
Selection Criteria: {job_data.get('selection_criteria', 'N/A')}

COMPANY DOSSIER:
{json.dumps(dossier, indent=2)}

USER PROFILE:
{json.dumps(user_profile, indent=2)}

KNOWLEDGE BASE CONTENT:
{kb_content}

GENERATION REQUIREMENTS:
- Theme: {theme_id}
- Tone of Voice: {tone_of_voice}
- Format: Generate as Markdown with clear structure
- Use Australian spelling and terminology
- Apply sector-specific language from the knowledge base
- Follow the CAR (Context-Action-Result) methodology for achievements
- Use STAR methodology for KSC responses where applicable

RESPONSE FORMAT:
Provide your response in the following JSON structure:
{{
    "document_type": "resume|cover_letter|ksc_response",
    "markdown_content": "Full markdown formatted document here",
    "key_achievements": ["Achievement 1", "Achievement 2", ...],
    "keywords_used": ["keyword1", "keyword2", ...]
}}

Generate a professional, tailored document that demonstrates strong alignment with the job requirements using authentic Australian community services language and best practices.
\"\"\"

    return prompt

def _parse_generation_response(response_text: str) -> Dict[str, Any]:
    """Parse the Gemini response and extract structured content."""

    try:
        # Try to parse as JSON first
        if response_text.strip().startswith('{'):
            parsed = json.loads(response_text)
            return {
                "markdown": parsed.get("markdown_content", ""),
                "document_text": parsed.get("markdown_content", "").replace('#', '').replace('*', '')
            }
        else:
            # Fallback to treating entire response as markdown
            return {
                "markdown": response_text,
                "document_text": response_text.replace('#', '').replace('*', '')
            }
    except json.JSONDecodeError:
        return {
            "markdown": response_text,
            "document_text": response_text.replace('#', '').replace('*', '')
        }

def load_knowledge_base() -> str:
    """Load all knowledge base artifacts into a single context string."""
    kb_dir = Path(__file__).parent.parent / "kb"
    kb_content = ""

    # Load all knowledge base files
    kb_files = [
        "pdf_themes_json.json",
        "australian_sector_glossary.md",
        "skill_taxonomy_community_services.md",
        "Gold-Standard-Knowledge-Artifact-1.md",
        "action_verbs_community_services.md"
    ]

    for filename in kb_files:
        file_path = kb_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                kb_content += f"\n\n=== {filename} ===\n"
                kb_content += f.read()

    return kb_content
