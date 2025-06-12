import asyncio
from typing import Any, List, Optional, TYPE_CHECKING

import discord
from langchain_core.language_models.chat_models import BaseChatModel

from mods.platform.base_platform import BasePlatform, ActiveChat
from mods.platform.platform_manager import PlatformManager
from mods.objects.chats.Chat import Chat
from mods.objects.messages.Message import Message
from mods.objects.person.Person import Person

if TYPE_CHECKING:
    from mods.config import Profile, SettingsManager


class DiscordPlatform(BasePlatform):
    """
    A platform for interacting with Discord using discord.py-self.
    This class inherits from discord.Client for proper event handling.
    """

    def __init__(
        self,
        discord_token: str,
        llm: BaseChatModel,
        profile: Optional["Profile"] = None,
        settings_manager: Optional["SettingsManager"] = None,
        **kwargs,
    ):
        """
        Initializes a DiscordPlatform instance.

        Args:
            discord_token (str): The Discord token for authentication.
            llm (BaseChatModel): The language model to use for decision making and response generation.
            profile (Optional[Profile]): The profile to use for the bot.
            settings_manager (Optional[SettingsManager]): The settings manager for hot-reloadable configuration.
            **kwargs: Additional keyword arguments to pass to the discord.Client constructor.
        """
        super().__init__(llm=llm, profile=profile, settings_manager=settings_manager)

        self.discord_token: str = discord_token
        self.discord_client = discord.Client(**kwargs)

        self._active_typing_contexts = {}

        self.platform_manager = PlatformManager(llm=llm, profile=profile, settings_manager=settings_manager)

        self._setup_discord_events()

    def _setup_discord_events(self):
        """Set up Discord client event handlers."""

        @self.discord_client.event
        async def on_ready():
            """Called when the Discord client has successfully connected."""
            self.logger.debug(f"Logged on as {self.discord_client.user}!")
            self._running = True

        @self.discord_client.event
        async def on_message(message: discord.Message):
            """Handle all incoming Discord messages."""
            try:
                if message.author == self.discord_client.user:
                    return await self._handle_own_message(message)
                elif message.author.bot is False:
                    # Check if we should always respond based on Discord-specific settings
                    should_always_respond = self._should_always_respond(message)

                    # Process if it's an active chat OR if Discord settings require always responding
                    if self._is_active_chat_message(message) or should_always_respond:
                        return await self._handle_user_message(message)

                self.cleanup_inactive_chats()
                return None
            except Exception as e:
                self.logger.error(f"Error in on_message: {e}")

    def get_platform_name(self) -> str:
        """Get the name of this platform."""
        return "discord"

    async def send_message(self, chat_id: str, content: str) -> bool:
        """Send a message to a Discord channel."""
        try:
            channel = self.discord_client.get_channel(int(chat_id))
            if channel:
                await channel.send(content)
                return True
            else:
                self.logger.error(f"Discord channel {chat_id} not found")
                return False
        except Exception as e:
            self.logger.error(f"Error sending Discord message: {e}")
            return False

    async def start_typing(self, chat_id: str) -> None:
        """Start typing indicator in a Discord channel."""
        try:
            channel = self.discord_client.get_channel(int(chat_id))
            if channel:
                typing_context = channel.typing()
                await typing_context.__aenter__()
                self._active_typing_contexts[chat_id] = typing_context
                self.logger.debug(f"Started typing indicator for channel {chat_id}")
        except Exception as e:
            self.logger.error(f"Error starting typing in Discord channel {chat_id}: {e}")

    async def stop_typing(self, chat_id: str) -> None:
        """Stop typing indicator in a Discord channel."""
        try:
            typing_context = self._active_typing_contexts.pop(chat_id, None)
            if typing_context:
                await typing_context.__aexit__(None, None, None)
                self.logger.debug(f"Stopped typing indicator for channel {chat_id}")
            else:
                self.logger.debug(f"No active typing context found for channel {chat_id}")
        except Exception as e:
            self.logger.error(f"Error stopping typing in Discord channel {chat_id}: {e}")
            self._active_typing_contexts.pop(chat_id, None)

    async def collect_context(self, message_ref: Any, max_context: int = 10) -> List[Message]:
        """
        Collect recent messages from Discord channel as context.

        Args:
            message_ref: Discord message object OR generic Message object to collect context for.
            max_context (int): Maximum number of messages to collect.

        Returns:
            List[Message]: List of Message objects representing the context.
        """
        context: List[Message] = []

        if hasattr(message_ref, 'channel'):
            chat = self.convert_platform_chat(message_ref.channel)
            channel_id = str(message_ref.channel.id)
            discord_channel = message_ref.channel
        else:
            channel_id = message_ref.chat.chat_id
            discord_channel = self.discord_client.get_channel(int(channel_id))
            if not discord_channel:
                self.logger.error(f"Could not find Discord channel {channel_id}")
                return []
            chat = self.convert_platform_chat(discord_channel)

        raw_messages = []
        async for msg in discord_channel.history(limit=max_context):
            raw_messages.append(msg)

        context_message_ids = [str(msg.id) for msg in raw_messages]
        self.remove_flagged_messages_not_in_context(channel_id, context_message_ids)

        flagged_count = 0
        for msg in raw_messages:
            message_id = str(msg.id)

            if self.is_message_flagged(message_id):
                flagged_count += 1
                self.logger.debug(f"🚫 Filtering out flagged message {message_id} from context")
                continue

            sender = self.convert_platform_user(msg.author)
            chat.add_participant(sender)
            message_obj = self.convert_platform_message(msg, chat, sender)
            context.append(message_obj)

        if flagged_count > 0:
            self.logger.debug(
                f"📋 Context collected: {len(context)} messages ({flagged_count} flagged messages filtered out)"
            )

        return context

    def convert_platform_message(self, platform_msg: discord.Message, chat: Chat, sender: Person) -> Message:
        """Convert a Discord message to a generic Message object."""
        mentions = self._extract_mentions(platform_msg)
        reply_to_message_id = self._get_reply_to_message_id(platform_msg)

        metadata = {
            "discord_message_id": str(platform_msg.id),
            "discord_channel_id": str(platform_msg.channel.id),
            "discord_guild_id": str(platform_msg.guild.id) if platform_msg.guild else None,
            "discord_channel_name": platform_msg.channel.name if hasattr(platform_msg.channel, "name") else None,
            "discord_author_name": platform_msg.author.name,
            "discord_author_display_name": platform_msg.author.display_name,
        }

        message = Message(
            message_id=str(platform_msg.id),
            content=platform_msg.content,
            sender=sender,
            chat=chat,
            reply_to_message_id=reply_to_message_id,
            mentions=mentions,
            created_at=platform_msg.created_at,
            updated_at=platform_msg.edited_at if platform_msg.edited_at else platform_msg.created_at,
            metadata=metadata,
        )

        return message

    def convert_platform_user(self, platform_user: discord.User) -> Person:
        """Convert a Discord user to a generic Person object."""
        user_id = str(platform_user.id)

        is_bot_self = self.discord_client.user and platform_user.id == self.discord_client.user.id
        person_id = user_id  # Use actual user ID for both bot and regular users
        storage_key = user_id

        if storage_key in self.persons:
            person = self.persons[storage_key]
            self._update_person_discord_info(person, platform_user)
            return person

        identifiers = [user_id, platform_user.name]

        if platform_user.display_name and platform_user.display_name != platform_user.name:
            identifiers.append(platform_user.display_name)

        if hasattr(platform_user, "global_name") and platform_user.global_name:
            if platform_user.global_name not in identifiers:
                identifiers.append(platform_user.global_name)

        if is_bot_self and "ai_assistant" not in identifiers:
            identifiers.append("ai_assistant")

        person = Person(person_id=person_id, identifiers=identifiers)
        self._update_person_discord_info(person, platform_user)
        self.persons[storage_key] = person
        return person

    def convert_platform_chat(self, platform_chat: discord.TextChannel) -> Chat:
        """Convert a Discord channel to a generic Chat object."""
        channel_id = str(platform_chat.id)

        if channel_id in self.chats:
            return self.chats[channel_id]

        chat = Chat(chat_id=channel_id)

        if hasattr(platform_chat, "members"):
            for member in platform_chat.members:
                try:
                    person = self.convert_platform_user(member)
                    chat.add_participant(person)
                except Exception as e:
                    self.logger.warning(f"Warning: Could not add participant {member.name}: {e}")

        self.chats[channel_id] = chat
        return chat

    async def start_platform(self) -> None:
        """Start the Discord platform client."""
        try:
            async with self.discord_client:
                await self.discord_client.start(self.discord_token)
        except Exception as e:
            self.logger.error(f"Error starting Discord platform: {e}")
            raise

    def is_running(self) -> bool:
        """Check if the Discord client is currently running and connected."""
        return self._running and not self.discord_client.is_closed()

    def get_or_create_person(self, discord_user: discord.User) -> Person:
        """
        Get or create a Person object from a Discord user.
        This is a legacy method that delegates to convert_platform_user.

        Args:
            discord_user (discord.User): The Discord user object.

        Returns:
            Person: The Person object representing the Discord user.
        """
        return self.convert_platform_user(discord_user)

    def _extract_mentions(self, discord_message: discord.Message) -> List[str]:
        """Extract mentioned user IDs from a Discord message."""
        mentions = []
        for mentioned_user in discord_message.mentions:
            mentions.append(str(mentioned_user.id))
        return mentions

    def _get_reply_to_message_id(self, discord_message: discord.Message) -> Optional[str]:
        """Get the message ID that this Discord message is replying to."""
        if discord_message.reference and discord_message.reference.message_id:
            return str(discord_message.reference.message_id)
        return None

    def _is_active_chat_message(self, message: discord.Message) -> bool:
        """Check if the message is part of an active chat."""
        chat_id = str(message.channel.id)
        existing_chat = next(
            (chat for chat in self.active_chats if chat.active_chat_id == chat_id), None
        )
        return existing_chat is not None

    def _is_direct_message(self, message: discord.Message) -> bool:
        """Check if a Discord message is a direct message using Discord's native detection."""
        return isinstance(message.channel, discord.DMChannel)

    def _is_bot_mentioned(self, message: discord.Message) -> bool:
        """Check if the bot is mentioned in a Discord message."""
        if not self.discord_client.user:
            return False
        return self.discord_client.user in message.mentions

    def _should_always_respond(self, message: discord.Message) -> bool:
        """
        Check if the bot should always respond based on Discord-specific settings.

        Returns:
            bool: True if the bot should always respond, False otherwise
        """
        if not self.settings_manager:
            return False

        # Check if it's a DM and always_answer_dms is enabled
        if self._is_direct_message(message):
            return self.settings_manager.get('platform_specific.discord.always_answer_dms', True)

        # Check if bot is mentioned and always_reply_to_mentions is enabled
        if self._is_bot_mentioned(message):
            return self.settings_manager.get('platform_specific.discord.always_reply_to_mentions', True)

        return False

    async def _handle_own_message(self, message: discord.Message):
        """Handle messages sent by the bot and manage active chats."""
        try:
            chat_id = str(message.channel.id)
            chat = self.convert_platform_chat(message.channel)
            sender = self.convert_platform_user(message.author)

            chat.add_participant(sender)
            msg_obj = self.convert_platform_message(message, chat, sender)
            chat.add_message(msg_obj)

            existing_active_chat = next(
                (chat_obj for chat_obj in self.active_chats if chat_obj.active_chat_id == chat_id), None
            )

            if existing_active_chat:
                existing_active_chat.update_last_message_time()
                existing_active_chat.chat_object = chat
            else:
                self.active_chats.append(ActiveChat(chat_id, chat))

            self.cleanup_inactive_chats()

        except Exception as e:
            self.logger.error(f"Error handling own message: {e}")

    async def _handle_user_message(self, message: discord.Message):
        """Handle messages from users using the platform manager."""
        try:
            chat_id = str(message.channel.id)
            chat = self.convert_platform_chat(message.channel)
            sender = self.convert_platform_user(message.author)

            chat.add_participant(sender)
            msg_obj = self.convert_platform_message(message, chat, sender)
            chat.add_message(msg_obj)

            existing_active_chat = next(
                (chat_obj for chat_obj in self.active_chats if chat_obj.active_chat_id == chat_id), None
            )

            if existing_active_chat:
                existing_active_chat.update_last_message_time()
                existing_active_chat.chat_object = chat

            context_messages = await self.collect_context(message)
            # Pass Discord's native DM detection to the platform manager
            is_dm = self._is_direct_message(message)
            await self.platform_manager.process_message(self, msg_obj, context_messages, is_dm_override=is_dm)

        except Exception as e:
            self.logger.error(f"Error handling user message: {e}")

    def _update_person_discord_info(self, person: Person, discord_user: discord.User):
        """
        Update a Person object with current Discord user information.

        Args:
            person (Person): The Person object to update.
            discord_user (discord.User): The Discord user object with current info.
        """
        discord_profile = {
            "user_id": str(discord_user.id),
            "username": discord_user.name,
            "display_name": discord_user.display_name,
            "discriminator": getattr(discord_user, "discriminator", None),
            "avatar_url": str(discord_user.avatar.url) if discord_user.avatar else None,
            "default_avatar_url": str(discord_user.default_avatar.url),
            "created_at": discord_user.created_at.isoformat(),
            "is_bot": discord_user.bot,
            "is_system": getattr(discord_user, "system", False),
        }

        if hasattr(discord_user, "global_name") and discord_user.global_name:
            discord_profile["global_name"] = discord_user.global_name

        if hasattr(discord_user, "banner") and discord_user.banner:
            discord_profile["banner_url"] = str(discord_user.banner.url)

        if hasattr(discord_user, "accent_color") and discord_user.accent_color:
            discord_profile["accent_color"] = str(discord_user.accent_color)

        if not hasattr(person, "metadata") or person.metadata is None:
            person.metadata = {}
        person.metadata["discord_profile"] = discord_profile

        generic_profile = {
            "platform": "discord",
            "user_id": str(discord_user.id),
            "username": discord_user.name,
            "display_name": discord_user.display_name,
            "avatar_url": str(discord_user.avatar.url) if discord_user.avatar else None,
            "created_at": discord_user.created_at.isoformat(),
            "is_bot": discord_user.bot,
        }

        if hasattr(discord_user, "global_name") and discord_user.global_name:
            generic_profile["global_name"] = discord_user.global_name

        if hasattr(discord_user, "banner") and discord_user.banner:
            generic_profile["banner_url"] = str(discord_user.banner.url)

        if hasattr(discord_user, "accent_color") and discord_user.accent_color:
            generic_profile["accent_color"] = str(discord_user.accent_color)

        person.metadata["platform_profile"] = generic_profile

        current_identifiers = set(person.get_identifiers())
        new_identifiers = [str(discord_user.id), discord_user.name]

        if discord_user.display_name and discord_user.display_name != discord_user.name:
            new_identifiers.append(discord_user.display_name)

        if hasattr(discord_user, "global_name") and discord_user.global_name:
            new_identifiers.append(discord_user.global_name)

        for identifier in new_identifiers:
            if identifier not in current_identifiers:
                person.identifiers.append(identifier)

    def get_or_create_chat(self, discord_channel: discord.TextChannel) -> Chat:
        """
        Get or create a Chat object from a Discord channel.
        This is a legacy method that delegates to convert_platform_chat.

        Args:
            discord_channel (discord.TextChannel): The Discord channel object.

        Returns:
            Chat: The Chat object representing the Discord channel.
        """
        return self.convert_platform_chat(discord_channel)

    def extract_mentions(self, discord_message: discord.Message) -> List[str]:
        """
        Extract mentioned user IDs from a Discord message.
        This is a legacy method that delegates to _extract_mentions.

        Args:
            discord_message (discord.Message): The Discord message.

        Returns:
            List[str]: List of mentioned user IDs (person_ids).
        """
        return self._extract_mentions(discord_message)

    def get_reply_to_message_id(self, discord_message: discord.Message) -> Optional[str]:
        """
        Get the message ID that this Discord message is replying to.
        This is a legacy method that delegates to _get_reply_to_message_id.

        Args:
            discord_message (discord.Message): The Discord message.

        Returns:
            Optional[str]: The message ID being replied to, or None.
        """
        return self._get_reply_to_message_id(discord_message)

    def discord_message_to_message(self, discord_msg: discord.Message, chat: Chat, sender: Person) -> Message:
        """
        Convert a Discord message to a Message object.
        This is a legacy method that delegates to convert_platform_message.

        Args:
            discord_msg (discord.Message): The Discord message.
            chat (Chat): The Chat object this message belongs to.
            sender (Person): The Person who sent the message.

        Returns:
            Message: The converted Message object.
        """
        return self.convert_platform_message(discord_msg, chat, sender)

    def run_platform(self):
        """
        Run the Discord platform. This creates a new event loop and runs the client.
        """
        try:
            asyncio.run(self.start_platform())
        except Exception as e:
            self.logger.error(f"Error running Discord platform: {e}")
            raise

    def cleanupInactiveChats(self):
        """
        Cleanup inactive chats.
        This is a legacy method that delegates to cleanup_inactive_chats.
        """
        self.cleanup_inactive_chats()

    def isActiveChatMessage(self, message: discord.Message) -> bool:
        """
        Check if the message is part of an active chat.
        This is a legacy method that delegates to _is_active_chat_message.

        Args:
            message (discord.Message): The Discord message to check.

        Returns:
            bool: True if the message is part of an active chat, False otherwise.
        """
        return self._is_active_chat_message(message)

    async def handleOwnMessage(self, message: discord.Message):
        """
        Handle messages sent by the bot and manage active chats.
        This is a legacy method that delegates to _handle_own_message.

        Args:
            message (discord.Message): The Discord message sent by the bot.
        """
        return await self._handle_own_message(message)

    async def handleMessage(self, message: discord.Message):
        """
        Process a regular message from Discord.
        This is a legacy method that delegates to _handle_user_message.

        Args:
            message (discord.Message): The Discord message to process.
        """
        return await self._handle_user_message(message)

    def get_chat(self, channel_id: str) -> Optional[Chat]:
        """
        Get a Chat object by channel ID.
        
        Args:
            channel_id (str): The Discord channel ID
            
        Returns:
            Optional[Chat]: The Chat object if found, else None
        """
        return self.chats.get(str(channel_id))
    
    def get_person(self, user_id: str) -> Optional[Person]:
        """
        Get a Person object by Discord user ID.
        
        Args:
            user_id (str): The Discord user ID
            
        Returns:
            Optional[Person]: The Person object if found, else None
        """
        return self.persons.get(str(user_id))
    
    def get_active_chats(self) -> List[Chat]:
        """
        Get all currently active Chat objects.
        
        Returns:
            List[Chat]: List of active Chat objects
        """
        active_chat_objects = []
        for active_chat in self.active_chats:
            if active_chat.chat_object and active_chat.isActive():
                active_chat_objects.append(active_chat.chat_object)
        return active_chat_objects
    
    def get_chat_messages(self, channel_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from a specific chat.

        Args:
            channel_id (str): The Discord channel ID
            limit (Optional[int]): Maximum number of messages to return

        Returns:
            List[Message]: List of Message objects from the chat
        """
        chat = self.get_chat(channel_id)
        if chat:
            return chat.get_messages(limit)
        return []

    def main(self):
        """
        Legacy method for backwards compatibility.
        Returns client info for external use.
        """
        return {
            "client": self,
            "platform": self
        }

__all__ = ['DiscordPlatform']