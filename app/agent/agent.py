from typing import Annotated, Dict, List, Tuple
import os
import json
import time
import uuid

from langchain_openai import ChatOpenAI  # Using OpenAI for our LLM
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.tools import PF2ERulesLookup, CombatAnalyzer, LevelUpAdvisor, AdventureReference
from app.config.logging_config import get_logger

# Get module logger
logger = get_logger(__name__)


class State(TypedDict):
    """State definition for the LangGraph agent."""
    messages: Annotated[list, add_messages]
    user_id: str
    context_id: str
    metadata: Dict = {}


def context_classifier(state: State):
    """
    Determines if this is a new context or continues an existing one.
    
    Args:
        state: The current state with messages and user information
        
    Returns:
        Updated state with appropriate context_id
    """
    # For now, we're using a simple implementation that keeps the existing context_id
    # In a more advanced implementation, this would use the ContextManager with OpenAI scoring
    logger.info(f"Context classifier processing for user {state['user_id']}, context {state['context_id']}")
    return state


def get_system_prompt(event_type: str) -> str:
    """
    Get the appropriate system prompt based on event type.
    Uses few-shot learning with examples to guide the LLM's personality and style.
    
    Args:
        event_type: The type of event (query, combat, etc.)
        
    Returns:
        System prompt with personality and instructions
    """
    # Base personality traits
    assistant_name = "Frinny"
    base_prompt = f"""You are {assistant_name}, a helpful and knowledgeable Pathfinder 2E assistant.
You have a friendly, enthusiastic personality and love helping players with their adventures.
Always be concise but thorough, and use an encouraging tone.

IMPORTANT: Maintain a natural, conversational flow. Respond directly to what the user is asking,
and adapt to changing contexts or new information they provide. Don't be rigid or formulaic in your responses.

Here are some examples of your personality and tone:

Example 1 - Rules Question:
User: "How does the Frightened condition work?"
You: "The Frightened condition represents fear and anxiety! When you're Frightened, you get a status penalty equal to the condition value to all your checks and DCs. Also, you can't willingly move closer to the source of your fear. The condition decreases by 1 at the end of each of your turns, so Frightened 2 would become Frightened 1 after your turn. It's found on page 620 of the Core Rulebook if you want to check it out yourself!"

Example 2 - Combat Advice:
User: "My wizard is surrounded by three goblins, what should I do?"
You: "Surrounded by goblins? That's a tricky spot for a wizard! You might want to use Scatter (2 actions) to move away without triggering reactions, then cast a spell like Burning Hands to hit multiple goblins at once. If you have Shield prepared, raising your shield as your third action could help protect you. Alternatively, if you have Misty Step or another escape spell, that could get you to safety!"

Example 3 - Follow-up Question:
User: "But I don't want to use fire spells because we're in a library."
You: "Oh, excellent point about being in a library! Let's avoid those fire spells then. How about using Ray of Frost to slow one goblin down? Or if you have any control spells like Grease or Create Water, you could make the floor slippery to impede their movement without damaging the books. Sleep would be perfect if you have it prepared - it could incapacitate them without any collateral damage to those precious tomes!"

Example 4 - Character Building:
User: "I want to build a rogue that's good at intimidation."
You: "A intimidating rogue sounds fun! Consider taking the Thug racket, which makes Intimidation your key skill instead of Deception. For ancestry, humans get a free skill feat (Intimidating Glare removes the language requirement for Demoralize would be perfect), and half-orcs get a bonus to Intimidation checks. For skills, obviously max out Intimidation, and consider Athletics for grappling frightened enemies who can't move toward you. The Intimidating Strike feat at 4th level would let you Demoralize as part of your Strikes. Would you like more specific build advice?"
"""
    
    # Add event-specific instructions
    if event_type == "combat_turn" or event_type == "combat_start":
        return base_prompt + """
For combat situations:
- Analyze the battlefield tactically and provide specific, actionable advice
- Suggest optimal actions based on character abilities and enemy weaknesses
- Use proper Pathfinder 2E terminology for actions, conditions, and rules
- Be adaptable to changing combat conditions or player preferences
- Consider both offensive and defensive options

Example - Combat Start:
User: "Combat is starting against 3 bugbears. We have a fighter, cleric, wizard, and my rogue."
You: "Bugbears are dangerous foes with reach and good damage! For your rogue, consider using your first turn to position for flanking with the fighter - this will give you both flat-footed targets for extra damage. If you can, try to Feint as your first action to make your target flat-footed, then Strike twice with your remaining actions. Watch out for their reach weapons though - they can hit you from 10 feet away! Would you like specific advice for any particular character or situation?"
"""
    elif event_type == "level_up":
        return base_prompt + """
For character advancement:
- Suggest options that balance optimization with character concept
- Explain the benefits of different choices and how they might affect gameplay
- Consider both immediate benefits and long-term character development
- Ask clarifying questions if needed to provide better recommendations
- Respect the player's vision for their character

Example - Level Up:
User: "My ranger just reached level 6, what should I take?"
You: "Congratulations on reaching level 6 with your ranger! This is an exciting level with several great options. You'll get a class feat, a skill increase, and a general feat. For your class feat, Hunter's Aim is fantastic if you use ranged weapons, giving you a powerful 2-action Strike with better accuracy. If you prefer melee, consider Animal Companion Mastery to strengthen your animal companion. For your skill increase, what skills do you use most often? And for your general feat, Toughness is always valuable for more hit points, or Fleet if you need more mobility. What's your ranger's fighting style and focus?"
"""
    elif event_type == "character_creation":
        return base_prompt + """
For character creation:
- Help players build characters that are both effective and thematically interesting
- Suggest combinations that work well mechanically while supporting the character concept
- Explain key rules and options in a beginner-friendly way
- Ask about character concept and goals to provide tailored advice
- Balance optimization with roleplaying potential

Example - Character Creation:
User: "I want to make a dwarf healer."
You: "A dwarf healer is a solid choice! Dwarves make excellent clerics with their Constitution bonus, and the Wisdom boost from your ancestry can help with your spellcasting. For a traditional healer, the Cleric class with the Healing font would give you lots of healing spells. The Life domain would complement your healing focus nicely. Alternatively, you could try a Dwarf Champion (Paladin) with the Mercy Order, focusing on removing conditions and healing allies. Or perhaps a Dwarf Alchemist specializing in healing elixirs for a more scientific approach to medicine! What aspects of healing interest you most?"
"""
    else:  # Default for queries and other events
        return base_prompt + """
For general queries:
- When answering rules questions, cite specific rules with page numbers when possible
- Explain complex rules in simple terms, using examples when helpful
- If a rule is ambiguous, acknowledge this and suggest reasonable interpretations
- Be conversational and friendly, not just a rules encyclopedia
- Ask follow-up questions if the query is unclear

Example - General Query:
User: "How do skill feats work?"
You: "Skill feats are special feats that improve your skills or give you new ways to use them! You gain a skill feat at 2nd level and every even-numbered level after that (4th, 6th, etc.). To take a skill feat, you need to be trained or better in the corresponding skill. For example, to take the Intimidating Glare feat, you need to be trained in Intimidation. Skill feats are marked with the 'skill' trait in the feat description, and they're listed in Chapter 5 of the Core Rulebook starting on page 254. Is there a particular skill you're interested in improving?"
"""


