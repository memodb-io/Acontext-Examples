# Agno with Acontext Example

This example demonstrates how to use [Agno](https://github.com/agno-agi/agno) - a Python framework for building multi-agent systems - with Acontext for session persistence and task extraction.

## Features

- **Multi-turn conversations**: Maintains conversation history across multiple interactions
- **Tool usage**: Demonstrates function calling with `get_weather` and `book_flight` tools
- **Message list input**: Shows how to pass conversation history using Agno's `Message` objects
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
python basic_persistent_agent.py
```



## Acontext Integration
Messages in OpenAI format can be sent directly to Acontext without any conversion:

```python
def append_message(message: dict, conversation: list[dict], session_id: str):
    conversation.append(message)
    acontext_client.sessions.send_message(session_id=session_id, blob=message)
    return conversation
```

## Output

The script will:
1. Show the conversation between user and agent
2. Display tool calls (weather checks, flight bookings)
3. Print extracted tasks with their status and metadata
4. Show any progress updates and user preferences identified by Acontext

