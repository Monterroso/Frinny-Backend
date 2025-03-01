"""
Personality registry for agent system.

This module handles the registration and retrieval of agent personalities.
"""
from typing import Dict, Type, Optional
import os
from app.agent.personalities.base import BasePersonality
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)


class PersonalityRegistry:
    """
    Registry for managing available agent personalities.
    
    This class allows registration of personality classes and
    selection of personalities by name or from configuration.
    """
    
    def __init__(self):
        """Initialize with an empty registry."""
        self._personalities: Dict[str, Type[BasePersonality]] = {}
        self._default_personality_name = "Frinny"  # Default personality name
        self._active_instances: Dict[str, BasePersonality] = {}
    
    def register(self, personality_class: Type[BasePersonality]) -> None:
        """
        Register a personality class.
        
        Args:
            personality_class: A class inheriting from BasePersonality
        """
        # Create a temporary instance to get the name
        temp_instance = personality_class()
        name = temp_instance.name
        
        self._personalities[name] = personality_class
        logger.info(f"Registered personality: {name}")
    
    def get(self, name: Optional[str] = None) -> BasePersonality:
        """
        Get a personality instance by name.
        
        Args:
            name: Name of the personality to retrieve, or None for default
            
        Returns:
            An instance of the requested personality
            
        Raises:
            ValueError: If the requested personality is not registered
        """
        personality_name = name or self._get_default_name()
        
        # Check if we already have an instance
        if personality_name in self._active_instances:
            return self._active_instances[personality_name]
        
        # Get the class and create an instance
        if personality_name not in self._personalities:
            raise ValueError(f"Personality '{personality_name}' not registered")
            
        personality_class = self._personalities[personality_name]
        instance = personality_class()
        
        # Cache the instance
        self._active_instances[personality_name] = instance
        
        return instance
    
    def _get_default_name(self) -> str:
        """
        Get the default personality name.
        First tries environment variable, then fallback to hardcoded default.
        
        Returns:
            Name of the default personality
        """
        return os.environ.get("DEFAULT_PERSONALITY", self._default_personality_name)
    
    def set_default(self, name: str) -> None:
        """
        Set the default personality.
        
        Args:
            name: Name of the personality to set as default
            
        Raises:
            ValueError: If the requested personality is not registered
        """
        if name not in self._personalities:
            raise ValueError(f"Cannot set default: Personality '{name}' not registered")
            
        self._default_personality_name = name
        logger.info(f"Set default personality to: {name}")
    
    def list_personalities(self) -> list:
        """
        List all registered personalities.
        
        Returns:
            List of personality names
        """
        return list(self._personalities.keys())


# Create a singleton registry
_registry = PersonalityRegistry()


def get_personality(name: Optional[str] = None) -> BasePersonality:
    """
    Shorthand function to get a personality from the registry.
    
    Args:
        name: Name of the personality to retrieve, or None for default
        
    Returns:
        An instance of the requested personality
    """
    return _registry.get(name)


# Import and register personalities
# This is done here to avoid circular imports
from app.agent.personalities.frinny import FrinnyPersonality
from app.agent.personalities.gamemaster import GameMasterPersonality

_registry.register(FrinnyPersonality)
_registry.register(GameMasterPersonality) 