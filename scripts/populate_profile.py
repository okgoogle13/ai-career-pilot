#!/usr/bin/env python3
"""
Script to populate user profile from resume using Firebase and Gemini AI
"""
import argparse
import json
import os
import sys
import re
from pathlib import Path

def clean_ai_response(response_text):
    """Clean AI response by removing markdown code blocks"""
    # Remove ```json and ``` markers
    cleaned = re.sub(r'^```json\s*', '', response_text.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def parse_resume_with_ai(resume_text, gemini_key):
    """Parse resume using Gemini AI"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=gemini_key)
        # Using the correct model name as previously discussed
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        Extract the following information from this resume and return it as valid JSON:
        {{
            "fullName": "",
            "email": "",
            "phone": "",
            "location": "",
            "personalStatement": "",
            "skills": [],
            "experience": [],
            "education": []
        }}
        
        Resume text:
        {resume_text}
        """
        
        response = model.generate_content(prompt)
        raw_response = response.text
        
        print(f"Raw AI response: {raw_response[:200]}...")
        
        # Clean the response
        cleaned_response = clean_ai_response(raw_response)
        
        try:
            parsed_data = json.loads(cleaned_response)
            return parsed_data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse cleaned AI response as JSON: {e}")
            print(f"Cleaned response: {cleaned_response[:500]}...")
            return None
            
    except Exception as e:
        print(f"Error calling Gemini AI: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Populate user profile from resume')
    parser.add_argument('resume_path', help='Path to resume PDF file')
    parser.add_argument('--firebase-creds', help='Path to Firebase credentials')
    # CORRECTED: Changed argument to '--gemini-key' to match its usage below
    parser.add_argument('--gemini-key', help='Gemini API key')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.resume_path):
        print(f"❌ Error: Resume file not found: {args.resume_path}")
        return 1
    
    print("✅ Profile Populator initialized successfully")
    print(f"📄 Processing resume: {args.resume_path}")
    
    # Extract text from resume
    resume_text = extract_text_from_pdf(args.resume_path)
    
    if resume_text:
        print(f"📝 Extracted {len(resume_text)} characters from resume")
        
        # Parse with AI
        # CORRECTED: This check now works correctly
        if args.gemini_key:
            print("🤖 Parsing resume with AI...")
            profile_data = parse_resume_with_ai(resume_text, args.gemini_key)
            
            if profile_data:
                print("✅ Successfully parsed resume with AI")
                print(f"Full Name: {profile_data.get('fullName', 'N/A')}")
                print(f"Email: {profile_data.get('email', 'N/A')}")
                print(f"Phone: {profile_data.get('phone', 'N/A')}")
                print("🚀 Profile population completed successfully!")
                return 0
            else:
                print("❌ Failed to parse resume with AI")
        else:
            print("⚠️ No Gemini API key provided, skipping AI parsing")
    else:
        print("❌ Failed to extract text from resume")
        return 1
    
    print("💥 Profile population failed!")
    return 1

if __name__ == "__main__":
    sys.exit(main())