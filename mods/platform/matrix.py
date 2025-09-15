"""
Matrix Platform Implementation for CloneMe

This module implements Matrix support using the matrix-nio client library.
It follows the same pattern as the Discord platform implementation.
"""

import asyncio
from typing import Any, List, Optional, TYPE_CHECKING

import re
import datetime

from nio import (
    AsyncClient,
    DownloadError,
    MatrixRoom,
    MatrixUser,
    ProfileGetAvatarError,
    ProfileGetAvatarResponse,
    RoomEncryptedMedia,
    RoomMessageAudio,
    RoomMessageEmote,
    RoomMessageFile,
    RoomMessageFormatted,
    RoomMessageImage,
    RoomMessageMedia,
    RoomMessageNotice,
    RoomMessageText,
    RoomMessageUnknown,
    SyncResponse,
    LoginResponse,
    JoinError,
    RoomSendError,
)
from langchain_core.language_models.chat_models import BaseChatModel

from mods.platform.base_platform import BasePlatform, ActiveChat
from mods.platform.platform_manager import PlatformManager
from mods.objects.chats.Chat import Chat
from mods.objects.messages.Message import Message
from mods.objects.person.Person import Person

if TYPE_CHECKING:
    from mods.config import Profile, SettingsManager


class MatrixPlatform(BasePlatform):
    """
    A platform for interacting with Matrix using matrix-nio.
    This class provides Matrix-specific implementation of the BasePlatform interface.
    """

    def __init__(
        self,
        homeserver: str,
        username: str,
        password: str,
        llm: BaseChatModel,
        profile: Optional["Profile"] = None,
        settings_manager: Optional["SettingsManager"] = None,
        device_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a MatrixPlatform instance.

        Args:
            homeserver (str): The Matrix homeserver URL (e.g., "https://matrix.org")
            username (str): The Matrix username (e.g., "@username:matrix.org")
            password (str): The Matrix password
            llm (BaseChatModel): The language model for AI decision making and response generation
            profile (Optional[Profile]): The profile to use for the bot
            settings_manager (Optional[SettingsManager]): The settings manager for hot-reloadable configuration
            device_id (Optional[str]): Device ID for the Matrix client
            **kwargs: Additional keyword arguments
        """
        super().__init__(llm=llm, profile=profile, settings_manager=settings_manager)

        self.homeserver = homeserver
        self.username = username
        self.password = password
        self.device_id = device_id

        # Initialize Matrix client
        self.matrix_client = AsyncClient(
            homeserver=homeserver, user=username, device_id=device_id
        )

        # Track typing contexts
        self._active_typing_contexts = {}

        # Initialize platform manager
        self.platform_manager = PlatformManager(
            llm=llm, profile=profile, settings_manager=settings_manager
        )

        # Setup Matrix event handlers
        self._setup_matrix_events()

    def _setup_matrix_events(self):
        """Set up Matrix client event handlers."""

        self.matrix_client.add_event_callback(self._on_message, RoomMessageText)
        self.matrix_client.add_response_callback(self._on_sync, SyncResponse)

    async def _on_sync(self, response: SyncResponse):
        """Called on each sync response from the Matrix server."""
        if not self._running:
            self._running = True
            self.logger.info(f"Matrix client synced and ready as {self.username}")

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming Matrix messages."""
        try:
            # Skip our own messages
            if event.sender == self.matrix_client.user_id:
                return await self._handle_own_message(event, room)

            # Process user messages
            return await self._handle_user_message(event, room)

        except Exception as e:
            self.logger.error(f"Error in Matrix message handler: {e}")

    async def _handle_own_message(self, event: RoomMessageText, room: MatrixRoom):
        """Handle messages sent by the bot itself."""
        self.logger.debug(f"Bot sent message in {room.room_id}: {event.body[:50]}...")

    async def _handle_user_message(self, event: RoomMessageText, room: MatrixRoom):
        """Handle messages from other users."""
        try:
            # Convert Matrix objects to CloneMe objects
            matrix_user = await self._get_matrix_user(event.sender, room)
            sender = self.convert_platform_user(matrix_user)
            chat = self.convert_platform_chat(room)
            msg_obj = self.convert_platform_message(event, room, chat, sender)
            chat.add_message(msg_obj)

            # Store objects for future reference
            # self.persons[person.person_id] = person
            # self.chats[chat.chat_id] = chat

            # Update active chats
            self._update_active_chat(chat.chat_id, chat)

            context_messages = await self.collect_context(event)
            # Process message through platform manager
            await self.platform_manager.process_message(self, msg_obj, context_messages)

        except Exception as e:
            self.logger.error(f"Error handling Matrix user message: {e}")

    def _update_person_matrix_info(self, person: Person, matrix_user: MatrixUser):
        """
        Update a Person object with current Matrix user information.

        Args:
            person (Person): The person object to update.
            matrix_user (MatrixUser): The Matrix user object with current info.
        """
        matrix_profile = {
            "user_id": str(matrix_user.user_id),
            "username": matrix_user.name,
            "display_name": matrix_user.display_name,
            "avatar_url": matrix_user.avatar_url,
        }

        if not hasattr(person, "metadata") or person.metadata is None:
            person.metadata = {}
        person.metadata["matrix_profile"] = matrix_profile

        generic_profile = {
            "platform": "matrix",
            "user_id": str(matrix_user.user_id),
            "username": matrix_user.name,
            "display_name": matrix_user.display_name,
            "avatar_url": matrix_user.avatar_url,
            "created_at": matrix_user.last_active_ago,
            "is_bot": False,
        }

        person.metadata["platform_profile"] = generic_profile

        current_identifiers = set(person.get_identifiers())
        new_identifiers = [str(matrix_user.user_id), matrix_user.name]

        if matrix_user.display_name and matrix_user.display_name != matrix_user.name:
            new_identifiers.append(matrix_user.display_name)
        for identifier in new_identifiers:
            if identifier not in current_identifiers:
                person.identifiers.append(identifier)

    async def _get_matrix_user(self, user_id: str, room: MatrixRoom):
        """Get user information from Matrix."""
        # Return a simple user object - in a real implementation,
        # you might want to fetch more user details
        avatar_url = None

        avatar_resp = await self.matrix_client.get_avatar(user_id)

        if isinstance(avatar_resp, ProfileGetAvatarResponse):
            avatar_url = avatar_resp.avatar_url
        elif isinstance(avatar_resp, ProfileGetAvatarError):
            print(f"Error while getting avatar: {avatar_resp.message}")

        return MatrixUser(
            user_id=user_id,
            display_name=room.user_name(user_id) or user_id,
            avatar_url=avatar_url,  # Could be fetched if needed
        )

    def _update_active_chat(self, chat_id: str, chat: Chat):
        """Update or add a chat to the active chats list."""
        # Find existing active chat
        for active_chat in self.active_chats:
            if active_chat.active_chat_id == chat_id:
                active_chat.update_last_message_time()
                active_chat.chat_object = chat
                return

        # Create new active chat
        active_chat = ActiveChat(chat_id, chat)
        self.active_chats.append(active_chat)

    # Implementation of abstract methods from BasePlatform

    def get_platform_name(self) -> str:
        """Get the name of this platform."""
        return "matrix"

    async def send_message(self, chat_id: str, content: str) -> bool:
        """Send a message to a Matrix room."""
        try:
            response = await self.matrix_client.room_send(
                room_id=chat_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": content},
            )

            if isinstance(response, RoomSendError):
                self.logger.error(
                    f"Failed to send message to {chat_id}: {response.message}"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error sending Matrix message: {e}")
            return False

    async def start_typing(self, chat_id: str) -> None:
        """Start typing indicator in a Matrix room."""
        try:
            await self.matrix_client.room_typing(chat_id, typing_state=True)
            self._active_typing_contexts[chat_id] = True
        except Exception as e:
            self.logger.error(f"Error starting typing in Matrix room {chat_id}: {e}")

    async def stop_typing(self, chat_id: str) -> None:
        """Stop typing indicator in a Matrix room."""
        try:
            await self.matrix_client.room_typing(chat_id, typing_state=False)
            self._active_typing_contexts.pop(chat_id, None)
        except Exception as e:
            self.logger.error(f"Error stopping typing in Matrix room {chat_id}: {e}")

    async def collect_context(
        self, message_ref: Any, max_context: int = 10
    ) -> List[Message]:
        """Collect recent messages from the Matrix room as context."""
        try:
            # Get the room from the message
            room = self.matrix_client.rooms.get(message_ref.room_id)
            if not room:
                return []

            context_messages = []

            # Get recent messages from room timeline
            # Note: This is a simplified implementation
            # In production, you might want to use room.messages() or similar

            return context_messages

        except Exception as e:
            self.logger.error(f"Error collecting Matrix context: {e}")
            return []

    def convert_platform_message(
        self, event, room: MatrixRoom, chat: Chat, sender: Person
    ) -> Message:
        """Convert a Matrix message to a generic Message object."""
        """
        if isinstance(event, RoomMessageMedia): # for all media events
            mxc = event.url
            url = await self.matrix_client.mxc_to_http(mxc) # media url
            msg_url = " [" + url + "]"

            resp = await download_mxc(self.matrix_client, mxc)
            if isinstance(resp, DownloadError):

        if isinstance(event, RoomEncryptedMedia): # for all e2e media
            pass
        if isinstance(event, RoomMessageAudio):
            pass
        elif isinstance(event, RoomMessageEmote):
            pass
        elif isinstance(event, RoomMessageFile):
            pass
        elif isinstance(event, RoomMessageFormatted):
            pass
        elif isinstance(event, RoomMessageImage):
            pass
        elif isinstance(event, RoomMessageNotice):
            pass
        elif isinstance(event, RoomMessageText):
            pass
        elif isinstance(event, RoomMessageUnknown):
            pass
        """
        timestamp = datetime.datetime.fromtimestamp(
            int(event.server_timestamp / 1000)
        )  # sec since 1970
        event_datetime = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        sender_nick = room.user_name(event.sender)
        if not sender_nick:  # convert @foo:mat.io into foo
            sender_nick = event.sender.split(":")[0][1:]
        room_nick = room.display_name
        if room_nick in (None, "", "Empty Room"):
            room_nick = "Undetermined"
        msg = event.body
        fixed_msg = re.sub("\n", "\n    ", msg)
        text = fixed_msg
        metadata = {
            "matrix_source": event.source,
            "matrix_room": room,
            "matrix_room_display_name": room.display_name,
            "matrix_sender_name": sender_nick,
            "matrix_datetime": event_datetime,
        }

        return Message(
            message_id=str(event.event_id),
            content=text,
            sender=sender,
            created_at=timestamp,
            chat=chat,
            metadata=metadata,
        )

    def convert_platform_user(self, platform_user: MatrixUser) -> Person:
        """Convert a Matrix user to a generic Person object."""
        user_id = str(platform_user.user_id)

        is_bot_self = (
            self.matrix_client.user
            and platform_user.user_id == self.matrix_client.user_id
        )
        person_id = user_id  # Use actual user ID for both bot and regular users
        storage_key = user_id

        if storage_key in self.persons:
            person = self.persons[storage_key]
            self._update_person_matrix_info(person, platform_user)
            return person

        identifiers = [user_id, platform_user.name]

        if (
            platform_user.display_name
            and platform_user.display_name != platform_user.name
        ):
            identifiers.append(platform_user.display_name)

        if is_bot_self and "ai_assistant" not in identifiers:
            identifiers.append("ai_assistant")

        person = Person(person_id=person_id, identifiers=identifiers)
        self._update_person_matrix_info(person, platform_user)
        self.persons[storage_key] = person
        return person

    def convert_platform_chat(self, platform_chat: MatrixRoom) -> Chat:
        """Convert a Matrix room to a generic Chat object."""
        chat = Chat(chat_id=platform_chat.room_id)

        if hasattr(platform_chat, "users"):
            for user in platform_chat.users:
                try:
                    person = self.convert_platform_user(platform_chat.users[user])
                    chat.add_participant(person)
                except Exception as e:
                    print(f"Error converting platform chat: {e}")

        return chat

    async def start_platform(self) -> None:
        """Start the Matrix client and begin listening for events."""
        try:
            self.logger.info("Starting Matrix platform...")

            # Login to Matrix
            login_response = await self.matrix_client.login(
                self.password, device_name=self.device_id
            )
            if isinstance(login_response, LoginResponse):
                self.logger.info(f"Logged in to Matrix as {self.username}")
            else:
                self.logger.error(f"Failed to login to Matrix: {login_response}")
                return

            # Start syncing
            await self.matrix_client.sync_forever(timeout=30000)

        except Exception as e:
            self.logger.error(f"Error starting Matrix platform: {e}")
            raise

    def is_running(self) -> bool:
        """Check if the Matrix client is currently running and connected."""
        return self._running and self.matrix_client.logged_in

    def run_platform(self):
        """Run the Matrix platform (blocking call)."""
        try:
            asyncio.run(self.start_platform())
        except KeyboardInterrupt:
            self.logger.info("Matrix platform stopped by user")
        except Exception as e:
            self.logger.error(f"Matrix platform error: {e}")
            raise

    async def join_room(self, room_id: str) -> bool:
        """Join a Matrix room."""
        try:
            response = await self.matrix_client.join(room_id)
            if isinstance(response, JoinError):
                self.logger.error(f"Failed to join room {room_id}: {response.message}")
                return False

            self.logger.info(f"Successfully joined room {room_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error joining Matrix room {room_id}: {e}")
            return False

    async def leave_room(self, room_id: str) -> bool:
        """Leave a Matrix room."""
        try:
            response = await self.matrix_client.room_leave(room_id)
            self.logger.info(f"Left room {room_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error leaving Matrix room {room_id}: {e}")
            return False

    async def close(self):
        """Close the Matrix client connection."""
        try:
            await self.matrix_client.logout()
            await self.matrix_client.close()
            self._running = False
            self.logger.info("Matrix client closed")
        except Exception as e:
            self.logger.error(f"Error closing Matrix client: {e}")


__all__ = ["MatrixPlatform"]
