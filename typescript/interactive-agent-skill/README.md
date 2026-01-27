# Agent Skill Demo (TypeScript)

A TypeScript demo showing how to create and use Acontext Skills within a sandbox environment, powered by an OpenAI agentic loop.

## What it does

1. Uploads a skill (from a zip file) to Acontext
2. Creates a sandbox with a persistent disk
3. Mounts the skill into the sandbox
4. Runs an interactive chat loop where an AI agent can execute bash commands, run Python scripts, and export files

## Prerequisites

- Node.js 18+
- npm or yarn
- API keys for OpenAI and Acontext
- An Acontext instance (local or cloud)

## Setup

1. **Install dependencies:**

```bash
npm install
```

2. **Configure environment variables:**

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual values:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Acontext Configuration
ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token

# Optional: Custom OpenAI base URL (uncomment if using a different endpoint)
# OPENAI_BASE_URL=https://api.openai.com/v1
```

**Required variables:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `ACONTEXT_API_KEY` - Your Acontext API key

**Optional variables:**
- `OPENAI_BASE_URL` - Custom OpenAI endpoint (only needed if using a proxy or alternative service)

## Usage

```bash
# Run with a skill zip file (development mode)
npm run dev -- <path_to_zip_file> [model_name]

# Or build and run
npm run build
npm start -- <path_to_zip_file> [model_name]

# Examples
npm run dev -- example_skills/pptx.zip
npm run dev -- example_skills/xlsx.zip gpt-4.1
```

### Interactive Commands

Once the sandbox is ready, you can:
- Type requests for the agent to execute
- Type `reset` to clear conversation history
- Type `quit` to exit

## Example Skills

You can use the example skill zip files from the Python version:
- `pptx.zip` - PowerPoint generation skill
- `xlsx.zip` - Excel file generation skill
- `web-artifacts-builder.zip` - Web artifacts builder skill

These are located in `../python/interactive-agent-skill/`.
