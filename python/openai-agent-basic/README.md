# OpenAI Agents SDK + Acontext Examples

This example demonstrates how to use OpenAI Agents SDK with Acontext for task extraction and context management.

## Overview

This example shows:
- Creating an agent with OpenAI Agents SDK
- Using function tools (weather, flight booking)
- Running multi-turn conversations with the agent
- Sending conversation history to Acontext
- Extracting tasks from Acontext sessions

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) package manager
- Acontext API key
- OpenAI API key

## Installation

1. Install dependencies using uv:

```bash
uv sync
```

2. Set up environment variables:

Create a `.env` file in this directory:

```bash
ACONTEXT_API_KEY=your-acontext-api-key
ACONTEXT_BASE_URL=http://localhost:8029/api/v1  
OPENAI_API_KEY=your-openai-api-key
```

## Running the Example

Activate the virtual environment and run:

```bash
source .venv/bin/activate 
python main.py
```