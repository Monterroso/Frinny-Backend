"""
Personalities module for the agent system.

This module provides personality definitions for different agent personas,
centralizing system prompts, error messages, and response formats.
"""

from app.agent.personalities.base import BasePersonality
from app.agent.personalities.registry import PersonalityRegistry, get_personality
from app.agent.personalities.frinny import FrinnyPersonality
from app.agent.personalities.gamemaster import GameMasterPersonality

__all__ = [
    'BasePersonality',
    'PersonalityRegistry', 
    'get_personality',
    'FrinnyPersonality',
    'GameMasterPersonality'
] 