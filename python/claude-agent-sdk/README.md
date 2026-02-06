[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Claude Agent SDK + Acontext (`ClaudeAgentStorage`) Example

This example shows how to use the [`ClaudeAgentStorage`](https://docs.acontext.io/integrations/claude-agent) integration to automatically persist Claude Agent SDK messages to Acontext.

## Overview

The script demonstrates:
- Connecting to the Claude Agent SDK via `ClaudeSDKClient`
- Using `ClaudeAgentStorage` from the Acontext SDK to stream messages directly into Acontext
- Automatic session-id discovery from the Claude Agent SDK stream
- The `replay-user-messages` flag to capture both user and assistant messages

Unlike the `claude-agent-basic` example that manually serializes messages, this approach uses the built-in `ClaudeAgentStorage` helper which handles message formatting, session management, and error handling automatically.

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) for dependency management
- `ANTHROPIC_API_KEY` for the Claude Agent SDK
- `ACONTEXT_API_KEY` for the Acontext SDK

## Installation

Install dependencies with uv:

```bash
uv sync
```

## Environment Variables

Create a `.env` file in this directory (see `.env.example`):

```bash
ANTHROPIC_API_KEY=your-anthropic-key
ACONTEXT_API_KEY=sk-ac-your-acontext-key
ACONTEXT_BASE_URL=http://localhost:8029/api/v1  # optional, defaults to this value
```

## Running the Example

```bash
# Option 1: traditional venv
source .venv/bin/activate
python main.py

# Option 2: no activation needed
uv run python main.py
```

## How it works

1. Creates an `AcontextAsyncClient` and wraps it with `ClaudeAgentStorage`
2. Sends a query to Claude via `ClaudeSDKClient`
3. Iterates over `receive_response()` and passes each message to `storage.save_message()`
4. `ClaudeAgentStorage` automatically discovers the session id, formats messages in Anthropic format, and stores them in Acontext

> **Tip:** The `replay-user-messages` flag ensures `UserMessage` is included in the stream so both sides of the conversation are persisted. Without it, only `AssistantMessage` appears and user messages won't be stored.

## Learn More

- [ClaudeAgentStorage docs](https://docs.acontext.io/integrations/claude-agent)
- [Acontext Python SDK](https://docs.acontext.io/chore/async_python)
