"""
Chat class defines a chat can be a group chat or a one to one chat

This class will be used to store the chat history of a chat
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union
import uuid

if TYPE_CHECKING:
    from mods.objects.messages.Message import Message

from mods.objects.person.Person import Person

class Chat:
    chat_id: str
    participants: Dict[str, Person]
    messages     : Dict[str, "Message"]
    
    def __init__(
        self,
        chat_id: str = None,
        participants: Dict[str, Person] = None,
        messages: Dict[str, "Message"] = None
    ):
        """
        Initialize the chat

        Args:
            chat_id (str): The id of the chat
            participants (Dict[str, Person]): The participants in the chat
            messages (Dict[str, Message]): Existing messages in the chat (for loading)
        """
        self.chat_id      = chat_id if chat_id is not None else uuid.uuid4().hex
        self.participants = participants if participants is not None else {}
        self.messages     = messages if messages is not None else {}
    
    """
    Chat participant methods
    
    1. Add a participant
    2. Remove a participant
    3. Get a participant
    4. Get all participants
    5. Get the number of participants
    6. Get a participant by identifier
    """
    def add_participant(self, participant: Person):
        """
        Add a participant to the chat
        
        Args:
            participant (Person): The participant to add
        """
        if not isinstance(participant, Person):
            raise TypeError("participant must be a Person object.")
        if participant.person_id in self.participants: return
        self.participants[participant.person_id] = participant
    
    def remove_participant(self, participant: Person):
        """
        Remove a participant from the chat
        
        Args:
            participant (Person): The participant to remove
        """
        if not isinstance(participant, Person):
            raise TypeError("participant must be a Person object.")
        if participant.person_id not in self.participants: return
        del self.participants[participant.person_id]
    
    def get_participant(self, participant_id: str) -> Optional[Person]:
        """
        Get a participant by their id
        
        Args:
            participant_id (str): The id of the participant to get
        
        Returns:
            Optional[Person]: The participant with the given id
        """
        if not isinstance(participant_id, str):
            raise TypeError("participant_id must be a string.")
        return self.participants.get(participant_id)
    
    def get_participants(self, limit: Optional[int] = None) -> List[Person]:
        """
        Get all participants in the chat
        
        Args:
            limit (int | None): The limit of participants to return
        
        Returns:
            List[Person]: The list of participants in the chat
        """
        all_participants = list(self.participants.values())
        if limit is None or limit < 0: return all_participants
        return all_participants[:limit]

    def get_participants_count(self) -> int:
        """
        Get the number of participants in the chat
        
        Returns:
            int: The number of participants in the chat
        """
        return len(self.participants)
    
    def get_participants_by_identifier(self, identifier: str) -> List[Person]:
        """
        Get all participants by identifier
        
        Args:
            identifier (str): The identifier to search for
        
        Returns:
            List[Person]: The list of participants with the identifier
        """
        if not isinstance(identifier, str):
            raise TypeError("identifier must be a string.")
        _participants = []
        for participant in self.participants.values():
            if identifier in participant.get_identifiers():
                _participants.append(participant)
        return _participants

    """
    Chat messages methods
    
    1. Add a message
    2. Remove a message
    3. Get a message
    4. Get all messages
    """
    def add_message(
        self,
        message: "Message",
    ) -> "Message":
        """
        Add a message to the chat.
        This method is responsible for linking messages to the chat and handling reply threading.
        
        Args:
            message (Message): The message object to add.
        
        Returns:
            Message: The added message object, with reply chain details populated.
        
        Raises:
            TypeError: If message is not a Message object.
            ValueError: If the message's sender is not a participant, or if chat_id doesn't match.
                        Or if replying to a non-existent message.
        """
        from mods.objects.messages.Message import Message
        if not isinstance(message, Message):
            raise TypeError("message must be a Message object.")
        
        if message.chat.chat_id != self.chat_id:
            raise ValueError(f"Message's chat_id '{message.chat.chat_id}' does not match this chat's ID '{self.chat_id}'.")

        if message.sender.person_id not in self.participants:
            raise ValueError(f"Sender '{message.sender.person_id}' is not a participant in this chat.")
        
        if message.reply_to_message_id:
            parent_message = self.messages.get(message.reply_to_message_id)
            if not parent_message:
                raise ValueError(f"Reply to message_id '{message.reply_to_message_id}' not found in chat.")
            
            message.root_message_id = parent_message.root_message_id if parent_message.root_message_id else parent_message.message_id
            
            message.reply_chain_ids = parent_message.reply_chain_ids + [parent_message.message_id]
        else:
            message.root_message_id = None
            message.reply_chain_ids = []

        if message.message_id in self.messages:
            pass
        self.messages[message.message_id] = message
        
        return message
    
    def remove_message(self, message_id: str):
        """
        Remove a message from the chat by its ID.
        
        Args:
            message_id (str): The ID of the message to remove.
        
        Returns:
            Optional["Message"]: The removed message object if found, else None.
        """
        if not isinstance(message_id, str):
            raise TypeError("message_id must be a string.")
            
        removed_message = self.messages.pop(message_id, None)
        
        if removed_message:
            return removed_message
        return None
    
    def get_message(self, message_id: str) -> Optional["Message"]:
        """
        Get a single message by its ID.
        
        Args:
            message_id (str): The ID of the message to retrieve.
        
        Returns:
            Message | None: The message object if found, else None.
        """
        if not isinstance(message_id, str):
            raise TypeError("message_id must be a string.")
        return self.messages.get(message_id)

    def get_messages(self, limit: Optional[int] = None) -> List["Message"]:
        """
        Get all messages in the chat.
        
        Args:
            limit (int | None): The limit of messages to return.
        
        Returns:
            List["Message"]: The list of messages in the chat (unsorted by default from dict.values()).
                           Consider sorting by created_at if order is critical.
        """
        all_messages = list(self.messages.values())

        if limit is None or limit < 0: return all_messages
        return all_messages[:limit]
    
    def __str__(self): return f"Chat(chat_id={self.chat_id}, participants_count={len(self.participants)}, messages_count={len(self.messages)})"
    def __repr__(self): return self.__str__()
    def __eq__(self, other): return self.chat_id == other.chat_id
    def __ne__(self, other): return self.chat_id != other.chat_id
    def __hash__(self): return hash(self.chat_id)
    
__all__ = ["Chat"]