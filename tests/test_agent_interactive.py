import asyncio
import os
import json
import logging
import argparse
from app.agent.agent import lang_graph_handler
from app.config.logging_config import get_logger

# Set up logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

async def send_message(message, event_type="query", user_id="test-user", context_id=None):
    """
    Send a message to the agent and return the response.
    
    Args:
        message: The message text to send
        event_type: The type of event (query, combat_turn, level_up, etc.)
        user_id: The user ID
        context_id: Optional context ID for continuing a conversation
        
    Returns:
        The agent's response
    """
    test_data = {
        "message": message,
        "request_id": f"test-{event_type}-{hash(message) % 10000}"
    }
    
    if context_id:
        test_data["context_id"] = context_id
    
    logger.info(f"Sending {event_type} to agent: {message}")
    
    response = await lang_graph_handler.process_event(
        event_type=event_type,
        data=test_data,
        user_id=user_id
    )
    
    logger.info("\n=== AGENT RESPONSE ===")
    logger.info(json.dumps(response, indent=2))
    logger.info("=====================\n")
    
    return response

async def interactive_session():
    """Run an interactive session with the agent."""
    print("\n=== INTERACTIVE AGENT TESTING ===")
    print("Type 'exit' to quit, 'help' for commands")
    
    user_id = "interactive-user"
    context_id = None
    event_type = "query"
    
    while True:
        try:
            message = input("\nYour message (or command): ")
            
            if message.lower() == "exit":
                print("Exiting interactive session.")
                break
                
            elif message.lower() == "help":
                print("\nAvailable commands:")
                print("  exit - Exit the interactive session")
                print("  help - Show this help message")
                print("  clear - Clear the conversation context")
                print("  event <type> - Change event type (query, combat_turn, level_up, character_creation)")
                print("  user <id> - Change user ID")
                continue
                
            elif message.lower() == "clear":
                context_id = None
                print("Conversation context cleared.")
                continue
                
            elif message.lower().startswith("event "):
                event_type = message.split(" ", 1)[1].strip()
                print(f"Event type changed to: {event_type}")
                continue
                
            elif message.lower().startswith("user "):
                user_id = message.split(" ", 1)[1].strip()
                print(f"User ID changed to: {user_id}")
                continue
            
            # Send the message to the agent
            response = await send_message(
                message=message,
                event_type=event_type,
                user_id=user_id,
                context_id=context_id
            )
            
            # Update context ID for the next message
            context_id = response.get("context_id")
            
            # Display the response content
            if "content" in response:
                print(f"\nAgent: {response['content']}")
            elif "message" in response:
                print(f"\nAgent: {response['message']}")
            else:
                print("\nAgent: [No content in response]")
                
        except KeyboardInterrupt:
            print("\nExiting due to keyboard interrupt.")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

async def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Test the LangGraph agent")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--message", "-m", help="Single message to send to the agent")
    parser.add_argument("--event-type", "-e", default="query", 
                        help="Event type (query, combat_turn, level_up, character_creation)")
    args = parser.parse_args()
    
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("ERROR: OPENAI_API_KEY environment variable is not set!")
        return 1
    
    try:
        if args.interactive:
            await interactive_session()
        elif args.message:
            await send_message(args.message, event_type=args.event_type)
        else:
            print("No action specified. Use --interactive or --message")
            return 1
            
        return 0
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 