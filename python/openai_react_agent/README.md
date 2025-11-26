# OpenAI ReAct Agent Demo

Minimal async ReAct-style agent that uses the OpenAI Python SDK plus the Acontext
Disk APIs to demonstrate tool-calling (write, read, download).

## Prerequisites
- Python 3.11+ (project uses `uv` but regular `pip` also works)
- OpenAI API key with access to the specified model
- Acontext API key (and optional base URL / disk ID for self-hosted setups)

## Setup
1. `cd Acontext-Examples/python/openai_react_agent`
2. Copy `.env.example` to `.env` and fill in:
   ```
   OPENAI_API_KEY=...
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_BASE_URL=https://api.openai.com/v1
   ACONTEXT_API_KEY=...
   ACONTEXT_BASE_URL=http://localhost:8029/api/v1
   ACONTEXT_DISK_ID=...  # optional, auto-created if omitted
   ```
3. Install dependencies:
   - With uv: `uv sync`
   - With pip: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`

## Run the Demo
```
uv run python main.py
```
The agent will:
1. Write `/notes/demo.txt` on the Acontext disk with a short tools summary
2. Read the file back to verify content
3. Download the file into `./downloads/demo.txt`

Console logs show each tool invocation and the final response.

## Repo Layout
```
agent/
  __init__.py        # exports react_agent()
  react.py           # chat loop + tool call handling
  tools.py           # tool schemas + async wrappers
  disk.py            # lazy DiskManager built on AcontextClient
downloads/           # local destination for downloaded artifacts
main.py              # demo entry point / prompt
```

## Troubleshooting
- Missing `.env` values → runtime `RuntimeError` when loading API keys.
- Disk errors → confirm `ACONTEXT_API_KEY` and the API server URL.
- Download step fails → ensure `downloads/` exists or let the tool create it.
# OpenAI React Agent (Python)

This companion section explains—still in English—how the demo is structured and how you can reuse the components in your own projects.

## Feature Highlights
- **Async execution**: `AsyncOpenAI` plus `asyncio` keep tool calls and model responses concurrent.
- **ReAct loop safeguards**: `max_turn` prevents infinite cycles during experimentation.
- **Modular tool layer**: `agent/disk.py` wraps the Disk APIs, while `agent/tools.py` declares schemas and async implementations.
- **Canonical download flow**: `download_disk_file` produces a temporary link and writes the artifact to `./downloads` (or a path you pass in).
- **Custom OpenAI endpoint**: point `base_url` at proxies or private deployments when needed.

> Set `ACONTEXT_DISK_ID` to reuse a single disk automatically, or pass `disk_id` per call when you want isolation.

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
   ACONTEXT_DISK_ID=dsk_xxx  # optional; auto-created if omitted
   ```
3. Run the demo:
   ```bash
   uv run python main.py
   ```

> To reuse elsewhere, import `react_agent` and pass `user_query`, `api_key`, and any overrides you need.

## Code Structure

```text
agent/
  __init__.py         # exposes react_agent
  disk.py             # Acontext DiskManager plus read/write helpers
  react.py            # ReAct loop orchestration
  tools.py            # tool schemas and async handlers
main.py               # demo entry point that loads env vars
pyproject.toml        # dependency manifest (openai + python-dotenv)
README.md             # this guide
```

## Execution Flow
1. Define tool schemas (OpenAI function specs).
2. Call `chat.completions` with the available tools.
3. When the model requests a tool via `tool_calls`:
   - Look up the local async implementation and execute it.
   - Append the result as a `role="tool"` message.
4. Continue querying the model until no more tool calls are present or `max_turn` is reached.

This pattern lets you wrap any sync or async Python function as a tool so the model can extend its capabilities.

### How the Disk Tools Work
- All disk operations go through `DiskManager`, which lazy-loads `AcontextClient` so the client is constructed just once.
- Configuration defaults to `.env` values; missing `ACONTEXT_DISK_ID` triggers automatic disk creation that is reused for the session.
- `write_disk_file` accepts an optional `meta` payload for provenance, tags, or any custom data.
- `read_disk_file` returns a bounded-length preview to avoid overwhelming the model with large payloads.
- `download_disk_file` fetches a temporary link, stores the file under `./downloads` (or your chosen path), and returns the local path in the tool result.


