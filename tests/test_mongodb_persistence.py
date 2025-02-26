import asyncio
import json
import logging
import os
import time
import uuid
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import shared utilities
from tests.utils.persistence_utils import MongoDBHelper, send_message

async def test_mongodb_connection() -> bool:
    """Test if we can connect to MongoDB and verify the database and collection exist."""
    logger.info("=== Testing MongoDB Connection ===")
    try:
        mongo_helper = MongoDBHelper()
        connection_success = mongo_helper.verify_connection()
        
        if connection_success:
            # Get database structure info
            client = mongo_helper.connect()
            db = client[mongo_helper.db_name]
            collections = db.list_collection_names()
            
            logger.info(f"Connected to MongoDB database: {mongo_helper.db_name}")
            logger.info(f"Collections in database: {collections}")
            
            client.close()
            logger.info("MongoDB connection test passed")
        
        return connection_success
    except Exception as e:
        logger.error(f"MongoDB connection test failed: {str(e)}")
        return False

async def test_checkpoint_creation() -> bool:
    """Test if a new conversation creates a checkpoint in MongoDB."""
    logger.info("=== Testing Checkpoint Creation ===")
    
    # Generate a unique user ID for this test
    test_user_id = f"mongodb-test-{uuid.uuid4()}"
    
    # Get initial checkpoint count
    mongo_helper = MongoDBHelper()
    initial_checkpoint_ids = mongo_helper.get_checkpoint_ids()
    logger.info(f"Initial checkpoint count: {len(initial_checkpoint_ids)}")
    
    # Send a message to create a new conversation
    logger.info(f"Sending message as user {test_user_id}")
    response = await send_message(
        "Hello, this is a test message for MongoDB persistence",
        user_id=test_user_id
    )
    
    # Get the context_id from the response
    context_id = response.get("context_id")
    if not context_id:
        logger.error("No context_id returned in response")
        return False
    
    # The checkpoint_id should be user_id:context_id
    checkpoint_id = f"{test_user_id}:{context_id}"
    logger.info(f"Expected checkpoint_id: {checkpoint_id}")
    
    # Check if a new checkpoint was created
    time.sleep(1)  # Allow time for async operations to complete
    updated_checkpoint_ids = mongo_helper.get_checkpoint_ids()
    
    # Look for checkpoints related to our test user
    user_checkpoints = mongo_helper.get_checkpoints_for_user(test_user_id)
    logger.info(f"Found {len(user_checkpoints)} checkpoints for test user")
    
    if len(user_checkpoints) > 0:
        logger.info("✅ Successfully created checkpoint in MongoDB")
        return True
    else:
        logger.error("❌ Failed to create checkpoint in MongoDB")
        return False

async def test_checkpoint_retrieval() -> bool:
    """Test if we can retrieve a conversation checkpoint and continue it."""
    logger.info("=== Testing Checkpoint Retrieval ===")
    
    # Generate a unique user ID for this test
    test_user_id = f"mongodb-retrieval-{uuid.uuid4()}"
    
    # Start a conversation with unique information
    unique_fruit = f"starfruit-{uuid.uuid4()}"
    logger.info(f"Sending initial message with unique information: {unique_fruit}")
    
    first_response = await send_message(
        f"My favorite fruit is {unique_fruit}",
        user_id=test_user_id
    )
    
    context_id = first_response.get("context_id")
    if not context_id:
        logger.error("No context_id returned in response")
        return False
        
    logger.info(f"Got context_id: {context_id}")
    
    # Wait briefly to ensure the checkpoint is saved
    time.sleep(2)
    
    # Now continue the conversation and ask about the unique information
    logger.info("Sending follow-up message to test retrieval")
    follow_up_response = await send_message(
        "What fruit did I say I like?",
        context_id=context_id,
        user_id=test_user_id
    )
    
    # Check if the response contains our unique fruit
    response_content = follow_up_response.get("content", "").lower()
    if unique_fruit.lower() in response_content:
        logger.info(f"✅ Successfully retrieved the unique information '{unique_fruit}' from MongoDB")
        return True
    else:
        logger.error(f"❌ Failed to retrieve the unique information from MongoDB")
        logger.error(f"Response did not contain '{unique_fruit}'")
        return False

async def main():
    """Run all MongoDB persistence tests."""
    logger.info("Starting MongoDB persistence tests")
    
    # Test MongoDB connection
    connection_result = await test_mongodb_connection()
    logger.info(f"MongoDB connection test {'PASSED' if connection_result else 'FAILED'}")
    
    if not connection_result:
        logger.error("Cannot continue tests without MongoDB connection")
        return False
    
    # Test checkpoint creation
    creation_result = await test_checkpoint_creation()
    logger.info(f"Checkpoint creation test {'PASSED' if creation_result else 'FAILED'}")
    
    # Test checkpoint retrieval
    retrieval_result = await test_checkpoint_retrieval()
    logger.info(f"Checkpoint retrieval test {'PASSED' if retrieval_result else 'FAILED'}")
    
    # Overall results
    if connection_result and creation_result and retrieval_result:
        logger.info("All MongoDB persistence tests PASSED")
        print("\n✅ SUCCESS: All MongoDB persistence tests passed!")
        return True
    else:
        logger.error("Some MongoDB persistence tests FAILED")
        print("\n❌ FAILURE: Some MongoDB persistence tests failed")
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