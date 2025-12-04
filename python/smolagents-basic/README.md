[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Smolagents + Acontext Example

This example demonstrates how to use [smolagents](https://github.com/huggingface/smolagents) with Acontext for session persistence and task extraction.

## Features

- **Multi-turn conversations**: Maintains conversation history across multiple interactions using agent memory
- **Tool-based agents**: Uses `Tool` class to define tools like `get_weather` and `book_flight`
- **Automatic tool execution**: The `ToolCallingAgent` handles tool calls automatically
- **Acontext integration**: Sends conversation messages to Acontext for task extraction and analysis
- **Session resumption**: Demonstrates how to load previous conversations from Acontext and continue with a new agent instance

## How It Works

The example creates an agent that helps plan a trip using two sessions:

### Session 1: Create and Store Conversation
1. **First interaction**: User asks for a 3-day trip plan in Finland
2. **Second interaction**: User requests weather check for Finland and asks about their name
3. **Third interaction**: User books a flight from Shanghai to Finland
4. **Fourth interaction**: User thanks the assistant

After the conversation, all messages are extracted from agent memory steps and sent to Acontext which:
- Extracts tasks from the conversation
- Tracks progress updates
- Identifies user preferences

### Session 2: Resume Conversation
1. Loads previous conversation messages from Acontext
2. Converts messages to string format for the agent
3. Continues the conversation with a summary request using a new agent instance

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Create a `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_key_here
ACONTEXT_API_KEY=your_acontext_key_here
ACONTEXT_BASE_URL=http://localhost:8029/api/v1  # or your Acontext server URL
SMOLAGENTS_MODEL_ID=gpt-4.1  # optional, defaults to gpt-4.1
OPENAI_BASE_URL=https://api.openai.com/v1  # optional, defaults to OpenAI API
```

## Running

```bash
python main.py
```

## Acontext Integration

### Sending Messages to Acontext

The conversation is extracted from agent memory steps and converted to OpenAI Chat Completions API format:

```python
# Extract messages from agent memory steps
messages = extract_messages_from_memory_steps(agent, previous_step_count)

# Send each message to Acontext
for msg in messages:
    acontext_client.sessions.send_message(session_id=session_id, blob=msg, format="openai")
```

The messages are extracted from `agent.memory.steps`, which contains:
- `TaskStep`: User messages
- `ActionStep`: Assistant messages with tool calls and tool responses
- `FinalAnswerStep`: Final assistant responses

### Loading Messages from Acontext

Messages are loaded from Acontext in Chat Completions API format and converted to string format for the agent:

```python
messages = acontext_client.sessions.get_messages(session_id, format="openai")

# Convert messages to string format
conversation_string = messages_to_string(messages.items)

# Use in agent prompt
user_prompt = f"Here is the conversation history:\n\n{conversation_string}\n\nPlease summarize..."
```

## Tool Definition

This example demonstrates tool-based agents with smolagents:

1. Define tools by extending the `Tool` class
2. Implement the `forward` method with tool logic
3. Register tools with the agent

```python
class GetWeatherTool(Tool):
    name = "get_weather"
    description = "Returns weather info for the specified city."
    inputs = {
        "city": {"type": "string", "description": "The city to get weather for"},
    }
    output_type = "string"

    def forward(self, city: str) -> str:
        return f"The weather in {city} is sunny"

class BookFlightTool(Tool):
    name = "book_flight"
    description = "Book a flight."
    inputs = {
        "from_city": {"type": "string", "description": "The departure city"},
        "to_city": {"type": "string", "description": "The destination city"},
        "date": {"type": "string", "description": "The date of the flight"},
    }
    output_type = "string"

    def forward(self, from_city: str, to_city: str, date: str) -> str:
        return f"Flight booked successfully for '{from_city}' to '{to_city}' on '{date}'"

agent = ToolCallingAgent(
    model=OpenAIModel(...),
    tools=[GetWeatherTool(), BookFlightTool()],
    max_steps=4,
)
```

The `ToolCallingAgent` automatically:
- Parses tool calls from model responses
- Executes the appropriate tool `forward` methods
- Injects tool results back into the conversation
- Handles multi-turn tool calling workflows
- Maintains conversation history in `agent.memory.steps`

## Message Format

The example uses the OpenAI Tools API format with `tool_calls`:
- Assistant messages with `tool_calls` array containing function calls
- Tool response messages with `role="tool"` and `tool_call_id`
- Standard user and assistant messages

## Output

The script will:
1. Show the conversation between user and agent in Session 1
2. Display tool calls and their results (weather checks, flight bookings)
3. Print extracted tasks with their status and metadata from Acontext
4. Show any progress updates and user preferences identified by Acontext
5. Resume the conversation in Session 2 with a summary request using a new agent instance
6. Demonstrate experience search from Acontext after learning completes
