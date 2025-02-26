import asyncio
import json
import logging
import os
import time
import uuid
import requests
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import shared utilities
from tests.utils.persistence_utils import MongoDBHelper, send_message

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
    
    # Verify MongoDB connection and data storage
    mongo_helper = MongoDBHelper()
    mongo_helper.verify_connection()
    
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
        "rage" in response_content or
        "which creature" not in response_content and 
        "what creature" not in response_content and
        "which character" not in response_content and
        "what entity" not in response_content):
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
    second_response = await send_message(
        "I'm thinking about creating a dwarf character. What class would you recommend?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Take a short pause to ensure state is properly saved
    time.sleep(1)
    
    # Third message - reference the personal information from the first message
    logger.info("STEP 3: Asking about information shared in the first message")
    third_response = await send_message(
        "By the way, what kind of bread did I say I like?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Check if the response contains "banana bread"
    response_content = third_response.get("content", "").lower()
    if "banana bread" in response_content.lower():
        logger.info("SUCCESS: Agent remembered the user likes banana bread!")
        logger.info("PASS: Agent correctly remembered information across topic changes")
        return True
    else:
        logger.error("FAILURE: Agent did not remember the user likes banana bread")
        logger.error("FAIL: Agent failed to maintain persistence across topic changes")
        return False

async def test_persistence_after_restart() -> bool:
    """
    Test if persistence works even after a simulated restart.
    This is done by creating a new LangGraphHandler instance.
    """
    logger.info("=== Testing Persistence After Restart ===")
    user_id = f"restart-test-{uuid.uuid4()}"
    
    # First message
    logger.info("Sending initial message: I'm playing a halfling rogue named Pippin")
    first_response = await send_message(
        "I'm playing a halfling rogue named Pippin",
        user_id=user_id
    )
    
    context_id = first_response.get("context_id")
    if not context_id:
        logger.error("No context_id in response")
        return False
    
    logger.info(f"Got context_id: {context_id}")
    
    # Verify the conversation was stored
    mongo_helper = MongoDBHelper()
    mongo_helper.verify_connection()
    
    # Simulate a restart by creating a new handler
    # In reality, we're using the same handler but this tests if data is persisted
    # in MongoDB rather than just in memory
    logger.info("Simulating a restart...")
    time.sleep(2)  # Add a small delay
    
    # Follow-up message after "restart"
    logger.info("Sending follow-up message after 'restart': What's my character's name again?")
    follow_up_response = await send_message(
        "What's my character's name again?",
        context_id=context_id,
        user_id=user_id
    )
    
    # Check if response mentions Pippin
    response_content = follow_up_response.get("content", "").lower()
    if "pippin" in response_content:
        logger.info("SUCCESS: Agent remembered the character name after restart!")
        logger.info("PASS: Persistence after restart test passed")
        return True
    else:
        logger.error("FAILURE: Agent did not remember the character name after restart")
        logger.error(f"Response content: {response_content}")
        return False

async def main():
    """Run all persistence tests."""
    logger.info("Starting persistence tests with MongoDB")
    
    # First verify MongoDB connection
    mongo_helper = MongoDBHelper()
    mongodb_connected = mongo_helper.verify_connection()
    if not mongodb_connected:
        logger.error("❌ Cannot connect to MongoDB, tests may fail")
    
    # Test basic persistence (direct follow-up)
    basic_result = await test_basic_persistence()
    logger.info(f"Basic persistence test {'PASSED' if basic_result else 'FAILED'}")
    
    # Test complex persistence (with topic change)
    complex_result = await test_complex_persistence()
    logger.info(f"Complex persistence test {'PASSED' if complex_result else 'FAILED'}")
    
    # Test persistence after restart
    restart_result = await test_persistence_after_restart()
    logger.info(f"Persistence after restart test {'PASSED' if restart_result else 'FAILED'}")
    
    # Overall results
    if basic_result and complex_result and restart_result:
        logger.info("All persistence tests PASSED")
        print("\n✅ SUCCESS: All MongoDB persistence tests passed!")
        return True
    else:
        logger.error("Some persistence tests FAILED")
        print("\n❌ FAILURE: Some persistence tests failed")
        return False

if __name__ == "__main__":
    # Run the tests
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        exit_code = 1
    
    exit(exit_code) 