"""
Centralized store for all LLM prompts used in the application.
"""

from typing import Dict, Any
import json

def construct_generation_prompt(
    job_data: Dict,
    user_profile: Dict,
    kb_content: str,
    dossier: Dict,
    theme_id: str,
    tone_of_voice: str
) -> str:
    """Constructs the structured prompt for the main document generation flow."""

    prompt = f"""
You are an expert Australian community services career consultant with deep knowledge of the sector. Your task is to generate a tailored career document (resume, cover letter, or KSC response) and perform ATS analysis.

**JOB ADVERTISEMENT DETAILS:**
Company: {job_data.get('company_name', 'N/A')}
Position: {job_data.get('job_title', 'N/A')}
Description: {job_data.get('job_description', 'N/A')}
Key Responsibilities: {job_data.get('key_responsibilities', 'N/A')}
Selection Criteria: {job_data.get('selection_criteria', 'N/A')}

**COMPANY DOSSIER:**
{json.dumps(dossier, indent=2)}

**USER PROFILE:**
{json.dumps(user_profile, indent=2)}

**KNOWLEDGE BASE CONTENT:**
{kb_content}

**GENERATION REQUIREMENTS:**
- Theme: {theme_id}
- Tone of Voice: {tone_of_voice}
- Format: Generate as Markdown with clear structure
- Use Australian spelling and terminology
- Apply sector-specific language from the knowledge base
- Follow the CAR (Context-Action-Result) methodology for achievements
- Use STAR methodology for KSC responses where applicable

**RESPONSE FORMAT:**
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

def construct_dossier_prompt(company_name: str) -> str:
    """Constructs the prompt for the background research dossier generation."""

    prompt = f"""
You are a world-class business analyst. Your task is to conduct thorough research on a company and generate a detailed "dossier".

**Company:** "{company_name}"

**Instructions:**
1.  **Organizational Overview:** Analyze the company's culture, vision, and values. What is their mission? What is the work environment like?
2.  **Communication Style:** Describe the company's typical communication style and tone (e.g., formal, informal, innovative, academic).
3.  **Strategic Priorities:** Identify the company's key strategic priorities for the current and next fiscal year. Look at annual reports, investor briefings, and recent news.
4.  **Key Pain Points:** What are the major challenges and pain points the company is currently facing within its industry?

**Output Format:**
Return the dossier as a JSON object with the following keys:
- "organizational_overview"
- "communication_style"
- "strategic_priorities"
- "key_pain_points"
"""
    return prompt

def construct_resume_processing_prompt(resume_text: str) -> str:
    """Constructs the prompt to process a resume and extract structured data."""

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
    return prompt
