import asyncio
import os
import json
import logging
from app.agent.agent import lang_graph_handler
from app.config.logging_config import get_logger, setup_logging

# Set up logging
setup_logging()
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

async def test_state_persistence():
    """
    Test if the agent correctly persists state between messages.
    This test simulates a conversation where later messages reference information
    provided in earlier messages.
    """
    user_id = "persistence-test-user"
    context_id = None
    
    # First message - establish some information
    logger.info("STEP 1: Sending initial message with personal information")
    initial_data = {
        "message": "Hi there! My name is Alex and I really love banana bread.",
        "request_id": "persistence-test-1"
    }
    
    initial_response = await lang_graph_handler.process_event(
        event_type="query",
        data=initial_data,
        user_id=user_id
    )
    
    # Save the context_id for the next message
    context_id = initial_response.get("context_id")
    logger.info(f"Got context_id: {context_id}")
    
    logger.info("\n=== INITIAL RESPONSE ===")
    logger.info(json.dumps(initial_response, indent=2))
    logger.info("=======================\n")
    
    # Second message - ask about character creation (unrelated topic)
    logger.info("STEP 2: Sending message about an unrelated topic")
    second_data = {
        "message": "I'm thinking about creating a dwarf character. What class would you recommend?",
        "request_id": "persistence-test-2",
        "context_id": context_id
    }
    
    second_response = await lang_graph_handler.process_event(
        event_type="query",
        data=second_data,
        user_id=user_id
    )
    
    logger.info("\n=== SECOND RESPONSE ===")
    logger.info(json.dumps(second_response, indent=2))
    logger.info("=======================\n")
    
    # Third message - reference the personal information from the first message
    logger.info("STEP 3: Asking about information shared in the first message")
    third_data = {
        "message": "By the way, what kind of bread did I say I like?",
        "request_id": "persistence-test-3",
        "context_id": context_id
    }
    
    third_response = await lang_graph_handler.process_event(
        event_type="query",
        data=third_data,
        user_id=user_id
    )
    
    logger.info("\n=== THIRD RESPONSE ===")
    logger.info(json.dumps(third_response, indent=2))
    logger.info("=======================\n")
    
    # Check if the response contains "banana bread"
    response_content = third_response.get("content", "")
    if "banana bread" in response_content.lower():
        logger.info("SUCCESS: Agent remembered the user likes banana bread!")
        print("\n✅ SUCCESS: Agent correctly remembered previous information!")
        print(f"Response: {response_content}")
        return True
    else:
        logger.error("FAILURE: Agent did not remember the user likes banana bread")
        print("\n❌ FAILURE: Agent did not remember previous information")
        print(f"Response: {response_content}")
        return False

async def main():
    """Main entry point for the test script."""
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("ERROR: OPENAI_API_KEY environment variable is not set!")
        return 1
    
    print("\n=== TESTING STATE PERSISTENCE ===")
    print("This test will verify if the agent correctly remembers information")
    print("from earlier in the conversation.\n")
    
    try:
        success = await test_state_persistence()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 