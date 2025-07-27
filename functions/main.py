"""
Personal AI Career Co-Pilot - Main Genkit Flows
Firebase Cloud Functions backend implementing document generation and job scouting.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Genkit imports
from genkit import ai
from genkit.flows import flow
from genkit.core import generate

# Firebase imports
from firebase_functions import https_fn, scheduler_fn
from firebase_admin import initialize_app, firestore
import google.cloud.firestore

# Google AI imports
from genkit.models.googleai import gemini_1_5_pro

# Local utilities
# Note: Ensure these files exist in the 'utils' directory
from utils.scraper import JobAdScraper
from utils.firebase_client import FirestoreClient
from utils.pdf_generator import PDFGenerator
from config import config

# Initialize Firebase Admin SDK
initialize_app()

# Initialize Firestore client
db = firestore.client()
firestore_client = FirestoreClient(db)

# Initialize utilities
job_scraper = JobAdScraper()
pdf_generator = PDFGenerator()

# Load knowledge base content
def load_knowledge_base() -> str:
    """Load all knowledge base artifacts into a single context string."""
    kb_dir = Path(__file__).parent / "kb"
    kb_content = ""
    
    # Load all knowledge base files
    kb_files = [
        "pdf_themes_json.json",
        "australian_sector_glossary.md", 
        "skill_taxonomy_community_services.md",
        "Gold Standard Knowledge Artifact.md"
    ]
    
    for filename in kb_files:
        file_path = kb_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                kb_content += f"\n\n=== {filename} ===\n"
                kb_content += f.read()
    
    return kb_content

@flow
async def generate_application(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Primary Genkit flow for generating tailored career documents and ATS analysis.
    
    Args:
        request: {
            "job_ad_url": str,
            "theme_id": str, 
            "tone_of_voice": str
        }
    
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
        # Step 1: Scrape job advertisement
        job_data = await job_scraper.scrape_job_ad(request["job_ad_url"])
        
        # Step 2: Retrieve user profile from Firestore
        user_profile = await firestore_client.get_user_profile()
        
        # Step 3: Load knowledge base content
        kb_content = load_knowledge_base()
        
        # Step 4: Construct structured prompt for Gemini
        prompt = _construct_generation_prompt(
            job_data=job_data,
            user_profile=user_profile,
            kb_content=kb_content,
            theme_id=request["theme_id"],
            tone_of_voice=request["tone_of_voice"]
        )
        
        # Step 5: Generate content using Gemini
        model = gemini_1_5_pro
        response = await generate(
            model=model,
            prompt=prompt,
            config={
                "max_output_tokens": 8192,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )
        
        # Step 6: Parse response and extract components
        generated_content = _parse_generation_response(response.text())
        
        # Step 7: Perform ATS analysis
        ats_analysis = _perform_ats_analysis(
            generated_content["document_text"],
            job_data["job_description"] + " " + job_data.get("selection_criteria", "")
        )
        
        return {
            "generatedMarkdown": generated_content["markdown"],
            "atsAnalysis": ats_analysis
        }
        
    except Exception as e:
        print(f"Error in generate_application flow: {str(e)}")
        raise e

def _construct_generation_prompt(job_data: Dict, user_profile: Dict, kb_content: str, 
                               theme_id: str, tone_of_voice: str) -> str:
    """Construct the structured prompt for Gemini."""
    
    prompt = f"""
You are an expert Australian community services career consultant with deep knowledge of the sector. Your task is to generate a tailored career document (resume, cover letter, or KSC response) and perform ATS analysis.

JOB ADVERTISEMENT DETAILS:
Company: {job_data.get('company_name', 'N/A')}
Position: {job_data.get('job_title', 'N/A')}
Description: {job_data.get('job_description', 'N/A')}
Key Responsibilities: {job_data.get('key_responsibilities', 'N/A')}
Selection Criteria: {job_data.get('selection_criteria', 'N/A')}

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

def _perform_ats_analysis(document_text: str, job_requirements: str) -> Dict[str, Any]:
    """Perform ATS keyword analysis comparing document against job requirements."""
    
    import re
    
    # Extract keywords from job requirements
    job_keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', job_requirements.lower()))
    job_keywords = {word for word in job_keywords if len(word) > 3}
    
    # Extract keywords from document
    doc_keywords = set(re.findall(r'\b[a-zA-Z]{3,}\b', document_text.lower()))
    
    # Find matches
    matched_keywords = list(job_keywords.intersection(doc_keywords))
    missing_keywords = list(job_keywords - doc_keywords)
    
    # Calculate match percentage
    match_percent = (len(matched_keywords) / len(job_keywords)) * 100 if job_keywords else 0
    
    # Generate suggestions
    suggestions = f"Consider incorporating these missing keywords: {', '.join(missing_keywords[:10])}" if missing_keywords else "Excellent keyword coverage!"
    
    return {
        "keywordMatchPercent": round(match_percent, 1),
        "matchedKeywords": matched_keywords[:20],
        "missingKeywords": missing_keywords[:20],
        "suggestions": suggestions
    }

# HTTP endpoints for Firebase Functions
@https_fn.on_request()
def generate_application_http(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint for the generate_application flow."""
    
    if req.method != 'POST':
        return https_fn.Response("Method not allowed", status=405)
    
    try:
        request_data = req.get_json()
        
        # Run the async flow
        result = asyncio.run(generate_application(request_data))
        
        return https_fn.Response(
            json.dumps(result),
            status=200,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={"Content-Type": "application/json"}
        )

