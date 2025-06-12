"""
Configuration management module for flexible profile-based AI behavior configuration.

This module provides a comprehensive system for managing AI behavior profiles with:
- Flexible JSON schema support with extensibility
- Multiple profile support with easy switching
- Object-oriented representation with type safety
- Platform integration capabilities
"""

from .profile import Profile
from .profile_manager import ProfileManager
from .config_schema import ConfigSchema, ValidationError
from .settings_manager import SettingsManager

__all__ = [
    'Profile',
    'ProfileManager',
    'ConfigSchema',
    'ValidationError',
    'SettingsManager'
]