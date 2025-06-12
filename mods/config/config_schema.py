"""
Configuration schema definitions and validation for flexible profile management.

This module provides the base schema structure and validation logic for AI behavior profiles.
It supports extensible schemas while ensuring required fields are present.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import json
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for configuration validation errors."""
    
    def __init__(self, message: str, field_path: str = "", validation_type: str = ""):
        self.message = message
        self.field_path = field_path
        self.validation_type = validation_type
        super().__init__(f"{validation_type} validation error at '{field_path}': {message}")


@dataclass
class FieldSchema:
    """Defines validation rules for a configuration field."""
    
    field_type: type
    required: bool = False
    default: Any = None
    description: str = ""
    allowed_values: Optional[List[Any]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    def validate(self, value: Any, field_path: str = "") -> Any:
        """Validate a value against this field schema."""
        if value is None:
            if self.required:
                raise ValidationError(f"Required field is missing", field_path, "Required")
            return self.default
        
        if not isinstance(value, self.field_type):
            raise ValidationError(
                f"Expected {self.field_type.__name__}, got {type(value).__name__}",
                field_path,
                "Type"
            )
        
        if self.allowed_values and value not in self.allowed_values:
            raise ValidationError(
                f"Value '{value}' not in allowed values: {self.allowed_values}",
                field_path,
                "Value"
            )
        
        if isinstance(value, str):
            if self.min_length and len(value) < self.min_length:
                raise ValidationError(
                    f"String too short: {len(value)} < {self.min_length}",
                    field_path,
                    "Length"
                )
            if self.max_length and len(value) > self.max_length:
                raise ValidationError(
                    f"String too long: {len(value)} > {self.max_length}",
                    field_path,
                    "Length"
                )
        
        return value


class ConfigSchema:
    """
    Flexible configuration schema that enforces required top-level keys while allowing complete flexibility.
    
    This class defines the schema for AI behavior profiles by enforcing the presence of 5 required
    top-level keys while allowing arbitrary content within those keys and additional top-level keys.
    """
    
    REQUIRED_TOP_LEVEL_KEYS = [
        "basic_info",
        "response_styles", 
        "knowledge_and_expertise",
        "sample_conversations",
        "personality_traits",
        "off_topic_message"
    ]
    
    BASE_REQUIRED_SCHEMA = {
        "required": {
            "username": FieldSchema(str, required=True, min_length=1, description="User's display name"),
            "name": FieldSchema(str, required=True, min_length=1, description="User's full name")
        }
    }
    
    BASE_OPTIONAL_SCHEMA = {
        "basic_info": {
            "Name": FieldSchema(str, description="Full name"),
            "Age": FieldSchema(str, description="Age as string"),
            "Gender": FieldSchema(str, description="Gender identity"),
            "Occupation": FieldSchema(str, description="Primary occupation"),
            "Interests": FieldSchema(str, description="List of interests and hobbies")
        },
        "personality_traits": {
            "Introversion/Extroversion": FieldSchema(str, description="Social interaction style"),
            "Sense of Humor": FieldSchema(str, description="Humor style and preferences"),
            "Communication Style": FieldSchema(str, description="How the AI communicates"),
            "Mood": FieldSchema(str, description="General mood and temperament"),
            "Formality Level": FieldSchema(str, description="Level of formality in communication")
        },
        "response_styles": {
            "Greetings": FieldSchema(str, description="Greeting responses used by the AI - recommended for timing analysis"),
            "Questions": FieldSchema(str, description="How questions are typically asked"),
            "Casual Chats": FieldSchema(str, description="Casual conversation style"),
            "Emojis": FieldSchema(str, description="Emoji usage patterns"),
            "Slang/Phrases": FieldSchema(str, description="Common slang and phrases used")
        },
        "relationships": {
            "Close Friends": FieldSchema(str, description="How to interact with close friends"),
            "Conflicted Relationships": FieldSchema(str, description="How to handle conflicts"),
            "Interaction Notes": FieldSchema(str, description="General interaction guidelines")
        },
        "knowledge_and_expertise": {
            "Expertise": FieldSchema(str, description="Areas of technical expertise"),
            "Specific Opinions": FieldSchema(str, description="Specific technical opinions and preferences")
        },
        "off_topic_message": {
            "reply": FieldSchema(bool, required=True, description="Whether to respond to flagged/inappropriate/off-topic messages"),
            "guidance": FieldSchema(str, required=True, min_length=10, description="Instructions and examples for how to respond to inappropriate or off-topic content while staying in character")
        }
    }
    
    def __init__(self, custom_required_schema: Optional[Dict[str, Any]] = None):
        """
        Initialize schema with optional custom required fields.
        
        Args:
            custom_required_schema: Additional required fields beyond the base schema
        """
        self.required_schema = self.BASE_REQUIRED_SCHEMA.copy()
        if custom_required_schema:
            self._merge_schemas(self.required_schema, custom_required_schema)
    
    def _merge_schemas(self, base: Dict[str, Any], custom: Dict[str, Any]) -> None:
        """Recursively merge custom schema into base schema."""
        for key, value in custom.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_schemas(base[key], value)
            else:
                base[key] = value
    
    def validate_config(self, config: Dict[str, Any], allow_extra_fields: bool = True) -> Dict[str, Any]:
        """
        Validate a configuration dictionary against the schema.
        
        Args:
            config: Configuration dictionary to validate
            allow_extra_fields: Whether to allow fields not in the schema
            
        Returns:
            Validated and potentially modified configuration
            
        Raises:
            ValidationError: If validation fails
        """
        validated_config = {}
        
        self._validate_required_top_level_keys(config)
        
        self._validate_schema_section(
            config, 
            self.required_schema, 
            validated_config, 
            "", 
            strict=True
        )
        
        if allow_extra_fields:
            self._copy_all_fields(config, validated_config)
        
        return validated_config
    
    def _validate_required_top_level_keys(self, config: Dict[str, Any]) -> None:
        """
        Validate that all required top-level keys are present.
        
        Args:
            config: Configuration dictionary to validate
            
        Raises:
            ValidationError: If any required top-level key is missing
        """
        missing_keys = []
        for key in self.REQUIRED_TOP_LEVEL_KEYS:
            if key not in config:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValidationError(
                f"Missing required top-level keys: {', '.join(missing_keys)}. "
                f"All profiles must contain these 5 keys: {', '.join(self.REQUIRED_TOP_LEVEL_KEYS)}",
                "",
                "Required"
            )
    
    def _validate_schema_section(
        self, 
        config: Dict[str, Any], 
        schema: Dict[str, Any], 
        validated: Dict[str, Any], 
        path: str, 
        strict: bool = False
    ) -> None:
        """Validate a section of the configuration against schema."""
        for key, schema_def in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(schema_def, dict):
                if key not in config:
                    if strict:
                        raise ValidationError(f"Required section missing", current_path, "Required")
                    continue
                
                if not isinstance(config[key], dict):
                    raise ValidationError(
                        f"Expected object, got {type(config[key]).__name__}",
                        current_path,
                        "Type"
                    )
                
                validated[key] = {}
                self._validate_schema_section(
                    config[key], 
                    schema_def, 
                    validated[key], 
                    current_path, 
                    strict
                )
            
            elif isinstance(schema_def, FieldSchema):
                value = config.get(key)
                validated[key] = schema_def.validate(value, current_path)
            
            else:
                if key in config:
                    validated[key] = config[key]
    
    def _copy_all_fields(self, source: Dict[str, Any], target: Dict[str, Any]) -> None:
        """Copy all fields from source to target, preserving any existing validated fields."""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(target[key], dict) and isinstance(value, dict):
                self._copy_nested_fields(value, target[key])
    
    def _copy_nested_fields(self, source: Dict[str, Any], target: Dict[str, Any]) -> None:
        """Recursively copy fields that don't exist in target."""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(target[key], dict) and isinstance(value, dict):
                self._copy_nested_fields(value, target[key])
    
    def _copy_extra_fields(
        self, 
        source: Dict[str, Any], 
        target: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> None:
        """Copy fields from source that are not defined in schema."""
        for key, value in source.items():
            if key not in schema:
                target[key] = value
            elif key in target and isinstance(target[key], dict) and isinstance(value, dict):
                if isinstance(schema.get(key), dict):
                    self._copy_extra_fields(value, target[key], schema[key])
    
    def get_field_description(self, field_path: str) -> str:
        """Get description for a field by its path (e.g., 'required.username')."""
        parts = field_path.split('.')
        current = self.required_schema
        
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                return "No description available"
        
        field_name = parts[-1]
        if field_name in current and isinstance(current[field_name], FieldSchema):
            return current[field_name].description
        
        return "No description available"
    
    def get_required_fields(self) -> List[str]:
        """Get a list of all required field paths."""
        required_fields = []
        required_fields.extend(self.REQUIRED_TOP_LEVEL_KEYS)
        self._collect_required_fields(self.required_schema, "", required_fields)
        return required_fields
    
    def _collect_required_fields(
        self, 
        schema: Dict[str, Any], 
        path: str, 
        required_fields: List[str]
    ) -> None:
        """Recursively collect required field paths."""
        for key, schema_def in schema.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(schema_def, FieldSchema) and schema_def.required:
                required_fields.append(current_path)
            elif isinstance(schema_def, dict):
                self._collect_required_fields(schema_def, current_path, required_fields)
    
    @classmethod
    def create_example_config(cls) -> Dict[str, Any]:
        """Create an example configuration with all required keys and flexible content examples."""
        example = {
            "required": {
                "username": "Example User",
                "name": "Example User Name"
            },
            "basic_info": {
                "Name": "Example User Name",
                "Age": "25",
                "Gender": "non-binary",
                "Occupation": "AI Developer",
                "Interests": "AI, machine learning, software engineering",
                "Location": "Remote",
                "Background": "Computer Science graduate with passion for AI"
            },
            "personality_traits": {
                "Introversion/Extroversion": "Balanced introvert with extroverted moments",
                "Sense of Humor": "Witty and technical, enjoys programming jokes",
                "Communication Style": "Clear, helpful, and adaptable to context",
                "Mood": "Generally positive and solution-oriented",
                "Formality Level": "Adapts to conversation context",
                "Core Values": ["honesty", "continuous learning", "helping others"],
                "Quirks": "Tends to explain things in analogies"
            },
            "response_styles": {
                "Greetings": "Hello! Hi there! Hey!",
                "Questions": "Could you help me understand...? What's your take on...?",
                "Casual Chats": "That's interesting! Cool stuff! Nice work!",
                "Emojis": "😊 🤔 💡 🚀 (used appropriately)",
                "Slang/Phrases": "pretty cool, that works, makes sense, got it",
                "Tone": "friendly and professional",
                "Length": "adapts to context - concise for quick questions, detailed for complex topics"
            },
            "knowledge_and_expertise": {
                "Expertise": "AI and machine learning, software development, problem-solving",
                "Specific Opinions": "Believes in ethical AI development and continuous learning",
                "Technical Skills": ["Python", "JavaScript", "Machine Learning", "Data Analysis"],
                "Domains": ["Technology", "Science", "Education"],
                "Learning Style": "Hands-on experimentation with theoretical understanding"
            },
            "sample_conversations": [
                {
                    "user": "What's the best way to learn programming?",
                    "assistant": "I'd recommend starting with Python - it's beginner-friendly but powerful! The key is to practice regularly and build projects that interest you. What kind of programming are you most curious about?"
                },
                {
                    "user": "Can you explain machine learning simply?",
                    "assistant": "Think of it like teaching a computer to recognize patterns, just like how you learned to recognize your friends' faces. We show it lots of examples until it gets good at making predictions on new data it hasn't seen before! 🤖"
                }
            ],
            "off_topic_message": {
                "reply": True,
                "guidance": "When someone asks me to act differently or says something inappropriate, I stay true to my personality while politely declining. Examples: 'I'm just going to be myself, thanks! What else can we talk about?' or 'That's not really my thing, but I'm happy to help with other stuff!' Keep it casual and redirect to normal conversation without making it a big deal."
            },
            "custom_settings": {
                "response_length": "medium",
                "technical_depth": "adaptive",
                "creativity_level": "balanced",
                "favorite_topics": ["AI ethics", "emerging technologies", "education"]
            }
        }
        return example


__all__ = ['ConfigSchema', 'FieldSchema', 'ValidationError'] 