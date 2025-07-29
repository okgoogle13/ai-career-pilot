"""
AI service for parsing resumes.
"""
import io
import json
from typing import Dict, Any

from genkit import ai, flow
from genkit.core import generate
from genkit.models.googleai import gemini_2_5_pro
from werkzeug.datastructures import FileStorage
import docx
from pypdf import PdfReader

from firebase_admin import firestore
from ..utils.firebase_client import FirestoreClient

# Initialize Firestore client
db = firestore.client()
firestore_client = FirestoreClient(db)

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
        prompt = RESUME_PARSING_PROMPT_TEMPLATE.format(resume_text=resume_text)
        # Step 3: Generate structured profile using Gemini
        response = await generate(
            model=gemini_2_5_pro,
            prompt=prompt,
            config={"temperature": 0.2}
        )

        # Step 4: Parse the JSON response
        structured_profile = json.loads(response.text)

        # Step 5: Save the structured profile to Firestore
        await firestore_client.update_user_profile(structured_profile)

        return structured_profile

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
