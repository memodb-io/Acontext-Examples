"""
Claude Agent SDK + Acontext integration example.

Run a short multi-turn conversation with Claude, capture the transcript in the
Anthropic message format, and forward it to Acontext to create tasks.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv

from acontext import AcontextClient
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

PROMPTS = [
    "I'd like to spend three days in Finland enjoying nature. Please propose a plan.",
    "That sounds fun. Can you check what the weather is typically like for that plan?",
    "Great, I'm currently in Shanghai. Please secure a flight that avoids red-eye departures.",
]


def require_env(key: str) -> str:
    """Fetch an environment variable or raise an informative error."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"The environment variable '{key}' is required for this example.")
    return value


def serialize_content_block(block: TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock) -> dict[str, Any]:
    """Convert SDK content blocks into Anthropic's message schema."""
    if isinstance(block, TextBlock):
        return {"type": "text", "text": block.text}
    if isinstance(block, ThinkingBlock):
        return {
            "type": "thinking",
            "thinking": block.thinking,
            "signature": block.signature,
        }
    if isinstance(block, ToolUseBlock):
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    if isinstance(block, ToolResultBlock):
        tool_result: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": block.tool_use_id,
        }
        if block.content is not None:
            tool_result["content"] = block.content
        if block.is_error is not None:
            tool_result["is_error"] = block.is_error
        return tool_result
    raise TypeError(f"Unsupported content block type: {type(block).__name__}")


def serialize_message(message: UserMessage | AssistantMessage) -> dict[str, Any]:
    """Convert SDK message objects into Anthropic-compatible dictionaries."""
    if isinstance(message, UserMessage):
        if isinstance(message.content, str):
            content = [{"type": "text", "text": message.content}]
        else:
            content = [serialize_content_block(block) for block in message.content]
        serialized: dict[str, Any] = {"role": "user", "content": content}
        if message.parent_tool_use_id:
            serialized["parent_tool_use_id"] = message.parent_tool_use_id
        return serialized

    content_blocks = [serialize_content_block(block) for block in message.content]
    serialized = {
        "role": "assistant",
        "content": content_blocks,
    }
    if message.parent_tool_use_id:
        serialized["parent_tool_use_id"] = message.parent_tool_use_id
    return serialized


def pretty_print_message(message: UserMessage | AssistantMessage) -> None:
    """Print friendly console output for user/assistant messages."""
    role = "[User]" if isinstance(message, UserMessage) else "[Claude]"
    if isinstance(message, UserMessage) and isinstance(message.content, str):
        print(f"{role} {message.content}")
        return

    blocks = message.content if isinstance(message.content, list) else []
    for block in blocks:
        if isinstance(block, TextBlock):
            print(f"{role} {block.text}")
        elif isinstance(block, ThinkingBlock):
            preview = block.thinking[:120].replace("\n", " ")
            print(f"{role} (thinking) {preview}...")
        elif isinstance(block, ToolUseBlock):
            print(f"{role} Tool call -> {block.name}: {json.dumps(block.input, ensure_ascii=False)}")
        elif isinstance(block, ToolResultBlock):
            snippet = block.content
            if isinstance(snippet, list):
                snippet = json.dumps(snippet, ensure_ascii=False)
            print(f"{role} Tool result -> {snippet}")


async def run_claude_conversation(
    anthropic_api_key: str,
    anthropic_base_url: str | None = None,
) -> tuple[list[dict[str, Any]], list[ResultMessage]]:
    """
    Execute the scripted prompts with Claude and return the Anthropic transcript.

    Returns:
        transcript: List of Anthropic-formatted message dicts.
        results: List of ResultMessage objects emitted by the SDK.
    """
    transcript: list[dict[str, Any]] = []
    results: list[ResultMessage] = []

    env = {"ANTHROPIC_API_KEY": anthropic_api_key}
    if anthropic_base_url:
        env["ANTHROPIC_BASE_URL"] = anthropic_base_url

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful travel assistant who produces structured plans.",
        max_turns=1,
        allowed_tools=["WebSearch", "Bash", "Read", "Write"],
        env=env,
    )

    async with ClaudeSDKClient(options=options) as client:
        for prompt in PROMPTS:
            print(f"\n[User] {prompt}")
            await client.query(prompt)

            async for message in client.receive_response():
                if isinstance(message, (UserMessage, AssistantMessage)):
                    pretty_print_message(message)
                    transcript.append(serialize_message(message))
                elif isinstance(message, ResultMessage):
                    results.append(message)
                    cost = message.total_cost_usd
                    if cost:
                        print(f"[Cost] Turn cost: ${cost:.4f}")

    return transcript, results


def send_transcript_to_acontext(
    transcript: list[dict[str, Any]],
    api_key: str,
    base_url: str,
) -> None:
    """Create an Acontext session, upload the transcript, and print extracted tasks."""
    if not transcript:
        raise ValueError("Transcript is empty – nothing to send to Acontext.")

    with AcontextClient(
        api_key=api_key,
        base_url=base_url,
        timeout=60,
    ) as client:
        print("\n[acontext] Creating space and session...")
        space = client.spaces.create()
        session = client.sessions.create(space_id=space.id)
        print(f"[acontext] Space: {space.id} | Session: {session.id}")

        print("[acontext] Sending messages (format='anthropic')...")
        for message in transcript:
            client.sessions.send_message(
                session_id=session.id,
                blob=message,
                format="anthropic",
            )

        print("[acontext] Flushing session to trigger task extraction...")
        client.sessions.flush(session.id)

        tasks = client.sessions.get_tasks(session.id)
        print(f"[acontext] Received {len(tasks.items)} tasks\n")

        for task in tasks.items:
            description = task.data.get("task_description", "Unknown task")
            print(f"- Task #{task.order} ({task.status}) -> {description}")
            progresses = task.data.get("progresses", [])
            if progresses:
                print("  Progress updates:")
                for progress in progresses:
                    print(f"    • {progress}")
            preferences = task.data.get("user_preferences", [])
            if preferences:
                print("  User preferences:")
                for pref in preferences:
                    print(f"    • {pref}")


async def main() -> None:
    """Entrypoint for running the example end-to-end."""
    load_dotenv()
    anthropic_api_key = require_env("ANTHROPIC_API_KEY")
    anthropic_base_url = os.getenv("ANTHROPIC_BASE_URL")
    acontext_api_key = require_env("ACONTEXT_API_KEY")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")

    transcript, results = await run_claude_conversation(
        anthropic_api_key=anthropic_api_key,
        anthropic_base_url=anthropic_base_url,
    )
    total_cost = sum(filter(None, (result.total_cost_usd for result in results)))
    print(f"\n[Summary] Total Claude SDK cost: ${total_cost:.4f}" if total_cost else "\n[Summary] Total Claude SDK cost: n/a")

    send_transcript_to_acontext(
        transcript=transcript,
        api_key=acontext_api_key,
        base_url=acontext_base_url,
    )


if __name__ == "__main__":
    asyncio.run(main())

