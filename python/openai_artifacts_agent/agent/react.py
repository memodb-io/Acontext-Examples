from __future__ import annotations

import json
from typing import Any, Dict

from openai import AsyncOpenAI

from .tools import tool_map, tools


async def react_agent(
    user_query: str,
    api_key: str,
    base_url: str | None = None,
    model: str = "gpt-4o-mini",
    max_turn: int = 5,
) -> str:
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    messages: list[Dict[str, Any]] = [{"role": "user", "content": user_query}]
    turn_count = 0

    while turn_count < max_turn:
        turn_count += 1
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        ai_msg = response.choices[0].message
        messages.append(ai_msg)

        tool_calls = ai_msg.tool_calls or []
        if not tool_calls:
            print("Agent final response:", ai_msg.content)
            return ai_msg.content or ""

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments or "{}"
            tool_args = json.loads(raw_args)
            tool_func = tool_map[tool_name]
            tool_result = await tool_func(**tool_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )
            print(f"Tool call [{tool_name}] args: {tool_args}, result: {tool_result}")

    final_msg = "Max interaction turns reached, stopping execution."
    print("Agent final response:", final_msg)
    return final_msg

