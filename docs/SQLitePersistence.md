# SQLite Persistence for LangGraph

## Overview

This document describes the implementation of SQLite-based state persistence for our LangGraph agent. We've transitioned from Redis to SQLite for improved simplicity, reliability, and portability.

## Implementation Details

### Dependencies

We've added the `langgraph-checkpoint-sqlite` package to our requirements.txt:

```
langgraph-checkpoint-sqlite>=1.0.0
```

### Configuration

The SQLite database path is configured via environment variables:

- `SQLITE_DB_PATH`: Path to the SQLite database file (default: "agent_state.db")

This can be set in your `.env` file or in the Docker environment.

### Integration with LangGraph

SQLite persistence is implemented in `app/agent/agent.py` with the following components:

1. **Import SQLiteSaver**:
   ```python
   from langgraph.checkpoint.sqlite import SqliteSaver
   ```

2. **Initialize Persistence**:
   ```python
   db_path = os.environ.get("SQLITE_DB_PATH", "agent_state.db")
   try:
       # Try to use SQLite persistence
       memory = SqliteSaver.from_conn_string(db_path)
   except Exception as e:
       # Fall back to MemorySaver if there's an issue with SQLite
       logger.warning(f"Failed to initialize SQLite persistence: {str(e)}")
       memory = MemorySaver()
   ```

3. **Compile Graph with Checkpointer**:
   ```python
   graph = graph_builder.compile(checkpointer=memory)
   ```

## Docker Configuration

In `docker-compose.yml`, we've configured:

1. **Volume for Data Persistence**:
   ```yaml
   volumes:
     - sqlite_data:/app/data
   ```

2. **Environment Variable**:
   ```yaml
   environment:
     - SQLITE_DB_PATH=/app/data/agent_state.db
   ```

## Benefits of SQLite

1. **Simplicity**: SQLite is a self-contained, serverless database that doesn't require a separate service.
2. **Reliability**: Data is persisted to disk, ensuring conversation history survives service restarts.
3. **Portability**: The database is a single file that can be easily backed up or transferred.
4. **Performance**: Efficient for the scale of our application with low overhead.
5. **No External Dependencies**: Eliminates dependency on Redis or other database services.

## Error Handling

Our implementation includes graceful fallback to in-memory storage if SQLite initialization fails:

```python
try:
    memory = SqliteSaver.from_conn_string(db_path)
except Exception as e:
    logger.warning(f"Failed to initialize SQLite persistence: {str(e)}")
    memory = MemorySaver()
```

This ensures the service remains operational even if there are issues with the database.

## Backup Recommendations

We recommend regular backups of the SQLite database file. This can be accomplished with:

1. **Simple File Copy**: Copy the database file when the service is not running.
2. **SQLite Backup API**: Use SQLite's backup API for hot backups.
3. **Volume Backups**: If using Docker, back up the entire volume.

A simple backup script might look like:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /path/to/data/agent_state.db /path/to/backups/agent_state_$DATE.db
```

## Testing

The SQLite persistence implementation is tested in `tests/test_mood_and_persistence.py`, which verifies:

1. Conversation context is maintained across multiple messages
2. State is properly persisted and can be retrieved
3. The system gracefully handles database errors 