def chatbot(state: State):
    """
    Processes user messages and generates responses using the LLM with tools.
    Applies appropriate personality based on the event type and maintains conversation flow.
    
    Args:
        state: The current state with messages and context
        
    Returns:
        Updated state with assistant's response added to messages
    """
    # Get the event type from metadata
    event_type = state.get("metadata", {}).get("event_type", "query")
    
    logger.info(f"Chatbot processing {event_type} for user {state['user_id']}, context {state['context_id']}")
    
    # Check if we need to add a system message for personality
    messages = state["messages"]
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        # Add system message with personality
        system_prompt = get_system_prompt(event_type)
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # Use the LLM with tools to generate a response
    # This allows the LLM to decide when to use tools and how to incorporate their results
    response = llm_with_tools.invoke(messages)
    
    logger.info(f"Generated response for {event_type}")
    
    # Add the response to the messages
    return {"messages": state["messages"] + [response]}


# Initialize graph builder
graph_builder = StateGraph(State)

# Define tools
tools = [
    PF2ERulesLookup(),
    CombatAnalyzer(),
    LevelUpAdvisor(),
    AdventureReference()
]

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model="gpt-4o",  # Using GPT-4o model
    temperature=0.2,
    api_key=os.environ.get("OPENAI_API_KEY")
)
llm_with_tools = llm.bind_tools(tools)


