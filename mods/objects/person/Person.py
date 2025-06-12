"""
Person class defines a person

This class will be used to store the person's information
"""
from typing import List, Dict, Any, Optional
import uuid

class Person:
    person_id   : str
    identifiers : list[str]
    metadata    : Dict[str, Any]
    
    def __init__(
        self,
        person_id   : str = uuid.uuid4().hex,
        identifiers : list[str] = [],
        metadata    : Dict[str, Any] = None,
    ):
        self.person_id   = person_id
        self.identifiers = identifiers
        self.metadata    = metadata if metadata is not None else {}
    
    """
    User identifier methods
    
    1. Add an identifier
    2. Remove an identifier
    3. Get an identifier
    4. Get all identifiers
    """
    def add_identifier(self, identifier: str)   : self.identifiers.append(identifier)
    def remove_identifier(self, identifier: str) : self.identifiers.remove(identifier)
    def get_identifier(self, identifier: str) -> Optional[str]:
        if identifier in self.identifiers:
            return identifier
        return None
    def get_identifiers(self, limit: Optional[int] = None) -> list[str]:
        if limit is None or limit < 0: return self.identifiers
        return self.identifiers[:limit]
    
    """
    User message methods
    
    These methods are being removed as message management is shifting to the Chat class.
    Messages sent by a person can be retrieved by querying Chat objects.
    """
    
    def __str__(self)  -> str: return f"Person(person_id={self.person_id}, identifiers={self.identifiers})"
    def __repr__(self) -> str: return self.__str__()
    def __eq__(self, other: Any) -> bool: return self.person_id == other.person_id
    def __ne__(self, other: Any) -> bool: return self.person_id != other.person_id
    def __hash__(self) -> int: return hash(self.person_id)
    
__all__ = ["Person"]