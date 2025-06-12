"""
Profile class for object-oriented representation of AI behavior configuration.

This module provides the Profile class which represents a complete AI behavior profile
with type-safe access methods and flexible data handling.
"""

from typing import Dict, Any, Optional, List, Union
import json
from datetime import datetime, timezone
from pathlib import Path
import copy

from .config_schema import ConfigSchema, ValidationError


class Profile:
    """
    Object-oriented representation of an AI behavior profile.
    
    This class provides a clean interface for accessing and manipulating profile data
    while maintaining the flexibility of the underlying JSON structure.
    """
    
    def __init__(
        self, 
        profile_name: str,
        config_data: Dict[str, Any],
        schema: Optional[ConfigSchema] = None,
        source_file: Optional[Path] = None
    ):
        """
        Initialize a Profile instance.
        
        Args:
            profile_name: Name/identifier for this profile
            config_data: Raw configuration data dictionary
            schema: Optional schema for validation (uses default if None)
            source_file: Optional path to the source JSON file
        """
        self.profile_name = profile_name
        self.source_file = source_file
        self.schema = schema if schema else ConfigSchema()
        self.created_at = datetime.now(timezone.utc)
        self.modified_at = self.created_at
        
        try:
            self._config_data = self.schema.validate_config(config_data, allow_extra_fields=True)
        except ValidationError as e:
            raise ValidationError(f"Profile '{profile_name}' validation failed: {e.message}", e.field_path, e.validation_type)
        
        self._access_cache = {}
    
    @property
    def config_data(self) -> Dict[str, Any]:
        """Get a deep copy of the configuration data."""
        return copy.deepcopy(self._config_data)
    
    def get_required_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get a required field value by path.
        
        Args:
            field_path: Dot-separated path to the field (e.g., 'required.username')
            default: Default value if field is not found
            
        Returns:
            Field value or default
        """
        return self._get_nested_value(self._config_data, field_path, default)
    
    def get_field(self, field_path: str, default: Any = None) -> Any:
        """
        Get any field value by path, including custom fields.
        
        Args:
            field_path: Dot-separated path to the field
            default: Default value if field is not found
            
        Returns:
            Field value or default
        """
        return self._get_nested_value(self._config_data, field_path, default)
    
    def set_field(self, field_path: str, value: Any) -> None:
        """
        Set a field value by path.
        
        Args:
            field_path: Dot-separated path to the field
            value: Value to set
        """
        self._set_nested_value(self._config_data, field_path, value)
        self.modified_at = datetime.now(timezone.utc)
        self._access_cache.pop(field_path, None)
    
    def has_field(self, field_path: str) -> bool:
        """
        Check if a field exists at the given path.
        
        Args:
            field_path: Dot-separated path to check
            
        Returns:
            True if field exists, False otherwise
        """
        try:
            self._get_nested_value(self._config_data, field_path)
            return True
        except (KeyError, TypeError):
            return False
    
    def remove_field(self, field_path: str) -> bool:
        """
        Remove a field at the given path.
        
        Args:
            field_path: Dot-separated path to the field to remove
            
        Returns:
            True if field was removed, False if it didn't exist
        """
        parts = field_path.split('.')
        if not parts:
            return False
        
        current = self._config_data
        for part in parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        
        final_key = parts[-1]
        if isinstance(current, dict) and final_key in current:
            del current[final_key]
            self.modified_at = datetime.now(timezone.utc)
            self._access_cache.pop(field_path, None)
            return True
        
        return False
    
    @property
    def username(self) -> str:
        """Get the username from required fields."""
        return self.get_required_field('required.username', '')
    
    @property
    def name(self) -> str:
        """Get the full name from required fields."""
        return self.get_required_field('required.name', '')
    
    @property
    def basic_info(self) -> Dict[str, Any]:
        """Get the basic info section."""
        return self.get_field('basic_info', {})
    
    @property
    def personality_traits(self) -> Dict[str, Any]:
        """Get the personality traits section."""
        return self.get_field('personality_traits', {})
    
    @property
    def response_styles(self) -> Dict[str, Any]:
        """Get the response styles section."""
        return self.get_field('response_styles', {})
    
    @property
    def relationships(self) -> Dict[str, Any]:
        """Get the relationships section."""
        return self.get_field('relationships', {})
    
    @property
    def knowledge_and_expertise(self) -> Dict[str, Any]:
        """Get the knowledge and expertise section."""
        return self.get_field('knowledge_and_expertise', {})
    
    @property
    def sample_conversations(self) -> List[Dict[str, Any]]:
        """Get sample conversations."""
        return self.get_field('sample_conversations', [])
    
    @property
    def off_topic_message(self) -> Dict[str, Any]:
        """Get the off-topic message handling configuration."""
        return self.get_field('off_topic_message', {"reply": False, "guidance": ""})
    
    def get_greeting_style(self) -> str:
        """Get greeting style from response_styles."""
        return self.get_field('response_styles.Greetings', 'Hello!')
    
    def get_communication_style(self) -> str:
        """Get communication style from personality traits."""
        return self.get_field('personality_traits.Communication Style', 'Clear and helpful')
    
    def get_humor_style(self) -> str:
        """Get humor style from personality traits."""
        return self.get_field('personality_traits.Sense of Humor', 'Appropriate and context-aware')
    
    def get_formality_level(self) -> str:
        """Get formality level from personality traits."""
        return self.get_field('personality_traits.Formality Level', 'Adaptive')
    
    def get_expertise_areas(self) -> str:
        """Get expertise areas from knowledge section."""
        return self.get_field('knowledge_and_expertise.Expertise', '')
    
    def should_reply_to_off_topic(self) -> bool:
        """Check if this profile should reply to off-topic/flagged messages."""
        return self.get_field('off_topic_message.reply', False)
    
    def get_off_topic_guidance(self) -> str:
        """Get guidance for responding to off-topic/flagged messages."""
        return self.get_field('off_topic_message.guidance', '')
    
    def get_custom_settings(self) -> Dict[str, Any]:
        """Get any custom settings that might be defined."""
        custom_fields = {}  
        base_fields = {'required', 'basic_info', 'personality_traits', 'response_styles', 
                      'relationships', 'knowledge_and_expertise', 'sample_conversations', 'off_topic_message'}
        
        for key, value in self._config_data.items():
            if key not in base_fields:
                custom_fields[key] = value
        
        return custom_fields
    
    def format_for_llm(self, include_metadata: bool = False) -> str:
        """
        Format the complete profile data in a structured, LLM-friendly format.
        
        This method presents all profile information in a clear, readable format
        regardless of the specific key names used, ensuring the LLM has access
        to the complete personality and behavior configuration.
        
        Args:
            include_metadata: Whether to include profile metadata (creation time, etc.)
            
        Returns:
            str: Formatted profile data ready for LLM consumption
        """
        def format_any_data(data: Any, indent: int = 0) -> str:
            """Recursively format any data structure into readable text."""
            prefix = "  " * indent
            
            if isinstance(data, dict):
                if not data:
                    return f"{prefix}(No data)\n"
                
                result = ""
                for key, value in data.items():
                    if isinstance(value, dict):
                        if value:
                            result += f"{prefix}- **{key}:**\n"
                            result += format_any_data(value, indent + 1)
                        else:
                            result += f"{prefix}- **{key}:** (Empty)\n"
                    elif isinstance(value, list):
                        if value:
                            result += f"{prefix}- **{key}:**\n"
                            result += format_any_data(value, indent + 1)
                        else:
                            result += f"{prefix}- **{key}:** (Empty list)\n"
                    else:
                        if isinstance(value, str) and '\n' in value:
                            lines = [line.strip() for line in value.split('\n') if line.strip()]
                            if len(lines) > 1:
                                result += f"{prefix}- **{key}:**\n"
                                for line in lines:
                                    result += f"{prefix}  {line}\n"
                            else:
                                result += f"{prefix}- **{key}:** {lines[0] if lines else value}\n"
                        else:
                            result += f"{prefix}- **{key}:** {value}\n"
                return result
                
            elif isinstance(data, list):
                if not data:
                    return f"{prefix}(No items)\n"
                
                result = ""
                for i, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        result += f"{prefix}{i}. **Item {i}:**\n"
                        result += format_any_data(item, indent + 1)
                    else:
                        result += f"{prefix}{i}. {item}\n"
                return result
                
            else:
                if isinstance(data, str) and '\n' in data:
                    lines = [line.strip() for line in data.split('\n') if line.strip()]
                    result = ""
                    for line in lines:
                        result += f"{prefix}{line}\n"
                    return result
                else:
                    return f"{prefix}{data}\n"
        
        sections = []
        
        header = f"""# AI PERSONALITY PROFILE: {self.profile_name}

