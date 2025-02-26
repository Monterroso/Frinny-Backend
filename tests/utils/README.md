# Test Utilities

This directory contains shared utilities for testing the application. The organization follows the separation of concerns principle, keeping functional tests separate from implementation tests while sharing common code.

## Structure

- `persistence_utils.py`: Shared utilities for persistence testing
  - `MongoDBHelper`: Helper class for MongoDB operations
  - `send_message()`: Utility function for sending messages to the agent

## Testing Approach

Our testing approach separates concerns into two main categories:

1. **Functional Testing** (`test_state_persistence.py`):
   - Tests the agent's ability to maintain conversation context
   - Focuses on user-level behavior
   - Verifies that the agent remembers information across messages
   - Tests complex scenarios like topic changes and restarts

2. **Implementation Testing** (`test_mongodb_persistence.py`):
   - Tests the MongoDB integration directly
   - Verifies that checkpoints are properly created and retrieved
   - Tests technical aspects of the implementation
   - Focuses on database operations and integrity

This separation allows us to:
- Change the persistence backend without affecting functional tests
- Diagnose issues more precisely (Is it a functional problem or a technical implementation problem?)
- Run more targeted tests when needed

## Running Tests

### Recommended Method: Docker Compose

**This is the preferred approach as MongoDB is only available through Docker in our setup.**

```bash
# Start MongoDB first (required for tests to work)
docker-compose up -d mongodb

# Run functional persistence tests
docker-compose run test-persistence

# Run MongoDB implementation tests
docker-compose run test-mongodb
```

### Alternative: Direct Python Execution

**Note: This method will only work if MongoDB is already running through Docker Compose.**

```bash
# FIRST: Make sure MongoDB is running via Docker Compose
docker-compose up -d mongodb

# Then you can run tests directly
python tests/test_state_persistence.py
python tests/test_mongodb_persistence.py
```

## Common Issues

If tests fail with MongoDB connection errors, the most likely cause is that the MongoDB container is not running. Ensure it's up and running with:

```bash
docker-compose ps
# If MongoDB is not running:
docker-compose up -d mongodb
``` 