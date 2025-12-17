[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# OpenAI Python SDK with Acontext Example

This example demonstrates how to use the [OpenAI Python SDK](https://github.com/openai/openai-python) directly with Acontext for session persistence and task extraction.

## Features

- **Multi-turn conversations**: Maintains conversation history across multiple interactions
- **Tool usage**: Demonstrates function calling with `get_weather` and `book_flight` tools
- **Manual tool execution**: Shows how to handle tool calls from OpenAI API responses
- **Acontext integration**: Sends conversation messages to Acontext for task extraction and analysis

## How It Works

The example creates an agent that helps plan a trip:

1. **First interaction**: User asks for a 3-day trip plan in Finland
2. **Second interaction**: User requests weather check for Finland
3. **Third interaction**: User books a flight from Shanghai to Finland

After the conversation, all messages are sent to Acontext which:
- Extracts tasks from the conversation
- Tracks progress updates
- Identifies user preferences

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

Messages in OpenAI format can be sent directly to Acontext without any conversion:

```python
def append_message(message: dict, conversation: list[dict], session_id: str):
    conversation.append(message)
    acontext_client.sessions.store_message(session_id=session_id, blob=message)
    return conversation
```

## Tool Calling

This example demonstrates manual tool calling with the OpenAI API:

1. Define tools in OpenAI's function calling format
2. Pass tools to the API call with `tool_choice="auto"`
3. Check if the response contains tool calls
4. Execute the requested tools
5. Send tool results back to the API
6. Continue until no more tool calls are needed

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

# Handle tool calls if present
if message.tool_calls:
    for tool_call in message.tool_calls:
        # Execute tool and add result to messages
        ...
```

## Output

The script will:
1. Show the conversation between user and agent
2. Display tool calls (weather checks, flight bookings)
3. Print extracted tasks with their status and metadata
4. Show any progress updates and user preferences identified by Acontext


