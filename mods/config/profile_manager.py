"""
Profile management system for loading, saving, and managing AI behavior profiles.

This module provides the ProfileManager class which handles all profile operations
including file I/O, profile discovery, and profile switching functionality.
"""

from typing import Dict, List, Optional, Union, Any
import json
import glob
from pathlib import Path
import shutil
from datetime import datetime, timezone
import logging

from .profile import Profile
from .config_schema import ConfigSchema, ValidationError


class ProfileManager:
    """
    Comprehensive profile management system.
    
    This class handles all aspects of profile management including:
    - Loading profiles from JSON files
    - Saving profiles to JSON files
    - Profile discovery and listing
    - Profile validation and conversion
    - Profile backup and restoration
    """
    
    def __init__(
        self, 
        profiles_directory: Union[str, Path] = ".",
        schema: Optional[ConfigSchema] = None,
        auto_backup: bool = True
    ):
        """
        Initialize the ProfileManager.
        
        Args:
            profiles_directory: Directory to search for profile files
            schema: Optional schema for validation (uses default if None)
            auto_backup: Whether to create backups when saving profiles
        """
        self.profiles_directory = Path(profiles_directory).resolve()
        self.schema = schema if schema else ConfigSchema()
        self.auto_backup = auto_backup
        self.logger = logging.getLogger("config.profile_manager")
        
        self._profile_cache: Dict[str, Profile] = {}
        self._file_cache: Dict[Path, datetime] = {}
        
        self.profiles_directory.mkdir(parents=True, exist_ok=True)
    
    def discover_profiles(self) -> List[Path]:
        """
        Discover all profile files in the profiles directory.
        
        Returns:
            List of Path objects pointing to profile JSON files
        """
        profile_files = []
        
        # Directories to exclude from profile discovery
        excluded_dirs = {'memories', '__pycache__', '.git', 'node_modules', 'settings'}
        
        # File patterns that should NOT be considered profiles
        excluded_patterns = {
            'discord_*.json',  # Memory files
            'telegram_*.json', # Memory files
            'backup_*.json',   # Backup files
            '*.backup.json',   # Backup files
            'temp_*.json',     # Temporary files
            'settings*.json',  # Settings configuration files
        }
        
        def should_exclude_file(file_path: Path) -> bool:
            """Check if a file should be excluded from profile discovery."""
            # Check if file is in excluded directory
            if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                return True
            
            # Check against excluded patterns
            for pattern in excluded_patterns:
                if file_path.match(pattern):
                    return True
                    
            return False
        
        # Search in main directory
        for pattern in ["*.json", "*Config.json", "*config.json", "*profile.json"]:
            for file_path in self.profiles_directory.glob(pattern):
                if file_path.is_file() and not should_exclude_file(file_path):
                    profile_files.append(file_path)
        
        # Search in subdirectories (but not excluded ones)
        for subdir in self.profiles_directory.iterdir():
            if subdir.is_dir() and subdir.name not in excluded_dirs:
                for pattern in ["*.json", "*Config.json", "*config.json", "*profile.json"]:
                    for file_path in subdir.glob(pattern):
                        if file_path.is_file() and not should_exclude_file(file_path):
                            profile_files.append(file_path)
        
        return sorted(set(profile_files))
    
    def load_profile(self, file_path: Union[str, Path], profile_name: Optional[str] = None) -> Profile:
        """
        Load a profile from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            profile_name: Optional name for the profile (uses filename if None)
            
        Returns:
            Profile instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValidationError: If the profile data is invalid
            json.JSONDecodeError: If the JSON is malformed
        """
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            raise FileNotFoundError(f"Profile file not found: {file_path}")
        
        cache_key = str(file_path)
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc)
        
        if (cache_key in self._profile_cache and 
            file_path in self._file_cache and 
            self._file_cache[file_path] >= file_mtime):
            self.logger.debug(f"Loading profile from cache: {cache_key}")
            return self._profile_cache[cache_key]
        
        self.logger.info(f"Loading profile from file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            config_data = self._extract_config_data(raw_data)
            
            if profile_name is None:
                profile_name = file_path.stem
            
            profile = Profile(
                profile_name=profile_name,
                config_data=config_data,
                schema=self.schema,
                source_file=file_path
            )
            
            self._profile_cache[cache_key] = profile
            self._file_cache[file_path] = file_mtime
            
            return profile
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in profile file {file_path}: {e.msg}", e.doc, e.pos)
        except ValidationError as e:
            raise ValidationError(f"Profile validation failed for {file_path}: {e.message}", e.field_path, e.validation_type)
        except Exception as e:
            raise Exception(f"Error loading profile from {file_path}: {str(e)}")
    
    def save_profile(self, profile: Profile, file_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save a profile to a JSON file.
        
        Args:
            profile: Profile instance to save
            file_path: Optional path to save to (uses profile.source_file if None)
            
        Returns:
            Path where the profile was saved
            
        Raises:
            ValueError: If no file path is available
        """
        if file_path is None:
            file_path = profile.source_file
        
        if file_path is None:
            safe_name = "".join(c for c in profile.profile_name if c.isalnum() or c in ('-', '_'))
            file_path = self.profiles_directory / f"{safe_name}_profile.json"
        
        file_path = Path(file_path).resolve()
        
        if self.auto_backup and file_path.exists():
            self._create_backup(file_path)
        
        self.logger.info(f"Saving profile '{profile.profile_name}' to {file_path}")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        save_data = {
            "profiles": {
                profile.profile_name: profile.config_data
            }
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            
            profile.source_file = file_path
            
            cache_key = str(file_path)
            self._profile_cache[cache_key] = profile
            self._file_cache[file_path] = datetime.now(timezone.utc)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Error saving profile to {file_path}: {str(e)}")
    
    def load_all_profiles(self) -> Dict[str, Profile]:
        """
        Load all discoverable profiles.
        
        Returns:
            Dictionary mapping profile names to Profile instances
        """
        profiles = {}
        profile_files = self.discover_profiles()
        
        for file_path in profile_files:
            try:
                profile = self.load_profile(file_path)
                profiles[profile.profile_name] = profile
                self.logger.debug(f"Loaded profile: {profile.profile_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load profile from {file_path}: {e}")
        
        return profiles
    
    def get_profile(self, profile_name: str) -> Optional[Profile]:
        """
        Get a specific profile by name.
        
        Args:
            profile_name: Name of the profile to retrieve
            
        Returns:
            Profile instance if found, None otherwise
        """
        all_profiles = self.load_all_profiles()
        return all_profiles.get(profile_name)
    
    def list_profiles(self) -> List[str]:
        """
        Get a list of all available profile names.
        
        Returns:
            List of profile names
        """
        return list(self.load_all_profiles().keys())
    
    def delete_profile(self, profile_name: str, create_backup: bool = True) -> bool:
        """
        Delete a profile and its associated file.
        
        Args:
            profile_name: Name of the profile to delete
            create_backup: Whether to create a backup before deletion
            
        Returns:
            True if deletion was successful, False otherwise
        """
        profile = self.get_profile(profile_name)
        if not profile or not profile.source_file:
            return False
        
        try:
            if create_backup:
                self._create_backup(profile.source_file)
            
            profile.source_file.unlink()
            
            cache_key = str(profile.source_file)
            self._profile_cache.pop(cache_key, None)
            self._file_cache.pop(profile.source_file, None)
            
            self.logger.info(f"Deleted profile: {profile_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting profile {profile_name}: {e}")
            return False
    
    def create_profile(
        self, 
        profile_name: str, 
        config_data: Dict[str, Any], 
        file_path: Optional[Union[str, Path]] = None
    ) -> Profile:
        """
        Create a new profile with the given configuration.
        
        Args:
            profile_name: Name for the new profile
            config_data: Configuration data for the profile
            file_path: Optional path to save the profile (auto-generated if None)
            
        Returns:
            New Profile instance
        """
        profile = Profile(
            profile_name=profile_name,
            config_data=config_data,
            schema=self.schema
        )
        
        saved_path = self.save_profile(profile, file_path)
        self.logger.info(f"Created new profile '{profile_name}' at {saved_path}")
        
        return profile
    
    def duplicate_profile(self, source_profile_name: str, new_profile_name: str) -> Optional[Profile]:
        """
        Create a duplicate of an existing profile with a new name.
        
        Args:
            source_profile_name: Name of the profile to duplicate
            new_profile_name: Name for the new profile
            
        Returns:
            New Profile instance if successful, None otherwise
        """
        source_profile = self.get_profile(source_profile_name)
        if not source_profile:
            return None
        
        return self.create_profile(
            profile_name=new_profile_name,
            config_data=source_profile.config_data
        )
    
    def validate_all_profiles(self) -> Dict[str, List[str]]:
        """
        Validate all discovered profiles.
        
        Returns:
            Dictionary mapping profile names to lists of validation errors
        """
        validation_results = {}
        all_profiles = self.load_all_profiles()
        
        for profile_name, profile in all_profiles.items():
            errors = profile.validate()
            validation_results[profile_name] = errors
        
        return validation_results
    
    def _extract_config_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract configuration data from various JSON structures.
        
        Handles different formats:
        - Direct config: {"required": {...}, "basic_info": {...}}
        - Nested profiles: {"profiles": {"default": {"required": {...}}}}
        - Single profile wrapper: {"profile_name": "...", "config_data": {...}}
        """
        if "profiles" in raw_data and isinstance(raw_data["profiles"], dict):
            profiles = raw_data["profiles"]
            
            if len(profiles) == 1:
                return list(profiles.values())[0]
            
            if "default" in profiles:
                return profiles["default"]
            
            return list(profiles.values())[0]
        
        if "config_data" in raw_data:
            return raw_data["config_data"]
        
        return raw_data
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup_{timestamp}{file_path.suffix}")
        shutil.copy2(file_path, backup_path)
        self.logger.debug(f"Created backup: {backup_path}")
        return backup_path
    
    def clear_cache(self) -> None:
        """Clear the profile cache."""
        self._profile_cache.clear()
        self._file_cache.clear()
        self.logger.debug("Profile cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            "cached_profiles": len(self._profile_cache),
            "cached_files": len(self._file_cache),
            "profiles_directory": str(self.profiles_directory),
            "auto_backup": self.auto_backup
        }


__all__ = ['ProfileManager'] 