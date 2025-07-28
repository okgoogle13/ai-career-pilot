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
from genkit import ai, flow
from genkit.core import generate
from genkit.models.googleai import gemini_2_5_pro

# Firebase imports
from firebase_functions import https_fn, scheduler_fn
from firebase_admin import initialize_app, firestore

# Local utilities
from utils.scraper import JobAdScraper
from utils.firebase_client import FirestoreClient
from utils.pdf_generator import PDFGenerator
from utils.gmail_client import GmailClient
from utils.calendar_client import CalendarClient
from config import Config

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
        
        # Step 4: Construct structured prompt for Gemini 2.5 Pro
        prompt = _construct_generation_prompt(
            job_data=job_data,
            user_profile=user_profile,
            kb_content=kb_content,
            theme_id=request["theme_id"],
            tone_of_voice=request["tone_of_voice"]
        )
        
        # Step 5: Generate content using Gemini 2.5 Pro
        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={
                "maxOutputTokens": 8192,
                "temperature": 0.7,
                "topP": 0.9
            }
        )
        
        # Step 6: Parse response and extract components
        generated_content = _parse_generation_response(response.text)
        
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

def _construct_generation_prompt(job_data: Dict, user_profile: Dict, kb_content: str, 
                               theme_id: str, tone_of_voice: str) -> str:
    """Construct the structured prompt for Gemini 2.5 Pro."""
    
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
    
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    import re

    # Download necessary NLTK data
    try:
        stopwords.words('english')
    exceptnltk.downloader.download('stopwords')
    except:
        nltk.downloader.download('punkt')

    stop_words = set(stopwords.words('english'))

    def extract_keywords(text: str) -> set:
        # Remove punctuation and convert to lower case
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Tokenize the text
        tokens = word_tokenize(text)
        # Filter out stop words and short words
        return {word for word in tokens if word not in stop_words and len(word) > 2}

    # Extract keywords from job requirements and document
    job_keywords = extract_keywords(job_requirements)
    doc_keywords = extract_keywords(document_text)

    # Find matches
    matched_keywords = list(job_keywords.intersection(doc_keywords))
    missing_keywords = list(job_keywords - doc_keywords)
    
    # Calculate match percentage
    match_percent = (len(matched_keywords) / len(job_keywords)) * 100 if job_keywords else 0
    
    # Generate suggestions
    suggestions = f"Consider incorporating these missing keywords: {', '.join(missing_keywords[:10])}" if missing_keywords else "Excellent keyword coverage!"
    
    return {
        "keywordMatchPercent": round(match_percent, 1),
        "matchedKeywords": matched_keywords[:20],  # Limit for response size
        "missingKeywords": missing_keywords[:20],   # Limit for response size
        "suggestions": suggestions
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
@https_fn.on_request(cors=True)
def generate_application_http(req: https_fn.Request) -> https_fn.Response:
    """HTTP endpoint for the generate_application flow."""
    
    if req.method == 'OPTIONS':
        # Handle preflight requests for CORS
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return https_fn.Response("", status=204, headers=headers)

    if req.method != 'POST':
        return https_fn.Response("Method not allowed", status=405)
    
    try:
        request_data = req.get_json()
        
        # Basic validation
        if not all(k in request_data for k in ["job_ad_url", "theme_id", "tone_of_voice"]):
            return https_fn.Response(
                json.dumps({"error": "Missing required fields"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )

        # Run the async flow
        result = asyncio.run(generate_application(request_data))
        
        return https_fn.Response(
            json.dumps(result),
            status=200,
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
        )
        
    except Exception as e:
        # Log the error for better debugging
        # from google.cloud import logging
        # client = logging.Client()
        # logger = client.logger('http_errors')
        # logger.log_struct({'message': f"Error in generate_application_http: {str(e)}"}, severity='ERROR')

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
