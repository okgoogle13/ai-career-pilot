"""
AI-powered career advisor service.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import io

from genkit import ai, flow
from genkit.core import generate
from genkit.models.googleai import gemini_2_5_pro
from werkzeug.datastructures import FileStorage
import docx
from pypdf import PdfReader

from src.backend.utils.firebase_client import FirestoreClient
from src.backend.utils.scraper import JobAdScraper
from src.backend.services.dossier_service import DossierService
from src.backend.utils.ats_analyzer import ATSAnalyzer

# Initialize services
firestore_client = FirestoreClient()
job_scraper = JobAdScraper()
dossier_service = DossierService()
ats_analyzer = ATSAnalyzer()


_cached_kb_content: Optional[str] = None

def load_knowledge_base() -> str:
    """Load all knowledge base artifacts into a single context string."""
    global _cached_kb_content
    if _cached_kb_content is None:
        kb_dir = Path(__file__).parent.parent.parent / "kb"
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

        _cached_kb_content = kb_content

    return _cached_kb_content
@flow
async def generate_application(request: Dict[str, Any], resume_file: Optional[FileStorage] = None) -> Dict[str, Any]:
    """
    Primary Genkit flow for generating tailored career documents and ATS analysis.
    """
    try:
        if resume_file:
            user_profile = await process_resume(resume_file)
        else:
            user_profile = await firestore_client.get_user_profile()

        job_data = await job_scraper.scrape_job_ad(request["job_ad_url"])
        company_name = job_data.get("company_name")
        if not company_name:
            raise ValueError(
                "We couldn't find the company name in the job posting. Please check the job ad URL and try again."
            )
        dossier = await dossier_service.generate_dossier(company_name)
        kb_content = load_knowledge_base()

        prompt = _construct_generation_prompt(
            job_data=job_data,
            user_profile=user_profile,
            kb_content=kb_content,
            dossier=dossier,
            theme_id=request["theme_id"],
            tone_of_voice=request["tone_of_voice"]
        )

        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={
                "maxOutputTokens": 8192,
                "temperature": 0.7,
                "topP": 0.9
            }
        )

        generated_content = _parse_generation_response(response.text)
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


@flow
async def process_resume(resume_file: FileStorage) -> Dict[str, Any]:
    """
    Flow to process an uploaded resume, extract its content, and generate a structured user profile.
    """
    try:
        resume_text = _extract_text_from_file(resume_file)
        prompt = f"""
        You are an expert in parsing resumes. Extract the following information from the provided resume text and return it as a JSON object:
        - personal_details (name, email, phone, address)
        - summary (professional summary or objective)
        - work_experience (list of objects with company, job_title, start_date, end_date, responsibilities)
        - education (list of objects with institution, degree, graduation_date)
        - skills (list of strings)

        Resume Text:
        {resume_text}
        """
        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={"temperature": 0.2}
        )
        structured_profile = json.loads(response.text)
        await firestore_client.update_user_profile(structured_profile)
        return structured_profile
    except Exception as e:
        print(f"Error in process_resume flow: {str(e)}")
        raise e


def _construct_generation_prompt(job_data: Dict, user_profile: Dict, kb_content: str,
                               dossier: Dict, theme_id: str, tone_of_voice: str) -> str:
    """Construct the structured prompt for Gemini 2.5 Pro."""
    prompt = f"""
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
"""
    return prompt


def _parse_generation_response(response_text: str) -> Dict[str, Any]:
    """Parse the Gemini response and extract structured content."""
    try:
        if response_text.strip().startswith('{'):
            parsed = json.loads(response_text)
            return {
                "markdown": parsed.get("markdown_content", ""),
                "document_text": parsed.get("markdown_content", "").replace('#', '').replace('*', '')
            }
        else:
            return {
                "markdown": response_text,
                "document_text": response_text.replace('#', '').replace('*', '')
            }
    except json.JSONDecodeError:
        return {
            "markdown": response_text,
            "document_text": response_text.replace('#', '').replace('*', '')
        }


def _extract_text_from_file(file: FileStorage) -> str:
    """
    Extracts text content from a given file (PDF or DOCX).
    """
    filename = (file.filename or '').lower()
    text = ""
    try:
        if filename.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(file.read()))
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file.read()))
            for para in doc.paragraphs:
                text += para.text + '\n'
        else:
            raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")
    except Exception as e:
        print(f"Error extracting text from {filename}: {str(e)}")
        raise
    return text
