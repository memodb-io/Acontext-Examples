[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Claude Agent SDK + Acontext (`ClaudeAgentStorage`) Example

This TypeScript example shows how to use the [`ClaudeAgentStorage`](https://docs.acontext.io/integrations/claude-agent) integration to automatically persist Claude Agent SDK messages to Acontext.

## Overview

The script demonstrates:
- Using the `@anthropic-ai/claude-agent-sdk` to query Claude
- Using `ClaudeAgentStorage` from `@acontext/acontext` to stream messages directly into Acontext
- Automatic session-id discovery from the Claude Agent SDK stream
- The `replay-user-messages` flag to capture both user and assistant messages

## Prerequisites

- Node.js 18 or newer
- `ANTHROPIC_API_KEY` for the Claude Agent SDK
- `ACONTEXT_API_KEY` for the Acontext SDK

## Installation

```bash
npm install
```

## Environment Variables

Create a `.env` file in this directory (see `.env.example`):

```
ANTHROPIC_API_KEY=your-anthropic-key
ACONTEXT_API_KEY=sk-ac-your-acontext-key
ACONTEXT_BASE_URL=http://localhost:8029/api/v1
```

## Running the Example

```bash
# Development (no build step)
npm run dev

# Or build and run
npm run build
npm start
```

## How it works

1. Creates an `AcontextClient` and wraps it with `ClaudeAgentStorage`
2. Sends a query to Claude via `query()`
3. Iterates over the async response stream and passes each message to `storage.saveMessage()`
4. `ClaudeAgentStorage` automatically discovers the session id, formats messages in Anthropic format, and stores them in Acontext

> **Tip:** The `replay-user-messages` flag ensures `UserMessage` is included in the stream so both sides of the conversation are persisted. Without it, only `AssistantMessage` appears and user messages won't be stored.

## Learn More

- [ClaudeAgentStorage docs](https://docs.acontext.io/integrations/claude-agent)
- [Acontext TypeScript SDK](https://docs.acontext.io/quick)
