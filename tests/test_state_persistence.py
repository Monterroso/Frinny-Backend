import asyncio
import json
import logging
import os
import time
import uuid
from typing import Dict, Optional

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Setup common test constants
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5001")
API_ENDPOINT = f"{API_BASE_URL}/api/agent/process"

async def send_message(message: str, context_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
    """
    Send a message to the agent and return the response.
    
    Args:
        message: Message text to send
        context_id: Optional context ID for continuing a conversation
        user_id: Optional user ID
        
    Returns:
        Response from the agent
    """
    if not user_id:
        user_id = f"test-{uuid.uuid4()}"
        
    request_data = {
        "request_id": f"test-{uuid.uuid4()}",
        "message": message,
        "user_id": user_id,
        "event_type": "query"
    }
    
    # Add context_id if provided
    if context_id:
        request_data["context_id"] = context_id
    
    # Use direct function call to agent.py rather than HTTP request for testing
    from app.agent.agent import LangGraphHandler
    
    # Initialize the agent handler
    handler = LangGraphHandler()
    
    # Process the query through the agent
    response = await handler.process_event("query", request_data, user_id)
    
    # Log the agent's response
    logger.info("\n=== AGENT RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("=====================\n")
    
    return response

async def test_basic_persistence() -> bool:
    """
    Test if the agent correctly persists state between related messages.
    This simulates asking about a topic and then following up with a 
    related question.
    """
    logger.info("=== Testing Basic Conversation Persistence ===")
    user_id = f"basic-persistence-test-{uuid.uuid4()}"
    
    # First message
    logger.info("Sending message to agent: Tell me about the Barbarian class in Pathfinder 2E")
    first_response = await send_message(
        "Tell me about the Barbarian class in Pathfinder 2E",
        user_id=user_id
    )
    
    # Extract context_id for the follow-up
    context_id = first_response.get("context_id")
    if not context_id:
        logger.error("No context_id in response")
        return False
    
    logger.info(f"Got context_id: {context_id} for conversation")
    
    # Follow-up question
    logger.info("Sending message to agent: What are their special abilities?")
    follow_up_response = await send_message(
        "What are their special abilities?",
        context_id=context_id,
        user_id=user_id
    )
    
    # If the agent remembered we were talking about Barbarians, it should provide
    # information about Barbarian abilities or ask for clarification about "their",
    # but not ask "whose special abilities?"
    response_content = follow_up_response.get("content", "").lower()
    
    if ("barbarian" in response_content or 
        "which creature" in response_content or 
        "what creature" in response_content or
        "which character" in response_content or
        "what entity" in response_content):
        logger.info("PASS: Response showed basic contextual understanding")
        logger.info("Basic persistence test PASSED")
        return True
    else:
        logger.error("FAIL: Response did not show contextual understanding")
        logger.error(f"Response content: {response_content}")
        return False

async def test_complex_persistence() -> bool:
    """
    Test if the agent correctly persists state between messages with topic changes.
    This test simulates a conversation where later messages reference information
    provided in earlier messages, even after discussing unrelated topics.
    """
    user_id = f"complex-persistence-test-{uuid.uuid4()}"
    context_id = None
    
    # First message - establish some information
    logger.info("STEP 1: Sending initial message with personal information")
    initial_response = await send_message(
        "Hi there! My name is Alex and I really love banana bread.",
        user_id=user_id
    )
    
    # Save the context_id for the next message
    context_id = initial_response.get("context_id")
    if not context_id:
        logger.error("No context_id returned in first response")
        return False
        
    logger.info(f"Got context_id: {context_id}")
    
    # Second message - ask about character creation (unrelated topic)
    logger.info("STEP 2: Sending message about an unrelated topic")
    await send_message(
        "I'm thinking about creating a dwarf character. What class would you recommend?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Third message - reference the personal information from the first message
    logger.info("STEP 3: Asking about information shared in the first message")
    third_response = await send_message(
        "By the way, what kind of bread did I say I like?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Check if the response contains "banana bread"
    response_content = third_response.get("content", "")
    if "banana bread" in response_content.lower():
        logger.info("SUCCESS: Agent remembered the user likes banana bread!")
        logger.info("PASS: Agent correctly remembered information across topic changes")
        return True
    else:
        logger.error("FAILURE: Agent did not remember the user likes banana bread")
        logger.error("FAIL: Agent failed to maintain persistence across topic changes")
        return False

# Async main function to ensure we have a running event loop
async def main():
    """Run all persistence tests."""
    logger.info("Starting persistence tests")
    
    # Initialize asyncio event loop
    loop = asyncio.get_event_loop()
    
    # Test basic persistence (direct follow-up)
    basic_result = await test_basic_persistence()
    logger.info(f"Basic persistence test {'PASSED' if basic_result else 'FAILED'}")
    
    # Test complex persistence (with topic change)
    complex_result = await test_complex_persistence()
    logger.info(f"Complex persistence test {'PASSED' if complex_result else 'FAILED'}")
    
    # Overall results
    if basic_result and complex_result:
        logger.info("All persistence tests PASSED")
        print("\n✅ SUCCESS: All persistence tests passed!")
    else:
        logger.error("Some persistence tests FAILED")
        print("\n❌ FAILURE: Some persistence tests failed")
    
    return basic_result and complex_result

if __name__ == "__main__":
    # Properly set up asyncio and run with proper event loop
    try:
        policy = asyncio.get_event_loop_policy()
        loop = policy.get_event_loop()
        exit_code = 0 if loop.run_until_complete(main()) else 1
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        exit_code = 1
    
    exit(exit_code) 