## CORE IDENTITY
- **Profile Name:** {self.profile_name}
- **Username:** {self.username}
- **Full Name:** {self.name}
"""
        
        if include_metadata:
            header += f"""- **Created:** {self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Last Modified:** {self.modified_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Source File:** {self.source_file if self.source_file else 'Not specified'}

"""
        else:
            header += "\n"
        
        sections.append(header)
        
        preferred_order = [
            ('basic_info', 'BASIC INFORMATION'),
            ('personality_traits', 'PERSONALITY TRAITS'),
            ('response_styles', 'COMMUNICATION & RESPONSE STYLES'),
            ('knowledge_and_expertise', 'KNOWLEDGE & EXPERTISE'),
            ('sample_conversations', 'SAMPLE CONVERSATIONS'),
            ('relationships', 'RELATIONSHIP DYNAMICS'),
        ]
        
        processed_keys = {'required'}
        
        for key, display_title in preferred_order:
            if self.has_field(key):
                data = self.get_field(key)
                section_content = f"## {display_title}\n"
                section_content += format_any_data(data, 0)
                sections.append(section_content)
                processed_keys.add(key)
        
        remaining_sections = []
        for key, value in self._config_data.items():
            if key not in processed_keys:
                display_title = key.replace('_', ' ').replace('-', ' ').title()
                section_content = f"## {display_title}\n"
                section_content += format_any_data(value, 0)
                remaining_sections.append(section_content)
        
        if remaining_sections:
            sections.append("## ADDITIONAL CONFIGURATION\n")
            sections.extend(remaining_sections)
        
        summary_parts = []
        
        if self.has_field('personality_traits.Communication Style'):
            summary_parts.append(f"**Communication Style:** {self.get_communication_style()}")
        if self.has_field('personality_traits.Formality Level'):
            summary_parts.append(f"**Formality Level:** {self.get_formality_level()}")
        if self.has_field('personality_traits.Sense of Humor'):
            summary_parts.append(f"**Humor Style:** {self.get_humor_style()}")
        
        expertise = self.get_expertise_areas()
        if expertise:
            summary_parts.append(f"**Primary Expertise:** {expertise[:100]}{'...' if len(expertise) > 100 else ''}")
        
        behavioral_notes = []
        greeting = self.get_greeting_style()
        if greeting:
            first_greeting = greeting.split('\n')[0] if '\n' in greeting else greeting
            behavioral_notes.append(f"Greeting Style: {first_greeting[:50]}{'...' if len(first_greeting) > 50 else ''}")
        
        interaction_notes = self.get_field('relationships.Interaction Notes', '')
        if interaction_notes:
            behavioral_notes.append(f"Interaction Approach: {str(interaction_notes)[:100]}{'...' if len(str(interaction_notes)) > 100 else ''}")
        
        if summary_parts or behavioral_notes:
            summary = "## BEHAVIORAL SUMMARY\n\n"
            if summary_parts:
                summary += "\n".join(summary_parts) + "\n\n"
            if behavioral_notes:
                summary += "**Key Behavioral Notes:**\n"
                for note in behavioral_notes:
                    summary += f"- {note}\n"
                summary += "\n"
            summary += "---\n*This profile provides comprehensive behavioral guidance for AI personality simulation and response generation.*\n"
            sections.append(summary)
        
        return "\n".join(sections)
    
    def get_llm_context_summary(self) -> str:
        """
        Get a concise summary of the profile for LLM context windows.
        
        Returns:
            str: Condensed profile information suitable for context-limited scenarios
        """
        summary_parts = [
            f"**AI Profile:** {self.profile_name} (@{self.username})",
            f"**Style:** {self.get_communication_style()}",
            f"**Formality:** {self.get_formality_level()}",
            f"**Humor:** {self.get_humor_style()}",
        ]
        
        expertise = self.get_expertise_areas()
        if expertise:
            summary_parts.append(f"**Expertise:** {expertise[:80]}{'...' if len(expertise) > 80 else ''}")
        
        personality = self.get_field('personality_traits')
        if isinstance(personality, dict):
            key_traits = []
            for key, value in list(personality.items())[:3]:  # First 3 traits
                if isinstance(value, str):
                    key_traits.append(f"{key}: {value[:40]}{'...' if len(value) > 40 else ''}")
            if key_traits:
                summary_parts.append(f"**Key Traits:** {'; '.join(key_traits)}")
        
        greetings = self.get_greeting_style()
        if greetings:
            sample_greeting = greetings.split('\n')[0] if '\n' in greetings else greetings
            summary_parts.append(f"**Sample Greeting:** {sample_greeting[:30]}{'...' if len(sample_greeting) > 30 else ''}")
        
        return " | ".join(summary_parts)
    
    def merge_profile(self, other_profile: 'Profile', prefer_other: bool = True) -> 'Profile':
        """
        Merge this profile with another profile.
        
        Args:
            other_profile: Profile to merge with
            prefer_other: If True, other_profile values take precedence on conflicts
            
        Returns:
            New Profile instance with merged data
        """
        merged_data = copy.deepcopy(self._config_data)
        other_data = other_profile.config_data
        
        if prefer_other:
            merged_data = self._deep_merge(merged_data, other_data)
        else:
            merged_data = self._deep_merge(other_data, merged_data)
        
        return Profile(
            profile_name=f"{self.profile_name}_merged_{other_profile.profile_name}",
            config_data=merged_data,
            schema=self.schema
        )
    
    def create_variant(self, variant_name: str, modifications: Dict[str, Any]) -> 'Profile':
        """
        Create a variant of this profile with specific modifications.
        
        Args:
            variant_name: Name for the new variant
            modifications: Dictionary of field paths and new values
            
        Returns:
            New Profile instance with modifications applied
        """
        variant_data = copy.deepcopy(self._config_data)
        
        for field_path, value in modifications.items():
            self._set_nested_value(variant_data, field_path, value)
        
        return Profile(
            profile_name=variant_name,
            config_data=variant_data,
            schema=self.schema
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to a dictionary representation.
        
        Returns:
            Dictionary containing profile metadata and configuration
        """
        return {
            'profile_name': self.profile_name,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'source_file': str(self.source_file) if self.source_file else None,
            'config_data': self.config_data
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert profile to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def validate(self) -> List[str]:
        """
        Validate the current profile configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        try:
            self.schema.validate_config(self._config_data, allow_extra_fields=True)
        except ValidationError as e:
            errors.append(str(e))
        
        return errors
    
    def _get_nested_value(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get a nested value from dictionary using dot notation."""
        if path in self._access_cache:
            return self._access_cache[path]
        
        parts = path.split('.')
        current = data
        
        try:
            for part in parts:
                current = current[part]
            
            self._access_cache[path] = current
            return current
        except (KeyError, TypeError):
            return default
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set a nested value in dictionary using dot notation."""
        parts = path.split('.')
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with overlay taking precedence."""
        result = copy.deepcopy(base)
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def __str__(self) -> str:
        """String representation of the profile."""
        return f"Profile(name='{self.profile_name}', username='{self.username}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the profile."""
        return (f"Profile(name='{self.profile_name}', username='{self.username}', "
                f"created_at='{self.created_at}', modified_at='{self.modified_at}')")
    
    def __eq__(self, other: Any) -> bool:
        """Check equality based on profile name and configuration data."""
        if not isinstance(other, Profile):
            return False
        return (self.profile_name == other.profile_name and 
                self._config_data == other._config_data)
    
    def __hash__(self) -> int:
        """Hash based on profile name."""
        return hash(self.profile_name)


__all__ = ['Profile'] 