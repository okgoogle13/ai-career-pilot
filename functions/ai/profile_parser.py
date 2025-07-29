"""
AI service for parsing and populating user profiles.
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from google.generativeai import GenerativeModel

def parse_resume_with_ai(resume_text: str, model: GenerativeModel) -> Optional[Dict[str, Any]]:
    """
    Parse resume text using Gemini 2.5 Pro to extract structured data

    Args:
        resume_text: Raw resume text
        model: The GenerativeModel to use for parsing.

    Returns:
        Structured profile data or None if failed
    """

    prompt = """
You are an expert career counselor specializing in Australian Community Services sector roles.
Parse the following resume and extract structured information in JSON format.

RESUME TEXT:
{resume_text}

Please extract and structure the information into the following JSON schema:
{{
    "fullName": "string",
    "email": "string",
    "phone": "string",
    "location": "string (suburb, state format if available)",
    "personalStatement": "string (professional summary if available)",
    "workExperience": [
        {{
            "jobTitle": "string",
            "employer": "string",
            "location": "string",
            "startDate": "string (YYYY-MM format if available, otherwise approximate)",
            "endDate": "string or 'Present'",
            "responsibilities": ["list of key responsibilities"],
            "achievements": ["list of achievements with metrics where possible"]
        }}
    ],
    "education": [
        {{
            "qualification": "string",
            "institution": "string",
            "year": "string",
            "details": "string (additional details if available)"
        }}
    ],
    "skills": [
        {{
            "category": "string (e.g., 'Technical Skills', 'Interpersonal Skills')",
            "skills": ["list of specific skills"]
        }}
    ],
    "certifications": [
        {{
            "name": "string",
            "issuer": "string",
            "year": "string",
            "expiryDate": "string (if applicable)"
        }}
    ],
    "volunteerWork": [
        {{
            "role": "string",
            "organization": "string",
            "duration": "string",
            "description": "string"
        }}
    ]
}}

Guidelines:
- Use Australian spelling and formatting
- Extract exact information where available, avoid assumptions
- Format phone numbers in Australian format if possible
- Identify community services related experience and skills
- Use empty arrays [] for sections with no information
- Ensure all JSON is valid and properly formatted

Return only the JSON object, no additional text.
\"\"\"

    try:
        response = model.generate_content(prompt)

        if not response.text:
            print("❌ No response from Gemini AI")
            return None

        # Parse JSON response
        profile_data = json.loads(response.text.strip())

        # Add metadata
        profile_data['createdAt'] = datetime.utcnow().isoformat()
        profile_data['lastUpdated'] = datetime.utcnow().isoformat()
        profile_data['dataSource'] = 'resume_parse'

        return profile_data

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse AI response as JSON: {str(e)}")
        print(f"Raw response: {response.text[:500]}...")
        return None

    except Exception as e:
        print(f"❌ Error calling Gemini AI: {str(e)}")
        return None

def parse_multiple_documents_with_ai(documents_text: str,
                                    document_types: List[str],
                                    model: GenerativeModel) -> Optional[Dict[str, Any]]:
    """
    Parse multiple career documents using Gemini 2.5 Pro

    Args:
        documents_text: Combined text from all documents
        document_types: List of identified document types
        model: The GenerativeModel to use for parsing.

    Returns:
        Comprehensive structured profile data
    """

    prompt = f\"\"\"
You are an expert career counselor specializing in Australian Community Services sector roles.
Parse the following career documents and create a comprehensive profile in JSON format.

DOCUMENT TYPES IDENTIFIED: {', '.join(document_types)}

DOCUMENTS TEXT:
{documents_text}

Create a comprehensive profile by extracting and consolidating information from all documents.
Use the following JSON schema:

{{
    "fullName": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "personalStatement": "string (synthesize from all documents)",
    "workExperience": [
        {{
            "jobTitle": "string",
            "employer": "string",
            "location": "string",
            "startDate": "string",
            "endDate": "string or 'Present'",
            "responsibilities": ["detailed list"],
            "achievements": ["quantified achievements where possible"],
            "keySkillsDemonstrated": ["skills shown in this role"]
        }}
    ],
    "education": [...],
    "skills": [
        {{
            "category": "string",
            "skills": ["list"],
            "proficiencyLevel": "Beginner|Intermediate|Advanced|Expert"
        }}
    ],
    "certifications": [...],
    "volunteerWork": [...],
    "careerHighlights": ["3-5 top achievements across all documents"],
    "sectorExperience": {{
        "communityServices": "number of years",
        "specificAreas": ["list of CS sub-sectors"],
        "clientGroups": ["populations worked with"],
        "serviceTypes": ["types of services delivered"]
    }},
    "writingSamples": {{
        "hasKSCExperience": boolean,
        "writingStrengths": ["identified from documents"],
        "preferredStyle": "professional|conversational|confident|compassionate"
    }}
}}

Instructions:
- Consolidate duplicate information intelligently
- Prioritize most recent and relevant information
- Identify community services specific experience and terminology
- Note any gaps or inconsistencies for future reference
- Use Australian terminology and formatting
- Extract examples of strong achievement statements using CAR/STAR methodology

Return only the JSON object.
\"\"\"

    try:
        response = model.generate_content(prompt)

        if not response.text:
            print("❌ No response from Gemini AI")
            return None

        profile_data = json.loads(response.text.strip())

        # Add metadata
        profile_data['createdAt'] = datetime.utcnow().isoformat()
        profile_data['lastUpdated'] = datetime.utcnow().isoformat()
        profile_data['dataSource'] = 'multi_document_parse'
        profile_data['sourcedDocuments'] = document_types

        return profile_data

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse AI response as JSON: {str(e)}")
        return None

    except Exception as e:
        print(f"❌ Error calling Gemini AI: {str(e)}")
        return None
