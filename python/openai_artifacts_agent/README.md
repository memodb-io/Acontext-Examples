# OpenAI ReAct Agent Demo

Minimal async ReAct-style agent that uses the OpenAI Python SDK plus the Acontext
Disk APIs to demonstrate tool-calling (write, read, list, download).

## Prerequisites
- Python 3.11+ (project uses `uv` but regular `pip` also works)
- OpenAI API key with access to the specified model
- Acontext API key (and optional base URL for self-hosted setups)

## Setup
1. `cd Acontext-Examples/python/openai_artifacts_agent`
2. Copy `.env.example` to `.env` and fill in:
   ```
   OPENAI_API_KEY=...
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_BASE_URL=https://api.openai.com/v1
   ACONTEXT_API_KEY=...
   ACONTEXT_BASE_URL=http://localhost:8029/api/v1
   ```
3. Install dependencies:
   - With uv: `uv sync`
   - With pip: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`

## Run the Demo
```
uv run python main.py
```
The agent will:
1. Create an Acontext disk automatically
2. Write `/notes/demo.txt` on the Acontext disk with a short tools summary
3. List the artifacts in `/notes/` directory
4. Read the file back to verify content
5. Download the file into `./downloads/demo.txt`

Console logs show each tool invocation and the final response.

## Repo Layout
```
agent/
  __init__.py        # exports AcontextArtifactAgent
  react.py           # AcontextArtifactAgent class with chat loop + tool call handling
  tools.py           # tool schemas + async wrappers (get_tools_schema, create_tool_map)
  disk.py            # DiskManager built on AcontextClient
  pretty_print.py    # console output formatting utilities
downloads/           # local destination for downloaded artifacts
main.py              # demo entry point: creates disk and runs agent
```
## Troubleshooting
- Missing `.env` values → runtime `RuntimeError` when loading API keys.
- Disk errors → confirm `ACONTEXT_API_KEY` and the API server URL.
- Download step fails → ensure `downloads/` exists or let the tool create it.

---

# OpenAI React Agent (Python)

This companion section explains how the demo is structured and how you can reuse the components in your own projects.

## Feature Highlights
- **Async execution**: `AsyncOpenAI` plus `asyncio` keep tool calls and model responses concurrent.
- **ReAct loop safeguards**: `max_turn` prevents infinite cycles during experimentation.
- **Modular tool layer**: `agent/disk.py` wraps the Disk APIs, while `agent/tools.py` declares schemas and async implementations.
- **Artifact listing**: `list_artifacts` allows the agent to explore directory contents on the Acontext disk.
- **Canonical download flow**: `download_file` produces a temporary link and writes the artifact to `./downloads` (or a path you pass in).
- **Custom OpenAI endpoint**: point `base_url` at proxies or private deployments when needed.
- **Explicit disk management**: Disk is created in `main.py` and passed to `AcontextArtifactAgent` for better control and isolation.

## Quick Start

1. Install dependencies:
   ```bash
   uv sync
   ```
2. Create `.env` and supply keys:
   ```env
   OPENAI_API_KEY=sk-your-key
   OPENAI_BASE_URL=https://api.openai.com/v1  # optional
   ACONTEXT_API_KEY=sk-ac-your-root-api-bearer-token
   ACONTEXT_BASE_URL=http://localhost:8029/api/v1  # optional
   ```
3. Run the demo:
   ```bash
   uv run python main.py
   ```

> To reuse elsewhere, import `AcontextArtifactAgent` and use it as an async context manager:
> ```python
> async with AcontextArtifactAgent(api_key=..., disk_id=...) as agent:
>     result = await agent.run(user_query)
> ```

## Code Structure

```text
agent/
  __init__.py         # exposes AcontextArtifactAgent
  disk.py             # Acontext DiskManager plus read/write helpers
  react.py            # AcontextArtifactAgent class with ReAct loop orchestration
  tools.py            # tool schemas and async handlers (get_tools_schema, create_tool_map)
  pretty_print.py     # console output formatting utilities
main.py               # demo entry point: creates disk and runs agent
pyproject.toml        # dependency manifest (openai + python-dotenv)
README.md             # this guide
```

## Execution Flow

1. **Initialization** (`main.py`):
   - Load environment variables from `.env`
   - Create `AcontextClient` and create a new disk
   - Pass `disk_id` to `AcontextArtifactAgent` when initializing the agent

2. **Agent Setup** (`react.py`):
   - `AcontextArtifactAgent` is initialized as an async context manager
   - On context entry: Create tool map with `disk_id` automatically injected
   - Initialize `AsyncOpenAI` client
   - Initialize conversation with user query

3. **ReAct Loop**:
   - Send messages to OpenAI API with available tools (via `get_tools_schema()`)
   - If model returns tool calls:
     - Execute each tool with `disk_id` automatically injected via tool map
     - Append tool results to conversation history
     - Print formatted tool call information using `pretty_print` utilities
   - Continue until model returns final answer or `max_turn` reached

4. **Tool Execution** (`tools.py`):
   - Tools automatically use the provided `disk_id`
   - `write_file`: Creates/updates files on Acontext disk
   - `read_file`: Reads file content with bounded preview
   - `list_artifacts`: Lists artifacts in a directory on the Acontext disk
   - `download_file`: Downloads file to local `./downloads/` directory

This pattern lets you wrap any sync or async Python function as a tool so the model can extend its capabilities.

### How the Disk Tools Work
- All disk operations go through `DiskManager`, which lazy-loads `AcontextClient` so the client is constructed just once.
- `disk_id` is passed explicitly from `main.py` to `AcontextArtifactAgent`, then injected into all tool calls via `create_tool_map()`.
- Tool schemas are generated via `get_tools_schema()` which converts `TOOL_DEFINITIONS` to OpenAI-compatible format.
- `write_file` accepts an optional `file_path` parameter for organizing files into directories.
- `read_file` returns a bounded-length preview (1200 chars) to avoid overwhelming the model with large payloads.
- `list_artifacts` lists all artifacts in a specified directory path, returning their names and types.
- `download_file` fetches a temporary link, stores the file under `./downloads` (or your chosen path), and returns the local path in the tool result.
- All tools use `ToolDefinition` dataclass that combines schema and implementation, with `disk_id` automatically injected via factory functions.


