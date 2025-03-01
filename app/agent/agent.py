from typing import Annotated, Dict, List, Tuple
import os
import json
import time
import uuid
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from pymongo import MongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

from app.agent.tools import pf2e_rules_lookup, combat_analyzer, level_up_advisor, adventure_reference
from app.config.logging_config import get_logger
from app.agent.personalities import get_personality

# Get module logger
logger = get_logger(__name__)


class State(TypedDict):
    """State definition for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    user_id: str
    context_id: str
    metadata: Dict = {}


def get_system_prompt(personality_name=None) -> str:
    """
    Get system prompt from the specified or default personality.
    
    Args:
        personality_name: Optional name of personality to use
        
    Returns:
        System prompt for the agent
    """
    personality = get_personality(personality_name)
    logger.info(f"Using personality: {personality}")
    return personality.system_prompt


def chatbot(state: State):
    """
    Processes user messages and generates responses using the LLM with tools.
    
    Args:
        state: Current state with messages and context
        
    Returns:
        Updated state with AI response
    """
    # Extract metadata and personality name if provided
    metadata = state.get("metadata", {})
    personality_name = metadata.get("personality", "Frinny")
    
    # Initialize LLM with larger context window for complex queries
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")
    
    # Get the current messages
    messages = state["messages"]
    
    # If this is a new conversation, add the system message
    if not any(isinstance(m, SystemMessage) for m in messages):
        system_message = SystemMessage(content=get_system_prompt(personality_name))
        messages = [system_message] + messages
    
    # Add user tool definitions
    tools = [
        pf2e_rules_lookup,
        combat_analyzer,
        level_up_advisor,
        adventure_reference
    ]
    
    # Generate AI response
    response = llm.bind_tools(tools).invoke(messages)
    
    # Return updated state with the new message
    return {"messages": messages + [response]}


# Initialize graph builder
graph_builder = StateGraph(State)

# Define tools
tools = [
    pf2e_rules_lookup,
    combat_analyzer,
    level_up_advisor,
    adventure_reference
]

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.2,
    api_key=os.environ.get("OPENAI_API_KEY")
)
llm_with_tools = llm.bind_tools(tools)

# Add nodes
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))

# Add edges with conditional routing
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

mongodb_client = MongoClient(os.environ.get("MONGODB_URI"))

# memory = AsyncMongoDBSaver(mongodb_client)
memory = MemorySaver()
logger.info(f"Memory: {memory}")
graph = graph_builder.compile(checkpointer=memory)


class LangGraphHandler:
    """Simple handler for processing events through LangGraph."""
    
    def __init__(self):
        """Initialize with memory persistence."""
        self.graph = graph
        self.memory = memory
    
    async def process_event(self, event_type: str, data: Dict, user_id: str) -> Dict:
        """
        Process any event type through LangGraph.
        
        Args:
            event_type: Type of the event (query, combat, etc.)
            data: Event data
            user_id: ID of the user
            
        Returns:
            Response from the LangGraph with appropriate format
        """
        try:
            # Extract or generate request_id
            request_id = data.get('request_id', str(uuid.uuid4()))
            
            # Get personality name if specified in data
            personality_name = data.get('personality')
            
            # Create a unique thread_id using only the user_id
            # This ensures all messages from the same user go to the same thread
            thread_id = f"user_{user_id}"
            logger.info(f"Using thread_id: {thread_id}")
            
            # Create message from current data
            content = data.get('message', data.get('content', json.dumps(data)))
            current_message = HumanMessage(content=content)
            
            # First try to get existing state from LangGraph memory
            existing_state = None
            try:
                existing_state = self.graph.get_state({"configurable": {"thread_id": thread_id}})
                if existing_state and "messages" in existing_state:
                    logger.info(f"Found existing state for user {user_id} with {len(existing_state['messages'])} messages")
                    messages = existing_state["messages"] + [current_message]
                else:
                    logger.info(f"No existing state found for user {user_id}, initializing new conversation")
                    messages = [current_message]
            except Exception as e:
                logger.warning(f"Error retrieving state for user {user_id}: {str(e)}")
                messages = [current_message]
            
            # Process through graph with the user's thread_id
            logger.info(f"Invoking graph with {len(messages)} messages for user {user_id}")
            
            # Prepare input state
            input_state = {
                "messages": messages,
                "user_id": user_id,
                "context_id": thread_id,  # Using thread_id here for consistency
                "metadata": {
                    "event_type": event_type,
                    "personality": personality_name
                }
            }
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Always use ainvoke since we have async tools
            result = await self.graph.ainvoke(input_state, config)
            
            logger.info(f"Result: {result}")
            
            # Get the last message (the response)
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Format response
            response = {
                'request_id': request_id,
                'status': 'success',
                'timestamp': int(time.time() * 1000),
                'context_id': thread_id  # Return the thread_id as context_id for consistency
            }
            
            # Add content with appropriate field name using personality formatting
            personality = get_personality(personality_name)
            formatted_content = personality.format_response(response_content, event_type)
            response.update(formatted_content)
                
            return response
            
        except Exception as e:
            # Get error message from personality
            personality = get_personality(data.get('personality'))
            error_message = personality.error_message
            
            logger.error(f"Error in LangGraph processing: {type(e)}")
            return {
                'request_id': data.get('request_id', str(uuid.uuid4())),
                'status': 'error',
                'timestamp': int(time.time() * 1000),
                'error': error_message,
                'debug_info': f"Error processing {event_type}: {str(e)}"
            }


# Create a singleton instance for use in socket_setup.py
lang_graph_handler = LangGraphHandler()