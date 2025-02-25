import asyncio
import os
import json
import logging
from app.agent.agent import lang_graph_handler
from app.config.logging_config import get_logger

# Set up logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

async def test_rules_query():
    """Test a basic rules query to the agent."""
    test_data = {
        "message": "How does the Frightened condition work in Pathfinder 2E?",
        "request_id": "test-rules-123"
    }
    
    user_id = "test-user-1"
    event_type = "query"
    
    logger.info(f"Sending rules query to agent: {test_data['message']}")
    
    response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=test_data,
        user_id=user_id
    )
    
    logger.info("\n=== RULES QUERY RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("============================\n")
    
    return response

async def test_combat_advice():
    """Test a combat advice query to the agent."""
    test_data = {
        "message": "My wizard is surrounded by three goblins, what should I do?",
        "request_id": "test-combat-123"
    }
    
    user_id = "test-user-2"
    event_type = "combat_turn"
    
    logger.info(f"Sending combat query to agent: {test_data['message']}")
    
    response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=test_data,
        user_id=user_id
    )
    
    logger.info("\n=== COMBAT ADVICE RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("==============================\n")
    
    return response

async def test_level_up_advice():
    """Test a level up advice query to the agent."""
    test_data = {
        "message": "My ranger just reached level 6, what should I take?",
        "request_id": "test-levelup-123"
    }
    
    user_id = "test-user-3"
    event_type = "level_up"
    
    logger.info(f"Sending level up query to agent: {test_data['message']}")
    
    response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=test_data,
        user_id=user_id
    )
    
    logger.info("\n=== LEVEL UP ADVICE RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("================================\n")
    
    return response

async def test_context_retention():
    """Test the agent's ability to retain context across multiple messages."""
    # First message
    initial_data = {
        "message": "I want to build a rogue that's good at intimidation.",
        "request_id": "test-context-123"
    }
    
    user_id = "test-user-4"
    event_type = "query"
    
    logger.info(f"Sending initial query to agent: {initial_data['message']}")
    
    initial_response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=initial_data,
        user_id=user_id
    )
    
    logger.info("\n=== INITIAL RESPONSE ===")
    logger.info(json.dumps(initial_response, indent=2))
    logger.info("=======================\n")
    
    # Follow-up message using the same context
    follow_up_data = {
        "message": "What ancestry would work best with this build?",
        "request_id": "test-context-124",
        "context_id": initial_response.get("context_id")  # Use the same context from previous response
    }
    
    logger.info(f"Sending follow-up query: {follow_up_data['message']}")
    
    follow_up_response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=follow_up_data,
        user_id=user_id
    )
    
    logger.info("\n=== FOLLOW-UP RESPONSE ===")
    logger.info(json.dumps(follow_up_response, indent=2))
    logger.info("==========================\n")
    
    return initial_response, follow_up_response

async def run_all_tests():
    """Run all test cases."""
    logger.info("Starting LangGraph agent tests...")
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("ERROR: OPENAI_API_KEY environment variable is not set!")
        return False
    
    try:
        # Run all tests
        await test_rules_query()
        await test_combat_advice()
        await test_level_up_advice()
        await test_context_retention()
        
        logger.info("All tests completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error during tests: {str(e)}")
        return False

if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1) 