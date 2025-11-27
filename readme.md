## `acontext-cli` examples

Supported Examples:

### Python Examples

- `python/acontext-basic`: Basic SDK examples for session management, task extraction, and artifact handling.
- `python/openai-basic`: Use OpenAI SDK and save the data to Acontext.
- `python/openai-agent-basic`: Use OpenAI Agents SDK and save the data to Acontext.
- `python/openai_artifacts_agent`: Async ReAct-style agent using OpenAI Python SDK with Acontext Disk APIs for tool-calling (write, read, download).
- `python/claude-agent-basic`: Use Claude Agent SDK with Acontext for session storage, task extraction, and progress tracking.
- `python/agno-basic`: Use Agno framework and save the data to Acontext.

### TypeScript Examples

- `typescript/openai-basic`: Use OpenAI SDK with Acontext integration for session management and task extraction.
- `typescript/vercel-ai-basic`: Use Vercel AI SDK with Acontext integration for session management and task extraction.



### Install/Update cli

```bash
curl -fsSL https://install.acontext.io | sh
```



### Download templates

```bash
acontext create my-project --template-path "python/openai_basic"
```



### Conventions

- We use `uv` as pkg manager for Python Examples
- We use `npm` as pkg manager for Typescript Examples
