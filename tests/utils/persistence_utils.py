import asyncio
import json
import logging
import os
import time
import uuid
import pymongo
from typing import Dict, Optional, List

# Configure logging for utilities
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import the LangGraphHandler directly
from app.agent.agent import lang_graph_handler

class MongoDBHelper:
    """Helper class for MongoDB operations during testing."""
    
    def __init__(self):
        self.mongodb_uri = os.environ.get("MONGODB_URI")
        self.db_name = os.environ.get("MONGODB_DATABASE")
        self.collection_name = "agent_state"
        
    def connect(self) -> pymongo.MongoClient:
        """Create a connection to MongoDB Atlas."""
        try:
            # Use a longer timeout for Atlas connections
            client = pymongo.MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test connection
            client.admin.command('ping')
            return client
        except Exception as e:
            logger.error(f"Error connecting to MongoDB Atlas: {str(e)}")
            raise
            
    def get_checkpoint_ids(self) -> List[str]:
        """Get a list of all checkpoint_ids in the database."""
        client = self.connect()
        try:
            db = client[self.db_name]
            collection = db[self.collection_name]
            # Find all distinct checkpoint_ids
            checkpoint_ids = collection.distinct("checkpoint_id")
            return checkpoint_ids
        except Exception as e:
            logger.error(f"Error getting checkpoint IDs: {str(e)}")
            return []
        finally:
            client.close()
            
    def get_checkpoints_for_user(self, user_id: str) -> List[Dict]:
        """Get all checkpoints for a specific user."""
        client = self.connect()
        try:
            db = client[self.db_name]
            collection = db[self.collection_name]
            # Find all checkpoints containing the user_id in the checkpoint_id field
            checkpoints = list(collection.find({"checkpoint_id": {"$regex": user_id}}))
            return checkpoints
        except Exception as e:
            logger.error(f"Error getting checkpoints for user {user_id}: {str(e)}")
            return []
        finally:
            client.close()
            
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint from MongoDB."""
        client = self.connect()
        try:
            db = client[self.db_name]
            collection = db[self.collection_name]
            result = collection.delete_many({"checkpoint_id": checkpoint_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting checkpoint {checkpoint_id}: {str(e)}")
            return False
        finally:
            client.close()
    
    def verify_connection(self) -> bool:
        """
        Verify that we can connect to MongoDB Atlas and the collection exists.
        Returns True if connection was successful, False otherwise.
        """
        if not self.mongodb_uri:
            logger.error("MONGODB_URI environment variable not set")
            return False
        
        try:
            # Connect to MongoDB Atlas and verify connection
            logger.info(f"Connecting to MongoDB Atlas")
            client = self.connect()
            
            # Check if database and collection exist
            db = client[self.db_name]
            collections = db.list_collection_names()
            
            if self.collection_name in collections:
                # Count documents in the collection
                doc_count = db[self.collection_name].count_documents({})
                logger.info(f"✅ Collection '{self.collection_name}' exists with {doc_count} documents")
            else:
                logger.info(f"Collection '{self.collection_name}' does not exist yet (will be created on first use)")
            
            # Insert and retrieve a test document to fully verify functionality
            test_collection = db["connection_test"]
            test_id = f"test_{uuid.uuid4()}"
            test_collection.insert_one({"_id": test_id, "timestamp": time.time()})
            retrieved = test_collection.find_one({"_id": test_id})
            
            if retrieved:
                logger.info("✅ Successfully inserted and retrieved test document")
                # Clean up test document
                test_collection.delete_one({"_id": test_id})
            else:
                logger.warning("⚠️ Could not insert/retrieve test document")
            
            client.close()
            logger.info("✅ Successfully connected to MongoDB Atlas")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB Atlas: {str(e)}")
            return False

async def send_message(message: str, context_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict:
    """
    Send a message directly to the LangGraphHandler and return the response.
    
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
        "message": message,
        "request_id": f"test-{uuid.uuid4()}"
    }
    
    # Add context_id if provided
    if context_id:
        request_data["context_id"] = context_id
    
    try:
        # Call the LangGraphHandler directly
        result = await lang_graph_handler.process_event("query", request_data, user_id)
        
        # Log the agent's response
        logger.info("\n=== AGENT RESPONSE ===")
        logger.info(json.dumps(result, indent=2))
        logger.info("=====================\n")
        
        return result
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        # Return a minimal error response
        return {
            "status": "error",
            "error": str(e),
            "content": f"Error occurred: {str(e)}"
        } 