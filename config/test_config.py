"""
Test suite for config.py module.

This module contains comprehensive tests for configuration loading,
validation, and error handling behavior.
"""

import os
import unittest
import logging
from unittest.mock import patch
from typing import Dict, Any

# Import the modules we're testing
from config import get_env_var, Config


class TestGetEnvVar(unittest.TestCase):
    """Test cases for the get_env_var helper function."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Store original environment to restore later
        self.original_env = os.environ.copy()
        
    def tearDown(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_get_env_var_with_existing_variable(self):
        """Test getting an existing environment variable."""
        os.environ['TEST_VAR'] = 'test_value'
        result = get_env_var('TEST_VAR')
        self.assertEqual(result, 'test_value')
    
    def test_get_env_var_with_default(self):
        """Test getting environment variable with default value."""
        result = get_env_var('NON_EXISTENT_VAR', default='default_value')
        self.assertEqual(result, 'default_value')
    
    def test_get_env_var_required_exists(self):
        """Test getting required environment variable that exists."""
        os.environ['REQUIRED_VAR'] = 'required_value'
        result = get_env_var('REQUIRED_VAR', required=True)
        self.assertEqual(result, 'required_value')
    
    def test_get_env_var_required_missing_raises_error(self):
        """Test that missing required environment variable raises ValueError."""
        with self.assertRaises(ValueError) as context:
            get_env_var('MISSING_REQUIRED_VAR', required=True)
        
        self.assertIn("Required environment variable 'MISSING_REQUIRED_VAR' is not set", 
                     str(context.exception))
    
    def test_get_env_var_required_empty_string_raises_error(self):
        """Test that empty required environment variable raises ValueError."""
        os.environ['EMPTY_VAR'] = ''
        with self.assertRaises(ValueError):
            get_env_var('EMPTY_VAR', required=True)
    
    def test_get_env_var_none_default(self):
        """Test getting environment variable with None as default."""
        result = get_env_var('NON_EXISTENT_VAR')
        self.assertIsNone(result)


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Store original environment to restore later
        self.original_env = os.environ.copy()
        
        # Clear any existing environment variables that might interfere
        env_vars_to_clear = [
            'FIREBASE_PROJECT_ID', 
            'GEMINI_API_KEY', 
            'PINECONE_API_KEY',
            'PINECONE_ENVIRONMENT',
            'LOG_LEVEL'
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def _set_valid_environment(self):
        """Helper method to set valid environment variables."""
        os.environ['FIREBASE_PROJECT_ID'] = 'test-project-id'
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
    
    def test_config_with_valid_environment(self):
        """Test Config initialization with all required environment variables set."""
        self._set_valid_environment()
        os.environ['PINECONE_ENVIRONMENT'] = 'test-environment'
        os.environ['LOG_LEVEL'] = 'DEBUG'
        
        config = Config()
        
        # Check that all values are loaded correctly
        self.assertEqual(config.FIREBASE_PROJECT_ID, 'test-project-id')
        self.assertEqual(config.GEMINI_API_KEY, 'test-gemini-key')
        self.assertEqual(config.PINECONE_API_KEY, 'test-pinecone-key')
        self.assertEqual(config.PINECONE_ENVIRONMENT, 'test-environment')
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
        self.assertEqual(config.DEFAULT_USER_ID, 'primary_user')
        
        # Check that logger is created
        self.assertIsInstance(config.logger, logging.Logger)
    
    def test_config_missing_firebase_project_id(self):
        """Test Config initialization fails when FIREBASE_PROJECT_ID is missing."""
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
        
        with self.assertRaises(ValueError) as context:
            Config()
        
        self.assertIn("Required environment variable 'FIREBASE_PROJECT_ID' is not set", 
                     str(context.exception))
    
    def test_config_missing_gemini_api_key(self):
        """Test Config initialization fails when GEMINI_API_KEY is missing."""
        os.environ['FIREBASE_PROJECT_ID'] = 'test-project-id'
        os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
        
        with self.assertRaises(ValueError) as context:
            Config()
        
        self.assertIn("Required environment variable 'GEMINI_API_KEY' is not set", 
                     str(context.exception))
    
    def test_config_missing_pinecone_api_key(self):
        """Test Config initialization fails when PINECONE_API_KEY is missing."""
        os.environ['FIREBASE_PROJECT_ID'] = 'test-project-id'
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        
        with self.assertRaises(ValueError) as context:
            Config()
        
        self.assertIn("Required environment variable 'PINECONE_API_KEY' is not set", 
                     str(context.exception))
    
    def test_config_optional_variables_default_values(self):
        """Test Config handles optional environment variables with defaults."""
        self._set_valid_environment()
        
        config = Config()
        
        # Check optional variables have correct defaults
        self.assertIsNone(config.PINECONE_ENVIRONMENT)
        self.assertEqual(config.LOG_LEVEL, 'INFO')
        self.assertEqual(config.DEFAULT_USER_ID, 'primary_user')
    
    @patch('logging.basicConfig')
    def test_logging_setup(self, mock_basic_config):
        """Test that logging is configured correctly."""
        self._set_valid_environment()
        os.environ['LOG_LEVEL'] = 'WARNING'
        
        config = Config()
        
        # Check that logging.basicConfig was called
        mock_basic_config.assert_called_once()
        
        # Check the call arguments
        call_args = mock_basic_config.call_args
        self.assertEqual(call_args[1]['level'], logging.WARNING)
        self.assertIn('%(asctime)s', call_args[1]['format'])
        self.assertIn('%(name)s', call_args[1]['format'])
        self.assertIn('%(levelname)s', call_args[1]['format'])
        self.assertIn('%(message)s', call_args[1]['format'])
    
    def test_config_repr_does_not_leak_secrets(self):
        """Test that the __repr__ method does not expose sensitive information."""
        self._set_valid_environment()
        
        config = Config()
        repr_str = repr(config)
        
        # Check that sensitive keys are not in the repr
        self.assertNotIn('test-gemini-key', repr_str)
        self.assertNotIn('test-pinecone-key', repr_str)
        
        # Check that safe information is in the repr
        self.assertIn('test-project-id', repr_str)
        self.assertIn('GEMINI_API_KEY_SET', repr_str)
        self.assertIn('PINECONE_API_KEY_SET', repr_str)
        self.assertIn('Yes', repr_str)  # API keys should be marked as set
    
    def test_config_repr_with_missing_keys(self):
        """Test __repr__ method when API keys are missing."""
        # Test with manually created config for repr testing
        self._set_valid_environment()
        config = Config()
        
        # Manually set one key to None to test the repr
        config.GEMINI_API_KEY = None
        
        repr_str = repr(config)
        self.assertIn("'GEMINI_API_KEY_SET': 'No'", repr_str)
    
    def test_config_with_empty_string_environment_variables(self):
        """Test Config handles empty string environment variables as missing."""
        os.environ['FIREBASE_PROJECT_ID'] = ''
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
        
        with self.assertRaises(ValueError) as context:
            Config()
        
        self.assertIn("Required environment variable 'FIREBASE_PROJECT_ID' is not set", 
                     str(context.exception))


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for the config module."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Store original environment to restore later
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_config_module_import_with_valid_env(self):
        """Test that the config module can be imported with valid environment."""
        # Set up valid environment
        os.environ['FIREBASE_PROJECT_ID'] = 'test-project-id'
        os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
        os.environ['PINECONE_API_KEY'] = 'test-pinecone-key'
        
        # Import the config module directly (not re-importing since already loaded)
        import config
        
        # Check that the config instance was created
        self.assertIsInstance(config.config, Config)
        # Note: we can't check the values since the config was already loaded with different env vars


if __name__ == '__main__':
    """
    Run the test suite when this file is executed directly.
    
    Usage:
        python test_config.py
        
    Or run specific test classes:
        python -m unittest test_config.TestConfig
        python -m unittest test_config.TestGetEnvVar
    """
    # Set up logging for test output
    logging.basicConfig(level=logging.DEBUG)
    
    # Run all tests
    unittest.main(verbosity=2)