"""
Background Research Dossier Generator
Generates a detailed dossier on a hiring organization using AI.
"""

from typing import Dict, Any
from genkit import ai
from genkit.models.googleai import gemini_2_5_pro

class DossierGenerator:
    """
    Generates a detailed dossier on a company using web search and AI.
    """

    def __init__(self):
        """Initialize the DossierGenerator."""
        self.model = gemini_2_5_pro

    async def generate_dossier(self, company_name: str) -> Dict[str, Any]:
        """
        Perform background research and generate a dossier on the hiring organization.

        Args:
            company_name: The name of the company to research.

        Returns:
            A dictionary containing the company dossier.
        """
        try:
            prompt = self._construct_dossier_prompt(company_name)

            response = await ai.generate(
                model=self.model,
                prompt=prompt,
                config={
                    "maxOutputTokens": 4096,
                    "temperature": 0.5,
                }
            )

            return self._parse_dossier_response(response.text)

        except Exception as e:
            print(f"Error generating dossier for {company_name}: {str(e)}")
            return {
                "error": str(e),
                "organizational_overview": "Could not generate dossier.",
                "communication_style": "N/A",
                "strategic_priorities": "N/A",
                "key_pain_points": "N/A"
            }

    def _construct_dossier_prompt(self, company_name: str) -> str:
        """Construct the prompt for the dossier generation."""

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

    def _parse_dossier_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI's response to extract the structured dossier."""
        import json
        try:
            # The model should return a JSON string.
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Handle cases where the response is not valid JSON
            return {
                "error": "Failed to parse dossier response.",
                "raw_response": response_text
            }
