"""
Message utility functions for the CloneMe project.

This module provides helper functions for working with Message and Person objects,
including AI message identification and message formatting utilities.
"""

from typing import TYPE_CHECKING, Optional, List
from ..utils.logging_config import LoggingConfig

if TYPE_CHECKING:
    from ..objects.messages.Message import Message
    from ..objects.person.Person import Person

logger = LoggingConfig.get_logger("message_utils")

def is_ai_message(message: "Message") -> bool:
    """
    Determine if a message was sent by the AI assistant.
    
    This function checks if the message sender is the AI by looking for 'ai_assistant'
    in the sender's identifiers list, which is more reliable than checking person_id
    since person_id contains the actual platform user ID.
    
    Args:
        message (Message): The message to check
        
    Returns:
        bool: True if the message was sent by the AI, False otherwise
    """
    if not message or not message.sender:
        return False
    
    # Check if 'ai_assistant' is in the sender's identifiers
    sender_identifiers = message.sender.get_identifiers()
    return 'ai_assistant' in sender_identifiers

def is_ai_person(person: "Person") -> bool:
    """
    Determine if a Person object represents the AI assistant.
    
    Args:
        person (Person): The person to check
        
    Returns:
        bool: True if the person is the AI, False otherwise
    """
    if not person:
        return False
    
    # Check if 'ai_assistant' is in the person's identifiers
    identifiers = person.get_identifiers()
    return 'ai_assistant' in identifiers

def get_sender_display_name(message: "Message", include_ai_indicator: bool = True) -> str:
    """
    Get a display-friendly name for the message sender.
    
    Args:
        message (Message): The message to get sender name for
        include_ai_indicator (bool): Whether to show "**YOU** (AI)" for AI messages
        
    Returns:
        str: Display name for the sender
    """
    if not message or not message.sender:
        return "Unknown"
    
    if is_ai_message(message):
        return "**YOU** (AI)" if include_ai_indicator else "AI"
    
    # For human users, try to get a friendly display name
    sender = message.sender
    identifiers = sender.get_identifiers()
    
    # Use the first non-ID identifier if available (usually username)
    for identifier in identifiers:
        # Skip if it looks like a numeric ID
        if not identifier.isdigit():
            return identifier
    
    # Fallback to person_id if no good identifier found
    return sender.person_id

def format_message_content_with_truncation(
    content: str, 
    max_length: Optional[int] = None,
    show_boundaries: bool = True
) -> str:
    """
    Format message content with proper truncation indicators.
    
    Args:
        content (str): The original message content
        max_length (Optional[int]): Maximum length before truncation
        show_boundaries (bool): Whether to show [MESSAGE START]/[MESSAGE END] boundaries
        
    Returns:
        str: Formatted content with truncation indicators
    """
    if not content:
        return ""
    
    # Clean up the content
    content = content.strip()
    
    if max_length is None or len(content) <= max_length:
        # No truncation needed
        if show_boundaries:
            return f"[MESSAGE START] {content} [MESSAGE END]"
        return content
    
    # Truncation needed
    truncated = content[:max_length].rstrip()
    
    if show_boundaries:
        return f"[MESSAGE START] {truncated}... [TRUNCATED - {len(content) - len(truncated)} chars cut] [MESSAGE END]"
    else:
        return f"{truncated}... [TRUNCATED - {len(content) - len(truncated)} chars cut]"

def format_message_for_context(
    message: "Message",
    max_content_length: Optional[int] = None,
    include_timestamp: bool = True,
    include_sender_info: bool = True,
    show_message_boundaries: bool = True
) -> str:
    """
    Format a message for display in conversation context.
    
    Args:
        message (Message): The message to format
        max_content_length (Optional[int]): Maximum content length before truncation
        include_timestamp (bool): Whether to include timestamp
        include_sender_info (bool): Whether to include sender information
        show_message_boundaries (bool): Whether to show message boundaries
        
    Returns:
        str: Formatted message string
    """
    if not message:
        return "[INVALID MESSAGE]"
    
    # Get sender display name
    sender_name = get_sender_display_name(message, include_ai_indicator=True) if include_sender_info else ""
    
    # Format timestamp
    timestamp = ""
    if include_timestamp and message.created_at:
        timestamp = f"[{message.created_at.strftime('%H:%M:%S')}] "
    
    # Format content with truncation
    formatted_content = format_message_content_with_truncation(
        message.content,
        max_content_length,
        show_message_boundaries
    )
    
    # Combine all parts
    if include_sender_info:
        return f"{timestamp}{sender_name}: {formatted_content}"
    else:
        return f"{timestamp}{formatted_content}"

def analyze_message_context(messages: List["Message"]) -> dict:
    """
    Analyze a list of messages to provide context information.
    
    Args:
        messages (List[Message]): List of messages to analyze
        
    Returns:
        dict: Analysis results including AI/user message counts, timing info, etc.
    """
    if not messages:
        return {
            "total_messages": 0,
            "ai_messages": 0,
            "user_messages": 0,
            "last_sender_was_ai": False,
            "conversation_active": False
        }
    
    ai_count = 0
    user_count = 0
    
    for msg in messages:
        if is_ai_message(msg):
            ai_count += 1
        else:
            user_count += 1
    
    last_message = messages[-1] if messages else None
    last_sender_was_ai = is_ai_message(last_message) if last_message else False
    
    # Check if conversation is active (last message within 5 minutes)
    conversation_active = False
    if last_message and last_message.created_at:
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        time_since_last = now - last_message.created_at
        conversation_active = time_since_last < timedelta(minutes=5)
    
    return {
        "total_messages": len(messages),
        "ai_messages": ai_count,
        "user_messages": user_count,
        "last_sender_was_ai": last_sender_was_ai,
        "conversation_active": conversation_active,
        "ai_participation_ratio": ai_count / len(messages) if messages else 0.0
    }

__all__ = [
    "is_ai_message",
    "is_ai_person", 
    "get_sender_display_name",
    "format_message_content_with_truncation",
    "format_message_for_context",
    "analyze_message_context"
]
