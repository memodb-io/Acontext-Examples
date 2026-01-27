# Agent Skill Demo

A demo showing how to create and use Acontext Skills within a sandbox environment, powered by an OpenAI agentic loop.

## What it does

1. Uploads a skill (from a zip file) to Acontext
2. Creates a sandbox with a persistent disk
3. Mounts the skill into the sandbox
4. Runs an interactive chat loop where an AI agent can execute bash commands, run Python scripts, and export files

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- API keys for OpenAI and Acontext

## Setup

```bash
# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export ACONTEXT_API_KEY="your-acontext-api-key"

# Optional: custom OpenAI base URL
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

## Usage

```bash
# Run with a skill zip file
python create_skill_sandbox.py <path_to_zip_file> [model_name]

# Examples
python create_skill_sandbox.py pptx.zip
python create_skill_sandbox.py xlsx.zip gpt-4.1
```

### Interactive Commands

Once the sandbox is ready, you can:
- Type requests for the agent to execute
- Type `reset` to clear conversation history
- Type `quit` to exit

## Example Skills

The folder includes example skill zip files:
- `pptx.zip` - PowerPoint generation skill
- `xlsx.zip` - Excel file generation skill
- `web-artifacts-builder.zip` - Web artifacts builder skill
