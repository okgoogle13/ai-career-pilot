"""
Pydantic schemas for validating the structure of LLM outputs.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class PersonalDetails(BaseModel):
    name: str
    email: str
    phone: str
    address: str

class WorkExperience(BaseModel):
    company: str
    job_title: str
    start_date: str
    end_date: str
    responsibilities: List[str]

class Education(BaseModel):
    institution: str
    degree: str
    graduation_date: str

class UserProfile(BaseModel):
    personal_details: PersonalDetails
    summary: str
    work_experience: List[WorkExperience]
    education: List[Education]
    skills: List[str]

class GenerationOutput(BaseModel):
    document_type: str
    markdown_content: str
    key_achievements: List[str]
    keywords_used: List[str]

class DossierOutput(BaseModel):
    organizational_overview: str
    communication_style: str
    strategic_priorities: str
    key_pain_points: str
