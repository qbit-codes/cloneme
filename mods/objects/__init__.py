"""
Objects package for CloneMe project
Contains modular components for objects
"""

__version__ = "1.0.0"
__author__ = "CloneMe Project"

from . import person, messages, chats

__all__ = [*person.__all__, *messages.__all__, *chats.__all__]