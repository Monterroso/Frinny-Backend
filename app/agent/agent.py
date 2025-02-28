from typing import Annotated, Dict, List, Tuple
import os
import json
import time
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import pf2e_rules_lookup, combat_analyzer, level_up_advisor, adventure_reference
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)


class State(TypedDict):
    """State definition for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    user_id: str
    context_id: str
    metadata: Dict = {}


def get_system_prompt() -> str:
    """
    Get a simple system prompt focused on tool usage.
    
    Returns:
        Simple system prompt with instructions
    """
    return """You are Frinny, a helpful Pathfinder 2E assistant.
You have access to tools that can help you answer questions about the Pathfinder 2E game system.
Use these tools whenever appropriate to provide accurate information.
Be concise and clear in your answers.
"""


def chatbot(state: State):
    """
    Processes user messages and generates responses using the LLM with tools.
    
    Args:
        state: The current state with messages and context
        
    Returns:
        Updated state with assistant's response added to messages
    """
    # Get the event type from metadata
    event_type = state.get("metadata", {}).get("event_type", "query")
    
    # Check if we need to add a system message
    messages = state["messages"]
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        # Add system message with personality
        system_prompt = get_system_prompt()
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # Use the LLM with tools to generate a response
    response = llm_with_tools.invoke(messages)
    
    # Add the response to the messages
    return {"messages": llm_with_tools.invoke(messages)}


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

# Use simple MemorySaver for persistence
memory = MemorySaver()
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
            result = await self.graph.ainvoke(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "context_id": thread_id,  # Using thread_id here for consistency
                    "metadata": {"event_type": event_type}
                },
                {"configurable": {"thread_id": thread_id}}
            )
            
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
            
            # Add content with appropriate field name
            if event_type == 'query':
                response['content'] = response_content
            else:
                response['message'] = response_content
                
            return response
            
        except Exception as e:
            error_message = "I'm sorry, I encountered a system error. Please try again."
            logger.error(f"Error in LangGraph processing: {str(e)}")
            return {
                'request_id': data.get('request_id', str(uuid.uuid4())),
                'status': 'error',
                'timestamp': int(time.time() * 1000),
                'error': error_message,
                'debug_info': f"Error processing {event_type}: {str(e)}"
            }


# Create a singleton instance for use in socket_setup.py
lang_graph_handler = LangGraphHandler()