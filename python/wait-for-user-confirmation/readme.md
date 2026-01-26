[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Wait for User Confirmation Example

This example demonstrates how to use Acontext for session management and task extraction from conversations.

## What This Example Does

This example simulates a flight booking conversation where:

1. **Creates a conversation**: Sends a series of messages between a user and an assistant about booking a flight to Tokyo
2. **Flushes session**: Triggers Acontext to process the conversation and extract tasks

## Key Features

- **Session Management**: Create and manage conversation sessions with Acontext
- **Task Extraction**: Automatically extract tasks from conversations
- **Interactive CLI**: User-friendly command-line interface using Rich for colored output

## Prerequisites

- Python 3.13 or higher
- An Acontext API key
- Access to an Acontext instance (local or cloud)

Detail doc is here: https://docs.acontext.io/learn/advance/wait-user.

## Installation

1. Install dependencies using `uv`:

```bash
uv sync
```

2. Set up your environment variables:

Create a `.env` file in the project root:

```env
ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
ACONTEXT_BASE_URL=http://localhost:8029/api/v1
```

Or export them directly:

```bash
export ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
export ACONTEXT_BASE_URL=http://localhost:8029/api/v1
```

## Running the Example

Execute the example:

```bash
uv run main.py
```

### Expected Output

The example will:

1. Display the simulated conversation messages
2. Flush the session to trigger task extraction

Example interaction:

```
━━━━━━━━━━━━━━━━ Sending Messages ━━━━━━━━━━━━━━━━
user: I want to book a flight to Tokyo. Please help me to book the flight.
assistant: My task is to book the flight to Tokyo. I will start now.
assistant: I have searched the flights
assistant: Done, I have selected the flight
user: You must remember: I only want the cheapest flight
assistant: Done, I have booked the flight
user: Yes, great job!
━━━━━━━━━━━━━━━━ Wait for Task Agent ━━━━━━━━━━━━━━━━
```

## How It Works

### 1. Session Creation

```python
session = acontext_client.sessions.create()
```

Creates a new session (conversation thread).

### 2. Sending Messages

```python
for m in messages:
    acontext_client.sessions.store_message(session_id=session.id, blob=m)
```

Sends each message in the conversation to Acontext for processing.

### 3. Flushing Session

```python
acontext_client.sessions.flush(session.id)
```

Flushes the session to trigger task extraction and processing.

## Use Cases

This pattern is particularly useful for:

- **Session Management**: Managing conversation sessions with Acontext
- **Task Extraction**: Automatically extracting tasks from conversations
- **Conversation Tracking**: Tracking multi-turn conversations

## Customization

You can modify the example to:

- Use real conversations instead of mock messages
- Add task processing logic
- Integrate with your own workflow systems
- Add custom message formatting

## Troubleshooting

### Session creation fails

- Check your Acontext instance is running properly
- Verify network connectivity to the Acontext API
- Ensure your API key is correct

