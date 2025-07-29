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
import io

# Genkit imports
from genkit import ai, flow
from genkit.core import generate
from genkit.models.googleai import gemini_2_5_pro

# Firebase imports
from firebase_functions import https_fn, scheduler_fn
from firebase_admin import initialize_app, firestore, auth
from werkzeug.datastructures import FileStorage

# Local utilities
from utils.scraper import JobAdScraper
from utils.firebase_client import FirestoreClient
from utils.pdf_generator import PDFGenerator
from utils.gmail_client import GmailClient
from utils.calendar_client import CalendarClient
from utils.dossier_generator import DossierGenerator
from utils.ats_analyzer import ATSAnalyzer
from config import Config
from prompts import construct_generation_prompt, construct_resume_processing_prompt
from schemas import GenerationOutput, UserProfile

# Resume parsing libraries
import docx
from pypdf import PdfReader
from pydantic import ValidationError

# Initialize Firebase Admin SDK
initialize_app()

# Initialize configuration
config = Config()

# Initialize Firestore client
db = firestore.client()
firestore_client = FirestoreClient(db)

# Initialize utilities
job_scraper = JobAdScraper()
pdf_generator = PDFGenerator()
gmail_client = GmailClient()
calendar_client = CalendarClient()
dossier_generator = DossierGenerator()
ats_analyzer = ATSAnalyzer()

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
        dossier = await dossier_generator.generate_dossier(company_name, firestore_client)
        
        # Step 5: Load knowledge base content
        kb_content = load_knowledge_base()
        
        # Step 6: Construct structured prompt for Gemini 2.5 Pro
        prompt = construct_generation_prompt(
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

@flow
async def job_scout() -> Dict[str, Any]:
    """
    Scheduled Genkit flow for monitoring Gmail and creating calendar events.
    Scans for interview invitations and job opportunities.
    
    Returns:
        {
            "processedEmails": int,
            "eventsCreated": int,
            "status": str
        }
    """
    
    try:
        # Scan for unread emails from job alert senders
        target_senders = [
            "noreply@s.seek.com.au",
            "noreply@ethicaljobs.com.au",
            "donotreply@jora.com",
            "support@careers.vic.gov.au"
        ]
        
        processed_emails = 0
        events_created = 0
        
        for sender in target_senders:
            # Get unread emails from sender
            emails = await gmail_client.get_unread_emails(sender)
            
            for email in emails:
                # Parse email for job opportunities
                job_opportunities = _extract_job_opportunities(email)
                
                # Create calendar reminders for each opportunity
                for opportunity in job_opportunities:
                    calendar_event = await calendar_client.create_reminder_event(
                        title=f"Apply: {opportunity['job_title']} - {opportunity['company']}",
                        description=f"Job URL: {opportunity['url']}\nDeadline: {opportunity.get('deadline', 'Not specified')}",
                        reminder_days=2  # Remind 2 days before application deadline
                    )
                    
                    if calendar_event:
                        events_created += 1
                
                # Mark email as read
                await gmail_client.mark_as_read(email['id'])
                processed_emails += 1
        
        return {
            "processedEmails": processed_emails,
            "eventsCreated": events_created,
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in job_scout flow: {str(e)}")
        # Log the error for better debugging
        # from google.cloud import logging
        # client = logging.Client()
        # logger = client.logger('job_scout_errors')
        # logger.log_struct({'message': f"Error in job_scout flow: {str(e)}"}, severity='ERROR')
        return {
            "processedEmails": 0,
            "eventsCreated": 0,
            "status": f"error: {str(e)}"
        }


def _parse_generation_response(response_text: str) -> Dict[str, Any]:
    """Parse the Gemini response and extract structured content."""
    
    try:
        # Try to parse as JSON first
        if response_text.strip().startswith('{'):
            parsed_data = json.loads(response_text)
            validated_data = GenerationOutput(**parsed_data)
            return {
                "markdown": validated_data.markdown_content,
                "document_text": validated_data.markdown_content.replace('#', '').replace('*', '')
            }
        else:
            # Fallback to treating entire response as markdown
            return {
                "markdown": response_text,
                "document_text": response_text.replace('#', '').replace('*', '')
            }
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing or validating generation response: {e}")
        return {
            "markdown": response_text,
            "document_text": response_text.replace('#', '').replace('*', '')
        }


def _extract_job_opportunities(email: Dict) -> List[Dict[str, Any]]:
    """Extract job opportunities from email content."""
    
    opportunities = []
    subject = email.get('subject', '')
    body = email.get('body', '')
    
    # Simple pattern matching for job opportunities
    # This would be enhanced with more sophisticated NLP
    if any(keyword in subject.lower() for keyword in ['job alert', 'new job', 'opportunities']):
        # Extract basic information (this is a simplified implementation)
        opportunities.append({
            "job_title": subject,
            "company": "Unknown",
            "url": "mailto:example@example.com",  # Would extract actual URLs
            "deadline": None
        })
    
    return opportunities

# HTTP endpoints for Firebase Functions
@flow
async def process_resume(resume_file: FileStorage) -> Dict[str, Any]:
    """
    Flow to process an uploaded resume, extract its content, and generate a structured user profile.

    Args:
        resume_file: A FileStorage object representing the uploaded resume.

    Returns:
        A dictionary containing the structured user profile data.
    """
    try:
        # Step 1: Extract text from the resume file
        resume_text = _extract_text_from_file(resume_file)

        # Step 2: Construct prompt for Gemini to parse the resume
        prompt = construct_resume_processing_prompt(resume_text)

        # Step 3: Generate structured profile using Gemini
        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={"temperature": 0.2}
        )

        # Step 4: Parse the JSON response
        structured_profile_data = json.loads(response.text)
        validated_profile = UserProfile(**structured_profile_data)

        # Step 5: Save the structured profile to Firestore
        await firestore_client.update_user_profile(validated_profile.dict())

        return validated_profile.dict()

    except Exception as e:
        print(f"Error in process_resume flow: {str(e)}")
        raise e

def _extract_text_from_file(file: FileStorage) -> str:
    """
    Extracts text content from a given file (PDF or DOCX).

    Args:
        file: A FileStorage object.

    Returns:
        The extracted text content as a string.
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

@https_fn.on_request(cors=True)
def generate_application_http(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint for the generate_application flow."""

    if req.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response("", status=204, headers=headers)

    if req.method != 'POST':
        return https_fn.Response("Method not allowed", status=405)

    # Verify Firebase Auth token
    auth_header = req.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return https_fn.Response("Unauthorized", status=401)

    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
    except auth.InvalidIdTokenError:
        return https_fn.Response("Invalid token", status=401)
    except auth.ExpiredIdTokenError:
        return https_fn.Response("Token expired", status=401)

    try:
        request_data_str = req.form.get('requestData')
        if not request_data_str:
            return https_fn.Response(json.dumps({"error": "Missing requestData"}), status=400, headers={"Content-Type": "application/json"})

        request_data = json.loads(request_data_str)
        resume_file = req.files.get('resume')

        if not all(k in request_data for k in ["job_ad_url", "theme_id", "tone_of_voice"]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        result = asyncio.run(generate_application(request_data, resume_file))
        
        return https_fn.Response(
            json.dumps(result),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": "An unexpected error occurred."}),
            status=500,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
        )

@scheduler_fn.on_schedule(schedule="0 */1 * * *")  # Run every hour
def job_scout_scheduled(event: scheduler_fn.ScheduledEvent) -> None:
    """Scheduled function for job scouting."""
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(job_scout())
        print(f"Job scout completed: {result}")
        
    except Exception as e:
        print(f"Job scout error: {str(e)}")
