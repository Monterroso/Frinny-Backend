# LangGraph Integration - Implementation Guide

## Overview
This document outlines the integration of LangGraph with our SocketIO backend to create an intelligent assistant for Pathfinder 2E. We will be using OpenAI's GPT models for the LLM component.

## Core System Flow
1. **Event Reception**: Receive events from frontend (combat actions, queries, etc.)
2. **Context Classification**: Determine if this is a new context or continues an existing one
3. **Agent Processing**: Use tools and context to generate appropriate responses
4. **Response Personalization**: Format the response according to bot's personality

## Implementation Structure
Our implementation will follow a structure similar to this example:

```python
from typing import Annotated
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI  # Using OpenAI for our LLM

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    context_id: str

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model="gpt-4o",  # Using GPT-4o model
    temperature=0.2,
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Create graph builder
graph_builder = StateGraph(State)

# Define tools
tools = [
    PF2ERulesLookup(),
    CombatAnalyzer(),
    LevelUpAdvisor(),
    AdventureReference()
]

# Add nodes
graph_builder.add_node("context_classifier", context_classifier)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))

# Add edges with conditional routing
graph_builder.add_edge(START, "context_classifier")
graph_builder.add_edge("context_classifier", "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# Use MemorySaver for persistence
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)
```

## Key Components

### 1. LLM-Based Context Management with OpenAI
```python
class ContextManager:
    """Manages multiple conversation contexts per user using OpenAI for classification."""
    
    def __init__(self, llm):
        # Initialize with OpenAI LLM
        self.llm = llm  # ChatOpenAI instance
        self.context_store = {}  # Or use MemorySaver
        self.similarity_threshold = 0.7  # Configurable threshold
    
    async def get_context(self, user_id: str, message_content: str) -> Tuple[str, Dict]:
        """
        Determines the appropriate context for a message using OpenAI scoring.
        
        1. Retrieves all contexts for the user
        2. Uses OpenAI to score each context's relevance to the current message
        3. Returns the highest-scoring context if above threshold, or creates new context
        """
        user_contexts = await self._get_user_contexts(user_id)
        
        if not user_contexts:
            # Create new context if user has none
            return await self._create_new_context(user_id, message_content)
        
        # Score each context using OpenAI
        context_scores = await self._score_contexts(message_content, user_contexts)
        
        # Find highest scoring context
        best_context_id, best_score = max(context_scores.items(), key=lambda x: x[1])
        
        # If best score is above threshold, use that context
        if best_score >= self.similarity_threshold:
            return best_context_id, user_contexts[best_context_id]
        else:
            # Create new context if no good match
            return await self._create_new_context(user_id, message_content)
    
    async def _calculate_relevance_score(self, message: str, context_summary: str) -> float:
        """
        Uses OpenAI to calculate relevance score between message and context.
        
        Returns:
            Float between 0.0 (completely unrelated) and 1.0 (perfect match)
        """
        prompt = f"""
        You are evaluating whether a new message belongs to an existing conversation context.
        
        CONTEXT SUMMARY:
        {context_summary}
        
        NEW MESSAGE:
        {message}
        
        On a scale from 0.0 to 1.0, how relevant is this message to the existing context?
        Consider:
        - Topic similarity
        - Continuation of previous discussion
        - References to entities mentioned in the context
        - Temporal connections ("as I was saying before...")
        
        Return only a number between 0.0 and 1.0.
        """
        
        # Format for OpenAI
        messages = [
            {"role": "system", "content": "You are a helpful assistant that evaluates message relevance."},
            {"role": "user", "content": prompt}
        ]
        
        # Call OpenAI
        response = await self.llm.ainvoke(messages)
        
        # Extract score from response
        try:
            score = float(response.content.strip())
            return min(max(score, 0.0), 1.0)  # Ensure in range [0.0, 1.0]
        except:
            # Fallback if parsing fails
            return 0.5
```

### 2. Context Storage Structure
```python
class UserContext:
    """Structure for storing user context information."""
    
    def __init__(self, context_id: str, initial_message: str):
        self.context_id = context_id
        self.created_at = time.time()
        self.last_updated = time.time()
        self.messages = [{"role": "user", "content": initial_message}]
        self.topic_summary = ""  # Can be updated by OpenAI periodically
        self.context_type = ""  # combat, rules_query, character_building, etc.
        self.metadata = {}
    
    def add_message(self, role: str, content: str):
        """Add a message to this context."""
        self.messages.append({"role": role, "content": content})
        self.last_updated = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "context_id": self.context_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "messages": self.messages,
            "topic_summary": self.topic_summary,
            "context_type": self.context_type,
            "metadata": self.metadata
        }
```

