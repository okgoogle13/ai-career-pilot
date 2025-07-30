import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()


def get_env_var(var_name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Helper function to get environment variables with validation.
    
    Args:
        var_name (str): The name of the environment variable
        default (Optional[str]): Default value if environment variable is not set
        required (bool): Whether the environment variable is required
        
    Returns:
        Optional[str]: The environment variable value or default
        
    Raises:
        ValueError: If a required environment variable is missing
        
    Example:
        >>> api_key = get_env_var('API_KEY', required=True)
        >>> optional_setting = get_env_var('OPTIONAL_SETTING', default='default_value')
    """
    value = os.getenv(var_name, default)
    if required and not value:
        raise ValueError(f"Required environment variable '{var_name}' is not set. "
                        f"Please set it in your environment or .env file.")
    return value


class Config:
    """
    Configuration class for the Personal AI Career Co-Pilot.
    
    This class loads and validates configuration settings from environment variables,
    sets up logging, and provides a centralized configuration management system.
    
    Required Environment Variables:
        - FIREBASE_PROJECT_ID: Google Cloud Project ID for Firebase services
        - GEMINI_API_KEY: API key for Google's Gemini AI service  
        - PINECONE_API_KEY: API key for Pinecone vector database service
        
    Optional Environment Variables:
        - PINECONE_ENVIRONMENT: Pinecone environment (e.g., 'us-west1-gcp')
        - LOG_LEVEL: Logging level (default: 'INFO')
        
    Example:
        >>> # Set environment variables
        >>> os.environ['FIREBASE_PROJECT_ID'] = 'my-project'
        >>> os.environ['GEMINI_API_KEY'] = 'your-api-key'
        >>> os.environ['PINECONE_API_KEY'] = 'your-pinecone-key'
        >>> 
        >>> # Initialize configuration
        >>> config = Config()
        >>> print(config.FIREBASE_PROJECT_ID)  # 'my-project'
    """
    
    def __init__(self):
        """
        Initializes the configuration settings.
        
        This method:
        1. Sets up logging configuration
        2. Loads and validates Firebase/Google Cloud settings
        3. Loads and validates AI service API keys
        4. Loads vector database configuration
        5. Sets application-specific settings
        
        Raises:
            ValueError: If any required environment variables are missing or invalid
        """
        # Setup logging configuration
        self._setup_logging()
        
        # Firebase/Google Cloud Project Configuration
        # Group all Firebase-related settings together
        self._load_firebase_config()
        
        # AI Service Configuration
        # Group all AI service API keys together  
        self._load_ai_service_config()
        
        # Vector Database Configuration
        # Group all Pinecone-related settings together
        self._load_vector_db_config()
        
        # Application Settings
        # Group all application-specific settings together
        self._load_application_config()
        
        # Log successful configuration loading
        self.logger.info("Configuration loaded successfully")
        
    def _setup_logging(self) -> None:
        """
        Configure Python logging for the application.
        
        Sets up basic logging configuration with a consistent format
        and creates a logger instance for this configuration class.
        """
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Configure basic logging
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create logger instance for this class
        self.logger = logging.getLogger(__name__)
        
    def _load_firebase_config(self) -> None:
        """
        Load and validate Firebase/Google Cloud configuration.
        
        Raises:
            ValueError: If FIREBASE_PROJECT_ID is not set
        """
        self.FIREBASE_PROJECT_ID: str = get_env_var(
            'FIREBASE_PROJECT_ID', 
            required=True
        )
        
    def _load_ai_service_config(self) -> None:
        """
        Load and validate AI service API keys.
        
        Raises:
            ValueError: If required API keys are not set
        """
        self.GEMINI_API_KEY: str = get_env_var(
            'GEMINI_API_KEY',
            required=True
        )
        
    def _load_vector_db_config(self) -> None:
        """
        Load and validate vector database configuration.
        
        Raises:
            ValueError: If PINECONE_API_KEY is not set
        """
        self.PINECONE_API_KEY: str = get_env_var(
            'PINECONE_API_KEY',
            required=True
        )
        
        self.PINECONE_ENVIRONMENT: Optional[str] = get_env_var(
            'PINECONE_ENVIRONMENT'
        )
        
    def _load_application_config(self) -> None:
        """
        Load application-specific configuration settings.
        
        These settings have sensible defaults and are not required
        to be set via environment variables.
        """
        self.DEFAULT_USER_ID: str = "primary_user"
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Placeholder for additional application settings
        # Add new application-specific configuration here:
        # self.SOME_NEW_SETTING: str = get_env_var('SOME_NEW_SETTING', default='default_value')
        
    def __repr__(self) -> str:
        """
        String representation of the Config object for debugging.
        
        This method provides a safe representation that does not expose
        sensitive API keys or credentials in logs.
        
        Returns:
            str: Safe string representation of the configuration
        """
        # Avoid printing sensitive keys
        safe_config = {
            "FIREBASE_PROJECT_ID": self.FIREBASE_PROJECT_ID,
            "DEFAULT_USER_ID": self.DEFAULT_USER_ID,
            "LOG_LEVEL": self.LOG_LEVEL,
            "GEMINI_API_KEY_SET": 'Yes' if self.GEMINI_API_KEY else 'No',
            "PINECONE_API_KEY_SET": 'Yes' if self.PINECONE_API_KEY else 'No',
            "PINECONE_ENVIRONMENT": self.PINECONE_ENVIRONMENT,
        }
        return f"<Config {safe_config}>"


# Create a single instance of the config to be imported by other modules
# This ensures consistent configuration across the entire application
config = Config()
