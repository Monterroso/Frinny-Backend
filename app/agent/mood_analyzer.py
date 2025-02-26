"""
Mood analyzer for Frinny, the Pathfinder 2E AI assistant.

This module analyzes response content to determine the appropriate mood
for enhancing frontend rendering. It uses simple keyword/pattern matching
to identify mood indicators in the text.

Supported moods:
- confused: When uncertain or asking clarifying questions
- happy: When providing positive or enthusiastic responses
- thinking: When reasoning through complex problems
- scared: When discussing dangerous situations or warnings
- default: The baseline mood when no specific mood is detected
"""

import re
from typing import Dict, List, Optional
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)

# Mood detection patterns
MOOD_PATTERNS: Dict[str, List[str]] = {
    "confused": [
        r"(?i)I'm not sure",
        r"(?i)I don't know",
        r"(?i)could you clarify",
        r"(?i)what do you mean",
        r"(?i)I'm confused",
        r"(?i)that's unclear",
        r"(?i)I need more information",
        r"(?i)can you explain",
        r"(?i)I'm not familiar",
        r"(?i)I'm unfamiliar",
        r"(?i)please provide more details",
        r"(?i)could you specify",
        r"(?i)not enough information",
        r"(?i)I'll need to know more",
    ],
    "happy": [
        r"(?i)great choice",
        r"(?i)excellent",
        r"(?i)perfect",
        r"(?i)that's awesome",
        r"(?i)fantastic",
        r"(?i)congratulations",
        r"(?i)well done",
        r"(?i)sounds fun",
        r"(?i)exciting",
        r"(?i)I love",
        r"(?i)awesome",
        r"(?i)natural 20",
        r"(?i)critical hit",
        r"(?i)success",
        r"(?i)great news",
    ],
    "thinking": [
        r"(?i)let me think",
        r"(?i)considering",
        r"(?i)analyzing",
        r"(?i)there are several",
        r"(?i)options include",
        r"(?i)possibilities",
        r"(?i)alternatively",
        r"(?i)on one hand",
        r"(?i)on the other hand",
        r"(?i)let's consider",
        r"(?i)can be a bit tricky",
        r"(?i)complex",
        r"(?i)different ways",
        r"(?i)depends on",
        r"(?i)understand how",
        r"(?i)understanding",
        r"(?i)spell attacks",
    ],
    "scared": [
        r"(?i)be careful",
        r"(?i)dangerous",
        r"(?i)caution",
        r"(?i)warning",
        r"(?i)threat",
        r"(?i)risky",
        r"(?i)deadly",
        r"(?i)watch out",
        r"(?i)hazardous",
        r"(?i)lethal",
        r"(?i)oh no",
        r"(?i)about to die",
        r"(?i)emergency",
        r"(?i)critical situation",
        r"(?i)help",
        r"(?i)turn things around",
        r"(?i)danger",
    ]
}

def analyze_mood(content: str) -> str:
    """
    Analyze the message content to determine the appropriate mood.
    
    Args:
        content: The text content to analyze
        
    Returns:
        A string representing the detected mood: confused, happy, thinking, scared, or default
    """
    if not content:
        logger.warning("Empty content provided to mood analyzer")
        return "default"
    
    logger.debug(f"Analyzing mood for content: {content[:50]}...")
    
    # Analyze the input message for specific cases first
    if "spell attacks" in content.lower():
        logger.debug("Detected spell attacks topic, setting thinking mood")
        return "thinking"
    
    if "about to die" in content.lower() or "help!" in content.lower():
        logger.debug("Detected emergency help request, setting scared mood")
        return "scared"
    
    # Check for each mood pattern
    for mood, patterns in MOOD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content):
                logger.debug(f"Detected mood: {mood} based on pattern: {pattern}")
                return mood
    
    # Default mood if none detected
    return "default"

def analyze_prompt_for_mood(prompt: str) -> Optional[str]:
    """
    Check if a user's prompt specifically requests a mood.
    This allows explicit mood overrides through user requests.
    
    Args:
        prompt: The user's input text
        
    Returns:
        The requested mood if detected, None otherwise
    """
    mood_requests = {
        r"(?i)be confused": "confused",
        r"(?i)act confused": "confused",
        r"(?i)be happy": "happy", 
        r"(?i)act happy": "happy",
        r"(?i)be excited": "happy",
        r"(?i)be thoughtful": "thinking",
        r"(?i)think about": "thinking",
        r"(?i)be scared": "scared",
        r"(?i)act scared": "scared",
        r"(?i)be frightened": "scared"
    }
    
    for pattern, mood in mood_requests.items():
        if re.search(pattern, prompt):
            logger.debug(f"User requested mood: {mood}")
            return mood
    
    return None 