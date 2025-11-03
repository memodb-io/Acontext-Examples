# Python + OpenAI Template

This template demonstrates how to integrate OpenAI SDK with Acontext, allowing you to send OpenAI messages to Acontext for context management and persistence.

## Overview

This template shows:
- How to use OpenAI SDK to create chat completions
- How to send OpenAI messages to Acontext sessions
- How to retrieve and manage conversation history through Acontext

## Features

- ✅ OpenAI chat completion integration
- ✅ Acontext session management
- ✅ Message persistence and retrieval
- ✅ Full conversation context tracking

## Prerequisites

- Python 3.10 or newer
- OpenAI API key
- Acontext API key

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Quick Start

### Basic Usage

Run the basic example:

```bash
python src/main.py
```

### Advanced Example

Check out the detailed example with conversation management:

```bash
python examples/basic_usage.py
```

## Code Example

```python
from openai import OpenAI
from acontext import AcontextClient
from openai.types.chat import ChatCompletionUserMessageParam

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
acontext_client = AcontextClient(api_key=os.getenv("ACONTEXT_API_KEY"))

# Create a space and session
space = acontext_client.spaces.create()
session = acontext_client.sessions.create(space_id=space["id"])

# Use OpenAI to generate a response
user_message = "Hello, how are you?"
openai_messages = [{"role": "user", "content": user_message}]
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=openai_messages
)

# Send both user and assistant messages to Acontext
user_msg = ChatCompletionUserMessageParam(role="user", content=user_message)
acontext_client.sessions.send_message(
    session["id"],
    blob=user_msg,
    format="openai"
)

assistant_msg = ChatCompletionAssistantMessageParam(
    role="assistant",
    content=response.choices[0].message.content
)
acontext_client.sessions.send_message(
    session["id"],
    blob=assistant_msg,
    format="openai"
)
```

## Environment Variables

See `.env.example` for all required environment variables.

## Documentation

- [Acontext Python SDK Documentation](https://github.com/memodb-io/Acontext)
- [OpenAI Python SDK Documentation](https://github.com/openai/openai-python)

