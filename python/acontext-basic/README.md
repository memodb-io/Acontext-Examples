[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

# Acontext Examples

This example demonstrates how to use the Acontext Python SDK for session management, task extraction, and artifact handling.

## Overview

This example shows:
- Creating spaces and sessions
- Sending messages to sessions
- Retrieving tasks from sessions
- Creating and retrieving artifacts (files)

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) package manager
- Acontext API key

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
```

## Running the Examples

Activate the virtual environment:

```bash
source .venv/bin/activate
```

### Session Example

Run the session example to see how to create sessions, send messages, and retrieve tasks:

```bash
python session.py
```

This example demonstrates:
- Creating a space and session
- Sending multiple messages (user and assistant messages, including tool calls)
- Flushing the session
- Retrieving and displaying tasks with their status and progress

### Artifacts Example

Run the artifacts example to see how to create and retrieve artifacts:

```bash
python artifacts.py
```

This example demonstrates:
- Creating a disk
- Uploading markdown and PNG files as artifacts
- Retrieving artifacts by file path and filename

