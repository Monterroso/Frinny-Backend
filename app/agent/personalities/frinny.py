"""
Frinny personality implementation.

This module defines the Frinny personality, a helpful Pathfinder 2E assistant.
"""
from typing import Dict, Any
from app.agent.personalities.base import BasePersonality


class FrinnyPersonality(BasePersonality):
    """
    Frinny: A helpful Pathfinder 2E assistant.
    
    Frinny is knowledgeable about Pathfinder 2E rules and provides
    concise, clear answers to player questions.
    """
    
    @property
    def name(self) -> str:
        return "Frinny"
    
    @property
    def system_prompt(self) -> str:
        return """You are Frinny, a helpful Pathfinder 2E assistant.
You have access to tools that can help you answer questions about the Pathfinder 2E game system.
Use these tools whenever appropriate to provide accurate information.
Be concise and clear in your answers.
"""
    
    @property
    def error_message(self) -> str:
        return "I'm sorry, I'm having trouble accessing my knowledge of Pathfinder rules. Please try asking in a different way or try again later."
    
    def format_response(self, content: str, event_type: str) -> Dict[str, Any]:
        """Format response with Frinny's personality touches."""
        # Example of how to add personality-specific formatting
        # For now, just use the base implementation
        return super().format_response(content, event_type) 