[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Claude Agent SDK + Acontext Example

This example shows how to pair the [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python) with Acontext for session storage, task extraction, and progress tracking.

## Overview

The script demonstrates:
- Running a short multi-turn conversation with `ClaudeSDKClient`
- Collecting assistant responses (text, thinking, and tool events) in Anthropic message format
- Creating an Acontext space + session
- Sending the full transcript to Acontext and triggering task extraction

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) for dependency management
- `ANTHROPIC_API_KEY` for the Claude Code CLI
- `ACONTEXT_API_KEY` for the Acontext SDK

## Installation

Install dependencies with uv:

```bash
uv sync
```

## Environment Variables

Create a `.env` file in this directory with the required keys:

```bash
ANTHROPIC_API_KEY=your-anthropic-key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # optional, override if self-hosting
ACONTEXT_API_KEY=your-acontext-key
ACONTEXT_BASE_URL=http://localhost:8029/api/v1  # optional, defaults to this value
```

## Running the Example

Activate the virtual environment (or use `uv run`) and execute the example:

```bash
# Option 1: traditional venv
source .venv/bin/activate
python main.py

# Option 2: no activation needed
uv run python main.py
```

You should see:
- Each user/assistant exchange with Claude
- Cost information returned by the Claude Agent SDK
- Space/session IDs created in Acontext
- Extracted tasks printed with their metadata

This serves as a starting point for wiring Claude-based agents into the broader Acontext workflow. Customize the prompts, system instructions, and downstream processing to match your application. 

