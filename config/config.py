import os
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

class Config:
    """
    Configuration class for the Personal AI Career Co-Pilot.
    Loads settings from environment variables with sensible defaults.
    """
    def __init__(self):
        """
        Initializes the configuration settings.
        """
        # Firebase/Google Cloud Project Configuration
        self.FIREBASE_PROJECT_ID: str = os.getenv('FIREBASE_PROJECT_ID', 'your-gcp-project-id')
        
        # Google AI (Gemini) API Key
        self.GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY')

        # Pinecone Configuration (if used for vector storage)
        self.PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY')
        self.PINECONE_ENVIRONMENT: str = os.getenv('PINECONE_ENVIRONMENT')

        # Application settings
        self.DEFAULT_USER_ID: str = "primary_user"
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()

    def __repr__(self) -> str:
        """
        String representation of the Config object for debugging.
        """
        # Avoid printing sensitive keys
        safe_config = {
            "FIREBASE_PROJECT_ID": self.FIREBASE_PROJECT_ID,
            "DEFAULT_USER_ID": self.DEFAULT_USER_ID,
            "LOG_LEVEL": self.LOG_LEVEL,
            "GEMINI_API_KEY_SET": 'Yes' if self.GEMINI_API_KEY else 'No',
            "PINECONE_API_KEY_SET": 'Yes' if self.PINECONE_API_KEY else 'No',
        }
        return f"<Config {safe_config}>"

# Create a single instance of the config to be imported by other modules
config = Config()
