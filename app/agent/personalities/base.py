"""
Base personality class for agent system.

This module defines the base interface that all personality implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePersonality(ABC):
    """
    Base class for all agent personalities.
    
    A personality defines system prompts, error messages, and response formats
    that give the agent its unique character and voice.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of this personality."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        The system prompt used to initialize the agent's behavior.
        This defines the core personality and capabilities.
        """
        pass
    
    @property
    def error_message(self) -> str:
        """
        Default error message returned when the agent encounters a problem.
        Can be overridden by specific personalities for custom error handling.
        """
        return "I'm sorry, I encountered a system error. Please try again."
    
    def format_response(self, content: str, event_type: str) -> Dict[str, Any]:
        """
        Format the content for the specific event type.
        This allows personalities to customize how responses are structured.
        
        Args:
            content: The raw content from the agent
            event_type: The type of event (query, character_creation, etc.)
            
        Returns:
            A dictionary with formatted content ready for emission
        """
        # Default implementation just returns the content in the appropriate field
        return {
            "content" if event_type == "query" else "message": content
        }
    
    def __str__(self) -> str:
        return f"{self.name} Personality" 