"""
Configuration package for the Personal AI Career Co-Pilot.

This package provides configuration management and validation
for the application.
"""

from .config import Config, get_env_var, config

__all__ = ['Config', 'get_env_var', 'config']