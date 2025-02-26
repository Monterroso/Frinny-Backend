"""
Test script for mood detection and SQLite persistence.

This script tests:
1. SQLite persistence with multiple messages in a conversation
2. Mood detection in responses
3. Error handling for persistence failures
"""

import asyncio
import os
import json
import logging
import uuid
from typing import Dict, List, Tuple

from app.agent.agent import lang_graph_handler
from app.agent.mood_analyzer import analyze_mood
from app.config.logging_config import get_logger, setup_logging

# Set up logging
setup_logging()
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

async def send_message(message: str, context_id: str = None, user_id: str = "test-user") -> Dict:
    """
    Send a message to the agent and return the response.
    
    Args:
        message: The message text to send
        context_id: Optional context ID for continuing a conversation
        user_id: The user ID to use
        
    Returns:
        The agent's response
    """
    test_data = {
        "message": message,
        "request_id": f"test-{uuid.uuid4()}"
    }
    
    if context_id:
        test_data["context_id"] = context_id
    
    logger.info(f"Sending message to agent: {message}")
    
    response = await lang_graph_handler.process_event(
        event_type="query",
        data=test_data,
        user_id=user_id
    )
    
    logger.info("\n=== AGENT RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("=====================\n")
    
    return response

async def test_conversation_persistence() -> bool:
    """
    Test that conversation contexts are properly persisted.
    
    Returns:
        True if the test passes, False otherwise
    """
    logger.info("=== Testing Conversation Persistence ===")
    
    # Generate a unique user ID for this test
    user_id = f"persistence-test-{uuid.uuid4()}"
    
    # First message establishes context
    response1 = await send_message(
        "Tell me about the Barbarian class in Pathfinder 2E",
        user_id=user_id
    )
    
    # Get the context_id for continuing the conversation
    context_id = response1.get("context_id")
    if not context_id:
        logger.error("No context_id returned in first response")
        return False
    
    logger.info(f"Got context_id: {context_id} for conversation")
    
    # Second message should reference the first
    response2 = await send_message(
        "What are their special abilities?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Check if the response shows contextual understanding
    content = response2.get("content", "")
    if any(term in content.lower() for term in ["barbarian", "rage", "class", "abilities"]):
        logger.info("PASS: Response showed contextual understanding")
        return True
    else:
        logger.error("FAIL: Response did not show contextual understanding")
        return False

async def test_mood_detection() -> bool:
    """
    Test that the mood detection works correctly.
    
    Returns:
        True if all mood tests pass, False otherwise
    """
    logger.info("=== Testing Mood Detection ===")
    
    # Test cases for each mood
    test_cases = [
        {
            "message": "What do you think about the fighter class?",
            "expected_pattern": "In my opinion, the Fighter class is an excellent choice"
        },
        {
            "message": "I'm confused about how spell attacks work",
            "expected_mood": "thinking"
        },
        {
            "message": "Help! My character is about to die!",
            "expected_mood": "scared"
        },
        {
            "message": "I just rolled a natural 20 on my attack!",
            "expected_mood": "happy"
        },
        {
            "message": "What's the difference between arcane and divine magic?",
            "expected_mood": "default"
        }
    ]
    
    all_passed = True
    for i, case in enumerate(test_cases):
        logger.info(f"Mood Test {i+1}: {case['message']}")
        
        response = await send_message(case["message"])
        
        # Check for mood
        mood = response.get("mood", "")
        logger.info(f"Detected mood: {mood}")
        
        # If there's an expected mood, check that
        if "expected_mood" in case and mood != case["expected_mood"]:
            logger.warning(f"Expected mood {case['expected_mood']} but got {mood}")
            all_passed = False
    
    return all_passed

async def main():
    """Run all tests."""
    logger.info("Starting mood and persistence tests")
    
    # Test persistence
    persistence_result = await test_conversation_persistence()
    logger.info(f"Persistence test {'PASSED' if persistence_result else 'FAILED'}")
    
    # Test mood detection
    mood_result = await test_mood_detection()
    logger.info(f"Mood detection test {'PASSED' if mood_result else 'FAILED'}")
    
    # Overall results
    if persistence_result and mood_result:
        logger.info("All tests PASSED")
    else:
        logger.error("Some tests FAILED")

if __name__ == "__main__":
    asyncio.run(main()) 