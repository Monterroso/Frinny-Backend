# Agent Testing

This directory contains scripts for testing the LangGraph agent in isolation from the rest of the application.

## Available Test Scripts

### 1. `test_agent.py`

Runs a comprehensive set of predefined tests against the agent, covering different types of queries and testing context retention.

```bash
# Run with docker-compose
docker-compose run --rm test-agent python tests/test_agent.py

# Run locally (if Python environment is set up)
python tests/test_agent.py
```

### 2. `test_agent_interactive.py`

Provides an interactive shell for testing the agent with custom queries. This is useful for ad-hoc testing and debugging.

```bash
# Run interactive mode with docker-compose
docker-compose run --rm test-agent python tests/test_agent_interactive.py --interactive

# Send a single message
docker-compose run --rm test-agent python tests/test_agent_interactive.py --message "How does the Frightened condition work?"

# Specify event type
docker-compose run --rm test-agent python tests/test_agent_interactive.py --message "My wizard is surrounded by goblins" --event-type combat_turn
```

## Interactive Mode Commands

When running in interactive mode, the following commands are available:

- `exit` - Exit the interactive session
- `help` - Show help message
- `clear` - Clear the conversation context
- `event <type>` - Change event type (query, combat_turn, level_up, character_creation)
- `user <id>` - Change user ID

## Environment Variables

Make sure your `.env` file contains the necessary environment variables:

```
OPENAI_API_KEY=your_api_key_here
```

## Docker Compose Configuration

The `test-agent` service in `docker-compose.yml` is configured to run these test scripts. You can modify the command in the docker-compose file to run a specific test script by default. 