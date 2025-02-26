# Testing Strategy

This document outlines the testing strategy for the application, with a focus on persistence testing.

## Persistence Testing

We use a layered approach to test the persistence functionality, separating concerns to ensure comprehensive coverage while maintaining code organization.

### Approach

Our persistence testing is divided into two main categories:

1. **Functional Testing** (`test_state_persistence.py`):
   - Tests the agent's ability to maintain conversation context
   - Focus on user experience and behavior
   - Verifies proper handling of conversation contexts
   - Tests complex scenarios like topic changes

2. **Implementation Testing** (`test_mongodb_persistence.py`):
   - Tests the MongoDB integration specifically
   - Verifies that checkpoints are properly created and retrieved
   - Tests technical details of the implementation

This separation allows us to change the persistence backend (e.g., from SQLite to MongoDB) without affecting the functional tests, as long as the behavior remains the same.

### Shared Utilities

We use shared utilities for common testing functionality:

- `tests/utils/persistence_utils.py`: Contains helpers for MongoDB operations and message sending
  - `MongoDBHelper`: A class for MongoDB operations during testing
  - `send_message()`: A utility function for sending messages to the agent

### Key Test Cases

1. **Basic Persistence**:
   - Tests if the agent remembers context in a simple conversation
   - Sends a message about a topic, then asks a follow-up

2. **Complex Persistence**:
   - Tests if the agent remembers information across topic changes
   - Introduces personal information, changes topic, then references earlier information

3. **Persistence After Restart**:
   - Tests if the agent can recover state after a restart
   - Simulates a restart by creating a delay between messages
   
4. **MongoDB Connection**:
   - Verifies connectivity to MongoDB
   - Checks database and collection existence

5. **Checkpoint Creation**:
   - Tests if new conversations create proper checkpoints in MongoDB
   - Verifies checkpoint structure

6. **Checkpoint Retrieval**:
   - Tests if checkpoints can be properly retrieved
   - Uses a unique identifier to ensure accurate retrieval

## Running Tests

### Preferred Method: Using Docker Compose

**This is the recommended approach as MongoDB is only available through Docker in our setup.**

```bash
# Start MongoDB first (required for tests to work)
docker-compose up -d mongodb

# Run all tests
docker-compose run test-persistence
docker-compose run test-mongodb

# For a full environment build and test
docker-compose build && docker-compose up -d mongodb
docker-compose run test-persistence
docker-compose run test-mongodb
```

### Alternative: Directly with Python

**Note: This method will only work if MongoDB is already running through Docker Compose.** Running tests directly with Python without first starting the MongoDB container will result in connection failures.

```bash
# FIRST: Make sure MongoDB is running via Docker Compose
docker-compose up -d mongodb

# Then you can run tests directly
python tests/test_state_persistence.py
python tests/test_mongodb_persistence.py
```

## Troubleshooting

If tests fail, check the following:

1. MongoDB connection issues:
   - **Most common issue**: Verify MongoDB container is running: `docker-compose ps`
   - If MongoDB is not running, start it with: `docker-compose up -d mongodb`
   - Check MongoDB logs: `docker-compose logs mongodb`
   - Verify connection string in .env file

2. Agent response issues:
   - Examine the agent's response content in the test output
   - Check if the context is properly maintained
   - Look for error messages or unexpected responses

3. Environment issues:
   - Make sure environment variables are properly set in docker-compose.yml
   - Verify Docker services are running correctly
   - Ensure network connections between services are working 