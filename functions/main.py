"""
Personal AI Career Co-Pilot - Main Entry Point
This file initializes the Firebase application and imports the cloud functions
from their respective modules.
"""

from firebase_admin import initialize_app

# Initialize Firebase Admin SDK
initialize_app()

# Import the cloud functions from their respective modules
from .api.document_generation import generate_application_http
from .jobs.job_scout import job_scout_scheduled

# The following line is for backwards compatibility with the genkit CLI
# and can be removed if you are not using the genkit CLI.
from .ai.document_generator import generate_application
