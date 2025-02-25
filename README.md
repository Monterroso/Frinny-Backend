# Pathfinder 2E Assistant with LangGraph

This project implements an intelligent assistant for Pathfinder 2E using LangGraph and OpenAI's GPT models. The assistant can answer rules questions, provide combat advice, help with character creation and leveling, and reference adventure content.

## Features

- **Natural Conversation**: Maintains context across messages for natural, flowing conversations
- **Specialized Tools**: Includes tools for rules lookup, combat analysis, character advancement, and adventure reference
- **Personality**: Friendly, enthusiastic personality with game-specific knowledge
- **WebSocket Integration**: Seamlessly integrates with the existing WebSocket backend

## Architecture

The implementation uses LangGraph to create a graph of components:

1. **Context Classification**: Determines if a message continues an existing conversation or starts a new one
2. **Chatbot**: Processes messages and generates responses using OpenAI's GPT models
3. **Tools**: Specialized tools for different aspects of the game
4. **Memory**: Persistent storage of conversation contexts

## Implementation Details

### Core Components

- `agent.py`: Implements the LangGraph agent with context management and tool integration
- `tools.py`: Implements specialized tools for Pathfinder 2E
- `languages/`: Contains localization files for UI elements and terminology

### Information Flow

1. User sends a message via WebSocket
2. Message is processed through the LangGraph
3. Tools are used as needed based on message content
4. Response is generated with the assistant's personality
5. Response is sent back to the user via WebSocket

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Run the application:
   ```
   python run.py
   ```

## Future Enhancements

- Implement actual functionality for the tools (currently using placeholders)
- Add more sophisticated context management with OpenAI-based scoring
- Expand the knowledge base with more Pathfinder 2E content
- Add support for additional languages 