### 3. Required Tools
```python
class PF2ERulesLookup:
    """Tool for finding and relaying PF2E rules."""
    
    def __call__(self, query: str) -> str:
        """
        Searches PF2E rulebooks for relevant information.
        Returns formatted rule text with citations.
        """

class CombatAnalyzer:
    """Tool for analyzing PF2E combat scenarios."""
    
    def __call__(self, combat_state: Dict) -> Dict:
        """
        Analyzes combat situation and provides tactical advice.
        Takes into account character abilities, enemy stats, and positioning.
        """

class LevelUpAdvisor:
    """Tool for providing character advancement advice."""
    
    def __call__(self, character_data: Dict, level_up_goals: List[str]) -> Dict:
        """
        Analyzes character data and provides level-up recommendations.
        Considers stated character goals and optimizes suggestions accordingly.
        """

class AdventureReference:
    """Tool for referencing adventure content."""
    
    def __call__(self, query: str, adventure_context: Dict) -> str:
        """
        Searches adventure database for relevant content.
        Provides narrative and mechanical information from adventures.
        """
```

### 4. State Management with MemorySaver
```python
# Initialize MemorySaver for data persistence
memory_saver = MemorySaver()

# State definition with user and context tracking
class FrinnyState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    context_id: str
    metadata: Dict

# Compile graph with memory saver
graph = graph_builder.compile(checkpointer=memory_saver)

# Function to retrieve conversation by context
async def get_conversation(user_id: str, context_id: str):
    """Retrieves a specific conversation context for a user."""
    return await memory_saver.get(f"{user_id}:{context_id}")
```

## WebSocket Integration

To integrate with the existing socket_setup.py, we'll create a handler that processes events through our LangGraph implementation:

```python
# app/handlers/langgraph_handler.py
class LangGraphHandler:
    """Handler for processing WebSocket events through LangGraph with OpenAI."""
    
    def __init__(self, api_key=None):
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Using GPT-4o model
            temperature=0.2,
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        self.context_manager = ContextManager(self.llm)
        self.memory = MemorySaver()
        self.graph = self._initialize_graph()
    
    async def process_event(self, event_type: str, data: Dict, user_id: str) -> Dict:
        """Process any event type through LangGraph."""
        # Create input with all available information
        input_data = {
            "event_type": event_type,
            "data": data,
            "user_id": user_id,
            "timestamp": int(time.time() * 1000)
        }
        
        # Determine context using OpenAI scoring
        context_id, context = await self.context_manager.get_context(
            user_id, 
            json.dumps(input_data)
        )
        
        # Process through graph with appropriate context
        result = await self.graph.ainvoke({
            "messages": context["messages"] + [{"role": "user", "content": json.dumps(data)}],
            "user_id": user_id,
            "context_id": context_id,
            "metadata": {"event_type": event_type}
        })
        
        # Update context with new message and response
        await self._update_context(user_id, context_id, data, result)
        
        # Return formatted response
        return self._format_response(result, data.get("request_id"))
```

Update the socket handlers to use this new handler:

```python
# In socket_setup.py
from app.handlers.langgraph_handler import LangGraphHandler
import os

# Initialize handler with OpenAI API key
langgraph_handler = LangGraphHandler(api_key=os.environ.get("OPENAI_API_KEY"))

@socketio.on('query')
async def handle_query(data):
    try:
        user_id = request.args.get('userId')
        log_event('query', 'Received new query', {'query_data': data})
        
        # Process through LangGraph with OpenAI
        response = await langgraph_handler.process_event('query', data, user_id)
        
        emit('query_response', response, room=user_id)
    except Exception as e:
        # Error handling (unchanged)
        log_event('query_error', 'Error processing query', error=str(e))
        emit('error', {...}, room=user_id)
```

## Implementation Checklist

### Setup
- [ ] Add LangGraph and OpenAI dependencies to requirements.txt
- [ ] Configure OpenAI API key in environment variables
- [ ] Set up MemorySaver for persistence

### Core Components
- [ ] Implement OpenAI-based ContextManager with scoring
- [ ] Create UserContext structure
- [ ] Implement context summary generation with OpenAI
- [ ] Create state management system with context tracking

### Tools Implementation
- [ ] PF2ERulesLookup tool
- [ ] CombatAnalyzer tool
- [ ] LevelUpAdvisor tool
- [ ] AdventureReference tool

### Context Switching
- [ ] Implement OpenAI-based context scoring
- [ ] Create context storage with user:context mapping
- [ ] Set appropriate similarity threshold
- [ ] Add periodic context summary updates

### Storage
- [ ] Configure MemorySaver for persistent storage
- [ ] Implement context retrieval functions
- [ ] Create backup/restore functionality

### WebSocket Integration
- [ ] Create LangGraphHandler class with OpenAI
- [ ] Update socket_setup.py event handlers
- [ ] Test with each event type

## Implementation Timeline
1. **Week 1**: Setup, MemorySaver configuration, and basic context management
2. **Week 2**: Tool implementation and LangGraph integration
3. **Week 3**: OpenAI-based context scoring and multi-context testing
4. **Week 4**: WebSocket integration, optimization and deployment 