# OpenAI ReAct Agent Demo

Minimal async ReAct-style agent that uses the OpenAI Python SDK plus the Acontext
Disk Tools to demonstrate tool-calling (write, read, replace, list).

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
   - With uv: `uv sync` (recommended)
   - With pip: `python -m venv .venv && .venv\Scripts\activate && pip install -e .`
   
   **Note**: This project requires `acontext>=0.1.0` for `DISK_TOOLS` support.

## Run the Demo
```
uv run python main.py
```
The agent will:
1. Create an Acontext disk automatically
2. Write `/notes/demo.txt` on the Acontext disk with a short tools summary
3. List the artifacts in `/notes/` directory
4. Read the file back to verify content
5. Use `replace_string` to modify content in the file

Console logs show each tool invocation and the final response.

## Repo Layout
```
agent/
  __init__.py        # exports AcontextArtifactAgent
  react.py           # AcontextArtifactAgent class with chat loop + tool call handling
  tools.py           # deprecated (now using DISK_TOOLS from SDK)
  disk.py            # deprecated (now using DISK_TOOLS from SDK)
  pretty_print.py    # console output formatting utilities
main.py              # demo entry point: creates disk and runs agent
```
## Troubleshooting
- Missing `.env` values → runtime `RuntimeError` when loading API keys.
- Disk errors → confirm `ACONTEXT_API_KEY` and the API server URL.

---

# OpenAI React Agent (Python)

This companion section explains how the demo is structured and how you can reuse the components in your own projects.

## Feature Highlights
- **Async execution**: `AsyncOpenAI` plus `asyncio` keep tool calls and model responses concurrent.
- **ReAct loop safeguards**: `max_turn` prevents infinite cycles during experimentation.
- **SDK-integrated tools**: Uses `DISK_TOOLS` from `acontext.agent.disk` for pre-built filesystem operations.
- **Artifact listing**: `list_artifacts` allows the agent to explore directory contents on the Acontext disk.
- **File manipulation**: `write_file`, `read_file`, and `replace_string` provide comprehensive file operations.
- **Custom OpenAI endpoint**: point `base_url` at proxies or private deployments when needed.
- **Explicit disk management**: Disk is created in `main.py` and tool context is passed to `AcontextArtifactAgent`.

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
> from acontext import AcontextClient
> from acontext.agent.disk import DISK_TOOLS
> 
> client = AcontextClient(api_key=..., base_url=...)
> disk = client.disks.create()
> ctx = DISK_TOOLS.format_context(client, disk.id)
> 
> async with AcontextArtifactAgent(api_key=..., tool_context=ctx) as agent:
>     result = await agent.run(user_query)
> ```

## Code Structure

```text
agent/
  __init__.py         # exposes AcontextArtifactAgent
  react.py            # AcontextArtifactAgent class with ReAct loop orchestration
  tools.py            # deprecated (now using DISK_TOOLS from SDK)
  disk.py             # deprecated (now using DISK_TOOLS from SDK)
  pretty_print.py     # console output formatting utilities
main.py               # demo entry point: creates disk and runs agent
pyproject.toml        # dependency manifest (openai + python-dotenv)
README.md             # this guide
```

## Execution Flow

1. **Initialization** (`main.py`):
   - Load environment variables from `.env`
   - Create `AcontextClient` and create a new disk
   - Create tool context using `DISK_TOOLS.format_context(client, disk.id)`
   - Pass `tool_context` to `AcontextArtifactAgent` when initializing the agent

2. **Agent Setup** (`react.py`):
   - `AcontextArtifactAgent` is initialized as an async context manager
   - On context entry: Initialize `AsyncOpenAI` client
   - Get tool schemas using `DISK_TOOLS.to_openai_tool_schema()`
   - Initialize conversation with user query

3. **ReAct Loop**:
   - Send messages to OpenAI API with available tools from `DISK_TOOLS`
   - If model returns tool calls:
     - Execute each tool using `DISK_TOOLS.execute_tool()` wrapped in `asyncio.to_thread()`
     - Append tool results to conversation history
     - Print formatted tool call information using `pretty_print` utilities
   - Continue until model returns final answer or `max_turn` reached

4. **Tool Execution** (via `DISK_TOOLS`):
   - Tools automatically use the provided tool context (contains `disk_id`)
   - `write_file`: Creates/updates text files on Acontext disk
   - `read_file`: Reads file content with optional `line_offset` and `line_limit` parameters
   - `replace_string`: Finds and replaces text in files
   - `list_artifacts`: Lists files and directories in a specified path (requires `file_path` parameter)

This pattern demonstrates how to use the SDK's pre-built `DISK_TOOLS` with async OpenAI clients.

### How the Disk Tools Work
- All disk operations go through `DISK_TOOLS` from `acontext.agent.disk`, which provides pre-configured tools.
- Tool context is created using `DISK_TOOLS.format_context(client, disk.id)` and contains the client and disk ID.
- Tool schemas are generated via `DISK_TOOLS.to_openai_tool_schema()` which returns OpenAI-compatible tool definitions.
- `write_file` accepts `filename`, `content`, and optional `file_path` parameters for organizing files into directories.
- `read_file` accepts `filename`, optional `file_path`, `line_offset` (default 0), and `line_limit` (default 100) parameters.
- `replace_string` accepts `filename`, `old_string`, `new_string`, and optional `file_path` parameters.
- `list_artifacts` requires `file_path` parameter (e.g., `"/notes/"` or `"/"`).
- Tool execution is synchronous, so `asyncio.to_thread()` is used to run `DISK_TOOLS.execute_tool()` in a thread pool.


