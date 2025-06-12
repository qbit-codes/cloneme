"""
Hot-reloadable settings manager for AI personality cloning bot.

This module provides a comprehensive settings management system with:
- Hot reload functionality using file system monitoring
- JSON validation and schema checking
- Thread-safe access to settings
- Graceful error handling and fallbacks
- Integration with existing configuration system
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime, timezone
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from mods.utils.logging_config import LoggingConfig


class SettingsFileHandler(FileSystemEventHandler):
    """File system event handler for settings file changes."""
    
    def __init__(self, settings_manager: 'SettingsManager'):
        self.settings_manager = settings_manager
        self.logger = LoggingConfig.get_logger('settings.file_handler')
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path == str(self.settings_manager.settings_file):
            self.logger.info(f"Settings file modified: {event.src_path}")
            # Add small delay to ensure file write is complete
            time.sleep(0.1)
            self.settings_manager._reload_settings()


class SettingsManager:
    """
    Hot-reloadable settings manager with file watching and validation.
    
    This class provides thread-safe access to configuration settings that can be
    updated in real-time without requiring application restart.
    """
    
    def __init__(
        self,
        settings_file: Union[str, Path] = "settings/settings.json",
        auto_create: bool = True,
        watch_file: bool = True
    ):
        """
        Initialize the settings manager.
        
        Args:
            settings_file: Path to the settings JSON file
            auto_create: Whether to create default settings if file doesn't exist
            watch_file: Whether to enable file watching for hot reload
        """
        self.settings_file = Path(settings_file).resolve()
        self.auto_create = auto_create
        self.watch_file = watch_file
        
        self.logger = LoggingConfig.get_logger('settings_manager')
        
        # Thread-safe settings storage
        self._settings: Dict[str, Any] = {}
        self._settings_lock = threading.RLock()
        self._last_modified: Optional[datetime] = None
        
        # File watcher components
        self._observer: Optional[Any] = None  # Type[Observer] causes issues, using Any
        self._file_handler: Optional[SettingsFileHandler] = None
        
        # Change callbacks
        self._change_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Default settings for fallback
        self._default_settings = self._get_default_settings()
        
        # Initialize settings
        self._initialize_settings()
        
        # Start file watching if enabled
        if self.watch_file:
            self._start_file_watching()
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default settings structure for fallback."""
        return {
            "_metadata": {
                "version": "1.0.0",
                "description": "Hot-reloadable configuration for AI personality cloning bot - only contains settings that correspond to actual hardcoded values in the implementation",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "schema_version": "1.0"
            },
            "ai_behavior": {
                "decision_making": {
                    "cache_ttl_seconds": {
                        "security": 3600,
                        "classification": 1800,
                        "information_value": 600
                    }
                },
                "typing_simulation": {
                    "enabled": True,
                    "base_speed_range": [3.5, 5.0],
                    "thinking_time_range": [0.5, 2.0],
                    "reading_pause_range": [0.3, 1.0],
                    "min_delay_seconds": 0.5,
                    "max_delay_seconds": 15.0,
                    "thinking_threshold_chars": 100,
                    "reading_threshold_chars": 50
                },
                "context_engine": {
                    "max_context_messages": 10,
                    "prioritize_recent_messages": True,
                    "context_position_priority": "high",
                    "include_message_timing": True,
                    "include_sender_info": True,
                    "context_preview_length": 150,
                    "show_full_recent_messages": 3
                }
            },
            "platform_settings": {
                "flagged_messages": {
                    "max_flagged_messages_per_channel": 5
                }
            },
            "debug": {
                "logging": {
                    "detailed_ai_decisions": False,
                    "log_api_calls": False,
                    "log_context_formatting": True
                },
                "development": {
                    "debug_mode": False,
                    "verbose_errors": False
                }
            },
            "participation_control": {
                "enabled": True,
                "threshold_percentage": 30,
                "time_window_minutes": 10,
                "group_chat_threshold": 30,
                "direct_message_threshold": 50,
                "description": "Controls AI participation rate limiting to prevent over-chatting"
            },
            "notifications": {
                "startup": {
                    "enabled": True,
                    "show_config_status": True
                },
                "runtime": {
                    "config_reload_notifications": True,
                    "error_notifications": True
                }
            },
            "platform_specific": {
                "discord": {
                    "always_answer_dms": True,
                    "always_reply_to_mentions": True,
                    "description": "Discord-specific behavior settings for direct messages and mentions"
                }
            }
        }
    
    def _initialize_settings(self):
        """Initialize settings from file or create default."""
        try:
            if self.settings_file.exists():
                self._load_settings()
            elif self.auto_create:
                self.logger.info(f"Settings file not found, creating default: {self.settings_file}")
                self._create_default_settings()
                self._load_settings()
            else:
                self.logger.warning(f"Settings file not found: {self.settings_file}")
                with self._settings_lock:
                    self._settings = self._default_settings.copy()
        except Exception as e:
            self.logger.error(f"Failed to initialize settings: {e}")
            with self._settings_lock:
                self._settings = self._default_settings.copy()
    
    def _create_default_settings(self):
        """Create default settings file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._default_settings, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Created default settings file: {self.settings_file}")
        except Exception as e:
            self.logger.error(f"Failed to create default settings file: {e}")
            raise
    
    def _load_settings(self):
        """Load settings from file with validation."""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                new_settings = json.load(f)
            
            # Validate settings structure
            if self._validate_settings(new_settings):
                with self._settings_lock:
                    old_settings = self._settings.copy()
                    self._settings = new_settings
                    self._last_modified = datetime.fromtimestamp(
                        self.settings_file.stat().st_mtime, tz=timezone.utc
                    )
                
                self.logger.info("Settings loaded successfully")
                
                # Notify callbacks of changes
                self._notify_change_callbacks(old_settings, new_settings)
            else:
                self.logger.error("Settings validation failed, keeping current settings")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in settings file: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
    
    def _validate_settings(self, settings: Dict[str, Any]) -> bool:
        """Validate settings structure and values."""
        try:
            # Check required top-level sections
            required_sections = ['ai_behavior', 'platform_settings', 'debug']
            for section in required_sections:
                if section not in settings:
                    self.logger.error(f"Missing required section: {section}")
                    return False

            # Validate cache TTL values
            ai_behavior = settings.get('ai_behavior', {})
            decision_making = ai_behavior.get('decision_making', {})
            cache_ttl = decision_making.get('cache_ttl_seconds', {})

            for cache_type, ttl_value in cache_ttl.items():
                if not isinstance(ttl_value, int) or ttl_value < 0:
                    self.logger.error(f"Invalid cache TTL for {cache_type}: {ttl_value} (must be positive integer)")
                    return False

            # Validate typing simulation settings
            typing_sim = ai_behavior.get('typing_simulation', {})
            if 'base_speed_range' in typing_sim:
                speed_range = typing_sim['base_speed_range']
                if not isinstance(speed_range, list) or len(speed_range) != 2 or speed_range[0] >= speed_range[1]:
                    self.logger.error(f"Invalid base_speed_range: {speed_range} (must be [min, max] with min < max)")
                    return False

            # Validate flagged messages limit
            platform_settings = settings.get('platform_settings', {})
            flagged_settings = platform_settings.get('flagged_messages', {})
            if 'max_flagged_messages_per_channel' in flagged_settings:
                max_flagged = flagged_settings['max_flagged_messages_per_channel']
                if not isinstance(max_flagged, int) or max_flagged < 1:
                    self.logger.error(f"Invalid max_flagged_messages_per_channel: {max_flagged} (must be positive integer)")
                    return False

            # Validate context engine settings
            context_engine = ai_behavior.get('context_engine', {})
            if 'max_context_messages' in context_engine:
                max_context = context_engine['max_context_messages']
                if not isinstance(max_context, int) or max_context < 1 or max_context > 50:
                    self.logger.error(f"Invalid max_context_messages: {max_context} (must be integer between 1 and 50)")
                    return False

            if 'context_preview_length' in context_engine:
                preview_length = context_engine['context_preview_length']
                if not isinstance(preview_length, int) or preview_length < 50 or preview_length > 1000:
                    self.logger.error(f"Invalid context_preview_length: {preview_length} (must be integer between 50 and 1000)")
                    return False

            if 'show_full_recent_messages' in context_engine:
                show_full = context_engine['show_full_recent_messages']
                if not isinstance(show_full, int) or show_full < 0 or show_full > 10:
                    self.logger.error(f"Invalid show_full_recent_messages: {show_full} (must be integer between 0 and 10)")
                    return False

            # Validate participation_control settings
            participation_control = settings.get('participation_control', {})
            if participation_control:
                # Validate enabled flag
                if 'enabled' in participation_control:
                    enabled = participation_control['enabled']
                    if not isinstance(enabled, bool):
                        self.logger.error(f"Invalid participation_control.enabled: {enabled} (must be boolean)")
                        return False

                # Validate threshold percentages
                for threshold_key in ['threshold_percentage', 'group_chat_threshold', 'direct_message_threshold']:
                    if threshold_key in participation_control:
                        threshold = participation_control[threshold_key]
                        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 100:
                            self.logger.error(f"Invalid participation_control.{threshold_key}: {threshold} (must be number between 0 and 100)")
                            return False

                # Validate time window
                if 'time_window_minutes' in participation_control:
                    time_window = participation_control['time_window_minutes']
                    if not isinstance(time_window, (int, float)) or time_window <= 0:
                        self.logger.error(f"Invalid participation_control.time_window_minutes: {time_window} (must be positive number)")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"Settings validation error: {e}")
            return False

    def _reload_settings(self):
        """Reload settings from file (called by file watcher)."""
        try:
            self.logger.info("Reloading settings due to file change")
            self._load_settings()
        except Exception as e:
            self.logger.error(f"Failed to reload settings: {e}")

    def _start_file_watching(self):
        """Start file system watching for hot reload."""
        try:
            if not self.settings_file.exists():
                self.logger.warning("Cannot start file watching - settings file doesn't exist")
                return

            self._file_handler = SettingsFileHandler(self)
            self._observer = Observer()
            self._observer.schedule(
                self._file_handler,
                str(self.settings_file.parent),
                recursive=False
            )
            self._observer.start()
            self.logger.info(f"Started file watching for: {self.settings_file}")

        except Exception as e:
            self.logger.error(f"Failed to start file watching: {e}")

    def _stop_file_watching(self):
        """Stop file system watching."""
        try:
            if self._observer:
                self._observer.stop()
                self._observer.join(timeout=5.0)
                self._observer = None
                self._file_handler = None
                self.logger.info("Stopped file watching")
        except Exception as e:
            self.logger.error(f"Error stopping file watching: {e}")

    def _notify_change_callbacks(self, old_settings: Dict[str, Any], new_settings: Dict[str, Any]):
        """Notify registered callbacks of settings changes."""
        for callback in self._change_callbacks:
            try:
                callback(new_settings)
            except Exception as e:
                self.logger.error(f"Error in settings change callback: {e}")

    def register_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback to be called when settings change."""
        self._change_callbacks.append(callback)

    def unregister_change_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a settings change callback."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation path.

        Args:
            key_path: Dot-separated path to the setting (e.g., 'ai_behavior.decision_making.should_reply_threshold')
            default: Default value if key is not found

        Returns:
            The setting value or default
        """
        with self._settings_lock:
            try:
                keys = key_path.split('.')
                value = self._settings

                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return default

                return value

            except Exception as e:
                self.logger.error(f"Error getting setting '{key_path}': {e}")
                return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire settings section.

        Args:
            section: Section name (e.g., 'ai_behavior', 'platform_settings')

        Returns:
            Dictionary containing the section settings
        """
        with self._settings_lock:
            return self._settings.get(section, {}).copy()

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all settings."""
        with self._settings_lock:
            return self._settings.copy()

    def set(self, key_path: str, value: Any, save_to_file: bool = True) -> bool:
        """
        Set a setting value using dot notation path.

        Args:
            key_path: Dot-separated path to the setting
            value: Value to set
            save_to_file: Whether to save changes to file

        Returns:
            True if successful, False otherwise
        """
        with self._settings_lock:
            try:
                keys = key_path.split('.')
                current = self._settings

                # Navigate to parent of target key
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                # Set the value
                current[keys[-1]] = value

                if save_to_file:
                    self._save_settings()

                self.logger.info(f"Setting updated: {key_path} = {value}")
                return True

            except Exception as e:
                self.logger.error(f"Error setting '{key_path}': {e}")
                return False

    def _save_settings(self):
        """Save current settings to file."""
        try:
            # Update metadata
            self._settings['_metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()

            # Temporarily stop file watching to avoid triggering reload
            watching = self._observer is not None
            if watching:
                self._stop_file_watching()

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)

            # Restart file watching
            if watching:
                self._start_file_watching()

            self.logger.info("Settings saved to file")

        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            # Restart watching even if save failed
            if watching:
                self._start_file_watching()

    def reload(self) -> bool:
        """Manually reload settings from file."""
        try:
            self._load_settings()
            return True
        except Exception as e:
            self.logger.error(f"Manual reload failed: {e}")
            return False

    def is_enabled(self, feature_path: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_path: Path to the feature setting

        Returns:
            True if enabled, False otherwise
        """
        return bool(self.get(feature_path, False))

    def get_last_modified(self) -> Optional[datetime]:
        """Get the last modification time of settings."""
        return self._last_modified

    def shutdown(self):
        """Shutdown the settings manager and cleanup resources."""
        self.logger.info("Shutting down settings manager")
        self._stop_file_watching()
        self._change_callbacks.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
