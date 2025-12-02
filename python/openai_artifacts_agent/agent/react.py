from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from openai import AsyncOpenAI

from .tools import create_tool_map, get_tools_schema
from .pretty_print import print_tool_call, print_info, print_success, print_box, print_warning


class AcontextArtifactAgent:
    """
    Acontext artifact agent as an async context manager.
    
    Usage:
        async with AcontextArtifactAgent(api_key=..., disk_id=...) as agent:
            result = await agent.run(user_query)
    """
    
    def __init__(
        self,
        api_key: str,
        disk_id: str,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        max_turn: int = 5,
    ):
        """
        Initialize AcontextArtifactAgent.
        
        Args:
            api_key: OpenAI API key
            disk_id: Acontext disk ID
            base_url: OpenAI base URL (optional)
            model: Model name to use
            max_turn: Maximum number of interaction turns
        """
        self.api_key = api_key
        self.disk_id = disk_id
        self.base_url = base_url
        self.model = model
        self.max_turn = max_turn
        self.client: AsyncOpenAI | None = None
        self.tool_map: dict[str, Any] | None = None
    
    async def __aenter__(self) -> "AcontextArtifactAgent":
        """Initialize OpenAI client and tool map when entering context."""
        # Create tool map with disk_id automatically injected
        self.tool_map = create_tool_map(self.disk_id)
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up resources when exiting context."""
        pass
    
    async def run(self, user_query: str) -> str:
        """
        Run the react agent with the given user query.
        
        Args:
            user_query: The user's query/request
            
        Returns:
            The final response from the agent
        """
        if self.client is None or self.tool_map is None:
            raise RuntimeError("AcontextArtifactAgent must be used as an async context manager")
        
        messages: list[Dict[str, Any]] = [{"role": "user", "content": user_query}]
        turn_count = 0

        # Main agent loop
        while turn_count < self.max_turn:
            turn_count += 1
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=get_tools_schema(),
                tool_choice="auto",
            )

            ai_msg = response.choices[0].message
            messages.append(ai_msg)

            tool_calls = ai_msg.tool_calls or []
            if not tool_calls:
                print_box("Agent Final Response", ai_msg.content or "")
                return ai_msg.content or ""

            # Execute tool calls with disk_id automatically injected
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                raw_args = tool_call.function.arguments or "{}"
                tool_args = json.loads(raw_args)
                tool_func = self.tool_map[tool_name]
                tool_result = await tool_func(**tool_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )
                print_tool_call(tool_name, tool_args, tool_result)

        final_msg = "Max interaction turns reached, stopping execution."
        print_warning(final_msg)
        return final_msg



