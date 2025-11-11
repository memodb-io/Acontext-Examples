# Python + Acontext Examples

This repository contains examples demonstrating how to use Acontext Python SDK, including integration with OpenAI for context management and persistence.

## Overview

This repository includes:
- **OpenAI Integration**: How to integrate OpenAI SDK with Acontext to send messages and retrieve tasks
- **Acontext Sessions**: How to create sessions, send messages, and retrieve tasks using Acontext format
- **Acontext Artifacts**: How to create and manage artifacts (files) in Acontext disks

## Prerequisites

- Python 3.10 or newer
- Acontext API key
- OpenAI API key (for OpenAI integration example)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
export ACONTEXT_API_KEY="your-acontext-api-key"
export ACONTEXT_BASE_URL="http://localhost:8029/api/v1"  # Optional, defaults to localhost
export OPENAI_API_KEY="your-openai-api-key"  # Required for openai/main.py
```


## Examples

### 1. OpenAI Integration (`openai/main.py`)

Demonstrates:
- Using OpenAI SDK to create chat completions
- Sending OpenAI messages to Acontext sessions
- Polling for task processing completion
- Retrieving tasks from Acontext

Run it:
```bash
python openai/main.py
```

### 2. Acontext Sessions (`acontext/session.py`)

Demonstrates:
- Creating spaces and sessions
- Sending messages in Acontext format
- Polling for task processing completion
- Retrieving tasks from sessions

Run it:
```bash
python acontext/session.py
```

### 3. Acontext Artifacts (`acontext/artifacts.py`)

Demonstrates:
- Creating disks
- Uploading artifacts (markdown and image files)
- Retrieving artifacts by file path and filename

Run it:
```bash
python acontext/artifacts.py
```