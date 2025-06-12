"""
Message class defines a message

This class will be used to store the message's information
"""
from datetime import datetime
import uuid, enum
import hashlib
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mods.objects.chats.Chat import Chat

from mods.objects.person.Person import Person

class ResponseType(enum.Enum):
    NO_ARGS_PROVIDED  = "no_args_provided"
    SENDER_NOT_PERSON = "sender_not_person"
    CHAT_NOT_CHAT     = "chat_not_chat"
    METADATA_NOT_DICT = "metadata_not_dict"
    SUCCESS           = "success"
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.value == other.value
    
    def __ne__(self, other):
        return self.value != other.value
    
class Message:
    """
    Message class defines a message

    This class will be used to store the message's information
    
    message_id             : str      # The unique identifier for the message
    content                : str      # The content of the message
    content_length         : int      # The length of the content
    content_hash           : str      # The hash of the content
    sender                 : Person   # The sender of the message
    chat                   : Chat     # The chat the message is in
    created_at             : datetime # The date and time the message was created
    updated_at             : datetime # The date and time the message was last updated
    metadata               : dict     # Extra key-value metadata for the message

    # Reply System Enhancements
    reply_to_message_id    : Optional[str] = None # The message_id of the message this directly replies to
    root_message_id        : Optional[str] = None # The message_id of the root message in the reply thread
    reply_chain_ids        : List[str]     = []   # Ordered list of message_ids from root to direct parent

    # Additional Features
    reactions              : Dict[str, List[str]] = {} # {emoji: [person_id, ...]}
    mentions               : List[str]            = [] # List of person_ids mentioned
    forwarded_from_message_id : Optional[str]     = None # Original message_id if forwarded
    forwarded_from_chat_id : Optional[str]      = None # Original chat_id if forwarded
    """
    message_id             : str
    content                : str
    content_length         : int
    content_hash           : str
    sender                 : Person
    chat                   : "Chat"
    created_at             : datetime
    updated_at             : datetime
    metadata               : Dict[str, Any]
    
    reply_to_message_id    : Optional[str]
    root_message_id        : Optional[str]
    reply_chain_ids        : List[str]

    reactions              : Dict[str, List[str]]
    mentions               : List[str]
    forwarded_from_message_id : Optional[str]
    forwarded_from_chat_id : Optional[str]
    
    def __init__(
        self,
        content     : str       = "",
        sender      : Person    = None,
        chat        : "Chat"    = None,
        message_id  : str       = None,
        reply_to_message_id : Optional[str] = None,
        root_message_id     : Optional[str] = None,
        reply_chain_ids     : List[str]     = None,
        reactions           : Dict[str, List[str]] = None,
        mentions            : List[str]            = None,
        forwarded_from_message_id : Optional[str] = None,
        forwarded_from_chat_id : Optional[str]    = None,
        created_at  : datetime  = None,
        updated_at  : datetime  = None,
        metadata    : Dict[str, Any] = None,
    ):
        self.message_id     = message_id if message_id is not None else uuid.uuid4().hex

        if not isinstance(self.message_id, str) or not self.message_id: raise ValueError("message_id must be a non-empty string!")
        if not isinstance(content, str): raise ValueError("content must be a string!")
        if not isinstance(sender, Person): raise ValueError("sender must be a Person object!") 
        from mods.objects.chats.Chat import Chat
        if not isinstance(chat, Chat): raise ValueError("chat must be a Chat object!")
        
        self.content        = content
        self.content_length = len(content)
        self.content_hash   = hashlib.sha256(content.encode('utf-8')).hexdigest()
        self.sender         = sender
        self.chat           = chat
        
        self.created_at     = created_at if created_at is not None else datetime.now()
        self.updated_at     = updated_at if updated_at is not None else datetime.now()
        
        self.metadata       = metadata if metadata is not None else {}
        if not isinstance(self.metadata, dict): raise ValueError("metadata must be a dictionary!")

        self.reply_to_message_id = reply_to_message_id
        if self.reply_to_message_id is not None and not isinstance(self.reply_to_message_id, str):
            raise ValueError("reply_to_message_id must be a string or None!")
        
        self.root_message_id = root_message_id
        if self.root_message_id is not None and not isinstance(self.root_message_id, str):
            raise ValueError("root_message_id must be a string or None!")

        self.reply_chain_ids = reply_chain_ids if reply_chain_ids is not None else []
        if not isinstance(self.reply_chain_ids, list) or not all(isinstance(i, str) for i in self.reply_chain_ids):
            raise ValueError("reply_chain_ids must be a list of strings!")
        
        self.reactions = reactions if reactions is not None else {}
        if not isinstance(self.reactions, dict) or not all(isinstance(k, str) and isinstance(v, list) for k, v in self.reactions.items()):
            raise ValueError("reactions must be a dictionary with string keys and list values!")

        self.mentions = mentions if mentions is not None else []
        if not isinstance(self.mentions, list) or not all(isinstance(i, str) for i in self.mentions):
            raise ValueError("mentions must be a list of strings (person_ids)!")

        self.forwarded_from_message_id = forwarded_from_message_id
        if self.forwarded_from_message_id is not None and not isinstance(self.forwarded_from_message_id, str):
            raise ValueError("forwarded_from_message_id must be a string or None!")
        
        self.forwarded_from_chat_id = forwarded_from_chat_id
        if self.forwarded_from_chat_id is not None and not isinstance(self.forwarded_from_chat_id, str):
            raise ValueError("forwarded_from_chat_id must be a string or None!")

    @property
    def is_reply(self) -> bool:
        return self.reply_to_message_id is not None
    
    def update(
        self, 
        content: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        reactions: Optional[Dict[str, List[str]]] = None,
        mentions: Optional[List[str]] = None,
    ) -> ResponseType:
        """
        Updates the message with the given arguments.
        
        Args:
            content (str): The new content of the message
            metadata (dict): The new metadata of the message
            reactions (Dict[str, List[str]]): New reactions data
            mentions (List[str]): New mentions list
        
        Returns:
            ResponseType: The response type of the update
        
        Extra:
            At least one argument must be provided!
        """
        
        if not any([content, metadata, reactions, mentions]): return ResponseType.NO_ARGS_PROVIDED
        
        if metadata is not None and not isinstance(metadata, dict): return ResponseType.METADATA_NOT_DICT
        if reactions is not None and (not isinstance(reactions, dict) or not all(isinstance(k, str) and isinstance(v, list) for k, v in reactions.items())):
            raise ValueError("reactions must be a dictionary with string keys and list values!")
        if mentions is not None and (not isinstance(mentions, list) or not all(isinstance(i, str) for i in mentions)):
            raise ValueError("mentions must be a list of strings (person_ids)!")

        if content  is not None:
            self.content        = content
            self.content_length = len(content)
            self.content_hash   = hashlib.sha256(content.encode('utf-8')).hexdigest()
        if metadata is not None: self.metadata  = metadata
        if reactions is not None: self.reactions = reactions
        if mentions is not None: self.mentions = mentions
        
        self.updated_at = datetime.now()
        
        return ResponseType.SUCCESS
    
    def __str__(self):
        reply_info = f", reply_to={self.reply_to_message_id}" if self.is_reply else ""
        thread_info = f", root={self.root_message_id}, chain={self.reply_chain_ids}" if self.root_message_id else ""
        forward_info = f", forwarded_from={self.forwarded_from_message_id}" if self.forwarded_from_message_id else ""

        content_preview = self.content[:30] + f"... [TRUNCATED - {len(self.content) - 30} chars cut]" if len(self.content) > 30 else self.content

        return (
            f"Message(id={self.message_id}, content='[MESSAGE START] {content_preview} [MESSAGE END]', "
            f"sender_id={self.sender.person_id}, chat_id={self.chat.chat_id}{reply_info}{thread_info}{forward_info}, "
            f"reactions={self.reactions}, mentions={self.mentions}, "
            f"created_at={self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    
    def __repr__(self):
        return self.__str__()
    
__all__ = ["Message"]