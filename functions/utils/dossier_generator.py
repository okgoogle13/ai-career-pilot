"""
Background Research Dossier Generator
Generates a detailed dossier on a hiring organization using AI.
"""

from typing import Dict, Any
from genkit import ai
from genkit.models.googleai import gemini_2_5_pro
from prompts import construct_dossier_prompt
from schemas import DossierOutput
from pydantic import ValidationError

class DossierGenerator:
    """
    Generates a detailed dossier on a company using web search and AI.
    """

    def __init__(self):
        """Initialize the DossierGenerator."""
        self.model = gemini_2_5_pro

    async def generate_dossier(self, company_name: str, firestore_client) -> Dict[str, Any]:
        """
        Perform background research and generate a dossier on the hiring organization.
        Caches results in Firestore to avoid redundant AI calls.

        Args:
            company_name: The name of the company to research.
            firestore_client: An instance of the FirestoreClient.

        Returns:
            A dictionary containing the company dossier.
        """
        # Check for a cached dossier first
        cached_dossier = await firestore_client.get_dossier(company_name)
        if cached_dossier:
            print(f"Returning cached dossier for {company_name}")
            return cached_dossier

        try:
            prompt = construct_dossier_prompt(company_name)

            response = await ai.generate(
                model=self.model,
                prompt=prompt,
                config={
                    "maxOutputTokens": 4096,
                    "temperature": 0.5,
                }
            )

            dossier_data = self._parse_dossier_response(response.text)

            # Cache the new dossier
            try:
                # Validate dossier_data using the DossierOutput model
                validated_dossier = DossierOutput(**dossier_data)
                await firestore_client.save_dossier(company_name, validated_dossier.model_dump())
            except ValidationError as e:
                print(f"Validation error for dossier data: {e}")
                return {
                    "error": "Validation failed for dossier data.",
                    "details": str(e)
                }
            return dossier_data

        except Exception as e:
            print(f"Error generating dossier for {company_name}: {str(e)}")
            return {
                "error": str(e),
                "organizational_overview": "Could not generate dossier.",
                "communication_style": "N/A",
                "strategic_priorities": "N/A",
                "key_pain_points": "N/A"
            }


    def _parse_dossier_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI's response to extract the structured dossier."""
        import json
        try:
            # The model should return a JSON string.
            parsed_data = json.loads(response_text)
            validated_data = DossierOutput(**parsed_data)
            return validated_data.dict()
        except (json.JSONDecodeError, ValidationError) as e:
            # Handle cases where the response is not valid JSON
            print(f"Error parsing or validating dossier response: {e}")
            return {
                "error": "Failed to parse dossier response.",
                "raw_response": response_text
            }
