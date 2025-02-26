# Mood Detection System

## Overview

The mood detection system enhances Frinny's interactions by analyzing response content and assigning an appropriate mood, which can be used by the frontend to render different visual states of the assistant character. This creates a more engaging and immersive experience for users.

## Supported Moods

The system currently supports the following moods:

| Mood | Description | Use Cases |
|------|-------------|-----------|
| `default` | Neutral, standard expression | General information, neutral responses |
| `confused` | Uncertain or questioning | When Frinny needs clarification or doesn't understand |
| `happy` | Positive and enthusiastic | When providing positive feedback or congratulations |
| `thinking` | Contemplative, analytical | When reasoning through complex problems or options |
| `scared` | Concerned or cautious | When warning about dangers or risks |

## How It Works

The mood detection system uses two main approaches:

1. **User-Requested Moods**: Users can explicitly request a specific mood in their prompt using phrases like "be happy" or "act confused". This takes precedence over detected moods.

2. **Content Analysis**: When no mood is explicitly requested, the system analyzes the assistant's response using pattern matching to identify emotional indicators.

### Implementation Details

The system is implemented in `app/agent/mood_analyzer.py` with two main functions:

- `analyze_prompt_for_mood(prompt)`: Checks if the user's prompt explicitly requests a mood
- `analyze_mood(content)`: Analyzes the assistant's response to determine an appropriate mood

## Integration with LangGraph

The mood detection is integrated into the `process_event` method of the `LangGraphHandler` class in `app/agent/agent.py`. The workflow is:

1. User message is processed and a response is generated
2. The system checks if the user explicitly requested a mood
3. If not, the system analyzes the response content to detect a mood
4. The detected mood is included in the response structure sent to the frontend

## Example Response Structure

```json
{
  "request_id": "abc123",
  "status": "success",
  "timestamp": 1689012345678,
  "context_id": "xyz789",
  "content": "I think the Fighter class would be an excellent choice for a new player!",
  "mood": "happy"
}
```

## Frontend Integration

The frontend can use the `mood` field to:

1. Change the character's facial expression or pose
2. Add animations or effects
3. Modify the speech bubble style
4. Adjust the text presentation (e.g., italics for "thinking")

## Extending the System

To add new moods or improve detection patterns:

1. Update the `MOOD_PATTERNS` dictionary in `mood_analyzer.py` with new patterns
2. Add new mood detection patterns to `analyze_prompt_for_mood` function
3. Update the documentation to reflect the new mood options
4. Ensure the frontend has appropriate visual assets for the new moods 