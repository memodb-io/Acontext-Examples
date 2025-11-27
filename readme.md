## `acontext-cli` examples

[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

Supported Examples:

### Python Examples

- `python/acontext-basic`: Core Acontext SDK examples demonstrating session management, task extraction, and artifact handling.
- `python/openai-basic`: Direct OpenAI Python SDK integration with Acontext for multi-turn conversations and manual tool calling.
- `python/openai-agent-basic`: OpenAI Agents SDK with Acontext for persistent sessions, automatic tool execution, and conversation resumption.
- `python/openai-agent-artifacts`: Async ReAct-style agent using OpenAI SDK with Acontext Disk APIs for file operations (write, read, download).
- `python/claude-agent-basic`: Claude Agent SDK paired with Acontext for session storage, task extraction, and progress tracking.
- `python/agno-basic`: Agno multi-agent framework integration with Acontext for session persistence and task extraction.
- `python/wait-for-user-confirmation`: Experience confirmation workflow allowing users to review and approve AI-learned patterns before saving to the knowledge base.

### TypeScript Examples

- `typescript/openai-basic`: OpenAI SDK with Acontext integration for session management, task extraction, and conversation history retrieval.
- `typescript/vercel-ai-basic`: Vercel AI SDK with Acontext integration for session management, task extraction, and experience search.



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
