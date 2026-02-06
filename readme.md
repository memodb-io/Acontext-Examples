## `acontext-cli` examples

[![Made with Acontext](https://assets.memodb.io/Acontext/badge-made-with-acontext-dark.svg)](https://acontext.io)

Supported Examples:

### Python Examples

- `python/acontext-basic`: Core Acontext SDK examples demonstrating session management, task extraction, and artifact handling.
- `python/openai-basic`: Direct OpenAI Python SDK integration with Acontext for multi-turn conversations and manual tool calling.
- `python/openai-agent-basic`: OpenAI Agents SDK with Acontext for persistent sessions, automatic tool execution, and conversation resumption.
- `python/openai-agent-artifacts`: Async ReAct-style agent using OpenAI SDK with Acontext Disk APIs for file operations (write, read, download).
- `python/claude-agent-sdk`: Claude Agent SDK with `ClaudeAgentStorage` for automatic message persistence and session-id discovery.
- `python/agno-basic`: Agno multi-agent framework integration with Acontext for session persistence and task extraction.
- `python/smolagents-basic`: Smolagents (HuggingFace) tool-calling agent with Acontext for session persistence, task extraction, and conversation resumption.
- `python/interactive-agent-skill`: Interactive sandbox demo that uploads Acontext Skills (zip) and runs an OpenAI agentic loop with bash, Python, and file export tools.
- `python/wait-for-user-confirmation`: User confirmation workflow allowing users to review and approve AI-learned patterns before saving to the knowledge base.

### TypeScript Examples

- `typescript/openai-basic`: OpenAI SDK with Acontext integration for session management, task extraction, and conversation history retrieval.
- `typescript/vercel-ai-basic`: Vercel AI SDK with Acontext integration for session management and task extraction.
- `typescript/claude-agent-sdk`: Claude Agent SDK with `ClaudeAgentStorage` for automatic message persistence and session-id discovery.
- `typescript/interactive-agent-skill`: Interactive sandbox demo (TypeScript) that uploads Acontext Skills and runs an OpenAI agentic loop with bash, Python, and file export tools.



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
