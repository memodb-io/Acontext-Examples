# Vercel AI SDK Basic Example with Acontext

This is a TypeScript example demonstrating how to use the Vercel AI SDK with Acontext integration.

## Features

- Uses Vercel AI SDK for chat completions with tool calling
- Integrates with Acontext for session management and task extraction
- Demonstrates multi-turn conversations with tool usage
- Shows how to retrieve and continue conversations from Acontext

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your-openai-api-key
ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
ACONTEXT_BASE_URL=http://localhost:8029/api/v1
OPENAI_BASE_URL=  # Optional, for custom OpenAI-compatible endpoints
```

## Usage

Run the example:
```bash
npm run dev
```

Or build and run:
```bash
npm run build
npm start
```

## What it does

1. Creates an Acontext space and session
2. Runs a multi-turn conversation with:
   - Planning a trip to Finland
   - Checking weather
   - Booking a flight
3. Extracts tasks from the conversation using Acontext
4. Retrieves conversation history and continues with a summary
5. Demonstrates experience search from Acontext

