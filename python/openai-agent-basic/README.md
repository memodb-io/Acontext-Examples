[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# OpenAI Agents SDK + Acontext Example

This example demonstrates how to use the [OpenAI Agents SDK](https://github.com/openai/agents-sdk-python) with Acontext for session persistence and task extraction.

## Features

- **Multi-turn conversations**: Maintains conversation history across multiple interactions
- **Function tools**: Uses `@function_tool` decorator to define tools like `get_weather` and `book_flight`
- **Automatic tool execution**: The Agents SDK handles tool calls automatically
- **Acontext integration**: Sends conversation messages to Acontext for task extraction and analysis
- **Session resumption**: Demonstrates how to load previous conversations from Acontext and continue

## How It Works

The example creates an agent that helps plan a trip using two sessions:

### Session 1: Create and Store Conversation
1. **First interaction**: User asks for a 3-day trip plan in Finland
2. **Second interaction**: User requests weather check for Finland
3. **Third interaction**: User books a flight from Shanghai to Finland
4. **Fourth interaction**: User thanks the assistant

After the conversation, all messages are converted to OpenAI format and sent to Acontext which:
- Extracts tasks from the conversation
- Tracks progress updates
- Identifies user preferences

### Session 2: Resume Conversation
1. Loads previous conversation messages from Acontext
2. Converts OpenAI format messages back to Responses API format
3. Continues the conversation with a summary request

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
```

## Running

```bash
python main.py
```

## Acontext Integration

### Sending Messages to Acontext

The conversation is converted from Responses API format to Chat Completions API format using `Converter.items_to_messages()`:

```python
messages = Converter.items_to_messages(result.to_input_list())
for msg in messages:
    acontext_client.sessions.store_message(session_id=session_id, blob=msg, format="openai")
```

### Loading Messages from Acontext

Messages are loaded from Acontext in Chat Completions API format and converted back to Responses API format using `message_to_input_items()`:

```python
messages = acontext_client.sessions.get_messages(session_id, format="openai")

conversation = []
for msg in messages.items:
    items = message_to_input_items(msg)
    conversation.extend(items)
```

## Function Tools

This example demonstrates function tools with the Agents SDK:

1. Define tools using the `@function_tool` decorator
2. Register tools with the agent
3. The SDK automatically handles tool calls and execution

```python
@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

@function_tool
def book_flight(from_city: str, to_city: str, date: str) -> str:
    """Book a flight."""
    return f"Flight booked successfully for '{from_city}' to '{to_city}' on '{date}'"

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    model=OpenAIChatCompletionsModel(...),
    tools=[get_weather, book_flight],
)
```

The Agents SDK automatically:
- Parses tool calls from model responses
- Executes the appropriate tool functions
- Injects tool results back into the conversation
- Handles multi-turn tool calling workflows

## Output

The script will:
1. Show the conversation between user and agent in Session 1
2. Display tool calls and their results (weather checks, flight bookings)
3. Print extracted tasks with their status and metadata from Acontext
4. Show any progress updates and user preferences identified by Acontext
5. Resume the conversation in Session 2 with a summary request