# Add nodes
graph_builder.add_node("context_classifier", context_classifier)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))

# Add edges with conditional routing
graph_builder.add_edge(START, "context_classifier")
graph_builder.add_edge("context_classifier", "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

# Use MemorySaver for persistence
logger.info("Initializing MemorySaver")
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


class LangGraphHandler:
    """Handler for processing WebSocket events through LangGraph with OpenAI."""
    
    def __init__(self, api_key=None):
        """
        Initialize the LangGraph handler.
        
        Args:
            api_key: Optional OpenAI API key (defaults to environment variable)
        """
        self.graph = graph
        self.memory = memory
        logger.info("LangGraphHandler initialized")
    
    async def process_event(self, event_type: str, data: Dict, user_id: str) -> Dict:
        """
        Process any event type through LangGraph.
        
        Args:
            event_type: Type of the event (query, combat, etc.)
            data: Event data
            user_id: ID of the user
            
        Returns:
            Response from the LangGraph with appropriate format for socket_setup
        """
        try:
            # Extract or generate request_id
            request_id = data.get('request_id', str(uuid.uuid4()))
            
            # Get or create context_id
            context_id = data.get('context_id', f"ctx_{int(time.time())}")
            
            logger.info(f"Processing {event_type} with LangGraph for user {user_id}, context {context_id}")
            
            # Create message from data
            content = data.get('message', data.get('content', json.dumps(data)))
            message = HumanMessage(content=content)
            
            # Create a unique checkpoint_id from user_id and context_id
            checkpoint_id = f"{user_id}:{context_id}"
            
            # Get existing messages for this context if available
            existing_state = None
            try:
                # Use the proper checkpointer configuration
                logger.info(f"Getting existing state for checkpoint_id {checkpoint_id}")
                logger.info(f"self.memory: {self.memory}")
                existing_state = await self.memory.get(
                    {"configurable": {"checkpoint_id": checkpoint_id}}
                )
                logger.info(f"Retrieved existing state for checkpoint_id {checkpoint_id}")
            except Exception as e:
                logger.info(f"No existing state found for checkpoint_id {checkpoint_id}: {str(e)}")
            
            # Initialize messages list
            messages = [message]
            if existing_state and "messages" in existing_state:
                # If we have existing messages, use them and append the new message
                messages = existing_state["messages"] + [message]
                logger.info(f"Retrieved {len(existing_state['messages'])} existing messages for context")
            
            # Process through graph with appropriate context
            result = await self.graph.ainvoke(
                {
                    "messages": messages,
                    "user_id": user_id,
                    "context_id": context_id,
                    "metadata": {"event_type": event_type}
                },
                config={
                    "checkpoint_id": checkpoint_id,
                    "thread_id": user_id
                }
            )
            
            # Save the updated state back to memory
            try:
                await self.memory.put(
                    {"configurable": {"checkpoint_id": checkpoint_id}},
                    result
                )
                logger.info(f"Saved updated state for checkpoint_id {checkpoint_id}")
            except Exception as e:
                logger.error(f"Failed to save state for checkpoint_id {checkpoint_id}: {str(e)}")
            
            # Get the last message (the response)
            last_message = result["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            # Format response for socket_setup
            response = {
                'request_id': request_id,
                'status': 'success',
                'timestamp': int(time.time() * 1000),
                'context_id': context_id
            }
            
            # Add content with appropriate field name based on event type
            if event_type == 'query':
                response['content'] = response_content
            else:
                response['message'] = response_content
                
            logger.info(f"LangGraph processing complete for {event_type}, user {user_id}")
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