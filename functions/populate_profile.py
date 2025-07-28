#!/usr/bin/env python3
"""
Personal AI Career Co-Pilot - Profile Population Script
Local script to parse user documents and populate Firestore profile using Gemini 2.5 Pro
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Firebase Admin SDK
from firebase_admin import initialize_app, credentials, firestore
import google.cloud.firestore

# Google AI for document parsing
from google.generativeai import GenerativeModel, configure
import google.generativeai as genai

# Document parsing libraries
import PyPDF2
from docx import Document

class ProfilePopulator:
    """
    Parses user career documents and creates structured profile in Firestore
    """
    
    def __init__(self, firebase_creds_path: str, gemini_api_key: str):
        """
        Initialize the profile populator
        
        Args:
            firebase_creds_path: Path to Firebase service account credentials
            gemini_api_key: Google AI API key for Gemini
        """
        
        # Initialize Firebase Admin
        cred = credentials.Certificate(firebase_creds_path)
        initialize_app(cred)
        self.db = firestore.client()
        
        # Initialize Gemini AI
        configure(api_key=gemini_api_key)
        self.model = GenerativeModel('gemini-2.5-pro')
        
        print("✅ Profile Populator initialized successfully")
    
    def populate_profile_from_resume(self, resume_path: str, 
                                   user_id: str = "primary_user") -> bool:
        """
        Parse resume and populate user profile in Firestore
        
        Args:
            resume_path: Path to resume file (PDF or DOCX)
            user_id: User identifier in Firestore
            
        Returns:
            Success boolean
        """
        
        try:
            print(f"📄 Processing resume: {resume_path}")
            
            # Extract text from resume
            resume_text = self._extract_document_text(resume_path)
            
            if not resume_text:
                print("❌ Failed to extract text from resume")
                return False
            
            print(f"📝 Extracted {len(resume_text)} characters from resume")
            
            # Parse resume using Gemini 2.5 Pro
            structured_profile = self._parse_resume_with_ai(resume_text)
            
            if not structured_profile:
                print("❌ Failed to parse resume with AI")
                return False
            
            # Save to Firestore
            success = self._save_profile_to_firestore(structured_profile, user_id)
            
            if success:
                print("✅ Profile populated successfully!")
                self._print_profile_summary(structured_profile)
            else:
                print("❌ Failed to save profile to Firestore")
            
            return success
            
        except Exception as e:
            print(f"❌ Error populating profile: {str(e)}")
            return False
    
    def populate_from_multiple_documents(self, document_paths: List[str], 
                                       user_id: str = "primary_user") -> bool:
        """
        Parse multiple career documents and create comprehensive profile
        
        Args:
            document_paths: List of paths to career documents
            user_id: User identifier in Firestore
            
        Returns:
            Success boolean
        """
        
        try:
            print(f"📚 Processing {len(document_paths)} documents")
            
            all_documents_text = ""
            document_types = []
            
            # Extract text from all documents
            for doc_path in document_paths:
                doc_text = self._extract_document_text(doc_path)
                if doc_text:
                    all_documents_text += f"\n\n=== {Path(doc_path).name} ===\n{doc_text}"
                    document_types.append(self._identify_document_type(doc_text))
            
            if not all_documents_text:
                print("❌ No text extracted from any documents")
                return False
            
            print(f"📝 Extracted text from documents: {', '.join(document_types)}")
            
            # Parse combined documents with AI
            structured_profile = self._parse_multiple_documents_with_ai(
                all_documents_text, document_types
            )
            
            if not structured_profile:
                print("❌ Failed to parse documents with AI")
                return False
            
            # Save to Firestore
            success = self._save_profile_to_firestore(structured_profile, user_id)
            
            if success:
                print("✅ Comprehensive profile populated successfully!")
                self._print_profile_summary(structured_profile)
            else:
                print("❌ Failed to save profile to Firestore")
            
            return success
            
        except Exception as e:
            print(f"❌ Error processing multiple documents: {str(e)}")
            return False
    
    def _extract_document_text(self, file_path: str) -> Optional[str]:
        """
        Extract text from PDF or DOCX file
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text or None if failed
        """
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return None
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return self._extract_docx_text(file_path)
            else:
                print(f"❌ Unsupported file format: {file_path.suffix}")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting text from {file_path}: {str(e)}")
            return None
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyPDF2"""
        
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"❌ PyPDF2 failed to extract text: {str(e)}")
            return ""
        
        return text.strip()
    
    def _extract_docx_text(self, docx_path: Path) -> str:
        """Extract text from DOCX file"""
        
        try:
            doc = Document(str(docx_path))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            print(f"❌ Error extracting DOCX text: {str(e)}")
            return ""
    
    def _identify_document_type(self, text: str) -> str:
        """
        Identify document type based on content
        
        Args:
            text: Document text
            
        Returns:
            Document type (resume, cover_letter, ksc_response)
        """
        
        text_lower = text.lower()
        
        # Look for key selection criteria indicators
        if any(phrase in text_lower for phrase in [
            'selection criteria', 'key selection criteria', 'essential criteria',
            'situation:', 'task:', 'action:', 'result:', 'star method'
        ]):
            return 'ksc_response'
        
        # Look for cover letter indicators
        elif any(phrase in text_lower for phrase in [
            'dear hiring manager', 'dear sir/madam', 'i am writing to apply',
            'position advertised', 'your advertisement', 'sincerely'
        ]):
            return 'cover_letter'
        
        # Default to resume
        else:
            return 'resume'
    
    def _parse_resume_with_ai(self, resume_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse resume text using Gemini 2.5 Pro to extract structured data
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Structured profile data or None if failed
        """
        
        prompt = f"""
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
"""
        
        try:
            response = self.model.generate_content(prompt)
            
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
    
    def _parse_multiple_documents_with_ai(self, documents_text: str, 
                                        document_types: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse multiple career documents using Gemini 2.5 Pro
        
        Args:
            documents_text: Combined text from all documents
            document_types: List of identified document types
            
        Returns:
            Comprehensive structured profile data
        """
        
        prompt = f"""
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
"""
        
        try:
            response = self.model.generate_content(prompt)
            
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
    
    def _save_profile_to_firestore(self, profile_data: Dict[str, Any], 
                                 user_id: str) -> bool:
        """
        Save structured profile data to Firestore
        
        Args:
            profile_data: Structured profile information
            user_id: User identifier
            
        Returns:
            Success boolean
        """
        
        try:
            # Save to profiles collection
            doc_ref = self.db.collection('profiles').document(user_id)
            doc_ref.set(profile_data, merge=False)  # Overwrite existing
            
            print(f"💾 Profile saved to Firestore for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to Firestore: {str(e)}")
            return False
    
    def _print_profile_summary(self, profile_data: Dict[str, Any]) -> None:
        """Print a summary of the populated profile"""
        
        print("\n" + "="*50)
        print("PROFILE SUMMARY")
        print("="*50)
        
        print(f"Name: {profile_data.get('fullName', 'Not found')}")
        print(f"Email: {profile_data.get('email', 'Not found')}")
        print(f"Phone: {profile_data.get('phone', 'Not found')}")
        print(f"Location: {profile_data.get('location', 'Not found')}")
        
        # Work experience summary
        work_exp = profile_data.get('workExperience', [])
        print(f"\nWork Experience: {len(work_exp)} positions")
        for i, job in enumerate(work_exp[:3]):  # Show first 3
            print(f"  {i+1}. {job.get('jobTitle')} at {job.get('employer')}")
        
        # Education summary
        education = profile_data.get('education', [])
        print(f"\nEducation: {len(education)} qualifications")
        
        # Skills summary
        skills = profile_data.get('skills', [])
        total_skills = sum(len(cat.get('skills', [])) for cat in skills)
        print(f"Skills: {total_skills} skills across {len(skills)} categories")
        
        print("\n" + "="*50)

def main():
    """Main entry point for the profile population script"""
    
    parser = argparse.ArgumentParser(
        description='Populate user profile in Firestore from career documents'
    )
    
    parser.add_argument(
        'documents', 
        nargs='+',
        help='Path(s) to career documents (PDF or DOCX)'
    )
    
    parser.add_argument(
        '--firebase-creds',
        required=True,
        help='Path to Firebase service account credentials JSON file'
    )
    
    parser.add_argument(
        '--gemini-key',
        required=True,
        help='Google AI API key for Gemini'
    )
    
    parser.add_argument(
        '--user-id',
        default='primary_user',
        help='User ID in Firestore (default: primary_user)'
    )
    
    parser.add_argument(
        '--test-extract',
        action='store_true',
        help='Test text extraction without AI parsing or Firestore saving'
    )
    
    args = parser.parse_args()
    
    # Validate files exist
    for doc_path in args.documents:
        if not Path(doc_path).exists():
            print(f"❌ File not found: {doc_path}")
            sys.exit(1)
    
    if not Path(args.firebase_creds).exists():
        print(f"❌ Firebase credentials file not found: {args.firebase_creds}")
        sys.exit(1)
    
    try:
        # Test mode - just extract text
        if args.test_extract:
            print("🧪 TEST MODE: Extracting text only")
            populator = ProfilePopulator(args.firebase_creds, args.gemini_key)
            
            for doc_path in args.documents:
                print(f"\n📄 Extracting from: {doc_path}")
                text = populator._extract_document_text(doc_path)
                if text:
                    print(f"✅ Extracted {len(text)} characters")
                    print(f"Preview: {text[:200]}...")
                else:
                    print("❌ No text extracted")
            return
        
        # Initialize populator
        populator = ProfilePopulator(args.firebase_creds, args.gemini_key)
        
        # Process documents
        if len(args.documents) == 1:
            success = populator.populate_profile_from_resume(
                args.documents[0], 
                args.user_id
            )
        else:
            success = populator.populate_from_multiple_documents(
                args.documents,
                args.user_id
            )
        
        if success:
            print("\n🎉 Profile population completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Profile population failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
