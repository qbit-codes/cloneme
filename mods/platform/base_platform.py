"""
Abstract Base Platform for Multi-Platform Support

This module defines the abstract base class that all platform implementations must inherit from.
It provides a standardized interface for platform-specific operations while keeping the core
AI logic platform-agnostic.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from langchain_core.language_models.chat_models import BaseChatModel

from mods.objects.chats.Chat import Chat
from mods.objects.messages.Message import Message
from mods.objects.person.Person import Person
from mods.utils.logging_config import LoggingConfig

if TYPE_CHECKING:
    from mods.config import Profile, SettingsManager
    from mods.agent.tools.tool import ToolCall


class ActiveChat:
    """
    Platform-agnostic representation of an active chat where the user has recently sent a message.
    This class is shared across all platforms.
    """

    def __init__(self, active_chat_id: str, chat_object: Optional[Chat] = None):
        """
        Initialize an ActiveChat instance.

        Args:
            active_chat_id (str): The ID of the active chat.
            chat_object (Optional[Chat]): The Chat object associated with the active chat.
        """
        self.active_chat_id = str(active_chat_id)
        self.last_message_time = datetime.now(timezone.utc)
        self.chat_object = chat_object

    def isActive(self) -> bool:
        """
        Check if the chat is active (last message was within 1 minute).

        Returns:
            bool: True if the chat is active, False otherwise.
        """
        return datetime.now(timezone.utc) - self.last_message_time < timedelta(minutes=1)

    def update_last_message_time(self):
        """Update the last message time to now."""
        self.last_message_time = datetime.now(timezone.utc)


class BasePlatform(ABC):
    """
    Abstract base class for all social media platform implementations.
    
    This class defines the interface that all platforms must implement to work with
    the unified AI system. Platform-specific implementations should inherit from this
    class and implement all abstract methods.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        profile: Optional["Profile"] = None,
        settings_manager: Optional["SettingsManager"] = None,
        **kwargs
    ):
        """
        Initialize the base platform.

        Args:
            llm (BaseChatModel): The language model for AI decision making and response generation.
            profile (Optional[Profile]): The profile to use for the bot.
            settings_manager (Optional[SettingsManager]): The settings manager for hot-reloadable configuration.
            **kwargs: Additional platform-specific arguments.
        """
        self.profile = profile
        self.settings_manager = settings_manager
        self.active_chats: List[ActiveChat] = []
        self.chats: Dict[str, Chat] = {}
        self.persons: Dict[str, Person] = {}
        self._running = False
        self.logger = LoggingConfig.get_logger(f"{self.__class__.__name__.lower()}")

        # Flagged messages tracking (shared across platforms)
        self.flagged_messages: List[Dict[str, Any]] = []
        self.max_flagged_messages_per_channel = self._get_max_flagged_messages_setting()

        # Register for settings changes if settings manager is available
        if self.settings_manager:
            self.settings_manager.register_change_callback(self._on_settings_changed)

    def _get_max_flagged_messages_setting(self) -> int:
        """Get max flagged messages per channel from settings or use default."""
        if self.settings_manager:
            return self.settings_manager.get('platform_settings.flagged_messages.max_flagged_messages_per_channel', 5)
        else:
            return 5  # Default value

    def _on_settings_changed(self, new_settings: Dict[str, Any]):
        """Handle settings changes by updating flagged messages limit."""
        try:
            old_limit = self.max_flagged_messages_per_channel
            self.max_flagged_messages_per_channel = self._get_max_flagged_messages_setting()

            # Log if the limit changed
            if old_limit != self.max_flagged_messages_per_channel:
                self.logger.info(f"Max flagged messages per channel updated: {old_limit} -> {self.max_flagged_messages_per_channel}")

        except Exception as e:
            self.logger.error(f"Error updating flagged messages limit: {e}")

    # Abstract methods that each platform must implement

    @abstractmethod
    async def send_message(self, chat_id: str, content: str) -> bool:
        """
        Send a message to a specific chat.

        Args:
            chat_id (str): The platform-specific chat/channel ID.
            content (str): The message content to send.

        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def start_typing(self, chat_id: str) -> None:
        """
        Start typing indicator in a specific chat.

        Args:
            chat_id (str): The platform-specific chat/channel ID.
        """
        pass

    @abstractmethod
    async def stop_typing(self, chat_id: str) -> None:
        """
        Stop typing indicator in a specific chat.

        Args:
            chat_id (str): The platform-specific chat/channel ID.
        """
        pass

    @abstractmethod
    async def collect_context(self, message_ref: Any, max_context: int = 10) -> List[Message]:
        """
        Collect recent messages from the chat as context.

        Args:
            message_ref: Platform-specific message reference to collect context for.
            max_context (int): Maximum number of messages to collect.

        Returns:
            List[Message]: List of Message objects representing the context.
        """
        pass

    @abstractmethod
    def convert_platform_message(self, platform_msg: Any, chat: Chat, sender: Person) -> Message:
        """
        Convert a platform-specific message to a generic Message object.

        Args:
            platform_msg: The platform-specific message object.
            chat (Chat): The Chat object this message belongs to.
            sender (Person): The Person who sent the message.

        Returns:
            Message: The converted Message object.
        """
        pass

    @abstractmethod
    def convert_platform_user(self, platform_user: Any) -> Person:
        """
        Convert a platform-specific user to a generic Person object.

        Args:
            platform_user: The platform-specific user object.

        Returns:
            Person: The converted Person object.
        """
        pass

    @abstractmethod
    def convert_platform_chat(self, platform_chat: Any) -> Chat:
        """
        Convert a platform-specific chat/channel to a generic Chat object.

        Args:
            platform_chat: The platform-specific chat/channel object.

        Returns:
            Chat: The converted Chat object.
        """
        pass

    @abstractmethod
    async def start_platform(self) -> None:
        """
        Start the platform client and begin listening for events.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if the platform client is currently running and connected.

        Returns:
            bool: True if running and connected, False otherwise.
        """
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the name of this platform.

        Returns:
            str: The platform name (e.g., "discord", "telegram", "twitter").
        """
        pass

    # Shared methods that all platforms can use

    def add_flagged_message(self, message_id: str, chat_id: str, flagged_line: str):
        """
        Add a message to the flagged messages tracking list.

        Args:
            message_id (str): The platform-specific message ID that was flagged.
            chat_id (str): The platform-specific chat ID where the message was sent.
            flagged_line (str): The specific content that was flagged.
        """
        flagged_entry = {
            "message_id": message_id,
            "chat_id": chat_id,
            "flagged_line": flagged_line,
            "timestamp": datetime.now(timezone.utc),
        }

        self.flagged_messages.append(flagged_entry)
        self._cleanup_flagged_messages()
        self.logger.info(f"🚩 Added flagged message {message_id} to tracking list: '{flagged_line}'")

    def is_message_flagged(self, message_id: str) -> bool:
        """
        Check if a message ID is in the flagged messages list.

        Args:
            message_id (str): The platform-specific message ID to check.

        Returns:
            bool: True if the message is flagged, False otherwise.
        """
        return any(flagged["message_id"] == message_id for flagged in self.flagged_messages)

    def get_flagged_messages_for_chat(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all flagged messages for a specific chat.

        Args:
            chat_id (str): The platform-specific chat ID.

        Returns:
            List[Dict[str, Any]]: List of flagged message entries for the chat.
        """
        return [flagged for flagged in self.flagged_messages if flagged["chat_id"] == chat_id]

    def _cleanup_flagged_messages(self):
        """
        Clean up the flagged messages list to prevent it from growing too large.
        Keeps only the most recent messages per chat and removes old entries.
        """
        by_chat = {}
        for flagged in self.flagged_messages:
            chat_id = flagged["chat_id"]
            if chat_id not in by_chat:
                by_chat[chat_id] = []
            by_chat[chat_id].append(flagged)

        cleaned_flagged = []
        for chat_id, chat_flagged in by_chat.items():
            sorted_flagged = sorted(chat_flagged, key=lambda x: x["timestamp"], reverse=True)
            cleaned_flagged.extend(sorted_flagged[: self.max_flagged_messages_per_channel])

        old_count = len(self.flagged_messages)
        self.flagged_messages = cleaned_flagged

        if old_count > len(self.flagged_messages):
            self.logger.debug(f"🧹 Cleaned up flagged messages: {old_count} -> {len(self.flagged_messages)}")

    def remove_flagged_messages_not_in_context(self, chat_id: str, context_message_ids: List[str]):
        """
        Remove flagged messages that are no longer appearing in the context.

        Args:
            chat_id (str): The platform-specific chat ID.
            context_message_ids (List[str]): List of message IDs currently in context.
        """
        before_count = len(self.flagged_messages)

        self.flagged_messages = [
            flagged
            for flagged in self.flagged_messages
            if flagged["chat_id"] != chat_id or flagged["message_id"] in context_message_ids
        ]

        after_count = len(self.flagged_messages)
        if before_count > after_count:
            self.logger.debug(
                f"🗑️ Removed {before_count - after_count} flagged messages no longer in context for chat {chat_id}"
            )

    def cleanup_inactive_chats(self):
        """Remove inactive chats from the active chats list."""
        self.active_chats = [chat for chat in self.active_chats if chat.isActive()]

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """
        Get a Chat object by chat ID.

        Args:
            chat_id (str): The platform-specific chat ID.

        Returns:
            Optional[Chat]: The Chat object if found, else None.
        """
        return self.chats.get(str(chat_id))

    def get_person(self, user_id: str) -> Optional[Person]:
        """
        Get a Person object by user ID.

        Args:
            user_id (str): The platform-specific user ID.

        Returns:
            Optional[Person]: The Person object if found, else None.
        """
        return self.persons.get(str(user_id))

    def get_active_chats(self) -> List[Chat]:
        """
        Get all currently active Chat objects.

        Returns:
            List[Chat]: List of active Chat objects.
        """
        active_chat_objects = []
        for active_chat in self.active_chats:
            if active_chat.chat_object and active_chat.isActive():
                active_chat_objects.append(active_chat.chat_object)
        return active_chat_objects


__all__ = ["BasePlatform", "ActiveChat"]
