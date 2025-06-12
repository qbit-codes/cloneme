"""
Mods package for CloneMe project
Contains modular components for LLM management and other utilities
"""

__version__ = "1.0.0"
__author__ = "CloneMe Project"

from . import llm, objects

__all__ = [*llm.__all__, *objects.__all__] 